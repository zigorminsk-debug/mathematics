"""variants.py — движок авторских тренировочных вариантов 2022–2026 годов.

Зачем нужен движок
------------------
Шесть вариантов по 30 заданий — это 180 заданий. Писать их руками долго и опасно:
опечатка в числе, единице или допуске ломает сборку. Поэтому варианты 2022–2026
собираются из **рецептов**: рецепт задаёт тему, формулу, условия и текст с
подстановками ``{symbol}``, а числа для каждого года берёт из :func:`params`.
Модель остаётся физической:

* ответ считает ядро (``kit.calc_task``) точной арифметикой в СИ;
* физические постоянные (g, ρ, k, h, c) объявлены как **постоянные задания**
  (``constants=``) — ученик видит их значение в «Дано», а не догадывается;
* неверные варианты части A выводятся из **неверных моделей**: дистрактор
  «забыт множитель ½» считает именно формула без ½. Если дистрактор случайно
  совпал с верным ответом, сборка падает (см. :func:`_a`).

Что это НЕ такое
----------------
Это не официальные материалы РИКЗ. Тексты, числа и разборы написаны автором по
программе и формату ЦТ (10 заданий части A, 20 заданий части B, 210 минут —
перечень РИКЗ, проверено 2026-10-14, см. ``periods.py``).

Как добавить задание
--------------------
1. Написать ``def r_xxx(year, p) -> Task`` (``p`` — числа года из :func:`params`).
2. Добавить функцию в :data:`PART_A` или :data:`PART_B` (порядок = порядок в варианте).
3. Проверить::

       python3 -c "import variants; variants.self_check()"
"""

from __future__ import annotations

from fractions import Fraction

import quantities
from kit import PhysicsError, calc_choice_task, calc_task
from quantities import Q, eval_model, format_quantity, parse_unit, to_fraction

#: годы, которые собирает движок (вариант 2021 года написан руками отдельно)
YEARS = (2022, 2023, 2024, 2025, 2026)

SRC = "авторское тренировочное задание по программе ЦТ по физике; не материалы РИКЗ"


def params(year: int) -> dict:
    """Числа года. Разные годы — разные данные, одна и та же физика."""
    k = year - 2022
    if not 0 <= k <= 4:
        raise PhysicsError(f"нет чисел для варианта {year}")
    return {
        # измерения
        "speed_kmh": 36 + 18 * k,                     # 36, 54, 72, 90, 108 км/ч
        # кинематика
        "fall_t": 2 + k,                              # 2 … 6 с
        "v0": 4 + 2 * k,                              # 4 … 12 м/с
        "accel": 1 + k,                               # 1 … 5 м/с²
        "accel_t": 3 + k,                             # 3 … 7 с
        "avg_s1": 6 + 2 * k,                          # 6 … 14 км
        "avg_t1": [0.5, 1, 1.5, 2, 2.5][k],           # ч
        "avg_s2": 12 + 4 * k,                         # 12 … 28 км
        "avg_t2": 1 + k,                              # 1 … 5 ч
        # динамика
        "mass": 2 + 2 * k,                            # 2 … 10 кг
        "mu": [0.2, 0.25, 0.3, 0.35, 0.4][k],         # коэффициент трения
        "force": 6 + 2 * k,                           # 6 … 14 Н
        "spring_k": 200 + 50 * k,                     # 200 … 400 Н/м
        "spring_x": 0.02 + 0.01 * k,                  # 0,02 … 0,06 м
        "weight_m": 8 + 2 * k,                        # 8 … 16 кг
        # работа, энергия, импульс
        "ke_m": 2 + k,                                # 2 … 6 кг
        "ke_v": 6 + 2 * k,                            # 6 … 14 м/с
        "work_f": 10 + 5 * k,                         # 10 … 30 Н
        "work_s": 2 + k,                              # 2 … 6 м
        "pe_m": 2 + k,                                # 2 … 6 кг
        "pe_h": 1 + k,                                # 1 … 5 м
        "mom_m": 3 + k,                               # 3 … 7 кг
        "mom_v": 2 + 2 * k,                           # 2 … 10 м/с
        # статика, давление, гидростатика
        "arch_v": 0.002 + 0.001 * k,                  # 0,002 … 0,006 м³
        "hydro_h": 3 + k,                             # 3 … 7 м
        # молекулярная физика и теплота
        "gas_v1": 2 + k,                              # 2 … 6 л
        "gas_t1": 300,                                # 300 К (27 °C)
        "gas_t2": 400,                                # 400 К (127 °C)
        "mol_mass": 44,                               # CO₂, г/моль
        "mol_m": 88 + 44 * k,                         # 88 … 264 г
        "heat_m": [0.4, 0.6, 0.8, 1.2, 1.6][k],       # 0,4 … 1,6 кг
        "heat_dt": 20 + 10 * k,                       # 20 … 60 К
        "latent_m": 0.5 + 0.5 * k,                    # 0,5 … 2,5 кг
        # электричество и магнетизм
        "charge_q1": 2 + k,                           # 2 … 6 мкКл
        "charge_q2": 3 + k,                           # 3 … 7 мкКл
        "charge_r": 0.03 + 0.01 * k,                  # 0,03 … 0,07 м
        "volt": 12 + 6 * k,                           # 12 … 36 В
        "res_r1": 2 + k,                              # 2 … 6 Ом
        "res_r2": 3 + k,                              # 3 … 7 Ом
        "lamp_u": 120 + 20 * k,                       # 120 … 200 В
        "lamp_r": 60,                                 # 60 Ом, одна и та же лампа
        "field_b": 0.2 + 0.1 * k,                     # 0,2 … 0,6 Тл
        "field_i": 4 + k,                             # 4 … 8 А
        "field_l": 0.1 + 0.05 * k,                    # 0,1 … 0,3 м
        # колебания, волны, оптика, кванты
        "wave_v": 300 + 40 * k,                       # 300 … 460 м/с
        "wave_t": 0.002 + 0.001 * k,                  # 0,002 … 0,006 с
        "optic_d": 0.25 + 0.05 * k,                   # 0,25 … 0,45 м
        "optic_f": 0.5 + 0.05 * k,                    # 0,5 … 0,7 м
        "photon_nu": 5 + k,                           # 5 … 9 ·10¹⁴ Гц
    }


# --------------------------------------------------------------------------- #
#  Помощники / helpers
# --------------------------------------------------------------------------- #

def _si(data: dict, vars_: dict, constants: dict) -> dict:
    """Данные и постоянные в СИ — теми же правилами, что и ядро заданий."""
    out = {}
    for symbol, (value, unit) in {**data, **constants}.items():
        if symbol not in vars_:
            raise PhysicsError(f"нет размерности для {symbol!r}")
        unit_obj = parse_unit(unit)
        if unit_obj.offset:
            raise PhysicsError("данные °C нужно задавать в кельвинах")
        out[symbol] = Q(to_fraction(value), unit_obj).si()
    return out


def _constants(spec: dict) -> dict:
    """``{"g": "м/с^2"}`` → ``{"g": ("9.8", "м/с^2")}`` из школьных соглашений."""
    resolved = {}
    for symbol, unit in spec.items():
        if symbol not in quantities.CONVENTIONS:
            raise PhysicsError(f"постоянная {symbol!r} неизвестна в CONVENTIONS")
        resolved[symbol] = (quantities.CONVENTIONS[symbol][0], unit)
    return resolved


def _wrong(expression: str, vars_: dict, data: dict, constants: dict, unit: str,
           rounding: int | None = None, lang: str = "ru") -> str:
    """Значение неверной модели в требуемой единице — это и есть дистрактор."""
    values = _si(data, vars_, constants)
    try:
        value = Fraction(eval_model(expression, values))
    except Exception as error:                       # noqa: BLE001 — ошибка автора рецепта
        raise PhysicsError(f"дистрактор {expression!r} не вычисляется: {error}") from error
    target = parse_unit(unit)
    return format_quantity(value / target.factor, target, lang, places=rounding)


def _a(year, n, topic, difficulty, ru, en, tags, formula, wrong_models, **kw):
    """Задание части A: верный ответ считает ядро, неверные — модели ошибок."""
    data, constants = kw["data"], _constants(kw.get("constants") or {})
    if constants:
        kw["constants"] = {symbol: unit for symbol, (_value, unit) in constants.items()}
    wrong = [(model, why_ru, why_en) for model, why_ru, why_en in wrong_models]
    if len(wrong) != 4:
        raise PhysicsError(f"phys-{year}-a{n}: нужно ровно 4 типичные ошибки")
    correct = _wrong(kw["model"].split("=", 1)[1], kw["vars"], data, constants,
                     kw["unit"], kw.get("rounding"))
    distractors = []
    for model, why_ru, why_en in wrong:
        distractors.append((_wrong(model, kw["vars"], data, constants, kw["unit"],
                                   kw.get("rounding"), "ru"), why_ru,
                            _wrong(model, kw["vars"], data, constants, kw["unit"],
                                   kw.get("rounding"), "en"), why_en))
    # Дистрактор, совпавший с верным ответом или с другим дистрактором, — ошибка
    # автора рецепта: ловим её здесь, пока известно, какой рецепт виноват.
    texts = [item[0] for item in distractors] + [correct]
    if len(set(texts)) != 5:
        raise PhysicsError(f"phys-{year}-a{n}: варианты ответа не различаются — {texts}")
    return calc_choice_task(id=f"phys-{year}-a{n}", year=year, n=n, topic=topic,
                            difficulty=difficulty, ru=ru, en=en, formula=formula,
                            distractors=distractors, tags=tags, src=SRC, **kw)


def _b(year, n, topic, difficulty, ru, en, tags, formula, **kw):
    if kw.get("constants"):
        kw["constants"] = {symbol: unit for symbol, unit in kw["constants"].items()}
    return calc_task(id=f"phys-{year}-b{n}", year=year, part="B", n=n, topic=topic,
                     difficulty=difficulty, ru=ru, en=en, formula=formula, tags=tags,
                     src=SRC, **kw)


G_UNIT = "м/с^2"


# --------------------------------------------------------------------------- #
#  Часть A — 10 заданий
# --------------------------------------------------------------------------- #

def a1_units(year, p):
    """Измерения: перевод км/ч в м/с."""
    return _a(year, 1, "measurements", 1,
              "Спидометр автомобиля показывает {V} км/ч. Выразите эту скорость в м/с.",
              "The speedometer reads {V} km/h. Express this speed in m/s.",
              tags=("перевод единиц",), formula="v = v₀ · 5/18 (1 км/ч = 5/18 м/с)",
              model="v = V", vars={"v": "m/s", "V": "m/s"},
              data={"V": (str(p["speed_kmh"]), "км/ч")}, ask="v", unit="м/с",
              symbols={"V": "v₀"}, rounding=0,
              wrong_models=[("V * 3.6", "число переписано без перевода единиц",
                             "the number was copied without converting units"),
                            ("V * 3.6 * 3.6", "умножение на 3,6 вместо деления",
                             "multiplied by 3.6 instead of dividing"),
                            ("V / 3.6", "деление на 3,6 вместо умножения на 5/18",
                             "divided by 3.6 instead of multiplying by 5/18"),
                            ("V * 3600", "число переведено в км/ч второй раз",
                             "the value was converted to km/h a second time")])


def a2_free_fall(year, p):
    """Кинематика: свободное падение."""
    return _a(year, 2, "kinematics", 2,
              "Тело падает из состояния покоя {t} с. Какой путь оно пройдёт? "
              "Ускорение свободного падения g = {g}, сопротивление воздуха не учитывается.",
              "A body falls from rest for {t} s. What distance does it cover? "
              "Take g = {g} and ignore air resistance.",
              tags=("свободное падение",), formula="h = g·t²/2",
              model="h = g*t^2/2",
              vars={"h": "m", "t": "s", "g": "m/s^2"}, constants={"g": G_UNIT},
              data={"t": (str(p["fall_t"]), "с")}, ask="h", unit="м", rounding=1,
              wrong_models=[("g*t^2", "забыт множитель ½",
                             "the factor ½ was dropped"),
                            ("g*t^2*2", "умножение на 2 вместо деления",
                             "multiplied by 2 instead of dividing"),
                            ("g*t/2", "время не возведено в квадрат",
                             "time was not squared"),
                            ("g*t/4", "время без квадрата и лишнее деление на 4",
                             "time was not squared and the divisor is wrong")])


def a3_friction(year, p):
    """Динамика: сила трения скольжения."""
    return _a(year, 3, "dynamics", 2,
              "Ящик массой {m} кг равномерно тянут по горизонтальному полу. "
              "Коэффициент трения μ = {mu}, g = {g}. Найдите силу трения.",
              "A crate of {m} kg is pulled at constant speed along a horizontal floor. "
              "The friction coefficient is μ = {mu}, g = {g}. Find the friction force.",
              tags=("сила трения",), formula="Fтр = μ·m·g",
              model="F = mu*m*g",
              vars={"F": "kg·m/s^2", "mu": "1", "m": "kg", "g": "m/s^2"},
              constants={"g": G_UNIT},
              data={"mu": (str(p["mu"]), "1"), "m": (str(p["mass"]), "кг")},
              ask="F", unit="Н", rounding=1,
              wrong_models=[("m*g", "коэффициент трения не учтён",
                             "the friction coefficient was ignored"),
                            ("mu*m", "g потеряно", "g was dropped"),
                            ("m/g", "деление на g вместо умножения",
                             "divided by g instead of multiplying"),
                            ("mu*m*g*2", "лишний множитель 2",
                             "an extra factor 2")])


def a4_kinetic(year, p):
    """Энергия: кинетическая энергия."""
    return _a(year, 4, "workenergy", 2,
              "Тело массой {m} кг движется со скоростью {v} м/с. "
              "Найдите его кинетическую энергию.",
              "A body of {m} kg moves at {v} m/s. Find its kinetic energy.",
              tags=("закон сохранения энергии",), formula="Eк = m·v²/2",
              model="E = m*v^2/2", vars={"E": "kg·m^2/s^2", "m": "kg", "v": "m/s"},
              data={"m": (str(p["ke_m"]), "кг"), "v": (str(p["ke_v"]), "м/с")},
              ask="E", unit="Дж", rounding=0,
              wrong_models=[("m*v", "скорость не возведена в квадрат",
                             "the speed was not squared"),
                            ("m*v^2", "забыт множитель ½",
                             "the factor ½ was dropped"),
                            ("v^2/2", "масса не учтена",
                             "the mass was ignored"),
                            ("m*v^2*2", "умножение на 2 вместо деления",
                             "multiplied by 2 instead of dividing")])


def a5_hydro(year, p):
    """Статика: гидростатическое давление."""
    return _a(year, 5, "statics", 2,
              "Определите давление воды на глубине {h} м. Плотность воды "
              "ρ = {rho_water}, g = {g}, атмосферное давление не учитывается.",
              "Find the water pressure at a depth of {h} m. Water density is "
              "ρ = {rho_water}, g = {g}; atmospheric pressure is not counted.",
              tags=("гидростатическое давление",), formula="p = ρ·g·h",
              model="p = rho_water*g*h",
              vars={"p": "kg/(m·s^2)", "h": "m", "rho_water": "kg/m^3", "g": "m/s^2"},
              constants={"rho_water": "кг/м^3", "g": G_UNIT},
              data={"h": (str(p["hydro_h"]), "м")}, ask="p", unit="кПа", rounding=1,
              wrong_models=[("rho_water*h", "g потеряно", "g was dropped"),
                            ("rho_water*h/g", "деление на g вместо умножения",
                             "divided by g instead of multiplying"),
                            ("rho_water*g*h*1000", "лишний множитель 1000",
                             "an extra factor of 1000"),
                            ("rho_water*g/h", "высота разделена вместо умножения",
                             "divided by the depth instead of multiplying")])


def a6_amount(year, p):
    """Молекулярная физика: количество вещества."""
    return _a(year, 6, "molecular", 1,
              "Найдите количество вещества в {m} г углекислого газа CO₂. "
              "Молярная масса CO₂ равна {M} г/моль.",
              "Find the amount of substance in {m} g of carbon dioxide CO₂. "
              "The molar mass of CO₂ is {M} g/mol.",
              tags=("количество вещества",), formula="ν = m/M",
              model="nu = m/M", vars={"nu": "mol", "m": "kg", "M": "kg/mol"},
              data={"m": (str(p["mol_m"]), "г"), "M": (str(p["mol_mass"]), "г/моль")},
              ask="nu", unit="моль", rounding=1,
              wrong_models=[("M/m", "деление перевёрнуто", "the division was inverted"),
                            ("m/M*1000", "граммы приняты за килограммы",
                             "grams were taken for kilograms"),
                            ("m/M/2", "взята половина количества вещества",
                             "half the amount was taken"),
                            ("m/M*10", "лишний множитель 10",
                             "an extra factor of 10")])


def a7_heat(year, p):
    """Теплота: нагревание воды."""
    return _a(year, 7, "thermo", 2,
              "Сколько теплоты нужно, чтобы нагреть {m} кг воды на {dt} К? "
              "Удельная теплоёмкость воды c = {c_water}.",
              "How much heat is needed to warm {m} kg of water by {dt} K? "
              "The specific heat capacity of water is c = {c_water}.",
              tags=("теплота и теплоёмкость",), formula="Q = c·m·Δt",
              model="Q = c_water*m*dt",
              vars={"Q": "kg·m^2/s^2", "c_water": "m^2/(s^2·K)", "m": "kg", "dt": "K"},
              constants={"c_water": "Дж/(кг·К)"},
              data={"m": (str(p["heat_m"]), "кг"), "dt": (str(p["heat_dt"]), "К")},
              ask="Q", unit="кДж", rounding=1,
              wrong_models=[("c_water*m", "изменение температуры не учтено",
                             "the temperature change was ignored"),
                            ("c_water*dt", "масса не учтена", "the mass was ignored"),
                            ("m*dt*1000", "вместо теплоёмкости взято 1000",
                             "the specific heat was replaced by 1000"),
                            ("c_water*m/dt", "Δt поделено вместо умножения",
                             "divided by Δt instead of multiplying")])


def a8_coulomb(year, p):
    """Электростатика: закон Кулона."""
    return _a(year, 8, "electrostatics", 3,
              "Два точечных заряда {q1} мкКл и {q2} мкКл находятся в вакууме на "
              "расстоянии {r} м. Найдите силу их взаимодействия. "
              "k = {k_coulomb}.",
              "Two point charges of {q1} µC and {q2} µC are {r} m apart in vacuum. "
              "Find the force between them. k = {k_coulomb}.",
              tags=("закон Кулона",), formula="F = k·q₁·q₂/r²",
              model="F = k_coulomb*q1*q2/r^2",
              vars={"F": "kg·m/s^2", "q1": "A·s", "q2": "A·s", "r": "m",
                    "k_coulomb": "kg·m^3/(s^4·A^2)"},
              constants={"k_coulomb": "Н·м^2/Кл^2"},
              data={"q1": (str(p["charge_q1"]), "мкКл"), "q2": (str(p["charge_q2"]), "мкКл"),
                    "r": (str(p["charge_r"]), "м")},
              ask="F", unit="Н", rounding=2,
              wrong_models=[("k_coulomb*q1*q2/r", "расстояние не возведено в квадрат",
                             "the distance was not squared"),
                            ("k_coulomb*q1*q2", "расстояние не учтено",
                             "the distance was ignored"),
                            ("k_coulomb*(q1+q2)/r^2", "заряды сложены вместо умножения",
                             "the charges were added instead of multiplied"),
                            ("k_coulomb*q1*q2/r^2/2", "лишний множитель ½",
                             "an extra factor ½")])


def a9_ohm(year, p):
    """Постоянный ток: закон Ома."""
    return _a(year, 9, "current", 1,
              "Напряжение на резисторе {U} В, его сопротивление {R} Ом. "
              "Найдите силу тока.",
              "The voltage across a resistor is {U} V and its resistance is {R} Ω. "
              "Find the current.",
              tags=("закон Ома",), formula="I = U/R",
              model="I = U/R",
              vars={"I": "A", "U": "kg·m^2/(s^3·A)", "R": "kg·m^2/(s^3·A^2)"},
              data={"U": (str(p["lamp_u"]), "В"), "R": (str(p["res_r1"] * 10), "Ом")},
              ask="I", unit="А", rounding=1,
              wrong_models=[("U*R", "умножение вместо деления",
                             "multiplied instead of dividing"),
                            ("R/U", "деление перевёрнуто", "the division was inverted"),
                            ("U/R/1000", "лишний множитель 1000",
                             "an extra factor of 1000"),
                            ("U/(2*R)", "лишний множитель ½ в знаменателе",
                             "an extra factor ½ in the denominator")])


def a10_optics(year, p):
    """Оптика: оптическая сила линзы."""
    return _a(year, 10, "optics", 2,
              "Собирающая линза даёт изображение предмета, стоящего на расстоянии {d} м, "
              "на расстоянии {f} м от линзы. Найдите оптическую силу линзы.",
              "A converging lens forms an image at {f} m for an object {d} m away. "
              "Find the optical power of the lens.",
              tags=("оптическая сила",), formula="D = 1/d + 1/f",
              model="D = 1/d + 1/f", vars={"D": "1/m", "d": "m", "f": "m"},
              data={"d": (str(p["optic_d"]), "м"), "f": (str(p["optic_f"]), "м")},
              ask="D", unit="дптр", rounding=2,
              wrong_models=[("d + f", "расстояния сложены без обращения",
                             "the distances were added without taking reciprocals"),
                            ("1/(d + f)", "обращение взято от суммы",
                             "the reciprocal was taken of the sum"),
                            ("1/d - 1/f", "минус вместо плюса",
                             "a minus sign was used instead of a plus"),
                            ("d*f", "расстояния перемножены",
                             "the distances were multiplied")])


# --------------------------------------------------------------------------- #
#  Часть B — 20 заданий
# --------------------------------------------------------------------------- #

def b1_speed(year, p):
    return _b(year, 1, "kinematics", 2,
              "Автомобиль движется со скоростью {v0} м/с и разгоняется с ускорением "
              "{a} м/с² в течение {t} с. Какова его скорость в конце разгона?",
              "A car moves at {v0} m/s and accelerates at {a} m/s² for {t} s. "
              "What is its speed at the end?",
              tags=("равноускоренное движение",), formula="v = v₀ + a·t",
              model="v = v0 + a*t",
              vars={"v": "m/s", "v0": "m/s", "a": "m/s^2", "t": "s"},
              data={"v0": (str(p["v0"]), "м/с"), "a": (str(p["accel"]), "м/с^2"),
                    "t": (str(p["accel_t"]), "с")},
              ask="v", unit="м/с", rounding=1)


def b2_average(year, p):
    return _b(year, 2, "kinematics", 3,
              "Первый участок пути {s1} км машина прошла за {t1} ч, второй участок "
              "{s2} км — за {t2} ч. Найдите среднюю скорость на всём пути.",
              "A car covered the first {s1} km in {t1} h and the second {s2} km in "
              "{t2} h. Find the average speed over the whole trip.",
              tags=("средняя скорость",), formula="vср = (s₁ + s₂)/(t₁ + t₂)",
              model="v = (s1 + s2)/(t1 + t2)",
              vars={"v": "m/s", "s1": "m", "s2": "m", "t1": "s", "t2": "s"},
              data={"s1": (str(p["avg_s1"]), "км"), "t1": (str(p["avg_t1"]), "ч"),
                    "s2": (str(p["avg_s2"]), "км"), "t2": (str(p["avg_t2"]), "ч")},
              ask="v", unit="км/ч", rounding=2)


def b3_newton(year, p):
    return _b(year, 3, "dynamics", 2,
              "На тело массой {m} кг действует равнодействующая сила {F} Н. "
              "Найдите ускорение тела.",
              "A net force of {F} N acts on a body of {m} kg. Find its acceleration.",
              tags=("второй закон Ньютона",), formula="a = F/m",
              model="a = F/m", vars={"a": "m/s^2", "F": "kg·m/s^2", "m": "kg"},
              data={"F": (str(p["force"]), "Н"), "m": (str(p["mass"]), "кг")},
              ask="a", unit="м/с^2", rounding=2)


def b4_hooke(year, p):
    return _b(year, 4, "dynamics", 2,
              "Пружина жёсткостью {k} Н/м растянута на {x} м. Найдите силу упругости.",
              "A spring of stiffness {k} N/m is stretched by {x} m. "
              "Find the elastic force.",
              tags=("сила упругости",), formula="F = k·x (в пределах упругости)",
              model="F = k*x", vars={"F": "kg·m/s^2", "k": "kg/s^2", "x": "m"},
              data={"k": (str(p["spring_k"]), "Н/м"), "x": (str(p["spring_x"]), "м")},
              ask="F", unit="Н", rounding=1)


def b5_weight(year, p):
    return _b(year, 5, "dynamics", 1,
              "Найдите силу тяжести, действующую на тело массой {m} кг. g = {g}.",
              "Find the force of gravity acting on a body of {m} kg. g = {g}.",
              tags=("сила тяжести и вес",), formula="F = m·g",
              model="F = m*g", vars={"F": "kg·m/s^2", "m": "kg", "g": "m/s^2"},
              constants={"g": G_UNIT}, data={"m": (str(p["weight_m"]), "кг")},
              ask="F", unit="Н", rounding=1)


def b6_work(year, p):
    return _b(year, 6, "workenergy", 1,
              "Сила {F} Н направлена вдоль перемещения {s} м. Найдите работу этой силы.",
              "A force of {F} N acts along a displacement of {s} m. Find the work done.",
              tags=("работа и мощность",), formula="A = F·s (cos α = 1)",
              model="A = F*s", vars={"A": "kg·m^2/s^2", "F": "kg·m/s^2", "s": "m"},
              data={"F": (str(p["work_f"]), "Н"), "s": (str(p["work_s"]), "м")},
              ask="A", unit="Дж", rounding=0)


def b7_potential(year, p):
    return _b(year, 7, "workenergy", 2,
              "Тело массой {m} кг подняли на высоту {h} м. Какой потенциальной "
              "энергией оно обладает? g = {g}.",
              "A body of {m} kg was lifted to a height of {h} m. What is its potential "
              "energy? Take g = {g}.",
              tags=("закон сохранения энергии",), formula="Eп = m·g·h",
              model="E = m*g*h",
              vars={"E": "kg·m^2/s^2", "m": "kg", "h": "m", "g": "m/s^2"},
              constants={"g": G_UNIT},
              data={"m": (str(p["pe_m"]), "кг"), "h": (str(p["pe_h"]), "м")},
              ask="E", unit="Дж", rounding=1)


def b8_momentum(year, p):
    return _b(year, 8, "workenergy", 2,
              "Найдите импульс тела массой {m} кг, движущегося со скоростью {v} м/с.",
              "Find the momentum of a body of {m} kg moving at {v} m/s.",
              tags=("импульс и закон сохранения",), formula="p = m·v",
              model="p = m*v", vars={"p": "kg·m/s", "m": "kg", "v": "m/s"},
              data={"m": (str(p["mom_m"]), "кг"), "v": (str(p["mom_v"]), "м/с")},
              ask="p", unit="кг·м/с", rounding=0)


def b9_archimedes(year, p):
    return _b(year, 9, "statics", 2,
              "Тело объёмом {V} м³ полностью погружено в воду. Плотность воды "
              "ρ = {rho_water}, g = {g}. Найдите силу Архимеда.",
              "A body of volume {V} m³ is fully submerged in water. Water density is "
              "ρ = {rho_water}, g = {g}. Find the buoyant force.",
              tags=("сила Архимеда",), formula="F = ρ·V·g",
              model="F = rho_water*V*g",
              vars={"F": "kg·m/s^2", "V": "m^3", "rho_water": "kg/m^3", "g": "m/s^2"},
              constants={"rho_water": "кг/м^3", "g": G_UNIT},
              data={"V": (str(p["arch_v"]), "м^3")}, ask="F", unit="Н", rounding=2)


def b10_liquid(year, p):
    return _b(year, 10, "statics", 2,
              "Определите давление воды на глубине {h} м без учёта атмосферного "
              "давления. ρ = {rho_water}, g = {g}.",
              "Find the water pressure at a depth of {h} m, atmospheric pressure "
              "excluded. ρ = {rho_water}, g = {g}.",
              tags=("давление",), formula="p = ρ·g·h",
              model="p = rho_water*g*h",
              vars={"p": "kg/(m·s^2)", "h": "m", "rho_water": "kg/m^3", "g": "m/s^2"},
              constants={"rho_water": "кг/м^3", "g": G_UNIT},
              data={"h": (str(p["hydro_h"]), "м")}, ask="p", unit="кПа", rounding=2)


def b11_gas_law(year, p):
    return _b(year, 11, "molecular", 2,
              "При постоянном давлении газ занимает объём {V1} л при температуре "
              "{T1} К. Каким станет объём при {T2} К?",
              "At constant pressure a gas occupies {V1} l at {T1} K. What volume will "
              "it take at {T2} K?",
              tags=("изопроцессы",), formula="V₁/T₁ = V₂/T₂ (p = const, T в кельвинах)",
              model="V2 = V1*T2/T1",
              vars={"V2": "m^3", "V1": "m^3", "T1": "K", "T2": "K"},
              data={"V1": (str(p["gas_v1"]), "л"), "T1": (str(p["gas_t1"]), "К"),
                    "T2": (str(p["gas_t2"]), "К")},
              ask="V2", unit="л", rounding=3)


def b12_amount(year, p):
    return _b(year, 12, "molecular", 1,
              "Найдите количество вещества в {m} г газа с молярной массой {M} г/моль.",
              "Find the amount of substance in {m} g of a gas with molar mass {M} g/mol.",
              tags=("количество вещества",), formula="ν = m/M",
              model="nu = m/M", vars={"nu": "mol", "m": "kg", "M": "kg/mol"},
              data={"m": (str(p["mol_m"]), "г"), "M": (str(p["mol_mass"]), "г/моль")},
              ask="nu", unit="моль", rounding=0)


def b13_heat_capacity(year, p):
    return _b(year, 13, "thermo", 2,
              "Воду массой {m} кг нагрели на {dt} К. Удельная теплоёмкость воды "
              "c = {c_water}. Сколько теплоты потребовалось?",
              "Water of mass {m} kg was heated by {dt} K. The specific heat capacity is "
              "c = {c_water}. How much heat was needed?",
              tags=("теплота и теплоёмкость",), formula="Q = c·m·Δt",
              model="Q = c_water*m*dt",
              vars={"Q": "kg·m^2/s^2", "c_water": "m^2/(s^2·K)", "m": "kg", "dt": "K"},
              constants={"c_water": "Дж/(кг·К)"},
              data={"m": (str(p["heat_m"]), "кг"), "dt": (str(p["heat_dt"]), "К")},
              ask="Q", unit="кДж", rounding=2)


def b14_latent(year, p):
    return _b(year, 14, "thermo", 2,
              "Сколько теплоты нужно, чтобы расплавить {m} кг льда при 0 °C? "
              "Удельная теплота плавления льда λ = {L_ice}.",
              "How much heat melts {m} kg of ice at 0 °C? The specific latent heat of "
              "melting is λ = {L_ice}.",
              tags=("удельная теплота",), formula="Q = λ·m",
              model="Q = L_ice*m",
              vars={"Q": "kg·m^2/s^2", "L_ice": "m^2/s^2", "m": "kg"},
              constants={"L_ice": "Дж/кг"},
              data={"m": (str(p["latent_m"]), "кг")}, ask="Q", unit="кДж", rounding=1)


def b15_coulomb(year, p):
    return _b(year, 15, "electrostatics", 3,
              "Два заряда {q1} мкКл и {q2} мкКл находятся в вакууме на расстоянии "
              "{r} м. Найдите силу взаимодействия. k = {k_coulomb}.",
              "Two charges of {q1} µC and {q2} µC in vacuum are {r} m apart. Find the "
              "force between them. k = {k_coulomb}.",
              tags=("закон Кулона",), formula="F = k·q₁·q₂/r²",
              model="F = k_coulomb*q1*q2/r^2",
              vars={"F": "kg·m/s^2", "q1": "A·s", "q2": "A·s", "r": "m",
                    "k_coulomb": "kg·m^3/(s^4·A^2)"},
              constants={"k_coulomb": "Н·м^2/Кл^2"},
              data={"q1": (str(p["charge_q1"]), "мкКл"), "q2": (str(p["charge_q2"]), "мкКл"),
                    "r": (str(p["charge_r"]), "м")},
              ask="F", unit="Н", rounding=2)


def b16_series(year, p):
    return _b(year, 16, "current", 2,
              "Резисторы {R1} Ом и {R2} Ом соединены последовательно и подключены к "
              "{U} В. Найдите силу тока в цепи.",
              "Resistors {R1} Ω and {R2} Ω are in series across {U} V. Find the current.",
              tags=("последовательное соединение",), formula="I = U/(R₁ + R₂)",
              model="I = U/(R1+R2)",
              vars={"I": "A", "U": "kg·m^2/(s^3·A)", "R1": "kg·m^2/(s^3·A^2)",
                    "R2": "kg·m^2/(s^3·A^2)"},
              data={"R1": (str(p["res_r1"]), "Ом"), "R2": (str(p["res_r2"]), "Ом"),
                    "U": (str(p["volt"]), "В")},
              ask="I", unit="А", rounding=2)


def b17_power(year, p):
    return _b(year, 17, "current", 2,
              "Найдите мощность тока в резисторе сопротивлением {R} Ом при напряжении "
              "{U} В.",
              "Find the power dissipated in a {R} Ω resistor at {U} V.",
              tags=("работа тока",), formula="P = U²/R",
              model="P = U^2/R",
              vars={"P": "kg·m^2/s^3", "U": "kg·m^2/(s^3·A)", "R": "kg·m^2/(s^3·A^2)"},
              data={"R": (str(p["lamp_r"]), "Ом"), "U": (str(p["lamp_u"]), "В")},
              ask="P", unit="Вт", rounding=1)


def b18_ampere(year, p):
    return _b(year, 18, "magnetism", 2,
              "Проводник длиной {l} м с током {I} А находится в магнитном поле с "
              "индукцией {B} Тл. Ток перпендикулярен полю. Найдите силу Ампера.",
              "A conductor of length {l} m carrying {I} A is placed in a magnetic field "
              "of {B} T. The current is perpendicular to the field. Find the Ampere force.",
              tags=("сила Ампера",), formula="F = B·I·l (sin α = 1)",
              model="F = B*I*l",
              vars={"F": "kg·m/s^2", "B": "kg/(s^2·A)", "I": "A", "l": "m"},
              data={"B": (str(p["field_b"]), "Тл"), "I": (str(p["field_i"]), "А"),
                    "l": (str(p["field_l"]), "м")},
              ask="F", unit="Н", rounding=2)


def b19_wave(year, p):
    return _b(year, 19, "oscillations", 2,
              "Волна распространяется со скоростью {v} м/с, период колебаний частиц "
              "{T} с. Найдите длину волны.",
              "A wave travels at {v} m/s; the period of the oscillations is {T} s. "
              "Find the wavelength.",
              tags=("длина волны",), formula="λ = v·T",
              model="lam = v*T", vars={"lam": "m", "v": "m/s", "T": "s"},
              data={"v": (str(p["wave_v"]), "м/с"), "T": (str(p["wave_t"]), "с")},
              ask="lam", unit="м", rounding=3)


def b20_photon(year, p):
    return _b(year, 20, "quantum", 3,
              "Найдите энергию фотона с частотой {nu} Гц. Постоянная Планка "
              "h = {h}.",
              "Find the energy of a photon with frequency {nu} Hz. Planck's constant is "
              "h = {h}.",
              tags=("фотоэффект",), formula="E = h·ν",
              model="E = h*nu", vars={"E": "kg·m^2/s^2", "nu": "1/s", "h": "kg·m^2/s"},
              constants={"h": "Дж·с"},
              data={"nu": (str(p["photon_nu"]) + "e14", "Гц")}, ask="E", unit="Дж",
              tolerance={"kind": "relative", "value": "0.01"})


PART_A = [a1_units, a2_free_fall, a3_friction, a4_kinetic, a5_hydro, a6_amount,
          a7_heat, a8_coulomb, a9_ohm, a10_optics]
PART_B = [b1_speed, b2_average, b3_newton, b4_hooke, b5_weight, b6_work, b7_potential,
          b8_momentum, b9_archimedes, b10_liquid, b11_gas_law, b12_amount,
          b13_heat_capacity, b14_latent, b15_coulomb, b16_series, b17_power, b18_ampere,
          b19_wave, b20_photon]


def build(year: int) -> list:
    """Собрать авторский вариант года: 10 заданий части A и 20 части B."""
    if year not in YEARS:
        raise PhysicsError(f"движок не собирает вариант {year}")
    p = params(year)
    tasks = [recipe(year, p) for recipe in PART_A] + [recipe(year, p) for recipe in PART_B]
    for task in tasks:
        task.verify()
    if len(tasks) != 30:
        raise PhysicsError(f"вариант {year}: собрано {len(tasks)} заданий вместо 30")
    return tasks


def self_check() -> int:
    """Проверить все рецепты во всех годах — то же, что делает сборка банка."""
    total = 0
    for year in YEARS:
        total += len(build(year))
    return total


__all__ = ["YEARS", "build", "params", "self_check", "PART_A", "PART_B", "SRC"]
