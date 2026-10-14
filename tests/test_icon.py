"""Иконка приложения по физике: атом, а не математическая «Σ».

Проверяется то, что легко испортить руками: растр обязан побайтово совпадать с
генератором (`tools/make_icon.py`), векторные исходники — рисовать тот же атом,
а математические знаки не должны остаться ни в одной из четырёх копий
(webapp, windows/web, android assets и Android-векторы лаунчера).
"""

from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import make_icon  # noqa: E402

COPIES = [
    ROOT / "webapp" / "icon.png",
    ROOT / "windows" / "web" / "icon.png",
    ROOT / "android" / "app" / "src" / "main" / "assets" / "webapp" / "icon.png",
]
SVG_COPIES = [
    ROOT / "webapp" / "icon.svg",
    ROOT / "windows" / "web" / "icon.svg",
    ROOT / "android" / "app" / "src" / "main" / "assets" / "webapp" / "icon.svg",
]
FOREGROUND = ROOT / "android" / "app" / "src" / "main" / "res" / "drawable" / "ic_launcher_foreground.xml"
BACKGROUND = ROOT / "android" / "app" / "src" / "main" / "res" / "drawable" / "ic_launcher_background.xml"
#: Знаки другого предмета: «Σ» — логотип математической версии.
FOREIGN = ("Σ", "\u03a3")


class Raster(unittest.TestCase):

    def test_the_png_is_exactly_what_the_generator_draws(self):
        expected = make_icon.render()
        for path in COPIES:
            self.assertTrue(path.exists(), f"нет файла {path}")
            stored = make_icon.decode_png(path.read_bytes())
            self.assertEqual(len(stored), make_icon.SIZE, path)
            differences = sum(1 for y in range(make_icon.SIZE) for x in range(make_icon.SIZE)
                              if stored[y][x] != expected[y][x])
            self.assertEqual(differences, 0,
                             f"{path.relative_to(ROOT)}: {differences} пикселей отличаются от "
                             f"генератора — перерисуйте: python3 tools/make_icon.py")

    def test_copies_are_identical(self):
        first = COPIES[0].read_bytes()
        for path in COPIES[1:]:
            self.assertEqual(path.read_bytes(), first, f"{path.relative_to(ROOT)} устарел")

    def test_the_drawing_uses_the_brand_colours(self):
        """Ядро — акцентный цвет, орбиты — белые, фон — фирменный синий."""
        rows = make_icon.render()
        center = rows[make_icon.SIZE // 2][make_icon.SIZE // 2]
        self.assertEqual(center[:3], make_icon.NUCLEUS_COLOR, "в центре должно быть ядро")
        self.assertEqual(center[3], 255)
        corner = rows[3][3]
        self.assertEqual(corner[3], 0, "за скруглением иконка прозрачна")
        # на орбите (крайняя точка по горизонтали) — белая линия
        middle = make_icon.SIZE // 2
        orbit_x = int(make_icon.CENTER[0] + make_icon.ORBIT_A)
        self.assertEqual(rows[middle][orbit_x][:3], make_icon.ORBIT_COLOR, "орбита должна быть белой")
        # вдали от рисунка (левый верхний угол) — фирменный синий, не жёлтый
        background = rows[30][30][:3]
        self.assertNotEqual(background, make_icon.NUCLEUS_COLOR)
        self.assertGreater(background[2], background[1], "фон — синий")
        self.assertGreater(background[2], background[0], "фон — синий")

    def test_three_orbits_are_visible(self):
        """Повороты 0°, 60° и −60° дают замкнутый рисунок: сверяем все три."""
        rows = make_icon.render()
        middle = make_icon.SIZE // 2
        for angle in make_icon.ORBIT_ANGLES:
            # точка на дальней части орбиты: поворачиваем вектор (a, 0) на угол
            cos, sin = make_icon._trig(angle * 3.141592653589793 / 180.0)
            x = make_icon.CENTER[0] + make_icon.ORBIT_A * cos
            y = make_icon.CENTER[1] - make_icon.ORBIT_A * sin
            pixel = rows[int(round(y))][int(round(x))]
            self.assertEqual(pixel[:3], make_icon.ORBIT_COLOR,
                             f"орбита {angle}° не нарисована в точке ({x:.1f}, {y:.1f})")


class Vectors(unittest.TestCase):

    def test_the_svg_draws_the_same_atom(self):
        for path in SVG_COPIES:
            text = path.read_text(encoding="utf-8")
            for foreign in FOREIGN:
                self.assertNotIn(foreign, text, f"{path.relative_to(ROOT)}: остался знак {foreign}")
            self.assertEqual(text.count("<ellipse"), 3, path)
            self.assertEqual(text.count("<circle"), 1, path)
            self.assertIn("rotate(60", text, path)
            self.assertIn("rotate(-60", text, path)
            self.assertIn("#ffd166", text.lower(), path)
            # геометрия совпадает с генератором растра (числа, а не строки)
            ellipses = re.findall(r'<ellipse cx="([\d.]+)" cy="([\d.]+)" rx="([\d.]+)" ry="([\d.]+)"', text)
            self.assertEqual(len(ellipses), 3, path)
            for cx, cy, rx, ry in ellipses:
                self.assertAlmostEqual(float(cx), make_icon.CENTER[0], places=3, msg=str(path))
                self.assertAlmostEqual(float(cy), make_icon.CENTER[1], places=3, msg=str(path))
                self.assertAlmostEqual(float(rx), make_icon.ORBIT_A, places=3, msg=str(path))
                self.assertAlmostEqual(float(ry), make_icon.ORBIT_B, places=3, msg=str(path))
            nucleus = re.search(r'<circle cx="[\d.]+" cy="[\d.]+" r="([\d.]+)"', text)
            self.assertIsNotNone(nucleus, path)
            self.assertAlmostEqual(float(nucleus.group(1)), make_icon.NUCLEUS_R, places=3, msg=str(path))
            stroke = re.search(r'stroke-width="([\d.]+)"', text)
            self.assertIsNotNone(stroke, path)
            self.assertAlmostEqual(float(stroke.group(1)), make_icon.ORBIT_WIDTH, places=3, msg=str(path))
            corner = re.search(r'rx="([\d.]+)" fill="url', text)
            self.assertIsNotNone(corner, path)
            self.assertAlmostEqual(float(corner.group(1)), make_icon.RADIUS, places=3, msg=str(path))

    def test_android_launcher_uses_the_atom(self):
        foreground = FOREGROUND.read_text(encoding="utf-8")
        for foreign in FOREIGN:
            self.assertNotIn(foreign, foreground, "в лаунчере остался математический знак")
        self.assertEqual(foreground.count('android:rotation="60"'), 1)
        self.assertEqual(foreground.count('android:rotation="-60"'), 1)
        # три орбиты одной формы (в каждой — по две дуги эллипса)
        self.assertEqual(foreground.count('android:pathData="M22.5,54 a31.5,11.8'), 3,
                         "три орбиты одной формы")
        self.assertIn("#FFD166", foreground, "ядро — акцентный цвет")
        self.assertIn("#FFFFFF", foreground, "орбиты белые")

    def test_android_background_stays_in_the_brand_palette(self):
        background = BACKGROUND.read_text(encoding="utf-8")
        for foreign in FOREIGN:
            self.assertNotIn(foreign, background)
        colours = set(re.findall(r"#[0-9A-Fa-f]{6}", background))
        palette = {"#213F9C", "#3A6FE0", "#4A7CE8", "#2F5FD0", "#FFD166"}
        self.assertTrue(colours <= palette, f"посторонние цвета: {sorted(colours - palette)}")
        self.assertGreaterEqual(len(colours), 2, "фон должен иметь светлую и тёмную часть")


if __name__ == "__main__":
    unittest.main()
