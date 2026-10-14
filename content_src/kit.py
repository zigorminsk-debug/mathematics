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
from fractions import Fraction as F  # noqa: N817  (F(3,4) reads well)

__all__ = [
    "F", "R", "E", "num", "dec", "pc", "sgn", "nth_root", "simplify_radical",
    "quad", "Task", "TOPICS", "TOPIC_ORDER", "TOOLS", "ANSWER_VECTORS",
    "normalize_answer", "answer_variants", "check_answer",
]

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
    elif isinstance(x, F):
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
    """Canonical form used by every platform.

    * drops spaces / non-breaking spaces
    * unifies all Unicode minus signs and dashes to ``-``
    * unifies decimal comma to a dot
    * drops a leading ``x=``, ``y=``, ``n=``, ``a=``, ``ответ:`` / ``answer:``
    * unifies ``*`` to ``·``, ``√`` variants keep as is
    * lower-cases and strips the trailing dot
    """
    if s is None:
        return ""
    s = str(s)
    for m in _MINUSES:
        s = s.replace(m, "-")
    s = s.replace("\u2212", "-")
    for sp in _SPACES:
        s = s.replace(sp, "")
    s = s.strip().lower()
    s = re.sub(r"^(ответ|answer)\s*[:=]\s*", "", s)
    s = re.sub(r"^[a-zа-я]\s*=\s*", "", s)
    if s.endswith("."):
        s = s[:-1]
    s = s.replace("*", "·")
    s = s.replace(":", ":").replace(";", ";")
    s = s.replace("√", "√").replace("⌄", "√")
    s = s.replace("pi", "π").replace("пі", "π")
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


def check_answer(user: str, task: dict) -> bool:
    """Decide whether ``user`` is a correct answer for ``task``.

    Three tiers: exact string match against the accepted variants, exact numeric
    equality (so ``8/10`` == ``0,8`` == ``0.80``), and a numeric-equality fallback
    for simple decimal approximations the student typed by hand.
    """
    nu = normalize_answer(user)
    if not nu:
        return False
    accepted = [normalize_answer(v) for v in task.get("accept", [])]
    if nu in accepted:
        return True
    if task.get("answerType") == "choice":
        return False
    fu = _as_fraction(nu)
    if fu is None:
        return False
    for v in accepted:
        fv = _as_fraction(v)
        if fv is not None and fv == fu:
            return True
    # decimal approximation written by the student: |u - v| <= 5e-4
    for v in accepted:
        fv = _as_fraction(v)
        if fv is not None and abs(float(fu) - float(fv)) < 5e-4:
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
