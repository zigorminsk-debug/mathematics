package main

// store.go — постоянное хранилище приложения Windows.
//
// Раскладка данных (каталог задаётся --data, иначе %APPDATA%\CTMathsTutor,
// при --portable — рядом с исполняемым файлом):
//
//	data/progress.json   успеваемость ученика (попытки, статистика по темам)
//	data/settings.json   язык, тема оформления, длительность экзамена, цель дня
//	data/session.json    незавершённый тест (можно продолжить)
//	data/content/*.json  банк заданий, скачанный «поверх» встроенного (обновление)
//	reports/*.html        выгруженные отчёты о прогрессе
//
// On-disk layout of the Windows app: JSON blobs, a content overlay that shadows
// the embedded bank, and exported HTML reports.

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// blobName matches the keys used by the shared UI (progress, settings, …) and by
// the content overlay (bank, analogous, …). Anything else is rejected so a
// malformed request can never escape the data directory.
var blobName = regexp.MustCompile(`^[a-z0-9][a-z0-9_-]{0,40}$`)

// maxBlobBytes caps a single JSON blob (progress with years of history is far
// smaller than this limit).
const maxBlobBytes = 32 << 20

// Store owns the data directory of the application.
type Store struct {
	root string
	http *http.Client
}

// NewStore prepares (and creates if needed) the data directory under base.
func NewStore(base string) (*Store, error) {
	if base == "" {
		return nil, errors.New("store: empty data directory")
	}
	root := filepath.Join(base, "data")
	if err := os.MkdirAll(root, 0o755); err != nil {
		return nil, fmt.Errorf("store: create %s: %w", root, err)
	}
	if err := os.MkdirAll(filepath.Join(base, "reports"), 0o755); err != nil {
		return nil, fmt.Errorf("store: create reports: %w", err)
	}
	return &Store{root: root, http: &http.Client{Timeout: 45 * time.Second}}, nil
}

// Root returns the data directory ("data").
func (s *Store) Root() string { return s.root }

// Base returns the parent directory holding "data" and "reports".
func (s *Store) Base() string { return filepath.Dir(s.root) }

// Reports returns the folder with exported HTML reports.
func (s *Store) Reports() string { return filepath.Join(s.Base(), "reports") }

// ContentDir returns the folder with the downloaded content overlay.
func (s *Store) ContentDir() string { return filepath.Join(s.root, "content") }

func (s *Store) blobPath(key string) (string, error) {
	if !blobName.MatchString(key) {
		return "", fmt.Errorf("store: bad key %q", key)
	}
	return filepath.Join(s.root, key+".json"), nil
}

// ReadBlob returns the stored JSON or nil when the blob does not exist yet.
func (s *Store) ReadBlob(key string) ([]byte, error) {
	path, err := s.blobPath(key)
	if err != nil {
		return nil, err
	}
	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return data, nil
}

// WriteBlob stores raw JSON atomically (write to a temp file, then rename), so a
// crash in the middle never leaves a truncated progress file behind.
func (s *Store) WriteBlob(key string, data []byte) error {
	path, err := s.blobPath(key)
	if err != nil {
		return err
	}
	if len(data) > maxBlobBytes {
		return fmt.Errorf("store: blob %s too large (%d bytes)", key, len(data))
	}
	if len(data) > 0 && !json.Valid(data) {
		return fmt.Errorf("store: blob %s is not valid JSON", key)
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

// ReadContent returns an overlay content file (downloaded update) when present.
func (s *Store) ReadContent(name string) ([]byte, bool) {
	if !blobName.MatchString(name) {
		return nil, false
	}
	data, err := os.ReadFile(filepath.Join(s.ContentDir(), name+".json"))
	if err != nil {
		return nil, false
	}
	return data, true
}

// WriteContent stores one content file of a downloaded update.
func (s *Store) WriteContent(name string, data []byte) error {
	if !blobName.MatchString(name) {
		return fmt.Errorf("store: bad content name %q", name)
	}
	if err := os.MkdirAll(s.ContentDir(), 0o755); err != nil {
		return err
	}
	tmp := filepath.Join(s.ContentDir(), name+".json.tmp")
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, filepath.Join(s.ContentDir(), name+".json"))
}

// WriteReport saves an exported HTML report and returns its path.
func (s *Store) WriteReport(kind string, html []byte) (string, error) {
	if kind == "" {
		kind = "progress"
	}
	kind = regexp.MustCompile(`[^a-z0-9_-]`).ReplaceAllString(strings.ToLower(kind), "")
	if kind == "" {
		kind = "progress"
	}
	name := fmt.Sprintf("%s-%s.html", kind, time.Now().Format("20060102-150405"))
	path := filepath.Join(s.Reports(), name)
	if err := os.WriteFile(path, html, 0o644); err != nil {
		return "", err
	}
	return path, nil
}

// ---------------------------------------------------------------- updates ---

// contentManifest mirrors dist/content/version.json published with a release.
type contentManifest struct {
	ContentVersion string `json:"contentVersion"`
	Built          string `json:"built"`
	BaseURL        string `json:"baseUrl"`
	Files          map[string]struct {
		SHA256 string `json:"sha256"`
		Bytes  int64  `json:"bytes"`
	} `json:"files"`
	Counts struct {
		Bank      int `json:"bank"`
		Analogous int `json:"analogous"`
	} `json:"counts"`
}

// UpdateResult is returned to the interface (and shown as a toast).
type UpdateResult struct {
	Status     string `json:"status"` // uptodate | updated | offline | error
	Version    string `json:"version"`
	Files      int    `json:"files"`
	NewTasks   int    `json:"newTasks"`
	Message    string `json:"message,omitempty"`
	Previous   string `json:"previous,omitempty"`
	Downloaded int64  `json:"downloaded,omitempty"`
}

const defaultFeed = "https://github.com/zigorminsk-debug/mathematics/releases/latest/download"

// CheckUpdates downloads the manifest, verifies every file (SHA-256) and installs
// the ones that differ into the content overlay. The installed version keeps
// working when the network is unavailable.
func (s *Store) CheckUpdates(feed, current string) UpdateResult {
	if feed == "" {
		feed = defaultFeed
	}
	feed = strings.TrimRight(feed, "/")

	manifestData, err := s.fetch(feed + "/version.json")
	if err != nil {
		return UpdateResult{Status: "offline", Message: err.Error(), Version: current}
	}
	var manifest contentManifest
	if err := json.Unmarshal(manifestData, &manifest); err != nil {
		return UpdateResult{Status: "error", Message: "manifest: " + err.Error(), Version: current}
	}
	if manifest.ContentVersion == "" || len(manifest.Files) == 0 {
		return UpdateResult{Status: "error", Message: "manifest is empty", Version: current}
	}
	if manifest.ContentVersion == current && !s.overlayOutdated() {
		return UpdateResult{Status: "uptodate", Version: current, Message: "already up to date"}
	}

	var total int64
	installed := 0
	for name, meta := range manifest.Files {
		base := strings.TrimSuffix(name, ".json")
		data, err := s.fetch(feed + "/" + name)
		if err != nil {
			return UpdateResult{Status: "error", Version: current, Message: name + ": " + err.Error()}
		}
		sum := sha256.Sum256(data)
		if meta.SHA256 != "" && !strings.EqualFold(hex.EncodeToString(sum[:]), meta.SHA256) {
			return UpdateResult{Status: "error", Version: current, Message: name + ": checksum mismatch"}
		}
		if err := s.WriteContent(base, data); err != nil {
			return UpdateResult{Status: "error", Version: current, Message: name + ": " + err.Error()}
		}
		total += int64(len(data))
		installed++
	}
	return UpdateResult{
		Status: "updated", Version: manifest.ContentVersion, Previous: current,
		Files: installed, NewTasks: manifest.Counts.Bank + manifest.Counts.Analogous,
		Downloaded: total, Message: "installed " + manifest.ContentVersion,
	}
}

// overlayOutdated reports whether a half-installed overlay exists (used when the
// feed still carries the same version but local files were removed).
func (s *Store) overlayOutdated() bool {
	entries, err := os.ReadDir(s.ContentDir())
	if err != nil {
		return true
	}
	for _, entry := range entries {
		if strings.HasSuffix(entry.Name(), ".json") {
			return false
		}
	}
	return true
}

// secureURL accepts https anywhere and plain http only on this machine (used by
// the tests and by a locally served update feed).
func secureURL(raw string) bool {
	if strings.HasPrefix(raw, "https://") {
		return true
	}
	if !strings.HasPrefix(raw, "http://") {
		return false
	}
	host := strings.TrimPrefix(raw, "http://")
	if cut := strings.IndexAny(host, "/?"); cut >= 0 {
		host = host[:cut]
	}
	if colon := strings.LastIndex(host, ":"); colon >= 0 {
		host = host[:colon]
	}
	return host == "localhost" || host == "127.0.0.1" || host == "[::1]" || host == "::1"
}

// fetch downloads a small file with a hard size limit (a content file is a few
// hundred kilobytes; the limit protects against a hostile feed).
func (s *Store) fetch(url string) ([]byte, error) {
	if !secureURL(url) {
		return nil, fmt.Errorf("refusing non-https url %q", url)
	}
	response, err := s.http.Get(url)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("GET %s: %s", url, response.Status)
	}
	limit := int64(maxBlobBytes)
	data, err := io.ReadAll(io.LimitReader(response.Body, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(data)) > limit {
		return nil, fmt.Errorf("GET %s: response too large", url)
	}
	return data, nil
}
