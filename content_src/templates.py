"""templates.py — генератор однотипных заданий («аналогичных примеров»).

Назначение
----------
1. Разбор ошибки: после неверного ответа приложение открывает конспект темы и
   предлагает похожее задание с другим числом — закрепить именно этот приём.
2. Режим тренировки: запас заданий не кончается, потому что числа разные.

Свойства
--------
* **Детерминированность.** Все числа берутся из ``random.Random(seed)`` при
  импорте, поэтому сборка воспроизводима: один и тот же банк байт в байт.
* **Физика, а не подстановка.** Каждое задание — это модель (``calc_task``) с
  размерностями и постоянными, а не готовый ответ: ядро считает ответ точно и
  само проверяет размерность, единицы, домены и разбор.
* **Покрытие.** По два генератора на каждую из 13 тем курса; сборка обязана
  видеть все темы (``tools/build_content.py`` падает, если тема не покрыта).
* **Границы модели называются.** Там, где ответ зависит от упрощения (потери,
  сопротивление воздуха, sin α = 1), это сказано в тексте задания.

Это авторские тренировочные задания, не материалы РИКЗ.
"""

from __future__ import annotations

import random

from kit import PhysicsError, calc_task
from quantities import CONVENTIONS
from variants import G_UNIT

SEED = 20261014
SRC = "авторское тренировочное задание (аналог) по физике; не материалы РИКЗ"

RNG = random.Random(SEED)


def _t(topic: str, number: int, difficulty: int, ru: str, en: str, tags, formula, **kw):
    return calc_task(id=f"phys-practice-{topic}-{number:02d}", year=0, part="B", n=1,
                     topic=topic, difficulty=difficulty, ru=ru, en=en, formula=formula,
                     tags=tags, src=SRC, **kw)


def _pick(values):
    return RNG.choice(values)


# --------------------------------------------------------------------------- #
#  1. Измерения и единицы / measurement and units
# --------------------------------------------------------------------------- #

def measurements_units():
    kmh = _pick([36, 54, 72, 90, 108, 144])
    return _t("measurements", 1, 1,
              "Переведите {V} км/ч в м/с.",
              "Convert {V} km/h to m/s.",
              ("перевод единиц",), "1 км/ч = 5/18 м/с",
              model="v = V", vars={"v": "m/s", "V": "m/s"},
              data={"V": (str(kmh), "км/ч")}, ask="v", unit="м/с", rounding=1)


def measurements_kwh():
    kwh = _pick([1, 2, 3, 5, 7.5])
    return _t("measurements", 2, 2,
              "Счётчик показал {W} кВт·ч. Выразите эту энергию в джоулях.",
              "The meter shows {W} kWh. Express this energy in joules.",
              ("приставки СИ",), "1 кВт·ч = 3,6·10⁶ Дж",
              model="E = W", vars={"E": "kg·m^2/s^2", "W": "kg·m^2/s^2"},
              data={"W": (str(kwh), "кВт·ч")}, ask="E", unit="Дж", rounding=0)


def measurements_scale():
    step = _pick([2, 5, 10])
    gaps = _pick([2, 4, 5])
    return _t("measurements", 3, 2,
              "Между подписями {a} В и {b} В на шкале вольтметра {n} промежутков. "
              "Найдите цену деления прибора.",
              "Between the marks {a} V and {b} V of a voltmeter scale there are {n} gaps. "
              "Find the scale division.",
              ("цена деления",), "c = (a₂ − a₁)/n",
              model="c = (b - a)/n",
              vars={"c": "kg·m^2/(s^3·A)", "a": "kg·m^2/(s^3·A)", "b": "kg·m^2/(s^3·A)",
                    "n": "1"},
              data={"a": (str(step), "В"), "b": (str(step * (gaps + 1)), "В"),
                    "n": (str(gaps), "1")},
              ask="c", unit="В", rounding=2)


# --------------------------------------------------------------------------- #
#  2. Кинематика / kinematics
# --------------------------------------------------------------------------- #

def kinematics_uniform():
    v = _pick([5, 8, 10, 12, 15, 20])
    t = _pick([4, 6, 8, 10, 12])
    return _t("kinematics", 1, 1,
              "Тело движется равномерно со скоростью {v} м/с в течение {t} с. "
              "Какой путь оно пройдёт?",
              "A body moves uniformly at {v} m/s for {t} s. What distance does it cover?",
              ("равноускоренное движение",), "s = v·t (равномерное движение)",
              model="s = v*t", vars={"s": "m", "v": "m/s", "t": "s"},
              data={"v": (str(v), "м/с"), "t": (str(t), "с")}, ask="s", unit="м",
              rounding=0)


def kinematics_accelerated():
    v0 = _pick([2, 4, 6])
    a = _pick([1, 2, 3])
    t = _pick([3, 4, 5])
    return _t("kinematics", 2, 2,
              "Автомобиль двигался со скоростью {v0} м/с и за {t} с увеличил её до "
              "{v1} м/с. Найдите ускорение.",
              "A car moving at {v0} m/s increased its speed to {v1} m/s in {t} s. "
              "Find the acceleration.",
              ("равноускоренное движение",), "a = (v − v₀)/t",
              model="a = (v1 - v0)/t",
              vars={"a": "m/s^2", "v0": "m/s", "v1": "m/s", "t": "s"},
              data={"v0": (str(v0), "м/с"), "v1": (str(v0 + a * t), "м/с"),
                    "t": (str(t), "с")},
              ask="a", unit="м/с^2", rounding=2)


def kinematics_average():
    s1, s2 = _pick([10, 15, 20]), _pick([20, 30, 40])
    t1, t2 = _pick([0.5, 1, 2]), _pick([1, 2, 3])
    return _t("kinematics", 3, 3,
              "Автомобиль проехал {s1} км за {t1} ч и {s2} км за {t2} ч. Найдите "
              "среднюю скорость на всём пути.",
              "A car covered {s1} km in {t1} h and {s2} km in {t2} h. Find the average "
              "speed over the whole trip.",
              ("средняя скорость",), "vср = (s₁ + s₂)/(t₁ + t₂)",
              model="v = (s1 + s2)/(t1 + t2)",
              vars={"v": "m/s", "s1": "m", "s2": "m", "t1": "s", "t2": "s"},
              data={"s1": (str(s1), "км"), "t1": (str(t1), "ч"),
                    "s2": (str(s2), "км"), "t2": (str(t2), "ч")},
              ask="v", unit="км/ч", rounding=2)


# --------------------------------------------------------------------------- #
#  3. Динамика / dynamics
# --------------------------------------------------------------------------- #

def dynamics_second_law():
    m = _pick([0.5, 1, 2, 4, 5])
    a = _pick([1, 2, 3, 4])
    return _t("dynamics", 1, 1,
              "На тело массой {m} кг действует равнодействующая сила {F} Н. "
              "Найдите ускорение.",
              "A net force of {F} N acts on a body of {m} kg. Find the acceleration.",
              ("второй закон Ньютона",), "a = F/m",
              model="a = F/m", vars={"a": "m/s^2", "F": "kg·m/s^2", "m": "kg"},
              data={"m": (str(m), "кг"), "F": (str(m * a), "Н")},
              ask="a", unit="м/с^2", rounding=2)


def dynamics_friction():
    m = _pick([2, 4, 5, 10])
    mu = _pick([0.1, 0.2, 0.25, 0.4])
    return _t("dynamics", 2, 2,
              "Брусок массой {m} кг равномерно скользит по горизонтальной поверхности. "
              "Коэффициент трения μ = {mu}, g = {g}. Найдите силу трения.",
              "A block of {m} kg slides at constant speed on a horizontal surface. The "
              "friction coefficient is μ = {mu}, g = {g}. Find the friction force.",
              ("сила трения",), "Fтр = μ·m·g",
              model="F = mu*m*g",
              vars={"F": "kg·m/s^2", "mu": "1", "m": "kg", "g": "m/s^2"},
              constants={"g": G_UNIT},
              data={"m": (str(m), "кг"), "mu": (str(mu), "1")}, ask="F", unit="Н",
              rounding=1)


def dynamics_hooke():
    k = _pick([100, 200, 250, 400, 500])
    x = _pick([0.01, 0.02, 0.04, 0.05])
    return _t("dynamics", 3, 2,
              "Пружина жёсткостью {k} Н/м сжата на {x} м. Найдите силу упругости.",
              "A spring of stiffness {k} N/m is compressed by {x} m. Find the elastic force.",
              ("сила упругости",), "F = k·x (в пределах упругости)",
              model="F = k*x", vars={"F": "kg·m/s^2", "k": "kg/s^2", "x": "m"},
              data={"k": (str(k), "Н/м"), "x": (str(x), "м")}, ask="F", unit="Н",
              rounding=1)


# --------------------------------------------------------------------------- #
#  4. Работа, энергия, импульс / work, energy, momentum
# --------------------------------------------------------------------------- #

def workenergy_work():
    f = _pick([5, 10, 20, 25, 40])
    s = _pick([2, 4, 5, 10])
    angle = _pick([0, 60, 90])
    model, cosine_en = {0: ("A = F*s", "1"),
                        60: ("A = F*s/2", "0.5"),
                        90: ("A = F*s*0", "0")}[angle]
    cosine_ru = cosine_en.replace(".", ",")
    return _t("workenergy", 1, 2,
              f"Сила {{F}} Н действует под углом {angle}° к перемещению {{s}} м. "
              f"Найдите работу силы. cos {angle}° = {cosine_ru}.",
              f"A force of {{F}} N acts at {angle}° to a displacement of {{s}} m. "
              f"Find the work. cos {angle}° = {cosine_en}.",
              ("работа и мощность",), "A = F·s·cos α",
              model=model, vars={"A": "kg·m^2/s^2", "F": "kg·m/s^2", "s": "m"},
              data={"F": (str(f), "Н"), "s": (str(s), "м")},
              ask="A", unit="Дж", rounding=0)


def workenergy_power():
    a = _pick([1200, 2400, 3600, 4800])
    t = _pick([10, 20, 30, 60])
    return _t("workenergy", 2, 2,
              "За {t} с совершена работа {A} Дж. Найдите среднюю мощность.",
              "A work of {A} J is done in {t} s. Find the average power.",
              ("работа и мощность",), "P = A/t",
              model="P = A/t", vars={"P": "kg·m^2/s^3", "A": "kg·m^2/s^2", "t": "s"},
              data={"A": (str(a), "Дж"), "t": (str(t), "с")}, ask="P", unit="Вт",
              rounding=1)


def workenergy_momentum():
    m = _pick([2, 3, 5, 8])
    v = _pick([3, 4, 6, 10])
    return _t("workenergy", 3, 1,
              "Тело массой {m} кг движется со скоростью {v} м/с. Найдите его импульс.",
              "A body of {m} kg moves at {v} m/s. Find its momentum.",
              ("импульс и закон сохранения",), "p = m·v",
              model="p = m*v", vars={"p": "kg·m/s", "m": "kg", "v": "m/s"},
              data={"m": (str(m), "кг"), "v": (str(v), "м/с")}, ask="p", unit="кг·м/с",
              rounding=0)


# --------------------------------------------------------------------------- #
#  5. Статика, давление, гидростатика / statics, pressure
# --------------------------------------------------------------------------- #

def statics_moment():
    f = _pick([10, 20, 30, 50])
    d = _pick([0.1, 0.2, 0.25, 0.5])
    return _t("statics", 1, 2,
              "К рычагу приложена сила {F} Н, плечо силы {d} м. Найдите момент силы "
              "относительно оси вращения.",
              "A force of {F} N is applied to a lever with an arm of {d} m. Find the "
              "moment of the force about the axis.",
              ("момент силы",), "M = F·d (плечо — перпендикулярное расстояние)",
              model="M = F*d", vars={"M": "kg·m^2/s^2", "F": "kg·m/s^2", "d": "m"},
              data={"F": (str(f), "Н"), "d": (str(d), "м")}, ask="M", unit="Н·м",
              rounding=1)


def statics_archimedes():
    v = _pick([0.001, 0.002, 0.005, 0.01])
    return _t("statics", 2, 2,
              "Тело объёмом {V} м³ полностью погружено в воду. ρ = {rho_water}, "
              "g = {g}. Найдите силу Архимеда.",
              "A body of volume {V} m³ is fully submerged in water. ρ = {rho_water}, "
              "g = {g}. Find the buoyant force.",
              ("сила Архимеда",), "F = ρ·V·g",
              model="F = rho_water*V*g",
              vars={"F": "kg·m/s^2", "V": "m^3", "rho_water": "kg/m^3", "g": "m/s^2"},
              constants={"rho_water": "кг/м^3", "g": G_UNIT},
              data={"V": (str(v), "м^3")}, ask="F", unit="Н", rounding=2)


def statics_pressure():
    s = _pick([0.01, 0.02, 0.05])
    f = _pick([100, 200, 500])
    return _t("statics", 3, 1,
              "На площадь {S} м² действует сила {F} Н. Найдите давление.",
              "A force of {F} N acts on an area of {S} m². Find the pressure.",
              ("давление",), "p = F/S",
              model="p = F/S", vars={"p": "kg/(m·s^2)", "F": "kg·m/s^2", "S": "m^2"},
              data={"F": (str(f), "Н"), "S": (str(s), "м^2")}, ask="p", unit="кПа",
              rounding=1)


# --------------------------------------------------------------------------- #
#  6. Молекулярная физика / molecular physics
# --------------------------------------------------------------------------- #

def molecular_amount():
    m = _pick([44, 88, 132, 176, 220])
    return _t("molecular", 1, 1,
              "Найдите количество вещества в {m} г углекислого газа CO₂ "
              "(молярная масса {M} г/моль).",
              "Find the amount of substance in {m} g of CO₂ (molar mass {M} g/mol).",
              ("количество вещества",), "ν = m/M",
              model="nu = m/M", vars={"nu": "mol", "m": "kg", "M": "kg/mol"},
              data={"m": (str(m), "г"), "M": ("44", "г/моль")}, ask="nu", unit="моль",
              rounding=0)


def molecular_isoprocess():
    v1 = _pick([2, 3, 4, 5])
    t1 = _pick([250, 300, 350])
    t2 = _pick([400, 500, 600])
    return _t("molecular", 2, 3,
              "При постоянном давлении газ занимает объём {V1} л при {T1} К. "
              "Какой объём он займёт при {T2} К?",
              "At constant pressure a gas occupies {V1} l at {T1} K. What volume will "
              "it occupy at {T2} K?",
              ("изопроцессы",), "V₁/T₁ = V₂/T₂ (p = const, T в кельвинах)",
              model="V2 = V1*T2/T1",
              vars={"V2": "m^3", "V1": "m^3", "T1": "K", "T2": "K"},
              data={"V1": (str(v1), "л"), "T1": (str(t1), "К"), "T2": (str(t2), "К")},
              ask="V2", unit="л", rounding=3)


def molecular_ideal_gas():
    nu = _pick([1, 2, 3])
    t = _pick([300, 320, 400])
    return _t("molecular", 3, 3,
              "Идеальный газ количеством {nu} моль находится при температуре {T} К. "
              "R = {R}. Найдите давление, если объём сосуда {V} л "
              "(газ считаем идеальным).",
              "An ideal gas of {nu} mol is at {T} K. R = {R}. Find the pressure if the "
              "vessel volume is {V} l (ideal-gas model).",
              ("уравнение состояния газа",), "pV = νRT",
              model="p = nu*R*T/V",
              vars={"p": "kg/(m·s^2)", "nu": "mol", "R": "kg·m^2/(s^2·K·mol)",
                    "T": "K", "V": "m^3"},
              constants={"R": "Дж/(моль·К)"},
              data={"nu": (str(nu), "моль"), "T": (str(t), "К"),
                    "V": (str(_pick([20, 25, 40, 50])), "л")},
              ask="p", unit="кПа", rounding=1)


# --------------------------------------------------------------------------- #
#  7. Теплота и термодинамика / heat and thermodynamics
# --------------------------------------------------------------------------- #

def thermo_heat():
    m = _pick([0.5, 1, 2, 3])
    dt = _pick([10, 20, 40, 50])
    return _t("thermo", 1, 2,
              "Сколько теплоты нужно, чтобы нагреть {m} кг воды на {dt} К? "
              "Удельная теплоёмкость воды c = {c_water}.",
              "How much heat warms {m} kg of water by {dt} K? The specific heat "
              "capacity is c = {c_water}.",
              ("теплота и теплоёмкость",), "Q = c·m·Δt",
              model="Q = c_water*m*dt",
              vars={"Q": "kg·m^2/s^2", "c_water": "m^2/(s^2·K)", "m": "kg", "dt": "K"},
              constants={"c_water": "Дж/(кг·К)"},
              data={"m": (str(m), "кг"), "dt": (str(dt), "К")}, ask="Q", unit="кДж",
              rounding=1)


def thermo_latent():
    m = _pick([0.5, 1, 2, 4])
    return _t("thermo", 2, 2,
              "Сколько теплоты нужно, чтобы расплавить {m} кг льда при 0 °C? "
              "λ = {L_ice}.",
              "How much heat melts {m} kg of ice at 0 °C? λ = {L_ice}.",
              ("удельная теплота",), "Q = λ·m",
              model="Q = L_ice*m",
              vars={"Q": "kg·m^2/s^2", "L_ice": "m^2/s^2", "m": "kg"},
              constants={"L_ice": "Дж/кг"},
              data={"m": (str(m), "кг")}, ask="Q", unit="МДж", rounding=2)


def thermo_efficiency():
    q = _pick([0.4, 0.5, 0.6, 0.8])
    return _t("thermo", 3, 3,
              "Нагреватель передал рабочему телу {Q} кДж, полезная работа {A} кДж. "
              "Найдите КПД теплового двигателя в процентах.",
              "The heater supplied {Q} kJ and useful work was {A} kJ. Find the "
              "efficiency of the heat engine in per cent.",
              ("КПД",), "η = Aполез/Qзатр, в процентах умножить на 100",
              model="eta = A*100/Q",
              vars={"eta": "1", "A": "kg·m^2/s^2", "Q": "kg·m^2/s^2"},
              data={"A": (str(q), "кДж"), "Q": ("2", "кДж")}, ask="eta", unit="1",
              rounding=0)


# --------------------------------------------------------------------------- #
#  8. Электростатика / electrostatics
# --------------------------------------------------------------------------- #

def electrostatics_coulomb():
    q = _pick([1, 2, 3, 5])
    r = _pick([0.01, 0.02, 0.05])
    return _t("electrostatics", 1, 3,
              "Два заряда {q1} мкКл и {q2} мкКл находятся на расстоянии {r} м "
              "в вакууме. k = {k_coulomb}. Найдите силу их взаимодействия "
              "(модуль силы).",
              "Two charges of {q1} µC and {q2} µC are {r} m apart in vacuum. "
              "k = {k_coulomb}. Find the magnitude of the force between them.",
              ("закон Кулона",), "F = k·q₁·q₂/r²",
              model="F = k_coulomb*q1*q2/r^2",
              vars={"F": "kg·m/s^2", "q1": "A·s", "q2": "A·s", "r": "m",
                    "k_coulomb": "kg·m^3/(s^4·A^2)"},
              constants={"k_coulomb": "Н·м^2/Кл^2"},
              data={"q1": (str(q), "мкКл"), "q2": (str(-q), "мкКл"), "r": (str(r), "м")},
              ask="F", unit="Н", rounding=1)


def electrostatics_field():
    q = _pick([1, 2, 4, 5])
    f = _pick([0.02, 0.05, 0.1])
    return _t("electrostatics", 2, 2,
              "На заряд {q} мкКл действует сила {F} Н. Найдите напряжённость поля.",
              "A force of {F} N acts on a charge of {q} µC. Find the field strength.",
              ("напряжённость и потенциал",), "E = F/q",
              model="E = F/q", vars={"E": "kg·m/(s^3·A)", "F": "kg·m/s^2", "q": "A·s"},
              data={"q": (str(q), "мкКл"), "F": (str(f), "Н")}, ask="E", unit="кН/Кл",
              rounding=1)


def electrostatics_potential():
    q = _pick([2, 4, 10])
    a = _pick([0.02, 0.1, 0.4])
    return _t("electrostatics", 3, 2,
              "При переносе заряда {q} мКл электрическое поле совершило работу {A} Дж. "
              "Найдите напряжение между точками.",
              "Moving a charge of {q} mC, the field did a work of {A} J. Find the "
              "voltage between the points.",
              ("напряжённость и потенциал",), "U = A/q",
              model="U = A/q", vars={"U": "kg·m^2/(s^3·A)", "A": "kg·m^2/s^2", "q": "A·s"},
              data={"q": (str(q), "мКл"), "A": (str(a), "Дж")}, ask="U", unit="В",
              rounding=2)


# --------------------------------------------------------------------------- #
#  9. Постоянный ток / direct current
# --------------------------------------------------------------------------- #

def current_ohm():
    u = _pick([6, 12, 24, 36])
    r = _pick([2, 3, 4, 6])
    return _t("current", 1, 1,
              "Напряжение на резисторе {U} В, сопротивление {R} Ом. Найдите силу тока.",
              "The voltage across a {R} Ω resistor is {U} V. Find the current.",
              ("закон Ома",), "I = U/R",
              model="I = U/R",
              vars={"I": "A", "U": "kg·m^2/(s^3·A)", "R": "kg·m^2/(s^3·A^2)"},
              data={"U": (str(u), "В"), "R": (str(r), "Ом")}, ask="I", unit="А",
              rounding=2)


def current_parallel():
    r1, r2 = _pick([2, 3, 4, 6]), _pick([6, 8, 12])
    return _t("current", 2, 3,
              "Два резистора {R1} Ом и {R2} Ом соединены параллельно. Найдите общее "
              "сопротивление участка.",
              "Two resistors {R1} Ω and {R2} Ω are connected in parallel. Find the "
              "total resistance.",
              ("параллельное соединение",), "R = R₁R₂/(R₁ + R₂)",
              model="R = R1*R2/(R1+R2)",
              vars={"R": "kg·m^2/(s^3·A^2)", "R1": "kg·m^2/(s^3·A^2)",
                    "R2": "kg·m^2/(s^3·A^2)"},
              data={"R1": (str(r1), "Ом"), "R2": (str(r2), "Ом")}, ask="R", unit="Ом",
              rounding=2)


def current_power():
    u = _pick([12, 24, 36, 48])
    r = _pick([4, 6, 8, 12])
    return _t("current", 3, 2,
              "Найдите мощность тока в резисторе сопротивлением {R} Ом при напряжении "
              "{U} В.",
              "Find the power in a {R} Ω resistor at {U} V.",
              ("работа тока",), "P = U²/R",
              model="P = U^2/R",
              vars={"P": "kg·m^2/s^3", "U": "kg·m^2/(s^3·A)", "R": "kg·m^2/(s^3·A^2)"},
              data={"U": (str(u), "В"), "R": (str(r), "Ом")}, ask="P", unit="Вт",
              rounding=1)


# --------------------------------------------------------------------------- #
#  10. Магнитное поле / magnetism
# --------------------------------------------------------------------------- #

def magnetism_ampere():
    b = _pick([0.1, 0.2, 0.4])
    i = _pick([2, 4, 5, 10])
    l = _pick([0.1, 0.2, 0.5])
    return _t("magnetism", 1, 2,
              "Проводник длиной {l} м с током {I} А расположен перпендикулярно "
              "магнитному полю с индукцией {B} Тл. Найдите силу Ампера.",
              "A conductor of length {l} m with current {I} A is perpendicular to a "
              "magnetic field of {B} T. Find the Ampere force.",
              ("сила Ампера",), "F = B·I·l (sin α = 1)",
              model="F = B*I*l",
              vars={"F": "kg·m/s^2", "B": "kg/(s^2·A)", "I": "A", "l": "m"},
              data={"B": (str(b), "Тл"), "I": (str(i), "А"), "l": (str(l), "м")},
              ask="F", unit="Н", rounding=2)


def magnetism_lorentz():
    q = _pick([1, 2, 4])
    v = _pick([200, 400, 500])
    b = _pick([0.01, 0.02, 0.05])
    return _t("magnetism", 2, 3,
              "Заряд {q} мкКл движется со скоростью {v} м/с перпендикулярно "
              "магнитному полю с индукцией {B} Тл. Найдите силу Лоренца.",
              "A charge of {q} µC moves at {v} m/s perpendicular to a magnetic field "
              "of {B} T. Find the Lorentz force.",
              ("сила Лоренца",), "F = |q|·v·B (sin α = 1)",
              model="F = q*v*B",
              vars={"F": "kg·m/s^2", "q": "A·s", "v": "m/s", "B": "kg/(s^2·A)"},
              data={"q": (str(q), "мкКл"), "v": (str(v), "м/с"), "B": (str(b), "Тл")},
              ask="F", unit="мН", rounding=2)


def magnetism_induction():
    b = _pick([0.2, 0.5, 0.8])
    s = _pick([0.01, 0.02, 0.05])
    return _t("magnetism", 3, 2,
              "Контур площадью {S} м² находится в однородном магнитном поле с "
              "индукцией {B} Тл перпендикулярно линиям индукции. Найдите магнитный "
              "поток.",
              "A loop of area {S} m² lies in a uniform magnetic field of {B} T "
              "perpendicular to the field lines. Find the magnetic flux.",
              ("электромагнитная индукция",), "Φ = B·S (cos α = 1)",
              model="Phi = B*S",
              vars={"Phi": "kg·m^2/(s^2·A)", "B": "kg/(s^2·A)", "S": "m^2"},
              data={"B": (str(b), "Тл"), "S": (str(s), "м^2")}, ask="Phi", unit="Вб",
              rounding=3)


# --------------------------------------------------------------------------- #
#  11. Колебания, волны, звук / oscillations and waves
# --------------------------------------------------------------------------- #

def oscillations_period():
    n = _pick([10, 20, 25, 40])
    t = _pick([5, 10, 20, 40])
    return _t("oscillations", 1, 2,
              "Маятник совершил {N} колебаний за {t} с. Найдите период колебаний.",
              "A pendulum made {N} oscillations in {t} s. Find the period.",
              ("период и частота",), "T = t/N",
              model="T = t/N", vars={"T": "s", "t": "s", "N": "1"},
              data={"t": (str(t), "с"), "N": (str(n), "1")}, ask="T", unit="с",
              rounding=3)


def oscillations_frequency():
    n = _pick([20, 50, 100])
    t = _pick([4, 10, 20])
    return _t("oscillations", 2, 1,
              "За {t} с тело совершило {N} колебаний. Найдите частоту колебаний.",
              "In {t} s a body made {N} oscillations. Find the frequency.",
              ("период и частота",), "ν = N/t",
              model="f = N/t", vars={"f": "1/s", "t": "s", "N": "1"},
              data={"t": (str(t), "с"), "N": (str(n), "1")}, ask="f", unit="Гц",
              rounding=2)


def oscillations_wave():
    v = _pick([340, 1500, 300])
    f = _pick([20, 50, 100, 200])
    return _t("oscillations", 3, 2,
              "Звук распространяется в воздухе со скоростью {v} м/с. Частота "
              "колебаний {f} Гц. Найдите длину волны.",
              "Sound travels in air at {v} m/s. The frequency is {f} Hz. Find the "
              "wavelength.",
              ("звук",), "λ = v/ν",
              model="lam = v/f", vars={"lam": "m", "v": "m/s", "f": "1/s"},
              data={"v": (str(v), "м/с"), "f": (str(f), "Гц")}, ask="lam", unit="м",
              rounding=3)


# --------------------------------------------------------------------------- #
#  12. Оптика / optics
# --------------------------------------------------------------------------- #

def optics_power():
    f = _pick([0.1, 0.2, 0.25, 0.5])
    return _t("optics", 1, 2,
              "Фокусное расстояние линзы {F} м. Найдите её оптическую силу.",
              "The focal length of a lens is {F} m. Find its optical power.",
              ("оптическая сила",), "D = 1/F",
              model="D = 1/F", vars={"D": "1/m", "F": "m"},
              data={"F": (str(f), "м")}, ask="D", unit="дптр", rounding=2)


def optics_magnification():
    d = _pick([0.1, 0.2, 0.3])
    f = _pick([0.4, 0.6, 0.9])
    return _t("optics", 2, 3,
              "Предмет стоит на расстоянии {d} м от линзы, изображение получилось на "
              "расстоянии {f} м. Найдите линейное увеличение линзы.",
              "An object is {d} m from a lens and the image is {f} m away. Find the "
              "linear magnification.",
              ("формула тонкой линзы",), "Г = f/d",
              model="G = f/d", vars={"G": "1", "d": "m", "f": "m"},
              data={"d": (str(d), "м"), "f": (str(f), "м")}, ask="G", unit="1",
              rounding=2)


def optics_refraction():
    n = _pick([1.33, 1.5, 1.6, 2])
    return _t("optics", 3, 3,
              "Свет переходит из воздуха в среду с показателем преломления n = {n}. "
              "Найдите скорость света в этой среде. c = {c}.",
              "Light enters a medium with refractive index n = {n}. Find the speed of "
              "light in the medium. c = {c}.",
              ("преломление света",), "n = c/v → v = c/n",
              model="v = c/n", vars={"v": "m/s", "c": "m/s", "n": "1"},
              constants={"c": "м/с"}, data={"n": (str(n), "1")}, ask="v", unit="м/с",
              rounding=0)


# --------------------------------------------------------------------------- #
#  13. Квантовые явления / quantum phenomena
# --------------------------------------------------------------------------- #

def quantum_photon():
    nu = _pick([2, 3, 4, 5, 8])
    return _t("quantum", 1, 3,
              "Найдите энергию фотона с частотой {nu}·10¹⁴ Гц. h = {h}.",
              "Find the energy of a photon with frequency {nu}·10¹⁴ Hz. h = {h}.",
              ("фотоэффект",), "E = h·ν",
              model="E = h*nu",
              vars={"E": "kg·m^2/s^2", "nu": "1/s", "h": "kg·m^2/s"},
              constants={"h": "Дж·с"},
              data={"nu": (str(nu) + "e14", "Гц")}, ask="E", unit="Дж",
              tolerance={"kind": "relative", "value": "0.01"})


def quantum_work_function():
    nu = _pick([6, 8, 10])
    return _t("quantum", 2, 3,
              "Работа выхода электрона {A} эВ. Найдите красную границу фотоэффекта — "
              "частоту, при которой энергия фотона равна работе выхода. h = {h}, "
              "1 эВ = 1,6·10⁻¹⁹ Дж.",
              "The work function is {A} eV. Find the threshold frequency at which the "
              "photon energy equals the work function. h = {h}, 1 eV = 1.6·10⁻¹⁹ J.",
              ("фотоэффект",), "hν = Aвых",
              model="nu = A/h", vars={"nu": "1/s", "A": "kg·m^2/s^2", "h": "kg·m^2/s"},
              constants={"h": "Дж·с"},
              data={"A": (str(_pick([1.9, 2.5, 4.0])), "эВ")}, ask="nu", unit="Гц",
              tolerance={"kind": "relative", "value": "0.01"})


def quantum_decay():
    periods = _pick([1, 2, 3, 4])
    half_life = _pick([2, 4, 5, 10])
    return _t("quantum", 3, 3,
              "Период полураспада {T} суток. Какая доля ядер распадётся за {t} суток?",
              "The half-life is {T} days. What fraction of the nuclei decays in {t} days?",
              ("радиоактивность",), "N = N₀·2^(−t/T); распалось 1 − 2^(−t/T)",
              model=f"f = 1 - 2^({-periods})",
              vars={"f": "1", "t": "s", "T": "s"},
              data={"t": (str(half_life * periods), "сут"), "T": (str(half_life), "сут")},
              ask="f", unit="1", rounding=3)


GENERATORS = (
    measurements_units, measurements_kwh, measurements_scale,
    kinematics_uniform, kinematics_accelerated, kinematics_average,
    dynamics_second_law, dynamics_friction, dynamics_hooke,
    workenergy_work, workenergy_power, workenergy_momentum,
    statics_moment, statics_archimedes, statics_pressure,
    molecular_amount, molecular_isoprocess, molecular_ideal_gas,
    thermo_heat, thermo_latent, thermo_efficiency,
    electrostatics_coulomb, electrostatics_field, electrostatics_potential,
    current_ohm, current_parallel, current_power,
    magnetism_ampere, magnetism_lorentz, magnetism_induction,
    oscillations_period, oscillations_frequency, oscillations_wave,
    optics_power, optics_magnification, optics_refraction,
    quantum_photon, quantum_work_function, quantum_decay,
)

#: тема → сколько заданий-аналогов её покрывают (проверяется сборкой)
def topics_covered() -> set[str]:
    return {generator().topic for generator in GENERATORS}


def generate() -> list:
    """Все аналогичные задания (детерминированно, в порядке объявления)."""
    tasks = [generator() for generator in GENERATORS]
    seen = set()
    for task in tasks:
        if task.id in seen:
            raise PhysicsError(f"дубликат идентификатора задания-аналога: {task.id}")
        seen.add(task.id)
        task.verify()
    missing = {task.topic for task in tasks}
    if len(missing) != 13:
        raise PhysicsError("генератор аналогов покрывает не все 13 тем: "
                           + ", ".join(sorted(missing)))
    return tasks


__all__ = ["GENERATORS", "generate", "topics_covered", "SEED", "SRC"]
