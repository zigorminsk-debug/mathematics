"""theory.py — офлайн-уроки физики: определение, правила, разбор, бытовое объяснение.

Каждый урок двуязычен, содержит точные определения и обозначения с единицами,
условия применимости формул, хотя бы один разобранный пример и объяснение
«через знакомую ситуацию» — с честными пределами модели. Уроки связаны с
разделами сборника формул (formulas.py) и с разборами типичных ошибок, поэтому
после неверного ответа ученик открывает именно тот материал, который объясняет
его ошибку. Схемы (diagrams.py) подключаются по идентификаторам.
"""

from __future__ import annotations

from kit import PhysicsError

LESSONS: dict[str, dict] = {}


def _lesson(key, title_ru, title_en, definitions, rules, examples, everyday, figures=()):
    if key in LESSONS:
        raise PhysicsError(f"урок {key!r} уже описан")
    LESSONS[key] = {
        "id": key,
        "title": {"ru": title_ru, "en": title_en},
        "definitions": {"ru": list(definitions[0]), "en": list(definitions[1])},
        "rules": {"ru": list(rules[0]), "en": list(rules[1])},
        "examples": [
            {"statement": {"ru": statement[0], "en": statement[1]},
             "steps": {"ru": list(steps[0]), "en": list(steps[1])}}
            for statement, steps in examples
        ],
        "everyday": {"ru": list(everyday[0]), "en": list(everyday[1])},
        "figures": list(figures),
    }


# --------------------------------------------------------------------------- #
#  1. Измерения и единицы
# --------------------------------------------------------------------------- #

_lesson(
    "units-si", "Система СИ и приставки", "SI units and prefixes",
    (["Международная система единиц (СИ) содержит семь основных единиц: метр (м), "
      "килограмм (кг), секунда (с), ампер (А), кельвин (К), моль (моль) и кандела (кд). "
      "Все остальные единицы — производные, например ньютон: 1 Н = 1 кг·м/с².",
      "Кратные и дольные приставки — это множители: 1 км = 10³ м, 1 см = 10⁻² м, "
      "1 мм = 10⁻³ м, 1 мкм = 10⁻⁶ м, 1 т = 10³ кг, 1 мН = 10⁻³ Н."],
     ["The SI contains seven base units: metre (m), kilogram (kg), second (s), ampere (A), "
      "kelvin (K), mole (mol) and candela (cd). Other units are derived, for example "
      "1 N = 1 kg·m/s².",
      "Prefixes are factors: 1 km = 10³ m, 1 cm = 10⁻² m, 1 mm = 10⁻³ m, 1 µm = 10⁻⁶ m, "
      "1 t = 10³ kg, 1 mN = 10⁻³ N."]),
    (["Прежде чем подставлять числа в формулу, переведите все величины в единицы СИ "
      "одной строки приставок — обычно в основные единицы.",
      "Приставка относится только к своей единице: 1 кВт·ч — это 1000 Вт × 3600 с, "
      "а не 1000 × 3600 Вт·ч.",
      "Не путайте массу и вес: масса в килограммах, вес (сила) в ньютонах."],
     ["Convert every value to SI, usually to the base units, before substituting numbers "
      "into a formula.",
      "A prefix belongs to its own unit only: 1 kWh is 1000 W × 3600 s, not 1000 × 3600 Wh.",
      "Do not mix up mass and weight: mass in kilograms, weight (a force) in newtons."]),
    [(("Переведите 72 км/ч в м/с.", "Convert 72 km/h to m/s."),
      (["1 км = 1000 м, 1 ч = 3600 с.", "72 км/ч = 72 000 м / 3600 с = 20 м/с.",
        "Ответ: 20 м/с."],
       ["1 km = 1000 m and 1 h = 3600 s.", "72 km/h = 72 000 m / 3600 s = 20 m/s.",
        "Answer: 20 m/s."])),
     (("Выразите 2,5 л в кубических метрах.", "Express 2.5 litres in cubic metres."),
      (["1 л = 1 дм³ = 10⁻³ м³.", "2,5 л = 2,5 · 10⁻³ м³ = 0,0025 м³.", "Ответ: 0,0025 м³."],
       ["1 l = 1 dm³ = 10⁻³ m³.", "2.5 l = 2.5 · 10⁻³ m³ = 0.0025 m³.", "Answer: 0.0025 m³."]))],
    (["Спидометр автомобиля показывает км/ч, а в формулах нужны м/с: разделите показание "
      "на 3,6. 36 км/ч — это ровно 10 м/с.",
      "Прейскурант электроэнергии считает киловатт-часы, а физика — джоули: "
      "1 кВт·ч = 3,6·10⁶ Дж. Модель «идеального» прибора без потерь здесь не работает: "
      "в реальном нагревателе часть энергии уходит в среду."],
     ["A car speedometer shows km/h while formulas want m/s: divide by 3.6. "
      "36 km/h is exactly 10 m/s.",
      "Electricity bills use kilowatt-hours while physics uses joules: 1 kWh = 3.6·10⁶ J. "
      "The lossless-appliance model is an approximation: part of the energy heats the room."]),
)

_lesson(
    "dimensions-check", "Размерность как проверка формулы", "Dimensions check a formula",
    (["Размерность величины — выражение через основные единицы СИ: скорость — м/с, "
      "ускорение — м/с², сила — кг·м/с² = Н, энергия — кг·м²/с² = Дж.",
      "Складывать и сравнивать можно только величины одинаковой размерности; "
      "под модулем (абсолютным значением) смысл имеет лишь разность координат."],
     ["The dimension of a quantity is its expression in base SI units: speed m/s, acceleration "
      "m/s², force kg·m/s² = N, energy kg·m²/s² = J.",
      "Only quantities of the same dimension may be added or compared."]),
    (["Проверка размерности отсекает неверные формулы: если справа получается м/с², "
      "а слева требуется м, формула выбрана неправильно.",
      "Аргумент синуса, косинуса, логарифма и экспоненты обязан быть безразмерным.",
      "Число с размерностью не «прибавляется» к безразмерному: sin(5 м) не имеет смысла."],
     ["A dimension check rejects wrong formulas: if the right side gives m/s² where metres are "
      "needed, the formula is wrong.",
      "Arguments of sine, cosine, logarithm and exponential must be dimensionless.",
      "A dimensional quantity cannot be added to a plain number: sin(5 m) is meaningless."]),
    [(("Проверьте по размерности формулу пути s = v·t + a·t.", "Check the formula s = v·t + a·t."),
      (["Второе слагаемое: (м/с²)·с = м/с.", "Первое слагаемое: (м/с)·с = м; размерности не совпадают.",
        "Верно s = v·t + a·t²/2: (м/с²)·с² = м."],
       ["The second term: (m/s²)·s = m/s.", "The first term is (m/s)·s = m; the dimensions differ.",
        "The correct formula is s = v·t + a·t²/2: (m/s²)·s² = m."]))],
    (["Покупая обои, площадь стен считают в м², а рулон продают «ширина × длина» в метрах — "
      "перемножать можно, потому что м·м даёт м².",
      "Ошибка «сложить метры с секундами» встречается и в быту: сравнивать время поездки "
      "с расстоянием нельзя без скорости — именно её и связывает формула."],
     ["Buying wallpaper you measure wall area in m² while a roll is sold as width × length in "
      "metres; the product gives m², so the units match.",
      "Adding metres to seconds is nonsense in everyday life too: distance and time can only be "
      "compared through speed, which is exactly what a formula does."]),
)

_lesson(
    "measure-accuracy", "Цена деления и погрешность измерения", "Scale division and uncertainty",
    (["Цена деления — разность двух соседних подписанных значений, делённая на число "
      "промежутков между ними.",
      "Погрешность отсчёта по прибору принимают равной половине цены деления; "
      "результат записывают с той же точностью, что и измерение."],
     ["The scale division is the difference between two neighbouring labelled values divided "
      "by the number of gaps between them.",
      "The reading uncertainty is half a scale division; the result is reported with the same "
      "precision as the measurement."]),
    (["Прибор не становится точнее от того, что вычисления сделаны с пятью знаками: "
      "точность результата ограничена измерением.",
      "Округлять промежуточные результаты рано нельзя: погрешность накапливается, "
      "округляйте ответ в конце.",
      "Прибор с нониусом (штангенциркуль) имеет цену деления, указанную в паспорте; "
      "на глаз половина деления не угадывается."],
     ["A device does not become more accurate because the arithmetic carries five digits: the "
      "result is limited by the measurement.",
      "Do not round intermediate results: the error accumulates — round the final answer.",
      "A vernier calliper has a documented division; half of it cannot be guessed."]),
    [(("Между подписями 20 и 40 мл на мензурке четыре промежутка. Найдите цену деления.",
       "Between the 20 ml and 40 ml marks a beaker has four gaps. Find the division."),
      (["Разность подписей: 40 − 20 = 20 мл.", "20 мл / 4 = 5 мл.", "Цена деления 5 мл; "
        "погрешность отсчёта не меньше 2,5 мл."],
       ["Difference of labels: 40 − 20 = 20 ml.", "20 ml / 4 = 5 ml.", "The division is 5 ml and "
        "the reading uncertainty is at least 2.5 ml."]))],
    (["Кухонные весы с шагом 5 г не покажут «127,3 г»: честный результат — "
      "(125 ± 2,5) г, и это нормально.",
      "Модель «прибор идеален» годится только для оценок: в реальном опыте всегда есть "
      "трение, теплообмен и неточность отсчёта."],
     ["Kitchen scales with a 5 g step cannot show 127.3 g: the honest reading is (125 ± 2.5) g.",
      "The ideal-instrument model is only an estimate: real experiments always have friction, "
      "heat exchange and reading error."]),
    figures=("scale-ruler",),
)

# --------------------------------------------------------------------------- #
#  2. Кинематика
# --------------------------------------------------------------------------- #

_lesson(
    "motion-terms", "Путь, перемещение, средняя скорость", "Distance, displacement, average speed",
    (["Путь s — длина траектории, величина неотрицательная. Перемещение — вектор из "
      "начального положения в конечное; при возврате в начальную точку оно равно нулю.",
      "Средняя скорость — весь путь, делённый на всё время движения: vср = s/t. "
      "Средняя путевая скорость и модуль средней скорости совпадают только при движении без поворотов."],
     ["Distance s is the length of the trajectory, never negative. Displacement is the vector "
      "from start to finish; returning to the start makes it zero.",
      "Average speed is total distance over total time: v = s/t."]),
    (["Скорость — вектор: одинаковые по модулю скорости с разными направлениями — разные скорости.",
      "Складывать скорости участков можно только при равных временах; иначе делите "
      "суммарный путь на суммарное время.",
      "В системе СИ путь измеряется в метрах, время в секундах, скорость в м/с."],
     ["Velocity is a vector: equal magnitudes with different directions are different velocities.",
      "Section speeds may be averaged only for equal time intervals; otherwise divide the total "
      "distance by the total time.",
      "In SI, distance is in metres, time in seconds and speed in m/s."]),
    [(("Турист прошёл 6 км за 2 ч и вернулся тем же путём за 1 ч. Найдите путь, "
       "перемещение и среднюю скорость.", "A hiker walks 6 km in 2 h and returns in 1 h. Find "
       "distance, displacement and average speed."),
      (["Путь = 6 + 6 = 12 км.", "Перемещение = 0, так как турист вернулся в начало.",
        "Средняя скорость = 12 км / 3 ч = 4 км/ч."],
       ["Distance = 6 + 6 = 12 km.", "Displacement = 0 because the hiker returned to the start.",
        "Average speed = 12 km / 3 h = 4 km/h."]))],
    (["Такси по навигатору показывает путь 7 км, а по прямой до цели 5 км: счётчик берёт "
      "деньги за путь, а перемещение — только прямая.",
      "Модель постоянной скорости на участке: в реальной поездке скорость меняется, "
      "поэтому средняя скорость — не «скорость в каждый момент»."],
     ["A taxi meter charges for the 7 km route while the displacement to the destination is "
      "5 km in a straight line.",
      "The constant-speed model holds only piecewise: in a real trip the speed changes, so the "
      "average is not the instantaneous speed."]),
    figures=("motion-route",),
)

_lesson(
    "uniform-motion", "Равномерное прямолинейное движение", "Uniform motion",
    (["Равномерное движение — движение по прямой с постоянной скоростью: за любые равные "
      "промежутки времени тело проходит одинаковые пути.",
      "Уравнение движения: x = x₀ + v·t, где x₀ — начальная координата, v — проекция скорости "
      "на ось (может быть отрицательной)."],
     ["Uniform motion is motion along a straight line at constant speed: equal time intervals "
      "give equal distances.",
      "Equation of motion: x = x₀ + v·t, where v is the velocity projection (may be negative)."]),
    (["Путь при равномерном движении s = v·t; график x(t) — прямая, наклон которой равен "
      "скорости.",
      "Знак проекции скорости говорит о направлении движения по выбранной оси.",
      "При равномерном движении ускорение равно нулю и равнодействующая сил тоже нулю."],
     ["Distance s = v·t; the x(t) graph is a straight line whose slope is the speed.",
      "The sign of the velocity projection shows the direction along the chosen axis.",
      "In uniform motion the acceleration is zero, hence so is the net force."]),
    [(("Поезд идёт со скоростью 15 м/с. Какой путь он пройдёт за 4 мин?",
       "A train moves at 15 m/s. What distance does it cover in 4 minutes?"),
      (["Переведём время: 4 мин = 240 с.", "s = v·t = 15 · 240 = 3600 м.", "Ответ: 3600 м = 3,6 км."],
       ["Convert time: 4 min = 240 s.", "s = v·t = 15 · 240 = 3600 m.", "Answer: 3600 m = 3.6 km."])),
     (("Два велосипедиста едут навстречу: 5 м/с и 3 м/с, расстояние 160 м. Через сколько "
       "встретятся?", "Two cyclists approach at 5 m/s and 3 m/s from 160 m apart. When do they meet?"),
      (["Скорость сближения при встречном движении: 5 + 3 = 8 м/с.",
        "t = s/v = 160 / 8 = 20 с.", "Ответ: через 20 с."],
       ["Approach speed: 5 + 3 = 8 m/s.", "t = 160 / 8 = 20 s.", "Answer: after 20 s."]))],
    (["Курьерский поезд и электричка: чтобы узнать время встречи, складывают скорости, "
      "а чтобы догнать — вычитают. Это одна и та же формула x₁ = x₂.",
      "Модель «скорость постоянна» для поезда годится только на перегоне без разгона и "
      "торможения."],
     ["An express and a commuter train: meeting uses the sum of speeds, catching up uses the "
      "difference — both follow from x₁ = x₂.",
      "The constant-speed model works only between acceleration and braking."]),
    figures=("graph-x-t",),
)

_lesson(
    "accelerated-motion", "Равноускоренное движение", "Uniformly accelerated motion",
    (["Равноускоренное движение — движение с постоянным ускорением a. Скорость меняется "
      "по закону v = v₀ + a·t, координата — по закону x = x₀ + v₀·t + a·t²/2.",
      "Ускорение — векторная величина: a = Δv/Δt, единица измерения 1 м/с². "
      "При торможении проекция ускорения отрицательна."],
     ["Uniformly accelerated motion has constant acceleration a with v = v₀ + a·t and "
      "x = x₀ + v₀·t + a·t²/2.",
      "Acceleration is a vector, a = Δv/Δt, measured in m/s². Braking gives a negative projection."]),
    (["Множитель ½ относится только к слагаемому ускорения: s = v₀t + at²/2.",
      "Полезные формулы без времени: s = (v₀ + v)·t/2 и s = (v² − v₀²)/(2a) — последняя "
      "работает и при торможении (a < 0).",
      "При равноускоренном движении из состояния покоя путь растёт как t²: в первые две "
      "секунды путь вчетверо больше, чем в первую."],
     ["The factor ½ belongs to the acceleration term only: s = v₀t + at²/2.",
      "Time-free formulas: s = (v₀ + v)t/2 and s = (v² − v₀²)/(2a), the latter also for braking.",
      "From rest the distance grows as t²: the first two seconds give four times the first one."]),
    [(("Автомобиль разгоняется с 10 м/с до 25 м/с за 5 с. Найдите ускорение и путь.",
       "A car speeds up from 10 m/s to 25 m/s in 5 s. Find acceleration and distance."),
      (["a = (v − v₀)/t = (25 − 10)/5 = 3 м/с².",
        "s = (v₀ + v)·t/2 = (10 + 25)·5/2 = 87,5 м.", "Ответ: 3 м/с² и 87,5 м."],
       ["a = (v − v₀)/t = (25 − 10)/5 = 3 m/s².",
        "s = (v₀ + v)·t/2 = (10 + 25)·5/2 = 87.5 m.", "Answer: 3 m/s² and 87.5 m."])),
     (("Поезд при торможении с 20 м/с остановился за 25 с. Найдите тормозной путь.",
       "A train braking from 20 m/s stops in 25 s. Find the braking distance."),
      (["Конечная скорость 0, значит a = (0 − 20)/25 = −0,8 м/с².",
        "s = (v₀ + v)·t/2 = (20 + 0)·25/2 = 250 м.", "Ответ: 250 м."],
       ["Final speed is 0, so a = (0 − 20)/25 = −0.8 m/s².",
        "s = (v₀ + v)·t/2 = (20 + 0)·25/2 = 250 m.", "Answer: 250 m."]))],
    (["Разгон метро от станции: в первую секунду вагон проходит около метра, а за десять "
      "секунд — уже десятки метров, потому что путь растёт как квадрат времени.",
      "Модель «ускорение постоянно» ломается у реального автомобиля после переключения "
      "передачи: там уже важно, как меняется тяга."],
     ["A metro train leaving a station covers about a metre in the first second but dozens of "
      "metres in ten, because distance grows as the square of time.",
      "The constant-acceleration model breaks for a real car after a gear shift, where the "
      "traction varies."]),
    figures=("graph-v-t",),
)

_lesson(
    "kinematics-graphs", "Чтение графиков движения", "Reading motion graphs",
    (["На графике x(t) наклон прямой равен проекции скорости; чем круче прямая, тем больше "
      "скорость. Горизонтальная линия означает покой.",
      "На графике v(t) наклон равен ускорению, а площадь между графиком и осью времени "
      "равна пути (с учётом знака)."],
     ["On an x(t) graph the slope equals the velocity projection; a horizontal line means rest.",
      "On a v(t) graph the slope is the acceleration and the area under the graph is the "
      "distance (with sign)."]),
    (["Физический смысл имеют только оси с подписями и единицами: «наклон 2» без осей "
      "не означает 2 м/с.",
      "Площадь под осью времени (v < 0) считается со знаком минус — это перемещение назад.",
      "Постоянная скорость — прямая на v(t); постоянное ускорение — прямая на графике "
      "скорости и парабола на графике координаты."],
     ["Only labelled axes with units carry physical meaning: a slope of 2 without axes is not 2 m/s.",
      "Area below the time axis (v < 0) counts negative: displacement backwards.",
      "Constant speed is a horizontal v(t); constant acceleration is a straight v(t) and a "
      "parabolic x(t)."]),
    [(("По графику v(t): 0–2 с скорость 4 м/с, 2–5 с скорость 0. Найдите путь.",
       "From a v(t) graph: 4 m/s for 0–2 s and 0 m/s for 2–5 s. Find the distance."),
      (["Путь — площадь под графиком: 4·2 = 8 м на первом участке.",
        "На втором участке тело стоит: вклад 0.", "Ответ: 8 м."],
       ["Area under the graph: 4·2 = 8 m in the first section.",
        "The body is at rest afterwards: contribution 0.", "Answer: 8 m."]))],
    (["Спидометр рисует мгновенную скорость, а пройденный путь — площадь под её графиком: "
      "именно поэтому «средняя по времени» скорость не равна среднему показанию спидометра "
      "при резких разгонах.",
      "Радар на дороге измеряет модуль скорости в одной точке, а не среднюю скорость за "
      "поездку — это разные физические величины."],
     ["A speedometer shows instantaneous speed while the travelled distance is the area under "
      "its graph, so the time-average differs from the mean reading during hard acceleration.",
      "A traffic radar measures the instantaneous speed at one point, not the trip average."]),
    figures=("graph-v-t",),
)

_lesson(
    "free-fall", "Свободное падение", "Free fall",
    (["Свободное падение — движение только под действием силы тяжести: у поверхности Земли "
      "ускорение g ≈ 9,8 м/с² направлено вниз.",
      "Формулы получаются из равноускоренного движения при v₀ = 0: h = g·t²/2, v = g·t, "
      "v = √(2gh)."],
     ["Free fall happens under gravity alone: near the Earth g ≈ 9.8 m/s² directed downwards.",
      "With v₀ = 0 the uniformly accelerated formulas give h = g·t²/2, v = g·t and v = √(2gh)."]),
    (["Без сопротивления воздуха время падения не зависит от массы: перо и молоток падают "
      "одинаково (это проверено в вакуумной камере).",
      "Если тело брошено вертикально вверх, в верхней точке скорость равна нулю, "
      "а ускорение по-прежнему g, направленное вниз.",
      "Движение вверх и вниз до одной высоты занимает одинаковое время."],
     ["Without air drag the falling time does not depend on mass: a feather and a hammer fall "
      "alike in a vacuum chamber.",
      "At the highest point of a vertical throw the speed is zero while the acceleration is "
      "still g directed downwards.",
      "Going up and coming back to the same height takes equal times."]),
    [(("Камень отпустили с высоты 45 м. Сколько он падает и с какой скоростью упадёт?",
       "A stone is dropped from 45 m. How long does it fall and how fast does it land?"),
      (["h = g·t²/2, значит t = √(2h/g) = √(90/9,8) ≈ 3,03 с.",
        "v = g·t ≈ 9,8·3,03 ≈ 29,7 м/с (или v = √(2gh)).", "Ответ: ≈ 3 с и ≈ 30 м/с."],
       ["h = g·t²/2 gives t = √(2h/g) = √(90/9.8) ≈ 3.03 s.",
        "v = g·t ≈ 9.8·3.03 ≈ 29.7 m/s (or v = √(2gh)).", "Answer: ≈ 3 s and ≈ 30 m/s."]))],
    (["Капли с карниза падают по одинаковому закону: за первую секунду ≈ 5 м, за вторую "
      "ещё ≈ 15 м — интервалы растут.",
      "Модель без сопротивления хороша для тяжёлого плотного тела на небольшой высоте; "
      "для парашюта и листа бумаги уже нужно учитывать сопротивление воздуха."],
     ["Roof drips fall the same way: about 5 m in the first second and 15 m more in the second.",
      "The drag-free model suits a heavy dense body over a short drop; a parachute or a sheet "
      "of paper needs air resistance."]),
    figures=("free-fall",),
)

# --------------------------------------------------------------------------- #
#  3. Динамика
# --------------------------------------------------------------------------- #

_lesson(
    "newton-laws", "Законы Ньютона", "Newton's laws",
    (["Первый закон: существуют системы отсчёта, в которых тело без внешних сил движется "
      "равномерно и прямолинейно или покоится (инерция).",
      "Второй закон: ускорение пропорционально равнодействующей всех сил и обратно "
      "пропорционально массе: a = F/m, то есть F = m·a.",
      "Третий закон: тела действуют друг на друга силами равными по модулю и "
      "противоположными по направлению, приложенными к разным телам."],
     ["First law: in an inertial frame a body with no net force stays at rest or moves "
      "uniformly along a straight line.",
      "Second law: the acceleration is proportional to the net force and inversely "
      "proportional to the mass: a = F/m.",
      "Third law: interacting bodies exert equal and opposite forces on each other."]),
    (["В F = m·a стоит равнодействующая всех сил: тяжесть, реакция опоры, тяга, трение, "
      "сила упругости — складывать нужно всё.",
      "Силы действия и противодействия приложены к разным телам, поэтому они не сокращаются "
      "в уравнении одного тела.",
      "Первый закон выполняется только в инерциальных системах: в разгоняющемся автобусе "
      "без внешней силы тело «уезжает» назад."],
     ["In F = m·a the force is the net force: gravity, normal reaction, pull, friction and "
      "elasticity all count.",
      "Action and reaction act on different bodies, so they never cancel in one body's equation.",
      "The first law holds only in inertial frames: in a braking bus a free object seems to move."]),
    [(("Тело массой 2 кг движется с ускорением 3 м/с². Найдите равнодействующую.",
       "A 2 kg body accelerates at 3 m/s². Find the net force."),
      (["F = m·a.", "F = 2 · 3 = 6 Н.", "Ответ: 6 Н в сторону ускорения."],
       ["F = m·a.", "F = 2 · 3 = 6 N.", "Answer: 6 N in the direction of the acceleration."])),
     (("На груз 5 кг действуют вверх 30 Н и вниз 40 Н. Найдите ускорение.",
       "A 5 kg load has 30 N up and 40 N down. Find the acceleration."),
      (["Равнодействующая: 30 − 40 = −10 Н (вниз).", "a = F/m = −10/5 = −2 м/с².",
        "Ответ: 2 м/с², направлено вниз."],
       ["Net force: 30 − 40 = −10 N (downwards).", "a = −10/5 = −2 m/s².",
        "Answer: 2 m/s², directed downwards."]))],
    (["Ремень в машине: при резком торможении тело продолжает двигаться по инерции — "
      "первый закон спасает жизнь именно в этой ситуации.",
      "Модель «масса точки в центре» подходит для коротких примеров; для вращающегося "
      "тела уже нужны момент силы и распределение массы."],
     ["A seat belt works through inertia: during hard braking the body keeps moving — the "
      "first law is exactly what the belt handles.",
      "The point-mass model suffices for simple problems; a rotating body needs torques and "
      "mass distribution."]),
    figures=("force-diagram",),
)

_lesson(
    "forces-weight", "Сила тяжести и вес", "Gravity and weight",
    (["Сила тяжести F = m·g приложена к самому телу и направлена к центру Земли.",
      "Вес — сила, с которой тело действует на опору или подвес; в покое на горизонтальной "
      "опоре вес равен m·g, но это разные силы, приложенные к разным телам."],
     ["Gravity F = m·g acts on the body itself and points to the Earth's centre.",
      "Weight is the force the body exerts on its support; at rest on a horizontal support it "
      "equals m·g, yet gravity and weight act on different bodies."]),
    (["В лифте, движущемся с ускорением вверх, вес растёт: P = m(g + a); при ускорении "
      "вниз — уменьшается: P = m(g − a).",
      "В состоянии невесомости (свободное падение) вес равен нулю, а масса сохраняется.",
      "Единицы измерения: масса — килограммы, сила и вес — ньютоны."],
     ["In an accelerating lift the weight changes: P = m(g + a) upwards and P = m(g − a) "
      "downwards.",
      "In weightlessness (free fall) the weight is zero while the mass remains.",
      "Units: mass in kilograms, force and weight in newtons."]),
    [(("Найдите вес груза 12 кг, стоящего на полу. g = 9,8 м/с².",
       "Find the weight of a 12 kg load standing on the floor. g = 9.8 m/s²."),
      (["P = m·g.", "P = 12 · 9,8 = 117,6 Н.", "Ответ: ≈ 118 Н (масса остаётся 12 кг)."],
       ["P = m·g.", "P = 12 · 9.8 = 117.6 N.", "Answer: ≈ 118 N (the mass stays 12 kg)."]))],
    (["В магазине «весят» на самом деле измеряют массу в килограммах: настоящий вес "
      "12 кг груза — около 118 Н, просто весы заранее поделили на g.",
      "Модель P = mg верна для покоя; в падающем лифте вес исчезает, поэтому ремень "
      "безопасности нужен и в вертикальном движении."],
     ["Shop scales actually measure mass in kilograms: the true weight of 12 kg is about 118 N, "
      "the device simply divided by g.",
      "P = mg holds at rest; in a falling lift the weight vanishes, which matters for safety "
      "belts."]),
)

_lesson(
    "friction-elasticity", "Силы трения и упругости", "Friction and elasticity",
    (["Сила трения скольжения Fтр = μ·N, где μ — коэффициент трения, N — сила нормального "
      "давления. Трение направлено против относительного движения.",
      "Сила упругости подчиняется закону Гука F = k·x в пределах упругости; x — деформация "
      "(удлинение или сжатие), k — жёсткость в Н/м."],
     ["Sliding friction is F = μ·N with μ the friction coefficient and N the normal force; it "
      "opposes relative motion.",
      "Within the elastic limit the elastic force obeys Hooke's law F = k·x, where x is the "
      "deformation and k the stiffness in N/m."]),
    (["На наклонной плоскости N = m·g·cos α, поэтому N меньше веса: подставлять m·g "
      "вместо N — типичная ошибка.",
      "Трение покоя принимает любое значение до μN и только при предельном значении "
      "начинается скольжение.",
      "Закон Гука работает только до предела упругости: за ним график F(x) становится "
      "нелинейным, а деформация — остаточной."],
     ["On an incline N = m·g·cos α, so N is smaller than the weight; substituting m·g for N is "
      "a classic mistake.",
      "Static friction can be anything up to μN; sliding starts at the limit.",
      "Hooke's law holds up to the elastic limit; beyond it the graph bends and the deformation "
      "becomes permanent."]),
    [(("Брусок 4 кг тянут по горизонтальному столу, μ = 0,25. Найдите силу трения.",
       "A 4 kg block is pulled across a table with μ = 0.25. Find the friction force."),
      (["N = m·g = 4 · 9,8 = 39,2 Н.", "Fтр = μ·N = 0,25 · 39,2 = 9,8 Н.",
        "Ответ: ≈ 9,8 Н (направлена против движения)."],
       ["N = m·g = 4 · 9.8 = 39.2 N.", "F = μ·N = 0.25 · 39.2 = 9.8 N.",
        "Answer: ≈ 9.8 N against the motion."])),
     (("Пружину жёсткостью 200 Н/м растянули на 4 см. Найдите силу упругости.",
       "A spring of stiffness 200 N/m is stretched by 4 cm. Find the elastic force."),
      (["Переведём: 4 см = 0,04 м.", "F = k·x = 200 · 0,04 = 8 Н.",
        "Ответ: 8 Н, направлена к положению равновесия."],
       ["Convert: 4 cm = 0.04 m.", "F = k·x = 200 · 0.04 = 8 N.",
        "Answer: 8 N towards the equilibrium."]))],
    (["Тормозной путь на льду в разы больше, чем на асфальте, потому что μ отличается "
      "в несколько раз — сила трения при той же массе разная.",
      "Модель «трение не зависит от площади контакта» верна для сухого трения скольжения; "
      "для широких шин важнее давление и материал, и это уже за рамками школьной модели."],
     ["Braking distances on ice are far longer than on asphalt because μ differs severalfold at "
      "the same mass.",
      "Independent-of-area dry friction is the school model; real tyres also depend on pressure "
      "and material."]),
    figures=("incline-forces", "spring-hooke"),
)

_lesson(
    "force-diagram", "Свободная диаграмма сил", "Free-body diagram",
    (["Свободная диаграмма сил — рисунок, на котором показано только рассматриваемое тело "
      "и все силы, действующие на него со стороны других тел.",
      "Порядок работы: выбрать тело, указать систему отсчёта, нарисовать все силы, "
      "выбрать оси и записать второй закон Ньютона в проекциях."],
     ["A free-body diagram shows the chosen body and every force acting on it from other bodies.",
      "Procedure: choose the body, state the frame, draw all forces, choose axes and write "
      "Newton's second law in projections."]),
    (["Одна стрелка — одна сила: если на тело действуют две силы со стороны одного тела, "
      "рисуют две стрелки (или одну равнодействующую, но тогда её и подписывают).",
      "Реакция опоры перпендикулярна поверхности; сила трения — вдоль поверхности.",
      "Силы, приложенные к другим телам, на диаграмму не переносятся."],
     ["One arrow per force: two forces from one body are drawn as two arrows (or as one "
      "resultant, labelled as such).",
      "A normal reaction is perpendicular to the surface; friction runs along the surface.",
      "Forces acting on other bodies are not transferred to this diagram."]),
    [(("Составьте уравнение движения для бруска, тянутого по столу с силой F.",
       "Write the equation of motion for a block pulled along a table by F."),
      (["По горизонтали: F − Fтр = m·a.", "По вертикали: N − m·g = 0, значит N = m·g.",
        "Отсюда a = (F − μmg)/m."],
       ["Horizontally: F − F_fr = m·a.", "Vertically: N − m·g = 0, so N = m·g.",
        "Therefore a = (F − μmg)/m."]))],
    (["Разбирая «почему санки не едут», полезно нарисовать силы: тяга, трение, тяжесть и "
      "реакция — тогда видно, какая из них слишком мала.",
      "Модель без сопротивления воздуха годится для медленных тел; для велосипедиста "
      "на спуске сопротивление уже сравнимо с тягой."],
     ["When a sledge will not move, a force sketch shows which of pull, friction, gravity or "
      "reaction is too small.",
      "Ignoring air drag is fine for slow bodies; for a cyclist downhill it is comparable to "
      "the drive."]),
    figures=("force-diagram", "incline-forces"),
)

# --------------------------------------------------------------------------- #
#  4. Работа, энергия, импульс
# --------------------------------------------------------------------------- #

_lesson(
    "work-power", "Работа, мощность, КПД", "Work, power, efficiency",
    (["Механическая работа A = F·s·cos α, где α — угол между силой и перемещением; "
      "измеряется в джоулях: 1 Дж = 1 Н·м.",
      "Мощность P = A/t — скорость совершения работы, измеряется в ваттах: 1 Вт = 1 Дж/с.",
      "КПД — отношение полезной работы ко всей затраченной: η = Aполез/Aзатр, обычно в процентах."],
     ["Work A = F·s·cos α with α the angle between force and displacement, measured in joules.",
      "Power P = A/t is the rate of work, measured in watts.",
      "Efficiency η = A_useful/A_total, usually given in percent."]),
    (["Если сила перпендикулярна перемещению (cos 90° = 0), работа равна нулю: сила тяжести "
      "не совершает работы при движении по горизонтали.",
      "При равномерном движении работа тяги равна работе против трения, а полезная "
      "работа меньше затраченной из-за потерь.",
      "КПД всегда меньше 100 %: часть энергии уходит в тепло и звук."],
     ["A force perpendicular to the displacement does no work: gravity does none in horizontal "
      "motion.",
      "In uniform motion the drive work balances friction, and useful work is less than total "
      "work because of losses.",
      "Efficiency is always below 100 %: part of the energy becomes heat and sound."]),
    [(("Ящик тянут силой 60 Н на 5 м под углом 60° к перемещению. Найдите работу.",
       "A crate is pulled with 60 N over 5 m at 60° to the displacement. Find the work."),
      (["A = F·s·cos α.", "cos 60° = 0,5.", "A = 60 · 5 · 0,5 = 150 Дж."],
       ["A = F·s·cos α.", "cos 60° = 0.5.", "A = 60 · 5 · 0.5 = 150 J."])),
     (("Подъёмник поднимает 200 кг на 6 м за 20 с. Найдите полезную мощность.",
       "A hoist lifts 200 kg by 6 m in 20 s. Find the useful power."),
      (["A = m·g·h = 200 · 9,8 · 6 = 11 760 Дж.", "P = A/t = 11 760 / 20 = 588 Вт.",
        "Ответ: ≈ 588 Вт (двигатель потребляет больше)."],
       ["A = m·g·h = 200 · 9.8 · 6 = 11 760 J.", "P = A/t = 11 760 / 20 = 588 W.",
        "Answer: ≈ 588 W (the motor draws more)."]))],
    (["Человек несёт чемодан по горизонтали: тяжесть не совершает работы, хотя руки "
      "устают — усталость не равна совершённой работе.",
      "Модель «КПД постоянен» верна для узкого диапазона нагрузки: у реального двигателя "
      "с ростом мощности КПД меняется."],
     ["Carrying a suitcase horizontally involves no work by gravity, although the arm tires — "
      "fatigue is not work.",
      "Constant efficiency holds only in a narrow load range; a real motor changes efficiency "
      "with load."]),
)

_lesson(
    "energy-conservation", "Закон сохранения энергии", "Conservation of energy",
    (["Кинетическая энергия Eк = m·v²/2; потенциальная энергия в поле тяжести Eп = m·g·h; "
      "энергия упругой деформации E = k·x²/2.",
      "Полная механическая энергия сохраняется, если действуют только консервативные силы "
      "(тяжесть, упругость) и нет трения и других потерь."],
     ["Kinetic energy E = m·v²/2, gravitational potential energy E = m·g·h, elastic energy "
      "E = k·x²/2.",
      "The total mechanical energy is conserved when only conservative forces act and losses "
      "are absent."]),
    (["С трением механическая энергия уменьшается, но полная энергия системы сохраняется: "
      "потерянное превращается во внутреннюю энергию.",
      "Энергию удобно считать от выбранного нулевого уровня: физический смысл имеет только "
      "изменение энергии.",
      "Скорость из закона сохранения: m·g·h = m·v²/2, откуда v = √(2gh) — масса сокращается."],
     ["With friction the mechanical energy decreases while the total energy of the system is "
      "conserved as internal energy.",
      "Energy is counted from a chosen zero level; only its change is physical.",
      "From m·g·h = m·v²/2 the speed is v = √(2gh): the mass cancels."]),
    [(("Санки скатываются с горки высотой 5 м без трения. Найдите скорость у подножия.",
       "A sledge slides down a 5 m hill without friction. Find the speed at the bottom."),
      (["m·g·h = m·v²/2.", "v = √(2gh) = √(2 · 9,8 · 5) = √98 ≈ 9,9 м/с.",
        "Ответ: ≈ 9,9 м/с независимо от массы."],
       ["m·g·h = m·v²/2.", "v = √(2gh) = √(2 · 9.8 · 5) = √98 ≈ 9.9 m/s.",
        "Answer: ≈ 9.9 m/s independent of mass."])),
     (("Найдите энергию пружины k = 400 Н/м, сжатой на 5 см.",
       "Find the energy of a spring k = 400 N/m compressed by 5 cm."),
      (["x = 0,05 м.", "E = k·x²/2 = 400 · 0,0025 / 2 = 0,5 Дж.",
        "Ответ: 0,5 Дж."],
       ["x = 0.05 m.", "E = 400 · 0.0025 / 2 = 0.5 J.", "Answer: 0.5 J."]))],
    (["Велосипедист на спуске разгоняется, а на подъёме замедляется: высота и скорость "
      "обмениваются, пока трение и сопротивление не «съедят» часть энергии.",
      "Модель без потерь завышает скорость и высоту подъёма: в реальности всегда есть "
      "трение в цепи и сопротивление воздуха."],
     ["A cyclist speeds up downhill and slows uphill: height and speed trade, until friction "
      "and drag take their share.",
      "The lossless model overestimates speed and climb: real chains and air always take energy."]),
)

_lesson(
    "momentum", "Импульс и закон сохранения импульса", "Momentum and its conservation",
    (["Импульс тела p = m·v — вектор, измеряется в кг·м/с. Импульс силы F·t равен "
      "изменению импульса тела.",
      "Импульс системы сохраняется, если внешние силы пренебрежимо малы или скомпенсированы."],
     ["Momentum p = m·v is a vector measured in kg·m/s; the impulse F·t equals its change.",
      "The momentum of a system is conserved when external forces are negligible or balanced."]),
    (["При абсолютно упругом ударе сохраняются и импульс, и кинетическая энергия; "
      "при неупругом — только импульс, тела движутся вместе.",
      "Импульс векторный: уравнения записывают в проекциях на выбранную ось.",
      "Реактивное движение и отдача — следствие сохранения импульса, а не «толчка воздуха»."],
     ["An elastic collision conserves both momentum and kinetic energy; a perfectly inelastic "
      "one keeps only momentum and the bodies move together.",
      "Momentum is a vector: write the equations in projections.",
      "Jet propulsion and recoil follow from momentum conservation."]),
    [(("Тело 2 кг со скоростью 3 м/с сцепляется с покоящимся телом 4 кг. Найдите общую скорость.",
       "A 2 kg body at 3 m/s sticks to a stationary 4 kg body. Find their common speed."),
      (["m₁v₁ = (m₁ + m₂)u.", "u = 2·3/(2+4) = 1 м/с.", "Ответ: 1 м/с в сторону движения."],
       ["m₁v₁ = (m₁ + m₂)u.", "u = 2·3/(2+4) = 1 m/s.", "Answer: 1 m/s in the original direction."])),
     (("Из ружья 4 кг вылетает пуля 10 г со скоростью 400 м/с. Найдите скорость отдачи.",
       "A 10 g bullet leaves a 4 kg rifle at 400 m/s. Find the recoil speed."),
      (["Импульсы равны по модулю: M·V = m·v.", "V = 0,01 · 400 / 4 = 1 м/с.",
        "Ответ: 1 м/с в сторону, противоположную пуле."],
       ["Equal momenta: M·V = m·v.", "V = 0.01 · 400 / 4 = 1 m/s.",
        "Answer: 1 m/s opposite to the bullet."]))],
    (["При столкновении двух машин импульс всей системы до и после примерно один и тот же — "
      "именно поэтому удар «сминает» лёгкую машину сильнее.",
      "Модель замкнутой системы годится для короткого удара: за время удара внешние "
      "силы не успевают изменить суммарный импульс."],
     ["In a car crash the momentum of the pair is nearly the same before and after; that is why "
      "the lighter car crumples more.",
      "The closed-system model works for a short impact, when external forces barely change the "
      "total momentum."]),
)

# --------------------------------------------------------------------------- #
#  5. Статика, давление, гидростатика
# --------------------------------------------------------------------------- #

_lesson(
    "torque", "Момент силы и равновесие", "Torque and equilibrium",
    (["Момент силы относительно оси M = F·d, где d — плечо: расстояние по перпендикуляру "
      "от оси вращения до линии действия силы; измеряется в Н·м.",
      "Тело в равновесии, когда равны нулю и сумма сил, и сумма моментов относительно "
      "любой оси: твёрдое тело не может «уехать» и не может «закрутиться»."],
     ["Torque about an axis M = F·d with d the perpendicular distance from the axis to the "
      "line of action, measured in N·m.",
      "Equilibrium needs zero net force and zero net torque about any axis."]),
    (["Плечо — перпендикуляр, а не длина рычага и не расстояние по наклонной линии действия.",
      "Момент вращает по часовой стрелке или против: у моментов есть знак, их складывают "
      "алгебраически.",
      "Правило рычага F₁·d₁ = F₂·d₂ — следствие равенства моментов."],
     ["The lever arm is the perpendicular distance, not the length of the lever.",
      "Torques have signs: clockwise and counter-clockwise torques add algebraically.",
      "The lever rule F₁d₁ = F₂d₂ follows from equal torques."]),
    [(("На рычаге плечо 0,2 м и груз 30 Н. Какую силу приложить к плечу 0,6 м для равновесия?",
       "A lever has a 30 N load on a 0.2 m arm. What force balances it on a 0.6 m arm?"),
      (["F₁·d₁ = F₂·d₂.", "30 · 0,2 = F · 0,6.", "F = 6 / 0,6 = 10 Н."],
       ["F₁·d₁ = F₂·d₂.", "30 · 0.2 = F · 0.6.", "F = 6 / 0.6 = 10 N."]))],
    (["Дверная ручка стоит далеко от петель именно чтобы плечо было больше и момент "
      "при меньшей силе — это и есть физика рычага.",
      "Модель «рычаг невесом» годится для школьных задач; у реального рычага есть "
      "собственный вес, и его момент тоже нужно учитывать."],
     ["A door handle sits far from the hinges to enlarge the lever arm and reduce the needed "
      "force.",
      "The weightless-lever model is fine for school problems; a real lever also has its own "
      "weight moment."]),
    figures=("lever-torque",),
)

_lesson(
    "pressure-hydrostatics", "Давление и гидростатика", "Pressure and hydrostatics",
    (["Давление p = F/S — сила, действующая перпендикулярно поверхности, делённая на "
      "площадь; измеряется в паскалях: 1 Па = 1 Н/м².",
      "Давление жидкости на глубине h: p = ρ·g·h, где ρ — плотность жидкости; "
      "добавочное давление зависит только от глубины."],
     ["Pressure p = F/S is the perpendicular force per unit area, measured in pascals.",
      "Liquid pressure at depth h is p = ρ·g·h, depending only on depth and density."]),
    (["Давление на одной глубине одинаково во всех направлениях: закон Паскаля.",
      "Форма и объём сосуда не входят в p = ρgh: узкий и широкий сосуды одинаковой высоты "
      "дают одинаковое давление на дне.",
      "Давление на дно больше атмосферного на ρgh; атмосферу добавляют, только если "
      "о ней спрашивают или требуется полное давление."],
     ["At a given depth the pressure is the same in all directions (Pascal's law).",
      "Vessel shape and volume do not enter p = ρgh: wide and narrow vessels of equal height "
      "give the same bottom pressure.",
      "Gauge pressure is ρgh above atmospheric; add the atmosphere only when the total pressure "
      "is requested."]),
    [(("Найдите давление воды на глубине 10 м. ρ = 1000 кг/м³, g = 9,8 м/с².",
       "Find the water pressure at 10 m. ρ = 1000 kg/m³, g = 9.8 m/s²."),
      (["p = ρ·g·h.", "p = 1000 · 9,8 · 10 = 98 000 Па.", "Ответ: ≈ 98 кПа добавочного давления."],
       ["p = ρ·g·h.", "p = 1000 · 9.8 · 10 = 98 000 Pa.", "Answer: ≈ 98 kPa of gauge pressure."])),
     (("Лыжник 70 кг стоит на лыжах площадью 0,2 м². Найдите давление на снег.",
       "A 70 kg skier stands on 0.2 m² skis. Find the pressure on the snow."),
      (["F = m·g = 70 · 9,8 = 686 Н.", "p = F/S = 686 / 0,2 = 3430 Па.",
        "Ответ: ≈ 3,4 кПа."],
       ["F = m·g = 70 · 9.8 = 686 N.", "p = F/S = 686 / 0.2 = 3430 Pa.", "Answer: ≈ 3.4 kPa."]))],
    (["Широкие лыжи снижают давление и человек не проваливается; тот же вес на узких "
      "ботинках давит в разы сильнее.",
      "Модель несжимаемой жидкости: вода почти не сжимается, поэтому p = ρgh работает "
      "хорошо; для газа она не применяется."],
     ["Wide skis spread the same weight over more area, so the pressure drops.",
      "The incompressible-liquid model suits water well; it does not apply to gases."]),
    figures=("pressure-depth",),
)

_lesson(
    "archimedes", "Сила Архимеда и плавание", "Buoyancy and floating",
    (["На тело, погружённое в жидкость, действует архимедова сила FА = ρж·Vпогр·g, "
      "направленная вертикально вверх и равная весу вытесненной жидкости.",
      "Условие плавания: FА = m·g, то есть ρж·Vпогр = ρтела·Vтела. Тело плавает, если его "
      "средняя плотность меньше плотности жидкости."],
     ["Buoyancy F = ρ_liquid·V_submerged·g points upwards and equals the weight of the "
      "displaced liquid.",
      "Floating needs ρ_liquid·V_submerged = ρ_body·V_body."]),
    (["В формуле стоит объём погружённой части, а не всего тела: у плавающего айсберга "
      "под водой примерно 90 % объёма.",
      "Если тело тонет, FА < m·g; если всплывает — FА > m·g.",
      "Сила Архимеда есть и в воздухе, но для бытовых тел она в сотни раз меньше веса."],
     ["The formula uses the submerged volume, not the whole body: about 90 % of an iceberg is "
      "under water.",
      "Sinking means F < mg; rising means F > mg.",
      "Buoyancy exists in air too, but is hundreds of times smaller than weight."]),
    [(("Брусок объёмом 0,002 м³ полностью погружён в воду. Найдите силу Архимеда.",
       "A 0.002 m³ block is fully submerged in water. Find the buoyant force."),
      (["FА = ρж·V·g.", "FА = 1000 · 0,002 · 9,8 = 19,6 Н.", "Ответ: 19,6 Н вверх."],
       ["F = ρ·V·g.", "F = 1000 · 0.002 · 9.8 = 19.6 N.", "Answer: 19.6 N upwards."])),
     (("Тело массой 1,2 кг и объёмом 0,001 м³ опустили в воду. Утонет ли оно?",
       "A 1.2 kg body of volume 0.001 m³ is put into water. Will it sink?"),
      (["FА = 1000 · 0,001 · 9,8 = 9,8 Н.", "mg = 1,2 · 9,8 = 11,76 Н.",
        "FА < mg, значит тело утонет."],
       ["F = 1000 · 0.001 · 9.8 = 9.8 N.", "mg = 1.2 · 9.8 = 11.76 N.",
        "F < mg, so the body sinks."]))],
    (["Корабль не тонет, потому что его средняя плотность с воздухом внутри меньше "
      "плотности воды, хотя сталь тяжелее воды.",
      "Модель «жидкость покоится» не учитывает волны и течение; в шторм плавучесть "
      "оценивают уже другими методами."],
     ["A ship floats because its average density including air is below that of water, although "
      "steel itself is denser.",
      "The still-liquid model ignores waves and currents."]),
    figures=("buoyancy",),
)

# --------------------------------------------------------------------------- #
#  6. Молекулярная физика
# --------------------------------------------------------------------------- #

_lesson(
    "amount-substance", "Количество вещества и молярная масса", "Amount of substance and molar mass",
    (["Количество вещества ν = m/M измеряется в молях, где M — молярная масса в г/моль. "
      "В одном моле содержится число Авогадро Nₐ ≈ 6,02·10²³ частиц.",
      "Число молекул N = ν·Nₐ = (m/M)·Nₐ."],
     ["Amount of substance ν = m/M is measured in moles with M the molar mass in g/mol; one "
      "mole contains Avogadro's number Nₐ ≈ 6.02·10²³ particles.",
      "The number of molecules is N = ν·Nₐ = (m/M)·Nₐ."]),
    (["Молярная масса численно равна относительной молекулярной массе: у воды M = 18 г/моль.",
      "Масса одной молекулы m₀ = M/Nₐ — очень маленькая величина порядка 10⁻²⁶ кг.",
      "При нормальных условиях один моль любого газа занимает ≈ 22,4 л."],
     ["Molar mass equals the relative molecular mass numerically: water has M = 18 g/mol.",
      "One molecule's mass m₀ = M/Nₐ is of the order of 10⁻²⁶ kg.",
      "At standard conditions one mole of any gas occupies ≈ 22.4 l."]),
    [(("Сколько молей в 90 г воды?", "How many moles are in 90 g of water?"),
      (["M(H₂O) = 2·1 + 16 = 18 г/моль.", "ν = 90/18 = 5 моль.",
        "Ответ: 5 моль, то есть ≈ 3·10²⁴ молекул."],
       ["M(H₂O) = 2·1 + 16 = 18 g/mol.", "ν = 90/18 = 5 mol.",
        "Answer: 5 mol, about 3·10²⁴ molecules."]))],
    (["«Моль» на кухне — это просто порция: 18 г воды, 44 г углекислого газа — по одному "
      "молю, хотя объёмы разные.",
      "Модель «молекулы — маленькие шарики» помогает считать, но не описывает химические "
      "связи; для реакций нужна уже химия."],
     ["A mole is a fixed portion: 18 g of water and 44 g of CO₂ are one mole each, though their "
      "volumes differ.",
      "The little-spheres model counts particles but does not describe chemical bonds."]),
)

_lesson(
    "ideal-gas", "Уравнение состояния идеального газа", "Ideal gas law",
    (["Уравнение состояния: p·V = ν·R·T, где R ≈ 8,31 Дж/(моль·К), T — абсолютная "
      "температура в кельвинах.",
      "Для одной и той же порции газа p₁V₁/T₁ = p₂V₂/T₂ — объединённый газовый закон."],
     ["Equation of state: p·V = ν·R·T with R ≈ 8.31 J/(mol·K) and T in kelvin.",
      "For one gas sample p₁V₁/T₁ = p₂V₂/T₂."]),
    (["Температура в газовых законах обязательно в кельвинах: T = t + 273.",
      "Идеальный газ — модель: молекулы не взаимодействуют, кроме упругих столкновений, "
      "а их размеры малы по сравнению с расстояниями.",
      "Из pV = νRT видно: при постоянном объёме рост температуры повышает давление."],
     ["Gas laws always use kelvin: T = t + 273.",
      "An ideal gas is a model: molecules interact only in elastic collisions and are small "
      "compared with the distances between them.",
      "At constant volume a higher temperature raises the pressure."]),
    [(("Газ занимает 2 л при 27 °C. Каким станет объём при 127 °C, если давление постоянное?",
       "A gas occupies 2 l at 27 °C. What volume does it take at 127 °C at constant pressure?"),
      (["Переведём: T₁ = 300 К, T₂ = 400 К.", "V₂ = V₁·T₂/T₁ = 2 · 400/300 ≈ 2,67 л.",
        "Ответ: ≈ 2,67 л (закон Гей-Люссака)."],
       ["Convert: T₁ = 300 K, T₂ = 400 K.", "V₂ = V₁·T₂/T₁ = 2 · 400/300 ≈ 2.67 l.",
        "Answer: ≈ 2.67 l (Gay-Lussac's law)."]))],
    (["Надувной мяч на морозе сжимается: при постоянном давлении объём пропорционален "
      "температуре в кельвинах, а не в градусах Цельсия.",
      "Модель идеального газа хороша при обычных давлениях; при высоком давлении и "
      "близко к сжижению она уже не подходит."],
     ["A ball shrinks in the cold because volume follows kelvin, not Celsius.",
      "The ideal-gas model works at ordinary pressures and fails near liquefaction."]),
)

_lesson(
    "isoprocesses", "Изопроцессы", "Isoprocesses",
    (["Изотермический процесс (T = const): p·V = const — закон Бойля–Мариотта, график — "
      "гипербола в координатах p(V).",
      "Изобарный (p = const): V/T = const — закон Гей-Люссака; изохорный (V = const): "
      "p/T = const — закон Шарля."],
     ["Isothermal (T = const): p·V = const, a hyperbola on the p(V) plane.",
      "Isobaric (p = const): V/T = const; isochoric (V = const): p/T = const."]),
    (["Выбор закона определяется тем, какая величина постоянна по условию задачи.",
      "В изотермическом процессе внутренняя энергия не меняется, но газ совершает работу: "
      "теплота подводится.",
      "Графики изопроцессов строят в координатах с правильными осями: «гипербола» без "
      "подписей физического смысла не имеет."],
     ["The law is chosen by the quantity that stays constant.",
      "In an isothermal process the internal energy is constant while the gas does work and "
      "absorbs heat.",
      "Isoprocess graphs need labelled axes to carry physical meaning."]),
    [(("Газ при 100 кПа занимает 4 л. Каким станет давление при 2 л, если T постоянна?",
       "A gas at 100 kPa occupies 4 l. Find the pressure at 2 l at constant T."),
      (["p₁V₁ = p₂V₂.", "p₂ = p₁V₁/V₂ = 100 · 4/2 = 200 кПа.", "Ответ: 200 кПа."],
       ["p₁V₁ = p₂V₂.", "p₂ = 100 · 4/2 = 200 kPa.", "Answer: 200 kPa."]))],
    (["Насос для велосипеда: при сжатии объём уменьшается и давление растёт — это "
      "изотермический процесс, если воздух не успевает нагреться.",
      "Модель изотермичности ломается при быстром сжатии: воздух заметно нагревается, "
      "и тогда нужен уже адиабатный подход."],
     ["A bicycle pump shows Boyle's law: less volume, more pressure, if the air stays cool.",
      "Fast compression heats the air, so the isothermal model breaks."]),
    figures=("gas-isotherm",),
)

# --------------------------------------------------------------------------- #
#  7. Теплота и термодинамика
# --------------------------------------------------------------------------- #

_lesson(
    "heat-capacity", "Количество теплоты и теплоёмкость", "Heat and specific heat",
    (["При нагревании Q = c·m·Δt, где c — удельная теплоёмкость, Δt — изменение температуры "
      "(в °C или К — численно одинаково).",
      "При сгорании топлива Q = q·m, где q — удельная теплота сгорания; при плавлении и "
      "парообразовании Q = λ·m и Q = L·m."],
     ["Heating: Q = c·m·Δt with c the specific heat and Δt the temperature change.",
      "Combustion gives Q = q·m; melting and boiling give Q = λ·m and Q = L·m."]),
    (["Уравнение теплового баланса: теплота, отданная горячими телами, равна теплоте, "
      "полученной холодными (без потерь).",
      "ΔT в кельвинах и Δt в градусах Цельсия равны численно; сами температуры "
      "переводить нужно, а разность — нет.",
      "Удельная теплоёмкость воды 4200 Дж/(кг·°C) — одна из самых больших у жидкостей."],
     ["Heat balance: the heat given by hot bodies equals the heat taken by cold ones (without "
      "losses).",
      "A difference of 1 °C equals 1 K numerically.",
      "Water's specific heat, 4200 J/(kg·°C), is unusually large."]),
    [(("Сколько теплоты нужно, чтобы нагреть 2 кг воды от 20 °C до 70 °C?",
       "How much heat warms 2 kg of water from 20 °C to 70 °C?"),
      (["Δt = 70 − 20 = 50 °C.", "Q = 4200 · 2 · 50 = 420 000 Дж.",
        "Ответ: 420 кДж."],
       ["Δt = 70 − 20 = 50 °C.", "Q = 4200 · 2 · 50 = 420 000 J.", "Answer: 420 kJ."])),
     (("В 1 кг воды при 20 °C долили 2 кг воды при 80 °C. Найдите конечную температуру.",
       "1 kg of water at 20 °C is mixed with 2 kg at 80 °C. Find the final temperature."),
      (["Тепловой баланс: 1·(t − 20) = 2·(80 − t).", "t + 2t = 160 + 20, значит t = 60 °C.",
        "Ответ: 60 °C."],
       ["Balance: 1·(t − 20) = 2·(80 − t).", "t + 2t = 160 + 20, so t = 60 °C.",
        "Answer: 60 °C."]))],
    (["Чайник нагревается долго именно из-за большой теплоёмкости воды: чтобы вскипятить "
      "литр, нужно около 3,4·10⁵ Дж.",
      "Модель «вся теплота идёт в воду» без потерь завышает итог: часть тепла уходит в "
      "воздух и сам чайник."],
     ["A kettle takes time because water's heat capacity is large: boiling a litre needs about "
      "3.4·10⁵ J.",
      "The lossless model overestimates: part of the heat warms the air and the kettle body."]),
)

_lesson(
    "phase-first-law", "Фазовые переходы и первый закон термодинамики", "Phase transitions and the first law",
    (["Во время плавления и кипения температура постоянна: подводимая теплота идёт на "
      "разрушение связей, Q = λ·m при плавлении и Q = L·m при парообразовании.",
      "Первый закон термодинамики: ΔU = Q + Aвнешн — изменение внутренней энергии равно "
      "сумме теплоты и работы внешних сил."],
     ["During melting and boiling the temperature stays constant: the heat breaks bonds, "
      "Q = λ·m and Q = L·m.",
      "First law: ΔU = Q + A_external."]),
    (["График нагрева-плавления имеет горизонтальные площадки; их длина показывает, сколько "
      "теплоты уходит на фазовый переход.",
      "Работа самого газа при расширении противоположна работе внешних сил: Aгаза = −Aвнешн.",
      "Внутренняя энергия идеального газа зависит только от температуры; при изотермическом "
      "процессе ΔU = 0, значит Q = −Aвнешн."],
     ["The heating graph has horizontal plateaus whose length shows the latent heat.",
      "The gas's own work on expansion is minus the work of external forces.",
      "For an ideal gas the internal energy depends only on temperature."]),
    [(("Сколько теплоты нужно, чтобы расплавить 2 кг льда при 0 °C? λ = 3,4·10⁵ Дж/кг.",
       "How much heat melts 2 kg of ice at 0 °C? λ = 3.4·10⁵ J/kg."),
      (["Q = λ·m.", "Q = 3,4·10⁵ · 2 = 6,8·10⁵ Дж.", "Ответ: 680 кДж, температура при этом не меняется."],
       ["Q = λ·m.", "Q = 3.4·10⁵ · 2 = 6.8·10⁵ J.", "Answer: 680 kJ with no temperature change."]))],
    (["Кипящая вода не становится горячее 100 °C при обычном давлении: вся подводимая "
      "энергия уходит на превращение в пар.",
      "Модель постоянных λ и L верна при данном давлении; в горах температура кипения "
      "ниже, и это уже другая точка фазового перехода."],
     ["Boiling water stays at 100 °C at normal pressure: the energy becomes vapour.",
      "λ and L hold at a given pressure; in the mountains water boils cooler."]),
    figures=("heating-curve",),
)

# --------------------------------------------------------------------------- #
#  8. Электростатика
# --------------------------------------------------------------------------- #

_lesson(
    "coulomb-field", "Закон Кулона и напряжённость поля", "Coulomb's law and field strength",
    (["Сила взаимодействия двух точечных зарядов F = k·|q₁q₂|/r², где k ≈ 9·10⁹ Н·м²/Кл²; "
      "одноимённые заряды отталкиваются, разноимённые притягиваются.",
      "Напряжённость электрического поля E = F/q — силовая характеристика, измеряется "
      "в В/м (или Н/Кл)."],
     ["Coulomb force F = k·|q₁q₂|/r² with k ≈ 9·10⁹ N·m²/C²; like charges repel.",
      "Field strength E = F/q is measured in V/m."]),
    (["Закон Кулона применим к точечным зарядам; при увеличении расстояния вдвое сила "
      "уменьшается вчетверо (обратный квадрат).",
      "Линии напряжённости выходят из положительных зарядов и входят в отрицательные; "
      "густота линий показывает величину поля.",
      "Сила Кулона направлена вдоль прямой, соединяющей заряды."],
     ["Coulomb's law holds for point charges; doubling the distance quarters the force.",
      "Field lines leave positive charges and enter negative ones; their density shows the "
      "field magnitude.",
      "The Coulomb force acts along the line joining the charges."]),
    [(("Два заряда по 2·10⁻⁶ Кл на расстоянии 0,1 м. Найдите силу взаимодействия.",
       "Two charges of 2·10⁻⁶ C are 0.1 m apart. Find the force."),
      (["F = k·q₁q₂/r².", "F = 9·10⁹ · (2·10⁻⁶)² / 0,01 = 3,6 Н.", "Ответ: 3,6 Н."],
       ["F = k·q₁q₂/r².", "F = 9·10⁹ · (2·10⁻⁶)² / 0.01 = 3.6 N.", "Answer: 3.6 N."]))],
    (["Статическое электричество на одежде: заряды разделились трением, а притягиваются "
      "они уже по закону Кулона — искра в темноте это разряд.",
      "Модель точечных зарядов не подходит для протяжённых тел: у реального заряженного "
      "шара поле снаружи такое же, как у точечного заряда в центре, но внутри — другое."],
     ["Static cling comes from charges separated by friction and then attracting by Coulomb's "
      "law.",
      "The point-charge model fails inside extended bodies."]),
    figures=("field-lines",),
)

_lesson(
    "potential-capacitance", "Потенциал, напряжение, конденсатор", "Potential, voltage, capacitor",
    (["Потенциал φ — энергетическая характеристика поля: работа по переносу заряда "
      "A = q·(φ₁ − φ₂) = q·U; напряжение измеряется в вольтах.",
      "Электроёмкость C = q/U измеряется в фарадах; для плоского конденсатора "
      "C = ε·ε₀·S/d."],
     ["Potential φ is the energy characteristic: A = q·(φ₁ − φ₂) = q·U, in volts.",
      "Capacitance C = q/U in farads; for a flat capacitor C = ε·ε₀·S/d."]),
    (["Напряжение — разность потенциалов, а не «заряд» и не «поток вещества».",
      "В однородном поле E = U/d: чем меньше расстояние между пластинами, тем сильнее поле "
      "при том же напряжении.",
      "Ёмкость увеличивают, сближая пластины и увеличивая площадь: C ~ S/d."],
     ["Voltage is a potential difference, not a charge or a flow of substance.",
      "In a uniform field E = U/d.",
      "Capacitance grows with area and shrinks with the gap: C ~ S/d."]),
    [(("Заряд 4·10⁻⁶ Кл перенесён между точками с напряжением 200 В. Найдите работу поля.",
       "A 4·10⁻⁶ C charge moves across 200 V. Find the work of the field."),
      (["A = q·U.", "A = 4·10⁻⁶ · 200 = 8·10⁻⁴ Дж.", "Ответ: 8·10⁻⁴ Дж."],
       ["A = q·U.", "A = 4·10⁻⁶ · 200 = 8·10⁻⁴ J.", "Answer: 8·10⁻⁴ J."]))],
    (["Батарейка «1,5 В» — это не «1,5 заряда», а разность потенциалов: она задаёт, какую "
      "работу совершит каждый кулон заряда.",
      "Модель однородного поля годится между плоскими пластинами; у точечного заряда "
      "потенциал убывает как 1/r."],
     ["A 1.5 V battery sets a potential difference, not an amount of charge.",
      "The uniform-field model fits flat plates; a point charge has φ ~ 1/r."]),
)

# --------------------------------------------------------------------------- #
#  9. Постоянный ток
# --------------------------------------------------------------------------- #

_lesson(
    "ohm-law", "Закон Ома и сопротивление", "Ohm's law and resistance",
    (["Сила тока I = q/t — заряд, проходящий через сечение за единицу времени; "
      "измеряется в амперах.",
      "Закон Ома для участка цепи: I = U/R, где R — сопротивление в омах. "
      "Сопротивление проводника R = ρ·l/S."],
     ["Current I = q/t, measured in amperes.",
      "Ohm's law: I = U/R, with resistance in ohms; R = ρ·l/S for a wire."]),
    (["Ток не «расходуется» в лампе: сила тока одинакова до и после неё, меняется "
      "напряжение (и нагрев).",
      "Сопротивление зависит от материала, длины и площади: длиннее — больше, толще — меньше.",
      "Закон Ома в виде I = U/R справедлив для металлов и резисторов при постоянной "
      "температуре."],
     ["Current is not consumed by a lamp: the same current flows before and after it.",
      "Resistance grows with length and falls with thickness.",
      "I = U/R holds for metals and resistors at constant temperature."]),
    [(("Напряжение на резисторе 12 В, сопротивление 4 Ом. Найдите ток и мощность.",
       "A resistor has 12 V across 4 Ω. Find current and power."),
      (["I = U/R = 12/4 = 3 А.", "P = U·I = 12 · 3 = 36 Вт.", "Ответ: 3 А и 36 Вт."],
       ["I = U/R = 12/4 = 3 A.", "P = U·I = 12 · 3 = 36 W.", "Answer: 3 A and 36 W."]))],
    (["Удлинитель на 20 метров добавляет сопротивление: при той же нагрузке нагреватель "
      "получит меньше напряжения, чем у короткого шнура.",
      "Модель «R постоянно» ломается при нагреве спирали: сопротивление нити лампы накала "
      "в холодном состоянии в разы меньше."],
     ["A long extension cord adds resistance, so the appliance receives less voltage.",
      "Constant R fails for a lamp filament: its cold resistance is several times smaller."]),
)

_lesson(
    "circuits", "Соединения проводников", "Series and parallel connections",
    (["Последовательное соединение: сила тока одинакова во всех элементах, напряжения "
      "складываются: R = R₁ + R₂ + …",
      "Параллельное соединение: напряжение одинаково, токи складываются, "
      "1/R = 1/R₁ + 1/R₂; общее сопротивление меньше наименьшего."],
     ["Series: the current is the same and voltages add, R = R₁ + R₂ + …",
      "Parallel: the voltage is the same and currents add, 1/R = 1/R₁ + 1/R₂."]),
    (["Амперметр включают последовательно (через него идёт измеряемый ток), вольтметр — "
      "параллельно участку; идеальные приборы не меняют цепь.",
      "Для двух параллельных резисторов удобна формула R = R₁·R₂/(R₁ + R₂), "
      "для двух последовательных — сумма.",
      "Лампы в гирлянде при последовательном соединении гаснут все, при параллельном — "
      "только одна."],
     ["An ammeter goes in series, a voltmeter in parallel.",
      "Two parallel resistors: R = R₁R₂/(R₁ + R₂).",
      "Series bulbs all go out together; parallel ones do not."]),
    [(("Резисторы 6 Ом и 3 Ом соединены параллельно. Найдите общее сопротивление.",
       "Resistors of 6 Ω and 3 Ω are in parallel. Find the total resistance."),
      (["1/R = 1/6 + 1/3 = 1/6 + 2/6 = 3/6.", "R = 2 Ом.",
        "Ответ: 2 Ом — меньше самого маленького."],
       ["1/R = 1/6 + 1/3 = 3/6.", "R = 2 Ω.", "Answer: 2 Ω, below the smallest resistor."])),
     (("Два резистора 2 Ом и 3 Ом соединены последовательно, напряжение 10 В. Найдите ток.",
       "Resistors 2 Ω and 3 Ω are in series across 10 V. Find the current."),
      (["R = 2 + 3 = 5 Ом.", "I = U/R = 10/5 = 2 А.", "Ответ: 2 А (через оба резистора один ток)."],
       ["R = 2 + 3 = 5 Ω.", "I = 10/5 = 2 A.", "Answer: 2 A through both resistors."]))],
    (["Лампочки в ёлочной гирлянде, соединённые последовательно, гаснут все сразу — "
      "это прямое следствие одинакового тока в цепи.",
      "Модель идеальных приборов: реальный вольтметр имеет большое, но конечное "
      "сопротивление и слегка «подгружает» цепь."],
     ["Series fairy lights all go out at once because the current is shared.",
      "Ideal meters have infinite and zero resistance; real ones slightly disturb the circuit."]),
    figures=("circuit-series", "circuit-parallel"),
)

_lesson(
    "current-work", "Работа и мощность тока", "Electric work and power",
    (["Работа тока A = U·I·t = I²·R·t = U²·t/R, мощность P = U·I измеряется в ваттах.",
      "Бытовая энергия измеряется в киловатт-часах: 1 кВт·ч = 3,6·10⁶ Дж."],
     ["Electric work A = UIt = I²Rt = U²t/R and power P = UI in watts.",
      "Domestic energy uses kilowatt-hours: 1 kWh = 3.6·10⁶ J."]),
    (["Из трёх записей мощности выбирают ту, где известны величины: P = I²R удобна при "
      "последовательном соединении, P = U²/R — при параллельном.",
      "Провода рассчитывают по допустимому току: нагрев пропорционален I²R, и тонкий "
      "провод перегревается.",
      "Счётчик электроэнергии фиксирует работу, а не мощность: важно, сколько времени "
      "прибор включён."],
     ["Pick the power form matching known values: P = I²R for series, P = U²/R for parallel.",
      "Wires are rated by current because heating goes as I²R.",
      "A meter counts work, not power: the time matters."]),
    [(("Чайник 2000 Вт работал 5 минут. Найдите работу тока в кВт·ч.",
       "A 2000 W kettle runs for 5 minutes. Find the electric work in kWh."),
      (["Переведём: 5 мин = 1/12 ч.", "A = P·t = 2 кВт · 1/12 ч ≈ 0,167 кВт·ч.",
        "Ответ: ≈ 0,17 кВт·ч = 6·10⁵ Дж."],
       ["Convert: 5 min = 1/12 h.", "A = 2 kW · 1/12 h ≈ 0.167 kWh.", "Answer: ≈ 0.17 kWh."])),
     (("Лампа 100 Вт при 220 В. Найдите ток и сопротивление.",
       "A 100 W lamp at 220 V. Find current and resistance."),
      (["I = P/U = 100/220 ≈ 0,45 А.", "R = U²/P = 220²/100 = 484 Ом.", "Ответ: ≈ 0,45 А и 484 Ом."],
       ["I = 100/220 ≈ 0.45 A.", "R = U²/P = 484 Ω.", "Answer: ≈ 0.45 A and 484 Ω."]))],
    (["Нагреватель и холодильник: мощность показывает скорость потребления, а счёт "
      "учитывает и мощность, и время работы.",
      "Модель «сопротивление постоянно» приближённая: у нити накала оно меняется при "
      "нагреве, поэтому реальный ток чуть отличается от расчётного."],
     ["A heater and a fridge differ in power, but the bill counts power multiplied by time.",
      "Filament resistance changes with temperature, so the real current differs slightly."]),
)

# --------------------------------------------------------------------------- #
#  10. Магнитное поле и индукция
# --------------------------------------------------------------------------- #

_lesson(
    "magnetic-forces", "Сила Ампера и сила Лоренца", "Ampère and Lorentz forces",
    (["На проводник с током I длиной l в магнитном поле B действует сила Ампера "
      "F = B·I·l·sin α, где α — угол между проводником и линиями поля.",
      "На заряд, движущийся в поле, действует сила Лоренца F = q·v·B·sin α; она "
      "перпендикулярна скорости и магнитному полю."],
     ["Ampère force on a wire: F = B·I·l·sin α.",
      "Lorentz force on a moving charge: F = q·v·B·sin α, perpendicular to velocity and field."]),
    (["Сила максимальна при α = 90° и равна нулю, когда проводник параллелен линиям поля.",
      "Сила Лоренца не совершает работы: она перпендикулярна перемещению, поэтому меняет "
      "направление скорости, но не её модуль.",
      "Направление определяют по правилу левой руки (для тока) или по правилу для "
      "положительного заряда (для отрицательного знак меняется)."],
     ["The force is maximal at α = 90° and zero when parallel to the field lines.",
      "The Lorentz force does no work: it turns the velocity without changing its magnitude.",
      "Direction follows the left-hand rule."]),
    [(("Проводник длиной 0,5 м с током 4 А в поле 0,2 Тл перпендикулярен линиям. "
       "Найдите силу.", "A 0.5 m wire with 4 A is perpendicular to a 0.2 T field. Find the force."),
      (["α = 90°, sin α = 1.", "F = B·I·l = 0,2 · 4 · 0,5 = 0,4 Н.", "Ответ: 0,4 Н."],
       ["α = 90°, sin α = 1.", "F = 0.2 · 4 · 0.5 = 0.4 N.", "Answer: 0.4 N."]))],
    (["Электродвигатель и динамик работают на силе Ампера: ток в поле создаёт движение — "
      "энергия электричества превращается в механическую.",
      "Модель однородного поля годится в пределах магнита; у реального магнита поле "
      "на краях слабее и неоднородно."],
     ["Motors and loudspeakers use the Ampère force to turn current into motion.",
      "The uniform-field model works inside a magnet; real fields weaken at the edges."]),
    figures=("magnetic-wire",),
)

_lesson(
    "induction", "Электромагнитная индукция", "Electromagnetic induction",
    (["Магнитный поток Φ = B·S·cos α через контур измеряется в веберах.",
      "ЭДС индукции |ε| = ΔΦ/Δt: она возникает только при изменении магнитного потока."],
     ["Magnetic flux Φ = B·S·cos α is measured in webers.",
      "Induced EMF |ε| = ΔΦ/Δt appears only while the flux changes."]),
    (["Поток меняется при изменении поля, площади контура или его ориентации.",
      "Правило Ленца: индукционный ток противодействует причине, его вызвавшей; именно "
      "поэтому вращать генератор приходится с усилием.",
      "Если поток постоянен, ЭДС нет: неподвижный магнит вблизи замкнутого контура "
      "ничего не создаёт."],
     ["The flux changes with the field, the loop area or its orientation.",
      "Lenz's rule: the induced current opposes the change that produced it.",
      "A steady flux produces no EMF."]),
    [(("Поток через контур вырос с 0,2 Вб до 1 Вб за 0,4 с. Найдите ЭДС индукции.",
       "The flux through a loop grows from 0.2 Wb to 1 Wb in 0.4 s. Find the induced EMF."),
      (["ΔΦ = 1 − 0,2 = 0,8 Вб.", "|ε| = 0,8/0,4 = 2 В.", "Ответ: 2 В."],
       ["ΔΦ = 0.8 Wb.", "|ε| = 0.8/0.4 = 2 V.", "Answer: 2 V."]))],
    (["Беспроводная зарядка телефона — это индукция: переменное поле катушки создаёт "
      "ЭДС в катушке телефона.",
      "Модель «идеальный контур» без сопротивления: в реальной катушке часть энергии "
      "уходит в нагрев проводов."],
     ["Wireless phone charging is induction: a changing field in the pad drives an EMF in the "
      "phone coil.",
      "Real coils heat up, so part of the energy is lost."]),
    figures=("induction-flux",),
)

# --------------------------------------------------------------------------- #
#  11. Колебания, волны, звук
# --------------------------------------------------------------------------- #

_lesson(
    "oscillations", "Механические колебания", "Mechanical oscillations",
    (["Колебания — повторяющееся движение около положения равновесия; период T — время "
      "одного полного колебания, частота ν = 1/T измеряется в герцах.",
      "Период математического маятника T = 2π√(l/g), пружинного T = 2π√(m/k)."],
     ["Oscillations repeat about equilibrium; period T and frequency ν = 1/T in hertz.",
      "Pendulums: T = 2π√(l/g) and T = 2π√(m/k)."]),
    (["Период нитяного маятника не зависит от массы груза; пружинного — от массы, "
      "но при малых колебаниях не зависит от амплитуды.",
      "Круговая частота ω = 2πν связана с периодом как ω = 2π/T.",
      "Резонанс — резкий рост амплитуды, когда частота внешней силы совпадает с "
      "собственной частотой системы."],
     ["A pendulum's period is independent of the bob mass; a spring's depends on the mass.",
      "Angular frequency ω = 2πν = 2π/T.",
      "Resonance happens when the drive frequency matches the natural one."]),
    [(("Маятник на нити 1 м. Найдите период. g = 9,8 м/с².",
       "A pendulum on a 1 m string. Find the period. g = 9.8 m/s²."),
      (["T = 2π√(l/g).", "T = 2π√(1/9,8) ≈ 2 · 3,14 · 0,32 ≈ 2 с.", "Ответ: ≈ 2 с."],
       ["T = 2π√(l/g).", "T = 2π√(1/9.8) ≈ 2 s.", "Answer: ≈ 2 s."])),
     (("Тело на пружине k = 100 Н/м массой 4 кг. Найдите период.",
       "A 4 kg body on a 100 N/m spring. Find the period."),
      (["T = 2π√(m/k).", "T = 2π√(4/100) = 2π·0,2 ≈ 1,26 с.", "Ответ: ≈ 1,26 с."],
       ["T = 2π√(m/k).", "T = 2π√(0.04) ≈ 1.26 s.", "Answer: ≈ 1.26 s."]))],
    (["Качели: чтобы раскачать их сильнее, толкать нужно в такт собственному периоду — "
      "иначе толчки гасят друг друга.",
      "Модель малых колебаний: при больших углах период нитяного маятника начинает "
      "зависеть от амплитуды, и формула 2π√(l/g) даёт уже неточный результат."],
     ["A swing is pumped at its natural period; mistimed pushes cancel each other.",
      "For large angles the pendulum formula breaks down and the amplitude starts to matter."]),
    figures=("pendulum",),
)

_lesson(
    "waves-sound", "Волны и звук", "Waves and sound",
    (["Волна — распространение колебаний в среде; длина волны λ = v·T = v/ν — расстояние, "
      "которое волна проходит за период.",
      "Скорость звука в воздухе ≈ 340 м/с; при эхе и работе эхолота сигнал идёт туда и "
      "обратно, поэтому 2s = v·t."],
     ["A wave transports oscillations through a medium; λ = v·T = v/ν.",
      "Sound travels about 340 m/s in air; echo and sonar use the doubled path 2s = v·t."]),
    (["Частота задаётся источником и при переходе в другую среду не меняется; скорость "
      "и длина волны меняются вместе.",
      "Громкость связана с амплитудой, высота тона — с частотой: это разные характеристики.",
      "Звук не распространяется в вакууме: нужна среда."],
     ["The source sets the frequency; entering another medium changes speed and wavelength.",
      "Loudness relates to amplitude and pitch to frequency.",
      "Sound cannot travel through a vacuum."]),
    [(("За 5 с лодка услышала эхо от скалы. Найдите расстояние до скалы. v = 340 м/с.",
       "A boat hears an echo from a cliff after 5 s. Find the distance. v = 340 m/s."),
      (["Сигнал прошёл туда и обратно: 2s = v·t.", "s = 340 · 5/2 = 850 м.",
        "Ответ: 850 м."],
       ["The pulse went there and back: 2s = v·t.", "s = 340 · 5/2 = 850 m.", "Answer: 850 m."])),
     (("Найдите длину волны звука частотой 680 Гц. v = 340 м/с.",
       "Find the wavelength of a 680 Hz sound. v = 340 m/s."),
      (["λ = v/ν.", "λ = 340/680 = 0,5 м.", "Ответ: 0,5 м."],
       ["λ = v/ν.", "λ = 340/680 = 0.5 m.", "Answer: 0.5 m."]))],
    (["Гром гремит позже вспышки молнии: свет приходит почти мгновенно, а звуку нужно "
      "время — по задержке оценивают расстояние, считая 3 с ≈ 1 км.",
      "Модель «звук идёт по прямой с постоянной скоростью» ломается при ветре и "
      "температурных слоях: скорость звука зависит от среды."],
     ["Thunder follows lightning because sound needs time: 3 seconds ≈ 1 km.",
      "Wind and temperature layers change the speed of sound."]),
    figures=("wave-profile", "echo-path"),
)

# --------------------------------------------------------------------------- #
#  12. Оптика
# --------------------------------------------------------------------------- #

_lesson(
    "reflection-refraction", "Отражение и преломление света", "Reflection and refraction",
    (["Угол падения равен углу отражения; оба угла отсчитываются от перпендикуляра "
      "к поверхности в точке падения.",
      "Показатель преломления n = sin α / sin γ = c/v: при переходе в оптически более "
      "плотную среду луч идёт ближе к перпендикуляру."],
     ["The angle of incidence equals the angle of reflection, both measured from the normal.",
      "Refractive index n = sin α / sin γ = c/v; entering a denser medium the ray bends towards "
      "the normal."]),
    (["Отражение бывает зеркальным и рассеянным: на шероховатой поверхности лучи уходят "
      "в разные стороны, поэтому мы видим предметы, а не отражения.",
      "В воде скорость света меньше, чем в воздухе, а частота не меняется.",
      "Полное внутреннее отражение возникает при переходе из плотной среды в менее "
      "плотную под большим углом."],
     ["Reflection is specular on smooth surfaces and diffuse on rough ones.",
      "Light slows down in water while its frequency stays the same.",
      "Total internal reflection occurs from dense to less dense media."]),
    [(("Луч падает на зеркало под 25° к перпендикуляру. Каков угол отражения?",
       "A ray reaches a mirror at 25° from the normal. What is the reflection angle?"),
      (["Угол падения равен углу отражения.", "Ответ: 25° от того же перпендикуляра.",
        "Между падающим и отражённым лучом тогда 50°."],
       ["The angles are equal.", "Answer: 25° from the same normal.",
       "The angle between the incident and reflected rays is then 50°."]))],
    (["Ложка в стакане воды «переламывается» на границе — это преломление; глаз "
      "продолжает лучи по прямой и видит смещённое изображение.",
      "Модель лучевой оптики не объясняет цвета радуги: там нужна уже волновая модель "
      "и зависимость n от длины волны."],
     ["A spoon in a glass looks broken because the eye extends refracted rays straight ahead.",
      "Ray optics cannot explain rainbow colours; the wave model is needed."]),
    figures=("reflection-mirror", "refraction-ray"),
)

_lesson(
    "lens", "Линзы и изображения", "Lenses and images",
    (["Формула тонкой линзы: 1/F = 1/d + 1/f, где F — фокусное расстояние, d — расстояние "
      "до предмета, f — до изображения.",
      "Оптическая сила D = 1/F измеряется в диоптриях; F берётся в метрах."],
     ["Thin lens equation: 1/F = 1/d + 1/f.",
      "Optical power D = 1/F in dioptres with F in metres."]),
    (["Собирающая линза при d > F даёт действительное перевёрнутое изображение; при d < F — "
      "мнимое прямое, для которого f < 0.",
      "Увеличение Γ = |f|/d: чем ближе предмет к фокусу, тем крупнее изображение.",
      "Действительное изображение можно поймать на экран, мнимое — нет."],
     ["A converging lens gives a real inverted image for d > F and a virtual one for d < F.",
      "Magnification Γ = |f|/d.",
      "A real image can be projected on a screen; a virtual one cannot."]),
    [(("Предмет на 0,3 м от линзы с F = 0,2 м. Найдите изображение.",
       "An object is 0.3 m from a lens with F = 0.2 m. Find the image."),
      (["1/f = 1/F − 1/d = 1/0,2 − 1/0,3 = (3 − 2)/0,6.", "f = 0,6 м.",
        "Ответ: действительное изображение на 0,6 м, увеличение 2."],
       ["1/f = 1/0.2 − 1/0.3 = 1/0.6.", "f = 0.6 m.",
        "Answer: a real image 0.6 m away, doubled."]))],
    (["Очки для близорукости — рассеивающие (мнимый фокус), для дальнозоркости — "
      "собирающие: диоптрии в рецепте указывают D = 1/F.",
      "Модель тонкой линзы не учитывает толщину стекла и аберрации реального объектива."],
     ["Glasses for short sight are diverging and for far sight converging; the prescription "
      "lists D = 1/F.",
      "The thin-lens model ignores thickness and aberrations."]),
    figures=("lens-image",),
)

# --------------------------------------------------------------------------- #
#  13. Квантовые явления, атом и ядро
# --------------------------------------------------------------------------- #

_lesson(
    "photoeffect", "Фотоэффект", "Photoelectric effect",
    (["Энергия фотона E = hν = h·c/λ, где h ≈ 6,63·10⁻³⁴ Дж·с.",
      "Уравнение Эйнштейна для фотоэффекта: hν = Aвых + Eк — энергия фотона расходуется "
      "на работу выхода и кинетическую энергию электрона."],
     ["Photon energy E = hν = hc/λ with h ≈ 6.63·10⁻³⁴ J·s.",
      "Einstein's equation: hν = A_escape + E_kinetic."]),
    (["Красная граница определена работой выхода: фотоэффект начинается, когда hν минимально "
      "превышает Aвых.",
      "Яркость света увеличивает число вылетающих электронов, но не энергию каждого — "
      "её задаёт частота.",
      "Работа выхода измеряется в электрон-вольтах: 1 эВ = 1,6·10⁻¹⁹ Дж."],
     ["The red threshold follows from the work function.",
      "Brightness changes the number of electrons, not the energy of one.",
      "Work functions are quoted in electronvolts: 1 eV = 1.6·10⁻¹⁹ J."]),
    [(("Найдите энергию фотона света с частотой 6·10¹⁴ Гц.",
       "Find the energy of a photon at 6·10¹⁴ Hz."),
      (["E = hν.", "E = 6,63·10⁻³⁴ · 6·10¹⁴ ≈ 4·10⁻¹⁹ Дж.", "Ответ: ≈ 4·10⁻¹⁹ Дж ≈ 2,5 эВ."],
       ["E = hν.", "E = 6.63·10⁻³⁴ · 6·10¹⁴ ≈ 4·10⁻¹⁹ J.", "Answer: ≈ 4·10⁻¹⁹ J ≈ 2.5 eV."]))],
    (["Солнечная батарея на калькуляторе работает фотоэффектом: свет выбивает электроны "
      "в полупроводнике, и появляется ток.",
      "Модель фотона как «порции энергии» нужна там, где волновая модель бессильна; "
      "для интерференции, наоборот, нужна волна."],
     ["A solar-powered calculator works through the photoelectric effect.",
      "The photon model is required where the wave model fails, and vice versa."]),
    figures=("photoeffect-scheme",),
)

_lesson(
    "atom-nucleus", "Атом и атомное ядро", "Atom and nucleus",
    (["Атом состоит из ядра (протоны и нейтроны) и электронов; заряд ядра равен числу "
      "протонов Z и совпадает с номером элемента в таблице Менделеева.",
      "Массовое число A — число нуклонов: A = Z + N, где N — число нейтронов."],
     ["An atom has a nucleus of protons and neutrons surrounded by electrons; Z equals the "
      "element number.",
      "Mass number A = Z + N counts nucleons."]),
    (["Изотопы различаются числом нейтронов при одинаковом Z.",
      "Размер ядра порядка 10⁻¹⁵ м, атома — 10⁻¹⁰ м: ядро в атоме занимает ничтожную часть "
      "объёма, но содержит почти всю массу.",
      "Энергия связи нуклонов в ядре огромна по сравнению с химическими энергиями: "
      "именно поэтому ядерная энергетика так эффективна."],
     ["Isotopes differ in neutron number at the same Z.",
      "A nucleus is about 10⁻¹⁵ m across inside an atom of 10⁻¹⁰ m.",
      "Nuclear binding energies far exceed chemical ones."]),
    [(("Для ядра ²³⁵U укажите число протонов и нейтронов.",
       "For the nucleus ²³⁵U give the numbers of protons and neutrons."),
      (["Z = 92 (номер урана).", "N = 235 − 92 = 143.", "Ответ: 92 протона, 143 нейтрона."],
       ["Z = 92 for uranium.", "N = 235 − 92 = 143.", "Answer: 92 protons and 143 neutrons."]))],
    (["Рентгеновский снимок возможен потому, что электронные оболочки тяжёлых атомов "
      "поглощают излучение по-разному — это уже атомная, а не ядерная физика.",
      "Модель «ядро как шарик» достаточна для школьных задач, но не объясняет деление "
      "ядер и энергию связи без дополнительных моделей."],
     ["X-rays work because heavy atoms absorb differently — atomic, not nuclear, physics.",
      "The ball-nucleus model suits school problems but not fission."]),
)

_lesson(
    "radioactivity", "Радиоактивность", "Radioactivity",
    (["α-распад уменьшает массовое число на 4 и заряд на 2; β-распад повышает заряд на 1 "
      "при неизменном массовом числе.",
      "Закон радиоактивного распада: N = N₀·2^(−t/T), где T — период полураспада."],
     ["Alpha decay lowers A by 4 and Z by 2; beta decay raises Z by 1.",
      "Decay law: N = N₀·2^(−t/T) with T the half-life."]),
    (["Число ядер убывает относительно, а не линейно: за каждый период распадается "
      "половина имеющихся.",
      "Период полураспада не зависит от температуры, давления и химического состояния.",
      "Активность пропорциональна числу оставшихся ядер, поэтому убывает по тому же закону."],
     ["The count halves each half-life rather than falling linearly.",
      "The half-life is independent of temperature, pressure and chemistry.",
      "Activity is proportional to the remaining nuclei."]),
    [(("Период полураспада 5 суток. Какая доля ядер останется через 15 суток?",
       "The half-life is 5 days. What fraction remains after 15 days?"),
      (["15 суток — это 3 периода: 15/5 = 3.", "N/N₀ = 2⁻³ = 1/8.",
        "Ответ: останется 1/8 ядер (распалось 7/8)."],
       ["15 days = three half-lives.", "N/N₀ = 2⁻³ = 1/8.", "Answer: one eighth remains."])),
     (("Ядро ²³⁸U испытало α-распад. Какое ядро получилось?",
       "A ²³⁸U nucleus underwent alpha decay. Which nucleus results?"),
      (["A: 238 − 4 = 234, Z: 92 − 2 = 90.", "Элемент с Z = 90 — торий.",
        "Ответ: ²³⁴Th."],
       ["A: 238 − 4 = 234, Z: 92 − 2 = 90.",
       "The element with Z = 90 is thorium.", "Answer: ²³⁴Th."]))],
    (["Дозиметр на экране показывает активность: фон можно измерять, но нельзя «ускорить» "
      "распад нагревом — период полураспада задан ядром.",
      "Модель статистическая: для малого числа ядер выводы о распаде вероятностные, "
      "точный закон N = N₀·2^(−t/T) работает для больших количеств."],
     ["A dosimeter shows activity; heating cannot speed up decay.",
      "The law is statistical: it holds for large numbers of nuclei."]),
    figures=("decay-graph",),
)


def payload() -> dict:
    """Уроки для topics.json: ключ → двуязычная запись."""
    if not LESSONS:
        raise PhysicsError("каталог уроков пуст")
    return LESSONS
