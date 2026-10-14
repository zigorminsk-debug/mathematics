#!/usr/bin/env python3
"""Знак приложения «Репетитор ЦТ: Английский язык»: речевое облако с «EN».

Иконка рисуется кодом (только ``zlib`` и ``struct`` — никаких зависимостей,
чтобы генератор работал и на голом CI-раннере) и живёт в четырёх видах, которые
обязаны совпадать:

* ``webapp/icon.png`` — favicon и ``apple-touch-icon`` (их отдаёт и Windows-сборка);
* ``webapp/icon.svg`` — та же геометрия вектором;
* ``android/app/src/main/res/mipmap-*/ic_launcher{,_round,_foreground}.png`` —
  растровые иконки лаунчера: ``ic_launcher`` — квадрат со скруглением
  (исторические лаунчеры), ``_round`` — круг, ``_foreground`` — передний слой
  адаптивной иконки (облако с «EN» без фона, вписанное в безопасную зону);
* ``android/app/src/main/res/drawable/ic_launcher_background.xml`` — векторный
  фон адаптивной иконки (бирюзовый градиент).

Смысл знака: облако — про речь и общение, «EN» — про английский язык как предмет.
Ни «Σ» математики, ни атом физики здесь не повторяются: своё облако, свой
бирюзовый градиент, своя пара букв. Проверяется тестом ``english/tests/test_icon.py``.

Использование::

    python3 english/tools/make_icon.py                 # перерисовать webapp/icon.png
    python3 english/tools/make_icon.py --android       # и все иконки Android
    python3 english/tools/make_icon.py --check         # сверить всё с генератором (CI)
"""

from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "webapp" / "icon.png"
ANDROID_RES = ROOT / "android" / "app" / "src" / "main" / "res"

# --- геометрия (192 × 192; те же числа заданы в webapp/icon.svg) ----------- #
SIZE = 192
RADIUS = 42                    # скругление квадрата
BUBBLE = (36.0, 44.0, 156.0, 130.0)   # облако: x0, y0, x1, y1
BUBBLE_RADIUS = 26.0
TAIL = ((66.0, 128.0), (98.0, 128.0), (70.0, 158.0))   # хвостик облака
LETTER_TOP, LETTER_BOTTOM = 68.0, 116.0
STROKE = 10.0                  # толщина штриха букв
E_X, E_BAR, E_TOP_WIDTH, E_MID_WIDTH = 46.0, 10.0, 44.0, 34.0
N_LEFT_X, N_RIGHT_X, N_WIDTH = 100.0, 134.0, 10.0

# --- палитра (та же, что в webapp/styles.css и android/.../colors.xml) ----- #
GRADIENT_FROM = (0x3D, 0xC9, 0xA6)   # бирюзовый
GRADIENT_TO = (0x11, 0x6E, 0x7A)     # глубокая бирюза
BUBBLE_COLOR = (0xFF, 0xFF, 0xFF)
LETTER_COLOR = (0x0E, 0x6B, 0x60)
SUPERSAMPLE = 3

# --- передний слой адаптивной иконки: 108 dp, безопасная зона 66 dp -------- #
FOREGROUND_SIZE = 108
FOREGROUND_SCALE = 0.44        # 120 × 86 арт-единиц облака → ~53 × 38 dp
FOREGROUND_OFFSET = (11.8, 9.6)

#: плотности Android: имя папки → коэффициент к 1x (48 dp для ic_launcher)
DENSITIES = (("mdpi", 1.0), ("hdpi", 1.5), ("xhdpi", 2.0),
             ("xxhdpi", 3.0), ("xxxhdpi", 4.0))
LAUNCHER_BASE = 48             # базовая иконка лаунчера, dp

BACKGROUND_XML = """<?xml version="1.0" encoding="utf-8"?>
<!-- Фон иконки: фирменный бирюзовый градиент #3DC9A6 → #116E7A (как в
     webapp/icon.svg). Две плоские фигуры вместо <gradient>: векторный градиент
     требует aapt-атрибутов, а фон обязан собираться на любой версии AGP без
     риска для сборки APK. Передний слой — mipmap-*/ic_launcher_foreground.png. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:pathData="M0,0h108v108h-108z" android:fillColor="#116E7A"/>
    <path android:pathData="M0,0h108L0,108z" android:fillColor="#3DC9A6"/>
    <path android:pathData="M0,0h108L54,54z" android:fillColor="#2FB894"/>
</vector>
"""


def _inside_rounded_square(x: float, y: float) -> bool:
    left, right = RADIUS, SIZE - RADIUS
    cx = min(max(x, left), right)
    cy = min(max(y, left), right)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= RADIUS * RADIUS


def _inside_circle(x: float, y: float) -> bool:
    dx, dy = x - SIZE / 2, y - SIZE / 2
    return dx * dx + dy * dy <= (SIZE / 2) ** 2


def _inside_rounded_rect(x: float, y: float, box, radius: float) -> bool:
    x0, y0, x1, y1 = box
    left, right, top, bottom = x0 + radius, x1 - radius, y0 + radius, y1 - radius
    cx = min(max(x, left), right)
    cy = min(max(y, top), bottom)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= radius * radius


def _inside_triangle(x: float, y: float, points) -> bool:
    (ax, ay), (bx, by), (cx, cy) = points

    def side(px, py, qx, qy):
        return (qx - px) * (y - py) - (qy - py) * (x - px)

    d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
    has_negative = d1 < 0 or d2 < 0 or d3 < 0
    has_positive = d1 > 0 or d2 > 0 or d3 > 0
    return not (has_negative and has_positive)


def _inside_bubble(x: float, y: float) -> bool:
    return (_inside_rounded_rect(x, y, BUBBLE, BUBBLE_RADIUS)
            or _inside_triangle(x, y, TAIL))


def _distance_to_segment(x: float, y: float, start, end) -> float:
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    if length == 0:
        return ((x - ax) ** 2 + (y - ay) ** 2) ** 0.5
    t = ((x - ax) * dx + (y - ay) * dy) / length
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    px, py = ax + t * dx, ay + t * dy
    return ((x - px) ** 2 + (y - py) ** 2) ** 0.5


def _inside_letter_e(x: float, y: float) -> bool:
    """Буква «E»: вертикальная стойка и три горизонтальных штриха."""
    if E_X <= x <= E_X + E_BAR and LETTER_TOP <= y <= LETTER_BOTTOM:
        return True
    bars = ((LETTER_TOP, E_TOP_WIDTH), ((LETTER_TOP + LETTER_BOTTOM) / 2 - STROKE / 2, E_MID_WIDTH),
            (LETTER_BOTTOM - STROKE, E_TOP_WIDTH))
    for top, width in bars:
        if E_X <= x <= E_X + width and top <= y <= top + STROKE:
            return True
    return False


def _inside_letter_n(x: float, y: float) -> bool:
    """Буква «N»: две стойки и диагональ между ними."""
    if LETTER_TOP <= y <= LETTER_BOTTOM:
        if N_LEFT_X <= x <= N_LEFT_X + N_WIDTH or N_RIGHT_X <= x <= N_RIGHT_X + N_WIDTH:
            return True
    diagonal = _distance_to_segment(x, y, (N_LEFT_X + N_WIDTH / 2, LETTER_TOP),
                                    (N_RIGHT_X + N_WIDTH / 2, LETTER_BOTTOM))
    return diagonal <= STROKE / 2


def _background(x: float, y: float):
    """Диагональный бирюзовый градиент."""
    t = (x + y) / (2.0 * SIZE)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return tuple(round(GRADIENT_FROM[i] + (GRADIENT_TO[i] - GRADIENT_FROM[i]) * t)
                 for i in range(3))


def _to_art_space(variant: str, size: int, column: int, row: int):
    """Пиксель результата → координаты арт-системы 192 × 192 (или None вне)."""
    if variant == "foreground":
        # canvas 108 dp: облако без фона, вписанное в безопасную зону
        scale = size / FOREGROUND_SIZE
        x = (column + 0.5) * scale
        y = (row + 0.5) * scale
        return ((x - FOREGROUND_OFFSET[0]) / FOREGROUND_SCALE,
                (y - FOREGROUND_OFFSET[1]) / FOREGROUND_SCALE)
    scale = SIZE / size
    return ((column + 0.5) * scale, (row + 0.5) * scale)


def render(size: int = SIZE, variant: str = "full") -> list[list[tuple[int, int, int, int]]]:
    """Нарисовать иконку: список строк пикселей RGBA (сверху вниз).

    ``variant``: ``full`` — квадрат со скруглением и градиентом, ``round`` — круг,
    ``foreground`` — только облако с «EN» на прозрачном фоне (слой лаунчера).
    """
    if variant not in ("full", "round", "foreground"):
        raise ValueError(f"неизвестный вид иконки: {variant}")
    samples = SUPERSAMPLE * SUPERSAMPLE
    rows = []
    for row in range(size):
        pixels = []
        for column in range(size):
            red = green = blue = alpha = 0.0
            for sy in range(SUPERSAMPLE):
                for sx in range(SUPERSAMPLE):
                    if variant == "foreground":
                        scale = size / FOREGROUND_SIZE
                        x = (column + (sx + 0.5) / SUPERSAMPLE) * scale
                        y = (row + (sy + 0.5) / SUPERSAMPLE) * scale
                        ax = (x - FOREGROUND_OFFSET[0]) / FOREGROUND_SCALE
                        ay = (y - FOREGROUND_OFFSET[1]) / FOREGROUND_SCALE
                        if not _inside_bubble(ax, ay):
                            continue
                        r, g, b = BUBBLE_COLOR
                        if _inside_letter_e(ax, ay) or _inside_letter_n(ax, ay):
                            r, g, b = LETTER_COLOR
                        red += r
                        green += g
                        blue += b
                        alpha += 255.0
                        continue
                    scale = SIZE / size
                    x = (column + (sx + 0.5) / SUPERSAMPLE) * scale
                    y = (row + (sy + 0.5) / SUPERSAMPLE) * scale
                    if variant == "round":
                        if not _inside_circle(x, y):
                            continue
                    elif not _inside_rounded_square(x, y):
                        continue  # за скруглением — прозрачность
                    r, g, b = _background(x, y)
                    if _inside_bubble(x, y):
                        r, g, b = BUBBLE_COLOR
                        if _inside_letter_e(x, y) or _inside_letter_n(x, y):
                            r, g, b = LETTER_COLOR
                    red += r
                    green += g
                    blue += b
                    alpha += 255.0
            if alpha == 0:
                pixels.append((0, 0, 0, 0))
                continue
            coverage = alpha / (samples * 255.0)
            scale_to_alpha = alpha / 255.0
            pixels.append((round(red / scale_to_alpha), round(green / scale_to_alpha),
                           round(blue / scale_to_alpha), round(255.0 * coverage)))
        rows.append(pixels)
    return rows


def encode_png(rows, size: int = SIZE) -> bytes:
    """PNG без внешних библиотек: RGBA, фильтр 0 в каждой строке."""
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for pixel in row:
            raw.extend(pixel)

    def chunk(name: bytes, payload: bytes) -> bytes:
        body = name + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def decode_png(data: bytes) -> tuple[int, list[list[tuple[int, int, int, int]]]]:
    """Прочитать RGBA-PNG (нужно для ``--check``: сравниваются пиксели)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("это не PNG")
    position, chunks, header = 8, {}, None
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        name = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        chunks.setdefault(name, b"")
        chunks[name] += payload
        if name == b"IHDR":
            header = struct.unpack(">IIBBBBB", payload)
        position += 12 + length
    if header is None:
        raise ValueError("нет IHDR")
    width, height, depth, color_type = header[0], header[1], header[2], header[3]
    if depth != 8 or color_type != 6:
        raise ValueError(f"ожидается RGBA 8 бит, а тут depth={depth} color_type={color_type}")
    raw = zlib.decompress(chunks[b"IDAT"])
    stride = width * 4
    rows, previous, position = [], bytearray(stride), 0
    for _ in range(height):
        filter_type = raw[position]
        line = bytearray(raw[position + 1:position + 1 + stride])
        position += 1 + stride
        for index in range(stride):
            left = line[index - 4] if index >= 4 else 0
            up = previous[index]
            up_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 1:
                line[index] = (line[index] + left) & 0xFF
            elif filter_type == 2:
                line[index] = (line[index] + up) & 0xFF
            elif filter_type == 3:
                line[index] = (line[index] + (left + up) // 2) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                predictor = left if (pa <= pb and pa <= pc) else (up if pb <= pc else up_left)
                line[index] = (line[index] + predictor) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"неизвестный фильтр PNG: {filter_type}")
        rows.append([tuple(line[i:i + 4]) for i in range(0, stride, 4)])
        previous = line
    return width, rows


def android_targets(res: pathlib.Path = ANDROID_RES) -> list[tuple[pathlib.Path, int, str]]:
    """Список файлов Android-иконок: путь, размер в пикселях и вид."""
    targets = []
    for folder, factor in DENSITIES:
        base = round(LAUNCHER_BASE * factor)
        directory = res / f"mipmap-{folder}"
        targets.append((directory / "ic_launcher.png", base, "full"))
        targets.append((directory / "ic_launcher_round.png", base, "round"))
        targets.append((directory / "ic_launcher_foreground.png",
                        round(FOREGROUND_SIZE * factor), "foreground"))
    return targets


def draw_android(res: pathlib.Path = ANDROID_RES) -> list[pathlib.Path]:
    """Нарисовать все растровые иконки Android и векторный фон адаптивной."""
    written = []
    for path, size, variant in android_targets(res):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode_png(render(size, variant), size))
        written.append(path)
    background = res / "drawable" / "ic_launcher_background.xml"
    background.parent.mkdir(parents=True, exist_ok=True)
    background.write_text(BACKGROUND_XML, encoding="utf-8")
    written.append(background)
    return written


def check_android(res: pathlib.Path = ANDROID_RES) -> list[str]:
    """Проблемы растровых иконок Android (пустой список — всё совпадает)."""
    problems = []
    for path, size, variant in android_targets(res):
        if not path.exists():
            problems.append(f"нет файла: {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
            continue
        try:
            width, stored = decode_png(path.read_bytes())
        except ValueError as error:
            problems.append(f"{path.name} (mipmap-{path.parent.name[7:]}): {error}")
            continue
        if width != size or stored != render(size, variant):
            problems.append(f"{path.name} ({size}×{size}, {variant}) не совпадает с генератором")
    background = res / "drawable" / "ic_launcher_background.xml"
    if not background.exists():
        problems.append("нет drawable/ic_launcher_background.xml")
    elif background.read_text(encoding="utf-8") != BACKGROUND_XML:
        problems.append("drawable/ic_launcher_background.xml расходится с генератором")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--size", type=int, default=SIZE,
                        help="нарисовать предпросмотр другого размера (например, 48)")
    parser.add_argument("--variant", choices=("full", "round", "foreground"), default="full",
                        help="вид иконки (foreground — слой адаптивной иконки Android)")
    parser.add_argument("--android", action="store_true",
                        help="перерисовать иконки Android (mipmap-*/ + фон адаптивной)")
    parser.add_argument("--check", action="store_true",
                        help="сравнить файлы с генератором и ничего не писать")
    args = parser.parse_args()

    if args.check:
        problems = []
        if not args.out.exists():
            problems.append(f"нет иконки: {args.out}")
        else:
            try:
                width, stored = decode_png(args.out.read_bytes())
                if width != SIZE or stored != render(SIZE, "full"):
                    problems.append(f"{args.out.name} не совпадает с генератором")
            except ValueError as error:
                problems.append(f"{args.out.name}: {error}")
        problems.extend(check_android())
        if problems:
            for problem in problems:
                print(f"::error::{problem}", file=sys.stderr)
            print("перерисуйте: python3 english/tools/make_icon.py --android", file=sys.stderr)
            return 1
        print("✓ иконка и её копии для Android совпадают с генератором: "
              "облако + «EN», градиент #3DC9A6→#116E7A")
        return 0

    if args.android:
        written = draw_android()
        print(f"✓ иконок Android нарисовано: {len(written)} "
              f"(mipmap-mdpi…xxxhdpi + фон адаптивной)")
        if args.size == SIZE and args.variant == "full":
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_bytes(encode_png(render()))
            print(f"✓ иконка приложения: {args.out} ({args.out.stat().st_size} байт, {SIZE}×{SIZE})")
        return 0

    rows = render(args.size, args.variant)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(encode_png(rows, args.size))
    print(f"✓ иконка нарисована: {args.out} ({args.out.stat().st_size} байт, "
          f"{args.size}×{args.size}, {args.variant})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
