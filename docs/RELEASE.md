# Release pipeline — «Репетитор ЦТ: Русский язык»

The repository `zigorminsk-debug/mathematics` hosts two independent tutors. The
mathematics tutor (tags `v…`) owns GitHub's repository-wide *latest*; this
branch publishes the Russian tutor as a **subject release** that must never touch
that channel. All identities come from `subject.json`.

## What a trusted push does

```
push (this branch) ─► prepare: tools/release_plan.py  (family russian-v, per-subject counter)
                  ├─► content: build/verify content, tests, parity, jsdom journeys, syntax
                  ├─► windows: go vet, go test, CTRussianTutor-amd64.exe / -arm64.exe
                  ├─► android: key pin, Kotlin unit tests, debug APK, signed release APK,
                  │            package/versionCode gate, previous SUBJECT APK gate
                  └─► publish (publish.yml → tools/publish_release.py), only if all succeeded
```

- `concurrency: ctrussian-release-pipeline` (queue max, no cancellation) — never the
  mathematics lock; the reusable Release caller uses a child lock (no deadlock).
- PR and fork runs only test (`--local` plan, publication disabled). The tag entry
  point `release.yml` reacts only to `russian-v*` tags; `v*` tags are invisible here.

## Versioning (per subject)

- Canonical `YYYY.M.P` (patch 0–99), Android `versionCode = (YYYY−2000)·10000 + M·100 + P`.
- `VERSION` is the source floor (first release `2026.10.1`, code `261001`). The planner
  allocates `max(floor, current month .0, previous russian release + 1)`, skipping
  tags/drafts reserved by other commits; a rerun of a published commit is idempotent.
- `release_version()` accepts only canonical `russian-v…` tags; mathematics `v…` and
  `physics-v…` releases, drafts and prereleases are ignored for the counter, the
  previous stable release, idempotency and lineage. `git tag --list "russian-v*"`
  reservations protect interrupted publishers.
- The first subject release has no previous stable release, so it is NOT compared with
  the mathematics APK; later releases must keep package + certificate and raise the code
  (`check_apk_update.py --previous`, `check_signature.py --apk previous`).

## Publication (`tools/publish_release.py`)

1. Validates the run: same repository/commit, `push`/`workflow_dispatch`, a branch ref or
   the exact `russian-v…` tag, the three build jobs succeeded.
2. Assembles exactly the same-run artifacts: 7 content JSON files, `version.json`,
   `app-release.apk`, two EXEs; the manifest must name subject `russian`, package
   `by.ziv.ctrussian`, schema 2, protocol 2; banks must name the subject too.
   Manifest URLs are tag-specific (`…/releases/download/russian-vX/…`), plus `tag`.
3. Writes `release-info.json` (subject/package/tag, run, checks, certificate, digests,
   repository latest before) and `SHA256SUMS.txt`; mirrors the JSON in the Release body.
4. Snapshots `/releases/latest` (expected: the mathematics release), reserves the tag,
   creates the draft with **`make_latest: "false"`**, uploads, verifies the inventory
   (names, uploaded state, server digests).
5. Promotes with PATCH `{"draft": false, "prerelease": false, "make_latest": "false"}`,
   then verifies **its own** release by id (not draft/prerelease, tag, inventory, tag →
   commit) — never through `/releases/latest`.
6. Reads `/releases/latest` again: it must be identical to the snapshot and must not be a
   `russian-v…` release. If GitHub made the subject release latest, the publisher restores
   the previous latest (`make_latest: "true"` on that release id) and fails the run.

Inventory (13 files): `analogous.json`, `answer_vectors.json`, `bank.json`,
`mistakes.json`, `rules.json`, `topics.json`, `ui_strings.json`, `version.json`,
`release-info.json`, `SHA256SUMS.txt`, `app-release.apk`, `CTRussianTutor-amd64.exe`,
`CTRussianTutor-arm64.exe`.

## Client update channel (subject-scoped)

Android (`UpdateFeed.kt` + `NativeBridge.kt`) and Windows (`store.go`) never use
`releases/latest`:

1. Page through `https://api.github.com/repos/zigorminsk-debug/mathematics/releases?per_page=100&page=N`
   (≤10 pages).
2. Keep non-draft, non-prerelease releases whose tag is a canonical `russian-v…` and whose
   assets are exactly the 13 expected, fully uploaded files; choose the highest version.
3. Download `version.json` from that tag; require subject/package/schema/protocol, tag and
   version equal to the release, exactly the 7 content files with SHA-256 and size.
4. Download each file from the tag URL, verify SHA-256/size/JSON; `bank.json` and
   `analogous.json` must name the subject; stage and install atomically. Never downgrade a
   newer embedded bank; progress/settings are never touched.
5. A stored overlay is served only if its manifest names this subject/package and it is
   not older than the embedded bank (a foreign or stale pack is ignored).

The web layer additionally rejects a foreign bank (`CT.content.subjectOk`).
Tests: `tests/test_release.py` (planner/publisher/workflows), `UpdateFeedTest.kt`,
`windows/main_test.go`, `tests/native_smoke.js`, `tests/content_schema.js`.

## Signing

`android/keystore/ctrussian-release.p12` (alias `ctrussian`, PKCS#12, RSA 3072, valid
to 2056), fingerprint pinned in `android/keystore/expected-cert-sha256.txt` **before the
first release**. The mathematics key is not present in this branch. Environment
overrides `ANDROID_KEYSTORE_FILE/PASSWORD`, `ANDROID_KEY_ALIAS/PASSWORD` remain supported
for a future move to secrets (only before wide distribution — a different key cannot
update an installed app; Android 9+ allows v3 key rotation only).

## Recovery

- Failed gate → nothing is published; fix, commit, push again.
- Interrupted publisher after the tag/draft was created → rerun CI for the same commit:
  the planner resumes the own draft; a different commit skips the reserved version.
- Published but audit doubts → read the Release body JSON (`gh api repos/…/releases/tags/<tag>`).
- Never delete/move a published tag or replace assets. If the repository latest were ever
  moved to a subject release, restore it with
  `gh api -X PATCH repos/zigorminsk-debug/mathematics/releases/<math-id> -f make_latest=true`.
