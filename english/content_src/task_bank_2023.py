"""Авторский набор с меткой 2023: современная тренировочная структура, не архив ЦТ."""
from variant_support import tasks_for

YEAR = 2023
CHOICES = [
    ('tenses.present_perfect_continuous', 'She ___ studying for three hours and is still at her desk.', ['has been', 'have been', 'is been', 'was been', 'does been'], 'Процесс начался раньше и продолжается: has been studying.', 'An activity continuing from the past takes has been studying.'),
    ('tenses.past_perfect', 'When the guests arrived yesterday, we ___ already prepared dinner.', ['had', 'have', 'are', 'do', 'will'], 'Подготовка предшествует прибытию гостей: had prepared.', 'Preparation precedes a past arrival: had prepared.'),
    ('modals.advice', 'Your tooth hurts. You ___ see a dentist.', ['should', 'should to', 'can to', 'must to', 'ought'], 'Совет: should + начальная форма без to.', 'Advice uses should + bare infinitive.'),
    ('passive.past_continuous', 'When I called the garage yesterday, my car ___ being repaired.', ['was', 'were', 'has', 'does', 'did'], 'Процесс ремонта в прошлом: was being repaired.', 'An ongoing past passive action uses was being repaired.'),
    ('conditionals.third', 'If we had booked earlier, we ___ have paid less.', ['would', 'will', 'can', 'may', 'shall'], 'Нереальное прошлое: would have + V3.', 'An unreal past result takes would have + past participle.'),
    ('nonfinite.gerund_after_verb', 'Please avoid ___ your phone during the lecture.', ['using', 'to use', 'use', 'used', 'uses'], 'Avoid требует герундий using.', 'Avoid takes the gerund using.'),
    ('articles.definite', 'Please close ___ door next to you.', ['the', 'an', 'a the', 'some a', 'an the'], 'Указана конкретная дверь next to you: the door.', 'The specific door next to you takes the.'),
    ('prepositions.collocation', 'Rita is very good ___ solving logic puzzles.', ['at', 'on', 'to', 'from', 'with'], 'Устойчивое сочетание good at.', 'The fixed collocation is good at.'),
    ('prepositions.agent', 'This picture was painted ___ a local artist.', ['by', 'from', 'on', 'at', 'to'], 'Исполнитель в пассиве вводится by.', 'The agent in a passive sentence is introduced by.'),
    ('pronouns.case', 'Anna called Peter and ___ after the meeting.', ['me', 'I', 'my', 'mine', 'myself'], 'После called нужно объектное me.', 'The object of called requires me.'),
    ('pronouns.conjunctions', 'I cannot decide ___ to take the bus or walk.', ['whether', 'that', 'what', 'which', 'whose'], 'Выбор между альтернативами: whether ... or.', 'A choice between alternatives uses whether ... or.'),
    ('noun_adj_adv.comparison', 'Today is ___ than yesterday.', ['colder', 'coldest', 'more cold', 'most cold', 'as cold'], 'Than указывает на сравнительную степень colder.', 'Than signals the comparative colder.'),
    ('noun_adj_adv.participle_adjective', 'The lecture was so ___ that nobody wanted it to end.', ['interesting', 'interested', 'interest', 'interests', 'interestingly'], 'Лекция вызывает интерес: interesting, не interested.', 'The lecture causes interest, so use interesting, not interested.'),
    ('tenses.present_simple', 'Water ___ at 100 degrees Celsius at sea level.', ['boils', 'boil', 'is boil', 'have boiled', 'boiling'], 'Общий факт с неисчисляемым water: boils.', 'A general fact with singular water takes boils.'),
    ('passive.present_simple', 'These parcels ___ delivered every morning.', ['are', 'is', 'have', 'do', 'did'], 'Регулярный пассив с parcels: are delivered.', 'Plural parcels and a regular passive action take are delivered.'),
    ('nonfinite.infinitive_after_verb', 'The team agreed ___ the match until Sunday.', ['to postpone', 'postponing', 'postpone', 'postponed', 'postpones'], 'После agree нужен инфинитив с to.', 'Agree takes a to-infinitive.'),
    ('communication.replies', 'A: I am sorry I broke your cup. B: ___', ["Never mind. It was an old one.", 'Happy anniversary!', 'Bon appetit!', 'Congratulations on your success!', 'Good luck in your exam!'], 'Never mind принимает извинение и успокаивает.', 'Never mind accepts an apology and reassures the speaker.'),
    ('communication.notice', 'Notice: Show your ticket to the driver before boarding. What must passengers do first?', ['Show their ticket.', 'Find a seat.', 'Open a window.', 'Call a friend.', 'Buy a newspaper.'], 'Before boarding: сначала показать билет водителю.', 'Before boarding means showing the ticket comes first.'),
]
WRITTEN = [
    ('gap_fill.collocation', 'The suitcase is full ___ books.', 'of', 'Устойчивое сочетание full of.', 'The fixed collocation is full of.'),
    ('gap_fill.preposition', 'Our train leaves ___ noon.', 'at', 'Noon употребляется с at.', 'Noon takes at.'),
    ('gap_fill.collocation', 'She apologised ___ being late.', 'for', 'Apologise for + герундий — извиняться за действие.', 'Apologise for takes a gerund for the action.'),
    ('gap_fill.auxiliary', '___ you see the match on TV last night?', 'Did', 'Last night: вопрос в Past Simple с Did.', 'Last night takes a Past Simple question with Did.'),
    ('gap_fill.comparison', 'This exercise is easier ___ the previous one.', 'than', 'Сравнительная степень с объектом сравнения: than.', 'The comparative followed by the second item takes than.'),
    ('gap_fill.modal', 'He could ___ won the race, but he fell near the finish.', 'have', 'Несостоявшаяся возможность в прошлом: could have won.', 'An unrealised past possibility uses could have won.'),
    ('gap_fill.collocation', 'Let us ___ a break before the next lesson. Use TAKE.', 'take', 'Устойчивое сочетание take a break.', 'The fixed collocation is take a break.'),
    ('gap_fill.preposition', 'We stayed at the campsite ___ a week.', 'for', 'A week обозначает длительность: for.', 'A week is a duration, so use for.'),
    ('extra_word.preposition', 'She entered in the classroom quietly.', 'in', 'Enter принимает прямое дополнение: entered the classroom.', 'Enter takes a direct object; delete in.'),
    ('extra_word.comparison', 'The second task was more easier than the first.', 'more', 'Easier уже сравнительная степень.', 'Easier is already comparative; delete more.'),
    ('extra_word.subject', 'My parents they travel by train every summer.', 'they', 'My parents уже подлежащее; they лишнее.', 'My parents already supplies the subject; delete they.'),
    ('extra_word.preposition', 'The guide may to arrive a little later.', 'to', 'May требует инфинитив без to.', 'May takes a bare infinitive; delete to.'),
    ('extra_word.object', 'The teacher asked to us several questions.', 'to', 'Ask us questions без предлога перед us.', 'Ask us questions has no preposition before us.'),
    ('extra_word.preposition', 'Despite of the wind, the ferry sailed on time.', 'of', 'Despite употребляется без of.', 'Despite takes no of; delete of.'),
    ('extra_word.preposition', 'We discussed about the new timetable yesterday.', 'about', 'Discuss принимает прямое дополнение.', 'Discuss takes a direct object, without about.'),
    ('extra_word.preposition', 'The dancers could to hear the music backstage.', 'to', 'Could требует начальную форму без to.', 'Could takes a bare infinitive; delete to.'),
    ('extra_word.comparison', 'It was the most smallest room in the hotel.', 'most', 'Smallest уже превосходная степень.', 'Smallest is already superlative; delete most.'),
    ('extra_word.subject', 'The letter it arrived on Thursday.', 'it', 'The letter уже подлежащее; it дублирует его.', 'The letter is already the subject; delete it.'),
    ('word_formation.suffix_noun', 'Thank you for your ___ (ASSIST) with the project.', 'assistance', 'После your нужно существительное assistance.', 'After your, use the noun assistance.', 'ASSIST'),
    ('word_formation.suffix_adjective', 'The puzzle looked ___ (HOPE); nobody could solve it.', 'hopeless', 'По контексту решить нельзя: отрицательный признак hopeless.', 'Nobody could solve it, so the negative adjective is hopeless.', 'HOPE'),
    ('word_formation.suffix_adverb', 'The audience waited ___ (PATIENT) for the curtain to rise.', 'patiently', 'Waited описывает наречие patiently.', 'The manner of waiting takes patiently.', 'PATIENT'),
    ('word_formation.suffix_person', 'The ___ (TEACH) explained the new grammar rule.', 'teacher', 'Человек, который обучает, — teacher.', 'A person who teaches is a teacher.', 'TEACH'),
]


def tasks():
    return tasks_for(YEAR, CHOICES, WRITTEN)
