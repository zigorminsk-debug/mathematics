"""kit.py — content model of the Russian-language tutor.

* 13 study AREAS (the subject handoff list) — practice/statistics/study topics;
* 9 RIKZ SECTIONS with the 2026 specification quotas (13/9/2/3/1/2/4/3/3);
* RULES — every task links to concrete rule cards (lessons), not only to an area;
* BLUEPRINT — the authored 40-slot plan (18 A + 22 B) of every practice variant;
* ``task()`` — the single constructor; ``validate_task()`` fails closed.

Checked Russian material (``text``/``items``) is language-neutral and is never
translated: the RU/EN switch changes only ``instruction``/``solution``/hints.
"""
from __future__ import annotations

import re

import checker


def bi(ru: str, en: str) -> dict:
    return {"ru": ru, "en": en}


AREAS = {
    "phonetics": bi("Фонетика, ударение, орфоэпия", "Phonetics, stress, pronunciation"),
    "lexis": bi("Лексика, паронимы, фразеология", "Vocabulary, paronyms, idioms"),
    "morphemics": bi("Морфемика и словообразование", "Morphemes and word formation"),
    "roots": bi("Орфография корней", "Spelling of roots"),
    "prefixes": bi("Приставки, Ъ и Ь, И/Ы", "Prefixes, Ъ and Ь, И/Ы"),
    "suffixes": bi("Суффиксы, окончания, части речи", "Suffixes, endings, parts of speech"),
    "spelling-ne": bi("Н/НН, НЕ/НИ, слитно, раздельно, через дефис", "Н/НН, НЕ/НИ, solid, separate, hyphenated"),
    "morph-norms": bi("Морфологические нормы", "Morphological norms"),
    "grammar-norms": bi("Грамматические (синтаксические) нормы", "Grammatical (syntactic) norms"),
    "simple-sentence": bi("Простое предложение и его пунктуация", "The simple sentence and its punctuation"),
    "complex-sentence": bi("Сложное предложение и его пунктуация", "The complex sentence and its punctuation"),
    "direct-speech": bi("Прямая речь, диалог, цитаты", "Direct speech, dialogue, quotations"),
    "text": bi("Текст: тема, связь, стили и типы речи", "Text: theme, cohesion, styles and types"),
}
AREA_ORDER = list(AREAS)

SECTIONS = {
    "orthography": (bi("Орфография (включая правописание частей речи)", "Spelling (including parts of speech)"), 13),
    "punctuation": (bi("Пунктуация", "Punctuation"), 9),
    "lexis": (bi("Лексика", "Vocabulary"), 2),
    "speech": (bi("Культура речи", "Speech norms"), 3),
    "phonetics": (bi("Фонетика", "Phonetics"), 1),
    "word": (bi("Состав слова. Образование слов", "Word structure and formation"), 2),
    "morphology": (bi("Морфология", "Morphology"), 4),
    "syntax": (bi("Синтаксис", "Syntax"), 3),
    "text": (bi("Текст. Стили речи", "Text. Styles"), 3),
}

# rule id -> (area, ru title, en title)
RULES = {
    "sounds-letters": ("phonetics", "Звуки и буквы; е, ё, ю, я", "Sounds and letters; е, ё, ю, я"),
    "stress": ("phonetics", "Ударение: орфоэпическая норма", "Stress: pronunciation norm"),
    "word-meaning": ("lexis", "Лексическое значение; прямое и переносное", "Lexical meaning; literal and figurative"),
    "synonyms-antonyms": ("lexis", "Синонимы и антонимы", "Synonyms and antonyms"),
    "paronyms": ("lexis", "Паронимы", "Paronyms"),
    "phraseology": ("lexis", "Фразеологизмы", "Set phrases (idioms)"),
    "pleonasm": ("lexis", "Лексическая сочетаемость и плеоназм", "Collocation and pleonasm"),
    "morphemes": ("morphemics", "Морфемы, окончание, однокоренные слова", "Morphemes, endings, cognates"),
    "word-formation": ("morphemics", "Способы образования слов", "Ways of forming words"),
    "root-vowels": ("roots", "Безударные гласные в корне", "Unstressed vowels in roots"),
    "root-alt-oa": ("roots", "Корни с чередованием О/А", "Roots alternating О/А"),
    "root-alt-ei": ("roots", "Корни с чередованием Е/И", "Roots alternating Е/И"),
    "consonants": ("roots", "Проверяемые и непроизносимые согласные", "Checkable and silent consonants"),
    "double-consonants": ("roots", "Двойные согласные", "Double consonants"),
    "prefix-z-s": ("prefixes", "Приставки на З/С", "Prefixes ending in З/С"),
    "prefix-pre-pri": ("prefixes", "Приставки ПРЕ- и ПРИ-", "Prefixes ПРЕ- and ПРИ-"),
    "y-after-prefix": ("prefixes", "И/Ы после приставок", "И/Ы after prefixes"),
    "hard-soft-sign": ("prefixes", "Разделительные Ъ и Ь", "Separating Ъ and Ь"),
    "soft-sign-sibilants": ("prefixes", "Ь после шипящих", "Ь after hushing consonants"),
    "noun-endings": ("suffixes", "Падежные окончания существительных", "Case endings of nouns"),
    "noun-adj-suffixes": ("suffixes", "Суффиксы существительных и прилагательных", "Noun and adjective suffixes"),
    "o-yo-sibilants": ("suffixes", "О, Е, Ё после шипящих", "О, Е, Ё after hushing consonants"),
    "verb-endings": ("suffixes", "Личные окончания и суффиксы глаголов", "Verb endings and verb suffixes"),
    "tsya": ("suffixes", "-ТСЯ и -ТЬСЯ в глаголах", "-ТСЯ and -ТЬСЯ in verbs"),
    "participle-suffixes": ("suffixes", "Суффиксы и окончания причастий", "Participle suffixes and endings"),
    "adjectives": ("suffixes", "Имя прилагательное: разряды и формы", "Adjectives: classes and forms"),
    "function-words": ("suffixes", "Предлог, союз, частица", "Prepositions, conjunctions, particles"),
    "verb-aspect": ("suffixes", "Вид глагола", "Verb aspect"),
    "n-nn": ("spelling-ne", "Н и НН в словах разных частей речи", "Н and НН in different parts of speech"),
    "ne-parts": ("spelling-ne", "НЕ с разными частями речи", "НЕ with different parts of speech"),
    "ne-ni": ("spelling-ne", "Частицы НЕ и НИ", "Particles НЕ and НИ"),
    "hyphen-compounds": ("spelling-ne", "Слитно или через дефис: существительные и прилагательные",
                         "Solid or hyphenated nouns and adjectives"),
    "adverbs": ("spelling-ne", "Наречия: слитно, раздельно, через дефис", "Adverbs: solid, separate, hyphenated"),
    "prep-conj-particles": ("spelling-ne", "Предлоги, союзы, частицы: слитно или раздельно",
                            "Prepositions, conjunctions, particles: solid or separate"),
    "noun-declension": ("morph-norms", "Склонение существительных", "Noun declension"),
    "numerals": ("morph-norms", "Склонение и употребление числительных", "Declension and use of numerals"),
    "government": ("grammar-norms", "Управление и предлоги с падежами", "Government and prepositions with cases"),
    "participial-gerund": ("grammar-norms", "Обороты и однородные члены: грамматическая норма",
                           "Participial/adverbial phrases and homogeneous parts: the norm"),
    "phrases": ("simple-sentence", "Словосочетание: согласование, управление, примыкание",
                "Phrases: agreement, government, adjunction"),
    "sentence-members": ("simple-sentence", "Члены предложения и типы сказуемого", "Sentence parts and predicate types"),
    "dash-subject": ("simple-sentence", "Тире между подлежащим и сказуемым", "Dash between subject and predicate"),
    "homogeneous": ("simple-sentence", "Однородные члены предложения", "Homogeneous parts of a sentence"),
    "isolation": ("simple-sentence", "Обособленные определения, приложения, обстоятельства",
                  "Set-off attributes, appositions, adverbials"),
    "introductory": ("simple-sentence", "Вводные слова и обращения", "Parenthetical words and address"),
    "kak": ("simple-sentence", "Конструкции с КАК", "Constructions with КАК"),
    "compound": ("complex-sentence", "Сложносочинённое предложение", "Compound sentence"),
    "complex": ("complex-sentence", "Сложноподчинённое предложение", "Complex sentence"),
    "asyndetic": ("complex-sentence", "Бессоюзное сложное предложение", "Asyndetic complex sentence"),
    "mixed": ("complex-sentence", "Сложное предложение с разными видами связи", "Sentences with mixed links"),
    "complex-types": ("complex-sentence", "Виды сложных предложений и их строение", "Types of complex sentences"),
    "direct-speech": ("direct-speech", "Прямая речь, диалог, цитаты", "Direct speech, dialogue, quotations"),
    "text-subtopics": ("text", "Тема, основная мысль, подтемы текста", "Theme, main idea, subtopics"),
    "text-cohesion": ("text", "Средства связи предложений в тексте", "Cohesion between sentences"),
    "text-styles": ("text", "Стили и типы речи", "Styles and types of speech"),
}
RULE_ORDER = list(RULES)

# Authored difficulty estimate per slot, distributed exactly like the
# specification (I-4, II-10, III-16, IV-6, V-4). Not an official RIKZ rating.
LEVELS = {
    "A1": 2, "A2": 2, "A3": 3, "A4": 3, "A5": 3, "A6": 2, "A7": 3, "A8": 3, "A9": 1, "A10": 3,
    "A11": 2, "A12": 2, "A13": 3, "A14": 3, "A15": 4, "A16": 3, "A17": 3, "A18": 3,
    "B1": 3, "B2": 1, "B3": 2, "B4": 3, "B5": 3, "B6": 2, "B7": 2, "B8": 4, "B9": 1, "B10": 4,
    "B11": 4, "B12": 3, "B13": 5, "B14": 2, "B15": 1, "B16": 4, "B17": 5, "B18": 5, "B19": 2,
    "B20": 4, "B21": 3, "B22": 5,
}

# 40 slots: (slot, section). The generator for each slot lives in generate.py.
BLUEPRINT = [
    ("A1", "orthography"), ("A2", "orthography"), ("A3", "orthography"), ("A4", "orthography"),
    ("A5", "orthography"), ("A6", "orthography"), ("A7", "orthography"), ("A8", "orthography"),
    ("A9", "punctuation"), ("A10", "punctuation"), ("A11", "punctuation"), ("A12", "punctuation"),
    ("A13", "punctuation"), ("A14", "punctuation"), ("A15", "punctuation"), ("A16", "punctuation"),
    ("A17", "text"), ("A18", "text"),
    ("B1", "text"), ("B2", "lexis"), ("B3", "orthography"), ("B4", "orthography"), ("B5", "phonetics"),
    ("B6", "morphology"), ("B7", "morphology"), ("B8", "morphology"), ("B9", "syntax"),
    ("B10", "orthography"), ("B11", "orthography"), ("B12", "orthography"), ("B13", "punctuation"),
    ("B14", "lexis"), ("B15", "morphology"), ("B16", "speech"), ("B17", "speech"), ("B18", "speech"),
    ("B19", "word"), ("B20", "word"), ("B21", "syntax"), ("B22", "syntax"),
]

_ID = re.compile(r"[a-z0-9][a-z0-9-]{1,60}")
_FIELDS = {"id", "kind", "year", "part", "n", "section", "topic", "rule", "rules", "itemRules", "level",
           "instruction", "text", "items", "choices", "check", "solution", "hints", "tags", "src"}


def lines(ru: list[str], en: list[str]) -> dict:
    return {"ru": list(ru), "en": list(en)}


def task(*, id: str, rule: str, instruction: dict, check: dict, solution: dict, kind: str = "analog",
         rules: list[str] | None = None, text: str | None = None, items: list[str] | None = None,
         choices: dict | None = None,
         item_rules: list[str] | None = None, hints: dict | None = None, tags: list[str] | None = None,
         year: int | None = None, slot: str | None = None, section: str | None = None,
         level: int | None = None) -> dict:
    entry = {
        "id": id, "kind": kind, "topic": RULES[rule][0], "rule": rule,
        "rules": list(dict.fromkeys([rule, *(rules or []), *(item_rules or [])])),
        "instruction": instruction, "check": check, "solution": solution,
        "hints": hints or {"ru": [], "en": []}, "tags": list(tags or []), "src": "authored",
    }
    if text is not None:
        entry["text"] = text
    if items is not None:
        entry["items"] = list(items)
    if choices is not None:
        entry["choices"] = {"ru": list(choices["ru"]), "en": list(choices["en"])}
    if item_rules is not None:
        entry["itemRules"] = list(item_rules)
    if slot:
        entry.update(year=year, part=slot[0], n=int(slot[1:]), section=section, level=level)
    elif level is not None:
        entry["level"] = level
    return entry


def _bilingual(value, field: str, *, lists=False) -> None:
    if not isinstance(value, dict) or set(value) != {"ru", "en"}:
        raise ValueError(f"{field} must be bilingual {{ru, en}}")
    if lists:
        if not all(isinstance(value[lang], list) for lang in ("ru", "en")) or len(value["ru"]) != len(value["en"]):
            raise ValueError(f"{field}: parallel RU/EN paragraph lists are required")
        if any(not isinstance(text, str) or not text.strip() for lang in ("ru", "en") for text in value[lang]):
            raise ValueError(f"{field}: empty paragraph")
    elif any(not isinstance(value[lang], str) or not value[lang].strip() for lang in ("ru", "en")):
        raise ValueError(f"{field}: empty translation")


def validate_task(entry: dict) -> dict:
    tid = entry.get("id", "?")
    try:
        if set(entry) - _FIELDS:
            raise ValueError(f"unexpected fields {sorted(set(entry) - _FIELDS)}")
        if not isinstance(tid, str) or not _ID.fullmatch(tid):
            raise ValueError("invalid id")
        if entry["kind"] not in ("variant", "analog"):
            raise ValueError("kind must be variant/analog")
        if entry["rule"] not in RULES or any(rule not in RULES for rule in entry["rules"]):
            raise ValueError("unknown rule link")
        if entry["topic"] != RULES[entry["rule"]][0]:
            raise ValueError("topic must be the area of the primary rule")
        _bilingual(entry["instruction"], "instruction")
        _bilingual(entry["solution"], "solution", lists=True)
        _bilingual(entry["hints"], "hints", lists=True)
        if len(entry["solution"]["ru"]) < 2:
            raise ValueError("a meaningful worked analysis has at least two steps")
        for field in ("text",):
            if field in entry and (not isinstance(entry[field], str) or not entry[field].strip()):
                raise ValueError("original Russian text must be a plain string (never translated)")
        items = entry.get("items")
        if items is not None and (not isinstance(items, list) or not items or
                                  any(not isinstance(item, str) or not item.strip() for item in items)):
            raise ValueError("items must be plain Russian strings")
        if "itemRules" in entry and (items is None or len(entry["itemRules"]) != len(items)):
            raise ValueError("itemRules must align with items")
        if "choices" in entry:
            _bilingual(entry["choices"], "choices", lists=True)
        spec = checker.validate(entry["check"])
        if spec["type"] in ("multi", "single"):
            options = items if items is not None else (entry.get("choices") or {}).get("ru")
            if options is None or len(options) != spec["options"] or (items is not None and "choices" in entry):
                raise ValueError("options come from items (Russian) or choices (bilingual) and match the count")
        if spec["type"] == "match":
            if items is None or len(items) != len(spec["labels"]) or len(entry.get("choices", {}).get("ru", [])) != spec["right"]:
                raise ValueError("match: items = left column, choices = right column")
        if spec["type"] == "numbers" and items is not None and len(items) != spec["max"] and "text" not in entry:
            raise ValueError("numbered items must match max")
        if entry["kind"] == "variant":
            slot = f"{entry['part']}{entry['n']}"
            if entry["section"] not in SECTIONS or (slot, entry["section"]) not in BLUEPRINT:
                raise ValueError("variant slot/section is not in the blueprint")
            if entry["part"] == "A" and spec["type"] != "multi":
                raise ValueError("part A uses several-of-five choice")
            if entry["part"] == "B" and spec["type"] in ("multi", "single"):
                raise ValueError("part B answers are written (word/digits/letters+digits)")
            if entry["level"] != LEVELS[slot]:
                raise ValueError("level must follow the authored blueprint")
        # The correct answer must itself be accepted by the reference checker.
        if not checker.check(_sample_answer(spec), spec):
            raise ValueError("the canonical answer is not accepted by the checker")
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"task {tid}: {error}") from error
    return entry


def _sample_answer(spec: dict) -> str:
    kind = spec["type"]
    if kind in ("multi", "numbers"):
        return " ".join(str(value) for value in spec["answer"])
    if kind in ("single", "integer"):
        return str(spec["answer"])
    if kind == "word":
        return spec["answer"]
    if kind == "stress":
        return spec["display"]
    return "".join(f"{label}{spec['answer'][label]}" for label in spec["labels"])
