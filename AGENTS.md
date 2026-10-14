# Agent handoff — CT Maths Tutor

Read this file, `docs/WORKLOG.md` and `docs/RELEASE.md` before changing the project.
The worklog is a dated human record, not a live release-status database. The
actual source is Git; the actual publication state is GitHub Actions/Releases.

## Standing user requirements (2026-10-14)

> «публикуй автоматически все сборки сразу после внесения изменений, и
> документируй все действия чтобы любой агент продолжил работу»

- After a trusted push to `zigorminsk-debug/mathematics`, CI must automatically
  publish the signed release APK, **both** Windows EXEs, and the content feed
  **after all checks pass**. Do not revert to artifact-only/manual publication.
- Record material changes, commands, validation results, failures, commit/PR/run
  identities, publication outcome and remaining uncertainties in
  `docs/WORKLOG.md`. Keep this handoff/runbook accurate when architecture changes.
- Every published release automatically carries `release-info.json` and
  `SHA256SUMS.txt`; Actions also keeps `release-audit` and step summaries.
  The same JSON ledger is also mirrored in Release body (API-readable even when
  binary asset redirects are blocked). These immutable records avoid an endless bot-commit → release → bot-commit loop.
- A new documentation-only push also produces a release. A rerun of an already
  published source is idempotent: never replace public assets or move a version tag.

## Repository and source of truth

- Android: `android/`, Kotlin/Gradle; Windows: `windows/`, Go.
- Shared UI: **edit `webapp/`**, then regenerate/sync platform copies.
- Authored RU/EN content: **edit `content_src/`**, not generated JSON/resources.
- `tools/build_content.py` verifies all task answers with exact arithmetic;
  `tools/sync_assets.py` distributes the shared interface and data.
- `VERSION` is the **minimum source/build version**, not necessarily the latest
  published version. CI allocates a higher effective version automatically,
  applies it to runner checkouts only, and uses it for all three artifacts.
  Never commit CI-generated release output or bump a version merely to log a run.
- `dist/`, `release/`, `staging/`, native builds, `.venv/`, `node_modules/`,
  `scratch/` are disposable/ignored. Do not commit binaries, caches or credentials.
- Honour the branch fixed by the active Arena session. This session is
  `arena/d7e34c80-mathematics`, PR #4 against `main`. Do not switch/create/push
  another branch here; do not merge/close a PR unless the user asks. Until PR #4
  is merged, old main does not contain these workflows/handoff documents; start
  from this working branch or integrate its published history before continuing.

## Invariants — do not regress

1. Stable Android package: **`by.ziv.ctmaths`**. Permanent certificate:
   **`B2:BD:B4:D1:26:B8:88:C7:D8:AF:50:80:F6:7E:CF:E1:E4:3F:EB:F2:8E:5D:1A:E6:61:D6:D7:AE:70:C5:14:65`**.
   Keep `android/keystore/ctmaths-release.p12` and the expected certificate unchanged.
   It is a public/demo key; do not substitute a private key for this installed app.
2. Effective version `YYYY.month.patch` has patch 0–99. APK code is
   `(year-2000)*10000 + month*100 + patch`. New public codes must strictly increase
   and both APK signatures/package IDs must match the previous stable APK.
3. Debug APK is development-only, package `by.ziv.ctmaths.debug`, and is **not**
   a phone update or a public Release asset. It remains a separate CI artifact.
4. Never suggest uninstalling to fix an update: that removes local statistics.
   Diagnose installed package, certificate and code first. Do not claim a physical
   phone installation was tested when only CI/browser checks were run.
5. Six **authored practice**, not official RIKZ papers, cover 2021–2026; 2026 has
   18 A + 12 B tasks. Keep RU/EN statements, hints, worked solutions and checks.
6. Wrong practice/analogous answers open relevant study; exam remediation happens
   after finishing. Revision points, formula groups and rows must open offline
   definitions/rules/theorems/examples. Back/language changes preserve session,
   answer, search, scroll and focus. Study currently has 56 lessons/18 topics.
7. Preserve atomic/checksummed content updates and protection against older
   downloaded banks hiding newer built-in content. Settings/statistics must survive.
8. Do not publish from a PR/fork or bypass any failed/skipped build/check job.
   Publication must reuse **same-run checked artifacts**, not rebuild separately.
   `BUILD_JOBS` in `tools/release_plan.py` must match CI job names if renamed.

## Start / check / finish

```bash
pwd; git branch --show-current; git status --short; git log -5 --oneline
# Actual publication and Actions state, not stale prose/VERSION:
gh api repos/zigorminsk-debug/mathematics/releases/latest \
  --jq '{tag: .tag_name, url: .html_url, source: .target_commitish, assets: [.assets[].name]}'
gh run list --workflow ci.yml --branch arena/d7e34c80-mathematics --limit 8 \
  --json databaseId,headSha,event,status,conclusion,url

python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
python3 tools/build_content.py
python3 tools/sync_assets.py
python3 tools/sync_assets.py --check
node --check webapp/core.js && node --check webapp/app.js
node tests/answer_parity.js
node tests/content_schema.js
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python tools/check_syntax.py --require
npm install --no-save jsdom
node tests/ui_smoke.js && node tests/native_smoke.js && node tests/theory_smoke.js
git diff --check
# Also go vet/test and Gradle/Kotlin/APK gates when local toolchains exist;
# regardless, wait for actual native CI checks and publication before claiming success.
```

After editing, update the worklog with what actually ran (distinguish local/CI,
planned/completed, device/browser). Commit/push only the session branch. A push
starts publication automatically: watch the run and verify latest contains all
13 expected assets, its tag targets the pushed SHA, and its audit reports the
same effective version/code. Report stable user download links, not expiring
Actions artifacts, when publication is confirmed. A failed run is not a release.

To continue after failure: follow `docs/RELEASE.md` recovery; query checks and
annotations rather than repeatedly downloading unavailable full logs. Never
force-publish an incomplete draft, weaken certificate/code gates, repoint a tag,
or bypass a stale-history error. A publishing branch must descend from the most
recent public release; integrate that history on the allowed working branch.

## Known Arena/environment limitations (dated 2026-10-14)

- `gh workflow run release.yml ...` returned **403 Resource not accessible by
  integration** (manual Actions-dispatch permission missing). Push-triggered CI
  does not need this permission and publishes with its own scoped `GITHUB_TOKEN`.
  If required GitHub operations still fail auth/permissions, tell the user to
  reconnect GitHub in Arena; never request/store passwords, PATs, OAuth or 2FA.
- Old local `gh pr edit` hits deprecated GraphQL Projects(classic). Update PR #4
  with REST instead: `gh api --method PATCH repos/zigorminsk-debug/mathematics/pulls/4 -F body=@scratch/pr-body.md`.
- Old `gh run list` lacks `--commit`: query `headSha` JSON and filter it.
- Artifact/APK/full-log redirects and binary tool downloads may be blocked by
  sandbox egress; GitHub-hosted runners and user-browser download links work.
  Local Go/JDK/Gradle were unavailable. Do not silently label native tests local.
- An Arena checkout may be shallow. If a known published ancestor appears
  unrelated, first `git rev-parse --is-shallow-repository`; when true, run
  `git fetch --unshallow origin`, then retry ancestry/plan. Do not merge an
  actually related tag or weaken the gate just because local history is incomplete.
- Runners are pinned to `ubuntu-24.04`; CI reported `ubuntu-latest` migrating
  to Ubuntu 26 on 2026-10-19. Upgrade intentionally only with native verification.
- `actionlint-py` locally could not fetch its binary; actionlint v1.7.12 also
  predates the documented Actions `queue` key. Workflow contracts/YAML parsing
  are tested here, and the real GitHub run is the authoritative validation.
- Preview binds to `0.0.0.0`; browser-facing APIs use relative URLs. Any scratch
  preview/mobile-test process is temporary, not the durable project handoff.
