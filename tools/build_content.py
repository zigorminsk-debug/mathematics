#!/usr/bin/env python3
"""tools/build_content.py — the single content pipeline of the Russian tutor.

    content_src/*.py ──► dist/content/*.json ──► Android assets / Windows web
                                              └─► generated Android strings.xml

Gates (the build fails on any of them):
  * every task passes kit.validate_task (explicit check contract, bilingual
    instruction/solution, Russian material never translated, canonical answer
    accepted by the reference checker);
  * each authored variant follows the 40-slot blueprint and the 2026 RIKZ
    section quotas (13/9/2/3/1/2/4/3/3) and difficulty distribution;
  * every rule has a card, a study link, a «Правила» entry and >= 3 analogs;
  * every string is NFC and free of invisible/bidi/control characters;
  * the answer-vector corpus is graded exactly as expected by Python.

Usage:  python3 tools/build_content.py [--check]
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content_src"
DIST = ROOT / "dist" / "content"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "tools"))

import checker  # noqa: E402
import diagrams  # noqa: E402
import generate  # noqa: E402
import kit  # noqa: E402
import mistakes  # noqa: E402
import periods  # noqa: E402
import rules  # noqa: E402
import sources  # noqa: E402
import subject  # noqa: E402
import texts  # noqa: E402
import ui_strings  # noqa: E402
import vectors  # noqa: E402

CONTENT_FILES = ("bank.json", "analogous.json", "topics.json", "rules.json", "ui_strings.json", "mistakes.json",
                 "answer_vectors.json")
FORBIDDEN = re.compile("[\u0000-\u0008\u000b-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
META = {"author": "Zakharevich Igor", "email": "ziv@csl.by", "phone": "+3753371412",
        "repo": f"https://github.com/{subject.REPOSITORY}"}


def fail(message: str):
    raise SystemExit("content error: " + message)


def scan_strings(value, where: str):
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            fail(f"{where}: string is not NFC: {value[:60]!r}")
        if FORBIDDEN.search(value):
            fail(f"{where}: invisible/control/bidi character in {value[:60]!r}")
    elif isinstance(value, dict):
        for key, item in value.items():
            scan_strings(item, f"{where}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_strings(item, f"{where}[{index}]")


def check_variants(bank: list[dict]):
    quotas = {key: count for key, (_, count) in kit.SECTIONS.items()}
    slots = [slot for slot, _ in kit.BLUEPRINT]
    if sum(quotas.values()) != 40 or len(slots) != 40:
        fail("blueprint must have 40 slots matching the 2026 quotas")
    for year in periods.years():
        tasks = [entry for entry in bank if entry.get("year") == year]
        got = [f"{entry['part']}{entry['n']}" for entry in tasks]
        if sorted(got) != sorted(slots):
            fail(f"variant {year} does not fill the 40-slot blueprint")
        if Counter(entry["section"] for entry in tasks) != Counter(quotas):
            fail(f"variant {year} breaks the RIKZ 2026 section quotas")
        if Counter(entry["part"] for entry in tasks) != Counter({"A": 18, "B": 22}):
            fail(f"variant {year} must have 18 A + 22 B tasks")
        levels = Counter(entry["level"] for entry in tasks)
        if levels != Counter({1: 4, 2: 10, 3: 16, 4: 6, 5: 4}):
            fail(f"variant {year} breaks the difficulty distribution I4/II10/III16/IV6/V4: {dict(levels)}")
        texts_used = {entry.get("text") for entry in tasks if entry["section"] == "text"}
        if len(texts_used) != 1:
            fail(f"variant {year}: the three text tasks must share one text")


def build_tasks():
    bank = generate.variants()
    analogous = generate.analogs()
    ids = [entry["id"] for entry in bank + analogous]
    if len(ids) != len(set(ids)):
        fail("duplicate task id")
    for entry in bank + analogous:
        kit.validate_task(entry)
    check_variants(bank)
    per_rule = Counter(entry["rule"] for entry in analogous)
    thin = [rule for rule in kit.RULES if per_rule[rule] < 3]
    if thin:
        fail(f"rules with fewer than 3 analogous exercises: {thin}")
    print(f"  ✓ {len(bank)} variant tasks (6 × 40) and {len(analogous)} analogous exercises verified")
    return bank, analogous


def build_topics(bank, analogous):
    figures = diagrams.validate(diagrams.payload())
    lessons = rules.lessons(diagrams.LESSON_FIGURES)
    for rid, lesson in lessons.items():
        for fid in lesson["figures"]:
            if fid not in figures:
                fail(f"lesson {rid} links a missing figure {fid}")
    study = rules.study()
    reachable = {rid for entry in study.values() for rid in entry["lessons"]}
    if reachable != set(lessons):
        fail("every rule card must be reachable from the study screen")
    counts = Counter(entry["topic"] for entry in bank + analogous)
    by_year = Counter(str(entry["year"]) for entry in bank)
    return {
        "subject": subject.SUBJECT,
        "topics": kit.AREAS, "order": kit.AREA_ORDER,
        "sections": {key: {"title": title, "tasks": count} for key, (title, count) in kit.SECTIONS.items()},
        "blueprint": [{"slot": slot, "section": section, "level": kit.LEVELS[slot]} for slot, section in kit.BLUEPRINT],
        "counts": dict(counts), "byYear": dict(by_year),
        "rules": {rid: {"topic": area, "title": kit.bi(ru, en)} for rid, (area, ru, en) in kit.RULES.items()},
        "study": study, "lessons": lessons, "figures": figures, "sources": sources.payload(),
        "memos": memos(),
        **periods.payload(),
    }


def memos():
    """Quick reference lists for the «Памятки» tool (Russian material + bilingual titles)."""
    return [
        {"id": "stress", "title": kit.bi("Ударения", "Stress"), "items": list(generate.PL.STRESS)},
        {"id": "pre-pri", "title": kit.bi("ПРЕ-/ПРИ- по словарю", "ПРЕ-/ПРИ- dictionary words"),
         "items": ["привередливый", "привилегия", "прихотливый", "пренебрегать", "президент", "премьера", "претензия"]},
        {"id": "conjugation", "title": kit.bi("Исключения спряжений", "Conjugation exceptions"),
         "items": ["гнать", "держать", "дышать", "слышать", "видеть", "обидеть", "ненавидеть", "зависеть", "вертеть",
                   "терпеть", "смотреть", "брить (I)", "стелить (I)"]},
        {"id": "n-nn", "title": kit.bi("Н/НН: исключения", "Н/НН exceptions"),
         "items": ["деревянный", "стеклянный", "оловянный", "ветреный", "нежданный", "негаданный", "невиданный",
                   "неслыханный", "желанный", "медленный", "священный", "смышлёный"]},
        {"id": "not-intro", "title": kit.bi("Не вводные слова", "Never parenthetical"),
         "items": ["вдруг", "вряд ли", "едва ли", "даже", "именно", "ведь", "будто бы", "как будто"]},
    ]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"    → {path.relative_to(ROOT)}  ({path.stat().st_size / 1024:.0f} KiB)")


def android_strings_xml(strings: dict, lang: str) -> str:
    def esc(value: str, fmt: bool) -> str:
        value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        value = value.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
        if fmt:
            counter = 0

            def number(_match):
                nonlocal counter
                counter += 1
                return "%%%d$s" % counter
            return re.sub(r"%s", number, value)
        return value.replace("%", "%%")

    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<!-- GENERATED by tools/build_content.py from content_src/ui_strings.py - do not edit -->', "<resources>"]
    for key in sorted(strings):
        out.append('    <string name="%s">%s</string>' % (key, esc(strings[key][lang], key.endswith("_fmt"))))
    out.append("</resources>")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify without writing files")
    args = parser.parse_args()
    print("Content pipeline (subject: %s)" % subject.SUBJECT)
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    bank, analogous = build_tasks()
    topics = build_topics(bank, analogous)
    reference = rules.reference()
    ui = ui_strings.payload()
    errors = mistakes.payload()
    corpus = vectors.payload()
    for case in corpus["cases"]:
        if case["check"].get("type") in checker.TYPES:
            checker.validate(case["check"])
        if checker.check(case["user"], case["check"]) != case["expect"]:
            fail(f"answer vector {case['id']} ({case['user']!r}) graded wrongly by Python")
    print(f"  ✓ {len(corpus['cases'])} answer vectors graded as expected by the Python reference checker")
    meta = {"subject": subject.SUBJECT, "package": subject.PACKAGE, "contentProtocol": subject.CONTENT_PROTOCOL,
            "contentVersion": version, "schema": 2, "years": periods.years(),
            "counts": {"bank": len(bank), "analogous": len(analogous), "rules": len(topics["lessons"]),
                       "figures": len(topics["figures"])}, **META}
    payloads = {
        "bank.json": {"meta": meta, "tasks": bank}, "analogous.json": {"meta": meta, "tasks": analogous},
        "topics.json": topics, "rules.json": reference, "ui_strings.json": {"strings": ui, "meta": meta},
        "mistakes.json": errors, "answer_vectors.json": corpus,
    }
    for name, payload in payloads.items():
        if name == "answer_vectors.json":
            # learner inputs in the corpus are deliberately non-NFC/invisible; the specs are not
            for case in payload["cases"]:
                scan_strings(case["check"], f"{name}.{case['id']}.check")
            continue
        scan_strings(payload, name)
    print("  ✓ every string is NFC and free of invisible/control characters")
    if args.check:
        print("check-only mode: no files written")
        return 0
    if DIST.exists():
        shutil.rmtree(DIST)
    print("Writing content")
    for name in CONTENT_FILES:
        write_json(DIST / name, payloads[name])
    manifest = {
        "schema": 2, "subject": subject.SUBJECT, "package": subject.PACKAGE, "contentProtocol": subject.CONTENT_PROTOCOL,
        "tagPrefix": subject.TAG_PREFIX, "contentVersion": version, "appVersion": version,
        "files": {name: {"sha256": sha256(DIST / name), "bytes": (DIST / name).stat().st_size} for name in CONTENT_FILES},
        "counts": meta["counts"], **periods.payload(),
    }
    write_json(DIST / "version.json", manifest)
    print("Generating Android string resources")
    for lang, folder in (("en", "values"), ("ru", "values-ru")):
        out = ROOT / "android" / "app" / "src" / "main" / "res" / folder / "strings.xml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(android_strings_xml(ui, lang), encoding="utf-8")
        print(f"    → {out.relative_to(ROOT)}")
    print("Done. Run tools/sync_assets.py to copy the content into both applications.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
