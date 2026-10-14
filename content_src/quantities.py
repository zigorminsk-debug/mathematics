"""quantities.py — размерности, единицы измерения и разбор ответов с единицами.

Это ядро предмета «физика». Без него нельзя ни проверить ответ ученика
(10 Н ≠ 10 кг, 10 см ≠ 10 м, 36 км/ч = 10 м/с), ни гарантировать, что формула в
задании физически правильна.

Состав
------
1. ``Dim`` — вектор показателей по семи основным единицам СИ (m, kg, s, A, K,
   mol, cd). Сложение и вычитание требуют одинаковой размерности (поэтому
   ``s = v0*t + a*t`` отвергается), умножение и деление перемножают показатели.
2. ``Unit`` — единица: символ, синонимы (латиница и кириллица), множитель к СИ,
   смещение для температур, признак «можно приставку СИ».
3. ``parse_unit`` — белый список единиц с разбором составных выражений
   («км/ч», «кг·м/с²», «Дж/(кг·К)», «мкФ»). Никакого eval: только грамматика
   единиц, целые степени, посторонние символы отвергаются.
4. ``Q`` — величина: точное значение (Fraction) и единица; перевод в СИ и в
   другую единицу той же размерности.
5. ``check_answer`` — контракт проверки ответа: тип ответа, требуемая или
   необязательная единица, допуск/округление, отдельные диагнозы «не та
   размерность» и «единица не указана» (это и есть физическая суть проверки).
6. ``eval_model``/``dim_balance`` — вычисление формулы задания при заданных
   данных и проверка баланса размерностей. Благодаря этому ответ в банке не
   «набит руками», а выведен из самой модели задания и проверен независимо.

Все числа — :class:`fractions.Fraction`: 0,1 + 0,2 ровно равно 0,3, а границы
округления (0,05 ± 0,005) сравниваются точно, без двоичных сюрпризов.
"""

from __future__ import annotations

import re
from fractions import Fraction

from decimal import Decimal, localcontext

__all__ = [
    "DIMS", "Dim", "Unit", "Q", "UNITS", "PREFIXES", "CONVENTIONS",
    "QuantityError", "ModelError", "parse_dim", "parse_unit", "unit_of",
    "parse_number", "format_number", "format_quantity", "sci_parts",
    "split_number_unit", "check_answer", "CheckResult", "eval_model",
    "dim_balance", "units_payload",
]

# --------------------------------------------------------------------------- #
#  Служебные таблицы / helper tables
# --------------------------------------------------------------------------- #

DIMS = ("m", "kg", "s", "A", "K", "mol", "cd")

_DIM_NAMES = {
    "ru": {"m": "м", "kg": "кг", "s": "с", "A": "А", "K": "К", "mol": "моль", "cd": "кд"},
    "en": {"m": "m", "kg": "kg", "s": "s", "A": "A", "K": "K", "mol": "mol", "cd": "cd"},
}

SUPERSCRIPTS = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
                "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻"}
_DIGITS_FROM_SUPER = {value: key for key, value in SUPERSCRIPTS.items()}


class QuantityError(ValueError):
    """Некорректная единица, размерность или число — всегда ошибка сборки."""


class ModelError(ValueError):
    """Формула задания не проходит размерностную или численную проверку."""


# --------------------------------------------------------------------------- #
#  Размерность / dimension
# --------------------------------------------------------------------------- #

class Dim:
    """Вектор показателей степеней по основным единицам СИ."""

    __slots__ = ("exps",)

    def __init__(self, exps):
        exps = tuple(int(e) for e in exps)
        if len(exps) != len(DIMS):
            raise QuantityError("dimension vector must have 7 components")
        self.exps = exps

    # --- построение -------------------------------------------------------- #
    @staticmethod
    def base(symbol: str) -> "Dim":
        if symbol not in DIMS:
            raise QuantityError(f"unknown base dimension: {symbol}")
        return Dim([1 if item == symbol else 0 for item in DIMS])

    @staticmethod
    def none() -> "Dim":
        return Dim([0] * len(DIMS))

    # --- алгебра ----------------------------------------------------------- #
    def __mul__(self, other: "Dim") -> "Dim":
        return Dim([a + b for a, b in zip(self.exps, other.exps)])

    def __truediv__(self, other: "Dim") -> "Dim":
        return Dim([a - b for a, b in zip(self.exps, other.exps)])

    def __pow__(self, power: int) -> "Dim":
        return Dim([a * int(power) for a in self.exps])

    def __eq__(self, other) -> bool:
        return isinstance(other, Dim) and self.exps == other.exps

    def __hash__(self) -> int:
        return hash(self.exps)

    def __repr__(self) -> str:
        return f"Dim({self.signature()})"

    # --- представление ----------------------------------------------------- #
    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def signature(self) -> str:
        """Машинная подпись: ``kg·m^2/s^3`` (латиница, годится для JSON)."""
        top, bottom = [], []
        for symbol, power in zip(DIMS, self.exps):
            if power == 0:
                continue
            bucket = top if power > 0 else bottom
            bucket.append(symbol if abs(power) == 1 else f"{symbol}^{abs(power)}")
        left = "·".join(top) or "1"
        if not bottom:
            return left
        return f"{left}/{bottom[0]}" if len(bottom) == 1 else f"{left}/({'·'.join(bottom)})"

    def display(self, lang: str = "ru") -> str:
        """Подпись для ученика: ``м/с²`` / ``m/s²``."""
        names = _DIM_NAMES["en" if lang == "en" else "ru"]
        top, bottom = [], []
        for symbol, power in zip(DIMS, self.exps):
            if power == 0:
                continue
            name = names[symbol]
            if abs(power) != 1:
                name += "".join(SUPERSCRIPTS[c] for c in str(abs(power)))
            (top if power > 0 else bottom).append(name)
        left = "·".join(top) or "1"
        if not bottom:
            return left
        return f"{left}/{bottom[0]}" if len(bottom) == 1 else f"{left}/({'·'.join(bottom)})"


# --------------------------------------------------------------------------- #
#  Единицы измерения / units
# --------------------------------------------------------------------------- #

class Unit:
    """Единица измерения: множитель к СИ, размерность, синонимы, приставки."""

    __slots__ = ("symbol", "_dim", "_dim_text", "factor", "offset", "aliases",
                 "prefixable", "ru", "en")

    def __init__(self, symbol, dim, factor=1, aliases=(), prefixable=False,
                 ru=None, en=None, offset=0):
        self.symbol = symbol
        if isinstance(dim, Dim):
            self._dim, self._dim_text = dim, None
        else:
            # размерность разбирается лениво: таблица единиц объявлена выше
            # разбора выражений единиц и не должна зависеть от порядка в файле
            self._dim, self._dim_text = None, dim
        self.factor = factor if isinstance(factor, Fraction) else Fraction(factor)
        self.offset = offset if isinstance(offset, Fraction) else Fraction(offset)
        self.aliases = tuple(aliases)
        self.prefixable = bool(prefixable)
        # пустая подпись допустима: у безразмерной величины «1» подписи нет
        self.ru = symbol if ru is None else ru
        self.en = symbol if en is None else en

    @property
    def dim(self) -> "Dim":
        if self._dim is None:
            self._dim = parse_dim(self._dim_text)
        return self._dim

    def display(self, lang: str = "ru") -> str:
        return self.en if lang == "en" else self.ru

    def to_json(self) -> dict:
        return {
            "symbol": self.symbol, "ru": self.ru, "en": self.en,
            "dim": self.dim.signature(),
            "factor": str(self.factor.numerator) if self.factor.denominator == 1 else
                      f"{float(self.factor):.12g}",
            "factorExact": f"{self.factor.numerator}/{self.factor.denominator}",
            "offset": float(self.offset), "prefixable": self.prefixable,
            "aliases": list(self.aliases),
        }

    def __repr__(self) -> str:
        return f"Unit({self.symbol})"


#: приставки СИ: (кириллица, латиница, множитель)
PREFIXES = (
    ("п", "p", Fraction(1, 10 ** 12)), ("н", "n", Fraction(1, 10 ** 9)),
    ("мк", "µ", Fraction(1, 10 ** 6)), ("мк", "u", Fraction(1, 10 ** 6)),
    ("м", "m", Fraction(1, 1000)), ("с", "c", Fraction(1, 100)),
    ("д", "d", Fraction(1, 10)), ("к", "k", Fraction(1000)),
    ("М", "M", Fraction(10 ** 6)), ("Г", "G", Fraction(10 ** 9)),
)

_UNIT_TABLE = [
    # --- основные единицы СИ --------------------------------------------- #
    Unit("m", "m", 1, ("м", "метр", "метра", "метров"), True, "м", "m"),
    Unit("kg", "kg", 1, ("кг", "килограмм", "килограмма", "килограммов"), True, "кг", "kg"),
    Unit("s", "s", 1, ("с", "сек", "секунда", "секунды", "секунд"), True, "с", "s"),
    Unit("A", "A", 1, ("А", "ампер", "ампера", "амперов"), True, "А", "A"),
    Unit("K", "K", 1, ("К", "кельвин", "кельвина", "кельвинов"), True, "К", "K"),
    Unit("mol", "mol", 1, ("моль", "молей", "моля"), True, "моль", "mol"),
    Unit("cd", "cd", 1, ("кд", "кандела"), True, "кд", "cd"),
    # --- внесистемные, но школьные --------------------------------------- #
    Unit("g", "kg", Fraction(1, 1000), ("г", "грамм", "грамма", "граммов"), True, "г", "g"),
    Unit("t", "kg", 1000, ("т", "тонна", "тонны", "тонн"), False, "т", "t"),
    Unit("min", "s", 60, ("мин", "минута", "минуты", "минут"), False, "мин", "min"),
    Unit("h", "s", 3600, ("ч", "час", "часа", "часов"), False, "ч", "h"),
    Unit("day", "s", 86400, ("сут", "сутки", "суток"), False, "сут", "сут"),
    Unit("l", "m^3", Fraction(1, 1000), ("л", "L", "литр", "литра", "литров"), True, "л", "l"),
    Unit("eV", "kg·m^2/s^2", Fraction(16, 10 ** 20), ("эВ", "эв"), False, "эВ", "eV"),
    Unit("u", "kg", Fraction(166, 10 ** 29), ("а.е.м.", "аем"), False, "а.е.м.", "u"),
    Unit("degC", "K", 1, ("°C", "⁰C", "цельсия", "градусцельсия"), False, "°C", "°C",
         offset=Fraction(27315, 100)),
    # --- производные единицы --------------------------------------------- #
    Unit("N", "kg·m/s^2", 1, ("Н", "ньютон", "ньютона", "ньютонов"), True, "Н", "N"),
    Unit("J", "kg·m^2/s^2", 1, ("Дж", "джоуль", "джоуля", "джоулей"), True, "Дж", "J"),
    Unit("W", "kg·m^2/s^3", 1, ("Вт", "ватт", "ватта", "ватт"), True, "Вт", "W"),
    Unit("Pa", "kg/(m·s^2)", 1, ("Па", "паскаль", "паскаля", "паскалей"), True, "Па", "Pa"),
    Unit("Hz", "1/s", 1, ("Гц", "герц", "герца"), True, "Гц", "Hz"),
    Unit("C", "A·s", 1, ("Кл", "кулон", "кулона", "кулонов"), True, "Кл", "C"),
    Unit("V", "kg·m^2/(s^3·A)", 1, ("В", "вольт", "вольта", "вольтов"), True, "В", "V"),
    Unit("Ohm", "kg·m^2/(s^3·A^2)", 1, ("Ω", "Ом", "ом", "ома", "омов"), True, "Ом", "Ω"),
    Unit("F", "s^4·A^2/(kg·m^2)", 1, ("Ф", "фарад", "фарада", "фарадов"), True, "Ф", "F"),
    Unit("T", "kg/(s^2·A)", 1, ("Тл", "тесла", "теслы"), True, "Тл", "T"),
    Unit("Wb", "kg·m^2/(s^2·A)", 1, ("Вб", "вебер", "вебера", "веберов"), True, "Вб", "Wb"),
    Unit("H", "kg·m^2/(s^2·A^2)", 1, ("Гн", "генри", "генри"), True, "Гн", "H"),
    Unit("dpt", "1/m", 1, ("дптр", "диоптрия", "диоптрии"), False, "дптр", "dpt"),
    # --- часто встречающиеся составные записи ----------------------------- #
    Unit("km/h", "m/s", Fraction(5, 18), ("км/ч",), False, "км/ч", "km/h"),
    Unit("m/s^2", "m/s^2", 1, ("м/с²",), False, "м/с²", "m/s²"),
    Unit("g/cm^3", "kg/m^3", 1000, ("г/см³",), False, "г/см³", "g/cm³"),
    Unit("kWh", "kg·m^2/s^2", 3600000, ("кВт·ч", "кВтч"), False, "кВт·ч", "kWh"),
    Unit("mmHg", "kg/(m·s^2)", Fraction(101325, 760), ("ммрт.ст.", "мм рт. ст."), False,
         "мм рт. ст.", "mm Hg"),
]

UNITS: dict[str, Unit] = {}
#: точные обозначения (регистр важен: «Т» — тесла, «т» — тонна, «T» и «t»)
_SYMBOLS: dict[str, Unit] = {}
#: словесные синонимы без учёта регистра («ньютон», «kelvin», «мм рт. ст.»)
_ALIASES: dict[str, Unit] = {}


def _alias_key(name: str) -> str:
    return str(name).strip().lower().replace(" ", "").replace("^", "").replace("·", "").replace("*", "")


def _is_single_latin(name: str) -> bool:
    return len(name) == 1 and "a" <= name.lower() <= "z"


def _register(unit: Unit) -> None:
    if unit.symbol in UNITS:
        raise QuantityError(f"duplicate unit symbol: {unit.symbol}")
    UNITS[unit.symbol] = unit
    for name in {unit.symbol, unit.ru, unit.en, *unit.aliases}:
        stripped = str(name).strip()
        previous = _SYMBOLS.get(stripped)
        if previous is not None and previous.symbol != unit.symbol:
            raise QuantityError(f"ambiguous unit symbol {name!r}: {previous.symbol} / {unit.symbol}")
        _SYMBOLS[stripped] = unit
        if _is_single_latin(stripped):
            continue           # однобуквенные латинские обозначения только с регистром
        key = _alias_key(stripped)
        previous = _ALIASES.get(key)
        if previous is not None and previous.symbol != unit.symbol:
            raise QuantityError(f"ambiguous unit alias {name!r}: {previous.symbol} / {unit.symbol}")
        _ALIASES.setdefault(key, unit)


for _unit in _UNIT_TABLE:
    _register(_unit)


#: школьные соглашения: символ → (значение, единица). Задание может переопределить
#: их в поле ``constants`` (например, g = 10 м/с² для устного счёта).
CONVENTIONS = {
    "g": ("9.8", "m/s^2"),
    "G": ("6.67e-11", "m^3/(kg·s^2)"),
    "k": ("1.38e-23", "J/K"),
    "NA": ("6.02e23", "1/mol"),
    "R": ("8.31", "J/(mol·K)"),
    "c": ("3e8", "m/s"),
    "h": ("6.63e-34", "J·s"),
    "e": ("1.6e-19", "C"),
    "me": ("9.1e-31", "kg"),
    "mp": ("1.67e-27", "kg"),
    "c_water": ("4200", "J/(kg·K)"),
    "c_ice": ("2100", "J/(kg·K)"),
    "c_iron": ("460", "J/(kg·K)"),
    "c_aluminium": ("920", "J/(kg·K)"),
    "L_water": ("2.3e6", "J/kg"),
    "L_ice": ("3.4e5", "J/kg"),
    "q_kerosene": ("4.6e7", "J/kg"),
    "q_petrol": ("4.6e7", "J/kg"),
    "rho_water": ("1000", "kg/m^3"),
    "rho_ice": ("900", "kg/m^3"),
    "rho_iron": ("7800", "kg/m^3"),
    "rho_aluminium": ("2700", "kg/m^3"),
    "atm": ("101325", "Pa"),
    "k_coulomb": ("9e9", "Н·м^2/Кл^2"),
}


def units_payload() -> list[dict]:
    """Белый список единиц для интерфейса (конвертер единиц, подсказки)."""
    return [unit.to_json() for unit in _UNIT_TABLE]


# --------------------------------------------------------------------------- #
#  Разбор единиц / unit parsing
# --------------------------------------------------------------------------- #

def _to_expression(text: str) -> str:
    """Нормализовать запись единицы: степени-надстрочники, ·, ×, запятая-разделитель."""
    s = str(text).strip()
    s = s.replace("**", "^")
    for symbol, digit in _DIGITS_FROM_SUPER.items():
        s = s.replace(symbol, f"^{digit}")
    s = s.replace("⁻", "-")
    for separator in ("⋅", "∙", "×", "·", "*"):
        s = s.replace(separator, "*")
    s = s.replace(" ", "").replace("\u00a0", "")
    return s


def _tokenize(expression: str) -> list[str]:
    tokens, i = [], 0
    while i < len(expression):
        ch = expression[i]
        if ch in "*/^()":
            tokens.append(ch)
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            j = i
            while j < len(expression) and (expression[j].isdigit() or expression[j] == "."):
                j += 1
            tokens.append(expression[i:j])
            i = j
            continue
        if ch == "-":
            tokens.append(ch)
            i += 1
            continue
        j = i
        while j < len(expression) and _is_unit_char(expression[j]):
            j += 1
        if j == i:
            raise QuantityError(f"unexpected character in unit: {ch!r}")
        tokens.append(expression[i:j])
        i = j
    return tokens


def _is_unit_char(ch: str) -> bool:
    if ch.isalnum() or ch in "._°Ωµμ":
        return True
    return "\u0400" <= ch <= "\u04ff"


class _UnitParser:
    """Рекурсивный разбор выражения единиц (без eval)."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse(self) -> tuple[Fraction, Dim]:
        factor, dim = self.expression()
        if self.pos != len(self.tokens):
            raise QuantityError("trailing input in unit: " + "".join(self.tokens[self.pos:]))
        return factor, dim

    def expression(self):
        factor, dim = self.term()
        while self.peek() in ("*", "/"):
            op = self.next()
            right_factor, right_dim = self.term()
            if op == "*":
                factor, dim = factor * right_factor, dim * right_dim
            else:
                factor, dim = factor / right_factor, dim / right_dim
        return factor, dim

    def term(self):
        factor, dim = self.atom()
        if self.peek() == "^":
            self.next()
            exponent = self.next()
            if exponent in ("-", "+"):
                digits = self.next()
                if digits is None:
                    raise QuantityError("missing exponent in unit")
                exponent = exponent + str(digits)
            if not re.fullmatch(r"-?\d{1,2}", str(exponent)):
                raise QuantityError(f"invalid exponent in unit: {exponent!r}")
            power = int(exponent)
            if power == 0:
                return Fraction(1), Dim.none()
            factor, dim = factor ** power, dim ** power
        return factor, dim

    def atom(self):
        token = self.next()
        if token is None:
            raise QuantityError("unexpected end of unit")
        if token == "(":
            factor, dim = self.expression()
            if self.next() != ")":
                raise QuantityError("missing ) in unit")
            return factor, dim
        if token == "1":
            return Fraction(1), Dim.none()
        if re.fullmatch(r"\d+(\.\d+)?", token):
            raise QuantityError("numeric factors are not allowed inside a unit")
        unit = _lookup_unit(token)
        if unit is None:
            raise QuantityError(f"unknown unit: {token!r}")
        if unit.offset and (self.pos < len(self.tokens) or len(self.tokens) > 1):
            # «Дж/(кг·°C)»: градус Цельсия в составной единице равен кельвину
            return unit.factor, unit.dim
        return unit.factor, unit.dim


def _base_lookup(name: str) -> Unit | None:
    """Единица по точному обозначению, затем по словесному синониму."""
    unit = _SYMBOLS.get(name)
    if unit is not None:
        return unit
    unit = _ALIASES.get(_alias_key(name))
    if unit is not None:
        return unit
    if _is_single_latin(name):
        # «н»/«n» без регистра: n → Н, j → Дж, но t остаётся тонной, а T — тесла
        return _SYMBOLS.get(name.upper())
    return None


def _lookup_unit(name: str) -> Unit | None:
    """Обозначение единицы, затем «приставка СИ + единица» («кДж», «мкФ», «мм»)."""
    unit = _base_lookup(name)
    if unit is not None:
        return unit
    for ru_prefix, latin_prefix, factor in sorted(PREFIXES, key=lambda item: -len(item[0])):
        for prefix in {ru_prefix, latin_prefix}:
            if not name.startswith(prefix) or len(name) == len(prefix):
                continue
            base = _base_lookup(name[len(prefix):])
            if base is None or not base.prefixable or base.offset:
                continue
            if base.symbol == "kg":
                continue  # «мкг» — не «микрокилограмм»: масса измеряется в кг через г
            return Unit(f"{latin_prefix}{base.symbol}", base.dim, base.factor * factor, (), False,
                        f"{ru_prefix}{base.ru}", f"{latin_prefix}{base.en}")
    return None


def parse_unit(text: str) -> Unit:
    """Разобрать единицу («м/с²», «кг·м/с²», «кДж/(кг·К)»). Ошибка — исключение."""
    raw = str(text or "").strip()
    if not raw:
        raise QuantityError("empty unit")
    expression = _to_expression(raw)
    tokens = _tokenize(expression)
    if not tokens:
        raise QuantityError("empty unit")
    if tokens == ["1"]:
        # безразмерная величина: подпись пустая, ответ печатается просто числом
        return Unit("1", Dim.none(), 1, (), False, "", "")
    factor, dim = _UnitParser(tokens).parse()
    if len(tokens) == 1:
        unit = _lookup_unit(tokens[0])
        if unit is not None and (unit.offset or unit.factor == factor):
            # сохраняем каноническую единицу вместе с синонимами и смещением
            return unit
    return Unit(_symbol_of(tokens), dim, factor, (), False,
                _display_of(tokens, "ru"), _display_of(tokens, "en"))


def unit_of(text: str) -> Unit | None:
    """Мягкий вариант разбора: None вместо исключения (для ответа ученика)."""
    try:
        return parse_unit(text)
    except QuantityError:
        return None


#: кириллические обозначения основных размерностей и надстрочники
_DIM_ALIASES = (("моль", "mol"), ("кг", "kg"), ("кд", "cd"), ("м", "m"),
                ("С", "s"), ("с", "s"), ("А", "A"), ("а", "A"),
                ("К", "K"), ("к", "K"))


def parse_dim(text) -> Dim:
    """Разобрать размерность: ``m/s^2``, ``kg·m^2/s^2``, ``м/с²``, ``1``.

    Размерность записывается только через основные единицы СИ — так подпись
    ``dimension`` в задании невозможно спутать с единицей измерения.
    """
    if isinstance(text, Dim):
        return text
    if isinstance(text, Unit):
        return text.dim
    raw = str(text or "").strip()
    if raw in ("", "1", "—", "-", "безразмерная", "dimensionless"):
        return Dim.none()
    expression = _to_expression(raw)
    for name, base in _DIM_ALIASES:
        expression = expression.replace(name, base)
    tree = _ModelParser(_tokenize_model(expression), set(DIMS)).parse()
    return _dim_node(tree, {name: Dim.base(name) for name in DIMS})


def _symbol_of(tokens) -> str:
    return "".join(tokens)


#: перевод подписи единицы между языками: русская запись ↔ латинская.
#: Порядок замен важен: сначала длинные названия, потом короткие обозначения.
_DISPLAY_TRANSLATION = (
    ("ru", "en", (("мм рт. ст.", "mm Hg"), ("моль", "mol"), ("дптр", "dpt"),
                  ("кВт·ч", "kWh"), ("Ом", "Ohm"), ("Вб", "Wb"), ("Гц", "Hz"),
                  ("кПа", "kPa"), ("МПа", "MPa"), ("кДж", "kJ"), ("МДж", "MJ"),
                  ("мДж", "mJ"), ("мН", "mN"), ("кН", "kN"), ("мкФ", "µF"), ("нФ", "nF"),
                  ("км/ч", "km/h"), ("кг/м", "kg/m"), ("кг", "kg"), ("моль", "mol"),
                  ("мДж", "mJ"), ("мин", "min"), ("сут", "day"), ("мкм", "µm"),
                  ("км", "km"), ("см", "cm"), ("мм", "mm"), ("кН", "kN"),
                  ("Н", "N"), ("Дж", "J"), ("Вт", "W"), ("Па", "Pa"), ("Кл", "C"),
                  ("В", "V"), ("Тл", "T"), ("Гн", "H"), ("Ф", "F"), ("К", "K"),
                  ("А", "A"), ("Вб", "Wb"), ("м", "m"), ("с", "s"), ("л", "l"),
                  ("ч", "h"), ("дптр", "dpt"))),
    ("en", "ru", (("mm Hg", "мм рт. ст."), ("Ohm", "Ом"), ("kg", "кг"), ("mol", "моль"),
                  ("min", "мин"), ("day", "сут"), ("dpt", "дптр"), ("Wb", "Вб"),
                  ("Hz", "Гц"), ("Pa", "Па"), ("J", "Дж"), ("W", "Вт"), ("C", "Кл"),
                  ("V", "В"), ("T", "Тл"), ("H", "Гн"), ("N", "Н"), ("K", "К"),
                  ("A", "А"), ("F", "Ф"), ("m", "м"), ("s", "с"), ("l", "л"),
                  ("h", "ч"))),
)


def _translate_display(text: str, lang: str) -> str:
    for source, target in (("ru", "en") if lang == "en" else ("en", "ru"),):
        table = next(item for item in _DISPLAY_TRANSLATION if item[0] == source)[2]
        for old, new in table:
            text = re.sub(r"(?<![A-Za-zА-Яа-я])" + re.escape(old) + r"(?![A-Za-zА-Яа-я])",
                          new, text)
    return text


def _display_of(tokens, lang: str) -> str:
    """Человеческая подпись составной единицы: «кг·м/с²», «kg·m/s²».

    Степени печатаются надстрочными знаками (``м^3`` → ``м³``), потому что именно
    так единицы записывают в учебнике и так их увидит ученик; при английском
    интерфейсе надпись переводится в латинские обозначения.
    """
    text = "".join(tokens).replace("*", "·").replace("degC", "°C")
    text = re.sub(r"\^(-?\d+)",
                  lambda match: "".join(SUPERSCRIPTS[c] for c in match.group(1)), text)
    return _translate_display(text, lang)


# --------------------------------------------------------------------------- #
#  Величина / quantity
# --------------------------------------------------------------------------- #

class Q:
    """Физическая величина: точное значение и единица измерения."""

    __slots__ = ("value", "unit")

    def __init__(self, value, unit):
        self.value = value if isinstance(value, Fraction) else to_fraction(value)
        self.unit = unit if isinstance(unit, Unit) else parse_unit(unit)

    @property
    def dim(self) -> Dim:
        return self.unit.dim

    def si(self) -> Fraction:
        """Значение в основных единицах СИ (для °C учитывается смещение 273,15)."""
        if self.unit.offset:
            return (self.value + self.unit.offset) * self.unit.factor
        return self.value * self.unit.factor

    def to(self, unit) -> "Q":
        """Перевести в другую единицу той же размерности."""
        target = unit if isinstance(unit, Unit) else parse_unit(unit)
        if target.dim != self.dim:
            raise QuantityError(f"cannot convert {self.unit.symbol} to {target.symbol}: "
                                f"{self.dim.signature()} ≠ {target.dim.signature()}")
        value = self.si()
        if target.offset:
            value = value / target.factor - target.offset
        else:
            value = value / target.factor
        return Q(value, target)

    def __mul__(self, other):
        if isinstance(other, Q):
            return Q(self.value * other.value,
                     Unit(f"{self.unit.symbol}·{other.unit.symbol}", self.dim * other.dim,
                          self.unit.factor * other.unit.factor))
        return Q(self.value * to_fraction(other), self.unit)

    def __truediv__(self, other):
        if isinstance(other, Q):
            return Q(self.value / other.value,
                     Unit(f"{self.unit.symbol}/{other.unit.symbol}", self.dim / other.dim,
                          self.unit.factor / other.unit.factor))
        return Q(self.value / to_fraction(other), self.unit)

    def __add__(self, other: "Q") -> "Q":
        if not isinstance(other, Q) or other.dim != self.dim:
            raise QuantityError("cannot add quantities of different dimensions")
        return Q(self.value + other.to(self.unit).value, self.unit)

    def __neg__(self) -> "Q":
        return Q(-self.value, self.unit)

    def __repr__(self) -> str:
        return f"Q({self.value} {self.unit.symbol})"


def to_fraction(value) -> Fraction:
    """Строгое преобразование в точную дробь (никаких двоичных приближений)."""
    if isinstance(value, bool):
        raise QuantityError("bool is not a physical quantity")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    text = str(value).strip().replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
        raise QuantityError(f"not a number: {value!r}")
    return Fraction(text)


# --------------------------------------------------------------------------- #
#  Числа и запись ответа / numbers and formatting
# --------------------------------------------------------------------------- #

_SCIENTIFIC_RE = re.compile(r"^([+-]?\d+(?:[.,]\d+)?)(?:[*]10(?:\^|\*\*)?\(?([+-]?\d+)\)?|[eE]([+-]?\d+))$")


def parse_number(text) -> Fraction | None:
    """Разобрать число в школьной записи; None — если это не число.

    Понимает ``12``, ``12,5``, ``12.5``, ``-3,5``, ``+2``, ``1e-3``,
    ``1,5·10⁻³``, ``1,5*10^-3``, ``3·10^5``, ``1,6*10-19`` и удаляет
    пробелы-разделители разрядов (``1 000``).
    """
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    s = s.replace("\u00a0", "").replace(" ", "")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    # «10⁻³» и «10¹⁹» — только степень десяти, а не любое число с надстрочником
    s = re.sub(r"10([\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079\u207b]+)",
               lambda m: "10^(" + "".join(_DIGITS_FROM_SUPER[c] for c in m.group(1)) + ")", s)
    for separator in ("⋅", "∙", "×", "·"):
        s = s.replace(separator, "*")
    match = _SCIENTIFIC_RE.match(s)
    if match:
        mantissa = match.group(1).replace(",", ".")
        exponent = match.group(2) or match.group(3) or "0"
        try:
            return Fraction(mantissa) * Fraction(10) ** int(exponent)
        except (ValueError, ZeroDivisionError):
            return None
    power_of_ten = re.fullmatch(r"10\^(?:\(([+-]?\d+)\)|([+-]?\d+))", s)
    if power_of_ten:
        return Fraction(10) ** int(power_of_ten.group(1) or power_of_ten.group(2))
    plain = s.replace(",", ".")
    if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", plain):
        return None
    return Fraction(plain)


def sci_parts(value: Fraction, digits: int = 3) -> tuple[Fraction, int]:
    """Представить значение как (мантисса, порядок): 0,0015 → (1,5; −3)."""
    if value == 0:
        return Fraction(0), 0
    sign = -1 if value < 0 else 1
    absolute = abs(value)
    order = 0
    while absolute >= 10:
        absolute /= 10
        order += 1
    while absolute < 1:
        absolute *= 10
        order -= 1
    scale = 10 ** digits
    mantissa = Fraction(round(absolute * scale), scale)
    if mantissa >= 10:
        mantissa /= 10
        order += 1
    return mantissa * sign, order


def _decimal_text(value: Fraction, places: int) -> str:
    """Десятичная запись с округлением (для π, √2 и других неточных значений)."""
    with localcontext() as context:
        context.prec = places + 6
        result = Decimal(value.numerator) / Decimal(value.denominator)
        text = str(+result)
    if "E" in text or "e" in text:
        text = format(Decimal(text), "f")
    return text


def format_number(value, lang: str = "ru", *, places: int | None = None,
                  scientific: bool = False, digits: int = 3) -> str:
    """Записать число: RU — «12,5», EN — «12.5», большие и малые — через 10ⁿ."""
    value = value if isinstance(value, Fraction) else to_fraction(value)
    if value == 0:
        return _round_text(Fraction(0), places, lang) if places else "0"
    if not scientific and (abs(value) >= 10 ** 5 or abs(value) <= Fraction(1, 10 ** 4)):
        scientific = True          # школьная запись: 4,6·10⁷ Дж/кг, 1,6·10⁻¹⁹ Кл
    if scientific:
        mantissa, order = sci_parts(value, digits)
        text = _round_text(mantissa, None, lang)
        if order == 0:
            return _round_text(value, places, lang)
        if lang == "en":
            return f"{text}·10^{order}"
        return f"{text}·10{''.join(SUPERSCRIPTS[c] for c in str(order))}"
    return _round_text(value, places, lang)


def _round_text(value: Fraction, places: int | None, lang: str) -> str:
    if places is None:
        text = _exact_text(value)
    else:
        scale = 10 ** places
        rounded = Fraction(round(value * scale), scale)
        text = _exact_text(rounded)
        whole, _, frac = text.partition(".")
        frac = (frac + "0" * places)[:places]
        text = f"{whole}.{frac}" if places else whole
    return text.replace(".", "," if lang != "en" else ".")


def _exact_text(value: Fraction) -> str:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        return _decimal_text(value, 12)
    digits = max(twos, fives)
    if digits == 0:
        return str(value.numerator)
    scale = 10 ** digits
    scaled = value.numerator * (scale // value.denominator)
    sign = "-" if scaled < 0 else ""
    raw = str(abs(scaled)).rjust(digits + 1, "0")
    text = f"{raw[:-digits]}.{raw[-digits:]}".rstrip("0").rstrip(".")
    return sign + (text or "0")


def format_quantity(value, unit, lang: str = "ru", *, places: int | None = None,
                    scientific: bool = False) -> str:
    """«12,5 м/с» / «12.5 m/s»."""
    label = unit.display(lang) if isinstance(unit, Unit) else str(unit)
    return f"{format_number(value, lang, places=places, scientific=scientific)} {label}".strip()


# --------------------------------------------------------------------------- #
#  Проверка ответа / answer checking
# --------------------------------------------------------------------------- #

class CheckResult:
    """Результат проверки и причина именно такого вывода (для разбора ошибки)."""

    __slots__ = ("ok", "reason", "value", "unit")

    def __init__(self, ok: bool, reason: str = "", value=None, unit=None):
        self.ok = ok
        self.reason = reason       # "" | "empty" | "dimension" | "unit" | "missing_unit" | "value"
        self.value = value
        self.unit = unit

    def __bool__(self) -> bool:
        return self.ok

    def __repr__(self) -> str:
        return f"CheckResult(ok={self.ok}, reason={self.reason!r})"

    def diagnosis(self) -> str:
        """Ключ строки интерфейса для объяснения ошибки."""
        return {
            "": "answer_correct",
            "empty": "answer_empty",
            "dimension": "answer_wrong_dimension",
            "unit": "answer_wrong_unit",
            "missing_unit": "answer_missing_unit",
            "value": "answer_incorrect",
        }.get(self.reason, "answer_incorrect")

    def to_json(self) -> dict:
        return {"ok": self.ok, "reason": self.reason}


def split_number_unit(text: str) -> tuple[str, str]:
    """«10 м/с» → («10», «м/с»); «10» → («10», ""); «1.5e-3 м» → («1.5e-3», «м»).

    Разделитель ищется по самой длинной числовой части: так корректно
    разбираются и «10Н» без пробела, и научная запись «1,5·10⁻³ м».
    """
    raw = str(text or "").strip()
    if not raw:
        return "", ""
    for index in range(len(raw), 0, -1):
        head, tail = raw[:index].strip(), raw[index:].strip()
        if not head or parse_number(head) is None:
            continue
        if not tail or unit_of(tail) is not None:
            return head, tail
    # единица может быть не распознана: отделяем её отдельным диагнозом
    fallback = re.match(r"^([^A-Za-zА-Яа-яЁёΩµμ°]+)\s*(.*)$", raw)
    if fallback and parse_number(fallback.group(1).strip()) is not None and fallback.group(2).strip():
        return fallback.group(1).strip(), fallback.group(2).strip()
    return raw, ""


def check_answer(user, spec: dict) -> CheckResult:
    """Проверить ответ ученика по контракту задания (``spec``).

    Поля ``spec``:
      * ``answerType``: ``choice`` | ``number`` | ``quantity`` | ``scientific``;
      * ``accept`` — список дополнительно принимаемых записей;
      * ``answerValue`` — точное значение ответа (в единице ``unit``);
      * ``unit`` — единица, в которой требуется ответ;
      * ``unitPolicy``: ``named`` (единица названа в условии, ввод без единицы
        допустим), ``optional``, ``required`` (единицу обязательно указать);
      * ``dimension`` — подпись размерности ответа (``m/s``);
      * ``tolerance`` — ``{"kind": "absolute"|"relative", "value": ...}``;
      * ``rounding`` — требуемое число знаков после запятой (допуск задаётся
        границей округления, когда tolerance не задан).
    """
    text = "" if user is None else str(user).strip()
    if not text:
        return CheckResult(False, "empty")

    answer_type = spec.get("answerType", "number")
    if answer_type == "choice":
        normalized = _normalize_choice(text)
        if not normalized:
            return CheckResult(False, "empty")
        for candidate in _choice_candidates(spec):
            if _normalize_choice(candidate) == normalized:
                return CheckResult(True)
        return CheckResult(False, "value")

    dimension = spec.get("dimension")
    dimension = parse_dim(dimension) if dimension else None
    target_unit = spec.get("unit") or ""
    target = unit_of(target_unit) if target_unit else None
    policy = spec.get("unitPolicy") or ("named" if target else "optional")

    number_text, unit_text = split_number_unit(text)
    number = parse_number(number_text)
    if number is None:
        return CheckResult(False, "empty")

    unit = unit_of(unit_text) if unit_text else None
    if unit_text and unit is None:
        return CheckResult(False, "unit")
    if unit is None and policy == "required":
        return CheckResult(False, "missing_unit")
    if unit is not None and dimension is not None and unit.dim != dimension:
        return CheckResult(False, "dimension", number, unit)

    expected = spec.get("answerValue")
    if expected is None:
        return CheckResult(False, "value")
    expected = to_fraction(expected)

    if unit is not None:
        if target is not None:
            if unit.dim != target.dim:
                return CheckResult(False, "dimension", number, unit)
            got = Q(number, unit).to(target).value
        else:
            if dimension is not None and unit.dim != dimension:
                return CheckResult(False, "dimension", number, unit)
            got = Q(number, unit).si()
    else:
        got = number

    tolerance = spec.get("tolerance")
    if tolerance is None:
        rounding = spec.get("rounding")
        if rounding is not None:
            tolerance = {"kind": "absolute", "value": Fraction(5, 10 ** (int(rounding) + 1))}
        else:
            tolerance = {"kind": "absolute", "value": Fraction(1, 10 ** 9)}
    allowed = _tolerance_value(expected, tolerance)
    if abs(got - expected) <= allowed:
        return CheckResult(True, "", got, unit or target)
    return CheckResult(False, "value", got, unit or target)


def _tolerance_value(expected: Fraction, tolerance: dict) -> Fraction:
    kind = tolerance.get("kind", "absolute")
    value = tolerance.get("value", 0)
    value = value if isinstance(value, Fraction) else to_fraction(value)
    if kind == "relative":
        return abs(expected) * value
    if kind == "absolute":
        return value
    raise QuantityError(f"unknown tolerance kind: {kind}")


def _choice_candidates(spec: dict) -> list[str]:
    out = []
    answer = spec.get("answer")
    if isinstance(answer, str):
        out.append(answer)
    elif isinstance(answer, dict):
        out.extend(str(answer.get(lang, "")) for lang in ("ru", "en"))
    for candidate in spec.get("accept") or []:
        if isinstance(candidate, dict):
            out.extend(str(candidate.get(lang, "")) for lang in ("ru", "en"))
        else:
            out.append(str(candidate))
    return [item for item in out if item.strip()]


def _normalize_choice(text: str) -> str:
    s = str(text).strip().lower()
    s = s.replace("\u00a0", " ").replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"^(ответ|answer)\s*[:.=]?\s*", "", s)
    s = re.sub(r"^\s*[а-яa-z]\s*[).:]\s*", "", s)      # «б) 12» → «12»
    s = s.replace(",", ".")
    s = s.replace(" ", "")
    return s


# --------------------------------------------------------------------------- #
#  Модель задания: формула, размерности, данные
# --------------------------------------------------------------------------- #

_MODEL_TOKEN = re.compile(r"\s*([A-Za-z_][A-Za-z_0-9]*|\d+(?:\.\d+)?|[-+*/^()])")


def _tokenize_model(expression: str) -> list[str]:
    tokens, pos = [], 0
    while pos < len(expression):
        if expression[pos].isspace():
            pos += 1
            continue
        match = _MODEL_TOKEN.match(expression, pos)
        if not match:
            raise ModelError(f"unexpected character in formula: {expression[pos]!r}")
        tokens.append(match.group(1))
        pos = match.end()
    return tokens


class _ModelParser:
    """Разбор формулы задания: символы, числа, ``+ - * / ^`` и скобки."""

    def __init__(self, tokens, variables):
        self.tokens = tokens
        self.pos = 0
        self.variables = variables

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse(self):
        node = self.expression()
        if self.pos != len(self.tokens):
            raise ModelError("trailing input in formula: " + " ".join(self.tokens[self.pos:]))
        return node

    def expression(self):
        node = self.term()
        while self.peek() in ("+", "-"):
            op = self.next()
            node = (op, node, self.term())
        return node

    def term(self):
        node = self.power()
        while self.peek() in ("*", "/"):
            op = self.next()
            node = (op, node, self.power())
        return node

    def power(self):
        node = self.atom()
        if self.peek() == "^":
            self.next()
            wrapped = False
            if self.peek() == "(":
                self.next()
                wrapped = True
            sign = 1
            if self.peek() == "-":
                self.next()
                sign = -1
            elif self.peek() == "+":
                self.next()
            exponent = self.next()
            if not re.fullmatch(r"\d+", str(exponent)):
                raise ModelError("only integer exponents are allowed in formulas")
            if wrapped and self.next() != ")":
                raise ModelError("missing ) after exponent in formula")
            node = ("^", node, sign * int(exponent))
        return node

    def atom(self):
        token = self.next()
        if token is None:
            raise ModelError("unexpected end of formula")
        if token == "(":
            node = self.expression()
            if self.next() != ")":
                raise ModelError("missing ) in formula")
            return node
        if token == "-":
            return ("neg", self.atom())
        if re.fullmatch(r"\d+(\.\d+)?", token):
            return ("num", Fraction(token))
        if token not in self.variables:
            raise ModelError(f"unknown symbol in formula: {token}")
        return ("var", token)


def _node_symbols(node, out: set) -> set:
    if node[0] == "var":
        out.add(node[1])
    elif node[0] in ("neg",):
        _node_symbols(node[1], out)
    elif node[0] in ("+", "-", "*", "/", "^"):
        _node_symbols(node[1], out)
        if node[0] != "^":
            _node_symbols(node[2], out)
    return out


def model_symbols(formula: str) -> set[str]:
    """Символы, встречающиеся в правой части формулы."""
    expression = formula.split("=", 1)[1] if "=" in formula else formula
    tree = _ModelParser(_tokenize_model(expression), _CollectingNames()).parse()
    return _node_symbols(tree, set())


class _CollectingNames:
    """Принимает любое имя: используется, когда символы заранее неизвестны."""

    def __contains__(self, name: str) -> bool:
        return True


def eval_model(formula: str, values: dict):
    """Вычислить правую часть формулы при заданных значениях символов."""
    expression = formula.split("=", 1)[1] if "=" in formula else formula
    tree = _ModelParser(_tokenize_model(expression), set(values)).parse()
    return _eval_node(tree, values)


def _eval_node(node, values):
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "var":
        try:
            return values[node[1]]
        except KeyError as error:
            raise ModelError(f"no value for symbol {node[1]!r}") from error
    if kind == "neg":
        return -_eval_node(node[1], values)
    if kind == "+":
        return _eval_node(node[1], values) + _eval_node(node[2], values)
    if kind == "-":
        return _eval_node(node[1], values) - _eval_node(node[2], values)
    if kind == "*":
        return _eval_node(node[1], values) * _eval_node(node[2], values)
    if kind == "/":
        left = _eval_node(node[1], values)
        right = _eval_node(node[2], values)
        if isinstance(right, Fraction) and right == 0:
            raise ModelError("division by zero in formula")
        return left / right
    if kind == "^":
        base = _eval_node(node[1], values)
        if node[2] < 0:
            base = to_fraction(base)      # Fraction ** (−n) остаётся точной дробью
        return base ** node[2]
    raise ModelError(f"bad formula node: {kind}")


def dim_balance(formula: str, variables: dict) -> Dim:
    """Размерность правой части формулы с проверкой баланса слагаемых.

    ``variables`` — символ → размерность (``Dim`` или строка). Каждое сложение
    требует одинаковой размерности — так ловится формула ``s = v0*t + a*t``.
    """
    dims = {name: (value if isinstance(value, Dim) else parse_dim(value))
            for name, value in variables.items()}
    expression = formula.split("=", 1)[1] if "=" in formula else formula
    tree = _ModelParser(_tokenize_model(expression), set(dims)).parse()
    return _dim_node(tree, dims)


def _dim_node(node, dims) -> Dim:
    kind = node[0]
    if kind == "num":
        return Dim.none()
    if kind == "var":
        return dims[node[1]]
    if kind == "neg":
        return _dim_node(node[1], dims)
    if kind in ("+", "-"):
        left = _dim_node(node[1], dims)
        right = _dim_node(node[2], dims)
        if left != right:
            raise ModelError(f"formula adds different dimensions: "
                             f"{left.signature()} and {right.signature()}")
        return left
    if kind == "*":
        return _dim_node(node[1], dims) * _dim_node(node[2], dims)
    if kind == "/":
        return _dim_node(node[1], dims) / _dim_node(node[2], dims)
    if kind == "^":
        return _dim_node(node[1], dims) ** node[2]
    raise ModelError(f"bad formula node: {kind}")
