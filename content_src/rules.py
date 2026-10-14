"""rules.py — rule cards (lessons), study notes per area and the «Правила» reference.

Every task links to a rule card; every card is reachable from the study screen,
from wrong-answer remediation and from the «Правила» reference.
"""
from __future__ import annotations

import kit
import rules_a
import rules_b
import sources

CARDS = {**rules_a.CARDS, **rules_b.CARDS}
_FIELDS = {"rule", "exceptions", "everyday", "correct", "wrong", "steps", "sources"}


def _pair(value, field, rid, *, minimum=1, min_len=0):
    ru, en = value
    if len(ru) != len(en) or len(ru) < minimum:
        raise ValueError(f"rule card {rid}: {field} needs parallel RU/EN paragraphs (at least {minimum})")
    for text in ru + en:
        if not isinstance(text, str) or len(text.strip()) <= min_len:
            raise ValueError(f"rule card {rid}: {field} paragraph is empty or too short")
    return {"ru": list(ru), "en": list(en)}


def lessons(figures: dict | None = None) -> dict:
    figures = figures or {}
    if set(CARDS) != set(kit.RULES):
        missing, extra = set(kit.RULES) - set(CARDS), set(CARDS) - set(kit.RULES)
        raise ValueError(f"rule cards must match kit.RULES (missing {sorted(missing)}, extra {sorted(extra)})")
    out = {}
    for rid in kit.RULE_ORDER:
        card = CARDS[rid]
        if set(card) != _FIELDS:
            raise ValueError(f"rule card {rid}: fields must be {sorted(_FIELDS)}")
        area, title_ru, title_en = kit.RULES[rid]
        if not card["correct"] or not card["wrong"]:
            raise ValueError(f"rule card {rid}: needs correct and wrong examples")
        for pair in card["wrong"]:
            if len(pair) != 2 or not all(isinstance(text, str) and text.strip() for text in pair) or pair[0] == pair[1]:
                raise ValueError(f"rule card {rid}: wrong examples are (wrong, corrected) pairs")
        unknown = [source for source in card["sources"] if source not in sources.SOURCES]
        if not card["sources"] or unknown:
            raise ValueError(f"rule card {rid}: unknown or missing sources {unknown}")
        out[rid] = {
            "id": rid, "topic": area, "title": kit.bi(title_ru, title_en),
            "rule": _pair(card["rule"], "rule", rid),
            "exceptions": _pair(card["exceptions"], "exceptions", rid),
            "everyday": _pair(card["everyday"], "everyday", rid, minimum=2, min_len=70),
            "correct": list(card["correct"]),
            "wrong": [{"wrong": wrong, "right": right} for wrong, right in card["wrong"]],
            "steps": _pair(card["steps"], "steps", rid, minimum=2),
            "sources": list(card["sources"]),
            "figures": list(figures.get(rid, [])),
        }
    return out


def study() -> dict:
    out = {}
    for area in kit.AREA_ORDER:
        ids = [rid for rid in kit.RULE_ORDER if kit.RULES[rid][0] == area]
        out[area] = {"ru": [kit.RULES[rid][1] for rid in ids], "en": [kit.RULES[rid][2] for rid in ids], "lessons": ids}
    return out


def reference() -> dict:
    """Groups of the «Правила» screen: one per area, one row per rule card."""
    groups = []
    for area in kit.AREA_ORDER:
        items = []
        for rid in kit.RULE_ORDER:
            if kit.RULES[rid][0] != area:
                continue
            card = CARDS[rid]
            items.append({"rule": rid, "name": kit.bi(kit.RULES[rid][1], kit.RULES[rid][2]),
                          "summary": kit.bi(card["rule"][0][0], card["rule"][1][0]),
                          "examples": list(card["correct"][:3])})
        groups.append({"id": area, **kit.AREAS[area], "items": items})
    return {"groups": groups}
