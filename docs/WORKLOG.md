# Worklog — «Репетитор ЦТ: Русский язык»

Dated record of what was done, how it was verified and what remains. History of the shared
codebase before this branch (the mathematics tutor up to `v2026.10.8`) is in
`git show v2026.10.8:docs/WORKLOG.md`.

## 2026-10-14 — session `arena/339e10e8-mathematics`: the Russian tutor

**Task:** «реализуй» the specification `docs/subjects/RUSSIAN.md` + `docs/subjects/README.md`
(at tag `v2026.10.8`): a standalone Russian-language tutor (Android + Windows) with release
isolation from the mathematics tutor in the same repository.

### Base and "before" snapshot

- Session branch fast-forwarded from old `main` (`22547d6`) to `b261274` = `v2026.10.8`
  (mathematics PR #4 head, branch `arena/d7e34c80-mathematics`); repository unshallowed.
- Mathematics latest before any Russian push: **`v2026.10.8`, release id `412525779`**,
  published 2026-10-14T09:09:31Z, source `b2612742a3746f77b6b560c60cc606a097cb7bd3`,
  13 assets. No `russian-*` tags/releases existed.
- `gh api …/actions/secrets/public-key` → HTTP 403 (secrets not writable from the session).

### Research (sources recorded in `content_src/sources.py`)

- RIKZ specification 2026 (<https://rikc.by/ru/specification/2026/01.pdf>, read 2026-10-14):
  40 tasks, A 18 (several of five) + B 22, 120 min, 9 sections 13/9/2/3/1/2/4/3/3, levels
  I-4/II-10/III-16/IV-6/V-4. The maths 18A+12B/180 min was NOT inherited.
- Adukar «Вопросы ЦЭ/ЦТ по русскому языку 2025» — slot themes A1–A18/B1–B22 (orientation only).
- «восемью и восьмью» (Словарь трудностей произношения и ударения, via lopatin.academic.ru).

### Implementation

- **Identity/isolation first:** `subject.json` + `tools/subject.py`; planner/publisher scoped
  to `russian-v` (`make_latest:"false"` on create and promote, own release verified by id,
  repository latest compared before/after with automatic restore); workflows with lock
  `ctrussian-release-pipeline`, tag trigger `russian-v*`; `check_apk_update` package from
  config; Android package `by.ziv.ctrussian` (Kotlin sources moved, theme/icon/strings);
  new key `ctrussian-release.p12` (SHA-256 `DE:65:1A:CC:E1:DB:76:9B:DC:A8:DB:EB:04:5C:94:9F:39:7F:85:7A:E6:DB:12:EE:D1:32:38:A0:83:B6:6A:3D`,
  pinned before the first release; the maths key removed from this branch only); Windows
  `CTRussianTutor-*.exe`, data dir `CTRussianTutor`, profile `ctrussian-window`;
  subject-scoped update resolvers (Releases API pagination, family, canonical version,
  inventory, tag URLs, manifest/bank subject checks) in Kotlin (`UpdateFeed.kt`) and Go.
- **Content:** 13 areas, 54 rule cards, 6 × 40 authored variants (240), 193 analogs (≥3 per
  rule), 49 figures (14 SVG, 26 tables, 9 trees), typical errors, sources, RU/EN strings;
  maths banks/templates/theory/formulas/calculator/plotter removed; stale
  `android/app/src/main/assets/content` (old maths copy) removed.
- **Checker:** `content_src/checker.py` ↔ `webapp/core.js` ↔ `AnswerChecker.kt`, 123 vectors.
- **UI:** answer controls for every type, rule cards, «Правила», memos, rule-specific
  remediation, statistics by rule, 120-min exam, Android text zoom follows system font scale.

### Validation (all local, 2026-10-14)

| Gate | Result |
|---|---|
| `python3 tools/build_content.py` | 240 variant tasks + 193 analogs verified; 123 vectors; NFC/invisible-char scan |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | **83 tests OK** (release isolation 31, Android build 11, checker 11, content 19, lexicon 6, diagrams 5) |
| `node tests/answer_parity.js` | 123 vectors + 433 canonical answers graded identically |
| `node tests/content_schema.js` | OK (blueprint, quotas, 54 cards, digests, Windows copy identical) |
| `node tests/ui_smoke.js` | 13 journeys (all 40 tasks via UI, wrong answer → card → analog, exam 5/40, report, search, EN, Back) |
| `node tests/native_smoke.js` | 26 checks incl. rejection of a maths bank |
| `node tests/rules_smoke.js` | 108 study + 108 «Правила» openings (RU+EN), 22 SVG viewers zoom/Back/focus |
| `tests/mobile_check.mjs` (Chromium 153, 393×851 touch) | RU/EN × light/dark × text 1.0/1.3: no overflow, tap targets ≥ 44 px, 54 cards, viewer; also against the **real Go backend** |
| Go (PyPI `go-bin` 1.27.2): `go vet`, `go test` | clean; **19 tests pass**; both EXEs cross-compiled (9.7 / 9.0 MB) |
| Real Go backend → `POST /api/update` (live api.github.com) | `uptodate: no published release of this subject yet` — maths `v…` releases ignored |
| Kotlin (npm `kotlin-compiler` 2.4 + PyPI `jdk4py` JRE, local org.json/JUnit stand-ins) | pure classes + **14 tests pass** (incl. 123 vectors); Android classes compile only in CI |
| `tools/check_syntax.py --require`, `check_signature.py --keystore …ctrussian…` | OK |

Errors found by the gates and fixed before any push: the dictionary gate (pymorphy3)
caught wrong authored items — «отрасль» (а, exception), gap placed in the prefix of
«загорелый», «тротуар» (one т), mis-masked «ясный»/«разливается», ambiguous
«в здании/в здание», «косный/костный», «дрожи/дрожжи», «плач/плачь», «таешь/таишь»,
«взволнованно/взволновано». The mobile browser caught a stale CSS copy, 42 px buttons,
a non-wrapping hero/run navigation and an unbreakable data-folder path at text scale 1.3.

### Local tool recipes (sandbox egress: GitHub/npm/PyPI only)

```
python3 -m venv /tmp/govenv && /tmp/govenv/bin/pip install go-bin      # Go toolchain
(cd windows && GOTOOLCHAIN=local /tmp/govenv/bin/go vet ./... && /tmp/govenv/bin/go test ./...)
npm install --prefix /tmp/kotlin kotlin-compiler; pip install jdk4py  # kotlinc + JRE (no javac)
npm install --prefix /tmp/browser @sparticuz/chromium puppeteer-core  # Chromium; unpack bin/al2023.tar.br
LD_LIBRARY_PATH=/tmp/al2023/lib CHROMIUM=/tmp/chromium PUPPETEER_MODULES=/tmp/browser/node_modules node tests/mobile_check.mjs
```

### Push / CI / release (actual)

- Commit **`564e4e0a57f35e0f143b9279b913f85bfb7221dc`** pushed to `arena/339e10e8-mathematics`
  (first push of the branch, 11:18 UTC).
- Push run **[38555641548](https://github.com/zigorminsk-debug/mathematics/actions/runs/38555641548)**:
  prepare, «Content & web», «Windows app (Go)», «Android app (APK)» (key pin, Kotlin unit tests,
  debug APK, signed release APK, signature, package/versionCode) and the publisher — all
  **success**; the previous-subject-APK gate was skipped by design (first release of the family).
  Full logs are not downloadable from the sandbox (redirect host blocked); step results via API.
- Release **[russian-v2026.10.1](https://github.com/zigorminsk-debug/mathematics/releases/tag/russian-v2026.10.1)**,
  id `412633540`, published 2026-10-14T11:20:39Z, not draft/prerelease, tag → `564e4e0`,
  13 assets uploaded; the 11 payload digests in the body JSON (`release-info.json`) equal the
  server-side SHA-256 digests and sizes; subject `russian`, package `by.ziv.ctrussian`,
  versionCode `261001`, certificate `DE:65:1A:CC:…`, `repositoryLatestBefore` = `v2026.10.8`/`412525779`.
  Sizes: APK 5 103 320 B, amd64 EXE 7 994 880 B, arm64 EXE 7 614 464 B.
- **Mathematics latest after publication: still `v2026.10.8`, id `412525779`** (unchanged).
- Live check of the shipped Windows resolver (Linux build with an embedded bank set to
  2026.10.0): it selected `russian-v2026.10.1` from the real Releases API (ignoring the maths
  latest) and requested that tag's `version.json`; the asset redirect host is blocked in the
  sandbox, so it reported `offline` and installed nothing (safe failure).
- This documentation commit is pushed too and, by the standing rule, publishes the next
  patch (`russian-v2026.10.2`); its own audit lives in that release (no bot-commit loop).

### Next steps

1. Physical-device checks are still open: install the APK on an Android phone next to the
   mathematics app, update over it with a later `russian-v…` APK; run both EXEs on Windows
   (x64 and ARM) — **not tested** by agents.
2. Content can grow: more items per pool/rule, more texts; keep the dictionary gate strict.
3. If the owner wants a private key before wider distribution, decide it BEFORE many users
   install the app (a different key cannot update an installed APK).
