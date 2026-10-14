package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
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
	if err != nil || !bytes.Equal(got, payload) {
		t.Fatalf("ReadBlob = %s (%v), want %s", got, err, payload)
	}
	if missing, err := store.ReadBlob("settings"); err != nil || missing != nil {
		t.Fatalf("ReadBlob(missing) = %s (%v), want nil", missing, err)
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
	good := []byte(`{"ok":true}`)
	if err := store.WriteBlob("progress", good); err != nil {
		t.Fatalf("WriteBlob: %v", err)
	}
	_ = store.WriteBlob("progress", []byte("broken"))
	if after, err := store.ReadBlob("progress"); err != nil || !bytes.Equal(after, good) {
		t.Fatalf("blob damaged after a failed write: %s (%v)", after, err)
	}
	if err := store.WriteContent("../../etc/passwd", good); err == nil {
		t.Fatal("WriteContent accepted a path traversal name")
	}
}

func TestWriteReport(t *testing.T) {
	store := newTestStore(t)
	path, err := store.WriteReport("russian-progress", []byte("<html>отчёт</html>"))
	if err != nil {
		t.Fatalf("WriteReport: %v", err)
	}
	if filepath.Dir(path) != store.Reports() {
		t.Fatalf("report saved to %s, want %s", path, store.Reports())
	}
	if data, err := os.ReadFile(path); err != nil || !strings.Contains(string(data), "отчёт") {
		t.Fatalf("report content: %s (%v)", data, err)
	}
}

/* ---------------------------------------------------- separate identities --- */

func TestSubjectIdentitiesAreSeparateFromMathematics(t *testing.T) {
	if appName != "Репетитор ЦТ: Русский язык" || dataDirName != "CTRussianTutor" || browserProfile != "ctrussian-window" {
		t.Fatalf("identities: %q %q %q", appName, dataDirName, browserProfile)
	}
	if !strings.HasSuffix(defaultDataDir(), dataDirName) && defaultDataDir() != executableDir() {
		t.Fatalf("default data dir %q", defaultDataDir())
	}
	if subjectID != "russian" || subjectPackage != "by.ziv.ctrussian" || subjectTag != "russian-v" {
		t.Fatal("subject constants must match subject.json")
	}
	for _, url := range []string{releasesAPI, downloadRoot} {
		if strings.Contains(url, "latest") {
			t.Fatalf("the subject channel must never use releases/latest: %s", url)
		}
	}
}

/* --------------------------------------------------------- release choice --- */

func boolPtr(value bool) *bool { return &value }

func release(tag string, draft, prerelease bool, assets []string) githubRelease {
	entry := githubRelease{TagName: tag, Draft: boolPtr(draft), Prerelease: boolPtr(prerelease)}
	for _, name := range assets {
		entry.Assets = append(entry.Assets, struct {
			Name  string `json:"name"`
			State string `json:"state"`
		}{Name: name, State: "uploaded"})
	}
	return entry
}

var mathAssets = []string{"analogous.json", "answer_vectors.json", "app-release.apk", "bank.json", "CTMathsTutor-amd64.exe",
	"CTMathsTutor-arm64.exe", "formulas.json", "mistakes.json", "release-info.json", "SHA256SUMS.txt", "topics.json",
	"ui_strings.json", "version.json"}

func without(list []string, drop string) []string {
	var out []string
	for _, item := range list {
		if item != drop {
			out = append(out, item)
		}
	}
	return out
}

func TestSelectReleaseIgnoresMathAndSiblingFamilies(t *testing.T) {
	got := selectRelease([]githubRelease{
		release("v2026.10.8", false, false, mathAssets),
		release("physics-v2026.10.4", false, false, releaseFiles),
		release("russian-v2026.10.1", false, false, releaseFiles),
	})
	if got == nil || got.Tag != "russian-v2026.10.1" || got.Version != "2026.10.1" {
		t.Fatalf("selected %+v", got)
	}
	if selectRelease([]githubRelease{release("v2026.10.8", false, false, mathAssets)}) != nil {
		t.Fatal("the mathematics latest must never be selected")
	}
}

func TestSelectReleaseExcludesUnsafeCandidates(t *testing.T) {
	missingFlags := githubRelease{TagName: "russian-v2026.10.9"}
	partial := release("russian-v2026.10.6", false, false, without(releaseFiles, "CTRussianTutor-arm64.exe"))
	extra := release("russian-v2026.10.5", false, false, append(append([]string{}, releaseFiles...), "app-debug.apk"))
	starter := release("russian-v2026.10.4", false, false, releaseFiles)
	starter.Assets[0].State = "starter"
	got := selectRelease([]githubRelease{
		missingFlags, release("russian-v2026.10.8", true, false, releaseFiles),
		release("russian-v2026.10.7", false, true, releaseFiles), release("russian-v2026.10.07", false, false, releaseFiles),
		partial, extra, starter, release("russian-v2026.10.2", false, false, releaseFiles),
	})
	if got == nil || got.Tag != "russian-v2026.10.2" {
		t.Fatalf("selected %+v", got)
	}
}

func TestSelectReleaseUsesCanonicalVersionNotOrder(t *testing.T) {
	got := selectRelease([]githubRelease{
		release("russian-v2026.10.99", false, false, releaseFiles),
		release("russian-v2026.11.0", false, false, releaseFiles),
		release("russian-v2026.9.12", false, false, releaseFiles),
	})
	if got == nil || got.Version != "2026.11.0" {
		t.Fatalf("selected %+v", got)
	}
}

/* ------------------------------------------------------- manifest + banks --- */

func russianBank(version string) []byte {
	return []byte(fmt.Sprintf(`{"meta":{"subject":"russian","package":"by.ziv.ctrussian","contentVersion":%q},"tasks":[]}`, version))
}

type pack struct {
	files    map[string][]byte
	manifest map[string]any
}

func newPack(version, tag string) pack {
	files := map[string][]byte{}
	for _, name := range contentFiles {
		files[name] = []byte(`{"ok":true}`)
	}
	files["bank.json"] = russianBank(version)
	files["analogous.json"] = russianBank(version)
	entries := map[string]any{}
	for name, data := range files {
		sum := sha256.Sum256(data)
		entries[name] = map[string]any{"sha256": hex.EncodeToString(sum[:]), "bytes": len(data)}
	}
	return pack{files: files, manifest: map[string]any{
		"schema": 2, "subject": "russian", "package": "by.ziv.ctrussian", "contentProtocol": 2, "tag": tag,
		"contentVersion": version, "files": entries, "counts": map[string]int{"bank": 240, "analogous": 193},
	}}
}

func (p pack) server(t *testing.T) *httptest.Server {
	t.Helper()
	return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		name := filepath.Base(r.URL.Path)
		if name == "version.json" {
			_ = json.NewEncoder(w).Encode(p.manifest)
			return
		}
		data, ok := p.files[name]
		if !ok {
			http.NotFound(w, r)
			return
		}
		_, _ = w.Write(data)
	}))
}

func decodeManifest(t *testing.T, raw map[string]any) contentManifest {
	t.Helper()
	data, _ := json.Marshal(raw)
	var manifest contentManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		t.Fatal(err)
	}
	return manifest
}

func TestManifestGateRejectsForeignContent(t *testing.T) {
	expected := &releaseCandidate{Tag: "russian-v2026.10.1", Version: "2026.10.1"}
	good := newPack("2026.10.1", "russian-v2026.10.1")
	if err := manifestError(decodeManifest(t, good.manifest), expected); err != nil {
		t.Fatalf("valid manifest rejected: %v", err)
	}
	mutations := map[string]func(map[string]any){
		"math subject": func(m map[string]any) { m["subject"] = "mathematics" },
		"math package": func(m map[string]any) { m["package"] = "by.ziv.ctmaths" },
		"old schema":   func(m map[string]any) { m["schema"] = 1 },
		"wrong tag":    func(m map[string]any) { m["tag"] = "v2026.10.8" },
		"extra file": func(m map[string]any) {
			m["files"].(map[string]any)["formulas.json"] = map[string]any{"sha256": strings.Repeat("a", 64), "bytes": 1}
		},
		"no checksum": func(m map[string]any) { m["files"].(map[string]any)["bank.json"] = map[string]any{"bytes": 1} },
	}
	for name, mutate := range mutations {
		broken := newPack("2026.10.1", "russian-v2026.10.1")
		mutate(broken.manifest)
		if manifestError(decodeManifest(t, broken.manifest), expected) == nil {
			t.Fatalf("%s accepted", name)
		}
	}
	if err := bankError([]byte(`{"meta":{"subject":"mathematics","package":"by.ziv.ctmaths"},"tasks":[]}`)); err == nil {
		t.Fatal("a mathematics bank was accepted")
	}
	if err := bankError(russianBank("2026.10.1")); err != nil {
		t.Fatalf("own bank rejected: %v", err)
	}
}

/* ------------------------------------------------------------ update flow --- */

func TestCheckUpdatesResolvesSubjectReleaseThroughAPI(t *testing.T) {
	store := newTestStore(t)
	files := newPack("2026.10.5", "russian-v2026.10.5")
	feed := files.server(t)
	defer feed.Close()
	var pages []string
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		pages = append(pages, r.URL.Query().Get("page"))
		if r.URL.Query().Get("per_page") != "100" || r.Header.Get("Accept") != "application/vnd.github+json" {
			t.Errorf("unexpected API request %s", r.URL)
		}
		var batch []githubRelease
		if r.URL.Query().Get("page") == "1" {
			for i := 0; i < 99; i++ {
				batch = append(batch, release(fmt.Sprintf("v2026.%d.%d", 1+i%12, i), false, false, mathAssets))
			}
			batch = append(batch, release("russian-v2026.10.3", false, false, releaseFiles))
		} else {
			batch = append(batch, release("russian-v2026.10.5", false, false, releaseFiles),
				release("russian-v2026.10.9", true, false, releaseFiles))
		}
		_ = json.NewEncoder(w).Encode(batch)
	}))
	defer api.Close()
	store.api = api.URL
	store.downloads = feed.URL + "/download/"
	got := store.CheckUpdates("", "2026.10.1")
	if got.Status != "updated" || got.Version != "2026.10.5" || got.Tag != "russian-v2026.10.5" {
		t.Fatalf("CheckUpdates = %+v", got)
	}
	if strings.Join(pages, ",") != "1,2" {
		t.Fatalf("pagination requested pages %v", pages)
	}
	if bank, ok := store.ReadContent("bank"); !ok || !bytes.Equal(bank, files.files["bank.json"]) {
		t.Fatal("bank not installed")
	}
	if manifest, ok := store.ReadContent("version"); !ok || !strings.Contains(string(manifest), `"subject":"russian"`) {
		t.Fatal("manifest not installed")
	}
}

func TestCheckUpdatesWithoutSubjectReleaseIsUpToDate(t *testing.T) {
	store := newTestStore(t)
	api := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode([]githubRelease{release("v2026.10.8", false, false, mathAssets)})
	}))
	defer api.Close()
	store.api = api.URL
	if got := store.CheckUpdates("", "2026.10.1"); got.Status != "uptodate" {
		t.Fatalf("a math-only repository must not update the Russian tutor: %+v", got)
	}
	if _, ok := store.ReadContent("bank"); ok {
		t.Fatal("something was installed")
	}
}

func TestCheckUpdatesRejectsForeignBankAndTampering(t *testing.T) {
	cases := map[string]func(*pack){
		"math bank": func(p *pack) {
			p.files["bank.json"] = []byte(`{"meta":{"subject":"mathematics","package":"by.ziv.ctmaths"},"tasks":[]}`)
			sum := sha256.Sum256(p.files["bank.json"])
			p.manifest["files"].(map[string]any)["bank.json"] = map[string]any{"sha256": hex.EncodeToString(sum[:]),
				"bytes": len(p.files["bank.json"])}
		},
		"tampered file": func(p *pack) { p.files["topics.json"] = []byte(`{"ok":false}`) },
		"math manifest": func(p *pack) { p.manifest["subject"] = "mathematics" },
	}
	for name, mutate := range cases {
		store := newTestStore(t)
		progress := []byte(`{"tasksDone":17}`)
		if err := store.WriteBlob("progress", progress); err != nil {
			t.Fatal(err)
		}
		files := newPack("2026.10.5", "russian-v2026.10.5")
		mutate(&files)
		feed := files.server(t)
		got := store.CheckUpdates(feed.URL, "2026.10.1")
		feed.Close()
		if got.Status != "error" {
			t.Fatalf("%s accepted: %+v", name, got)
		}
		if _, ok := store.ReadContent("bank"); ok {
			t.Fatalf("%s left a partial pack", name)
		}
		if data, _ := store.ReadBlob("progress"); !bytes.Equal(data, progress) {
			t.Fatalf("%s changed progress", name)
		}
	}
}

func TestUpdateFeedCannotDowngradeNewBuild(t *testing.T) {
	store := newTestStore(t)
	files := newPack("2026.10.1", "")
	feed := files.server(t)
	defer feed.Close()
	if got := store.CheckUpdates(feed.URL, "2026.10.3"); got.Status != "uptodate" || got.Version != "2026.10.3" {
		t.Fatalf("downgrade was accepted: %+v", got)
	}
}

func TestCheckUpdatesOffline(t *testing.T) {
	store := newTestStore(t)
	store.api = "http://127.0.0.1:1/releases"
	if got := store.CheckUpdates("", "2026.10.1"); got.Status != "offline" {
		t.Fatalf("offline check = %+v", got)
	}
	if got := store.CheckUpdates("ftp://example.com/feed", "2026.10.1"); got.Status != "offline" {
		t.Fatalf("non-https feed must be refused: %+v", got)
	}
}

/* --------------------------------------------------------------- HTTP API --- */

func newTestServer(t *testing.T) (*server, *Store) {
	t.Helper()
	store := newTestStore(t)
	return &server{store: store, version: appVersion, build: "test", dataDir: store.Base(), quit: make(chan struct{})}, store
}

func TestAPIStateAndBlob(t *testing.T) {
	srv, _ := newTestServer(t)
	mux := http.NewServeMux()
	mux.HandleFunc("/api/state", srv.handleState)
	mux.HandleFunc("/api/blob", srv.handleBlob)
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/api/state", nil))
	var state map[string]any
	if err := json.Unmarshal(recorder.Body.Bytes(), &state); err != nil {
		t.Fatalf("state json: %v", err)
	}
	app := state["app"].(map[string]any)
	if app["platform"] != "windows" || app["subject"] != "russian" || app["name"] != appName {
		t.Fatalf("state.app = %+v", app)
	}
	if state["content"].(map[string]any)["channel"] != "russian-v" {
		t.Fatalf("state.content = %+v", state["content"])
	}
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, "/api/blob?key=progress",
		strings.NewReader(`{"attempts":[{"id":"a1"}],"tasksDone":1}`)))
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

func contentMux(t *testing.T, srv *server) *http.ServeMux {
	t.Helper()
	webRoot, err := fs.Sub(embedded, "web")
	if err != nil {
		t.Fatalf("embedded web root: %v", err)
	}
	mux := http.NewServeMux()
	mux.Handle("/content/", srv.contentHandler(webRoot))
	mux.Handle("/", srv.staticHandler(webRoot))
	return mux
}

func TestEmbeddedBankIsTheRussianTutor(t *testing.T) {
	srv, _ := newTestServer(t)
	mux := contentMux(t, srv)
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/", nil))
	if !strings.Contains(recorder.Body.String(), "Репетитор ЦТ: Русский язык") {
		t.Fatal("index.html is not the Russian tutor")
	}
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if err := bankError(recorder.Body.Bytes()); err != nil {
		t.Fatalf("embedded bank: %v", err)
	}
	if srv.contentVersion() == "" {
		t.Fatal("embedded content version is empty — did tools/sync_assets.py run?")
	}
}

func TestValidOverlayIsServedAndForeignOverlayIgnored(t *testing.T) {
	srv, store := newTestServer(t)
	mux := contentMux(t, srv)
	overlay := []byte(`{"meta":{"subject":"russian","package":"by.ziv.ctrussian"},"tasks":[{"id":"overlay-task"}]}`)
	if err := store.WriteContent("bank", overlay); err != nil {
		t.Fatal(err)
	}
	foreign := `{"subject":"mathematics","package":"by.ziv.ctmaths","contentVersion":"2099.1.0","files":{}}`
	if err := store.WriteContent("version", []byte(foreign)); err != nil {
		t.Fatal(err)
	}
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if strings.Contains(recorder.Body.String(), "overlay-task") || srv.overlayCurrent() {
		t.Fatal("a foreign overlay shadowed the embedded bank")
	}
	own := `{"subject":"russian","package":"by.ziv.ctrussian","contentVersion":"2099.1.0","files":{}}`
	if err := store.WriteContent("version", []byte(own)); err != nil {
		t.Fatal(err)
	}
	recorder = httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet, "/content/bank.json", nil))
	if !strings.Contains(recorder.Body.String(), "overlay-task") || srv.contentVersion() != "2099.1.0" {
		t.Fatalf("valid overlay not served: %s", recorder.Body)
	}
	stale := `{"subject":"russian","package":"by.ziv.ctrussian","contentVersion":"2000.1.1","files":{}}`
	if err := store.WriteContent("version", []byte(stale)); err != nil {
		t.Fatal(err)
	}
	if srv.overlayCurrent() || srv.contentVersion() != embeddedVersion() {
		t.Fatal("a stale overlay hid the newer embedded bank")
	}
}

func TestReportEndpoint(t *testing.T) {
	srv, store := newTestServer(t)
	mux := http.NewServeMux()
	mux.HandleFunc("/api/report", srv.handleReport)
	payload, _ := json.Marshal(map[string]string{"kind": "russian-progress", "html": "<html>ok</html>"})
	recorder := httptest.NewRecorder()
	mux.ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, "/api/report", bytes.NewReader(payload)))
	if recorder.Code != http.StatusOK {
		t.Fatalf("report code = %d: %s", recorder.Code, recorder.Body)
	}
	if entries, err := os.ReadDir(store.Reports()); err != nil || len(entries) != 1 {
		t.Fatalf("reports dir = %v (%v)", entries, err)
	}
}

func TestNumericContentVersions(t *testing.T) {
	cases := []struct {
		left, right string
		want        int
	}{{"2026.10.3", "2026.9.99", 1}, {"2026.10.2", "2026.10.3", -1}, {"2026.10", "2026.10.0", 0}, {"2027.1.0", "2026.12.99", 1}}
	for _, item := range cases {
		if got := compareContentVersions(item.left, item.right); got != item.want {
			t.Fatalf("compare(%q,%q) = %d, want %d", item.left, item.right, got, item.want)
		}
	}
	if version, ok := versionOfTag("russian-v2026.10.1"); !ok || version != "2026.10.1" {
		t.Fatal("canonical tag not parsed")
	}
	for _, tag := range []string{"v2026.10.1", "russian-v2026.10.01", "russian-v2026.13.1", "physics-v2026.10.1"} {
		if _, ok := versionOfTag(tag); ok {
			t.Fatalf("%s accepted", tag)
		}
	}
}

func TestRecoverContentBackup(t *testing.T) {
	base := t.TempDir()
	store, err := NewStore(base)
	if err != nil {
		t.Fatal(err)
	}
	old := []byte(`{"old":true}`)
	if err := store.WriteContent("bank", old); err != nil {
		t.Fatal(err)
	}
	if err := os.Rename(store.ContentDir(), filepath.Join(store.Root(), "content.previous")); err != nil {
		t.Fatal(err)
	}
	recovered, err := NewStore(base)
	if err != nil {
		t.Fatal(err)
	}
	if got, ok := recovered.ReadContent("bank"); !ok || !bytes.Equal(got, old) {
		t.Fatal("pack not recovered")
	}
}
