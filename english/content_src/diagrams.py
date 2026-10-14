"""content_src/diagrams.py — типизированные схемы (безопасный SVG без разметки).

Схема описывается данными: узлы с координатами, рамкой и подписью на двух языках,
стрелки между узлами. Интерфейс сам рисует SVG — в контенте нет ни строки
HTML/SVG-разметки, поэтому скрипты и внешние ссылки не могут попасть в схему
(проверяется сборкой). Координаты кратны сетке 4 px, чтобы линии не «плыли».

Схемы английского — не графики, а опоры для рассуждения: дерево предложения,
временная ось, решение об артикле, словообразовательная цепочка и карта предлогов.
"""

from __future__ import annotations

WIDTH, HEIGHT = 420, 280

#: роли узлов (интерфейс выбирает стиль по роли, а не по цвету в данных)
ROLES = ("subject", "verb", "object", "marker", "point", "question", "answer",
         "root", "derived", "place", "time", "accent")


def _node(node_id: str, label_ru: str, label_en: str, x: int, y: int, role: str,
          width: int = 96, height: int = 36) -> dict:
    if role not in ROLES:
        raise ValueError(f"{node_id}: неизвестная роль {role!r}")
    if x % 4 or y % 4:
        raise ValueError(f"{node_id}: координаты должны быть кратны 4 px")
    return {"id": node_id, "label": {"ru": label_ru, "en": label_en},
            "x": x, "y": y, "w": width, "h": height, "role": role}


def _edge(source: str, target: str, label_ru: str = "", label_en: str = "") -> dict:
    return {"from": source, "to": target,
            "label": {"ru": label_ru, "en": label_en} if (label_ru or label_en) else None}


DIAGRAMS = [
    {
        "id": "sentence-tree", "kind": "tree", "width": WIDTH, "height": HEIGHT,
        "title": {"ru": "Разбор предложения по членам", "en": "Sentence structure"},
        "caption": {"ru": "Подлежащее называет предмет, сказуемое — действие; лишних членов нет.",
                    "en": "The subject names the object, the predicate the action; there is no extra member."},
        "nodes": [
            _node("s", "My friend", "My friend", 24, 24, "subject", 112),
            _node("v", "lives", "lives", 156, 24, "verb", 88),
            _node("o", "in Brest", "in Brest", 264, 24, "place", 112),
            _node("x", "he (лишнее)", "he (extra)", 156, 120, "accent", 112),
        ],
        "edges": [
            _edge("s", "v", "кто?", "who?"),
            _edge("v", "o", "где?", "where?"),
            _edge("x", "s", "повтор подлежащего", "repeated subject"),
        ],
    },
    {
        "id": "tense-timeline", "kind": "timeline", "width": WIDTH, "height": HEIGHT,
        "title": {"ru": "Временная ось и маркеры", "en": "Timeline and markers"},
        "caption": {"ru": "Маркер задаёт место действия на оси, а не «правильность» формы.",
                    "en": "The marker places the action on the timeline; it does not judge the form."},
        "nodes": [
            _node("past", "yesterday\nPast Simple", "yesterday\nPast Simple", 24, 96, "marker", 112),
            _node("now", "now\nPresent Continuous", "now\nPresent Continuous", 152, 96, "marker", 128),
            _node("since", "since 2019\nPresent Perfect", "since 2019\nPresent Perfect", 24, 176, "point", 160),
            _node("future", "by next June\nFuture Perfect", "by next June\nFuture Perfect", 200, 176, "marker", 168),
        ],
        "edges": [
            _edge("past", "now", "время идёт", "time passes"),
            _edge("now", "future", "время идёт", "time passes"),
            _edge("since", "now", "действие продолжается", "the action continues"),
        ],
    },
    {
        "id": "article-tree", "kind": "tree", "width": WIDTH, "height": HEIGHT,
        "title": {"ru": "Как выбрать артикль", "en": "Choosing an article"},
        "caption": {"ru": "Сначала исчисляемость, потом известность: это два независимых вопроса.",
                    "en": "Countability comes first, then familiarity: two independent questions."},
        "nodes": [
            _node("q1", "Считаем штуки?", "Countable?", 24, 24, "question", 136),
            _node("yes", "да", "yes", 180, 32, "answer", 64),
            _node("no", "нет", "no", 180, 112, "answer", 64),
            _node("q2", "Первое упоминание?", "First mention?", 264, 24, "question", 144),
            _node("zero", "без артикля\nadvice, breakfast", "no article\nadvice, breakfast", 24, 112, "answer", 152),
            _node("a", "a / an", "a / an", 264, 96, "answer", 144),
            _node("the", "the (уже известен)", "the (already known)", 264, 168, "answer", 144),
        ],
        "edges": [
            _edge("q1", "yes", "", ""),
            _edge("q1", "no", "", ""),
            _edge("yes", "q2", "", ""),
            _edge("q2", "a", "да", "yes"),
            _edge("q2", "the", "нет", "no"),
            _edge("no", "zero", "", ""),
        ],
    },
    {
        "id": "formation-chain", "kind": "flow", "width": WIDTH, "height": HEIGHT,
        "title": {"ru": "Словообразовательная цепочка", "en": "Word formation chain"},
        "caption": {"ru": "Форма слова меняется по месту в предложении: значение остаётся, часть речи — нет.",
                    "en": "The form changes with its position: the meaning stays, the part of speech does not."},
        "nodes": [
            _node("root", "success\nсуществительное", "success\nnoun", 24, 40, "root", 128),
            _node("adj", "successful\nприлагательное", "successful\nadjective", 176, 40, "derived", 152),
            _node("adv", "successfully\nнаречие", "successfully\nadverb", 24, 136, "derived", 152),
            _node("neg", "unsuccessful\nотрицание", "unsuccessful\nnegative", 200, 136, "derived", 168),
        ],
        "edges": [
            _edge("root", "adj", "-ful", "-ful"),
            _edge("adj", "adv", "-ly", "-ly"),
            _edge("adj", "neg", "un-", "un-"),
        ],
    },
    {
        "id": "preposition-map", "kind": "flow", "width": WIDTH, "height": HEIGHT,
        "title": {"ru": "Предлоги места и времени", "en": "Prepositions of place and time"},
        "caption": {"ru": "Место: точка — at, поверхность — on, пространство — in.",
                    "en": "Place: a point takes at, a surface on, a space in."},
        "nodes": [
            _node("at", "at\nточка во времени и пространстве", "at\na point", 24, 32, "point", 152),
            _node("on", "on\nдень и поверхность", "on\na day and a surface", 200, 32, "place", 168),
            _node("in", "in\nмесяц, год, пространство", "in\na month, a year, a space", 24, 152, "time", 184),
            _node("ex", "at school, on Monday,\nin 2026", "at school, on Monday,\nin 2026", 224, 152, "answer", 168),
        ],
        "edges": [
            _edge("at", "ex", "пример", "example"),
            _edge("on", "ex", "пример", "example"),
            _edge("in", "ex", "пример", "example"),
        ],
    },
]


def figures() -> dict:
    return {diagram["id"]: diagram for diagram in DIAGRAMS}


def ids() -> list[str]:
    return [diagram["id"] for diagram in DIAGRAMS]
