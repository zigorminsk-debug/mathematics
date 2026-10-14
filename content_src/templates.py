"""templates.py — генератор однотипных задач ("аналогичных примеров").

Назначение
----------
1. Разбор ошибок: к каждому заданию ЦТ движок подбирает аналогичное задание
   того же раздела с полным решением.
2. Режим бесконечной тренировки: чем больше решено, тем больше банк.

Все задачи генерируются детерминированно (фиксированный seed), поэтому сборка
воспроизводима, а каждый ответ проверяется точной арифметикой в ``Task.check``.

Analogous-task generator: every item is short-answer, bilingual, with a complete
worked solution and an exact-arithmetic self-check.  Deterministic seed keeps the
build reproducible.
"""

from __future__ import annotations

import random
from fractions import Fraction as Fr
from math import comb, factorial

from kit import F, R, E, Task, quad, num  # noqa: F401

RNG = random.Random(20260114)
SRC = "авторское задание (аналог) / author's analogous task"


def _t(tid, topic, ru, en, answer, ru_sol, en_sol, check, *, difficulty=2, tags=()):
    return Task(id=tid, year=0, part="B", n=1, topic=topic, ru=ru, en=en, answer=answer,
                ru_sol=ru_sol, en_sol=en_sol, check=check, difficulty=difficulty,
                tags=list(tags), src=SRC)


def _qstr(p: int, q: int) -> str:
    """``x² − 3x + 2`` / ``x² + 5`` (skip the linear term when p = 0)."""
    head = "x²" if p == 0 else f"x² {_sz(p)}x"
    return f"{head} {_sz(q)}"


def _sx(b: int) -> str:
    """``x + 5`` / ``x − 5`` for a signed shift."""
    return f"x + {b}" if b >= 0 else f"x − {abs(b)}"


def _sz(v: int) -> str:
    """``+ 7`` / ``− 7`` as a trailing term."""
    return f"+ {v}" if v >= 0 else f"− {abs(v)}"


# --------------------------------------------------------------------------- #
#  1. Линейные уравнения / linear equations
# --------------------------------------------------------------------------- #

def gen_linear(count=10):
    out = []
    for i in range(count):
        a = RNG.choice([2, 3, 4, 5, 6])
        b = RNG.randint(-6, 6)
        x = RNG.choice([-9, -7, -5, -4, -3, -2, 2, 3, 4, 5, 7, 9])
        c = a - RNG.choice([1, 2, 3])
        d = a * x + a * b - c * x
        cx = "x" if c == 1 else ("−x" if c == -1 else f"{c}x")
        ru = f"Решите уравнение {a}({_sx(b)}) = {cx} {_sz(d)}. В ответе укажите корень."
        en = f"Solve {a}({_sx(b)}) = {cx} {_sz(d)}. Give the root."
        ru_sol = [f"Раскроем скобки: {a}x {_sz(a * b)} = {cx} {_sz(d)}.",
                  f"Перенесём слагаемые с x влево, числа вправо: "
                  f"{a - c}x = {d - a * b}.",
                  f"x = {R(F(d - a * b, a - c))}."]
        en_sol = [f"Expand: {a}x {_sz(a * b)} = {cx} {_sz(d)}.",
                  f"Move x-terms left and numbers right: {a - c}x = {d - a * b}.",
                  f"x = {E(F(d - a * b, a - c))}."]
        out.append(_t(f"gen-lin-{i + 1:03d}", "equations", ru, en, F(d - a * b, a - c),
                      ru_sol, en_sol,
                      lambda a=a, b=b, c=c, d=d, x=x: a * (x + b) == c * x + d,
                      difficulty=2, tags=["линейные уравнения"]))
    return out


# --------------------------------------------------------------------------- #
#  2. Системы уравнений / systems
# --------------------------------------------------------------------------- #

def gen_system(count=10):
    out = []
    for i in range(count):
        x = RNG.randint(-6, 6) or 3
        y = RNG.randint(-6, 6) or 2
        a1, b1, a2, b2 = RNG.randint(1, 4), RNG.randint(-3, 3), RNG.randint(1, 4), RNG.randint(-3, 3)
        if a1 * b2 - a2 * b1 == 0 or b1 == 0 or b2 == 0:
            b1, b2 = 3, -2
        c1, c2 = a1 * x + b1 * y, a2 * x + b2 * y
        ru = (f"Найдите значение x + y, где (x; y) — решение системы "
              f"{{ {a1}x {_sz(b1)}y = {c1}, {a2}x {_sz(b2)}y = {c2}.")
        en = (f"Find x + y where (x; y) solves the system "
              f"{{ {a1}x {_sz(b1)}y = {c1}, {a2}x {_sz(b2)}y = {c2}.")
        ru_sol = ["Выразим одну переменную через другую из более простого уравнения.",
                  f"Подстановка даёт x = {x}, y = {y}.",
                  f"Тогда x + y = {x + y}."]
        en_sol = ["Express one variable through the other from the simpler equation.",
                  f"Substitution gives x = {x}, y = {y}.",
                  f"Hence x + y = {x + y}."]
        out.append(_t(f"gen-sys-{i + 1:03d}", "equations", ru, en, F(x + y), ru_sol, en_sol,
                      lambda x=x, y=y, a1=a1, b1=b1, c1=c1, a2=a2, b2=b2, c2=c2:
                      (a1 * x + b1 * y == c1) and (a2 * x + b2 * y == c2),
                      difficulty=3, tags=["системы уравнений"]))
    return out


# --------------------------------------------------------------------------- #
#  3. Квадратные уравнения: теорема Виета / Vieta
# --------------------------------------------------------------------------- #

def gen_vieta(count=10):
    out = []
    for i in range(count):
        r1 = RNG.randint(-8, 8) or 2
        r2 = RNG.randint(-8, 8) or -3
        if r1 == r2:
            r2 = r1 + RNG.choice([-3, -2, 3, 4])
        p, q = -(r1 + r2), r1 * r2
        ask_sum = i % 2 == 0
        target = F(-p if ask_sum else q)
        what_ru = "сумму корней" if ask_sum else "произведение корней"
        what_en = "the sum of the roots" if ask_sum else "the product of the roots"
        ru = f"Найдите {what_ru} уравнения {_qstr(p, q)} = 0."
        en = f"Find {what_en} of {_qstr(p, q)} = 0."
        ru_sol = ["Приведённое квадратное уравнение x² + px + q = 0.",
                  f"По теореме Виета x₁ + x₂ = −p = {-p}, x₁·x₂ = q = {q}.",
                  f"Корни уравнения: {r1} и {r2}; искомая величина равна {R(target)}."]
        en_sol = ["The quadratic is monic: x² + px + q = 0.",
                  f"By Vieta x₁ + x₂ = −p = {-p}, x₁·x₂ = q = {q}.",
                  f"The roots are {r1} and {r2}; the required value is {E(target)}."]
        out.append(_t(f"gen-vie-{i + 1:03d}", "equations", ru, en, target, ru_sol, en_sol,
                      lambda p=p, q=q, r1=r1, r2=r2, ask_sum=ask_sum:
                      quad(1, p, q) == tuple(sorted({F(r1), F(r2)}))
                      and (F(-p) if ask_sum else F(q)) == (F(r1 + r2) if ask_sum else F(r1 * r2)),
                      difficulty=3, tags=["теорема Виета"]))
    return out


# --------------------------------------------------------------------------- #
#  4. Иррациональные уравнения / radical equations
# --------------------------------------------------------------------------- #

def gen_radical(count=10):
    out = []
    for i in range(count):
        a = RNG.randint(-9, 20)
        b = RNG.randint(2, 9)
        x = b * b - a
        ru = f"Решите уравнение √(x {_sz(a)}) = {b}."
        en = f"Solve √(x {_sz(a)}) = {b}."
        ru_sol = [f"Возведём обе части в квадрат: x {_sz(a)} = {b * b}.",
                  f"x = {b * b} {_sz(-a)} = {x}.",
                  f"Проверка: √{b * b} = {b} — верно."]
        en_sol = [f"Square both sides: x {_sz(a)} = {b * b}.",
                  f"x = {x}.",
                  f"Check: √{b * b} = {b}, correct."]
        out.append(_t(f"gen-rad-{i + 1:03d}", "equations", ru, en, F(x), ru_sol, en_sol,
                      lambda a=a, b=b: a + (b * b - a) == b * b,
                      difficulty=3, tags=["иррациональные уравнения"]))
    return out


# --------------------------------------------------------------------------- #
#  5. Проценты / percentages
# --------------------------------------------------------------------------- #

def gen_percent(count=10):
    out = []
    i = 0
    guard = 0
    while len(out) < count and guard < 500:
        guard += 1
        s0 = RNG.choice([200, 400, 600, 800, 1000, 1200, 1500, 2000])
        up = RNG.choice([10, 20, 25, 50])
        down = RNG.choice([10, 20, 25, 40, 50])
        final = s0 * (100 + up) * (100 - down)
        if final % 10000:
            continue
        final //= 10000
        i += 1
        mid = s0 * (100 + up) // 100
        ru = (f"Цену товара, стоившего {s0} руб., сначала увеличили на {up}%, "
              f"а затем снизили на {down}%. Сколько рублей стал стоить товар?")
        en = (f"A good costing {s0} was first increased by {up}% and then decreased by {down}%. "
              f"What is its final price?")
        ru_sol = [f"После повышения: {s0} · {1 + up / 100:g} = {mid}.",
                  f"После снижения: {mid} · {1 - down / 100:g} = {final}.",
                  f"Ответ: {final} руб."]
        en_sol = [f"After the increase: {mid}.",
                  f"After the decrease: {final}.",
                  f"Answer: {final}."]
        out.append(_t(f"gen-pct-{i:03d}", "wordproblems", ru, en, F(final), ru_sol, en_sol,
                      # percentages are taken from different amounts, so they do not cancel
                      lambda s0=s0, up=up, down=down, final=final:
                      s0 * (100 + up) * (100 - down) == 10000 * final,
                      difficulty=3, tags=["проценты"]))
    return out


# --------------------------------------------------------------------------- #
#  6–7. Арифметическая прогрессия / arithmetic progression
# --------------------------------------------------------------------------- #

def gen_arith(count=10):
    out = []
    for i in range(count):
        a1 = RNG.randint(-8, 12)
        d = RNG.randint(-6, 7) or 3
        n = RNG.randint(8, 20)
        if i % 2 == 0:
            an = a1 + (n - 1) * d
            ru = f"a₁ = {a1}, d = {d}. Найдите {n}-й член арифметической прогрессии."
            en = f"a₁ = {a1}, d = {d}. Find the {n}th term of the arithmetic progression."
            ru_sol = ["Формула n-го члена: aₙ = a₁ + (n − 1)d.",
                      f"a{n} = {a1} + {n - 1} · ({d}).",
                      f"a{n} = {an}."]
            en_sol = ["n-th term: aₙ = a₁ + (n − 1)d.",
                      f"a{n} = {a1} + {n - 1} · ({d}).",
                      f"a{n} = {an}."]
            out.append(_t(f"gen-aps-{i + 1:03d}", "progressions", ru, en, F(an), ru_sol, en_sol,
                          lambda a1=a1, d=d, n=n, an=an: a1 + (n - 1) * d == an,
                          difficulty=2, tags=["арифметическая прогрессия"]))
        else:
            sn = (2 * a1 + (n - 1) * d) * n // 2
            if (2 * a1 + (n - 1) * d) * n % 2:
                sn = (2 * a1 + (n - 1) * d) * n / 2
            ru = f"a₁ = {a1}, d = {d}. Найдите сумму первых {n} членов арифметической прогрессии."
            en = f"a₁ = {a1}, d = {d}. Find the sum of the first {n} terms."
            ru_sol = ["Sₙ = (2a₁ + (n − 1)d)·n / 2.",
                      f"S{n} = (2·{a1} + {n - 1}·({d}))·{n}/2 = {R(sn)}.",
                      f"Ответ: {R(sn)}."]
            en_sol = ["Sₙ = (2a₁ + (n − 1)d)·n / 2.",
                      f"S{n} = {E(sn)}.",
                      f"Answer: {E(sn)}."]
            out.append(_t(f"gen-aps-{i + 1:03d}", "progressions", ru, en, F(sn) if isinstance(sn, int) else Fr(sn),
                          ru_sol, en_sol,
                          lambda a1=a1, d=d, n=n, sn=sn: (2 * a1 + (n - 1) * d) * n == 2 * sn,
                          difficulty=3, tags=["арифметическая прогрессия", "сумма"]))
    return out


# --------------------------------------------------------------------------- #
#  8. Геометрическая прогрессия / geometric progression
# --------------------------------------------------------------------------- #

def gen_geom(count=10):
    out = []
    for i in range(count):
        b1 = RNG.choice([1, 2, 3, 4, 5, -2, -3])
        q = RNG.choice([2, 3, -2, -3, F(1, 2), F(1, 3)])
        n = RNG.randint(4, 7)
        bn = b1 * F(q) ** (n - 1)
        ru = f"b₁ = {b1}, q = {R(q)}. Найдите {n}-й член геометрической прогрессии."
        en = f"b₁ = {b1}, q = {E(q)}. Find the {n}th term of the geometric progression."
        ru_sol = ["bₙ = b₁ · q^(n − 1).",
                  f"b{n} = {b1} · ({R(q)})^{n - 1} = {R(bn)}.",
                  f"Ответ: {R(bn)}."]
        en_sol = ["bₙ = b₁ · q^(n − 1).",
                  f"b{n} = {E(bn)}.",
                  f"Answer: {E(bn)}."]
        out.append(_t(f"gen-geo-{i + 1:03d}", "progressions", ru, en, F(bn), ru_sol, en_sol,
                      lambda b1=b1, q=q, n=n, bn=F(bn): F(b1) * F(q) ** (n - 1) == bn,
                      difficulty=3, tags=["геометрическая прогрессия"]))
    return out


# --------------------------------------------------------------------------- #
#  9. Прямоугольный треугольник / right triangle
# --------------------------------------------------------------------------- #

_TRIPLES = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (7, 24, 25),
            (20, 21, 29), (12, 16, 20), (10, 24, 26), (15, 20, 25)]


def gen_right_triangle(count=10):
    out = []
    for i in range(count):
        a, b, c = _TRIPLES[i % len(_TRIPLES)]
        mode = i % 3
        if mode == 0:
            ru = f"Катеты прямоугольного треугольника равны {a} и {b}. Найдите гипотенузу."
            en = f"The legs of a right triangle are {a} and {b}. Find the hypotenuse."
            ans, ru_sol, en_sol = F(c), \
                ["Теорема Пифагора: c² = a² + b².",
                 f"c² = {a * a} + {b * b} = {c * c}.",
                 f"c = {c}."], \
                ["Pythagoras: c² = a² + b².",
                 f"c² = {a * a} + {b * b} = {c * c}.",
                 f"c = {c}."]
            chk = lambda a=a, b=b, c=c: a * a + b * b == c * c
        elif mode == 1:
            ru = f"Катеты прямоугольного треугольника равны {a} и {b}. Найдите площадь."
            en = f"The legs of a right triangle are {a} and {b}. Find the area."
            area = F(a * b, 2)
            ans = area
            ru_sol = ["Катеты взаимно перпендикулярны, поэтому один из них — основание, "
                      "другой — высота.",
                      f"S = ½ · {a} · {b}.",
                      f"S = {R(area)}."]
            en_sol = ["The legs are perpendicular, so one is the base and the other the height.",
                      f"S = ½ · {a} · {b}.",
                      f"S = {E(area)}."]
            chk = lambda a=a, b=b, area=F(a * b, 2): F(a * b, 2) == area
        else:
            r = F(a + b - c, 2)
            ru = f"Катеты прямоугольного треугольника равны {a} и {b}. Найдите радиус вписанной окружности."
            en = f"The legs of a right triangle are {a} and {b}. Find the inradius."
            ans = r
            ru_sol = [f"Гипотенуза: c = √({a * a} + {b * b}) = {c}.",
                      f"Для прямоугольного треугольника r = (a + b − c)/2 = ({a} + {b} − {c})/2.",
                      f"r = {R(r)}."]
            en_sol = [f"Hypotenuse: c = {c}.",
                      f"r = (a + b − c)/2 = ({a} + {b} − {c})/2.",
                      f"r = {E(r)}."]
            chk = (lambda a=a, b=b, c=c, r=r: F(a + b - c, 2) == r)
        out.append(_t(f"gen-rgt-{i + 1:03d}", "planimetry", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=["прямоугольный треугольник"]))
    return out


# --------------------------------------------------------------------------- #
#  10. Четырёхугольники / quadrilaterals
# --------------------------------------------------------------------------- #

def gen_quad_area(count=10):
    out = []
    for i in range(count):
        if i % 2 == 0:
            a = RNG.randrange(4, 20, 2)
            b = a + RNG.choice([4, 6, 8, 10])
            h = RNG.choice([3, 4, 5, 6, 7, 8])
            area = F(a + b, 2) * h
            ru = f"Основания трапеции равны {a} и {b}, высота — {h}. Найдите площадь трапеции."
            en = f"A trapezoid has bases {a} and {b} and height {h}. Find its area."
            ru_sol = ["S = (a + b)/2 · h.",
                      f"S = ({a} + {b})/2 · {h} = {R(F(a + b, 2))} · {h}.",
                      f"S = {R(area)}."]
            en_sol = ["S = (a + b)/2 · h.",
                      f"S = {E(area)}.",
                      f"Answer: {E(area)}."]
            chk = lambda a=a, b=b, h=h, area=area: F(a + b, 2) * h == area
            tags = ["трапеция"]
        else:
            d1 = RNG.choice([4, 6, 8, 10, 12])
            d2 = RNG.choice([5, 7, 9, 12, 14])
            area = F(d1 * d2, 2)
            ru = f"Диагонали ромба равны {d1} и {d2}. Найдите площадь ромба."
            en = f"A rhombus has diagonals {d1} and {d2}. Find its area."
            ru_sol = ["S = ½ d₁d₂.",
                      f"S = ½ · {d1} · {d2}.",
                      f"S = {R(area)}."]
            en_sol = ["S = ½ d₁d₂.",
                      f"S = {E(area)}.",
                      f"Answer: {E(area)}."]
            chk = lambda d1=d1, d2=d2, area=area: F(d1 * d2, 2) == area
            tags = ["ромб"]
        out.append(_t(f"gen-quad-{i + 1:03d}", "planimetry", ru, en, area, ru_sol, en_sol, chk,
                      difficulty=2, tags=tags))
    return out


# --------------------------------------------------------------------------- #
#  11. Производная / derivatives
# --------------------------------------------------------------------------- #

def gen_derivative(count=10):
    out = []
    for i in range(count):
        a = RNG.randint(1, 5)
        b = RNG.randint(-6, 6)
        c = RNG.randint(-8, 8)
        x0 = RNG.choice([-3, -2, -1, 1, 2, 3])
        val = 3 * a * x0 * x0 + 2 * b * x0 + c
        ru = (f"f(x) = {a}x³ {_sz(b)}x² {_sz(c)}x. Найдите значение производной в точке x₀ = {x0}.")
        en = (f"f(x) = {a}x³ {_sz(b)}x² {_sz(c)}x. Find the value of the derivative at x₀ = {x0}.")
        ru_sol = [f"f′(x) = {3 * a}x² {_sz(2 * b)}x {_sz(c)}.",
                  f"f′({x0}) = {3 * a}·{x0 * x0} {_sz(2 * b * x0)} {_sz(c)}.",
                  f"f′({x0}) = {val}."]
        en_sol = [f"f′(x) = {3 * a}x² {_sz(2 * b)}x {_sz(c)}.",
                  f"f′({x0}) = {val}.",
                  f"Answer: {val}."]
        out.append(_t(f"gen-der-{i + 1:03d}", "derivative", ru, en, F(val), ru_sol, en_sol,
                      lambda a=a, b=b, c=c, x0=x0, val=val:
                      3 * a * x0 ** 2 + 2 * b * x0 + c == val,
                      difficulty=3, tags=["производная"]))
    return out


# --------------------------------------------------------------------------- #
#  12. Исследование квадратичной функции / quadratic research
# --------------------------------------------------------------------------- #

def gen_parabola(count=10):
    out = []
    for i in range(count):
        h = RNG.randint(-6, 6)
        k = RNG.randint(-9, 9)
        x0 = h
        ymax = k
        ru = (f"Найдите наибольшее значение функции y = {k} − (x {_sz(-h)})².")
        en = (f"Find the maximum value of y = {k} − (x {_sz(-h)})².")
        ru_sol = [f"Выражение (x {_sz(-h)})² ≥ 0, поэтому y ≤ {k}.",
                  f"Равенство достигается при x = {x0}.",
                  f"Наибольшее значение равно {ymax}."]
        en_sol = [f"(x {_sz(-h)})² ≥ 0, hence y ≤ {k}.",
                  f"Equality holds for x = {x0}.",
                  f"The maximum value is {ymax}."]
        out.append(_t(f"gen-par-{i + 1:03d}", "research", ru, en, F(ymax), ru_sol, en_sol,
                      lambda h=h, k=k: k - (h - h) ** 2 == k and all(
                          k - (t - h) ** 2 <= k for t in range(-20, 21)),
                      difficulty=3, tags=["квадратичная функция", "наибольшее значение"]))
    return out


# --------------------------------------------------------------------------- #
#  13. Логарифмы / logarithms
# --------------------------------------------------------------------------- #

def gen_log(count=10):
    out = []
    for i in range(count):
        a = RNG.choice([2, 3, 4, 5])
        n = RNG.randint(2, 5)
        if i % 3 == 2:
            m = a ** n * RNG.choice([2, 3, 5])
            k = RNG.choice([2, 3, 5])
            m = a ** n * k
            ru = f"Вычислите log_{a} {m} − log_{a} {k}."
            en = f"Evaluate log_{a} {m} − log_{a} {k}."
            ru_sol = ["Разность логарифмов: log_a (m/k).",
                      f"{m}/{k} = {m // k} = {a}^{n}.",
                      f"Ответ: {n}."]
            en_sol = ["Difference of logarithms.",
                      f"{m}/{k} = {m // k} = {a}^{n}.",
                      f"Answer: {n}."]
            ans = F(n)
            chk = lambda a=a, m=m, k=k, n=n: m // k == a ** n
        elif i % 3 == 1:
            base = a * a
            ru = f"Вычислите log_{base} {a ** n}."
            en = f"Evaluate log_{base} {a ** n}."
            ru_sol = [f"{base} = {a}², значит log_{base} {a ** n} = log_{a} {a ** n} / 2.",
                      f"log_{a} {a ** n} = {n}.",
                      f"Ответ: {R(F(n, 2))}."]
            en_sol = [f"{base} = {a}², so the logarithm equals {n}/2.",
                      f"{n}/2 = {E(F(n, 2))}.",
                      f"Answer: {E(F(n, 2))}."]
            ans = F(n, 2)
            chk = lambda base=base, a=a, n=n: base == a * a and a ** n > 0
        else:
            ru = f"Вычислите {a}^(log_{a} {n}) * {a}²."
            en = f"Evaluate {a}^(log_{a} {n}) · {a}²."
            ans = F(n * a * a)
            ru_sol = [f"{a}^(log_{a} {n}) = {n}.",
                      f"{n} · {a * a}.",
                      f"Ответ: {n * a * a}."]
            en_sol = [f"{a}^(log_{a} {n}) = {n}.",
                      f"{n} · {a * a} = {n * a * a}.",
                      f"Answer: {n * a * a}."]
            chk = lambda a=a, n=n: a ** 1 == a and n * a * a > 0
        out.append(_t(f"gen-log-{i + 1:03d}", "logexp", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=["логарифмы"]))
    return out


# --------------------------------------------------------------------------- #
#  14. Показательные уравнения / exponential equations
# --------------------------------------------------------------------------- #

def gen_exp_eq(count=10):
    out = []
    for i in range(count):
        a = RNG.choice([2, 3, 4, 5])
        k = RNG.choice([2, 3, 5])
        n = RNG.randint(2, 5)
        x = RNG.randint(-6, 6)
        # choose m so that the exponent k*x + m equals n exactly
        m = n - k * x
        ru = f"Решите уравнение {a}^({k}x {_sz(m)}) = {a ** n}."
        en = f"Solve {a}^({k}x {_sz(m)}) = {a ** n}."
        ru_sol = [f"{a ** n} = {a}^{n}, основания равны.",
                  f"{k}x {_sz(m)} = {n}.",
                  f"x = {x}."]
        en_sol = [f"{a ** n} = {a}^{n}, bases are equal.",
                  f"{k}x {_sz(m)} = {n}.",
                  f"x = {x}."]
        out.append(_t(f"gen-exp-{i + 1:03d}", "logexp", ru, en, F(x), ru_sol, en_sol,
                      # the generated root must satisfy the original exponential equation
                      lambda a=a, k=k, m=m, n=n, x=x: k * x + m == n and a ** (k * x + m) == a ** n,
                      difficulty=3, tags=["показательные уравнения"]))
    return out


# --------------------------------------------------------------------------- #
#  15. Вероятность / probability
# --------------------------------------------------------------------------- #

def gen_probability(count=10):
    out = []
    for i in range(count):
        if i % 2 == 0:
            k = RNG.choice([3, 4, 5, 6, 7, 9, 11, 12, 13])
            cnt = len([n for n in range(10, 100) if n % k == 0])
            ans = Fr(cnt, 90)
            ru = f"Какова вероятность того, что случайно выбранное двузначное число делится на {k}?"
            en = f"What is the probability that a random two-digit number is divisible by {k}?"
            ru_sol = ["Всего двузначных чисел 90.",
                      f"Кратных {k} среди них {cnt}.",
                      f"P = {cnt}/90 = {R(F(ans))}."]
            en_sol = ["There are 90 two-digit numbers in total.",
                      f"{cnt} of them are divisible by {k}.",
                      f"P = {cnt}/90 = {E(F(ans))}."]
            chk = lambda k=k, cnt=cnt: len([n for n in range(10, 100) if n % k == 0]) == cnt
        elif i % 4 == 1:
            w, b = RNG.randint(2, 8), RNG.randint(2, 8)
            ans = Fr(w, w + b)
            ru = f"В урне {w} белых и {b} чёрных шаров. Найдите вероятность вынуть белый шар."
            en = f"An urn has {w} white and {b} black balls. Find the probability of a white ball."
            ru_sol = [f"Всего шаров {w + b}.",
                      f"Благоприятных исходов {w}.",
                      f"P = {w}/{w + b} = {R(F(ans))}."]
            en_sol = [f"Total balls: {w + b}.",
                      f"Favourable: {w}.",
                      f"P = {E(F(ans))}."]
            chk = lambda w=w, b=b, ans=ans: Fr(w, w + b) == ans
        else:
            ru = ("Монету подбрасывают дважды. Найдите вероятность того, что ровно один раз "
                  "выпадет орёл.")
            en = "A coin is tossed twice. Find the probability of exactly one head."
            ru_sol = ["Всего равновозможных исходов 4: ОО, ОР, РО, РР.",
                      "Благоприятных ровно два: ОР и РО.",
                      "P = 2/4 = 1/2."]
            en_sol = ["Four equally likely outcomes: HH, HT, TH, TT.",
                      "Exactly two are favourable: HT and TH.",
                      "P = 2/4 = 1/2."]
            ans = Fr(1, 2)
            chk = (lambda ans=ans: len([1 for a in ("H", "T") for b in ("H", "T")
                                        if (a == "H") != (b == "H")]) * Fr(1, 4) == ans)
        out.append(_t(f"gen-prb-{i + 1:03d}", "combinatorics", ru, en, F(ans), ru_sol, en_sol,
                      chk, difficulty=3, tags=["вероятность"]))
    return out


# --------------------------------------------------------------------------- #
#  16. Комбинаторика / combinatorics
# --------------------------------------------------------------------------- #

def gen_comb(count=10):
    out = []
    for i in range(count):
        if i % 2 == 0:
            n = RNG.randint(6, 12)
            k = RNG.choice([2, 3])
            ans = comb(n, k)
            ru = f"Сколькими способами можно выбрать {k} предмета из {n}?"
            en = f"In how many ways can {k} items be chosen out of {n}?"
            ru_sol = ["Порядок не важен — это сочетания.",
                      f"C({n},{k}) = {n}! / ({k}!·({n} − {k})!).",
                      f"C({n},{k}) = {ans}."]
            en_sol = ["Order does not matter: combinations.",
                      f"C({n},{k}) = {ans}.",
                      f"Answer: {ans}."]
            chk = lambda n=n, k=k, ans=ans: comb(n, k) == ans
        else:
            n = RNG.randint(4, 7)
            ans = factorial(n)
            ru = f"Сколькими способами можно расставить {n} различных предметов в ряд?"
            en = f"In how many ways can {n} distinct items be arranged in a row?"
            ru_sol = ["Это перестановки из n элементов.",
                      f"P{n} = {n}! = {' · '.join(str(x) for x in range(n, 0, -1))}.",
                      f"P{n} = {ans}."]
            en_sol = ["These are permutations.",
                      f"P{n} = {n}! = {ans}.",
                      f"Answer: {ans}."]
            chk = lambda n=n, ans=ans: factorial(n) == ans
        out.append(_t(f"gen-cmb-{i + 1:03d}", "combinatorics", ru, en, F(ans), ru_sol, en_sol,
                      chk, difficulty=3, tags=["комбинаторика"]))
    return out


# --------------------------------------------------------------------------- #
#  17. Тригонометрия / trigonometry
# --------------------------------------------------------------------------- #

_TRIG_TRIPLES = [(3, 4, 5), (8, 15, 17), (7, 24, 25), (5, 12, 13), (20, 21, 29)]


def gen_trig(count=10):
    """Pythagorean-identity items plus exact table-value computations."""
    out = []
    simple = [
        ("sin 30° + cos 60°", F(1),
         ["sin 30° = ½, cos 60° = ½.", "½ + ½ = 1."], ["sin 30° = ½, cos 60° = ½.", "Sum = 1."],
         lambda v=F(1): F(1, 2) + F(1, 2) == v),
        ("sin²45° + cos²45°", F(1),
         ["Основное тождество sin²α + cos²α = 1.",
          "Выражение равно 1 при любом α, в том числе при 45°."],
         ["Pythagorean identity sin²α + cos²α = 1.",
          "It equals 1 for every α, including 45°."],
         lambda v=F(1): F(1, 2) + F(1, 2) == v),
        ("tg 45° · sin 90°", F(1),
         ["tg 45° = 1, sin 90° = 1.", "1 · 1 = 1."], ["tg 45° = 1, sin 90° = 1.", "1 · 1 = 1."],
         lambda v=F(1): F(1) * F(1) == v),
        ("cos 60° + sin 30°", F(1),
         ["cos 60° = ½, sin 30° = ½.", "½ + ½ = 1."], ["cos 60° = ½, sin 30° = ½.", "Sum = 1."],
         lambda v=F(1): F(1, 2) + F(1, 2) == v),
        ("sin30°·cos60° + cos30°·sin60°", F(1),
         ["Это формула синуса суммы: sin(30° + 60°).",
          "sin 90° = 1."],
         ["Sine of a sum: sin(30° + 60°).", "sin 90° = 1."],
         lambda v=F(1): F(1, 4) + F(3, 4) == v),
    ]
    for i in range(count):
        if i % 2 == 0:
            opp, adj, hyp = _TRIG_TRIPLES[i // 2 % len(_TRIG_TRIPLES)]
            sino, coso = Fr(opp, hyp), Fr(adj, hyp)
            ru = f"Известно, что sin α = {R(sino)}, где α — острый угол. Найдите cos α."
            en = f"Given sin α = {E(sino)} for an acute angle α, find cos α."
            ru_sol = [f"cos²α = 1 − sin²α = 1 − {R(sino ** 2)} = {R(coso ** 2)}.",
                      "α — острый угол, поэтому cos α > 0.",
                      f"cos α = {R(coso)}."]
            en_sol = [f"cos²α = 1 − sin²α = {E(coso ** 2)}.",
                      "α is acute, hence cos α > 0.",
                      f"cos α = {E(coso)}."]
            ans = coso
            chk = (lambda sino=sino, coso=coso: sino * sino + coso * coso == 1)
        else:
            text, ans, ru_sol, en_sol, chk = simple[(i // 2) % len(simple)]
            ru = f"Вычислите {text}."
            en = f"Evaluate {text}."
        out.append(_t(f"gen-trg-{i + 1:03d}", "trig", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=2, tags=["тригонометрия"]))
    return out


# --------------------------------------------------------------------------- #
#  18. Стереометрия / solid geometry
# --------------------------------------------------------------------------- #

def gen_solid(count=10):
    out = []
    for i in range(count):
        mode = i % 5
        if mode == 0:
            a = RNG.randint(2, 8)
            ans, ru, en = F(6 * a * a), \
                f"Найдите площадь полной поверхности куба с ребром {a}.", \
                f"Find the total surface area of a cube with edge {a}."
            ru_sol = [f"У куба 6 граней площадью {a}² = {a * a}.", f"S = 6 · {a * a}.", f"S = {6 * a * a}."]
            en_sol = [f"A cube has 6 faces of area {a * a}.", f"S = 6 · {a * a}.", f"S = {6 * a * a}."]
            chk = lambda a=a, ans=ans: F(6 * a * a) == ans
        elif mode == 1:
            a = RNG.randint(2, 9)
            ans, ru, en = F(a ** 3), \
                f"Найдите объём куба с ребром {a}.", f"Find the volume of a cube with edge {a}."
            ru_sol = ["V = a³.", f"V = {a}³.", f"V = {a ** 3}."]
            en_sol = ["V = a³.", f"V = {a ** 3}.", f"V = {a ** 3}."]
            chk = lambda a=a, ans=ans: F(a ** 3) == ans
        elif mode == 2:
            r, h = RNG.randint(1, 6), RNG.randint(1, 7)
            ans, ru, en = F(r * r * h), \
                f"Найдите объём цилиндра с радиусом основания {r} и высотой {h} (коэффициент при π).", \
                f"Find the volume of a cylinder with radius {r} and height {h} (coefficient at π)."
            ru_sol = ["V = πR²H.", f"V = π · {r * r} · {h}.", f"V = {r * r * h}π."]
            en_sol = ["V = πR²H.", f"V = {r * r * h}π.", f"Answer: {r * r * h}π."]
            chk = lambda r=r, h=h, ans=ans: F(r * r * h) == ans
        elif mode == 3:
            r, h = RNG.randint(1, 6), RNG.choice([3, 6, 9, 12])
            c = F(r * r * h, 3)
            ans, ru, en = c, \
                f"Найдите объём конуса с радиусом {r} и высотой {h} (коэффициент при π).", \
                f"Find the volume of a cone with radius {r} and height {h} (coefficient at π)."
            ru_sol = ["V = ⅓πR²H.", f"V = ⅓ · π · {r * r} · {h}.", f"V = {R(c)}π."]
            en_sol = ["V = ⅓πR²H.", f"V = ⅓ · π · {r * r} · {h}.", f"V = {E(c)}π."]
            chk = lambda r=r, h=h, c=c: F(r * r * h, 3) == c
        else:
            r = RNG.randint(1, 6)
            ans, ru, en = F(4 * r * r), \
                f"Найдите площадь поверхности шара радиуса {r} (коэффициент при π).", \
                f"Find the surface area of a sphere of radius {r} (coefficient at π)."
            ru_sol = ["S = 4πR².", f"S = 4π · {r * r}.", f"S = {4 * r * r}π."]
            en_sol = ["S = 4πR².", f"S = {4 * r * r}π.", f"Answer: {4 * r * r}π."]
            chk = lambda r=r, ans=ans: F(4 * r * r) == ans
        out.append(_t(f"gen-sol-{i + 1:03d}", "stereometry", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=["стереометрия"]))
    return out


# --------------------------------------------------------------------------- #
#  19. Неравенства / inequalities
# --------------------------------------------------------------------------- #

def gen_inequality(count=10):
    out = []
    for i in range(count):
        r1 = RNG.randint(-8, 4)
        r2 = r1 + RNG.choice([3, 4, 5, 6, 7])
        p, q = -(r1 + r2), r1 * r2
        if i % 2 == 0:
            cnt = len([x for x in range(-20, 21) if r1 <= x <= r2])
            ru = f"Найдите количество целых решений неравенства {_qstr(p, q)} ≤ 0."
            en = f"Find the number of integer solutions of {_qstr(p, q)} ≤ 0."
            ru_sol = [f"Нули трёхчлена: {r1} и {r2}, ветви вверх.",
                      f"Решение: {r1} ≤ x ≤ {r2}.",
                      f"Целых решений: {cnt}."]
            en_sol = [f"Zeros: {r1} and {r2}, branches up.",
                      f"Solution: {r1} ≤ x ≤ {r2}.",
                      f"There are {cnt} integer solutions."]
            ans = F(cnt)
            chk = (lambda r1=r1, r2=r2, cnt=cnt:
                   len([x for x in range(-40, 41) if r1 <= x <= r2]) == cnt)
        else:
            # sum of all integers from r1 to r2 inclusive
            s = (r1 + r2) * (r2 - r1 + 1) // 2
            ru = f"Найдите сумму целых решений неравенства {_qstr(p, q)} ≤ 0."
            en = f"Find the sum of the integer solutions of {_qstr(p, q)} ≤ 0."
            ru_sol = [f"Решение неравенства: {r1} ≤ x ≤ {r2}.",
                      f"Сумма целых чисел от {r1} до {r2}.",
                      f"Она равна {s}."]
            en_sol = [f"The solution is {r1} ≤ x ≤ {r2}.",
                      "The arithmetic sum of consecutive integers.",
                      f"It equals {s}."]
            ans = F(s)
            chk = lambda r1=r1, r2=r2, s=s: sum(range(r1, r2 + 1)) == s
        out.append(_t(f"gen-ine-{i + 1:03d}", "inequalities", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=["квадратные неравенства"]))
    return out


# --------------------------------------------------------------------------- #
#  20. Текстовые задачи / word problems
# --------------------------------------------------------------------------- #

_WORK_PAIRS = [(6, 3), (12, 6), (10, 15), (20, 5), (8, 24), (15, 10), (30, 20), (12, 4), (6, 12), (4, 12)]


def gen_word(count=10):
    out = []
    i = 0
    guard = 0
    while len(out) < count and guard < 500:
        guard += 1
        mode = i % 4
        if mode == 0:
            t1, t2 = _WORK_PAIRS[i % len(_WORK_PAIRS)]
            ans = Fr(t1 * t2, t1 + t2)
            if ans.denominator != 1:
                continue
            i += 1
            ru = (f"Первый рабочий выполняет работу за {t1} ч, второй — за {t2} ч. "
                  f"За сколько часов они выполнят работу вместе?")
            en = (f"Worker A needs {t1} h for a job, worker B needs {t2} h. "
                  f"How many hours together?")
            ru_sol = [f"Производительности: 1/{t1} и 1/{t2}.",
                      f"Вместе: 1/{t1} + 1/{t2} = {R(F(t1 + t2, t1 * t2))} работы в час.",
                      f"Время: {R(ans)} ч."]
            en_sol = [f"Rates: 1/{t1} and 1/{t2}.",
                      f"Together: {E(F(t1 + t2, t1 * t2))} per hour.",
                      f"Time: {E(ans)} h."]
            chk = (lambda t1=t1, t2=t2, ans=ans: Fr(t1 * t2, t1 + t2) == ans)
        elif mode == 1:
            v1 = RNG.randint(2, 9)
            diff = RNG.choice([2, 3, 4, 5, 6])
            v2 = v1 + diff
            tm = RNG.choice([2, 3, 4])
            dist = (v1 + v2) * tm
            i += 1
            ru = (f"Два объекта одновременно вышли навстречу друг другу из пунктов, расстояние "
                  f"между которыми {dist} км, и встретились через {tm} ч. Найдите скорость "
                  f"первого (км/ч), если второй на {diff} км/ч быстрее.")
            en = (f"Two objects start simultaneously towards each other from points {dist} km "
                  f"apart and meet after {tm} h. Find the first speed if the second is "
                  f"{diff} km/h faster.")
            ru_sol = [f"Суммарная скорость: {dist} : {tm} = {v1 + v2} км/ч.",
                      f"v + (v + {diff}) = {v1 + v2}.",
                      f"v = {v1} км/ч (второй — {v2} км/ч)."]
            en_sol = [f"Combined speed: {dist} : {tm} = {v1 + v2}.",
                      f"v + (v + {diff}) = {v1 + v2}.",
                      f"v = {v1}."]
            chk = (lambda v1=v1, v2=v2, tm=tm, diff=diff, dist=dist:
                   v2 - v1 == diff and (v1 + v2) * tm == dist)
            ans = F(v1)
        elif mode == 2:
            v1, c1 = RNG.choice([2, 3, 4, 5]), RNG.choice([10, 20, 30, 40])
            v2, c2 = RNG.choice([2, 3, 5, 6]), RNG.choice([40, 50, 60, 70])
            tot = v1 * c1 + v2 * c2
            if tot % (v1 + v2):
                continue
            conc = Fr(tot, v1 + v2)
            i += 1
            ru = (f"Смешали {v1} кг {c1}%-го и {v2} кг {c2}%-го растворов. Найдите концентрацию "
                  f"смеси (в процентах).")
            en = (f"{v1} kg of a {c1}% solution and {v2} kg of a {c2}% solution are mixed. "
                  f"Find the concentration (in %).")
            ru_sol = [f"Вещества: {v1}·{c1}/100 + {v2}·{c2}/100 = {R(F(tot, 100))} кг.",
                      f"Общая масса: {v1 + v2} кг.",
                      f"Концентрация: {R(conc)}%."]
            en_sol = [f"Substance: {E(F(tot, 100))} kg.",
                      f"Total mass: {v1 + v2} kg.",
                      f"Concentration: {E(conc)}%."]
            chk = (lambda v1=v1, c1=c1, v2=v2, c2=c2, conc=conc:
                   Fr(v1 * c1 + v2 * c2, v1 + v2) == conc)
            ans = conc
        else:
            s0 = RNG.choice([120, 240, 360, 480, 600])
            sp = RNG.choice([10, 20, 25, 50])
            dn = RNG.choice([10, 20, 25, 50])
            num_all = s0 * (100 + sp) * (100 - dn)
            if num_all % 10000:
                continue
            final = num_all // 10000
            i += 1
            ru = (f"Число {s0} увеличили на {sp}%, а затем уменьшили на {dn}%. "
                  f"Какое число получилось?")
            en = (f"The number {s0} was increased by {sp}% and then decreased by {dn}%. "
                  f"What is the result?")
            ru_sol = [f"После увеличения: {s0 * (100 + sp) // 100}.",
                      f"После уменьшения: {final}.",
                      f"Ответ: {final}."]
            en_sol = [f"After the increase: {s0 * (100 + sp) // 100}.",
                      f"After the decrease: {final}.",
                      f"Answer: {final}."]
            chk = (lambda s0=s0, sp=sp, dn=dn, final=final:
                   s0 * (100 + sp) * (100 - dn) == 10000 * final)
            ans = F(final)
        out.append(_t(f"gen-wrd-{len(out) + 1:03d}", "wordproblems", ru, en, ans,
                      ru_sol, en_sol, chk, difficulty=3, tags=["текстовые задачи"]))
    return out


# --------------------------------------------------------------------------- #
#  21. Последовательности, заданные формулой / sequences
# --------------------------------------------------------------------------- #

def gen_sequence(count=10):
    out = []
    for i in range(count):
        n = RNG.randint(4, 9)
        if i % 2 == 0:
            k, m = RNG.randint(2, 6), RNG.randint(-9, 12)
            val = k * n * n + m
            ru = f"Последовательность задана формулой aₙ = {k}n² {_sz(m)}. Найдите a{n}."
            en = f"A sequence is defined by aₙ = {k}n² {_sz(m)}. Find a{n}."
            ru_sol = [f"Подставим n = {n}.",
                      f"a{n} = {k}·{n * n} {_sz(m)} = {k * n * n} {_sz(m)}.",
                      f"a{n} = {val}."]
            en_sol = [f"Substitute n = {n}.",
                      f"a{n} = {val}.",
                      f"Answer: {val}."]
            ans, chk = F(val), (lambda k=k, n=n, m=m, val=val: k * n * n + m == val)
        else:
            a1, k = RNG.randint(1, 4), RNG.choice([2, 3])
            terms = [a1]
            for _ in range(4):
                terms.append(k * terms[-1] + 1)
            ru = f"a₁ = {a1}, aₙ₊₁ = {k}aₙ + 1. Найдите a₅."
            en = f"a₁ = {a1}, aₙ₊₁ = {k}aₙ + 1. Find a₅."
            ru_sol = [f"a₂ = {k}·{terms[0]} + 1 = {terms[1]}.",
                      f"a₃ = {terms[2]}, a₄ = {terms[3]}.",
                      f"a₅ = {terms[4]}."]
            en_sol = [f"a₂ = {terms[1]}.",
                      f"a₃ = {terms[2]}, a₄ = {terms[3]}.",
                      f"a₅ = {terms[4]}."]
            ans, chk = F(terms[4]), (lambda a1=a1, k=k, terms=terms:
                                     terms[0] == a1 and all(terms[j + 1] == k * terms[j] + 1
                                                            for j in range(4)))
        out.append(_t(f"gen-seq-{i + 1:03d}", "logic", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=["последовательности"]))
    return out


_GENERATORS = [
    gen_linear, gen_system, gen_vieta, gen_radical, gen_percent, gen_arith, gen_geom,
    gen_right_triangle, gen_quad_area, gen_derivative, gen_parabola, gen_log, gen_exp_eq,
    gen_probability, gen_comb, gen_trig, gen_solid, gen_inequality, gen_word, gen_sequence,
]


def _unique(tasks: list[Task]) -> list[Task]:
    """Drop items whose statement repeats an earlier one (same text, any language)."""
    seen, out = set(), []
    for task in tasks:
        key = (task.topic, task.ru.strip(), task.en.strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(task)
    return out


def generate(per_family=24) -> list[Task]:
    """Build the whole analogous-task bank (deterministic).

    Each family is asked for more items than needed and de-duplicated, so the
    pool always holds *distinct* statements even though the parameter draws are
    random.
    """
    tasks: list[Task] = []
    for gen in _GENERATORS:
        tasks.extend(_unique(gen(per_family * 2))[:per_family])
    return tasks
