"""content_src/pools.py — сводный пул упражнений по всем 13 темам.

Банк берёт из пула первые ``BANK_PER_TOPIC`` заданий (они же показываются в
тренировке), остальные становятся «однотипными заданиями»: то же правило, другие
слова. Ничего не выдумывается на ходу — генератор только выбирает порядок.
"""

from __future__ import annotations

import importlib
import random

import pools_a
import pools_b
import pools_c

#: сколько заданий темы попадает в тренировочный банк
BANK_PER_TOPIC = 5

_MEDIA = {**pools_a.MEDIA, **pools_b.MEDIA, **pools_c.MEDIA}

#: порядок тем — как в программе, а не как в словаре
ORDER = ("tenses", "modals", "passive", "conditionals", "nonfinite", "articles",
         "prepositions", "pronouns_numerals", "noun_adj_adv", "word_formation",
         "gap_fill", "extra_word", "communication")


def pool(topic: str) -> list[dict]:
    if topic not in _MEDIA:
        raise KeyError(f"нет пула для темы {topic!r}")
    return list(_MEDIA[topic])


def all_pools() -> dict[str, list[dict]]:
    return {topic: pool(topic) for topic in ORDER}


def bank_practice() -> list[dict]:
    """Задания тренировочного банка: первые BANK_PER_TOPIC из каждой темы."""
    tasks = []
    for topic in ORDER:
        tasks.extend(pool(topic)[:BANK_PER_TOPIC])
    return tasks


def analogous() -> list[dict]:
    """Однотипные задания: остаток пула по каждой теме."""
    tasks = []
    for topic in ORDER:
        tasks.extend(pool(topic)[BANK_PER_TOPIC:])
    return tasks


def draw(topic: str, seed: int, count: int) -> list[dict]:
    """Детерминированная выборка ``count`` заданий темы для отработки правила."""
    items = pool(topic)
    if not items:
        return []
    rng = random.Random(f"{topic}:{seed}")
    shuffled = items[:]
    rng.shuffle(shuffled)
    picked, seen = [], set()
    while len(picked) < min(count, len(shuffled)):
        for task in shuffled:
            if task["id"] not in seen:
                picked.append(task)
                seen.add(task["id"])
                if len(picked) == min(count, len(shuffled)):
                    break
    return picked


def load(name: str):
    return importlib.import_module(name)
