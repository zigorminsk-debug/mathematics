"""formulas.py — справочник формул (RU/EN), который открывается на экзамене.

Formula sheet shown by the "Сборник формул / Formula sheet" tool of both apps.
Formulas are plain Unicode so they render without any math engine and work
offline.
"""

from __future__ import annotations


def _g(gid, ru, en, items):
    return {"id": gid, "title": {"ru": ru, "en": en},
            "items": [{"name": {"ru": n_ru, "en": n_en}, "formula": f} for n_ru, n_en, f in items]}


GROUPS = [
    _g("powers", "Степени и корни", "Powers and roots", [
        ("Свойства степеней", "Power rules", "aᵐ · aⁿ = aᵐ⁺ⁿ;  aᵐ : aⁿ = aᵐ⁻ⁿ;  (aᵐ)ⁿ = aᵐⁿ"),
        ("Отрицательный и нулевой показатель", "Negative and zero exponent",
         "a⁻ⁿ = 1/aⁿ;  a⁰ = 1  (a ≠ 0)"),
        ("Дробный показатель", "Fractional exponent", "a^(m/n) = ⁿ√(aᵐ)  (a ≥ 0)"),
        ("Корни", "Roots", "√(ab) = √a·√b;  √(a/b) = √a/√b;  (√a)² = a  (a ≥ 0)"),
        ("Вынесение множителя", "Simplifying radicals", "√(a²b) = a√b  (a ≥ 0)"),
        ("Модуль", "Absolute value", "|a| = a при a ≥ 0;  |a| = −a при a < 0"),
    ]),
    _g("algebra", "Формулы сокращённого умножения", "Algebraic identities", [
        ("Квадрат суммы и разности", "Square of a sum / difference",
         "(a ± b)² = a² ± 2ab + b²"),
        ("Разность квадратов", "Difference of squares", "a² − b² = (a − b)(a + b)"),
        ("Куб суммы и разности", "Cube of a sum / difference",
         "(a ± b)³ = a³ ± 3a²b + 3ab² ± b³"),
        ("Сумма и разность кубов", "Sum / difference of cubes",
         "a³ ± b³ = (a ± b)(a² ∓ ab + b²)"),
    ]),
    _g("quadratic", "Квадратное уравнение", "Quadratic equation", [
        ("Дискриминант", "Discriminant", "D = b² − 4ac"),
        ("Корни", "Roots", "x = (−b ± √D)/(2a);  при D > 0 два корня, D = 0 один, D < 0 нет"),
        ("Теорема Виета", "Vieta's theorem", "x₁ + x₂ = −b/a;  x₁·x₂ = c/a"),
        ("Разложение трёхчлена", "Factoring", "ax² + bx + c = a(x − x₁)(x − x₂)"),
        ("Вершина параболы", "Parabola vertex", "x₀ = −b/(2a);  y₀ = y(x₀)"),
    ]),
    _g("progressions", "Прогрессии", "Progressions", [
        ("Арифметическая: n-й член", "Arithmetic: n-th term", "aₙ = a₁ + (n − 1)d"),
        ("Арифметическая: сумма", "Arithmetic: sum",
         "Sₙ = (a₁ + aₙ)·n/2 = (2a₁ + (n − 1)d)·n/2"),
        ("Геометрическая: n-й член", "Geometric: n-th term", "bₙ = b₁ · qⁿ⁻¹"),
        ("Геометрическая: сумма", "Geometric: sum", "Sₙ = b₁(qⁿ − 1)/(q − 1),  q ≠ 1"),
        ("Бесконечная сумма", "Infinite sum", "S = b₁/(1 − q),  |q| < 1"),
    ]),
    _g("trig", "Тригонометрия", "Trigonometry", [
        ("Основное тождество", "Pythagorean identity", "sin²α + cos²α = 1"),
        ("Тангенс и котангенс", "Tangent and cotangent", "tg α = sin α / cos α;  ctg α = cos α / sin α"),
        ("Двойной угол", "Double angle",
         "sin 2α = 2 sin α cos α;  cos 2α = cos²α − sin²α = 1 − 2sin²α;  tg 2α = 2tg α/(1 − tg²α)"),
        ("Сумма и разность углов", "Sum and difference",
         "sin(α ± β) = sin α cos β ± cos α sin β;  cos(α ± β) = cos α cos β ∓ sin α sin β"),
        ("Преобразование суммы в произведение", "Sum to product",
         "sin α + sin β = 2 sin((α+β)/2)·cos((α−β)/2)"),
        ("Табличные значения", "Table values",
         "30°: ½, √3/2, √3/3;  45°: √2/2, √2/2, 1;  60°: √3/2, ½, √3"),
        ("Формулы понижения степени", "Power reduction", "sin²α = (1 − cos 2α)/2;  cos²α = (1 + cos 2α)/2"),
    ]),
    _g("logs", "Логарифмы", "Logarithms", [
        ("Определение", "Definition", "log_a b = c ⟺ a^c = b  (a > 0, a ≠ 1, b > 0)"),
        ("Свойства", "Properties", "log_a(xy) = log_a x + log_a y;  log_a(x/y) = log_a x − log_a y"),
        ("Степень под логарифмом", "Power rule", "log_a xⁿ = n·log_a x"),
        ("Переход к новому основанию", "Change of base", "log_a b = log_c b / log_c a"),
        ("Основное логарифмическое тождество", "Logarithmic identity", "a^(log_a b) = b"),
    ]),
    _g("derivative", "Производные", "Derivatives", [
        ("Основные правила", "Basic rules", "(C)′ = 0;  (xⁿ)′ = n·xⁿ⁻¹;  (u ± v)′ = u′ ± v′"),
        ("Произведение и частное", "Product and quotient",
         "(uv)′ = u′v + uv′;  (u/v)′ = (u′v − uv′)/v²"),
        ("Сложная функция", "Chain rule", "(f(u))′ = f′(u) · u′"),
        ("Тригонометрические функции", "Trigonometric functions",
         "(sin x)′ = cos x;  (cos x)′ = −sin x;  (tg x)′ = 1/cos²x"),
        ("Показательная и логарифмическая", "Exponential and logarithmic",
         "(eˣ)′ = eˣ;  (aˣ)′ = aˣ ln a;  (ln x)′ = 1/x"),
        ("Геометрический смысл", "Geometric meaning", "k = f′(x₀) — угловой коэффициент касательной"),
        ("Физический смысл", "Physical meaning", "v(t) = s′(t) — скорость;  a(t) = v′(t) — ускорение"),
    ]),
    _g("planimetry", "Планиметрия", "Plane geometry", [
        ("Треугольник: площадь", "Triangle area",
         "S = ½ab·sin γ;  S = abc/(4R);  S = pr"),
        ("Теорема косинусов", "Law of cosines", "c² = a² + b² − 2ab·cos γ"),
        ("Теорема синусов", "Law of sines", "a/sin α = b/sin β = c/sin γ = 2R"),
        ("Правильный треугольник", "Equilateral triangle",
         "S = a²√3/4;  r = a√3/6;  R = a√3/3"),
        ("Трапеция", "Trapezoid", "S = (a + b)/2 · h;  средняя линия m = (a + b)/2"),
        ("Окружность", "Circle", "C = 2πR;  S = πR²;  длина дуги l = πRα/180°"),
        ("Вписанный угол", "Inscribed angle", "Вписанный угол равен половине центрального на ту же дугу"),
        ("Ромб", "Rhombus", "S = ½d₁d₂;  S = a²·sin α"),
    ]),
    _g("stereometry", "Стереометрия", "Solid geometry", [
        ("Параллелепипед", "Box", "V = abc;  S = 2(ab + bc + ac);  d² = a² + b² + c²"),
        ("Призма", "Prism", "V = S_осн · H"),
        ("Пирамида", "Pyramid", "V = ⅓·S_осн·H"),
        ("Цилиндр", "Cylinder", "V = πR²H;  S_бок = 2πRH"),
        ("Конус", "Cone", "V = ⅓πR²H;  S_бок = πRl"),
        ("Шар и сфера", "Sphere", "V = 4/3πR³;  S = 4πR²"),
        ("Куб", "Cube", "V = a³;  S = 6a²;  d = a√3"),
    ]),
    _g("probability", "Вероятность и комбинаторика", "Probability and combinatorics", [
        ("Классическое определение", "Classical definition", "P(A) = m/n"),
        ("Сложение и умножение", "Addition and multiplication",
         "P(A + B) = P(A) + P(B) − P(AB);  P(AB) = P(A)·P(B|A)"),
        ("Противоположное событие", "Complement", "P(Ā) = 1 − P(A)"),
        ("Бернулли", "Bernoulli", "Pₙ(k) = C(n,k)·pᵏ·(1 − p)ⁿ⁻ᵏ"),
        ("Математическое ожидание", "Expectation", "E = np для числа успехов в n испытаниях"),
        ("Перестановки и сочетания", "Permutations and combinations",
         "Pₙ = n!;  C(n,k) = n!/(k!(n − k)!)"),
    ]),
    _g("exam", "Полезно на ЦТ", "Exam tips", [
        ("Порядок действий", "Order of operations", "Степени → умножение/деление → сложение/вычитание"),
        ("Оценка результата", "Sanity check",
         "Прикиньте ответ: он должен быть разумного порядка и знака"),
        ("Проверка корня", "Root check", "Подставьте найденное значение в исходное уравнение"),
        ("Знаки", "Signs", "Умножение или деление неравенства на отрицательное число меняет знак"),
        ("Перевод единиц", "Unit conversion", "1 км/ч = 1000/3600 м/с ≈ 0,278 м/с"),
    ]),
]


def groups() -> dict:
    return {"groups": GROUPS,
            "note": {"ru": "Справочник доступен в любом режиме, включая экзаменационный.",
                     "en": "The sheet is available in every mode, including the exam mode."}}
