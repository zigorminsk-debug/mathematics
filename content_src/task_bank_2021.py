"""Авторский тренировочный вариант 2021 года (10 заданий части A + 20 части B).

Это НЕ официальные задания РИКЗ: вариант составлен по программе и формату ЦТ по
физике (проверено: 10 заданий части A, 20 заданий части B, 210 минут). Все ответы
выводятся из физической модели точной арифметикой, данные каждого задания обязаны
встречаться в обоих текстах, а единицы значений — проходить проверку размерности.
"""

from __future__ import annotations

from kit import calc_choice_task, calc_task

YEAR = 2021
SRC = "авторское тренировочное задание по мотивам ЦТ 2021; не материалы РИКЗ"

#: Задание b20: 15 суток при периоде полураспада 5 суток — ровно 3 периода.
#: Число периодов вычисляется здесь, а не «на глаз»: показатель степени в модели
#: обязан совпадать с отношением данных, поэтому делимость проверяется кодом.
_DECAY_T, _DECAY_HALF_LIFE = 15, 5
assert _DECAY_T % _DECAY_HALF_LIFE == 0, "число периодов полураспада должно быть целым"
_DECAY_PERIODS = _DECAY_T // _DECAY_HALF_LIFE


def _a(n, topic, difficulty, ru, en, **kw):
    return calc_choice_task(id=f"phys-2021-a{n}", year=YEAR, n=n, topic=topic,
                            difficulty=difficulty, ru=ru, en=en, src=SRC, **kw)


def _b(n, topic, difficulty, ru, en, **kw):
    return calc_task(id=f"phys-2021-b{n}", year=YEAR, part="B", n=n, topic=topic,
                     difficulty=difficulty, ru=ru, en=en, src=SRC, **kw)


def tasks():
    return [
        # ------------------------------ часть A ------------------------------ #
        _a(1, "measurements", 1,
           "Автомобиль едет по трассе со скоростью {v0} км/ч. Выразите эту скорость в м/с.",
           "A car travels at {v0} km/h. Express this speed in m/s.",
           model="v = v0 * 5 / 18", vars={"v": "m/s", "v0": "m/s"},
           data={"v0": ("72", "км/ч")}, ask="v", unit="м/с", formula="v = v₀ · 5/18",
           symbols={"v0": "v₀"}, rounding=0,
           tags=("перевод единиц",),
           distractors=[
               ("72 м/с", "число переписано без перевода единиц", "72 m/s", "the number was copied without converting units"),
               ("259,2 м/с", "умножение на 3,6 вместо деления", "259.2 m/s", "multiplied by 3.6 instead of dividing"),
               ("2 м/с", "деление на 36 вместо 3,6", "2 m/s", "divided by 36 instead of 3.6"),
               ("0,02 м/с", "приставка «кило» потеряна дважды", "0.02 m/s", "the kilo prefix was lost twice")]),
        _a(2, "kinematics", 2,
           "Автобус движется со скоростью {v} м/с и разгоняется с ускорением {a} м/с² в течение {t} с. "
           "Какой путь он пройдёт за это время?",
           "A bus moves at {v} m/s and accelerates at {a} m/s² for {t} s. What distance does it cover?",
           model="s = v*t + a*t^2/2", vars={"s": "m", "v": "m/s", "a": "m/s^2", "t": "s"},
           data={"v": ("4", "м/с"), "a": ("2", "м/с^2"), "t": ("3", "с")}, ask="s", unit="м",
           formula="s = v·t + a·t²/2", rounding=0, tags=("равноускоренное движение",),
           distractors=[
               ("12 м", "учтено только равномерное движение, без ускорения", "12 m", "only the uniform part was counted"),
               ("18 м", "забыт множитель ½ у слагаемого ускорения", "18 m", "the factor ½ was dropped"),
               ("30 м", "ускорение подставлено вместо скорости", "30 m", "the acceleration was used as the speed"),
               ("9 м", "время возведено в квадрат, но не у слагаемого ускорения", "9 m", "time was squared in the wrong term")]),
        _a(3, "dynamics", 2,
           "Тело массой {m} кг движется с ускорением {a} м/с². Найдите равнодействующую всех сил.",
           "A body of {m} kg accelerates at {a} m/s². Find the net force.",
           model="F = m*a", vars={"F": "kg·m/s^2", "m": "kg", "a": "m/s^2"},
           data={"m": ("0,5", "кг"), "a": ("6", "м/с^2")}, ask="F", unit="Н",
           formula="F = m·a", rounding=0, tags=("второй закон Ньютона",),
           distractors=[
               ("12 Н", "ускорение поделено на массу, а не умножено", "12 N", "the acceleration was divided by the mass"),
               ("6,5 Н", "величины сложены вместо умножения", "6.5 N", "the values were added instead of multiplied"),
               ("0,083 Н", "деление вместо умножения", "0.083 N", "divided instead of multiplied"),
               ("6 Н", "масса не учтена, взято численное значение ускорения", "6 N", "the mass was ignored")]),
        _a(4, "workenergy", 2,
           "Ящик тянут с силой {F} Н на расстояние {s} м. Сила направлена под углом 60° к перемещению "
           "(cos 60° = ½). Найдите работу силы.",
           "A crate is pulled with {F} N over {s} m. The force is at 60° to the displacement "
           "(cos 60° = ½). Find the work.",
           model="A = F*s/2", vars={"A": "kg·m^2/s^2", "F": "kg·m/s^2", "s": "m"},
           data={"F": ("20", "Н"), "s": ("3", "м")}, ask="A", unit="Дж",
           formula="A = F·s·cos α", rounding=0, tags=("работа и мощность",),
           distractors=[
               ("60 Дж", "косинус угла не учтён", "60 J", "the cosine was ignored"),
               ("120 Дж", "деление на ½ превращено в умножение на 2", "120 J", "dividing by ½ became multiplying by 2"),
               ("52 Дж", "F и s сложены", "52 J", "F and s were added"),
               ("15 Дж", "деление на 2 применено дважды", "15 J", "divided by 2 twice")]),
        _a(5, "statics", 2,
           "Лыжник массой {m} кг стоит на лыжах площадью {s} м². g = {g} м/с². "
           "Какое давление он оказывает на снег?",
           "A skier of {m} kg stands on {s} m² of skis. g = {g} m/s². Find the pressure on the snow.",
           model="p = m*g/s", vars={"p": "kg/(m·s^2)", "m": "kg", "g": "m/s^2", "s": "m^2"},
           data={"m": ("60", "кг"), "g": ("9,8", "м/с^2"), "s": ("0,3", "м²")}, ask="p", unit="Па",
           formula="p = m·g/S", rounding=0, tags=("давление",),
           distractors=[
               ("196 Па", "площадь умножена вместо деления", "196 Pa", "the area was multiplied instead of divided"),
               ("588 Па", "сила тяжести не поделена на площадь", "588 Pa", "the weight was not divided by the area"),
               ("200 Па", "g округлено до 10 без основания", "200 Pa", "g was rounded to 10 without reason"),
               ("1,8 Па", "S подставлено вместо m", "1.8 Pa", "S was used as the mass")]),
        _a(6, "molecular", 2,
           "Сколько молей содержится в {m} г углекислого газа CO₂? Молярная масса {M} г/моль.",
           "How many moles are in {m} g of carbon dioxide CO₂? The molar mass is {M} g/mol.",
           model="nu = m/M", vars={"nu": "mol", "m": "kg", "M": "kg/mol"},
           data={"m": ("88", "г"), "M": ("44", "г/моль")}, ask="nu", unit="моль",
           formula="ν = m/M", rounding=0, tags=("количество вещества",),
           distractors=[
               ("0,5 моль", "деление перевёрнуто", "0.5 mol", "the division was inverted"),
               ("3872 моль", "масса умножена на молярную массу", "3872 mol", "the mass was multiplied by the molar mass"),
               ("2 · 10²⁶ моль", "вместо молей посчитаны молекулы", "2 · 10²⁶ mol", "molecules were counted instead of moles"),
               ("0,002 моль", "граммы переведены в килограммы дважды", "0.002 mol", "grams were converted to kilograms twice")]),
        _a(7, "thermo", 2,
           "Воду массой {m} кг нагревают на {dt} °C. Удельная теплоёмкость воды {c} Дж/(кг·°C). "
           "Сколько теплоты нужно?",
           "Water of {m} kg is heated by {dt} °C. The specific heat is {c} J/(kg·°C). How much heat is needed?",
           model="Q = c*m*dt", vars={"Q": "kg·m^2/s^2", "c": "m^2/(s^2·K)", "m": "kg", "dt": "K"},
           data={"c": ("4200", "Дж/(кг·К)"), "m": ("0,5", "кг"), "dt": ("40", "К")}, ask="Q", unit="Дж",
           formula="Q = c·m·Δt", rounding=0, tags=("теплота и теплоёмкость",),
           distractors=[
               ("8400 Дж", "масса не учтена", "8400 J", "the mass was ignored"),
               ("16 800 Дж", "перепутано умножение и деление на массу", "16 800 J", "multiplication and division by mass were mixed up"),
               ("168 000 Дж", "лишний множитель 10", "168 000 J", "an extra factor of 10"),
               ("42 000 Дж", "Δt уменьшено вдвое", "42 000 J", "Δt was halved")]),
        _a(8, "electrostatics", 3,
           "Два одинаковых точечных заряда по {q} Кл находятся на расстоянии {r} м. k = {k} Н·м²/Кл². "
           "Найдите силу их взаимодействия.",
           "Two equal point charges of {q} C are {r} m apart. k = {k} N·m²/C². Find the force.",
           model="F = k*q^2/r^2", vars={"F": "kg·m/s^2", "k": "m^3·kg/(s^4·A^2)", "q": "A·s", "r": "m"},
           data={"k": ("9000000000", "Н·м^2/Кл^2"), "q": ("0,000002", "Кл"), "r": ("0,1", "м")},
           ask="F", unit="Н", formula="F = k·q²/r²", rounding=0, tags=("закон Кулона",),
           distractors=[
               ("0,036 Н", "деление на квадрат расстояния забыто", "0.036 N", "division by r² was forgotten"),
               ("360 Н", "расстояние возведено в четвёртую степень", "360 N", "the distance was raised to the fourth power"),
               ("36 Н", "лишний множитель 10", "36 N", "an extra factor of 10"),
               ("0,36 Н", "лишний делитель 10", "0.36 N", "an extra factor of 10 in the denominator")]),
        _a(9, "current", 2,
           "Два резистора {r1} Ом и {r2} Ом соединены параллельно. Найдите общее сопротивление.",
           "Resistors of {r1} Ω and {r2} Ω are connected in parallel. Find the total resistance.",
           model="R = r1*r2/(r1+r2)", vars={"R": "kg·m^2/(s^3·A^2)", "r1": "kg·m^2/(s^3·A^2)", "r2": "kg·m^2/(s^3·A^2)"},
           data={"r1": ("6", "Ом"), "r2": ("3", "Ом")}, ask="R", unit="Ом",
           formula="1/R = 1/R₁ + 1/R₂", rounding=0, tags=("параллельное соединение",),
           distractors=[
               ("9 Ом", "сопротивления сложены, как при последовательном соединении", "9 Ω", "resistances were added as in series"),
               ("4,5 Ом", "взято среднее арифметическое", "4.5 Ω", "the arithmetic mean was taken"),
               ("18 Ом", "перемножены и не поделены на сумму", "18 Ω", "multiplied but not divided by the sum"),
               ("3 Ом", "взято меньшее сопротивление", "3 Ω", "the smaller resistance was taken")]),
        _a(10, "magnetism", 2,
           "Проводник длиной {l} м с током {i} А расположен перпендикулярно магнитному полю {b} Тл. "
           "Найдите силу Ампера.",
           "A wire of {l} m with current {i} A is perpendicular to a {b} T field. Find the Ampère force.",
           model="F = b*i*l", vars={"F": "kg·m/s^2", "b": "kg/(s^2·A)", "i": "A", "l": "m"},
           data={"b": ("0,4", "Тл"), "i": ("5", "А"), "l": ("0,2", "м")}, ask="F", unit="Н",
           formula="F = B·I·l", rounding=1, tags=("сила Ампера",),
           distractors=[
               ("0,04 Н", "потерян множитель 10", "0.04 N", "a factor of 10 is missing"),
               ("4 Н", "лишний множитель 10", "4 N", "an extra factor of 10"),
               ("2 Н", "l и i перепутаны", "2 N", "l and i were swapped"),
               ("0,1 Н", "l не учтена", "0.1 N", "l was dropped")]),

        # ------------------------------ часть B ------------------------------ #
        _b(1, "kinematics", 1,
           "Поезд идёт равномерно со скоростью {v} м/с. Какой путь он пройдёт за {t} с?",
           "A train moves uniformly at {v} m/s. What distance does it cover in {t} s?",
           model="s = v*t", vars={"s": "m", "v": "m/s", "t": "s"},
           data={"v": ("8", "м/с"), "t": ("15", "с")}, ask="s", unit="м",
           formula="s = v·t", rounding=0, tags=("равноускоренное движение",)),
        _b(2, "kinematics", 2,
           "Скорость тела массой... Скорость тела увеличилась с {v0} м/с до некоторой за {t} с при ускорении "
           "{a} м/с². Найдите конечную скорость.",
           "A body speeds up from {v0} m/s for {t} s at {a} m/s². Find the final speed.",
           model="v = v0 + a*t", vars={"v": "m/s", "v0": "m/s", "a": "m/s^2", "t": "s"},
           data={"v0": ("5", "м/с"), "a": ("3", "м/с^2"), "t": ("4", "с")}, ask="v", unit="м/с",
           symbols={"v0": "v₀"}, formula="v = v₀ + a·t", rounding=0, tags=("равноускоренное движение",)),
        _b(3, "kinematics", 2,
           "Тело падает без начальной скорости с высоты. g = {g} м/с². Какой путь оно пройдёт за {t} с?",
           "A body falls from rest. g = {g} m/s². How far does it fall in {t} s?",
           model="h = g*t^2/2", vars={"h": "m", "g": "m/s^2", "t": "s"},
           data={"g": ("9,8", "м/с^2"), "t": ("2", "с")}, ask="h", unit="м",
           formula="h = g·t²/2", rounding=1, tags=("свободное падение",)),
        _b(4, "kinematics", 2,
           "Первый участок {s1} км пройден за {t1} ч, второй {s2} км — за {t2} ч. Найдите среднюю скорость.",
           "The first {s1} km took {t1} h and the next {s2} km took {t2} h. Find the average speed.",
           model="v = (s1+s2)/(t1+t2)", vars={"v": "m/s", "s1": "m", "s2": "m", "t1": "s", "t2": "s"},
           data={"s1": ("6", "км"), "t1": ("0,5", "ч"), "s2": ("12", "км"), "t2": ("1", "ч")},
           ask="v", unit="км/ч", formula="vср = (s₁ + s₂)/(t₁ + t₂)", rounding=0,
           tags=("средняя скорость",)),
        _b(5, "dynamics", 2,
           "Автомобиль массой {m} кг разгоняется с ускорением {a} м/с². Найдите силу тяги, если "
           "сопротивлением можно пренебречь.",
           "A car of {m} kg accelerates at {a} m/s². Find the driving force, neglecting resistance.",
           model="F = m*a", vars={"F": "kg·m/s^2", "m": "kg", "a": "m/s^2"},
           data={"m": ("1200", "кг"), "a": ("0,5", "м/с^2")}, ask="F", unit="Н",
           formula="F = m·a", rounding=0, tags=("второй закон Ньютона",)),
        _b(6, "dynamics", 2,
           "Брусок массой {m} кг тянут по столу с силой трения, коэффициент трения {mu}. g = {g} м/с², "
           "движение горизонтальное. Найдите силу трения.",
           "A block of {m} kg slides on a table with friction coefficient {mu}. g = {g} m/s². Find the friction force.",
           model="F = mu*m*g", vars={"F": "kg·m/s^2", "mu": "1", "m": "kg", "g": "m/s^2"},
           data={"m": ("4", "кг"), "mu": ("0,25", "1"), "g": ("9,8", "м/с^2")}, ask="F", unit="Н",
           formula="Fтр = μ·N = μ·m·g", rounding=1, tags=("сила трения",)),
        _b(7, "dynamics", 2,
           "Пружину жёсткостью {k} Н/м растянули на {x} см. Найдите силу упругости.",
           "A spring of stiffness {k} N/m is stretched by {x} cm. Find the elastic force.",
           model="F = k*x", vars={"F": "kg·m/s^2", "k": "kg/s^2", "x": "m"},
           data={"k": ("200", "Н/м"), "x": ("4", "см")}, ask="F", unit="Н",
           formula="F = k·x", rounding=0, tags=("сила упругости",)),
        _b(8, "dynamics", 2,
           "Найдите вес груза массой {m} кг, лежащего на горизонтальной опоре. g = {g} м/с².",
           "Find the weight of a {m} kg load on a horizontal support. g = {g} m/s².",
           model="P = m*g", vars={"P": "kg·m/s^2", "m": "kg", "g": "m/s^2"},
           data={"m": ("12", "кг"), "g": ("9,8", "м/с^2")}, ask="P", unit="Н",
           formula="P = m·g", rounding=1, tags=("сила тяжести и вес",)),
        _b(9, "workenergy", 2,
           "Тело массой {m} кг движется со скоростью {v} м/с. Найдите кинетическую энергию.",
           "A body of {m} kg moves at {v} m/s. Find its kinetic energy.",
           model="E = m*v^2/2", vars={"E": "kg·m^2/s^2", "m": "kg", "v": "m/s"},
           data={"m": ("2", "кг"), "v": ("3", "м/с")}, ask="E", unit="Дж",
           formula="Eк = m·v²/2", rounding=0, tags=("закон сохранения энергии",)),
        _b(10, "workenergy", 2,
           "Тело массой {m} кг поднято на высоту {h} м. g = {g} м/с². Найдите потенциальную энергию.",
           "A body of {m} kg is lifted to {h} m. g = {g} m/s². Find its potential energy.",
           model="E = m*g*h", vars={"E": "kg·m^2/s^2", "m": "kg", "g": "m/s^2", "h": "m"},
           data={"m": ("5", "кг"), "g": ("9,8", "м/с^2"), "h": ("2", "м")}, ask="E", unit="Дж",
           formula="Eп = m·g·h", rounding=0, tags=("закон сохранения энергии",)),
        _b(11, "workenergy", 2,
           "Тело массой {m} кг движется со скоростью {v} м/с. Найдите импульс.",
           "A body of {m} kg moves at {v} m/s. Find its momentum.",
           model="p = m*v", vars={"p": "kg·m/s", "m": "kg", "v": "m/s"},
           data={"m": ("3", "кг"), "v": ("4", "м/с")}, ask="p", unit="кг·м/с",
           formula="p = m·v", rounding=0, tags=("импульс и закон сохранения",)),
        _b(12, "statics", 2,
           "На плечо рычага {d} м действует сила {f} Н перпендикулярно рычагу. Найдите момент силы.",
           "A force of {f} N acts perpendicular to a lever arm of {d} m. Find the torque.",
           model="M = f*d", vars={"M": "kg·m^2/s^2", "f": "kg·m/s^2", "d": "m"},
           data={"f": ("30", "Н"), "d": ("0,2", "м")}, ask="M", unit="Н·м",
           formula="M = F·d", rounding=0, tags=("момент силы",)),
        _b(13, "statics", 2,
           "Найдите давление воды на глубине {h} м. Плотность {rho} кг/м³, g = {g} м/с².",
           "Find the water pressure at {h} m. Density {rho} kg/m³, g = {g} m/s².",
           model="p = rho*g*h", vars={"p": "kg/(m·s^2)", "rho": "kg/m^3", "g": "m/s^2", "h": "m"},
           data={"rho": ("1000", "кг/м^3"), "g": ("9,8", "м/с^2"), "h": ("5", "м")},
           ask="p", unit="кПа", formula="p = ρ·g·h", rounding=0, tags=("гидростатическое давление",)),
        _b(14, "statics", 3,
           "Тело объёмом {v} м³ полностью погружено в воду плотностью {rho} кг/м³. g = {g} м/с². "
           "Найдите силу Архимеда.",
           "A body of volume {v} m³ is fully submerged in water of density {rho} kg/m³. g = {g} m/s². "
           "Find the buoyant force.",
           model="F = rho*v*g", vars={"F": "kg·m/s^2", "rho": "kg/m^3", "v": "m^3", "g": "m/s^2"},
           data={"rho": ("1000", "кг/м^3"), "v": ("0,002", "м³"), "g": ("9,8", "м/с^2")},
           ask="F", unit="Н", formula="FА = ρж·V·g", rounding=1, tags=("сила Архимеда",)),
        _b(15, "molecular", 2,
           "Газ занимает объём {v} л при температуре 27 °C ({T1} К). Каким станет объём при 127 °C "
           "({T2} К), если давление постоянное?",
           "A gas occupies {v} l at 27 °C ({T1} K). What volume will it take at 127 °C ({T2} K) "
           "at constant pressure?",
           model="V2 = v*T2/T1", vars={"V2": "m^3", "v": "m^3", "T2": "K", "T1": "K"},
           data={"v": ("2", "л"), "T1": ("300", "К"), "T2": ("400", "К")}, ask="V2", unit="л",
           formula="V₂ = V₁·T₂/T₁", rounding=2, tags=("уравнение состояния газа",)),
        _b(16, "thermo", 2,
           "Сколько теплоты нужно, чтобы расплавить {m} кг льда при 0 °C? "
           "Удельная теплота плавления {lam} Дж/кг.",
           "How much heat melts {m} kg of ice at 0 °C? The specific latent heat is {lam} J/kg.",
           model="Q = lam*m", vars={"Q": "kg·m^2/s^2", "lam": "m^2/s^2", "m": "kg"},
           data={"lam": ("340000", "Дж/кг"), "m": ("2", "кг")}, ask="Q", unit="кДж",
           formula="Q = λ·m", rounding=0, tags=("фазовые переходы",)),
        _b(17, "current", 2,
           "Напряжение на резисторе {u} В, сопротивление {r} Ом. Найдите силу тока.",
           "The voltage across a {r} Ω resistor is {u} V. Find the current.",
           model="I = u/r", vars={"I": "A", "u": "kg·m^2/(s^3·A)", "r": "kg·m^2/(s^3·A^2)"},
           data={"u": ("12", "В"), "r": ("4", "Ом")}, ask="I", unit="А",
           formula="I = U/R", rounding=0, tags=("закон Ома",)),
        _b(18, "current", 2,
           "Два резистора {r1} Ом и {r2} Ом соединены последовательно и подключены к {u} В. "
           "Найдите силу тока в цепи.",
           "Resistors {r1} Ω and {r2} Ω are in series across {u} V. Find the current.",
           model="I = u/(r1+r2)", vars={"I": "A", "u": "kg·m^2/(s^3·A)", "r1": "kg·m^2/(s^3·A^2)", "r2": "kg·m^2/(s^3·A^2)"},
           data={"r1": ("2", "Ом"), "r2": ("3", "Ом"), "u": ("10", "В")}, ask="I", unit="А",
           formula="I = U/(R₁ + R₂)", rounding=0, tags=("последовательное соединение",)),
        _b(19, "current", 3,
           "Лампа мощностью {p} Вт работает при напряжении {u} В. Найдите сопротивление лампы.",
           "A {p} W lamp works at {u} V. Find its resistance.",
           model="R = u^2/p", vars={"R": "kg·m^2/(s^3·A^2)", "u": "kg·m^2/(s^3·A)", "p": "kg·m^2/s^3"},
           data={"p": ("100", "Вт"), "u": ("200", "В")}, ask="R", unit="Ом",
           formula="R = U²/P", rounding=0, tags=("работа тока",)),
        _b(20, "quantum", 3,
           "Период полураспада изотопа {tt} суток, то есть за {t} суток проходит ровно "
           "3 периода. Какая доля ядер распадётся за это время?",
           "The half-life is {tt} days, so {t} days span exactly 3 half-lives. What fraction "
           "of the nuclei decays?",
           model=f"f = 1 - 2^(-{_DECAY_PERIODS})", vars={"f": "1", "t": "s", "tt": "s"},
           data={"t": (str(_DECAY_T), "сут"), "tt": (str(_DECAY_HALF_LIFE), "сут")},
           ask="f", unit="1", formula="N = N₀·2^(−t/T)", rounding=3,
           tags=("радиоактивность",)),
    ]
