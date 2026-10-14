"""kit.py — authoring & verification toolkit for the ЦТ/CT mathematics item bank.

Design goals
------------
1. *One source of truth.*  Every task is authored once (Python) and emitted to a
   language-neutral JSON bank consumed by BOTH the Android app (Kotlin) and the
   Windows app (Go + embedded HTML/JS).
2. *Machine-checked mathematics.*  Every task carries a ``check`` callable that
   re-derives the answer with exact arithmetic (fractions, integer roots, exact
   trig values, ...).  ``tools/build_content.py`` evaluates all of them and
   refuses to build the bank if any answer is wrong.
3. *No runtime dependencies.*  Answers are pre-computed here, therefore neither
   Android nor the Go/JS front-end needs a CAS at runtime.

Formula markup
--------------
Plain Unicode (``x²``, ``√3``, ``π``, ``≤``, ``−``).  Both front-ends render it
verbatim with a math-capable font — no LaTeX engine and no network access are
needed on the device, which matters for the offline exam use-case.
"""

from __future__ import annotations

import math
import re
from fractions import Fraction as _Fraction

__all__ = [
    "F", "R", "E", "num", "dec", "pc", "sgn", "nth_root", "simplify_radical",
    "quad", "Task", "TOPICS", "TOPIC_ORDER", "TOOLS", "ANSWER_VECTORS",
    "normalize_answer", "answer_variants", "check_answer", "is_expression_answer",
    "expression_value",
]

# --------------------------------------------------------------------------- #
#  Точные числа / exact numbers
# --------------------------------------------------------------------------- #

_DECIMAL_LITERAL = re.compile(r"-?\d+\.\d+")


class F(_Fraction):  # noqa: N801 - F(3,4) reads well inside formulas
    """Дробь, которая помнит, как её записали в исходном тексте задания.

    * ``F(1.9)``  → ровно ``19/10`` (десятичная запись из исходника, а не двоичное
      приближение float) и выводится как «1,9»;
    * ``F(11, 2)`` → «11/2» (как записано), а в принимаемых ответах добавляется и
      десятичный вариант «5,5» (см. :func:`answer_variants`).

    A fraction that remembers the literal used in the source, so options and
    answers are printed the way the author wrote them.
    """

    __slots__ = ("literal",)

    def __new__(cls, numerator=0, denominator=None):
        if denominator is None and isinstance(numerator, float):
            exact = _Fraction(str(numerator))
            obj = super().__new__(cls, exact.numerator, exact.denominator)
            obj.literal = str(numerator)
            return obj
        obj = super().__new__(cls, numerator, denominator)
        obj.literal = None
        return obj

    @property
    def written(self) -> str | None:
        """Исходная десятичная запись (``'1.9'``) или ``None``."""
        literal = getattr(self, "literal", None)
        return literal if literal and _DECIMAL_LITERAL.fullmatch(literal) else None


# --------------------------------------------------------------------------- #
#  Number formatting (localised: Russian uses a decimal comma)
# --------------------------------------------------------------------------- #

_GROUP_RE = re.compile(r"(?<![\d.,])(\d+)(\d{3})(?![\d.,])")


def _trim(s: str) -> str:
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return "0" if s in ("", "-", "-0") else s


def _fraction_to_decimal_string(fr: F, max_digits: int = 12) -> str | None:
    """Exact decimal string if the denominator is 2^a*5^b, else None."""
    den = fr.denominator
    a = b = 0
    while den % 2 == 0:
        den //= 2
        a += 1
    while den % 5 == 0:
        den //= 5
        b += 1
    if den != 1:
        return None
    d = max(a, b)
    if d > max_digits:
        return None
    scaled = fr.numerator * (10 ** d) // fr.denominator
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).rjust(d + 1, "0")
    return _trim(f"{sign}{digits[:-d]}.{digits[-d:]}") if d else f"{sign}{digits}"


def num(x, lang: str = "ru", *, decimal: bool = False) -> str:
    """Format a number exactly for a given language.

    * ``F(7, 12)``      -> ``"7/12"``
    * ``F(3, 2)``       -> ``"3/2"``  (``decimal=True`` -> ``"1,5"`` / ``"1.5"``)
    * ``F(2, 1)``       -> ``"2"``
    * floats are printed with at most 10 significant digits, trailing zeros cut.
    """
    if isinstance(x, bool):
        raise TypeError("bool is not a number here")
    if isinstance(x, int):
        s = str(x)
    elif isinstance(x, _Fraction):
        written = x.written if isinstance(x, F) else None
        if written:
            return written.replace(".", ",") if lang == "ru" else written
        if x.denominator == 1:
            s = str(x.numerator)
        elif decimal:
            s = _fraction_to_decimal_string(x)
            if s is None:
                s = f"{x.numerator}/{x.denominator}"
        else:
            s = f"{x.numerator}/{x.denominator}"
    elif isinstance(x, float):
        if x.is_integer() and abs(x) < 1e15:
            s = str(int(x))
        else:
            s = f"{x:.10g}"
            if "e" not in s:
                s = _trim(s)
    else:
        raise TypeError(f"unsupported number type: {type(x)!r}")
    return s.replace(".", ",") if lang == "ru" else s


def R(x, **kw) -> str:  # noqa: N802 - terse on purpose, used inside f-strings
    """Russian formatting shortcut."""
    return num(x, "ru", **kw)


def E(x, **kw) -> str:  # noqa: N802
    """English formatting shortcut."""
    return num(x, "en", **kw)


def dec(x, lang: str = "ru") -> str:
    return num(x, lang, decimal=True)


def pc(x, lang: str = "ru") -> str:
    """Percent: F(3,20) -> ``"15%"`` (percent sign is language neutral here)."""
    return num(F(x) * 100, lang) + "%"


def sgn(x) -> str:
    x = F(x)
    return f"+{num(x)}" if x >= 0 else num(x)


# --------------------------------------------------------------------------- #
#  Exact helpers (used by item authors and by the answer verification pass)
# --------------------------------------------------------------------------- #

def nth_root(n: int, k: int) -> tuple[int, int]:
    """Return ``(outside, inside)`` with ``n = outside^k * inside`` (inside minimal).

    ``nth_root(72, 2) == (6, 2)`` because ``√72 = 6√2``.
    """
    if n < 0:
        raise ValueError("use simplify_radical for sign handling")
    outside, inside = 1, n
    d = 2
    while d * d <= inside:
        e = 0
        while inside % d == 0:
            inside //= d
            e += 1
        outside *= d ** (e // k)
        inside *= d ** (e % k)
        d += 1
    return outside, inside


def simplify_radical(n: int, k: int = 2) -> str:
    """Pretty exact radical: ``simplify_radical(72) -> "6√2"``, ``(8,3) -> "2"``."""
    sign = "−" if n < 0 else ""
    outside, inside = nth_root(abs(n), k)
    if inside == 1:
        return f"{sign}{outside}"
    head = "" if outside == 1 else str(outside)
    if k == 2:
        return f"{sign}{head}√{inside}"
    return f"{sign}{head}{chr(0x2070 + k)}√{inside}".replace("⁰√", "√")


def quad(a, b, c):
    """Exact real roots of ax²+bx+c=0 as a sorted tuple of Fractions (may be 1 or 0)."""
    d = b * b - 4 * a * c
    if d < 0:
        return ()
    r = math.isqrt(d)
    if r * r != d:
        return ()
    return tuple(sorted({F(-b + r, 2 * a), F(-b - r, 2 * a)}))


# --------------------------------------------------------------------------- #
#  Taxonomy
# --------------------------------------------------------------------------- #

TOPICS: dict[str, dict[str, str]] = {
    "numbers":      {"ru": "Числа и вычисления", "en": "Numbers and computation"},
    "expressions":  {"ru": "Тождественные преобразования", "en": "Algebraic expressions"},
    "equations":    {"ru": "Уравнения и системы", "en": "Equations and systems"},
    "inequalities": {"ru": "Неравенства", "en": "Inequalities"},
    "functions":    {"ru": "Функции и графики", "en": "Functions and graphs"},
    "progressions": {"ru": "Прогрессии", "en": "Progressions"},
    "wordproblems": {"ru": "Текстовые задачи", "en": "Word problems"},
    "trig":         {"ru": "Тригонометрия", "en": "Trigonometry"},
    "trigequations":{"ru": "Тригонометрические уравнения", "en": "Trigonometric equations"},
    "logexp":       {"ru": "Показательные и логарифмические", "en": "Exponential and logarithmic"},
    "planimetry":   {"ru": "Планиметрия", "en": "Plane geometry"},
    "stereometry":  {"ru": "Стереометрия", "en": "Solid geometry"},
    "derivative":   {"ru": "Производная", "en": "Derivative"},
    "research":     {"ru": "Исследование функций", "en": "Function study"},
    "combinatorics":{"ru": "Комбинаторика и вероятность", "en": "Combinatorics and probability"},
    "vectors":      {"ru": "Векторы и координаты", "en": "Vectors and coordinates"},
    "param":        {"ru": "Задачи с параметром", "en": "Problems with a parameter"},
    "logic":        {"ru": "Логика и последовательности", "en": "Logic and sequences"},
}

#: Order used by the UI when listing topics (mirrors the ЦТ А1…А18 order).
TOPIC_ORDER: list[str] = list(TOPICS.keys())

TOOLS: dict[str, dict[str, str]] = {
    "calc":    {"ru": "Калькулятор", "en": "Calculator"},
    "sheet":   {"ru": "Сборник формул", "en": "Formula sheet"},
    "scratch": {"ru": "Черновик", "en": "Scratchpad"},
    "graph":   {"ru": "Построение графика", "en": "Function plotter"},
    "hint":    {"ru": "Подсказка", "en": "Hint"},
}

# Vectors shared with Kotlin/JVM and JavaScript implementations of the answer
# checker — filled by the build script, then dumped to dist/content/.
ANSWER_VECTORS: list[dict] = []


# --------------------------------------------------------------------------- #
#  Answer checking (identical algorithm is re-implemented in Kotlin and JS)
# --------------------------------------------------------------------------- #

_MINUSES = "−–—‒"
_SPACES = " \u00a0\u2009\u202f\t"


def normalize_answer(s) -> str:
    """Canonical form used by **every** platform (Python, JavaScript, Kotlin).

    The same rules are implemented in ``webapp/core.js`` (``CT.answer.normalize``)
    and in ``android/.../AnswerChecker.kt``; the shared vectors in
    ``dist/content/answer_vectors.json`` are what keeps the three copies honest.

    * lower-cases and strips the input;
    * removes spaces (ordinary, non-breaking, thin, figure) — «1 000» == «1000»;
    * unifies every Unicode minus/dash to ``-`` and ``× · ∙`` to ``*``;
    * unifies the Cyrillic letters «х»/«у» used instead of Latin x/y;
    * writes ``π`` as ``pi`` and ``√`` as ``sqrt``;
    * drops a leading ``ответ:``/``answer:`` or a single letter with ``=``/``:``
      («x = 12»);
    * unwraps one level of parentheses and turns the decimal comma into a dot.
    """
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("\u00a0", " ")
    for m in _MINUSES:
        s = s.replace(m, "-")
    for ch in ("×", "·", "∙"):
        s = s.replace(ch, "*")
    s = s.replace("х", "x").replace("у", "y")
    s = s.replace("π", "pi").replace("√", "sqrt")
    s = re.sub(r"^(ответ|answer)\s*[:=]?\s*", "", s)
    s = re.sub(r"^[a-zа-я]{1,2}\s*[:=]\s*", "", s)
    for sp in _SPACES:
        s = s.replace(sp, "")
    s = re.sub(r"^\((.*)\)$", r"\1", s)
    s = s.replace(",", ".")
    if s.endswith("."):
        s = s[:-1]
    return s


def _as_fraction(s: str):
    """Parse ``s`` as an exact number (int / fraction / decimal) or return None."""
    if not s:
        return None
    if "/" in s:
        a, _, b = s.partition("/")
        try:
            fa, fb = F(a), F(b)
        except (ValueError, ZeroDivisionError):
            return None
        return fa / fb if fb != 0 else None
    try:
        return F(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
#  Оценка простых выражений (та же грамматика, что в JS и Kotlin)
#  Evaluation of simple expressions: numbers, + - * / % ^, parentheses,
#  sqrt/abs/sin/cos/tan/ln/lg, constants pi and e, implicit multiplication
#  («6√2», «2π» читаются как 6·√2 и 2·π).
# --------------------------------------------------------------------------- #

_EVAL_NUMBER = re.compile(r"(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?")


def _tokenize_expr(src: str):
    tokens, i = [], 0
    while i < len(src):
        ch = src[i]
        if ch.isspace():
            i += 1
            continue
        match = _EVAL_NUMBER.match(src, i)
        if match and any(character.isdigit() for character in match.group(0)):
            tokens.append(("num", float(match.group(0))))
            i = match.end()
            continue
        if ch.isalpha() or ch == "_":
            match = re.compile(r"[a-zA-Zа-яА-Я_]+").match(src, i)
            tokens.append(("name", match.group(0).lower()))
            i = match.end()
            continue
        if ch in "+-*/^%()":
            tokens.append(("op", ch))
            i += 1
            continue
        raise ValueError(f"bad symbol {ch!r}")
    return tokens


_EXPR_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "tg": math.tan, "ln": math.log, "lg": lambda x: math.log10(x), "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
}
_EXPR_CONSTS = {"pi": math.pi, "e": math.e, "tau": 2 * math.pi}


def _eval_tokens(tokens):
    """Recursive-descent parser; returns a value or raises ValueError."""
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        token = peek()
        pos += 1
        return token

    def starts_atom(token):
        if token is None:
            return False
        if token[0] == "num":
            return True
        if token[0] == "name":
            return True
        return token == ("op", "(")

    def expression():
        node = term()
        while peek() in (("op", "+"), ("op", "-")):
            op = take()[1]
            node = node + term() if op == "+" else node - term()
        return node

    def term():
        node = unary()
        while True:
            token = peek()
            if token in (("op", "*"), ("op", "/"), ("op", "%")):
                op = take()[1]
                right = unary()
                if op == "*":
                    node *= right
                elif op == "/":
                    node /= right
                else:
                    node %= right
                continue
            # неявное умножение: «6√2», «2π», «3(4+1)»
            if starts_atom(token):
                node *= unary()
                continue
            return node

    def unary():
        if peek() in (("op", "-"), ("op", "+")):
            op = take()[1]
            value = unary()
            return -value if op == "-" else value
        return power()

    def power():
        base = atom()
        if peek() == ("op", "^"):
            take()
            return base ** unary()
        return base

    def atom():
        token = take()
        if token is None:
            raise ValueError("unexpected end of expression")
        if token[0] == "num":
            return token[1]
        if token[0] == "name":
            name = token[1]
            if name in _EXPR_FUNCS and peek() == ("op", "("):
                take()
                argument = expression()
                if take() != ("op", ")"):
                    raise ValueError("missing )")
                return _EXPR_FUNCS[name](argument)
            if name in _EXPR_FUNCS:
                return _EXPR_FUNCS[name](power())      # «sqrt2», «sin pi/6»
            if name in _EXPR_CONSTS:
                return _EXPR_CONSTS[name]
            raise ValueError(f"unknown name {name!r}")
        if token == ("op", "("):
            value = expression()
            if take() != ("op", ")"):
                raise ValueError("missing )")
            return value
        raise ValueError("unexpected token")

    value = expression()
    if pos != len(tokens):
        raise ValueError("trailing input")
    return value


def expression_value(text):
    """Numeric value of a simple expression, ``None`` when unparsable.

    Mirrors ``CT.math.value`` in the interface and ``AnswerChecker.value`` in the
    Android build, so all three platforms compare answers the same way.
    """
    if text is None:
        return None
    source = str(text)
    for old, new in (("−", "-"), ("×", "*"), ("·", "*"), ("∙", "*"), ("√", "sqrt"),
                     ("π", "pi"), ("**", "^")):
        source = source.replace(old, new)
    source = source.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    source = source.replace("²", "^2").replace("³", "^3")
    try:
        value = _eval_tokens(_tokenize_expr(source))
    except (ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def is_expression_answer(text) -> bool:
    """Ответ записан выражением (корень, π, дробная степень), а не просто числом."""
    normalized = normalize_answer(text)
    if not normalized:
        return False
    if _as_fraction(normalized) is not None:
        return False
    return any(marker in normalized for marker in ("sqrt", "pi", "^", "(", ")"))


def check_answer(user: str, task: dict) -> bool:
    """Decide whether ``user`` is a correct answer for ``task``.

    Four tiers, identical on every platform:

    1. canonical string match against the accepted spellings;
    2. choice tasks stop here (a lucky number is not an answer);
    3. exact numeric equality (``8/10`` == ``0,8`` == ``0.80``);
    A whole-number answer must be exact; the rounding band is reserved for
    non-integer candidates (``5/6`` vs ``0,833``) and for expressions with roots
    or π (``√2/2`` vs ``0,707``, ``2π`` vs ``6,28``).
    """
    nu = normalize_answer(user)
    if not nu:
        return False
    accepted = [normalize_answer(v) for v in task.get("accept", []) if v not in (None, "")]
    if nu in accepted:
        return True
    if task.get("answerType") == "choice":
        return False
    fu = _as_fraction(nu)
    if fu is not None:
        for v in accepted:
            fv = _as_fraction(v)
            if fv is None:
                continue
            if fv == fu:
                return True
            # снисходительность — только к «нецелым» ответам (1/3, 5/6, 3/7):
            # округление до трёх знаков не должно превращать 1000,5 в 1000
            if fv.denominator == 1:
                continue
            if abs(float(fu) - float(fv)) <= 5e-4 * max(1.0, abs(float(fv))):
                return True
    user_value = expression_value(nu)
    if user_value is None:
        return False
    user_is_expression = is_expression_answer(nu)
    for v in accepted:
        # третий рубеж включается только когда хотя бы одна сторона записана
        # выражением («√2/2», «2π»): обычные числа уже сравнены точно, и
        # снисходительность здесь была бы неуместна («1000,5» против «1000»)
        if not user_is_expression and not is_expression_answer(v):
            continue
        candidate = expression_value(v)
        if candidate is None:
            continue
        if abs(user_value - candidate) <= 1e-3 * max(1.0, abs(candidate)):
            return True
    return False


def answer_variants(answer, lang: str = "ru") -> list[str]:
    """All sensible spellings of a correct answer, for the ``accept`` list."""
    out: list[str] = []
    if isinstance(answer, (F, int, float)):
        fr = F(answer)
        out.append(num(fr, "en"))
        out.append(num(fr, "ru"))
        if fr.denominator != 1:
            out.append(num(fr, "en", decimal=True))
            out.append(num(fr, "ru", decimal=True))
        if fr.denominator in (2, 4, 5, 8, 10, 16, 20, 25, 40, 50):
            d = _fraction_to_decimal_string(fr)
            if d:
                out.append(d)
                out.append(d.replace(".", ","))
            # rounded 3-decimal form (students round): 0,583
            out.append(f"{float(fr):.3f}".rstrip("0").rstrip("."))
        if fr < 0:
            out.append(num(fr, "en").replace("-", "−"))
    else:
        out.append(str(answer))
    if lang == "en":
        out.append("")
    seen, res = set(), []
    for v in out:
        if v and v not in seen:
            seen.add(v)
            res.append(v)
    return res


# --------------------------------------------------------------------------- #
#  Task authoring
# --------------------------------------------------------------------------- #

class Task:
    """One exam-style item.

    Parameters
    ----------
    id        stable identifier, e.g. ``ct-2024-a7`` (never reuse / rename!)
    year      exam year (or 0 for the generated "analogous tasks" pool)
    part      ``"A"`` = 5-option choice (ЦТ А1…А18), ``"B"`` = short answer (В1…В12)
    n         number inside the part (1…18 for A, 1…12 for B)
    topic     key of :data:`TOPICS`
    ru/en     statement text
    options   A-part only: exactly 5 values (numbers are localised automatically,
              strings are used verbatim)
    answer    the correct value; must be one of *options* for the A part
    ru_sol/en_sol  step-by-step solution ("разбор"), 2…6 steps
    ru_hints/en_hints  progressive hints shown by the "hint" tool
    tools     available instruments, keys of :data:`TOOLS`
    check     zero-argument callable returning True — re-derives the answer
    accept    extra accepted spellings for the B part
    src       provenance note, e.g. "по мотивам ЦТ 2024"
    """

    def __init__(self, *, id, year, part, n, topic, ru, en, answer,
                 options=None, ru_sol, en_sol, ru_hints=(), en_hints=(),
                 tools=("calc", "sheet", "scratch"), check=None, accept=(),
                 difficulty=2, src=None, tags=()):
        if topic not in TOPICS:
            raise ValueError(f"{id}: unknown topic {topic!r}")
        if part not in ("A", "B"):
            raise ValueError(f"{id}: part must be A or B")
        for t in tools:
            if t not in TOOLS:
                raise ValueError(f"{id}: unknown tool {t!r}")
        if not callable(check):
            raise ValueError(f"{id}: a check() lambda is mandatory")
        if part == "A":
            if not options or len(options) != 5:
                raise ValueError(f"{id}: part A needs exactly 5 options")
            if not any(_values_equal(o, answer) for o in options):
                raise ValueError(f"{id}: answer {answer!r} absent from options {options!r}")
            if sum(1 for o in options if _values_equal(o, answer)) != 1:
                raise ValueError(f"{id}: duplicated correct option in {options!r}")
        if not ru_sol or not en_sol:
            raise ValueError(f"{id}: solution steps required in both languages")
        self.id = id
        self.year = year
        self.part = part
        self.n = n
        self.topic = topic
        self.ru = ru
        self.en = en
        self.options = list(options) if options else None
        self.answer = answer
        self.ru_sol = list(ru_sol)
        self.en_sol = list(en_sol)
        self.ru_hints = list(ru_hints)
        self.en_hints = list(en_hints)
        self.tools = list(tools)
        self.check = check
        self.accept = list(accept)
        self.difficulty = difficulty
        self.src = src or (f"по мотивам ЦТ {year}" if year else "авторское задание")
        self.tags = list(tags)

    # -- serialisation ----------------------------------------------------- #

    def to_json(self) -> dict:
        ru_opts = [num(o, "ru") if isinstance(o, (int, F, float)) else str(o)
                   for o in (self.options or [])]
        en_opts = [num(o, "en") if isinstance(o, (int, F, float)) else str(o)
                   for o in (self.options or [])]
        answer_type = "choice" if self.part == "A" else "short"
        if self.part == "A":
            correct = next(i for i, o in enumerate(self.options)
                           if _values_equal(o, self.answer))
            answer_disp = {"ru": ru_opts[correct], "en": en_opts[correct]}
            accept = [ru_opts[correct], en_opts[correct]]
        else:
            answer_disp = {"ru": _disp(self.answer, "ru"), "en": _disp(self.answer, "en")}
            accept = list(self.accept) + answer_variants(self.answer)
        return {
            "id": self.id,
            "year": self.year,
            "part": self.part,
            "n": self.n,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "answerType": answer_type,
            "text": {"ru": self.ru, "en": self.en},
            "options": {"ru": ru_opts, "en": en_opts} if self.options else None,
            "answer": answer_disp,
            "accept": _dedup(accept),
            "solution": {"ru": self.ru_sol, "en": self.en_sol},
            "hints": {"ru": self.ru_hints, "en": self.en_hints},
            "tools": self.tools,
            "src": self.src,
            "tags": self.tags,
        }

    # -- verification ------------------------------------------------------ #

    def verify(self) -> None:
        """Run the author-supplied exact-arithmetic check."""
        try:
            ok = self.check()
        except Exception as exc:  # pragma: no cover - surfacing authoring bugs
            raise AssertionError(f"{self.id}: check() raised {exc!r}") from exc
        if ok is not True:
            raise AssertionError(f"{self.id}: check() returned {ok!r}")


def _values_equal(a, b) -> bool:
    if isinstance(a, (int, F, float)) and isinstance(b, (int, F, float)):
        return F(a) == F(b)
    return normalize_answer(a) == normalize_answer(b)


def _disp(x, lang: str) -> str:
    return num(x, lang) if isinstance(x, (int, F, float)) else str(x)


def _dedup(seq) -> list:
    seen, out = set(), []
    for v in seq:
        k = str(v)
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out
