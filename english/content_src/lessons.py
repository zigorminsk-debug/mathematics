"""content_src/lessons.py — уроки «что изучить» (13 разделов программы).

Урок открывается из разбора ошибки и из справочника: это не пересказ правила, а
разобранный пример по шагам, бытовое объяснение и границы применимости правила
(где форма зависит от контекста и где норма допускает варианты). Каждый урок
ссылается на карточку справочника и, где полезно, на схему.
"""

from __future__ import annotations

LESSONS = [
    {
        "id": "lesson-tenses", "topic": "tenses", "rule": "present-simple",
        "title": {"ru": "Как выбрать время по маркеру", "en": "Choosing the tense by its marker"},
        "summary": {"ru": "Маркер времени в предложении — главная подсказка: он прямо указывает на форму.",
                    "en": "A time marker in the sentence is the main clue: it points at the form directly."},
        "sections": [
            {"kind": "text",
             "ru": "Сначала найдите в предложении обстоятельство времени и только потом выбирайте форму.",
             "en": "Find the time expression first and choose the form afterwards."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«She ___ in Minsk since 2019»", "Маркер: since 2019 — точка отсчёта в прошлом.",
                    "Действие длится до сих пор → Present Perfect.", "Ответ: has lived."],
             "en": ["“She ___ in Minsk since 2019”", "Marker: since 2019 — a starting point in the past.",
                    "The action still continues → Present Perfect.", "Answer: has lived."]},
        ],
        "figure": "tense-timeline",
        "everyday": {"ru": "Как строка в квитанции с датой: «с 2019 года» — значит, срок идёт и сейчас.",
                     "en": "Like a date on a receipt: “since 2019” means the period is still running."},
    },
    {
        "id": "lesson-modals", "topic": "modals", "rule": "modal-meaning",
        "title": {"ru": "Модальный глагол: обязанность, совет или вывод",
                    "en": "A modal: obligation, advice or deduction"},
        "summary": {"ru": "Значение модального глагола определяется ситуацией, а не переводом отдельного слова.",
                    "en": "The meaning of a modal comes from the situation, not from a single translation."},
        "sections": [
            {"kind": "text",
             "ru": "Определите, что выражает предложение: запрет, совет, уверенность или вероятность.",
             "en": "Decide what the sentence expresses: prohibition, advice, certainty or possibility."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«You should have told me earlier»", "Речь о прошлом, действие не выполнено.",
                    "Упрёк выражается «should have + V3».", "Ответ: should."],
             "en": ["“You should have told me earlier”", "The action is in the past and was not done.",
                    "A reproach takes “should have + V3”.", "Answer: should."]},
        ],
        "figure": None,
        "everyday": {"ru": "Надпись «Не курить» — запрет (mustn't), а «можешь не спешить» — отсутствие "
                           "необходимости (needn't).",
                     "en": "“No smoking” forbids; “you needn't hurry” removes the necessity."},
    },
    {
        "id": "lesson-passive", "topic": "passive", "rule": "passive-forms",
        "title": {"ru": "Пассив: когда действие важнее исполнителя",
                    "en": "Passive: when the action matters more than the doer"},
        "summary": {"ru": "Пассив — это «be + V3», а время показывает глагол «be».",
                    "en": "The passive is “be + V3”, and the verb “be” carries the tense."},
        "sections": [
            {"kind": "text",
             "ru": "Проверьте, действует ли подлежащее само: если нет — нужен пассив.",
             "en": "Check whether the subject acts by itself: if it does not, the passive is needed."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«The window ___ by the storm»", "Окно не действует само — пострадавший предмет.",
                    "Прошедшее время, единственное число → was broken."],
             "en": ["“The window ___ by the storm”", "The window does not act — it is affected.",
                    "Past tense, singular → was broken."]},
        ],
        "figure": None,
        "everyday": {"ru": "Табличка «Дом построен в 1897 году» говорит о доме, а не о строителях.",
                     "en": "A plaque saying the house “was built in 1897” speaks about the house, not the builders."},
    },
    {
        "id": "lesson-conditionals", "topic": "conditionals", "rule": "conditionals",
        "title": {"ru": "Условие: реальное, нереальное, невыполненное",
                    "en": "Conditions: real, unreal, unfulfilled"},
        "summary": {"ru": "Тип условия определяется тем, возможно ли оно: это и задаёт формы.",
                    "en": "The type of condition depends on whether it is possible — that decides the forms."},
        "sections": [
            {"kind": "text",
             "ru": "Спросите себя: условие может исполниться (I), не может сейчас (II) или не исполнилось "
                   "в прошлом (III)?",
             "en": "Ask yourself: can the condition come true (I), is it impossible now (II), or did it not "
                   "happen in the past (III)?"},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«If she ___ earlier, she would have caught the train»",
                    "Речь о прошлом и о несбывшемся условии → III тип.",
                    "В условии III типа: had + V3.", "Ответ: had left."],
             "en": ["“If she ___ earlier, she would have caught the train”",
                    "A past condition that did not happen → type III.",
                    "The if-clause takes “had + V3”.", "Answer: had left."]},
        ],
        "figure": None,
        "everyday": {"ru": "«Если завтра дождь, возьму зонт» — план (I тип). «Если бы я был тобой» — "
                           "нереальное условие (II тип).",
                     "en": "“If it rains tomorrow, I will take an umbrella” is a real plan; “if I were you” "
                           "is unreal."},
    },
    {
        "id": "lesson-nonfinite", "topic": "nonfinite", "rule": "gerund-vs-infinitive",
        "title": {"ru": "Герундий или инфинитив", "en": "Gerund or infinitive"},
        "summary": {"ru": "Форму подсказывает предыдущее слово: предлог и часть глаголов требуют герундий.",
                    "en": "The form is decided by the preceding word: prepositions and some verbs take the gerund."},
        "sections": [
            {"kind": "text",
             "ru": "Посмотрите на слово перед пропуском: предлог → герундий; would like / decide → инфинитив.",
             "en": "Look at the word before the gap: a preposition takes the gerund; “would like” or "
                   "“decide” take the infinitive."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«They suggested ___ the meeting»", "С «suggest» инфинитив не употребляется.",
                    "Значит, герундий: postponing."],
             "en": ["“They suggested ___ the meeting”", "After “suggest” the infinitive is impossible.",
                    "The gerund is required: postponing."]},
        ],
        "figure": "formation-chain",
        "everyday": {"ru": "«Люблю плавать» — занятие вообще (герундий), «хочу поплавать сегодня» — "
                           "конкретное намерение (инфинитив).",
                     "en": "“I enjoy swimming” is the activity in general; “I want to swim today” is a "
                           "particular intention."},
    },
    {
        "id": "lesson-articles", "topic": "articles", "rule": "articles-basic",
        "title": {"ru": "Артикль как подсказка «какой именно»", "en": "The article as the word “which one”"},
        "summary": {"ru": "Артикль сообщает собеседнику, знает ли он предмет: любой, известный или неисчисляемый.",
                    "en": "The article tells the listener whether the object is any, known or uncountable."},
        "sections": [
            {"kind": "text",
             "ru": "Проверьте по шагам: предмет исчисляемый? упомянут впервые? известен собеседнику?",
             "en": "Check step by step: is the object countable? is it mentioned for the first time? is it "
                   "known to the listener?"},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«He is ___ honest man»", "Существительное в единственном числе, первое упоминание → a/an.",
                    "Звук в начале слова — гласный (h не читается) → an.", "Ответ: an."],
             "en": ["“He is ___ honest man”", "A singular noun mentioned first takes a/an.",
                    "The first sound is a vowel (“h” is silent) → an.", "Answer: an."]},
        ],
        "figure": "article-tree",
        "everyday": {"ru": "В кафе «нужна вилка» (любая) и «дай ту вилку» (та, что видит собеседник) — "
                           "по-английски это a fork и the fork.",
                     "en": "In a café “I need a fork” means any fork, “the fork” means the one in sight."},
    },
    {
        "id": "lesson-prepositions", "topic": "prepositions", "rule": "prepositions-collocation",
        "title": {"ru": "Предлог учится вместе со словом", "en": "Prepositions are learnt with their word"},
        "summary": {"ru": "Предлог не выбирается по смыслу русского перевода: он закреплён за словом.",
                    "en": "A preposition is not chosen by translating Russian: it is fixed by its word."},
        "sections": [
            {"kind": "text",
             "ru": "Вспомните сочетание целиком: depend on, interested in, good at, responsible for.",
             "en": "Recall the whole collocation: depend on, interested in, good at, responsible for."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«Our success depends ___ careful planning»",
                    "Глагол «depend» в английском требует «on».", "Ответ: on."],
             "en": ["“Our success depends ___ careful planning”",
                    "The verb “depend” takes “on” in English.", "Answer: on."]},
        ],
        "figure": "preposition-map",
        "everyday": {"ru": "Русское «зависеть от» тянет за собой «от», а английское «depend» — «on». "
                           "Переводить предлог отдельно нельзя.",
                     "en": "Russian “зависеть от” uses “от”, while English “depend” takes “on” — prepositions "
                           "are not translated one by one."},
    },
    {
        "id": "lesson-pronouns", "topic": "pronouns_numerals", "rule": "quantifiers",
        "title": {"ru": "Исчисляемое и неисчисляемое", "en": "Countable and uncountable"},
        "summary": {"ru": "Выбор much/many, few/little зависит от того, считаем ли мы предметы.",
                    "en": "Much/many and few/little depend on whether the objects are counted."},
        "sections": [
            {"kind": "text",
             "ru": "Определите, можно ли сказать «одна штука, две штуки»: если да — исчисляемое.",
             "en": "Ask whether you can say “one, two” of the object: if yes, it is countable."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«There are ___ students than last year»", "Студентов считаем → fewer.",
                    "«Less» осталось для неисчисляемого: less time."],
             "en": ["“There are ___ students than last year”", "Students are counted → fewer.",
                    "“Less” is used with uncountable nouns: less time."]},
        ],
        "figure": None,
        "everyday": {"ru": "Деньги — «много» (much money), монеты — «много» (many coins): считаем не смысл, "
                           "а штуки.",
                     "en": "Money is “much”, coins are “many”: what matters is whether the objects are counted."},
    },
    {
        "id": "lesson-noun-adj-adv", "topic": "noun_adj_adv", "rule": "adjective-adverb",
        "title": {"ru": "Прилагательное описывает предмет, наречие — действие",
                    "en": "An adjective describes a thing, an adverb an action"},
        "summary": {"ru": "Смотрите, к какому слову относится определение: к существительному или к глаголу.",
                    "en": "Look at what the word modifies: a noun or a verb."},
        "sections": [
            {"kind": "text",
             "ru": "После «be, look, feel» обычно прилагательное; после глагола действия — наречие с -ly.",
             "en": "After “be, look, feel” an adjective is usual; an action verb takes the “-ly” adverb."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«She speaks English ___»", "«Speaks» — глагол действия → наречие.",
                    "Fluent → fluently."],
             "en": ["“She speaks English ___”", "“Speaks” is an action verb → the adverb is required.",
                    "Fluent → fluently."]},
        ],
        "figure": "formation-chain",
        "everyday": {"ru": "«Внимательный водитель» — про человека, «водит внимательно» — про действие. "
                           "По-английски это разные слова.",
                     "en": "“A careful driver” is about the person, “drives carefully” about the action."},
    },
    {
        "id": "lesson-word-formation", "topic": "word_formation", "rule": "suffixes",
        "title": {"ru": "Словообразование по месту в предложении",
                    "en": "Word formation by position in the sentence"},
        "summary": {"ru": "Сначала часть речи, потом суффикс: место в предложении важнее словаря.",
                    "en": "First the part of speech, then the suffix: the position matters more than the dictionary."},
        "sections": [
            {"kind": "text",
             "ru": "После «his, my, the» обычно существительное; перед существительным — прилагательное; "
                   "после глагола — наречие.",
             "en": "After “his, my, the” a noun is usual; before a noun an adjective; after a verb an adverb."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«Regular exercise improves your ___ (PERFORM)»", "После «your» нужно существительное.",
                    "Perform → performance."],
             "en": ["“Regular exercise improves your ___ (PERFORM)”", "“Your” needs a noun.",
                    "Perform → performance."]},
        ],
        "figure": "formation-chain",
        "everyday": {"ru": "Одно слово собирается по-разному: успех (success), успешный (successful), "
                           "успешно (successfully).",
                     "en": "One word takes different shapes: success, successful, successfully."},
    },
    {
        "id": "lesson-gap-fill", "topic": "gap_fill", "rule": "gap-strategy",
        "title": {"ru": "Что просит пропуск", "en": "What the gap asks for"},
        "summary": {"ru": "Пропуск требует ровно одну единицу: предлог, вспомогательный глагол или союз.",
                    "en": "A gap asks for exactly one item: a preposition, an auxiliary verb or a conjunction."},
        "sections": [
            {"kind": "text",
             "ru": "Прочитайте предложение целиком и переведите: чего не хватает по-английски, а не по-русски.",
             "en": "Read the whole sentence and ask what English misses, not what Russian would need."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«We have known each other ___ childhood»", "Нужна точка отсчёта времени.",
                    "Since + точка, for + отрезок → since."],
             "en": ["“We have known each other ___ childhood”", "A starting point in time is missing.",
                    "Since takes a point, for a period → since."]},
        ],
        "figure": None,
        "everyday": {"ru": "Пазл со стыками: соседние слова сами подсказывают пропущенную деталь.",
                     "en": "Like a puzzle: the neighbouring words suggest the missing piece."},
    },
    {
        "id": "lesson-extra-word", "topic": "extra_word", "rule": "extra-word-strategy",
        "title": {"ru": "Лишнее слово в строке", "en": "The extra word in a line"},
        "summary": {"ru": "В строке ровно одно лишнее слово; чаще всего это предлог, местоимение или артикль.",
                    "en": "Each line has exactly one extra word; usually a preposition, a pronoun or an article."},
        "sections": [
            {"kind": "text",
             "ru": "Уберите подозрительное слово мысленно и проверьте, осталось ли предложение грамматичным.",
             "en": "Remove the suspected word and check whether the sentence stays grammatical."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«He entered into the room without knocking»",
                    "«Enter» — переходный глагол, предлог не нужен.", "Лишнее слово: into."],
             "en": ["“He entered into the room without knocking”",
                    "“Enter” is transitive and takes no preposition.", "The extra word is “into”."]},
        ],
        "figure": "sentence-tree",
        "everyday": {"ru": "Как лишняя деталь после сборки: всё на месте, кроме одной — её и надо назвать.",
                     "en": "Like an unused piece after assembly: everything fits except one — name it."},
    },
    {
        "id": "lesson-communication", "topic": "communication", "rule": "replies",
        "title": {"ru": "Реплики и объявления: читаем буквально",
                    "en": "Replies and notices: read them literally"},
        "summary": {"ru": "В разговоре и в объявлениях есть готовые формулы, и понимать их надо точно.",
                    "en": "Conversation and notices use fixed formulas that must be understood exactly."},
        "sections": [
            {"kind": "text",
             "ru": "Различайте благодарность, извинение и предложение: у каждого своя готовая реакция.",
             "en": "Tell thanks, apologies and offers apart: each has its own fixed reply."},
            {"kind": "steps",
             "title": {"ru": "Разбор", "en": "Worked example"},
             "ru": ["«Last admission is at 17:30; the museum closes at 18:00»",
                    "Вход возможен до последнего допуска, а не до закрытия.", "Ответ: before 17:30."],
             "en": ["“Last admission is at 17:30; the museum closes at 18:00”",
                    "Entry is possible until the last admission, not until closing.", "Answer: before 17:30."]},
        ],
        "figure": None,
        "everyday": {"ru": "Объявление в аэропорту — это правило, а не совет: опоздал на минуту — не пустят.",
                     "en": "An airport notice is a rule, not advice: a minute late means not boarding."},
    },
]


def lessons() -> dict:
    return {lesson["id"]: lesson for lesson in LESSONS}


def lesson_by_id(lesson_id: str) -> dict | None:
    return lessons().get(lesson_id)
