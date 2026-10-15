"""Авторский набор с меткой 2024: современная тренировочная структура, не архив ЦТ."""
from variant_support import tasks_for

YEAR = 2024
CHOICES = [
    ('tenses.present_perfect', 'The children ___ just finished their homework.', ['have', 'has', 'are', 'do', 'did'], 'Результат к настоящему с children: have finished.', 'A present result with plural children takes have finished.'),
    ('tenses.future_continuous', 'At this time tomorrow, I ___ over the Atlantic.', ['will be flying', 'will flying', 'have fly', 'flies', 'am fly'], 'Процесс в момент будущего: will be flying.', 'An activity in progress at a future time takes will be flying.'),
    ('modals.deduction', 'That ___ be Oleg at the door: he is in Canada this week.', ['cannot', 'must', 'will', 'should', 'may'], 'Факт пребывания в Канаде исключает предположение: cannot be.', 'Being in Canada rules out the possibility: cannot be.'),
    ('passive.past_perfect', 'When we returned yesterday, the roof ___ already been repaired.', ['had', 'has', 'is', 'was', 'does'], 'Ремонт закончен до прошлого возвращения: had been repaired.', 'The repair precedes a past return: had been repaired.'),
    ('conditionals.wish', 'I wish I ___ speak Japanese, but I cannot.', ['could', 'can', 'will', 'may', 'shall'], 'Нереальное желание о способности сейчас: wish + could.', 'A wish about an unavailable present ability takes could.'),
    ('nonfinite.gerund_after_preposition', 'He left the house without ___ goodbye.', ['saying', 'to say', 'say', 'said', 'says'], 'После without нужен герундий saying.', 'The preposition without takes the gerund saying.'),
    ('articles.definite', 'We stayed near ___ River Thames during our trip.', ['the', 'an', 'a the', 'some a', 'an the'], 'Названия рек употребляются с the.', 'Names of rivers take the.'),
    ('prepositions.place', 'The keys are ___ my pocket.', ['in', 'into', 'at', 'to', 'from'], 'Положение внутри кармана: in, а не направление into.', 'Location inside a pocket takes in, not the movement preposition into.'),
    ('prepositions.phrasal_verb', 'Please turn ___ the light; I cannot see the page.', ['on', 'off', 'away', 'over', 'out'], 'Чтобы стало светло, turn on — включить.', 'To make it brighter, turn on the light.'),
    ('pronouns.reflexive', 'The boys made the wooden boat ___.', ['themselves', 'himself', 'ourselves', 'itself', 'yourself'], 'Boys множественное число: themselves.', 'Plural boys requires themselves.'),
    ('pronouns.quantifiers', 'There is very ___ milk left; we should buy some.', ['little', 'few', 'many', 'a few', 'fewer'], 'Milk неисчисляемое: very little.', 'Uncountable milk takes very little.'),
    ('noun_adj_adv.comparison', 'Her second novel is ___ than her first one.', ['better', 'best', 'more good', 'most good', 'the good'], 'Неправильная сравнительная форма good → better.', 'The irregular comparative of good is better.'),
    ('noun_adj_adv.participle_adjective', 'After the long hike, the walkers felt ___.', ['exhausted', 'exhausting', 'exhaust', 'exhausts', 'exhaustion'], 'Люди испытывают усталость: exhausted, не exhausting.', 'People experiencing tiredness feel exhausted, not exhausting.'),
    ('tenses.present_simple', 'The Earth ___ around the Sun.', ['moves', 'move', 'is move', 'have moved', 'moving'], 'Общий факт в Present Simple с Earth: moves.', 'A general fact with singular Earth takes moves.'),
    ('passive.future_simple', 'The results ___ be announced tomorrow morning.', ['will', 'have', 'are', 'did', 'were'], 'Будущий пассив: will be announced.', 'The future passive is will be announced.'),
    ('nonfinite.infinitive_after_verb', 'I cannot afford ___ a new laptop this month.', ['to buy', 'buying', 'buy', 'bought', 'buys'], 'После afford требуется инфинитив с to.', 'Afford takes a to-infinitive.'),
    ('communication.replies', 'A: Would you like some tea? B: ___', ['Yes, please.', 'Happy birthday!', 'My condolences.', 'Congratulations!', 'Get well soon!'], 'Yes, please — вежливое принятие предложения.', 'Yes, please politely accepts an offer.'),
    ('communication.notice', 'Notice: Keep your receipt. Returns accepted within fourteen days. What should a buyer keep?', ['The receipt.', 'The shopping basket.', 'The price label only.', 'The shop window display.', 'The delivery van.'], 'Keep your receipt прямо требует сохранить чек.', 'Keep your receipt explicitly asks the buyer to retain the receipt.'),
]
WRITTEN = [
    ('gap_fill.collocation', 'This bag belongs ___ my grandmother.', 'to', 'Belong to — принадлежать кому-либо.', 'The fixed collocation is belong to.'),
    ('gap_fill.preposition', 'Many birds fly south ___ winter.', 'in', 'Времена года употребляются с in.', 'Seasons take in.'),
    ('gap_fill.collocation', 'I agree ___ you about the best route.', 'with', 'Согласие с человеком: agree with.', 'Agreement with a person is expressed by agree with.'),
    ('gap_fill.auxiliary', 'Why ___ you crying now?', 'are', 'Процесс сейчас: are you crying.', 'An ongoing action with you requires are you crying.'),
    ('gap_fill.comparison', 'This box is twice as heavy ___ that one.', 'as', 'Конструкция сравнения: twice as ... as.', 'The comparison pattern is twice as ... as.'),
    ('gap_fill.modal', 'They might ___ missed the last bus yesterday.', 'have', 'Предположение о прошлом: might have missed.', 'A possibility concerning the past takes might have missed.'),
    ('gap_fill.collocation', 'Please ___ attention to the safety instructions. Use PAY.', 'pay', 'Устойчивое выражение pay attention to.', 'The fixed expression is pay attention to.'),
    ('gap_fill.preposition', 'I have not seen him ___ last Tuesday.', 'since', 'Last Tuesday — точка отсчёта: since.', 'Last Tuesday is a starting point: since.'),
    ('extra_word.preposition', 'We approached to the old castle at sunset.', 'to', 'Approach принимает прямое дополнение без to.', 'Approach takes a direct object; delete to.'),
    ('extra_word.comparison', 'This sofa is more softer than that chair.', 'more', 'Softer уже сравнительная степень.', 'Softer is already comparative; delete more.'),
    ('extra_word.subject', 'The chef he prepared a special dessert.', 'he', 'The chef уже подлежащее: he лишнее.', 'The chef is already the subject; delete he.'),
    ('extra_word.preposition', 'The visitors must to leave before six.', 'to', 'Must требует начальную форму без to.', 'Must takes a bare infinitive; delete to.'),
    ('extra_word.object', 'Our coach told to us the good news.', 'to', 'Tell us без предлога to.', 'Tell takes us directly; delete to.'),
    ('extra_word.preposition', 'Despite of the traffic, we reached the airport early.', 'of', 'Несмотря на: despite без of.', 'Despite means in spite of but takes no of.'),
    ('extra_word.preposition', 'The speaker emphasised on the main problem.', 'on', 'Emphasise принимает прямое дополнение.', 'Emphasise takes a direct object; delete on.'),
    ('extra_word.preposition', 'We might to stay at the cottage tonight.', 'to', 'Might требует инфинитив без to.', 'Might takes the bare infinitive; delete to.'),
    ('extra_word.comparison', 'This is the most warmest coat in the shop.', 'most', 'Warmest уже превосходная степень.', 'Warmest is already superlative; delete most.'),
    ('extra_word.subject', 'The kitten it fell asleep on the cushion.', 'it', 'The kitten уже подлежащее; it повторяет его.', 'The kitten is already the subject; delete it.'),
    ('word_formation.suffix_noun', 'The project was a great ___ (SUCCEED).', 'success', 'После a great нужно существительное success.', 'After a great, use the noun success.', 'SUCCEED'),
    ('word_formation.suffix_adjective', 'The children were ___ (EXCITE) about the school trip.', 'excited', 'Дети испытывают эмоцию: excited.', 'The children experience the feeling: excited.', 'EXCITE'),
    ('word_formation.suffix_adverb', 'The storm arrived ___ (SUDDEN).', 'suddenly', 'Arrived описывает наречие suddenly.', 'The manner of arrival takes the adverb suddenly.', 'SUDDEN'),
    ('word_formation.suffix_person', 'The male ___ (ACT) played the king in the film.', 'actor', 'Исполнитель роли — actor.', 'A male performer of a role is an actor.', 'ACT'),
]


def tasks():
    return tasks_for(YEAR, CHOICES, WRITTEN)
