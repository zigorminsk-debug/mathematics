"""Content gates for the clickable offline theory catalogue."""
from copy import deepcopy
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_content as build
import formulas
import kit
import study
import theory


class TheoryContentTests(unittest.TestCase):
    def test_complete_reachable_catalogue(self):
        with contextlib.redirect_stdout(io.StringIO()):
            lessons = build.build_theory()
            notes = build.build_study(kit.TOPIC_ORDER, lessons)
        self.assertEqual(set(kit.TOPIC_ORDER), set(notes))
        self.assertEqual(54, sum(len(entry["lessons"]) for entry in notes.values()))
        self.assertEqual(116, sum(len(group["items"]) for group in formulas.groups()["groups"]))
        self.assertGreaterEqual(len(lessons), 50)

    def test_definitions_and_theorems_cannot_be_empty(self):
        for field in ("definitions", "rules"):
            for lang in ("ru", "en"):
                lessons = deepcopy(theory.payload())
                lessons["order"][field][lang] = []
                with self.subTest(field=field, lang=lang), \
                     patch.object(theory, "payload", return_value=lessons), \
                     self.assertRaises(SystemExit):
                    build.build_theory()

    def test_example_needs_bilingual_solution(self):
        lessons = deepcopy(theory.payload())
        lessons["fractions"]["examples"][0]["steps"]["en"] = ["No solution"]
        with patch.object(theory, "payload", return_value=lessons), self.assertRaises(SystemExit):
            build.build_theory()

    def test_parallel_language_paragraphs(self):
        lessons = deepcopy(theory.payload())
        lessons["order"]["rules"]["ru"].append("Untranslated paragraph")
        with patch.object(theory, "payload", return_value=lessons), self.assertRaises(SystemExit):
            build.build_theory()

    def test_each_summary_point_needs_a_link(self):
        for ids in (["order", "fractions"], ["order", "missing-lesson", "decimals"]):
            notes = deepcopy(study.payload())
            notes["numbers"]["lessons"] = ids
            with self.subTest(ids=ids), patch.object(study, "payload", return_value=notes), \
                 self.assertRaises(SystemExit):
                build.build_study(kit.TOPIC_ORDER, theory.payload())

    def test_each_formula_needs_a_valid_link(self):
        for invalid in (None, "missing-lesson"):
            groups = deepcopy(formulas.groups())
            groups["groups"][0]["items"][0]["lesson"] = invalid
            with self.subTest(invalid=invalid), patch.object(formulas, "groups", return_value=groups), \
                 self.assertRaises(SystemExit):
                build.build_study(kit.TOPIC_ORDER, theory.payload())

    def test_authoring_cannot_add_unlinked_formula(self):
        with patch.dict(theory.FORMULA_LESSONS, {"powers": ["powers"]}):
            with self.assertRaises(ValueError):
                formulas.groups()

    def test_unreachable_lessons_are_rejected(self):
        lessons = deepcopy(theory.payload())
        lessons["unreachable"] = deepcopy(lessons["order"])
        lessons["unreachable"]["id"] = "unreachable"
        with self.assertRaises(SystemExit):
            build.build_study(kit.TOPIC_ORDER, lessons)


if __name__ == "__main__":
    unittest.main()
