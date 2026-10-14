// Command CTMathsTutor — Windows-версия приложения «Репетитор ЦТ: Математика».
//
// Программа запускает локальный HTTP-сервер только на loopback-адресе, отдаёт
// встроенный (через go:embed) интерфейс и банк заданий, хранит прогресс в
// %APPDATA%\CTMathsTutor и открывает окно приложения в Edge или Chrome в режиме
// --app (без адресной строки), а при их отсутствии — в браузере по умолчанию.
//
// The Windows front-end: one self-contained executable that serves the shared
// offline interface on a loopback port, keeps the progress JSON files and opens
// a chromeless app window. Everything needed to pass the CT exam works offline.
package main

import (
	"embed"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"log"
	"mime"
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

//go:embed all:web
var embedded embed.FS

// webRootFS exposes the embedded interface as a filesystem rooted at web/.
func webRootFS() (fs.FS, error) { return fs.Sub(embedded, "web") }

// buildStamp is filled by the release build:
//
//	go build -ldflags "-X main.buildStamp=2026.10.1+42"
var buildStamp = "dev"

const (
	appName    = "Репетитор ЦТ: Математика"
	appVersion = "2026.10.1"
	appRepo    = "https://github.com/zigorminsk-debug/mathematics"
	developer  = "Захаревич Игорь (Zakharevich Igor)"
	devEmail   = "ziv@csl.by"
	devPhone   = "+3753371412"
)

// server holds everything the HTTP handlers need.
type server struct {
	store     *Store
	version   string
	build     string
	started   time.Time
	lastHit   atomic.Int64 // unix nanoseconds of the last request (idle watchdog)
	dataDir   string
	feed      string
	quit      chan struct{}
	closeOnce atomic.Bool
}

func main() {
	log.SetFlags(log.Ltime)

	var (
		addr       = flag.String("addr", "127.0.0.1:0", "адрес локального сервера (loopback)")
		dataDir    = flag.String("data", "", "каталог данных (по умолчанию %APPDATA%\\CTMathsTutor)")
		portable   = flag.Bool("portable", false, "хранить данные рядом с приложением (портативный режим)")
		noBrowser  = flag.Bool("no-browser", false, "не открывать окно приложения")
		idleMin    = flag.Int("idle-exit", 60, "выйти после N минут без запросов (0 — не выходить)")
		printVer   = flag.Bool("version", false, "показать версию и выйти")
		feedURL    = flag.String("feed", defaultFeed, "адрес потока обновлений банка заданий")
		openFolder = flag.String("open", "", "открыть каталог данных (data|reports) и выйти")
	)
	flag.Parse()

	if *printVer {
		fmt.Printf("%s %s (build %s)\n", appName, appVersion, buildStamp)
		return
	}

	base := *dataDir
	if base == "" {
		if *portable {
			base = executableDir()
		} else {
			base = defaultDataDir()
		}
	}
	store, err := NewStore(base)
	if err != nil {
		fatal(err)
	}
	if *openFolder != "" {
		path := store.Root()
		if strings.EqualFold(*openFolder, "reports") {
			path = store.Reports()
		}
		if err := openPath(path); err != nil {
			fatal(err)
		}
		return
	}

	webRoot, err := webRootFS()
	if err != nil {
		fatal(err)
	}

	srv := &server{
		store:   store,
		version: appVersion,
		build:   buildStamp,
		started: time.Now(),
		dataDir: store.Base(),
		feed:    *feedURL,
		quit:    make(chan struct{}),
	}
	srv.touch()

	mux := http.NewServeMux()
	mux.HandleFunc("/api/state", srv.handleState)
	mux.HandleFunc("/api/blob", srv.handleBlob)
	mux.HandleFunc("/api/update", srv.handleUpdate)
	mux.HandleFunc("/api/report", srv.handleReport)
	mux.HandleFunc("/api/open-folder", srv.handleOpenFolder)
	mux.HandleFunc("/api/quit", srv.handleQuit)
	mux.Handle("/content/", srv.contentHandler(webRoot))
	mux.Handle("/", srv.staticHandler(webRoot))

	listener, err := net.Listen("tcp", *addr)
	if err != nil {
		fatal(err)
	}
	url := fmt.Sprintf("http://%s/index.html", listener.Addr().String())

	httpServer := &http.Server{
		Handler:           logRequests(srv, mux),
		ReadHeaderTimeout: 10 * time.Second,
		IdleTimeout:       120 * time.Second,
	}

	fmt.Printf("%s %s\n", appName, appVersion)
	fmt.Printf("  данные:  %s\n", store.Base())
	fmt.Printf("  интерфейс: %s\n", url)
	if *idleMin > 0 {
		fmt.Printf("  выход после %d мин бездействия (окно можно закрыть)\n", *idleMin)
	}
	if !*noBrowser {
		if err := openUI(url); err != nil {
			fmt.Printf("  не удалось открыть окно (%v) — откройте адрес вручную\n", err)
		}
	}

	go func() {
		if err := httpServer.Serve(listener); err != nil && err != http.ErrServerClosed {
			log.Printf("сервер остановлен: %v", err)
		}
	}()

	watchdog(httpServer, srv, *idleMin)
	fmt.Println("До свидания!")
}

/* ------------------------------------------------------------- handlers --- */

func (s *server) touch() { s.lastHit.Store(time.Now().UnixNano()) }

func (s *server) handleState(w http.ResponseWriter, r *http.Request) {
	s.touch()
	overlay := map[string]bool{}
	if entries, err := os.ReadDir(s.store.ContentDir()); err == nil {
		for _, entry := range entries {
			name := strings.TrimSuffix(entry.Name(), ".json")
			if name != entry.Name() {
				overlay[name] = true
			}
		}
	}
	payload := map[string]any{
		"app": map[string]any{
			"name": appName, "version": s.version, "build": s.build,
			"os": runtime.GOOS, "platform": "windows", "arch": runtime.GOARCH,
			"shell": "windows-go", "dataDir": s.dataDir,
			"repo": appRepo, "developer": developer, "email": devEmail, "phone": devPhone,
			"startedAt": s.started.Format(time.RFC3339),
		},
		"content": map[string]any{"version": s.contentVersion(), "overlay": overlay},
		"blobs":   []string{"progress", "settings", "session", "history"},
	}
	writeJSON(w, http.StatusOK, payload)
}

// contentVersion reads the manifest from the overlay (downloaded update) or,
// when there is none, from the embedded bank.
func (s *server) contentVersion() string {
	if data, ok := s.store.ReadContent("version"); ok {
		var manifest contentManifest
		if json.Unmarshal(data, &manifest) == nil && manifest.ContentVersion != "" {
			return manifest.ContentVersion
		}
	}
	return embeddedVersion()
}

func embeddedVersion() string {
	f, err := embedded.Open("web/content/version.json")
	if err != nil {
		return ""
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, 1<<20))
	if err != nil {
		return ""
	}
	var manifest contentManifest
	if json.Unmarshal(data, &manifest) != nil {
		return ""
	}
	return manifest.ContentVersion
}

func (s *server) handleBlob(w http.ResponseWriter, r *http.Request) {
	s.touch()
	key := r.URL.Query().Get("key")
	switch r.Method {
	case http.MethodGet:
		data, err := s.store.ReadBlob(key)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		if data == nil {
			writeJSON(w, http.StatusOK, nil)
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_, _ = w.Write(data)
	case http.MethodPost, http.MethodPut:
		body, err := readBody(r, maxBlobBytes)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		if err := s.store.WriteBlob(key, body); err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "bytes": len(body)})
	default:
		writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "use GET or POST"})
	}
}

func (s *server) handleUpdate(w http.ResponseWriter, r *http.Request) {
	s.touch()
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "use POST"})
		return
	}
	var request struct {
		BaseURL string `json:"baseUrl"`
		Current string `json:"current"`
	}
	body, err := readBody(r, 1<<16)
	if err == nil && len(body) > 0 {
		_ = json.Unmarshal(body, &request)
	}
	if request.BaseURL == "" {
		request.BaseURL = s.feed
	}
	if request.Current == "" {
		request.Current = s.contentVersion()
	}
	result := s.store.CheckUpdates(request.BaseURL, request.Current)
	writeJSON(w, http.StatusOK, result)
}

func (s *server) handleReport(w http.ResponseWriter, r *http.Request) {
	s.touch()
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "use POST"})
		return
	}
	var request struct {
		Kind string `json:"kind"`
		HTML string `json:"html"`
	}
	body, err := readBody(r, maxBlobBytes)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	if err := json.Unmarshal(body, &request); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	path, err := s.store.WriteReport(request.Kind, []byte(request.HTML))
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	_ = openPath(path)
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "path": path, "folder": s.store.Reports()})
}

func (s *server) handleOpenFolder(w http.ResponseWriter, r *http.Request) {
	s.touch()
	which := r.URL.Query().Get("which")
	path := s.store.Root()
	if strings.EqualFold(which, "reports") {
		path = s.store.Reports()
	}
	if err := openPath(path); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"ok": true, "path": path})
}

func (s *server) handleQuit(w http.ResponseWriter, r *http.Request) {
	s.touch()
	writeJSON(w, http.StatusOK, map[string]any{"ok": true})
	if s.closeOnce.CompareAndSwap(false, true) {
		close(s.quit)
	}
}

/* ------------------------------------------------------- static content --- */

// staticHandler serves the shared interface; files are read from the embedded
// copy (single executable, offline by design).
func (s *server) staticHandler(webRoot fs.FS) http.Handler {
	files := http.FileServer(http.FS(webRoot))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.touch()
		if r.URL.Path == "/" || r.URL.Path == "" {
			http.ServeFileFS(w, r, webRoot, "index.html")
			return
		}
		if r.URL.Path == "/apple-touch-icon.png" {
			http.ServeFileFS(w, r, webRoot, "icon.png")
			return
		}
		if _, err := fs.Stat(webRoot, strings.TrimPrefix(r.URL.Path, "/")); err != nil {
			// неизвестный путь — отдаём приложение (внутренняя навигация по хешу)
			http.ServeFileFS(w, r, webRoot, "index.html")
			return
		}
		files.ServeHTTP(w, r)
	})
}

// contentHandler serves the task bank: a downloaded update (overlay) wins over
// the embedded copy, so progress files are never touched by an update.
func (s *server) contentHandler(webRoot fs.FS) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.touch()
		name := strings.TrimSuffix(strings.TrimPrefix(r.URL.Path, "/content/"), ".json")
		if name == "" {
			http.NotFound(w, r)
			return
		}
		w.Header().Set("Cache-Control", "no-cache")
		if data, ok := s.store.ReadContent(name); ok {
			w.Header().Set("Content-Type", "application/json; charset=utf-8")
			_, _ = w.Write(data)
			return
		}
		http.ServeFileFS(w, r, webRoot, filepath.ToSlash(filepath.Join("content", name+".json")))
	})
}

/* ----------------------------------------------------------------- misc --- */

func readBody(r *http.Request, limit int64) ([]byte, error) {
	defer r.Body.Close()
	data, err := io.ReadAll(io.LimitReader(r.Body, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("request body too large")
	}
	return data, nil
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	encoder := json.NewEncoder(w)
	encoder.SetEscapeHTML(false)
	_ = encoder.Encode(payload)
}

// logRequests remembers the last request (idle watchdog) and logs API calls.
func logRequests(s *server, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.touch()
		if strings.HasPrefix(r.URL.Path, "/api/") && r.Method != http.MethodGet {
			log.Printf("%s %s", r.Method, r.URL.Path)
		}
		next.ServeHTTP(w, r)
	})
}

// watchdog exits the process after a long silence, so a forgotten window does
// not keep the executable running forever. The UI also has an explicit exit.
func watchdog(httpServer *http.Server, s *server, idleMinutes int) {
	if idleMinutes <= 0 {
		select {
		case <-s.quit:
		}
		shutdown(httpServer)
		return
	}
	ticker := time.NewTicker(20 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-s.quit:
			shutdown(httpServer)
			return
		case <-ticker.C:
			last := time.Unix(0, s.lastHit.Load())
			if time.Since(last) > time.Duration(idleMinutes)*time.Minute {
				log.Printf("нет запросов %d мин — закрываюсь", idleMinutes)
				shutdown(httpServer)
				return
			}
		}
	}
}

func shutdown(httpServer *http.Server) {
	_ = httpServer.Close()
}

func defaultDataDir() string {
	if dir, err := os.UserConfigDir(); err == nil && dir != "" {
		return filepath.Join(dir, "CTMathsTutor")
	}
	return executableDir()
}

func executableDir() string {
	path, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(path)
}

// openUI opens a chromeless app window: Edge/Chrome in --app mode when present,
// otherwise the default handler. This is what makes the Go build feel like a
// native application while still being plain HTML.
func openUI(url string) error {
	if runtime.GOOS == "windows" {
		for _, candidate := range browserCandidates() {
			if _, err := os.Stat(candidate); err == nil {
				cmd := exec.Command(candidate, "--app="+url, "--window-size=1280,900",
					"--user-data-dir="+filepath.Join(os.TempDir(), "ctmaths-window"))
				if err := cmd.Start(); err == nil {
					return nil
				}
			}
		}
		return exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	}
	if runtime.GOOS == "darwin" {
		return exec.Command("open", url).Start()
	}
	return exec.Command("xdg-open", url).Start()
}

// browserCandidates lists the Chromium executables that can show the interface
// as a chromeless app window (Edge ships with Windows 10/11).
func browserCandidates() []string {
	roots := []string{
		os.Getenv("ProgramFiles(x86)"), os.Getenv("ProgramFiles"), os.Getenv("LOCALAPPDATA"),
	}
	var out []string
	for _, root := range roots {
		if root == "" {
			continue
		}
		out = append(out,
			filepath.Join(root, "Microsoft", "Edge", "Application", "msedge.exe"),
			filepath.Join(root, "Google", "Chrome", "Application", "chrome.exe"),
		)
	}
	return out
}

// openPath reveals a file or folder in the system file manager.
func openPath(path string) error {
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	if runtime.GOOS == "windows" {
		if info.IsDir() {
			return exec.Command("explorer", path).Start()
		}
		return exec.Command("explorer", "/select,"+path).Start()
	}
	if runtime.GOOS == "darwin" {
		if info.IsDir() {
			return exec.Command("open", path).Start()
		}
		return exec.Command("open", "-R", path).Start()
	}
	target := path
	if !info.IsDir() {
		target = filepath.Dir(path)
	}
	return exec.Command("xdg-open", target).Start()
}

func fatal(err error) {
	_, _ = fmt.Fprintln(os.Stderr, "ошибка:", err)
	os.Exit(1)
}

func init() {
	// .json отдаётся с правильным типом даже на старых Windows.
	_ = mime.AddExtensionType(".json", "application/json; charset=utf-8")
	_ = mime.AddExtensionType(".js", "text/javascript; charset=utf-8")
}
