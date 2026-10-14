"""content_src/kit.py — темы, конструкторы заданий, проверка и генераторы.

Каждое задание банка собирается конструктором, поэтому обязательные поля не
забываются, а ответ немедленно проверяется нормативной политикой
(``content_src/policy.py``). Конструктор части А всегда даёт ровно пять
уникальных вариантов, первый из которых верный (интерфейс перемешивает их сам).

Генераторы однотипных заданий («отработать тему») детерминированы: тот же
вопрос с тем же зерном даёт тот же текст, ответ и объяснение. Таблицы подстановок
составлены так, чтобы **любая** комбинация была грамматически верной — генератор
не может выпустить бессмыслицу, и это проверяется сборкой контента.
"""

from __future__ import annotations

import importlib
import random

import policy

#: ---------------------------------------------------------------------------
#: Темы (13 областей программы) — ключ, русское и английское название
#: ---------------------------------------------------------------------------

TOPICS = {
    "tenses": {"ru": "Времена и аспекты", "en": "Tenses and aspects",
               "rule": "tenses"},
    "modals": {"ru": "Модальные глаголы", "en": "Modal verbs", "rule": "modals"},
    "passive": {"ru": "Страдательный залог", "en": "Passive voice", "rule": "passive"},
    "conditionals": {"ru": "Условные предложения и согласование времён",
                     "en": "Conditionals and reported speech", "rule": "conditionals"},
    "nonfinite": {"ru": "Инфинитив, герундий, причастие",
                  "en": "Infinitive, gerund, participle", "rule": "nonfinite"},
    "articles": {"ru": "Артикли и определители", "en": "Articles and determiners",
                 "rule": "articles"},
    "prepositions": {"ru": "Предлоги и фразовые глаголы",
                     "en": "Prepositions and phrasal verbs", "rule": "prepositions"},
    "pronouns_numerals": {"ru": "Местоимения, числительные, союзы",
                          "en": "Pronouns, numerals, conjunctions", "rule": "pronouns"},
    "noun_adj_adv": {"ru": "Существительное, прилагательное, наречие",
                     "en": "Nouns, adjectives, adverbs", "rule": "noun_adj_adv"},
    "word_formation": {"ru": "Словообразование (часть В)",
                       "en": "Word formation (Part B)", "rule": "word_formation"},
    "gap_fill": {"ru": "Вставка пропущенного слова (часть В)",
                 "en": "Gap fill (Part B)", "rule": "gap_fill"},
    "extra_word": {"ru": "Поиск лишнего слова (часть В)",
                   "en": "Extra word (Part B)", "rule": "extra_word"},
    "communication": {"ru": "Чтение, реплики, социокультурный контекст",
                      "en": "Reading, replies, culture", "rule": "communication"},
}

TOPIC_ORDER = tuple(TOPICS)

#: инструменты интерфейса (как у соседних приложений: калькулятор не нужен)
TOOLS = {
    "train": {"ru": "Тренировка по темам", "en": "Practice by topic"},
    "exam": {"ru": "Вариант целиком", "en": "Full variant"},
}

#: типы заданий и что они требуют от интерфейса
TYPES = {
    "choice": {"ru": "выбор одного варианта из пяти", "en": "one option out of five"},
    "gap": {"ru": "вписать пропущенное слово", "en": "type the missing word"},
    "form": {"ru": "образовать нужную форму слова", "en": "form the required word"},
    "extra": {"ru": "найти лишнее слово", "en": "find the extra word"},
    "translate": {"ru": "перевести фрагмент", "en": "translate the fragment"},
}

INSTRUCTIONS = {
    "choice": {"ru": "Выберите правильный вариант.",
               "en": "Choose the correct option."},
    "gap": {"ru": "Заполните пропуск одним словом.",
            "en": "Fill the gap with one word."},
    "form": {"ru": "Образуйте от данного слова подходящую по смыслу и форме форму.",
             "en": "Form the correct word from the one given."},
    "extra": {"ru": "Найдите лишнее слово в строке и впишите его.",
              "en": "Find the extra word in the line and type it."},
    "translate": {"ru": "Переведите фрагмент на английский язык.",
                  "en": "Translate the fragment into English."},
}


def topic_title(key: str) -> dict:
    return TOPICS.get(key, {"ru": key, "en": key})


#: ---------------------------------------------------------------------------
#: Конструкторы заданий
#: ---------------------------------------------------------------------------

def _task(task_id: str, *, topic: str, kind: str, text: str, answer: str,
          accepted=(), options=(), year: int | None = None, part: str | None = None,
          n: int | None = None, correction: dict | None = None, tags=(),
          rule: str | None = None, policy_overrides: dict | None = None,
          given: str | None = None, source: str = "authored") -> dict:
    if topic not in TOPICS:
        raise ValueError(f"{task_id}: неизвестная тема {topic!r}")
    if kind not in TYPES:
        raise ValueError(f"{task_id}: неизвестный тип {kind!r}")
    task = {
        "id": task_id,
        "topic": topic,
        "type": kind,
        "instruction": dict(INSTRUCTIONS[kind]),
        "text": text,
        "answer": {"value": answer},
        "accepted": list(dict.fromkeys([answer, *accepted])),
        "policy": dict(policy.DEFAULT_POLICY, **(policy_overrides or {})),
        "tags": list(tags),
        "rule": rule or TOPICS[topic]["rule"],
        "source": source,
    }
    if options:
        if kind != "choice":
            raise ValueError(f"{task_id}: варианты бывают только у заданий части А")
        if len(options) != 5 or len(set(options)) != 5:
            raise ValueError(f"{task_id}: нужно ровно пять уникальных вариантов")
        if options[0] != answer:
            raise ValueError(f"{task_id}: первый вариант обязан быть верным (интерфейс перемешивает)")
        task["options"] = list(options)
    elif kind == "choice":
        raise ValueError(f"{task_id}: задание-выбор без вариантов")
    if given is not None:
        task["given"] = given          # слово-подсказка для словообразования
    if year is not None:
        if part not in ("A", "B") or n is None:
            raise ValueError(f"{task_id}: у задания варианта обязательны part и n")
        task.update({"year": year, "part": part, "n": n})
    if correction is not None:
        task["correction"] = dict(correction)
    else:
        task["correction"] = {"ru": "", "en": ""}
    return task


def choice(task_id: str, *, topic: str, text: str, answer: str, options,
           distractors: dict | None = None, **kwargs) -> dict:
    """Задание части А: пять вариантов, первый верный."""
    if len(options) != 5:
        raise ValueError(f"{task_id}: часть А — пять вариантов")
    task = _task(task_id, topic=topic, kind="choice", text=text, answer=answer,
                 options=options, **kwargs)
    if distractors:
        unknown = set(distractors) - set(options[1:])
        if unknown:
            raise ValueError(f"{task_id}: объяснения для несуществующих вариантов {sorted(unknown)}")
        task["distractors"] = dict(distractors)
    return task


def typed(task_id: str, *, topic: str, kind: str, text: str, answer: str, **kwargs) -> dict:
    """Задание части В: ответ вписывается словом (или фрагментом)."""
    if kind == "choice":
        raise ValueError(f"{task_id}: для выбора используйте choice()")
    return _task(task_id, topic=topic, kind=kind, text=text, answer=answer, **kwargs)


#: ---------------------------------------------------------------------------
#: Проверка задания
#: ---------------------------------------------------------------------------

def verify(task: dict) -> list[str]:
    """Вернуть список проблем задания (пустой список — всё в порядке)."""
    problems = []
    task_id = task.get("id", "<без id>")
    if not task_id or not isinstance(task_id, str):
        problems.append("нет идентификатора")
    if not task.get("text", "").strip():
        problems.append("пустой текст задания")
    correction = task.get("correction") or {}
    for lang in ("ru", "en"):
        if not (correction.get(lang) or "").strip():
            problems.append(f"нет пояснения ({lang})")
    answer = (task.get("answer") or {}).get("value", "")
    if not answer.strip():
        problems.append("пустой ответ")
    if task.get("type") == "choice":
        options = task.get("options") or []
        if len(options) != 5 or len(set(options)) != 5:
            problems.append("варианты части А должны быть пятью уникальными")
        elif options[0] != answer:
            problems.append("первый вариант должен совпадать с ответом")
        if "___" not in task.get("text", "") and task.get("type") == "choice" \
                and "?" not in task.get("text", ""):
            problems.append("в задании-выборе нет пропуска или вопроса")
    # нормативная проверка: каждый допустимый ответ принимается, типичные
    # неверные формы — отвергаются с понятной причиной
    for accepted in task.get("accepted", []):
        result = policy.check(task, accepted)
        if not result["ok"]:
            problems.append(f"допустимый ответ {accepted!r} отвергнут: {result['reason']}")
    empty = policy.check(task, "   ")
    expected_empty = "ok" if policy.policy_for(task)["empty"] == "accept" else "empty"
    if empty["reason"] != expected_empty:
        problems.append(f"пустой ввод должен давать причину {expected_empty}")
    return problems


#: ---------------------------------------------------------------------------
#: Генераторы однотипных заданий (детерминированные)
#: ---------------------------------------------------------------------------

#: Правильно подобранные таблицы: любая комбинация даёт верное предложение.
_TENSE_TABLE = (
    # (маркер времени, форма ответа, перевод фрагмента)
    ("every day", "works", {"ru": "работает", "en": "works"}),
    ("yesterday", "worked", {"ru": "работал", "en": "worked"}),
    ("right now", "is working", {"ru": "работает сейчас", "en": "is working now"}),
    ("since 2019", "has worked", {"ru": "работает с 2019 года", "en": "has worked"}),
    ("by next June", "will have worked", {"ru": "проработает", "en": "will have worked"}),
)

_PREPOSITION_TABLE = (
    ("depend", "on", {"ru": "зависеть от", "en": "depend on"}),
    ("interested", "in", {"ru": "интересоваться", "en": "interested in"}),
    ("good", "at", {"ru": "хорошо владеть", "en": "good at"}),
    ("afraid", "of", {"ru": "бояться", "en": "afraid of"}),
    ("responsible", "for", {"ru": "отвечать за", "en": "responsible for"}),
)

_FORMATION_TABLE = (
    ("care", "carefully", "наречие: внимательно", "adverb"),
    ("success", "successful", "прилагательное: успешный", "adjective"),
    ("differ", "difference", "существительное: различие", "noun"),
    ("create", "creative", "прилагательное: творческий", "adjective"),
    ("possible", "impossible", "отрицательное: невозможный", "negative"),
)


def _generator_choice(task_id: str, topic: str, question_ru: str, question_en: str,
                      correct: str, wrong: list[str], why: dict, tags) -> dict:
    """Собрать однотипное задание-выбор: верный вариант первым."""
    return choice(task_id, topic=topic,
                  text=f"{question_ru}\n{question_en}",
                  answer=correct, options=[correct, *wrong],
                  correction={"ru": why["ru"], "en": why["en"]},
                  tags=tags, source="generated")


def generate(topic: str, seed: int, count: int) -> list[dict]:
    """Однотипные задания по теме: детерминированы зерном ``seed``."""
    rng = random.Random(f"{topic}:{seed}")
    out: list[dict] = []
    if topic == "tenses":
        for index in range(count):
            marker, form, meaning = _TENSE_TABLE[(seed + index) % len(_TENSE_TABLE)]
            wrong = [item[1] for item in _TENSE_TABLE if item[1] != form][:4]
            out.append(_generator_choice(
                f"gen-tenses-{seed}-{index}", "tenses",
                f"She ___ in the office. (Маркер времени: {marker})",
                f"The time marker is “{marker}”.",
                form, wrong,
                {"ru": f"Маркер «{marker}» требует формы {form} ({meaning['ru']}).",
                 "en": f"The marker “{marker}” requires {form} ({meaning['en']})."},
                ["tenses.marker"]))
    elif topic == "prepositions":
        for index in range(count):
            head, preposition, meaning = _PREPOSITION_TABLE[(seed + index) % len(_PREPOSITION_TABLE)]
            wrong = [item[1] for item in _PREPOSITION_TABLE if item[1] != preposition][:4]
            out.append(_generator_choice(
                f"gen-prepositions-{seed}-{index}", "prepositions",
                f"The result may {head} ___ the weather.",
                f"Choose the preposition that goes with “{head}”.",
                f"{head} {preposition}",
                [f"{head} {item}" for item in wrong],
                {"ru": f"Устойчивое сочетание: {meaning['ru']}.",
                 "en": f"Fixed collocation: {meaning['en']}."},
                ["prepositions.collocation"]))
    elif topic == "word_formation":
        for index in range(count):
            base, form, hint, kind = _FORMATION_TABLE[(seed + index) % len(_FORMATION_TABLE)]
            out.append(typed(
                f"gen-formation-{seed}-{index}", topic="word_formation", kind="form",
                text=f"Sentence with a gap: “He did the task ___.” ({base})",
                answer=form, given=base,
                correction={"ru": f"От «{base}» образуется {kind}: {hint}.",
                            "en": f"“{base}” forms the {kind} {form}: {hint}."},
                tags=["word_formation.suffix"], source="generated",
                policy_overrides={"case": "insensitive"}))
    elif topic == "poster":
        # служебная ветка: пустой набор (тема без генератора)
        out = []
    return out


#: сколько однотипных заданий у каждой темы (каталог для интерфейса)
GENERATOR_TOPICS = ("tenses", "prepositions", "word_formation")


def generator_count(topic: str) -> int:
    return 8 if topic in GENERATOR_TOPICS else 0


def load(name: str):
    return importlib.import_module(name)
