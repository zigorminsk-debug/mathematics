"""formulas.py — сборник формул по физике (разделы и строки).

Каждая строка ссылается на урок теории: в приложении формулу можно открыть
вместе с определением, обозначениями и границами применимости. Группы формул
привязаны к темам через study.py, поэтому при неверном ответе ученик получает
и конспект, и нужный раздел формул.
"""

from __future__ import annotations

from kit import PhysicsError


def _row(name_ru: str, name_en: str, formula: str, lesson: str) -> dict:
    return {"name": {"ru": name_ru, "en": name_en}, "formula": formula, "lesson": lesson}


GROUPS: list[dict] = [
    {
        "id": "units", "ru": "Измерения, единицы, размерность", "en": "Measurement, units, dimensions",
        "lessons": ["units-si", "dimensions-check", "measure-accuracy"],
        "items": [
            _row("Скорость из единиц", "Speed from units", "1 км/ч = 5/18 м/с ≈ 0,278 м/с", "dimensions-check"),
            _row("Приставки СИ", "SI prefixes", "мк = 10⁻⁶, м = 10⁻³, с = 10⁻², к = 10³, М = 10⁶", "units-si"),
            _row("Мощность и энергия", "Power and energy", "1 кВт·ч = 3,6·10⁶ Дж; 1 кВт = 1000 Вт", "units-si"),
            _row("Цена деления", "Scale division", "c = (a₂ − a₁)/n — разность соседних подписей на число промежутков", "measure-accuracy"),
        ],
    },
    {
        "id": "kinematics", "ru": "Кинематика", "en": "Kinematics",
        "lessons": ["motion-terms", "uniform-motion", "accelerated-motion", "kinematics-graphs", "free-fall"],
        "items": [
            _row("Средняя скорость", "Average speed", "vср = s/t (весь путь на всё время)", "motion-terms"),
            _row("Равномерное движение", "Uniform motion", "s = vt, x = x₀ + vt", "uniform-motion"),
            _row("Скорость при разгоне", "Velocity under acceleration", "v = v₀ + at", "accelerated-motion"),
            _row("Путь при разгоне", "Distance under acceleration", "s = v₀t + at²/2, s = (v₀ + v)t/2", "accelerated-motion"),
            _row("Путь без времени", "Distance without time", "s = (v² − v₀²)/(2a)", "accelerated-motion"),
            _row("Свободное падение", "Free fall", "h = gt²/2, v = gt (при v₀ = 0, без сопротивления)", "free-fall"),
            _row("Наклон на графике v(t)", "Slope of v(t)", "a = Δv/Δt, путь = площадь под графиком", "kinematics-graphs"),
        ],
    },
    {
        "id": "dynamics", "ru": "Динамика", "en": "Dynamics",
        "lessons": ["newton-laws", "forces-weight", "friction-elasticity", "force-diagram"],
        "items": [
            _row("Второй закон Ньютона", "Second law", "a = F/m, F = ma (равнодействующая)", "newton-laws"),
            _row("Третий закон", "Third law", "F₁₂ = −F₂₁: силы приложены к разным телам", "newton-laws"),
            _row("Сила тяжести и вес", "Weight", "F = mg; P = mg при покое на горизонтальной опоре", "forces-weight"),
            _row("Трение скольжения", "Sliding friction", "Fтр = μN", "friction-elasticity"),
            _row("Закон Гука", "Hooke's law", "F = kx (в пределах упругости)", "friction-elasticity"),
        ],
    },
    {
        "id": "energy", "ru": "Работа, энергия, импульс", "en": "Work, energy, momentum",
        "lessons": ["work-power", "energy-conservation", "momentum"],
        "items": [
            _row("Механическая работа", "Work", "A = Fs·cos α", "work-power"),
            _row("Мощность и КПД", "Power and efficiency", "P = A/t, η = Aполез/Aзатр", "work-power"),
            _row("Кинетическая энергия", "Kinetic energy", "Eк = mv²/2", "energy-conservation"),
            _row("Потенциальная энергия", "Potential energy", "Eп = mgh, Eупр = kx²/2", "energy-conservation"),
            _row("Импульс и сохранение", "Momentum", "p = mv; m₁v₁ + m₂v₂ = m₁v₁′ + m₂v₂′", "momentum"),
        ],
    },
    {
        "id": "statics", "ru": "Статика, давление, гидростатика", "en": "Statics, pressure, hydrostatics",
        "lessons": ["torque", "pressure-hydrostatics", "archimedes"],
        "items": [
            _row("Момент силы", "Torque", "M = Fd, где d — плечо (перпендикуляр от оси)", "torque"),
            _row("Правило рычага", "Lever rule", "F₁d₁ = F₂d₂", "torque"),
            _row("Давление", "Pressure", "p = F/S; 1 Па = 1 Н/м²", "pressure-hydrostatics"),
            _row("Давление жидкости", "Liquid pressure", "p = ρgh (глубина, не объём)", "pressure-hydrostatics"),
            _row("Сила Архимеда", "Buoyancy", "FА = ρжVпогрg; условие плавания FА = mg", "archimedes"),
        ],
    },
    {
        "id": "molecular", "ru": "Молекулярная физика", "en": "Molecular physics",
        "lessons": ["amount-substance", "ideal-gas", "isoprocesses"],
        "items": [
            _row("Количество вещества", "Amount of substance", "ν = m/M; N = νNₐ", "amount-substance"),
            _row("Уравнение состояния", "Ideal gas law", "pV = νRT, T = t + 273", "ideal-gas"),
            _row("Объединённый газовый закон", "Combined gas law", "p₁V₁/T₁ = p₂V₂/T₂", "ideal-gas"),
            _row("Изопроцессы", "Isoprocesses", "T = const: pV = const; p = const: V/T = const; V = const: p/T = const", "isoprocesses"),
        ],
    },
    {
        "id": "thermo", "ru": "Теплота и термодинамика", "en": "Heat and thermodynamics",
        "lessons": ["heat-capacity", "phase-first-law"],
        "items": [
            _row("Нагревание", "Heating", "Q = cm(t₂ − t₁)", "heat-capacity"),
            _row("Сгорание топлива", "Fuel combustion", "Q = qm", "heat-capacity"),
            _row("Плавление и парообразование", "Phase change", "Q = λm (плавление), Q = Lm (кипение)", "phase-first-law"),
            _row("Первый закон термодинамики", "First law", "ΔU = Q + Aвнешн", "phase-first-law"),
        ],
    },
    {
        "id": "electrostatics", "ru": "Электростатика", "en": "Electrostatics",
        "lessons": ["coulomb-field", "potential-capacitance"],
        "items": [
            _row("Закон Кулона", "Coulomb's law", "F = k|q₁q₂|/r²", "coulomb-field"),
            _row("Напряжённость поля", "Field strength", "E = F/q, E = U/d для однородного поля", "coulomb-field"),
            _row("Работа поля и напряжение", "Field work", "A = qU = q(φ₁ − φ₂)", "potential-capacitance"),
            _row("Электроёмкость", "Capacitance", "C = q/U; для плоского конденсатора C = εε₀S/d", "potential-capacitance"),
        ],
    },
    {
        "id": "dc", "ru": "Постоянный ток", "en": "Direct current",
        "lessons": ["ohm-law", "circuits", "current-work"],
        "items": [
            _row("Закон Ома", "Ohm's law", "I = U/R", "ohm-law"),
            _row("Сопротивление проводника", "Wire resistance", "R = ρl/S", "ohm-law"),
            _row("Последовательное соединение", "Series connection", "I = const, R = R₁ + R₂, U = U₁ + U₂", "circuits"),
            _row("Параллельное соединение", "Parallel connection", "U = const, 1/R = 1/R₁ + 1/R₂, I = I₁ + I₂", "circuits"),
            _row("Работа и мощность тока", "Electric work and power", "A = UIt, P = UI = I²R = U²/R", "current-work"),
        ],
    },
    {
        "id": "magnetism", "ru": "Магнитное поле и индукция", "en": "Magnetic field and induction",
        "lessons": ["magnetic-forces", "induction"],
        "items": [
            _row("Сила Ампера", "Ampère force", "F = BIl·sin α", "magnetic-forces"),
            _row("Сила Лоренца", "Lorentz force", "F = qvB·sin α (перпендикулярна скорости)", "magnetic-forces"),
            _row("Магнитный поток", "Magnetic flux", "Φ = BS·cos α", "induction"),
            _row("ЭДС индукции", "Induced EMF", "|ε| = ΔΦ/Δt", "induction"),
        ],
    },
    {
        "id": "waves", "ru": "Колебания, волны, звук", "en": "Oscillations, waves, sound",
        "lessons": ["oscillations", "waves-sound"],
        "items": [
            _row("Период и частота", "Period and frequency", "ν = 1/T, ω = 2πν", "oscillations"),
            _row("Маятники", "Pendulums", "T = 2π√(l/g); T = 2π√(m/k)", "oscillations"),
            _row("Длина волны", "Wavelength", "λ = vT = v/ν", "waves-sound"),
            _row("Звук и эхо", "Sound and echo", "2s = vt (сигнал идёт туда и обратно)", "waves-sound"),
        ],
    },
    {
        "id": "optics", "ru": "Оптика", "en": "Optics",
        "lessons": ["reflection-refraction", "lens"],
        "items": [
            _row("Отражение", "Reflection", "угол падения равен углу отражения", "reflection-refraction"),
            _row("Показатель преломления", "Refractive index", "n = sin α / sin γ = c/v", "reflection-refraction"),
            _row("Формула тонкой линзы", "Thin lens", "1/F = 1/d + 1/f", "lens"),
            _row("Оптическая сила", "Optical power", "D = 1/F (диоптрии), F в метрах", "lens"),
        ],
    },
    {
        "id": "quantum", "ru": "Квантовые явления и ядро", "en": "Quantum phenomena and nucleus",
        "lessons": ["photoeffect", "atom-nucleus", "radioactivity"],
        "items": [
            _row("Энергия фотона", "Photon energy", "E = hν = hc/λ", "photoeffect"),
            _row("Уравнение фотоэффекта", "Photoelectric equation", "hν = Aвых + Eк", "photoeffect"),
            _row("Строение ядра", "Nucleus", "Z протонов, A − Z нейтронов; ᴬZ X", "atom-nucleus"),
            _row("Закон радиоактивного распада", "Decay law", "N = N₀·2^(−t/T), α-распад: A − 4, Z − 2", "radioactivity"),
        ],
    },
]


def groups() -> dict:
    ids = [group["id"] for group in GROUPS]
    if len(set(ids)) != len(ids):
        raise PhysicsError("идентификаторы разделов формул повторяются")
    lessons = [lesson for group in GROUPS for lesson in group["lessons"]]
    if len(set(lessons)) != len(lessons):
        raise PhysicsError("урок теории попал в два раздела формул без нужды")
    items = 0
    for group in GROUPS:
        if not group["lessons"]:
            raise PhysicsError(f"раздел {group['id']} не связан с теорией")
        for item in group["items"]:
            if item["lesson"] not in group["lessons"]:
                raise PhysicsError(f"{group['id']}: строка без урока теории")
            items += 1
    return {"groups": GROUPS, "counts": {"groups": len(GROUPS), "items": items}}
