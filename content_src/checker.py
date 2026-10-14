"""Subject answer checker for Russian-language tasks — reference implementation.

This is NOT the mathematics normaliser. In language tasks a space, a hyphen,
the letter ё, a capital letter or a stress mark is very often the answer
itself, so nothing is removed implicitly. Every task carries an explicit
``check`` object; the JavaScript (webapp/core.js) and Kotlin
(AnswerChecker.kt) ports implement exactly the same contract and are tested
against the shared vectors in ``answer_vectors.json``.

Contract (all-or-nothing scoring, ``"scoring": "exact"``):

``multi``    part-A choice of several options: ``options`` (N) and a sorted
             unique ``answer`` list. Input: option numbers, any order, with or
             without separators (" ", ",", ";"). Duplicates, 0, numbers > N or
             a missing/extra selection never match.
``single``   exactly one option number out of ``options``.
``numbers``  numbered places/sentences 1..``max``; ``order`` is
             ``unordered`` (compared as a set, written in any order) or
             ``ordered`` (sequence, order is the answer). Concatenated digits
             ("135") are accepted only while ``max`` <= 9; otherwise numbers
             must be separated. Duplicates are invalid, never de-duplicated.
``word``     a word/word form/phrase. Policies are explicit per task:
             ``case`` (``insensitive``|``sensitive``), ``yo``
             (``strict``|``e-equals-yo``), ``hyphen`` (``strict``|
             ``typographic`` — only U+2010/U+2011 become "-"; dashes and minus
             never do). Leading/trailing whitespace is trimmed and a run of
             whitespace becomes ONE space: a significant space is never
             deleted. Input containing a stress/grave mark is rejected.
             Extra punctuation (a final period) does not match. Alternatives
             are only the explicit, justified ``accept`` list.
``stress``   the stressed vowel of ``word``: input is the word with one
             combining acute (U+0301) after the vowel, or the word with only
             the stressed vowel capitalised ("звонИт"). Compared by index.
``match``    pairs label → number ("А3Б1В4", separators " ,;-:" allowed);
             every label exactly once, numbers 1..``right``.
``integer``  a non-negative integer without sign or leading zeros.
"""
from __future__ import annotations

import re
import unicodedata

# Explicit whitespace set shared by the three implementations. Invisible
# format characters (U+200B, U+FEFF, …) are deliberately NOT whitespace: an
# invisible character must never turn "также" into "так же".
WHITESPACE = ("\t\n\u000b\u000c\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
              "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000")
VOWELS = "аеёиоуыэюя"
ACUTE = "\u0301"
GRAVE = "\u0300"
TYPOGRAPHIC_HYPHENS = ("\u2010", "\u2011")
MATCH_SEPARATORS = " ,;-:"
TYPES = ("multi", "single", "numbers", "word", "stress", "match", "integer")
_DIGITS = re.compile(r"[0-9]+")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def squeeze(text: str) -> str:
    """Trim the ends and replace each internal run of whitespace by one space."""
    out: list[str] = []
    pending = False
    for char in text:
        if char in WHITESPACE:
            pending = True
            continue
        if pending and out:
            out.append(" ")
        pending = False
        out.append(char)
    return "".join(out)


def _number(token: str) -> int | None:
    if not _DIGITS.fullmatch(token) or (len(token) > 1 and token[0] == "0"):
        return None
    return int(token)


def parse_numbers(raw: str, maximum: int) -> list[int] | None:
    """Numbers 1..maximum in input order, or None when the input is invalid."""
    text = squeeze(nfc(raw))
    if not text:
        return None
    tokens = [token for token in re.split(r"[ ,;]+", text) if token]
    if not tokens:
        return None
    if len(tokens) == 1 and maximum <= 9 and len(tokens[0]) > 1:
        if not _DIGITS.fullmatch(tokens[0]):
            return None
        tokens = list(tokens[0])
    values: list[int] = []
    for token in tokens:
        if maximum <= 9 and len(token) != 1:
            return None
        value = _number(token)
        if value is None or not 1 <= value <= maximum or value in values:
            return None
        values.append(value)
    return values


def fold_word(text: str, check: dict) -> str:
    text = nfc(text)
    if check["hyphen"] == "typographic":
        for char in TYPOGRAPHIC_HYPHENS:
            text = text.replace(char, "-")
    text = squeeze(text)
    if check["case"] == "insensitive":
        text = text.lower()
    if check["yo"] == "e-equals-yo":
        text = text.replace("ё", "е").replace("Ё", "Е")
    return text


def parse_stress(raw: str, word: str) -> int | None:
    text = squeeze(nfc(raw))
    if not text or " " in text or GRAVE in text or text.count(ACUTE) > 1:
        return None
    if ACUTE in text:
        position = text.index(ACUTE) - 1
        base = text.replace(ACUTE, "")
        if position < 0 or base.lower() != word or base[position].lower() not in VOWELS:
            return None
        return position
    capitals = [index for index, char in enumerate(text) if char != char.lower()]
    if len(capitals) != 1:
        return None
    position = capitals[0]
    if text.lower() != word or text[position].lower() not in VOWELS:
        return None
    return position


def parse_match(raw: str, labels: list[str], right: int) -> dict | None:
    text = squeeze(nfc(raw)).upper()
    for char in MATCH_SEPARATORS:
        text = text.replace(char, "")
    if not text or not re.fullmatch(r"(?:[А-ЯЁ][0-9]{1,2})+", text):
        return None
    pairs: dict[str, int] = {}
    for label, digits in re.findall(r"([А-ЯЁ])([0-9]{1,2})", text):
        value = _number(digits)
        if label not in labels or label in pairs or value is None or not 1 <= value <= right:
            return None
        pairs[label] = value
    return pairs if set(pairs) == set(labels) else None


def check(user, spec: dict) -> bool:
    """Grade one answer. Never raises on user input; unknown types fail closed."""
    raw = "" if user is None else str(user)
    kind = spec.get("type")
    if kind == "multi":
        values = parse_numbers(raw, spec["options"])
        return values is not None and sorted(values) == list(spec["answer"])
    if kind == "single":
        values = parse_numbers(raw, spec["options"])
        return values is not None and values == [spec["answer"]]
    if kind == "numbers":
        values = parse_numbers(raw, spec["max"])
        if values is None:
            return False
        if spec["order"] == "ordered":
            return values == list(spec["answer"])
        return sorted(values) == list(spec["answer"])
    if kind == "word":
        normalized = nfc(raw)
        if ACUTE in normalized or GRAVE in normalized:
            return False
        got = fold_word(raw, spec)
        if not got:
            return False
        return any(got == fold_word(candidate, spec) for candidate in [spec["answer"], *spec.get("accept", [])])
    if kind == "stress":
        return parse_stress(raw, spec["word"]) == spec["answer"]
    if kind == "match":
        pairs = parse_match(raw, spec["labels"], spec["right"])
        return pairs is not None and pairs == dict(spec["answer"])
    if kind == "integer":
        value = _number(squeeze(nfc(raw)))
        return value is not None and value == spec["answer"]
    return False


def display(spec: dict) -> str:
    """Human-readable canonical answer (used in explanations and reports)."""
    kind = spec["type"]
    if kind in ("multi", "numbers"):
        return ", ".join(str(value) for value in spec["answer"])
    if kind in ("single", "integer"):
        return str(spec["answer"])
    if kind == "word":
        return spec["answer"]
    if kind == "stress":
        return spec["display"]
    if kind == "match":
        return " ".join(f"{label}{spec['answer'][label]}" for label in spec["labels"])
    raise ValueError("unknown check type")


def validate(spec: dict) -> dict:
    """Authoring-time contract of a check object (fail closed)."""
    kind = spec.get("type")
    if kind not in TYPES:
        raise ValueError(f"unknown check type {kind!r}")
    if spec.get("scoring") != "exact":
        raise ValueError("every task must declare exact all-or-nothing scoring")
    common = {"type", "scoring", "order", "answer"}
    allowed = {
        "multi": common | {"options"}, "single": common | {"options"},
        "numbers": common | {"max"}, "integer": common,
        "word": common | {"accept", "case", "yo", "hyphen", "acceptWhy"},
        "stress": common | {"word", "display"},
        "match": common | {"labels", "right"},
    }[kind]
    if set(spec) - allowed or "answer" not in spec:
        raise ValueError(f"unexpected/missing fields in {kind} check: {sorted(set(spec) ^ allowed)}")
    order = spec.get("order")
    expected_order = {"multi": "unordered", "single": "n/a", "integer": "n/a", "word": "n/a",
                      "stress": "n/a", "match": "by-label"}.get(kind)
    if kind == "numbers":
        if order not in ("unordered", "ordered"):
            raise ValueError("numbers check must declare unordered/ordered")
    elif order != expected_order:
        raise ValueError(f"{kind} check must declare order {expected_order!r}")
    answer = spec["answer"]
    if kind in ("multi", "numbers"):
        limit = spec["options"] if kind == "multi" else spec["max"]
        if not isinstance(limit, int) or not 2 <= limit <= 40:
            raise ValueError("invalid option/position count")
        if not isinstance(answer, list) or not answer or any(
                not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= limit for v in answer):
            raise ValueError("invalid number answer")
        if len(set(answer)) != len(answer):
            raise ValueError("duplicate numbers in answer")
        if (kind == "multi" or order == "unordered") and answer != sorted(answer):
            raise ValueError("unordered answers are stored sorted")
        if kind == "multi" and not 2 <= len(answer) <= limit - 1:
            raise ValueError("part A has several (2..N-1) correct options, never all/none")
    elif kind == "single":
        if not isinstance(spec["options"], int) or not 2 <= spec["options"] <= 9 or answer not in range(1, spec["options"] + 1):
            raise ValueError("invalid single-choice answer")
    elif kind == "integer":
        if not isinstance(answer, int) or isinstance(answer, bool) or answer < 0:
            raise ValueError("invalid integer answer")
    elif kind == "word":
        if spec.get("case") not in ("insensitive", "sensitive") or spec.get("yo") not in ("strict", "e-equals-yo") \
                or spec.get("hyphen") not in ("strict", "typographic"):
            raise ValueError("word check must declare case/yo/hyphen policies")
        candidates = [answer, *spec.get("accept", [])]
        if spec.get("accept") and len(spec.get("acceptWhy", {}).get("ru", [])) != len(spec["accept"]):
            raise ValueError("each accepted alternative needs a justification")
        for candidate in candidates:
            if not isinstance(candidate, str) or candidate != squeeze(nfc(candidate)) or not candidate:
                raise ValueError("word answers must be NFC, trimmed and single-spaced")
            if ACUTE in candidate or GRAVE in candidate:
                raise ValueError("word answers never contain stress marks (use a stress task)")
            if spec["hyphen"] == "typographic" and any(char in candidate for char in TYPOGRAPHIC_HYPHENS):
                raise ValueError("store the canonical ASCII hyphen")
        folded = [fold_word(candidate, spec) for candidate in candidates]
        if len(set(folded)) != len(folded):
            raise ValueError("duplicate accepted alternative after normalisation")
    elif kind == "stress":
        word = spec.get("word", "")
        if not word or word != word.lower() or "ё" in word or not isinstance(answer, int) \
                or not 0 <= answer < len(word) or word[answer] not in VOWELS:
            raise ValueError("invalid stress task")
        if spec.get("display") != word[:answer + 1] + ACUTE + word[answer + 1:]:
            raise ValueError("stress display must be the word with U+0301 after the stressed vowel")
    elif kind == "match":
        labels = spec.get("labels")
        if not isinstance(labels, list) or not 2 <= len(labels) <= 6 or len(set(labels)) != len(labels) \
                or any(not re.fullmatch(r"[А-ЯЁ]", label) for label in labels):
            raise ValueError("invalid match labels")
        if not isinstance(answer, dict) or set(answer) != set(labels) or any(
                not isinstance(v, int) or not 1 <= v <= spec["right"] for v in answer.values()):
            raise ValueError("invalid match answer")
    return spec
