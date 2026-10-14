package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func newTestStore(t *testing.T) *Store {
	t.Helper()
	dir := t.TempDir()
	st, err := NewStore(dir)
	if err != nil {
		t.Fatalf("NewStore: %v", err)
	}
	return st
}

func TestStoreSaveLoadRoundTrip(t *testing.T) {
	st := newTestStore(t)
	payload := []byte(`{"attempts":[{"id":"a","correct":18,"total":30}]}`)
	if err := st.Save("progress", payload); err != nil {
		t.Fatalf("Save: %v", err)
	}
	got, ok := st.Load("progress")
	if !ok {
		t.Fatal("Load reported a missing file")
	}
	if strings.TrimSpace(string(got)) != string(payload) {
		t.Fatalf("round trip mismatch: %s", got)
	}
}

func TestStoreRejectsBadInput(t *testing.T) {
	st := newTestStore(t)
	if err := st.Save("progress", []byte("not json")); err == nil {
		t.Fatal("expected an error for invalid JSON")
	}
	if err := st.Save("../escape", []byte(`{}`)); err == nil {
		t.Fatal("expected an error for a path-traversal key")
	}
	if _, ok := st.Load("../escape"); ok {
		t.Fatal("path traversal key must not resolve")
	}
}

func TestContentOverlayWins(t *testing.T) {
	st := newTestStore(t)
	embedded := []byte(`{"tasks":[]}`)
	if got := st.ReadContent("bank", embedded); string(got) != string(embedded) {
		t.Fatalf("expected the embedded bank, got %s", got)
	}
	updated := []byte(`{"tasks":[{"id":"new"}]}`)
	if err := st.WriteContent("bank", updated); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	if got := st.ReadContent("bank", embedded); string(got) != string(updated) {
		t.Fatalf("overlay must win over the embedded bank, got %s", got)
	}
}

func TestContentVersionAndCount(t *testing.T) {
	st := newTestStore(t)
	if v := st.ContentVersion(); v != "" {
		t.Fatalf("expected an empty version before an update, got %q", v)
	}
	man := []byte(`{"contentVersion":"2027.01.1"}`)
	if err := st.WriteContent("version", man); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	if v := st.ContentVersion(); v != "2027.01.1" {
		t.Fatalf("unexpected version %q", v)
	}
	bank := []byte(`{"tasks":[{"id":"a"},{"id":"b"}]}`)
	if err := st.WriteContent("bank", bank); err != nil {
		t.Fatalf("WriteContent: %v", err)
	}
	if n := st.countTasks(); n != 2 {
		t.Fatalf("expected 2 tasks, got %d", n)
	}
}

func TestUpdateContentOffline(t *testing.T) {
	st := newTestStore(t)
	res := st.UpdateContent("http://127.0.0.1:1", "2026.10.1")
	if res.Status != "offline" {
		t.Fatalf("expected status offline, got %q (%s)", res.Status, res.Message)
	}
}

func TestUpdateContentInstallsPack(t *testing.T) {
	bank := []byte(`{"tasks":[{"id":"x"},{"id":"y"},{"id":"z"}]}`)
	sum := sha256Hex(bank)
	mux := http.NewServeMux()
	mux.HandleFunc("/version.json", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"contentVersion":"2027.02.1","files":{"bank.json":{"sha256":"` +
			sum + `"}}}`))
	})
	mux.HandleFunc("/bank.json", func(w http.ResponseWriter, r *http.Request) { _, _ = w.Write(bank) })
	srv := httptest.NewServer(mux)
	defer srv.Close()

	st := newTestStore(t)
	res := st.UpdateContent(srv.URL, "2026.10.1")
	if res.Status != "ok" {
		t.Fatalf("expected ok, got %q (%s)", res.Status, res.Message)
	}
	if res.Version != "2027.02.1" || res.NewTasks != 3 {
		t.Fatalf("unexpected result %+v", res)
	}
	if got := string(st.ReadContent("bank", nil)); got != string(bank) {
		t.Fatalf("installed bank mismatch: %s", got)
	}
	// second run must report that everything is up to date
	if again := st.UpdateContent(srv.URL, "2027.02.1"); again.Status != "uptodate" {
		t.Fatalf("expected uptodate, got %q", again.Status)
	}
}

func TestUpdateContentRejectsTamperedPack(t *testing.T) {
	mux := http.NewServeMux()
	mux.HandleFunc("/version.json", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"contentVersion":"9.9.9","files":{"bank.json":{"sha256":"deadbeef"}}}`))
	})
	mux.HandleFunc("/bank.json", func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"tasks":[]}`))
	})
	srv := httptest.NewServer(mux)
	defer srv.Close()

	st := newTestStore(t)
	if res := st.UpdateContent(srv.URL, "1.0.0"); res.Status != "error" {
		t.Fatalf("tampered pack must be rejected, got %q", res.Status)
	}
}

func TestAPIStateAndBlob(t *testing.T) {
	st = newTestStore(t)
	defer func() { store = nil }()

	mux := http.NewServeMux()
	registerRoutes(mux)

	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/state", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("GET /api/state -> %d", rec.Code)
	}
	var st1 appState
	if err := json.Unmarshal(rec.Body.Bytes(), &st1); err != nil {
		t.Fatalf("state is not valid JSON: %v", err)
	}
	if st1.App.Version != AppVersion || st1.App.Developer.Email != "ziv@csl.by" {
		t.Fatalf("unexpected state payload: %+v", st1.App)
	}

	body := strings.NewReader(`{"attempts":1}`)
	rec = httptest.NewRecorder()
	mux.ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/api/blob?k=progress", body))
	if rec.Code != http.StatusOK {
		t.Fatalf("POST /api/blob -> %d", rec.Code)
	}
	if _, ok := st.Load("progress"); !ok {
		t.Fatal("progress blob was not persisted")
	}

	rec = httptest.NewRecorder()
	mux.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/blob?k=progress", nil))
	if rec.Code != http.StatusOK || !strings.Contains(rec.Body.String(), "attempts") {
		t.Fatalf("GET /api/blob -> %d %s", rec.Code, rec.Body.String())
	}
}

func TestIndexIsServed(t *testing.T) {
	st = newTestStore(t)
	defer func() { store = nil }()
	mux := http.NewServeMux()
	registerRoutes(mux)

	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("GET / -> %d", rec.Code)
	}
	if !strings.Contains(rec.Body.String(), "<html") {
		t.Fatalf("interface is not HTML: %.80s", rec.Body.String())
	}
}

func TestReportSaved(t *testing.T) {
	st := newTestStore(t)
	path, err := st.SaveReport("progress report", []byte("<html></html>"))
	if err != nil {
		t.Fatalf("SaveReport: %v", err)
	}
	if filepath.Ext(path) != ".html" {
		t.Fatalf("unexpected report path %q", path)
	}
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("report file missing: %v", err)
	}
}
