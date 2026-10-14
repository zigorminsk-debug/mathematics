"""kit.py — авторский инструментарий и проверка банка заданий по физике.

Принципы (те же, что в математике, но для физических величин)
------------------------------------------------------------
1. *Один источник правды.*  Задание пишется один раз здесь и превращается в
   языконезависимый JSON, который читают Android (Kotlin) и Windows (Go + JS).
2. *Ответ выводится из модели, а не набивается руками.*  Автор задаёт формулу
   (``model``), размерности символов (``vars``) и данные (``data``); значение
   ответа считает ядро — точно, в дробях. Сборка падает, если формула
   размерностно не сбалансирована, данные не совпадают с текстом, ответ нельзя
   выразить в требуемой единице или не задан допуск.
3. *Независимая проверка.*  Где возможно, задание указывает второй путь
   (``alt``) — другую формулу, которая обязана дать то же значение.
4. *Каждый ответ с единицей измерения проверяется на размерность*, поэтому
   «10 Н» никогда не будет принято вместо «10 кг», а «10 см» — вместо «10 м».

Единицы в тексте задания подставляются шаблонами ``{v0}``: значение печатает
ядро (в русском тексте с запятой, в английском с точкой), и сборка проверяет,
что оно действительно попало в оба текста.
"""

from __future__ import annotations

import re
from fractions import Fraction

from quantities import (CONVENTIONS, Dim, ModelError, Q, QuantityError, check_answer,
                        dim_balance, eval_model, format_number, format_quantity,
                        format_quantity, parse_dim, parse_number, parse_unit, sci_parts,
                        to_fraction, unit_of)

__all__ = [
    "PhysicsError", "bi", "Task", "choice_task", "calc_task", "calc_choice_task",
    "TOPICS", "TOPIC_ORDER", "TOOLS", "ANSWER_VECTORS", "vectors_payload",
    "formula_groups", "MISTAKE_TAGS",
]

DEFAULT_TOOLS = ("calc", "sheet", "units", "scratch")


class PhysicsError(AssertionError):
    """Задание не проходит физическую проверку — банк не собирается."""


def bi(ru, en=None):
    """Двуязычная строка."""
    return {"ru": str(ru), "en": str(ru if en is None else en)}


def plural(count: int, one: str, few: str, many: str) -> str:
    count = abs(int(count)) % 100
    if 11 <= count <= 19:
        return many
    count %= 10
    if count == 1:
        return one
    if 2 <= count <= 4:
        return few
    return many


# --------------------------------------------------------------------------- #
#  Разделы курса / topics
# --------------------------------------------------------------------------- #

TOPICS = {
    "measurements": bi("Измерения и единицы", "Measurement and units"),
    "kinematics": bi("Кинематика", "Kinematics"),
    "dynamics": bi("Динамика", "Dynamics"),
    "workenergy": bi("Работа, мощность, энергия, импульс", "Work, power, energy, momentum"),
    "statics": bi("Статика, давление, гидростатика", "Statics, pressure, hydrostatics"),
    "molecular": bi("Молекулярная физика и газовые законы", "Molecular physics and gas laws"),
    "thermo": bi("Теплота и термодинамика", "Heat and thermodynamics"),
    "electrostatics": bi("Электростатика", "Electrostatics"),
    "current": bi("Постоянный ток", "Direct current"),
    "magnetism": bi("Магнитное поле и индукция", "Magnetic field and induction"),
    "oscillations": bi("Колебания, волны, звук", "Oscillations, waves, sound"),
    "optics": bi("Оптика", "Optics"),
    "quantum": bi("Квантовые явления, атом и ядро", "Quantum phenomena, atom and nucleus"),
}

TOPIC_ORDER = ["measurements", "kinematics", "dynamics", "workenergy", "statics",
               "molecular", "thermo", "electrostatics", "current", "magnetism",
               "oscillations", "optics", "quantum"]

TOOLS = {
    "calc": bi("Калькулятор", "Calculator"),
    "sheet": bi("Сборник формул", "Formula sheet"),
    "units": bi("Единицы и размерности", "Units and dimensions"),
    "scratch": bi("Черновик", "Scratchpad"),
    "graph": bi("График", "Plotter"),
    "hint": bi("Подсказка", "Hint"),
}

#: типичные ошибки: тег задания → объяснение (используется в mistakes.json)
MISTAKE_TAGS: dict[str, tuple[str, str]] = {}


def register_mistake(tag: str, ru: str, en: str) -> None:
    """Связать тег задания с типичной ошибкой (для mistakes.json)."""
    if tag in MISTAKE_TAGS:
        raise PhysicsError(f"типичная ошибка с тегом {tag!r} уже описана")
    MISTAKE_TAGS[tag] = (ru, en)


# --------------------------------------------------------------------------- #
#  Служебные помощники / helpers
# --------------------------------------------------------------------------- #

def _fraction(value) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(str(value))
    parsed = parse_number(str(value))
    if parsed is None:
        raise PhysicsError(f"не число: {value!r}")
    return parsed


def _plain_number(value: Fraction, digits: int = 15) -> str:
    """Ответ для машины: только английская запись (её читают JS/Kotlin)."""
    if value.denominator == 1:
        return str(value.numerator)
    text = format_number(value, "en", scientific=False)
    if "·10" in text:
        mantissa, order = sci_parts(value, digits)
        return f"{format_number(mantissa, 'en')}e{order}" if order else format_number(mantissa, "en")
    # конечная десятичная дробь или округление до 15 значащих цифр
    if value.denominator not in (1,) and not _is_terminating(value):
        from decimal import Decimal, localcontext
        with localcontext() as context:
            context.prec = digits
            return str(+((Decimal(value.numerator) / Decimal(value.denominator)).normalize()))
    return _decimal_string(value)


def _is_terminating(value: Fraction) -> bool:
    denominator = value.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    return denominator == 1


def _decimal_string(value: Fraction) -> str:
    from decimal import Decimal, localcontext
    with localcontext() as context:
        context.prec = 40
        result = Decimal(value.numerator) / Decimal(value.denominator)
        text = format(result, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _tolerance_json(tolerance) -> dict | None:
    if tolerance is None:
        return None
    if isinstance(tolerance, dict):
        kind = tolerance.get("kind", "absolute")
        value = _fraction(tolerance["value"])
    else:                     # просто число — абсолютный допуск
        kind, value = "absolute", _fraction(tolerance)
    if kind not in ("absolute", "relative"):
        raise PhysicsError(f"неизвестный вид допуска: {kind}")
    return {"kind": kind, "value": _plain_number(value)}


#: распространённые «соседние» единицы: в них тоже принимается верный ответ
_ALTERNATIVE_UNITS = {
    "m": ("cm", "mm", "km"),
    "m/s": ("km/h",),
    "m/s^2": (),
    "kg": ("g", "t"),
    "s": ("min", "h", "ms"),
    "m^3": ("l",),
    "kg/m^3": ("g/cm^3",),
    "kg·m^2/s^2": ("kJ", "MJ", "eV"),
    "kg·m^2/s^3": ("kW", "mW"),
    "kg/(m·s^2)": ("kPa", "MPa"),
    "A": ("mA", "µA"),
    "A·s": ("mC", "µC"),
    "kg·m^2/(s^3·A)": ("mV", "kV"),
    "kg·m^2/(s^3·A^2)": ("kOhm", "MOhm"),
    "K": ("°C",),
    "1/s": ("kHz", "MHz"),
    "kg/(s^2·A)": ("mT",),
    "kg·m/s": (),
}


class Task:
    """Одно задание банка или генератора: данные, ответ, разбор, проверки."""

    def __init__(self, *, id, year, part, n, topic, difficulty, answer_type,
                 text_ru, text_en, options=None, answer_value=None, answer_display=None,
                 accept=(), unit=None, unit_policy=None, dimension=None, tolerance=None,
                 rounding=None, given=(), model=None, solution_ru=(), solution_en=(),
                 hints_ru=(), hints_en=(), tools=None, src=None, tags=(), constants=None,
                 correct_index=None, literal=False, celsius_answer=False, domain=None):
        self.id = id
        self.year = year
        self.part = part
        self.n = n
        self.topic = topic
        self.difficulty = difficulty
        self.answer_type = answer_type
        self.text_ru = text_ru
        self.text_en = text_en
        self.options = options
        self.answer_value = answer_value
        self.answer_display = answer_display
        self.extra_accept = list(accept)
        self.unit = unit
        self.unit_policy = unit_policy
        self.dimension = dimension
        self.tolerance = tolerance
        self.rounding = rounding
        self.given = list(given)
        self.model = model
        self.solution_ru = list(solution_ru)
        self.solution_en = list(solution_en)
        self.hints_ru = list(hints_ru)
        self.hints_en = list(hints_en)
        self.tools = list(tools or DEFAULT_TOOLS)
        self.src = src or "авторское тренировочное задание (не материалы РИКЗ)"
        self.tags = list(tags)
        self.constants = dict(constants or {})
        self.correct_index = correct_index
        self.literal = literal
        self.celsius_answer = celsius_answer
        self.domain = dict(domain or {})
        self.accept: list[str] = []
        self.checks: list[str] = []

    # -- проверка ----------------------------------------------------------- #
    def verify(self) -> None:
        """Полная проверка задания. Любая ошибка — исключение PhysicsError."""
        if not self.id or not isinstance(self.id, str):
            raise PhysicsError("у задания нет идентификатора")
        if self.topic not in TOPICS:
            raise PhysicsError(f"{self.id}: неизвестный раздел {self.topic!r}")
        if self.part not in ("A", "B"):
            raise PhysicsError(f"{self.id}: часть должна быть A или B")
        if not (1 <= self.n <= 40):
            raise PhysicsError(f"{self.id}: номер задания вне диапазона")
        if self.year and not (2021 <= self.year <= 2026):
            raise PhysicsError(f"{self.id}: неизвестный период {self.year}")
        if not self.text_ru.strip() or not self.text_en.strip():
            raise PhysicsError(f"{self.id}: нет двуязычного условия")
        for tag in self.tags:
            if tag not in MISTAKE_TAGS:
                raise PhysicsError(f"{self.id}: тег {tag!r} не описан в mistakes")
        if not self.solution_ru or not self.solution_en:
            raise PhysicsError(f"{self.id}: нет разбора решения")
        if len(self.solution_ru) != len(self.solution_en):
            raise PhysicsError(f"{self.id}: разбор на русском и английском разной длины")

        if self.answer_type == "choice":
            self._verify_choice()
        else:
            self._verify_numeric()
        if self.model:
            for key in ("formula", "dim", "vars"):
                if key not in self.model:
                    raise PhysicsError(f"{self.id}: в модели нет поля {key}")
        self.checks.append("структура")

    def _verify_choice(self) -> None:
        options = self.options or {}
        for lang in ("ru", "en"):
            values = options.get(lang)
            if not isinstance(values, list) or len(values) != 5:
                raise PhysicsError(f"{self.id}: в части A должно быть ровно 5 вариантов ({lang})")
            if len(set(values)) != 5:
                raise PhysicsError(f"{self.id}: варианты ответа повторяются ({lang})")
            if any(not str(value).strip() for value in values):
                raise PhysicsError(f"{self.id}: пустой вариант ответа ({lang})")
        if self.correct_index is None or not (0 <= self.correct_index < 5):
            raise PhysicsError(f"{self.id}: не указан номер верного варианта")
        self.answer_display = {lang: options[lang][self.correct_index] for lang in ("ru", "en")}
        self.accept = [self.answer_display["ru"], self.answer_display["en"]]
        self.checks.append("варианты")

    def _verify_numeric(self) -> None:
        if self.answer_value is None:
            raise PhysicsError(f"{self.id}: не вычислено значение ответа")
        if self.dimension is None:
            raise PhysicsError(f"{self.id}: не указана размерность ответа")
        parse_dim(self.dimension)          # выбросит ошибку, если размерность неверная
        if self.unit:
            unit = parse_unit(self.unit)
            if unit.dim != parse_dim(self.dimension):
                raise PhysicsError(f"{self.id}: единица {self.unit!r} не соответствует "
                                   f"размерности {self.dimension!r}")
        if self.answer_type == "quantity" and not self.unit:
            raise PhysicsError(f"{self.id}: ответ-величина требует единицы измерения")
        integer = self.answer_value.denominator == 1
        if not integer and self.tolerance is None and self.rounding is None:
            raise PhysicsError(f"{self.id}: для нецелого ответа нужен допуск или округление")
        if self.unit_policy == "required" and not self.unit:
            raise PhysicsError(f"{self.id}: обязательная единица не задана")
        # домены: время неотрицательно, масса положительна и т.п.
        allowed = {"positive", "nonnegative", "nonzero", "any"}
        for symbol, rule in self.domain.items():
            if rule not in allowed:
                raise PhysicsError(f"{self.id}: неизвестное условие домена {rule!r}")
        self.accept = self._accepted_forms()
        self.checks.append("значение")
        self._self_check()

    def _accepted_forms(self) -> list[str]:
        """Все записи, которые приложение обязано принять как верные."""
        value, unit = self.answer_value, self.unit
        forms: list[str] = []
        unit_ru = parse_unit(unit).display("ru") if unit else ""
        unit_en = parse_unit(unit).display("en") if unit else ""
        plain = _plain_number(value)
        for places in (None, self.rounding):
            if places is None:
                forms.append(format_number(value, "ru"))
                forms.append(format_number(value, "en"))
            else:
                forms.append(format_number(value, "ru", places=places))
                forms.append(format_number(value, "en", places=places))
        if abs(value) >= 10 ** 5 or (value != 0 and abs(value) <= Fraction(1, 10 ** 4)):
            forms.append(format_number(value, "ru", scientific=True))
            forms.append(format_number(value, "en", scientific=True))
        for text in (unit_ru, unit_en):
            if text:
                forms.append(f"{plain} {text}")
                forms.append(f"{format_number(value, 'ru')} {unit_ru}")
        if unit:
            alternative = self._alternative_units()
            forms.extend(alternative)
        forms.extend(self.extra_accept)
        # убираем дубликаты, сохраняя порядок
        unique: list[str] = []
        for item in forms:
            item = str(item).strip()
            if item and item not in unique:
                unique.append(item)
        return unique

    def _alternative_units(self) -> list[str]:
        """Верный ответ в соседних единицах: «36 км/ч» для «10 м/с» и т.п."""
        if not self.unit or self.answer_type == "choice":
            return []
        unit = parse_unit(self.unit)
        out: list[str] = []
        for candidate in _ALTERNATIVE_UNITS.get(unit.dim.signature(), ()):
            if not candidate:
                continue
            try:
                other = Q(self.answer_value, unit).to(candidate)
            except QuantityError:
                continue
            if other.unit.dim == parse_dim("K") and unit.dim == parse_dim("K"):
                if not self.celsius_answer and candidate == "°C":
                    continue      # температуру в °C принимаем только там, где это уместно
            text = other.unit.display("ru")
            out.append(f"{_plain_number(other.value)} {text}")
            out.append(f"{format_number(other.value, 'ru')} {text}")
            out.append(f"{format_number(other.value, 'en')} {other.unit.display('en')}")
        return out

    def _self_check(self) -> None:
        """Ответ обязан проходить собственную проверку — и не проходить чужие."""
        spec = self.spec()
        for form in self.accept:
            result = check_answer(form, spec)
            if not result.ok:
                raise PhysicsError(f"{self.id}: принимаемая запись {form!r} не проходит проверку "
                                   f"({result.reason})")
        wrong = self._wrong_forms()
        for form in wrong:
            if check_answer(form, spec).ok:
                raise PhysicsError(f"{self.id}: неверная запись {form!r} принимается за верную")
        self.checks.append("самопроверка")

    def _wrong_forms(self) -> list[str]:
        """Записи, которые обязаны быть отвергнуты (для сборки и тестов)."""
        value = self.answer_value
        forms: list[str] = []
        if value != 0:
            forms.append(_plain_number(value * 2 if value > 0 else value / 2))
        if self.unit:
            unit = parse_unit(self.unit)
            for foreign in ("кг", "Н", "с", "Дж", "м", "км/ч"):
                foreign_unit = unit_of(foreign)
                if foreign_unit is None or foreign_unit.dim == unit.dim:
                    continue
                forms.append(f"{_plain_number(value)} {foreign}")
        if self.unit and (self.unit_policy == "required"):
            forms.append(_plain_number(value))       # единицу обязательно указывать
        return forms

    # -- сериализация -------------------------------------------------------- #
    def spec(self) -> dict:
        """Контракт проверки для приложений (совпадает с quantities.check_answer)."""
        spec = {
            "answerType": self.answer_type,
            "answerValue": _plain_number(self.answer_value) if self.answer_value is not None else None,
            "accept": list(self.answer_display.values()) if self.answer_type == "choice" else [],
        }
        if self.answer_type == "choice":
            return spec
        if self.unit:
            spec["unit"] = self.unit
        spec["unitPolicy"] = self.unit_policy or ("named" if self.unit else "optional")
        spec["dimension"] = self.dimension
        if self.tolerance is not None:
            spec["tolerance"] = _tolerance_json(self.tolerance)
        if self.rounding is not None:
            spec["rounding"] = self.rounding
        return spec

    def to_json(self) -> dict:
        payload = {
            "id": self.id,
            "year": self.year,
            "part": self.part,
            "n": self.n,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "answerType": self.answer_type,
            "text": bi(self._render(self.text_ru, "ru"), self._render(self.text_en, "en")),
            "options": ({"ru": list(self.options["ru"]), "en": list(self.options["en"])}
                        if self.answer_type == "choice" else None),
            "answer": bi(self.answer_display["ru"], self.answer_display["en"])
                      if isinstance(self.answer_display, dict) else bi(self.answer_display),
            "accept": self.accept,
            "solution": {"ru": self.solution_ru, "en": self.solution_en},
            "hints": {"ru": self.hints_ru, "en": self.hints_en},
            "tools": self.tools,
            "src": self.src,
            "tags": self.tags,
        }
        if self.answer_type != "choice":
            payload.update({
                "unit": bi(parse_unit(self.unit).display("ru"), parse_unit(self.unit).display("en"))
                        if self.unit else None,
                "unitPolicy": self.unit_policy or ("named" if self.unit else "optional"),
                "dimension": self.dimension,
                "tolerance": _tolerance_json(self.tolerance),
                "rounding": self.rounding,
                "given": self.given,
                "spec": self.spec(),
            })
            if getattr(self, "distractors", None):
                payload["distractors"] = {"ru": list(self.distractors["ru"]),
                                          "en": list(self.distractors["en"])}
        else:
            payload["given"] = self.given
            if getattr(self, "distractors", None):
                payload["distractors"] = {"ru": list(self.distractors["ru"]),
                                          "en": list(self.distractors["en"])}
        if self.model:
            payload["model"] = {
                "formula": bi(self.model["formula"], self.model.get("formula_en")),
                "dim": self.model["dim"],
                "vars": self.model["vars"],
                "ask": self.model.get("ask"),
            }
        return payload

    def _render(self, text: str, lang: str) -> str:
        """Подставить значения данных вместо шаблонов ``{symbol}``."""
        out = text
        for entry in self.given:
            token = "{" + entry["symbol"] + "}"
            if token in out:
                value = entry["value_ru"] if lang == "ru" else entry["value_en"]
                out = out.replace(token, value)
        return out


# --------------------------------------------------------------------------- #
#  Авторские конструкторы / authoring helpers
# --------------------------------------------------------------------------- #

def _check_placeholders(task_id: str, text: str, given, lang: str) -> None:
    known = {entry["symbol"] for entry in given}
    for token in re.findall(r"\{(\w+)\}", text):
        if token not in known:
            raise PhysicsError(f"{task_id}: в тексте есть {token!r} без данных "
                               f"({lang}) — подстановка останется незаполненной")
    for entry in given:
        token = "{" + entry["symbol"] + "}"
        if token in text:
            continue
        value = entry["value_ru"] if lang == "ru" else entry["value_en"]
        if not _appears(value, text):
            raise PhysicsError(f"{task_id}: значение {value!r} ({entry['symbol']}) не встречается "
                               f"в тексте ({lang})")


def _appears(value: str, text: str) -> bool:
    pattern = r"(?<![\d,.])" + re.escape(value) + r"(?![\d])"
    return re.search(pattern, text) is not None


def _given_entries(symbols, data, display, lang_label) -> list[dict]:
    entries = []
    for symbol, (value, unit) in data.items():
        unit_obj = parse_unit(unit)
        entries.append({
            "symbol": symbol,
            "name": display.get(symbol, symbol),
            "value_ru": format_number(value, "ru"),
            "value_en": format_number(value, "en"),
            "unit": bi(unit_obj.display("ru"), unit_obj.display("en")),
            "unit_symbol": unit_obj.display(lang_label),
        })
    return entries


def _resolve_constants(task_id, vars_, constants) -> dict:
    """Постоянные (g, ρ, k…) → значения в СИ, как обычные данные.

    ``constants`` — символ → либо готовая пара ``(значение, единица)``, либо
    только единица (тогда значение берётся из школьных ``CONVENTIONS``).
    Размерность постоянной обязана быть объявлена в ``vars``: это защищает от
    «магических чисел» в формулах — каждая постоянная названа и объяснена.
    """
    resolved = {}
    for symbol, spec in constants.items():
        if isinstance(spec, (tuple, list)):
            value, unit = spec
        else:
            if symbol not in CONVENTIONS:
                raise PhysicsError(f"{task_id}: постоянная {symbol!r} неизвестна — "
                                   f"задайте значение и единицу")
            value, unit = CONVENTIONS[symbol][0], spec or CONVENTIONS[symbol][1]
        entry = (to_fraction(value), unit)
        if symbol not in vars_:
            raise PhysicsError(f"{task_id}: у постоянной {symbol!r} нет размерности в vars")
        resolved[symbol] = entry
    return resolved


def _solve(task_id, model, vars_, data, constants):
    values_si = {}
    for symbol, (value, unit) in data.items():
        if symbol not in vars_:
            raise PhysicsError(f"{task_id}: для {symbol!r} не указана размерность")
        unit_obj = parse_unit(unit)
        if unit_obj.offset:
            raise PhysicsError(f"{task_id}: данные в °C нужно задавать в кельвинах")
        if unit_obj.dim != parse_dim(vars_[symbol]):
            raise PhysicsError(f"{task_id}: единица {unit!r} не соответствует размерности "
                               f"{vars_[symbol]!r} у символа {symbol!r}")
        values_si[symbol] = Q(value, unit_obj).si()
    for symbol, (value, unit) in constants.items():
        unit_obj = parse_unit(unit)
        if unit_obj.dim != parse_dim(vars_[symbol]):
            raise PhysicsError(f"{task_id}: единица постоянной {symbol!r} не соответствует "
                               f"размерности {vars_[symbol]!r}")
        values_si[symbol] = Q(value, unit_obj).si()
    lhs = model.split("=", 1)[0].strip() if "=" in model else None
    if lhs is None:
        raise PhysicsError(f"{task_id}: модель должна быть записана как «ответ = формула»")
    if lhs not in vars_:
        raise PhysicsError(f"{task_id}: левая часть модели {lhs!r} без размерности")
    try:
        answer_si = eval_model(model, values_si)
    except ModelError as error:
        raise PhysicsError(f"{task_id}: модель не вычисляется — {error}") from error
    return values_si, Fraction(answer_si)


def _solution_steps(task_id, model, display, data, answer_value, target_unit, lang, rounding):
    """Сгенерировать шаги решения: формула → подстановка → результат."""
    rhs = model.split("=", 1)[1] if "=" in model else model
    lhs = model.split("=", 1)[0].strip() if "=" in model else "ответ"
    expression = rhs
    for symbol in sorted(set(display) | set(data), key=len, reverse=True):
        expression = _replace_symbol(expression, symbol, display.get(symbol, symbol))
    expression = expression.replace("*", "·").replace("^2", "²").replace("^3", "³")
    substituted = expression
    for symbol in sorted(data, key=len, reverse=True):
        value, unit = data[symbol]
        text = format_number(value, lang)
        substituted = _replace_symbol(substituted, display.get(symbol, symbol), text)
    unit_text = parse_unit(target_unit).display(lang) if target_unit else ""
    result = format_number(answer_value, lang, places=rounding)
    if lang == "ru":
        return [
            f"Запишем формулу: {display.get(lhs, lhs)} = {expression}.",
            f"Подставим данные: {display.get(lhs, lhs)} = {substituted}.",
            f"Вычислим: {display.get(lhs, lhs)} = {result} {unit_text}.".replace("  ", " ").strip(),
        ]
    return [
        f"Write the formula: {display.get(lhs, lhs)} = {expression}.",
        f"Substitute the data: {display.get(lhs, lhs)} = {substituted}.",
        f"Compute: {display.get(lhs, lhs)} = {result} {unit_text}.".replace("  ", " ").strip(),
    ]


def _replace_symbol(expression: str, symbol: str, replacement: str) -> str:
    return re.sub(r"(?<![A-Za-z_0-9])" + re.escape(symbol) + r"(?![A-Za-z_0-9])", replacement, expression)


def calc_task(*, id, year, part, n, topic, difficulty, ru, en, model, vars, data, ask,
              unit, formula, symbols=None, tolerance=None, rounding=None, alt=None,
              steps_ru=(), steps_en=(), hints_ru=(), hints_en=(), tags=(), tools=None,
              src=None, constants=None, domain=None, celsius_answer=False, answer_type=None,
              literal=False, extra_accept=()):
    """Расчётное задание: ответ выводится из формулы и данных.

    ``model``   — «s = v0*t + a*t^2/2» (левая часть — искомая величина);
    ``vars``    — символ → размерность («t»: «s»);
    ``data``    — символ → (значение, единица) ровно в той записи, что в тексте;
    ``unit``    — единица, в которой требуется ответ;
    ``formula`` — человеческая запись формулы (с индексами) для разбора.
    """
    display = dict(symbols or {})
    constants = _resolve_constants(id, vars, dict(constants or {}))
    data = {key: (to_fraction(value), unit_text) for key, (value, unit_text) in data.items()}
    values_si, answer_si = _solve(id, model, vars, data, constants)
    expected_si = None
    try:
        expected_si = dim_balance(model, vars)
    except ModelError as error:
        raise PhysicsError(f"{id}: формула размерностно не сбалансирована — {error}") from error
    if expected_si != parse_dim(vars[ask]):
        raise PhysicsError(f"{id}: формула даёт {expected_si.signature()}, "
                           f"а ожидается {vars[ask]!r}")
    target = parse_unit(unit)
    if target.dim != parse_dim(vars[ask]):
        raise PhysicsError(f"{id}: единица ответа {unit!r} не соответствует {vars[ask]!r}")
    answer_value = answer_si / target.factor
    if target.offset:
        raise PhysicsError(f"{id}: единица ответа со смещением (°C) не поддерживается")
    if alt:
        alt_formula, alt_extra = (alt if isinstance(alt, tuple) else (alt, {}))
        extra_values = dict(values_si)
        for symbol, (extra_formula, extra_dim) in alt_extra.items():
            extra_values[symbol] = eval_model(extra_formula, extra_values)
            if dim_balance(extra_formula, {**vars, **{s: d for s, (_f, d) in alt_extra.items()}}) \
                    != parse_dim(extra_dim):
                raise PhysicsError(f"{id}: вспомогательная формула {symbol!r} не сходится по размерности")
        second = Fraction(eval_model(alt_formula, extra_values))
        if abs(second - answer_si) > max(Fraction(1, 10 ** 9), abs(answer_si) * Fraction(1, 10 ** 9)):
            raise PhysicsError(f"{id}: второй путь решения даёт другое значение")
    for symbol, rule in (domain or {}).items():
        value = values_si.get(symbol)
        if value is None:
            continue
        if rule == "positive" and value <= 0:
            raise PhysicsError(f"{id}: {symbol} должно быть положительным")
        if rule == "nonnegative" and value < 0:
            raise PhysicsError(f"{id}: {symbol} не может быть отрицательным")
        if rule == "nonzero" and value == 0:
            raise PhysicsError(f"{id}: {symbol} не может быть нулём")
    # «Дано» показывает и данные, и использованные постоянные: ученик видит,
    # какое значение g, ρ или k подставлялось, а не догадывается об этом.
    given = _given_entries(symbols, {**data, **constants}, display, "ru")
    _check_placeholders(id, ru, given, "ru")
    _check_placeholders(id, en, given, "en")
    generated_ru = list(steps_ru) or _solution_steps(id, model, display, data, answer_value, unit, "ru", rounding)
    generated_en = list(steps_en) or _solution_steps(id, model, display, data, answer_value, unit, "en", rounding)
    if steps_ru and steps_en:
        generated_ru, generated_en = list(steps_ru), list(steps_en)
    hints_ru = list(hints_ru) or [f"Формула: {formula}"]
    hints_en = list(hints_en) or [f"Formula: {formula}"]
    answer_display = bi(format_quantity(answer_value, target, "ru", places=rounding),
                        format_quantity(answer_value, target, "en", places=rounding))
    task = Task(
        id=id, year=year, part=part, n=n, topic=topic, difficulty=difficulty,
        answer_type=answer_type or ("quantity" if unit else "number"),
        text_ru=ru, text_en=en, answer_value=answer_value, answer_display=answer_display,
        unit=unit, unit_policy="named", dimension=vars[ask], tolerance=tolerance,
        rounding=rounding, given=given,
        model={"formula": formula, "dim": model, "vars": dict(vars), "ask": ask},
        solution_ru=generated_ru, solution_en=generated_en,
        hints_ru=hints_ru, hints_en=hints_en, tools=tools, src=src, tags=tags,
        constants=constants, domain=domain, celsius_answer=celsius_answer,
        accept=extra_accept, literal=literal)
    task.verify()
    return task


def calc_choice_task(*, id, year, n, topic, difficulty, ru, en, model, vars, data, ask,
                     unit, formula, distractors, symbols=None, tolerance=None, rounding=None,
                     alt=None, hints_ru=(), hints_en=(), tags=(), tools=None, src=None,
                     constants=None, domain=None, steps_ru=(), steps_en=()):
    """Задание части A: верный ответ считается, неверные — типичные ошибки."""
    base = calc_task(id=id, year=year, part="A", n=n, topic=topic, difficulty=difficulty,
                     ru=ru, en=en, model=model, vars=vars, data=data, ask=ask, unit=unit,
                     formula=formula, symbols=symbols, tolerance=tolerance, rounding=rounding,
                     alt=alt, hints_ru=hints_ru, hints_en=hints_en, tags=tags, tools=tools,
                     src=src, constants=constants, domain=domain,
                     steps_ru=steps_ru, steps_en=steps_en)
    target = parse_unit(unit)
    correct_text = format_quantity(base.answer_value, target, "ru", places=rounding)
    options_ru = [(correct_text, None)]
    options_en = [(format_quantity(base.answer_value, target, "en", places=rounding), None)]
    for item in distractors:
        wrong_ru, reason_ru = item[0], item[1]
        wrong_en, reason_en = (item[2], item[3]) if len(item) > 3 else (wrong_ru, reason_ru)
        options_ru.append((wrong_ru, reason_ru))
        options_en.append((wrong_en, reason_en))
    if len(options_ru) != 5:
        raise PhysicsError(f"{id}: нужно ровно 5 вариантов ответа (верный + 4 типичные ошибки)")
    for values in (options_ru, options_en):
        for index, (text, reason) in enumerate(values):
            if index and not reason:
                raise PhysicsError(f"{id}: у неверного варианта {text!r} нет объяснения ошибки")
    base.answer_type = "choice"
    base.options = {"ru": [text for text, _ in options_ru], "en": [text for text, _ in options_en]}
    base.distractors = {"ru": [reason for _, reason in options_ru],
                        "en": [reason for _, reason in options_en]}
    base.correct_index = 0
    base._verify_choice()
    return base


def choice_task(*, id, year, part, n, topic, difficulty, ru, en, options, correct_index,
                solution_ru, solution_en, hints_ru=(), hints_en=(), tags=(), tools=None,
                src=None, given=()):
    """Качественное задание с выбором ответа (без расчёта)."""
    task = Task(id=id, year=year, part=part, n=n, topic=topic, difficulty=difficulty,
                answer_type="choice", text_ru=ru, text_en=en,
                options={"ru": list(options), "en": list(options)},
                correct_index=correct_index, given=list(given),
                solution_ru=solution_ru, solution_en=solution_en,
                hints_ru=hints_ru, hints_en=hints_en, tags=tags, tools=tools, src=src)
    task.verify()
    return task


# --------------------------------------------------------------------------- #
#  Общие векторы ответов / shared answer vectors
# --------------------------------------------------------------------------- #

def _vector(id, note, spec, cases):
    return {"id": id, "note": note, "spec": spec, "cases": cases}


def _spec(unit, dimension, value, tolerance=None, rounding=None, policy="named",
          answer_type="number"):
    spec = {"answerType": answer_type, "answerValue": value, "dimension": dimension,
            "unitPolicy": policy}
    if unit:
        spec["unit"] = unit
    if tolerance is not None:
        spec["tolerance"] = tolerance
    if rounding is not None:
        spec["rounding"] = rounding
    return spec


def _case(text, ok, reason=""):
    return {"input": text, "ok": ok, "reason": reason}


#: Ручной набор пограничных случаев: его обязаны повторить Python, JS и Kotlin.
ANSWER_VECTORS = [
    _vector("unit-kmh", "36 км/ч = 10 м/с — принимается наравне с 10 м/с",
            _spec("м/с", "m/s", "10", tolerance={"kind": "absolute", "value": "0.5"}),
            [_case("10", True), _case("10 м/с", True), _case("36 км/ч", True),
             _case("36", False, "value"), _case("10 км/ч", False, "value")]),
    _vector("unit-cm", "10 см — это 0,1 м, а не 10 м",
            _spec("м", "m", "10", tolerance={"kind": "absolute", "value": "0.5"}),
            [_case("10 м", True), _case("1000 см", True), _case("10 см", False, "value"),
             _case("0,1 м", False, "value")]),
    _vector("dim-newton", "10 Н нельзя принять за 10 кг",
            _spec("кг", "kg", "10", tolerance={"kind": "absolute", "value": "0.1"}),
            [_case("10 кг", True), _case("10000 г", True), _case("10 Н", False, "dimension"),
             _case("10", True)]),
    _vector("unit-required", "Единицу обязали указать — «10» не ответ",
            _spec("м/с", "m/s", "10", tolerance={"kind": "absolute", "value": "0.5"},
                  policy="required"),
            [_case("10 м/с", True), _case("36 км/ч", True), _case("10", False, "missing_unit")]),
    _vector("rounding-boundary", "Границы округления считаются точно",
            _spec("м", "m", "0.05", rounding=2),
            [_case("0,05", True), _case("0,054", True), _case("0,06", False, "value"),
             _case("0,044", False, "value")]),
    _vector("scientific", "1,5·10⁻³ проверяется как 1,5*10^-3",
            _spec("м", "m", "0.0015", tolerance={"kind": "absolute", "value": "0.0005"}),
            [_case("1,5·10⁻³ м", True), _case("1,5*10^-3 м", True), _case("1.5e-3 м", True),
             _case("1,5·10⁻² м", False, "value"), _case("0,0015", True)]),
    _vector("celsius", "Температура: 27 °C = 300,15 К, «27» К — грубая ошибка",
            _spec("К", "K", "300.15", tolerance={"kind": "absolute", "value": "0.5"}),
            [_case("300,15 К", True), _case("27 °C", True), _case("300", True),
             _case("27", False, "value"), _case("300 °C", False, "value")]),
    _vector("mass-units", "Тонны и граммы переводятся, а не подставляются как числа",
            _spec("кг", "kg", "2500", tolerance={"kind": "absolute", "value": "1"}),
            [_case("2,5 т", True), _case("2500 кг", True), _case("2500000 г", True),
             _case("2,5 кг", False, "value"), _case("2,5", False, "value")]),
    _vector("volume-litres", "1 л = 0,001 м³",
            _spec("м^3", "m^3", "0.002", tolerance={"kind": "absolute", "value": "0.0005"}),
            [_case("2 л", True), _case("0,002 м^3", True), _case("2 м^3", False, "value"),
             _case("2", False, "value")]),
    _vector("energy-scientific", "Большие числа: 4,6·10⁷ Дж",
            _spec("Дж", "kg·m^2/s^2", "46000000",
                  tolerance={"kind": "relative", "value": "0.01"}),
            [_case("4,6·10⁷ Дж", True), _case("46 МДж", True), _case("46000000", True),
             _case("4,6·10⁶ Дж", False, "value"), _case("4,6·10⁷ Дж/кг", False, "dimension")]),
    _vector("speed-light", "Допуск по доле задаётся самим заданием",
            _spec("м/с", "m/s", "300000000",
                  tolerance={"kind": "relative", "value": "0.01"}),
            [_case("3·10⁸ м/с", True), _case("3,01·10⁸ м/с", True),
             _case("3,1·10⁸ м/с", False, "value"), _case("3·10⁸", True)]),
    _vector("unknown-unit", "Неизвестная единица отвергается, а не игнорируется",
            _spec("Н", "kg·m/s^2", "10", tolerance={"kind": "absolute", "value": "0.1"}),
            [_case("10 Н", True), _case("10 фунтов", False, "unit"),
             _case("10", True), _case("10,5 Н", False, "value")]),    _vector("fraction", "Обыкновенная дробь «1/2» — это 0,5",
            _spec("1", "1", "0.5", rounding=2),
            [_case("1/2", True), _case("0,5", True), _case("0.50", True),
             _case("3/4", False, "value"), _case("1/0", False, "empty")]),

    _vector("empty-and-junk", "Пустой и мусорный ввод не считаются ответом",
            _spec("м", "m", "5", tolerance={"kind": "absolute", "value": "0.1"}),
            [_case("", False, "empty"), _case("   ", False, "empty"),
             _case("пять", False, "empty"), _case("5 м", True), _case("5,0 м", True)]),
    _vector("temperature-celsius-neg", "Отрицательные температуры по Цельсию",
            _spec("К", "K", "263.15", tolerance={"kind": "absolute", "value": "0.5"}),
            [_case("-10 °C", True), _case("263,15 К", True), _case("-10 К", False, "value")]),
    _vector("choice-format", "Вариант ответа сравнивается с точностью до записи",
            {"answerType": "choice", "answer": "2,5 м", "accept": ["2,5 м"]},
            [_case("2,5 м", True), _case("2.5 м", True), _case("ответ: 2,5 м", True),
             _case("б) 2,5 м", True), _case("2,5м", True), _case("2,5 км", False, "value")]),
]


def vectors_payload(extra=()) -> dict:
    cases = list(ANSWER_VECTORS) + list(extra)
    ids = [case["id"] for case in cases]
    if len(set(ids)) != len(ids):
        raise PhysicsError("векторы ответов содержат повторяющиеся идентификаторы")
    return {"cases": cases, "count": len(cases)}
