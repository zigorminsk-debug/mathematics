#!/usr/bin/env python3
"""tools/subject.py — профиль предмета, которым работают общие инструменты.

В репозитории живут несколько самостоятельных репетиторов, использующих **одну
проверенную** машинерию релизов (планировщик версии, публикатор, синхронизация
ассетов, проверки подписи). Какой именно предмет берётся, выбирает переменная
окружения ``CT_SUBJECT``:

===============  =============================  ===============================
``CT_SUBJECT``   профиль                        приложение
===============  =============================  ===============================
``physics``      ``tools/subject_physics.py``   «Репетитор ЦТ: Физика»
``english``      ``tools/subject_english.py``   «Репетитор ЦТ: Английский язык»
===============  =============================  ===============================

По умолчанию — ``physics``: историческое поведение всех команд сохраняется,
поэтому существующие workflow физики не меняются. Английский тренажёр вызывает
те же скрипты с ``CT_SUBJECT=english``, и они работают в своём дереве
(``english/``), со своей семьёй тегов ``english-v…``, своим пакетом, ключом
подписи и очередью публикации.

Профиль — единственный источник правды о предмете: идентификаторы, каталог
данных, семья тегов, набор публикуемых файлов и цели синхронизации. Тесты
(``tests/test_release.py``, ``tests/test_isolation.py``) проверяют, что значения
двух предметов не пересекаются.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

#: Известные предметы (файл ``tools/subject_<имя>.py``).
AVAILABLE = ("physics", "english")

#: Какое приложение обслуживают инструменты в этом процессе.
PROFILE_NAME = os.environ.get("CT_SUBJECT", "physics").strip().lower() or "physics"


def _load_profile(name: str):
    path = _HERE / f"subject_{name}.py"
    if not path.is_file():
        raise RuntimeError(
            f"unknown CT_SUBJECT={name!r}: {path.name} is missing; "
            f"expected one of {', '.join(AVAILABLE)}")
    spec = importlib.util.spec_from_file_location(f"subject_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


if PROFILE_NAME not in AVAILABLE:
    raise RuntimeError(
        f"unknown CT_SUBJECT={PROFILE_NAME!r}; expected one of {', '.join(AVAILABLE)}")

SUBJECT_PROFILE = _load_profile(PROFILE_NAME)

# Re-export the profile values so that ``import subject; subject.SUBJECT`` keeps
# working for every tool, exactly as before this dispatcher existed.
for _name, _value in list(vars(SUBJECT_PROFILE).items()):
    if not _name.startswith("_"):
        globals()[_name] = _value
del _name, _value
