package main

// store.go — постоянное хранилище приложения Windows.
//
// Раскладка данных (каталог задаётся --data, иначе %APPDATA%\CTRussianTutor,
// при --portable — рядом с исполняемым файлом). Данные отделены от других
// репетиторов (математика, физика): свой каталог, свой профиль окна.
//
//	data/progress.json   успеваемость ученика (попытки, статистика по темам)
//	data/settings.json   язык, тема оформления, длительность экзамена, цель дня
//	data/session.json    незавершённый тест (можно продолжить)
//	data/content/*.json  проверенный банк ЭТОГО предмета (выпуск russian-v…) поверх встроенного
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
	"sort"
	"strconv"
	"strings"
	"sync"
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
	root      string
	http      *http.Client
	api       string // Releases API of the repository (overridable in tests)
	downloads string // tag-specific download root (overridable in tests)
	contentMu sync.RWMutex
	updateMu  sync.Mutex
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
	// Restore the last pack after a crash between the commit renames.
	content := filepath.Join(root, "content")
	backup := filepath.Join(root, "content.previous")
	if _, err := os.Stat(content); errors.Is(err, os.ErrNotExist) {
		if _, err := os.Stat(backup); err == nil {
			if err := os.Rename(backup, content); err != nil {
				return nil, err
			}
		}
	}
	return &Store{root: root, http: &http.Client{Timeout: 45 * time.Second}, api: releasesAPI, downloads: downloadRoot}, nil
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
	s.contentMu.RLock()
	defer s.contentMu.RUnlock()
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
	s.contentMu.Lock()
	defer s.contentMu.Unlock()
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

// Subject identity of this executable (subject.json). The repository-wide
// GitHub "latest" belongs to the mathematics tutor, so it is never used: the
// release is chosen through the paginated Releases API and every file comes
// from that release's tag-specific URL. A pack of another subject is rejected.
const (
	subjectID       = "russian"
	subjectPackage  = "by.ziv.ctrussian"
	subjectTag      = "russian-v"
	contentSchema   = 2
	contentProtocol = 2
	releasesAPI     = "https://api.github.com/repos/zigorminsk-debug/mathematics/releases"
	downloadRoot    = "https://github.com/zigorminsk-debug/mathematics/releases/download/"
	releasePageSize = 100
	maxReleasePages = 10
)

// contentFiles is the exact content inventory of a subject manifest.
var contentFiles = []string{"analogous.json", "answer_vectors.json", "bank.json", "mistakes.json", "rules.json",
	"topics.json", "ui_strings.json"}

// releaseFiles is the exact asset inventory of a complete subject release.
var releaseFiles = append(append([]string{}, contentFiles...), "version.json", "release-info.json", "SHA256SUMS.txt",
	"app-release.apk", "CTRussianTutor-amd64.exe", "CTRussianTutor-arm64.exe")

var (
	releaseTag = regexp.MustCompile(`^russian-v(20[0-9]{2})\.([1-9]|1[0-2])\.(0|[1-9][0-9]?)$`)
	sha256Hex  = regexp.MustCompile(`^[0-9a-f]{64}$`)
	versionRe  = regexp.MustCompile(`^[0-9]+(\.[0-9]+)*$`)
)

// contentManifest mirrors dist/content/version.json of a subject release.
type contentManifest struct {
	Schema          int    `json:"schema"`
	Subject         string `json:"subject"`
	Package         string `json:"package"`
	ContentProtocol int    `json:"contentProtocol"`
	Tag             string `json:"tag"`
	ContentVersion  string `json:"contentVersion"`
	BaseURL         string `json:"baseUrl"`
	Files           map[string]struct {
		SHA256 string `json:"sha256"`
		Bytes  int64  `json:"bytes"`
	} `json:"files"`
	Counts struct {
		Bank      int `json:"bank"`
		Analogous int `json:"analogous"`
	} `json:"counts"`
}

// githubRelease is the part of a Releases API entry the channel needs. Missing
// draft/prerelease flags fail closed (treated as not stable).
type githubRelease struct {
	TagName    string `json:"tag_name"`
	Draft      *bool  `json:"draft"`
	Prerelease *bool  `json:"prerelease"`
	Assets     []struct {
		Name  string `json:"name"`
		State string `json:"state"`
	} `json:"assets"`
}

type releaseCandidate struct {
	Tag     string
	Version string
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
	Tag        string `json:"tag,omitempty"`
}

// versionOfTag returns the canonical version of a tag of THIS family.
func versionOfTag(tag string) (string, bool) {
	match := releaseTag.FindStringSubmatch(tag)
	if match == nil {
		return "", false
	}
	return match[1] + "." + match[2] + "." + match[3], true
}

// completeInventory: exactly the expected, fully uploaded assets.
func completeInventory(release githubRelease) bool {
	if len(release.Assets) != len(releaseFiles) {
		return false
	}
	names := map[string]bool{}
	for _, asset := range release.Assets {
		if asset.State != "uploaded" {
			return false
		}
		names[asset.Name] = true
	}
	for _, name := range releaseFiles {
		if !names[name] {
			return false
		}
	}
	return len(names) == len(releaseFiles)
}

// selectRelease picks the highest canonical version among published, complete
// releases of this subject family (drafts, prereleases and foreign families —
// the mathematics "v…" latest included — are ignored).
func selectRelease(releases []githubRelease) *releaseCandidate {
	var best *releaseCandidate
	for _, release := range releases {
		if release.Draft == nil || *release.Draft || release.Prerelease == nil || *release.Prerelease {
			continue
		}
		version, ok := versionOfTag(release.TagName)
		if !ok || !completeInventory(release) {
			continue
		}
		if best == nil || compareContentVersions(version, best.Version) > 0 {
			best = &releaseCandidate{Tag: release.TagName, Version: version}
		}
	}
	return best
}

// manifestError checks a manifest before any content file is downloaded.
func manifestError(manifest contentManifest, expected *releaseCandidate) error {
	switch {
	case manifest.Subject != subjectID:
		return errors.New("manifest belongs to another subject")
	case manifest.Package != subjectPackage:
		return errors.New("manifest belongs to another package")
	case manifest.Schema != contentSchema || manifest.ContentProtocol != contentProtocol:
		return errors.New("unsupported manifest schema")
	case !versionRe.MatchString(manifest.ContentVersion):
		return errors.New("manifest has no valid contentVersion")
	}
	if expected != nil && (manifest.ContentVersion != expected.Version || manifest.Tag != expected.Tag) {
		return errors.New("manifest does not match the selected release tag")
	}
	if len(manifest.Files) != len(contentFiles) {
		return errors.New("manifest must list exactly the content files")
	}
	for _, name := range contentFiles {
		meta, ok := manifest.Files[name]
		if !ok || !sha256Hex.MatchString(meta.SHA256) || meta.Bytes <= 0 {
			return fmt.Errorf("manifest entry %s is missing or has no SHA-256/size", name)
		}
	}
	return nil
}

// overlayManifestError: a stored overlay is usable only for this subject/package.
func overlayManifestError(manifest contentManifest) error {
	if manifest.Subject != subjectID || manifest.Package != subjectPackage {
		return errors.New("foreign overlay")
	}
	if !versionRe.MatchString(manifest.ContentVersion) {
		return errors.New("overlay version unknown")
	}
	return nil
}

// bankError rejects a bank of another subject (for example the mathematics bank).
func bankError(data []byte) error {
	var bank struct {
		Meta struct {
			Subject string `json:"subject"`
			Package string `json:"package"`
		} `json:"meta"`
	}
	if err := json.Unmarshal(data, &bank); err != nil {
		return err
	}
	if bank.Meta.Subject != subjectID || bank.Meta.Package != subjectPackage {
		return errors.New("foreign bank rejected")
	}
	return nil
}

// compareContentVersions сравнивает версии банка по числовым компонентам:
// "2026.10.3" новее "2026.9.9", хотя лексикографически было бы наоборот.
func compareContentVersions(left, right string) int {
	parse := func(version string) []int {
		parts := strings.Split(version, ".")
		out := make([]int, len(parts))
		for i, part := range parts {
			out[i], _ = strconv.Atoi(part)
		}
		return out
	}
	a, b := parse(left), parse(right)
	for i := 0; i < len(a) || i < len(b); i++ {
		var x, y int
		if i < len(a) {
			x = a[i]
		}
		if i < len(b) {
			y = b[i]
		}
		if x < y {
			return -1
		}
		if x > y {
			return 1
		}
	}
	return 0
}

// resolveRelease pages through the Releases API (100 per page, bounded).
func (s *Store) resolveRelease() (*releaseCandidate, error) {
	var all []githubRelease
	for page := 1; page <= maxReleasePages; page++ {
		data, err := s.fetchWith(fmt.Sprintf("%s?per_page=%d&page=%d", s.api, releasePageSize, page), true)
		if err != nil {
			return nil, err
		}
		var batch []githubRelease
		if err := json.Unmarshal(data, &batch); err != nil {
			return nil, fmt.Errorf("releases page %d: %w", page, err)
		}
		all = append(all, batch...)
		if len(batch) < releasePageSize {
			break
		}
	}
	return selectRelease(all), nil
}

// CheckUpdates installs a newer, fully verified content pack of THIS subject.
// An explicit override (tests, a local feed) skips only the release selection;
// the manifest/bank subject checks and every checksum still apply.
func (s *Store) CheckUpdates(override, current string) UpdateResult {
	s.updateMu.Lock()
	defer s.updateMu.Unlock()
	var candidate *releaseCandidate
	feed := strings.TrimRight(strings.TrimSpace(override), "/")
	if feed == "" {
		found, err := s.resolveRelease()
		if err != nil {
			return UpdateResult{Status: "offline", Message: err.Error(), Version: current}
		}
		if found == nil {
			return UpdateResult{Status: "uptodate", Version: current, Message: "no published release of this subject yet"}
		}
		if compareContentVersions(found.Version, current) <= 0 {
			return UpdateResult{Status: "uptodate", Version: current, Message: "already up to date", Tag: found.Tag}
		}
		candidate = found
		feed = strings.TrimRight(s.downloads, "/") + "/" + found.Tag
	}
	manifestData, err := s.fetch(feed + "/version.json")
	if err != nil {
		return UpdateResult{Status: "offline", Message: err.Error(), Version: current}
	}
	var manifest contentManifest
	if err := json.Unmarshal(manifestData, &manifest); err != nil {
		return UpdateResult{Status: "error", Message: "manifest: " + err.Error(), Version: current}
	}
	if err := manifestError(manifest, candidate); err != nil {
		return UpdateResult{Status: "error", Message: err.Error(), Version: current}
	}
	if compareContentVersions(manifest.ContentVersion, current) <= 0 {
		// A build can be ahead of the newest release. Never downgrade its bank.
		return UpdateResult{Status: "uptodate", Version: current, Message: "already up to date"}
	}
	stage, err := os.MkdirTemp(s.root, "content-update-")
	if err != nil {
		return UpdateResult{Status: "error", Version: current, Message: err.Error()}
	}
	defer os.RemoveAll(stage)

	var total int64
	names := append([]string{}, contentFiles...)
	sort.Strings(names)
	for _, name := range names {
		meta := manifest.Files[name]
		data, err := s.fetch(feed + "/" + name)
		if err != nil {
			return UpdateResult{Status: "error", Version: current, Message: name + ": " + err.Error()}
		}
		sum := sha256.Sum256(data)
		if !strings.EqualFold(hex.EncodeToString(sum[:]), meta.SHA256) || meta.Bytes != int64(len(data)) {
			return UpdateResult{Status: "error", Version: current, Message: name + ": checksum or size mismatch"}
		}
		if !json.Valid(data) {
			return UpdateResult{Status: "error", Version: current, Message: name + ": invalid JSON"}
		}
		if name == "bank.json" || name == "analogous.json" {
			if err := bankError(data); err != nil {
				return UpdateResult{Status: "error", Version: current, Message: name + ": " + err.Error()}
			}
		}
		if err := os.WriteFile(filepath.Join(stage, name), data, 0o644); err != nil {
			return UpdateResult{Status: "error", Version: current, Message: name + ": " + err.Error()}
		}
		total += int64(len(data))
	}
	// The manifest is stored too: it carries the installed version and subject.
	if err := os.WriteFile(filepath.Join(stage, "version.json"), manifestData, 0o644); err != nil {
		return UpdateResult{Status: "error", Version: current, Message: "version.json: " + err.Error()}
	}
	if err := s.installContentPack(stage); err != nil {
		return UpdateResult{Status: "error", Version: current, Message: err.Error()}
	}
	tag := manifest.Tag
	return UpdateResult{
		Status: "updated", Version: manifest.ContentVersion, Previous: current, Files: len(names),
		NewTasks: manifest.Counts.Bank + manifest.Counts.Analogous, Downloaded: total, Tag: tag,
		Message: "installed " + manifest.ContentVersion,
	}
}

// installContentPack commits only a fully verified pack; errors leave the
// previous bank and all progress/settings/session blobs untouched.
func (s *Store) installContentPack(stage string) error {
	s.contentMu.Lock()
	defer s.contentMu.Unlock()
	backup := filepath.Join(s.root, "content.previous")
	if err := os.RemoveAll(backup); err != nil {
		return err
	}
	_, err := os.Stat(s.ContentDir())
	hadPrevious := err == nil
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if hadPrevious {
		if err := os.Rename(s.ContentDir(), backup); err != nil {
			return err
		}
	}
	if err := os.Rename(stage, s.ContentDir()); err != nil {
		if hadPrevious {
			_ = os.Rename(backup, s.ContentDir())
		}
		return err
	}
	_ = os.RemoveAll(backup)
	return nil
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
func (s *Store) fetch(url string) ([]byte, error) { return s.fetchWith(url, false) }

func (s *Store) fetchWith(url string, api bool) ([]byte, error) {
	if !secureURL(url) {
		return nil, fmt.Errorf("refusing non-https url %q", url)
	}
	request, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	request.Header.Set("User-Agent", "CTRussianTutor/"+appVersion)
	if api {
		request.Header.Set("Accept", "application/vnd.github+json")
	}
	response, err := s.http.Do(request)
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
