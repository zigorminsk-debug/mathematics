"""content_src/periods.py — структура и периоды (английский язык).

Источник структуры: РИКЗ, перечень предметов и количество заданий/время
(«Перечень и коды учебных предметов, количество заданий и время выполнения
экзаменационных (тестовых) работ … для проведения ЦЭ, ЦТ и РЦЭ», форма № 3):
Английский язык — код 07, часть А 18, часть В 22, всего 40, 120 минут.

Проверено 2026-10-14 по https://result.rikc.by/ru/documents/filesofregpunkts/rce_2025/form__3.pdf
(таблица для 2025 года; совпадает с таблицей РТ и материалов приёмных комиссий).

**Авторские наборы** («периоды») — тренировочная практика, составленная для этого
приложения; они не являются официальными материалами РИКЗ и не выдаются за них.
"""

from __future__ import annotations

import importlib

#: состав теста: 18 заданий части А и 22 задания части В, 120 минут
PARTS = {"A": 18, "B": 22}
MINUTES = 120
TOTAL = sum(PARTS.values())

#: откуда взята структура — URL и дата проверки
SOURCE = ("РИКЗ, «Перечень и коды учебных предметов …», форма № 3, Английский язык: "
          "18 A + 22 B = 40 заданий, 120 минут — "
          "https://result.rikc.by/ru/documents/filesofregpunkts/rce_2025/form__3.pdf "
          "(проверено 2026-10-14)")

#: честная оговорка для интерфейса, отчёта и release notes
DISCLAIMER = ("Авторские тренировочные наборы этого приложения не являются "
              "официальными материалами РИКЗ и не выдаются за них. Формат "
              "подготовки повторяет структуру теста по английскому языку "
              "(18 A + 22 B, 120 минут), но задания составлены автором приложения. Год — метка набора, "
              "не архив экзамена этого года; все наборы используют современную "
              "тренировочную структуру, а не исторический формат.")

#: периоды, для которых банк уже наполнен полностью
RELEASED_PERIODS = (2021, 2022, 2023, 2024, 2025, 2026)

#: периоды, которые появятся в следующих выпусках (не выдаём их за готовые)
PLANNED_PERIODS = ()

#: за какой год собирается отдельный модуль ``task_bank_<год>.py``
YEAR_MODULES = (*RELEASED_PERIODS,)


def modules() -> list[str]:
    return [f"task_bank_{year}" for year in YEAR_MODULES]


def payload() -> dict:
    """Поля структуры для ``version.json`` и интерфейса."""
    return {
        "parts": dict(PARTS),
        "total": TOTAL,
        "minutes": MINUTES,
        "structureSource": SOURCE,
        "disclaimer": DISCLAIMER,
        "periods": {"released": list(RELEASED_PERIODS), "planned": list(PLANNED_PERIODS)},
    }


def load(name: str):
    return importlib.import_module(name)


def validate_variants(tasks: list[dict]) -> None:
    """Fail closed on incomplete, duplicated or incorrectly labelled yearly sets."""
    if set(RELEASED_PERIODS) & set(PLANNED_PERIODS):
        raise ValueError("год одновременно выпущен и запланирован")
    annual = [task for task in tasks if task.get("year") is not None]
    years = {task["year"] for task in annual}
    if years != set(RELEASED_PERIODS):
        raise ValueError(f"годы банка {sorted(years)} не совпадают с выпущенными")
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("повтор идентификатора задания")
    texts = [" ".join(task["text"].split()).casefold() for task in annual]
    if len(texts) != len(set(texts)):
        raise ValueError("в годовых наборах повторяется текст задания")
    for year in RELEASED_PERIODS:
        variant = [task for task in annual if task["year"] == year]
        if len(variant) != TOTAL:
            raise ValueError(f"{year}: нужно {TOTAL} заданий, получено {len(variant)}")
        for part, count in PARTS.items():
            section = [task for task in variant if task.get("part") == part]
            if sorted(task.get("n", 0) for task in section) != list(range(1, count + 1)):
                raise ValueError(f"{year}: часть {part} должна содержать номера 1–{count}")
            for task in section:
                if task["id"] != f"en-{year}-{part}{task['n']}":
                    raise ValueError(f"{year}: неверная метка {task['id']}")
                if (task["type"] == "choice") != (part == "A"):
                    raise ValueError(f"{task['id']}: тип не соответствует части")
                if task.get("source") != "authored":
                    raise ValueError(f"{task['id']}: набор обязан быть авторским")
