#!/usr/bin/env python3
"""Explicit subject configuration shared by every build/release tool.

The subject of this branch is read from ``subject.json`` — never guessed from a
branch name such as ``arena/...``. All release identities derive from it:
tag family, Android package, Windows binary names, inventory and manifest
fields. Tests assert that the YAML workflows use the same identities.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "subject.json"


def load(path: Path = CONFIG_FILE) -> dict:
    config = json.loads(path.read_text(encoding="utf-8"))
    validate(config)
    return config


def validate(config: dict) -> dict:
    if config.get("schema") != 1:
        raise ValueError("subject.json: unsupported schema")
    subject = config.get("subject")
    if not isinstance(subject, str) or not re.fullmatch(r"[a-z]{3,20}", subject):
        raise ValueError("subject.json: invalid subject id")
    prefix = config.get("tagPrefix")
    if prefix != f"{subject}-v":
        raise ValueError("subject.json: tag family must be '<subject>-v' so it never matches another family")
    android = config.get("android", {})
    package = android.get("applicationId", "")
    if not re.fullmatch(r"by\.ziv\.ct[a-z]+", package):
        raise ValueError("subject.json: invalid Android package")
    if android.get("debugApplicationId") != package + ".debug":
        raise ValueError("subject.json: debug package must be '<package>.debug'")
    release = config.get("release", {})
    if release.get("makeLatest") is not False:
        raise ValueError("subject.json: a subject release must never become the repository latest")
    if package in release.get("foreignPackages", []) or prefix in release.get("foreignTagPrefixes", []):
        raise ValueError("subject.json: own identity listed as foreign")
    stem = config.get("windows", {}).get("binaryStem", "")
    if not re.fullmatch(r"CT[A-Z][a-zA-Z]+Tutor", stem):
        raise ValueError("subject.json: invalid Windows binary stem")
    if not isinstance(config.get("contentProtocol"), int) or config["contentProtocol"] < 2:
        raise ValueError("subject.json: contentProtocol must be an integer >= 2")
    return config


CONFIG = load()
SUBJECT = CONFIG["subject"]
TAG_PREFIX = CONFIG["tagPrefix"]
PACKAGE = CONFIG["android"]["applicationId"]
DEBUG_PACKAGE = CONFIG["android"]["debugApplicationId"]
STEM = CONFIG["windows"]["binaryStem"]
REPOSITORY = CONFIG["repository"]
CONTENT_PROTOCOL = CONFIG["contentProtocol"]
PIPELINE_LOCK = CONFIG["release"]["pipelineLock"]
TITLE = CONFIG["title"]
WINDOWS_EXES = (f"{STEM}-amd64.exe", f"{STEM}-arm64.exe")
KEYSTORE = ROOT / CONFIG["android"]["keystore"]
CERTIFICATE_FILE = ROOT / CONFIG["android"]["certificateSha256File"]
