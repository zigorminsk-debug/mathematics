# Agent handoff — «Репетитор ЦТ: Русский язык» (CT Russian Tutor)

Read this file, `docs/WORKLOG.md`, `docs/RELEASE.md` and `docs/CONTENT.md` before
changing the project. The worklog is a dated human record; the actual source is
Git, the actual publication state is GitHub Actions/Releases.

**This branch is the Russian-language tutor**, a standalone app built from the
verified mathematics tutor (history from `v2026.10.8`, commit `b261274`). It
shares the repository `zigorminsk-debug/mathematics` with the mathematics tutor
(branch `arena/d7e34c80-mathematics`, tags `v…`, which owns the repository-wide
GitHub *latest*). Subject identity is explicit in `subject.json` — never guessed
from a branch name.

## Standing user requirements (2026-10-14)

> «публикуй автоматически все сборки сразу после внесения изменений, и
> документируй все действия чтобы любой агент продолжил работу»

> «реализуй» — the specification `docs/subjects/RUSSIAN.md` + `docs/subjects/README.md`.

- After a trusted push of this branch, CI automatically publishes the signed
  release APK, **both** Windows EXEs and the content feed **after all checks pass**
  — as a SUBJECT release `russian-vYYYY.M.P` with `make_latest=false`.
- Record changes, commands, validation results, failures, commit/run/release
  identities and remaining uncertainties in `docs/WORKLOG.md`.
- Never publish anything through the mathematics latest pipeline; never change the
  mathematics package `by.ziv.ctmaths`, its key/certificate, statistics, its branch,
  `main`, or the repository latest. No sibling branches, no new repositories, no PR
  merge/close without an explicit request. Never recommend uninstalling an app.
- Do not present authored tasks as official RIKZ materials; do not claim a release
  before the actual CI run succeeded; never ask for credentials; mark phone/Windows
  installation as **not tested** unless it was really tested.

## Identities (subject.json — single source; tests assert YAML and code agree)

| Property | Russian tutor (this branch) | Mathematics (do not touch) |
|---|---|---|
| subject | `russian` | `mathematics` |
| Android package | `by.ziv.ctrussian` (debug `by.ziv.ctrussian.debug`) | `by.ziv.ctmaths` |
| Certificate SHA-256 | `DE:65:1A:CC:…:83:B6:6A:3D` (`android/keystore/expected-cert-sha256.txt`) | `B2:BD:B4:…:C5:14:65` |
| Windows | `CTRussianTutor-amd64.exe` / `CTRussianTutor-arm64.exe`, data `%APPDATA%\CTRussianTutor`, profile `ctrussian-window` | `CTMathsTutor…` |
| Tag family | `russian-vYYYY.M.P`, `make_latest=false` | `vYYYY.M.P`, latest |
| CI lock | `ctrussian-release-pipeline` | `ctmaths-release-pipeline` |
| Update channel | Releases API, family `russian-v`, tag-specific URLs | `releases/latest/download` |

## Repository and source of truth

- Shared UI: **edit `webapp/`**; authored content: **edit `content_src/`**. Then
  `python3 tools/build_content.py && python3 tools/sync_assets.py` (CI fails on
  stale copies). Generated: `dist/`, `android/.../assets/webapp/`, `windows/web/`,
  `android/.../res/values*/strings.xml`, `android/app/src/test/resources/answer_vectors.json`.
- Content model: 13 areas × 54 rule cards, 6 authored variants × 40 tasks by the
  RIKZ 2026 specification (40 tasks: A 18 + B 22, 120 min), 193 analogous exercises
  (≥3 per rule). Details: `docs/CONTENT.md`.
- Answer checking is the subject checker (`content_src/checker.py` = `webapp/core.js`
  `CT.answer` = `AnswerChecker.kt`), never the maths normaliser.
- `VERSION` is the minimum source version of THIS subject (first: `2026.10.1`);
  CI allocates the effective version per family and applies it in runner checkouts.

## Local gates (all must pass before a push)

```
python3 tools/build_content.py && python3 tools/sync_assets.py --check
python3 -m pip install -r requirements-dev.txt     # PyYAML, tree-sitter, pymorphy3 (+dicts)
python3 -m unittest discover -s tests -p 'test_*.py'
node --check webapp/core.js && node --check webapp/app.js
node tests/answer_parity.js && node tests/content_schema.js
npm install --no-save jsdom && node tests/ui_smoke.js && node tests/native_smoke.js && node tests/rules_smoke.js
python3 tools/check_syntax.py --require
python3 tools/check_signature.py --require --keystore android/keystore/ctrussian-release.p12
```

Optional local native/browser tools found to work in the build sandbox (egress only
to GitHub/npm/PyPI): Go from PyPI `go-bin` (`go vet`, `go test`, both EXEs);
`kotlin-compiler` from npm + JRE from PyPI `jdk4py` (pure Kotlin classes/tests with
local org.json/JUnit stand-ins — Android classes only compile in CI); Chromium from
npm `@sparticuz/chromium` + `puppeteer-core` for `tests/mobile_check.mjs`
(393 px touch, RU/EN, dark, text 1.3, real Go backend via `BASE_URL`). Commands are
in `docs/WORKLOG.md`.

## Release/recovery rules

See `docs/RELEASE.md`. Never move/replace a published tag or asset; a rerun of a
published source is idempotent; failed/skipped gates block publication; PR/fork
runs never publish; the publisher verifies its own release by id and that the
repository latest is identical before/after (and restores it if GitHub moved it).
If CI fails, fix and push again — every failing run publishes nothing.

## Known limits (be honest)

- Physical phone and real Windows installation: **not tested** by agents.
- `gh workflow run` returns HTTP 403 in agent sessions (no manual dispatch);
  `gh pr edit` was unreliable (use REST). Release asset downloads redirect to a host
  outside the sandbox egress; read `release-info.json` via the Release body/API.
- Actions secrets are not writable here (403), so the subject key is committed like
  the mathematics key — see `android/keystore/README.md` for the trade-off.
