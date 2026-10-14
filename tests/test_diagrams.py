"""Диаграммы физики: типизированный SVG, безопасность и достижимость.

Рисунки рисует не картинка, а список примитивов (``drawing``), который
приложение превращает в SVG. Поэтому проверять нужно не «красиво ли», а
безопасно ли: только белый список примитивов и атрибутов, только конечные
координаты внутри полотна, только переводимые подписи.
"""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "content_src"))

import build_content as build  # noqa: E402
import diagrams  # noqa: E402

ALLOWED = {
    "line": {"x1", "y1", "x2", "y2"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "rect": {"x", "y", "width", "height"},
    "polyline": {"points"},
    "polygon": {"points"},
    "text": {"x", "y", "text", "anchor"},
}
COMMON = {"kind", "role", "filled"}


class DiagramCatalogue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.figures = build.build_diagrams()

    def test_geometry_matches_the_interface(self):
        self.assertEqual((diagrams.WIDTH, diagrams.HEIGHT), (420, 280))
        self.assertGreaterEqual(len(self.figures), 26)

    def test_every_figure_is_bilingual_and_drawable(self):
        for figure_id, figure in self.figures.items():
            self.assertEqual(figure["id"], figure_id)
            self.assertEqual(figure["width"], diagrams.WIDTH)
            self.assertEqual(figure["height"], diagrams.HEIGHT)
            for lang in ("ru", "en"):
                self.assertTrue(figure["title"][lang].strip(), figure_id)
                self.assertTrue(figure["caption"][lang].strip(), figure_id)
            self.assertTrue(figure["drawing"], figure_id)

    def test_only_whitelisted_primitives_and_attributes(self):
        for figure_id, figure in self.figures.items():
            for node in figure["drawing"]:
                kind = node.get("kind")
                self.assertIn(kind, ALLOWED, f"{figure_id}: {kind}")
                allowed = COMMON | ALLOWED[kind]
                self.assertEqual(set(node) - allowed, set(),
                                 f"{figure_id}: посторонние атрибуты {sorted(set(node) - allowed)}")
                self.assertIn(node.get("role"), diagrams.ROLES, f"{figure_id}: {node.get('role')}")

    def test_coordinates_are_finite_and_inside_the_canvas(self):
        for figure_id, figure in self.figures.items():
            for node in figure["drawing"]:
                for key, value in node.items():
                    if key in ("x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r",
                               "rx", "ry", "width", "height"):
                        self.assertIsInstance(value, (int, float), f"{figure_id}.{key}")
                        self.assertFalse(value != value, f"{figure_id}.{key} — NaN")
                        self.assertTrue(0 <= value <= max(diagrams.WIDTH, diagrams.HEIGHT),
                                        f"{figure_id}.{key} = {value} вне полотна")
                if node.get("kind") in ("polyline", "polygon"):
                    self.assertTrue(node.get("points"), figure_id)
                    for point in node["points"]:
                        self.assertEqual(len(point), 2, figure_id)
                        for value in point:
                            self.assertIsInstance(value, (int, float), figure_id)
                            self.assertTrue(0 <= value <= max(diagrams.WIDTH, diagrams.HEIGHT),
                                            f"{figure_id}: точка {point} вне полотна")

    def test_labels_are_translated(self):
        for figure_id, figure in self.figures.items():
            for node in figure["drawing"]:
                if node["kind"] != "text":
                    continue
                text = node["text"]
                self.assertIsInstance(text, dict, f"{figure_id}: подпись не двуязычная")
                for lang in ("ru", "en"):
                    self.assertTrue(str(text[lang]).strip(), f"{figure_id}: пустая подпись")

    def test_no_unsafe_markup_in_labels(self):
        """Подписи — это текст, а не разметка.

        Сравнения вида «α > γ» в физике законны, поэтому запрещаем именно
        теги и обработчики, а не любые угловые скобки: рендер обязан
        экранировать текст (это проверяет theory_smoke).
        """
        import re
        tag = re.compile(r"<[a-zA-Z/]")
        for figure_id, figure in self.figures.items():
            for node in figure["drawing"]:
                if node["kind"] != "text":
                    continue
                for lang in ("ru", "en"):
                    value = str(node["text"][lang]).lower()
                    self.assertIsNone(tag.search(value), f"{figure_id}: {value!r}")
                    for forbidden in ("javascript:", "onload", "onerror"):
                        self.assertNotIn(forbidden, value, f"{figure_id}: {value!r}")

    def test_every_area_has_a_figure(self):
        """Каждая из 13 содержательных областей опирается хотя бы на одну схему."""
        with contextlib.redirect_stdout(io.StringIO()):
            lessons = build.build_theory(self.figures)
        covered = {figure for lesson in lessons.values() for figure in lesson["figures"]}
        self.assertEqual(set(self.figures) - covered, set())
        self.assertGreaterEqual(len(self.figures), 26)


if __name__ == "__main__":
    unittest.main()
