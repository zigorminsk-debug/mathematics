"""periods.py — периоды (годы) ЦТ, представленные в базе заданий.

Один источник правды о том, какие варианты входят в банк: как называется модуль
автора, сколько заданий в каждой части и сколько времени отводится на вариант.
``tools/build_content.py`` берёт отсюда список модулей (``YEAR_MODULES``) и
записывает свойства периодов в ``dist/content/version.json``, чтобы интерфейс
показывал годы и состав варианта, не зашивая их в код.

Добавить следующий год — значит дописать одну запись здесь и создать
``content_src/task_bank_<год>.py`` (см. docs/CONTENT.md).

Exam periods (years) covered by the task bank: one record per variant, used both
by the content pipeline and by the applications.
"""

from __future__ import annotations

#: Сколько времени отводится на вариант в тренажёре (совпадает со значением по
#: умолчанию в настройках приложения: 180 минут).
DEFAULT_MINUTES = 180

#: Материалы не являются официальными заданиями РИКЗ: это варианты, составленные
#: автором по мотивам соответствующего года (дисклеймер — в README).
DISCLAIMER = {
    "ru": "Задания составлены по мотивам ЦТ соответствующего года и не являются "
          "официальными материалами РИКЗ.",
    "en": "The tasks follow the format of the corresponding CT year and are not "
          "official RIKZ materials.",
}

PERIODS: list[dict] = [
    {"year": 2021, "module": "task_bank_2021", "parts": {"A": 18, "B": 12},
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2021", "en": "Variant 2021"}},
    {"year": 2022, "module": "task_bank_2022", "parts": {"A": 18, "B": 12},
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2022", "en": "Variant 2022"}},
    {"year": 2023, "module": "task_bank_2023", "parts": {"A": 18, "B": 12},
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2023", "en": "Variant 2023"}},
    {"year": 2024, "module": "task_bank_2024", "parts": {"A": 18, "B": 12},
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2024", "en": "Variant 2024"}},
    {"year": 2025, "module": "task_bank_2025", "parts": {"A": 18, "B": 12},
     "minutes": DEFAULT_MINUTES, "label": {"ru": "Вариант 2025", "en": "Variant 2025"}},
]


def years() -> list[int]:
    """Годы, для которых в базе есть целый вариант."""
    return [period["year"] for period in PERIODS]


def modules() -> list[str]:
    """Имена модулей автора — их импортирует ``tools/build_content.py``."""
    return [period["module"] for period in PERIODS]


def payload() -> dict:
    """Часть манифеста ``version.json``: периоды и общий дисклеймер."""
    return {
        "periods": [
            {
                "year": period["year"],
                "label": period["label"],
                "parts": period["parts"],
                "minutes": period["minutes"],
                "tasks": period["parts"]["A"] + period["parts"]["B"],
            }
            for period in PERIODS
        ],
        "disclaimer": DISCLAIMER,
        "examMinutes": DEFAULT_MINUTES,
    }
