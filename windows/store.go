package main

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
	"sync"
	"time"
)

// Store keeps every mutable artefact of the desktop app on disk:
// student progress, settings, a resumable session, generated reports and the
// downloaded content overlay (new task banks installed on top of the embedded
// ones, exactly like the Android updater).
type Store struct {
	dir string
	mu  sync.Mutex
}

var keyRe = regexp.MustCompile(`^[a-z0-9_\-]{1,32}$`)

// sha256Hex is used to verify every downloaded content pack.
func sha256Hex(b []byte) string {
	sum := sha256.Sum256(b)
	return hex.EncodeToString(sum[:])
}

func NewStore(base string) (*Store, error) {
	dir := filepath.Join(base, "data")
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(filepath.Join(dir, "content"), 0o755); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(filepath.Join(dir, "reports"), 0o755); err != nil {
		return nil, err
	}
	return &Store{dir: dir}, nil
}

func (s *Store) Dir() string       { return s.dir }
func (s *Store) ContentDir() string { return filepath.Join(s.dir, "content") }
func (s *Store) ReportsDir() string { return filepath.Join(s.dir, "reports") }

// ---- blobs (progress, settings, history, session) ------------------------- //

func (s *Store) path(key string) (string, error) {
	if !keyRe.MatchString(key) {
		return "", fmt.Errorf("invalid storage key %q", key)
	}
	return filepath.Join(s.dir, key+".json"), nil
}

func (s *Store) Load(key string) ([]byte, bool) {
	p, err := s.path(key)
	if err != nil {
		return nil, false
	}
	b, err := os.ReadFile(p)
	if err != nil {
		return nil, false
	}
	return b, true
}

func (s *Store) Save(key string, data []byte) error {
	p, err := s.path(key)
	if err != nil {
		return err
	}
	if !json.Valid(data) {
		return errors.New("payload is not valid JSON")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, data, 0o644); err != nil {
		return err
	}
	return os.Rename(tmp, p)
}

// ---- content overlay ------------------------------------------------------ //

// ReadContent returns the newest version of a bank: the downloaded overlay wins
// over the bank embedded into the executable.
func (s *Store) ReadContent(name string, embedded []byte) []byte {
	if !keyRe.MatchString(name) {
		return embedded
	}
	b, err := os.ReadFile(filepath.Join(s.ContentDir(), name+".json"))
	if err == nil && json.Valid(b) {
		return b
	}
	return embedded
}

func (s *Store) WriteContent(name string, data []byte) error {
	if !keyRe.MatchString(name) {
		return fmt.Errorf("invalid content name %q", name)
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	return os.WriteFile(filepath.Join(s.ContentDir(), name+".json"), data, 0o644)
}

func (s *Store) ContentVersion() string {
	b, err := os.ReadFile(filepath.Join(s.ContentDir(), "version.json"))
	if err != nil {
		return ""
	}
	var v struct {
		ContentVersion string `json:"contentVersion"`
	}
	if json.Unmarshal(b, &v) != nil {
		return ""
	}
	return v.ContentVersion
}

// ---- in-place content update ---------------------------------------------- //

type UpdateResult struct {
	Status   string `json:"status"` // ok | uptodate | offline | error
	Version  string `json:"version"`
	NewTasks int    `json:"newTasks"`
	Message  string `json:"message"`
}

var errOffline = errors.New("network unavailable")

// UpdateContent downloads a newer content pack from the release feed and installs
// it over the existing bank without touching progress.
func (s *Store) UpdateContent(base, currentVersion string) UpdateResult {
	if base == "" {
		return UpdateResult{Status: "error", Message: "no update source configured"}
	}
	client := &http.Client{Timeout: 30 * time.Second}

	manifest, err := fetch(client, base+"/version.json")
	if err != nil {
		return UpdateResult{Status: "offline", Version: currentVersion,
			Message: "could not reach the update server: " + err.Error()}
	}
	var man struct {
		ContentVersion string `json:"contentVersion"`
		Files          map[string]struct {
			SHA256 string `json:"sha256"`
		} `json:"files"`
	}
	if err := json.Unmarshal(manifest, &man); err != nil {
		return UpdateResult{Status: "error", Version: currentVersion,
			Message: "malformed manifest: " + err.Error()}
	}
	if man.ContentVersion == "" {
		return UpdateResult{Status: "error", Version: currentVersion, Message: "manifest has no version"}
	}
	if currentVersion != "" && man.ContentVersion == currentVersion {
		return UpdateResult{Status: "uptodate", Version: currentVersion, Message: "content is up to date"}
	}

	installed := 0
	for name, meta := range man.Files {
		stem := name
		if ext := filepath.Ext(stem); ext == ".json" {
			stem = stem[:len(stem)-len(ext)]
		}
		body, err := fetch(client, base+"/"+name)
		if err != nil {
			return UpdateResult{Status: "offline", Version: currentVersion,
				Message: fmt.Sprintf("failed to download %s: %v", name, err)}
		}
		if meta.SHA256 != "" {
			sum := sha256.Sum256(body)
			if hex.EncodeToString(sum[:]) != meta.SHA256 {
				return UpdateResult{Status: "error", Version: currentVersion,
					Message: "checksum mismatch for " + name}
			}
		}
		if err := s.WriteContent(stem, body); err != nil {
			return UpdateResult{Status: "error", Version: currentVersion, Message: err.Error()}
		}
		installed++
	}

	result := UpdateResult{Status: "ok", Version: man.ContentVersion, NewTasks: s.countTasks()}
	if installed == 0 {
		result.Status = "uptodate"
	}
	result.Message = fmt.Sprintf("installed %d content files, content version %s", installed, man.ContentVersion)
	return result
}

func (s *Store) countTasks() int {
	b, err := os.ReadFile(filepath.Join(s.ContentDir(), "bank.json"))
	if err != nil {
		return 0
	}
	var bank struct {
		Tasks []json.RawMessage `json:"tasks"`
	}
	if json.Unmarshal(b, &bank) != nil {
		return 0
	}
	return len(bank.Tasks)
}

func fetch(client *http.Client, url string) ([]byte, error) {
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "CTMathsTutor/"+AppVersion)
	resp, err := client.Do(req)
	if err != nil {
		return nil, errOffline
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("http %d", resp.StatusCode)
	}
	return io.ReadAll(io.LimitReader(resp.Body, 32<<20))
}

// ---- report --------------------------------------------------------------- //

func (s *Store) SaveReport(name string, html []byte) (string, error) {
	if name == "" {
		name = "progress"
	}
	clean := regexp.MustCompile(`[^a-zA-Z0-9_\-]+`).ReplaceAllString(name, "_")
	if len(clean) > 60 {
		clean = clean[:60]
	}
	path := filepath.Join(s.ReportsDir(), fmt.Sprintf("%s_%s.html", clean, time.Now().Format("20060102-150405")))
	return path, os.WriteFile(path, html, 0o644)
}
