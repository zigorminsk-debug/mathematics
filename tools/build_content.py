#!/usr/bin/env python3
"""tools/build_content.py — the single content pipeline of the project.

    content_src/*.py  ──►  dist/content/*.json  ──►  Android assets
                                                └─►  Windows embedded web app
                                                └─►  generated Android strings.xml

Steps
-----
1. import every authoring module (``task_bank_2021``…``task_bank_2025``,
   ``templates``, ``templates_extra``, …);
2. run the exact-arithmetic ``check()`` of **every** item — the build fails if a
   single answer is wrong, a task has no solution, or part A is malformed;
3. serialise language-neutral banks (ru + en side by side);
4. write update manifests (version + SHA-256) used by the in-app updater of both
   platforms to download newer banks on top of the installed one;
5. copy everything into the Android asset folder and the Windows web folder.

Usage::

    python3 tools/build_content.py            # build + verify
    python3 tools/build_content.py --check    # verify only (used by CI)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content_src"
DIST = ROOT / "dist" / "content"

sys.path.insert(0, str(SRC))

import periods  # noqa: E402  (лежит рядом, подключается после sys.path)

YEAR_MODULES = periods.modules()
EXTRA_MODULES = ["templates", "templates_extra", "formulas", "ui_strings", "mistakes"]

CONTENT_VERSION_FILE = ROOT / "VERSION"


def load(mod: str):
    try:
        return importlib.import_module(mod)
    except ModuleNotFoundError as exc:
        if exc.name == mod:
            return None
        raise


def collect_tasks() -> tuple[list, list]:
    """Return (bank_tasks, analogous_tasks) as serialised dicts, fully verified."""
    bank, analogous = [], []
    seen_ids: set[str] = set()
    total_checks = 0

    for name in YEAR_MODULES:
        mod = load(name)
        if mod is None:
            print(f"  · {name}: not present yet (skipped)")
            continue
        tasks = mod.tasks()
        for t in tasks:
            t.verify()
            total_checks += 1
            if t.id in seen_ids:
                raise SystemExit(f"duplicate task id: {t.id}")
            seen_ids.add(t.id)
            bank.append(t.to_json())
        print(f"  · {name}: {len(tasks)} items verified")

    tmod = load("templates")
    if tmod is not None:
        items = list(tmod.generate())
        emod = load("templates_extra")
        if emod is not None:
            items += list(emod.generate_extra())
        seen_text = set()
        unique = []
        for t in items:
            key = (t.topic, t.ru.strip(), t.en.strip())
            if key in seen_text:
                continue
            seen_text.add(key)
            unique.append(t)
        items = unique
        for t in items:
            t.verify()
            total_checks += 1
            if t.id in seen_ids:
                raise SystemExit(f"duplicate task id: {t.id}")
            seen_ids.add(t.id)
            analogous.append(t.to_json())
        print(f"  · templates: {len(items)} analogous items verified")

    print(f"  ✓ {total_checks} exact-arithmetic checks passed")
    missing = [year for year in periods.years() if not (SRC / f"task_bank_{year}.py").exists()]
    if missing:
        # periods.py — единственный источник правды: год без модуля означает, что в
        # манифест попал вариант, которого нет в банке
        raise SystemExit("нет модулей для периодов: " + ", ".join(str(year) for year in missing))
    return bank, analogous


def build_topics() -> dict:
    from kit import TOPICS, TOPIC_ORDER, TOOLS
    counts: dict[str, int] = {}
    by_year: dict[str, int] = {}
    return {"topics": TOPICS, "order": TOPIC_ORDER, "tools": TOOLS,
            "counts": counts, "byYear": by_year}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False),
                    encoding="utf-8")
    print(f"    → {path.relative_to(ROOT)}  ({path.stat().st_size / 1024:.0f} KiB)")


def android_strings_xml(strings: dict, lang: str) -> str:
    """Render the shared string catalogue as Android resources.

    Keys ending in ``_fmt`` keep their ``%s`` placeholder: it is rewritten to the
    positional form ``%1$s`` and the escape of ``%`` is skipped for them.
    """
    def esc(s: str, fmt: bool) -> str:
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = s.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
        if fmt:
            counter = 0

            def number_argument(_match):
                nonlocal counter
                counter += 1
                return "%%%d$s" % counter

            s = re.sub(r"%s", number_argument, s)
        else:
            s = s.replace("%", "%%")
        return s

    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- GENERATED by tools/build_content.py from content_src/ui_strings.py - do not edit -->',
             '<resources>']
    for key in sorted(strings):
        entry = strings[key]
        val = entry.get(lang) or entry.get("en") or entry.get("ru") or ""
        fmt = key.endswith("_fmt")
        lines.append('    <string name="%s">%s</string>' % (key, esc(val, fmt)))
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the bank without writing any file")
    args = ap.parse_args()

    print("Content pipeline")
    bank, analogous = collect_tasks()
    if not bank and not analogous:
        print("nothing to build — authoring modules are missing", file=sys.stderr)
        return 1

    # Отметки времени в самом банке нет: файлы заданий обязаны собираться
    # байт в байт одинаково (иначе проверка «копии не разъехались» зависела бы от
    # момента запуска).  Время сборки живёт только в манифесте version.json и
    # берётся из SOURCE_DATE_EPOCH — так делает CI (время коммита).
    built = datetime.fromtimestamp(
        int(os.environ.get("SOURCE_DATE_EPOCH", time.time())), timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {
        "contentVersion": CONTENT_VERSION_FILE.read_text(encoding="utf-8").strip()
        if CONTENT_VERSION_FILE.exists() else "1.0.0",
        "schema": 1,
        "years": sorted({t["year"] for t in bank if t["year"]}),
        "counts": {
            "bank": len(bank),
            "analogous": len(analogous),
            "choice": sum(1 for t in bank if t["answerType"] == "choice"),
            "short": sum(1 for t in bank if t["answerType"] == "short"),
        },
        "author": "Zakharevich Igor",
        "email": "ziv@csl.by",
        "phone": "+3753371412",
        "repo": "https://github.com/zigorminsk-debug/mathematics",
    }

    topics = build_topics()
    for t in bank:
        topics["counts"][t["topic"]] = topics["counts"].get(t["topic"], 0) + 1
        if t["year"]:
            topics["byYear"][str(t["year"])] = topics["byYear"].get(str(t["year"]), 0) + 1
    for t in analogous:
        topics["counts"][t["topic"]] = topics["counts"].get(t["topic"], 0) + 1

    fmod = load("formulas")
    formulas = fmod.groups() if fmod else {"groups": []}
    umod = load("ui_strings")
    ui = umod.STRINGS if umod else {}
    mmod = load("mistakes")
    mistake_help = mmod.payload() if mmod else {"errors": {}, "checklist": []}

    from kit import ANSWER_VECTORS, check_answer
    vectors = ANSWER_VECTORS or default_vectors()
    for index, vector in enumerate(vectors):
        graded = check_answer(vector["user"], {"accept": vector["accept"],
                                               "answerType": vector.get("answerType", "short")})
        if graded != bool(vector["expect"]):
            raise SystemExit(f"answer vector #{index} ({vector['user']!r} vs {vector['accept']}) "
                             f"graded {graded}, expected {vector['expect']}")
    print(f"  ✓ {len(vectors)} answer vectors graded by the Python implementation")

    if args.check:
        print("check-only mode: no files written")
        return 0

    print("Writing banks")
    write_json(DIST / "bank.json", {"meta": meta, "tasks": bank})
    write_json(DIST / "analogous.json", {"meta": meta, "tasks": analogous})
    write_json(DIST / "topics.json", topics)
    write_json(DIST / "formulas.json", formulas)
    write_json(DIST / "ui_strings.json", {"strings": ui, "meta": meta})
    write_json(DIST / "answer_vectors.json", {"cases": vectors})
    write_json(DIST / "mistakes.json", mistake_help)

    version = {
        **meta,
        "built": built,
        **periods.payload(),
        "files": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
                  for p in sorted(DIST.glob("*.json")) if p.name != "version.json"},
        "baseUrl": "https://github.com/zigorminsk-debug/mathematics/releases/latest/download",
    }
    write_json(DIST / "version.json", version)

    print("Copying into the applications")
    targets = [
        (ROOT / "android" / "app" / "src" / "main" / "assets" / "content", DIST),
        (ROOT / "windows" / "web" / "content", DIST),
    ]
    for dst, src in targets:
        if not dst.parent.exists():
            print(f"    · skipped {dst.relative_to(ROOT)} (app not scaffolded yet)")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"    → {dst.relative_to(ROOT)}/")

    if ui:
        print("Generating Android string resources")
        for lang, folder in (("en", "values"), ("ru", "values-ru")):
            out = ROOT / "android" / "app" / "src" / "main" / "res" / folder / "strings.xml"
            if out.parent.parent.exists():
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(android_strings_xml(ui, lang), encoding="utf-8")
                print(f"    → {out.relative_to(ROOT)}")

    print("Done.")
    return 0


def default_vectors() -> list[dict]:
    """The shared contract of the portable answer checker.

    Every row is graded by **all three implementations** — Python
    (:func:`kit.check_answer`), JavaScript (``webapp/core.js`` → ``CT.answer``,
    checked by ``tests/answer_parity.js``) and Kotlin (``AnswerChecker.kt``,
    checked by ``AnswerCheckerTest.kt``) — and the builds fail when any of them
    disagrees.  Four tiers are covered: canonical string match, choice tasks
    (never graded numerically), exact numbers with a rounding band for
    fractions, and expressions with roots or π that at least one side wrote as an
    expression.
    """
    return [
        # 1. каноническая строка / canonical string forms
        {"user": "  − 7 ", "accept": ["-7"], "answerType": "short", "expect": True},
        {"user": "X = 12", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "х = 12", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "ответ: 12", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "(12)", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "1 000", "accept": ["1000"], "answerType": "short", "expect": True},
        {"user": "-1/3", "accept": ["−1/3"], "answerType": "short", "expect": True},
        {"user": "6√2", "accept": ["6√2"], "answerType": "short", "expect": True},
        {"user": "6√2", "accept": ["6√3"], "answerType": "short", "expect": False},
        {"user": "", "accept": ["4"], "answerType": "short", "expect": False},

        # 2. выбор варианта: «повезло с числом» — не ответ
        {"user": "4", "accept": ["4"], "answerType": "choice", "expect": True},
        {"user": "3", "accept": ["4"], "answerType": "choice", "expect": False},
        {"user": "8/2", "accept": ["4"], "answerType": "choice", "expect": False},

        # 3. точные числа и округления, написанные рукой
        {"user": "0,8", "accept": ["4/5"], "answerType": "short", "expect": True},
        {"user": "0.80", "accept": ["4/5"], "answerType": "short", "expect": True},
        {"user": "8/10", "accept": ["0,8"], "answerType": "short", "expect": True},
        {"user": "12,0", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "12.", "accept": ["12"], "answerType": "short", "expect": True},
        {"user": "2,5", "accept": ["5/2"], "answerType": "short", "expect": True},
        {"user": "2,51", "accept": ["5/2"], "answerType": "short", "expect": False},
        {"user": "0,833", "accept": ["5/6"], "answerType": "short", "expect": True},
        {"user": "0,8", "accept": ["5/6"], "answerType": "short", "expect": False},
        {"user": "0,333", "accept": ["1/3"], "answerType": "short", "expect": True},
        {"user": "0,33", "accept": ["1/3"], "answerType": "short", "expect": False},
        {"user": "1000,5", "accept": ["1000"], "answerType": "short", "expect": False},

        # 4. ответы, записанные выражением (корни, π)
        {"user": "0,707", "accept": ["√2/2"], "answerType": "short", "expect": True},
        {"user": "0,7", "accept": ["√2/2"], "answerType": "short", "expect": False},
        {"user": "√2/2", "accept": ["0,707"], "answerType": "short", "expect": True},
        {"user": "6,28", "accept": ["2π"], "answerType": "short", "expect": True},
        {"user": "8,49", "accept": ["6√2"], "answerType": "short", "expect": True},
    ]


if __name__ == "__main__":
    raise SystemExit(main())
