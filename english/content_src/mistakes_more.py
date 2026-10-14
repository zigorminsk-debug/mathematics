"""content_src/mistakes_more.py — дополнительные диагнозы типичных ошибок.

Первая часть диагнозов (самые частые ошибки) — в ``mistakes.py``; здесь
дополнение, чтобы **каждый** тег задания имел объяснение: сборка контента падает,
если задание ссылается на несуществующий диагноз.

Формат тот же: ``title`` — о чём ошибка, ``why`` — почему так отвечают,
``fix`` — как правильно, ``rule`` — карточка справочника для разбора.
"""

from __future__ import annotations

ERRORS = {
    # --- времена ------------------------------------------------------------
    "tenses.present_simple": {
        "title": {"ru": "Постоянное действие и расписание",
                  "en": "Habits and timetables"},
        "why": {"ru": "Обычное действие и расписание описываются Present Simple.",
                "en": "Habits and timetables take the Present Simple."},
        "fix": {"ru": "every day / on Mondays → V(s).", "en": "every day / on Mondays → V(s)."},
        "rule": "present-simple"},
    "tenses.future_continuous": {
        "title": {"ru": "Процесс в будущем", "en": "An action in progress in the future"},
        "why": {"ru": "«This time tomorrow» описывает действие в процессе, а не факт.",
                "en": "“This time tomorrow” describes an action in progress, not a fact."},
        "fix": {"ru": "will be + Ving.", "en": "will be + Ving."},
        "rule": "perfect-forms"},
    "tenses.future_perfect": {
        "title": {"ru": "Результат к моменту в будущем", "en": "Completion by a future moment"},
        "why": {"ru": "«By the end of …» требует формы, которая подчёркивает завершение.",
                "en": "“By the end of …” needs a form that marks completion."},
        "fix": {"ru": "will have + V3.", "en": "will have + V3."},
        "rule": "perfect-forms"},
    "tenses.present_perfect_continuous": {
        "title": {"ru": "Длительность до момента речи", "en": "Duration up to now"},
        "why": {"ru": "Подчёркивается сам процесс и его продолжительность.",
                "en": "The process and its duration are emphasised."},
        "fix": {"ru": "has/have been + Ving.", "en": "has/have been + Ving."},
        "rule": "perfect-forms"},
    # --- модальные ----------------------------------------------------------
    "modals.ability": {
        "title": {"ru": "Умение", "en": "Ability"},
        "why": {"ru": "«Can» не имеет формы прошедшего времени; в прошлом — «could».",
                "en": "“Can” has no past form; the past of ability is “could”."},
        "fix": {"ru": "could swim when she was five.", "en": "could swim when she was five."},
        "rule": "modal-meaning"},
    "modals.advice": {
        "title": {"ru": "Совет", "en": "Advice"},
        "why": {"ru": "Совет выражают «should» и «had better»; «must» — обязанность.",
                "en": "Advice takes “should” or “had better”; “must” states obligation."},
        "fix": {"ru": "You should / had better take an umbrella.", "en": "You should / had better take an umbrella."},
        "rule": "modal-meaning"},
    "modals.prohibition": {
        "title": {"ru": "Запрет", "en": "Prohibition"},
        "why": {"ru": "Запрет — «must not»; «may not» звучит как формальное разрешение.",
                "en": "A prohibition takes “must not”; “may not” sounds like a formal restriction."},
        "fix": {"ru": "Passengers must not smoke on board.", "en": "Passengers must not smoke on board."},
        "rule": "modal-meaning"},
    "modals.request": {
        "title": {"ru": "Вежливая просьба", "en": "A polite request"},
        "why": {"ru": "Вежливая просьба начинается с «Could/Would you …?».",
                "en": "A polite request starts with “Could/Would you …?”."},
        "fix": {"ru": "Could you help me, please?", "en": "Could you help me, please?"},
        "rule": "modal-meaning"},
    # --- пассив -------------------------------------------------------------
    "passive.present_simple": {
        "title": {"ru": "Общий факт в пассиве", "en": "A general fact in the passive"},
        "why": {"ru": "Действие совершается над подлежащим постоянно.",
                "en": "The action is regularly performed on the subject."},
        "fix": {"ru": "is/are + V3.", "en": "is/are + V3."},
        "rule": "passive-forms"},
    "passive.present_perfect": {
        "title": {"ru": "Результат в пассиве", "en": "A result in the passive"},
        "why": {"ru": "Важен результат к моменту речи, а не исполнитель.",
                "en": "The result up to now matters, not the doer."},
        "fix": {"ru": "has/have been + V3.", "en": "has/have been + V3."},
        "rule": "passive-forms"},
    "passive.past_perfect": {
        "title": {"ru": "Пассив раньше другого действия",
                  "en": "A passive action earlier than another"},
        "why": {"ru": "Одно действие совершилось до другого прошедшего.",
                "en": "One action happened before another past action."},
        "fix": {"ru": "had been + V3.", "en": "had been + V3."},
        "rule": "passive-forms"},
    "passive.past_continuous": {
        "title": {"ru": "Процесс в пассиве", "en": "A process in the passive"},
        "why": {"ru": "Действие происходило в определённый момент в прошлом.",
                "en": "The action was in progress at a past moment."},
        "fix": {"ru": "was/were being + V3.", "en": "was/were being + V3."},
        "rule": "passive-forms"},
    # --- условные -----------------------------------------------------------
    "conditionals.second": {
        "title": {"ru": "Нереальное условие о настоящем", "en": "An unreal present condition"},
        "why": {"ru": "«If I were you» — нереальное условие: в главной части «would».",
                "en": "“If I were you” is unreal, so the main clause takes “would”."},
        "fix": {"ru": "if + Past Simple, would + V.", "en": "if + Past Simple, would + V."},
        "rule": "conditionals"},
    "conditionals.wish": {
        "title": {"ru": "Сожаление", "en": "Regret"},
        "why": {"ru": "После «I wish» время сдвигается назад: о прошлом — Past Perfect.",
                "en": "After “I wish” the tense shifts back: the past takes the Past Perfect."},
        "fix": {"ru": "I wish I had had more time.", "en": "I wish I had had more time."},
        "rule": "conditionals"},
    # --- неличные формы -----------------------------------------------------
    "nonfinite.infinitive_after_verb": {
        "title": {"ru": "Инфинитив после глагола", "en": "The infinitive after a verb"},
        "why": {"ru": "Would like, want, decide, hope требуют инфинитив с «to».",
                "en": "Would like, want, decide and hope take the infinitive with “to”."},
        "fix": {"ru": "would like to read.", "en": "would like to read."},
        "rule": "gerund-vs-infinitive"},
    "nonfinite.participle": {
        "title": {"ru": "Причастие вместо придаточного", "en": "A participle instead of a clause"},
        "why": {"ru": "Причастие сокращает придаточное: письмо, которое отправили → the letter sent.",
                "en": "A participle shortens a clause: the letter that was sent → the letter sent."},
        "fix": {"ru": "Having heard the news, she called her mother.",
                "en": "Having heard the news, she called her mother."},
        "rule": "gerund-vs-infinitive"},
    # --- артикли ------------------------------------------------------------
    "articles.geographical": {
        "title": {"ru": "Артикль с географическими названиями",
                  "en": "The article with place names"},
        "why": {"ru": "С the употребляются названия стран во множественном числе, океаны, реки.",
                "en": "Plural country names, oceans and rivers take “the”."},
        "fix": {"ru": "the Netherlands, the USA, the Pacific.", "en": "the Netherlands, the USA, the Pacific."},
        "rule": "articles-basic"},
    "articles.plural": {
        "title": {"ru": "Артикль с множественным числом", "en": "Articles with plural nouns"},
        "why": {"ru": "В общем смысле множественное число идёт без артикля.",
                "en": "Plural nouns in a general sense take no article."},
        "fix": {"ru": "Cars are expensive.", "en": "Cars are expensive."},
        "rule": "articles-basic"},
    # --- предлоги -----------------------------------------------------------
    "prepositions.agent": {
        "title": {"ru": "Исполнитель с «by»", "en": "The agent with “by”"},
        "why": {"ru": "В пассиве исполнитель вводится предлогом «by», инструмент — «with».",
                "en": "In the passive the doer takes “by”, the instrument “with”."},
        "fix": {"ru": "written by Mark Twain / cut with a knife.",
                "en": "written by Mark Twain / cut with a knife."},
        "rule": "prepositions-collocation"},
    "prepositions.phrasal_verb": {
        "title": {"ru": "Фразовый глагол", "en": "A phrasal verb"},
        "why": {"ru": "Смысл глагола задаёт частица: fill in, look after, put off.",
                "en": "The particle decides the meaning: fill in, look after, put off."},
        "fix": {"ru": "Учите глагол вместе с частицей.", "en": "Learn the verb with its particle."},
        "rule": "prepositions-collocation"},
    "prepositions.place": {
        "title": {"ru": "Предлоги места", "en": "Prepositions of place"},
        "why": {"ru": "Точка — at, поверхность — on, пространство — in.",
                "en": "A point takes at, a surface on, a space in."},
        "fix": {"ru": "at the airport, on the wall, in the room.",
                "en": "at the airport, on the wall, in the room."},
        "rule": "prepositions-collocation"},
    # --- местоимения --------------------------------------------------------
    "pronouns.case": {
        "title": {"ru": "Падеж местоимения", "en": "The case of a pronoun"},
        "why": {"ru": "После глагола и предлога употребляется объектная форма (me, him, her).",
                "en": "After a verb or a preposition the object form is used (me, him, her)."},
        "fix": {"ru": "It was me; they invited her.", "en": "It was me; they invited her."},
        "rule": "quantifiers"},
    "pronouns.conjunctions": {
        "title": {"ru": "Парные союзы", "en": "Paired conjunctions"},
        "why": {"ru": "Союзы употребляются парой: either … or, neither … nor, both … and.",
                "en": "These conjunctions come in pairs: either … or, neither … nor, both … and."},
        "fix": {"ru": "Neither the teacher nor the students were late.",
                "en": "Neither the teacher nor the students were late."},
        "rule": "quantifiers"},
    "pronouns.numerals": {
        "title": {"ru": "Порядковые числительные", "en": "Ordinal numerals"},
        "why": {"ru": "В порядковых дефис и -th/-st/-nd: twenty-first, fifth, third.",
                "en": "Ordinals use a hyphen and -th/-st/-nd: twenty-first, fifth, third."},
        "fix": {"ru": "on the twenty-first of May.", "en": "on the twenty-first of May."},
        "rule": "quantifiers"},
    "pronouns.reflexive": {
        "title": {"ru": "Возвратные местоимения", "en": "Reflexive pronouns"},
        "why": {"ru": "Формы на -self согласуются с подлежащим: himself, herself, themselves.",
                "en": "The -self forms agree with the subject: himself, herself, themselves."},
        "fix": {"ru": "He did it himself.", "en": "He did it himself."},
        "rule": "quantifiers"},
    # --- части речи ---------------------------------------------------------
    "noun_adj_adv.participle_adjective": {
        "title": {"ru": "Причастие-прилагательное", "en": "Participle adjectives"},
        "why": {"ru": "Предмет «разочаровывает» (disappointing), человек «разочарован» (disappointed).",
                "en": "Things are disappointing; people feel disappointed."},
        "fix": {"ru": "-ing о предмете, -ed о человеке.", "en": "Use -ing for the cause, -ed for the person."},
        "rule": "adjective-adverb"},
    "noun_adj_adv.quantifiers": {
        "title": {"ru": "Количественные слова", "en": "Quantifiers"},
        "why": {"ru": "Much/little — с неисчисляемыми, many/few — с исчисляемыми.",
                "en": "Much/little take uncountables; many/few take countables."},
        "fix": {"ru": "too much sugar, too many sweets.", "en": "too much sugar, too many sweets."},
        "rule": "quantifiers"},
    "noun_adj_adv.plural": {
        "title": {"ru": "Особые формы множественного числа", "en": "Irregular plurals"},
        "why": {"ru": "People, children, feet — множественное число не по общему правилу.",
                "en": "People, children, feet are irregular plurals."},
        "fix": {"ru": "Учите такие слова отдельно.", "en": "Learn irregular plurals separately."},
        "rule": "quantifiers"},
    "noun_adj_adv.subject_verb": {
        "title": {"ru": "Согласование подлежащего и сказуемого",
                  "en": "Subject-verb agreement"},
        "why": {"ru": "Названия наук и неисчисляемые существительные требуют единственного числа.",
                "en": "Names of sciences and uncountable nouns take a singular verb."},
        "fix": {"ru": "Physics is difficult; the news is good.",
                "en": "Physics is difficult; the news is good."},
        "rule": "quantifiers"},
    # --- словообразование ---------------------------------------------------
    "word_formation.participle_adjective": {
        "title": {"ru": "Результат или причина", "en": "Result or cause"},
        "why": {"ru": "Результаты «разочаровывают» (disappointing), а не «разочарованы».",
                "en": "Results are disappointing; people are disappointed."},
        "fix": {"ru": "The results were disappointing.", "en": "The results were disappointing."},
        "rule": "suffixes"},
    "word_formation.suffix_person": {
        "title": {"ru": "Название человека", "en": "Naming a person"},
        "why": {"ru": "Профессия образуется суффиксами -er/-or/-ist: translator, writer.",
                "en": "Professions take -er/-or/-ist: translator, writer."},
        "fix": {"ru": "translate → translator.", "en": "translate → translator."},
        "rule": "suffixes"},
    # --- часть В ------------------------------------------------------------
    "gap_fill.auxiliary": {
        "title": {"ru": "Вспомогательный глагол в пропуске",
                  "en": "An auxiliary verb in the gap"},
        "why": {"ru": "Пропуск может требовать have/had/will, а не смысловой глагол.",
                "en": "The gap may need have/had/will rather than a main verb."},
        "fix": {"ru": "had to wait, have been waiting.", "en": "had to wait, have been waiting."},
        "rule": "gap-strategy"},
    "gap_fill.comparison": {
        "title": {"ru": "Сравнительная конструкция", "en": "A comparative pattern"},
        "why": {"ru": "«The more …, the better …» — устойчивая конструкция.",
                "en": "“The more …, the better …” is a fixed pattern."},
        "fix": {"ru": "the more you practise, the better you speak.",
                "en": "the more you practise, the better you speak."},
        "rule": "gap-strategy"},
    "gap_fill.modal": {
        "title": {"ru": "Модальный глагол в пропуске", "en": "A modal verb in the gap"},
        "why": {"ru": "Смысл подсказывает значение: способность, необходимость, запрет.",
                "en": "The meaning decides: ability, necessity or prohibition."},
        "fix": {"ru": "could not continue, had better tidy.",
                "en": "could not continue, had better tidy."},
        "rule": "gap-strategy"},
    "gap_fill.tense_form": {
        "title": {"ru": "Форма времени в пропуске", "en": "A tense form in the gap"},
        "why": {"ru": "«It was the first time that …» требует Past Perfect.",
                "en": "“It was the first time that …” takes the Past Perfect."},
        "fix": {"ru": "It was the first time that I had seen.",
                "en": "It was the first time that I had seen."},
        "rule": "gap-strategy"},
    # --- лишнее слово -------------------------------------------------------
    "extra_word.conjunction": {
        "title": {"ru": "Лишний союз", "en": "An extra conjunction"},
        "why": {"ru": "Союз может разрывать предложение, оставляя его без главной части.",
                "en": "A conjunction may split the sentence and leave it without its main part."},
        "fix": {"ru": "Уберите союз и проверьте структуру.",
                "en": "Remove the conjunction and check the structure."},
        "rule": "extra-word-strategy"},
    "extra_word.object": {
        "title": {"ru": "Лишнее дополнение", "en": "An extra object"},
        "why": {"ru": "Английский глагол сам управляет дополнением: need, enter, discuss.",
                "en": "English verbs govern their object directly: need, enter, discuss."},
        "fix": {"ru": "they need a helping hand.", "en": "they need a helping hand."},
        "rule": "extra-word-strategy"},
    "extra_word.comparison": {
        "title": {"ru": "Двойное сравнение", "en": "A double comparative"},
        "why": {"ru": "«Most easiest» и «less fewer» — две формы одного значения.",
                "en": "“Most easiest” and “less fewer” use two comparative markers for one meaning."},
        "fix": {"ru": "the easiest, fewer accidents.", "en": "the easiest, fewer accidents."},
        "rule": "extra-word-strategy"},
    "extra_word.reported_speech": {
        "title": {"ru": "Лишний вспомогательный глагол",
                  "en": "An extra auxiliary verb"},
        "why": {"ru": "В косвенной речи will заменяется на would, а не соседствует с ним.",
                "en": "Reported speech replaces “will” with “would” instead of keeping both."},
        "fix": {"ru": "she would come later.", "en": "she would come later."},
        "rule": "extra-word-strategy"},
    # --- коммуникация -------------------------------------------------------
    "communication.greetings": {
        "title": {"ru": "Приветствия", "en": "Greetings"},
        "why": {"ru": "«How do you do?» — приветствие при знакомстве, а не вопрос о здоровье.",
                "en": "“How do you do?” greets a new acquaintance; it is not about health."},
        "fix": {"ru": "Ответ на него — то же приветствие.",
                "en": "The answer repeats the same greeting."},
        "rule": "replies"},
    "communication.notice": {
        "title": {"ru": "Чтение объявления", "en": "Reading a notice"},
        "why": {"ru": "Объявление читается буквально: last admission, until, closes.",
                "en": "A notice is read literally: last admission, until, closes."},
        "fix": {"ru": "Сверьте время и слово-ограничитель.",
                "en": "Check the time and the limiting word."},
        "rule": "replies"},
    "communication.replies": {
        "title": {"ru": "Готовые реплики", "en": "Fixed replies"},
        "why": {"ru": "У каждой ситуации своя формула: благодарность, извинение, предложение.",
                "en": "Each situation has its own formula: thanks, apology, offer."},
        "fix": {"ru": "Thank you → You are welcome; Sorry → That is all right.",
                "en": "Thank you → You are welcome; Sorry → That is all right."},
        "rule": "replies"},
}
