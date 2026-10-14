package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io"
	"io/fs"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func newTestStore(t *testing.T) *Store {
	t.Helper()
	store, err := NewStore(t.TempDir())
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	return store
}

func TestBlobRoundTrip(t *testing.T) {
	store := newTestStore(t)
	payload := []byte(`{"attempts":[],"tasksDone":0}`)

	if err := store.WriteBlob("progress", payload); err != nil {
		t.Fatalf("WriteBlob: %v", err)
	}
	got, err := store.ReadBlob("progress")
	if err != nil {
		t.Fatalf("ReadBlob: %v", err)
	}
	if !bytes.Equal(got, payload) {
		t.Fatalf("ReadBlob = %s, want %s", got, payload)
	}

	missing, err := store.ReadBlob("settings")
	if err != nil {
		t.Fatalf("ReadBlob(missing): %v", err)
	}
	if missing != nil {
		t.Fatalf("ReadBlob(missing) = %s, want nil", missing)
	}
}

func TestBlobRejectsBadInput(t *testing.T) {
	store := newTestStore(t)

	if err := store.WriteBlob("../escape", []byte(`{}`)); err == nil {
		t.Fatal("WriteBlob accepted a path traversal key")
	}
	if err := store.WriteBlob("progress", []byte(`{oops`)); err == nil {
		t.Fatal("WriteBlob accepted invalid JSON")
	}
	if _, err := store.ReadBlob("Progress"); err == nil {
		t.Fatal("ReadBlob accepted an invalid key")
	}
	good := []byte(`{"ok":true}`)
	if err := store.WriteBlob("progress", good); err != nil {
		t.Fatalf("WriteBlob: %v", err)
	}
	_ = store.WriteBlob("progress", []byte("broken"))
	after, err := store.ReadBlob("progress")
	if err != nil || !bytes.Equal(after, good) {
		t.Fatalf("blob damaged after a failed write: %s (%v)", after, err)
	}
}

func TestContentOverlayTakesPrecedence(t *testing.T) {
	store := newTestStore(t)
	if _, ok := store.ReadContent("bank"); ok {
		t.Fatal("overlay should be empty on a fresh install")
	}
	overlay := []byte(`{"tasks":[{"id":"new-task"}]}`)
	if err := store.WriteContent("bank", overlay); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	got, ok := store.ReadContent("bank")
	if !ok || !bytes.Equal(got, overlay) {
		t.Fatalf("ReadContent = %s, %v", got, ok)
	}
	if err := store.WriteContent("../../etc/passwd", overlay); err == nil {
		t.Fatal("WriteContent accepted a path traversal name")
	}
}

func TestWriteReport(t *testing.T) {
	store := newTestStore(t)
	path, err := store.WriteReport("progress", []byte("<html>отчёт</html>"))
	if err != nil {
		t.Fatalf("WriteReport: %v", err)
	}
	if filepath.Dir(path) != store.Reports() {
		t.Fatalf("report saved to %s, want %s", path, store.Reports())
	}
	data, err := os.ReadFile(path)
	if err != nil || !strings.Contains(string(data), "отчёт") {
		t.Fatalf("report content: %s (%v)", data, err)
	}
}

// feedServer publishes a content manifest plus one file, like a GitHub release.
func feedServer(t *testing.T, version string, bank []byte) *httptest.Server {
	t.Helper()
	sum := sha256.Sum256(bank)
	mux := http.NewServeMux()
	mux.HandleFunc("/version.json", func(w http.ResponseWriter, r *http.Request) {
		manifest := map[string]any{
			"contentVersion": version,
			"counts":         map[string]int{"bank": 150, "analogous": 552},
			"files": map[string]any{
				"bank.json": map[string]any{"sha256": hex.EncodeToString(sum[:]), "bytes": len(bank)},
			},
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(manifest)
	})
	mux.HandleFunc("/bank.json", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write(bank)
	})
	return httptest.NewServer(mux)
}

func TestCheckUpdatesInstallsNewVersion(t *testing.T) {
	store := newTestStore(t)
	bank := []byte(`{"meta":{"contentVersion":"2026.10.9"},"tasks":[]}`)
	feed := feedServer(t, "2026.10.9", bank)
	defer feed.Close()

	result := store.CheckUpdates(feed.URL, "2026.10.1")
	if result.Status != "updated" {
		t.Fatalf("status = %q (%s)", result.Status, result.Message)
	}
	if result.Version != "2026.10.9" || result.Files != 1 {
		t.Fatalf("result = %+v", result)
	}
	installed, ok := store.ReadContent("bank")
	if !ok || !bytes.Equal(installed, bank) {
		t.Fatalf("installed bank = %s", installed)
	}

	again := store.CheckUpdates(feed.URL, "2026.10.9")
	if again.Status != "uptodate" {
		t.Fatalf("second check = %+v", again)
	}
}

func TestCheckUpdatesRejectsTamperedFile(t *testing.T) {
	store := newTestStore(t)
	feed := feedServer(t, "2026.11.1", []byte(`{"tasks":[{"id":"honest"}]}`))
	defer feed.Close()

	// подменяем содержимое банка, оставив прежнюю контрольную сумму в манифесте
	tampered := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "bank.json") {
			_, _ = w.Write([]byte(`{"tasks":[{"id":"evil"}]}`))
			return
		}
		response, err := http.Get(feed.URL + r.URL.Path)
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		defer response.Body.Close()
		w.Header().Set("Content-Type", "application/json")
		body, _ := io.ReadAll(response.Body)
		_, _ = w.Write(body)
	}))
	defer tampered.Close()

	result := store.CheckUpdates(tampered.URL, "2026.10.1")
	if result.Status != "error" || !strings.Contains(result.Message, "checksum") {
		t.Fatalf("tampered update accepted: %+v", result)
	}
	if _, ok := store.ReadContent("bank"); ok {
		t.Fatal("tampered content was installed")
	}
}

func TestCheckUpdatesOffline(t *testing.T) {
	store := newTestStore(t)
	// Закрытый порт на этой машине: соединение отклоняется сразу, поэтому тест
	// не зависит от того, доступен ли настоящий канал обновлений.
	result := store.CheckUpdates("http://127.0.0.1:1", "2026.10.1")
	if result.Status != "offline" {
		t.Fatalf("status = %q, want offline", result.Status)
	}
	// Пустой адрес означает «взять канал по умолчанию»; сам адрес должен
	// указывать на последний релиз репозитория (без обращения к сети).
	want := "https://github.com/zigorminsk-debug/mathematics/releases/latest/download"
	if defaultFeed != want {
		t.Fatalf("defaultFeed = %q, want %q", defaultFeed, want)
	}
}

/* ------------------------------------------------------------- HTTP API --- */

func newTestServer(t *testing.T) (*server, *Store) {
	t.Helper()
	store := newTestStore(t)
	return &server{
		store:   store,
		version: appVersion,
		build:   "test",
		dataDir: store.Base(),
		quit:    make(chan struct{}),
	}, store
}

func TestAPIStateAndBlob(t *testing.T) {
	srv, _ := newTestServer(t)
	mux := http.NewServeMux()
	mux.HandleFunc("/api/state", srv.handleState)
	mux.HandleFunc("/api/blob", srv.handleBlob)

	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/api/state", nil))
	if recorder.Code != http.StatusOK {
		t.Fatalf("state code = %d", recorder.Code)
	}
	var state map[string]any
	if err := json.Unmarshal(recorder.Body.Bytes(), &state); err != nil {
		t.Fatalf("state json: %v", err)
	}
	app := state["app"].(map[string]any)
	if app["platform"] != "windows" || app["developer"] == "" {
		t.Fatalf("state.app = %+v", app)
	}

	body := strings.NewReader(`{"attempts":[{"id":"a1"}],"tasksDone":1}`)
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, "/api/blob?key=progress", body))
	if recorder.Code != http.StatusOK {
		t.Fatalf("save code = %d: %s", recorder.Code, recorder.Body)
	}
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/api/blob?key=progress", nil))
	if !strings.Contains(recorder.Body.String(), `"a1"`) {
		t.Fatalf("loaded blob = %s", recorder.Body)
	}

	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/api/blob?key=../secret", nil))
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("bad key code = %d", recorder.Code)
	}
}

func TestStaticServingAndContentOverlay(t *testing.T) {
	srv, store := newTestServer(t)
	webRoot, err := fs.Sub(embedded, "web")
	if err != nil {
		t.Fatalf("embedded web root: %v", err)
	}
	mux := http.NewServeMux()
	mux.Handle("/content/", srv.contentHandler(webRoot))
	mux.Handle("/", srv.staticHandler(webRoot))

	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/", nil))
	if recorder.Code != http.StatusOK {
		t.Fatalf("index code = %d", recorder.Code)
	}
	if !strings.Contains(recorder.Body.String(), "<!DOCTYPE html>") {
		t.Fatal("index.html not served from the embedded filesystem")
	}

	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if recorder.Code != http.StatusOK || !strings.Contains(recorder.Body.String(), "\"tasks\"") {
		t.Fatalf("embedded bank not served (code %d)", recorder.Code)
	}

	overlay := []byte(`{"meta":{"contentVersion":"2099.1"},"tasks":[{"id":"overlay-task"}]}`)
	if err := store.WriteContent("bank", overlay); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	if err := store.WriteContent("version", []byte(`{"contentVersion":"2099.1","files":{}}`)); err != nil {
		t.Fatalf("WriteContent(version): %v", err)
	}
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if !strings.Contains(recorder.Body.String(), "overlay-task") {
		t.Fatalf("overlay not served: %s", recorder.Body)
	}
	if srv.contentVersion() != "2099.1" {
		t.Fatalf("contentVersion = %q", srv.contentVersion())
	}
}

// TestStaleOverlayDoesNotShadowEmbeddedBank: a pack downloaded by the previous
// build must not hide the newer bank embedded in a new executable — after an
// in-place update the new variant has to appear without a manual refresh.
func TestStaleOverlayDoesNotShadowEmbeddedBank(t *testing.T) {
	srv, store := newTestServer(t)
	embeddedVersionName := embeddedVersion()
	if embeddedVersionName == "" {
		t.Fatal("embedded content version is empty")
	}
	stale := []byte(`{"meta":{"contentVersion":"2000.1.1"},"tasks":[{"id":"stale-task"}]}`)
	if err := store.WriteContent("bank", stale); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	if err := store.WriteContent("version", []byte(`{"contentVersion":"2000.1.1","files":{}}`)); err != nil {
		t.Fatalf("WriteContent(version): %v", err)
	}
	if srv.overlayCurrent() {
		t.Fatal("stale overlay reported as current")
	}
	if got := srv.contentVersion(); got != embeddedVersionName {
		t.Fatalf("contentVersion = %q, want embedded %q", got, embeddedVersionName)
	}
	webRoot, err := fs.Sub(embedded, "web")
	if err != nil {
		t.Fatalf("embedded web root: %v", err)
	}
	mux := http.NewServeMux()
	mux.Handle("/content/", srv.contentHandler(webRoot))
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if strings.Contains(recorder.Body.String(), "stale-task") {
		t.Fatalf("stale overlay was served over the embedded bank: %s", recorder.Body)
	}
	if !strings.Contains(recorder.Body.String(), "\"tasks\"") {
		t.Fatalf("embedded bank not served (code %d)", recorder.Code)
	}
}

// TestCheckUpdatesInstallsTheManifest checks that a downloaded update also stores
// the manifest, because that is where the installed content version comes from.
func TestCheckUpdatesInstallsTheManifest(t *testing.T) {
	store := newTestStore(t)
	bank := []byte(`{"meta":{"contentVersion":"2026.10.9"},"tasks":[]}`)
	feed := feedServer(t, "2026.10.9", bank)
	defer feed.Close()

	if result := store.CheckUpdates(feed.URL, "2026.10.1"); result.Status != "updated" {
		t.Fatalf("status = %q (%s)", result.Status, result.Message)
	}
	manifest, ok := store.ReadContent("version")
	if !ok || !strings.Contains(string(manifest), "2026.10.9") {
		t.Fatalf("manifest not installed: %s (%v)", manifest, ok)
	}
}

func TestReportEndpoint(t *testing.T) {
	srv, store := newTestServer(t)
	mux := http.NewServeMux()
	mux.HandleFunc("/api/report", srv.handleReport)
	payload, _ := json.Marshal(map[string]string{"kind": "progress", "html": "<html>ok</html>"})
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, "/api/report", bytes.NewReader(payload)))
	if recorder.Code != http.StatusOK {
		t.Fatalf("report code = %d: %s", recorder.Code, recorder.Body)
	}
	entries, err := os.ReadDir(store.Reports())
	if err != nil || len(entries) != 1 {
		t.Fatalf("reports dir = %v (%v)", entries, err)
	}
}

func TestContentVersionFallsBackToEmbedded(t *testing.T) {
	srv, _ := newTestServer(t)
	if version := srv.contentVersion(); version == "" {
		t.Fatal("embedded content version is empty — did tools/sync_assets.py run?")
	}
}

func TestNumericContentVersions(t *testing.T) {
    cases := []struct { left, right string; want int }{
        {"2026.10.3", "2026.9.99", 1},
        {"2026.10.2", "2026.10.3", -1},
        {"2026.10", "2026.10.0", 0},
        {"2027.1.0", "2026.12.99", 1},
    }
    for _, item := range cases {
        if got := compareContentVersions(item.left, item.right); got != item.want {
            t.Fatalf("compare(%q,%q) = %d, want %d", item.left, item.right, got, item.want)
        }
    }
}

func TestUpdateFeedCannotDowngradeNewBuild(t *testing.T) {
    store := newTestStore(t)
    bank := []byte(`{"meta":{"contentVersion":"2026.10.1"},"tasks":[]}`)
    feed := feedServer(t, "2026.10.1", bank)
    defer feed.Close()
    got := store.CheckUpdates(feed.URL, "2026.10.3")
    if got.Status != "uptodate" || got.Version != "2026.10.3" {
        t.Fatalf("downgrade was accepted: %+v", got)
    }
    if _, ok := store.ReadContent("bank"); ok { t.Fatal("an older bank was installed") }
}

func TestBrokenPackLeavesPreviousContentAndProgressIntact(t *testing.T) {
    store := newTestStore(t)
    old := []byte(`{"old":true}`)
    for _, name := range []string{"bank", "topics", "version"} {
        if err := store.WriteContent(name, old); err != nil { t.Fatal(err) }
    }
    progress := []byte(`{"tasksDone":17}`)
    if err := store.WriteBlob("progress", progress); err != nil { t.Fatal(err) }
    fresh := []byte(`{"tasks":[]}`)
    digest := sha256.Sum256(fresh)
    feed := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path == "/version.json" {
            json.NewEncoder(w).Encode(map[string]any{
                "contentVersion":"2027.1.0",
                "files":map[string]any{
                    "bank.json":map[string]any{"sha256":hex.EncodeToString(digest[:])},
                    "topics.json":map[string]any{"sha256":strings.Repeat("0",64)},
                },
            })
        } else { w.Write(fresh) }
    }))
    defer feed.Close()
    if got := store.CheckUpdates(feed.URL,"2026.10.3"); got.Status != "error" {
        t.Fatalf("bad checksum accepted: %+v",got)
    }
    for _, name := range []string{"bank", "topics", "version"} {
        if got, ok := store.ReadContent(name); !ok || !bytes.Equal(got, old) { t.Fatalf("%s changed on failed update",name) }
    }
    if got, _ := store.ReadBlob("progress"); !bytes.Equal(got,progress) { t.Fatal("progress changed on update") }
}

func TestRecoverContentBackup(t *testing.T) {
    base := t.TempDir()
    store, err := NewStore(base)
    if err != nil { t.Fatal(err) }
    old := []byte(`{"old":true}`)
    if err := store.WriteContent("bank", old); err != nil { t.Fatal(err) }
    if err := os.Rename(store.ContentDir(), filepath.Join(store.Root(), "content.previous")); err != nil { t.Fatal(err) }
    recovered, err := NewStore(base)
    if err != nil { t.Fatal(err) }
    if got, ok := recovered.ReadContent("bank"); !ok || !bytes.Equal(got, old) { t.Fatal("pack not recovered") }
}
