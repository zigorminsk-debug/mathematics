"""Офлайновая теория физики: уроки, конспекты и достижимость ссылок.

Каждый пункт конспекта («что повторить») обязан открывать урок с определениями,
условиями применимости формул, бытовым объяснением и разобранным примером — и всё
это на двух языках. Эти тесты ловят именно разъезд текстов, а не опечатки в
разметке.
"""

from __future__ import annotations

import contextlib
import copy
import io
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "content_src"))

import build_content as build  # noqa: E402
import diagrams  # noqa: E402
import formulas  # noqa: E402
import kit  # noqa: E402
import study  # noqa: E402
import theory  # noqa: E402


def quiet(function, *arguments, **keywords):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*arguments, **keywords)


class TheoryCatalogue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.figures = quiet(build.build_diagrams)
        cls.lessons = quiet(build.build_theory, cls.figures)
        cls.notes = quiet(build.build_study, kit.TOPIC_ORDER, cls.lessons)

    def test_every_topic_has_notes(self):
        self.assertEqual(set(self.notes), set(kit.TOPIC_ORDER))
        self.assertEqual(len(kit.TOPIC_ORDER), 13)

    def test_summary_points_link_to_lessons(self):
        for topic, entry in self.notes.items():
            for lang in ("ru", "en"):
                self.assertGreaterEqual(len(entry[lang]), 2, topic)
                self.assertEqual(len(entry[lang]), len(entry["lessons"]), topic)
            self.assertTrue(entry.get("formulas"), topic)
            for lesson_id in entry["lessons"]:
                self.assertIn(lesson_id, self.lessons, topic)

    def test_lessons_are_reachable(self):
        used = {lesson for entry in self.notes.values() for lesson in entry["lessons"]}
        for group in formulas.groups()["groups"]:
            used.update(group["lessons"])
        self.assertEqual(set(self.lessons) - used, set(),
                         "уроки, недостижимые из конспектов")

    def test_lessons_are_bilingual_and_complete(self):
        for lesson_id, lesson in self.lessons.items():
            self.assertEqual(lesson["id"], lesson_id)
            for lang in ("ru", "en"):
                self.assertTrue(lesson["title"][lang].strip(), lesson_id)
                self.assertEqual(len(lesson["definitions"]["ru"]),
                                 len(lesson["definitions"]["en"]), lesson_id)
                self.assertEqual(len(lesson["rules"]["ru"]),
                                 len(lesson["rules"]["en"]), lesson_id)
                self.assertEqual(len(lesson["everyday"]["ru"]),
                                 len(lesson["everyday"]["en"]), lesson_id)
            self.assertGreaterEqual(len(lesson["definitions"]["ru"]), 1, lesson_id)
            self.assertGreaterEqual(len(lesson["everyday"]["ru"]), 2, lesson_id)

    def test_worked_examples_have_parallel_solutions(self):
        for lesson_id, lesson in self.lessons.items():
            for example in lesson["examples"]:
                for lang in ("ru", "en"):
                    self.assertTrue(example["statement"][lang].strip(), lesson_id)
                    self.assertGreaterEqual(len(example["steps"][lang]), 2, lesson_id)

    def test_model_limits_are_explained(self):
        """У каждого урока есть оговорка о том, где модель перестаёт работать.

        Формулировки живут в ``theory.LIMITS`` и попадают последним абзацем в
        бытовое объяснение: так их видно в приложении и нельзя потерять при
        правке текста.
        """
        self.assertEqual(set(theory.LIMITS), set(self.lessons),
                         "оговорка нужна каждому уроку и только существующим")
        for lesson_id, lesson in self.lessons.items():
            ru, en = theory.LIMITS[lesson_id]
            self.assertEqual(lesson["everyday"]["ru"][-1], ru, lesson_id)
            self.assertEqual(lesson["everyday"]["en"][-1], en, lesson_id)
            self.assertGreaterEqual(len(ru.split()), 8, lesson_id)
            self.assertGreaterEqual(len(en.split()), 8, lesson_id)

    def test_figures_are_linked_and_existing(self):
        for lesson_id, lesson in self.lessons.items():
            for figure in lesson["figures"]:
                self.assertIn(figure, self.figures, lesson_id)
        linked = {figure for lesson in self.lessons.values() for figure in lesson["figures"]}
        self.assertEqual(set(self.figures) - linked, set(), "фигуры без урока")


class AuthoringGates(unittest.TestCase):
    """Сборка обязана останавливаться на неполном тексте, а не публиковать его."""

    def test_empty_definitions_are_rejected(self):
        broken = copy.deepcopy(theory.payload())
        first = next(iter(broken))
        broken[first]["definitions"]["en"] = []
        with patch.object(theory, "payload", return_value=broken), self.assertRaises(SystemExit):
            quiet(build.build_theory, quiet(build.build_diagrams))

    def test_parallel_language_paragraphs_are_enforced(self):
        broken = copy.deepcopy(theory.payload())
        first = next(iter(broken))
        broken[first]["rules"]["ru"].append("Абзац без перевода")
        with patch.object(theory, "payload", return_value=broken), self.assertRaises(SystemExit):
            quiet(build.build_theory, quiet(build.build_diagrams))

    def test_missing_figure_link_is_rejected(self):
        broken = copy.deepcopy(theory.payload())
        first = next(iter(broken))
        broken[first]["figures"] = ["no-such-figure"]
        with patch.object(theory, "payload", return_value=broken), self.assertRaises(SystemExit):
            quiet(build.build_theory, quiet(build.build_diagrams))

    def test_study_point_without_lesson_is_rejected(self):
        lessons = quiet(build.build_theory, quiet(build.build_diagrams))
        broken = copy.deepcopy(study.payload())
        topic = kit.TOPIC_ORDER[0]
        broken[topic]["lessons"] = broken[topic]["lessons"][:-1]
        with patch.object(study, "payload", return_value=broken), self.assertRaises(SystemExit):
            quiet(build.build_study, kit.TOPIC_ORDER, lessons)


if __name__ == "__main__":
    unittest.main()
