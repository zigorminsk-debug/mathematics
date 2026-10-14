"""formulas.py — справочник формул, доступный во время решения задания.

Каждая группа двуязычна: название группы, названия формул (ru/en) и сама формула
в виде обычного текста (без LaTeX, чтобы её можно было показывать и в Android, и
в Windows, и в печатном отчёте, и искать простым поиском по строке).

Formula reference book shown by the "formula sheet" tool of both applications.
"""

from __future__ import annotations

GROUPS = [
    {
        "id": "powers",
        "ru": "Степени, корни, модуль",
        "en": "Powers, roots, absolute value",
        "items": [
            {"ru": "Произведение степеней", "en": "Product of powers", "f": "aᵐ · aⁿ = aᵐ⁺ⁿ"},
            {"ru": "Частное степеней", "en": "Quotient of powers", "f": "aᵐ : aⁿ = aᵐ⁻ⁿ"},
            {"ru": "Степень степени", "en": "Power of a power", "f": "(aᵐ)ⁿ = aᵐⁿ"},
            {"ru": "Дробный показатель", "en": "Fractional exponent", "f": "a^(1/n) = ⁿ√a,  a^(m/n) = ⁿ√(aᵐ)"},
            {"ru": "Корень из произведения", "en": "Root of a product", "f": "√(a·b) = √a · √b  (a, b ≥ 0)"},
            {"ru": "Корень из частного", "en": "Root of a quotient", "f": "√(a : b) = √a : √b  (a ≥ 0, b > 0)"},
            {"ru": "Квадрат корня", "en": "Square of a root", "f": "(√a)² = a = √(a²) = |a|"},
            {"ru": "Вынесение множителя", "en": "Extracting a factor", "f": "√(a²b) = |a|·√b"},
            {"ru": "Модуль", "en": "Absolute value", "f": "|x| = x при x ≥ 0;  |x| = −x при x < 0"},
            {"ru": "Свойства модуля", "en": "Properties of |x|", "f": "|a·b| = |a|·|b|,  |a + b| ≤ |a| + |b|"},
        ],
    },
    {
        "id": "multiplication",
        "ru": "Формулы сокращённого умножения",
        "en": "Algebraic identities",
        "items": [
            {"ru": "Квадрат суммы", "en": "Square of a sum", "f": "(a + b)² = a² + 2ab + b²"},
            {"ru": "Квадрат разности", "en": "Square of a difference", "f": "(a − b)² = a² − 2ab + b²"},
            {"ru": "Разность квадратов", "en": "Difference of squares", "f": "a² − b² = (a − b)(a + b)"},
            {"ru": "Куб суммы", "en": "Cube of a sum", "f": "(a + b)³ = a³ + 3a²b + 3ab² + b³"},
            {"ru": "Куб разности", "en": "Cube of a difference", "f": "(a − b)³ = a³ − 3a²b + 3ab² − b³"},
            {"ru": "Сумма кубов", "en": "Sum of cubes", "f": "a³ + b³ = (a + b)(a² − ab + b²)"},
            {"ru": "Разность кубов", "en": "Difference of cubes", "f": "a³ − b³ = (a − b)(a² + ab + b²)"},
            {"ru": "Полный квадрат", "en": "Completing the square", "f": "ax² + bx + c = a(x + b/(2a))² − (b² − 4ac)/(4a)"},
        ],
    },
    {
        "id": "quadratic",
        "ru": "Квадратное уравнение и парабола",
        "en": "Quadratic equation and parabola",
        "items": [
            {"ru": "Корни квадратного уравнения", "en": "Roots of ax² + bx + c = 0", "f": "x = (−b ± √D) : (2a),  D = b² − 4ac"},
            {"ru": "Чётный коэффициент b", "en": "Even middle coefficient", "f": "x = (−b/2 ± √(b²/4 − ac)) : a"},
            {"ru": "Теорема Виета", "en": "Vieta's theorem", "f": "x₁ + x₂ = −b/a,  x₁·x₂ = c/a"},
            {"ru": "Разложение на множители", "en": "Factored form", "f": "ax² + bx + c = a(x − x₁)(x − x₂)"},
            {"ru": "Вершина параболы", "en": "Vertex of a parabola", "f": "x₀ = −b/(2a),  y₀ = c − b²/(4a)"},
            {"ru": "Знаки D", "en": "Signs of the discriminant", "f": "D > 0 — два корня, D = 0 — один, D < 0 — нет"},
            {"ru": "Формула для корня при D > 0", "en": "Simplified root formula", "f": "x = (2c) : (−b ∓ √D)"},
        ],
    },
    {
        "id": "progressions",
        "ru": "Прогрессии",
        "en": "Progressions",
        "items": [
            {"ru": "n-й член арифметической", "en": "n-th term, arithmetic", "f": "aₙ = a₁ + (n − 1)d"},
            {"ru": "Сумма арифметической", "en": "Sum, arithmetic", "f": "Sₙ = (a₁ + aₙ)·n/2 = (2a₁ + (n − 1)d)·n/2"},
            {"ru": "Свойство арифметической", "en": "Arithmetic mean property", "f": "aₙ = (aₙ₋₁ + aₙ₊₁)/2"},
            {"ru": "n-й член геометрической", "en": "n-th term, geometric", "f": "bₙ = b₁·qⁿ⁻¹"},
            {"ru": "Сумма геометрической", "en": "Sum, geometric", "f": "Sₙ = b₁(qⁿ − 1)/(q − 1),  q ≠ 1"},
            {"ru": "Бесконечная геометрическая", "en": "Infinite geometric series", "f": "S = b₁/(1 − q),  |q| < 1"},
            {"ru": "Сумма натуральных чисел", "en": "Sum of integers", "f": "1 + 2 + … + n = n(n + 1)/2"},
            {"ru": "Проценты", "en": "Percentages", "f": "на p% → умножить на (1 + p/100); снижение на p% → (1 − p/100)"},
        ],
    },
    {
        "id": "trig",
        "ru": "Тригонометрия",
        "en": "Trigonometry",
        "items": [
            {"ru": "Основное тождество", "en": "Pythagorean identity", "f": "sin²α + cos²α = 1"},
            {"ru": "Тангенс и котангенс", "en": "Tangent and cotangent", "f": "tg α = sin α / cos α,  ctg α = 1 / tg α"},
            {"ru": "Формула сложения", "en": "Addition formulas", "f": "sin(α ± β) = sin α cos β ± cos α sin β;  cos(α ± β) = cos α cos β ∓ sin α sin β"},
            {"ru": "Двойной угол", "en": "Double angle", "f": "sin 2α = 2 sin α cos α;  cos 2α = cos²α − sin²α"},
            {"ru": "Понижение степени", "en": "Reduction of powers", "f": "sin²α = (1 − cos 2α)/2;  cos²α = (1 + cos 2α)/2"},
            {"ru": "Таблица значений", "en": "Table of values", "f": "sin 30° = 1/2, sin 45° = √2/2, sin 60° = √3/2, sin 90° = 1"},
            {"ru": "Чётность", "en": "Parity", "f": "cos(−α) = cos α (чётная), sin(−α) = −sin α, tg(−α) = −tg α"},
            {"ru": "Решение sin x = a", "en": "Solution of sin x = a", "f": "x = (−1)ⁿ arcsin a + πn"},
            {"ru": "Решение cos x = a", "en": "Solution of cos x = a", "f": "x = ± arccos a + 2πn"},
            {"ru": "Решение tg x = a", "en": "Solution of tg x = a", "f": "x = arctg a + πn"},
            {"ru": "Теорема синусов", "en": "Law of sines", "f": "a / sin A = b / sin B = c / sin C = 2R"},
            {"ru": "Теорема косинусов", "en": "Law of cosines", "f": "c² = a² + b² − 2ab·cos C"},
        ],
    },
    {
        "id": "logexp",
        "ru": "Логарифмы и показательные",
        "en": "Logarithms and exponentials",
        "items": [
            {"ru": "Определение логарифма", "en": "Definition", "f": "log_a b = c ⇔ aᶜ = b  (a > 0, a ≠ 1, b > 0)"},
            {"ru": "Логарифм произведения", "en": "Logarithm of a product", "f": "log_a(b·c) = log_a b + log_a c"},
            {"ru": "Логарифм частного", "en": "Logarithm of a quotient", "f": "log_a(b/c) = log_a b − log_a c"},
            {"ru": "Логарифм степени", "en": "Logarithm of a power", "f": "log_a bᵏ = k·log_a b"},
            {"ru": "Переход к новому основанию", "en": "Change of base", "f": "log_a b = log_c b / log_c a"},
            {"ru": "Следствия", "en": "Immediate consequences", "f": "log_a a = 1,  log_a 1 = 0,  a^(log_a b) = b"},
            {"ru": "Степени двойки", "en": "Powers of two", "f": "2³ = 8, 2⁴ = 16, 2⁵ = 32, 2⁶ = 64, 2⁷ = 128, 2⁸ = 256, 2¹⁰ = 1024"},
            {"ru": "Степени тройки", "en": "Powers of three", "f": "3³ = 27, 3⁴ = 81, 3⁵ = 243"},
            {"ru": "Решение a^x = b", "en": "Solving aˣ = b", "f": "x = log_a b (приводим обе части к одному основанию)"},
        ],
    },
    {
        "id": "derivative",
        "ru": "Производная и исследование функции",
        "en": "Derivative and function study",
        "items": [
            {"ru": "Степень", "en": "Power rule", "f": "(xⁿ)′ = n·xⁿ⁻¹"},
            {"ru": "Постоянная и линейная", "en": "Constant and linear", "f": "(C)′ = 0,  (kx + b)′ = k"},
            {"ru": "Сумма", "en": "Sum", "f": "(u + v)′ = u′ + v′"},
            {"ru": "Произведение", "en": "Product", "f": "(u·v)′ = u′v + uv′"},
            {"ru": "Частное", "en": "Quotient", "f": "(u/v)′ = (u′v − uv′)/v²"},
            {"ru": "Геометрический смысл", "en": "Geometric meaning", "f": "f′(x₀) = tg α — угловой коэффициент касательной"},
            {"ru": "Уравнение касательной", "en": "Tangent line", "f": "y = f(x₀) + f′(x₀)(x − x₀)"},
            {"ru": "Монотонность", "en": "Monotonicity", "f": "f′ > 0 — возрастает, f′ < 0 — убывает"},
            {"ru": "Экстремум", "en": "Extremum", "f": "f′(x₀) = 0 и смена знака: − на + минимум, + на − максимум"},
            {"ru": "Наибольшее значение", "en": "Maximum on a segment", "f": "сравниваем значения в критических точках и на концах отрезка"},
        ],
    },
    {
        "id": "planimetry",
        "ru": "Планиметрия",
        "en": "Plane geometry",
        "items": [
            {"ru": "Площадь треугольника", "en": "Area of a triangle", "f": "S = a·h/2 = (a·b·sin C)/2 = p·r = abc/(4R)"},
            {"ru": "Формула Герона", "en": "Heron's formula", "f": "S = √(p(p − a)(p − b)(p − c)),  p = (a + b + c)/2"},
            {"ru": "Прямоугольный треугольник", "en": "Right triangle", "f": "c² = a² + b²;  r = (a + b − c)/2;  R = c/2"},
            {"ru": "Параллелограмм", "en": "Parallelogram", "f": "S = a·h = a·b·sin α"},
            {"ru": "Трапеция", "en": "Trapezoid", "f": "S = (a + b)·h/2,  средняя линия m = (a + b)/2"},
            {"ru": "Ромб", "en": "Rhombus", "f": "S = d₁·d₂/2 = a²·sin α"},
            {"ru": "Круг и окружность", "en": "Circle", "f": "S = πR²,  C = 2πR,  длина дуги l = πR·α°/180°"},
            {"ru": "Вписанный угол", "en": "Inscribed angle", "f": "вписанный угол равен половине центрального, опирающегося на ту же дугу"},
            {"ru": "Касательная и хорда", "en": "Tangent and chord", "f": "квадрат касательной = произведение секущей на её внешнюю часть"},
            {"ru": "Подобие", "en": "Similarity", "f": "площади относятся как квадрат коэффициента подобия: S₂/S₁ = k²"},
        ],
    },
    {
        "id": "stereometry",
        "ru": "Стереометрия",
        "en": "Solid geometry",
        "items": [
            {"ru": "Призма", "en": "Prism", "f": "V = Sосн · h,  Sбок = Pосн · h"},
            {"ru": "Пирамида", "en": "Pyramid", "f": "V = Sосн · h / 3"},
            {"ru": "Цилиндр", "en": "Cylinder", "f": "V = πR²h,  Sбок = 2πRh"},
            {"ru": "Конус", "en": "Cone", "f": "V = πR²h/3,  Sбок = πRl,  l = √(R² + h²)"},
            {"ru": "Шар и сфера", "en": "Sphere and ball", "f": "V = 4πR³/3,  S = 4πR²"},
            {"ru": "Куб", "en": "Cube", "f": "V = a³,  S = 6a²,  d = a√3"},
            {"ru": "Теорема о трёх перпендикулярах", "en": "Theorem of three perpendiculars", "f": "проекция наклонной ⟂ прямой ⇔ наклонная ⟂ прямой"},
            {"ru": "Угол между прямой и плоскостью", "en": "Angle between a line and a plane", "f": "угол между прямой и её проекцией"},
        ],
    },
    {
        "id": "combinatorics",
        "ru": "Комбинаторика и вероятность",
        "en": "Combinatorics and probability",
        "items": [
            {"ru": "Перестановки", "en": "Permutations", "f": "Pₙ = n!"},
            {"ru": "Размещения", "en": "Arrangements", "f": "Aₙᵏ = n!/(n − k)!"},
            {"ru": "Сочетания", "en": "Combinations", "f": "Cₙᵏ = n!/(k!(n − k)!)"},
            {"ru": "Классическая вероятность", "en": "Classical probability", "f": "P = m/n — благоприятные исходы к общему числу равновозможных"},
            {"ru": "Вероятность суммы несовместных", "en": "Sum of disjoint events", "f": "P(A ∪ B) = P(A) + P(B)"},
            {"ru": "Вероятность произведения независимых", "en": "Product of independent events", "f": "P(A ∩ B) = P(A)·P(B)"},
            {"ru": "Противоположное событие", "en": "Complement", "f": "P(Ā) = 1 − P(A)"},
            {"ru": "Значения факториалов", "en": "Factorials", "f": "3! = 6, 4! = 24, 5! = 120, 6! = 720"},
        ],
    },
    {
        "id": "numbers",
        "ru": "Числа и делимость",
        "en": "Numbers and divisibility",
        "items": [
            {"ru": "Признак делимости на 3 и 9", "en": "Divisible by 3 and 9", "f": "сумма цифр делится на 3 (на 9)"},
            {"ru": "Признак делимости на 4", "en": "Divisible by 4", "f": "две последние цифры образуют число, кратное 4"},
            {"ru": "Признак делимости на 11", "en": "Divisible by 11", "f": "разность сумм цифр на чётных и нечётных местах кратна 11"},
            {"ru": "НОД и НОК", "en": "GCD and LCM", "f": "НОК(a, b) = a·b : НОД(a, b)"},
            {"ru": "Деление с остатком", "en": "Division with remainder", "f": "a = b·q + r,  0 ≤ r < b"},
            {"ru": "Простые числа до 50", "en": "Primes below 50", "f": "2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47"},
            {"ru": "Оценка корня", "en": "Estimating a root", "f": "√a между соседними целыми: n ≤ √a < n + 1 ⇔ n² ≤ a < (n + 1)²"},
        ],
    },
]


def groups() -> dict:
    """The JSON body written to ``dist/content/formulas.json``.

    Authoring uses the compact keys ``ru``/``en``/``f``; the exported shape is
    ``name`` (bilingual) plus a plain-text ``formula`` body, which is what both
    the interface and the schema test expect.
    """
    exported = []
    for group in GROUPS:
        items = [
            {"name": {"ru": item["ru"], "en": item["en"]}, "formula": item["f"]}
            for item in group["items"]
        ]
        exported.append({"id": group["id"], "ru": group["ru"], "en": group["en"], "items": items})
    total = sum(len(group["items"]) for group in exported)
    return {"groups": exported, "counts": {"groups": len(exported), "items": total}}


def tasks():
    """No exam tasks here — the module is a reference, not a task bank."""
    return []
