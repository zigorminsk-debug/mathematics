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

import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import subject  # noqa: E402  (профиль предмета: CT_SUBJECT, по умолчанию physics)

SUBJECT_ROOT = pathlib.Path(subject.SUBJECT_ROOT)
DEFAULT_APK = SUBJECT_ROOT / subject.GRADLE_APK
EXPECTED = SUBJECT_ROOT / subject.EXPECTED_CERT

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


def check_keystore(expected_file: pathlib.Path, keystore: pathlib.Path, password: str, required: bool = False) -> int:
    """Сверить сам ключ с эталоном — работает и без Android SDK (через openssl)."""
    if not keystore.exists():
        print(f"· подписи: ключа {keystore} нет")
        return 1 if required else 0
    if shutil.which("openssl") is None:
        print("· подписи: openssl не найден")
        return 1 if required else 0
    extract = subprocess.run(
        ["openssl", "pkcs12", "-in", str(keystore), "-passin", f"pass:{password}", "-nokeys", "-clcerts"],
        capture_output=True, check=False)
    if extract.returncode != 0:
        print("✗ не удалось прочитать ключ (нужен пароль от keystore.properties)")
        print(extract.stderr.decode(errors="replace").strip()[:400])
        return 1
    info = subprocess.run(["openssl", "x509", "-noout", "-fingerprint", "-sha256"],
                          input=extract.stdout, capture_output=True, check=False)
    digest = re.search(r"=([0-9a-fA-F:]+)", info.stdout.decode(errors="replace"))
    if digest is None:
        print("✗ не удалось посчитать отпечаток ключа")
        return 1
    actual = normalize(digest.group(1))
    expected = normalize(expected_file.read_text(encoding="utf-8"))
    if actual != expected:
        print(f"✗ ключ не совпадает с эталоном: {actual} ≠ {expected}")
        return 1
    print(f"✓ ключ подписи совпадает с эталоном ({actual})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require", action="store_true", help="fail instead of skipping when tools/files are missing")
    parser.add_argument("--apk", default=str(DEFAULT_APK))
    parser.add_argument("--expected", default=str(EXPECTED))
    parser.add_argument("--tool", default=None, help="путь к apksigner")
    parser.add_argument("--keystore", default=None,
                        help="проверить сам ключ (.p12), а не собранный APK")
    parser.add_argument("--keystore-password", default=None)
    args = parser.parse_args()

    if args.keystore:
        password = args.keystore_password
        if password is None:
            properties = pathlib.Path(args.keystore).with_name("keystore.properties")
            if properties.exists():
                for line in properties.read_text(encoding="utf-8").splitlines():
                    if line.strip().startswith("storePassword="):
                        password = line.split("=", 1)[1].strip()
        if not password:
            print("· подписи: пароль ключа не задан — пропускаю")
            return 1 if args.require else 0
        return check_keystore(pathlib.Path(args.expected), pathlib.Path(args.keystore), password, args.require)

    apk = pathlib.Path(args.apk)
    expected_file = pathlib.Path(args.expected)
    if not apk.exists():
        print(f"· подписи: {apk} нет — проверять нечего")
        return 1 if args.require else 0
    if not expected_file.exists():
        print(f"· подписи: нет эталона {expected_file} — пропускаю")
        return 1 if args.require else 0

    tool = find_apksigner(args.tool)
    if tool is None:
        print("· подписи: apksigner не найден (в CI он берётся из Android SDK)")
        return 1 if args.require or args.tool else 0

    output = subprocess.run([tool, "verify", "--print-certs", str(apk)],
                            capture_output=True, text=True, check=False)
    text = output.stdout + output.stderr
    if output.returncode != 0:
        print("✗ APK не прошёл apksigner verify")
        print(text.strip()[:800])
        return 1
    digests = {normalize(match) for match in DIGEST.findall(text)}
    expected = normalize(expected_file.read_text(encoding="utf-8"))

    if not digests:
        print("✗ не удалось прочитать сертификат APK")
        print(text.strip()[:800])
        return 1
    if digests != {expected}:
        print(f"✗ APK подписан другим ключом: ожидался {expected}, получены {sorted(digests)}")
        print("  Обновление не установится поверх предыдущей версии!")
        return 1
    print(f"✓ подпись постоянным ключом подтверждена ({expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
