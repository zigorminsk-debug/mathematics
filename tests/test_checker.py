"""The subject answer checker (Python reference) and its explicit check contract."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content_src"))
import checker  # noqa: E402
import vectors  # noqa: E402


def word(answer, **policy):
    spec = {"type": "word", "scoring": "exact", "order": "n/a", "answer": answer, "accept": [],
            "case": "insensitive", "yo": "strict", "hyphen": "typographic"}
    spec.update(policy)
    return spec


class VectorCorpusTests(unittest.TestCase):
    def test_every_hand_written_vector(self):
        self.assertGreaterEqual(len(vectors.CASES), 100)
        for spec, user, expect, why in vectors.CASES:
            with self.subTest(user=user, why=why):
                self.assertEqual(expect, checker.check(user, spec))

    def test_corpus_covers_the_required_classes(self):
        whys = " ".join(case[3] for case in vectors.CASES)
        for topic in ("significant space", "hyphen", "ё", "case", "stress", "NFC", "extra selection", "order is the answer",
                      "duplicate", "missing selection", "unknown check type", "Latin"):
            self.assertIn(topic, whys)
        kinds = {case[0]["type"] for case in vectors.CASES}
        self.assertEqual(set(checker.TYPES) | {"formula"}, kinds)

    def test_payload_shape(self):
        payload = vectors.payload()
        self.assertEqual(2, payload["schema"])
        self.assertEqual(len(vectors.CASES), len({case["id"] for case in payload["cases"]}))


class ContractTests(unittest.TestCase):
    def test_policies_are_mandatory(self):
        for field in ("case", "yo", "hyphen", "scoring", "order"):
            broken = word("так же")
            del broken[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                checker.validate(broken)
        with self.assertRaises(ValueError):
            checker.validate(word("так же", scoring="partial"))

    def test_canonical_answers_must_be_clean(self):
        for bad in (" так же", "так  же", "е\u0308лка", "за\u0301мок", "по\u2011новому"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                checker.validate(word(bad))
        with self.assertRaises(ValueError):  # alternatives need a justification
            checker.validate(word("восемью", accept=["восьмью"]))
        with self.assertRaises(ValueError):  # duplicate alternative after normalisation
            checker.validate(word("Тоже", accept=["тоже"], acceptWhy={"ru": ["x"], "en": ["x"]}))

    def test_part_a_has_several_but_not_all_correct_options(self):
        base = {"type": "multi", "scoring": "exact", "order": "unordered", "options": 5}
        checker.validate(dict(base, answer=[1, 3]))
        for answer in ([1], [1, 2, 3, 4, 5], [3, 1], [1, 1], [6], []):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                checker.validate(dict(base, answer=answer))

    def test_order_declarations(self):
        checker.validate({"type": "numbers", "scoring": "exact", "order": "ordered", "max": 5, "answer": [2, 1]})
        with self.assertRaises(ValueError):
            checker.validate({"type": "numbers", "scoring": "exact", "order": "unordered", "max": 5, "answer": [2, 1]})
        with self.assertRaises(ValueError):
            checker.validate({"type": "numbers", "scoring": "exact", "order": "any", "max": 5, "answer": [1, 2]})

    def test_stress_tasks_are_exact(self):
        spec = {"type": "stress", "scoring": "exact", "order": "n/a", "word": "каталог", "answer": 5, "display": "катало\u0301г"}
        checker.validate(spec)
        for bad in (dict(spec, answer=4), dict(spec, display="ката\u0301лог"), dict(spec, word="Каталог"),
                    dict(spec, word="ёлка", answer=0, display="ё\u0301лка")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                checker.validate(bad)

    def test_no_keyword_or_regex_leniency(self):
        spec = word("сломя голову")
        for attempt in ("сломя голову бежал", "голову", ".*", "сломя.*голову", "сломяголову"):
            self.assertFalse(checker.check(attempt, spec), attempt)

    def test_match_requires_every_label_once(self):
        spec = {"type": "match", "scoring": "exact", "order": "by-label", "labels": ["А", "Б"], "right": 3,
                "answer": {"А": 2, "Б": 2}}
        checker.validate(spec)
        self.assertTrue(checker.check("А2Б2", spec))
        self.assertFalse(checker.check("А2", spec))
        broken = deepcopy(spec)
        broken["answer"]["В"] = 1
        with self.assertRaises(ValueError):
            checker.validate(broken)

    def test_display_forms(self):
        self.assertEqual("1, 3", checker.display({"type": "multi", "answer": [1, 3]}))
        self.assertEqual("А1 Б2", checker.display({"type": "match", "labels": ["А", "Б"], "answer": {"А": 1, "Б": 2}}))


if __name__ == "__main__":
    unittest.main()
