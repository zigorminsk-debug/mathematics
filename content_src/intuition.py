"""Authored RU/EN everyday explanations; an aid, not a replacement for a theorem.

Each entry connects a familiar situation to the notation and states relevant
limits (units, domain, equiprobability, constant rates, idealised models).
The theory builder requires coverage and parallel translations for all lessons.
"""
from __future__ import annotations

EXPLANATIONS = {
    "order": [
        ("В магазине три одинаковых набора: в каждом тетрадь за 4 рубля и ручка за 2 рубля. Сначала узнаём цену одного набора: 4 + 2 = 6. Затем трёх: 3 · (4 + 2) = 18 рублей.",
         "A shop sells three identical sets, each with a 4-ruble notebook and a 2-ruble pen. First find one set's price: 4 + 2 = 6. Then three sets cost 3 × (4 + 2) = 18 rubles."),
        ("Скобки показывают, что относится к одному набору. Без них 3 · 4 + 2 = 14: это уже три тетради и только одна ручка. Порядок действий меняет смысл покупки, а не только способ записи.",
         "Brackets show what belongs to one set. Without them, 3 × 4 + 2 = 14 means three notebooks and only one pen. The operation order changes the purchase itself, not just the notation.")],
    "fractions": [
        ("Пиццу разделили на 8 равных кусочков. Три кусочка — 3/8 пиццы: знаменатель 8 говорит, на сколько равных частей разделили целое, числитель 3 — сколько взяли.",
         "A pizza is cut into 8 equal slices. Three slices are 3/8 of the pizza: denominator 8 tells how many equal parts make the whole, numerator 3 tells how many were taken."),
        ("Половина пиццы — и 1/2, и 4/8: кусочки мельче, но еды столько же. Складывать доли удобно после разрезания на одинаковые кусочки. Сравнение долей предполагает одно и то же целое: половина маленькой пиццы не равна половине большой по массе.",
         "Half a pizza is both 1/2 and 4/8: the slices are smaller but the amount is unchanged. Add fractions after using equal-sized slices. The whole must be the same: half a small pizza and half a large one need not have equal mass.")],
    "decimals": [
        ("На весах 2,5 кг яблок, цена 4,2 рубля за килограмм. Стоимость: 2,5 · 4,2 = 10,5 рубля. Десятичная дробь — обычная доля единицы: 0,5 кг — половина килограмма.",
         "Apples weigh 2.5 kg and cost 4.2 rubles per kilogram. The cost is 2.5 × 4.2 = 10.5 rubles. A decimal is a fraction of a unit: 0.5 kg is half a kilogram."),
        ("Оценка помогает проверить запятую: около 2,5 кг по 4 рубля стоят около 10 рублей, а не 105. Округление удобно для оценки; в точном расчёте округляйте только окончательный результат до требуемой точности.",
         "Estimate to check the decimal point: about 2.5 kg at 4 rubles costs about 10 rubles, not 105. Rounding helps estimation; for an exact calculation round only the final result to the requested precision.")],
    "divisibility": [
        ("Есть 18 яблок и 24 груши. Хотим собрать как можно больше одинаковых подарков без остатка. НОД(18,24) = 6: получится 6 подарков, в каждом 3 яблока и 4 груши.",
         "There are 18 apples and 24 pears. Make as many identical gifts as possible with nothing left over. GCD(18,24) = 6: six gifts each contain 3 apples and 4 pears."),
        ("Один сигнал повторяется каждые 6 минут, другой — каждые 8. Если сейчас они прозвучали вместе, следующее совпадение через НОК(6,8) = 24 минуты. Делители — про одинаковые группы, кратные — про повторяющиеся циклы.",
         "One signal repeats every 6 minutes and another every 8. If they coincide now, the next coincidence is after LCM(6,8) = 24 minutes. Divisors describe equal groups; multiples describe repeating cycles.")],
    "powers": [
        ("Представьте один лист бумаги: после каждого сгиба число слоёв удваивается. В идеальной модели после трёх сгибов слоёв 2 · 2 · 2 = 2³ = 8. Показатель степени — число одинаковых множителей, а не число прибавлений.",
         "Start with one sheet of paper: each fold doubles its layers. In an idealised model, three folds give 2 × 2 × 2 = 2³ = 8 layers. An exponent counts equal factors, not additions."),
        ("Деление пополам — обратное действие: 2⁻³ = 1/8. Для квадратного участка со стороной 3 м площадь 3² = 9 м²; для куба с ребром 3 м объём 3³ = 27 м³. Не смешивайте длину, площадь и объём.",
         "Repeated halving is the inverse operation: 2⁻³ = 1/8. A square with side 3 m has area 3² = 9 m²; a cube with edge 3 m has volume 3³ = 27 m³. Do not mix length, area and volume.")],
    "roots-absolute": [
        ("У квадратного ковра площадь 9 м². Чтобы узнать длину стороны, ищем положительное число, квадрат которого равен 9: √9 = 3 м. Корень «возвращает» нас от площади к стороне.",
         "A square carpet has area 9 m². Its side is the positive number whose square is 9: √9 = 3 m. A square root takes us from area back to side length."),
        ("Дом в 4 км слева от остановки можно обозначить координатой −4, справа — +4. Расстояние до остановки одинаково: |−4| = |4| = 4 км. Модуль убирает направление, но координата его сохраняет; √(x²) = |x|, а не всегда x.",
         "A home 4 km left of a bus stop can have coordinate −4; one on the right has +4. Both are 4 km away: |−4| = |4| = 4 km. Absolute value removes direction, while coordinates retain it; √(x²) = |x|, not always x.")],
    "identities": [
        ("К квадратному участку со стороной 5 м добавили по 2 м в длину и ширину. Новый квадрат 7 × 7 имеет площадь 49 м²: старые 25, две полосы по 10 и маленький угол 4.",
         "A square garden with side 5 m is extended by 2 m in both directions. The new 7 × 7 square has area 49 m²: the old 25, two strips of 10 and a small corner of 4."),
        ("Это и есть (5 + 2)² = 5² + 2 · 5 · 2 + 2². Если забыть две полосы, получится неверное 25 + 4 = 29. Формула (a + b)² описывает четыре части большого квадрата.",
         "This is (5 + 2)² = 5² + 2 × 5 × 2 + 2². Forgetting the strips gives the incorrect 25 + 4 = 29. The formula (a + b)² describes four pieces of the large square.")],
    "factoring": [
        ("Восемь подарков содержат по три карандаша и две ручки. Всего предметов 8 · 3 + 8 · 2 = 8 · (3 + 2) = 40. Общий множитель 8 — число одинаковых подарков, которое удобно вынести за скобки.",
         "Eight gifts each contain three pencils and two pens. There are 8 × 3 + 8 × 2 = 8 × (3 + 2) = 40 objects. Common factor 8 is the number of identical gifts, moved outside the brackets."),
        ("Сокращение дроби — убрать одинаковый множитель сверху и снизу, а не вычеркнуть похожие слагаемые. Если сокращаем (x − 3), условие x ≠ 3 всё равно сохраняется: упрощение не делает деление на ноль допустимым.",
         "Reducing a fraction removes a common factor from numerator and denominator, not similar-looking terms. Cancelling (x − 3) still requires x ≠ 3: simplification does not make division by zero valid.")],
    "linear-equations": [
        ("Такси берёт 5 рублей за посадку и 2 рубля за километр. Поездка стоит 17 рублей: 5 + 2x = 17. Убираем плату за посадку с обеих сторон: 2x = 12; получаем x = 6 км.",
         "A taxi charges 5 rubles to start and 2 per kilometre. A 17-ruble trip gives 5 + 2x = 17. Remove the starting charge from both sides: 2x = 12, so x = 6 km."),
        ("Равенство похоже на весы: одно и то же допустимое действие с обеими чашами сохраняет баланс. Умножать или делить обе части можно лишь так, чтобы не потерять условия задачи; делить на ноль нельзя.",
         "An equation is like balanced scales: the same valid operation on both sides preserves balance. Multiplication and division must retain the problem's conditions; division by zero is forbidden.")],
    "quadratic": [
        ("Прямоугольный огород имеет периметр 8 м и площадь 3 м². Если одна сторона x, другая 4 − x: x(4 − x) = 3, то есть x² − 4x + 3 = 0. Получаем x = 1 или x = 3 — размеры 1 × 3 м.",
         "A rectangular garden has perimeter 8 m and area 3 m². If one side is x, the other is 4 − x: x(4 − x) = 3, or x² − 4x + 3 = 0. Thus x = 1 or 3, giving dimensions 1 × 3 m."),
        ("На графике корни — места встречи параболы с осью x. Два пересечения дают два разных корня, касание — один двукратный, отсутствие пересечений — ни одного действительного. В задаче о длинах дополнительно нужны положительные стороны.",
         "Graphically, roots are where a parabola meets the x-axis. Two intersections give two distinct roots, tangency a double root, and no intersections no real roots. A length problem additionally needs positive sides.")],
    "equation-domain": [
        ("Разделить 12 конфет между x детьми значит получить 12/x конфет на ребёнка. При x = 0 такая запись не имеет смысла. В реальной задаче число детей ещё и целое положительное, хотя алгебраическое выражение допускает другие ненулевые x.",
         "Sharing 12 sweets among x children gives 12/x per child. At x = 0 this is undefined. In the real problem x must also be a positive integer, even though the algebraic expression permits other non-zero x."),
        ("ОДЗ — проверка того, работает ли исходная модель. Возведение в квадрат похоже на стирание знака: и 3, и −3 дают 9. Поэтому после такого действия найденный ответ нужно проверить в исходном уравнении.",
         "The domain checks whether the original model works. Squaring removes a sign: both 3 and −3 give 9. After squaring, test each candidate in the original equation.")],
    "linear-inequalities": [
        ("Есть 20 рублей, вход в музей стоит 5, билет на занятие — 3. Сколько занятий можно оплатить? 5 + 3x ≤ 20 ⇒ x ≤ 5. Знак ≤ разрешает потратить ровно весь бюджет.",
         "You have 20 rubles; admission costs 5 and each activity costs 3. How many can you afford? 5 + 3x ≤ 20 gives x ≤ 5. The ≤ sign allows spending the exact budget."),
        ("Число занятий дополнительно целое и неотрицательное: 0,1,2,3,4,5. В алгебре x ≤ 5 включает и отрицательные числа. Условие |x − 3| ≤ 2 означает «не дальше двух единиц от 3», то есть 1 ≤ x ≤ 5.",
         "The activity count must also be a non-negative integer: 0,1,2,3,4,5. Algebraic x ≤ 5 includes negatives too. The condition |x − 3| ≤ 2 means within two units of 3, hence 1 ≤ x ≤ 5.")],
    "intervals": [
        ("Температура может быть ниже нуля, равна нулю или выше нуля. Между отметками, на которых знак меняется, сохраняется один режим. У дроби (x − 1)/(x + 2) такими границами служат −2 и 1.",
         "Temperature can be below, at or above zero. Between sign-changing boundaries, one regime is retained. For (x − 1)/(x + 2), the boundaries are −2 and 1."),
        ("В каждом промежутке проверяем знак: при x = −3 дробь положительна, при x = 0 отрицательна, при x = 2 положительна. Для ≥ 0 точку 1 включаем, а −2 никогда: там знаменатель равен нулю. Это проверка конкретной дроби, не правило о любой температурной модели.",
         "Test each interval: at x = −3 the fraction is positive, at 0 negative, at 2 positive. For ≥ 0 include 1 but never −2, where the denominator is zero. This verifies this fraction; it is not a rule about every temperature model.")],
    "quadratic-inequalities": [
        ("Для прямоугольного участка с периметром 8 м площадь равна x(4 − x). Хотим не меньше 3 м²: x(4 − x) ≥ 3 ⇒ x² − 4x + 3 ≤ 0. Подходят ширины от 1 до 3 м включительно.",
         "A rectangular plot with perimeter 8 m has area x(4 − x). Require at least 3 m²: x(4 − x) ≥ 3 gives x² − 4x + 3 ≤ 0. Widths from 1 to 3 m, inclusive, work."),
        ("На рисунке нужная часть параболы лежит на оси x или ниже неё. Корни 1 и 3 — границы. При строгом < 0 границы не входят; физическое условие 0 < x < 4 здесь также выполнено.",
         "On the graph, the required part of the parabola is on or below the x-axis. Roots 1 and 3 are its boundaries. Strict < 0 excludes them; the physical condition 0 < x < 4 is also satisfied here.")],
    "function-domain-range": [
        ("Автомат продаёт билет по введённому возрасту и установленному тарифу: допустимому входу соответствует один определённый результат. Функция устроена так же: каждому x из области определения соответствует ровно одно y.",
         "A ticket machine uses the entered age and a fixed tariff to produce one defined price. A function similarly assigns exactly one y to every x in its domain."),
        ("Для квадратного ковра: площадь x ≥ 0, длина стороны y = √x ≥ 0. Область определения — допустимые площади, область значений — возможные длины. Это разные наборы величин; отрицательная площадь в этой модели невозможна.",
         "For a square carpet, area x ≥ 0 gives side y = √x ≥ 0. The domain contains allowable areas; the range contains possible lengths. These are different quantities; negative area is impossible in this model.")],
    "graph-transformations": [
        ("Представьте прозрачную плёнку с параболой y = x². Сдвигаем плёнку вправо на 1 и вниз на 1: вершина из (0;0) переходит в (1;−1), уравнение становится y = (x − 1)² − 1.",
         "Imagine a transparent sheet carrying y = x². Move it 1 unit right and 1 down: the vertex moves from (0,0) to (1,−1), producing y = (x − 1)² − 1."),
        ("Минус внутри скобок означает сдвиг вправо, потому что прежнее значение при x = 0 теперь получается при x = 1. Перемещение всего рисунка не то же самое, что растяжение или отражение.",
         "The minus inside means a shift right because the old input 0 is now reached at x = 1. Moving an entire graph is different from stretching or reflecting it.")],
    "function-properties": [
        ("Цена при покупке по 2 рубля за штуку — y = 2x: прямая через начало. Для такси с посадкой 1 рубль — y = 2x + 1: наклон тот же, но есть начальная плата. Если четыре одинаковые порции делят между x людьми, на каждого приходится 4/x.",
         "At 2 rubles per item the total is y = 2x, a line through the origin. A taxi with starting charge 1 gives y = 2x + 1, the same slope with an initial fee. Sharing four equal portions among x people gives 4/x per person."),
        ("Зеркало поясняет чётность: y = x² симметричен относительно оси y; у y = x³ симметрия относительно начала координат. Реальные количества обычно неотрицательны или целочисленны, поэтому полный математический график шире бытовой модели.",
         "A mirror illustrates evenness: y = x² is symmetric about the y-axis; y = x³ about the origin. Real quantities are often non-negative or integral, so a full mathematical graph extends beyond the everyday model.")],
    "arithmetic-progression": [
        ("Каждую неделю откладываете на 5 рублей больше: 10, 15, 20, 25, 30. Разность соседних взносов постоянна: d = 5. Пятый взнос a₅ = 10 + 4 · 5 = 30 рублей.",
         "Each week you save 5 rubles more: 10, 15, 20, 25, 30. Consecutive differences are constant: d = 5. The fifth payment is a₅ = 10 + 4 × 5 = 30 rubles."),
        ("Между первым и пятым взносами четыре перехода, отсюда n − 1 в формуле. Номер недели — целое число: точки последовательности не означают дополнительные взносы в «полтора недели».",
         "There are four steps between the first and fifth payments, hence n − 1 in the formula. Week numbers are integers: sequence points do not create extra payments at 'one and a half weeks'.")],
    "geometric-progression": [
        ("В идеальной схеме число приглашённых каждый раунд удваивается: 1, 2, 4, 8, 16. Важна не одинаковая прибавка, а одинаковое отношение q = 2. Пятый член 1 · 2⁴ = 16.",
         "In an idealised invitation scheme, the number doubles each round: 1, 2, 4, 8, 16. The ratio q = 2 is constant, not the added amount. The fifth term is 1 × 2⁴ = 16."),
        ("Повторная скидка 10% даёт множитель 0,9 каждый раз, а не вычитание 10% от первоначальной цены. Модель «удваивается всегда» — условие примера, не обещание роста в реальной жизни.",
         "Repeated 10% discounts multiply by 0.9 each time, rather than subtracting 10% of the original price. 'Always doubles' is an assumption of this example, not a promise about real-life growth.")],
    "progression-sums": [
        ("Взносы за пять недель 10 + 15 + 20 + 25 + 30 удобнее сложить попарно: 10 + 30 = 40, 15 + 25 = 40, в середине 20. Итого 100 рублей. Сумма — все взносы, не только последний.",
         "Pair five weekly payments 10 + 15 + 20 + 25 + 30: 10 + 30 = 40, 15 + 25 = 40, with 20 in the middle. Total 100 rubles. The sum counts all payments, not just the last."),
        ("Для количества 1, 2, 4, 8, 16 сумма 31, хотя последний член 16. Бесконечная геометрическая сумма имеет смысл только при |q| < 1: кусочки 1/2 + 1/4 + 1/8 + … заполняют одну целую единицу, а удваивающиеся кусочки не имеют конечной суммы.",
         "The quantities 1, 2, 4, 8, 16 sum to 31 although the last term is 16. An infinite geometric sum is finite only for |q| < 1: pieces 1/2 + 1/4 + 1/8 + … fill one whole, whereas doubling pieces have no finite sum.")],
    "modeling": [
        ("Три одинаковые тетради и доставка за 2 рубля стоят 14. Если цена тетради x рублей, переводим покупку в запись 3x + 2 = 14 и получаем x = 4 рубля.",
         "Three identical notebooks and delivery costing 2 rubles total 14. If one notebook costs x rubles, translate the purchase into 3x + 2 = 14, giving x = 4 rubles."),
        ("Сначала назовите неизвестное и единицу измерения. Затем каждое слагаемое должно обозначать совместимую величину: нельзя складывать рубли с километрами. После решения проверьте покупку и смысл ответа.",
         "First name the unknown and its unit. Each added term must represent compatible quantities: rubles cannot be added to kilometres. After solving, check the purchase and the meaning of the answer.")],
    "motion-work": [
        ("Если идти с постоянной скоростью 4 км/ч, за 1,5 часа пройдёте 4 · 1,5 = 6 км. Два человека, выполняющие работу за 6 и 3 часа, вместе делают 1/6 + 1/3 = 1/2 работы в час: всё за 2 часа.",
         "Walking at a constant 4 km/h for 1.5 hours covers 4 × 1.5 = 6 km. Two workers taking 6 and 3 hours individually have combined rate 1/6 + 1/3 = 1/2 job per hour, finishing in 2 hours."),
        ("Складываются производительности, а не времена. Эти формулы предполагают постоянные скорости и независимую совместную работу без помех; в реальности условия могут быть другими.",
         "Add rates, not completion times. These formulas assume constant speeds and independent work without interference; real conditions may differ.")],
    "percentages": [
        ("Куртка стоила 100 рублей. Скидка 20% оставляет 80; последующая наценка 10% берётся уже от 80 и добавляет 8. Итог 88 рублей — на 12% меньше исходной цены.",
         "A jacket costs 100 rubles. A 20% discount leaves 80; a later 10% increase applies to 80, adding 8. The result is 88 rubles, 12% below the original price."),
        ("Поэтому проценты последовательных изменений не складывают: 100 · 0,8 · 1,1 = 88. Каждый раз уточняйте, какое число сейчас принято за 100%.",
         "Do not add successive percentage changes: 100 × 0.8 × 1.1 = 88. Always identify which current amount represents 100%.")],
    "trig-identities": [
        ("Лестница длиной 5 м стоит под углом к полу. Если её верх поднялся на 3 м, горизонтальное расстояние до стены 4 м. Для угла у пола sin = 3/5, cos = 4/5: это доли одной и той же гипотенузы.",
         "A 5 m ladder leans against a wall. If its top is 3 m high, its foot is 4 m from the wall. For the ground angle, sin = 3/5 and cos = 4/5: fractions of the same hypotenuse."),
        ("Равенство (3/5)² + (4/5)² = 1 — теорема Пифагора, разделённая на 5². На единичной окружности cos и sin становятся координатами точки; это распространяет смысл на любые углы.",
         "The equality (3/5)² + (4/5)² = 1 is Pythagoras divided by 5². On the unit circle, cos and sin become point coordinates, extending the idea to all angles.")],
    "trig-values": [
        ("Колесо радиуса R повернулось на угол α радиан: точка на ободе прошла дугу Rα. Один радиан — поворот, при котором дуга по длине равна радиусу; половина оборота — π радиан = 180°.",
         "A wheel of radius R rotates through α radians: a rim point travels arc length Rα. One radian makes the arc as long as the radius; half a turn is π radians = 180°."),
        ("При R = 6 и повороте 60° = π/3 дуга равна 2π. Градусы нельзя подставлять в Rα без перевода в радианы. На круге знаки sin и cos следуют знакам вертикальной и горизонтальной координат.",
         "With R = 6 and rotation 60° = π/3, the arc is 2π. Convert degrees to radians before using Rα. Sine and cosine signs follow the vertical and horizontal coordinate signs.")],
    "trig-formulas": [
        ("Повернули стрелку сначала на 30°, затем ещё на 30°: общий поворот 60°. Но высота её конца не удваивается: sin 30° = 1/2, а sin 60° = √3/2, не 1.",
         "Rotate a pointer by 30° and then another 30°: the total is 60°. Its tip's height does not double: sin 30° = 1/2 but sin 60° = √3/2, not 1."),
        ("Координаты конца меняются одновременно. Формула sin(α + β) учитывает и вертикальную, и горизонтальную проекции; поэтому sin(α + β) не равен просто sin α + sin β.",
         "Both tip coordinates change together. The sine addition formula uses horizontal and vertical projections, so sin(α + β) is not simply sin α + sin β.")],
    "trig-equations": [
        ("Точка на колесе единичного радиуса имеет высоту 1/2 над центром дважды за оборот: при 30° и 150°. Поэтому sin x = 1/2 имеет не один, а два семейства решений.",
         "A point on a unit-radius wheel is 1/2 above its centre twice per turn: at 30° and 150°. Thus sin x = 1/2 has two solution families, not just one."),
        ("После полного оборота положение повторяется: к каждому углу прибавляем 2πk, k — целое. Это геометрическое объяснение периодичности; углы в формулах записываются в радианах.",
         "After a full turn the position repeats: add 2πk to each angle, with integer k. This explains periodicity geometrically; formula angles use radians.")],
    "trig-selection": [
        ("Для sin x = 1/2 на одном обороте 0 ≤ x ≤ 2π оставляем только π/6 и 5π/6. Решения за пределами этого оборота существуют, но не отвечают заданному ограничению.",
         "For sin x = 1/2 within one turn 0 ≤ x ≤ 2π, retain only π/6 and 5π/6. Other solutions exist but do not meet this restriction."),
        ("Это как выбирать отправления автобуса только внутри указанного промежутка времени: сначала все повторяющиеся моменты, затем фильтр по границам. Для открытого промежутка события ровно на границе не включают.",
         "It is like selecting bus departures within a time window: first list the repeated times, then filter by the boundaries. An open interval excludes events exactly at its endpoints.")],
    "log-definition": [
        ("Одна условная единица каждый шаг удваивается: 1 → 2 → 4 → 8. Вопрос «сколько шагов до 8?» — log₂ 8 = 3. Степень говорит, какой результат получится; логарифм — сколько таких умножений требуется.",
         "One unit doubles each step: 1 → 2 → 4 → 8. 'How many steps to reach 8?' is log₂ 8 = 3. A power gives the result; a logarithm gives the required number of such multiplications."),
        ("Если целого числа шагов нет, логарифм может быть дробным. В действительных числах аргумент положителен, основание положительно и не равно 1: повторение множителя 1 никогда не изменяет результат.",
         "When the step count is not integral, the logarithm may be fractional. For real logarithms the argument is positive and the base is positive and not 1: multiplying by 1 never changes the result.")],
    "log-properties": [
        ("Чтобы получить 8 = 2³, нужно три удвоения; 4 = 2² — два. Получить произведение 8 · 4 = 32 = 2⁵ — пять: log₂(8 · 4) = log₂ 8 + log₂ 4 = 5.",
         "Reaching 8 = 2³ takes three doublings; 4 = 2² takes two. Their product 8 × 4 = 32 = 2⁵ takes five: log₂(8 × 4) = log₂ 8 + log₂ 4 = 5."),
        ("Складываются показатели при умножении, поэтому логарифм произведения становится суммой. Для суммы 8 + 4 такого правила нет: log₂ 12 не равен 3 + 2. Условия положительности каждого логарифмируемого множителя сохраняются.",
         "Exponents add under multiplication, so a product's logarithm becomes a sum. There is no such rule for 8 + 4: log₂ 12 is not 3 + 2. Each factor whose logarithm is taken must remain positive.")],
    "exponential-equations": [
        ("Количество в учебной модели удваивается за каждый час: через t часов N = 2ᵗ. Чтобы достичь 8 единиц, решаем 2ᵗ = 8 и получаем t = 3 часа.",
         "An educational model doubles a quantity every hour: after t hours N = 2ᵗ. To reach 8 units, solve 2ᵗ = 8, giving t = 3 hours."),
        ("График показывает пересечение кривой роста и горизонтального уровня N = 8. Для половинного уменьшения база 1/2 задаёт убывание: направление сравнения меняется. Реальный рост не обязан оставаться экспоненциальным бесконечно.",
         "The graph shows the growth curve crossing horizontal level N = 8. A halving base 1/2 gives decrease and reverses comparisons. Actual growth need not remain exponential forever.")],
    "plane-figures": [
        ("В треугольной крыше высота — кратчайший путь от вершины к прямой основания, строго под 90°. Медиана ведёт к середине основания, а биссектриса делит угол крыши пополам: это три разных задания для отрезка.",
         "In a triangular roof, the altitude is the shortest route from the vertex to the base line, exactly at 90°. A median goes to the base midpoint; a bisector halves the roof angle. These are three different tasks for a segment."),
        ("Они совпадают у равнобедренной крыши при проведении к основанию, но не у любого треугольника. На схеме отметки середины и прямого угла задают свойства: одной похожей картинки недостаточно для доказательства.",
         "They coincide in an isosceles roof when drawn to its base, but not in every triangle. Midpoint and right-angle marks state properties; a similar-looking picture alone is not proof.")],
    "right-triangle": [
        ("Лестницу длиной 5 м поставили так, что её низ в 4 м от вертикальной стены. При прямом угле между стеной и полом высота 3 м, потому что 3² + 4² = 5².",
         "A 5 m ladder has its foot 4 m from a vertical wall. When wall and ground form a right angle, the height is 3 m because 3² + 4² = 5²."),
        ("Лестница — гипотенуза, стена и пол — катеты. По тем же расчётам находят диагональ прямоугольного экрана или кратчайшее расстояние по прямой. Теорема требует прямого угла, а не любого треугольника.",
         "The ladder is the hypotenuse; wall and floor form the legs. The same calculation finds a rectangular screen's diagonal or straight-line distance. The theorem requires a right angle, not just any triangle.")],
    "plane-areas": [
        ("Прямоугольник 4 × 3 м покрывают 12 квадратами 1 × 1 м. Диагональ делит его на два равных треугольника: площадь каждого 4 · 3 / 2 = 6 м².",
         "A 4 × 3 m rectangle fits twelve 1 × 1 m squares. Its diagonal splits it into two equal triangles, each with area 4 × 3 / 2 = 6 m²."),
        ("Если наклонить верхнюю сторону параллелограмма, сохраняя основание и перпендикулярную высоту, площадь не изменится. Длина наклонной стороны — не высота. Краску покупают по площади (м²), плинтус — по периметру (м).",
         "Slanting a parallelogram while keeping its base and perpendicular height leaves the area unchanged. The sloping side is not the height. Paint is bought by area (m²); edging by perimeter (m).")],
    "circle-theorems": [
        ("Обод колеса — окружность, вся круглая крышка — круг. Для обода важна длина 2πR, для количества краски на крышке — площадь πR². Радиус R идёт от центра к краю.",
         "A wheel's rim is a circumference; an entire round lid is a disk. Rim material uses length 2πR, while paint for the lid uses area πR². Radius R runs from centre to edge."),
        ("Натянутая нить, касающаяся круглого ролика в одной точке, лежит по касательной. Радиус к этой точке перпендикулярен нити. Вписанный угол смотрит на ту же дугу с края и вдвое меньше центрального.",
         "A taut thread touching a round roller at one point follows a tangent. The radius to that point is perpendicular to the thread. An inscribed angle views the same arc from the rim and is half the central angle.")],
    "similarity": [
        ("Увеличили фотографию в 2 раза по ширине и высоте: формы и углы сохранились, каждое расстояние удвоилось. Но бумаги понадобится в 4 раза больше, потому что площадь умножилась на 2².",
         "Enlarge a photo by factor 2 in both width and height: shape and angles remain, and each length doubles. Paper area grows by 2² = 4, not 2."),
        ("Так же работают масштаб карты и подобные треугольники. Растяжение только по ширине не сохраняет подобие: соответствующие стороны должны меняться в одной пропорции.",
         "Map scales and similar triangles work the same way. Stretching only the width does not preserve similarity: corresponding sides must share one scale factor.")],
    "prism-cylinder": [
        ("Прямоугольная коробка с основанием 4 × 3 см и высотой 5 см имеет объём 12 · 5 = 60 см³. Представьте пять слоёв по 12 кубиков со стороной 1 см.",
         "A rectangular box with 4 × 3 cm base and height 5 cm has volume 12 × 5 = 60 cm³. Imagine five layers of twelve unit cubes."),
        ("У круглой банки площадь основания πr² и объём πr²h. Для r = 3 см, h = 6 см это 54π см³. Ёмкость — объём, металл на стенки — площадь поверхности; 1 литр = 1000 см³. В формуле объёма нужна перпендикулярная высота.",
         "A round can has base area πr² and volume πr²h. With r = 3 cm and h = 6 cm this is 54π cm³. Capacity is volume; wall material is surface area; 1 litre = 1000 cm³. Use perpendicular height for volume.")],
    "pyramid-cone": [
        ("Конус и цилиндр с одинаковыми основанием и высотой вмещают разное количество: идеальный конус имеет треть объёма цилиндра. При r = 3, h = 4 объёмы 12π и 36π кубических единиц.",
         "A cone and a cylinder with the same base and height hold different amounts: an ideal cone has one third of the cylinder's volume. For r = 3 and h = 4 their volumes are 12π and 36π cubic units."),
        ("Для конического колпака нужны две разные длины: высота h идёт внутри перпендикулярно основанию, образующая l — по наклонной поверхности. При этих размерах l = √(3² + 4²) = 5; нельзя подставлять 5 вместо h в объём.",
         "A cone-shaped cap has two lengths: height h is perpendicular to the base inside; slant height l lies along its side. Here l = √(3² + 4²) = 5; do not replace h by 5 in the volume formula.")],
    "sphere-cube": [
        ("Ребро кубической коробки 2 см: внутри помещаются 8 единичных кубиков, объём 2³ = 8 см³. Для упаковочной бумаги нужны шесть граней по 4 см²: 6 · 2² = 24 см².",
         "A cube-shaped box with 2 cm edges holds eight unit cubes, volume 2³ = 8 cm³. Wrapping needs six faces of 4 cm²: 6 × 2² = 24 cm²."),
        ("Сфера — только поверхность мяча, шар — весь объём внутри и поверхность. Для радиуса 3 см площадь сферы 36π см², объём шара 36π см³: числа совпали, но единицы и физический смысл разные.",
         "A sphere is a ball's surface; a solid ball includes its interior. At radius 3 cm the surface area is 36π cm² and volume 36π cm³: equal numerical coefficients, but different units and meanings.")],
    "solid-perpendiculars": [
        ("Фонарь находится над землёй в точке A, а A₀ — его вертикальная проекция. Наклонный путь AP к точке P на земле и его «тень» A₀P различаются по длине; тень лежит в плоскости земли.",
         "A lamp is at A above the ground, with vertical projection A₀. The sloping segment AP to ground point P differs from its 'shadow' A₀P, which lies in the ground plane."),
        ("Если прямая на земле проходит через P и перпендикулярна проекции A₀P, она перпендикулярна и AP — теорема о трёх перпендикулярах. Это утверждение о пространстве и ортогональной проекции, а не о произвольной тени от косого света.",
         "If a ground line through P is perpendicular to projection A₀P, it is also perpendicular to AP, by the three-perpendiculars theorem. This uses an orthogonal projection in space, not any shadow from oblique light.")],
    "derivative-table": [
        ("Средняя скорость — весь пройденный путь, делённый на время. Показание спидометра — скорость сейчас. Производная расстояния по времени описывает именно мгновенное изменение.",
         "Average speed divides total travelled distance by time. A speedometer shows speed now. The derivative of distance with respect to time describes instantaneous change."),
        ("В модели s(t) = t² м при t ≥ 0 с скорость s′(t) = 2t м/с: на второй секунде 4 м/с, хотя за первые 2 секунды средняя скорость 4/2 = 2 м/с. Для формул производных тригонометрические аргументы измеряют в радианах.",
         "In the model s(t) = t² metres for t ≥ 0 seconds, speed is s′(t) = 2t m/s. At 2 seconds it is 4 m/s, while the average over the first 2 seconds is 4/2 = 2 m/s. Trigonometric derivative formulas use radians.")],
    "derivative-rules": [
        ("Если два счётчика показывают количества u(t) и v(t), скорость изменения суммы — u′ + v′. Но площадь прямоугольника u(t)v(t) меняется при изменении обеих сторон: (uv)′ = u′v + uv′.",
         "If two counters show u(t) and v(t), their sum changes at rate u′ + v′. A rectangle's area u(t)v(t), however, changes with both sides: (uv)′ = u′v + uv′."),
        ("Для сторон u(t) = t, v(t) = 2t площадь 2t² и скорость её изменения 4t, а не u′v′ = 2. Произведение производных не является производной произведения; единицы изменения площади — квадратные единицы за единицу времени.",
         "For sides u(t) = t and v(t) = 2t, area is 2t² and its rate is 4t, not u′v′ = 2. A product of derivatives is not the derivative of a product; area rate uses square units per time unit.")],
    "chain-rule": [
        ("Объём куба V = a³ зависит от ребра a, а ребро — от времени: a(t) = 2t. Изменение проходит через две связи: время → длина → объём.",
         "A cube's volume V = a³ depends on edge a, which depends on time: a(t) = 2t. Change passes through two links: time → length → volume."),
        ("Поэтому dV/dt = (dV/da) · (da/dt) = 3a² · 2 = 24t². Если забыть внутреннюю скорость 2, результат будет вдвое меньше. Это правило для дифференцируемых зависимостей.",
         "Thus dV/dt = (dV/da) × (da/dt) = 3a² × 2 = 24t². Forgetting inner rate 2 halves the result. The rule requires differentiable dependencies.")],
    "derivative-point": [
        ("Касательная похожа на прямую линейку, приложенную к плавной кривой в одной точке. Её наклон показывает, насколько быстро y меняется при небольшом изменении x около этой точки.",
         "A tangent is like a straight ruler laid against a smooth curve at one point. Its slope shows how quickly y changes for small changes in x near that point."),
        ("Для y = x² в точке (1;1) наклон 2: касательная y = 2x − 1. При x = 1,1 она даёт 1,2, а кривая 1,21: линейная оценка близка, но не равна функции вдали от точки. «Касается» не значит «совпадает с графиком».",
         "For y = x² at (1,1), slope is 2 and tangent y = 2x − 1. At x = 1.1 the tangent gives 1.2, the curve 1.21: a close local approximation, not exact away from the point. Touching does not mean matching the whole graph.")],
    "extrema": [
        ("Профиль дороги помогает различать подъём и спуск. На подъёме высота растёт, на спуске падает. На гладкой вершине уклон на миг нулевой, затем рост сменяется убыванием — местный максимум.",
         "A road profile distinguishes uphill from downhill: height rises uphill and falls downhill. At a smooth summit the slope is briefly zero, then rise becomes fall, a local maximum."),
        ("Но горизонтальный участок касательной не гарантирует вершину: y = x³ в нуле продолжает возрастать, хотя производная равна нулю. Смотрите на смену знака производной, а не только на равенство f′ = 0.",
         "A horizontal tangent does not guarantee a summit: y = x³ keeps increasing through zero although its derivative is zero there. Check the derivative's sign change, not just f′ = 0.")],
    "segment-extrema": [
        ("Ищем самую высокую точку только на участке дороги от A до B. Она может оказаться не на внутренней вершине, а прямо в начале или в конце маршрута.",
         "Find the highest point only on a road segment from A to B. It may be an interior summit or the route's start or end."),
        ("Для y = (x − 2)² − 1 на [0;3] проверяем x = 0, 2, 3: значения 3, −1, 0. Минимум −1 при x = 2, максимум 3 при x = 0. Одного поиска критических точек недостаточно: границы тоже кандидаты.",
         "For y = (x − 2)² − 1 on [0,3], check x = 0,2,3, obtaining 3,−1,0. The minimum −1 is at 2; the maximum 3 at 0. Critical points alone are insufficient; endpoints are candidates too.")],
    "counting": [
        ("Из трёх друзей А, Б, В выбираем двоих для команды: АБ, АВ, БВ — три варианта, порядок не важен. Но если нужны капитан и помощник, АБ и БА — разные назначения: вариантов шесть.",
         "Choose two of three friends A,B,C for a team: AB, AC, BC, three choices without order. If choosing a captain and assistant, AB and BA assign different roles: six possibilities."),
        ("Это различие сочетаний и размещений. Чтобы расставить всех троих в очередь, есть 3 · 2 · 1 = 6 перестановок. Уточняйте, важен ли порядок и разрешены ли повторения: одни и те же друзья не могут занять две роли одновременно в этом примере.",
         "This distinguishes combinations from ordered selections. Queuing all three gives 3 × 2 × 1 = 6 permutations. Ask whether order matters and repetition is allowed; here one friend cannot occupy both roles.")],
    "probability": [
        ("В непрозрачном мешке три красных и две синих одинаковых на ощупь фишки. При равновероятном выборе одной фишки вероятность красной 3/5: три подходящих исхода из пяти.",
         "An opaque bag holds three red and two blue tokens identical to the touch. With an equally likely draw of one token, red has probability 3/5: three favourable outcomes out of five."),
        ("Это не обещает ровно три красных в каждых пяти попытках. Для двух извлечений с возвратом вероятность двух красных (3/5)² = 9/25; без возврата 3/5 · 2/4 = 3/10. Во втором случае шансы зависят от первого результата.",
         "This does not promise exactly three reds in every five trials. Two draws with replacement give red twice with probability (3/5)² = 9/25; without replacement, 3/5 × 2/4 = 3/10. In the latter case the second chance depends on the first result.")],
    "factorials": [
        ("Четыре разные книги ставим на полку: для первой позиции четыре выбора, затем три, два и один. Всего 4! = 4 · 3 · 2 · 1 = 24 порядка.",
         "Arrange four different books on a shelf: four choices for the first position, then three, two and one. There are 4! = 4 × 3 × 2 × 1 = 24 orders."),
        ("Если выбираем две книги без учёта порядка, пары АБ и БА — одна покупка. Поэтому из 4 · 3 упорядоченных выборов каждый посчитан 2! раз: C₄² = 12/2 = 6. Нулевой факториал 0! = 1 согласуется с единственным способом выбрать ничего.",
         "When choosing two books without order, AB and BA are one purchase. Each unordered pair is counted 2! times among 4 × 3 ordered choices, so C₄² = 12/2 = 6. The value 0! = 1 matches the single way to select nothing.")],
    "vector-coordinates": [
        ("От дома прошли 3 квартала на восток и 4 на север. Вектор перемещения (3;4) описывает направление и величину. Его длина 5 кварталов — расстояние по прямой, хотя по улицам пройдено 7.",
         "Walk 3 blocks east and 4 north from home. Displacement vector (3,4) gives direction and magnitude. Its length is 5 blocks straight-line, although the street route totals 7."),
        ("Вектор не привязан к одному дому: такую же стрелку можно перенести параллельно. Но при сравнении координат используйте те же оси и единицы; длина и сумма пройденных участков — разные величины.",
         "A vector is not tied to one house: translate the same arrow parallel to itself. Use the same axes and units when comparing coordinates; displacement length and travelled route length are different quantities.")],
    "dot-product": [
        ("Векторы можно представить направлениями на плане. Если один идёт вдоль улицы, другой строго поперёк, угол 90° и их скалярное произведение равно нулю: cos 90° = 0.",
         "Vectors can represent directions on a map. If one goes along a street and another directly across it, the angle is 90° and their dot product is zero because cos 90° = 0."),
        ("У a = (3;1) и b = (−1;3) произведение 3 · (−1) + 1 · 3 = 0 — независимая проверка прямого угла. Положительный результат означает острый угол, отрицательный — тупой; это описание угла для ненулевых векторов.",
         "For a = (3,1) and b = (−1,3), the product 3 × (−1) + 1 × 3 = 0 independently verifies the right angle. A positive product means an acute angle, a negative one obtuse; this angle description requires non-zero vectors.")],
    "midpoint-collinearity": [
        ("Два дома имеют координаты A(1;1) и B(5;3). Точка посередине прямого отрезка между ними — M((1 + 5)/2; (1 + 3)/2) = (3;2). Усредняем каждую координату отдельно.",
         "Two houses have coordinates A(1,1) and B(5,3). The straight segment's midpoint is M((1 + 5)/2,(1 + 3)/2) = (3,2). Average each coordinate separately."),
        ("Шаг (4;2) направлен так же, как (2;1): один вектор вдвое другого, они коллинеарны. Отрицательный множитель разворачивает направление. Середина по прямой не обязательно совпадает с серединой маршрута по извилистой дороге.",
         "A step (4,2) points the same way as (2,1): one vector is twice the other, so they are collinear. A negative multiplier reverses direction. A straight-line midpoint need not be a winding route's halfway point.")],
    "parameters": [
        ("Участок с периметром 8 м может иметь разные площади p. Уравнение x(4 − x) = p превращается в x² − 4x + p = 0: p — выбранная площадь, x — искомая сторона.",
         "A plot with perimeter 8 m can have different areas p. The equation x(4 − x) = p becomes x² − 4x + p = 0: p is the chosen area and x the unknown side."),
        ("При 0 < p < 4 есть два положительных значения x (перестановка сторон); при p = 4 только x = 2, квадрат; при p > 4 такого участка нет. Алгебраические корни для p ≤ 0 не дают прямоугольник с положительными сторонами: параметр требует проверки смысла.",
         "For 0 < p < 4 there are two positive x-values, interchanging the sides. At p = 4 only x = 2, a square; at p > 4 no such plot exists. Algebraic roots for p ≤ 0 do not give a rectangle with positive sides; interpret the parameter.")],
    "parameter-tangency": [
        ("Приложите прямую линейку к плавной параболе. При небольшом сдвиге линейка может пересекать кривую дважды, лишь касаться или не встречать её. Параметр задаёт этот сдвиг.",
         "Place a straight ruler against a smooth parabola. Moving it slightly may produce two crossings, one contact or none. The parameter controls this shift."),
        ("Для y = x² и y = 2x + k касание при k = −1 в (1;1): (x − 1)² = 0. Один геометрический контакт соответствует двукратному корню. У произвольных кривых один общий пункт сам по себе не доказывает касание.",
         "For y = x² and y = 2x + k, tangency occurs at k = −1 and (1,1): (x − 1)² = 0. One geometric contact corresponds to a double root. For arbitrary curves, a single intersection alone does not prove tangency.")],
    "sequences": [
        ("Записи шагомера за дни 1, 2, 3 — последовательность: каждому номеру дня соответствует одно число. Если в учебном плане каждый день добавлять ровно 100 шагов, правило aₙ = a₁ + 100(n − 1) определит все дни.",
         "Pedometer readings for days 1,2,3 form a sequence: each day number has a value. If an exercise plan adds exactly 100 steps daily, the rule aₙ = a₁ + 100(n − 1) specifies every day."),
        ("Но три прошлых записи сами не обещают такой же завтрашний результат: разные правила могут совпасть в первых нескольких точках. Продолжение нужно обосновать заданной формулой, рекурсией или дополнительным условием.",
         "Three past readings do not promise the same pattern tomorrow: different rules can agree at the first few points. Justify continuation using a given formula, recurrence or additional condition.")],
    "modular-cycles": [
        ("На часах после 12 снова 1. Если сейчас 10, через 5 часов стрелка покажет 3: 10 + 5 = 15, остаток при делении на 12 равен 3. Счёт идёт по кругу.",
         "A clock returns to 1 after 12. Starting at 10, five hours later it shows 3: 10 + 5 = 15 has remainder 3 modulo 12. Counting wraps around."),
        ("Для последней цифры степеней 7 круг другой: 7 → 9 → 3 → 1 → 7. Уточняйте модуль и начало цикла; в записи остатков часов 0 соответствует отметке 12, а не новому часу вне цикла.",
         "Last digits of powers of 7 use another cycle: 7 → 9 → 3 → 1 → 7. Identify the modulus and cycle start; clock remainder 0 corresponds to mark 12, not an extra hour outside the cycle.")],
}


def payload() -> dict:
    return {key: {"ru": [pair[0] for pair in pairs], "en": [pair[1] for pair in pairs]}
            for key, pairs in EXPLANATIONS.items()}
