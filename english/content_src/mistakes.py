"""content_src/mistakes.py — типичные ошибки: диагноз и что с этим делать.

Ключ — тег задания (``task.tags``). При неверном ответе приложение показывает
диагноз: почему так отвечают, как правильно и на какую карточку справочника
перейти. Диагноз формулируется как учебная подсказка, а не как оценка.
"""

from __future__ import annotations

ERRORS = {
    "tenses.present_perfect": {
        "title": {"ru": "Present Perfect вместо Past Simple (и наоборот)",
                  "en": "Present Perfect instead of Past Simple"},
        "why": {"ru": "С «since» и «already» действие связано с настоящим, поэтому Past Simple не подходит.",
                "en": "With “since” and “already” the action is linked to the present, so the Past Simple fails."},
        "fix": {"ru": "Проверьте, идёт ли действие до сих пор: если да — have/has + V3.",
                "en": "Check whether the action continues up to now: if yes, use have/has + V3."},
        "rule": "present-simple"},
    "tenses.present_continuous": {
        "title": {"ru": "Действие «прямо сейчас»", "en": "An action happening right now"},
        "why": {"ru": "«Look!», «now», «at the moment» указывают на момент речи.",
                "en": "“Look!”, “now” and “at the moment” point at the moment of speaking."},
        "fix": {"ru": "В момент речи: am/is/are + Ving.", "en": "At the moment of speaking: am/is/are + Ving."},
        "rule": "present-simple"},
    "tenses.past_perfect": {
        "title": {"ru": "Порядок действий в прошлом", "en": "The order of past actions"},
        "why": {"ru": "Если одно действие произошло раньше другого, нужен Past Perfect.",
                "en": "When one action happened before another, the Past Perfect is required."},
        "fix": {"ru": "Раньше другого прошедшего — had + V3.", "en": "Earlier than another past action: had + V3."},
        "rule": "perfect-forms"},
    "tenses.past_continuous": {
        "title": {"ru": "Прерванное действие", "en": "An interrupted action"},
        "why": {"ru": "Фоновое действие в прошлом описывается Past Continuous.",
                "en": "A background action in the past is described with the Past Continuous."},
        "fix": {"ru": "Фон — was/were + Ving, короткое действие — Past Simple.",
                "en": "The background takes was/were + Ving; the short action takes the Past Simple."},
        "rule": "perfect-forms"},
    "modals.criticism": {
        "title": {"ru": "Упрёк о прошлом", "en": "A reproach about the past"},
        "why": {"ru": "«Should have + V3» говорит о том, чего не сделали.",
                "en": "“Should have + V3” describes what was not done."},
        "fix": {"ru": "Не выполнено в прошлом: should have + V3 (не «should did»).",
                "en": "For an unfulfilled past action: should have + V3."},
        "rule": "modal-meaning"},
    "modals.deduction": {
        "title": {"ru": "Уверенный вывод и невозможность", "en": "Deduction and impossibility"},
        "why": {"ru": "«Must» — уверенность, «cannot have» — «не может быть, чтобы».",
                "en": "“Must” states certainty; “cannot have” states impossibility."},
        "fix": {"ru": "Для прошлого: must have + V3 / cannot have + V3.",
                "en": "For the past: must have + V3 / cannot have + V3."},
        "rule": "modal-meaning"},
    "passive.future_simple": {
        "title": {"ru": "Будущее в пассиве", "en": "The future passive"},
        "why": {"ru": "В пассиве время показывает «be», поэтому нужен «will be + V3».",
                "en": "In the passive the verb “be” carries the tense, so “will be + V3” is required."},
        "fix": {"ru": "Будущее действие над предметом: will be + V3.",
                "en": "A future action on the object: will be + V3."},
        "rule": "passive-forms"},
    "passive.past_simple": {
        "title": {"ru": "Предмет не действует сам", "en": "The object does not act by itself"},
        "why": {"ru": "Если подлежащее испытывает действие, нужен пассив.",
                "en": "When the subject receives the action, the passive is required."},
        "fix": {"ru": "was/were + V3, исполнитель — с «by».",
                "en": "was/were + V3, with the doer introduced by “by”."},
        "rule": "passive-forms"},
    "conditionals.first": {
        "title": {"ru": "Будущее в условии", "en": "The future in the if-clause"},
        "why": {"ru": "После «if» будущее не употребляется.",
                "en": "The future is not used after “if”."},
        "fix": {"ru": "Условие — Present Simple, главная часть — will + V.",
                "en": "The if-clause takes the Present Simple, the main clause will + V."},
        "rule": "conditionals"},
    "conditionals.third": {
        "title": {"ru": "Нереальное условие о прошлом", "en": "An unreal past condition"},
        "why": {"ru": "Раз действие не состоялось, нужен III тип условия.",
                "en": "Because the action did not happen, the third conditional is required."},
        "fix": {"ru": "if + had + V3, would have + V3.", "en": "if + had + V3, would have + V3."},
        "rule": "conditionals"},
    "conditionals.reported_speech": {
        "title": {"ru": "Сдвиг времени в косвенной речи", "en": "Tense shift in reported speech"},
        "why": {"ru": "При переводе в косвенную речь время сдвигается назад.",
                "en": "In reported speech the tense shifts one step back."},
        "fix": {"ru": "will → would, is → was, Present Perfect → Past Perfect.",
                "en": "will → would, is → was, Present Perfect → Past Perfect."},
        "rule": "conditionals"},
    "nonfinite.gerund_after_preposition": {
        "title": {"ru": "После предлога — герундий", "en": "A preposition takes the gerund"},
        "why": {"ru": "После предлога инфинитив невозможен.",
                "en": "The infinitive cannot follow a preposition."},
        "fix": {"ru": "interested in learning, without saying.",
                "en": "interested in learning, without saying."},
        "rule": "gerund-vs-infinitive"},
    "nonfinite.gerund_after_verb": {
        "title": {"ru": "Глаголы, требующие герундий", "en": "Verbs that take the gerund"},
        "why": {"ru": "Enjoy, avoid, mind, suggest требуют герундий, а не инфинитив.",
                "en": "Enjoy, avoid, mind and suggest take the gerund, not the infinitive."},
        "fix": {"ru": "Запомните группу: enjoy/avoid/mind/suggest + Ving.",
                "en": "Memorise the group: enjoy/avoid/mind/suggest + Ving."},
        "rule": "gerund-vs-infinitive"},
    "articles.definite": {
        "title": {"ru": "Определённый артикль", "en": "The definite article"},
        "why": {"ru": "«The» ставится перед единственным в своём роде и в устойчивых выражениях "
                      "с инструментами.",
                "en": "“The” is used for unique objects and fixed expressions with instruments."},
        "fix": {"ru": "play the piano, the sun, the Netherlands.",
                "en": "play the piano, the sun, the Netherlands."},
        "rule": "articles-basic"},
    "articles.zero": {
        "title": {"ru": "Нулевой артикль", "en": "The zero article"},
        "why": {"ru": "С неисчисляемыми, с приёмами пищи и в выражениях at school артикль не нужен.",
                "en": "Uncountable nouns, meals and expressions like at school take no article."},
        "fix": {"ru": "have breakfast, at school, advice, information.",
                "en": "have breakfast, at school, advice, information."},
        "rule": "articles-basic"},
    "articles.indefinite": {
        "title": {"ru": "a или an", "en": "a or an"},
        "why": {"ru": "Выбор зависит от звука, а не от буквы.",
                "en": "The choice depends on the sound, not on the letter."},
        "fix": {"ru": "an hour, a university, an honest man.",
                "en": "an hour, a university, an honest man."},
        "rule": "articles-basic"},
    "articles.uncountable": {
        "title": {"ru": "Неисчисляемые существительные", "en": "Uncountable nouns"},
        "why": {"ru": "Advice, information, news не имеют формы множественного числа.",
                "en": "Advice, information and news have no plural form."},
        "fix": {"ru": "Some advice, a piece of news — через «piece».",
                "en": "Use “some advice”, “a piece of news”."},
        "rule": "articles-basic"},
    "prepositions.collocation": {
        "title": {"ru": "Предлог закреплён за словом", "en": "The preposition belongs to its word"},
        "why": {"ru": "Переводить предлог отдельно от слова нельзя.",
                "en": "The preposition cannot be translated apart from its word."},
        "fix": {"ru": "depend on, good at, interested in, responsible for.",
                "en": "depend on, good at, interested in, responsible for."},
        "rule": "prepositions-collocation"},
    "prepositions.time": {
        "title": {"ru": "since и for", "en": "since and for"},
        "why": {"ru": "«Since» — точка отсчёта, «for» — отрезок времени.",
                "en": "“Since” takes a starting point, “for” takes a period."},
        "fix": {"ru": "since 2019 / for five years.", "en": "since 2019 / for five years."},
        "rule": "prepositions-collocation"},
    "pronouns.quantifiers": {
        "title": {"ru": "fewer/less, neither/none", "en": "fewer/less, neither/none"},
        "why": {"ru": "Выбор зависит от исчисляемости и от количества предметов.",
                "en": "The choice depends on countability and on how many objects there are."},
        "fix": {"ru": "fewer students, less time, neither of two, none of many.",
                "en": "fewer students, less time, neither of two, none of many."},
        "rule": "quantifiers"},
    "pronouns.possessive": {
        "title": {"ru": "its и it's", "en": "its and it's"},
        "why": {"ru": "«It's» — сокращение «it is», притяжательное — «its».",
                "en": "“It's” means “it is”; the possessive form is “its”."},
        "fix": {"ru": "The company opened its office; it's raining.",
                "en": "The company opened its office; it's raining."},
        "rule": "quantifiers"},
    "noun_adj_adv.adjective": {
        "title": {"ru": "Прилагательное или наречие", "en": "Adjective or adverb"},
        "why": {"ru": "Прилагательное описывает предмет, наречие — действие.",
                "en": "An adjective describes a thing; an adverb describes an action."},
        "fix": {"ru": "The task is useful (прилагательное); he works usefully? — нет: works hard.",
                "en": "The task is useful; the adverb is used with verbs."},
        "rule": "adjective-adverb"},
    "noun_adj_adv.adverb": {
        "title": {"ru": "Наречия на -ly и исключения", "en": "Adverbs in -ly and the exceptions"},
        "why": {"ru": "Hard — «усердно», hardly — «едва»: похожие слова, разный смысл.",
                "en": "Hard means “with effort”, hardly means “almost not”."},
        "fix": {"ru": "he works hard; he hardly works.",
                "en": "he works hard; he hardly works."},
        "rule": "adjective-adverb"},
    "noun_adj_adv.comparison": {
        "title": {"ru": "Степени сравнения", "en": "Comparative and superlative"},
        "why": {"ru": "У коротких слов — -er/-est, у длинных — more/most; вместе их не смешивают.",
                "en": "Short words take -er/-est, long words take more/most; the two are not mixed."},
        "fix": {"ru": "better — the best, more interesting — the most interesting.",
                "en": "better — the best, more interesting — the most interesting."},
        "rule": "quantifiers"},
    "word_formation.suffix_noun": {
        "title": {"ru": "Нужно существительное", "en": "A noun is required"},
        "why": {"ru": "После «his, my, the» и прилагательного стоит существительное.",
                "en": "After “his, my, the” and adjectives a noun stands."},
        "fix": {"ru": "achieve → achievement, kind → kindness.",
                "en": "achieve → achievement, kind → kindness."},
        "rule": "suffixes"},
    "word_formation.suffix_adjective": {
        "title": {"ru": "Нужно прилагательное", "en": "An adjective is required"},
        "why": {"ru": "Перед существительным и после «be» стоит прилагательное.",
                "en": "Before a noun and after “be” an adjective stands."},
        "fix": {"ru": "success → successful, ambition → ambitious.",
                "en": "success → successful, ambition → ambitious."},
        "rule": "suffixes"},
    "word_formation.suffix_adverb": {
        "title": {"ru": "Нужно наречие", "en": "An adverb is required"},
        "why": {"ru": "Глагол действия определяет наречие на -ly.",
                "en": "An action verb takes the adverb in -ly."},
        "fix": {"ru": "confident → confidently, angry → angrily.",
                "en": "confident → confidently, angry → angrily."},
        "rule": "suffixes"},
    "word_formation.prefix_negative": {
        "title": {"ru": "Отрицательное значение", "en": "The negative meaning"},
        "why": {"ru": "Отрицание образуется приставкой un-/im-/in-/dis-.",
                "en": "Negation is formed with un-/im-/in-/dis-."},
        "fix": {"ru": "possible → impossible, predictable → unpredictable.",
                "en": "possible → impossible, predictable → unpredictable."},
        "rule": "suffixes"},
    "gap_fill.collocation": {
        "title": {"ru": "Устойчивое сочетание в пропуске", "en": "A fixed collocation in the gap"},
        "why": {"ru": "В устойчивых выражениях ответ не выводится из правила.",
                "en": "In fixed expressions the answer does not follow from a rule."},
        "fix": {"ru": "be used to, keen on, fall asleep — учить целиком.",
                "en": "be used to, keen on, fall asleep — learn them as a whole."},
        "rule": "gap-strategy"},
    "gap_fill.preposition": {
        "title": {"ru": "Предлог в пропуске", "en": "A preposition in the gap"},
        "why": {"ru": "Предлог зависит от соседнего слова, а не от русского перевода.",
                "en": "The preposition depends on its neighbouring word."},
        "fix": {"ru": "at nine o'clock, since childhood, for five years.",
                "en": "at nine o'clock, since childhood, for five years."},
        "rule": "gap-strategy"},
    "extra_word.preposition": {
        "title": {"ru": "Лишний предлог", "en": "An extra preposition"},
        "why": {"ru": "Русский глагол требует предлога, английский — нет: discuss, enter, marry.",
                "en": "Russian verbs may need a preposition where English ones do not: discuss, enter, marry."},
        "fix": {"ru": "Уберите предлог и перечитайте: discuss the plan, enter the room.",
                "en": "Remove the preposition and reread: discuss the plan, enter the room."},
        "rule": "extra-word-strategy"},
    "extra_word.subject": {
        "title": {"ru": "Лишнее подлежащее", "en": "An extra subject"},
        "why": {"ru": "По-русски можно повторить подлежащее, по-английски — нет.",
                "en": "Russian may repeat the subject; English does not."},
        "fix": {"ru": "My friend lives in Brest (без «he»).",
                "en": "My friend lives in Brest (without “he”)."},
        "rule": "extra-word-strategy"},
    "communication.translation": {
        "title": {"ru": "Перевод фрагмента", "en": "Translating a fragment"},
        "why": {"ru": "Дословный перевод сохраняет русскую форму вместо английской.",
                "en": "A word-for-word translation keeps Russian forms instead of English ones."},
        "fix": {"ru": "Смотрите на время и структуру: have never been to, if + Past Simple, would + V.",
                "en": "Follow English patterns: have never been to, if + Past Simple, would + V."},
        "rule": "replies"},
    "__default": {
        "title": {"ru": "Разберите правило и попробуйте ещё раз",
                  "en": "Review the rule and try again"},
        "why": {"ru": "Ошибка не привязана к одной теме: посмотрите правило и разобранный пример.",
                "en": "The mistake is not tied to a single area: review the rule and the worked example."},
        "fix": {"ru": "Откройте «Правила», прочитайте карточку и выполните однотипные задания.",
                "en": "Open “Rules”, read the card and do the analogous exercises."},
        "rule": "gap-strategy"},
}

CHECKLIST = [
    {"ru": "Проверьте, не изменился ли смысл: время, число, порядок слов.",
     "en": "Check whether the meaning changed: tense, number, word order."},
    {"ru": "Посмотрите на слово перед пропуском — оно подсказывает форму.",
     "en": "Look at the word before the gap — it suggests the form."},
    {"ru": "Перечитайте предложение целиком после ответа.",
     "en": "Reread the whole sentence after answering."},
    {"ru": "Отдельно проверьте предлог и артикль: их чаще всего теряют.",
     "en": "Check the preposition and the article separately: they are the most frequent omissions."},
    {"ru": "Если ответ не сходится, откройте правило из разбора ошибки.",
     "en": "If the answer does not work out, open the rule from the mistake analysis."},
]


#: дополнительные диагнозы (см. mistakes_more.py) — на каждый тег заданий
import mistakes_more  # noqa: E402

ALL_ERRORS = {**ERRORS, **mistakes_more.ERRORS}


def payload() -> dict:
    return {"errors": ALL_ERRORS, "checklist": CHECKLIST}


def tags() -> list[str]:
    return sorted(key for key in ALL_ERRORS if not key.startswith("__"))
