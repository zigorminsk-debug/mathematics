"""diagrams.py — offline visual aids for the rule cards.

Three strictly typed kinds (no markup, no URLs, no code):

* ``svg``   — short schemes drawn from a fixed primitive allowlist inside a
              420×280 viewBox (stress, letters/sounds, morpheme parsing, word
              chains, sentence base, phrase links, complex-sentence schemes);
* ``table`` — contrast tables rendered as semantic HTML ``<table>`` (large text
              stays real text, never tiny SVG labels);
* ``tree``  — rule decision trees rendered as nested lists with yes/no branches
              (an accessible linear description by construction).

Russian material inside figures is language-neutral (the same string for RU and
EN); captions/labels are bilingual. Colour is always accompanied by words.
"""
from __future__ import annotations

from copy import deepcopy
import math

WIDTH, HEIGHT = 420, 280
ROLES = {"axis", "grid", "primary", "secondary", "helper", "region", "point", "openpoint", "text", "accent"}
FIELDS = {"line": {"x1", "y1", "x2", "y2"}, "circle": {"cx", "cy", "r"}, "ellipse": {"cx", "cy", "rx", "ry"},
          "rect": {"x", "y", "width", "height"}, "polyline": {"points"}, "polygon": {"points"},
          "text": {"x", "y", "text", "anchor"}}


def bi(ru, en=None):
    return {"ru": ru, "en": ru if en is None else en}


# --------------------------------------------------------------- primitives
def text(x, y, ru, en=None, anchor="middle"):
    return {"kind": "text", "role": "text", "filled": False, "x": round(x, 1), "y": round(y, 1), "text": bi(ru, en),
            "anchor": anchor}


def line(x1, y1, x2, y2, role="helper"):
    return {"kind": "line", "role": role, "filled": False, "x1": round(x1, 1), "y1": round(y1, 1),
            "x2": round(x2, 1), "y2": round(y2, 1)}


def rect(x, y, w, h, role="region", filled=False):
    return {"kind": "rect", "role": role, "filled": filled, "x": round(x, 1), "y": round(y, 1),
            "width": round(w, 1), "height": round(h, 1)}


def circle(cx, cy, r, role="point", filled=True):
    return {"kind": "circle", "role": role, "filled": filled, "cx": round(cx, 1), "cy": round(cy, 1), "r": r}


def poly(points, role="primary", closed=False):
    return {"kind": "polygon" if closed else "polyline", "role": role, "filled": False,
            "points": [[round(x, 1), round(y, 1)] for x, y in points]}


def arrow(x1, y1, x2, y2, role="helper"):
    angle = math.atan2(y2 - y1, x2 - x1)
    head = [(x2, y2), (x2 - 9 * math.cos(angle - .45), y2 - 9 * math.sin(angle - .45)),
            (x2 - 9 * math.cos(angle + .45), y2 - 9 * math.sin(angle + .45))]
    shape = poly(head, role, closed=True)
    shape["filled"] = True
    return [line(x1, y1, x2, y2, role), shape]


def underline(x1, x2, y, kind):
    if kind == "single":
        return [line(x1, y, x2, y, "primary")]
    if kind == "double":
        return [line(x1, y, x2, y, "primary"), line(x1, y + 5, x2, y + 5, "primary")]
    if kind == "wavy":
        steps = max(4, int((x2 - x1) / 6))
        return [poly([(x1 + (x2 - x1) * i / steps, y + (3 if i % 2 else -3)) for i in range(steps + 1)], "primary")]
    if kind == "dashed":
        return [line(x1, y, x2, y, "helper")]
    if kind == "dashdot":
        out, x = [], x1
        while x < x2 - 2:
            out.append(line(x, y, min(x + 12, x2), y, "axis"))
            if x + 17 < x2:
                out.append(circle(x + 16, y, 1.6, "point"))
            x += 21
        return out
    raise ValueError(kind)


def letters_row(word, x0, y, step=34, highlight=(), height=36):
    out = []
    for index, char in enumerate(word):
        x = x0 + index * step
        out.append(rect(x, y, step - 4, height, "accent" if index in highlight else "region", index in highlight))
        out.append(text(x + (step - 4) / 2, y + height / 2 + 6, char))
    return out


def svg(key, title, caption, drawing, legend=None):
    entry = {"id": key, "kind": "svg", "title": bi(*title), "caption": bi(*caption), "width": WIDTH, "height": HEIGHT,
             "drawing": drawing}
    if legend:
        entry["legend"] = [{"role": role, "text": bi(*label)} for role, label in legend]
    return entry


def table(key, title, caption, columns, rows):
    return {"id": key, "kind": "table", "title": bi(*title), "caption": bi(*caption),
            "columns": [bi(*column) if isinstance(column, tuple) else bi(column) for column in columns],
            "rows": [[bi(*cell) if isinstance(cell, tuple) else cell for cell in row] for row in rows]}


def tree(key, title, caption, root):
    return {"id": key, "kind": "tree", "title": bi(*title), "caption": bi(*caption), "root": root}


def node(q_ru, q_en, yes, no):
    return {"q": bi(q_ru, q_en), "yes": yes, "no": no}


def leaf(ru, en, *examples):
    return {"result": bi(ru, en), "examples": list(examples)}


# ------------------------------------------------------------------ figures
def _stress():
    word, accent = "звонит", 4
    x0 = 108
    drawing = letters_row(word, x0, 90, 34, highlight=(accent,))
    ax = x0 + accent * 34 + 15
    drawing += [line(ax - 4, 80, ax + 6, 66, "primary"), text(210, 50, "звони́т")]
    drawing += [line(x0, 150, x0 + 3 * 34 - 4, 150, "axis"), line(x0 + 3 * 34, 150, x0 + 6 * 34 - 4, 150, "axis"),
                text(x0 + 49, 172, "1-й слог", "syllable 1"), text(x0 + 151, 172, "2-й слог: ударный", "syllable 2: stressed")]
    drawing += [text(210, 222, "так же: звоня́т, звони́шь, позвони́т", "likewise: звоня́т, звони́шь, позвони́т")]
    return svg("stress-zvonit", ("Ударение: звони́т", "Stress: звони́т"),
               ("Ударный гласный выделен цветом и знаком ударения: звони́т — ударение на втором слоге, во всех формах на окончании.",
                "The stressed vowel is highlighted and marked: звони́т — stress on the second syllable, on the ending in all forms."),
               drawing, legend=[("accent", ("ударный гласный", "stressed vowel"))])


def _sounds():
    drawing = letters_row("ёлка", 140, 50, 36)
    sounds = ["й'", "о", "л", "к", "а"]
    for index, sound in enumerate(sounds):
        x = 96 + index * 50
        drawing += [rect(x, 160, 40, 36, "region"), text(x + 20, 184, sound)]
    links = [(0, 0), (0, 1), (1, 2), (2, 3), (3, 4)]
    for letter, sound in links:
        drawing.append(line(140 + letter * 36 + 16, 86, 96 + sound * 50 + 20, 160, "primary" if letter == 0 else "helper"))
    drawing += [text(46, 74, "буквы", "letters", "middle"), text(46, 184, "звуки", "sounds", "middle"),
                text(210, 240, "4 буквы — 5 звуков [й'олка]", "4 letters — 5 sounds [й'олка]")]
    return svg("letters-sounds", ("Буквы и звуки: ёлка", "Letters and sounds: ёлка"),
               ("Буква ё в начале слова обозначает два звука [й'о], поэтому звуков на один больше, чем букв.",
                "Word-initial ё stands for two sounds [й'о], so there is one sound more than letters."),
               drawing, legend=[("primary", ("одна буква — два звука", "one letter — two sounds"))])


def _morphemes():
    word = "подоконник"
    x0, step, y = 40, 30, 120
    drawing = letters_row(word, x0, y, step)
    drawing += [poly([(x0, 104), (x0 + 3 * step - 4, 104), (x0 + 3 * step - 4, 114)])]  # prefix ⌐
    arc = [(x0 + 3 * step + (4 * step - 4) * i / 12, 104 - 12 * math.sin(math.pi * i / 12)) for i in range(13)]
    drawing += [poly(arc)]  # root ⌒
    sx = x0 + 7 * step
    drawing += [poly([(sx, 114), (sx + (3 * step - 4) / 2, 98), (sx + 3 * step - 4, 114)])]  # suffix ^
    drawing += [rect(x0 + 10 * step + 4, y, 26, 36, "primary"), text(x0 + 10 * step + 17, y + 24, "∅")]
    drawing += [text(x0 + 43, 186, "приставка", "prefix"), text(x0 + 3 * step + 58, 186, "корень", "root"),
                text(x0 + 7 * step + 43, 186, "суффикс", "suffix"), text(x0 + 10 * step + 17, 210, "окончание", "ending"),
                text(210, 248, "окно → под- + окон + -ник: приставочно-суффиксальный", "окно → под- + окон + -ник: prefix + suffix")]
    return svg("morpheme-podokonnik", ("Морфемный разбор: подоконник", "Morpheme parsing: подоконник"),
               ("Приставка под-, корень -окон- (окно), суффикс -ник-, нулевое окончание (подоконника).",
                "Prefix под-, root -окон- (окно), suffix -ник-, zero ending (подоконника)."), drawing)


def _chain():
    boxes = [("учить", 22), ("учитель", 152), ("учительница", 282)]
    drawing = []
    for word, x in boxes:
        drawing += [rect(x, 110, 116, 44, "region"), text(x + 58, 138, word)]
    drawing += arrow(140, 132, 150, 132) + arrow(270, 132, 280, 132)
    drawing += [text(145, 96, "-тель", "-тель"), text(275, 96, "-ниц-", "-ниц-"),
                text(210, 200, "каждый шаг — суффиксальный способ", "each step is suffixal")]
    return svg("chain-uchit", ("Словообразовательная цепочка", "Word-formation chain"),
               ("учить → учитель (суффикс -тель) → учительница (суффикс -ниц-): каждое слово образовано от предыдущего.",
                "учить → учитель → учительница: each word is formed from the previous one."), drawing)


def _root_check():
    drawing = letters_row("з.лотой", 90, 60, 34, highlight=(1,))
    drawing[3]["text"] = bi("?")
    drawing += letters_row("золото", 107, 170, 34, highlight=(1,))
    drawing += [text(124 + 34, 160, "´")] + arrow(158, 160, 158, 102, "primary")
    drawing += [text(210, 40, "з..лотой", "з..лотой"), text(210, 236, "зо́лото: о под ударением → золотой",
                                                                "зо́лото: stressed о → золотой")]
    return svg("root-check", ("Проверка безударной гласной", "Checking an unstressed vowel"),
               ("Однокоренное слово с ударением на том же слоге показывает букву: зо́лото → золотой.",
                "A cognate stressed on the same syllable shows the letter: зо́лото → золотой."), drawing,
               legend=[("accent", ("проверяемая гласная", "checked vowel"))])


def _sentence():
    words = [("Старый", 40, "wavy"), ("парк", 128, "single"), ("спал", 196, "double"), ("под снегом.", 262, "dashdot")]
    widths = {"Старый": 62, "парк": 42, "спал": 42, "под снегом.": 96}
    drawing = []
    for word, x, kind in words:
        drawing.append(text(x, 120, word, word, "start"))
        drawing += underline(x, x + widths[word], 130, kind)
    drawing += arrow(150, 100, 70, 100) + arrow(220, 96, 160, 96)
    drawing += [text(108, 86, "какой?", "which?"), text(190, 82, "что сделал?", "did what?"),
                text(210, 190, "грамматическая основа: парк спал", "subject + predicate: парк спал"),
                text(210, 222, "определение ~~~, обстоятельство — · —", "attribute ~~~, adverbial — · —")]
    return svg("sentence-base", ("Грамматическая основа и члены предложения", "Sentence base and parts"),
               ("Подлежащее подчёркнуто одной чертой, сказуемое — двумя, определение — волнистой, обстоятельство — штрихпунктиром.",
                "Subject: one line; predicate: two lines; attribute: wavy; adverbial: dash-dot."), drawing,
               legend=[("primary", ("основа: одна черта — подлежащее, две — сказуемое", "base: one line subject, two predicate")),
                       ("axis", ("обстоятельство — штрихпунктир", "adverbial — dash-dot"))])


def _phrases():
    rows = [("высокий", "дом", "согласование", "agreement", "какой?"), ("книгу", "читать", "управление", "government", "что?"),
            ("быстро", "бежать", "примыкание", "adjunction", "как?")]
    drawing = []
    for index, (dep, head, ru, en, q) in enumerate(rows):
        y = 60 + index * 70
        drawing += [text(70, y, head), text(200, y, dep)] + arrow(98, y - 5, 168, y - 5, "primary")
        drawing += [text(134, y - 14, q), text(330, y, ru, en)]
    return svg("phrase-links", ("Виды связи в словосочетании", "Links in phrases"),
               ("Стрелка идёт от главного слова к зависимому; вопрос задаётся от главного. Тип связи подписан словами.",
                "The arrow goes from the head to the dependent; the type is written in words."), drawing)


def _bracket(x, w, y, label=None, round_=False):
    if round_:
        out = [poly([(x + 8, y - 18), (x, y), (x + 8, y + 18)]), poly([(x + w - 8, y - 18), (x + w, y), (x + w - 8, y + 18)])]
    else:
        out = [poly([(x + 8, y - 18), (x, y - 18), (x, y + 18), (x + 8, y + 18)]),
               poly([(x + w - 8, y - 18), (x + w, y - 18), (x + w, y + 18), (x + w - 8, y + 18)])]
    if label:
        out.append(text(x + w / 2, y + 5, label))
    return out


def _schemes():
    drawing = []
    drawing += _bracket(30, 150, 60, "Солнце скрылось") + [text(190, 66, ", и")] + _bracket(214, 170, 60, "подул ветер")
    drawing += [text(210, 104, "ССП: [ ], и [ ].", "compound: [ ], и [ ].")]
    drawing += _bracket(30, 120, 160, "Я знаю") + [text(156, 166, ",")] + _bracket(170, 200, 160, "что ты придёшь", round_=True)
    drawing += arrow(90, 182, 250, 182, "helper") + [text(170, 200, "(что?)", "(what?)")]
    drawing += [text(210, 236, "СПП: [ ], (что …).", "complex: [ ], (что …).")]
    return svg("scheme-ssp-spp", ("Схемы ССП и СПП", "Compound and complex schemes"),
               ("Квадратные скобки — главные (равноправные) части, круглые — придаточная; стрелка показывает вопрос от главной части.",
                "Square brackets: main clauses; round: subordinate; the arrow shows the question."), drawing)


def _bsp():
    drawing = []
    drawing += _bracket(20, 140, 70, "Я знаю") + [text(172, 76, ":")] + _bracket(186, 210, 70, "ты придёшь")
    drawing += [text(210, 116, "= что: пояснение → двоеточие", "= что: explanation → colon")]
    drawing += _bracket(20, 140, 176, "Лес рубят") + [text(172, 182, "—")] + _bracket(186, 210, 176, "щепки летят")
    drawing += [text(210, 222, "= поэтому: следствие → тире", "= поэтому: result → dash")]
    return svg("scheme-bsp", ("Знаки в бессоюзном предложении", "Marks in asyndetic sentences"),
               ("Подставьте союз: «что», «потому что» — двоеточие; «поэтому», «если», «а» — тире.",
                "Insert a conjunction: «что/потому что» → colon; «поэтому/если/а» → dash."), drawing)


def _dash():
    drawing = [text(110, 80, "Москва"), text(210, 80, "—"), text(310, 80, "столица"),
               text(110, 108, "сущ., И. п.", "noun, nom."), text(310, 108, "сущ., И. п.", "noun, nom."),
               text(110, 180, "Он"), text(310, 180, "студент"), text(210, 180, "—"),
               line(196, 168, 224, 190, "secondary"), line(224, 168, 196, 190, "secondary"),
               text(110, 208, "личное мест.", "personal pron."), text(210, 246, "тире нет", "no dash")]
    drawing += underline(76, 144, 88, "single") + underline(270, 350, 88, "double")
    drawing += underline(96, 124, 188, "single") + underline(272, 348, 188, "double")
    return svg("dash-subject", ("Тире между подлежащим и сказуемым", "Dash between subject and predicate"),
               ("Существительное — существительное в И. п. без связки: тире. Подлежащее — личное местоимение: тире нет.",
                "Noun — noun in the nominative without a link: dash. A personal pronoun subject: no dash."), drawing,
               legend=[("secondary", ("крест — знак не ставится", "cross — no mark"))])


def _isolation():
    drawing = [text(20, 70, "Дорога, ведущая к лесу, заросла.", "Дорога, ведущая к лесу, заросла.", "start"),
               rect(84, 48, 140, 30, "accent", True)]
    drawing += arrow(150, 86, 50, 86, "primary") + [text(250, 110, "оборот после слова → запятые", "after its noun → commas")]
    drawing += [text(20, 180, "Ведущая к лесу дорога заросла.", "Ведущая к лесу дорога заросла.", "start"),
                rect(16, 158, 128, 30, "accent", True)]
    drawing += arrow(80, 196, 172, 196, "primary") + [text(250, 222, "оборот перед словом → без запятых",
                                                             "before its noun → no commas")]
    return svg("isolation-position", ("Место причастного оборота", "Position of a participial phrase"),
               ("Стрелка ведёт от оборота к определяемому слову. После слова оборот обособляется, перед ним — нет.",
                "The arrow points to the noun. After it the phrase is set off, before it — not."), drawing,
               legend=[("accent", ("причастный оборот", "participial phrase"))])


def _text_structure():
    drawing = []
    for index, (ru, en) in enumerate([("Тезис", "Thesis"), ("Доказательства", "Arguments"), ("Вывод", "Conclusion")]):
        x = 20 + index * 135
        drawing += [rect(x, 100, 120, 50, "region"), text(x + 60, 131, ru, en)]
        if index < 2:
            drawing += arrow(x + 120, 125, x + 134, 125)
    drawing += [text(80, 180, "(2)", "(2)"), text(215, 180, "(3)–(5)", "(3)–(5)"), text(350, 180, "(6) Поэтому…", "(6) Поэтому…"),
                text(210, 236, "рассуждение: почему так?", "reasoning: why?")]
    return svg("text-reasoning", ("Строение рассуждения", "Structure of reasoning"),
               ("Тезис → доказательства → вывод; в тексте о чтении это предложения 2, 3–5 и 6.",
                "Thesis → arguments → conclusion; in the reading text these are sentences 2, 3–5 and 6."), drawing)


def _cohesion():
    drawing = []
    labels = [("(3) Хорошая книга учит…", 30), ("(4) Она помогает…", 150), ("(6) Поэтому чтение…", 280)]
    for ru, x in labels:
        drawing += [rect(x, 100, 112, 54, "region"), text(x + 56, 132, ru.split(" ", 1)[1][:16])]
        drawing.append(text(x + 56, 92, ru.split(" ")[0]))
    drawing += arrow(206, 168, 86, 168, "primary") + [text(146, 190, "она = книга", "она = книга")]
    drawing += arrow(336, 176, 206, 176, "primary") + [text(272, 210, "поэтому → вывод", "поэтому → conclusion")]
    return svg("cohesion-chain", ("Средства связи предложений", "Cohesion between sentences"),
               ("Слово в предложении отсылает к предыдущему: «она» заменяет «книгу», «поэтому» связывает вывод с доводами.",
                "A word refers back: «она» replaces «книга», «поэтому» links the conclusion to the arguments."), drawing)


def _boundary():
    drawing = letters_row("подъезд", 60, 70, 40, highlight=(3,))
    drawing += [line(60 + 3 * 40 - 2, 56, 60 + 3 * 40 - 2, 120, "secondary"), text(110, 146, "приставка под-", "prefix под-"),
                text(280, 146, "корень -езд-", "root -езд-")]
    drawing += letters_row("вьюга", 100, 180, 40, highlight=(1,))
    drawing += [text(210, 250, "ь — внутри корня, ъ — после приставки", "ь inside a root, ъ after a prefix")]
    return svg("hard-soft-boundary", ("Ъ на границе, Ь внутри корня", "Ъ at the border, Ь inside the root"),
               ("Разделительный ъ стоит на границе приставки и корня (под|ъезд), ь — внутри корня (вьюга).",
                "ъ stands at the prefix–root border (под|ъезд), ь inside the root (вьюга)."), drawing,
               legend=[("secondary", ("граница приставки и корня", "prefix–root border"))])


TABLES = [
    table("table-tozhe", ("Тоже / то же, также / так же", "Тоже / то же, также / так же"),
          ("Слитно — союз (= и); раздельно — местоимение или наречие с частицей; рядом часто «что», «как».",
           "Solid: conjunction (= и); separate: pronoun/adverb + particle, often with что/как."),
          [("Написание", "Spelling"), ("Что это", "What it is"), ("Проверка", "Check"), ("Пример", "Example")],
          [["тоже", ("союз", "conjunction"), ("= и, также", "= also"), "Я тоже пойду."],
           ["то же", ("местоимение + частица", "pronoun + particle"), ("рядом «что»; же можно убрать", "with «что»"),
            "Он заказал то же, что и я."],
           ["также", ("союз", "conjunction"), ("= и, тоже", "= also"), "Сестра также любит музыку."],
           ["так же", ("наречие + частица", "adverb + particle"), ("рядом «как»", "with «как»"), "Он поступил так же, как брат."]]),
    table("table-chtoby", ("Союзы и сочетания-двойники", "Look-alike conjunctions"),
          ("Союз пишется слитно; местоимение или наречие с частицей/предлогом — раздельно.", "Conjunctions are solid."),
          [("Слитно", "Solid"), ("Раздельно", "Separate"), ("Как различить", "How to tell")],
          [["чтобы (цель)", "что бы (бы можно убрать)", ("«для того чтобы» или «что бы ни»", "purpose vs pronoun")],
           ["зато (= но)", "за то (что)", ("«но» или «за то, что»", "«но» vs «за то, что»")],
           ["итак (= следовательно)", "и так (= и без того)", ("вывод или усиление", "conclusion vs emphasis")],
           ["причём (= к тому же)", "при чём (при каком предмете)", ("союз или вопрос", "conjunction vs question")],
           ["поэтому (= по этой причине)", "по этому (мосту)", ("при существительном — раздельно", "with a noun — separate")]]),
    table("table-prepositions", ("Производные предлоги", "Derived prepositions"),
          ("Слитно: вследствие, ввиду, насчёт, несмотря на. Раздельно: в течение, в продолжение (на конце -е).",
           "Solid: вследствие, ввиду, насчёт, несмотря на. Separate: в течение, в продолжение."),
          [("Предлог", "Preposition"), ("Значение", "Meaning"), ("Не путать с", "Do not confuse with")],
          [["в течение недели", ("время", "time"), "в течении реки (сущ.)"],
           ["в продолжение разговора", ("время", "time"), "в продолжении романа (сущ.)"],
           ["вследствие болезни", ("причина", "cause"), "в следствии по делу (сущ.)"],
           ["ввиду погоды", ("причина", "cause"), "иметь в виду"],
           ["насчёт поездки", ("= о", "= about"), "перевести на счёт фирмы"],
           ["несмотря на дождь", ("уступка", "concession"), "не смотря под ноги (деепр.)"]]),
    table("table-pre-pri", ("ПРЕ- и ПРИ-", "ПРЕ- and ПРИ-"),
          ("Значение приставки решает написание; словарные слова запоминают.", "The prefix meaning decides."),
          [("Приставка", "Prefix"), ("Значение", "Meaning"), ("Примеры", "Examples")],
          [["пре-", ("«очень»", "«very»"), "прекрасный, премудрый"], ["пре-", ("«пере-»", "«пере-»"), "преодолеть, прервать"],
           ["при-", ("приближение, присоединение", "approach, joining"), "приехать, пристроить"],
           ["при-", ("близость", "nearness"), "прибрежный, привокзальный"],
           ["при-", ("неполнота действия", "incomplete action"), "приоткрыть, присесть"],
           [("по словарю", "dictionary"), ("значение не выделяется", "opaque"), "привилегия, пренебрегать, президент"]]),
    table("table-paronyms", ("Паронимы", "Paronyms"),
          ("Похожие слова различаются значением и сочетаемостью; в тренажёре проверяется правильный выбор.",
           "Similar words differ in meaning and collocation."),
          [("Пароним", "Paronym"), ("Значение", "Meaning"), ("Пример", "Example")],
          [["одеть", ("кого? (ребёнка)", "someone"), "одеть сына"], ["надеть", ("что? (одежду)", "something"), "надеть шапку"],
           ["предоставить", ("дать в пользование", "grant"), "предоставить отпуск"],
           ["представить", ("показать, познакомить", "present"), "представить отчёт"],
           ["абонемент", ("право пользования", "subscription"), "абонемент в бассейн"],
           ["абонент", ("тот, кто пользуется", "subscriber"), "абонент недоступен"],
           ["эффективный", ("действенный", "effective"), "эффективное лекарство"],
           ["эффектный", ("производящий впечатление", "striking"), "эффектное платье"]]),
    table("table-alt-oa", ("Корни с чередованием О/А", "Roots alternating О/А"),
          ("Гласная зависит от согласной после корня, суффикса -а-, ударения или значения — не от проверки ударением.",
           "The vowel depends on the following consonant, the suffix -а-, stress or meaning."),
          [("Корень", "Root"), ("Условие", "Condition"), ("Примеры", "Examples"), ("Исключения", "Exceptions")],
          [["-лаг-/-лож-", ("г — а, ж — о", "г → а, ж → о"), "предлагать, предложение", "—"],
           ["-раст-/-ращ-/-рос-", ("ст, щ — а; с — о", "ст/щ → а; с → о"), "растение, заросли", "росток, отрасль"],
           ["-кас-/-кос-", ("суффикс -а- — а", "suffix -а- → а"), "касаться, коснуться", "—"],
           ["-скак-/-скоч-", ("к — а, ч — о", "к → а, ч → о"), "скакать, выскочить", "скачок, скачу"],
           ["-гар-/-гор-", ("без ударения — о", "unstressed о"), "загорелый", "выгарки, изгарь"],
           ["-зар-/-зор-", ("без ударения — а", "unstressed а"), "заря", "зоревать, зорянка"],
           ["-клан-/-клон-, -твар-/-твор-", ("без ударения — о", "unstressed о"), "поклониться, творение", "утварь"],
           ["-плав-", ("а", "а"), "поплавок", "пловец, пловчиха, плывуны"],
           ["-равн-/-ровн-", ("«равный» — а, «ровный» — о", "meaning"), "уравнять, выровнять", "равнина, ровесник, поровну"]]),
    table("table-alt-ei", ("Корни с чередованием Е/И", "Roots alternating Е/И"),
          ("Перед суффиксом -а- пишется и, без него — е.", "и before the suffix -а-, otherwise е."),
          [("Корень", "Root"), ("С -а- → и", "With -а- → и"), ("Без -а- → е", "Without -а- → е")],
          [["-бер-/-бир-", "собирать", "соберу"], ["-мер-/-мир-", "замирать", "замереть"], ["-тер-/-тир-", "вытирать", "вытереть"],
           ["-блест-/-блист-", "блистать", "блестеть"], ["-жег-/-жиг-", "зажигать", "зажечь"], ["-стел-/-стил-", "застилать", "застелить"],
           [("исключения", "exceptions"), "—", "сочетать, сочетание, чета"]]),
    table("table-n-nn", ("Н и НН", "Н and НН"),
          ("Сначала определите, от чего образовано слово; затем — приставку, зависимые слова и исключения.",
           "Find the source word first, then prefix, dependents and exceptions."),
          [("Случай", "Case"), ("Н/НН", "Н/НН"), ("Примеры", "Examples")],
          [[("суффиксы -ан-, -ян-, -ин-", "suffixes -ан-, -ян-, -ин-"), "н", "кожаный, серебряный, гусиный"],
           [("исключения", "exceptions"), "нн", "деревянный, стеклянный, оловянный"],
           [("суффиксы -енн-, -онн-", "suffixes -енн-, -онн-"), "нн", "клюквенный, традиционный"],
           [("основа на н + н", "stem in н + н"), "нн", "лимонный, каменный"],
           [("отглагольное без приставки и зависимых слов", "deverbal, no prefix/dependents"), "н", "жареная картошка"],
           [("причастие: приставка или зависимые слова", "participle: prefix or dependents"), "нн", "пожаренная, жаренная в масле"],
           [("краткое причастие", "short participle"), "н", "задача решена"],
           [("исключения с одной н", "one-н exceptions"), "н", "ветреный, смышлёный"]]),
    table("table-conjugation", ("Спряжение глаголов", "Verb conjugation"),
          ("II спряжение: на -ить (кроме брить, стелить) и 11 исключений; остальные — I.",
           "2nd: verbs in -ить (except брить, стелить) and 11 exceptions; others 1st."),
          [("Спряжение", "Conjugation"), ("Окончания", "Endings"), ("Глаголы", "Verbs")],
          [["I", "-ешь, -ет, -ем, -ете, -ут/-ют", ("остальные + брить, стелить", "the rest + брить, стелить")],
           ["II", "-ишь, -ит, -им, -ите, -ат/-ят", ("на -ить + гнать, держать, дышать, слышать, видеть, обидеть, ненавидеть, "
                                                   "зависеть, вертеть, терпеть, смотреть", "-ить verbs + 11 exceptions")]]),
    table("table-declension", ("Три склонения", "Three declensions"),
          ("Склонение определяют по роду и окончанию в именительном падеже единственного числа.",
           "Declension is found by gender and nominative singular ending."),
          [("Склонение", "Declension"), ("Род и окончание", "Gender and ending"), ("Примеры", "Examples")],
          [["1-е", ("ж. и м. р. на -а, -я", "fem./masc. in -а/-я"), "земля, дядя, юноша"],
           ["2-е", ("м. р. с нулевым окончанием, ср. р. на -о, -е", "masc. zero ending, neut. -о/-е"), "конь, поле, здание"],
           ["3-е", ("ж. р. на -ь", "fem. in -ь"), "ночь, мышь, тень"],
           [("разносклоняемые", "heteroclites"), ("10 слов на -мя и путь", "10 nouns in -мя and путь"), "время, имя, путь"],
           [("несклоняемые", "indeclinable"), ("одна форма", "one form"), "пальто, кофе, метро"]]),
    table("table-numerals", ("Склонение составного числительного", "Declining a compound numeral"),
          ("Каждое слово меняется: 548 по падежам.", "Every word changes: 548 by case."),
          [("Падеж", "Case"), ("Форма", "Form")],
          [[("именительный", "nominative"), "пятьсот сорок восемь"], [("родительный", "genitive"), "пятисот сорока восьми"],
           [("дательный", "dative"), "пятистам сорока восьми"], [("творительный", "instrumental"), "пятьюстами сорока восемью (восьмью)"],
           [("предложный", "prepositional"), "о пятистах сорока восьми"]]),
    table("table-styles", ("Стили речи", "Styles of speech"),
          ("Стиль определяют по сфере общения, задаче и языковым приметам, а не по теме.", "Style: sphere, purpose, language."),
          [("Стиль", "Style"), ("Задача", "Purpose"), ("Приметы", "Markers")],
          [[("научный", "scientific"), ("сообщить точные знания", "precise knowledge"), ("термины, логичность, нет оценок", "terms, logic")],
           [("официально-деловой", "official"), ("регулировать отношения", "regulate"), ("стандартные формулы, точность", "formulas")],
           [("публицистический", "journalistic"), ("воздействовать, убедить", "persuade"), ("оценка, призыв, общественная тема", "evaluation")],
           [("художественный", "literary"), ("создать образ", "create images"), ("тропы, эмоциональность", "imagery")],
           [("разговорный", "colloquial"), ("непринуждённое общение", "casual talk"), ("разговорные слова, диалог", "colloquialisms")]]),
    table("table-types", ("Типы речи", "Types of speech"),
          ("Тип речи — по тому, что сообщает текст.", "The type depends on what the text conveys."),
          [("Тип", "Type"), ("Вопрос", "Question"), ("Признак", "Feature")],
          [[("повествование", "narration"), ("что произошло?", "what happened?"), ("смена событий во времени", "events in time")],
           [("описание", "description"), ("какой?", "what is it like?"), ("признаки в один момент", "features at one moment")],
           [("рассуждение", "reasoning"), ("почему?", "why?"), ("тезис, доводы, вывод", "thesis, arguments, conclusion")]]),
    table("table-cohesion", ("Средства связи предложений", "Means of cohesion"),
          ("Средство ищут в данном предложении и связывают с предыдущим.", "Look in the given sentence, link to the previous."),
          [("Средство", "Means"), ("Пример", "Example")],
          [[("личное местоимение", "personal pronoun"), "Книга учит… Она помогает…"],
           [("указательное местоимение", "demonstrative pronoun"), "…не нужны. С этим мнением…"],
           [("лексический повтор", "repetition"), "…к пруду. Пруд замёрз…"],
           [("синоним, родовое слово", "synonym, general word"), "…цапля. …провожали птицу…"],
           [("союз в начале", "initial conjunction"), "Однако с этим трудно согласиться."],
           [("наречие", "adverb"), "Поэтому чтение… / Тогда дерево…"], [("вводное слово", "parenthetical"), "Например, … / Следовательно, …"],
           [("однокоренное слово", "cognate"), "…листья? Листопад…"]]),
    table("table-asyndetic", ("Знаки в бессоюзном предложении", "Marks in asyndetic sentences"),
          ("Подставьте союз — он подскажет знак.", "Insert a conjunction — it tells the mark."),
          [("Подставляется", "Insert"), ("Отношение", "Relation"), ("Знак", "Mark"), ("Пример", "Example")],
          [["и, а также", ("перечисление", "list"), ",", "Ветер стих, небо прояснилось."],
           ["что, а именно", ("пояснение", "explanation"), ":", "Я знаю: ты придёшь."],
           ["потому что", ("причина", "reason"), ":", "Мне не спалось: мешал шум."],
           ["и увидел, что", ("восприятие", "perception"), ":", "Я оглянулся: никого не было."],
           ["поэтому, так что", ("следствие", "result"), "—", "Лес рубят — щепки летят."],
           ["если, когда", ("условие, время", "condition, time"), "—", "Приедешь — поговорим."],
           ["а, но", ("противопоставление", "contrast"), "—", "Хотел выйти — дверь заперта."]]),
    table("table-direct-speech", ("Схемы прямой речи", "Direct speech patterns"),
          ("П/п — прямая речь (с прописной/строчной), А/а — слова автора.", "П/п — speech, А/а — author's words."),
          [("Схема", "Pattern"), ("Пример", "Example")],
          [["А: «П».", "Брат сказал: «Я приду завтра»."], ["«П», — а.", "«Я приду завтра», — сказал брат."],
           ["«П?» — а.", "«Ты придёшь?» — спросила мама."], ["«П, — а, — п».", "«Знаешь, — сказала она, — я давно хотела…»"],
           ["«П, — а. — П».", "«Я устал, — сказал он. — Пойду спать»."],
           [("цитата в предложении", "built-in quotation"), "По словам Пушкина, «чтение — вот лучшее учение»."]]),
    table("table-hyphen", ("Слитно, раздельно, через дефис", "Solid, separate, hyphenated"),
          ("Сложные прилагательные, пол-, наречия.", "Compound adjectives, пол-, adverbs."),
          [("Написание", "Spelling"), ("Когда", "When"), ("Примеры", "Examples")],
          [[("через дефис", "hyphen"), ("равноправные основы, цвета, стороны света", "equal stems, colours, compass"),
            "литературно-художественный, сине-зелёный, северо-западный"],
           [("слитно", "solid"), ("от подчинительного словосочетания", "from a subordinate phrase"), "железнодорожный, сельскохозяйственный"],
           [("раздельно", "separate"), ("наречие + прилагательное", "adverb + adjective"), "широко известный"],
           [("пол- через дефис", "пол- hyphen"), ("перед гласной, л, прописной", "before a vowel, л, capital"), "пол-яблока, пол-лимона, пол-Минска"],
           [("пол- слитно", "пол- solid"), ("перед другими согласными", "other consonants"), "полчаса, полметра"],
           [("наречия через дефис", "adverbs, hyphen"), ("по-…-ому, -ски; во-…-ых", "по-…-ому; во-…-ых"), "по-новому, по-братски, во-первых"],
           [("наречия слитно", "adverbs, solid"), ("предлог + краткое прилагательное и др.", "preposition + short adjective"),
            "досуха, налево, напоказ, вдвоём"], [("наречия раздельно", "adverbs, separate"), ("сохраняется падеж", "case kept"),
                                                  "без устали, с разбегу, по двое"]]),
    table("table-ending", ("Нулевое окончание и отсутствие окончания", "Zero ending vs no ending"),
          ("Изменяемое слово с невыраженным окончанием — нулевое окончание; неизменяемое слово окончания не имеет.",
           "A changeable word may have a zero ending; an invariable word has none."),
          [("Слово", "Word"), ("Окончание", "Ending"), ("Почему", "Why")],
          [["конь", ("нулевое", "zero"), "коня, коню"], ["читал", ("нулевое", "zero"), "читала, читали"],
           ["пальто", ("нет", "none"), ("несклоняемое", "indeclinable")], ["красиво", ("нет", "none"), ("наречие", "adverb")],
           ["читая", ("нет", "none"), ("деепричастие", "verbal adverb")]]),
    table("table-formation", ("Способы образования слов", "Ways of forming words"),
          ("Сравнивайте слово с производящим и смотрите, что добавлено.", "Compare with the source word."),
          [("Способ", "Method"), ("Пример", "Example")],
          [[("приставочный", "prefixal"), "читать → перечитать"], [("суффиксальный", "suffixal"), "лес → лесник"],
           [("приставочно-суффиксальный", "prefix + suffix"), "окно → подоконник"], [("постфиксальный", "postfixal"), "мыть → мыться"],
           [("приставочно-постфиксальный", "prefix + postfix"), "бежать → разбежаться"], [("сложение", "compounding"), "пар + ход → пароход"],
           [("сложение + суффиксация", "compounding + suffix"), "железная дорога → железнодорожный"]]),
    table("table-iotated", ("Когда е, ё, ю, я обозначают два звука", "When е, ё, ю, я give two sounds"),
          ("Два звука — в начале слова, после гласной и после ъ, ь; после согласной — один звук.", "Two sounds initially, "
           "after a vowel and after ъ/ь."),
          [("Позиция", "Position"), ("Звуки", "Sounds"), ("Пример", "Example")],
          [[("начало слова", "word start"), ("два", "two"), "ель [й'эл']"], [("после гласной", "after a vowel"), ("два", "two"), "маяк [май'ак]"],
           [("после ъ, ь", "after ъ/ь"), ("два", "two"), "вьюга [в'й'уга]"], [("после согласной", "after a consonant"), ("один", "one"),
                                                                              "мясо [м'аса]"]]),
    table("table-stress", ("Памятка ударений", "Stress memo"),
          ("Слова с одним нормативным ударением (по орфоэпическому словарю).", "Words with one normative stress."),
          [("Слово", "Word"), ("Ударный слог", "Stressed syllable")],
          [["звони́т", "2"], ["катало́г", "3"], ["кварта́л", "2"], ["краси́вее", "2"], ["ку́хонный", "1"], ["щаве́ль", "2"],
           ["жалюзи́", "3"], ["то́рты", "1"], ["взяла́", "2"], ["при́нял", "1"], ["обеспе́чение", "3"], ["облегчи́ть", "3"]]),
    table("table-soft-sign", ("Ь после шипящих", "Ь after hushing consonants"),
          ("Решают часть речи и род, а не звучание.", "Part of speech and gender decide."),
          [("Часть речи", "Part of speech"), ("Ь", "Ь"), ("Примеры", "Examples")],
          [[("сущ. ж. р., 3-е скл.", "fem. noun, 3rd decl."), ("пишется", "yes"), "ночь, мощь"],
           [("сущ. м. р.", "masc. noun"), ("нет", "no"), "плач, калач"], [("Р. п. мн. ч.", "gen. pl."), ("нет", "no"), "туч, задач"],
           [("глагол", "verb"), ("пишется", "yes"), "читаешь, печь, режь"], [("наречие", "adverb"), ("пишется", "yes"), "настежь, сплошь"],
           [("искл.: уж, замуж, невтерпёж", "exc.: уж, замуж, невтерпёж"), ("нет", "no"), "уж, замуж"],
           [("краткое прил.", "short adj."), ("нет", "no"), "горяч, хорош"]]),
    table("table-predicates", ("Типы сказуемого", "Predicate types"),
          ("Смотрите на состав сказуемого.", "Look at the composition."),
          [("Тип", "Type"), ("Строение", "Structure"), ("Пример", "Example")],
          [[("простое глагольное", "simple verbal"), ("глагол в любой форме", "a verb form"), "Мы гуляли. Он будет работать."],
           [("составное глагольное", "compound verbal"), ("вспомогательный глагол + инфинитив", "aux + infinitive"), "Я начал читать."],
           [("составное именное", "compound nominal"), ("связка + именная часть", "link + nominal"), "Вечер был тихим. Брат — студент."]]),
    table("table-complex-types", ("Виды сложных предложений", "Types of complex sentences"),
          ("Тип — по средству связи частей.", "The type depends on the link."),
          [("Вид", "Type"), ("Связь", "Link"), ("Пример", "Example")],
          [[("ССП", "compound"), ("сочинительный союз", "coordinating"), "Наступила весна, и растаял снег."],
           [("СПП", "complex"), ("подчинительный союз, союзное слово", "subordinating"), "Когда наступила весна, растаял снег."],
           [("БСП", "asyndetic"), ("без союзов", "none"), "Наступила весна — растаял снег."],
           [("с разными видами связи", "mixed"), ("несколько видов", "several"), "Я позвонил, но он не ответил, потому что уехал."]]),
    table("table-introductory", ("Вводные и не вводные слова", "Parenthetical or not"),
          ("Список «не вводных» помогает не ставить лишние запятые.", "The «never parenthetical» list saves extra commas."),
          [("Вводные (выделяются)", "Parenthetical"), ("Не вводные (не выделяются)", "Not parenthetical")],
          [["конечно, наверное, кажется", "вдруг, вряд ли, едва ли"], ["к счастью, к сожалению", "даже, именно, ведь"],
           ["во-первых, значит, итак", "будто бы, как будто, приблизительно"], ["говорят, по-моему, по-видимому", "однако (в начале = но)"]]),
    table("table-ne", ("НЕ: слитно или раздельно", "НЕ: solid or separate"),
          ("Сначала часть речи, потом условия.", "Part of speech first, then conditions."),
          [("Слитно", "Solid"), ("Раздельно", "Separate")],
          [["без НЕ не употребляется: ненавидеть, небрежный", "с глаголом и деепричастием: не читая, не заметил"],
           ["есть синоним без НЕ: невесёлый (= грустный)", "противопоставление с А: не весёлый, а грустный"],
           ["полное причастие без зависимых слов: нерешённая задача", "причастие с зависимыми словами: не решённая ещё задача"],
           ["отрицательные местоимения: некого, нечего", "краткое причастие: не решена; далеко не простой"]]),
]

TREES = [
    tree("tree-ne", ("Как писать НЕ", "How to write НЕ"),
         ("Пройдите вопросы сверху вниз; ответ — внизу ветки.", "Answer the questions top-down."),
         node("Слово — глагол или деепричастие?", "Is it a verb or a verbal adverb?",
              leaf("Раздельно (кроме слов без НЕ: ненавидеть).", "Separate (except words without НЕ: ненавидеть).", "не читая", "не заметил"),
              node("Есть противопоставление с союзом А?", "Is there a contrast with А?",
                   leaf("Раздельно.", "Separate.", "не весёлый, а грустный"),
                   node("Это причастие с зависимыми словами или краткое причастие?", "A participle with dependents or a short one?",
                        leaf("Раздельно.", "Separate.", "не решённая ещё задача", "задача не решена"),
                        leaf("Слитно, если слово без НЕ не употребляется или есть синоним без НЕ.",
                             "Solid if the word does not exist without НЕ or has a synonym without НЕ.", "небрежный", "невесёлый вид"))))),
    tree("tree-n-nn", ("Н или НН в отглагольном слове", "Н or НН in a deverbal word"),
         ("Для отыменных прилагательных смотрите таблицу суффиксов.", "For denominal adjectives see the suffix table."),
         node("Есть приставка (кроме не-)?", "Is there a prefix (other than не-)?", leaf("НН.", "НН.", "покрашенный пол"),
              node("Есть зависимые слова?", "Are there dependent words?", leaf("НН.", "НН.", "жаренная в масле картошка"),
                   node("Это краткая форма?", "Is it a short form?", leaf("Н.", "Н.", "задача решена"),
                        leaf("Н (проверьте исключения: желанный, медленный, нежданный — НН).",
                             "Н (check exceptions: желанный, медленный — НН).", "жареная картошка", "кованый сундук"))))),
    tree("tree-tsya", ("-ТСЯ или -ТЬСЯ", "-ТСЯ or -ТЬСЯ"), ("Вопрос задаётся от главного слова.", "Ask from the head word."),
         node("Глагол отвечает на вопрос «что делать?» / «что сделать?»", "Does the verb answer «что делать?/что сделать?»",
              leaf("-ться (в вопросе есть ь).", "-ться (the question has ь).", "нужно научиться", "любят купаться"),
              leaf("-тся («что делает?» / «что сделает?»).", "-тся («что делает?»).", "ему не терпится", "ветка качается"))),
    tree("tree-dash", ("Нужно ли тире между подлежащим и сказуемым", "Is a dash needed"),
         ("Тире ставится только без связки.", "A dash only without a linking verb."),
         node("Подлежащее — личное местоимение, есть НЕ, союз «как» или связка?", "Personal pronoun, НЕ, «как» or a link?",
              leaf("Тире не ставится.", "No dash.", "Он студент.", "Бедность не порок."),
              node("Оба главных члена — существительные в И. п., числительные или инфинитивы?",
                   "Both are nominative nouns, numerals or infinitives?",
                   leaf("Ставится тире.", "Dash.", "Москва — столица России.", "Дважды два — четыре."),
                   leaf("Тире не ставится (например, сказуемое — прилагательное).", "No dash (e.g. an adjective predicate).",
                        "Вода холодная.")))),
    tree("tree-comma-i", ("Запятая перед И", "Comma before И"), ("Сначала посчитайте основы.", "Count the clauses first."),
         node("И соединяет две грамматические основы?", "Does И join two clauses?",
              node("Есть общий второстепенный член или общая придаточная часть?", "Is there a shared part?",
                   leaf("Запятая не ставится.", "No comma.", "Вдруг солнце скрылось и подул ветер."),
                   leaf("Запятая ставится.", "Comma.", "Солнце скрылось, и подул ветер.")),
              leaf("Это однородные члены или однородные придаточные — запятая не ставится.",
                   "Homogeneous parts/clauses — no comma.", "Он открыл окно и выглянул."))),
    tree("tree-o-yo", ("О или Ё после шипящих", "О or Ё after hushing consonants"),
         ("Сначала определите морфему с пропуском.", "Find the morpheme first."),
         node("Пропуск в корне?", "Is the gap in the root?",
              node("Есть однокоренное слово с е?", "Is there a cognate with е?", leaf("Ё.", "Ё.", "чёрный — чернеть"),
                   leaf("О (словарное слово, заимствование, беглая гласная).", "О (dictionary word, loan, fleeting vowel).",
                        "шорох", "шоколад", "шов")),
              node("Это суффикс или окончание существительного, прилагательного или наречия под ударением?",
                   "A stressed noun/adjective/adverb suffix or ending?",
                   leaf("О.", "О.", "плащом", "медвежонок", "горячо"),
                   leaf("Ё (глагольные формы и слова от них, суффикс -ёр-).", "Ё (verbal forms, -ёр-).", "дирижёр", "тушёнка")))),
    tree("tree-pre-pri", ("ПРЕ- или ПРИ-", "ПРЕ- or ПРИ-"), ("Определите значение приставки.", "Find the prefix meaning."),
         node("Можно заменить на «очень» или «пере-»?", "Replaceable by «очень» or «пере-»?",
              leaf("ПРЕ-.", "ПРЕ-.", "прекрасный", "преодолеть"),
              node("Значение — приближение, присоединение, близость, неполнота действия?",
                   "Approach, joining, nearness or an incomplete action?",
                   leaf("ПРИ-.", "ПРИ-.", "приехать", "прибрежный", "приоткрыть"),
                   leaf("Проверьте по словарю.", "Check the dictionary.", "привилегия", "пренебрегать")))),
    tree("tree-asyndetic", ("Знак в бессоюзном предложении", "Mark in an asyndetic sentence"),
         ("Вставьте подходящий союз.", "Insert a fitting conjunction."),
         node("Подходит «что», «а именно» или «потому что»?", "Does «что/а именно/потому что» fit?",
              leaf("Двоеточие.", "Colon.", "Я знаю: ты придёшь.", "Мне не спалось: мешал шум."),
              node("Подходит «поэтому», «если», «когда», «а», «но»?", "Does «поэтому/если/когда/а/но» fit?",
                   leaf("Тире.", "Dash.", "Лес рубят — щепки летят.", "Приедешь — поговорим."),
                   leaf("Запятая (перечисление).", "Comma (listing).", "Ветер стих, небо прояснилось.")))),
    tree("tree-alt-ei", ("Е или И в корне с чередованием", "Е or И in an alternating root"),
         ("Корни: -бер-, -дер-, -мер-, -пер-, -тер-, -блест-, -жег-, -стел-, -чет-.", "Roots: -бер-, -дер-, …"),
         node("После корня стоит суффикс -а-?", "Does the suffix -а- follow the root?",
              leaf("И (исключения: сочетать, сочетание).", "И (exceptions: сочетать, сочетание).", "собирать", "блистать"),
              leaf("Е.", "Е.", "соберу", "блестеть"))),
]

SVGS = [_stress(), _sounds(), _morphemes(), _chain(), _root_check(), _sentence(), _phrases(), _schemes(), _bsp(), _dash(),
        _isolation(), _text_structure(), _cohesion(), _boundary()]
FIGURES = {entry["id"]: entry for entry in SVGS + TABLES + TREES}

LESSON_FIGURES = {
    "sounds-letters": ["letters-sounds", "table-iotated"], "stress": ["stress-zvonit", "table-stress"],
    "word-meaning": ["table-paronyms"], "synonyms-antonyms": ["table-paronyms"], "paronyms": ["table-paronyms"],
    "phraseology": ["table-styles"], "pleonasm": ["table-paronyms"], "morphemes": ["morpheme-podokonnik", "table-ending"],
    "word-formation": ["chain-uchit", "table-formation"], "root-vowels": ["root-check"], "root-alt-oa": ["table-alt-oa"],
    "root-alt-ei": ["table-alt-ei", "tree-alt-ei"], "consonants": ["root-check"], "double-consonants": ["table-hyphen"],
    "prefix-z-s": ["table-pre-pri"], "prefix-pre-pri": ["table-pre-pri", "tree-pre-pri"], "y-after-prefix": ["hard-soft-boundary"],
    "hard-soft-sign": ["hard-soft-boundary"], "soft-sign-sibilants": ["table-soft-sign"], "noun-endings": ["table-declension"],
    "noun-adj-suffixes": ["table-n-nn"], "o-yo-sibilants": ["tree-o-yo"], "verb-endings": ["table-conjugation"],
    "tsya": ["tree-tsya"], "participle-suffixes": ["table-conjugation"], "adjectives": ["phrase-links"],
    "function-words": ["table-prepositions"], "verb-aspect": ["table-predicates"], "n-nn": ["table-n-nn", "tree-n-nn"],
    "ne-parts": ["table-ne", "tree-ne"], "ne-ni": ["table-ne"], "hyphen-compounds": ["table-hyphen"], "adverbs": ["table-hyphen"],
    "prep-conj-particles": ["table-tozhe", "table-chtoby", "table-prepositions"], "noun-declension": ["table-declension"],
    "numerals": ["table-numerals"], "government": ["phrase-links"], "participial-gerund": ["isolation-position"],
    "phrases": ["phrase-links"], "sentence-members": ["sentence-base", "table-predicates"], "dash-subject": ["dash-subject", "tree-dash"],
    "homogeneous": ["sentence-base"], "isolation": ["isolation-position"], "introductory": ["table-introductory"],
    "kak": ["table-introductory"], "compound": ["scheme-ssp-spp", "tree-comma-i"], "complex": ["scheme-ssp-spp"],
    "asyndetic": ["scheme-bsp", "table-asyndetic", "tree-asyndetic"], "mixed": ["scheme-ssp-spp"],
    "complex-types": ["table-complex-types"], "direct-speech": ["table-direct-speech"],
    "text-subtopics": ["text-reasoning"], "text-cohesion": ["cohesion-chain", "table-cohesion"],
    "text-styles": ["table-styles", "table-types"],
}


def payload():
    return deepcopy(FIGURES)


def _bilingual(value):
    return isinstance(value, dict) and set(value) == {"ru", "en"} and all(
        isinstance(value[lang], str) and value[lang].strip() for lang in ("ru", "en"))


def _cell(value):
    return (isinstance(value, str) and value.strip()) or _bilingual(value)


def _tree(entry, depth=0):
    if depth > 6 or not isinstance(entry, dict):
        raise ValueError("invalid decision tree")
    if set(entry) == {"result", "examples"}:
        if not _bilingual(entry["result"]) or not isinstance(entry["examples"], list) or any(
                not isinstance(example, str) or not example.strip() for example in entry["examples"]):
            raise ValueError("invalid decision tree leaf")
        return
    if set(entry) != {"q", "yes", "no"} or not _bilingual(entry["q"]):
        raise ValueError("invalid decision tree node")
    _tree(entry["yes"], depth + 1)
    _tree(entry["no"], depth + 1)


UNSAFE = ("<", ">", "://", "javascript:", "data:")


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def validate(figures):
    """Strict JSON contract for all three kinds. Fail closed even for a broken last item."""
    if not isinstance(figures, dict) or not figures:
        raise ValueError("diagram catalogue is empty")
    for key, entry in figures.items():
        if any(marker in text.lower() for text in _strings(entry) for marker in UNSAFE):
            raise ValueError(f"diagram {key}: markup or URLs are not allowed in figure text")
        if entry.get("id") != key or not key or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in key):
            raise ValueError("invalid diagram id")
        kind = entry.get("kind")
        if not _bilingual(entry.get("title")) or not _bilingual(entry.get("caption")):
            raise ValueError(f"diagram {key} needs bilingual title and caption")
        if kind == "table":
            if set(entry) != {"id", "kind", "title", "caption", "columns", "rows"}:
                raise ValueError("unexpected table field")
            columns, rows = entry["columns"], entry["rows"]
            if not isinstance(columns, list) or not 2 <= len(columns) <= 5 or not all(_bilingual(c) for c in columns):
                raise ValueError("invalid table header")
            if not isinstance(rows, list) or not 1 <= len(rows) <= 30 or any(
                    not isinstance(row, list) or len(row) != len(columns) or not all(_cell(cell) for cell in row) for row in rows):
                raise ValueError(f"invalid table rows in {key}")
            continue
        if kind == "tree":
            if set(entry) != {"id", "kind", "title", "caption", "root"}:
                raise ValueError("unexpected tree field")
            _tree(entry["root"])
            continue
        if kind != "svg":
            raise ValueError("unknown diagram kind")
        if set(entry) - {"id", "kind", "title", "caption", "width", "height", "drawing", "legend"}:
            raise ValueError("unexpected diagram field")
        if entry.get("width") != WIDTH or entry.get("height") != HEIGHT:
            raise ValueError("invalid diagram viewport")
        drawing = entry.get("drawing")
        if not isinstance(drawing, list) or not 1 <= len(drawing) <= 250:
            raise ValueError("invalid diagram drawing")
        for item in drawing:
            shape = item.get("kind")
            if shape not in FIELDS or set(item) - ({"kind", "role", "filled"} | FIELDS[shape]) or FIELDS[shape] - set(item):
                raise ValueError("unsafe or incomplete diagram primitive")
            if item.get("role") not in ROLES or not isinstance(item.get("filled"), bool):
                raise ValueError("invalid diagram styling")
            for field in FIELDS[shape] - {"points", "text", "anchor"}:
                value = item[field]
                bound = HEIGHT if field.startswith("y") or field in {"cy", "height", "ry"} else WIDTH
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= bound:
                    raise ValueError(f"invalid diagram coordinate in {key}")
                if field in {"r", "rx", "ry", "width", "height"} and value <= 0:
                    raise ValueError("invalid diagram size")
            if shape in {"polyline", "polygon"}:
                points = item["points"]
                if not isinstance(points, list) or not (3 if shape == "polygon" else 2) <= len(points) <= 500:
                    raise ValueError("invalid diagram points")
                for point in points:
                    if not isinstance(point, list) or len(point) != 2 or any(
                            isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in point) \
                            or not (0 <= point[0] <= WIDTH and 0 <= point[1] <= HEIGHT):
                        raise ValueError(f"invalid diagram point in {key}")
            if shape == "text" and (item["anchor"] not in {"start", "middle", "end"} or not _bilingual(item["text"])):
                raise ValueError("invalid bilingual diagram label")
        for item in entry.get("legend", []):
            if set(item) != {"role", "text"} or item["role"] not in ROLES or not _bilingual(item["text"]):
                raise ValueError("invalid diagram legend")
    return figures
