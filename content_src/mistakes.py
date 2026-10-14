"""mistakes.py — каталог типичных ошибок по физике.

Каждый тег задания связан с объяснением «что именно перепутано и как это
проверить». При неверном ответе приложение открывает конспект темы и показывает
именно те ошибки, к которым относятся теги задания, — а не общее «попробуйте ещё
раз». Теги повторяются в заданиях банка и генератора, поэтому каталог заполняется
один раз здесь, а задания только ссылаются на готовые теги.
"""

from __future__ import annotations

from kit import MISTAKE_TAGS, PhysicsError, register_mistake

#: тег → (объяснение по-русски, объяснение по-английски)
CATALOGUE = {
    "приставки СИ": (
        "Приставка меняет множитель единицы: мм = 10⁻³ м, км = 10³ м, мкм = 10⁻⁶ м. "
        "Прежде чем считать, переведите все данные в одну строку приставок.",
        "A prefix changes the unit factor: mm = 10⁻³ m, km = 10³ m, µm = 10⁻⁶ m. "
        "Convert every quantity to the same prefix before calculating."),
    "перевод единиц": (
        "Единицы пересчитывают умножением на множитель: 36 км/ч = 10 м/с, 1 кВт = 1000 Вт, "
        "1 л = 0,001 м³. Подставлять число без перевода единицы нельзя.",
        "Units convert by a factor: 36 km/h = 10 m/s, 1 kW = 1000 W, 1 l = 0.001 m³. "
        "Never substitute a bare number without converting its unit."),
    "размерность": (
        "Проверьте размерность результата: путь — в метрах, сила — в ньютонах, "
        "энергия — в джоулях. Если размерность не та, формула выбрана неверно.",
        "Check the dimension of the result: distance in metres, force in newtons, energy in "
        "joules. A wrong dimension means a wrong formula, not a wrong multiplication."),
    "цена деления": (
        "Цена деления — разность двух соседних подписанных значений, делённая на число "
        "промежутков между ними. Одна подпись шкалы — это ещё не цена деления.",
        "The scale division is the difference between two neighbouring labelled values divided "
        "by the number of gaps between them."),
    "погрешность измерения": (
        "Погрешность прибора — половина цены деления; её нельзя «убрать» более точным "
        "расчётом. Результат записывают с той же точностью, что и измерение.",
        "Instrument uncertainty is half the scale division; a more precise calculation cannot "
        "remove it. Report the result with the accuracy of the measurement."),
    "путь и перемещение": (
        "Путь — длина траектории, перемещение — вектор из начальной точки в конечную. "
        "При возврате в начальную точку путь не ноль, а перемещение равно нулю.",
        "Distance is the length of the trajectory; displacement is the vector from start to "
        "finish. Returning to the start gives zero displacement but non-zero distance."),
    "средняя скорость": (
        "Средняя скорость — весь путь, делённый на всё время. Складывать скорости на "
        "отдельных участках (или делить пополам) можно только при равных участках времени.",
        "Average speed is total distance over total time. Averaging section speeds is allowed "
        "only when the sections take equal time."),
    "относительность движения": (
        "Скорости складывают векторно, в одной системе отсчёта. Сначала выбирают тело "
        "отсчёта и указывают, относительно чего измерены скорости.",
        "Velocities add as vectors in one chosen reference frame. State the frame and relative "
        "to what each velocity is measured."),
    "равноускоренное движение": (
        "При равноускоренном движении v = v₀ + at, а путь s = v₀t + at²/2. Множитель ½ "
        "относится только к слагаемому ускорения.",
        "For uniformly accelerated motion v = v₀ + at and s = v₀t + at²/2. The factor ½ belongs "
        "only to the acceleration term."),
    "свободное падение": (
        "Свободное падение — частный случай равноускоренного движения с a = g ≈ 9,8 м/с². "
        "Если сопротивление воздуха не учитывается, масса на время падения не влияет.",
        "Free fall is uniformly accelerated motion with a = g ≈ 9.8 m/s². Ignoring air drag, "
        "mass does not change the falling time."),
    "график скорости": (
        "На графике v(t) наклон прямой равен ускорению, а площадь под графиком — путь. "
        "Ось и единицы определяют смысл: по графику нельзя читать путь без площади.",
        "On a v(t) graph the slope is acceleration and the area under it is the distance. "
        "Always read the axes and units before drawing conclusions."),
    "второй закон Ньютона": (
        "Ускорение пропорционально равнодействующей всех сил и обратно пропорционально массе: "
        "a = F/m. Складывать нужно все силы, включая силу трения и тяжести.",
        "Acceleration is proportional to the net force and inversely proportional to mass: "
        "a = F/m. Sum all forces, friction and weight included."),
    "сила тяжести и вес": (
        "Вес — сила, с которой тело действует на опору; масса измеряется в килограммах. "
        "В невесомости масса сохраняется, а вес исчезает.",
        "Weight is the force a body exerts on its support; mass is measured in kilograms. "
        "In weightlessness mass remains while weight disappears."),
    "третий закон Ньютона": (
        "Силы действия и противодействия приложены к разным телам, поэтому они не "
        "уравновешивают друг друга и не могут сокращаться в одной сумме сил.",
        "Action and reaction act on different bodies, so they never cancel inside one force sum."),
    "сила трения": (
        "Сила трения скольжения равна μN, где N — сила нормального давления, а не вес "
        "автоматически: на наклонной плоскости N меньше mg.",
        "Sliding friction equals μN where N is the normal force — not automatically the weight: "
        "on an incline N is smaller than mg."),
    "сила упругости": (
        "Закон Гука F = kx работает только в пределах упругости, а x — удлинение, "
        "а не полная длина пружины.",
        "Hooke's law F = kx holds within the elastic limit, and x is the extension, not the "
        "full length of the spring."),
    "импульс и закон сохранения": (
        "Импульс p = mv меняется только под действием внешних сил. Закон сохранения "
        "применяют к системе тел, для которой внешние силы пренебрежимо малы.",
        "Momentum p = mv changes only under external forces. Apply conservation to a system "
        "whose external forces are negligible."),
    "работа и мощность": (
        "Работа A = Fs·cos α, мощность P = A/t. Если сила перпендикулярна перемещению, "
        "работа равна нулю, как бы велика ни была сила.",
        "Work A = Fs·cos α and power P = A/t. A force perpendicular to the displacement does "
        "no work, however large it is."),
    "закон сохранения энергии": (
        "Полная механическая энергия сохраняется, только если нет трения и других потерь. "
        "С потерями уменьшается механическая энергия, а полная энергия системы сохраняется.",
        "Mechanical energy is conserved only without friction and other losses. With losses "
        "mechanical energy drops while the total energy of the system stays."),
    "КПД": (
        "КПД — отношение полезной работы ко всей затраченной: η = Aполез/Aзатр. Он всегда "
        "меньше 100 %, потому что часть энергии уходит в тепло.",
        "Efficiency is useful work over total work: η = A_useful/A_total, always below 100 % "
        "because part of the energy becomes heat."),
    "момент силы": (
        "Момент силы M = Fd, где d — плечо: расстояние по перпендикуляру от оси до линии "
        "действия силы, а не длина ручки или рычага.",
        "Torque M = Fd where d is the perpendicular distance from the axis to the line of "
        "action, not the length of the lever itself."),
    "условие равновесия": (
        "Тело в равновесии, когда равны нулю и сумма сил, и сумма моментов относительно "
        "любой оси. Одного равенства сил недостаточно.",
        "Equilibrium requires both zero net force and zero net torque about any axis; balancing "
        "forces alone is not enough."),
    "давление": (
        "Давление p = F/S: сила делится на площадь опоры. Один и тот же вес на узкой опоре "
        "даёт большее давление.",
        "Pressure p = F/S: the force is divided by the contact area. The same weight on a "
        "narrow support gives a higher pressure."),
    "гидростатическое давление": (
        "Давление жидкости p = ρgh зависит от глубины, а не от формы сосуда и не от объёма "
        "налитой жидкости.",
        "Liquid pressure p = ρgh depends on depth, not on the shape of the vessel or the "
        "volume of liquid."),
    "сила Архимеда": (
        "Архимедова сила равна весу вытесненной жидкости: F = ρжVпогрg. Использовать объём "
        "всего тела можно только при полном погружении.",
        "The buoyant force equals the weight of the displaced liquid: F = ρ_liquid·V_submerged·g."),
    "количество вещества": (
        "Количество вещества ν = m/M измеряется в молях, где M — молярная масса в г/моль. "
        "Молярная масса численно равна относительной молекулярной.",
        "Amount of substance ν = m/M is measured in moles, where M is the molar mass in g/mol."),
    "уравнение состояния газа": (
        "В уравнении pV = νRT температура обязательно в кельвинах: T = t + 273. "
        "Один и тот же газ при изменении состояния описывают отношением pV/T = const.",
        "In pV = νRT the temperature must be in kelvin: T = t + 273. For one gas sample "
        "pV/T = const."),
    "изопроцессы": (
        "Изотермический процесс — T = const (закон Бойля–Мариотта), изобарный — p = const "
        "(Гей-Люссак), изохорный — V = const (Шарль). Выбирайте закон по тому, что постоянно.",
        "Isothermal: T = const (Boyle–Mariotte), isobaric: p = const (Gay-Lussac), isochoric: "
        "V = const (Charles). Choose the law by the constant quantity."),
    "теплота и теплоёмкость": (
        "Количество теплоты Q = cmΔt зависит от разности температур, а не от абсолютной "
        "температуры. Δt в °C и ΔT в К численно равны.",
        "Heat Q = cmΔt depends on the temperature difference, not on absolute temperature. "
        "A difference in °C equals the same difference in K."),
    "удельная теплота": (
        "Удельная теплота сгорания q относится к массе топлива, удельная теплота "
        "парообразования L — к массе пара (Q = Lm).",
        "Specific heat of combustion q applies to fuel mass, latent heat L to the mass that "
        "changes phase (Q = Lm)."),
    "фазовые переходы": (
        "При плавлении и кипении температура не меняется, а теплота расходуется на "
        "разрушение связей. На графике это горизонтальные участки.",
        "During melting and boiling the temperature stays constant: heat changes the bonding, "
        "not the temperature. On a graph these are horizontal sections."),
    "первый закон термодинамики": (
        "ΔU = Q + Авнешн: теплота и работа внешних сил увеличивают внутреннюю энергию. "
        "Работа самого газа при расширении считается с минусом в этой записи.",
        "ΔU = Q + A_external. The work done by the gas on expansion enters with the opposite "
        "sign in this form."),
    "закон Кулона": (
        "Сила Кулона F = kq₁q₂/r² зависит от расстояния в квадрате: увеличение r вдвое "
        "уменьшает силу вчетверо.",
        "Coulomb force F = kq₁q₂/r² falls as the square of the distance: doubling r makes the "
        "force four times smaller."),
    "напряжённость и потенциал": (
        "Напряжённость — силовая характеристика поля (В/м), потенциал — энергетическая (В). "
        "Работа поля A = qU, а напряжённость связана с напряжением E = U/d.",
        "Field strength is the force characteristic (V/m), potential the energy one (V). "
        "Field work A = qU and E = U/d for a uniform field."),
    "последовательное соединение": (
        "При последовательном соединении I одинаков во всех элементах, U складывается, "
        "R = R₁ + R₂. Амперметр включают последовательно, вольтметр — параллельно.",
        "In series the current is the same, voltages add and R = R₁ + R₂. An ammeter goes in "
        "series, a voltmeter in parallel."),
    "параллельное соединение": (
        "При параллельном соединении U одинаково, токи складываются, а 1/R = 1/R₁ + 1/R₂. "
        "Общее сопротивление меньше самого маленького.",
        "In parallel the voltage is the same, currents add and 1/R = 1/R₁ + 1/R₂. The total "
        "resistance is smaller than the smallest one."),
    "закон Ома": (
        "Закон Ома I = U/R связывает ток в проводнике с напряжением на нём и его "
        "сопротивлением. Ток не «расходуется» в лампе — он одинаков до и после неё.",
        "Ohm's law I = U/R relates the current to the voltage across that conductor. Current "
        "is not consumed by a lamp: it is the same before and after it."),
    "работа тока": (
        "Работа тока A = UIt, мощность P = UI = I²R = U²/R. В быту энергию измеряют в "
        "кВт·ч: 1 кВт·ч = 3,6·10⁶ Дж.",
        "Electric work A = UIt and power P = UI = I²R = U²/R. Domestic energy uses kWh: "
        "1 kWh = 3.6·10⁶ J."),
    "сила Ампера": (
        "Сила Ампера F = BIl·sin α действует на проводник с током в магнитном поле и "
        "максимальна, когда проводник перпендикулярен линиям поля.",
        "Ampère force F = BIl·sin α acts on a current-carrying wire and is maximal when the "
        "wire is perpendicular to the field lines."),
    "сила Лоренца": (
        "Сила Лоренца F = qvB·sin α перпендикулярна скорости, поэтому работы не совершает "
        "и меняет только направление движения, но не модуль скорости.",
        "The Lorentz force is perpendicular to the velocity, does no work and changes only the "
        "direction of motion, not the speed."),
    "электромагнитная индукция": (
        "ЭДС индукции |ε| = ΔΦ/Δt. Магнитный поток меняется при изменении поля, площади "
        "контура или его ориентации; без изменения потока ЭДС нет.",
        "Induced EMF |ε| = ΔΦ/Δt appears while the flux changes — through field, area or "
        "orientation. No change of flux means no EMF."),
    "период и частота": (
        "Период T и частота ν связаны как ν = 1/T. Частота измеряется в герцах, а круговая "
        "частота ω = 2πν — в радианах в секунду.",
        "Period T and frequency ν satisfy ν = 1/T. Frequency is in hertz; angular frequency "
        "ω = 2πν in radians per second."),
    "маятник": (
        "Период математического маятника T = 2π√(l/g) не зависит от массы; период "
        "пружинного T = 2π√(m/k) не зависит от амплитуды при малых колебаниях.",
        "A simple pendulum has T = 2π√(l/g) independent of mass; a spring pendulum has "
        "T = 2π√(m/k) independent of amplitude for small oscillations."),
    "длина волны": (
        "Длина волны λ = vT = v/ν: это расстояние, которое волна проходит за период. "
        "Скорость волны определяется средой, а частота — источником.",
        "Wavelength λ = vT = v/ν; wave speed is set by the medium, frequency by the source."),
    "звук": (
        "Скорость звука в воздухе около 340 м/с. Эхо и эхолот используют удвоенный путь: "
        "2s = vt, поэтому s = vt/2.",
        "Sound travels about 340 m/s in air. Echo and sonar use the doubled path: 2s = vt, "
        "hence s = vt/2."),
    "закон отражения": (
        "Угол падения равен углу отражения, оба отсчитываются от перпендикуляра к "
        "поверхности, а не от самой поверхности.",
        "The angle of incidence equals the angle of reflection, both measured from the normal, "
        "not from the surface."),
    "преломление света": (
        "При переходе в оптически более плотную среду луч отклоняется к перпендикуляру; "
        "показатель преломления n = sin α / sin γ (скорость света там меньше).",
        "Entering a denser medium the ray bends towards the normal; n = sin α / sin γ and the "
        "speed of light is lower there."),
    "формула тонкой линзы": (
        "1/F = 1/d + 1/f. Собирающая линза даёт действительное изображение при d > F; "
        "мнимое изображение получают с f < 0.",
        "1/F = 1/d + 1/f. A converging lens gives a real image for d > F; a virtual image "
        "needs f < 0."),
    "оптическая сила": (
        "Оптическая сила D = 1/F измеряется в диоптриях, F — в метрах: линза 5 дптр имеет "
        "фокусное расстояние 0,2 м.",
        "Optical power D = 1/F is measured in dioptres with F in metres: 5 D means F = 0.2 m."),
    "фотоэффект": (
        "Энергия фотона E = hν, уравнение Эйнштейна hν = Aвых + Eк. Красная граница "
        "определяется работой выхода, а интенсивность света на энергию фотона не влияет.",
        "Photon energy E = hν and hν = A_escape + E_kinetic. The intensity changes the number "
        "of electrons, not the energy of one photon."),
    "строение атома": (
        "Атом состоит из ядра (протоны и нейтроны) и электронов. Массовое число равно числу "
        "нуклонов, заряд ядра — числу протонов в таблице Менделеева.",
        "An atom has a nucleus (protons and neutrons) and electrons. The mass number counts "
        "nucleons, the charge is the proton number."),
    "радиоактивность": (
        "α-распад уменьшает массовое число на 4 и заряд на 2, β-распад повышает заряд на 1. "
        "Число ядер со временем убывает по закону N = N₀·2^(−t/T).",
        "Alpha decay lowers the mass number by 4 and the charge by 2; beta decay raises the "
        "charge by 1. Activity decays as N = N₀·2^(−t/T)."),
}


def payload() -> dict:
    """Каталог типичных ошибок для mistakes.json (регистрирует и возвращает)."""
    for tag, (ru, en) in CATALOGUE.items():
        if tag not in MISTAKE_TAGS:
            register_mistake(tag, ru, en)
    return {"errors": {tag: {"ru": ru, "en": en} for tag, (ru, en) in MISTAKE_TAGS.items()},
            "default": {
                "ru": "Проверьте решение по шагам: дано → единицы СИ → формула → "
                      "подстановка → размерность → смысл ответа.",
                "en": "Recheck the solution step by step: data → SI units → formula → "
                      "substitution → dimension → physical meaning."},
            "checklist": [
                {"ru": "Дано: все ли данные использованы и переведены ли они в единицы СИ?",
                 "en": "Data: is every quantity used and converted to SI units?"},
                {"ru": "Формула: подходит ли она этому процессу и не забыт ли множитель ½?",
                 "en": "Formula: does it describe this process, and is the factor ½ there?"},
                {"ru": "Размерность: совпадает ли единица ответа с требуемой в вопросе?",
                 "en": "Dimension: does the unit of the answer match the one asked for?"},
                {"ru": "Подстановка: подставлены ли значения в тех же единицах, что в условии?",
                 "en": "Substitution: are the values in the same units as in the statement?"},
                {"ru": "Смысл: правдоподобен ли ответ (знак, порядок, границы модели)?",
                 "en": "Sense: is the answer plausible (sign, magnitude, limits of the model)?"},
            ]}


#: историческое имя: сборка вызывает payload(), тесты — register()
register = payload
