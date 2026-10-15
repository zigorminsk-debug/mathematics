#!/usr/bin/env python3
"""Publish ONLY the verified APK/EXEs/content artifacts of the current CI run.

Physics isolation (see ``tools/subject.py``): the release is created under the
``physics-vYYYY.M.P`` tag with **make_latest=false**, so the repository-wide
`releases/latest` keeps serving mathematics. The publisher additionally records
the global latest release before and after publication and fails the build if it
changed. The content feed gets tag-specific immutable URLs — physics clients
never read ``releases/latest/download``.

Assets are assembled and checked in a draft. Published releases and tags are
never overwritten. Run through .github/workflows/publish.yml, not as a shortcut
around CI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import subject
from release_plan import (ROOT, SUBJECT_ROOT, BUILD_JOBS, CONTENT_FILES, INSTALLERS,
                          RELEASE_FILES, canonical, check_lineage, gh, gh_json, gh_pages,
                          git_commit, stable_releases, validate_repo, version_code)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def metadata(path: Path) -> dict:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def validate_run(run: dict, jobs: list[dict], repo: str, sha: str, source_ref: str, tag: str) -> list[dict]:
    if run.get("repository", {}).get("full_name") != repo or run.get("head_sha") != sha:
        raise ValueError("artifacts must belong to this exact repository/source commit")
    if run.get("event") not in {"push", "workflow_dispatch"}:
        raise ValueError("PR/fork/untrusted workflow runs must never publish")
    if not ((source_ref.startswith("refs/heads/") and len(source_ref) > len("refs/heads/"))
            or source_ref == "refs/tags/" + tag):
        raise ValueError("only trusted repository branch pushes and explicit version tags may publish")
    verified = []
    for name in BUILD_JOBS:
        matches = [job for job in jobs if job["name"] == name or job["name"].endswith(" / " + name)]
        if len(matches) != 1 or matches[0].get("conclusion") != "success":
            raise ValueError(f"required build/check job did not succeed: {name}")
        job = matches[0]
        verified.append({"name": name, "id": job["id"], "conclusion": job["conclusion"],
                         "started_at": job.get("started_at"), "completed_at": job.get("completed_at"),
                         "url": job.get("html_url")})
    return verified


def exact_files(directory: Path, expected: set[str]) -> None:
    actual = {path.name for path in directory.iterdir()} if directory.is_dir() else set()
    if actual != expected or any(not (directory / name).is_file() or (directory / name).is_symlink()
                                 or not (directory / name).stat().st_size for name in actual):
        raise ValueError(f"incomplete/unexpected artifact inventory in {directory}: "
                         f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")


def assemble(staging: Path, output: Path, version: str, repo: str) -> dict:
    exact_files(staging / "content", CONTENT_FILES | {"version.json"})
    exact_files(staging / "windows", INSTALLERS - {subject.APK_ASSET})
    exact_files(staging / "android", {subject.APK_ASSET})
    if output.exists() and any(output.iterdir()):
        raise ValueError("release output directory must be empty")
    output.mkdir(parents=True, exist_ok=True)
    for directory in ("content", "windows", "android"):
        for path in (staging / directory).iterdir():
            shutil.copyfile(path, output / path.name)
    manifest = json.loads((output / "version.json").read_text(encoding="utf-8"))
    if manifest.get("contentVersion") != version or manifest.get("appVersion", version) != version:
        raise ValueError("content artifact version is not the allocated APK/EXE version")
    if manifest.get("subject") != subject.SUBJECT or manifest.get("package") != subject.ANDROID_PACKAGE:
        raise ValueError("content artifact does not carry this subject's identity")
    if set(manifest.get("files", {})) != CONTENT_FILES:
        raise ValueError("content manifest does not describe all and only content JSON files")
    base = subject.content_base_url(repo, version)
    for name in sorted(CONTENT_FILES):
        path = output / name
        json.loads(path.read_text(encoding="utf-8"))  # invalid/truncated JSON cannot be published
        actual = metadata(path)
        expected = manifest["files"][name]
        if expected.get("sha256") != actual["sha256"] or expected.get("bytes") != actual["bytes"]:
            raise ValueError("artifact checksum/size mismatch: " + name)
        manifest["files"][name] = {"url": f"{base}/{name}", **actual}
    manifest["baseUrl"] = base
    manifest["appVersion"] = version
    manifest["tag"] = subject.tag(version)
    manifest["subject"] = subject.SUBJECT
    manifest["package"] = subject.ANDROID_PACKAGE
    manifest["updatePolicy"] = "immutable version-specific URLs; no repository latest"
    write_json(output / "version.json", manifest)
    return manifest


def validate_inventory(release: dict, output: Path) -> None:
    assets = release.get("assets", [])
    if len(assets) != len(RELEASE_FILES) or {asset["name"] for asset in assets} != RELEASE_FILES:
        raise ValueError("GitHub draft is missing assets or contains unexpected files (debug APK is forbidden)")
    for asset in assets:
        path = output / asset["name"]
        if asset.get("state") != "uploaded" or asset.get("size") != path.stat().st_size:
            raise ValueError("GitHub asset is incomplete: " + asset["name"])
        # Modern GitHub exposes a server-side digest. Compare when provided;
        # older API responses omit it. The same-run download action and local
        # manifest/SHA256SUMS supply the independent artifact checks as well.
        server_digest = asset.get("digest")
        if server_digest and server_digest != "sha256:" + digest(path):
            raise ValueError("GitHub uploaded asset digest mismatch: " + asset["name"])


def reserve_tag(repo: str, tag: str, sha: str, existing: str | None) -> None:
    """Резервирует тег версии до создания черновика.

    Отдельный helper, потому что GitHub отдаёт только что созданный ref с
    задержкой: чтение сразу после POST может вернуть 404. Именно на этом упал
    выпуск `english-v2026.10.2` («tag changed during preparation»), хотя тег был
    создан и указывал на нужный коммит. Поэтому после создания тега несколько
    раз перечитываем его, прежде чем считать тег подменённым.
    """
    if not existing:
        gh_json(f"repos/{repo}/git/refs", method="POST",
                fields={"ref": "refs/tags/" + tag, "sha": sha})
    current = existing
    for attempt in range(8):
        current = tag_commit(repo, tag)
        if current == sha:
            return
        time.sleep(1 + attempt)   # чтение может отставать от записи
    raise ValueError(f"tag {tag} does not point at {sha} after reservation "
                     f"(read {current}); refusing to create a draft")


def tag_commit(repo: str, tag: str) -> str | None:
    ref = gh_json(f"repos/{repo}/git/ref/tags/{tag}", allow_404=True)
    if not ref:
        return None
    obj = ref["object"]
    for _ in range(8):
        if obj["type"] == "commit":
            return obj["sha"]
        if obj["type"] != "tag":
            break
        obj = gh_json(f"repos/{repo}/git/tags/{obj['sha']}")["object"]
    raise ValueError("release tag does not resolve to a commit")


def release_notes(version: str, sha: str, run_url: str, code: int) -> str:
    content_notice = "Задания авторские, не официальные материалы РИКЗ."
    sources = ""
    if subject.SUBJECT == "english":
        manifest_path = SUBJECT_ROOT / "content_src" / "archive" / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            content_notice = ("305 авторских тренировочных заданий и 216 распознанных заданий из пяти исходных "
                              "вариантов № 1 (не все варианты сборников). Архив отделён от авторских наборов; "
                              "это не официальный продукт РИКЗ. Задания и печатные ключи принадлежат исходным "
                              "правообладателям; приложение добавляет распознавание, проверку и комментарии. "
                              "2024 указан только по имени файла, год независимо не подтверждён.")
            sources = "\n### Источники архивных вариантов\n" + "\n".join(
                f"- [{item['filename']}]({item['url']}) — вариант 1, ключ: PDF-страница {item['keyPdfPage']}."
                for item in manifest["variants"]
            ) + "\n\nПодробнее: `docs/subjects/ENGLISH_ARCHIVE.md` в исходниках этого тега.\n"
    return f"""## {subject.TITLE['ru']} {version}

Автоматическая публикация после успешных проверок контента и интерфейса, Windows и Android.
Source: `{sha}` · [Проверки и журнал сборки]({run_url}).

### Скачать / Download
- **Android:** `{subject.APK_ASSET}`, пакет `{subject.ANDROID_PACKAGE}`, versionCode **{code}**.
  Установите **поверх** существующей release-версии; **не удаляйте приложение** — это удалит статистику.
  Это **не обновление математики**: пакет, статистика и банк у {"английского языка" if subject.SUBJECT == "english" else "физики"} свои.
- **Windows:** `{subject.WINDOWS_BINARY}-amd64.exe` или `{subject.WINDOWS_BINARY}-arm64.exe`.
- **Банк заданий:** приложение получает `version.json` и проверенные JSON по
  неизменяемым ссылкам **этого** выпуска (`{subject.TAG_PREFIX}{version}`); общий
  `/releases/latest/download` не используется.

Встроенная база и RU/EN-материалы работают офлайн. {content_notice}
Этот релиз не помечается как repository latest намеренно: математика продолжает отдаваться по своей ссылке.
Debug APK остаётся отдельным артефактом разработки и в этот релиз не входит.
{sources}
### Аудит / Agent handoff
`release-info.json` содержит subject/package, commit, run/attempt, effective/source version, результаты
трёх обязательных jobs, отпечаток постоянного сертификата и SHA-256/размеры файлов.
`SHA256SUMS.txt` проверяет также сам журнал.
Инструкции продолжения: `AGENTS.md`, `docs/WORKLOG.md`, `docs/RELEASE.md` в исходниках этого тега.
"""


def publish(args) -> dict:
    validate_repo(args.repo)
    version = canonical(args.version)
    tag = subject.tag(version)
    sha = git_commit("HEAD")
    source_version = (SUBJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if args.source_version != source_version or version_code(version) < version_code(source_version):
        raise ValueError("source floor/effective version mismatch")
    if sha != os.environ.get("GITHUB_SHA") or args.run_id != os.environ.get("GITHUB_RUN_ID"):
        raise ValueError("publisher must run on its own exact GitHub Actions commit/run")
    run = gh_json(f"repos/{args.repo}/actions/runs/{args.run_id}")
    jobs = gh_pages(f"repos/{args.repo}/actions/runs/{args.run_id}/jobs?filter=latest&per_page=100")
    verified = validate_run(run, jobs, args.repo, sha, os.environ.get("GITHUB_REF", ""), tag)
    releases = gh_pages(f"repos/{args.repo}/releases?per_page=100")
    stable = stable_releases(releases)
    previous = stable[-1] if stable else None
    if previous and version_code(version) <= version_code(subject.release_version(previous["tag_name"])):
        raise ValueError("a newer/equal stable version already exists; rerun CI to re-plan, never overwrite it")
    # Снимок общерепозиторного latest до публикации: физика обязана его не сдвинуть.
    latest_before = gh_json(f"repos/{args.repo}/releases/latest", allow_404=True)
    latest_before_id = latest_before["id"] if latest_before else None
    latest_before_tag = latest_before["tag_name"] if latest_before else None
    check_lineage(previous, sha)
    existing_tag_sha = tag_commit(args.repo, tag)
    if existing_tag_sha and existing_tag_sha != sha:
        raise ValueError("release tag is already owned by a different source commit")
    release = next((entry for entry in releases if entry["tag_name"] == tag), None)
    if release and (not release["draft"] or (existing_tag_sha or release.get("target_commitish")) != sha):
        raise ValueError("only an interrupted draft for this same tagged source commit may be resumed")
    manifest = assemble(args.staging, args.output, version, args.repo)
    code = version_code(version)
    run_url = f"https://github.com/{args.repo}/actions/runs/{args.run_id}"
    payloads = {name: metadata(args.output / name) for name in sorted(CONTENT_FILES | INSTALLERS | {"version.json"})}
    info = {
        "schemaVersion": 2, "repository": args.repo, "subject": subject.SUBJECT,
        "package": subject.ANDROID_PACKAGE, "app": subject.WINDOWS_BINARY,
        "tag": tag, "version": version,
        "sourceVersion": source_version, "sourceCommit": sha,
        "verifiedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "run": {"id": int(args.run_id), "attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
                "url": run_url, "event": run["event"], "ref": os.environ["GITHUB_REF"]},
        "checks": verified, "previousStableTag": previous["tag_name"] if previous else None,
        "android": {"applicationId": subject.ANDROID_PACKAGE, "versionName": version, "versionCode": code,
                    "certificateSha256": (SUBJECT_ROOT / subject.EXPECTED_CERT).read_text().strip(),
                    "signatureAndPreviousApkGate": "passed"},
        "content": {"version": manifest["contentVersion"], "files": sorted(CONTENT_FILES)},
        "assets": payloads,
        "publication": {"strategy": "verified draft, then publish with make_latest=false",
                        "overwritePublishedAssets": False,
                        "repositoryLatestBefore": latest_before_tag,
                        "repositoryLatestMustRemain": latest_before_tag},
    }
    write_json(args.output / "release-info.json", info)
    (args.output / "SHA256SUMS.txt").write_text("".join(
        f"{digest(path)}  {path.name}\n" for path in sorted(args.output.iterdir()) if path.is_file()), encoding="utf-8")
    exact_files(args.output, RELEASE_FILES)
    notes = release_notes(version, sha, run_url, code)
    # Mirror the machine ledger in release metadata: agents with sandbox egress
    # restrictions can read it through the API without binary-storage redirects.
    notes += "\n<details>\n<summary>Machine-readable release audit / JSON</summary>\n\n```json\n"
    notes += json.dumps(info, ensure_ascii=False, indent=2) + "\n```\n</details>\n"
    # Reserve an immutable tag before creating/uploading the draft. Read-only
    # planners can see this tag even if draft visibility is restricted. A later
    # source skips the reservation; the same source can resume it. No bot commits
    # or workflow recursion: this API mutation uses the Actions GITHUB_TOKEN.
    reserve_tag(args.repo, tag, sha, existing_tag_sha)
    fields = {"tag_name": tag, "target_commitish": sha, "name": f"{subject.TITLE['ru']} {version}",
              "body": notes, "draft": True, "prerelease": False}
    if release:
        if {asset["name"] for asset in release.get("assets", [])} - RELEASE_FILES:
            raise ValueError("draft has unrelated assets; review it instead of silently removing them")
        release = gh_json(f"repos/{args.repo}/releases/{release['id']}", method="PATCH", fields=fields)
    else:
        release = gh_json(f"repos/{args.repo}/releases", method="POST", fields=fields)
    # --clobber is restricted to a nonpublic draft that belongs to this SHA.
    # A failed upload/validation leaves latest untouched; a rerun resumes it.
    current = gh_json(f"repos/{args.repo}/releases/{release['id']}")
    if not current["draft"] or tag_commit(args.repo, tag) != sha:
        raise ValueError("draft was externally published or tag changed; public assets cannot be clobbered")
    gh(["release", "upload", tag, "--repo", args.repo, "--clobber",
        *[str(args.output / name) for name in sorted(RELEASE_FILES)]])
    release = gh_json(f"repos/{args.repo}/releases/{release['id']}")
    validate_inventory(release, args.output)
    if tag_commit(args.repo, tag) != sha:
        raise ValueError("tag changed during publication; refusing to switch latest")
    release = gh_json(f"repos/{args.repo}/releases/{release['id']}", method="PATCH",
                      fields={"draft": False, "prerelease": False, "make_latest": "false"})
    validate_inventory(release, args.output)
    published = gh_json(f"repos/{args.repo}/releases/{release['id']}")
    if published["draft"] or published.get("prerelease"):
        raise ValueError("GitHub did not confirm the physics release as published stable")
    if published["tag_name"] != tag:
        raise ValueError("published release tag mismatch")
    # Общий latest обязан остаться математическим (или прежним, если математики нет).
    latest_after = gh_json(f"repos/{args.repo}/releases/latest", allow_404=True)
    latest_after_id = latest_after["id"] if latest_after else None
    if latest_after_id != latest_before_id:
        raise ValueError("repository latest changed during physics publication — isolation violated")
    print("Published:", release["html_url"])
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as output:
            output.write(f"## Published {tag}\n\n[Release]({release['html_url']}) · [Build checks]({run_url})\n\n")
            output.write(f"Source: `{sha}`; source VERSION: `{source_version}`; APK code: `{code}`.\n\n")
            output.write("All three build/check jobs succeeded. Complete verified draft promoted to latest.\n\n")
            output.write("| Asset | Bytes | SHA-256 |\n|---|---:|---|\n")
            for path in sorted(args.output.iterdir()):
                output.write(f"| `{path.name}` | {path.stat().st_size} | `{digest(path)}` |\n")
    return release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        publish(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("::error::Publication: " + str(error).replace("\n", " "), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
