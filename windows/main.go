// Command ctmaths is the Windows build of the CT maths tutor.
//
// It is a single self-contained executable: the whole HTML/CSS/JS interface and
// the content bank are embedded with go:embed, the local HTTP server binds to a
// free loopback port, and the window is opened either in Edge/Chrome "app mode"
// (a chrome-less window that looks like a native application) or in the default
// browser.  Student progress is stored in %APPDATA%\CTMathsTutor and downloaded
// content packs are installed on top of the embedded bank without losing data.
package main

import (
	"embed"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync/atomic"
	"time"
)

const AppVersion = "1.0.0"

// buildStamp is injected by the build scripts:
//
//	go build -ldflags "-X main.buildStamp=202610141200"
var buildStamp = "dev"

//go:embed all:web
var webFS embed.FS

var store *Store

type appState struct {
	App struct {
		Version   string `json:"version"`
		Build     string `json:"build"`
		OS        string `json:"os"`
		Platform  string `json:"platform"`
		Shell     string `json:"shell"`
		DataDir   string `json:"dataDir"`
		Developer struct {
			Name  string `json:"name"`
			Email string `json:"email"`
			Phone string `json:"phone"`
		} `json:"developer"`
	} `json:"app"`
	Content struct {
		Version string `json:"version"`
		Overlay bool   `json:"overlay"`
	} `json:"content"`
	Blobs map[string]json.RawMessage `json:"blobs"`
}

func main() {
	var (
		addr      = flag.String("addr", "127.0.0.1:0", "address to listen on (port 0 picks a free port)")
		noBrowser = flag.Bool("no-browser", false, "do not open the interface window")
		portable  = flag.Bool("portable", false, "keep progress next to the executable")
		dataDir   = flag.String("data", "", "explicit data directory")
		quitAfter = flag.Duration("idle-exit", 0, "exit after being idle for this long (0 = never)")
		version   = flag.Bool("version", false, "print the version and exit")
	)
	flag.Parse()

	if *version {
		fmt.Printf("CT Maths Tutor %s (%s/%s, Go %s)\n", AppVersion, runtime.GOOS, runtime.GOARCH,
			runtime.Version())
		return
	}

	base := *dataDir
	if base == "" {
		switch {
		case *portable:
			exe, err := os.Executable()
			if err != nil {
				log.Fatalf("cannot locate the executable: %v", err)
			}
			base = filepath.Dir(exe)
		default:
			cfg, err := os.UserConfigDir()
			if err != nil {
				cfg = "."
			}
			base = filepath.Join(cfg, "CTMathsTutor")
		}
	}
	var err error
	store, err = NewStore(base)
	if err != nil {
		log.Fatalf("cannot prepare the data directory: %v", err)
	}

	ln, err := net.Listen("tcp", *addr)
	if err != nil {
		log.Fatalf("cannot listen on %s: %v", *addr, err)
	}
	url := fmt.Sprintf("http://%s/", ln.Addr().String())

	mux := http.NewServeMux()
	registerRoutes(mux)

	srv := &http.Server{Handler: withLogging(mux), ReadHeaderTimeout: 10 * time.Second}
	log.Printf("CT Maths Tutor %s", AppVersion)
	log.Printf("interface: %s", url)
	log.Printf("data:      %s", store.Dir())

	lastRequest.Store(time.Now().Unix())
	if *idleExit > 0 {
		go watchIdle(*idleExit)
	}

	if !*noBrowser {
		openUI(url)
	}
	if err := srv.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatalf("server stopped: %v", err)
	}
}

func registerRoutes(mux *http.ServeMux) {
	webRoot, err := fs.Sub(webFS, "web")
	if err != nil {
		log.Fatalf("embedded assets are broken: %v", err)
	}
	files := http.FileServer(http.FS(webRoot))

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		p := strings.TrimPrefix(r.URL.Path, "/")
		if p == "" {
			serveIndex(w, webRoot)
			return
		}
		// content/bank.json → overlay if the user installed an update pack
		if strings.HasPrefix(p, "content/") {
			serveContent(w, strings.TrimSuffix(strings.TrimPrefix(p, "content/"), ".json"))
			return
		}
		if _, err := fs.Stat(webRoot, p); err != nil {
			serveIndex(w, webRoot)
			return
		}
		files.ServeHTTP(w, r)
	})
	mux.HandleFunc("/api/state", handleState)
	mux.HandleFunc("/api/blob", handleBlob)
	mux.HandleFunc("/api/update", handleUpdate)
	mux.HandleFunc("/api/report", handleReport)
	mux.HandleFunc("/api/open-folder", handleOpenFolder)
	mux.HandleFunc("/api/quit", handleQuit)
}

func serveIndex(w http.ResponseWriter, webRoot fs.FS) {
	b, err := fs.ReadFile(webRoot, "index.html")
	if err != nil {
		http.Error(w, "interface is missing", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}

func serveContent(w http.ResponseWriter, name string) {
	if name == "" || strings.Contains(name, "/") || strings.Contains(name, "..") {
		http.NotFound(w, nil)
		return
	}
	embedded, err := fs.ReadFile(mustSub("web/content"), name+".json")
	var body []byte
	if store != nil {
		body = store.ReadContent(name, embedded)
	} else {
		body = embedded
	}
	if body == nil {
		http.NotFound(w, nil)
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(body)
}

func mustSub(dir string) fs.FS {
	sub, err := fs.Sub(webFS, dir)
	if err != nil {
		log.Fatalf("embedded assets are broken: %v", err)
	}
	return sub
}

func handleState(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var st appState
	st.App.Version = AppVersion
	st.App.Build = buildStamp
	st.App.OS = runtime.GOOS
	st.App.Platform = runtime.GOOS + "/" + runtime.GOARCH
	st.App.Shell = "go"
	st.App.DataDir = store.Dir()
	st.App.Developer.Name = "Zakharevich Igor (Захаревич Игорь)"
	st.App.Developer.Email = "ziv@csl.by"
	st.App.Developer.Phone = "+3753371412"
	st.Blobs = map[string]json.RawMessage{}
	for _, key := range []string{"progress", "settings", "history", "session"} {
		if b, ok := store.Load(key); ok {
			st.Blobs[key] = json.RawMessage(b)
		}
	}
	st.Content.Version = store.ContentVersion()
	if st.Content.Version == "" {
		st.Content.Version = embeddedContentVersion()
	}
	_, statErr := os.Stat(filepath.Join(store.ContentDir(), "version.json"))
	st.Content.Overlay = statErr == nil
	writeJSON(w, st)
}

func embeddedContentVersion() string {
	b, err := fs.ReadFile(mustSub("web/content"), "version.json")
	if err != nil {
		return "unknown"
	}
	var v struct {
		ContentVersion string `json:"contentVersion"`
	}
	if json.Unmarshal(b, &v) != nil {
		return "unknown"
	}
	return v.ContentVersion
}

func handleBlob(w http.ResponseWriter, r *http.Request) {
	key := r.URL.Query().Get("k")
	switch r.Method {
	case http.MethodGet:
		b, ok := store.Load(key)
		if !ok {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_, _ = w.Write(b)
	case http.MethodPost:
		body, err := readBody(r)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if err := store.Save(key, body); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		writeJSON(w, map[string]any{"ok": true, "bytes": len(body)})
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func handleUpdate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		Base    string `json:"baseUrl"`
		Current string `json:"currentVersion"`
	}
	_ = json.NewDecoder(r.Body).Decode(&req)
	if req.Base == "" {
		req.Base = "https://github.com/zigorminsk-debug/mathematics/releases/latest/download"
	}
	if req.Current == "" {
		req.Current = store.ContentVersion()
	}
	res := store.UpdateContent(strings.TrimSuffix(req.Base, "/"), req.Current)
	writeJSON(w, res)
}

func handleReport(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req struct {
		Name string `json:"name"`
		HTML string `json:"html"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request: "+err.Error(), http.StatusBadRequest)
		return
	}
	path, err := store.SaveReport(req.Name, []byte(req.HTML))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	writeJSON(w, map[string]string{"path": path})
}

func handleOpenFolder(w http.ResponseWriter, r *http.Request) {
	target := store.Dir()
	if r.URL.Query().Get("which") == "reports" {
		target = store.ReportsDir()
	}
	openFolder(target)
	writeJSON(w, map[string]string{"path": target})
}

func handleQuit(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, map[string]bool{"ok": true})
	go func() {
		time.Sleep(150 * time.Millisecond)
		os.Exit(0)
	}()
}

// ---- helpers -------------------------------------------------------------- //

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func withLogging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		next.ServeHTTP(w, r)
		lastRequest.Store(time.Now().Unix())
	})
}

// lastRequest holds the Unix time of the most recent HTTP request so the
// process can exit on its own when the interface has been idle for a long time.
var lastRequest atomic.Int64

func readBody(r *http.Request) ([]byte, error) {
	if r.Body == nil {
		return nil, fmt.Errorf("empty request body")
	}
	defer r.Body.Close()
	return io.ReadAll(io.LimitReader(r.Body, 8<<20))
}

func watchIdle(d time.Duration) {
	for {
		time.Sleep(time.Minute)
		if time.Since(time.Unix(lastRequest.Load(), 0)) > d {
			log.Printf("idle for %s, shutting down", d)
			os.Exit(0)
		}
	}
}

func openUI(url string) {
	if runtime.GOOS == "windows" {
		candidates := [][]string{
			{os.Getenv("ProgramFiles(x86)"), "Microsoft", "Edge", "Application", "msedge.exe"},
			{os.Getenv("ProgramFiles"), "Microsoft", "Edge", "Application", "msedge.exe"},
			{os.Getenv("ProgramFiles"), "Google", "Chrome", "Application", "chrome.exe"},
			{os.Getenv("ProgramFiles(x86)"), "Google", "Chrome", "Application", "chrome.exe"},
			{os.Getenv("LOCALAPPDATA"), "Google", "Chrome", "Application", "chrome.exe"},
		}
		for _, c := range candidates {
			if c[0] == "" {
				continue
			}
			exe := filepath.Join(c...)
			if _, err := os.Stat(exe); err == nil {
				// app mode: a chrome-less window that behaves like a native app
				if err := exec.Command(exe, "--app="+url, "--window-size=1360,900").Start(); err == nil {
					return
				}
			}
		}
		_ = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
		return
	}
	if runtime.GOOS == "darwin" {
		_ = exec.Command("open", url).Start()
		return
	}
	_ = exec.Command("xdg-open", url).Start()
}

func openFolder(path string) {
	switch runtime.GOOS {
	case "windows":
		_ = exec.Command("explorer", path).Start()
	case "darwin":
		_ = exec.Command("open", path).Start()
	default:
		_ = exec.Command("xdg-open", path).Start()
	}
}
