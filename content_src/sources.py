"""Normative sources and what exactly was verified (honest status per source).

``status``:
  * ``checked`` — the source was actually opened/queried for this release
    (date recorded); the listed facts were compared with it;
  * ``automated`` — used by an automatic gate in CI (version recorded);
  * ``reference`` — the standard normative reference the rule formulations
    follow; bank items are authored, not copied, and disputed items were
    excluded from the bank instead of being made artificially unambiguous.
"""
from __future__ import annotations

SOURCES = {
    "spec2026": {
        "title": "Спецификация экзаменационной (тестовой) работы по учебному предмету «Русский язык» для проведения ЦЭ "
                 "и ЦТ в 2026 году (утв. 03.11.2025; РИКЗ)",
        "url": "https://rikc.by/ru/specification/2026/01.pdf", "status": "checked", "date": "2026-10-14",
        "facts": "40 заданий (A — 18, B — 22), 120 минут, 9 разделов и их квоты, уровни сложности, программный материал",
    },
    "adukar2025": {
        "title": "Адукар: «Вопросы в тестах ЦЭ/ЦТ по русскому языку 2025 года» (перечень тем А1–А18, В1–В22)",
        "url": "https://adukar.com/by/news/abiturientu/voprosy-ce-ct-po-russkomu-yazyku-2025-goda",
        "status": "checked", "date": "2026-10-14",
        "facts": "тематическое наполнение позиций варианта; использовано только как ориентир для авторского плана",
    },
    "gorbachevich": {
        "title": "Словарь трудностей произношения и ударения в современном русском языке (статья «восемь», цитата на "
                 "lopatin.academic.ru)",
        "url": "https://lopatin.academic.ru/17635/", "status": "checked", "date": "2026-10-14",
        "facts": "твор. п. «восемью и восьмью» — обе формы допустимы (обоснование альтернативного ответа)",
    },
    "opencorpora": {
        "title": "Морфологический словарь OpenCorpora через pymorphy3 2.0.6 и pymorphy3-dicts-ru (tests/test_lexicon.py)",
        "url": "https://pypi.org/project/pymorphy3/", "status": "automated", "date": "2026-10-14",
        "facts": "каждое правильное написание орфографических упражнений — известная словоформа; ошибочные варианты "
                 "неизвестны, кроме явно перечисленных омонимов; вид глагола и часть речи сверяются по тегам",
    },
    "lopatin": {
        "title": "Правила русской орфографии и пунктуации. Полный академический справочник / под ред. В. В. Лопатина. "
                 "— М., 2006 (и переиздания)", "url": "", "status": "reference", "date": "",
        "facts": "формулировки орфографических и пунктуационных правил",
    },
    "rosenthal": {
        "title": "Розенталь Д. Э. Справочник по правописанию и литературной правке (многократные переиздания)",
        "url": "", "status": "reference", "date": "", "facts": "правила и исключения, нормы управления и согласования",
    },
    "rus-orfo": {
        "title": "Русский орфографический словарь РАН / отв. ред. В. В. Лопатин, О. Е. Иванова. — 4-е изд. — М., 2013",
        "url": "", "status": "reference", "date": "", "facts": "словарные написания, слитное/раздельное/дефисное написание",
    },
    "orthoepy": {
        "title": "Резниченко И. Л. Орфоэпический словарь русского языка: Произношение. Ударение. — М., 2003 (и переиздания)",
        "url": "", "status": "reference", "date": "",
        "facts": "ударения; в банк включены только слова с одним нормативным вариантом",
    },
    "ozhegov": {
        "title": "Ожегов С. И., Шведова Н. Ю. Толковый словарь русского языка. — 4-е изд. — М., 1997",
        "url": "", "status": "reference", "date": "", "facts": "лексические значения, прямое и переносное значение",
    },
    "paronyms": {
        "title": "Вишнякова О. В. Словарь паронимов русского языка. — М., 1984", "url": "", "status": "reference",
        "date": "", "facts": "значение и сочетаемость паронимов",
    },
    "phraseology": {
        "title": "Фразеологический словарь русского литературного языка / сост. А. И. Фёдоров. — М., 2008", "url": "",
        "status": "reference", "date": "", "facts": "значения фразеологизмов",
    },
    "tikhonov": {
        "title": "Тихонов А. Н. Словообразовательный словарь русского языка: в 2 т. — М., 1985", "url": "",
        "status": "reference", "date": "",
        "facts": "производящие слова; спорные случаи (договориться, разговориться) исключены из банка",
    },
    "grammar1980": {
        "title": "Русская грамматика: в 2 т. / гл. ред. Н. Ю. Шведова. — М.: Наука, 1980", "url": "",
        "status": "reference", "date": "", "facts": "морфемика, морфология, синтаксис",
    },
}


def payload() -> dict:
    return SOURCES
