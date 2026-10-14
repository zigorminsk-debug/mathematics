"""Shared answer-checker vector corpus (Python ↔ JavaScript ↔ Kotlin).

Every expected value below is written by hand from the checking contract and
the language minimal pair it documents — it is never computed by any checker.
These vectors test the technical equality contract only; language norms are
verified separately (tests/test_lexicon.py, tests/test_content.py).
"""
from __future__ import annotations


def _word(answer, *, accept=(), why=(), case="insensitive", yo="strict", hyphen="typographic"):
    spec = {"type": "word", "scoring": "exact", "order": "n/a", "answer": answer,
            "accept": list(accept), "case": case, "yo": yo, "hyphen": hyphen}
    if accept:
        spec["acceptWhy"] = {"ru": list(why), "en": list(why)}
    return spec


def _numbers(answer, maximum, order="unordered"):
    return {"type": "numbers", "scoring": "exact", "order": order, "max": maximum, "answer": list(answer)}


TAK_ZHE = _word("так же")
TAKZHE = _word("также")
TO_ZHE = _word("то же")
CHTOBY = _word("чтобы")
PO_NOVOMU = _word("по-новому")
PO_NOVOMU_STRICT = _word("по-новому", hyphen="strict")
YOLKA = _word("ёлка")
VSYO = _word("всё")
RESHYONNY = _word("решённый", yo="e-equals-yo")
MINSK = _word("Минск", case="sensitive")
ZAMOK = _word("замок")
NUMERAL = _word("пятьюстами сорока восемью", accept=["пятьюстами сорока восьмью"],
                why=["Лопатин В. В. (ред.), Русский орфографический словарь РАН: восемью и восьмью — равноправные формы"])
IDIOM = _word("сломя голову")
CHAIKA = _word("чайка")
ZVONIT = {"type": "stress", "scoring": "exact", "order": "n/a", "word": "звонит", "answer": 4, "display": "звони\u0301т"}
KATALOG = {"type": "stress", "scoring": "exact", "order": "n/a", "word": "каталог", "answer": 5, "display": "катало\u0301г"}
MULTI_13 = {"type": "multi", "scoring": "exact", "order": "unordered", "options": 5, "answer": [1, 3]}
MULTI_245 = {"type": "multi", "scoring": "exact", "order": "unordered", "options": 5, "answer": [2, 4, 5]}
SINGLE_2 = {"type": "single", "scoring": "exact", "order": "n/a", "options": 4, "answer": 2}
SET_25 = _numbers([2, 5], 6)
SET_3_11 = _numbers([3, 11], 12)
SEQ = _numbers([2, 1, 3, 5, 4], 5, "ordered")
MATCH = {"type": "match", "scoring": "exact", "order": "by-label", "labels": ["А", "Б", "В", "Г"], "right": 5,
         "answer": {"А": 3, "Б": 1, "В": 4, "Г": 2}}
INTEGER_3 = {"type": "integer", "scoring": "exact", "order": "n/a", "answer": 3}
UNKNOWN = {"type": "formula", "scoring": "exact", "order": "n/a", "answer": "x"}

CASES = [
    # significant spaces: также ≠ так же, тоже ≠ то же, чтобы ≠ что бы
    (TAK_ZHE, "так же", True, "exact phrase"),
    (TAK_ZHE, "также", False, "deleting the significant space changes the word"),
    (TAK_ZHE, "  так   же  ", True, "trim + one space for a run of spaces"),
    (TAK_ZHE, "так\u00a0же", True, "no-break space is a space"),
    (TAK_ZHE, "так\u200bже", False, "zero-width space is invisible, not a space"),
    (TAK_ZHE, "так\ufeffже", False, "U+FEFF is not whitespace"),
    (TAK_ZHE, "Так же", True, "case-insensitive policy"),
    (TAK_ZHE, "так-же", False, "a hyphen is not a space"),
    (TAK_ZHE, "так же.", False, "extra punctuation is not ignored"),
    (TAK_ZHE, "", False, "empty answer"),
    (TAKZHE, "также", True, "conjunction"),
    (TAKZHE, "так же", False, "adverb + particle is a different answer"),
    (TO_ZHE, "то же", True, "pronoun + particle"),
    (TO_ZHE, "тоже", False, "conjunction is a different answer"),
    (CHTOBY, "чтобы", True, "conjunction"),
    (CHTOBY, "что бы", False, "pronoun + particle is a different answer"),
    # hyphens: only typographic hyphens are equivalent, dashes/minus never
    (PO_NOVOMU, "по-новому", True, "ASCII hyphen-minus"),
    (PO_NOVOMU, "по\u2010новому", True, "U+2010 hyphen under the typographic policy"),
    (PO_NOVOMU, "по\u2011новому", True, "U+2011 non-breaking hyphen under the typographic policy"),
    (PO_NOVOMU, "по\u2013новому", False, "en dash is not a hyphen"),
    (PO_NOVOMU, "по\u2014новому", False, "em dash is not a hyphen"),
    (PO_NOVOMU, "по\u2212новому", False, "minus sign is not a hyphen"),
    (PO_NOVOMU, "по новому", False, "hyphen is never erased"),
    (PO_NOVOMU, "поновому", False, "hyphen is never erased"),
    (PO_NOVOMU, "по - новому", False, "spaces around a hyphen are significant"),
    (PO_NOVOMU_STRICT, "по\u2010новому", False, "strict policy keeps only the canonical hyphen"),
    (PO_NOVOMU_STRICT, "по-новому", True, "strict policy, canonical hyphen"),
    # ё is not globally interchangeable with е
    (YOLKA, "ёлка", True, "exact"),
    (YOLKA, "елка", False, "strict ё policy"),
    (YOLKA, "ЁЛКА", True, "case-insensitive"),
    (YOLKA, "е\u0308лка", True, "decomposed ё is composed by NFC"),
    (VSYO, "все", False, "всё and все are different words"),
    (RESHYONNY, "решенный", True, "explicit e-equals-yo policy"),
    (RESHYONNY, "решённый", True, "explicit e-equals-yo policy"),
    (RESHYONNY, "решеный", False, "Н/НН is still checked"),
    # case
    (MINSK, "Минск", True, "proper name"),
    (MINSK, "минск", False, "case-sensitive policy"),
    (MINSK, "МИНСК", False, "case-sensitive policy"),
    # stress marks in a word answer are not silently stripped
    (ZAMOK, "замок", True, "plain word"),
    (ZAMOK, "за\u0301мок", False, "stress mark is never deleted as noise"),
    (ZAMOK, "замо\u0300к", False, "grave mark is rejected"),
    # justified alternatives only; no keyword or regex leniency
    (NUMERAL, "пятьюстами сорока восемью", True, "canonical form"),
    (NUMERAL, "пятьюстами сорока восьмью", True, "documented equivalent form"),
    (NUMERAL, "пятьюстами  сорока восемью", True, "double space collapses to one"),
    (NUMERAL, "пятьюстамисорока восемью", False, "missing significant space"),
    (NUMERAL, "сорока пятьюстами восемью", False, "word order"),
    (NUMERAL, "пятистами сорока восемью", False, "wrong case form"),
    (NUMERAL, "пятьюстами сорока восемь", False, "wrong case form"),
    (IDIOM, "сломя голову", True, "exact phraseological unit"),
    (IDIOM, "бежать сломя голову", False, "extra word is not accepted"),
    (IDIOM, "сломя", False, "missing word is not accepted"),
    (IDIOM, "голову сломя", False, "word order"),
    (CHAIKA, "чаи\u0306ка", True, "decomposed й is composed by NFC"),
    # stress tasks: composed/decomposed marks and the capital-vowel convention
    (ZVONIT, "звони\u0301т", True, "acute after the stressed vowel"),
    (ZVONIT, "звонИт", True, "capitalised stressed vowel"),
    (ZVONIT, "зво\u0301нит", False, "wrong syllable"),
    (ZVONIT, "звОнит", False, "wrong syllable"),
    (ZVONIT, "звонит", False, "no stress marked"),
    (ZVONIT, "ЗВОНИТ", False, "all capitals mark nothing"),
    (ZVONIT, "Звонит", False, "a capital consonant marks nothing"),
    (ZVONIT, "звони\u0301\u0301т", False, "two stress marks"),
    (ZVONIT, "звони\u0300т", False, "grave accent is not the stress mark"),
    (ZVONIT, "звон\u0301ит", False, "stress mark after a consonant"),
    (ZVONIT, "звони\u0301т ", True, "trailing space is trimmed"),
    (ZVONIT, "звоня\u0301т", False, "a different word form"),
    (KATALOG, "катало\u0301г", True, "acute after the stressed vowel"),
    (KATALOG, "ката\u0301лог", False, "wrong syllable"),
    (KATALOG, "каталОг", True, "capitalised stressed vowel"),
    # part A: several correct options out of five
    (MULTI_13, "13", True, "concatenated digits"),
    (MULTI_13, "31", True, "any order"),
    (MULTI_13, "1,3", True, "comma separator"),
    (MULTI_13, "3; 1", True, "semicolon separator"),
    (MULTI_13, "13 ", True, "trailing space"),
    (MULTI_13, "1", False, "missing selection"),
    (MULTI_13, "134", False, "extra selection never equals the correct subset"),
    (MULTI_13, "113", False, "duplicates are invalid, not de-duplicated"),
    (MULTI_13, "136", False, "option out of range"),
    (MULTI_13, "0 1 3", False, "zero is not an option"),
    (MULTI_13, "13 x", False, "garbage"),
    (MULTI_13, "\uff11\uff13", False, "full-width digits are not accepted"),
    (MULTI_13, "1 3 5", False, "extra selection"),
    (MULTI_245, "542", True, "any order"),
    (MULTI_245, "24", False, "missing selection"),
    (MULTI_245, "2345", False, "extra selection"),
    (SINGLE_2, "2", True, "single option"),
    (SINGLE_2, "02", False, "leading zero"),
    (SINGLE_2, "2 2", False, "duplicate"),
    (SINGLE_2, "23", False, "two options for a single choice"),
    # numbered places: unordered sets and ordered sequences
    (SET_25, "25", True, "concatenated, max <= 9"),
    (SET_25, "52", True, "unordered"),
    (SET_25, "2, 5", True, "separated"),
    (SET_25, "2 5 6", False, "extra place"),
    (SET_25, "2", False, "missing place"),
    (SET_3_11, "3 11", True, "separated two-digit place"),
    (SET_3_11, "11, 3", True, "unordered"),
    (SET_3_11, "311", False, "concatenation is ambiguous when max >= 10"),
    (SET_3_11, "3,11,", True, "trailing separator"),
    (SET_3_11, "03 11", False, "leading zero"),
    (SET_3_11, "3 11 12", False, "extra place"),
    (SEQ, "21354", True, "ordered sequence"),
    (SEQ, "2 1 3 5 4", True, "ordered sequence, separated"),
    (SEQ, "12345", False, "order is the answer"),
    (SEQ, "2135", False, "missing element"),
    (SEQ, "213544", False, "duplicate element"),
    # matching
    (MATCH, "А3Б1В4Г2", True, "canonical"),
    (MATCH, "а3б1в4г2", True, "labels are case-insensitive"),
    (MATCH, "А3 Б1 В4 Г2", True, "spaces"),
    (MATCH, "Г2В4Б1А3", True, "pairs in any order"),
    (MATCH, "А-3, Б-1, В-4, Г-2", True, "hyphen/comma separators"),
    (MATCH, "А3Б1В4", False, "missing label"),
    (MATCH, "А3Б1В4Г2А3", False, "duplicate label"),
    (MATCH, "А3Б1В4Г6", False, "number out of range"),
    (MATCH, "A3Б1В4Г2", False, "Latin A is not the Cyrillic label"),
    (MATCH, "А3Б1В4Г2Д5", False, "unknown label"),
    (MATCH, "А3Б1В2Г4", False, "wrong mapping"),
    # integers
    (INTEGER_3, "3", True, "integer"),
    (INTEGER_3, " 3 ", True, "trimmed"),
    (INTEGER_3, "03", False, "leading zero"),
    (INTEGER_3, "+3", False, "sign"),
    (INTEGER_3, "3.0", False, "decimal"),
    (INTEGER_3, "три", False, "word"),
    (INTEGER_3, "", False, "empty"),
    # unknown types fail closed
    (UNKNOWN, "x", False, "unknown check type"),
]


def payload() -> dict:
    return {"schema": 2, "cases": [
        {"id": f"v{index:03d}", "check": spec, "user": user, "expect": expect, "why": why}
        for index, (spec, user, expect, why) in enumerate(CASES, 1)]}
