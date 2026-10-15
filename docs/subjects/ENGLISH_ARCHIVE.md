# English Drive archive — attribution and publication, 2026-10-15

The user explicitly requested publication with source attribution:
**«Публикуется со ссылкой на источник»**. Proceed through all normal CI gates;
do not bypass signing, parity or release verification. Publication is requested,
not yet verified at the time of this preflight entry. Previously shipped version:
`english-v2026.10.7` / `d16f8b3`.

Original task/key rights remain with their respective rights holders. The 2025
publisher notice requires written permission for reproduction; independent
confirmation of that permission has not been supplied. Attribution is not a
redistribution licence, and neither the app nor these documents claims otherwise.
The user's instruction authorizes the requested repository/release operation;
it is not recorded as proof of a licence from the publisher.

Source links are visible in every archive card and every task, outside the
collapsed scan reader, and open in the system browser. Release notes list all
five source files with URLs and key page references. No public availability of a
private Drive file is promised; Drive may require the user's own access.

## Exact scope

One COMPLETE **first variant** from each of five supplied books, **not all
variants in those books**. 216 source tasks are separate from the 305 existing
authored tasks. The local bank has 521 tasks, 39 analogous exercises, 80 mistake
diagnoses and 1,732 checker vectors. Authored IDs/year sets/statistics are not
replaced by source tasks. Archive task IDs are `en-archive-YYYY-v1-A/Bn`; their
`source=archive`, `archiveYear`/`archiveId` are separate from authored `year`.

| Supplied file year | Part A | Part B | Task PDF pages | Key PDF/printed page | Duration |
|---|---:|---:|---|---|---|
| 2021 | 30 | 18 | 2–5 | 42 / 44, column 1 | not established |
| 2022 | 30 | 18 | 2–5 | 42 / 44, column 1 | not established |
| 2023 | 18 | 22 | 5–7 | 43 / 34, column 1 | 120 min, PDF p4 |
| **2024, filename only** | 18 | 22 | 2–4 | 32 / 34, column 1 | not established |
| 2025 | 18 | 22 | 6–9 | 50 / 45, column 1 | 120 min, PDF p5 |

2024 has `verifiedYear=null`; the year qualification is visible on cards/titles.
For unstated durations the app explicitly uses a configurable practice timer,
not an invented historical duration. Some books are mixed CE/CT collections;
provenance is not a claim that every task is an independently authenticated
particular exam sitting. The 2021 extract lacks a publisher imprint.

## Transcription and source evidence

* `english/content_src/archive_text.py`: all **216** transcriptions, manually
  checked against the **18** JPEG question pages, with **534** numbered answer
  labels. OCR was a draft, not a trusted publication source. All reading passages
  are retained, including context on a preceding page (e.g. 2023 A17/A18,
  2024 A18, 2025 A15–A18 and A11/A12). This is not a placeholder task that only
  says “Original task…”.
* Intentional grammar/spelling defects are preserved. Square brackets with
  numbers replace underlining in error-location questions. The ten B extra-word
  lines retain their original B numbers, even when the device wraps a line.
  The OCR-missed 2025 B12 line has been restored from the image. Paragraphs,
  apostrophes, Cyrillic glosses and Russian fragments for translation survive.
* `english/content_src/archive/manifest.json`: source Drive URLs/IDs, retrieval
  date, PDF hashes/sizes, page hashes/geometry, key proof references and year /
  duration caveats. `drive-YYYY-v1/answers.json` holds the complete printed keys;
  accepted variants only: 2022 B5 inconvenience(s), 2025 B2 to/over.
  2022 B17 requires `else's`; `elses` and `else` are rejected.
* `english/content_src/archives.py`: fail-closed source importer, complete key /
  transcription / label / image / key-proof integrity checks. `given` stems
  supplied for all word-formation tasks. Corrections are app-authored, not a
  claim that explanatory prose was in the original printed key.
* `english/source_audit/*-key.jpg`: five answer-key proof pages; never embedded
  in exam `sourcePages`. The 18 question JPEGs are embedded once in the bank
  (~9.6 MB raw images). The bank is about 13.9 MB, with a regression assertion
  below the native updater's 32 MiB limit.

The user requested recognition for all tasks; all **216 currently imported**
tasks now have text. The rest of the books is still out of scope for this patch,
not silently marked imported. A explanations mostly remain “printed key + rule”;
B has short task-specific notes, but many extra-word explanations are generic.
**Do not claim complete per-option detailed explanations.**

## Interface and compatibility

`#/archives` is a distinct route. Training and exam sessions retain `archiveId`
in the session and attempt history. The new reader displays selectable plain
text and the FULL answer labels. The original image is a collapsed comparison
panel, with all context pages, previous/next controls and 100–400% zoom. No remote
image, iframe, raw OCR HTML or answer-key scan is rendered. Optional source-open
button accepts only the manifest's HTTPS Drive file URL shape.

New fields: `conditionText`, `optionLabels`, `transcriptionReviewed`,
`transcriptionSha256`. `text` ALSO contains the complete condition plus all
numbered choices, so an older installed reader can solve a downloaded task even
if it ignores the image or `optionLabels`. No mandatory “upgrade to see the
condition” placeholder remains. The new loader rejects missing/wrong-source /
remote pages, broken context-page metadata, missing conditions and labels.

The canonical checker bank still keeps the correct choice first by contract;
the archive UI sorts the ORIGINAL NUMBERS rather than exposing that ordering.
Exam choices/inputs/navigation grid acknowledge submissions neutrally, not with
correct/wrong colors. Exam auto-advance no longer depends on correctness, and a
stale delayed callback cannot advance a different session.

All Android assets/webapp copies, Windows embedded web files and Kotlin fixtures
have been synced by `CT_SUBJECT=english python3 tools/sync_assets.py`.
The subject/package/keystore/update channel remain unchanged. Physics files and
mathematics releases are not changed.

## Local checks and remaining gates

Completed locally:

* English build + asset sync/check; JS content schema; JS parity against 1,732
  Python-generated vectors and all 521 + 39 tasks.
* **13** Python archive tests: completeness, exact key checkpoints, safe JPEG
  hashes, key proofs, original option counts, no invented accepted variants,
  required apostrophe, text/labels/stems, shared contexts, all 50 extra-word
  answers in their actual source lines, intentional errors, fail-closed inputs.
* **10** period tests; **10** icon tests; jsdom archive journeys for all five
  variants, offline images, context navigation, zoom, plain conditions / labels,
  language switch, original number ordering, neutral exam feedback, training
  diagnosis → rule → analogous, B input, history, and six malformed-bank cases.
* `CT_SUBJECT=english .venv/bin/python tools/check_syntax.py --require`:
  **29** Go/Kotlin/Gradle files, zero syntax errors. System Python initially
  lacked tree-sitter; the established virtual environment has it.
* Root physics build to restore ignored dist, then **124/124** shared unittest
  tests passed with no skips; no tracked physics change.

**Pending remote CI at preflight:** native Kotlin/Gradle test execution, Go tests / EXE
cross-compilation (neither toolchain is on PATH in this sandbox), signed APK
build, actual GitHub Actions, physical phone/Windows install. The JS parity tool
prints a shared Python/JS/Kotlin headline, but it does NOT execute Kotlin: do not
misrepresent that output as native testing.

Before claiming publication: complete and verify native/CI gates and the actual
release inventory. Every trusted push automatically publishes only when green. Do not replace an already published tag or alter `main`/PR #4.

Reproduce local checks:

```sh
CT_SUBJECT=english python3 english/tools/build_content.py
CT_SUBJECT=english python3 tools/sync_assets.py
CT_SUBJECT=english python3 tools/sync_assets.py --check
python3 english/tests/test_archives.py
python3 english/tests/test_periods.py
python3 english/tests/test_icon.py
node english/tests/content_schema.js
node english/tests/answer_parity.js
node english/tests/ui_smoke.js  # npm install --no-save --package-lock=false jsdom@26
CT_SUBJECT=english .venv/bin/python tools/check_syntax.py --require
python3 tools/build_content.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

Large downloaded PDFs and intermediate PNG renders were moved to the ignored,
snapshot-excluded `.cache/english-drive/`; never add them to Git. These caches
may disappear on environment restoration. Re-download via the Drive IDs in the
manifest if needed. Small OCR draft txt/json plus the original one-off preparation
script remain ignored under `scratch/english-drive/`. That script expects the
original PDFs alongside it and is NOT the ongoing content builder; rerunning it
would regenerate source evidence. Canonical inputs for builds are under
`english/content_src/` and `english/source_audit/`, not scratch/cache.
