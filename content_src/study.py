"""study.py — что изучить по каждой теме («тема для изучения» при ошибке).

Когда ученик отвечает неверно, приложение не ограничивается правильным ответом:
оно сразу открывает тему, к которой относится задание, — этот короткий конспект
(что повторить + какие разделы сборника формул открыть), а на отдельном экране
«Изучение» — ещё и разобранные примеры и переход к тренировке по теме.

``STUDY`` покрывает каждую тему из ``kit.TOPICS``: ``build_content.py`` падает,
если тема осталась без конспекта или указан несуществующий раздел формул, а
``formulas`` — ключи разделов из ``content_src/formulas.py``.

Study notes per topic: what to revise after a mistake, plus the formula-sheet
sections that belong to the topic. Opened automatically on a wrong answer.
"""

from __future__ import annotations

STUDY: dict[str, dict] = {
    "numbers": {
        "formulas": ["numbers", "powers"],
        "ru": ["Порядок действий: скобки → степень → умножение и деление → сложение и вычитание.",
               "Обыкновенные дроби приводим к общему знаменателю; деление заменяем умножением на обратную дробь.",
               "Десятичную дробь полезно записать обыкновенной (0,125 = 1/8), а результат оценить по величине."],
        "en": ["Order of operations: brackets → powers → multiplication and division → addition and subtraction.",
               "Give fractions a common denominator; replace division by multiplication by the reciprocal.",
               "Rewrite a decimal as a fraction (0.125 = 1/8) and sanity-check the size of the result."],
    },
    "expressions": {
        "formulas": ["powers", "multiplication"],
        "ru": ["Действия со степенями: при умножении показатели складываются, при возведении степени в степень — перемножаются.",
               "Формулы сокращённого умножения применяются целиком, среднее слагаемое 2ab не теряется.",
               "Сокращать можно только общие множители после разложения на множители, а не отдельные слагаемые."],
        "en": ["Power rules: exponents add when multiplying and multiply when raising a power to a power.",
               "Apply the identities as a whole; do not drop the middle term 2ab.",
               "Only common factors may be cancelled, after factoring — never individual terms."],
    },
    "equations": {
        "formulas": ["quadratic", "multiplication"],
        "ru": ["При переносе слагаемого через знак равенства его знак меняется; пропорция решается крест-накрест.",
               "Квадратное уравнение: дискриминант и формула корней, для приведённого — теорема Виета.",
               "После решения проверяем ОДЗ и отбрасываем посторонние корни подстановкой."],
        "en": ["A term moved across the equals sign changes its sign; solve proportions by cross-multiplying.",
               "Quadratic equations: the discriminant and the root formula; Vieta's theorem for monic ones.",
               "After solving, check the domain and discard extraneous roots by substitution."],
    },
    "inequalities": {
        "formulas": ["inequalities", "quadratic"],
        "ru": ["При умножении или делении на отрицательное число знак неравенства переворачивается.",
               "Метод интервалов: корни на числовую прямую, знак на каждом интервале, строгие точки выколоты.",
               "Для квадратного неравенства смотрим на корни трёхчлена и направление ветвей параболы."],
        "en": ["Multiplying or dividing by a negative number reverses the inequality sign.",
               "Interval method: roots on the number line, the sign on each interval, strict points are open.",
               "For a quadratic inequality use the roots of the trinomial and the direction of the branches."],
    },
    "functions": {
        "formulas": ["functions", "quadratic"],
        "ru": ["Область определения: знаменатель не равен нулю, под корнем чётной степени — неотрицательное выражение.",
               "Область значений y = a + b·sin x (или cos x) получаем из −1 ≤ sin x ≤ 1, не теряя знаки при умножении.",
               "Преобразования графика: сдвиги, растяжения и отражения от осей."],
        "en": ["Domain: the denominator must not vanish; an even root needs a non-negative radicand.",
               "The range of y = a + b·sin x (or cos x) comes from −1 ≤ sin x ≤ 1, keeping track of sign flips.",
               "Graph transformations: shifts, stretches and reflections in the axes."],
    },
    "progressions": {
        "formulas": ["progressions"],
        "ru": ["Арифметическая: aₙ = a₁ + (n − 1)d — между первым и n-м членом n − 1 шагов.",
               "Геометрическая: bₙ = b₁·qⁿ⁻¹; из b₃/b₁ получаем q², знак q выбираем по условию.",
               "Сумма: Sₙ = (a₁ + aₙ)·n/2 для арифметической и b₁(qⁿ − 1)/(q − 1) для геометрической."],
        "en": ["Arithmetic: aₙ = a₁ + (n − 1)d — there are n − 1 steps between the first and n-th terms.",
               "Geometric: bₙ = b₁·qⁿ⁻¹; b₃/b₁ gives q², and the sign of q follows from the statement.",
               "Sums: Sₙ = (a₁ + aₙ)·n/2 (arithmetic) and b₁(qⁿ − 1)/(q − 1) (geometric)."],
    },
    "wordproblems": {
        "formulas": ["numbers", "progressions"],
        "ru": ["Обозначаем неизвестное за x и записываем, что именно одинаково в двух ситуациях (путь, работа, стоимость).",
               "Движение: s = vt; навстречу скорости складываются, по течению — собственная плюс скорость течения.",
               "Проценты берутся от текущей величины: снижение на p% — умножение на (1 − p/100), и следующий процент уже от новой цены."],
        "en": ["Let x be the unknown and write down what is equal in the two situations (distance, work, cost).",
               "Motion: s = vt; speeds add when moving towards each other, and downstream the current is added.",
               "Percentages refer to the current value: a p% reduction multiplies by (1 − p/100), and the next percentage applies to the new price."],
    },
    "trig": {
        "formulas": ["trig"],
        "ru": ["Основное тождество sin²α + cos²α = 1 связывает синус и косинус одного угла.",
               "Знак функции определяем по четверти, значение — по табличным углам 30°, 45°, 60°.",
               "Формулы двойного угла: sin 2α = 2sin α·cos α, cos 2α = cos²α − sin²α = 1 − 2sin²α."],
        "en": ["The Pythagorean identity sin²α + cos²α = 1 links the sine and cosine of one angle.",
               "Fix the sign from the quadrant and the value from the table angles 30°, 45°, 60°.",
               "Double-angle formulas: sin 2α = 2sin α·cos α, cos 2α = cos²α − sin²α = 1 − 2sin²α."],
    },
    "trigequations": {
        "formulas": ["trig"],
        "ru": ["Сначала приводим уравнение к простейшему виду sin x = a, cos x = a или tg x = a.",
               "Записываем общую серию корней и только потом отбираем корни на заданном отрезке или наименьший положительный.",
               "Не теряем вторую серию: у sin x = a корни даёт формула (−1)ⁿ arcsin a + πn."],
        "en": ["First reduce the equation to a basic form sin x = a, cos x = a or tg x = a.",
               "Write the general series of roots, and only then select the roots on the given interval or the smallest positive one.",
               "Do not lose the second series: sin x = a gives x = (−1)ⁿ arcsin a + πn."],
    },
    "logexp": {
        "formulas": ["logexp"],
        "ru": ["Определение: log_a b = c ⇔ aᶜ = b (a > 0, a ≠ 1, b > 0); отсюда a^(log_a b) = b.",
               "Свойства: логарифм произведения — сумма логарифмов, степени — показатель выносится множителем.",
               "Показательное уравнение приводим к одному основанию и приравниваем показатели; в логарифмическом проверяем ОДЗ."],
        "en": ["Definition: log_a b = c ⇔ aᶜ = b (a > 0, a ≠ 1, b > 0); hence a^(log_a b) = b.",
               "Properties: the logarithm of a product is a sum, and an exponent comes out as a factor.",
               "For an exponential equation use one common base and equate the exponents; for a logarithmic one check the domain."],
    },
    "planimetry": {
        "formulas": ["planimetry"],
        "ru": ["Начинаем с чертежа и известных элементов: стороны, углы, высоты, диагонали.",
               "Прямоугольный треугольник: теорема Пифагора, медиана к гипотенузе равна её половине.",
               "Площади: треугольник a·h/2, трапеция (a + b)·h/2, ромб d₁·d₂/2; теоремы синусов и косинусов связывают стороны и углы."],
        "en": ["Start from a drawing and the known elements: sides, angles, heights, diagonals.",
               "Right triangle: the Pythagorean theorem; the median to the hypotenuse equals half of it.",
               "Areas: triangle a·h/2, trapezoid (a + b)·h/2, rhombus d₁·d₂/2; the laws of sines and cosines link sides and angles."],
    },
    "stereometry": {
        "formulas": ["stereometry"],
        "ru": ["Объём призмы и цилиндра — площадь основания на высоту: V = Sосн·h.",
               "У пирамиды и конуса появляется множитель 1/3: V = Sосн·h/3, V = πR²h/3.",
               "Если спрашивают коэффициент при π, выносим π за скобки и не подставляем 3,14."],
        "en": ["Volumes of prisms and cylinders are base area times height: V = S·h.",
               "Pyramids and cones carry a factor 1/3: V = S·h/3, V = πR²h/3.",
               "If the coefficient at π is requested, factor π out and do not substitute 3.14."],
    },
    "derivative": {
        "formulas": ["derivative"],
        "ru": ["Таблица производных: (xⁿ)′ = n·xⁿ⁻¹, (sin x)′ = cos x, (cos x)′ = −sin x.",
               "Сложная функция: сначала производная внешней, затем умножаем на производную внутренней.",
               "Значение в точке считаем после записи производной: подставляем x₀ в f′, а не в f."],
        "en": ["Derivative table: (xⁿ)′ = n·xⁿ⁻¹, (sin x)′ = cos x, (cos x)′ = −sin x.",
               "Composite functions: differentiate the outer function, then multiply by the derivative of the inner one.",
               "Differentiate first and only then substitute x₀ into f′, not into f."],
    },
    "research": {
        "formulas": ["derivative", "functions"],
        "ru": ["Критические точки — нули производной; вид экстремума определяет смена знака f′.",
               "Через точку, где f′ меняет знак с − на +, — минимум, с + на − — максимум.",
               "На отрезке наибольшее и наименьшее значения ищем и в критических точках, и на концах."],
        "en": ["Critical points are the zeros of the derivative; the type of extremum follows from the sign change of f′.",
               "A sign change − → + gives a minimum, + → − gives a maximum.",
               "On a segment, check both the critical points and the endpoints for the largest and smallest values."],
    },
    "combinatorics": {
        "formulas": ["combinatorics"],
        "ru": ["Порядок важен — размещения или перестановки, не важен — сочетания Cₙᵏ = n!/(k!(n − k)!).",
               "Классическая вероятность P = m/n: благоприятные исходы ко всем равновозможным.",
               "Факториалы и сочетания сокращаем до вычисления: C(n,2) = n(n − 1)/2."],
        "en": ["If the order matters use arrangements or permutations; if not, combinations Cₙᵏ = n!/(k!(n − k)!).",
               "Classical probability P = m/n: favourable outcomes over all equally likely outcomes.",
               "Cancel factorials and combinations before computing: C(n,2) = n(n − 1)/2."],
    },
    "vectors": {
        "formulas": ["vectors", "planimetry"],
        "ru": ["Координаты вектора — разность координат конца и начала; длина — корень из суммы квадратов координат.",
               "Скалярное произведение: a·b = x₁x₂ + y₁y₂ = |a||b|cos φ; перпендикулярность ⇔ a·b = 0.",
               "Середина отрезка — полусумма координат концов, коллинеарность — пропорциональность координат."],
        "en": ["Vector coordinates are the end minus the start; the length is the root of the sum of squared coordinates.",
               "Dot product: a·b = x₁x₂ + y₁y₂ = |a||b|cos φ; perpendicularity ⇔ a·b = 0.",
               "The midpoint is the half-sum of the endpoint coordinates; collinearity means proportional coordinates."],
    },
    "param": {
        "formulas": ["quadratic", "functions"],
        "ru": ["Условие на число корней переводим в условие на дискриминант: D > 0, D = 0 или D < 0.",
               "Касание прямой и параболы — тоже D = 0 у уравнения, полученного приравниванием.",
               "Из нескольких значений параметра выбираем то, что спрашивает условие (наибольшее, наименьшее, целое)."],
        "en": ["Translate the condition on the number of roots into a condition on the discriminant: D > 0, D = 0 or D < 0.",
               "Tangency of a line and a parabola is also D = 0 for the equation obtained by equating them.",
               "From several parameter values pick the one the statement asks for (largest, smallest, integer)."],
    },
    "logic": {
        "formulas": ["numbers", "progressions"],
        "ru": ["Ищем правило: разности соседних членов, формулу n-го члена или периодичность остатков.",
               "Остатки степеней по модулю повторяются циклами — важен остаток показателя при делении на длину цикла.",
               "Проверяем найденное правило на всех заданных членах, а не только на первых двух."],
        "en": ["Look for the rule: differences of consecutive terms, an n-th term formula, or a cycle of residues.",
               "Residues of powers repeat in cycles — what matters is the exponent modulo the cycle length.",
               "Check the rule you found against every given term, not just the first two."],
    },
}


def topics() -> list[str]:
    """Темы, для которых есть конспект (порядок задаёт kit.TOPIC_ORDER)."""
    return list(STUDY)


def payload() -> dict:
    """Часть ``topics.json``: конспекты по ключам тем из ``kit.TOPICS``."""
    return {key: {"formulas": entry["formulas"], "ru": entry["ru"], "en": entry["en"]}
            for key, entry in STUDY.items()}
