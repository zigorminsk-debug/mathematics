"""Иконка английского тренажёра: речевое облако с «EN».

Проверяется то, что легко испортить руками: растр обязан побайтово совпадать с
генератором (``english/tools/make_icon.py``), векторный исходник — рисовать то же
облако, все копии (webapp, english/windows/web, android assets и растровые иконки
лаунчера) должны быть одинаковыми, а знаки других предметов — «Σ» математики и
атом физики — не должны остаться нигде.
"""

from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGLISH = ROOT / "english"
sys.path.insert(0, str(ENGLISH / "tools"))

import make_icon  # noqa: E402

COPIES = [
    ENGLISH / "webapp" / "icon.png",
    ENGLISH / "windows" / "web" / "icon.png",
    ENGLISH / "android" / "app" / "src" / "main" / "assets" / "webapp" / "icon.png",
]
SVG_COPIES = [
    ENGLISH / "webapp" / "icon.svg",
    ENGLISH / "windows" / "web" / "icon.svg",
    ENGLISH / "android" / "app" / "src" / "main" / "assets" / "webapp" / "icon.svg",
]
BACKGROUND = ENGLISH / "android" / "app" / "src" / "main" / "res" / "drawable" / "ic_launcher_background.xml"
#: Знаки других предметов: «Σ» — математика, атом — физика.
FOREIGN = ("Σ", "\u03a3", "атом", "орбит", "ellipse")
#: Фирменные цвета английского приложения (styles.css, colors.xml, генератор).
PALETTE = {"#3DC9A6", "#116E7A", "#0E6B60", "#FFFFFF"}
FORBIDDEN_COLOURS = ("#FFD166", "#213F9C", "#2F5FD0", "#3A6FE0", "#4A7CE8")   # физика и математика


class Raster(unittest.TestCase):

    def test_the_png_is_exactly_what_the_generator_draws(self):
        expected = make_icon.render()
        for path in COPIES:
            self.assertTrue(path.exists(), f"нет файла {path}")
            size, stored = make_icon.decode_png(path.read_bytes())
            self.assertEqual(size, make_icon.SIZE, path)
            differences = sum(1 for y in range(size) for x in range(size)
                              if stored[y][x] != expected[y][x])
            self.assertEqual(differences, 0,
                             f"{path.relative_to(ROOT)}: {differences} пикселей отличаются от "
                             f"генератора — перерисуйте: python3 english/tools/make_icon.py")

    def test_copies_are_identical(self):
        first = COPIES[0].read_bytes()
        for path in COPIES[1:]:
            self.assertEqual(path.read_bytes(), first, f"{path.relative_to(ROOT)} устарел")

    def test_the_drawing_uses_the_english_brand_colours(self):
        """Облако белое, буквы тёмно-бирюзовые, фон — бирюзовый градиент."""
        rows = make_icon.render()
        middle = make_icon.SIZE // 2
        # внутри облака, левее буквы — белое поле
        bubble = rows[mid_bubble_y := middle][make_icon.BUBBLE[0] and 42]
        self.assertEqual(bubble[:3], make_icon.BUBBLE_COLOR, "внутри облака должно быть белое поле")
        self.assertEqual(bubble[3], 255)
        # буква «E» — вертикальная стойка
        letter = rows[int((make_icon.LETTER_TOP + make_icon.LETTER_BOTTOM) / 2)][int(make_icon.E_X + 2)]
        self.assertEqual(letter[:3], make_icon.LETTER_COLOR, "буква «E» не нарисована")
        # за скруглением квадрата — прозрачность
        self.assertEqual(rows[1][1][3], 0, "за скруглением иконка прозрачна")
        # фон в левом верхнем углу — бирюзовый, и он светлее правого нижнего
        top_left = rows[24][24][:3]
        bottom_right = rows[make_icon.SIZE - 24][make_icon.SIZE - 24][:3]
        for channel in range(3):
            self.assertGreaterEqual(top_left[channel], bottom_right[channel],
                                    "градиент идёт светлым вверх-влево и тёмным вниз-вправо")
        self.assertGreater(top_left[1], top_left[0], "фон бирюзовый: зелёного больше синего")
        self.assertNotIn("#%02X%02X%02X" % bottom_right, FORBIDDEN_COLOURS)

    def test_both_letters_are_visible(self):
        """«E» и «N» — не пустое облако: в точках стоек обеих букв тёмный цвет."""
        rows = make_icon.render()
        y = int((make_icon.LETTER_TOP + make_icon.LETTER_BOTTOM) / 2)
        for x in (int(make_icon.E_X + 2), int(make_icon.N_LEFT_X + 2), int(make_icon.N_RIGHT_X + 2)):
            self.assertEqual(rows[y][x][:3], make_icon.LETTER_COLOR, f"буква не нарисована в x={x}")

    def test_the_foreground_layer_fits_the_safe_zone(self):
        """Слой адаптивной иконки: облако в безопасной зоне, фон прозрачный."""
        size = make_icon.FOREGROUND_SIZE
        rows = make_icon.render(size, "foreground")
        # углы прозрачны (Android рисует там свой фон)
        self.assertEqual(rows[0][0][3], 0)
        self.assertEqual(rows[size - 1][size - 1][3], 0)
        # в центре — белое облако с тёмными буквами
        centre = rows[size // 2][size // 2]
        self.assertIn(centre[:3], (make_icon.BUBBLE_COLOR, make_icon.LETTER_COLOR))
        # рисунок не касается краёв: значит, любая маска лаунчера его не обрежет
        painted = [(x, y) for y in range(size) for x in range(size) if rows[y][x][3] > 0]
        self.assertTrue(painted, "передний слой пуст")
        xs = [point[0] for point in painted]
        ys = [point[1] for point in painted]
        margin = min(min(xs), min(ys), size - 1 - max(xs), size - 1 - max(ys))
        self.assertGreaterEqual(margin, 8, f"рисунок вплотную к краю (отступ {margin} px)")

    def test_the_round_variant_is_a_circle(self):
        rows = make_icon.render(make_icon.SIZE, "round")
        self.assertEqual(rows[0][0][3], 0, "углы круглой иконки прозрачны")
        self.assertEqual(rows[4][make_icon.SIZE - 5][3], 0, "правый верхний угол — вне круга")
        self.assertEqual(rows[make_icon.SIZE // 2 - 30][make_icon.SIZE // 2][3], 255,
                         "внутри круга иконка непрозрачна")
        # на самой окружности и чуть внутри — рисунок есть
        inside = rows[make_icon.SIZE // 2 - int(make_icon.SIZE / 2) + 6][make_icon.SIZE // 2]
        self.assertEqual(inside[3], 255, "у верхней точки круга рисунок непрозрачен")


class Vectors(unittest.TestCase):

    def test_the_svg_draws_the_same_bubble(self):
        for path in SVG_COPIES:
            text = path.read_text(encoding="utf-8")
            for foreign in ("Σ", "\u03a3", "атом", "ellipse"):
                self.assertNotIn(foreign, text, f"{path.relative_to(ROOT)}: остался знак «{foreign}»")
            self.assertIn("#3DC9A6", text, path)
            self.assertIn("#116E7A", text, path)
            self.assertIn("#0E6B60", text, path)
            # геометрия совпадает с генератором (числа, а не похожесть строк)
            corner = re.search(r'<rect width="192" height="192" rx="([\d.]+)"', text)
            self.assertIsNotNone(corner, path)
            self.assertAlmostEqual(float(corner.group(1)), make_icon.RADIUS, places=3, msg=str(path))
            bubble = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="([\d.]+)"',
                               text)
            self.assertIsNotNone(bubble, path)
            self.assertEqual(float(bubble.group(1)), make_icon.BUBBLE[0], path)
            self.assertEqual(float(bubble.group(2)), make_icon.BUBBLE[1], path)
            self.assertEqual(float(bubble.group(3)), make_icon.BUBBLE[2] - make_icon.BUBBLE[0], path)
            self.assertEqual(float(bubble.group(4)), make_icon.BUBBLE[3] - make_icon.BUBBLE[1], path)
            self.assertEqual(float(bubble.group(5)), make_icon.BUBBLE_RADIUS, path)
            tail = re.search(r'<polygon points="([^"]+)"', text)
            self.assertIsNotNone(tail, path)
            points = [tuple(float(value) for value in pair.split(",")) for pair in tail.group(1).split()]
            self.assertEqual(points, [tuple(point) for point in make_icon.TAIL],
                             f"{path.relative_to(ROOT)}: хвостик облака разошёлся с генератором")
            # буквы: стойки «E» и «N» и диагональ — те же числа, что в генераторе
            self.assertIn(f'x="{make_icon.E_X:g}"', text, path)
            self.assertIn(f'x="{make_icon.N_LEFT_X:g}"', text, path)
            self.assertIn(f'x="{make_icon.N_RIGHT_X:g}"', text, path)
            self.assertIn(f'stroke-width="{make_icon.STROKE:g}"', text, path)

    def test_android_launcher_uses_the_bubble(self):
        """Растр лаунчера совпадает с генератором, фон — векторный градиент."""
        problems = make_icon.check_android()
        self.assertEqual(problems, [], "; ".join(problems))
        background = BACKGROUND.read_text(encoding="utf-8")
        for foreign in FORBIDDEN_COLOURS:
            self.assertNotIn(foreign, background, "в фоне лаунчера остался цвет другого предмета")
        colours = set(re.findall(r"#[0-9A-Fa-f]{6}", background))
        self.assertTrue(colours, "фон лаунчера без цветов")
        self.assertTrue(colours <= {"#3DC9A6", "#116E7A", "#2FB894"},
                        f"посторонние цвета: {sorted(colours)}")

    def test_every_density_has_all_three_icons(self):
        for folder, factor in make_icon.DENSITIES:
            directory = make_icon.ANDROID_RES / f"mipmap-{folder}"
            for name, base in (("ic_launcher.png", make_icon.LAUNCHER_BASE),
                               ("ic_launcher_round.png", make_icon.LAUNCHER_BASE),
                               ("ic_launcher_foreground.png", make_icon.FOREGROUND_SIZE)):
                path = directory / name
                self.assertTrue(path.exists(), f"нет {path.relative_to(ROOT)}")
                size, _ = make_icon.decode_png(path.read_bytes())
                self.assertEqual(size, round(base * factor), path)

    def test_the_generator_has_no_third_party_dependencies(self):
        """Иконка рисуется стандартной библиотекой: CI не тянет картинки из сети."""
        source = (ENGLISH / "tools" / "make_icon.py").read_text(encoding="utf-8")
        imports = set(re.findall(r"^\s*(?:import|from)\s+([a-zA-Z_][\w.]*)", source, re.M))
        self.assertTrue(imports <= {"__future__", "argparse", "pathlib", "struct", "sys", "zlib"},
                        f"лишние зависимости: {sorted(imports)}")


if __name__ == "__main__":
    unittest.main()
