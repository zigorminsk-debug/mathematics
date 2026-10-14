"""study.py — конспект «что изучить по теме» для каждой области курса.

Открывается сразу после неверного ответа: три-четыре пункта по существу, каждый
со ссылкой на урок теории и на раздел сборника формул. Именно поэтому здесь нет
общих слов: каждый пункт — это то, что ученик реально перепутал в задании.
"""

from __future__ import annotations

from kit import PhysicsError, TOPIC_ORDER


def _entry(ru, en, lessons, groups):
    if len(ru) != len(en) or len(ru) != len(lessons):
        raise PhysicsError("конспект темы: пункты и ссылки на теорию должны совпадать")
    return {"ru": list(ru), "en": list(en), "lessons": list(lessons), "formulas": list(groups)}


STUDY: dict[str, dict] = {
    "measurements": _entry(
        ["Все величины в СИ: м, кг, с, А, К, моль. Перед подстановкой в формулу переведите данные в одну систему единиц.",
         "Приставки меняют множитель: 1 км = 10³ м, 1 см = 10⁻² м, 1 мм = 10⁻³ м, 1 мкм = 10⁻⁶ м, 1 кВт = 10³ Вт.",
         "Размерность проверяет формулу: путь — м, скорость — м/с, ускорение — м/с², сила — Н, энергия — Дж.",
         "У измеренной величины есть погрешность: она не меньше половины цены деления прибора."],
        ["All quantities in SI: m, kg, s, A, K, mol. Convert the data to one system of units before substitution.",
         "Prefixes change the factor: 1 km = 10³ m, 1 cm = 10⁻² m, 1 mm = 10⁻³ m, 1 µm = 10⁻⁶ m, 1 kW = 10³ W.",
         "The dimension checks the formula: m, m/s, m/s², N, J.",
         "Every measured value carries an uncertainty of at least half a scale division."],
        ["units-si", "dimensions-check", "dimensions-check", "measure-accuracy"], ["units"]),
    "kinematics": _entry(
        ["Путь — длина траектории, перемещение — вектор из начала в конец; при возврате они различаются.",
         "Средняя скорость — весь путь, делённый на всё время, а не среднее арифметическое скоростей.",
         "При равноускоренном движении v = v₀ + at и s = v₀t + at²/2: множитель ½ только у слагаемого ускорения.",
         "На графике v(t) наклон — ускорение, площадь под графиком — путь; свободное падение идёт с a = g."],
        ["Distance and displacement differ: the first is the trajectory length, the second is a vector.",
         "Average speed is total distance over total time, not the mean of the speeds.",
         "Uniformly accelerated motion: v = v₀ + at and s = v₀t + at²/2 — the factor ½ belongs to the acceleration term.",
         "On a v(t) graph the slope is acceleration and the area is distance; free fall has a = g."],
        ["motion-terms", "motion-terms", "accelerated-motion", "kinematics-graphs"], ["kinematics"]),
    "dynamics": _entry(
        ["Второй закон Ньютона работает с равнодействующей всех сил: a = F/m.",
         "Сила тяжести F = mg приложена к телу, вес — к опоре; масса измеряется в килограммах.",
         "Трение скольжения Fтр = μN, где N — сила нормального давления, а не всегда mg.",
         "Силы удобно рисовать: выберите тело, покажите все силы и только потом пишите уравнение."],
        ["The second law uses the net force: a = F/m.",
         "Gravity acts on the body, weight on the support; mass is measured in kilograms.",
         "Sliding friction F = μN where N is the normal force, not always mg.",
         "Draw a free-body diagram: choose the body, show every force, then write the equation."],
        ["newton-laws", "forces-weight", "friction-elasticity", "force-diagram"], ["dynamics"]),
    "workenergy": _entry(
        ["Работа A = Fs·cos α: сила, перпендикулярная перемещению, работы не совершает.",
         "Мощность P = A/t, КПД — отношение полезной работы к затраченной и всегда меньше 100 %.",
         "Механическая энергия сохраняется только без трения и потерь; с потерями часть её уходит в тепло.",
         "Импульс p = mv сохраняется в замкнутой системе, удар и отдача — типичные примеры."],
        ["Work A = Fs·cos α: a force perpendicular to the displacement does no work.",
         "Power P = A/t, efficiency is useful work over total work and stays below 100 %.",
         "Mechanical energy is conserved only without friction and losses.",
         "Momentum p = mv is conserved in a closed system; collisions and recoil are the standard cases."],
        ["work-power", "work-power", "energy-conservation", "momentum"], ["energy"]),
    "statics": _entry(
        ["Момент силы M = Fd, где d — плечо: перпендикуляр от оси вращения до линии действия силы.",
         "Равновесие требует равенства нулю и суммы сил, и суммы моментов.",
         "Давление p = F/S; давление жидкости p = ρgh зависит от глубины, а не от формы сосуда.",
         "Сила Архимеда F = ρжVпогрg; тело плавает, когда она уравновешивает силу тяжести."],
        ["Torque M = Fd where d is the perpendicular distance from the axis to the line of action.",
         "Equilibrium needs both zero net force and zero net torque.",
         "Pressure p = F/S; liquid pressure p = ρgh depends on depth, not on the shape of the vessel.",
         "Buoyancy F = ρ_liquid·V_submerged·g balances gravity for a floating body."],
        ["torque", "torque", "pressure-hydrostatics", "archimedes"], ["statics"]),
    "molecular": _entry(
        ["Количество вещества ν = m/M в молях; молярная масса численно равна относительной молекулярной.",
         "В уравнении pV = νRT температура обязательно в кельвинах: T = t + 273.",
         "Для одной порции газа p₁V₁/T₁ = p₂V₂/T₂; выбирайте закон по постоянной величине (T, p или V).",
         "Средняя кинетическая энергия молекул растёт с температурой, а не с объёмом сосуда."],
        ["Amount of substance ν = m/M in moles; molar mass equals the relative molecular mass numerically.",
         "In pV = νRT the temperature is in kelvin: T = t + 273.",
         "For one gas sample p₁V₁/T₁ = p₂V₂/T₂; pick the law by the constant quantity.",
         "The mean kinetic energy of molecules grows with temperature, not with volume."],
        ["amount-substance", "ideal-gas", "isoprocesses", "amount-substance"], ["molecular"]),
    "thermo": _entry(
        ["Теплота нагревания Q = cmΔt зависит от разности температур; Δt в °C равно ΔT в К.",
         "При плавлении и кипении температура постоянна: Q = λm и Q = Lm.",
         "Тепловой баланс: сколько теплоты отдано, столько и получено (с потерями — меньше).",
         "Первый закон термодинамики ΔU = Q + Aвнешн: теплота и работа меняют внутреннюю энергию."],
        ["Heat Q = cmΔt depends on the temperature difference; a difference in °C equals one in K.",
         "During melting and boiling the temperature is constant: Q = λm and Q = Lm.",
         "Heat balance: the heat given away equals the heat received (less with losses).",
         "First law ΔU = Q + A_external: heat and work change internal energy."],
        ["heat-capacity", "phase-first-law", "heat-capacity", "phase-first-law"], ["thermo"]),
    "electrostatics": _entry(
        ["Закон Кулона F = k|q₁q₂|/r²: сила убывает как квадрат расстояния и направлена вдоль прямой между зарядами.",
         "Напряжённость E = F/q — силовая характеристика поля, измеряется в В/м.",
         "Напряжение — это работа поля по переносу единичного заряда: U = A/q, в однородном поле E = U/d.",
         "Ёмкость конденсатора C = q/U; для плоского C = εε₀S/d."],
        ["Coulomb's law F = k|q₁q₂|/r² falls as the square of the distance.",
         "Field strength E = F/q is measured in V/m.",
         "Voltage is work per unit charge: U = A/q, and E = U/d in a uniform field.",
         "Capacitance C = q/U; for a flat capacitor C = εε₀S/d."],
        ["coulomb-field", "coulomb-field", "potential-capacitance", "potential-capacitance"], ["electrostatics"]),
    "current": _entry(
        ["Закон Ома для участка цепи I = U/R: ток не «расходуется» в лампе.",
         "Последовательное соединение: ток одинаков, сопротивления складываются.",
         "Параллельное соединение: напряжение одинаково, общее сопротивление меньше наименьшего.",
         "Работа и мощность тока: A = UIt, P = UI; амперметр — последовательно, вольтметр — параллельно."],
        ["Ohm's law I = U/R: current is not consumed by a lamp.",
         "In series the current is the same and resistances add.",
         "In parallel the voltage is the same and the total resistance is the smallest one's limit.",
         "A = UIt and P = UI; an ammeter goes in series, a voltmeter in parallel."],
        ["ohm-law", "circuits", "circuits", "current-work"], ["dc"]),
    "magnetism": _entry(
        ["Сила Ампера F = BIl·sin α действует на проводник с током; максимум при перпендикулярном поле.",
         "Сила Лоренца перпендикулярна скорости: она не совершает работы и меняет только направление.",
         "Магнитный поток Φ = BS·cos α; ЭДС индукции возникает при изменении потока: |ε| = ΔΦ/Δt.",
         "Правило Ленца: индукционный ток противодействует причине, его вызвавшей."],
        ["Ampère force F = BIl·sin α is maximal when the field is perpendicular to the wire.",
         "The Lorentz force is perpendicular to the velocity, does no work and only turns the motion.",
         "Flux Φ = BS·cos α; EMF appears while the flux changes: |ε| = ΔΦ/Δt.",
         "Lenz's rule: the induced current opposes the change that produced it."],
        ["magnetic-forces", "magnetic-forces", "induction", "induction"], ["magnetism"]),
    "oscillations": _entry(
        ["Период и частота: ν = 1/T; круговая частота ω = 2πν.",
         "Период нитяного маятника T = 2π√(l/g) не зависит от массы, пружинного — от амплитуды (при малых колебаниях).",
         "Длина волны λ = vT = v/ν; скорость волны задаёт среда, частоту — источник.",
         "Эхо и эхолот: сигнал идёт туда и обратно, поэтому 2s = vt."],
        ["Period and frequency: ν = 1/T, angular frequency ω = 2πν.",
         "A pendulum's period T = 2π√(l/g) is independent of mass; a spring pendulum's is independent of small amplitudes.",
         "Wavelength λ = vT = v/ν: the medium sets the speed, the source the frequency.",
         "Echo and sonar use the doubled path: 2s = vt."],
        ["oscillations", "oscillations", "waves-sound", "waves-sound"], ["waves"]),
    "optics": _entry(
        ["Углы падения и отражения отсчитываются от перпендикуляра к поверхности.",
         "При переходе в более плотную среду луч идёт ближе к перпендикуляру, n = sin α / sin γ.",
         "Формула тонкой линзы 1/F = 1/d + 1/f; для мнимого изображения f < 0.",
         "Оптическая сила D = 1/F в диоптриях, фокусное расстояние — в метрах."],
        ["Angles of incidence and reflection are measured from the normal.",
         "Entering a denser medium the ray bends towards the normal, n = sin α / sin γ.",
         "Thin lens: 1/F = 1/d + 1/f; a virtual image has f < 0.",
         "Optical power D = 1/F in dioptres with F in metres."],
        ["reflection-refraction", "reflection-refraction", "lens", "lens"], ["optics"]),
    "quantum": _entry(
        ["Энергия фотона E = hν = hc/λ; интенсивность света меняет число фотонов, а не энергию одного.",
         "Уравнение фотоэффекта hν = Aвых + Eк; красная граница определяется работой выхода.",
         "Ядро: Z протонов, A − Z нейтронов; при α-распаде A уменьшается на 4, Z — на 2, при β-распаде Z растёт на 1.",
         "Закон распада N = N₀·2^(−t/T): период полураспада не зависит от внешних условий."],
        ["Photon energy E = hν = hc/λ; intensity changes the number of photons, not the energy of one.",
         "Photoelectric equation hν = A_escape + E_kinetic; the red threshold comes from the work function.",
         "Nucleus: Z protons, A − Z neutrons; alpha decay reduces A by 4 and Z by 2, beta decay raises Z by 1.",
         "Decay law N = N₀·2^(−t/T): the half-life is independent of external conditions."],
        ["photoeffect", "photoeffect", "atom-nucleus", "radioactivity"], ["quantum"]),
}


def payload() -> dict:
    missing = [topic for topic in TOPIC_ORDER if topic not in STUDY]
    if missing:
        raise PhysicsError("нет конспекта для тем: " + ", ".join(missing))
    extra = [topic for topic in STUDY if topic not in TOPIC_ORDER]
    if extra:
        raise PhysicsError("конспект для неизвестных тем: " + ", ".join(extra))
    return STUDY
