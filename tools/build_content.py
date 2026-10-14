#!/usr/bin/env python3
"""tools/build_content.py — единственный конвейер контента физики.

    content_src/*.py  ──►  dist/content/*.json  ──►  Android assets
                                                └─►  Windows web
                                                └─►  сгенерированный strings.xml

Что здесь проверяется (сборка падает, а не «предупреждает»)
----------------------------------------------------------
1. **Каждое задание** банка и генератора проходит ``Task.verify()``: ответ
   выводится из физической модели точной арифметикой, размерность формулы
   сходится, единицы данных и ответа совместимы, данные встречаются в тексте,
   у неверных вариантов части A есть объяснения типичных ошибок.
2. **Все шесть вариантов** 2021–2026 годов на месте: ``periods.py`` — источник
   правды о составе варианта.
3. **Теория**: у каждого урока есть определения, правила, разобранный пример,
   бытовое объяснение в двух абзацах и ссылки только на существующие схемы; ни
   одна схема не остаётся недостижимой.
4. **Конспекты и формулы**: у каждой темы есть конспект со ссылками на теорию и
   группы формул; каждая строка сборника формул ссылается на существующий урок.
5. **Покрытие тем**: каждая из 13 областей программы встречается и в варианте, и
   среди аналогичных заданий.
6. **Векторы ответов**: общий набор пограничных случаев (единицы, размерности,
   округление, °C, научная запись) обязан быть оценён ядром так, как записано.
7. **Строки интерфейса**: ключ, который использует ``webapp/*.js``, обязан быть в
   ``ui_strings.py``; у ключей ``*_fmt`` число подстановок совпадает в ru и en.
8. **Никаких математических остатков**: тексты заданий и надписи не содержат
   названий чужого предмета — это физика, а не переименованная математика.

Использование::

    python3 tools/build_content.py            # собрать и проверить
    python3 tools/build_content.py --check    # только проверить (CI)
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

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "content_src"
DIST = ROOT / "dist" / "content"
TOOLS = ROOT / "tools"
VERSION_FILE = ROOT / "VERSION"

for _path in (str(TOOLS), str(SRC)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import unit_table  # noqa: E402  (таблица единиц — общий источник для JS и Kotlin)

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TOOLS))

import periods  # noqa: E402
import subject  # noqa: E402

YEAR_MODULES = periods.modules()
#: все модули, без которых релиз физики неполон
REQUIRED_MODULES = ["templates", "formulas", "study", "theory", "diagrams", "mistakes",
                    "ui_strings"]

#: признаки чужого предмета: их не должно быть в заданиях и надписях интерфейса.
#: Учебная проза теории может упоминать логарифм или геометрию по делу (синус
#: безразмерного аргумента, построение изображения), поэтому здесь только прямые
#: названия чужого приложения и предмета.
FOREIGN_WORDS = ("математик", "mathemat", "ctmaths", "ctmathstutor")


def load(name: str):
    """Импортировать модуль автора; отсутствие обязательного модуля — ошибка."""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:
        if error.name == name:
            return None
        raise


def collect_tasks() -> tuple[list, list]:
    """Банк и аналогичные задания: каждое проверено ядром."""
    bank, analogous = [], []
    seen: set[str] = set()
    checks = 0

    mistakes = load("mistakes")
    if mistakes is None:
        raise SystemExit("content_src/mistakes.py отсутствует — каталог типичных ошибок "
                         "обязателен для разбора неверных ответов")
    mistakes.register()

    for name in YEAR_MODULES:
        module = load(name)
        if module is None:
            raise SystemExit(f"нет модуля варианта: content_src/{name}.py — "
                             f"варианты 2021–2026 обязательны (periods.py)")
        items = module.tasks()
        expected = periods.PARTS["A"] + periods.PARTS["B"]
        if len(items) != expected:
            raise SystemExit(f"{name}: собрано {len(items)} заданий вместо {expected}")
        parts = {part: sum(1 for item in items if item.part == part) for part in ("A", "B")}
        if parts != periods.PARTS:
            raise SystemExit(f"{name}: части варианта не совпадают с periods.PARTS — {parts}")
        for task in items:
            task.verify()
            checks += 1
            if task.id in seen:
                raise SystemExit(f"повторяющийся идентификатор задания: {task.id}")
            seen.add(task.id)
            bank.append(task.to_json())
        print(f"  · {name}: {len(items)} заданий проверено "
              f"(A {parts['A']} + B {parts['B']})")

    templates = load("templates")
    if templates is None:
        raise SystemExit("content_src/templates.py отсутствует — без генератора "
                         "аналогичных заданий разбор ошибки пуст")
    items = templates.generate()
    for task in items:
        task.verify()
        checks += 1
        if task.id in seen:
            raise SystemExit(f"повторяющийся идентификатор задания: {task.id}")
        seen.add(task.id)
        analogous.append(task.to_json())
    print(f"  · templates: {len(items)} аналогичных заданий проверено")

    coverage = {task["topic"] for task in bank} | {task["topic"] for task in analogous}
    missing = [topic for topic in periods.__dict__.get("TOPIC_ORDER", TOPIC_ORDER)
               if topic not in coverage]
    if missing:
        raise SystemExit("темы без заданий: " + ", ".join(missing))
    print(f"  ✓ {checks} заданий проверено точной арифметикой; тем покрыто: {len(coverage)}")
    return bank, analogous


def check_foreign_words(bank: list, analogous: list, lessons: dict, ui: dict) -> None:
    """Ни один текст физики не должен называть чужой предмет."""
    def scan(text: str, where: str) -> None:
        lowered = text.lower()
        for word in FOREIGN_WORDS:
            if word in lowered:
                raise SystemExit(f"{where}: текст похож на математический ({word!r}): "
                                 f"{text[:80]}…")

    for task in bank + analogous:
        for field in ("text", "solution", "hints"):
            value = task.get(field)
            if isinstance(value, dict):
                for lang in ("ru", "en"):
                    for line in value.get(lang) or []:
                        scan(str(line), task["id"] + f".{field}")
            elif isinstance(value, dict) is False and isinstance(value, str):
                scan(value, task["id"] + f".{field}")
    for key, entry in ui.items():
        for lang in ("ru", "en"):
            scan(str(entry.get(lang, "")), f"ui:{key}")
    for key, entry in lessons.items():
        for lang in ("ru", "en"):
            for group in ("definitions", "rules", "everyday"):
                for line in (entry.get(group) or {}).get(lang) or []:
                    scan(str(line), f"lesson {key}.{group}")
            for example in entry.get("examples") or []:
                scan(str((example.get("statement") or {}).get(lang, "")),
                     f"lesson {key}.example")
    print("  ✓ тексты не содержат чужих предметных названий")


def _bilingual_text(value, where: str) -> None:
    for lang in ("ru", "en"):
        if not isinstance(value, dict) or not isinstance(value.get(lang), str) \
                or not value[lang].strip():
            raise SystemExit(f"{where}: нет текста ({lang})")


def _bilingual_lines(value, where: str, minimum: int = 1) -> None:
    for lang in ("ru", "en"):
        lines = value.get(lang) if isinstance(value, dict) else None
        if not isinstance(lines, list) or len(lines) < minimum or any(
                not isinstance(line, str) or not line.strip() for line in lines):
            raise SystemExit(f"{where}: неполный список ({lang})")
    if len(value["ru"]) != len(value["en"]):
        raise SystemExit(f"{where}: разное число абзацев ru/en")


def build_diagrams() -> dict:
    module = load("diagrams")
    if module is None:
        raise SystemExit("content_src/diagrams.py отсутствует — офлайн-схемы обязательны "
                         "(без них уроки показывают только текст)")
    try:
        figures = module.validate(module.payload())
    except (TypeError, ValueError, KeyError) as error:
        raise SystemExit("некорректная схема: " + str(error)) from error
    if not figures:
        raise SystemExit("каталог схем пуст")
    print(f"  · diagrams: {len(figures)} схем проверено (типизированный SVG, 420×280)")
    return figures


def build_theory(figures: dict) -> dict:
    module = load("theory")
    if module is None:
        raise SystemExit("content_src/theory.py отсутствует — офлайн-теория обязательна")
    lessons = module.payload()
    if not lessons:
        raise SystemExit("каталог уроков пуст")
    used = set()
    for key, entry in lessons.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", key) or entry.get("id") != key:
            raise SystemExit(f"неверный идентификатор урока: {key}")
        _bilingual_text(entry.get("title"), f"урок {key}: заголовок")
        _bilingual_lines(entry.get("everyday"), f"урок {key}: бытовое объяснение", 2)
        _bilingual_lines(entry.get("definitions"), f"урок {key}: определения")
        _bilingual_lines(entry.get("rules"), f"урок {key}: правила и условия")
        refs = entry.get("figures")
        if not isinstance(refs, list) or len(refs) != len(set(refs)) or any(
                ref not in figures for ref in refs):
            raise SystemExit(f"урок {key}: ссылки на схемы отсутствуют или дублируются")
        used.update(refs)
        if not entry.get("examples"):
            raise SystemExit(f"урок {key}: нет разобранного примера")
        for example in entry["examples"]:
            _bilingual_text(example.get("statement"), f"урок {key}: условие примера")
            _bilingual_lines(example.get("steps"), f"урок {key}: решение примера", 2)
    unreachable = set(figures) - used
    if unreachable:
        raise SystemExit("схемы, недостижимые из уроков: " + ", ".join(sorted(unreachable)))
    print(f"  · theory: {len(lessons)} двуязычных уроков + бытовые объяснения проверены")
    return lessons


def build_study(topic_order: list, lessons: dict) -> dict:
    module = load("study")
    if module is None:
        raise SystemExit("content_src/study.py отсутствует — при неверном ответе "
                         "приложению нечего открыть ученику")
    study = module.payload()
    formulas = load("formulas")
    groups = formulas.groups()["groups"] if formulas else []
    group_ids = {group["id"] for group in groups}
    used_lessons = set()
    for group in groups:
        group_lessons = group.get("lessons") or []
        if not group_lessons or any(key not in lessons for key in group_lessons):
            raise SystemExit(f"группа формул {group['id']} ссылается на несуществующий урок")
        for item in group["items"]:
            key = item.get("lesson")
            if key not in lessons or key not in group_lessons:
                raise SystemExit(f"строка формул в {group['id']} ссылается на урок {key!r}, "
                                 f"которого нет в группе")
            used_lessons.add(key)
    missing = [topic for topic in topic_order if topic not in study]
    if missing:
        raise SystemExit("нет конспекта для тем: " + ", ".join(missing))
    for topic, entry in study.items():
        if topic not in topic_order:
            raise SystemExit(f"конспект для неизвестной темы: {topic}")
        for lang in ("ru", "en"):
            if len(entry.get(lang) or []) < 2:
                raise SystemExit(f"конспект {topic} слишком короткий ({lang})")
        lesson_ids = entry.get("lessons") or []
        if len(lesson_ids) != len(entry["ru"]) or len(lesson_ids) != len(entry["en"]):
            raise SystemExit(f"конспект {topic}: на каждый пункт нужна ссылка на урок "
                             f"в обоих языках")
        if any(key not in lessons for key in lesson_ids):
            raise SystemExit(f"конспект {topic} ссылается на несуществующий урок")
        used_lessons.update(lesson_ids)
        unknown = [group for group in entry.get("formulas") or [] if group not in group_ids]
        if unknown:
            raise SystemExit(f"конспект {topic} ссылается на неизвестные группы формул: "
                             + ", ".join(unknown))
        if not entry.get("formulas"):
            raise SystemExit(f"конспект {topic} не ссылается на сборник формул")
    unreachable = set(lessons) - used_lessons
    if unreachable:
        raise SystemExit("уроки, недостижимые из конспектов: " + ", ".join(sorted(unreachable)))
    print(f"  · study: конспекты и ссылки на теорию для {len(study)} тем проверены")
    return study


def check_ui_strings() -> dict:
    module = load("ui_strings")
    if module is None:
        raise SystemExit("content_src/ui_strings.py отсутствует — интерфейс без строк")
    strings = module.STRINGS
    for key, entry in strings.items():
        for lang in ("ru", "en"):
            if not str(entry.get(lang, "")).strip():
                raise SystemExit(f"строка {key}: пустой {lang}")
        if key.endswith("_fmt"):
            if entry["ru"].count("%s") != entry["en"].count("%s") \
                    or entry["ru"].count("%s") < 1:
                raise SystemExit(f"строка {key}: подстановок %s разное число в ru/en")
    used = set()
    for path in sorted((ROOT / "webapp").glob("*.js")):
        for match in re.finditer(r"\bt\(\s*'([a-z0-9_]+)'", path.read_text(encoding="utf-8")):
            used.add(match.group(1))
    missing = sorted(used - set(strings))
    if missing:
        raise SystemExit("в интерфейсе используются строки, которых нет в ui_strings.py: "
                         + ", ".join(missing))
    print(f"  · ui_strings: {len(strings)} надписей; ключей интерфейса без строки нет "
          f"({len(used)} используется)")
    return strings


def check_vectors() -> dict:
    kit = load("kit")
    from quantities import check_answer
    payload = kit.vectors_payload()
    for case in payload["cases"]:
        spec = case["spec"]
        for item in case["cases"]:
            result = check_answer(item["input"], spec)
            if bool(result.ok) != bool(item["ok"]):
                raise SystemExit(f"вектор {case['id']}: запись {item['input']!r} оценена "
                                 f"{result.ok!r} вместо {item['ok']!r}")
            if not item["ok"] and item.get("reason") and result.reason != item["reason"]:
                raise SystemExit(f"вектор {case['id']}: причина для {item['input']!r} — "
                                 f"{result.reason!r}, ожидалась {item['reason']!r}")
    print(f"  · answer vectors: {payload['count']} векторов оценено ядром эталонно")
    return payload


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=False),
                    encoding="utf-8")
    print(f"    → {path.relative_to(ROOT)}  ({path.stat().st_size / 1024:.0f} KiB)")


def android_strings_xml(strings: dict, lang: str) -> str:
    """Каталог строк → resources Android (``%s`` → ``%1$s``, ``%2$s`` …)."""
    def esc(value: str, fmt: bool) -> str:
        value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        value = value.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n")
        if fmt:
            counter = 0

            def number_argument(_match):
                nonlocal counter
                counter += 1
                return "%%%d$s" % counter

            value = re.sub(r"%s", number_argument, value)
        else:
            value = value.replace("%", "%%")
        return value

    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<!-- GENERATED by tools/build_content.py from content_src/ui_strings.py '
             '- do not edit -->',
             "<resources>"]
    for key in sorted(strings):
        entry = strings[key]
        value = entry.get(lang) or entry.get("en") or ""
        lines.append('    <string name="%s">%s</string>' % (key, esc(value, key.endswith("_fmt"))))
    lines.append("</resources>")
    return "\n".join(lines) + "\n"


TOPIC_ORDER = ["measurements", "kinematics", "dynamics", "workenergy", "statics",
               "molecular", "thermo", "electrostatics", "current", "magnetism",
               "oscillations", "optics", "quantum"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="проверить банк, ничего не записывая (используется в CI)")
    args = parser.parse_args()

    print("Конвейер контента физики")
    if not VERSION_FILE.exists():
        raise SystemExit("нет файла VERSION — нечего публиковать")
    content_version = VERSION_FILE.read_text(encoding="utf-8").strip()

    bank, analogous = collect_tasks()
    vectors = check_vectors()
    ui = check_ui_strings()
    figures = build_diagrams()
    lessons = build_theory(figures)
    study = build_study(TOPIC_ORDER, lessons)
    check_foreign_words(bank, analogous, lessons, ui)

    kit = load("kit")
    topics = {"topics": kit.TOPICS, "order": kit.TOPIC_ORDER, "tools": kit.TOOLS,
              "counts": {}, "byYear": {}, "study": study, "lessons": lessons,
              "figures": figures}
    for task in bank:
        topics["counts"][task["topic"]] = topics["counts"].get(task["topic"], 0) + 1
        if task["year"]:
            key = str(task["year"])
            topics["byYear"][key] = topics["byYear"].get(key, 0) + 1
    for task in analogous:
        topics["counts"][task["topic"]] = topics["counts"].get(task["topic"], 0) + 1

    mistakes = load("mistakes").payload()

    meta = {
        "contentVersion": content_version,
        "schema": 1,
        "subject": subject.SUBJECT,
        "package": subject.ANDROID_PACKAGE,
        "app": subject.WINDOWS_BINARY,
        "years": sorted({task["year"] for task in bank if task["year"]}),
        "counts": {
            "bank": len(bank),
            "analogous": len(analogous),
            "choice": sum(1 for task in bank if task["answerType"] == "choice"),
            "quantity": sum(1 for task in bank if task["answerType"] != "choice"),
            "lessons": len(lessons),
            "figures": len(figures),
        },
        "author": "Zakharevich Igor",
        "repo": "https://github.com/zigorminsk-debug/mathematics",
        "disclosure": periods.DISCLAIMER,
        "structureSource": periods.SOURCE,
    }

    if args.check:
        print("режим --check: файлы не записаны")
        return 0

    print("Запись банка")
    write_json(DIST / "bank.json", {"meta": meta, "tasks": bank})
    write_json(DIST / "analogous.json", {"meta": meta, "tasks": analogous})
    write_json(DIST / "topics.json", topics)
    write_json(DIST / "formulas.json", load("formulas").groups())
    write_json(DIST / "mistakes.json", mistakes)
    write_json(DIST / "ui_strings.json", {"strings": ui, "meta": meta})
    write_json(DIST / "answer_vectors.json", vectors)

    version = {
        **meta,
        **periods.payload(),
        "updatePolicy": "subject-scoped releases API; no global /latest/download",
        "baseUrl": subject.content_base_url("zigorminsk-debug/mathematics", content_version),
        "files": {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
                  for path in sorted(DIST.glob("*.json")) if path.name != "version.json"},
    }
    write_json(DIST / "version.json", version)

    print("Копирование в приложения")
    for target in (ROOT / "android" / "app" / "src" / "main" / "assets" / "content",
                   ROOT / "windows" / "web" / "content"):
        if not target.parent.exists():
            print(f"    · пропущено {target.relative_to(ROOT)} (приложение ещё не собрано)")
            continue
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(DIST, target)
        print(f"    → {target.relative_to(ROOT)}/")

    print("Генерация таблицы единиц (Python → JS → Kotlin)")
    core_js = ROOT / "webapp" / "core.js"
    if core_js.exists():
        core_js.write_text(unit_table.apply_javascript(core_js.read_text(encoding="utf-8")),
                           encoding="utf-8")
        print("    → webapp/core.js (блок units:generated)")
    unit_table.write_unit_vectors()
    print("    → tests/unit_vectors.json")
    kotlin = (ROOT / "android" / "app" / "src" / "main" / "java" / "by" / "ziv"
              / "ctphysics" / "UnitTable.kt")
    if kotlin.parent.exists():
        kotlin.write_text(unit_table.render_kotlin(), encoding="utf-8")
        print(f"    → {kotlin.relative_to(ROOT)}")

    print("Генерация строк Android")
    for lang, folder in (("en", "values"), ("ru", "values-ru")):
        out = ROOT / "android" / "app" / "src" / "main" / "res" / folder / "strings.xml"
        if out.parent.parent.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(android_strings_xml(ui, lang), encoding="utf-8")
            print(f"    → {out.relative_to(ROOT)}")

    print("Готово.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
