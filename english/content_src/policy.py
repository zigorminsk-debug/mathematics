"""content_src/policy.py — политика проверки ответа (нормативный источник).

Правила языка нельзя проверять «математическим» нормализатором: в английских
упражнениях **пробел, дефис, апостроф и порядок слов часто и есть ответ**.
Поэтому каждое задание явно описывает, что допускается, а этот модуль реализует
ровно эти операции. Тот же алгоритм повторён в ``webapp/core.js``
(``CT.answer``) и в ``android/.../AnswerChecker.kt``; совпадение трёх реализаций
проверяется общими векторами ``dist/content/answer_vectors.json``.

Политики (ключи словаря ``policy`` в задании):

``case``        ``insensitive`` (по умолчанию) | ``sensitive`` — для имён собственных
                и заданий, где важна заглавная буква.
``article``     ``checked`` (по умолчанию: артикль — часть ответа) | ``ignored``
                (артикль не проверяется: ни лишний, ни пропущенный не мешает).
``apostrophe``  ``ignore`` (по умолчанию) | ``required`` — считается ли апостроф
                частью проверяемой формы (``don't`` / ``dont``).
``hyphen``      ``significant`` (по умолчанию) | ``ignore`` — влияет ли дефис
                (``well-known`` против ``wellknown``).
``space``       ``significant`` (по умолчанию) | ``collapse`` — можно ли схлопывать
                пробелы внутри ответа (по умолчанию НЕЛЬЗЯ: ``a lot`` ≠ ``alot``).
``stress``      ``significant`` (по умолчанию) | ``ignore`` — диакритика (café/cafe).
``empty``       ``reject`` (по умолчанию) | ``accept`` — бывает задание, где пропуск
                должен остаться пустым (артикль не нужен): пустой ответ верен, а
                лишнее слово — нет.

Причины отказа (одинаковы во всех трёх реализациях), в порядке проверки:

``empty``       пустой ввод (в том числе после обрезки пробелов);
``article``     разница ровно в артикле: лишний или пропущенный;
``case``        ответ верный, но регистр не совпал при ``case: sensitive``;
``apostrophe``  верный ответ без обязательного апострофа;
``hyphen``      верный ответ с другим дефисом или без него;
``space``       пробелы расставлены иначе (лишний, пропущенный или двойной);
``stress``      различается только диакритика (café против cafe);
``near``        «почти совпало»: другая форма слова, лишний знак или лишнее слово;
``exact``       полное несовпадение со всеми допустимыми вариантами;
``ok``          ответ принят.

Причина нужна интерфейсу: он показывает не «неверно», а **что именно** не
совпало, и предлагает правило для разбора.
"""

from __future__ import annotations

import re
import unicodedata

#: значение «пропуск должен остаться пустым» в ответе задания
NOTHING = "—"

#: значения по умолчанию: то, что задание не уточнило
DEFAULT_POLICY = {
    "case": "insensitive",
    "article": "checked",
    "apostrophe": "ignore",
    "hyphen": "significant",
    "space": "significant",
    "stress": "significant",
    "empty": "reject",
}

#: порядок ключей одинаков во всех реализациях (для читаемых diff'ов)
POLICY_KEYS = ("case", "article", "apostrophe", "hyphen", "space", "stress", "empty")

#: допустимые значения — их проверяет сборка контента
ALLOWED = {
    "case": ("insensitive", "sensitive"),
    "article": ("checked", "ignored"),
    "apostrophe": ("ignore", "required"),
    "hyphen": ("significant", "ignore"),
    "space": ("significant", "collapse"),
    "stress": ("significant", "ignore"),
    "empty": ("reject", "accept"),
}

APOSTROPHES = "\u2019\u02bc\u2018'`"
DASHES = "\u2010\u2011\u2012\u2013\u2014\u2212"
ARTICLES = ("a", "an", "the")


def policy_for(task: dict) -> dict:
    """Политика задания с подставленными значениями по умолчанию."""
    merged = dict(DEFAULT_POLICY)
    merged.update(task.get("policy") or {})
    unknown = set(merged) - set(DEFAULT_POLICY)
    if unknown:
        raise ValueError(f"неизвестные ключи политики: {sorted(unknown)}")
    for key, value in merged.items():
        if value not in ALLOWED[key]:
            raise ValueError(f"{task.get('id')}: политика {key}={value!r} недопустима, "
                             f"ожидается одно из {ALLOWED[key]}")
    return merged


def normalize(text: str, policy: dict) -> str:
    """Привести ответ к сравнимому виду **только** по разрешённым правилам."""
    if text is None:
        return ""
    value = str(text).replace("\u00a0", " ")
    # дефис: либо один и тот же знак, либо не значим вовсе
    for dash in DASHES:
        value = value.replace(dash, "-" if policy["hyphen"] == "significant" else "")
    if policy["hyphen"] != "significant":
        value = value.replace("-", "")
    # апостроф: либо один и тот же знак, либо не значим вовсе
    for apostrophe in APOSTROPHES:
        value = value.replace(apostrophe, "'" if policy["apostrophe"] == "required" else "")
    # диакритика
    if policy["stress"] == "ignore":
        value = _without_diacritics(value)
    if policy["space"] == "collapse":
        value = re.sub(r"\s+", " ", value)
    value = value.strip()
    if policy["case"] == "insensitive":
        # регистр снимается до артиклей: иначе «The» не распознаётся как артикль
        value = value.lower()
    if policy["article"] == "ignored":
        # удаление артикля может оставить лишний пробел — его схлопываем всегда:
        # это следствие нормализации, а не расстановка пробелов пользователем
        value = re.sub(r"\s+", " ", _drop_articles(value)).strip()
    return value


def check(task: dict, typed: str) -> dict:
    """Сравнить ввод с допустимыми ответами задания.

    Порядок причин отказа — часть контракта (его повторяют JavaScript и Kotlin):
    ``empty → case → apostrophe → hyphen → space → article → stress → near → exact``.
    Он выбран так, чтобы интерфейс показывал самую полезную подсказку.
    """
    policy = policy_for(task)
    accepted = [task.get("answer", {}).get("value", "")]
    accepted += list(task.get("accepted") or [])
    accepted = [item for item in accepted if item != ""]
    if not accepted:
        raise ValueError(f"у задания {task.get('id')!r} нет допустимого ответа")

    got_raw = "" if typed is None else str(typed).strip()
    got = normalize(got_raw, policy)
    if got == "":
        # «ничего не нужно» — законный ответ задания, объявившего empty: accept
        if policy["empty"] == "accept":
            return {"ok": True, "reason": "ok", "expected": "", "got": got_raw}
        return {"ok": False, "reason": "empty", "expected": accepted[0], "got": got_raw}

    # задание, где пропуск должен остаться пустым: любое слово — уже ошибка
    if accepted == [NOTHING]:
        reason = "article" if _without_articles(_tokens(got)) != _tokens(got) else "exact"
        return {"ok": False, "reason": reason, "expected": "", "got": got_raw}

    expected_norms = [normalize(item, policy) for item in accepted]
    if got in expected_norms:
        return {"ok": True, "reason": "ok", "expected": accepted[0], "got": got_raw}

    for expected, expected_norm in zip(accepted, expected_norms):
        if _differs_only_by_case(got, expected_norm, policy):
            return {"ok": False, "reason": "case", "expected": expected, "got": got_raw}
        if policy["apostrophe"] == "required" and _strip_apostrophes(got) == _strip_apostrophes(expected_norm):
            return {"ok": False, "reason": "apostrophe", "expected": expected, "got": got_raw}
        if policy["hyphen"] == "significant" and (
                expected_norm.replace("-", " ") == got or expected_norm.replace("-", "") == got):
            return {"ok": False, "reason": "hyphen", "expected": expected, "got": got_raw}
        if policy["space"] == "significant" and _collapse(got) == _collapse(expected_norm):
            return {"ok": False, "reason": "space", "expected": expected, "got": got_raw}
        if (_without_articles(_tokens(expected_norm)) == _without_articles(_tokens(got))
                and got != expected_norm):
            return {"ok": False, "reason": "article", "expected": expected, "got": got_raw}
        if policy["stress"] == "significant" and _without_diacritics(got) == _without_diacritics(expected_norm):
            return {"ok": False, "reason": "stress", "expected": expected, "got": got_raw}
        if _near(got, expected_norm):
            return {"ok": False, "reason": "near", "expected": expected, "got": got_raw}
    return {"ok": False, "reason": "exact", "expected": accepted[0], "got": got_raw}


def describe_policy(policy: dict) -> str:
    """Короткая человеческая расшифровка политики (для интерфейса и отчёта)."""
    parts = []
    if policy["case"] == "sensitive":
        parts.append("регистр букв важен")
    if policy["article"] == "ignored":
        parts.append("артикль не проверяется")
    if policy["apostrophe"] == "required":
        parts.append("апостроф обязателен")
    if policy["hyphen"] == "ignore":
        parts.append("дефис не проверяется")
    if policy["space"] == "collapse":
        parts.append("пробелы можно схлопывать")
    if policy["stress"] == "ignore":
        parts.append("диакритика не проверяется")
    if policy["empty"] == "accept":
        parts.append("если ничего не нужно, поле остаётся пустым")
    return "; ".join(parts) if parts else "точное совпадение"


def _is_combining(char: str) -> bool:
    code = ord(char)
    return 0x0300 <= code <= 0x036F or code in (0x00B4, 0x02CA, 0x02C7, 0x02D8)


def _without_diacritics(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", value) if not _is_combining(ch))


def _tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[ \t]+", value) if token]


def _without_articles(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in ARTICLES]


def _drop_articles(value: str) -> str:
    """Убрать артикли, не трогая остальные слова и пробелы."""
    return re.sub(r"(?<![^\s])(?:a|an|the)(?![^\s])", "", value)


def _differs_only_by_case(got: str, expected: str, policy: dict) -> bool:
    if policy["case"] != "sensitive":
        return False
    return got != expected and got.lower() == expected.lower()


def _strip_apostrophes(value: str) -> str:
    return value.replace("'", "")


def _collapse(value: str) -> str:
    return value.replace(" ", "").replace("\t", "")


def _letters(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value)


def _near(got: str, expected: str) -> bool:
    """«Почти совпало»: другая форма слова или лишнее/пропущенное слово."""
    a, b = _letters(got), _letters(expected)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    common = 0
    for left, right in zip(a, b):
        if left != right:
            break
        common += 1
    return common >= 3 and abs(len(a) - len(b)) <= 2
