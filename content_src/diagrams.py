"""Определённые, офлайн-безопасные физические схемы как типизированные SVG-примитивы.

Никакого raw SVG/HTML, скриптов, картинок, путей, CSS или внешних URL в контенте.
Кривые графиков сэмплируются из именованных функций Python (в JS формулы никогда
не вычисляются). Координаты — в единицах области рисования 420×280; пропорции
линейных схем соблюдены, качественно-условные рисунки помечены словом «схема» в
подписи и не выдаются за измерение. Модель каждой схемы описана в поле ``model``,
чтобы тест мог проверить физику (наклон, площадь, единицы, полярность).

Цвет избыточен: смысл несут подписи, роли и легенда.
"""

from __future__ import annotations

from copy import deepcopy
import math

WIDTH, HEIGHT = 420, 280
ROLES = {"axis", "grid", "primary", "secondary", "helper", "region", "point", "openpoint", "text"}
FIELDS = {
    "line": {"x1", "y1", "x2", "y2"}, "polyline": {"points"}, "polygon": {"points"},
    "circle": {"cx", "cy", "r"}, "ellipse": {"cx", "cy", "rx", "ry"},
    "rect": {"x", "y", "width", "height"}, "text": {"x", "y", "text", "anchor"},
}
#: Именованные функции графиков: x — аргумент оси времени/координаты,
#: y — значение функции в единицах выбранного рисунка.
FUNCTIONS = {
    "uniform-x": lambda t: 5 * t,             # x = v t, v = 5 м/с
    "accelerated-v": lambda t: 2 * t,         # v = a t, a = 2 м/с²
    "hooke": lambda x: 200 * x / 100,         # F = k x, k = 200 Н/м, x в см
    "isotherm": lambda v: 3.2 / v,            # p = νRT / V при νRT = 3,2
    "decay": lambda n: 2 ** (-n),             # N/N₀ через n периодов полураспада
    "sine-wave": lambda x: math.sin(x),       # гармоническая волна
    "one-over": lambda x: 2 / x,              # зависимость E ~ 1/r
}


def bi(ru, en=None):
    return {"ru": str(ru), "en": str(ru if en is None else en)}


def n(value):
    return round(float(value), 5)


def shape(kind, role="primary", filled=False, **coordinates):
    return {"kind": kind, "role": role, "filled": filled, **coordinates}


def line(x1, y1, x2, y2, role="primary"):
    return shape("line", role, x1=n(x1), y1=n(y1), x2=n(x2), y2=n(y2))


def poly(points, role="primary", filled=False, closed=False):
    return shape("polygon" if closed else "polyline", role, filled,
                 points=[[n(x), n(y)] for x, y in points])


def circle(x, y, r, role="primary", filled=False):
    return shape("circle", role, filled, cx=n(x), cy=n(y), r=n(r))


def ellipse(x, y, rx, ry, role="primary"):
    return shape("ellipse", role, cx=n(x), cy=n(y), rx=n(rx), ry=n(ry))


def rect(x, y, w, h, role="region", filled=False):
    return shape("rect", role, filled, x=n(x), y=n(y), width=n(w), height=n(h))


def text(x, y, label, en=None, anchor="middle", role="text"):
    return shape("text", role, x=n(x), y=n(y), text=bi(label, en), anchor=anchor)


def arrow(x1, y1, x2, y2, role="primary"):
    angle = math.atan2(y2 - y1, x2 - x1)
    a = (x2 - 10 * math.cos(angle - .4), y2 - 10 * math.sin(angle - .4))
    b = (x2 - 10 * math.cos(angle + .4), y2 - 10 * math.sin(angle + .4))
    return [line(x1, y1, x2, y2, role), poly([a, (x2, y2), b], role, True, True)]


def figure(key, title, caption, drawing, *, legend=None, model=None):
    result = {"id": key, "title": bi(*title), "caption": bi(*caption),
              "width": WIDTH, "height": HEIGHT, "drawing": drawing}
    if legend:
        result["legend"] = [{"role": role, "text": bi(*label)} for role, label in legend]
    if model:
        result["model"] = model
    return result


def _frame_plot(key, title, caption, bounds, series, axis_labels, *, xticks=None,
                yticks=None, markers=None, legend=None, extra=()):
    """График с подписанными осями: ось x — ``axis_labels[0]``, ось y — ``axis_labels[1]``."""
    entry = plot(key, title, caption, bounds, series, xticks=xticks, yticks=yticks,
                 markers=markers, legend=legend)
    entry["drawing"] = entry["drawing"] + [text(370, 250, axis_labels[0]), text(30, 20, axis_labels[1])] + list(extra)
    entry["model"] = {**entry.get("model", {}), "axes": list(axis_labels)}
    return entry


def plot(key, title, caption, bounds, series, *, xticks=None, yticks=None, markers=None, legend=None):
    xmin, xmax, ymin, ymax = bounds
    frame = [48, 28, 324, 204]
    left, top, width, height = frame

    def pos(x, y):
        return left + (x - xmin) / (xmax - xmin) * width, top + (ymax - y) / (ymax - ymin) * height

    def label(value):
        common = f"{value:g}".replace("-", "−")
        return bi(common.replace(".", ","), common)

    drawing = []
    xticks = xticks if xticks is not None else list(range(math.ceil(xmin), math.floor(xmax) + 1))
    yticks = yticks if yticks is not None else list(range(math.ceil(ymin), math.floor(ymax) + 1))
    for tick in xticks:
        x, tx = tick if isinstance(tick, tuple) else (tick, label(tick))
        px, _ = pos(x, 0)
        if left <= px <= left + width:
            drawing.append(line(px, top, px, top + height, "grid"))
            item = text(px, top + height + 21, "")
            item["text"] = tx
            drawing.append(item)
    for tick in yticks:
        y, tx = tick if isinstance(tick, tuple) else (tick, label(tick))
        _, py = pos(0, y)
        if top <= py <= top + height:
            drawing.append(line(left, py, left + width, py, "grid"))
            item = text(left - 9, py + 5, "", anchor="end")
            item["text"] = tx
            drawing.append(item)
    axis_y = pos(0, min(ymax, max(ymin, 0)))[1]
    axis_x = pos(min(xmax, max(xmin, 0)), 0)[0]
    drawing += arrow(left, axis_y, left + width + 12, axis_y, "axis")
    drawing += arrow(axis_x, top + height, axis_x, top - 12, "axis")
    descriptions = []
    for fn, role, domains in series:
        count = 0
        for a, b in domains:
            segment = []
            for index in range(121):
                x = a + (b - a) * index / 120
                try:
                    y = FUNCTIONS[fn](x)
                except (ValueError, ZeroDivisionError, OverflowError):
                    y = float("nan")
                if math.isfinite(y) and xmin <= x <= xmax and ymin <= y <= ymax:
                    segment.append(pos(x, y))
                else:
                    if len(segment) >= 2:
                        drawing.append(poly(segment, role))
                        count += 1
                    segment = []
            if len(segment) >= 2:
                drawing.append(poly(segment, role))
                count += 1
        descriptions.append({"function": fn, "role": role, "segments": count})
    for x, y, label_text, dx, dy in markers or []:
        px, py = pos(x, y)
        label_item = text(px + dx, py + dy, *label_text) if isinstance(label_text, tuple) else text(px + dx, py + dy, label_text)
        drawing += [circle(px, py, 4, "point", True), label_item]
    return figure(key, title, caption, drawing, legend=legend,
                  model={"type": "plot", "bounds": list(bounds), "frame": frame, "series": descriptions})


FIGURES = {}


def add(entry):
    if entry["id"] in FIGURES:
        raise ValueError("duplicate diagram id")
    FIGURES[entry["id"]] = entry


# --------------------------------------------------------------------------- #
#  Измерения
# --------------------------------------------------------------------------- #

add(figure("scale-ruler", ("Цена деления линейки", "Scale division of a ruler"),
           ("Между подписями 2 см и 4 см один промежуток, значит цена деления 2 см; "
            "между 4 и 6 — тоже 2 см. Погрешность линейки не меньше половины деления.",
            "Between the 2 cm and 4 cm labels there is one gap, so the division is 2 cm; "
            "between 4 and 6 it is also 2 cm. The uncertainty is at least half a division."),
           [rect(40, 120, 340, 56, "region", True)]
           + [line(40 + 56.7 * i, 120, 40 + 56.7 * i, 150, "grid") for i in range(7)]
           + [line(40 + 28.3 + 56.7 * i, 120, 40 + 28.3 + 56.7 * i, 138, "grid") for i in range(6)]
           + [text(40 + 56.7 * i, 108, str(2 * i) + " см") for i in (0, 2, 4, 6)]
           + [text(210, 212, "цена деления c = 2 см", "scale division c = 2 cm")],
           model={"type": "measurement", "divisionCm": 2, "labelsCm": [0, 2, 4, 6, 8, 10, 12],
                  "uncertaintyCm": 1}))

# --------------------------------------------------------------------------- #
#  Кинематика
# --------------------------------------------------------------------------- #

add(figure("motion-route", ("Путь и перемещение", "Distance and displacement"),
           ("Точка прошла по дуге A → B → C и вернулась в A. Пройденный путь равен длине "
            "траектории, перемещение — вектор из A в A, то есть нуль.",
            "A point travels along the arc A → B → C and returns to A. The distance is the "
            "trajectory length; the displacement vector from A to A is zero."),
           [poly([[60, 190], [140, 90], [230, 92], [320, 140], [240, 210], [150, 215], [60, 190]], "primary")]
           + [*arrow(170, 60, 220, 60, "secondary"), text(196, 48, "перемещение = 0", "displacement = 0")]
           + [circle(60, 190, 5, "point", True), text(48, 214, "A"), circle(150, 215, 5, "point", True), text(150, 240, "B"),
              circle(320, 140, 5, "point", True), text(334, 132, "C")]
           + [text(120, 120, "путь", "distance")],
           model={"type": "kinematics-route", "displacement": 0, "pathPositive": True}))

add(_frame_plot("graph-x-t", ("График x(t) равномерного движения", "x(t) of uniform motion"),
                ("x = v·t при v = 5 м/с: за каждую секунду координата растёт на 5 м. "
                 "Наклон графика равен скорости, прямая начинается в нуле координат.",
                 "x = v·t with v = 5 m/s: the coordinate grows by 5 m each second. The slope "
                 "equals the speed and the line starts at the origin."),
                (0, 8, 0, 40), [("uniform-x", "primary", [(0, 8)])],
                ("t, с", "x, м"),
                xticks=[0, 2, 4, 6, 8], yticks=[0, 10, 20, 30, 40],
                markers=[(4, 20, ("4 с → 20 м", "4 s → 20 m"), 0, -16)]))

add(_frame_plot("graph-v-t", ("График v(t): наклон и площадь", "v(t): slope and area"),
                ("v = a·t при a = 2 м/с². Наклон прямой — ускорение; закрашенная площадь "
                 "под графиком от 0 до 3 с равна пути: ½·2·3² = 9 м.",
                 "v = a·t with a = 2 m/s². The slope is the acceleration; the shaded area "
                 "from 0 to 3 s equals the distance ½·2·3² = 9 m."),
                (0, 8, 0, 16), [("accelerated-v", "primary", [(0, 8)])],
                ("t, с", "v, м/с"),
                xticks=[0, 2, 4, 6, 8], yticks=[0, 4, 8, 12, 16],
                markers=[(3, 6, ("площадь = 9 м", "area = 9 m"), 20, 26)],
                extra=[poly([[48, 223], [48 + 324 * 3 / 8, 28 + 204 * (16 - 6) / 16],
                             [48 + 324 * 3 / 8, 223]], "region", True, True)]))

add(figure("free-fall", ("Свободное падение без сопротивления", "Free fall without drag"),
           ("Два тела разной массы отпущены с одинаковой высоты: без сопротивления воздуха "
            "они падают одинаково, h = gt²/2. Масса в формулу не входит.",
            "Two bodies of different mass are released from the same height: without air drag "
            "they fall identically, h = gt²/2. Mass does not appear in the formula."),
           [line(60, 40, 360, 40, "grid"), line(60, 40, 60, 240, "axis"), *arrow(60, 240, 60, 30, "axis")]
           + [circle(70, 52, 9, "primary", True), circle(90, 52, 14, "secondary", True),
              line(60, 118, 360, 118, "helper"), line(60, 196, 360, 196, "helper")]
           + [text(120, 44, "m₁ и m₂ вместе", "m₁ and m₂ together"), text(300, 44, "t = 0", "t = 0")]
           + [text(300, 122, "t₁ = √(2h₁/g)", "t₁ = √(2h₁/g)"), text(300, 200, "t₂ = √(2h₂/g)", "t₂ = √(2h₂/g)")]
           + [text(210, 262, "a = g ≈ 9,8 м/с²", "a = g ≈ 9.8 m/s²")],
           model={"type": "free-fall", "massIndependent": True, "g": 9.8}))

# --------------------------------------------------------------------------- #
#  Динамика
# --------------------------------------------------------------------------- #

add(figure("force-diagram", ("Силы на теле: свободная диаграмма", "Forces on a body"),
           ("На брусок действуют тяжесть mg, нормальная реакция N, тяга F и трение Fтр. "
            "Стрелка показывает направление каждой силы, тело отсчёта — стол, движение вправо.",
            "A block is acted on by gravity mg, the normal force N, a pull F and friction Fтр. "
            "Each arrow shows a direction; the reference frame is the table, motion to the right."),
           [line(30, 210, 390, 210, "axis"), rect(150, 148, 120, 62, "region", True)]
           + [*arrow(210, 210, 210, 108, "secondary"), *arrow(210, 210, 210, 128, "helper"),
              *arrow(150, 179, 82, 179, "secondary"), *arrow(270, 179, 344, 179, "primary")]
           + [text(232, 104, "N"), text(178, 140, "mg"), text(96, 166, "F", ), text(330, 166, "Fтр", "F_fr")]
           + [text(210, 240, "равнодействующая F − Fтр", "net force F − F_fr")],
           model={"type": "force-diagram", "forces": ["N", "mg", "F", "Fтр"],
                  "direction": "right", "massPositive": True}))

add(figure("incline-forces", ("Наклонная плоскость: N меньше mg", "Incline: N is smaller than mg"),
           ("На склоне с углом α сила тяжести раскладывается: N = mg·cos α, скатывающая "
            "составляющая mg·sin α. При α = 0 получается горизонтальная опора, N = mg; с ростом угла N падает.",
            "On a slope of angle α gravity splits: N = mg·cos α and the down-slope component "
            "is mg·sin α. At α = 0 the support is horizontal with N = mg; N falls as α grows."),
           [poly([[60, 220], [340, 220], [340, 60]], "region", True), line(60, 220, 340, 60, "primary")]
           + [rect(196, 148, 52, 26, "region")]
           + [*arrow(222, 161, 222, 96, "secondary"), *arrow(222, 161, 160, 191, "secondary"),
              *arrow(222, 161, 222, 210, "primary")]
           + [text(244, 92, "N"), text(150, 206, "mg·sin α", "mg sin α"), text(244, 214, "mg")]
           + [text(232, 238, "угол α отмечен между склоном и горизонтом", "angle α measured from the horizontal")],
           model={"type": "incline", "normalFactor": "cos", "componentFactor": "sin"}))

add(_frame_plot("spring-hooke", ("Закон Гука: график F(x)", "Hooke's law: F(x) graph"),
                ("F = k·x при k = 200 Н/м. График — прямая через начало координат: "
                 "удвоение растяжения удваивает силу. За пределом упругости эта прямая уже не работает.",
                 "F = k·x with k = 200 N/m. The graph is a straight line through the origin: "
                 "doubling the extension doubles the force. Beyond the elastic limit this line fails."),
                (0, 8, 0, 16), [("hooke", "primary", [(0, 8)])],
                ("x, см", "F, Н"),
                xticks=[0, 2, 4, 6, 8], yticks=[0, 4, 8, 12, 16],
                markers=[(4, 8, ("x = 4 см → 8 Н", "x = 4 cm → 8 N"), 0, -16)]))

# --------------------------------------------------------------------------- #
#  Статика, давление, гидростатика
# --------------------------------------------------------------------------- #

add(figure("lever-torque", ("Момент силы и плечо", "Torque and lever arm"),
           ("Рычаг на опоре O. Момент M = F·d, где d — перпендикуляр от оси до линии "
            "действия силы. В равновесии F₁d₁ = F₂d₂: короткое плечо требует большей силы.",
            "A lever on the pivot O. Torque M = F·d where d is the perpendicular distance "
            "from the axis to the line of action. In equilibrium F₁d₁ = F₂d₂."),
           [poly([[40, 190], [380, 190]], "primary", False), poly([[200, 190], [215, 214], [185, 214], [200, 190]], "region", True)]
           + [*arrow(110, 190, 110, 128, "secondary"), *arrow(300, 190, 300, 96, "primary")]
           + [text(110, 118, "F₁", "F₁"), text(300, 86, "F₂", "F₂"),
              line(110, 190, 110, 205, "helper"), line(300, 190, 300, 205, "helper"),
              text(153, 226, "d₁ = 90 см", "d₁ = 90 cm"), text(256, 226, "d₂ = 100 см", "d₂ = 100 cm"),
              circle(200, 190, 4, "point", True), text(200, 244, "O")]
           + [text(210, 262, "F₁·90 = F₂·100", "F₁·90 = F₂·100")],
           model={"type": "torque", "leftArmCm": 90, "rightArmCm": 100, "equilibrium": "F1*d1 = F2*d2"}))

add(figure("pressure-depth", ("Давление зависит от глубины", "Pressure depends on depth"),
           ("p = ρgh: на глубине 10 м добавочное давление воды ≈ 98 кПа независимо от ширины "
            "сосуда. Широкий и узкий сосуды одинаковой высоты дают одинаковое давление на дне.",
            "p = ρgh: at 10 m the water pressure adds about 98 kPa regardless of the vessel "
            "width. Wide and narrow vessels of equal height give the same bottom pressure."),
           [rect(60, 60, 120, 180, "helper"), rect(240, 60, 120, 180, "helper")]
           + [line(60, 110, 180, 110, "axis"), line(240, 110, 360, 110, "axis")]
           + [line(60, 240, 180, 240, "primary"), line(240, 240, 360, 240, "primary")]
           + [line(120, 110, 120, 240, "grid"), line(300, 110, 300, 240, "grid")]
           + [text(120, 52, "узкий", "narrow"), text(300, 52, "широкий", "wide"),
              text(120, 128, "10 м", "10 m"), text(300, 128, "10 м", "10 m"),
              text(210, 272, "на дне давление одинаково: p = ρgh", "equal bottom pressure: p = ρgh")],
           model={"type": "hydrostatic", "depthM": 10, "rhoWater": 1000, "g": 9.8,
                  "pressurePa": 98000, "shapeIndependent": True}))

add(figure("buoyancy", ("Сила Архимеда", "Buoyant force"),
           ("Тело погружено в воду. Архимедова сила FА = ρжVпогрg направлена вверх и равна "
            "весу вытесненной воды. Если FА = mg, тело плавает; если FА < mg — тонет.",
            "A body is submerged. Buoyancy F = ρ_liquid·V_submerged·g points up and equals the "
            "weight of the displaced water. Floating needs F = mg, sinking means F < mg."),
           [rect(70, 120, 280, 130, "helper"), line(70, 120, 350, 120, "axis")]
           + [rect(180, 160, 90, 70, "region", True)]
           + [*arrow(225, 230, 225, 150, "primary"), *arrow(225, 195, 225, 268, "secondary")]
           + [text(258, 152, "FА = ρжVg", "F = ρ_liquid·V·g"), text(258, 262, "mg", "mg"),
              text(210, 108, "уровень воды", "water level"),
              text(210, 60, "вытесненный объём равен Vпогр", "displaced volume equals V_submerged")],
           model={"type": "buoyancy", "forces": ["buoyancy-up", "gravity-down"],
                  "floatCondition": "F = mg"}))

# --------------------------------------------------------------------------- #
#  Молекулярная физика и термодинамика
# --------------------------------------------------------------------------- #

add(_frame_plot("gas-isotherm", ("Изотерма: pV = const", "Isotherm: pV = const"),
                ("При постоянной температуре p = νRT/V, поэтому график — гипербола и "
                 "pV не меняется. Точка (2; 1,6) и точка (4; 0,8) дают одно и то же произведение 3,2.",
                 "At constant temperature p = νRT/V, so the graph is a hyperbola and the "
                 "product pV stays constant. Points (2, 1.6) and (4, 0.8) give the same 3.2."),
                (0, 8, 0, 4), [("isotherm", "primary", [(0.55, 8)])],
                ("V, м³", "p, кПа"),
                xticks=[0, 2, 4, 6, 8], yticks=[0, 1, 2, 3, 4],
                markers=[(2, 1.6, ("(2; 1,6)", "(2; 1.6)"), 34, -12), (4, 0.8, ("(4; 0,8)", "(4; 0.8)"), 34, -12)]))

add(figure("heating-curve", ("Нагрев и плавление: горизонтальная площадка", "Heating and melting"),
           ("Температура растёт, пока лёд нагревается; во время плавления теплота идёт на "
            "разрушение решётки и температура не меняется. Горизонтальный участок — не ошибка графика.",
            "Temperature rises while ice warms; during melting the heat breaks the lattice and "
            "the temperature stays constant. The flat section is a real plateau."),
           [line(48, 40, 48, 240, "axis"), line(48, 240, 400, 240, "axis"), *arrow(400, 240, 412, 240, "axis"), *arrow(48, 240, 48, 28, "axis")]
           + [poly([[48, 220], [120, 150], [200, 150], [280, 80], [330, 80], [400, 46]], "primary")]
           + [text(84, 196, "лёд", "ice"), text(160, 138, "плавление", "melting"),
              text(240, 122, "вода", "water"), text(305, 68, "кипение", "boiling"),
              text(360, 34, "пар", "steam"), text(416, 260, "t", "t"), text(28, 32, "T")]
           + [text(210, 272, "нагрев → плавление → нагрев → кипение", "heat → melt → heat → boil")],
           model={"type": "heating-curve", "plateaus": ["melting", "boiling"], "temperatureConstantOnPlateau": True}))

# --------------------------------------------------------------------------- #
#  Электричество и магнетизм
# --------------------------------------------------------------------------- #

add(figure("circuit-series", ("Последовательное соединение", "Series circuit"),
           ("В последовательной цепи ток один и тот же во всех элементах, напряжения "
            "складываются: R = R₁ + R₂. Амперметр включён последовательно, вольтметр — параллельно лампе.",
            "In a series circuit the current is the same everywhere and voltages add: "
            "R = R₁ + R₂. The ammeter is in series, the voltmeter is across the lamp."),
           [line(70, 90, 350, 90, "primary"), line(70, 90, 70, 200, "primary"), line(70, 200, 350, 200, "primary")]
           + [line(350, 90, 350, 200, "primary"), rect(190, 82, 60, 16, "secondary")]
           + [circle(110, 200, 18, "point"), text(110, 206, "A")]
           + [circle(250, 60, 12, "helper"), text(250, 55, "V"), line(250, 72, 250, 90, "primary"),
              line(250, 60, 220, 90, "primary"), line(250, 60, 280, 90, "primary")]
           + [text(120, 130, "R₁", "R₁"), text(280, 130, "R₂", "R₂"),
              text(210, 232, "I одинаков, U = U₁ + U₂", "same current, U = U₁ + U₂")],
           model={"type": "circuit", "connection": "series", "currentSame": True,
                  "resistanceRule": "sum", "ammeter": "series", "voltmeter": "parallel"}))

add(figure("circuit-parallel", ("Параллельное соединение", "Parallel circuit"),
           ("В параллельных ветвях напряжение одно и то же, токи складываются: 1/R = 1/R₁ + 1/R₂. "
            "Общее сопротивление меньше самого маленького из ветвей.",
            "Branches in parallel share the same voltage and currents add: 1/R = 1/R₁ + 1/R₂. "
            "The total resistance is smaller than the smallest branch."),
           [line(70, 80, 350, 80, "primary"), line(70, 80, 70, 210, "primary"), line(70, 210, 350, 210, "primary")]
           + [line(350, 80, 350, 210, "primary"), line(180, 80, 180, 210, "primary"),
              rect(150, 130, 16, 40, "secondary"), rect(320, 130, 16, 40, "secondary"),
              circle(70, 145, 17, "point"), text(70, 151, "A")]
           + [text(120, 100, "R₁", "R₁"), text(292, 100, "R₂", "R₂"),
              text(210, 240, "U одинаково, I = I₁ + I₂", "same voltage, I = I₁ + I₂")],
           model={"type": "circuit", "connection": "parallel", "voltageSame": True,
                  "resistanceRule": "reciprocal-sum"}))

add(figure("field-lines", ("Поле точечного заряда", "Field of a point charge"),
           ("Линии напряжённости выходят из положительного заряда радиально. "
            "Напряжённость E = kq/r² убывает как квадрат расстояния: вдвое дальше — вчетверо слабее.",
            "Field lines leave a positive charge radially. The field E = kq/r² falls as the "
            "square of the distance: twice as far means four times weaker."),
           [circle(210, 140, 12, "primary", True), text(210, 146, "+q", "+q")]
           + [item for angle in [math.pi * i / 6 for i in range(12)]
              for item in (line(210 + 22 * math.cos(angle), 140 + 22 * math.sin(angle),
                                210 + 108 * math.cos(angle), 140 + 108 * math.sin(angle), "helper"),
                           *arrow(210 + 96 * math.cos(angle), 140 + 96 * math.sin(angle),
                                  210 + 112 * math.cos(angle), 140 + 112 * math.sin(angle), "primary"))]
           + [ellipse(210, 140, 60, 60, "grid"), ellipse(210, 140, 104, 104, "grid"),
              text(340, 60, "r", "r"), text(336, 84, "E ~ 1/r²", "E ~ 1/r²")]
           + [text(210, 262, "работа поля A = qU", "field work A = qU")],
           model={"type": "field", "chargeSign": "positive", "inverseSquare": True}))

add(figure("magnetic-wire", ("Сила Ампера", "Ampère force"),
           ("Проводник с током I в магнитном поле B. Сила Ампера F = B·I·l·sin α максимальна, "
            "когда проводник перпендикулярен линиям поля; направление задаёт правило левой руки.",
            "A wire with current I in a magnetic field B. The Ampère force F = B·I·l·sin α is "
            "maximal when the wire is perpendicular to the field lines (left-hand rule)."),
           [line(40, 60, 380, 60, "primary"), line(40, 200, 380, 200, "primary")]
           + [text(60, 44, "B", "B"), text(60, 224, "B", "B")]
           + [rect(196, 60, 28, 140, "secondary", True)]
           + [*arrow(210, 60, 210, 30, "helper"), text(232, 40, "I", "I")]
           + [*arrow(210, 130, 320, 130, "primary"), text(330, 148, "F = B·I·l", "F = B·I·l")]
           + [text(210, 262, "α = 90°: sin α = 1", "α = 90°: sin α = 1")],
           model={"type": "ampere-force", "angleDeg": 90, "formula": "F = B*I*l*sin(alpha)"}))

add(figure("induction-flux", ("Магнитный поток и ЭДС индукции", "Magnetic flux and induced EMF"),
           ("Магнитный поток Φ = B·S·cos α через контур. Пока поток не меняется, ЭДС нет; "
            "при движении магнита поток растёт и в контуре появляется индукционный ток.",
            "Magnetic flux Φ = B·S·cos α through a loop. No change of flux means no EMF; moving "
            "the magnet changes the flux and drives an induced current."),
           [rect(120, 90, 180, 104, "region"), rect(158, 118, 104, 48, "secondary", True)]
           + [*arrow(70, 140, 116, 140, "primary"), text(74, 118, "v", "v")]
           + [text(210, 210, "Φ = B·S·cos α", "Φ = B·S·cos α"), text(210, 240, "|ε| = ΔΦ/Δt", "|ε| = ΔΦ/Δt")],
           model={"type": "induction", "fluxFormula": "B*S*cos(alpha)", "emfFormula": "dPhi/dt"}))

# --------------------------------------------------------------------------- #
#  Колебания, волны, звук
# --------------------------------------------------------------------------- #

add(figure("pendulum", ("Математический маятник", "Simple pendulum"),
           ("Нить длиной l с грузом отведена на малый угол. Период T = 2π√(l/g) не зависит "
            "от массы груза и при малых колебаниях почти не зависит от амплитуды.",
            "A string of length l with a bob is displaced by a small angle. The period "
            "T = 2π√(l/g) is independent of the bob mass and, for small swings, of the amplitude."),
           [line(150, 40, 290, 40, "axis"), line(220, 40, 220, 120, "primary"),
              circle(220, 120, 16, "primary", True), poly([[220, 40], [220, 120]], "helper")]
           + [poly([[220, 40], [150, 150]], "helper"), poly([[220, 40], [292, 152]], "helper")]
           + [circle(150, 150, 16, "secondary", True), circle(292, 152, 16, "secondary", True)]
           + [text(96, 168, "m₁", "m₁"), text(310, 172, "m₂", "m₂"), text(232, 90, "l", "l")]
           + [text(210, 232, "T = 2π√(l/g): обе массы — один период", "T = 2π√(l/g): equal periods")],
           model={"type": "pendulum", "periodFormula": "2*pi*sqrt(l/g)", "massIndependent": True,
                  "smallAmplitude": True}))

add(_frame_plot("wave-profile", ("Профиль волны: длина волны", "Wave profile: wavelength"),
                ("За время одного периода волна проходит расстояние λ = v·T. Соседние гребни "
                 "отстоят ровно на длину волны; частота задаётся источником, скорость — средой.",
                 "In one period the wave travels λ = v·T. Neighbouring crests are one wavelength "
                 "apart; the source sets the frequency and the medium the speed."),
                (0, 2 * math.pi, -1.4, 1.4), [("sine-wave", "primary", [(0, 2 * math.pi)])],
                ("x, м", "y, м"),
                xticks=[(0, bi("0")), (math.pi / 2, bi("λ/4")), (math.pi, bi("λ/2")),
                        (3 * math.pi / 2, bi("3λ/4")), (2 * math.pi, bi("λ"))],
                yticks=[-1, 0, 1],
                markers=[(math.pi / 2, 1, ("гребень", "crest"), 0, -16),
                         (3 * math.pi / 2, -1, ("впадина", "trough"), 0, 22)]))

add(figure("echo-path", ("Эхо и эхолот: путь туда и обратно", "Echo: the doubled path"),
           ("Сигнал идёт до препятствия и возвращается, поэтому 2s = v·t и s = v·t/2. "
            "В воздухе v ≈ 340 м/с: за 2 с эхо приходит от препятствия на 340 м.",
            "The pulse travels to the obstacle and back, so 2s = v·t and s = v·t/2. In air "
            "v ≈ 340 m/s: an echo after 2 s comes from 340 m away."),
           [rect(60, 130, 40, 90, "region", True), line(100, 90, 100, 220, "primary")]
           + [*arrow(120, 120, 300, 120, "primary"), *arrow(300, 170, 120, 170, "secondary")]
           + [text(210, 106, "туда: s = v·t₁", "there: s = v·t₁"), text(210, 190, "обратно: s = v·t₂", "back: s = v·t₂")]
           + [text(330, 132, "препятствие", "obstacle"), text(210, 246, "2s = v·t → s = v·t/2", "2s = v·t → s = v·t/2")],
           model={"type": "echo", "roundTrip": True, "speedAir": 340}))

# --------------------------------------------------------------------------- #
#  Оптика
# --------------------------------------------------------------------------- #

add(figure("reflection-mirror", ("Отражение: углы от перпендикуляра", "Reflection: angles from the normal"),
           ("Луч падает на зеркало и отражается: угол падения равен углу отражения, оба "
            "отсчитываются от перпендикуляра к поверхности, а не от самого зеркала.",
            "A ray hits the mirror and reflects: the angle of incidence equals the angle of "
            "reflection, both measured from the normal to the surface."),
           [line(40, 210, 380, 210, "axis"), line(210, 210, 210, 60, "helper")]
           + [*arrow(110, 110, 210, 210, "primary"), *arrow(210, 210, 310, 110, "secondary")]
           + [text(126, 100, "падающий луч", "incident ray"), text(300, 100, "отражённый", "reflected"),
              text(216, 84, "перпендикуляр N", "normal N"),
              text(160, 186, "α", "α"), text(252, 186, "α", "α"), text(210, 240, "α = α", "α = α")],
           model={"type": "reflection", "incidenceEqualsReflection": True, "anglesFromNormal": True}))

add(figure("refraction-ray", ("Преломление: к перпендикуляру", "Refraction: towards the normal"),
           ("При переходе в оптически более плотную среду луч отклоняется к перпендикуляру, "
            "скорость света уменьшается, n = sin α / sin γ > 1.",
            "Entering an optically denser medium, the ray bends towards the normal, light slows "
            "down and n = sin α / sin γ > 1."),
           [line(40, 140, 380, 140, "axis"), line(210, 140, 210, 50, "helper"), line(210, 140, 210, 230, "helper")]
           + [*arrow(110, 60, 210, 140, "primary"), *arrow(210, 140, 268, 222, "secondary")]
           + [text(232, 100, "воздух, n₁", "air, n₁"), text(250, 196, "стекло, n₂", "glass, n₂"),
              text(160, 118, "α", "α"), text(224, 176, "γ", "γ")]
           + [text(210, 262, "n₁ sin α = n₂ sin γ, α > γ", "n₁ sin α = n₂ sin γ, α > γ")],
           model={"type": "refraction", "bendsTowardsNormal": True, "alphaGreaterGamma": True}))

add(figure("lens-image", ("Тонкая линза: действительное изображение", "Thin lens: real image"),
           ("Собирающая линза: 1/F = 1/d + 1/f. Предмет стоит дальше фокуса, изображение "
            "действительное и перевёрнутое; при d < F изображение мнимое и прямое.",
            "A converging lens: 1/F = 1/d + 1/f. Beyond the focus the image is real and "
            "inverted; for d < F it becomes virtual and upright."),
           [line(40, 140, 400, 140, "axis"), ellipse(210, 140, 14, 78, "helper")]
           + [*arrow(120, 140, 120, 90, "primary"), *arrow(300, 140, 300, 198, "secondary")]
           + [line(120, 90, 300, 198, "helper"), line(120, 90, 300, 82, "helper"), line(120, 140, 300, 140, "helper")]
           + [text(120, 82, "предмет", "object"), text(300, 214, "изображение", "image"),
              text(226, 128, "F", "F"), circle(210, 140, 3, "point", True),
              text(160, 158, "d", "d"), text(260, 158, "f", "f"), text(210, 258, "1/F = 1/d + 1/f", "1/F = 1/d + 1/f")],
           model={"type": "lens", "formula": "1/F = 1/d + 1/f", "image": "real-inverted"}))

# --------------------------------------------------------------------------- #
#  Квантовые явления
# --------------------------------------------------------------------------- #

add(figure("photoeffect-scheme", ("Фотоэффект: энергия фотона", "Photoelectric effect"),
           ("Фотон с энергией hν выбивает электрон: hν = Aвых + Eк. Красную границу задаёт "
            "работа выхода; яркость света меняет число электронов, но не энергию одного фотона.",
            "A photon of energy hν releases an electron: hν = A_escape + E_kinetic. The work "
            "function sets the red threshold; brightness changes the count, not one photon's energy."),
           [rect(150, 90, 130, 130, "region", True), line(150, 90, 280, 90, "primary")]
           + [*arrow(60, 60, 150, 60, "primary"), text(66, 44, "hν", "hν")]
           + [*arrow(285, 155, 356, 155, "secondary"), text(320, 138, "e⁻", "e⁻")]
           + [text(210, 246, "hν = Aвых + Eк", "hν = A_escape + E_kinetic"),
              text(210, 70, "металл: Aвых > 0", "metal: A_escape > 0")],
           model={"type": "photoeffect", "equation": "h*nu = A + E", "thresholdFromWorkFunction": True}))

add(_frame_plot("decay-graph", ("Закон радиоактивного распада", "Radioactive decay law"),
                ("N = N₀·2^(−t/T): за каждый период полураспада остаётся половина ядер. "
                 "Через три периода — одна восьмая; период не зависит от внешних условий.",
                 "N = N₀·2^(−t/T): each half-life leaves half of the nuclei. After three "
                 "half-lives one eighth remains; the half-life is independent of conditions."),
                (0, 4, 0, 1.1), [("decay", "primary", [(0, 4.2)])],
                ("t, периоды T", "N/N₀"),
                xticks=[0, 1, 2, 3, 4], yticks=[0, 0.25, 0.5, 0.75, 1],
                markers=[(1, 0.5, ("1/2", "1/2"), -14, -8), (2, 0.25, ("1/4", "1/4"), -14, -8),
                         (3, 0.125, ("1/8", "1/8"), -16, -8)]))


def payload():
    return deepcopy(FIGURES)


def validate(figures):
    """Строгий контракт JSON → SVG: опасная или неполная фигура отвергается целиком."""
    if not isinstance(figures, dict) or not figures:
        raise ValueError("diagram catalogue is empty")
    for key, entry in figures.items():
        if entry.get("id") != key or not key or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in key):
            raise ValueError("invalid diagram id")
        if set(entry) - {"id", "title", "caption", "width", "height", "drawing", "legend", "model"}:
            raise ValueError("unexpected diagram field")
        for field in ("title", "caption"):
            if not isinstance(entry.get(field), dict) or any(
                    not isinstance(entry[field].get(lang), str) or not entry[field][lang].strip()
                    for lang in ("ru", "en")):
                raise ValueError(f"diagram {key} needs bilingual {field}")
        if entry.get("width") != WIDTH or entry.get("height") != HEIGHT:
            raise ValueError("invalid diagram viewport")
        drawing = entry.get("drawing")
        if not isinstance(drawing, list) or not 1 <= len(drawing) <= 250:
            raise ValueError("invalid diagram drawing")
        for item in drawing:
            kind = item.get("kind")
            if kind not in FIELDS or set(item) - ({"kind", "role", "filled"} | FIELDS[kind]) \
                    or FIELDS[kind] - set(item):
                raise ValueError("unsafe or incomplete diagram primitive")
            if item.get("role") not in ROLES or not isinstance(item.get("filled"), bool):
                raise ValueError("invalid diagram styling")
            for field in FIELDS[kind] - {"points", "text", "anchor"}:
                v = item[field]
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) \
                        or not 0 <= v <= (HEIGHT if field.startswith("y") or field in {"cy", "height", "ry"} else WIDTH):
                    raise ValueError("invalid diagram coordinate")
                if field in {"r", "rx", "ry", "width", "height"} and v <= 0:
                    raise ValueError("invalid diagram size")
            if kind in {"polyline", "polygon"}:
                pts = item["points"]
                if not isinstance(pts, list) or not (3 if kind == "polygon" else 2) <= len(pts) <= 500:
                    raise ValueError("invalid diagram points")
                for point in pts:
                    if not isinstance(point, list) or len(point) != 2 \
                            or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                                   for v in point) or not (0 <= point[0] <= WIDTH and 0 <= point[1] <= HEIGHT):
                        raise ValueError("invalid diagram point")
            if kind == "text":
                if item["anchor"] not in {"start", "middle", "end"} or not isinstance(item["text"], dict) \
                        or any(not isinstance(item["text"].get(lang), str) or not item["text"][lang].strip()
                               for lang in ("ru", "en")):
                    raise ValueError("invalid bilingual diagram label")
        for item in entry.get("legend", []):
            if set(item) != {"role", "text"} or item["role"] not in ROLES or not isinstance(item["text"], dict) \
                    or any(not isinstance(item["text"].get(lang), str) or not item["text"][lang].strip()
                           for lang in ("ru", "en")):
                raise ValueError("invalid diagram legend")
    return figures
