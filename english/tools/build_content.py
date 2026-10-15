#!/usr/bin/env python3
"""english/tools/build_content.py — единственный конвейер контента английского.

    content_src/*.py  ──►  english/dist/content/*.json  ──►  Android assets
                                                        └─►  Windows web
                                                        └─►  strings.xml Android

Сборка падает, а не «предупреждает», если:

1. **Задание не проверяется нормативной политикой** (``content_src/policy.py``):
   каждый допустимый ответ принимается, пустой ввод даёт причину ``empty``,
   у авторского задания-выбора пять уникальных вариантов; у архива —
   исходные 3/4/5 номеров и полная распознанная подпись каждого; первый — верный
   в каноническом банке (архивный UI показывает исходный порядок номеров).
2. **Тема не покрыта**: у каждой из 13 областей программы есть задания и в
   тренировочном банке, и среди однотипных, и карточка в справочнике «Правила».
3. **Справочник и уроки расходятся**: каждая ссылка «правило → урок» и
   «урок → схема» существует, каждая схема достижима, теги заданий описаны в
   «типичных ошибках».
4. **Строки интерфейса**: ключ, который использует ``webapp/*.js``, обязан быть
   в ``ui_strings.py``; у ключей ``*_fmt`` число подстановок совпадает в ru и en.
5. **Векторы ответа**: каждый авторский вектор обязан совпасть с реализацией —
   и принятие, и причина отказа.
6. **Чужой предмет**: в заданиях и надписях нет названий математики и физики —
   это английский тренажёр, а не переименованное соседнее приложение.

Использование::

    python3 english/tools/build_content.py            # собрать и проверить
    python3 english/tools/build_content.py --check    # только проверить (CI)
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUBJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = SUBJECT_ROOT / "content_src"
DIST = SUBJECT_ROOT / "dist" / "content"
VERSION_FILE = SUBJECT_ROOT / "VERSION"
WEBAPP = SUBJECT_ROOT / "webapp"

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SUBJECT_ROOT / "tools"))

import subject  # noqa: E402  (профиль предмета: CT_SUBJECT)
import periods  # noqa: E402
import policy  # noqa: E402

#: Признаки чужого приложения. Проверяются **идентичность и оформление**, а не
#: предложения упражнений: в английском задании законно встретить «She is good at
#: mathematics» или «Physics is a difficult subject» — это содержание предмета
#: «английский язык», а не переименованная математика. Поэтому скан идёт по
#: надписям интерфейса, названиям и формулировкам справочника и по инструкциям
#: заданий, где чужой продукт действительно был бы ошибкой.
FOREIGN_WORDS = ("репетитор цт: физика", "репетитор цт: математика",
                 "репетитор цт: русский", "ctphysicstutor", "ctmathstutor",
                 "ctrussiantutor", "ctphysics", "ctmaths", "by.ziv.ctphysics",
                 "by.ziv.ctmaths", "физика", "математика")

#: ключи, которые обязаны быть в ui_strings: их использует интерфейс
REQUIRED_UI_KEYS = (
    "app_name", "app_tagline", "about_text", "disclaimer", "language_note",
    "home", "back", "next", "check", "train", "exam", "rules", "mistakes", "study",
    "statistics", "settings", "topics", "exam_rules_fmt", "variant_note", "part_a",
    "part_b", "score_fmt", "score_parts_fmt", "answer_hint", "answer_word_hint",
    "correction_title", "rule_open", "reason_ok", "reason_empty", "reason_case",
    "reason_article", "reason_apostrophe", "reason_hyphen", "reason_space",
    "reason_stress", "reason_near", "reason_exact", "expected_fmt", "analogous", "analogous_hint", "checklist",
    "periods_note_fmt", "study_example", "type_choice", "type_gap", "type_form",
    "type_extra", "type_translate", "given_word", "accepted_forms_fmt",
    "policy_title", "policy_case_insensitive", "policy_article_ignore",
    "policy_apostrophe_ignore", "policy_hyphen_significant", "policy_exact",
)


def load(name: str):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:
        if error.name == name:
            return None
        raise


def check_ui_strings() -> dict:
    module = load("ui_strings")
    if module is None:
        raise SystemExit("нет content_src/ui_strings.py")
    strings = module.STRINGS
    problems = []
    seen_keys = []
    for key, value in strings.items():
        if set(value) != {"ru", "en"}:
            problems.append(f"строка {key}: нужны ровно 'ru' и 'en'")
            continue
        for lang, text in value.items():
            if not str(text).strip():
                problems.append(f"строка {key} ({lang}): пустая")
        if key.endswith("_fmt"):
            ru, en = value["ru"].count("%s"), value["en"].count("%s")
            if ru != en:
                problems.append(f"строка {key}: %s в ru и en не совпадает ({ru} ≠ {en})")
        seen_keys.append(key)
    # каждая надпись, которую просит интерфейс, обязана существовать
    used = set()
    for path in sorted(WEBAPP.glob("*.js")):
        text = path.read_text(encoding="utf-8")
        used.update(re.findall(r"\bt\(\s*'([a-z0-9_]+)'", text))
        used.update(re.findall(r"\bt\(\s*\"([a-z0-9_]+)\"", text))
    missing = sorted(used - set(strings))
    if missing:
        problems.append("ключи, которых требует интерфейс: " + ", ".join(missing))
    for key in REQUIRED_UI_KEYS:
        if key not in strings:
            problems.append(f"нет обязательной надписи {key}")
    unused = sorted(set(strings) - used)
    if problems:
        raise SystemExit("Строки интерфейса:\n  - " + "\n  - ".join(problems))
    if unused:
        print(f"  · надписи без использования в интерфейсе (допустимо): {len(unused)}")
    return strings


def check_diagrams() -> dict:
    module = load("diagrams")
    if module is None:
        raise SystemExit("нет content_src/diagrams.py")
    figures = module.figures()
    lessons = load("lessons").lessons()
    problems = []
    referenced = set()
    for lesson in lessons.values():
        figure = lesson.get("figure")
        if figure:
            if figure not in figures:
                problems.append(f"урок {lesson['id']}: схема {figure} не существует")
            referenced.add(figure)
    unreachable = sorted(set(figures) - referenced)
    if unreachable:
        problems.append("схемы, на которые никто не ссылается: " + ", ".join(unreachable))
    for figure in figures.values():
        if len(figure["nodes"]) < 2 or not figure["edges"]:
            problems.append(f"схема {figure['id']}: нужны минимум два узла и связи")
        for node in figure["nodes"]:
            if node["x"] + node["w"] > figure["width"] or node["y"] + node["h"] > figure["height"]:
                problems.append(f"схема {figure['id']}: узел {node['id']} выходит за границы")
    if problems:
        raise SystemExit("Схемы:\n  - " + "\n  - ".join(problems))
    return figures


def uncovered_groups(rules: dict, lessons: dict) -> list[str]:
    """Разделы справочника, у которых нет урока со ссылкой на одну из карточек.

    Урок ссылается на **карточку** правила (``item.id``), а не на раздел: в
    разделе может быть несколько карточек, и урок описывает ту, которая важнее
    для темы.
    """
    covered = {lesson["rule"] for lesson in lessons.values()}
    return [group["id"] for group in rules["groups"]
            if not covered & {item["id"] for item in group["items"]}]


def check_references(rules: dict, lessons: dict, mistakes: dict, bank: list, analogous: list) -> None:
    problems = []
    for group in uncovered_groups(rules, lessons):
        problems.append(f"раздел {group}: нет урока, ссылающегося на его карточку")
    for task in [*bank, *analogous]:
        rule_id = task["rule"]
        if rule_id not in {group["rule"] for group in rules["groups"]}:
            problems.append(f"задание {task['id']}: правило {rule_id!r} отсутствует в справочнике")
        for tag in task["tags"]:
            if tag not in mistakes["errors"]:
                problems.append(f"задание {task['id']}: тег {tag!r} не описан в типичных ошибках")
    for tag, entry in mistakes["errors"].items():
        if tag.startswith("__"):
            continue
        if entry["rule"] not in {item["id"] for group in rules["groups"] for item in group["items"]}:
            problems.append(f"диагноз {tag}: правило {entry['rule']!r} отсутствует")
    if problems:
        raise SystemExit("Ссылки:\n  - " + "\n  - ".join(problems))


def check_foreign_words(bank: list, analogous: list, lessons: dict, rules: dict, ui: dict) -> None:
    """Оформление принадлежит английскому тренажёру, а не соседнему приложению."""
    texts = [task["instruction"]["ru"] for task in [*bank, *analogous]]
    for lesson in lessons.values():
        texts.append(lesson["title"]["ru"])
        texts.append(lesson["summary"]["ru"])
    for group in rules["groups"]:
        texts.append(group["title"]["ru"])
        for item in group["items"]:
            texts.append(item["title"]["ru"])
            texts.append(item["formulation"]["ru"])
    for entry in mistakes_errors(ui):
        texts.append(entry)
    texts.extend(value["ru"] for value in ui.values())
    lowered = "\n".join(texts).lower()
    hits = [word for word in FOREIGN_WORDS if word in lowered]
    if hits:
        raise SystemExit("Чужой предмет в оформлении: " + ", ".join(sorted(hits)))


def mistakes_errors(ui: dict) -> list[str]:
    """Названия диагнозов и подсказок — тоже оформление приложения."""
    module = load("mistakes")
    payload = module.payload()
    texts = [payload["errors"][tag]["title"]["ru"] for tag in payload["errors"]]
    texts += [item["ru"] for item in payload["checklist"]]
    return texts


def check_vectors(strings: dict) -> dict:
    module = load("vectors")
    if module is None:
        raise SystemExit("нет content_src/vectors.py")
    cases = []
    problems = []
    for case in module.cases():
        task = {"id": case["id"], "answer": {"value": case["answer"]},
                "policy": dict(policy.DEFAULT_POLICY, **(case.get("policy") or {}))}
        if case.get("accepted"):
            task["accepted"] = list(case["accepted"])
        result = policy.check(task, case["typed"])
        if result["ok"] != case["expect"] or result["reason"] != case["reason"]:
            problems.append(f"вектор {case['id']}: ожидалось {case['expect']}/{case['reason']}, "
                            f"получено {result['ok']}/{result['reason']}")
        cases.append({"id": case["id"], "task": task, "typed": case["typed"],
                      "expect": case["expect"], "reason": case["reason"],
                      "note": case.get("note")})
    if problems:
        raise SystemExit("Векторы ответа:\n  - " + "\n  - ".join(problems))
    return {"schema": 1, "subject": subject.SUBJECT, "cases": cases}


def task_cases(bank: list, analogous: list) -> list[dict]:
    """Векторы, вытекающие из самих заданий: ответ, его формы и отказы.

    Ожидания берутся у реализации (``policy.check``), а не выписываются руками:
    задание, где ответ — «ничего не нужно» (``empty: accept``), честно принимает
    пустое поле, и вектор обязан это повторить.  При этом сборка **требует**,
    чтобы у каждого задания с выбором был хотя бы один отвергаемый вариант, а у
    задания с вводом — отвергаемая порча ответа: иначе задания нечего проверять.
    """
    cases = []
    for task in [*bank, *analogous]:
        cases.append({"id": f"task-{task['id']}", "task": task, "typed": task["answer"]["value"],
                      "expect": True, "reason": "ok", "note": None})
        for accepted in task["accepted"]:
            if accepted == task["answer"]["value"]:
                continue
            cases.append({"id": f"task-{task['id']}-alt", "task": task, "typed": accepted,
                          "expect": True, "reason": "ok", "note": None})

        empty = policy.check(task, "   ")
        cases.append({"id": f"task-{task['id']}-empty", "task": task, "typed": "   ",
                      "expect": empty["ok"], "reason": empty["reason"], "note": None})

        decoys = [option for option in (task.get("options") or [])
                  if option != task["answer"]["value"]]
        if task["type"] != "choice":
            decoys = [task["answer"]["value"] + "s", "zz" + task["answer"]["value"]]
        rejected = [option for option in decoys if not policy.check(task, option)["ok"]]
        if not rejected:
            raise SystemExit(f"задание {task['id']}: ни один вариант-обманка не отвергается")
        wrong = rejected[0]
        cases.append({"id": f"task-{task['id']}-wrong", "task": task, "typed": wrong,
                      "expect": False, "reason": policy.check(task, wrong)["reason"], "note": None})
    return cases


def android_strings_xml(strings: dict, lang: str) -> str:
    """values/strings.xml для Android: только те надписи, что нужны оболочке."""
    keys = ("app_name", "app_tagline", "disclaimer")
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             "<!-- сгенерировано english/tools/build_content.py: правьте content_src/ui_strings.py -->",
             "<resources>"]
    for key in keys:
        value = (strings[key][lang].replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace("'", "\\'").replace('"', '\\"'))
        lines.append(f'    <string name="{key}">{value}</string>')
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="проверить, ничего не записывая")
    args = parser.parse_args()

    print(f"Конвейер контента английского (subject={subject.SUBJECT})")
    if not VERSION_FILE.exists():
        raise SystemExit("нет english/VERSION — нечего публиковать")
    content_version = VERSION_FILE.read_text(encoding="utf-8").strip()

    kit = load("kit")
    pools = load("pools")
    bank_modules = [load(name) for name in periods.modules()]
    rules = load("rules").groups()
    lessons = load("lessons").lessons()
    mistakes = load("mistakes").payload()
    ui = check_ui_strings()
    figures = check_diagrams()

    archive = load("archives").payload()
    bank = [*pools.bank_practice(),
            *(task for module in bank_modules for task in module.tasks()), *archive["tasks"]]
    periods.validate_variants(bank)
    analogous = pools.analogous()

    problems = []
    for task in [*bank, *analogous]:
        problems.extend(f"{task['id']}: {issue}" for issue in kit.verify(task))
    if problems:
        raise SystemExit("Проверка заданий:\n  - " + "\n  - " + "\n  - ".join(problems))

    check_references(rules, lessons, mistakes, bank, analogous)
    check_foreign_words(bank, analogous, lessons, rules, ui)

    vectors = check_vectors(ui)
    vectors["cases"].extend(task_cases(bank, analogous))

    # покрытие: у каждой темы есть банк, однотипные задания, правило и урок
    coverage = {}
    for task in [*bank, *analogous]:
        entry = coverage.setdefault(task["topic"], {"bank": 0, "analogous": 0})
        entry["bank" if task in bank else "analogous"] += 1
    uncovered = [topic for topic in kit.TOPIC_ORDER
                 if coverage.get(topic, {}).get("bank", 0) == 0]
    if uncovered:
        raise SystemExit("Темы без заданий: " + ", ".join(uncovered))
    missing_lessons = uncovered_groups(rules, lessons)
    if missing_lessons:
        raise SystemExit("у разделов нет уроков: " + ", ".join(missing_lessons))

    counts = {}
    by_year = {}
    for task in bank:
        counts[task["topic"]] = counts.get(task["topic"], 0) + 1
        if task.get("year"):
            by_year[str(task["year"])] = by_year.get(str(task["year"]), 0) + 1
    for task in analogous:
        counts[task["topic"]] = counts.get(task["topic"], 0) + 1

    meta = {
        "contentVersion": content_version,
        "schema": 1,
        "subject": subject.SUBJECT,
        "package": subject.ANDROID_PACKAGE,
        "app": subject.WINDOWS_BINARY,
        "years": sorted({task["year"] for task in bank if task.get("year")}),
        "counts": {
            "bank": len(bank),
            "practice": len(pools.bank_practice()),
            "authored": len(bank) - len(archive["tasks"]),
            "archive": len(archive["tasks"]),
            "archiveVariants": len(archive["variants"]),
            "analogous": len(analogous),
            "choice": sum(1 for task in bank if task["type"] == "choice"),
            "typed": sum(1 for task in bank if task["type"] != "choice"),
            "lessons": len(lessons),
            "rules": len(rules["groups"]),
            "figures": len(figures),
            "topics": len(kit.TOPIC_ORDER),
        },
        "parts": dict(periods.PARTS),
        "minutes": periods.MINUTES,
        "author": "Zakharevich Igor",
        "repo": "https://github.com/zigorminsk-debug/mathematics",
        "disclosure": periods.DISCLAIMER,
        "structureSource": periods.SOURCE,
    }

    topics = {
        "topics": kit.TOPICS,
        "order": list(kit.TOPIC_ORDER),
        "tools": kit.TOOLS,
        "types": kit.TYPES,
        "instructions": kit.INSTRUCTIONS,
        "counts": counts,
        "byYear": by_year,
        "lessons": lessons,
        "figures": figures,
        "rules": rules,
        "checklist": mistakes["checklist"],
        "archiveVariants": archive["variants"],
        "periods": {"released": list(periods.RELEASED_PERIODS),
                    "planned": list(periods.PLANNED_PERIODS)},
        "generators": {topic: kit.generator_count(topic) for topic in kit.TOPIC_ORDER},
    }

    print(f"  · заданий: {len(bank)} в банке ({len(pools.bank_practice())} тренировка + "
          f"{len(bank) - len(pools.bank_practice()) - len(archive['tasks'])} авторские варианты + {len(archive['tasks'])} архив), {len(analogous)} однотипных")
    print(f"  · разделов: {len(rules['groups'])}, уроков: {len(lessons)}, схем: {len(figures)}, "
          f"диагнозов: {len(mistakes['errors']) - 1}, векторов: {len(vectors['cases'])}")

    if args.check:
        print("режим --check: файлы не записаны")
        return 0

    write_json(DIST / "bank.json", {"meta": meta, "tasks": bank, "sourcePages": archive["sourcePages"]})
    write_json(DIST / "analogous.json", {"meta": meta, "tasks": analogous})
    write_json(DIST / "topics.json", topics)
    write_json(DIST / "rules.json", rules)
    write_json(DIST / "mistakes.json", mistakes)
    write_json(DIST / "ui_strings.json", {"strings": ui, "meta": meta})
    write_json(DIST / "answer_vectors.json", vectors)

    version = {
        **meta,
        "updatePolicy": "subject-scoped releases API; no global /latest/download",
        "baseUrl": subject.content_base_url("zigorminsk-debug/mathematics", content_version),
        "periods": {"released": list(periods.RELEASED_PERIODS),
                    "planned": list(periods.PLANNED_PERIODS)},
        "files": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
                  for path in sorted(DIST.glob("*.json")) if path.name != "version.json"},
    }
    write_json(DIST / "version.json", version)

    # копии в приложения (то же делает tools/sync_assets.py для webapp)
    for target in (SUBJECT_ROOT / "android" / "app" / "src" / "main" / "assets" / "content",
                   SUBJECT_ROOT / "windows" / "web" / "content"):
        if target.parent.exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(DIST, target)
            print(f"    → {target.relative_to(SUBJECT_ROOT)}/")
        else:
            print(f"    · пропущено {target.relative_to(SUBJECT_ROOT)} (приложение ещё не собрано)")

    # строки Android
    for lang, folder in (("ru", "values-ru"), ("en", "values")):
        path = SUBJECT_ROOT / "android" / "app" / "src" / "main" / "res" / folder / "strings.xml"
        if path.parent.exists():
            path.write_text(android_strings_xml(ui, lang), encoding="utf-8")
            print(f"    → {path.relative_to(SUBJECT_ROOT)}")

    print("Готово.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
