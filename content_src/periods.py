"""periods.py — периоды (годы) авторской практики по физике.

Один источник правды о составе варианта. Структура сверена с официальным
перечнем РИКЗ (см. physics/docs/CONTENT.md): физика — часть A 10 заданий
(выбор одного ответа из пяти), часть B 20 заданий (краткий ответ), всего 30
заданий, 210 минут. Значения 18+12/180 из математики сюда НЕ переносятся.

Самое важное: это авторские тренировочные варианты «по мотивам» ЦТ, а не
официальные материалы РИКЗ. Дисклеймер и источник записаны в version.json,
docs/CONTENT.md и в экране «О программе».
"""

from __future__ import annotations

#: Структура одного варианта (проверено 2026-10-14):
#: https://result.rikc.by/ru/documents/filesofregpunkts/rce_2025/form__3.pdf
PARTS = {"A": 10, "B": 20}
DEFAULT_MINUTES = 210
SOURCE = ("Перечень РИКЗ: физика — 10 заданий части A, 20 заданий части B, "
          "всего 30, 210 минут (ЦТ/ЦЭ 2025). Проверено 2026-10-14.")

DISCLAIMER = {
    "ru": "Авторские тренировочные варианты, составленные по программе и формату ЦТ "
          "по физике. Это не официальные задания РИКЗ.",
    "en": "Authored practice papers written to the physics CT syllabus and format. "
          "They are not official RIKZ materials.",
}

PERIODS: list[dict] = [
    {"year": 2021, "module": "task_bank_2021", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2021", "en": "Variant 2021"}},
    {"year": 2022, "module": "task_bank_2022", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2022", "en": "Variant 2022"}},
    {"year": 2023, "module": "task_bank_2023", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2023", "en": "Variant 2023"}},
    {"year": 2024, "module": "task_bank_2024", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2024", "en": "Variant 2024"}},
    {"year": 2025, "module": "task_bank_2025", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2025", "en": "Variant 2025"}},
    {"year": 2026, "module": "task_bank_2026", "parts": dict(PARTS),
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2026", "en": "Variant 2026"}},
]


def years() -> list[int]:
    return [period["year"] for period in PERIODS]


def modules() -> list[str]:
    return [period["module"] for period in PERIODS]


def payload() -> dict:
    return {
        "periods": [
            {"year": period["year"], "label": period["label"], "parts": period["parts"],
             "minutes": period["minutes"],
             "tasks": period["parts"]["A"] + period["parts"]["B"]}
            for period in PERIODS
        ],
        "disclaimer": DISCLAIMER,
        "examMinutes": DEFAULT_MINUTES,
        "structureSource": SOURCE,
    }
