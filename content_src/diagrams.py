"""Deterministic, offline mathematical figures as safe typed SVG primitives.

No raw SVG/HTML, scripts, images, paths, CSS or external URLs in content.
Plot curves are sampled from named Python functions (never evaluated in JS).
Coordinates are viewport units; geometry marked as a perspective sketch is not
meant for measuring physical lengths. See tests/test_diagrams.py for math gates.
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
FUNCTIONS = {
    "square": lambda x: x*x, "cube": lambda x: x*x*x,
    "parabola-roots": lambda x: (x-1)*(x-3),
    "shifted-square": lambda x: (x-1)**2-1,
    "linear": lambda x: 2*x+1, "taxi": lambda x: 2*x+5, "distance": lambda x: 4*x, "tangent": lambda x: 2*x-1,
    "speed-tangent": lambda x: 4*x-4,
    "reciprocal": lambda x: 4/x, "square-root": lambda x: math.sqrt(x-1),
    "sine": math.sin, "cosine": math.cos,
    "exponential": lambda x: 2**x, "logarithm": math.log2,
    "extrema": lambda x: x**3-3*x,
    "segment": lambda x: (x-2)**2-1,
    "constant-half": lambda x: 0.5, "constant-eight": lambda x: 8,
    "parameter-low": lambda x: (x-2)**2-1,
    "parameter-zero": lambda x: (x-2)**2,
    "parameter-high": lambda x: (x-2)**2+1,
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
    angle = math.atan2(y2-y1, x2-x1)
    a = (x2-10*math.cos(angle-.4), y2-10*math.sin(angle-.4))
    b = (x2-10*math.cos(angle+.4), y2-10*math.sin(angle+.4))
    return [line(x1, y1, x2, y2, role), poly([a, (x2, y2), b], role, True, True)]


def figure(key, title, caption, drawing, *, legend=None, model=None):
    result = {"id": key, "title": bi(*title), "caption": bi(*caption),
              "width": WIDTH, "height": HEIGHT, "drawing": drawing}
    if legend:
        result["legend"] = [{"role": role, "text": bi(*label)} for role, label in legend]
    if model:
        result["model"] = model
    return result


def plot(key, title, caption, bounds, series, *, xticks=None, yticks=None, markers=None, legend=None):
    xmin, xmax, ymin, ymax = bounds
    frame = [48, 28, 324, 204]
    left, top, width, height = frame

    def pos(x, y):
        return left+(x-xmin)/(xmax-xmin)*width, top+(ymax-y)/(ymax-ymin)*height

    def label(value):
        common = f"{value:g}".replace("-", "−")
        return bi(common.replace(".", ","), common)

    drawing = []
    xticks = xticks if xticks is not None else list(range(math.ceil(xmin), math.floor(xmax)+1))
    yticks = yticks if yticks is not None else list(range(math.ceil(ymin), math.floor(ymax)+1))
    for tick in xticks:
        x, tx = tick if isinstance(tick, tuple) else (tick, label(tick))
        px, _ = pos(x, 0)
        if left <= px <= left+width:
            drawing.append(line(px, top, px, top+height, "grid"))
            item = text(px, top+height+21, "")
            item["text"] = tx
            drawing.append(item)
    for tick in yticks:
        y, tx = tick if isinstance(tick, tuple) else (tick, label(tick))
        _, py = pos(0, y)
        if top <= py <= top+height:
            drawing.append(line(left, py, left+width, py, "grid"))
            item = text(left-9, py+5, "", anchor="end")
            item["text"] = tx
            drawing.append(item)
    axis_y = pos(0, min(ymax, max(ymin, 0)))[1]
    axis_x = pos(min(xmax, max(xmin, 0)), 0)[0]
    drawing += arrow(left, axis_y, left+width+12, axis_y, "axis")
    drawing += arrow(axis_x, top+height, axis_x, top-12, "axis")
    drawing += [text(left+width+24, axis_y+6, "x"), text(axis_x+14, top-10, "y")]
    descriptions = []
    for fn, role, domains in series:
        count = 0
        for a, b in domains:
            segment = []
            for index in range(121):
                x = a+(b-a)*index/120
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
        label = text(px+dx, py+dy, *label_text) if isinstance(label_text, tuple) else text(px+dx, py+dy, label_text)
        drawing += [circle(px, py, 4, "point", True), label]
    return figure(key, title, caption, drawing, legend=legend,
                  model={"type": "plot", "bounds": list(bounds), "frame": frame, "series": descriptions})


FIGURES = {}


def add(entry):
    if entry["id"] in FIGURES:
        raise ValueError("duplicate diagram id")
    FIGURES[entry["id"]] = entry


add(plot("parabola-roots", ("Корни — пересечения с осью", "Roots are x-axis intersections"),
         ("y = (x − 1)(x − 3). Корни 1 и 3, вершина (2;−1). Для y ≤ 0 берём [1;3], включая обе границы.",
          "y = (x − 1)(x − 3). Roots 1 and 3, vertex (2,−1). For y ≤ 0 choose [1,3], including both endpoints."),
         (0, 4, -2, 4), [("parabola-roots", "primary", [(0,4)])],
         markers=[(1,0,"(1;0)",-15,-14),(3,0,"(3;0)",18,-14),(2,-1,"(2;−1)",0,24)],
         yticks=[-2,-1,0,2,4]))
add(plot("domain-root", ("Где определён квадратный корень", "Where the square root is defined"),
         ("y = √(x − 1) начинается в (1;0): допустимы x ≥ 1, значения y ≥ 0. Слева от 1 действительного графика нет.",
          "y = √(x − 1) begins at (1,0): x ≥ 1 is allowed and y ≥ 0 is the range. No real graph exists to the left of 1."),
         (-1,5,-.5,2.5), [("square-root","primary",[(1,5)])], yticks=[0,1,2],
         markers=[(1,0,"(1;0)",18,-14),(5,2,"(5;2)",-24,-12)]))
add(plot("graph-shift", ("Сдвиг вправо и вниз", "Shift right and down"),
         ("Сплошная: y = x². Пунктирная: y = (x − 1)² − 1. Каждая точка переместилась на (1;−1), вершина стала (1;−1).",
          "Solid: y = x². Dashed: y = (x − 1)² − 1. Every point moves by (1,−1); the new vertex is (1,−1)."),
         (-2,4,-2,5), [("square","primary",[(-2,4)]),("shifted-square","secondary",[(-2,4)])],
         yticks=[-2,0,2,4], markers=[(0,0,"(0;0)",-20,-12),(1,-1,"(1;−1)",20,24)],
         legend=[("primary",("y = x²","y = x²")),("secondary",("y = (x − 1)² − 1","y = (x − 1)² − 1"))]))
add(plot("linear-graph", ("Постоянная прибавка: прямая", "Constant increase: a line"),
         ("y = 2x + 1. При увеличении x на 1 значение y растёт на 2. Начальное значение при x = 0 равно 1.",
          "y = 2x + 1. Increasing x by 1 increases y by 2. The starting value at x = 0 is 1."),
         (-2,3,-4,8), [("linear","primary",[(-2,3)])], yticks=[-4,-2,0,2,4,6,8],
         markers=[(0,1,"(0;1)",28,-7),(1,3,"(1;3)",26,-7)]))
add(plot("hyperbola", ("Обратная пропорциональность", "Inverse proportionality"),
         ("y = 4/x, x ≠ 0. Чем больше положительный x, тем меньше доля 4/x. Ветви не соединены через ноль: там функция не определена.",
          "y = 4/x, x ≠ 0. A larger positive x gives a smaller share 4/x. The branches are not connected across zero, where the function is undefined."),
         (-5,5,-5,5), [("reciprocal","primary",[(-5,-.1),(.1,5)])],
         xticks=[-4,-2,0,2,4], yticks=[-4,-2,0,2,4],
         markers=[(2,2,"(2;2)",-20,-15),(4,1,"(4;1)",-4,-16)]))
add(plot("even-odd", ("Чётная и нечётная функции", "Even and odd functions"),
         ("y = x² симметричен относительно оси y. y = x³ симметричен относительно начала: у (−1;−1) и (1;1) координаты противоположны.",
          "y = x² is symmetric about the y-axis. y = x³ is symmetric about the origin: (−1,−1) and (1,1) have opposite coordinates."),
         (-2,2,-4,4), [("square","primary",[(-2,2)]),("cube","secondary",[(-2,2)])],
         yticks=[-4,-2,0,2,4],
         legend=[("primary",("y = x²","y = x²")),("secondary",("y = x³","y = x³"))]))
add(plot("sine-solutions", ("Две высоты за оборот", "Two crossings per turn"),
         ("sin x = 1/2 на [0;2π]: пересечения с уровнем 1/2 при π/6 и 5π/6. За границами выбранного оборота периодические решения продолжаются.",
          "sin x = 1/2 on [0,2π]: crossings with height 1/2 occur at π/6 and 5π/6. Periodic solutions continue beyond the selected turn."),
         (0,2*math.pi,-1.25,1.25), [("sine","primary",[(0,2*math.pi)]),("constant-half","secondary",[(0,2*math.pi)])],
         xticks=[(0,bi("0")),(math.pi/2,bi("π/2")),(math.pi,bi("π")),(3*math.pi/2,bi("3π/2")),(2*math.pi,bi("2π"))], yticks=[-1,0,1],
         markers=[(math.pi/6,.5,"π/6",0,-15),(5*math.pi/6,.5,"5π/6",0,-15)],
         legend=[("primary",("y = sin x","y = sin x")),("secondary",("y = 1/2","y = 1/2"))]))
add(plot("sine-cosine", ("Проекции вращения", "Projections of rotation"),
         ("За один оборот 0…2π координаты точки sin x и cos x повторяют свои значения. Синус в нуле равен 0, косинус — 1; обе функции принимают значения от −1 до 1.",
          "During one turn 0…2π, point coordinates sin x and cos x repeat. At zero sine is 0 and cosine 1; both range from −1 to 1."),
         (0,2*math.pi,-1.25,1.25), [("sine","primary",[(0,2*math.pi)]),("cosine","secondary",[(0,2*math.pi)])],
         xticks=[(0,bi("0")),(math.pi/2,bi("π/2")),(math.pi,bi("π")),(3*math.pi/2,bi("3π/2")),(2*math.pi,bi("2π"))], yticks=[-1,0,1],
         legend=[("primary",("y = sin x","y = sin x")),("secondary",("y = cos x","y = cos x"))]))
add(plot("exponential", ("Сколько удвоений до восьми", "How many doublings to eight"),
         ("Кривая y = 2ˣ достигает уровня y = 8 при x = 3. Точка (3;8) одновременно объясняет 2³ = 8 и log₂ 8 = 3.",
          "Curve y = 2ˣ reaches y = 8 at x = 3. Point (3,8) explains both 2³ = 8 and log₂ 8 = 3."),
         (-1,3.5,0,12), [("exponential","primary",[(-1,3.5)]),("constant-eight","secondary",[(-1,3.5)])], yticks=[0,2,4,8,12],
         markers=[(0,1,"(0;1)",24,0),(3,8,"(3;8)",0,-16)],
         legend=[("primary",("y = 2ˣ","y = 2ˣ")),("secondary",("y = 8","y = 8"))]))
add(plot("logarithm", ("Логарифм — обратный вопрос", "A logarithm asks the inverse question"),
         ("y = log₂ x определён только при x > 0. В точке (1;0) удвоений не нужно, (2;1) означает одно, (4;2) — два.",
          "y = log₂ x is defined only for x > 0. At (1,0) no doublings are needed; (2,1) means one, (4,2) means two."),
         (0,5,-3,3), [("logarithm","primary",[(.125,5)])], yticks=[-2,0,2],
         markers=[(1,0,"(1;0)",22,-13),(2,1,"(2;1)",23,-10),(4,2,"(4;2)",-18,-14)]))
add(plot("tangent", ("Касательная в точке (1;1)", "Tangent at (1,1)"),
         ("Для y = x² касательная в (1;1) — y = 2x − 1, наклон 2. Равенство x² = 2x − 1 даёт (x − 1)² = 0, один двукратный корень.",
          "For y = x² the tangent at (1,1) is y = 2x − 1, slope 2. Equating them gives (x − 1)² = 0, one double root."),
         (-1,3,-3,7), [("square","primary",[(-1,3)]),("tangent","secondary",[(-1,3)])], yticks=[-2,0,2,4,6],
         markers=[(1,1,"(1;1)",33,0)],
         legend=[("primary",("y = x²","y = x²")),("secondary",("y = 2x − 1","y = 2x − 1"))]))
add(plot("speed-tangent", ("Мгновенное изменение", "Instantaneous rate of change"),
         ("В модели s(t) = t² при t = 2: s = 4, наклон касательной 4. Если t — секунды, s — метры, производная измеряется в м/с; ось x изображает t, ось y — s.",
          "For s(t) = t² at t = 2, s = 4 and tangent slope is 4. With seconds and metres, the derivative uses m/s; the x-axis represents t and y represents s."),
         (0,3,-1,9), [("square","primary",[(0,3)]),("speed-tangent","secondary",[(0,3)])], yticks=[0,2,4,6,8],
         markers=[(2,4,"(2;4)",30,0)],
         legend=[("primary",("s = t²","s = t²")),("secondary",("s = 4t − 4","s = 4t − 4"))]))
add(plot("extrema", ("Где рост меняется на убывание", "Where increase becomes decrease"),
         ("y = x³ − 3x: местный максимум (−1;2), минимум (1;−2). Знак производной 3x² − 3: +, затем −, затем +. Эти экстремумы не являются глобальными на всей прямой.",
          "y = x³ − 3x has local maximum (−1,2) and minimum (1,−2). Its derivative 3x² − 3 has signs +, then −, then +. These are not global extrema on the entire real line."),
         (-2.2,2.2,-4,4), [("extrema","primary",[(-2.2,2.2)])], xticks=[-2,-1,0,1,2], yticks=[-4,-2,0,2,4],
         markers=[(-1,2,"(−1;2)",-3,-15),(1,-2,"(1;−2)",3,24)]))
add(plot("segment-extrema", ("Проверяем также концы отрезка", "Check the endpoints too"),
         ("y = (x − 2)² − 1, 0 ≤ x ≤ 3. Минимум −1 при x = 2; максимум 3 на левой границе x = 0. На рисунке показана только заданная часть графика.",
          "y = (x − 2)² − 1 for 0 ≤ x ≤ 3. Minimum −1 at x = 2; maximum 3 at left endpoint x = 0. Only the specified graph segment is drawn."),
         (-.5,3.5,-2,4), [("segment","primary",[(0,3)])], xticks=[0,1,2,3], yticks=[-2,-1,0,2,4],
         markers=[(0,3,"(0;3)",25,-12),(2,-1,"(2;−1)",0,24),(3,0,"(3;0)",10,-14)]))
for suffix, fn, p, label in [("two","parameter-low",3,"D > 0"),("one","parameter-zero",4,"D = 0"),("none","parameter-high",5,"D < 0")]:
    count_ru, count_en = {3:("Два корня","Two roots"),4:("Один двукратный корень","One double root"),5:("Действительных корней нет","No real roots")}[p]
    add(plot("parameter-"+suffix, (count_ru, count_en),
             (f"y = x² − 4x + {p}, {label}. Параметр меняет высоту параболы; корни — пересечения с осью x.",
              f"y = x² − 4x + {p}, {label}. The parameter changes the parabola's height; roots are x-axis intersections."),
             (0,4,-2,5), [(fn,"primary",[(0,4)])], yticks=[-2,0,2,4]))


def discrete(key, title, caption, values, ylabel):
    d = []
    left, base, step, scale = 76, 223, 64, 160/max(values)
    d += arrow(left-22,base,left+step*(len(values)-1)+22,base,"axis")
    d += arrow(left-22,base,left-22,35,"axis")
    d += [text(385,base+5,"n"),text(26,28,ylabel)]
    for index, value in enumerate(values):
        x, y = left+step*index, base-scale*value
        d += [line(x,base,x,y,"helper"),circle(x,y,5,"point",True),text(x,y-12,str(value)),text(x,base+23,str(index+1))]
    return figure(key,title,caption,d, model={"type":"sequence","values":values,"joined":False})


add(discrete("arithmetic-dots", ("Одинаковая прибавка", "Equal increments"),
             ("Взносы 10, 15, 20, 25, 30 рублей: между соседними точками прибавка 5. n — номер недели, целое число. Всего за пять недель 100 рублей.",
              "Payments 10,15,20,25,30 rubles: each adjacent value adds 5. n is an integer week number. The five-week total is 100 rubles."), [10,15,20,25,30],"aₙ"))
add(discrete("geometric-dots", ("Одинаковый множитель", "Equal multipliers"),
             ("1, 2, 4, 8, 16: соседние значения отличаются в 2 раза, а прибавки растут. Пять значений дают сумму 31. Точки не соединены: n принимает только целые номера.",
              "1,2,4,8,16: adjacent values have ratio 2, but increments grow. Five values sum to 31. Points are not joined because n takes integer indices only."), [1,2,4,8,16],"aₙ"))

add(plot("taxi-cost", ("Переводим цену в уравнение", "Turn a price into an equation"),
         ("Плата 5 + 2x рублей при x километрах. Точка (6;17) показывает: поездка за 17 рублей имеет длину 6 км. Ось x — км, y — рубли; модель действует при x ≥ 0.",
          "Cost is 5 + 2x rubles for x kilometres. Point (6,17) shows a 17-ruble trip covers 6 km. x is km, y rubles; the model requires x ≥ 0."),
         (0,7,0,20), [("taxi","primary",[(0,7)])], xticks=[0,2,4,6], yticks=[0,5,10,15,20],
         markers=[(0,5,"(0;5)",27,-7),(6,17,"(6;17)",-2,-15)]))
add(plot("constant-speed", ("Постоянная скорость: путь растёт равномерно", "Constant speed: distance grows evenly"),
         ("s = 4t: за 1,5 часа пройдено 6 км. Ось x изображает t в часах, y — s в километрах. Прямая через начало относится к движению с постоянной скоростью и нулевым начальным путём.",
          "s = 4t: 1.5 hours covers 6 km. x represents t in hours and y distance s in kilometres. A line through the origin models constant speed with zero initial distance."),
         (0,2,0,8), [("distance","primary",[(0,2)])], xticks=[0,.5,1,1.5,2], yticks=[0,2,4,6,8],
         markers=[(1.5,6,("(1,5;6)","(1.5,6)"),-20,-15)]))
# Drawings for fractions, intervals and geometry are below; all are local data.
add(figure("fraction-bar", ("Три восьмых одного целого", "Three eighths of one whole"),
           ("Вся полоска — одно целое, восемь равных частей. Закрашены три: 3/8. Четыре части из восьми составляют половину.",
            "The whole strip is one unit in eight equal parts. Three are shaded: 3/8. Four eighths make one half."),
           [rect(42+42*i,100,42,64,"region" if i<3 else "helper") for i in range(8)] +
           [text(105,80,"3/8"),line(42,186,210,186,"secondary"),text(126,211,"4/8 = 1/2"),text(210,258,"Одна и та же единица","The same whole")],
           model={"type":"fraction","parts":8,"shaded":3}))
add(figure("identity-areas", ("Из чего состоит (a + b)²", "Pieces of (a + b)²"),
           ("a = 5, b = 2. Большой квадрат состоит из a² = 25, двух прямоугольников ab = 10 и b² = 4: всего 49. Все длины на этой схеме в одном масштабе.",
            "a = 5, b = 2. The large square has a² = 25, two rectangles ab = 10 and b² = 4: total 49. All lengths use one scale."),
           [rect(102,36,140,140,"region"),rect(242,36,56,140,"secondary"),rect(102,176,140,56,"secondary"),rect(242,176,56,56,"region"),
            text(172,110,"a² = 25"),text(270,110,"ab"),text(172,210,"ab = 10"),text(270,210,"b²"),
            text(172,26,"a = 5"),text(270,26,"b = 2"),text(200,265,"25 + 10 + 10 + 4 = 49")],
           model={"type":"identity","a":5,"b":2,"scale":28}))


def numberline(key,title,caption,marks,segments):
    # Fixed real interval [-5,5], same scale for all marks.
    left,right,y,scale=42,378,144,33.6
    px=lambda x: left+(x+5)*scale
    d=arrow(left,y,right+10,y,"axis")
    for value in range(-5,6):
        d += [line(px(value),y-4,px(value),y+4,"axis"),text(px(value),y+24,str(value).replace('-','−'))]
    for a,b,label_text,role in segments:
        d += [line(px(a),y-22,px(b),y-22,role),text((px(a)+px(b))/2,y-42,label_text)]
    for x,closed in marks:
        d.append(circle(px(x),y,6,"point" if closed else "openpoint",closed))
    return figure(key,title,caption,d,model={"type":"numberline","marks":[{"x":x,"closed":closed} for x,closed in marks]})


add(numberline("absolute-distance", ("Расстояние без направления", "Distance without direction"),
               ("Точки −4 и 4 на одинаковом расстоянии от нуля: |−4| = |4| = 4. Координаты разные, расстояния одинаковые.",
                "Points −4 and 4 are equally far from zero: |−4| = |4| = 4. Coordinates differ, distances agree."),
               [(-4,True),(0,True),(4,True)],[(-4,0,"4","primary"),(0,4,"4","secondary")]))
add(numberline("absolute-interval", ("Не дальше двух единиц от трёх", "Within two units of three"),
               ("|x − 3| ≤ 2 означает [1;5]. Обе крайние точки включены: они ровно на расстоянии 2 от центра 3.",
                "|x − 3| ≤ 2 means [1,5]. Both endpoints are included, exactly 2 units from centre 3."),
               [(1,True),(3,True),(5,True)],[(1,5,"[1;5]","primary")]))
add(numberline("interval-signs", ("Знак дроби и запрещённая точка", "A fraction's signs and excluded point"),
               ("(x − 1)/(x + 2) ≥ 0: решение (−∞;−2) ∪ [1;+∞). Пустая точка −2 запрещена знаменателем; закрашенная 1 даёт ноль. Стрелки оси продолжаются за рисунок.",
                "(x − 1)/(x + 2) ≥ 0 has solution (−∞,−2) ∪ [1,+∞). Open point −2 is excluded by the denominator; filled 1 gives zero. The number line continues beyond the drawing."),
               [(-2,False),(1,True)],[(-5,-2,"+","primary"),(-2,1,"−","secondary"),(1,5,"+","primary")]))

add(figure("percent-stages", ("Проценты от новой базы", "Percentages use the new base"),
           ("100 рублей → скидка 20% → 80 → наценка 10% от 80 → 88. Последний столбец ниже первого: общая потеря 12%, не 10%.",
            "100 rubles → 20% discount → 80 → 10% increase on 80 → 88. The final bar is below the first: total decrease 12%, not 10%."),
           [line(50,222,374,222,"axis"),rect(65,52,64,170,"region"),rect(176,86,64,136,"secondary"),rect(287,72.4,64,149.6,"region"),
            text(97,40,"100"),text(208,74,"80"),text(319,61,"88"),text(97,247,"До","Before"),text(208,247,"−20%"),text(319,247,"+10%"),text(210,20,"рубли","rubles")],
           model={"type":"percentages","values":[100,80,88]}))


def circle_point(angle,cx=210,cy=150,r=86):
    return cx+r*math.cos(angle),cy-r*math.sin(angle)


def arc(start,end,cx=210,cy=150,r=86,role="secondary"):
    return poly([circle_point(start+(end-start)*i/60,cx,cy,r) for i in range(61)],role)


cx,cy,r=210,146,86
px,py=circle_point(math.pi/6,cx,cy,r)
add(figure("unit-circle", ("Синус и косинус — координаты", "Sine and cosine are coordinates"),
           ("Единичный радиус OP = 1, угол 30°. P = (√3/2;1/2). Горизонтальная проекция — cos 30°, вертикальная — sin 30°; сумма их квадратов 1.",
            "Unit radius OP = 1, angle 30°. P = (√3/2,1/2). Horizontal projection is cos 30°, vertical is sin 30°; their squares sum to 1."),
           [circle(cx,cy,r),*arrow(96,cy,328,cy,"axis"),*arrow(cx,246,cx,43,"axis"),line(cx,cy,px,py),line(px,py,px,cy,"secondary"),line(cx,py,px,py,"helper"),
            circle(px,py,4,"point",True),arc(0,math.pi/6,cx,cy,30),text(cx-14,cy+19,"O"),text(px+13,py-8,"P"),text(344,cy+5,"x"),text(cx+16,42,"y"),
            text(250,172,"√3/2"),text(311,126,"1/2"),text(249,136,"30°"),text(175,56,"OP = 1")],
           model={"type":"unit-circle","angle":math.pi/6,"point":[math.cos(math.pi/6),math.sin(math.pi/6)]}))
add(figure("radian-arc", ("Дуга и радианы", "Arc length and radians"),
           ("Красная дуга — 60° = π/3 радиан, треть π и шестая часть оборота. При R = 6 её длина R · π/3 = 2π. Радиус и дуга — разные величины.",
            "The highlighted arc is 60° = π/3 radians, one sixth of a turn. With R = 6, length R × π/3 = 2π. Radius and arc length are different quantities."),
           [circle(210,145,88),line(210,145,298,145),line(210,145,*circle_point(math.pi/3,210,145,88)),arc(0,math.pi/3,210,145,88),arc(0,math.pi/3,210,145,28),
            text(233,132,"60°"),text(265,166,"R = 6"),text(329,92,"2π"),text(210,261,"α = π/3, L = Rα")],
           model={"type":"arc","radius":6,"angle":math.pi/3,"length":2*math.pi}))
pa=circle_point(math.pi/6,210,148,86)
pb=circle_point(5*math.pi/6,210,148,86)
add(figure("circle-two-solutions", ("Одна высота, два угла", "One height, two angles"),
           ("На единичной окружности высоту 1/2 имеют две точки: углы π/6 и 5π/6. За каждый полный оборот они повторяются, давая два семейства решений sin x = 1/2.",
            "Two unit-circle points have height 1/2, at π/6 and 5π/6. Each full turn repeats them, producing two families for sin x = 1/2."),
           [circle(210,148,86),*arrow(103,148,326,148,"axis"),*arrow(210,245,210,42,"axis"),line(115,105,305,105,"secondary"),line(210,148,*pa),line(210,148,*pb),
            circle(*pa,4,"point",True),circle(*pb,4,"point",True),text(308,95,"π/6"),text(112,95,"5π/6"),text(339,110,"1/2"),text(210,263,"sin x = 1/2")],
           model={"type":"sine-solutions","angles":[math.pi/6,5*math.pi/6],"height":.5}))

# Plane diagrams use an honest common scale when asserting metric proportions.
a,b,c=(70,217),(294,217),(70,49)
add(figure("ladder-triangle", ("Лестница, стена и пол: 3–4–5", "Ladder, wall and ground: 3–4–5"),
           ("AB = 4 м, AC = 3 м, BC = 5 м. Угол A прямой. Лестница BC — гипотенуза: 3² + 4² = 5². Все три стороны нарисованы в одном масштабе.",
            "AB = 4 m, AC = 3 m, BC = 5 m. Angle A is right. Ladder BC is the hypotenuse: 3² + 4² = 5². All sides share one scale."),
           [poly([a,b,c],closed=True),poly([(70,202),(85,202),(85,217)],"helper"),text(58,237,"A"),text(311,229,"B"),text(55,45,"C"),
            text(181,241,"4 м","4 m"),text(41,136,"3 м","3 m"),text(199,128,"5 м","5 m"),text(183,27,"3² + 4² = 5²")],
           model={"type":"right-triangle","legs":[3,4],"hypotenuse":5,"scale":56}))
# A scalene triangle: altitude, midpoint median, angle-bisector foot are distinct.
A,B,C=(72,218),(342,218),(153,48)
ca,cb=math.dist(C,A),math.dist(C,B)
D=(A[0]+(B[0]-A[0])*ca/(ca+cb),218)
add(figure("triangle-lines", ("Высота, медиана, биссектриса", "Altitude, median and angle bisector"),
           ("Из вершины C: высота CH перпендикулярна AB; медиана CM идёт к середине M; биссектриса CD делит угол C поровну. В этом разностороннем треугольнике H, D и M различны.",
            "From vertex C: altitude CH is perpendicular to AB; median CM reaches midpoint M; bisector CD halves angle C. In this scalene triangle H, D and M differ."),
           [poly([A,B,C],closed=True),line(*C,153,218,"helper"),line(*C,207,218,"secondary"),line(*C,*D,"primary"),
            poly([(153,202),(169,202),(169,218)],"helper"),text(59,238,"A"),text(356,237,"B"),text(153,34,"C"),text(147,238,"H"),text(D[0],262,"D"),text(216,238,"M"),
            line(136,210,136,225,"secondary"),line(280,210,280,225,"secondary")],
           legend=[("helper",("CH: высота","CH: altitude")),("secondary",("CM: медиана","CM: median")),("primary",("CD: биссектриса","CD: bisector"))],
           model={"type":"triangle-lines","vertices":[list(A),list(B),list(C)],"altitude":[153,218],"median":[207,218],"bisector":list(D)}))
add(figure("triangle-area", ("Половина прямоугольника", "Half a rectangle"),
           ("Прямоугольник 4 × 3 имеет площадь 12. Диагональ делит его на два равных треугольника площадью 6. Высота 3 перпендикулярна основанию 4.",
            "A 4 × 3 rectangle has area 12. Its diagonal gives two equal triangles of area 6. Height 3 is perpendicular to base 4."),
           [rect(98,50,224,168,"helper"),poly([(98,218),(322,218),(98,50)],"region",closed=True),
            text(210,242,"4"),text(75,137,"3"),text(169,171,"S = 6"),text(255,110,"S = 6")],
           model={"type":"triangle-area","base":4,"height":3,"area":6}))
add(figure("parallelogram-area", ("Нужна высота, не наклонная сторона", "Use the height, not the sloping side"),
           ("Основание a = 6, высота h = 3: S = 18. Наклонная сторона b длиннее h. Перенос бокового треугольника даёт прямоугольник с теми же a и h.",
            "Base a = 6 and height h = 3 give S = 18. Sloping side b is longer than h. Moving a side triangle forms a rectangle with the same a and h."),
           [poly([(63,218),(297,218),(357,101),(123,101)],"region",closed=True),line(123,101,123,218,"secondary"),
            poly([(123,202),(139,202),(139,218)],"helper"),text(213,245,"a = 6"),text(148,166,"h = 3"),text(76,155,"b"),text(240,168,"S = 18")],
           model={"type":"parallelogram","base":6,"height":3,"area":18}))
add(figure("similar-triangles", ("Длины ×2, площади ×4", "Lengths ×2, areas ×4"),
           ("Малый треугольник с катетами 3 и 4 имеет площадь 6; большой с 6 и 8 — 24. Одинаковый масштаб чертежа показывает коэффициент подобия 2 и отношение площадей 4.",
            "The small triangle's legs 3 and 4 give area 6; the large triangle's 6 and 8 give 24. One drawing scale shows similarity factor 2 and area ratio 4."),
           [poly([(44,218),(124,218),(44,158)],"region",closed=True),poly([(187,218),(347,218),(187,98)],"region",closed=True),
            text(28,190,"3"),text(82,241,"4"),text(172,162,"6"),text(268,241,"8"),text(64,206,"6"),text(230,195,"24"),text(209,40,"k = 2, S₂/S₁ = 4")],
           model={"type":"similarity","small":[3,4,5],"large":[6,8,10],"areas":[6,24],"scale":20}))
# A 120-degree central angle and 60-degree inscribed angle subtend the same minor arc.
O=(204,146); R=82
P=circle_point(0,*O,R); Q=circle_point(2*math.pi/3,*O,R); V=circle_point(4*math.pi/3,*O,R)
add(figure("circle-angles", ("Одна дуга, два угла", "The same arc, two angles"),
           ("Центральный угол POQ = 120°, вписанный PVQ = 60° опираются на одну дугу PQ. V лежит на другой части окружности. Вписанный угол вдвое меньше.",
            "Central angle POQ = 120° and inscribed angle PVQ = 60° subtend the same arc PQ. V lies on the other arc. The inscribed angle is half the central angle."),
           [circle(*O,R),line(*O,*P),line(*O,*Q),line(*V,*P,"secondary"),line(*V,*Q,"secondary"),arc(0,2*math.pi/3,*O,R),
            text(196,166,"O"),text(P[0]+15,P[1]+5,"P"),text(Q[0]-10,Q[1]-10,"Q"),text(V[0]-15,V[1]+18,"V"),text(224,116,"120°"),text(V[0]+24,V[1]-25,"60°")],
           model={"type":"circle-angles","central":120,"inscribed":60,"centre":list(O),"radius":R,"points":[list(P),list(Q),list(V)]}))
add(figure("circle-tangent", ("Радиус перпендикулярен касательной", "Radius is perpendicular to tangent"),
           ("Окружность с центром O касается прямой в T. OT — радиус, угол с касательной 90°. Хорда AB соединяет две точки окружности; весь внутренний круг — другая фигура, чем только обод.",
            "A circle centred at O touches the line at T. Radius OT makes 90° with the tangent. Chord AB joins two circle points; the filled disk differs from just the rim."),
           [circle(206,132,78),line(206,132,206,210),line(71,210,349,210,"secondary"),poly([(206,194),(222,194),(222,210)],"helper"),
            line(138.45,93,273.55,93,"helper"),text(191,139,"O"),text(205,232,"T"),text(136,82,"A"),text(278,82,"B"),text(231,169,"R"),text(210,264,"OT ⟂ касательной","OT ⟂ tangent")],
           model={"type":"tangent-circle","centre":[206,132],"radius":78,"contact":[206,210],"lineY":210}))

# Solid figures are labelled perspective sketches, not scale measurements.
def box_drawing(x=104,y=218,w=166,h=135,dx=54,dy=-39):
    a,b,c,d=(x,y),(x+w,y),(x+w,y-h),(x,y-h)
    aa,bb,cc,dd=[(px+dx,py+dy) for px,py in (a,b,c,d)]
    return [poly([a,b,c,d],closed=True),poly([d,dd,cc,c],closed=True),poly([b,bb,cc,c],closed=True),
            line(*a,*aa,"helper"),line(*aa,*bb,"helper"),line(*aa,*dd,"helper")]


add(figure("prism-box", ("Коробка: площадь слоя × высота", "A box: layer area × height"),
           ("Схематическая перспектива прямоугольной призмы: основание 4 × 3 см, высота 5 см. V = 4 · 3 · 5 = 60 см³. Высота перпендикулярна основанию; наклон изображения не меняет её.",
            "Perspective sketch of a rectangular prism: base 4 × 3 cm, height 5 cm. V = 4 × 3 × 5 = 60 cm³. The height is perpendicular to the base despite the perspective."),
           box_drawing()+[text(180,241,"4 см","4 cm"),text(304,219,"3 см","3 cm"),text(80,153,"5 см","5 cm"),text(210,28,"V = 60 см³","V = 60 cm³")],
           model={"type":"prism","base":[4,3],"height":5,"volume":60}))
add(figure("cylinder", ("Цилиндр: радиус и высота", "Cylinder: radius and height"),
           ("Схематическая перспектива банки: r = 3 см, h = 6 см. Основания круги (в перспективе эллипсы); V = πr²h = 54π см³. Радиус — половина диаметра.",
            "Perspective sketch of a can: r = 3 cm, h = 6 cm. Bases are circles (ellipses in perspective); V = πr²h = 54π cm³. Radius is half the diameter."),
           [ellipse(210,66,73,23),ellipse(210,211,73,23),line(137,66,137,211),line(283,66,283,211),line(210,66,210,211,"helper"),line(210,211,283,211,"secondary"),
            text(113,148,"h = 6"),text(251,203,"r = 3"),text(210,264,"V = 54π см³","V = 54π cm³")],
           model={"type":"cylinder","radius":3,"height":6,"volumePi":54}))
add(figure("pyramid", ("Пирамида: треть объёма призмы", "Pyramid: one third of prism volume"),
           ("Схематическая перспектива: квадратное основание со стороной 4, перпендикулярная высота h = 9. S основания = 16, V = 16 · 9 / 3 = 48. Высота идёт внутрь, не по боковому ребру.",
            "Perspective sketch: square base of side 4 and perpendicular height h = 9. Base area is 16; V = 16 × 9 / 3 = 48. Height lies inside, not along a sloping edge."),
           [poly([(104,211),(214,243),(324,207),(214,177)],"helper",closed=True),line(104,211,214,40),line(214,243,214,40),line(324,207,214,40),line(214,177,214,40,"helper"),
            line(214,40,214,209,"secondary"),text(244,128,"h = 9"),text(166,243,"4"),text(284,239,"4"),text(211,20,"V = Sₒh/3 = 48")],
           model={"type":"pyramid","baseArea":16,"height":9,"volume":48}))
add(figure("cone", ("Высота и образующая — не одно", "Height and slant height differ"),
           ("Схематическая перспектива конуса: r = 3, h = 4, образующая l = 5. Прямой треугольник внутри даёт l² = r² + h². V = π · 3² · 4 / 3 = 12π.",
            "Perspective sketch of a cone: r = 3, h = 4, slant height l = 5. The internal right triangle gives l² = r² + h². V = π × 3² × 4 / 3 = 12π."),
           [ellipse(210,211,80,23),line(130,211,210,41),line(290,211,210,41),line(210,41,210,211,"secondary"),line(210,211,290,211,"secondary"),
            poly([(210,197),(224,197),(224,211)],"helper"),text(180,137,"h = 4"),text(277,122,"l = 5"),text(257,205,"r = 3"),text(210,264,"V = 12π")],
           model={"type":"cone","radius":3,"height":4,"slant":5,"volumePi":12}))
add(figure("sphere", ("Поверхность и объём мяча", "A ball's surface and volume"),
           ("Схематический шар радиуса R = 3. Сфера — поверхность S = 4πR² = 36π; шар — объём V = 4πR³/3 = 36π. Квадратные и кубические единицы нельзя смешивать.",
            "Sketch of a ball with R = 3. Its sphere is the surface S = 4πR² = 36π; the solid ball has V = 4πR³/3 = 36π. Square and cubic units must not be mixed."),
           [circle(210,135,85),ellipse(210,135,85,25,"helper"),line(210,135,295,135,"secondary"),circle(210,135,3,"point",True),text(255,125,"R = 3"),
            text(210,245,"S = 36π; V = 36π")],
           model={"type":"sphere","radius":3,"areaPi":36,"volumePi":36}))
add(figure("cube", ("Куб: грань, объём и диагональ", "Cube: face, volume and diagonal"),
           ("Схематическая перспектива куба с a = 2. Объём a³ = 8, площадь шести граней 6a² = 24. Пространственная диагональ 2√3 соединяет противоположные вершины через внутренность.",
            "Perspective sketch of a cube with a = 2. Volume a³ = 8 and six-face area 6a² = 24. Space diagonal 2√3 joins opposite vertices through the interior."),
           box_drawing(108,220,147,147,55,-34)+[line(108,220,310,39,"secondary"),text(182,243,"a = 2"),text(225,143,"d = 2√3"),text(209,22,"V = 8, S = 24")],
           model={"type":"cube","edge":2,"volume":8,"area":24,"diagonal":2*math.sqrt(3)}))
add(figure("three-perpendiculars", ("Наклонная и её проекция", "Sloping segment and its projection"),
           ("Схематическая плоскость земли. AA₀ ⟂ плоскости, A₀P — ортогональная проекция AP. Прямая l проходит через P, лежит в плоскости и перпендикулярна A₀P, значит l ⟂ AP. Перспективный рисунок не сохраняет видимые углы.",
            "Perspective sketch of the ground plane. AA₀ is perpendicular to it; A₀P is the orthogonal projection of AP. Line l passes through P in the plane and is perpendicular to A₀P, hence to AP. Perspective does not preserve apparent angles."),
           [poly([(80,207.5),(284,258.5),(374,168.5),(170,117.5)],"region",closed=True),line(150,51,150,180),line(150,51,286,214,"secondary"),line(150,180,286,214,"helper"),
            line(250,250,322,178),text(136,45,"A"),text(130,188,"A₀"),text(299,233,"P"),text(337,179,"l"),text(210,24,"AA₀ ⟂ плоскости","AA₀ ⟂ plane")],
           model={"type":"orthogonal-projection","height":[0,0,3],"projection":[4,0,0],"lineDirection":[0,1,0],
                  "screenOrigin":[150,180],"screenBasis":[[34,8.5],[18,-18],[0,-43]]}))

# Coordinate/vector figures have equal horizontal and vertical length scales.
add(figure("vector-displacement", ("Путь по улицам и перемещение", "Street route and displacement"),
           ("Из O три единицы вправо, четыре вверх: путь 7, прямое перемещение 5. Вектор OP = (3;4), |OP| = 5. По осям один масштаб, прямой угол обозначен.",
            "From O go 3 units right and 4 up: route length 7, displacement 5. OP = (3,4), |OP| = 5. Both axes use one scale and the right angle is marked."),
           [*arrow(96,222,278,222,"axis"),*arrow(96,222,96,27,"axis"),line(96,222,222,222,"helper"),line(222,222,222,54,"helper"),*arrow(96,222,222,54),
            poly([(207,222),(207,207),(222,207)],"helper"),text(79,242,"O"),text(240,50,"P(3;4)"),text(158,243,"3"),text(243,149,"4"),text(140,129,"5"),text(294,226,"x"),text(79,31,"y")],
           model={"type":"vector","coordinates":[3,4],"length":5,"routeLength":7,"scale":42}))
vorigin=(188,215); sa=36
va=(vorigin[0]+3*sa,vorigin[1]-sa); vb=(vorigin[0]-sa,vorigin[1]-3*sa)
u=(3/math.sqrt(10),-1/math.sqrt(10)); v=(-1/math.sqrt(10),-3/math.sqrt(10))
rmarker=[(vorigin[0]+u[0]*17,vorigin[1]+u[1]*17),
         (vorigin[0]+(u[0]+v[0])*17,vorigin[1]+(u[1]+v[1])*17),
         (vorigin[0]+v[0]*17,vorigin[1]+v[1]*17)]
add(figure("dot-perpendicular", ("Проверка прямого угла координатами", "Checking a right angle with coordinates"),
           ("a = (3;1), b = (−1;3): a·b = 3·(−1) + 1·3 = 0. Ненулевые векторы перпендикулярны. Оба нарисованы в одном масштабе, поэтому прямой угол не искажён.",
            "a = (3,1), b = (−1,3): a·b = 3×(−1) + 1×3 = 0. Non-zero vectors are perpendicular. One scale for both axes preserves their right angle."),
           [*arrow(*vorigin,*va),*arrow(*vorigin,*vb,"secondary"),poly(rmarker,"helper"),text(310,184,"a = (3;1)"),text(140,83,"b = (−1;3)"),
            text(188,242,"O"),text(210,38,"a·b = 0")],
           model={"type":"dot-product","a":[3,1],"b":[-1,3],"dot":0,"scale":36}))
add(figure("midpoint", ("Середина: две равные половины", "Midpoint: two equal halves"),
           ("A(1;1), B(5;3), M(3;2). Вектор AM = MB = (2;1). M — середина, координаты усреднены отдельно; одна половина всей стрелки соответствует множителю 1/2.",
            "A(1,1), B(5,3), M(3,2). AM = MB = (2,1). M is the midpoint; coordinates are averaged separately. One half of the whole vector gives factor 1/2."),
           [*arrow(54,233,357,233,"axis"),*arrow(54,233,54,58,"axis"),line(96,191,264,107),circle(96,191,4,"point",True),circle(180,149,4,"point",True),circle(264,107,4,"point",True),
            text(96,215,"A(1;1)"),text(190,176,"M(3;2)"),text(275,91,"B(5;3)"),text(382,238,"x"),text(39,53,"y")],
           model={"type":"midpoint","a":[1,1],"b":[5,3],"midpoint":[3,2],"scale":42}))
add(figure("product-area", ("Меняются обе стороны", "Both sides change"),
           ("У прямоугольника стороны u и v. Если прирастут на Δu и Δv, добавятся две полосы vΔu и uΔv и угол ΔuΔv. В пределе угол не даёт отдельного слагаемого производной: (uv)′ = u′v + uv′.",
            "If rectangle sides u and v increase by Δu and Δv, new pieces have areas vΔu, uΔv and ΔuΔv. In the limit the corner adds no derivative term: (uv)′ = u′v + uv′."),
           [rect(77,63,208,125,"region"),rect(285,63,45,125,"secondary"),rect(77,188,208,36,"secondary"),rect(285,188,45,36,"region"),
            text(180,131,"uv"),text(308,127,"vΔu"),text(180,212,"uΔv"),text(311,241,"ΔuΔv"),text(180,44,"u"),text(43,127,"v"),text(309,44,"Δu"),text(42,215,"Δv")],
           model={"type":"product-rule","smallCornerOrder":2}))
add(figure("chain-flow", ("Два последовательных изменения", "Two linked changes"),
           ("Время t → ребро a = 2t → объём V = a³. Скорости по цепочке перемножаются: dV/dt = (3a²)·2 = 24t². Внутренний множитель 2 не исчезает.",
            "Time t → edge a = 2t → volume V = a³. Rates multiply along the chain: dV/dt = (3a²)×2 = 24t². The inner factor 2 must not be dropped."),
           [rect(30,92,90,72,"region"),rect(165,92,90,72,"region"),rect(300,92,90,72,"region"),*arrow(124,128,158,128,"secondary"),*arrow(259,128,293,128,"secondary"),
            text(75,133,"t"),text(210,133,"a = 2t"),text(345,133,"V = a³"),text(140,74,"×2"),text(277,74,"×3a²"),text(210,218,"dV/dt = 24t²")],
           model={"type":"chain-rule","edgeRate":2,"volumeRateCoefficient":24}))
# Colour is redundant: tokens carry R/B letters, and the caption supplies counts.
add(figure("probability-tokens", ("Три подходящих из пяти", "Three favourable out of five"),
           ("Пять одинаково вероятных фишек, три R (красные) и две B (синие). P(R) = 3/5. При извлечении без возврата число фишек меняется; при возврате сохраняется.",
            "Five equally likely tokens: three R (red) and two B (blue). P(R) = 3/5. Drawing without replacement changes the token count; replacement preserves it."),
           [rect(44,74,332,127,"helper")]+[item for i in range(5) for item in [circle(80+65*i,137,22,"secondary" if i<3 else "primary"),text(80+65*i,143,"R" if i<3 else "B")]]+
           [text(210,247,"P(R) = 3/5")],
           model={"type":"probability","total":5,"favourable":3,"probability":[3,5]}))
add(figure("counting-roles", ("Команда или разные роли", "A team or different roles"),
           ("Три человека A, B, C. Без ролей выбираем пары AB, AC, BC: 3. Для капитана и помощника порядок важен: AB, AC, BA, BC, CA, CB — 6. Повторять человека в паре нельзя.",
            "Three people A,B,C. Without roles choose AB,AC,BC: 3. Captain and assistant make order matter: AB,AC,BA,BC,CA,CB, six. A person cannot repeat within a pair."),
           [text(87,42,"Капитан","Captain"),text(249,42,"Помощник","Assistant")]+[item for i,first in enumerate("ABC") for item in
            [circle(87,82+66*i,17,"point",True),text(87,88+66*i,first),line(106,82+66*i,203,69+66*i,"helper"),line(106,82+66*i,203,97+66*i,"helper"),
             text(234,74+66*i," / ".join(x for x in "ABC" if x!=first)),text(327,88+66*i,", ".join(first+x for x in "ABC" if x!=first))]],
           model={"type":"counting","n":3,"k":2,"ordered":6,"unordered":3}))
clock=[circle(210,139,87)]
for hour in range(12):
    theta=math.pi/2-hour*math.pi/6
    x,y=circle_point(theta,210,139,98)
    clock.append(text(x,y+5,str(hour or 12)))
clock += arrow(210,139,*circle_point(math.pi/2-10*math.pi/6,210,139,68))
clock += arrow(210,139,*circle_point(math.pi/2-3*math.pi/6,210,139,77),"secondary")
clock += [text(210,265,"10 + 5 ≡ 3 (mod 12)")]
add(figure("clock-cycle", ("После полного круга счёт повторяется", "Counting repeats after a full turn"),
           ("С 10 часов через 5 часов получится 3. Полный круг 12 не меняет положение стрелки. Остаток 0 на рисунке обозначен 12; это одна и та же отметка, не два часа.",
            "Five hours after 10 it is 3. A full cycle of 12 leaves the hand's position unchanged. Remainder 0 is marked 12, the same clock position, not an extra hour."), clock,
           legend=[("primary",("Начало: 10","Start: 10")),("secondary",("Через 5 часов: 3","After 5 hours: 3"))],
           model={"type":"modular","modulus":12,"start":10,"increment":5,"result":3}))

# One figure may serve related lessons without duplicating SVG data in JSON.
LESSON_FIGURES = {
    "fractions":["fraction-bar"], "powers":["geometric-dots","cube"],
    "roots-absolute":["absolute-distance"], "identities":["identity-areas"],
    "linear-equations":["taxi-cost"], "quadratic":["parabola-roots"],
    "equation-domain":["domain-root","hyperbola"], "linear-inequalities":["absolute-interval"],
    "intervals":["interval-signs"], "quadratic-inequalities":["parabola-roots"],
    "function-domain-range":["domain-root"], "graph-transformations":["graph-shift"],
    "function-properties":["linear-graph","hyperbola","even-odd"],
    "arithmetic-progression":["arithmetic-dots"], "geometric-progression":["geometric-dots"],
    "progression-sums":["arithmetic-dots","geometric-dots"], "motion-work":["constant-speed"],
    "percentages":["percent-stages"], "trig-identities":["unit-circle","ladder-triangle"],
    "trig-values":["radian-arc","unit-circle"], "trig-formulas":["unit-circle","sine-cosine"],
    "trig-equations":["circle-two-solutions","sine-solutions"], "trig-selection":["sine-solutions"],
    "log-definition":["exponential","logarithm"], "log-properties":["logarithm"],
    "exponential-equations":["exponential"], "plane-figures":["triangle-lines"],
    "right-triangle":["ladder-triangle"], "plane-areas":["triangle-area","parallelogram-area"],
    "circle-theorems":["circle-angles","circle-tangent","radian-arc"], "similarity":["similar-triangles"],
    "prism-cylinder":["prism-box","cylinder"], "pyramid-cone":["pyramid","cone"],
    "sphere-cube":["sphere","cube"], "solid-perpendiculars":["three-perpendiculars"],
    "derivative-table":["speed-tangent"], "derivative-rules":["product-area"],
    "chain-rule":["chain-flow"], "derivative-point":["tangent"],
    "extrema":["extrema","even-odd"], "segment-extrema":["segment-extrema"],
    "counting":["counting-roles"], "probability":["probability-tokens"],
    "factorials":["counting-roles"], "vector-coordinates":["vector-displacement"],
    "dot-product":["dot-perpendicular"], "midpoint-collinearity":["midpoint"],
    "parameters":["parameter-two","parameter-one","parameter-none"],
    "parameter-tangency":["tangent"], "sequences":["arithmetic-dots"], "modular-cycles":["clock-cycle"],
}


def payload():
    return deepcopy(FIGURES)


def validate(figures):
    """Strict JSON-to-SVG contract. Fail closed even for a broken last shape."""
    if not isinstance(figures,dict) or not figures:
        raise ValueError("diagram catalogue is empty")
    for key,entry in figures.items():
        if entry.get("id") != key or not key or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in key):
            raise ValueError("invalid diagram id")
        if set(entry)-{"id","title","caption","width","height","drawing","legend","model"}:
            raise ValueError("unexpected diagram field")
        for field in ("title","caption"):
            if not isinstance(entry.get(field),dict) or any(not isinstance(entry[field].get(lang),str) or not entry[field][lang].strip() for lang in ("ru","en")):
                raise ValueError(f"diagram {key} needs bilingual {field}")
        if entry.get("width")!=WIDTH or entry.get("height")!=HEIGHT:
            raise ValueError("invalid diagram viewport")
        drawing=entry.get("drawing")
        if not isinstance(drawing,list) or not 1<=len(drawing)<=250:
            raise ValueError("invalid diagram drawing")
        for item in drawing:
            kind=item.get("kind")
            if kind not in FIELDS or set(item)-({"kind","role","filled"}|FIELDS[kind]) or FIELDS[kind]-set(item):
                raise ValueError("unsafe or incomplete diagram primitive")
            if item.get("role") not in ROLES or not isinstance(item.get("filled"),bool):
                raise ValueError("invalid diagram styling")
            for field in FIELDS[kind]-{"points","text","anchor"}:
                v=item[field]
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=(HEIGHT if field.startswith("y") or field in {"cy","height","ry"} else WIDTH):
                    raise ValueError("invalid diagram coordinate")
                if field in {"r","rx","ry","width","height"} and v<=0:
                    raise ValueError("invalid diagram size")
            if kind in {"polyline","polygon"}:
                pts=item["points"]
                if not isinstance(pts,list) or not (3 if kind=="polygon" else 2)<=len(pts)<=500:
                    raise ValueError("invalid diagram points")
                for point in pts:
                    if not isinstance(point,list) or len(point)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in point) or not (0<=point[0]<=WIDTH and 0<=point[1]<=HEIGHT):
                        raise ValueError("invalid diagram point")
            if kind=="text":
                if item["anchor"] not in {"start","middle","end"} or not isinstance(item["text"],dict) or any(not isinstance(item["text"].get(lang),str) or not item["text"][lang].strip() for lang in ("ru","en")):
                    raise ValueError("invalid bilingual diagram label")
        for item in entry.get("legend",[]):
            if set(item)!={"role","text"} or item["role"] not in ROLES or not isinstance(item["text"],dict) or any(not isinstance(item["text"].get(lang),str) or not item["text"][lang].strip() for lang in ("ru","en")):
                raise ValueError("invalid diagram legend")
    return figures
