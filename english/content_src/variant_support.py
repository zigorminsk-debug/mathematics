"""Constructors for explicitly authored yearly practice sets (not exam archives).

Each row contains a new question, exact answer and bilingual explanation.
Years label sets; all use the current practice structure, not a claim about
historical ЦТ structures. No questions are copied or relabelled from 2026.
"""
import kit


def tasks_for(year, choices, written):
    out = []
    for n, row in enumerate(choices, 1):
        tag, text, options, ru, en = row
        topic = {"pronouns": "pronouns_numerals"}.get(tag.split('.')[0], tag.split('.')[0])
        out.append(kit.choice(
            f"en-{year}-A{n}", year=year, part="A", n=n, topic=topic,
            text=text, answer=options[0], options=options,
            correction={"ru": ru, "en": en}, tags=[tag]))
    for n, row in enumerate(written, 1):
        tag, text, answer, ru, en, *given = row
        topic = tag.split('.')[0]
        kind = {"gap_fill": "gap", "extra_word": "extra", "word_formation": "form"}[topic]
        out.append(kit.typed(
            f"en-{year}-B{n}", year=year, part="B", n=n, topic=topic,
            kind=kind, text=text, answer=answer,
            correction={"ru": ru, "en": en}, tags=[tag],
            **(given[0] if given and isinstance(given[0], dict) else
               {"given": given[0]} if given else {})))
    return out
