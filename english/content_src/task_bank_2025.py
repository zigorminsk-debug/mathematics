"""Авторский набор с меткой 2025: современная тренировочная структура, не архив ЦТ."""
from variant_support import tasks_for

YEAR = 2025
CHOICES = [
    ('tenses.present_perfect', 'Eva ___ already sent the application.', ['has', 'have', 'is', 'does', 'did'], 'Eva единственное число; результат: has sent.', 'Singular Eva and a present result take has sent.'),
    ('tenses.past_continuous', 'While I ___ home yesterday, it suddenly started to snow.', ['was walking', 'am walking', 'have walked', 'walks', 'will walk'], 'Снег прервал процесс в прошлом: was walking.', 'Snow interrupts an ongoing past activity: was walking.'),
    ('modals.request', '___ you please pass me the salt?', ['Could', 'Must to', 'Should to', 'Ought', 'Need to'], 'Вежливая просьба: Could you please ...?', 'A polite request uses Could you please ...?'),
    ('passive.present_simple', 'The classroom ___ cleaned every evening.', ['is', 'are', 'does', 'has', 'did'], 'Регулярный пассив с classroom: is cleaned.', 'A regular passive action with singular classroom takes is cleaned.'),
    ('conditionals.reported_speech', 'Yesterday Tim said that he ___ tired at that moment.', ['was', 'is', 'will be', 'has', 'does'], 'Косвенная речь о состоянии в прошлом: said he was tired.', 'Reported speech describing that past moment uses said he was tired.'),
    ('nonfinite.gerund_after_verb', 'Have you finished ___ the invitations?', ['printing', 'to print', 'print', 'printed', 'prints'], 'Finish требует герундий printing.', 'Finish takes the gerund printing.'),
    ('articles.indefinite', 'It took us ___ hour to get to the lake.', ['an', 'a', 'the an', 'some a', 'an the'], 'В hour начальный h не произносится: an hour.', 'Hour begins with a vowel sound because h is silent: an hour.'),
    ('prepositions.collocation', 'These two bags are similar ___ each other.', ['to', 'at', 'on', 'from', 'into'], 'Устойчивое сочетание similar to.', 'The fixed collocation is similar to.'),
    ('prepositions.time', 'The fireworks start ___ midnight.', ['at', 'on', 'in', 'for', 'since'], 'Midnight употребляется с at.', 'Midnight takes at.'),
    ('pronouns.case', 'The manager invited Olga and ___ to the meeting.', ['us', 'we', 'our', 'ours', 'ourselves'], 'Объект invited: Olga and us.', 'The object of invited is Olga and us.'),
    ('pronouns.conjunctions', 'Take a torch ___ the path will be dark after sunset.', ['because', 'because of', 'despite', 'during', 'in spite of'], 'Причина выражена полным предложением: because.', 'A reason expressed as a full clause takes because.'),
    ('noun_adj_adv.comparison', 'The journey took ___ than we expected.', ['longer', 'longest', 'more long', 'most long', 'as long'], 'Than требует сравнительной формы longer.', 'Than requires the comparative longer.'),
    ('noun_adj_adv.adverb', 'The nurse spoke ___ to the frightened child.', ['gently', 'gentle', 'gentleness', 'gentler', 'gentlest'], 'Способ разговора описывает наречие gently.', 'The manner of speaking is described by gently.'),
    ('tenses.future_perfect', 'By the end of this week, they ___ the new website.', ['will have launched', 'will launching', 'have launch', 'launches', 'are launch'], 'Завершение к будущему сроку: will have launched.', 'Completion by a future deadline takes will have launched.'),
    ('passive.past_simple', 'The stolen bicycles ___ found yesterday.', ['were', 'was', 'are being', 'has', 'did'], 'Bicycles множественное число, yesterday — прошлое: were found.', 'Plural bicycles and yesterday require were found.'),
    ('nonfinite.infinitive_after_verb', 'The receptionist offered ___ us to our room.', ['to show', 'showing', 'show', 'shown', 'shows'], 'Offer требует инфинитив с to.', 'Offer takes a to-infinitive.'),
    ('communication.replies', 'A: I have an important exam tomorrow. B: ___', ['Good luck!', 'Happy birthday!', 'My condolences.', 'Bon appetit!', 'Welcome home!'], 'Перед экзаменом желают удачи: Good luck!', 'Before an exam, Good luck is the appropriate wish.'),
    ('communication.notice', 'Notice: Group tours require advance booking. Individual visitors may buy tickets on arrival. Who must book ahead?', ['Groups.', 'All visitors.', 'Only individual visitors.', 'Nobody.', 'Only children.'], 'Предварительная запись требуется только для групповых экскурсий.', 'Advance booking is required for group tours, not individual visitors.'),
]
WRITTEN = [
    ('gap_fill.collocation', 'The town is famous ___ its ancient castle.', 'for', 'Famous for — известный благодаря чему-либо.', 'The fixed collocation is famous for.'),
    ('gap_fill.preposition', 'There is a bus stop ___ front of the station.', 'in', 'Устойчивое выражение in front of.', 'The fixed expression is in front of.'),
    ('gap_fill.collocation', 'I prefer tea ___ coffee.', 'to', 'Prefer ... to — предпочитать одно другому; over также допустим.', 'Prefer tea to coffee and prefer tea over coffee are both valid.', {'accepted': ['over']}),
    ('gap_fill.auxiliary', '___ she been working here for long?', 'Has', 'Present Perfect Continuous с she: Has she been working?', 'Present Perfect Continuous with she begins with Has.'),
    ('gap_fill.comparison', 'The more you practise, the ___ you become. Use the comparative of GOOD.', 'better', 'В парной сравнительной конструкции good → better.', 'The paired comparative pattern uses the comparative of good: better.'),
    ('gap_fill.modal', 'You ought ___ apologise for that remark.', 'to', 'Ought требует инфинитив с to.', 'Ought takes a to-infinitive.'),
    ('gap_fill.collocation', 'Please ___ a seat while you wait. Use TAKE.', 'take', 'Take a seat — сесть.', 'The fixed expression is take a seat.'),
    ('gap_fill.preposition', 'They have lived next door ___ six months.', 'for', 'Six months — длительность, поэтому for.', 'Six months is a duration, so use for.'),
    ('extra_word.preposition', 'The hikers reached at the summit before noon.', 'at', 'Reach принимает прямое дополнение без at.', 'Reach takes a direct object; delete at.'),
    ('extra_word.comparison', 'The new entrance is more wider than the old one.', 'more', 'Wider уже сравнительная степень.', 'Wider is already comparative; delete more.'),
    ('extra_word.subject', 'My uncle he repairs old clocks.', 'he', 'My uncle уже подлежащее; he повторяет его.', 'My uncle is already the subject; delete he.'),
    ('extra_word.preposition', 'I shall to write to you next week.', 'to', 'После shall удаляем первый to: shall write to you.', 'Delete the first to, after shall: shall write to you.'),
    ('extra_word.object', 'The visitor asked to me the way to the station.', 'to', 'Удаляем to после asked: asked me the way.', 'Delete to after asked: asked me the way.'),
    ('extra_word.preposition', 'Despite of the delay, the show was a success.', 'of', 'Despite не требует of.', 'Despite takes no of; delete of.'),
    ('extra_word.preposition', 'We attended to the concert on Saturday.', 'to', 'В значении посетить мероприятие attend принимает прямое дополнение.', 'When attending an event, attend takes a direct object without to.'),
    ('extra_word.preposition', 'You would to enjoy this exhibition.', 'to', 'Would требует начальную форму без to.', 'Would takes a bare infinitive; delete to.'),
    ('extra_word.comparison', 'That is the most deepest lake in the region.', 'most', 'Deepest уже превосходная степень.', 'Deepest is already superlative; delete most.'),
    ('extra_word.subject', 'The students they organised a charity sale.', 'they', 'The students уже подлежащее: they лишнее.', 'The students already supplies the subject; delete they.'),
    ('word_formation.suffix_noun', 'There is a clear ___ (DIFFER) between the two plans.', 'difference', 'После a clear нужно существительное difference.', 'After a clear, use the noun difference.', 'DIFFER'),
    ('word_formation.suffix_adjective', 'The room was warm and ___ (COMFORT).', 'comfortable', 'Положительный признак комнаты: comfortable.', 'A positive description of the room uses comfortable.', 'COMFORT'),
    ('word_formation.suffix_adverb', 'The guests were greeted ___ (WARM).', 'warmly', 'Greeted описывает наречие warmly.', 'The manner of greeting takes warmly.', 'WARM'),
    ('word_formation.suffix_person', 'The male ___ (SING) performed three songs.', 'singer', 'Человек, который поёт, — singer.', 'A person who sings is a singer.', 'SING'),
]


def tasks():
    return tasks_for(YEAR, CHOICES, WRITTEN)
