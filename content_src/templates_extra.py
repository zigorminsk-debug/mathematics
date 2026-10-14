"""templates_extra.py — дополнительные семейства однотипных заданий.

Покрывают разделы, которых не было в ``templates.py``: числа (делимость,
остатки, цифры), тождественные преобразования выражений, свойства функций,
задачи с параметром и простейшие тригонометрические уравнения.  Для каждого
раздела задания всё так же однотипны, двуязычны, снабжены пошаговым решением и
проверяются точной арифметикой (``Task.check``).

Extra analogous-task families: numbers, algebraic expressions, functions,
parameter problems and basic trigonometric equations.
"""

from __future__ import annotations

from fractions import Fraction as Fr
from math import gcd

from kit import F, R, E, Task  # noqa: F401
from templates import RNG, _t, _sz, _unique


# --------------------------------------------------------------------------- #
#  Числа: делимость, остатки, цифры / divisibility, remainders, digits
# --------------------------------------------------------------------------- #

def gen_numbers(count=20):
    out = []
    for i in range(count):
        kind = i % 5
        if kind == 0:
            a, b, m = RNG.choice([2, 3, 5, 7]), RNG.randint(9, 20), RNG.choice([3, 5, 7, 9, 11, 13])
            rem = pow(a, b, m)
            ru = f"Найдите остаток от деления числа {a}^{b} на {m}."
            en = f"Find the remainder when {a}^{b} is divided by {m}."
            ru_sol = [f"Работаем по модулю {m}: {a}² ≡ {a * a % m}, "
                      f"{a}⁴ ≡ {pow(a, 4, m)}, {a}⁸ ≡ {pow(a, 8, m)}, …",
                      f"Показатель {b} записываем в двоичном виде: {b} = {bin(b)[2:]}, "
                      f"и перемножаем остатки тех степеней, которые входят в разложение.",
                      f"{a}^{b} ≡ {rem} (mod {m}); остаток равен {rem}."]
            en_sol = [f"Work modulo {m}: {a}² ≡ {a * a % m}, {a}⁴ ≡ {pow(a, 4, m)}, "
                      f"{a}⁸ ≡ {pow(a, 8, m)}, …",
                      f"Write the exponent in binary, {b} = {bin(b)[2:]}, and multiply the "
                      f"remainders of the corresponding powers.",
                      f"{a}^{b} ≡ {rem} (mod {m}); the remainder is {rem}."]
            chk = (lambda a=a, b=b, m=m: pow(a, b, m) == pow(a, b) % m)
            ans = F(rem)
            tags = ["делимость"]
        elif kind == 1:
            k, n = RNG.choice([3, 4, 5, 6, 7, 8, 9, 11, 12]), RNG.randint(80, 400)
            cnt = n // k
            ru = f"Сколько натуральных чисел, не превосходящих {n}, делится на {k}?"
            en = f"How many natural numbers up to {n} are divisible by {k}?"
            ru_sol = [f"Это числа {k}, 2·{k}, …, {cnt}·{k}.",
                      f"Их количество равно целой части от деления: ⌊{n} : {k}⌋ = {cnt}.",
                      f"Ответ: {cnt}."]
            en_sol = [f"These are {k}, 2·{k}, …, {cnt}·{k}.",
                      f"Their number is ⌊{n} : {k}⌋ = {cnt}.",
                      f"Answer: {cnt}."]
            chk = (lambda k=k, n=n, cnt=cnt: len([x for x in range(1, n + 1) if x % k == 0]) == cnt)
            ans = F(cnt)
            tags = ["делимость"]
        elif kind == 2:
            a, b = RNG.randint(12, 96), RNG.randint(12, 96)
            g, l = gcd(a, b), a * b // gcd(a, b)
            ru = f"Найдите наименьшее общее кратное чисел {a} и {b}."
            en = f"Find the least common multiple of {a} and {b}."
            ru_sol = [f"НОД({a}, {b}) = {g} (алгоритм Евклида).",
                      f"НОК(a, b) = a·b : НОД(a, b) = {a}·{b} : {g} = {l}.",
                      f"Ответ: {l}."]
            en_sol = [f"gcd({a}, {b}) = {g}.",
                      f"lcm = {a}·{b} : {g} = {l}.",
                      f"Answer: {l}."]
            chk = (lambda a=a, b=b, l=l: l % a == 0 and l % b == 0 and
                   not any(x % a == 0 and x % b == 0 for x in range(1, l)))
            ans = F(l)
            tags = ["НОК и НОД"]
        elif kind == 3:
            a, b = RNG.choice([2, 3, 4, 7, 8, 9, 12, 13]), RNG.randint(5, 30)
            last = pow(a, b, 10)
            ru = f"Найдите последнюю цифру числа {a}^{b}."
            en = f"Find the last digit of {a}^{b}."
            ru_sol = [f"Последняя цифра степени {a} повторяется с периодом 4.",
                      f"Показатель: {b} = 4·{b // 4} + {b % 4}, поэтому смотрим {a}^{b % 4 or 4}.",
                      f"Последняя цифра: {last}."]
            en_sol = [f"Last digits of powers of {a} repeat with period 4.",
                      f"{b} = 4·{b // 4} + {b % 4}, so look at {a}^{b % 4 or 4}.",
                      f"The last digit is {last}."]
            chk = (lambda a=a, b=b, last=last: pow(a, b, 10) == last)
            ans = F(last)
            tags = ["последняя цифра"]
        else:
            n = RNG.randint(1000, 99999)
            digits = [int(c) for c in str(n)]
            s = sum(digits)
            ru = f"Найдите сумму цифр числа {n}."
            en = f"Find the sum of the digits of {n}."
            ru_sol = [f"Выпишем цифры числа: {' + '.join(str(d) for d in digits)}.",
                      f"Складываем: {s}.",
                      f"Ответ: {s}."]
            en_sol = [f"Digits: {' + '.join(str(d) for d in digits)}.",
                      f"Sum: {s}.",
                      f"Answer: {s}."]
            chk = (lambda n=n, s=s: sum(int(c) for c in str(n)) == s)
            ans = F(s)
            tags = ["цифры числа"]
        out.append(_t(f"gen-dig-{i + 1:03d}", "numbers", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=2, tags=tags))
    return out


# --------------------------------------------------------------------------- #
#  Тождественные преобразования / algebraic expressions
# --------------------------------------------------------------------------- #

def gen_expressions(count=20):
    out = []
    for i in range(count):
        kind = i % 5
        if kind == 0:
            a, b = RNG.choice([2, 3, 5, 6, 7, 10, 11, 13]), RNG.randint(2, 15)
            m, n = RNG.randint(2, 7), RNG.randint(2, 7)
            k = RNG.randint(1, min(m + n - 1, 6))
            val = F(m + n - k)
            ru = f"Упростите и найдите значение выражения a^{m}·a^{n} : a^{k} при a = {b}."
            en = f"Simplify a^{m}·a^{n} : a^{k} and evaluate it for a = {b}."
            ru_sol = [f"a^{m}·a^{n} = a^{m + n} (основание одинаковое — показатели складываем).",
                      f"a^{m + n} : a^{k} = a^{m + n - k} = a^{m + n - k}.",
                      f"При a = {b}: {b}^{m + n - k} = {b ** (m + n - k)}."]
            en_sol = [f"a^{m}·a^{n} = a^{m + n}.",
                      f"a^{m + n} : a^{k} = a^{m + n - k}.",
                      f"For a = {b}: {b}^{m + n - k} = {b ** (m + n - k)}."]
            ans = F(b ** (m + n - k))
            chk = (lambda b=b, m=m, n=n, k=k: b ** m * b ** n // b ** k == b ** (m + n - k))
            tags = ["свойства степеней"]
        elif kind == 1:
            a, b = RNG.choice([2, 3, 5, 6, 7, 8, 10, 11, 12]), RNG.choice([2, 3, 5, 7, 10, 13, 15])
            if a == b:
                b += 1
            val = a - b
            ru = f"Вычислите (√{a} − √{b})(√{a} + √{b})."
            en = f"Evaluate (√{a} − √{b})(√{a} + √{b})."
            ru_sol = ["Применим формулу разности квадратов: (√a − √b)(√a + √b) = a − b.",
                      f"Подставляем: (√{a})² − (√{b})² = {a} − {b}.",
                      f"Значение выражения: {val}."]
            en_sol = ["Difference of squares: (√a − √b)(√a + √b) = a − b.",
                      f"(√{a})² − (√{b})² = {a} − {b}.",
                      f"The value is {val}."]
            ans = F(val)
            chk = (lambda a=a, b=b, val=val: a - b == val)
            tags = ["разность квадратов", "иррациональности"]
        elif kind == 2:
            c, v = RNG.randint(3, 12), RNG.randint(4, 20)
            if v == c:
                v += 1
            val = v + c
            ru = f"Сократите дробь (x² − {c * c}) : (x − {c}) и найдите её значение при x = {v}."
            en = f"Simplify (x² − {c * c}) : (x − {c}) and evaluate it for x = {v}."
            ru_sol = [f"Числитель раскладываем на множители: x² − {c * c} = (x − {c})(x + {c}).",
                      f"Сокращаем на (x − {c}): остаётся x + {c}.",
                      f"При x = {v}: {v} + {c} = {val}."]
            en_sol = [f"x² − {c * c} = (x − {c})(x + {c}).",
                      f"Cancel (x − {c}): x + {c} remains.",
                      f"For x = {v}: {val}."]
            ans = F(val)
            chk = (lambda c=c, v=v, val=val: (v * v - c * c) // (v - c) == val)
            tags = ["сокращение дробей"]
        elif kind == 3:
            a = RNG.choice([2, 3, 5, 6, 7])
            b, c = RNG.randint(2, 6), RNG.randint(2, 6)
            val = a ** (b * c)
            ru = f"Вычислите ({a}^{b})^{c}."
            en = f"Evaluate ({a}^{b})^{c}."
            ru_sol = [f"При возведении степени в степень показатели перемножаются: "
                      f"({a}^{b})^{c} = {a}^{b * c}.",
                      f"{a}^{b * c} = {val}.",
                      f"Ответ: {val}."]
            en_sol = [f"({a}^{b})^{c} = {a}^{b * c}.",
                      f"{a}^{b * c} = {val}.",
                      f"Answer: {val}."]
            ans = F(val)
            chk = (lambda a=a, b=b, c=c, val=val: pow(a, b) ** c == val)
            tags = ["свойства степеней"]
        else:
            a, b = RNG.choice([2, 3, 5, 6, 7, 8]), RNG.choice([2, 3, 5, 6, 7, 8])
            val = a * b
            ru = f"Упростите √{a * a * b * b} и найдите значение выражения."
            en = f"Simplify √{a * a * b * b} and give its value."
            ru_sol = [f"√{a * a * b * b} = √({a * b}·{a * b}) — под корнем полный квадрат.",
                      f"√(({a * b})²) = {a * b}.",
                      f"Ответ: {val}."]
            en_sol = [f"√{a * a * b * b} = √(({a * b})²).",
                      f"√(({a * b})²) = {a * b}.",
                      f"Answer: {val}."]
            ans = F(val)
            chk = (lambda a=a, b=b, val=val: a * a * b * b == val * val)
            tags = ["квадратные корни"]
        out.append(_t(f"gen-alf-{i + 1:03d}", "expressions", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=2, tags=tags))
    return out


# --------------------------------------------------------------------------- #
#  Функции / functions
# --------------------------------------------------------------------------- #

def gen_functions(count=20):
    out = []
    for i in range(count):
        kind = i % 5
        if kind == 0:
            b, c, x = RNG.randint(1, 9), RNG.randint(-9, 9), RNG.randint(2, 8)
            val = x * x - b * x + c
            ru = f"Дана функция f(x) = x² − {b}x {_sz(c)}. Найдите f({x})."
            en = f"Given f(x) = x² − {b}x {_sz(c)}, find f({x})."
            ru_sol = [f"Подставляем x = {x}: f({x}) = {x}² − {b}·{x} {_sz(c)}.",
                      f"= {x * x} − {b * x} {_sz(c)}.",
                      f"f({x}) = {val}."]
            en_sol = [f"Substitute x = {x}: f({x}) = {x * x} − {b * x} {_sz(c)}.",
                      f"= {val}.",
                      f"f({x}) = {val}."]
            chk = (lambda b=b, c=c, x=x, val=val: x * x - b * x + c == val)
            ans = F(val)
            tags = ["значение функции"]
        elif kind == 1:
            a, b, x = RNG.randint(1, 6), RNG.randint(1, 6), RNG.randint(2, 12)
            if x == b:
                x += 1
            val = Fr(x + a, x - b)
            ru = f"Дана функция f(x) = (x + {a}) : (x − {b}). Найдите f({x})."
            en = f"Given f(x) = (x + {a}) / (x − {b}), find f({x})."
            ru_sol = [f"Подставляем x = {x}: f({x}) = ({x} + {a}) : ({x} − {b}).",
                      f"= {x + a} : {x - b}.",
                      f"f({x}) = {R(val)}."]
            en_sol = [f"Substitute x = {x}: ({x} + {a}) / ({x} − {b}).",
                      f"= {x + a} / {x - b}.",
                      f"f({x}) = {E(val)}."]
            chk = (lambda a=a, b=b, x=x, val=val: x - b != 0 and Fr(x + a, x - b) == val)
            ans = val
            tags = ["значение функции"]
        elif kind == 2:
            a, b = RNG.randint(1, 9), RNG.randint(1, 9)
            ru = f"Найдите наименьшее значение функции y = |x − {a}| + {b}."
            en = f"Find the minimum of y = |x − {a}| + {b}."
            ru_sol = ["Модуль неотрицателен: |x − a| ≥ 0.",
                      f"Наименьшее значение модуля равно 0 — оно достигается при x = {a}.",
                      f"Тогда y = 0 + {b} = {b}."]
            en_sol = ["The absolute value is non-negative: |x − a| ≥ 0.",
                      f"The minimum of the modulus is 0, attained at x = {a}.",
                      f"Hence the minimum of y is {b}."]
            chk = (lambda a=a, b=b: all(abs(x - a) + b >= b for x in range(-50, 50)) and
                   min(abs(x - a) for x in range(-50, 51)) == 0)
            ans = F(b)
            tags = ["модуль", "наименьшее значение"]
        elif kind == 3:
            x1, x2 = RNG.randint(-6, 0), RNG.randint(1, 6)
            k = RNG.choice([2, 3, -2, -3])
            y1, y2 = k * x1 + 2, k * x2 + 2
            ru = (f"Прямая y = kx + b проходит через точки A({x1}; {y1}) и B({x2}; {y2}). "
                  f"Найдите k.")
            en = f"The line y = kx + b passes through A({x1}; {y1}) and B({x2}; {y2}). Find k."
            ru_sol = [f"k = (y₂ − y₁) : (x₂ − x₁) = ({y2} − {y1}) : ({x2} − {x1}).",
                      f"= {y2 - y1} : {x2 - x1}.",
                      f"k = {k}."]
            en_sol = [f"k = (y₂ − y₁) / (x₂ − x₁) = ({y2} − {y1}) / ({x2} − {x1}).",
                      f"= {k}.",
                      f"k = {k}."]
            chk = (lambda x1=x1, x2=x2, y1=y1, y2=y2, k=k:
                   x1 != x2 and Fr(y2 - y1, x2 - x1) == k)
            ans = F(k)
            tags = ["линейная функция", "угловой коэффициент"]
        else:
            a, r, m = RNG.randint(1, 5), RNG.randint(2, 6), RNG.randint(1, 4)
            inner = 2 * r + m
            val = a * inner
            ru = (f"Даны функции f(x) = {a}x и g(x) = x + {m}. Найдите f(g({2 * r})) — "
                  f"то есть значение f от g({2 * r}).")
            en = (f"Given f(x) = {a}x and g(x) = x + {m}, find f(g({2 * r})).")
            ru_sol = [f"Сначала g({2 * r}) = {2 * r} + {m} = {inner}.",
                      f"Затем f({inner}) = {a}·{inner} = {val}.",
                      f"Ответ: {val}."]
            en_sol = [f"g({2 * r}) = {inner}.",
                      f"f({inner}) = {a}·{inner} = {val}.",
                      f"Answer: {val}."]
            chk = (lambda a=a, r=r, m=m, val=val: a * (2 * r + m) == val)
            ans = F(val)
            tags = ["композиция функций"]
        out.append(_t(f"gen-fnc-{i + 1:03d}", "functions", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=2, tags=tags))
    return out


# --------------------------------------------------------------------------- #
#  Задачи с параметром / parameter problems
# --------------------------------------------------------------------------- #

def gen_param(count=20):
    out = []
    for i in range(count):
        kind = i % 5
        if kind == 0:
            x0, a = RNG.choice([2, 3, 4, 5, 6, 8]), RNG.randint(2, 12)
            b = a * x0
            ru = (f"При каком значении a уравнение ax = {b} имеет единственный корень x = {x0}?")
            en = f"For which value of a does ax = {b} have the single root x = {x0}?"
            ru_sol = [f"Подставим корень в уравнение: a·{x0} = {b}.",
                      f"Отсюда a = {b} : {x0}.",
                      f"a = {a}."]
            en_sol = [f"Substitute the root: a·{x0} = {b}.",
                      f"a = {b} / {x0} = {a}.",
                      f"Answer: a = {a}."]
            chk = (lambda a=a, x0=x0, b=b: a * x0 == b)
            ans = F(a)
            tags = ["параметр"]
        elif kind == 1:
            p = RNG.choice([2, 4, 6, 8, 10, 12])
            q = p * p // 4
            ru = (f"Уравнение x² − {p}x + q = 0 имеет один корень (D = 0). "
                  f"Найдите q.")
            en = f"The equation x² − {p}x + q = 0 has one root (D = 0). Find q."
            ru_sol = [f"D = p² − 4q = 0, значит q = p² : 4.",
                      f"p = {p}, поэтому q = {p * p} : 4.",
                      f"q = {q} (корень при этом x = {p // 2})."]
            en_sol = [f"D = 0 ⇒ q = p²/4.",
                      f"q = {p * p} / 4 = {q}.",
                      f"Answer: q = {q}."]
            chk = (lambda p=p, q=q: p * p - 4 * q == 0)
            ans = F(q)
            tags = ["параметр", "дискриминант"]
        elif kind == 2:
            k, x0 = RNG.choice([2, 3, -2, 4, -1]), RNG.randint(-6, 6)
            y0 = RNG.randint(-9, 9)
            b = y0 - k * x0
            ru = f"Прямая y = {k}x + b проходит через точку ({x0}; {y0}). Найдите b."
            en = f"The line y = {k}x + b passes through ({x0}; {y0}). Find b."
            ru_sol = [f"Подставим координаты точки: {y0} = {k}·({x0}) + b.",
                      f"{y0} = {k * x0} + b.",
                      f"b = {b}."]
            en_sol = [f"Substitute the point: {y0} = {k}·({x0}) + b.",
                      f"b = {y0} − {k * x0} = {b}.",
                      f"Answer: b = {b}."]
            chk = (lambda k=k, x0=x0, y0=y0, b=b: k * x0 + b == y0)
            ans = F(b)
            tags = ["параметр"]
        elif kind == 3:
            p_shift, q_shift = RNG.randint(1, 9), RNG.randint(-9, 9)
            c = p_shift * p_shift + q_shift          # y = x² + 2p·x + c = (x + p)² + q
            ru = (f"При каком значении параметра a прямая y = a имеет с графиком функции "
                  f"y = x² + {2 * p_shift}x + {c} ровно одну общую точку?")
            en = (f"For which value of the parameter a does the line y = a touch the graph of "
                  f"y = x² + {2 * p_shift}x + {c} (exactly one common point)?")
            ru_sol = [f"Выделим полный квадрат: x² + {2 * p_shift}x + {c} = (x + {p_shift})² {_sz(q_shift)}.",
                      f"Наименьшее значение функции равно {q_shift} и достигается в вершине "
                      f"x = −{p_shift}.",
                      f"Горизонтальная прямая имеет ровно одну общую точку с параболой только в "
                      f"вершине, значит a = {q_shift}."]
            en_sol = [f"Complete the square: (x + {p_shift})² {_sz(q_shift)}.",
                      f"The minimum of the parabola is {q_shift}, attained at x = −{p_shift}.",
                      f"A horizontal line touches the parabola only at the vertex, so a = {q_shift}."]
            # the vertex value of y = x² + 2px + c is c − p² and must equal q
            chk = (lambda p_shift=p_shift, c=c, q_shift=q_shift:
                   (p_shift + p_shift) == 2 * p_shift and c - p_shift * p_shift == q_shift)
            ans = F(q_shift)
            tags = ["параметр", "парабола"]
        else:
            v = RNG.choice([1, 2, 3, 4, 5, 6])
            ru = (f"При каком значении параметра a уравнение (a − {v})x = a² − {v * v} "
                  f"имеет бесконечно много корней?")
            en = (f"For which value of the parameter a does (a − {v})x = a² − {v * v} "
                  f"have infinitely many roots?")
            ru_sol = [f"При a = {v} левая часть равна 0·x = 0, а правая: {v}² − {v * v} = 0 — "
                      f"получаем тождество 0 = 0, решений бесконечно много.",
                      f"Проверим, что других таких a нет: при a ≠ {v} правая часть "
                      f"a² − {v * v} = (a − {v})(a + {v}), и после деления на (a − {v}) "
                      f"остаётся ровно один корень x = a + {v}.",
                      f"Ответ: a = {v}."]
            en_sol = [f"At a = {v} the left side is 0·x = 0 and the right side {v}² − {v * v} = 0, "
                      f"so 0 = 0 holds for every x.",
                      f"For a ≠ {v} we may divide by (a − {v}) since a² − {v * v} = "
                      f"(a − {v})(a + {v}), leaving the single root x = a + {v}.",
                      f"Answer: a = {v}."]
            chk = (lambda v=v: all((a - v) * (a + v) == a * a - v * v for a in range(-20, 20)) and
                   v * v - v * v == (v - v) * (v + v))
            ans = F(v)
            tags = ["параметр"]
        out.append(_t(f"gen-prm-{i + 1:03d}", "param", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=tags))
    return out


# --------------------------------------------------------------------------- #
#  Простейшие тригонометрические уравнения / basic trig equations
# --------------------------------------------------------------------------- #

def _count_on(offsets, hi, period=2):
    """Number of solutions x/π = offset + period·k lying in [0; hi] (exact fractions)."""
    total = 0
    for offset in offsets:
        for k in range(-4, int(hi) + 5):
            value = offset + period * k
            if 0 <= value <= hi:
                total += 1
    return total


def gen_trigeq(count=20):
    out = []
    for i in range(count):
        kind = i % 5
        if kind == 0:
            n = RNG.choice([1, 2, 3, 4, 6])
            hi = Fr(n)
            offsets = [Fr(1, 6), Fr(5, 6)]           # sin x = 1/2
            roots = _count_on(offsets, hi)
            ru = f"Сколько корней имеет уравнение sin x = 1/2 на отрезке [0; {n}π]?"
            en = f"How many roots does sin x = 1/2 have on the interval [0; {n}π]?"
            ru_sol = ["Уравнение sin x = 1/2 имеет две серии корней: x = π/6 + 2πk и x = 5π/6 + 2πk.",
                      f"Отбираем те, что попадают в [0; {n}π]: π/6, 5π/6, 13π/6, 17π/6, … — "
                      f"двигаемся шагом 2π, пока не выйдем за правый конец отрезка.",
                      f"Таких значений {roots}."]
            en_sol = ["sin x = 1/2 has two series of roots: x = π/6 + 2πk and x = 5π/6 + 2πk.",
                      f"Keep those inside [0; {n}π]: π/6, 5π/6, 13π/6, 17π/6, … stepping by 2π.",
                      f"There are {roots} of them."]
            chk = (lambda roots=roots, hi=hi: roots == _count_on([Fr(1, 6), Fr(5, 6)], hi))
            ans = F(roots)
            tags = ["тригонометрические уравнения"]
        elif kind == 1:
            n = RNG.choice([1, 2, 3, 4, 6])
            hi = Fr(n)
            roots = _count_on([Fr(1)], hi)           # cos x = −1
            ru = f"Сколько корней имеет уравнение cos x = −1 на отрезке [0; {n}π]?"
            en = f"How many roots does cos x = −1 have on the interval [0; {n}π]?"
            ru_sol = ["cos x = −1 только при x = π + 2πk — одна серия с шагом 2π.",
                      f"В отрезок [0; {n}π] попадают значения π, 3π, 5π, … (пока не больше {n}π).",
                      f"Их {roots}."]
            en_sol = ["cos x = −1 only for x = π + 2πk, a single series with step 2π.",
                      f"Inside [0; {n}π] lie π, 3π, 5π, … up to {n}π.",
                      f"There are {roots} roots."]
            chk = (lambda roots=roots, hi=hi: roots == _count_on([Fr(1)], hi))
            ans = F(roots)
            tags = ["тригонометрические уравнения"]
        elif kind == 2:
            k = RNG.choice([2, 3, 4])
            roots = 2 * k + 1
            ru = f"Сколько корней имеет уравнение sin {k}x = 0 на отрезке [0; 2π]?"
            en = f"How many roots does sin {k}x = 0 have on the interval [0; 2π]?"
            ru_sol = [f"sin {k}x = 0 ⇔ {k}x = πm ⇔ x = πm/{k}.",
                      f"Условие 0 ≤ πm/{k} ≤ 2π даёт m = 0, 1, …, {2 * k}.",
                      f"Всего корней: {2 * k} + 1 = {roots}."]
            en_sol = [f"sin {k}x = 0 ⇔ x = πm/{k}.",
                      f"0 ≤ πm/{k} ≤ 2π gives m = 0, 1, …, {2 * k}.",
                      f"Total: {roots} roots."]
            chk = (lambda k=k, roots=roots: roots == 2 * k + 1)
            ans = F(roots)
            tags = ["тригонометрические уравнения"]
        elif kind == 3:
            n = RNG.choice([1, 2, 3, 4])
            roots = n
            ru = f"Сколько корней имеет уравнение tg x = 1 на промежутке (0; {n}π)?"
            en = f"How many roots does tg x = 1 have on the interval (0; {n}π)?"
            ru_sol = ["tg x = 1 ⇔ x = π/4 + πk: в каждом интервале длины π ровно один корень.",
                      f"Промежуток (0; {n}π) содержит {n} таких интервалов.",
                      f"Значит корней {roots}."]
            en_sol = ["tg x = 1 ⇔ x = π/4 + πk — one root in every interval of length π.",
                      f"(0; {n}π) contains {n} such intervals.",
                      f"Answer: {roots}."]
            chk = (lambda n=n, roots=roots: roots == n)
            ans = F(roots)
            tags = ["тригонометрические уравнения"]
        else:
            n = RNG.choice([2, 3, 4, 6])
            hi = Fr(2)
            offsets = [Fr(2 * m, n) for m in range(n + 1)]     # cos n x = 1
            roots = _count_on(offsets, hi)
            ru = f"Сколько корней имеет уравнение cos {n}x = 1 на отрезке [0; 2π]?"
            en = f"How many roots does cos {n}x = 1 have on the interval [0; 2π]?"
            ru_sol = [f"cos {n}x = 1 ⇔ {n}x = 2πm ⇔ x = 2πm/{n}.",
                      f"0 ≤ 2πm/{n} ≤ 2π даёт m = 0, 1, …, {n}.",
                      f"Всего корней: {n} + 1 = {roots}."]
            en_sol = [f"cos {n}x = 1 ⇔ x = 2πm/{n}.",
                      f"m = 0, 1, …, {n} ⇒ {roots} roots.",
                      f"Answer: {roots}."]
            chk = (lambda roots=roots, offsets=offsets, hi=hi: roots == _count_on(offsets, hi))
            ans = F(roots)
            tags = ["тригонометрические уравнения"]
        out.append(_t(f"gen-teq-{i + 1:03d}", "trigequations", ru, en, ans, ru_sol, en_sol, chk,
                      difficulty=3, tags=tags))
    return out


GENERATORS_EXTRA = [gen_numbers, gen_expressions, gen_functions, gen_param, gen_trigeq]


def generate_extra() -> list[Task]:
    """Build the additional families (20 unique items each)."""
    tasks: list[Task] = []
    for gen in GENERATORS_EXTRA:
        tasks.extend(_unique(gen(24))[:20])
    return tasks
