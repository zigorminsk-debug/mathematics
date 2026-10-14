"""content_src/vectors.py — независимые векторы проверки ответа.

Это **авторские** ожидания, а не то, что «сказала программа»: в каждом случае
записано, что должно быть принято и с какой причиной отказа. Тот же файл потом
проверяет JavaScript (``webapp/core.js``) и Kotlin (``AnswerChecker.kt``), поэтому
расхождение реализаций видно сразу, а не у пользователя.

Границы, которые здесь зафиксированы:

* значимый пробел («a lot» ≠ «alot») и разрешённое схлопывание;
* дефис (обычный, короткий, длинный) и слитное написание;
* апострофы: типографский ’ и машинный ' — один знак; «don't» ≠ «dont», когда
  апостроф проверяется;
* артикли: игнорируются / обязательны / запрещены;
* регистр: не важен по умолчанию, важен там, где это объявлено;
* диакритика (café/cafe), пунктуация в конце фразы, лишние слова, пустой ввод.
"""

from __future__ import annotations

#: cases: task — мини-задание (ответ + политика), typed — ввод, expect/reason — ожидание
CASES = [
    # --- артикль не проверяется (по умолчанию) -----------------------------
    {"id": "art-1", "answer": "an honest man", "policy": {"article": "ignored"},
     "typed": "honest man", "expect": True, "reason": "ok",
     "note": {"ru": "Если задание объявило, что артикль не проверяется, пропуск допустим.",
              "en": "When the task declares the article unchecked, omitting it is accepted."}},
    {"id": "art-2", "answer": "an honest man", "typed": "an honest man",
     "expect": True, "reason": "ok"},
    {"id": "art-3", "answer": "an honest man", "typed": "AN HONEST MAN",
     "expect": True, "reason": "ok",
     "note": {"ru": "Регистр не важен, если не объявлено обратное.",
              "en": "Case is ignored unless declared otherwise."}},
    {"id": "art-4", "answer": "the piano", "typed": "piano",
     "expect": False, "reason": "article",
     "note": {"ru": "По умолчанию артикль — часть ответа, и без него ответ не принимается.",
              "en": "By default the article is part of the answer, so its absence is rejected."}},
    {"id": "art-5", "answer": "piano", "typed": "the piano",
     "expect": False, "reason": "article",
     "note": {"ru": "Лишний артикль — та же причина отказа.",
              "en": "An extra article gets the same failure reason."}},
    {"id": "art-6", "answer": "piano", "typed": "piano", "expect": True, "reason": "ok"},
    {"id": "art-7", "answer": "advice", "policy": {"article": "ignored"},
     "typed": "an advice", "expect": True, "reason": "ok",
     "note": {"ru": "При «article: ignored» лишний артикль тоже не влияет.",
              "en": "With “article: ignored” an extra article does not matter either."}},
    {"id": "art-8", "answer": "—", "policy": {"empty": "accept"},
     "typed": "   ", "expect": True, "reason": "ok",
     "note": {"ru": "Задание, где артикль не нужен: пустое поле — верный ответ.",
              "en": "A task where no article is needed: the empty field is correct."}},
    {"id": "art-9", "answer": "—", "policy": {"empty": "accept"},
     "typed": "the", "expect": False, "reason": "article",
     "note": {"ru": "Лишний артикль там, где он не нужен, отвергается с объяснением.",
              "en": "An unnecessary article is rejected with an explanation."}},

    # --- пробел значим ------------------------------------------------------
    {"id": "space-1", "answer": "a lot of", "typed": "a lot of",
     "expect": True, "reason": "ok"},
    {"id": "space-2", "answer": "a lot of", "typed": "alot of",
     "expect": False, "reason": "space",
     "note": {"ru": "Пробел — часть ответа: «alot» не принимается (причина — «почти совпало»).",
              "en": "The space is part of the answer: “alot” is rejected as a near miss."}},
    {"id": "space-3", "answer": "in spite of", "typed": "inspite of",
     "expect": False, "reason": "space"},
    {"id": "space-4", "answer": "a lot of", "policy": {"space": "collapse"},
     "typed": "a   lot of", "expect": True, "reason": "ok",
     "note": {"ru": "Схлопывание пробелов разрешено политикой задания.",
              "en": "Collapsing spaces is allowed by the task policy."}},
    {"id": "space-5", "answer": "a lot of", "typed": "a  lot of",
     "expect": False, "reason": "space",
     "note": {"ru": "Двойной пробел внутри ответа — тоже ошибка, но с понятной причиной.",
              "en": "A double space inside the answer fails with an explicit reason."}},

    # --- дефис --------------------------------------------------------------
    {"id": "hyphen-1", "answer": "well-known", "typed": "well-known",
     "expect": True, "reason": "ok"},
    {"id": "hyphen-2", "answer": "well-known", "typed": "well\u2011known",
     "expect": True, "reason": "ok",
     "note": {"ru": "Разные начертания дефиса — один знак.",
              "en": "Different dash glyphs are the same sign."}},
    {"id": "hyphen-3", "answer": "well-known", "typed": "wellknown",
     "expect": False, "reason": "hyphen",
     "note": {"ru": "Дефис значим: слитное написание — ошибка с понятной причиной.",
              "en": "The hyphen matters: the joined form fails with an explicit reason."}},
    {"id": "hyphen-4", "answer": "twenty-first", "typed": "twenty first",
     "expect": False, "reason": "hyphen",
     "note": {"ru": "Пробел вместо дефиса — та же ошибка дефиса.",
              "en": "A space instead of a hyphen gets the hyphen reason."}},
    {"id": "hyphen-5", "answer": "well-known", "policy": {"hyphen": "ignore"},
     "typed": "wellknown", "expect": True, "reason": "ok"},

    # --- апостроф -----------------------------------------------------------
    {"id": "apost-1", "answer": "don't", "policy": {"apostrophe": "required"},
     "typed": "don't", "expect": True, "reason": "ok"},
    {"id": "apost-2", "answer": "don't", "policy": {"apostrophe": "required"},
     "typed": "don\u2019t", "expect": True, "reason": "ok",
     "note": {"ru": "Типографский апостроф равен машинному.",
              "en": "A typographic apostrophe equals the keyboard one."}},
    {"id": "apost-3", "answer": "don't", "policy": {"apostrophe": "required"},
     "typed": "dont", "expect": False, "reason": "apostrophe",
     "note": {"ru": "Апостроф проверяется, если задание объявило это.",
              "en": "The apostrophe is checked when the task says so."}},
    {"id": "apost-4", "answer": "don't", "typed": "dont",
     "expect": True, "reason": "ok",
     "note": {"ru": "По умолчанию апостроф не проверяется.",
              "en": "By default the apostrophe is not checked."}},
    {"id": "apost-5", "answer": "its", "policy": {"apostrophe": "required"},
     "typed": "it's", "expect": False, "reason": "apostrophe",
     "note": {"ru": "«Its» и «it's» — разные формы: лишний апостроф отвергается.",
              "en": "“Its” and “it's” differ: an added apostrophe is rejected."}},

    # --- регистр ------------------------------------------------------------
    {"id": "case-1", "answer": "English", "policy": {"case": "sensitive"},
     "typed": "english", "expect": False, "reason": "case",
     "note": {"ru": "Языки и имена собственные пишутся с заглавной буквы.",
              "en": "Languages and proper names take a capital letter."}},
    {"id": "case-2", "answer": "English", "policy": {"case": "sensitive"},
     "typed": "English", "expect": True, "reason": "ok"},
    {"id": "case-3", "answer": "English", "typed": "english",
     "expect": True, "reason": "ok",
     "note": {"ru": "Если регистр не объявлен значимым, он не проверяется.",
              "en": "Unless declared significant, case is ignored."}},

    # --- диакритика ---------------------------------------------------------
    {"id": "stress-1", "answer": "café", "policy": {"stress": "significant"},
     "typed": "cafe", "expect": False, "reason": "stress",
     "note": {"ru": "Диакритика значима, если задание об этом говорит.",
              "en": "A diacritic matters when the task says so."}},
    {"id": "stress-2", "answer": "café", "policy": {"stress": "ignore"},
     "typed": "cafe", "expect": True, "reason": "ok"},
    {"id": "stress-3", "answer": "café", "typed": "café", "expect": True, "reason": "ok"},

    # --- форма слова и лишние слова ----------------------------------------
    {"id": "form-1", "answer": "has lived", "typed": "lived",
     "expect": False, "reason": "near",
     "note": {"ru": "Похожая, но другая форма — отдельная причина отказа.",
              "en": "A similar but different form gets its own failure reason."}},
    {"id": "form-2", "answer": "going", "typed": "go",
     "expect": False, "reason": "near"},
    {"id": "extra-1", "answer": "where", "typed": "where is",
     "expect": False, "reason": "near",
     "note": {"ru": "Лишние слова не принимаются: сравнивается весь ответ.",
              "en": "Extra words are not accepted: the whole string is compared."}},
    {"id": "extra-2", "answer": "where", "typed": " where ",
     "expect": True, "reason": "ok",
     "note": {"ru": "Крайние пробелы обрезаются всегда.",
              "en": "Leading and trailing spaces are always trimmed."}},

    # --- пустой ввод --------------------------------------------------------
    {"id": "empty-1", "answer": "on", "typed": "",
     "expect": False, "reason": "empty"},
    {"id": "empty-2", "answer": "on", "typed": "   ",
     "expect": False, "reason": "empty"},
    {"id": "empty-3", "answer": "on", "typed": "on.", "expect": False, "reason": "near",
     "note": {"ru": "Точка в конце — лишний знак: ответ не принят и назван «почти совпавшим».",
              "en": "A trailing full stop is an extra sign: the answer fails as a near miss."}},

    # --- несколько допустимых вариантов ------------------------------------
    {"id": "multi-1", "answer": "achievement", "accepted": ["achievement"],
     "typed": "achievement", "expect": True, "reason": "ok"},
    {"id": "multi-2", "answer": "historic", "accepted": ["historic", "historical"],
     "typed": "historical", "expect": True, "reason": "ok",
     "note": {"ru": "Допустимые варианты перечислены в задании явно.",
              "en": "Accepted variants are listed in the task explicitly."}},
    {"id": "multi-3", "answer": "historic", "accepted": ["historic", "historical"],
     "typed": "historian", "expect": False, "reason": "near",
     "note": {"ru": "Другое слово того же семейства описывается как «почти совпало».",
              "en": "A different word of the same family is reported as a near miss."}},
]


def cases() -> list[dict]:
    return CASES
