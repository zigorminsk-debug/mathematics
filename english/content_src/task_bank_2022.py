"""Авторский набор с меткой 2022: современная тренировочная структура, не архив ЦТ."""
from variant_support import tasks_for

YEAR = 2022
CHOICES = [
    ('tenses.present_perfect', 'I ___ never seen such a bright rainbow before.', ['have', 'has', 'am', 'did', 'was'], 'Опыт до настоящего момента: I have seen.', 'Experience up to now uses I have seen.'),
    ('tenses.past_continuous', 'At eight yesterday evening, Dan ___ dinner; he was still in the kitchen at nine.', ['was cooking', 'cooks', 'is cooking', 'has cooked', 'will cook'], 'Процесс в указанный момент прошлого: was cooking.', 'An action in progress at a past time uses was cooking.'),
    ('modals.ability', 'When she was six, Vera ___ already read simple books.', ['could', 'can', 'must', 'may', 'will'], 'Способность в прошлом выражается could.', 'A general ability in the past is expressed by could.'),
    ('passive.present_perfect', 'The broken window ___ already been repaired.', ['has', 'have', 'is', 'does', 'did'], 'Window единственное число; результат ремонта — has been repaired.', 'Singular window and a present result require has been repaired.'),
    ('conditionals.first', 'If it ___ tomorrow, we will cancel the picnic.', ['rains', 'will rain', 'would rain', 'raining', 'rain'], 'В условии I типа о будущем употребляется Present Simple.', 'A first conditional if-clause uses Present Simple for the future.'),
    ('nonfinite.gerund_after_preposition', 'Thank you for ___ me with the luggage.', ['helping', 'help', 'to help', 'helped', 'helps'], 'После предлога for нужен герундий helping.', 'After the preposition for, use the gerund helping.'),
    ('articles.indefinite', 'My aunt works as ___ engineer at a factory.', ['an', 'a', 'the an', 'some a', 'an the'], 'Название профессии в единственном числе; гласный звук: an engineer.', 'A singular profession beginning with a vowel sound takes an.'),
    ('prepositions.time', 'Our final exam is ___ Monday morning.', ['on', 'at', 'in', 'for', 'since'], 'Конкретный день с частью суток требует on.', 'A named day with a part of the day takes on.'),
    ('prepositions.collocation', 'Are you afraid ___ spiders?', ['of', 'from', 'with', 'at', 'to'], 'Устойчивое сочетание afraid of.', 'The fixed collocation is afraid of.'),
    ('pronouns.reflexive', 'Leo, be careful with that knife or you will hurt ___.', ['yourself', 'yours', 'you', 'your', 'yourselves'], 'Обращение к одному человеку: возвратное yourself.', 'Addressing one person requires the reflexive yourself.'),
    ('pronouns.quantifiers', 'There are very ___ chairs in this room; we need more.', ['few', 'little', 'much', 'a little', 'less'], 'Chairs исчисляемое множественное: very few.', 'Plural countable chairs takes very few.'),
    ('noun_adj_adv.comparison', 'This is the ___ building in our town.', ['tallest', 'taller', 'more tall', 'most tall', 'as tall'], 'Сравнение со всеми зданиями: the tallest.', 'Comparison with all buildings requires the tallest.'),
    ('noun_adj_adv.adverb', 'The children listened ___ to the storyteller.', ['attentively', 'attentive', 'attention', 'attend', 'attended'], 'Обстоятельство образа действия — наречие attentively.', 'The manner of listening requires the adverb attentively.'),
    ('tenses.future_perfect', 'By this time tomorrow, we ___ the whole report.', ['will have finished', 'will finishing', 'have finish', 'finishes', 'are finish'], 'К будущему сроку работа будет завершена: Future Perfect.', 'Completion by a future deadline takes Future Perfect.'),
    ('passive.past_simple', 'This bridge ___ built more than a century ago.', ['was', 'were', 'has', 'did', 'does'], 'Bridge единственное число; ago — прошлое: was built.', 'Singular bridge and ago require was built.'),
    ('nonfinite.infinitive_after_verb', 'We hope ___ our cousins during the holidays.', ['to visit', 'visiting', 'visit', 'visited', 'visits'], 'После hope нужен инфинитив to visit.', 'Hope takes the to-infinitive to visit.'),
    ('communication.replies', 'A: I have passed my driving test! B: ___', ['Congratulations!', 'My condolences.', 'Get well soon!', 'Happy New Year!', 'Excuse me.'], 'Успех собеседника отмечают Congratulations!', 'Congratulations is the appropriate response to an achievement.'),
    ('communication.notice', 'Notice: Swimming pool closed on Tuesday for cleaning; open on all other days. Which day should you avoid?', ['Tuesday.', 'Monday.', 'Wednesday.', 'Friday.', 'Sunday.'], 'Вторник — единственный день закрытия.', 'Tuesday is the only day when the pool is closed.'),
]
WRITTEN = [
    ('gap_fill.collocation', 'Who is responsible ___ booking the tickets?', 'for', 'Responsible for — отвечать за.', 'The collocation is responsible for.'),
    ('gap_fill.preposition', 'We arrived ___ the airport two hours early.', 'at', 'Для отдельного пункта airport с arrive нужен at.', 'Arrive at is used for a specific point such as an airport.'),
    ('gap_fill.collocation', 'Do you believe ___ ghosts?', 'in', 'Believe in — верить в существование.', 'Believe in expresses belief in existence.'),
    ('gap_fill.auxiliary', '___ your father work at this factory? Use the Present Simple.', 'Does', 'Present Simple с father образует вопрос с Does.', 'A Present Simple question with singular father uses Does.'),
    ('gap_fill.comparison', 'My room is not as large ___ yours.', 'as', 'Сравнение равенства: as ... as.', 'Equality is expressed with as ... as.'),
    ('gap_fill.modal', 'The lights are on. Someone must ___ at home now.', 'be', 'Текущее предположение: must be.', 'A deduction about a current state uses must be.'),
    ('gap_fill.collocation', 'I would ___ to reserve a table for two. Use LIKE.', 'like', 'Вежливое желание: would like to.', 'A polite wish is expressed by would like to.'),
    ('gap_fill.preposition', 'The meeting lasted ___ three hours.', 'for', 'Длительность выражается for + период.', 'Duration takes for + a period.'),
    ('extra_word.preposition', 'The audience listened to carefully.', 'to', 'Без дополнения здесь нужно listened carefully; удаляем to.', 'There is no object after listen here; delete to: listened carefully.'),
    ('extra_word.comparison', 'My new bicycle is more lighter than the old one.', 'more', 'Lighter уже сравнительная степень; more лишнее.', 'Lighter is already comparative; delete more.'),
    ('extra_word.subject', 'The driver he stopped at the red light.', 'he', 'The driver уже подлежащее: he лишнее.', 'The driver already supplies the subject; delete he.'),
    ('extra_word.preposition', 'We will to send you the details tomorrow.', 'to', 'После will нужен инфинитив без to.', 'Will takes the bare infinitive; delete to.'),
    ('extra_word.object', 'I asked to him a simple question.', 'to', 'Ask him a question без to.', 'Ask him a question takes no to before him.'),
    ('extra_word.preposition', 'Despite of the cold, we went for a walk.', 'of', 'Despite употребляется без of.', 'Despite takes no of; delete of.'),
    ('extra_word.preposition', 'They approached to the entrance quietly.', 'to', 'Approach принимает прямое дополнение.', 'Approach takes a direct object, without to.'),
    ('extra_word.preposition', 'You should to wear a helmet on this ride.', 'to', 'Should требует начальную форму без to.', 'Should takes a bare infinitive; delete to.'),
    ('extra_word.comparison', 'That was the most longest film I had ever seen.', 'most', 'Longest уже превосходная степень.', 'Longest already marks the superlative; delete most.'),
    ('extra_word.subject', 'Our neighbours they grow tomatoes in their garden.', 'they', 'Our neighbours уже подлежащее; they дублирует его.', 'Our neighbours is already the subject; delete they.'),
    ('word_formation.suffix_noun', 'We received an ___ (INVITE) to the wedding.', 'invitation', 'После an нужно существительное invitation.', 'After an, use the noun invitation.', 'INVITE'),
    ('word_formation.suffix_adjective', 'The mountain path was steep and ___ (DANGER).', 'dangerous', 'После was нужен признак пути: dangerous.', 'The path is described by the adjective dangerous.', 'DANGER'),
    ('word_formation.suffix_adverb', 'The man spoke ___ (POLITE) to the receptionist.', 'politely', 'Spoke описывает наречие politely.', 'The manner of speaking takes politely.', 'POLITE'),
    ('word_formation.suffix_person', 'The ___ (DRIVE) waited beside his taxi.', 'driver', 'Человек, управляющий машиной, — driver.', 'The person driving the taxi is the driver.', 'DRIVE'),
]


def tasks():
    return tasks_for(YEAR, CHOICES, WRITTEN)
