#!/usr/bin/env python3
"""Resolve a monotonically increasing release version without bot commits.

VERSION is the source's minimum version. Trusted CI builds resolve an effective
version against published releases and apply it only in the runner checkout.
The APK, EXEs and JSON feed all use that exact effective version. Re-running an
already published source commit is idempotent; published assets are immutable.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

from check_apk_update import version_code

ROOT = Path(__file__).resolve().parents[1]
CONTENT_FILES = {"bank.json", "analogous.json", "topics.json", "formulas.json",
                 "ui_strings.json", "mistakes.json", "answer_vectors.json"}
INSTALLERS = {"app-release.apk", "CTMathsTutor-amd64.exe", "CTMathsTutor-arm64.exe"}
RELEASE_FILES = CONTENT_FILES | INSTALLERS | {"version.json", "release-info.json", "SHA256SUMS.txt"}
BUILD_JOBS = ("Content & web (verify, parity, assets)", "Windows app (Go)", "Android app (APK)")


def canonical(version: str) -> str:
    version_code(version)
    return ".".join(str(int(part)) for part in version.split("."))


def next_version(version: str) -> str:
    year, month, patch = map(int, canonical(version).split("."))
    if patch < 99:
        patch += 1
    elif month < 12:
        month, patch = month + 1, 0
    else:
        year, month, patch = year + 1, 1, 0
    return canonical(f"{year}.{month}.{patch}")


def release_version(release: dict) -> str | None:
    tag = release.get("tag_name", "")
    if not tag.startswith("v"):
        return None
    try:
        return canonical(tag[1:])
    except ValueError:
        return None


def stable_releases(releases: list[dict]) -> list[dict]:
    return sorted((entry for entry in releases if not entry.get("draft")
                   and not entry.get("prerelease") and release_version(entry)),
                  key=lambda entry: version_code(release_version(entry)))


def choose_version(source: str, releases: list[dict], commit: str,
                   today: date, requested_tag: str = "") -> dict:
    """Pure release policy, covered by test_release.py."""
    floor = canonical(source)
    stable = stable_releases(releases)
    previous = stable[-1] if stable else None
    same_commit = [entry for entry in stable if entry.get("_source_sha", entry.get("target_commitish")) == commit
                   and version_code(release_version(entry)) >= version_code(floor)]
    if same_commit:
        existing = same_commit[-1]
        missing = RELEASE_FILES - {asset["name"] for asset in existing.get("assets", [])}
        if missing:
            raise ValueError("published source has incomplete assets; do not overwrite it: " + ", ".join(sorted(missing)))
        version = release_version(existing)
        already = True
        url = existing["html_url"]
    else:
        candidates = [floor, canonical(f"{today.year}.{today.month}.0")]
        if previous:
            candidates.append(next_version(release_version(previous)))
        version = max(candidates, key=version_code)
        own_reservations = [release_version(entry) for entry in releases
                            if entry.get("draft") and entry.get("_source_sha", entry.get("target_commitish")) == commit
                            and release_version(entry)
                            and version_code(release_version(entry)) >= version_code(floor)
                            and (not previous or version_code(release_version(entry)) > version_code(release_version(previous)))]
        if own_reservations:
            version = max(own_reservations, key=version_code)
        # An interrupted draft for this source can be resumed. Never replace a
        # draft reserved by a different source commit, or a prerelease tag.
        by_tag = {entry["tag_name"]: entry for entry in releases}
        while "v" + version in by_tag:
            reserved = by_tag["v" + version]
            if reserved.get("draft") and reserved.get("_source_sha", reserved.get("target_commitish")) == commit:
                break
            version = next_version(version)
        already, url = False, ""
    tag = "v" + version
    if requested_tag and requested_tag != tag:
        raise ValueError(f"requested tag {requested_tag} must be {tag}; no downgrades or tag rewrites")
    return {"version": version, "tag": tag, "source_version": source,
            "source_sha": commit, "already_published": already, "release_url": url,
            "previous_tag": previous["tag_name"] if previous else "",
            "previous_version": release_version(previous) if previous else "", "publish": True}


def gh(arguments: list[str], *, allow_404=False) -> str | None:
    result = subprocess.run(["gh", *arguments], text=True, capture_output=True)
    if result.returncode:
        if allow_404 and "HTTP 404" in result.stderr:
            return None
        raise RuntimeError("GitHub command failed: " + (result.stderr or result.stdout).strip())
    return result.stdout


def gh_json(path: str, *, method="GET", fields: dict | None = None, allow_404=False):
    arguments = ["api", "--method", method, path]
    for key, value in (fields or {}).items():
        if isinstance(value, bool):
            arguments += ["-F", f"{key}={'true' if value else 'false'}"]
        else:
            arguments += ["-f", f"{key}={value}"]
    raw = gh(arguments, allow_404=allow_404)
    return json.loads(raw) if raw is not None else None


def gh_pages(path: str) -> list[dict]:
    # --paginate emits one JSON array/object per page. Decode consecutive JSON
    # documents; --slurp is intentionally avoided for older local gh versions.
    raw = gh(["api", "--paginate", path])
    decoder, cursor, result = json.JSONDecoder(), 0, []
    while cursor < len(raw):
        while cursor < len(raw) and raw[cursor].isspace():
            cursor += 1
        if cursor == len(raw):
            break
        page, cursor = decoder.raw_decode(raw, cursor)
        result.extend(page if isinstance(page, list) else page.get("jobs", []))
    return result


def validate_repo(repo: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("invalid GitHub repository name")


def git_commit(ref: str) -> str:
    return subprocess.check_output(["git", "rev-parse", "--verify", ref + "^{commit}"],
                                   cwd=ROOT, text=True, stderr=subprocess.PIPE).strip()


def resolve_release_sources(releases: list[dict]) -> None:
    # GitHub may retain a branch name as target_commitish when a tag already
    # exists. The immutable tag, not today's moving branch, identifies source.
    for entry in releases:
        if not release_version(entry):
            continue
        ref = "refs/tags/" + entry["tag_name"]
        try:
            entry["_source_sha"] = git_commit(ref)
        except subprocess.CalledProcessError:
            if entry.get("draft"):
                continue  # a manually created, untagged draft may only have a SHA
            subprocess.run(["git", "fetch", "origin", "tag", entry["tag_name"]],
                           cwd=ROOT, check=True, capture_output=True, text=True)
            entry["_source_sha"] = git_commit(ref)


def unpublished_tag_reservations(releases: list[dict]) -> list[dict]:
    """Keep read-only planning aware of tags reserved by interrupted publishers."""
    known = {entry["tag_name"] for entry in releases}
    tags = subprocess.check_output(["git", "tag", "--list", "v*"], cwd=ROOT, text=True).splitlines()
    reservations = []
    for tag in tags:
        if tag not in known and release_version({"tag_name": tag}):
            reservations.append({"tag_name": tag, "target_commitish": git_commit("refs/tags/" + tag),
                                 "draft": True, "prerelease": False})
    return reservations


def check_lineage(previous: dict | None, commit: str) -> None:
    if not previous:
        return
    tag = previous["tag_name"]
    if not release_version(previous):
        raise ValueError("invalid previous release tag")
    try:
        ancestor = git_commit("refs/tags/" + tag)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "fetch", "origin", "tag", tag], cwd=ROOT, check=True,
                       capture_output=True, text=True)
        ancestor = git_commit("refs/tags/" + tag)
    result = subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, commit], cwd=ROOT)
    if result.returncode != 0:
        raise ValueError(f"source {commit} does not descend from published {tag} ({ancestor}); "
                         "bring the published history into the working branch before releasing")


def apply_version(path: Path, version: str) -> None:
    actual = canonical(version)
    source = path.read_text(encoding="utf-8").strip()
    if version_code(actual) < version_code(source):
        raise ValueError("effective build version must not be below VERSION")
    path.write_text(actual + "\n", encoding="utf-8")


def write_outputs(plan: dict, path: Path | None) -> None:
    if path:
        with path.open("a", encoding="utf-8") as output:
            for key, value in plan.items():
                text = str(value).lower() if isinstance(value, bool) else str(value)
                if "\n" in text or "\r" in text:
                    raise ValueError("multiline workflow output rejected")
                output.write(f"{key}={text}\n")
    print(json.dumps(plan, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--commit", default="")
    parser.add_argument("--tag", default="")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--local", action="store_true", help="tests/PR build: no publication or API calls")
    parser.add_argument("--apply-version", help="apply an allocated version only in the current build checkout")
    args = parser.parse_args()
    try:
        if args.apply_version:
            apply_version(ROOT / "VERSION", args.apply_version)
            print("Effective build version:", args.apply_version)
            return 0
        source = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        canonical(source)
        commit = args.commit or git_commit("HEAD")
        if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != git_commit("HEAD"):
            raise ValueError("the release source must be the exact checked-out commit")
        if args.local:
            plan = {"version": source, "source_version": source, "source_sha": commit,
                    "tag": "v" + source, "publish": False, "already_published": False, "release_url": ""}
        else:
            if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
                raise ValueError("commit source changes before allocating a public build; checkout must be clean")
            validate_repo(args.repo)
            releases = gh_pages(f"repos/{args.repo}/releases?per_page=100")
            resolve_release_sources(releases)
            plan = choose_version(source, releases + unpublished_tag_reservations(releases), commit,
                                  datetime.now(ZoneInfo("Europe/Moscow")).date(), args.tag)
            if not plan["already_published"]:
                stable = stable_releases(releases)
                check_lineage(stable[-1] if stable else None, commit)
        write_outputs(plan, args.output)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as output:
                output.write("## Release plan\n\n")
                output.write(f"Source: `{commit}`; VERSION floor: `{source}`; effective version: `{plan['version']}`.\n\n")
                if plan["already_published"]:
                    output.write(f"Already published; assets will not be overwritten: {plan['release_url']}\n")
                elif plan["publish"]:
                    output.write("Publication waits for all content, Windows and Android checks.\n")
                else:
                    output.write("Untrusted/PR/test run: publication is disabled.\n")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("::error::Release plan: " + str(error).replace("\n", " "), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
