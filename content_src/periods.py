"""periods.py — authored practice periods and the verified exam structure.

The structure of the Russian-language CE/CT is NOT inherited from mathematics
(18A + 12B, 180 min). It was checked against the official specification:

    Спецификация экзаменационной (тестовой) работы по учебному предмету
    «Русский язык» для проведения централизованного экзамена и
    централизованного тестирования в 2026 году. Утверждена Министром
    образования Республики Беларусь 03.11.2025, опубликована РИКЗ 05.11.2025:
    https://rikc.by/ru/specification/2026/01.pdf  (прочитано 2026-10-14)

    40 заданий: часть A — 18 (закрытые, выбор нескольких верных из пяти),
    часть B — 22 (открытые: слово, несколько цифр или буквы + цифры);
    120 минут; разделы: орфография 13, пунктуация 9, лексика 2,
    культура речи 3, фонетика 1, состав слова 2, морфология 4,
    синтаксис 3, текст 3.

The six variants labelled 2021–2026 are AUTHORED training sets. All of them
follow the 2026 specification; the year is only the name of the set, not a
copy of that year's exam, and nothing here is an official RIKZ material.
"""
from __future__ import annotations

DEFAULT_MINUTES = 120

SPECIFICATION = {
    "title": {
        "ru": "Спецификация экзаменационной (тестовой) работы по учебному предмету «Русский язык» "
              "для проведения ЦЭ и ЦТ в 2026 году (утв. 03.11.2025, опубл. РИКЗ 05.11.2025)",
        "en": "RIKZ specification of the 2026 CE/CT test in Russian (approved 03.11.2025, "
              "published 05.11.2025)",
    },
    "url": "https://rikc.by/ru/specification/2026/01.pdf",
    "checked": "2026-10-14",
    "tasks": 40, "parts": {"A": 18, "B": 22}, "minutes": 120,
    "partA": {"ru": "закрытые задания: выбор нескольких правильных ответов из пяти",
              "en": "closed tasks: choose several correct answers out of five"},
    "partB": {"ru": "открытые задания: ответ — слово, несколько цифр или сочетание букв и цифр",
              "en": "open tasks: the answer is a word, several digits or letters with digits"},
    "levels": {"I": 4, "II": 10, "III": 16, "IV": 6, "V": 4},
}

DISCLAIMER = {
    "ru": "Варианты 2021–2026 — авторская тренировочная практика по структуре спецификации РИКЗ 2026 года "
          "(40 заданий, 120 минут). Год — название набора, а не копия экзамена; это не официальные материалы РИКЗ.",
    "en": "Variants 2021–2026 are authored practice sets built on the structure of the 2026 RIKZ specification "
          "(40 tasks, 120 minutes). The year only names the set; these are not official RIKZ materials.",
}

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

PERIODS: list[dict] = [
    {"year": year, "parts": {"A": 18, "B": 22}, "minutes": DEFAULT_MINUTES,
     "label": {"ru": f"Вариант {year} (авторский)", "en": f"Variant {year} (authored)"}}
    for year in YEARS
]


def years() -> list[int]:
    return list(YEARS)


def payload() -> dict:
    return {
        "periods": [dict(period, tasks=period["parts"]["A"] + period["parts"]["B"]) for period in PERIODS],
        "disclaimer": DISCLAIMER,
        "examMinutes": DEFAULT_MINUTES,
        "specification": SPECIFICATION,
    }
