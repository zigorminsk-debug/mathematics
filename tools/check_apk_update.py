#!/usr/bin/env python3
"""Check APK package/version metadata, optionally against the previous release.

Uses aapt2 from the Android SDK. Certificate validation is performed separately
by check_signature.py. Missing tools/APKs are errors here: CI must not skip this
check and pretend an unsigned, differently named or downgraded APK can update.

Пакет берётся из ``tools/subject.py``: у физики это ``by.ziv.ctphysics``, и
математический APK не может пройти эту проверку (чужой пакет/подпись).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

import subject

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = subject.ANDROID_PACKAGE


def version_code(version: str) -> int:
    match = re.fullmatch(r"(20\d{2})\.(\d{1,2})\.(\d{1,2})", version)
    if not match:
        raise ValueError("VERSION must use YYYY.month.patch (patch 0–99)")
    year, month, patch = map(int, match.groups())
    if not 1 <= month <= 12:
        raise ValueError("VERSION month must be 1–12")
    return (year - 2000) * 10000 + month * 100 + patch


def parse_badging(text: str) -> dict:
    line = next((line for line in text.splitlines() if line.startswith("package: ")), "")
    values = dict(re.findall(r"(?:^|\s)(name|versionCode|versionName)='([^']*)'", line))
    if not all(key in values for key in ("name", "versionCode", "versionName")):
        raise ValueError("aapt2 returned no APK package/version metadata")
    values["versionCode"] = int(values["versionCode"])
    return values


def read_metadata(apk: Path, tool: str) -> dict:
    if not apk.is_file():
        raise ValueError(f"APK is missing: {apk}")
    result = subprocess.run([tool, "dump", "badging", str(apk)],
                            capture_output=True, text=True, check=True)
    return parse_badging(result.stdout)


def validate(actual: dict, version: str, previous: dict | None = None) -> None:
    expected = version_code(version)
    if actual["name"] != PACKAGE:
        raise ValueError(f"package {actual['name']} is not {PACKAGE}; it cannot replace the release")
    if actual["versionCode"] != expected or actual["versionName"] != version:
        raise ValueError(f"APK must be {version} (versionCode {expected}), got {actual}")
    if previous is not None:
        if previous["name"] != actual["name"]:
            raise ValueError("previous and new APKs have different packages")
        if actual["versionCode"] <= previous["versionCode"]:
            raise ValueError("release versionCode must exceed the previous release; increment VERSION")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--tool", default="aapt2")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--print-version-code", action="store_true")
    args = parser.parse_args()
    try:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        if args.print_version_code:
            print(version_code(version))
            return 0
        if not args.apk:
            raise ValueError("--apk is required")
        actual = read_metadata(args.apk, args.tool)
        previous = read_metadata(args.previous, args.tool) if args.previous else None
        validate(actual, version, previous)
        print(f"✓ APK package {actual['name']}, version {version}, versionCode {actual['versionCode']}")
        if previous:
            print(f"✓ versionCode increased from {previous['versionCode']}")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        # CI exposes this annotation even when the full runner log is inaccessible.
        message = f"APK update compatibility: {error}"
        if isinstance(error, subprocess.CalledProcessError):
            message += ": " + ((error.stderr or "") + (error.stdout or "")).strip()[:1000]
        print("::error::" + message.replace("\n", " "), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
