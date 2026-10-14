#!/usr/bin/env python3
"""Иконка приложения по физике: атом (ядро + три орбиты).

Иконка рисуется кодом, а не хранится «как попало»: тот же рисунок, что лежит в
``webapp/icon.svg`` и в Android-векторах ``ic_launcher_foreground.xml`` /
``ic_launcher_background.xml``. PNG нужен для favicon и ``apple-touch-icon``
(их отдаёт и Windows-версия), а Android рисует вектор — поэтому важно, чтобы
оба варианта совпадали по геометрии и цветам.

Почему не «просто картинка»: иконка обязана оставаться резкой на 48 px в
лаунчере и на 192 px в браузере, а цвета — совпадать с оформлением приложения
(``webapp/styles.css`` → ``--brand``). Поэтому растр строится из тех же
констант, что и векторы, с трёхкратным сглаживанием.

Использование::

    python3 tools/make_icon.py            # перерисовать webapp/icon.png
    python3 tools/make_icon.py --check    # сверить PNG с генератором (CI)
"""

from __future__ import annotations

import argparse
import pathlib
import struct
import sys
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "webapp" / "icon.png"

# --- геометрия (192 × 192; те же числа заданы в webapp/icon.svg) ----------- #
SIZE = 192
RADIUS = 42          # скругление квадрата
CENTER = (96.0, 96.0)
ORBIT_A = 56.0       # большая полуось орбиты
ORBIT_B = 21.0       # малая полуось
ORBIT_ANGLES = (0.0, 60.0, -60.0)
ORBIT_WIDTH = 6.5    # толщина линии орбиты
NUCLEUS_R = 11.5     # радиус ядра

# --- палитра (та же, что в webapp/styles.css и android/.../colors.xml) ----- #
GRADIENT_FROM = (0x4A, 0x7C, 0xE8)
GRADIENT_TO = (0x21, 0x3F, 0x9C)
ORBIT_COLOR = (0xFF, 0xFF, 0xFF)
NUCLEUS_COLOR = (0xFF, 0xD1, 0x66)
SUPERSAMPLE = 3


def _rotated(point, angle):
    """Точка в системе координат повёрнутой орбиты."""
    x, y = point[0] - CENTER[0], point[1] - CENTER[1]
    radians = angle * 3.141592653589793 / 180.0
    cos, sin = _cos(radians), _sin(radians)
    return x * cos + y * sin, -x * sin + y * cos


def _cos(value: float) -> float:
    return _trig(value)[0]


def _sin(value: float) -> float:
    return _trig(value)[1]


def _trig(value: float):
    """sin/cos без импорта math (точности float достаточно)."""
    import math
    return math.cos(value), math.sin(value)


def _inside_rounded_square(x: float, y: float) -> bool:
    left, right = RADIUS, SIZE - RADIUS
    cx = min(max(x, left), right)
    cy = min(max(y, left), right)
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= RADIUS * RADIUS


def _orbit_distance(x: float, y: float) -> float:
    """Расстояние до ближайшей орбиты (первая поправка метода уровней)."""
    best = float("inf")
    for angle in ORBIT_ANGLES:
        u, v = _rotated((x, y), angle)
        radius = ((u / ORBIT_A) ** 2 + (v / ORBIT_B) ** 2) ** 0.5
        gradient = ((u / ORBIT_A**2) ** 2 + (v / ORBIT_B**2) ** 2) ** 0.5
        if gradient == 0:
            continue
        best = min(best, abs(radius - 1.0) / gradient)
    return best


def _nucleus_distance(x: float, y: float) -> float:
    return ((x - CENTER[0]) ** 2 + (y - CENTER[1]) ** 2) ** 0.5 - NUCLEUS_R


def _background(x: float, y: float):
    """Диагональный градиент: цвет пикселя внутри квадрата."""
    t = (x + y) / (2.0 * SIZE)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return tuple(round(GRADIENT_FROM[i] + (GRADIENT_TO[i] - GRADIENT_FROM[i]) * t) for i in range(3))


def render() -> list[list[tuple[int, int, int, int]]]:
    """Нарисовать иконку: список строк пикселей RGBA (сверху вниз)."""
    step = 1.0 / SUPERSAMPLE
    samples = SUPERSAMPLE * SUPERSAMPLE
    rows = []
    for row in range(SIZE):
        pixels = []
        for column in range(SIZE):
            red = green = blue = alpha = 0.0
            for sy in range(SUPERSAMPLE):
                for sx in range(SUPERSAMPLE):
                    x = column + (sx + 0.5) * step
                    y = row + (sy + 0.5) * step
                    if not _inside_rounded_square(x, y):
                        continue  # за скруглением — прозрачность
                    r, g, b = _background(x, y)
                    if _orbit_distance(x, y) <= ORBIT_WIDTH / 2.0:
                        r, g, b = ORBIT_COLOR
                    if _nucleus_distance(x, y) <= 0.0:
                        r, g, b = NUCLEUS_COLOR
                    red += r
                    green += g
                    blue += b
                    alpha += 255.0
            if alpha == 0:
                pixels.append((0, 0, 0, 0))
                continue
            # при прозрачных «дырках» внутри скругления цвет берём по покрытию
            coverage = alpha / (samples * 255.0)
            scale = alpha / 255.0
            pixels.append((round(red / scale), round(green / scale), round(blue / scale),
                           round(255.0 * coverage)))
        rows.append(pixels)
    return rows


def encode_png(rows) -> bytes:
    """PNG без внешних библиотек: RGBA, фильтр 0 в каждой строке."""
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for pixel in row:
            raw.extend(pixel)
    def chunk(name: bytes, payload: bytes) -> bytes:
        body = name + payload
        return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def decode_png(data: bytes) -> list[list[tuple[int, int, int, int]]]:
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
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT)
    parser.add_argument("--check", action="store_true",
                        help="сравнить существующий PNG с генератором и не писать файл")
    args = parser.parse_args()

    rows = render()
    if args.check:
        if not args.out.exists():
            print(f"::error::иконки нет: {args.out.relative_to(ROOT)}", file=sys.stderr)
            return 1
        try:
            stored = decode_png(args.out.read_bytes())
        except ValueError as error:
            print(f"::error::{args.out.name}: {error}; перерисуйте: python3 tools/make_icon.py",
                  file=sys.stderr)
            return 1
        if stored != rows:
            print(f"::error::{args.out.relative_to(ROOT)} не совпадает с генератором; "
                  f"перерисуйте: python3 tools/make_icon.py", file=sys.stderr)
            return 1
        print(f"✓ иконка совпадает с генератором: {args.out.relative_to(ROOT)} "
              f"({SIZE}×{SIZE}, {len(ORBIT_ANGLES)} орбиты, ядро {NUCLEUS_COLOR and '#FFD166'})")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(encode_png(rows))
    print(f"✓ иконка нарисована: {args.out.relative_to(ROOT)} "
          f"({args.out.stat().st_size} байт, {SIZE}×{SIZE})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
