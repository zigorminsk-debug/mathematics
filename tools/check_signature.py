#!/usr/bin/env python3
"""tools/check_signature.py — подпись релизного APK проверяется автоматически.

Обновление Android устанавливается «поверх» старой версии **только** если APK
подписан тем же сертификатом.  Поэтому эталонный отпечаток ключа хранится в
репозитории (`android/keystore/expected-cert-sha256.txt`), а CI сверяет с ним
каждый собранный APK.  Подмена или пересоздание ключа немедленно ломает сборку,
а не выясняется у пользователя при установке.

Usage:
    python3 tools/check_signature.py [--apk PATH] [--expected PATH] [--tool apksigner]

Если apksigner недоступен (например, вне Android SDK), проверка мягко
пропускается — CI всегда передаёт путь к инструменту явно.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk"
EXPECTED = ROOT / "android" / "keystore" / "expected-cert-sha256.txt"

DIGEST = re.compile(r"certificate SHA-256 digest:\s*([0-9a-fA-F:]+)")


def normalize(value: str) -> str:
    """B2:BD:... и b2bd... — один и тот же отпечаток."""
    return value.replace(":", "").strip().lower()


def find_apksigner(explicit: str | None) -> str | None:
    if explicit:
        return explicit if pathlib.Path(explicit).exists() else None
    found = shutil.which("apksigner")
    if found:
        return found
    sdk = pathlib.Path.home() / "Android" / "Sdk" / "build-tools"
    if sdk.exists():
        for candidate in sorted(sdk.glob("*/apksigner"), reverse=True):
            return str(candidate)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", default=str(DEFAULT_APK))
    parser.add_argument("--expected", default=str(EXPECTED))
    parser.add_argument("--tool", default=None, help="путь к apksigner")
    args = parser.parse_args()

    apk = pathlib.Path(args.apk)
    expected_file = pathlib.Path(args.expected)
    if not apk.exists():
        print(f"· подписи: {apk} нет — проверять нечего")
        return 0
    if not expected_file.exists():
        print(f"· подписи: нет эталона {expected_file} — пропускаю")
        return 0

    tool = find_apksigner(args.tool)
    if tool is None:
        print("· подписи: apksigner не найден — пропускаю (в CI он берётся из Android SDK)")
        return 0

    output = subprocess.run([tool, "verify", "--print-certs", str(apk)],
                            capture_output=True, text=True, check=False)
    text = output.stdout + output.stderr
    digests = {normalize(match) for match in DIGEST.findall(text)}
    expected = normalize(expected_file.read_text(encoding="utf-8"))

    if not digests:
        print("✗ не удалось прочитать сертификат APK")
        print(text.strip()[:800])
        return 1
    if expected not in digests:
        print(f"✗ APK подписан другим ключом: ожидался {expected}, получены {sorted(digests)}")
        print("  Обновление не установится поверх предыдущей версии!")
        return 1
    print(f"✓ подпись постоянным ключом подтверждена ({expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
