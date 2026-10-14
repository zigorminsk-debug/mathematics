"""generate.py — authored variants (6 × 40 by the 2026 blueprint) and analogous
exercises for every concrete rule.

Answers are derived from the annotated material (fill letters, derived
solid/separate/hyphen category, braces of tested marks, stress marks,
transcriptions, text annotations) — never typed twice. Generation is
deterministic (seeded) so the committed banks are reproducible.
"""
from __future__ import annotations

from collections import Counter
import random
import re

import checker
import kit
from kit import LEVELS, bi, lines, task
import pools_language as PL
import pools_punctuation as PP
import pools_spelling as PS
import texts as TX

ACUTE = "\u0301"
STYLE_NOM = {"publicistic": ("публицистический", "journalistic"), "scientific": ("научный", "scientific"),
             "artistic": ("художественный", "literary"), "official": ("официально-деловой", "official"),
             "colloquial": ("разговорный", "colloquial")}
VOWELS = "аеёиоуыэюя"
LABELS = ["А", "Б", "В", "Г"]
USE: Counter = Counter()


# ------------------------------------------------------------------ checks
def c_multi(answer, options=5):
    return {"type": "multi", "scoring": "exact", "order": "unordered", "options": options, "answer": sorted(answer)}


def c_numbers(answer, maximum, order="unordered"):
    return {"type": "numbers", "scoring": "exact", "order": order, "max": maximum,
            "answer": list(answer) if order == "ordered" else sorted(answer)}


def c_single(answer, options):
    return {"type": "single", "scoring": "exact", "order": "n/a", "options": options, "answer": answer}


def c_integer(answer):
    return {"type": "integer", "scoring": "exact", "order": "n/a", "answer": answer}


def c_word(answer, *, accept=(), why_ru=(), why_en=(), case="insensitive", yo="strict", hyphen="typographic"):
    spec = {"type": "word", "scoring": "exact", "order": "n/a", "answer": answer, "accept": list(accept),
            "case": case, "yo": yo, "hyphen": hyphen}
    if accept:
        spec["acceptWhy"] = {"ru": list(why_ru), "en": list(why_en)}
    return spec


def c_stress(stressed):
    plain = stressed.replace(ACUTE, "")
    return {"type": "stress", "scoring": "exact", "order": "n/a", "word": plain, "answer": stressed.index(ACUTE) - 1,
            "display": stressed}


def c_match(answer, right):
    return {"type": "match", "scoring": "exact", "order": "by-label", "labels": LABELS[:len(answer)], "right": right,
            "answer": dict(answer)}


def shown(spec):
    return checker.display(spec)


# ---------------------------------------------------------------- helpers
def choose(rng, items, count, key=lambda item: item[0]):
    ranked = sorted(items, key=lambda item: (USE[key(item)], rng.random()))
    chosen = ranked[:count]
    for item in chosen:
        USE[key(item)] += 1
    return chosen


def mix(rng, positives, negatives, total, k, key=lambda item: item[0]):
    total = min(total, len(positives) + len(negatives))
    k = max(1, min(k, len(positives), total - 1))
    k = max(k, total - len(negatives))
    chosen = choose(rng, positives, k, key) + choose(rng, negatives, total - k, key)
    rng.shuffle(chosen)
    return chosen


def answer_line(spec):
    return f"Ответ: {shown(spec)}", f"Answer: {shown(spec)}"


def numbered_text(sentences):
    return " ".join(f"({index}) {sentence}" for index, sentence in enumerate(sentences, 1))


NUMBERS_NOTE = ("Запишите номера цифрами, например: 135.", "Write the numbers as digits, e.g. 135.")


def variant_meta(year, slot):
    section = dict(kit.BLUEPRINT)[slot]
    return {"kind": "variant", "year": year, "slot": slot, "section": section, "level": LEVELS[slot]}


def build(tid, rule, instruction, check, intro, entries_lines, *, meta=None, hints=None, **extra):
    """Assemble one task with a worked analysis: intro, one line per item, answer."""
    ru_lines = [intro[0]] + [line[0] for line in entries_lines]
    en_lines = [intro[1]] + [line[1] for line in entries_lines]
    final = answer_line(check)
    ru_lines.append(final[0])
    en_lines.append(final[1])
    entry = task(id=tid, rule=rule, instruction=bi(*instruction), check=check, solution=lines(ru_lines, en_lines),
                 hints=lines(*(hints or ([], []))), **(meta or {}), **extra)
    return kit.validate_task(entry)


# ------------------------------------------------------------- spelling gaps
WORDCHARS = re.compile(r"[А-Яа-яЁё]*\.\.[А-Яа-яЁё]*")


def gap_items(pool_name):
    pool = PS.GAP[pool_name]
    out = []
    for raw in pool["items"]:
        masked, fill, code = raw[:3]
        note = raw[3] if len(raw) > 3 else None
        reason = pool["reasons"][code]
        token = WORDCHARS.search(masked).group(0)
        out.append({"masked": masked, "fill": fill, "full": masked.replace("..", fill),
                    "word": token.replace("..", fill), "code": code, "rule": reason["rule"],
                    "ru": reason["ru"], "en": reason["en"], "note": note})
    return out


def gap_line(index, item):
    fill_ru = f"пишется «{item['fill']}»" if item["fill"] else "ничего не пишется"
    fill_en = f"write «{item['fill']}»" if item["fill"] else "nothing is written"
    ru = f"{index}) {item['full']}: {fill_ru} — {item['ru']}"
    en = f"{index}) {item['full']}: {fill_en} — {item['en']}"
    if item["note"]:
        ru += f"; проверочное слово: {item['note']}"
        en += f"; check word: {item['note']}"
    return ru, en


GAP_TARGETS = {
    # pool: unit, {target: (predicate, ru phrase, en phrase)}
    "root-oa": ("word", {"о": ("о",), "а": ("а",)}),
    "root-ei": ("word", {"и": ("и",), "е": ("е",)}),
    "double": ("word", {"double": (lambda fill: len(fill) == 2, "пишется удвоенная согласная", "a double consonant is written")}),
    "consonants": ("word", {"silent": (lambda fill: fill != "", "пишется непроизносимая согласная",
                                       "a silent consonant is written")}),
    "endings-suffixes": ("word", {"и": ("и",), "е": ("е",)}),
    "ne-ni": ("sentence", {"и": (lambda fill: fill == "и", "на месте пропуска пишется НИ", "the gap takes НИ"),
                           "е": (lambda fill: fill == "е", "на месте пропуска пишется НЕ", "the gap takes НЕ")}),
    "tsya": ("sentence", {"ть": (lambda fill: fill == "ть", "пишется -ться (с Ь)", "-ться (with Ь) is written"),
                          "т": (lambda fill: fill == "т", "пишется -тся (без Ь)", "-тся (without Ь) is written")}),
    "n-nn": ("word", {"нн": (lambda fill: fill == "нн", "пишется НН", "НН is written"),
                      "н": (lambda fill: fill == "н", "пишется одна Н", "a single Н is written")}),
    "o-yo": ("word", {"о": ("о",), "ё": ("ё",)}),
    "soft-sign": ("word", {"ь": (lambda fill: fill == "ь", "на месте пропуска пишется Ь", "the gap takes Ь"),
                           "": (lambda fill: fill == "", "Ь на месте пропуска не пишется", "no Ь is written")}),
    "verb-endings": ("word", {"е": ("е",), "и": ("и",)}),
    "pre-pri": ("word", {"и": (lambda fill: fill == "и", "пишется приставка ПРИ-", "the prefix is ПРИ-"),
                         "е": (lambda fill: fill == "е", "пишется приставка ПРЕ-", "the prefix is ПРЕ-")}),
    "prefix-z-s": ("word", {"с": ("с",), "з": ("з",)}),
    "hard-soft": ("word", {"ъ": ("ъ",), "ь": ("ь",)}),
    "y-after-prefix": ("word", {"ы": ("ы",), "и": ("и",)}),
}


def gap_target(pool_name, target):
    unit, targets = GAP_TARGETS[pool_name]
    spec = targets[target]
    if len(spec) == 1:
        letter = spec[0]
        return unit, (lambda fill: fill == letter), f"на месте пропуска пишется буква «{letter}»", \
            f"the gap takes the letter «{letter}»"
    return (unit, *spec)


def gap_choice_task(tid, pool_name, target, rng, *, part, total, k, rule=None, meta=None, restrict=None):
    unit, predicate, phrase_ru, phrase_en = gap_target(pool_name, target)
    items = gap_items(pool_name)
    if restrict:
        items = [item for item in items if item["rule"] == restrict]
    pos = [item for item in items if predicate(item["fill"])]
    neg = [item for item in items if not predicate(item["fill"])]
    chosen = mix(rng, pos, neg, total, k, key=lambda item: item["masked"])
    answer = [index for index, item in enumerate(chosen, 1) if predicate(item["fill"])]
    noun_ru = "слова" if unit == "word" else "предложения"
    noun_en = "words" if unit == "word" else "sentences"
    if part == "A":
        instruction = (f"Укажите {noun_ru}, в которых {phrase_ru}.", f"Mark the {noun_en} in which {phrase_en}.")
        check = c_multi(answer, len(chosen))
    else:
        instruction = (f"Укажите номера: {noun_ru}, в которых {phrase_ru}. {NUMBERS_NOTE[0]}",
                       f"Give the numbers of the {noun_en} in which {phrase_en}. {NUMBERS_NOTE[1]}")
        check = c_numbers(answer, len(chosen))
    rules = [item["rule"] for item in chosen]
    primary = rule or Counter(rules).most_common(1)[0][0]
    return build(tid, primary, instruction, check,
                 ("Восстановим написание каждого слова и назовём правило.", "Restore each spelling and name the rule."),
                 [gap_line(index, item) for index, item in enumerate(chosen, 1)], meta=meta,
                 hints=(["Сначала определите часть слова с пропуском, затем примените правило."],
                        ["Find the part of the word with the gap first, then apply the rule."]),
                 items=[item["masked"] for item in chosen], item_rules=rules)


def gap_word_task(tid, item, pool_name):
    yo = "strict" if pool_name == "o-yo" else "e-equals-yo"
    instruction = (f"Вставьте пропущенную букву (буквы) и запишите слово с пропуском целиком: «{item['masked']}».",
                   f"Fill in the missing letter(s) and write the whole word that has the gap: «{item['masked']}».")
    return build(tid, item["rule"], instruction, c_word(item["word"], yo=yo),
                 ("Найдём правило для пропуска.", "Find the rule for the gap."), [gap_line(1, item)],
                 hints=([item["ru"].split(":")[0] + "."], [item["en"].split(":")[0] + "."]), text=item["masked"])


# ---------------------------------------------------------------- brackets
FRAGMENT = re.compile(r"([А-Яа-яЁё]*)\(([А-Яа-яЁё]+)\)([А-Яа-яЁё]*)")
CATEGORY = {"solid": ("слитно", "solid"), "separate": ("раздельно", "separately"), "hyphen": ("через дефис", "with a hyphen")}


def bracket_items(pool_name):
    pool = PS.BRACKET[pool_name]
    out = []
    for text, full, code in pool["items"]:
        match = FRAGMENT.search(text)
        left, inside, right = match.groups()
        if left and right:
            raise ValueError(f"ambiguous bracket fragment in {text!r}")
        first, second = (inside, right) if not left else (left, inside)
        if full == first + second:
            category = "solid"
        elif full == first + " " + second:
            category = "separate"
        elif full == first + "-" + second:
            category = "hyphen"
        else:
            raise ValueError(f"{text!r}: {full!r} is not a spelling of the bracketed fragment")
        reason = pool["reasons"][code]
        out.append({"text": text, "full": full, "category": category, "rule": reason["rule"], "ru": reason["ru"],
                    "en": reason["en"], "corrected": text[:match.start()] + full + text[match.end():]})
    return out


def bracket_line(index, item):
    cat = CATEGORY[item["category"]]
    return (f"{index}) {item['corrected']} — {cat[0]}: {item['ru']}", f"{index}) {item['corrected']} — {cat[1]}: {item['en']}")


BRACKET_PHRASES = {
    "ne-parts": ("НЕ со словом пишется {cat}", "НЕ is written {cat}"),
    "hyphen": ("слово пишется {cat}", "the word is written {cat}"),
    "prep-conj": ("выделенное слово (сочетание) пишется {cat}", "the bracketed word is written {cat}"),
}


def bracket_choice_task(tid, pool_name, category, rng, *, part, total, k, meta=None, restrict=None, rule=None):
    items = bracket_items(pool_name)
    if restrict:
        items = [item for item in items if item["rule"] == restrict]
    pos = [item for item in items if item["category"] == category]
    neg = [item for item in items if item["category"] != category]
    chosen = mix(rng, pos, neg, total, k, key=lambda item: item["text"])
    answer = [index for index, item in enumerate(chosen, 1) if item["category"] == category]
    phrase = BRACKET_PHRASES[pool_name]
    ru = phrase[0].format(cat=CATEGORY[category][0])
    en = phrase[1].format(cat=CATEGORY[category][1])
    if part == "A":
        instruction = (f"Раскройте скобки. Укажите варианты, в которых {ru}.", f"Open the brackets. Mark the items where {en}.")
        check = c_multi(answer, len(chosen))
    else:
        instruction = (f"Раскройте скобки. Укажите номера вариантов, в которых {ru}. {NUMBERS_NOTE[0]}",
                       f"Open the brackets. Give the numbers of the items where {en}. {NUMBERS_NOTE[1]}")
        check = c_numbers(answer, len(chosen))
    rules = [item["rule"] for item in chosen]
    return build(tid, rule or Counter(rules).most_common(1)[0][0], instruction, check,
                 ("Запишем каждое слово правильно и объясним написание.", "Write each item correctly and explain it."),
                 [bracket_line(index, item) for index, item in enumerate(chosen, 1)], meta=meta,
                 hints=(["Определите часть речи и проверьте условия правила (противопоставление, зависимые слова)."],
                        ["Identify the part of speech and check the conditions (contrast, dependent words)."]),
                 items=[item["text"] for item in chosen], item_rules=rules)


def bracket_word_task(tid, item):
    instruction = (f"Раскройте скобки и запишите выделенное слово (сочетание) правильно: «{item['text']}».",
                   f"Open the brackets and write the bracketed word correctly: «{item['text']}».")
    check = c_word(item["full"], yo="e-equals-yo")
    return build(tid, item["rule"], instruction, check,
                 ("Определим, слитно, раздельно или через дефис.", "Decide: solid, separate or hyphenated."),
                 [bracket_line(1, item)], text=item["text"],
                 hints=(["Пробел и дефис здесь — часть ответа: проверьте условие правила."],
                        ["A space or a hyphen is part of the answer here."]))


# ------------------------------------------------------------------- marks
MARKER = re.compile(r"\{([^{}]*)\}")
MARK_PHRASES = {
    "dash-subject": ("нужно поставить тире между подлежащим и сказуемым", "a dash is needed between subject and predicate"),
    "isolation": ("нужны запятые при обособленных членах предложения", "commas are needed around set-off parts"),
    "introductory": ("нужны запятые при вводных словах или обращениях", "commas are needed for parenthetical words or address"),
    "homogeneous": ("нужна запятая между однородными членами", "a comma is needed between homogeneous parts"),
    "comma-before-i": ("нужна запятая перед союзом И (другие знаки расставлены)", "a comma is needed before И (other marks are set)"),
    "kak": ("нужны запятые при обороте или придаточном с КАК", "commas are needed with the КАК phrase or clause"),
    "complex-commas": ("нужна запятая между частями сложноподчинённого предложения",
                       "a comma is needed between the parts of the complex sentence"),
}


def mark_items(pool_name):
    pool = PP.MARK[pool_name]
    out = []
    for sentence, code in pool["items"]:
        marks = MARKER.findall(sentence)
        display = re.sub(r" {2,}", " ", MARKER.sub(lambda m: " " if " " in m.group(1) else "", sentence))
        correct = MARKER.sub(lambda m: m.group(1), sentence)
        reason = pool["reasons"][code]
        out.append({"display": display, "correct": correct, "marks": marks, "rule": reason["rule"],
                    "ru": reason["ru"], "en": reason["en"], "code": code})
    return out


def mark_line(index, item):
    return f"{index}) {item['correct']} — {item['ru']}", f"{index}) {item['correct']} — {item['en']}"


def mark_choice_task(tid, pool_name, rng, *, part, total, k, target=None, meta=None, restrict=None, rule=None):
    items = mark_items(pool_name)
    if restrict:
        items = [item for item in items if item["rule"] == restrict]
    target = target or PP.MARK[pool_name]["target"]
    positive = (lambda item: target in item["marks"])
    pos = [item for item in items if positive(item)]
    neg = [item for item in items if not positive(item)]
    chosen = mix(rng, pos, neg, total, k, key=lambda item: item["display"])
    answer = [index for index, item in enumerate(chosen, 1) if positive(item)]
    if pool_name == "asyndetic":
        mark_ru, mark_en = {":": ("двоеточие", "a colon"), " — ": ("тире", "a dash")}[target]
        phrase = (f"на стыке частей бессоюзного предложения нужно поставить {mark_ru}",
                  f"{mark_en} is needed at the junction of the clauses")
    else:
        phrase = MARK_PHRASES[pool_name]
    if part == "A":
        instruction = (f"Укажите предложения, в которых {phrase[0]}.", f"Mark the sentences in which {phrase[1]}.")
        check = c_multi(answer, len(chosen))
    else:
        instruction = (f"Укажите номера предложений, в которых {phrase[0]}. {NUMBERS_NOTE[0]}",
                       f"Give the numbers of the sentences in which {phrase[1]}. {NUMBERS_NOTE[1]}")
        check = c_numbers(answer, len(chosen))
    rules = [item["rule"] for item in chosen]
    return build(tid, rule or Counter(rules).most_common(1)[0][0], instruction, check,
                 ("Расставим знаки и объясним каждое предложение.", "Punctuate each sentence and explain it."),
                 [mark_line(index, item) for index, item in enumerate(chosen, 1)], meta=meta,
                 hints=(["Найдите грамматическую основу и проверьте условия правила."],
                        ["Find the subject and predicate, then check the conditions of the rule."]),
                 items=[item["display"] for item in chosen], item_rules=rules)


def mark_count_task(tid, item):
    count = sum(1 for mark in item["marks"] if mark == ",")
    instruction = (f"Сколько запятых нужно поставить в предложении? «{item['display']}» Запишите число.",
                   f"How many commas does the sentence need? «{item['display']}» Write the number.")
    return build(tid, item["rule"], instruction, c_integer(count),
                 ("Найдём проверяемые конструкции.", "Find the constructions in question."), [mark_line(1, item)],
                 text=item["display"], hints=(["Обособленный оборот в середине выделяется с двух сторон."],
                                              ["A set-off phrase in the middle takes commas on both sides."]))


def asyndetic_single_task(tid, item):
    mark = item["marks"][0]
    options = {",": 1, ":": 2, " — ": 3}
    choices = {"ru": ["запятая", "двоеточие", "тире"], "en": ["a comma", "a colon", "a dash"]}
    instruction = (f"Какой знак нужен на стыке частей: «{item['display']}»?",
                   f"Which mark is needed at the junction: «{item['display']}»?")
    return build(tid, item["rule"], instruction, c_single(options[mark], 3),
                 ("Определим смысловые отношения между частями.", "Find the meaning relation between the clauses."),
                 [mark_line(1, item)], text=item["display"], choices=choices,
                 hints=(["Попробуйте вставить союз: «что», «потому что» — двоеточие; «поэтому», «если», «а» — тире."],
                        ["Try a conjunction: «что/потому что» → colon; «поэтому/если/а» → dash."]))


# -------------------------------------------------------------- statements
def statement_items():
    out = []
    for text, fix, code in PP.STATEMENTS:
        reason = PP.STATEMENT_REASONS[code]
        out.append({"text": text, "fix": fix, "ok": fix is None, "rule": reason["rule"], "ru": reason["ru"],
                    "en": reason["en"]})
    return out


def statement_line(index, item):
    if item["ok"]:
        return f"{index}) верно — {item['ru']}", f"{index}) correct — {item['en']}"
    return (f"{index}) неверно — {item['ru']}. Правильно: {item['fix']}",
            f"{index}) wrong — {item['en']}. Correct: {item['fix']}")


def statement_task(tid, rng, *, part, total, k, meta=None):
    items = statement_items()
    pos = [item for item in items if item["ok"]]
    neg = [item for item in items if not item["ok"]]
    chosen = mix(rng, pos, neg, total, k, key=lambda item: item["text"])
    answer = [index for index, item in enumerate(chosen, 1) if item["ok"]]
    if part == "A":
        instruction = ("Укажите предложения, в которых знаки препинания при прямой речи и цитате расставлены правильно.",
                       "Mark the sentences where direct speech or a quotation is punctuated correctly.")
        check = c_multi(answer, len(chosen))
    else:
        instruction = (f"Укажите номера предложений, в которых знаки препинания при прямой речи и цитате расставлены "
                       f"правильно. {NUMBERS_NOTE[0]}",
                       f"Give the numbers of the correctly punctuated sentences. {NUMBERS_NOTE[1]}")
        check = c_numbers(answer, len(chosen))
    return build(tid, "direct-speech", instruction, check,
                 ("Сверим каждое предложение со схемами прямой речи.", "Compare each sentence with the patterns."),
                 [statement_line(index, item) for index, item in enumerate(chosen, 1)], meta=meta,
                 items=[item["text"] for item in chosen],
                 hints=(["Где стоят слова автора: до, после или внутри прямой речи? Запятая и точка — после кавычек."],
                        ["Where are the author's words? Commas and periods go after the closing quotes."]))


# ----------------------------------------------------------------- numbered
def numbered_task(tid, entry, *, meta=None):
    text, commas, correct, notes_ru, notes_en = entry
    places = len(re.findall(r"\(\d+\)", text))
    instruction = (f"Укажите номера мест, где нужно поставить запятые. {NUMBERS_NOTE[0]}",
                   f"Give the numbers of the places that need commas. {NUMBERS_NOTE[1]}")
    reason = PP.NUMBERED_REASONS["mixed"]
    steps = [(f"Правильно: {correct}", f"Correct: {correct}")] + list(zip(notes_ru, notes_en))
    return build(tid, "mixed", instruction, c_numbers(commas, places),
                 (f"Выделим части и союзы: {reason['ru']}.", f"Find the clauses and conjunctions: {reason['en']}."),
                 steps, meta=meta, text=text, rules=["complex", "compound"],
                 hints=(["Сначала найдите все грамматические основы, затем границы частей."],
                        ["Find all subject–predicate pairs first, then the clause boundaries."]))


# -------------------------------------------------------- classification
def classify_task(tid, rule, entries, instruction, *, part="B", meta=None, intro, hints=None, text=None,
                  choices=None):
    """entries: (display, positive, line_ru, line_en)."""
    answer = [index for index, entry in enumerate(entries, 1) if entry[1]]
    check = c_multi(answer, len(entries)) if part == "A" else c_numbers(answer, len(entries))
    lines_ = [(f"{index}) {entry[2]}", f"{index}) {entry[3]}") for index, entry in enumerate(entries, 1)]
    extra = {"items": [entry[0] for entry in entries]} if choices is None else {"choices": choices}
    return build(tid, rule, instruction, check, intro, lines_, meta=meta, hints=hints, text=text, **extra)


def letters(word):
    return sum(1 for char in word if char.isalpha())


def two_sound_letters(word):
    out = []
    for index, char in enumerate(word):
        prev = word[index - 1] if index else ""
        if char in "еёюя" and (not prev or prev in VOWELS or prev in "ъь"):
            out.append(char)
        elif char == "и" and prev == "ь":
            out.append(char)
    return out


PHON_TYPES = {
    "more-letters": (lambda w, s: letters(w) > len(s.split()), "букв больше, чем звуков", "there are more letters than sounds"),
    "more-sounds": (lambda w, s: len(s.split()) > letters(w), "звуков больше, чем букв", "there are more sounds than letters"),
    "two-sounds": (lambda w, s: bool(two_sound_letters(w)), "буква е, ё, ю или я обозначает два звука",
                   "е, ё, ю or я stands for two sounds"),
}


def phonetics_task(tid, kind, rng, *, total=6, k=3, meta=None):
    test, phrase_ru, phrase_en = PHON_TYPES[kind]
    pos = [item for item in PL.PHONETICS if test(*item)]
    neg = [item for item in PL.PHONETICS if not test(*item)]
    chosen = mix(rng, pos, neg, total, k)
    entries = [(word, test(word, sounds), f"{word} [{sounds.replace(' ', '')}] — {letters(word)} букв, {len(sounds.split())} звуков",
                f"{word} [{sounds.replace(' ', '')}] — {letters(word)} letters, {len(sounds.split())} sounds")
               for word, sounds in chosen]
    return classify_task(tid, "sounds-letters", entries,
                         (f"Укажите номера слов, в которых {phrase_ru}. {NUMBERS_NOTE[0]}",
                          f"Give the numbers of the words in which {phrase_en}. {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Сравним буквы и звуки каждого слова.", "Compare letters and sounds."),
                         hints=(["Ь и Ъ звуков не обозначают; е, ё, ю, я в начале слова, после гласной и после Ь, Ъ дают два звука."],
                                ["Ь and Ъ are silent; е, ё, ю, я give two sounds initially, after a vowel and after Ь/Ъ."]))


def syllable(stressed):
    position = stressed.index(ACUTE) - 1
    return sum(1 for char in stressed[:position + 1] if char in VOWELS)


def stress_numbers_task(tid, target, rng, *, total=6, k=3, meta=None):
    pos = [word for word in PL.STRESS if syllable(word) == target]
    neg = [word for word in PL.STRESS if syllable(word) != target]
    chosen = mix(rng, pos, neg, total, k, key=lambda word: word)
    entries = [(word.replace(ACUTE, ""), syllable(word) == target, f"{word} — ударный {syllable(word)}-й слог",
                f"{word} — stress on syllable {syllable(word)}") for word in chosen]
    ordinal = {1: "первый", 2: "второй", 3: "третий"}[target]
    return classify_task(tid, "stress", entries,
                         (f"Укажите номера слов, в которых ударение падает на {ordinal} слог. {NUMBERS_NOTE[0]}",
                          f"Give the numbers of the words stressed on syllable {target}. {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Поставим ударение по орфоэпической норме.", "Mark the normative stress."),
                         hints=(["Проверьте слово по орфоэпическому словарю; не опирайтесь на просторечное произношение."],
                                ["Check the orthoepic dictionary, not colloquial pronunciation."]))


def stress_tap_task(tid, stressed):
    plain = stressed.replace(ACUTE, "")
    return build(tid, "stress", (f"Отметьте ударный гласный в слове «{plain}».", f"Mark the stressed vowel in «{plain}»."),
                 c_stress(stressed), ("Ударение по орфоэпическому словарю.", "Stress by the orthoepic dictionary."),
                 [(f"Нормативно: {stressed} — ударный {syllable(stressed)}-й слог.",
                   f"Normative: {stressed} — syllable {syllable(stressed)}.")], text=plain,
                 hints=(["Можно нажать на гласную или ввести слово, выделив ударную гласную заглавной (звонИт)."],
                        ["Tap the vowel or type the word with the stressed vowel capitalised (звонИт)."]))


# ------------------------------------------------------------- text tasks
def text_statements_task(tid, text, rng, *, kind, meta=None):
    pool = text["statements"] if kind == "statements" else text["subtopics"]
    order = list(range(len(pool)))
    rng.shuffle(order)
    chosen = [pool[index] for index in order]
    entries = [(statement, truth, f"{statement} — {'верно' if truth else 'неверно'}",
                f"{statement} — {'true' if truth else 'false'}") for statement, truth in chosen]
    if kind == "statements":
        instruction = ("Прочитайте текст. Укажите утверждения, которые соответствуют содержанию текста.",
                       "Read the text. Mark the statements that match its content.")
    else:
        instruction = ("Прочитайте текст. Укажите подтемы, которые раскрываются в тексте.",
                       "Read the text. Mark the subtopics developed in the text.")
    return classify_task(tid, "text-subtopics", entries, instruction, part="A", meta=meta,
                         intro=(f"Тема текста — {text['theme'][0]}; основная мысль — {text['idea'][0]}.",
                                f"Theme: {text['theme'][1]}; main idea: {text['idea'][1]}."),
                         text=numbered_text(text["sentences"]),
                         hints=(["Сверяйте каждое утверждение с конкретным предложением текста."],
                                ["Check every statement against a specific sentence."]))


def text_style_task(tid, text, rng, *, meta=None):
    styles = [text["style"]] + rng.sample([key for key in ("publicistic", "scientific", "artistic") if key != text["style"]], 2)
    kinds = [text["type"], rng.choice([key for key in TX.TYPES if key != text["type"]])]
    options = [("style", key) for key in styles] + [("type", key) for key in kinds]
    rng.shuffle(options)
    ru, en, entries = [], [], []
    for kind, key in options:
        if kind == "style":
            ru.append(f"Текст относится к {TX.STYLES[key][0]} стилю.")
            en.append(f"The text belongs to the {TX.STYLES[key][1]} style.")
            truth = key == text["style"]
            why = text["why_style"]
        else:
            ru.append(f"Основной тип речи в тексте — {TX.TYPES[key][0]}.")
            en.append(f"The main type of speech is {TX.TYPES[key][1]}.")
            truth = key == text["type"]
            why = text["why_type"]
        entries.append((ru[-1], truth, f"{ru[-1]} — {'верно' if truth else 'неверно'}" + (f": {why[0]}" if truth else ""),
                        f"{en[-1]} — {'true' if truth else 'false'}" + (f": {why[1]}" if truth else "")))
    return classify_task(tid, "text-styles", entries, ("Укажите верные утверждения о стиле и типе речи текста.",
                                                       "Mark the true statements about the style and type of the text."),
                         part="A", meta=meta, intro=("Определим сферу общения, задачу речи и строение текста.",
                                                     "Find the sphere, purpose and structure of the text."),
                         text=numbered_text(text["sentences"]), choices={"ru": ru, "en": en},
                         hints=(["Стиль — по сфере и задаче речи; тип — по тому, что сообщается: события, признаки или причины."],
                                ["Style: sphere and purpose; type: events, features or reasons."]))


def text_link_task(tid, text, code, *, meta=None):
    answer = [index for index, links in enumerate(text["links"], 1) if code in links]
    means = TX.MEANS[code]
    entries = [(f"({index})", code in links,
                f"({index}) — " + (", ".join(TX.MEANS[c][0] for c in links) if links else "связь по смыслу"),
                f"({index}) — " + (", ".join(TX.MEANS[c][1] for c in links) if links else "linked by meaning"))
               for index, links in enumerate(text["links"], 1) if index > 1]
    instruction = (f"Укажите номера предложений, которые связаны с предыдущим с помощью средства: {means[0]}. {NUMBERS_NOTE[0]}",
                   f"Give the numbers of the sentences linked to the previous one by {means[1]}. {NUMBERS_NOTE[1]}")
    lines_ = [(entry[2], entry[3]) for entry in entries]
    return build(tid, "text-cohesion", instruction, c_numbers(answer, len(text["sentences"])),
                 ("Сравним каждое предложение с предыдущим.", "Compare each sentence with the previous one."), lines_,
                 meta=meta, text=numbered_text(text["sentences"]),
                 hints=(["Ищите слово, которое отсылает к предыдущему предложению: он, это, тогда, поэтому…"],
                        ["Look for a word that refers back: он, это, тогда, поэтому…"]))


def text_order_task(tid, text, rng):
    sentences = text["sentences"][:5]
    shuffled = list(range(len(sentences)))
    while shuffled == sorted(shuffled):
        rng.shuffle(shuffled)
    shown_ = [sentences[index] for index in shuffled]
    answer = [shuffled.index(index) + 1 for index in range(len(sentences))]
    instruction = (f"Восстановите порядок предложений текста: запишите номера в нужной последовательности. {NUMBERS_NOTE[0]}",
                   f"Restore the order of the sentences: write their numbers in sequence. {NUMBERS_NOTE[1]}")
    lines_ = [(f"{position}. {sentences[index]}", f"{position}. {sentences[index]}")
              for position, index in enumerate(range(len(sentences)), 1)]
    return build(tid, "text-subtopics", instruction, c_numbers(answer, len(sentences), "ordered"),
                 ("Опираемся на средства связи и логику изложения.", "Use cohesion and logic."), lines_,
                 items=shown_, hints=(["Первое предложение вводит тему и не содержит отсылок назад (он, это, затем)."],
                                      ["The first sentence introduces the topic and has no back-references."]))


# ------------------------------------------------------------ small tasks
def category_task(tid, rule, pool, target, labels, rng, *, total=6, k=3, meta=None, instruction, intro, hints):
    pos = [item for item in pool if item[1] == target]
    neg = [item for item in pool if item[1] != target]
    chosen = mix(rng, pos, neg, total, k)
    entries = [(item[0], item[1] == target, f"{item[0]} — {labels[item[1]][0]}", f"{item[0]} — {labels[item[1]][1]}")
               for item in chosen]
    return classify_task(tid, rule, entries, instruction, meta=meta, intro=intro, hints=hints)


DECL_LABELS = {1: ("1-е склонение", "1st declension"), 2: ("2-е склонение", "2nd declension"),
               3: ("3-е склонение", "3rd declension"), "razn": ("разносклоняемое", "heteroclite"),
               "fixed": ("несклоняемое", "indeclinable")}
ADJ_LABELS = {"qual": ("качественное", "qualitative"), "rel": ("относительное", "relative"),
              "poss": ("притяжательное", "possessive")}
FW_LABELS = {"prep": ("предлог", "preposition"), "adv": ("наречие", "adverb"), "gerund": ("деепричастие", "verbal adverb")}
ASPECT_LABELS = {"perf": ("совершенный вид (что сделать?)", "perfective"), "impf": ("несовершенный вид (что делать?)", "imperfective")}
PHRASE_LABELS = {"gov": ("управление", "government"), "agr": ("согласование", "agreement"), "adj": ("примыкание", "adjunction")}
PRED_LABELS = {"pgp": ("простое глагольное", "simple verbal"), "cgp": ("составное глагольное", "compound verbal"),
               "cnp": ("составное именное", "compound nominal")}
CT_LABELS = {"spp": ("сложноподчинённое", "complex"), "ssp": ("сложносочинённое", "compound"),
             "bsp": ("бессоюзное", "asyndetic"), "mixed": ("с разными видами связи", "mixed links")}


def decl_task(tid, target, rng, meta=None):
    ordinal = {1: "1-го", 2: "2-го", 3: "3-го"}[target]
    return category_task(tid, "noun-declension", PL.DECLENSION, target, DECL_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера существительных {ordinal} склонения. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the {target}-declension nouns. {NUMBERS_NOTE[1]}"),
                         intro=("Определим род и окончание в начальной форме.", "Find gender and ending in the dictionary form."),
                         hints=(["1-е: ж. и м. р. на -а/-я; 2-е: м. р. с нулевым окончанием и ср. р. на -о/-е; 3-е: ж. р. на -ь."],
                                ["1st: -а/-я; 2nd: masc. zero ending, neut. -о/-е; 3rd: fem. -ь."]))


def adj_task(tid, target, rng, meta=None):
    name = ADJ_LABELS[target]
    return category_task(tid, "adjectives", PL.ADJECTIVES, target, ADJ_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера словосочетаний, в которых прилагательное {name[0]}. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the phrases with a {name[1]} adjective. {NUMBERS_NOTE[1]}"),
                         intro=("Разряд прилагательного зависит от значения в сочетании.", "The class depends on the meaning."),
                         hints=(["Качественное обозначает признак, который бывает больше или меньше; относительное — признак по "
                                 "отношению к предмету; притяжательное — принадлежность (чей?)."],
                                ["Qualitative: gradable; relative: relation to a thing; possessive: whose?"]))


def fw_task(tid, target, rng, meta=None):
    name = FW_LABELS[target]
    return category_task(tid, "function-words", PL.FUNCTION_WORDS, target, FW_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера предложений, в которых выделенное слово является словом «{name[0]}». "
                                      f"{NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the sentences where the capitalised word is a {name[1]}. {NUMBERS_NOTE[1]}"),
                         intro=("Проверим, есть ли при слове зависимое существительное или местоимение.",
                                "Check whether a noun or pronoun depends on the word."),
                         hints=(["Предлог не бывает членом предложения и стоит при существительном/местоимении."],
                                ["A preposition stands with a noun or pronoun and is not a sentence part."]))


def aspect_task(tid, target, rng, meta=None):
    name = ASPECT_LABELS[target]
    return category_task(tid, "verb-aspect", PL.ASPECT, target, ASPECT_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера глаголов, которые имеют {name[0].split(' (')[0]}. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the {name[1]} verbs. {NUMBERS_NOTE[1]}"),
                         intro=("Зададим вопрос «что делать?» или «что сделать?».", "Ask «что делать?» or «что сделать?»."),
                         hints=(["Совершенный вид — «что сделать?», несовершенный — «что делать?»."],
                                ["Perfective answers «что сделать?», imperfective «что делать?»."]))


def phrase_task(tid, target, rng, meta=None):
    name = PHRASE_LABELS[target]
    return category_task(tid, "phrases", PL.PHRASES, target, PHRASE_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера словосочетаний со связью {name[0]}. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the phrases linked by {name[1]}. {NUMBERS_NOTE[1]}"),
                         intro=("Изменим главное слово и посмотрим на зависимое.", "Change the head word and watch the dependent."),
                         hints=(["Согласование — зависимое меняется вместе с главным; управление — падеж не меняется; "
                                 "примыкание — зависимое неизменяемо."],
                                ["Agreement: changes together; government: fixed case; adjunction: invariable."]))


def predicate_task(tid, target, rng, meta=None):
    name = PRED_LABELS[target]
    return category_task(tid, "sentence-members", PL.PREDICATES, target, PRED_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера предложений, в которых {name[0]} сказуемое. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the sentences with a {name[1]} predicate. {NUMBERS_NOTE[1]}"),
                         intro=("Найдём сказуемое и определим, из чего оно состоит.", "Find the predicate and its parts."),
                         hints=(["«Будет работать» — простое глагольное (будущее время); «буду рад» — составное именное."],
                                ["«будет работать» is simple verbal; «буду рад» is compound nominal."]))


def complex_type_task(tid, target, rng, meta=None):
    name = CT_LABELS[target]
    return category_task(tid, "complex-types", PL.COMPLEX_TYPES, target, CT_LABELS, rng, meta=meta,
                         instruction=(f"Укажите номера предложений, которые являются сложными: {name[0]}. {NUMBERS_NOTE[0]}",
                                      f"Give the numbers of the {name[1]} sentences. {NUMBERS_NOTE[1]}"),
                         intro=("Найдём основы и средства связи между частями.", "Find the clauses and their links."),
                         hints=(["Сочинительные союзы (и, а, но) — ССП; подчинительные (что, когда, если) — СПП; без союзов — БСП."],
                                ["Coordinating → compound; subordinating → complex; none → asyndetic."]))


def zero_task(tid, rng, meta=None):
    pos = [item for item in PL.ZERO_ENDINGS if item[1]]
    neg = [item for item in PL.ZERO_ENDINGS if not item[1]]
    chosen = mix(rng, pos, neg, 6, 3)
    entries = [(word, zero, f"{word} — " + ("нулевое окончание" if zero else note_ru),
                f"{word} — " + ("zero ending" if zero else note_en)) for word, zero, note_ru, note_en in chosen]
    return classify_task(tid, "morphemes", entries, (f"Укажите номера слов с нулевым окончанием. {NUMBERS_NOTE[0]}",
                                                     f"Give the numbers of the words with a zero ending. {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Изменим слово: если появляется окончание, в начальной форме оно нулевое.",
                                           "Change the word: if an ending appears, the dictionary form has a zero ending."),
                         hints=(["У неизменяемых слов (наречия, деепричастия, несклоняемые существительные) окончания нет вообще."],
                                ["Invariable words have no ending at all."]))


def cognate_task(tid, base_index, rng, meta=None):
    base, words = PL.COGNATES[base_index]
    chosen = list(words)
    rng.shuffle(chosen)
    chosen = chosen[:6]
    entries = [(word, ok, f"{word} — " + ("однокоренное" if ok else note_ru), f"{word} — " + ("cognate" if ok else note_en))
               for word, ok, note_ru, note_en in chosen]
    return classify_task(tid, "morphemes", entries,
                         (f"Укажите номера слов, однокоренных слову «{base}». {NUMBERS_NOTE[0]}",
                          f"Give the numbers of the words with the same root as «{base}». {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Однокоренные слова имеют общий корень и общее лексическое значение.",
                                           "Cognates share the root AND its meaning."),
                         hints=(["Созвучный отрезок с другим значением — это омонимичный корень, а не тот же корень."],
                                ["A look-alike segment with another meaning is a homonymous root."]))


def formation_task(tid, rng, meta=None):
    methods = list(PL.FORMATION_METHODS)
    while True:
        picked = rng.sample(PL.FORMATION, 4)
        used = {item[1] for item in picked}
        if len(used) >= 3:
            break
    pool = list(dict.fromkeys([item[1] for item in picked]))
    extra = [method for method in methods if method not in pool]
    rng.shuffle(extra)
    options = pool + extra[:5 - len(pool)]
    rng.shuffle(options)
    answer = {LABELS[index]: options.index(item[1]) + 1 for index, item in enumerate(picked)}
    choices = {"ru": [PL.FORMATION_METHODS[key][0] for key in options], "en": [PL.FORMATION_METHODS[key][1] for key in options]}
    lines_ = [(f"{LABELS[index]}) {word} ← {source}: {PL.FORMATION_METHODS[method][0]}",
               f"{LABELS[index]}) {word} ← {source}: {PL.FORMATION_METHODS[method][1]}")
              for index, (word, method, source) in enumerate(picked)]
    return build(tid, "word-formation", ("Установите соответствие между словом и способом его образования. "
                                         "Ответ запишите буквами и цифрами, например: А1Б3В2Г4.",
                                         "Match each word with its way of formation. Write letters and digits, e.g. А1Б3В2Г4."),
                 c_match(answer, len(options)), ("Найдём производящее слово и то, что к нему добавлено.",
                                                 "Find the source word and what was added."), lines_, meta=meta,
                 items=[item[0] for item in picked], choices=choices,
                 hints=(["Сравните слово с самым близким по смыслу и форме производящим словом."],
                        ["Compare the word with its closest source word."]))


# ------------------------------------------------------------ word answers
def synonym_task(tid, item, meta=None):
    sentence, relation, given, answer = item
    rel = ("антоним", "antonym") if relation == "antonym" else ("синоним", "synonym")
    rule = "synonyms-antonyms"
    return build(tid, rule, (f"Выпишите из предложения {rel[0]} к слову «{given}» в той форме, в которой он употреблён.",
                             f"Copy the {rel[1]} of «{given}» from the sentence in the form used there."),
                 c_word(answer, yo="e-equals-yo"), (f"Ищем слово с {'противоположным' if relation == 'antonym' else 'близким'} значением.",
                                                    f"Look for a word with the {'opposite' if relation == 'antonym' else 'same'} meaning."),
                 [(f"«{given}» — «{answer}»: {rel[0]} в предложении.", f"«{given}» — «{answer}»: the {rel[1]} in the sentence.")],
                 meta=meta, text=sentence,
                 hints=(["Выписывайте слово точно в той форме, в какой оно стоит в предложении."],
                        ["Copy the word exactly in the form used in the sentence."]))


def idiom_task(tid, item, meta=None):
    sentence, meaning_ru, meaning_en, idiom = item
    return build(tid, "phraseology", (f"Выпишите из предложения фразеологизм со значением «{meaning_ru}» в той форме, в которой он "
                                      f"употреблён.", f"Copy the set phrase meaning «{meaning_en}» in the form used."),
                 c_word(idiom, yo="e-equals-yo"), ("Фразеологизм — устойчивое сочетание с целостным значением.",
                                                    "A set phrase has one unified meaning."),
                 [(f"«{idiom}» = «{meaning_ru}»; слова не заменяются и не опускаются.",
                   f"«{idiom}» = «{meaning_en}»; words are neither replaced nor dropped.")], meta=meta, text=sentence,
                 hints=(["Выпишите все слова оборота и только их."], ["Copy all words of the phrase and nothing else."]))


def figurative_task(tid, rng, meta=None):
    pos = [item for item in PL.FIGURATIVE if item[1]]
    neg = [item for item in PL.FIGURATIVE if not item[1]]
    chosen = mix(rng, pos, neg, 6, 3)
    entries = [(phrase, fig, f"{phrase} — " + ("переносное значение" if fig else "прямое значение"),
                f"{phrase} — " + ("figurative" if fig else "literal")) for phrase, fig in chosen]
    return classify_task(tid, "word-meaning", entries,
                         (f"Укажите номера сочетаний, в которых прилагательное употреблено в переносном значении. {NUMBERS_NOTE[0]}",
                          f"Give the numbers of the phrases where the adjective is figurative. {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Прямое значение называет признак предмета, переносное — перенесённый по сходству признак.",
                                           "Literal names the real feature; figurative transfers it by similarity."),
                         hints=(["Спросите себя: действительно ли предмет сделан из золота, имеет температуру?"],
                                ["Ask yourself: is it really made of gold, does it have a temperature?"]))


def paronym_task(tid, entry, meta=None):
    sentences, wrong, answer, pair_ru, pair_en = entry
    text = "\n".join(f"{index}) {sentence}" for index, sentence in enumerate(sentences, 1))
    corrected = re.sub(r"\b[А-ЯЁ]{2,}\b", answer.upper(), sentences[wrong - 1], count=1)
    return build(tid, "paronyms", ("В одном из предложений неверно употреблено выделенное слово. Исправьте ошибку и запишите "
                                   "правильное слово в нужной форме.",
                                   "One capitalised word is misused. Correct it and write the right word in the needed form."),
                 c_word(answer, yo="e-equals-yo"), (f"Ошибка в предложении {wrong}.", f"The error is in sentence {wrong}."),
                 [(f"Паронимы: {pair_ru}.", f"Paronyms: {pair_en}."), (f"Правильно: {corrected}", f"Correct: {corrected}")],
                 meta=meta, text=text,
                 hints=(["Паронимы похожи по звучанию, но различаются значением и сочетаемостью."],
                        ["Paronyms sound alike but differ in meaning and collocation."]))


def pleonasm_task(tid, item, meta=None):
    sentence, extra = item
    return build(tid, "pleonasm", ("Найдите речевую избыточность (плеоназм). Выпишите лишнее слово (слова) в той форме, в которой "
                                   "оно употреблено.", "Find the pleonasm and copy the redundant word(s) as used."),
                 c_word(extra, yo="e-equals-yo"), ("Плеоназм — повтор смысла, уже выраженного другим словом.",
                                                    "A pleonasm repeats a meaning already expressed."),
                 [(f"«{extra}» повторяет значение соседнего слова; без него смысл не меняется.",
                   f"«{extra}» repeats the meaning of the neighbouring word.")], meta=meta, text=sentence,
                 hints=(["Попробуйте убрать слово: если смысл сохранился, оно было лишним."],
                        ["Try removing the word: if the meaning stays, it was redundant."]))


def numeral_task(tid, item, meta=None):
    sentence, digits, case_ru, case_en, answer, accept, why = item
    check = c_word(answer, accept=accept, why_ru=[why] * len(accept), why_en=[why] * len(accept), yo="strict")
    steps = [(f"{digits} в форме падежа «{case_ru}»: {answer}" + (f" (допустимо также: {', '.join(accept)}; {why})" if accept else ""),
              f"{digits} in the {case_en} case: {answer}" + (f" (also accepted: {', '.join(accept)})" if accept else ""))]
    return build(tid, "numerals", ("Запишите словами числительное из предложения в нужной форме (только числительное).",
                                   "Write the numeral of the sentence in words in the needed case (the numeral only)."),
                 check, ("В составном количественном числительном склоняется каждое слово.",
                         "In a compound cardinal numeral every word is declined."), steps, meta=meta, text=sentence,
                 hints=(["Определите падеж по предлогу или управляющему слову и склоняйте каждую часть."],
                        ["Find the case from the preposition or head word and decline every part."]))


def numeral_usage_task(tid, rng, meta=None):
    pos = [item for item in PL.NUMERAL_USAGE if item[1]]
    neg = [item for item in PL.NUMERAL_USAGE if not item[1]]
    chosen = mix(rng, pos, neg, 6, 3)
    entries = [(sentence, ok, f"{sentence} — " + ("верно" if ok else f"ошибка, правильно: {fix}"),
                f"{sentence} — " + ("correct" if ok else f"error, correct: {fix}")) for sentence, ok, fix in chosen]
    return classify_task(tid, "numerals", entries,
                         (f"Укажите номера предложений, в которых числительные употреблены правильно. {NUMBERS_NOTE[0]}",
                          f"Give the numbers of the sentences with correctly used numerals. {NUMBERS_NOTE[1]}"),
                         meta=meta, intro=("Проверим род (оба/обе) и сочетаемость собирательных числительных.",
                                           "Check оба/обе and the use of collective numerals."),
                         hints=(["Собирательные (двое, трое) не сочетаются с существительными женского рода."],
                                ["Collective numerals do not combine with feminine nouns."]))


def grammar_task(tid, rng, *, rule=None, meta=None):
    pool = [item for item in PL.GRAMMAR if rule is None or PL.GRAMMAR_REASONS[item[3]][0] == rule]
    pos = [item for item in pool if item[1]]
    neg = [item for item in pool if not item[1]]
    chosen = mix(rng, pos, neg, 6, 3)
    entries = []
    for sentence, ok, fix, code in chosen:
        reason = PL.GRAMMAR_REASONS[code]
        entries.append((sentence, ok, f"{sentence} — " + ("верно" if ok else f"ошибка; правильно: {fix}") + f" ({reason[1]})",
                        f"{sentence} — " + ("correct" if ok else f"error; correct: {fix}") + f" ({reason[2]})"))
    rules = list(dict.fromkeys(PL.GRAMMAR_REASONS[item[3]][0] for item in chosen))
    entry = classify_task(tid, rule or rules[0], entries,
                          (f"Укажите номера предложений без грамматических ошибок. {NUMBERS_NOTE[0]}",
                           f"Give the numbers of the sentences without grammatical errors. {NUMBERS_NOTE[1]}"),
                          meta=meta, intro=("Проверим управление, деепричастные и причастные обороты, однородные члены.",
                                            "Check government, verbal-adverb and participial phrases, homogeneous parts."),
                          hints=(["Задайте вопрос от главного слова к зависимому; найдите, кто совершает действие деепричастия."],
                                 ["Ask the question from the head word; find who performs the verbal adverb's action."]))
    entry["rules"] = list(dict.fromkeys([entry["rule"], *rules]))
    return entry


def government_fix_task(tid, item):
    sentence, answer, why = item
    return build(tid, "government", ("Исправьте ошибку в управлении: запишите выделенное слово в правильной форме.",
                                     "Correct the government error: write the capitalised word in the right form."),
                 c_word(answer, yo="e-equals-yo"), ("Определим падеж, которого требует предлог или глагол.",
                                                    "Find the case required by the preposition or verb."),
                 [(f"{why}: {answer}", f"{why}: {answer}")], text=sentence,
                 hints=(["Благодаря, согласно, вопреки — дательный падеж; по (= после) — предложный."],
                        ["благодаря/согласно/вопреки → dative; по (= after) → prepositional."]))


# ------------------------------------------------------------------ variants
def variant(year):
    def m(slot):
        return variant_meta(year, slot)

    def rng(slot):
        return random.Random(f"variant-{year}-{slot}")

    odd = year % 2 == 1
    text = next(item for item in TX.TEXTS if item["id"] == TX.VARIANT_TEXTS[year])
    tid = lambda slot: f"v{year}-{slot.lower()}"  # noqa: E731
    out = [
        gap_choice_task(tid("A1"), "root-oa", "о" if odd else "а", rng("A1"), part="A", total=5, k=rng("k1").choice([2, 3]),
                        meta=m("A1")),
        gap_choice_task(tid("A2"), "root-ei", "и" if year % 3 else "е", rng("A2"), part="A", total=5,
                        k=rng("k2").choice([2, 3]), meta=m("A2")),
        gap_choice_task(tid("A3"), "double" if odd else "consonants", "double" if odd else "silent", rng("A3"), part="A",
                        total=5, k=rng("k3").choice([2, 3]), meta=m("A3")),
        gap_choice_task(tid("A4"), "endings-suffixes", "и" if year % 3 != 1 else "е", rng("A4"), part="A", total=5,
                        k=rng("k4").choice([2, 3]), meta=m("A4")),
        gap_choice_task(tid("A5"), "ne-ni", "и" if odd else "е", rng("A5"), part="A", total=5, k=rng("k5").choice([2, 3]),
                        meta=m("A5")),
        bracket_choice_task(tid("A6"), "ne-parts", "solid" if year % 3 else "separate", rng("A6"), part="A", total=5,
                            k=rng("k6").choice([2, 3]), meta=m("A6")),
        bracket_choice_task(tid("A7"), "hyphen", "hyphen" if odd else "solid", rng("A7"), part="A", total=5,
                            k=rng("k7").choice([2, 3]), meta=m("A7")),
        bracket_choice_task(tid("A8"), "prep-conj", "solid" if year % 3 else "separate", rng("A8"), part="A", total=5,
                            k=rng("k8").choice([2, 3]), meta=m("A8")),
        mark_choice_task(tid("A9"), "dash-subject", rng("A9"), part="A", total=5, k=rng("k9").choice([2, 3]), meta=m("A9")),
        mark_choice_task(tid("A10"), "isolation", rng("A10"), part="A", total=5, k=rng("k10").choice([2, 3]), meta=m("A10")),
        mark_choice_task(tid("A11"), "introductory", rng("A11"), part="A", total=5, k=rng("k11").choice([2, 3]),
                         meta=m("A11")),
        mark_choice_task(tid("A12"), "homogeneous", rng("A12"), part="A", total=5, k=rng("k12").choice([2, 3]),
                         meta=m("A12")),
        mark_choice_task(tid("A13"), "comma-before-i", rng("A13"), part="A", total=5, k=rng("k13").choice([2, 3]),
                         meta=m("A13")),
        mark_choice_task(tid("A14"), "asyndetic", rng("A14"), part="A", total=5, k=rng("k14").choice([2, 3]),
                         target=":" if odd else " — ", meta=m("A14")),
        statement_task(tid("A15"), rng("A15"), part="A", total=5, k=rng("k15").choice([2, 3]), meta=m("A15")),
        mark_choice_task(tid("A16"), "kak", rng("A16"), part="A", total=5, k=rng("k16").choice([2, 3]), meta=m("A16")),
        text_statements_task(tid("A17"), text, rng("A17"), kind="statements" if odd else "subtopics", meta=m("A17")),
        text_style_task(tid("A18"), text, rng("A18"), meta=m("A18")),
    ]
    link_codes = [code for code in TX.MEANS if any(code in links for links in text["links"])]
    out.append(text_link_task(tid("B1"), text, rng("B1").choice(link_codes), meta=m("B1")))
    syn = [item for item in PL.SYNONYMS]
    out.append(synonym_task(tid("B2"), syn[(year - 2021) * 2 % len(syn)], meta=m("B2")))
    out.append(gap_choice_task(tid("B3"), "tsya", "ть" if odd else "т", rng("B3"), part="B", total=6, k=3, meta=m("B3")))
    out.append(gap_choice_task(tid("B4"), "n-nn", "нн" if year % 3 else "н", rng("B4"), part="B", total=6, k=3,
                               meta=m("B4")))
    out.append(phonetics_task(tid("B5"), ["more-letters", "more-sounds", "two-sounds"][year % 3], rng("B5"), meta=m("B5")))
    out.append(decl_task(tid("B6"), [1, 2, 3][year % 3], rng("B6"), meta=m("B6")))
    out.append(adj_task(tid("B7"), ["qual", "rel", "poss"][year % 3], rng("B7"), meta=m("B7")))
    out.append(fw_task(tid("B8"), "prep", rng("B8"), meta=m("B8")))
    out.append(phrase_task(tid("B9"), ["gov", "agr", "adj"][year % 3], rng("B9"), meta=m("B9")))
    out.append(gap_choice_task(tid("B10"), "o-yo" if odd else "soft-sign", ("о" if year % 4 == 1 else "ё") if odd else "ь",
                               rng("B10"), part="B", total=6, k=3, meta=m("B10")))
    out.append(gap_choice_task(tid("B11"), "verb-endings", "е" if odd else "и", rng("B11"), part="B", total=6, k=3,
                               meta=m("B11")))
    b12 = {2021: ("pre-pri", "и"), 2023: ("pre-pri", "е"), 2025: ("pre-pri", "и"), 2022: ("prefix-z-s", "с"),
           2024: ("hard-soft", "ъ"), 2026: ("y-after-prefix", "ы")}[year]
    out.append(gap_choice_task(tid("B12"), b12[0], b12[1], rng("B12"), part="B", total=6, k=3, meta=m("B12")))
    out.append(numbered_task(tid("B13"), PP.NUMBERED[year - 2021], meta=m("B13")))
    out.append(idiom_task(tid("B14"), PL.IDIOMS[(year - 2021) * 2], meta=m("B14")) if odd
               else figurative_task(tid("B14"), rng("B14"), meta=m("B14")))
    out.append(aspect_task(tid("B15"), "perf" if odd else "impf", rng("B15"), meta=m("B15")))
    if odd:
        out.append(stress_numbers_task(tid("B16"), {2021: 2, 2023: 1, 2025: 3}[year], rng("B16"), meta=m("B16")))
    elif year == 2024:
        out.append(pleonasm_task(tid("B16"), PL.PLEONASMS[0], meta=m("B16")))
    else:
        out.append(paronym_task(tid("B16"), PL.PARONYM_SETS[0 if year == 2022 else 1], meta=m("B16")))
    out.append(numeral_task(tid("B17"), PL.NUMERAL_WORDS[year - 2021], meta=m("B17")))
    out.append(grammar_task(tid("B18"), rng("B18"), meta=m("B18")))
    out.append(zero_task(tid("B19"), rng("B19"), meta=m("B19")) if odd
               else cognate_task(tid("B19"), (year // 2) % 2, rng("B19"), meta=m("B19")))
    out.append(formation_task(tid("B20"), rng("B20"), meta=m("B20")))
    out.append(predicate_task(tid("B21"), ["cnp", "cgp", "pgp"][year % 3], rng("B21"), meta=m("B21")))
    out.append(complex_type_task(tid("B22"), ["spp", "ssp", "bsp", "mixed"][year % 4], rng("B22"), meta=m("B22")))
    return out


def variants():
    return [entry for year in (2021, 2022, 2023, 2024, 2025, 2026) for entry in variant(year)]


# ------------------------------------------------------------------ analogs
def analogs():
    out: list[dict] = []
    counter: Counter = Counter()

    def add(entry):
        counter[entry["rule"]] += 1
        out.append(entry)

    def nid(rule):
        return f"an-{rule}-{counter[rule] + 1}"

    rng = random.Random("analogs")
    # spelling gap pools: one numbers task per rule (+2 word tasks)
    gap_targets = {"root-oa": "о", "root-ei": "и", "double": "double", "consonants": "silent", "endings-suffixes": "и",
                   "ne-ni": "и", "tsya": "ть", "n-nn": "нн", "o-yo": "ё", "soft-sign": "ь", "verb-endings": "и",
                   "pre-pri": "и", "prefix-z-s": "з", "hard-soft": "ъ", "y-after-prefix": "ы"}
    for pool_name, target in gap_targets.items():
        items = gap_items(pool_name)
        unit, predicate = gap_target(pool_name, target)[:2]
        for rule in dict.fromkeys(item["rule"] for item in items):
            mine = [item for item in items if item["rule"] == rule]
            pos = [item for item in mine if predicate(item["fill"])]
            if len(mine) >= 6 and 1 <= len(pos) <= len(mine) - 1:
                add(gap_choice_task(nid(rule), pool_name, target, rng, part="B", total=6, k=3, restrict=rule, rule=rule))
            words = sorted(mine, key=lambda item: (USE[item["masked"]], rng.random()))[:2 if len(mine) >= 6 else 3]
            for item in words:
                add(gap_word_task(nid(rule), item, pool_name))
    for pool_name, category in (("ne-parts", "solid"), ("hyphen", "hyphen"), ("prep-conj", "solid")):
        items = bracket_items(pool_name)
        for rule in dict.fromkeys(item["rule"] for item in items):
            mine = [item for item in items if item["rule"] == rule]
            cats = Counter(item["category"] for item in mine)
            target = category if 0 < cats[category] < len(mine) else cats.most_common(1)[0][0]
            if 0 < cats[target] < len(mine) and len(mine) >= 5:
                add(bracket_choice_task(nid(rule), pool_name, target, rng, part="B", total=min(6, len(mine)), k=3,
                                        restrict=rule, rule=rule))
            for item in sorted(mine, key=lambda item: (USE[item["text"]], rng.random()))[:3]:
                add(bracket_word_task(nid(rule), item))
    for pool_name in ("dash-subject", "isolation", "introductory", "homogeneous", "comma-before-i", "kak", "complex-commas"):
        items = mark_items(pool_name)
        for rule in dict.fromkeys(item["rule"] for item in items):
            mine = [item for item in items if item["rule"] == rule]
            target = PP.MARK[pool_name]["target"]
            pos = [item for item in mine if target in item["marks"]]
            if len(mine) >= 6 and 1 <= len(pos) <= len(mine) - 1:
                add(mark_choice_task(nid(rule), pool_name, rng, part="B", total=6, k=3, restrict=rule, rule=rule))
            for item in [item for item in mine if "," in item["marks"]][:2]:
                add(mark_count_task(nid(rule), item))
    asyn = mark_items("asyndetic")
    add(mark_choice_task(nid("asyndetic"), "asyndetic", rng, part="B", total=6, k=3, target=":"))
    add(mark_choice_task(nid("asyndetic"), "asyndetic", rng, part="B", total=6, k=3, target=" — "))
    for item in asyn[::4]:
        add(asyndetic_single_task(nid("asyndetic"), item))
    for index in range(3):
        add(statement_task(nid("direct-speech"), rng, part="B", total=6, k=3))
    for entry in PP.NUMBERED[6:]:
        add(numbered_task(nid("mixed"), entry))
    for kind in PHON_TYPES:
        add(phonetics_task(nid("sounds-letters"), kind, rng))
    word, sounds = PL.PHONETICS[10]
    add(build(nid("sounds-letters"), "sounds-letters", (f"Сколько звуков в слове «{word}»? Запишите число.",
                                                        f"How many sounds are there in «{word}»? Write the number."),
              c_integer(len(sounds.split())), ("Запишем транскрипцию.", "Write the transcription."),
              [(f"[{sounds.replace(' ', '')}] — {len(sounds.split())} звуков, {letters(word)} букв",
                f"[{sounds.replace(' ', '')}] — {len(sounds.split())} sounds, {letters(word)} letters")], text=word))
    for stressed in ("катало́г", "краси́вее", "щаве́ль", "обеспе́чение"):
        add(stress_tap_task(nid("stress"), stressed))
    add(stress_numbers_task(nid("stress"), 3, rng))
    for item in PL.SYNONYMS[1::2]:
        add(synonym_task(nid("synonyms-antonyms"), item))
    for item in PL.IDIOMS[1::2]:
        add(idiom_task(nid("phraseology"), item))
    for _ in range(3):
        add(figurative_task(nid("word-meaning"), rng))
    for entry in PL.PARONYM_SETS[2:]:
        add(paronym_task(nid("paronyms"), entry))
    for item in PL.PLEONASMS[1:5]:
        add(pleonasm_task(nid("pleonasm"), item))
    for item in PL.NUMERAL_WORDS[6:]:
        add(numeral_task(nid("numerals"), item))
    add(numeral_usage_task(nid("numerals"), rng))
    add(numeral_usage_task(nid("numerals"), rng))
    for rule in ("government", "participial-gerund"):
        for _ in range(3):
            add(grammar_task(nid(rule), rng, rule=rule))
    for _ in range(2):
        add(mark_choice_task(nid("dash-subject"), "dash-subject", rng, part="B", total=6, k=3, rule="dash-subject"))
    for item in PL.GOVERNMENT_FIX:
        add(government_fix_task(nid("government"), item))
    for target in (1, 2, 3):
        add(decl_task(nid("noun-declension"), target, rng))
    for target in ("qual", "rel", "poss"):
        add(adj_task(nid("adjectives"), target, rng))
    for target in ("prep", "adv", "prep"):
        add(fw_task(nid("function-words"), target, rng))
    for target in ("perf", "impf", "perf"):
        add(aspect_task(nid("verb-aspect"), target, rng))
    for target in ("gov", "agr", "adj"):
        add(phrase_task(nid("phrases"), target, rng))
    for target in ("cnp", "cgp", "pgp"):
        add(predicate_task(nid("sentence-members"), target, rng))
    for target in ("spp", "ssp", "bsp", "mixed"):
        add(complex_type_task(nid("complex-types"), target, rng))
    add(zero_task(nid("morphemes"), rng))
    add(cognate_task(nid("morphemes"), 0, rng))
    add(cognate_task(nid("morphemes"), 1, rng))
    for _ in range(3):
        add(formation_task(nid("word-formation"), rng))
    money = next(item for item in TX.TEXTS if item["id"] == "money")
    add(text_statements_task(nid("text-subtopics"), money, rng, kind="statements"))
    add(text_statements_task(nid("text-subtopics"), money, rng, kind="subtopics"))
    add(text_order_task(nid("text-subtopics"), money, rng))
    add(text_order_task(nid("text-subtopics"), next(item for item in TX.TEXTS if item["id"] == "beaver"), rng))
    for code in ("pron-pers", "pron-dem", "intro"):
        add(text_link_task(nid("text-cohesion"), money, code))
    add(text_style_task(nid("text-styles"), money, rng))
    styles = list(TX.STYLES)
    for sample, why in ((TX.NOTICE, TX.NOTICE["why_style"]),
                        ({"style": "colloquial", "sentences": ["— Ты куда это собрался?", "— Да в магазин сбегаю, хлеба нет.",
                                                               "— Ну давай, только недолго!"]},
                         ("диалог, разговорные слова и обороты (сбегаю, ну давай), неполные предложения",
                          "a dialogue, colloquial words, incomplete sentences"))):
        answer = styles.index(sample["style"]) + 1
        add(build(nid("text-styles"), "text-styles", ("Определите стиль речи текста.", "Identify the style of the text."),
                  c_single(answer, len(styles)), ("Сфера общения и языковые приметы.", "Sphere and language features."),
                  [(f"Стиль — {STYLE_NOM[sample['style']][0]}: {why[0]}",
                    f"Style: {STYLE_NOM[sample['style']][1]} — {why[1]}")], text="\n".join(sample["sentences"]),
                  choices={"ru": [STYLE_NOM[key][0] for key in styles], "en": [STYLE_NOM[key][1] for key in styles]}))
    return out
