"""Авторский набор с меткой 2021: современная тренировочная структура, не архив ЦТ."""
from variant_support import tasks_for

YEAR = 2021
CHOICES = [
    ('tenses.present_simple', 'The school bus usually ___ at seven on weekdays.', ['arrives', 'arrive', 'is arrive', 'arriving', 'have arrived'], 'Usually обозначает привычку; с bus нужно arrives.', 'Usually marks a habit; the singular bus takes arrives.'),
    ('tenses.present_continuous', 'Please be quiet: the baby ___ right now.', ['is sleeping', 'sleep', 'are sleeping', 'has sleep', 'sleeping'], 'Right now: процесс сейчас, is + sleeping.', 'Right now signals an action in progress: is sleeping.'),
    ('modals.prohibition', 'The sign says NO ENTRY. Visitors ___ enter this room.', ['must not', 'need not', 'do not have to', 'may', 'should'], 'NO ENTRY запрещает вход: must not, а не отсутствие необходимости.', 'NO ENTRY is a prohibition: must not, not a lack of necessity.'),
    ('passive.past_simple', 'The first photographs of this village ___ taken in 1905.', ['were', 'was', 'are being', 'have', 'did'], 'Photographs во множественном числе; в прошлом пассив were taken.', 'Plural photographs and a finished past date require were taken.'),
    ('conditionals.second', 'If I ___ a map, I would show you the route.', ['had', 'have', 'will have', 'would have', 'has'], 'Нереальное условие о настоящем: if + Past Simple.', 'An unreal present condition uses if + Past Simple.'),
    ('nonfinite.gerund_after_verb', 'Marta enjoys ___ short stories for children.', ['writing', 'to write', 'write', 'wrote', 'writes'], 'После enjoy употребляется герундий writing.', 'Enjoy is followed by the gerund writing.'),
    ('articles.indefinite', 'We bought ___ umbrella because it was raining.', ['an', 'a', 'the an', 'some a', 'an the'], 'Umbrella начинается с гласного звука: an umbrella.', 'Umbrella starts with a vowel sound: an umbrella.'),
    ('prepositions.collocation', 'My brother is interested ___ astronomy.', ['in', 'on', 'at', 'to', 'from'], 'Устойчивое сочетание interested in.', 'The fixed collocation is interested in.'),
    ('prepositions.time', 'The concert begins ___ half past six.', ['at', 'in', 'on', 'for', 'since'], 'Точное время требует at.', 'Clock times take at.'),
    ('pronouns.possessive', 'This coat belongs to Leo. It is ___.', ['his', 'him', 'he', 'himself', 'he is'], 'После is нужна самостоятельная притяжательная форма his.', 'A standalone possessive is needed after is: his.'),
    ('pronouns.conjunctions', '___ it was raining, the runners finished the race.', ['Although', 'Because of', 'Despite', 'In spite of', 'During'], 'Перед полным предложением при уступке ставим although.', 'A concessive clause with subject and verb takes although.'),
    ('noun_adj_adv.comparison', 'A train is usually ___ than a bicycle.', ['faster', 'fastest', 'more fast', 'most fast', 'the fast'], 'Than требует сравнительной степени: faster.', 'Than requires the comparative faster.'),
    ('noun_adj_adv.adverb', 'The pianist played the final passage ___.', ['beautifully', 'beautiful', 'beauty', 'beautify', 'beautified'], 'Способ действия played описывает наречие beautifully.', 'The manner of playing is described by the adverb beautifully.'),
    ('tenses.past_perfect', 'By the time we reached the station yesterday, our train ___ already left.', ['had', 'has', 'is', 'does', 'will'], 'Уход поезда предшествует другому прошлому: had left.', 'Leaving precedes another past event: had left.'),
    ('passive.present_simple', 'English ___ taught at our school every weekday.', ['is', 'are', 'does', 'has', 'did'], 'Язык изучают: регулярный пассив is taught.', 'The subject receives a regular action: is taught.'),
    ('nonfinite.infinitive_after_verb', 'Nina decided ___ a summer course.', ['to take', 'taking', 'take', 'taken', 'takes'], 'Decide требует инфинитив с to.', 'Decide takes a to-infinitive.'),
    ('communication.replies', 'A: Thank you for carrying my bag. B: ___', ["You are welcome.", 'Happy birthday!', 'Good night!', 'Get well soon!', 'Congratulations!'], 'Ответ на благодарность: You are welcome.', 'You are welcome is a response to thanks.'),
    ('communication.notice', 'Notice: Return library books by Friday; the building is closed at weekends. When is the deadline?', ['Friday.', 'Saturday.', 'Sunday.', 'Monday.', 'No deadline.'], 'By Friday задаёт крайний срок возврата — пятницу.', 'By Friday sets Friday as the return deadline.'),
]
WRITTEN = [
    ('gap_fill.collocation', 'The success of the trip depends ___ the weather.', 'on', 'Depend on — зависеть от; upon также допустим.', 'Depend on and depend upon are both valid.', {'accepted': ['upon']}),
    ('gap_fill.preposition', 'The children went to school ___ foot.', 'on', 'Устойчивое выражение on foot.', 'The fixed expression is on foot.'),
    ('gap_fill.collocation', 'I am looking forward ___ meeting your family.', 'to', 'В look forward to слово to — предлог перед герундием.', 'Look forward to takes the preposition to before a gerund.'),
    ('gap_fill.auxiliary', '___ you ever visited the National Library?', 'Have', 'Present Perfect образует вопрос с Have перед you.', 'A Present Perfect question with you begins with Have.'),
    ('gap_fill.comparison', 'This suitcase is heavier ___ mine.', 'than', 'После сравнительной степени при сопоставлении нужен than.', 'A comparative followed by the second item takes than.'),
    ('gap_fill.modal', 'You should ___ checked the address before leaving.', 'have', 'Упрёк о прошлом: should have + V3.', 'Past criticism uses should have + past participle.'),
    ('gap_fill.collocation', 'Would you ___ closing the window? Use MIND.', 'mind', 'Вежливая просьба: Would you mind + герундий.', 'A polite request uses Would you mind + gerund.'),
    ('gap_fill.preposition', 'The museum has been open ___ 2010.', 'since', '2010 — начальная точка, поэтому since.', '2010 is a starting point, so use since.'),
    ('extra_word.comparison', 'This road is more narrower than the main street.', 'more', 'Удаляем more: narrower уже сравнительная степень.', 'Delete more: narrower is already comparative.'),
    ('extra_word.subject', 'My sister she works at the hospital.', 'she', 'My sister уже подлежащее; удаляем повтор she.', 'My sister is already the subject; delete the duplicate she.'),
    ('extra_word.preposition', 'They reached to the hotel before midnight.', 'to', 'Reach принимает прямое дополнение: reached the hotel.', 'Reach takes a direct object: reached the hotel.'),
    ('extra_word.preposition', 'We must to finish the report today.', 'to', 'После must нужен инфинитив без to.', 'Must takes the bare infinitive; delete to.'),
    ('extra_word.object', 'She told to me a funny story.', 'to', 'Tell me без предлога; удаляем to.', 'Tell takes me directly; delete to.'),
    ('extra_word.preposition', 'Despite of the rain, the runners completed the race.', 'of', 'Despite употребляется без of.', 'Despite takes no of; delete of.'),
    ('extra_word.preposition', 'He married with his childhood friend.', 'with', 'Marry принимает прямое дополнение; with лишнее.', 'Marry takes a direct object; delete with.'),
    ('extra_word.preposition', 'She can to solve this puzzle quickly.', 'to', 'После can используется начальная форма без to.', 'Can takes a bare infinitive; delete to.'),
    ('extra_word.comparison', 'It was the most cheapest ticket available.', 'most', 'Cheapest уже превосходная степень: most лишнее.', 'Cheapest is already superlative; delete most.'),
    ('extra_word.subject', 'The tourists they waited outside the palace.', 'they', 'Подлежащее The tourists уже есть; they дублирует его.', 'The tourists is already the subject; delete they.'),
    ('word_formation.suffix_noun', 'Her ___ (DECIDE) surprised the whole team.', 'decision', 'После her требуется существительное decision.', 'Her needs the noun decision here.', 'DECIDE'),
    ('word_formation.suffix_adverb', 'Please read these instructions ___ (CAREFUL).', 'carefully', 'Read описывает наречие carefully.', 'The verb read is modified by carefully.', 'CAREFUL'),
    ('word_formation.suffix_person', 'The ___ (PAINT) signed his latest portrait.', 'painter', 'Человек, который рисует картины, — painter.', 'The person who paints portraits is a painter.', 'PAINT'),
    ('word_formation.suffix_adjective', 'The guide gave us some ___ (USE) advice.', 'useful', 'Перед advice нужно прилагательное useful.', 'Before advice, use the adjective useful.', 'USE'),
]


def tasks():
    return tasks_for(YEAR, CHOICES, WRITTEN)
