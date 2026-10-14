"""Rule cards, part 1: phonetics, vocabulary, morphemics, roots, prefixes, suffixes.

Each card: exact formulation (``rule``), applicability/exceptions, an everyday
explanation with its limits, correct and wrong examples (Russian material is
never translated), step-by-step reasoning and normative sources.
"""
from __future__ import annotations

CARDS = {
    "sounds-letters": dict(
        rule=(["Звук мы слышим и произносим, букву видим и пишем; количество букв и звуков в слове может не совпадать.",
               "Буквы е, ё, ю, я обозначают два звука ([й'э], [й'о], [й'у], [й'а]) в начале слова, после гласной и после ъ и ь; "
               "после согласной они обозначают один гласный звук и мягкость предшествующего согласного.",
               "Буквы ъ и ь звуков не обозначают. Непроизносимые согласные (лестница, солнце) не дают звука; "
               "звонкие согласные на конце слова и перед глухими оглушаются, глухие перед звонкими озвончаются."],
              ["We hear and pronounce sounds and see and write letters; their numbers in a word may differ.",
               "е, ё, ю, я stand for two sounds ([j]+vowel) at the start of a word, after a vowel and after ъ/ь; after a "
               "consonant they give one vowel and soften the consonant.",
               "ъ and ь have no sound. Silent consonants (лестница, солнце) give no sound; voiced consonants are devoiced at the "
               "end of a word and before voiceless ones, voiceless ones are voiced before voiced ones."]),
        exceptions=(["Сочетания сч, зч, жч обычно дают один звук [щ'] (счастье, извозчик).",
                     "Буква и после ь тоже обозначает два звука: соловьи [с а л а в' й' и]."],
                    ["сч, зч, жч usually give one sound [щ'] (счастье).", "и after ь also gives two sounds: соловьи."]),
        everyday=(["Буквы — как ноты на бумаге, а звуки — сама музыка: одна нота может звучать долго, а пометка «пауза» "
                   "звука не даёт. Так и ь с ъ: на письме они есть, а в звучании их нет.",
                   "Удобная проверка — медленно произнести слово и записать каждый звук отдельной клеткой. Но это лишь опора: "
                   "в спорных случаях (мягкость перед мягкими согласными) нужна школьная норма транскрипции, а не ощущение."],
                  ["Letters are like notes on paper and sounds are the music: a rest sign is written but not heard — just like "
                   "ь and ъ in a word.",
                   "A useful check is to say the word slowly and write one sound per box. It is only a support: in disputed "
                   "cases follow the school transcription norm, not a feeling."]),
        correct=["ёлка — 4 буквы, 5 звуков [й'олка]", "день — 4 буквы, 3 звука [д'эн']", "лестница — 8 букв, 7 звуков"],
        wrong=[("счастье — 7 звуков", "счастье — 6 звуков: сч = [щ']"), ("ель — 2 звука", "ель — 3 звука [й'эл']")],
        steps=(["Запишите слово и пронумеруйте буквы.", "Отметьте ъ, ь (без звука) и непроизносимые согласные.",
                "Найдите е, ё, ю, я в начале слова, после гласных и после ъ, ь — каждая даст два звука.",
                "Сравните число букв и звуков."],
               ["Write the word and number the letters.", "Mark ъ, ь (silent) and silent consonants.",
                "Find е, ё, ю, я initially, after vowels and after ъ/ь — each gives two sounds.", "Compare the counts."]),
        sources=["grammar1980", "spec2026"],
    ),
    "stress": dict(
        rule=(["Ударение в русском языке разноместное и подвижное: оно может падать на любой слог и переходить в разных "
               "формах слова (при́нял — приняла́). Нормативное ударение проверяется по орфоэпическому словарю.",
               "Часто ошибаются в глаголах на -ить (звони́т, включи́т, сверли́т), в кратких формах женского рода прошедшего "
               "времени (взяла́, поняла́, начала́) и в ряде существительных (катало́г, кварта́л, щаве́ль)."],
              ["Russian stress is free and mobile: it can fall on any syllable and move between forms (при́нял — приняла́). "
               "The normative stress is checked in an orthoepic dictionary.",
               "Typical errors: verbs in -ить (звони́т, включи́т), feminine past forms (взяла́, поняла́) and nouns such as "
               "катало́г, кварта́л, щаве́ль."]),
        exceptions=(["Есть слова с двумя допустимыми вариантами ударения (творо́г и тво́рог); такие слова в тренажёре не "
                     "проверяются, чтобы не делать допустимый вариант ошибкой."],
                    ["Some words have two accepted stresses (творо́г/тво́рог); the tutor does not test them."]),
        everyday=(["Ударение похоже на правильный пин-код: цифры те же, но если нажать их не в том порядке, «дверь» не "
                   "откроется — слово прозвучит ненормативно, хотя его поймут.",
                   "Запоминать удобно связками-подсказками («звони́т — говори́т»), но подсказка не заменяет словарь: "
                   "похожие слова могут иметь разное ударение, поэтому каждое слово сверяйте отдельно."],
                  ["Stress is like a PIN: the same digits in the wrong order do not open the door — the word is understood "
                   "but sounds non-standard.",
                   "Memory hooks («звони́т — говори́т») help, but they do not replace the dictionary: similar words may differ."]),
        correct=["звони́т", "катало́г", "краси́вее", "ку́хонный", "взяла́", "при́нял"],
        wrong=[("зво́нит", "звони́т"), ("ката́лог", "катало́г"), ("красиве́е", "краси́вее")],
        steps=(["Произнесите слово в той форме, которая дана.", "Сверьте с орфоэпическим минимумом/словарём.",
                "Посчитайте гласные до ударной — это номер ударного слога."],
               ["Say the word in the given form.", "Check it against the orthoepic list/dictionary.",
                "Count the vowels up to the stressed one — that is the syllable number."]),
        sources=["orthoepy"],
    ),
    "word-meaning": dict(
        rule=(["Лексическое значение — то, что слово обозначает. Прямое значение прямо называет предмет или признак "
               "(золотое кольцо), переносное возникает по сходству или смежности (золотые руки — умелые).",
               "Многозначное слово имеет несколько связанных значений; однозначное — одно."],
              ["The lexical meaning is what a word denotes. A literal meaning names the object directly (золотое кольцо), "
               "a figurative one arises by similarity (золотые руки — skilful).",
               "A polysemous word has several related meanings; a monosemous word has one."]),
        exceptions=(["Омонимы (лук — растение и оружие) — разные слова, а не значения одного слова."],
                    ["Homonyms (лук — plant/weapon) are different words, not meanings of one word."]),
        everyday=(["«Тёплый шарф» греет по-настоящему, а «тёплый приём» — нет: температура тут ни при чём, важна похожая "
                   "приятность. Переносное значение как бы одалживает признак у прямого.",
                   "Проверка вопросом «это буквально так?» помогает, но не всегда: у многих слов переносное значение стало "
                   "привычным (ножка стола), поэтому смотрите толкование в словаре."],
                  ["A warm scarf really warms, a «warm welcome» does not: the shared feature is pleasantness. The figurative "
                   "meaning borrows a feature from the literal one.",
                   "Asking «is it literally so?» helps, but many figurative meanings are fixed (ножка стола), so use the dictionary."]),
        correct=["железный гвоздь — прямое", "железная воля — переносное", "глубокие знания — переносное"],
        wrong=[("острый нож — переносное", "острый нож — прямое значение")],
        steps=(["Определите, о каком предмете идёт речь.", "Спросите: признак реальный (из железа, горячий) или перенесён по "
                "сходству?", "Сверьтесь с толковым словарём при сомнении."],
               ["Find the object.", "Ask: is the feature real or transferred by similarity?", "Check the dictionary if unsure."]),
        sources=["ozhegov"],
    ),
    "synonyms-antonyms": dict(
        rule=(["Синонимы — слова одной части речи, близкие или тождественные по значению (храбрый — смелый).",
               "Антонимы — слова одной части речи с противоположными значениями (глубокий — мелкий)."],
              ["Synonyms are words of the same part of speech with close meanings (храбрый — смелый).",
               "Antonyms are words of the same part of speech with opposite meanings (глубокий — мелкий)."]),
        exceptions=(["Контекстные синонимы и антонимы сближаются только в данном тексте; в задании «выпишите» берите слово "
                     "точно в той форме, в которой оно стоит в предложении."],
                    ["Contextual synonyms/antonyms exist only in a given text; copy the word in its form."]),
        everyday=(["Синонимы — как разные ключи от одной двери: открывают одно и то же, но к разным «замкам» стиля подходят "
                   "по-разному. Антонимы — две стороны одной монеты: без одной нет другой.",
                   "Подставьте найденное слово вместо данного: смысл должен сохраниться (синоним) или смениться на обратный "
                   "(антоним). Если меняется и часть речи, это уже не синоним."],
                  ["Synonyms are different keys to one door; antonyms are two sides of one coin.",
                   "Substitute the word: the meaning must stay (synonym) or reverse (antonym); the part of speech must stay too."]),
        correct=["пасмурный — ясный", "старый — молодой", "тропа — дорожка"],
        wrong=[("тихо — громкий", "тихо — громко (та же часть речи)")],
        steps=(["Определите часть речи данного слова.", "Найдите в предложении слово той же части речи с близким или "
                "противоположным значением.", "Выпишите его в той форме, в которой оно употреблено."],
               ["Find the part of speech.", "Find a word of the same part of speech with a close/opposite meaning.",
                "Copy it in the form used."]),
        sources=["ozhegov"],
    ),
    "paronyms": dict(
        rule=(["Паронимы — однокоренные слова, близкие по звучанию, но различающиеся значением и сочетаемостью: "
               "одеть (кого?) — надеть (что?), предоставить (дать) — представить (показать), абонемент — абонент.",
               "Подмена паронима — лексическая ошибка, даже если предложение понятно."],
              ["Paronyms are cognates that sound alike but differ in meaning and collocation: одеть (someone) — надеть "
               "(something), предоставить — представить, абонемент — абонент.",
               "Using the wrong paronym is a lexical error even if the sentence is understood."]),
        exceptions=(["Паронимы не равны синонимам: их нельзя свободно заменять друг другом."],
                    ["Paronyms are not synonyms and are not interchangeable."]),
        everyday=(["Одеть ребёнка, но надеть пальто: мы одеваем кого-то и надеваем что-то. Это как разница между «отправить "
                   "письмо» и «получить письмо» — слова похожи, а действия разные.",
                   "Подсказка «одеть Надежду, надеть одежду» помогает запомнить пару, но для других паронимов нужна своя "
                   "проверка по словарю паронимов: универсальной рифмы нет."],
                  ["We dress (одеть) someone and put on (надеть) something — similar words, different actions.",
                   "The mnemonic «одеть Надежду, надеть одежду» works for one pair only; others need a paronym dictionary."]),
        correct=["надеть шапку", "предоставить отпуск", "купить абонемент", "дипломант конкурса"],
        wrong=[("одеть шапку", "надеть шапку"), ("представить отпуск", "предоставить отпуск"), ("купить абонент", "купить абонемент")],
        steps=(["Найдите выделенное слово и его пару-пароним.", "Сравните значения: что именно хотел сказать автор?",
                "Замените слово паронимом в той же форме."],
               ["Find the word and its paronym.", "Compare meanings.", "Replace it with the paronym in the same form."]),
        sources=["paronyms", "ozhegov"],
    ),
    "phraseology": dict(
        rule=(["Фразеологизм — устойчивое сочетание слов с целостным значением, которое не выводится из значений его "
               "частей: сломя голову (очень быстро), бить баклуши (бездельничать).",
               "Слова фразеологизма не заменяются синонимами и не переставляются; в предложении он — один член предложения."],
              ["A set phrase has one unified meaning not derived from its parts: сломя голову (very fast), бить баклуши (idle).",
               "Its words are not replaced or reordered; in a sentence it is one sentence part."]),
        exceptions=(["Глагольные фразеологизмы изменяются по формам глагола (бил баклуши), поэтому выписывайте их в той форме, "
                     "в которой они даны."],
                    ["Verbal idioms change with the verb (бил баклуши); copy the form used."]),
        everyday=(["«Рукой подать» — не о вытянутой руке, а о близком расстоянии: фразеологизм работает как одна «кнопка», "
                   "которую нельзя разобрать на детали без потери смысла.",
                   "Если в обороте заменить слово (сломя шею вместо сломя голову), получится речевая ошибка. Проверка "
                   "по смыслу полезна, но значение фразеологизма надо знать или посмотреть в словаре."],
                  ["«Рукой подать» means «very close», not an outstretched arm: an idiom is one button that cannot be taken apart.",
                   "Replacing a word (сломя шею instead of сломя голову) produces a speech error. Checking by sense helps, but the meaning of an idiom must be known or looked up in a dictionary."]),
        correct=["как две капли воды", "душа в душу", "ни свет ни заря"],
        wrong=[("сломя шею", "сломя голову"), ("бежать сломя голову (если просят выписать только фразеологизм)", "сломя голову")],
        steps=(["Найдите сочетание, значение которого нельзя сложить из значений слов.", "Сверьте его со значением в задании.",
                "Выпишите все слова оборота и только их."],
               ["Find the phrase whose meaning is not the sum of its words.", "Compare it with the given meaning.",
                "Copy all its words and nothing else."]),
        sources=["phraseology"],
    ),
    "pleonasm": dict(
        rule=(["Плеоназм — употребление лишнего слова, значение которого уже выражено другим словом: свободная вакансия "
               "(вакансия — свободная должность), памятный сувенир, в мае месяце, подниматься вверх.",
               "Нарушение лексической сочетаемости — соединение слов, которые не сочетаются по смыслу или традиции."],
              ["A pleonasm adds a word whose meaning is already expressed: свободная вакансия, памятный сувенир, в мае месяце.",
               "A collocation error joins words that do not combine by meaning or usage."]),
        exceptions=(["Закреплённые сочетания (масло масляное как шутка, устойчивые термины) оцениваются по словарю, а не по "
                     "формальному «повтору»."],
                    ["Fixed expressions are judged by the dictionary, not by a formal repetition."]),
        everyday=(["«Памятный сувенир» — как «мокрая вода»: сувенир и есть вещь на память. Лишнее слово не добавляет смысла, "
                   "а только утяжеляет фразу.",
                   "Проверка удалением полезна: убрали слово — смысл не изменился, значит, оно было лишним. Но так проверяют "
                   "только смысл; стилистику и устойчивость сочетания проверяют по словарю."],
                  ["«A memorable souvenir» is like «wet water»: a souvenir already means a keepsake.",
                   "Deleting the word is a good test of meaning; style and fixed use are checked in the dictionary."]),
        correct=["вакансия инженера", "сувенир", "в мае", "подниматься"],
        wrong=[("свободная вакансия", "вакансия"), ("впервые познакомились", "познакомились"), ("вернулся назад", "вернулся")],
        steps=(["Определите значение каждого слова.", "Найдите слово, смысл которого уже содержится в соседнем.",
                "Проверьте, сохранится ли смысл без него."],
               ["Find each word's meaning.", "Find the word already contained in its neighbour.", "Check the meaning without it."]),
        sources=["ozhegov", "rosenthal"],
    ),
    "morphemes": dict(
        rule=(["Морфемы — значимые части слова: корень, приставка, суффикс, постфикс, соединительная гласная, окончание.",
               "Окончание — изменяемая часть, образующая формы слова; нулевое окончание не выражено звуком (стол∅, ночь∅, "
               "читал∅). У неизменяемых слов (наречий, деепричастий, несклоняемых существительных) окончания нет.",
               "Однокоренные слова имеют общий корень и общее лексическое значение; созвучный отрезок с другим значением — "
               "омонимичный корень (вод-а и вод-ить)."],
              ["Morphemes are meaningful parts: root, prefix, suffix, postfix, linking vowel, ending.",
               "The ending forms the word's forms; a zero ending is not pronounced (стол∅). Invariable words have no ending.",
               "Cognates share a root AND its meaning; a look-alike segment with another meaning is a homonymous root."]),
        exceptions=(["Формы одного слова (вода — воды) не являются однокоренными словами — это одно слово.",
                     "Пальто, кофе, метро — несклоняемые: окончания у них нет, это не нулевое окончание."],
                    ["Forms of one word are not cognates.", "Indeclinable nouns have no ending at all."]),
        everyday=(["Слово — как конструктор: корень — основная деталь, приставки и суффиксы — насадки, окончание — "
                   "сменная «шестерёнка», которая меняет форму. Нулевое окончание — пустое гнездо, в которое при изменении "
                   "встаёт деталь (стол — стола).",
                   "Совпадение букв обманчиво: «водитель» и «вода» похожи, но водитель не связан с водой. Сначала ищите "
                   "общее значение, а не общие буквы."],
                  ["A word is a construction set; the ending is a replaceable gear, and a zero ending is an empty socket.",
                   "Matching letters mislead: водитель has nothing to do with вода; look for a shared meaning first."]),
        correct=["конь∅ (коня)", "читал∅ (читала)", "водный — вода (однокоренные)"],
        wrong=[("пальто — нулевое окончание", "пальто — окончания нет"), ("водитель — однокоренное к «вода»", "корень от «водить»")],
        steps=(["Измените слово: что меняется, то окончание.", "Если слово не изменяется — окончания нет.",
                "Для однокоренных подберите толкование: есть ли общее значение корня?"],
               ["Change the word: the changing part is the ending.", "An invariable word has no ending.",
                "For cognates check that the root meaning is shared."]),
        sources=["grammar1980", "tikhonov"],
    ),
    "word-formation": dict(
        rule=(["Способ образования определяется по производящему слову и тому, что к нему добавлено: приставочный "
               "(читать → перечитать), суффиксальный (лес → лесник), приставочно-суффиксальный (окно → подоконник), "
               "постфиксальный (мыть → мыться), приставочно-постфиксальный (бежать → разбежаться), сложение "
               "(пар + ход → пароход), сложение в сочетании с суффиксацией (железная дорога → железнодорожный)."],
              ["The way of formation is found from the source word and what was added: prefixal, suffixal, prefix+suffix, "
               "postfixal, prefix+postfix, compounding, compounding + suffix."]),
        exceptions=(["Если промежуточного слова не существует (разбежать), значит приставка и постфикс присоединились "
                     "одновременно — приставочно-постфиксальный способ."],
                    ["If the intermediate word does not exist (разбежать), prefix and postfix were added together."]),
        everyday=(["Производящее слово — как исходный рецепт, а способ образования — что добавили к блюду: только соль "
                   "(суффикс), только перец (приставку) или и то и другое сразу.",
                   "Проверяйте промежуточные «рецепты»: если слова «подокно» нет, значит под- и -ник добавлены одновременно. "
                   "В спорных случаях решает словообразовательный словарь, а не догадка."],
                  ["The source word is like the base recipe, and the way of formation tells what was added to the dish: only salt (a suffix), only pepper (a prefix) or both at once.",
                   "Check intermediate words: if «подокно» does not exist, both affixes were added together."]),
        correct=["перечитать ← читать (приставочный)", "подоконник ← окно (приставочно-суффиксальный)", "пароход ← пар, ход (сложение)"],
        wrong=[("подоконник — суффиксальный от «подокно»", "слова «подокно» нет: приставочно-суффиксальный")],
        steps=(["Подберите самое близкое производящее слово.", "Выделите, что к нему добавлено.",
                "Проверьте, существует ли промежуточное слово."],
               ["Find the closest source word.", "Mark what was added.", "Check whether the intermediate word exists."]),
        sources=["tikhonov", "spec2026"],
    ),
    "root-vowels": dict(
        rule=(["Безударную гласную в корне проверяют ударением: подбирают однокоренное слово или форму, где этот слог "
               "ударный (з..лотой — зо́лото).",
               "Проверочное слово должно иметь тот же корень и то же значение: полоскать бельё (поло́щет), но поласкать "
               "котёнка (ла́ска).",
               "Непроверяемые гласные запоминают по орфографическому словарю (вокзал, корабль, тетрадь)."],
              ["An unstressed root vowel is checked by stress in a cognate (з..лотой — зо́лото).",
               "The check word must keep the same root and meaning: полоскать бельё (поло́щет) but поласкать котёнка (ла́ска).",
               "Uncheckable vowels are learnt from the dictionary (вокзал, корабль, тетрадь)."]),
        exceptions=(["Корни с чередованием (-лаг-/-лож-, -бер-/-бир- и др.) ударением не проверяются — для них свои правила."],
                    ["Alternating roots are not checked by stress — they follow their own rules."]),
        everyday=(["Проверочное слово — как фонарик: в безударной позиции гласная «в тени», а под ударением её видно ясно.",
                   "Но фонарик надо направить на тот же предмет: «посидеть» проверяем словом «сидя», а «поседеть» — словом "
                   "«сед». Похожее слово с другим значением даст неверный ответ."],
                  ["The check word is a torch: an unstressed vowel is in the shadow, a stressed one is clear.",
                   "But the torch must point at the same object: посидеть is checked by сидя, while поседеть is checked by сед. A similar word with another meaning gives the wrong letter."]),
        correct=["золотой (зо́лото)", "посидеть (си́дя)", "поседеть (се́д)", "вокзал (словарное)"],
        wrong=[("сидеть → седеть по «сед»", "посидеть — си́дя"), ("кортофель", "картофель")],
        steps=(["Найдите корень.", "Убедитесь, что это не корень с чередованием.",
                "Подберите однокоренное слово с тем же значением, где гласная под ударением.",
                "Если проверить нельзя — словарное слово."],
               ["Find the root.", "Make sure it is not an alternating root.", "Find a cognate with the same meaning where the "
                "vowel is stressed.", "If impossible — a dictionary word."]),
        sources=["lopatin", "rus-orfo"],
    ),
    "root-alt-oa": dict(
        rule=(["-лаг-/-лож-: а перед г, о перед ж (предлагать — предложение).",
               "-раст-/-ращ-/-рос-: а перед ст и щ, о перед с (растение, выращенный — заросли).",
               "-кас-/-кос-: а, если за корнем следует суффикс -а- (касаться — коснуться).",
               "-скак-/-скоч-: а перед к, о перед ч (скакать — выскочить).",
               "-гар-/-гор-, -клан-/-клон-, -твар-/-твор-: без ударения о; -зар-/-зор-: без ударения а.",
               "-плав-: а; -мак-/-мок-: «погружать в жидкость» — а, «пропускать жидкость» — о; -равн-/-ровн-: «равный» — а, "
               "«ровный, гладкий» — о."],
              ["-лаг-/-лож-: а before г, о before ж.", "-раст-/-ращ-/-рос-: а before ст/щ, о before с.",
               "-кас-/-кос-: а when the suffix -а- follows.", "-скак-/-скоч-: а before к, о before ч.",
               "-гар-/-гор-, -клан-/-клон-, -твар-/-твор-: unstressed о; -зар-/-зор-: unstressed а.",
               "-плав-: а; -мак-/-мок- and -равн-/-ровн- depend on the meaning."]),
        exceptions=(["росток, ростовщик (о перед ст), отрасль (а перед с); скачок, скачу; выгарки, изгарь; зоревать, "
                     "зорянка; утварь; пловец, пловчиха, плывуны; равнина; ровесник, ровня, поровну."],
                    ["росток, ростовщик, отрасль; скачок, скачу; зоревать; утварь; пловец; равнина; ровесник, поровну."]),
        everyday=(["Чередующийся корень похож на светофор: цвет (гласная) зависит не от того, как вы слышите, а от сигнала "
                   "рядом — согласной после корня, суффикса -а- или значения.",
                   "Ударение здесь не помогает: «предложить» нельзя проверить словом «предло́г» — это другой корень с другим "
                   "значением. Поэтому сначала узнайте корень по списку, затем ищите его «сигнал»."],
                  ["An alternating root is like a traffic light: the vowel depends on the signal next to it, not on hearing.",
                   "Stress does not help here; identify the root by the list first, then its signal."]),
        correct=["предлагать", "предложение", "выращенный", "заросли", "прикасаться", "отрасль"],
        wrong=[("предлогать", "предлагать"), ("выростить", "вырастить"), ("отросль", "отрасль")],
        steps=(["Узнайте корень по списку чередующихся.", "Определите, от чего зависит гласная: согласная, суффикс -а-, "
                "ударение или значение.", "Проверьте исключения."],
               ["Identify the root in the list.", "Find what decides the vowel.", "Check the exceptions."]),
        sources=["lopatin", "rosenthal"],
    ),
    "root-alt-ei": dict(
        rule=(["В корнях -бер-/-бир-, -дер-/-дир-, -мер-/-мир-, -пер-/-пир-, -тер-/-тир-, -блест-/-блист-, -жег-/-жиг-, "
               "-стел-/-стил-, -чет-/-чит- пишется и, если после корня стоит суффикс -а-; иначе — е.",
               "Пример: собирать — соберу, замирать — замереть, зажигать — зажечь."],
              ["Roots -бер-/-бир-, …, -чет-/-чит- take и when the suffix -а- follows the root, otherwise е.",
               "Example: собирать — соберу, замирать — замереть."]),
        exceptions=(["сочетать, сочетание, чета — пишется е, хотя после корня есть -а-."],
                    ["сочетать, сочетание, чета keep е."]),
        everyday=(["Суффикс -а- работает как «пропуск»: есть он сразу после корня — в корне пишется и (собирать), нет — е "
                   "(соберу). Смотрите на соседа справа, а не на ударение.",
                   "Ловушка — похожие корни с другим значением: «вычитание» (-чит-) и «почитать» (от «читать») относятся к "
                   "разным корням. Проверьте значение, прежде чем применять правило."],
                  ["The suffix -а- is a pass: present right after the root → и, absent → е.",
                   "Beware of look-alike roots with other meanings: вычитание (-чит-) and почитать (from читать) belong to different roots. Check the meaning before applying the rule."]),
        correct=["собирать", "соберу", "блистать", "блестеть", "сочетание"],
        wrong=[("соберать", "собирать"), ("зажичь", "зажечь"), ("сочитание", "сочетание")],
        steps=(["Убедитесь, что корень из списка.", "Посмотрите на букву после корня: суффикс -а-?",
                "Есть -а- — пишите и, нет — е; проверьте исключения."],
               ["Make sure the root is in the list.", "Look for the suffix -а- after it.", "-а- → и, otherwise е; check exceptions."]),
        sources=["lopatin"],
    ),
    "consonants": dict(
        rule=(["Сомнительную согласную в корне проверяют формой, где после неё стоит гласная или сонорный (ло́дка — ло́дочка).",
               "Непроизносимую согласную пишут, если в проверочном слове она произносится (праздник — праздновать, "
               "солнце — солнышко), и не пишут, если её нет (опасный — опасен, вкусный — вкус)."],
              ["A doubtful consonant is checked by a form where a vowel follows it.",
               "A silent consonant is written if it is heard in a check word (праздник — праздновать) and not written "
               "otherwise (опасный — опасен)."]),
        exceptions=(["лестница, чувство, здравствуйте — написание непроизносимой согласной запоминают (словарные слова)."],
                    ["лестница, чувство, здравствуйте are dictionary words."]),
        everyday=(["Непроизносимая согласная — как тихий сосед: в одном слове его не слышно, но в «родственном» слове он "
                   "говорит в полный голос (праздник — праздновать).",
                   "Если «родственника», где буква звучит, нет, не добавляйте её по аналогии: «опасный» пишется без т, хотя "
                   "рядом есть «честный». Аналогия по звучанию правилом не является."],
                  ["A silent consonant is a quiet neighbour that speaks up in a related word.",
                   "Do not add it by analogy: «опасный» has no т even though «честный» does."]),
        correct=["праздник", "солнце", "опасный", "вкусный", "лестница"],
        wrong=[("празник", "праздник"), ("опастный", "опасный"), ("вкустный", "вкусный")],
        steps=(["Найдите сочетание согласных в корне.", "Подберите однокоренное слово, где после согласной гласная.",
                "Слышна — пишите, нет — не пишите."],
               ["Find the consonant cluster.", "Find a cognate with a vowel after it.", "Heard → write it, otherwise not."]),
        sources=["lopatin", "rus-orfo"],
    ),
    "double-consonants": dict(
        rule=(["Двойные согласные пишутся: на стыке приставки и корня (рассказ, поддержка), корня и суффикса "
               "(длинный — длин-н-ый), в части русских корней (жужжать, вожжи) и во многих заимствованных словах "
               "(коллектив, аккорд, аппетит) — по словарю."],
              ["Double consonants appear at prefix–root junctions (рассказ), root–suffix junctions, in some native roots "
               "(жужжать) and in many borrowed words (коллектив) — by the dictionary."]),
        exceptions=(["В ряде заимствований пишется одна согласная: карьера, дипломант, коридор, гимнастика, тротуар, "
                     "параллель (одна р)."],
                    ["Some loanwords have a single consonant: карьера, коридор, тротуар."]),
        everyday=(["Удвоение на стыке частей слова — как стык двух рельсов: «рас» + «сказ» встречаются, и обе с сохраняются.",
                   "В заимствованиях логика другая: удвоение пришло из языка-источника и не слышно в речи, поэтому опора — "
                   "орфографический словарь, а не произношение."],
                  ["Doubling at the junction of two parts of a word is like two rails meeting: рас + сказ come together and both letters с stay.",
                   "In loanwords the doubling comes from the source language — check the dictionary."]),
        correct=["коллектив", "рассказ", "поддержка", "карьера", "тротуар"],
        wrong=[("колектив", "коллектив"), ("расказ", "рассказ"), ("троттуар", "тротуар")],
        steps=(["Разберите слово по составу: есть ли стык приставки и корня?", "Если слово заимствованное — сверьтесь "
                "со словарём.", "Помните частые исключения с одной согласной."],
               ["Parse the word: is there a junction?", "For loanwords use the dictionary.", "Remember single-consonant exceptions."]),
        sources=["rus-orfo", "opencorpora"],
    ),
    "prefix-z-s": dict(
        rule=(["В приставках без-/бес-, воз-/вос-, вз-/вс-, из-/ис-, низ-/нис-, раз-/рас-, роз-/рос-, через-/черес- пишется з "
               "перед звонкой согласной и гласной, с — перед глухой (безграничный — бесшумный).",
               "Под ударением роз-/рос-, без ударения раз-/рас- (ро́спись — расписание)."],
              ["Prefixes без-/бес- etc.: з before voiced consonants and vowels, с before voiceless ones.",
               "Stressed роз-/рос-, unstressed раз-/рас-."]),
        exceptions=(["Остальные приставки (в-, над-, под-, от-, с-) пишутся всегда одинаково: сделать, отбить."],
                    ["Other prefixes never change: сделать, отбить."]),
        everyday=(["Приставка на з/с «подстраивается» под следующий звук, как человек, который говорит тише в библиотеке: "
                   "перед глухим — с, перед звонким и гласной — з.",
                   "Правило касается только перечисленных приставок: «сделать» не превращается в «зделать», хотя звук [з] "
                   "слышен. Сначала узнайте приставку."],
                  ["The prefix adapts to the next sound like a person lowering their voice.",
                   "The rule covers only the listed prefixes: «сделать» never turns into «зделать», although the sound [з] is heard. Identify the prefix first."]),
        correct=["безграничный", "бесшумный", "роспись", "расписание", "чересчур"],
        wrong=[("безшумный", "бесшумный"), ("росписание", "расписание")],
        steps=(["Убедитесь, что приставка из списка.", "Посмотрите на первую букву корня: звонкая/гласная или глухая?",
                "Учитывайте ударение для роз-/раз-."],
               ["Check the prefix is in the list.", "Look at the next letter: voiced/vowel or voiceless?", "Mind the stress."]),
        sources=["lopatin"],
    ),
    "prefix-pre-pri": dict(
        rule=(["ПРЕ- пишется в значении «очень» (прекрасный) и «пере-» (преодолеть, прервать).",
               "ПРИ- пишется в значениях приближения, присоединения, близости, неполноты действия, доведения до конца "
               "(приехать, пристроить, прибрежный, приоткрыть).",
               "Различают по значению: пребывать — прибывать, преемник — приёмник, презирать — призреть, предать — придать."],
              ["ПРЕ- means «very» or «пере-».", "ПРИ- means approach, joining, nearness, an incomplete action.",
               "Distinguish by meaning: пребывать — прибывать, преемник — приёмник."]),
        exceptions=(["В словах с неясным значением приставки написание по словарю: привередливый, пренебрегать, привилегия, "
                     "президент, премьера, претензия."],
                    ["Where the prefix meaning is opaque, use the dictionary: привередливый, пренебрегать."]),
        everyday=(["ПРИ- — «рядом и вместе»: приморский город стоит у моря, пристройка прилегает к дому. ПРЕ- — «очень» или "
                   "«пере-»: преинтересный значит очень интересный, преградить — перегородить.",
                   "Замена на «очень» или «пере-» — удобная проверка, но не для словарных слов: «привилегия» не означает "
                   "приближения, её просто запоминают."],
                  ["ПРИ- means «near and together»: a seaside (приморский) town stands by the sea, an extension (пристройка) adjoins the house. ПРЕ- means «very» or «пере-»: преинтересный = very interesting.",
                   "The substitution test does not work for dictionary words such as привилегия."]),
        correct=["прекрасный", "преодолеть", "приморский", "приоткрыть", "пребывать в Минске", "поезд прибывает"],
        wrong=[("приодолеть", "преодолеть"), ("пребрежный", "прибрежный")],
        steps=(["Определите значение приставки.", "Попробуйте заменить на «очень» или «пере-».",
                "Если значение не выделяется — проверьте по словарю."],
               ["Find the prefix meaning.", "Try «очень»/«пере-».", "Otherwise use the dictionary."]),
        sources=["lopatin", "rus-orfo"],
    ),
    "y-after-prefix": dict(
        rule=(["После русских приставок на согласную корень, начинающийся с и, пишется с ы: играть — разыграть, "
               "история — предыстория.",
               "После приставок меж- и сверх-, после иноязычных приставок (дез-, контр-, пост-, суб-, транс-) и в "
               "сложносокращённых словах сохраняется и: межинститутский, сверхизысканный, дезинформация, пединститут."],
              ["After native prefixes ending in a consonant, root-initial и becomes ы: разыграть.",
               "After меж-, сверх-, foreign prefixes and in abbreviated compounds и stays: межинститутский, дезинформация."]),
        exceptions=(["взимать — пишется и."], ["взимать keeps и."]),
        everyday=(["Русская приставка «притягивает» произношение: мы говорим [разыграть], и буква следует за звуком.",
                   "Иноязычные приставки так не действуют: «дезинформация» сохраняет и. Помните, что сверх- и меж- тоже "
                   "сохраняют и — по традиции, а не по слуху."],
                  ["A native prefix pulls the pronunciation, and the letter follows the sound.",
                   "Foreign prefixes do not work this way: «дезинформация» keeps и. Remember that сверх- and меж- also keep и — by tradition, not by hearing."]),
        correct=["разыграть", "предыстория", "сверхизысканный", "дезинформация", "взимать"],
        wrong=[("разиграть", "разыграть"), ("сверхызысканный", "сверхизысканный")],
        steps=(["Найдите приставку и первую букву корня.", "Русская приставка на согласную → ы.",
                "Меж-, сверх-, иноязычная приставка, сложносокращённое слово → и."],
               ["Find the prefix and the root's first letter.", "Native prefix → ы.", "меж-/сверх-/foreign/abbreviation → и."]),
        sources=["lopatin"],
    ),
    "hard-soft-sign": dict(
        rule=(["Разделительный ъ пишется после приставки на согласную перед е, ё, ю, я (подъезд, съёмка, предъюбилейный), "
               "в сложных словах с двух-, трёх-, четырёх- (двухъядерный) и после иноязычных приставок (адъютант, субъект, "
               "инъекция).",
               "Разделительный ь пишется внутри корня и перед окончанием перед е, ё, ю, я, и (вьюга, семья, серьёзный) и в "
               "некоторых заимствованиях перед о (бульон, медальон)."],
              ["Separating ъ: after a prefix ending in a consonant before е, ё, ю, я; in compounds with двух-/трёх-; after "
               "foreign prefixes.", "Separating ь: inside a root/before an ending before е, ё, ю, я, и; before о in some loans."]),
        exceptions=(["Перед другими гласными после приставок ъ не пишется: безоблачный, сэкономить."],
                    ["Before other vowels no ъ: безоблачный."]),
        everyday=(["Ъ — как шлагбаум на границе приставки и корня, Ь — разделитель внутри «одной страны» корня.",
                   "Граница видна только при разборе: «объявление» = об + явление (ъ), а «вьюга» — одна морфема (ь). "
                   "По слуху их не отличить, нужен разбор слова."],
                  ["Ъ is like a barrier on the border between a prefix and a root, while Ь is a separator inside the «same country» of the root.",
                   "The border is visible only when you parse the word: «объявление» = об + явление (ъ), while «вьюга» is one morpheme (ь). You cannot tell them apart by ear."]),
        correct=["подъезд", "объявление", "двухъядерный", "вьюга", "бульон"],
        wrong=[("подьезд", "подъезд"), ("въюга", "вьюга")],
        steps=(["Найдите место перед е, ё, ю, я.", "Это граница приставки и корня? → ъ.", "Внутри корня или перед окончанием? → ь."],
               ["Find the spot before е, ё, ю, я.", "Prefix–root border → ъ.", "Inside the root/before the ending → ь."]),
        sources=["lopatin"],
    ),
    "soft-sign-sibilants": dict(
        rule=(["После шипящих на конце слова ь пишется: у существительных женского рода 3-го склонения (ночь, мощь), "
               "в глаголах (читаешь, печь, режь), в наречиях (настежь, сплошь).",
               "Ь не пишется: у существительных мужского рода (плач, калач), в родительном падеже множественного числа "
               "(туч, задач), у кратких прилагательных (горяч, хорош)."],
              ["After hushing consonants at the end ь is written in feminine 3rd declension nouns, verbs and adverbs.",
               "No ь in masculine nouns, genitive plurals and short adjectives."]),
        exceptions=(["уж, замуж, невтерпёж — наречия без ь."], ["уж, замуж, невтерпёж — no ь."]),
        everyday=(["Мягкий знак после шипящих ничего не смягчает — ш, ж, ч, щ звучат одинаково и с ним, и без него. Здесь "
                   "ь работает как ярлык части речи и рода.",
                   "Поэтому слух бесполезен: «плач» и «плачь» звучат одинаково. Решает часть речи (существительное или "
                   "глагол) и род — их и нужно определить."],
                  ["Ь after hushing consonants softens nothing; it is a label of part of speech and gender.",
                   "That is why hearing is useless: «плач» (crying, noun) and «плачь» (cry!, verb) sound the same. The part of speech and the gender decide, so determine them first."]),
        correct=["ночь", "громкий плач", "читаешь", "настежь", "много туч", "суп горяч"],
        wrong=[("плачь (сущ.)", "плач"), ("ночь → ноч", "ночь"), ("настеж", "настежь")],
        steps=(["Определите часть речи.", "Для существительного — род и падеж.", "Примените правило и проверьте исключения."],
               ["Find the part of speech.", "For nouns — gender and case.", "Apply the rule and check exceptions."]),
        sources=["lopatin"],
    ),
    "noun-endings": dict(
        rule=(["Существительные на -ий, -ие, -ия в предложном падеже (а на -ия ещё и в дательном) имеют окончание -и: "
               "в санатории, о гении, на лекции.",
               "Остальные существительные 1-го и 2-го склонения в этих падежах имеют -е (по аллее, в ущелье), "
               "существительные 3-го склонения в Р., Д., П. п. — -и (по тетради)."],
              ["Nouns in -ий, -ие, -ия take -и in the prepositional (and dative for -ия): в санатории, на лекции.",
               "Other 1st/2nd declension nouns take -е (по аллее, в ущелье); 3rd declension nouns take -и."]),
        exceptions=(["Существительные на -ье (ущелье, счастье) — это не -ие: в ущелье, о счастье."],
                    ["Nouns in -ье are not -ие: в ущелье."]),
        everyday=(["Подставьте вместо слова «проверочное» существительное того же склонения с ударным окончанием: в "
                   "санатории — как «в земле»? Нет, у -ий своё правило, поэтому сначала посмотрите на начальную форму.",
                   "Частая ловушка — предлог «в»: «в здание» (куда?) и «в здании» (где?) — разные падежи. Сначала задайте "
                   "вопрос, потом выбирайте окончание."],
                  ["Start from the dictionary form of the noun: words in -ий, -ие, -ия follow their own rule (в санатории), all others take -е in the same cases (в ущелье).",
                   "A frequent trap is the preposition «в»: «в здание» (where to?) and «в здании» (where?) are different cases. Ask the question first, then choose the ending."]),
        correct=["в санатории", "на лекции", "по аллее", "в ущелье", "по тетради"],
        wrong=[("в санаторие", "в санатории"), ("по аллеи", "по аллее")],
        steps=(["Поставьте слово в начальную форму.", "Определите склонение и падеж (задайте вопрос).",
                "Выберите окончание по правилу."],
               ["Put the word in its dictionary form.", "Find declension and case.", "Choose the ending."]),
        sources=["lopatin"],
    ),
    "noun-adj-suffixes": dict(
        rule=(["-ек-/-ик-: если гласная при склонении выпадает — -ек- (замочек — замочка), сохраняется — -ик- "
               "(ключик — ключика).",
               "-ец- (мужской род), -иц- (женский); в среднем роде -ец- при ударении на окончании (пальтецо́), -иц- при "
               "ударении на основе (пла́тьице).",
               "Суффиксы прилагательных -лив-, -чив- пишутся с и; -ев- пишется после мягких и шипящих без ударения "
               "(плюшевый), -еньк- — всегда с е."],
              ["-ек-/-ик-: a dropping vowel → -ек-, a stable one → -ик-.", "-ец-/-иц-; neuter: -ец- if the ending is stressed.",
               "-лив-, -чив- with и; -ев- after soft/hushing consonants when unstressed; -еньк- with е."]),
        exceptions=(["Под ударением после шипящих пишется -ов- (грошо́вый)."], ["Stressed after hushing: -ов- (грошо́вый)."]),
        everyday=(["Проверка «выпадает — не выпадает» как проверка шва: потяните слово в другой падеж — если гласная исчезла "
                   "(замочек — замочка), шов был «мягким» (-ек-).",
                   "Проверка работает только для этих суффиксов: в корне (горошек — горох) рассуждения другие. Сначала "
                   "выделите суффикс."],
                  ["The «drops or stays» test is like testing a seam: pull the word into another case — if the vowel disappears (замочек — замочка), the suffix was -ек-.",
                   "The test works only for these suffixes; in a root (горошек — горох) the reasoning is different. Isolate the suffix before applying the test."]),
        correct=["замочек", "ключик", "пальтецо", "платьице", "заботливый", "плюшевый"],
        wrong=[("замочик", "замочек"), ("ключек", "ключик"), ("заботлевый", "заботливый")],
        steps=(["Выделите суффикс.", "Для -ек-/-ик- измените падеж; для -ец-/-иц- определите род и ударение.",
                "Для прилагательных вспомните -лив-, -чив-, -ев-, -еньк-."],
               ["Isolate the suffix.", "Change the case / find gender and stress.", "Recall -лив-, -чив-, -ев-, -еньк-."]),
        sources=["lopatin"],
    ),
    "o-yo-sibilants": dict(
        rule=(["В корне под ударением после шипящих пишется ё, если в однокоренном слове пишется е (чёрный — чернеть); "
               "если такого чередования нет — о (шорох, крыжовник).",
               "В суффиксах и окончаниях существительных, прилагательных и наречий под ударением пишется о (плащом, "
               "медвежонок, горячо); в глагольных формах и словах от них — ё (дирижёр, сгущёнка, тушёнка)."],
              ["In a stressed root after hushing consonants write ё when a cognate has е (чёрный — чернеть), otherwise о.",
               "Stressed noun/adjective/adverb suffixes and endings have о (плащом); verbal forms and their derivatives have ё."]),
        exceptions=(["В заимствованиях после шипящих — о (шоколад, жокей); беглая гласная — о (шов — шва)."],
                    ["Loanwords have о (шоколад); a fleeting vowel is о (шов)."]),
        everyday=(["Ё в корне — «замаскированное е»: стоит изменить слово, и маскировка спадает (жёлудь — желудей).",
                   "Если маскировку снять нельзя, буква — о. Но в суффиксах и окончаниях правило другое: смотрите на часть "
                   "слова, а не на звучание."],
                  ["ё in a root is a disguised е: change the word and the disguise falls (жёлудь — желудей).",
                   "If it cannot be removed, write о; suffixes/endings follow another rule."]),
        correct=["чёрный", "шорох", "плащом", "медвежонок", "дирижёр", "шоколад"],
        wrong=[("чорный", "чёрный"), ("плащём", "плащом"), ("шёколад", "шоколад")],
        steps=(["Определите часть слова с пропуском: корень, суффикс или окончание.",
                "В корне подберите слово с е; в суффиксе/окончании учтите часть речи.", "Проверьте исключения."],
               ["Find the morpheme.", "Root: look for е; suffix/ending: mind the part of speech.", "Check exceptions."]),
        sources=["lopatin"],
    ),
    "verb-endings": dict(
        rule=(["Ко II спряжению относятся глаголы на -ить (кроме брить, стелить) и 11 исключений: гнать, держать, дышать, "
               "слышать, видеть, обидеть, ненавидеть, зависеть, вертеть, терпеть, смотреть; их окончания -ишь, -ит, -им, "
               "-ите, -ат/-ят. Остальные — I спряжение: -ешь, -ет, -ем, -ете, -ут/-ют.",
               "Перед суффиксом -л- пишется та же гласная, что перед -ть (клеить — клеил).",
               "-ова-/-ева- пишется, если в 1-м лице -ую/-юю (ночую — ночевать); -ыва-/-ива-, если -ываю/-иваю."],
              ["2nd conjugation: verbs in -ить (except брить, стелить) and 11 exceptions; others are 1st conjugation.",
               "Before -л- keep the vowel before -ть.", "-ова-/-ева- if the 1st person ends in -ую/-юю, else -ыва-/-ива-."]),
        exceptions=(["брить, стелить — I спряжение (бреешь, стелешь)."], ["брить, стелить are 1st conjugation."]),
        everyday=(["Спряжение — как «прописка» глагола: чтобы узнать окончание, смотрим не на форму (видишь), а на "
                   "начальную форму (видеть) — она скажет, в каком «доме» глагол живёт.",
                   "Начальную форму берите того же вида: «выгонишь» проверяйте глаголом «выгнать», а не «выгонять». Иначе "
                   "можно ошибиться со спряжением."],
                  ["Conjugation is the verb's address: look at the infinitive, not at the form.",
                   "Take the infinitive of the same aspect: «выгонишь» is checked by «выгнать», not «выгонять». Otherwise you may get the conjugation wrong."]),
        correct=["борешься", "видишь", "клеишь", "стелешь", "клеил", "ночевать"],
        wrong=[("видешь", "видишь"), ("стелишь", "стелешь"), ("клеял", "клеил")],
        steps=(["Поставьте ударение: под ударением окончание слышно.", "Если окончание безударное — найдите начальную "
                "форму того же вида.", "Определите спряжение с учётом исключений."],
               ["Check the stress.", "If unstressed, find the infinitive of the same aspect.", "Find the conjugation."]),
        sources=["lopatin"],
    ),
    "tsya": dict(
        rule=(["В глаголах пишется -тся, если глагол отвечает на вопрос «что делает?» / «что сделает?» (3-е лицо); "
               "-ться — если на вопрос «что делать?» / «что сделать?» (неопределённая форма)."],
              ["-тся when the verb answers «что делает?/что сделает?»; -ться for the infinitive «что делать?/что сделать?»."]),
        exceptions=(["Вопрос задают от того слова, к которому относится глагол: «будет (что делать?) длиться»."],
                    ["Ask the question from the word the verb depends on."]),
        everyday=(["Мягкий знак «переходит» из вопроса в ответ: в вопросе «что делать?» есть ь — пишем -ться, в вопросе "
                   "«что делает?» его нет — пишем -тся.",
                   "Главное — задать вопрос от правильного слова. В предложении «Нужно научиться» спрашиваем «нужно что "
                   "сделать?», а не «он что сделает?»."],
                  ["The soft sign moves from the question to the answer: the question «что делать?» has ь, so we write -ться; «что делает?» has none, so we write -тся.",
                   "The key is to ask from the right word. In «Нужно научиться» we ask «нужно что сделать?», not «он что сделает?»."]),
        correct=["ему не терпится", "нужно научиться", "река разливается", "будет длиться"],
        wrong=[("ему не терпиться", "ему не терпится"), ("нужно научится", "нужно научиться")],
        steps=(["Найдите слово, к которому относится глагол.", "Задайте от него вопрос.", "Есть ь в вопросе — пишите -ться."],
               ["Find the word the verb depends on.", "Ask the question.", "Ь in the question → -ться."]),
        sources=["lopatin"],
    ),
    "participle-suffixes": dict(
        rule=(["Суффиксы действительных причастий настоящего времени: -ущ-/-ющ- (I спряжение), -ащ-/-ящ- (II); страдательных: "
               "-ем- (I), -им- (II).",
               "Перед -вш- сохраняется гласная неопределённой формы (ненавидеть — ненавидевший).",
               "Окончание причастия проверяется вопросом «какой?» в нужной форме (о каком? — о волнующемся)."],
              ["Present active participles: -ущ-/-ющ- (1st), -ащ-/-ящ- (2nd); passive: -ем- (1st), -им- (2nd).",
               "Before -вш- keep the infinitive vowel.", "The ending follows the question «какой?»."]),
        exceptions=(["движимый — пишется -им-, хотя «двигать» — глагол I спряжения."], ["движимый is an exception."]),
        everyday=(["Причастие наследует «гены» глагола: спряжение глагола подсказывает суффикс (видеть — II — видимый).",
                   "Но наследство надо проверить у правильного «родителя»: начальная форма того же вида и значения. "
                   "Исключение «движимый» просто запомните."],
                  ["A participle inherits the «genes» of its verb: the verb's conjugation suggests the suffix (видеть — 2nd conjugation — видимый).",
                   "But check the inheritance with the right «parent»: an infinitive of the same aspect and meaning. Simply memorise the exception «движимый»."]),
        correct=["видимый", "решаемый", "ненавидевший", "клеивший", "о волнующемся море"],
        wrong=[("видемый", "видимый"), ("ненавидивший", "ненавидевший")],
        steps=(["Найдите начальную форму глагола.", "Определите спряжение.", "Подставьте суффикс; окончание проверьте вопросом."],
               ["Find the infinitive.", "Find the conjugation.", "Choose the suffix; check the ending by a question."]),
        sources=["lopatin"],
    ),
    "adjectives": dict(
        rule=(["Качественные прилагательные обозначают признак, который может быть больше или меньше (смелый — смелее), "
               "имеют краткую форму и степени сравнения.",
               "Относительные обозначают признак через отношение к предмету, материалу, времени, месту (деревянный, летний).",
               "Притяжательные отвечают на вопрос «чей?» (мамин, лисий)."],
              ["Qualitative adjectives are gradable and have short forms and comparison degrees.",
               "Relative adjectives express a relation to a material, time or place.", "Possessive adjectives answer «чей?»."]),
        exceptions=(["В переносном значении относительное или притяжательное прилагательное становится качественным: "
                     "железная воля, золотой характер."],
                    ["In figurative use a relative adjective becomes qualitative: железная воля."]),
        everyday=(["Качество можно «подкрутить» как громкость: смелый — смелее — очень смелый. Деревянный стол не может "
                   "быть «деревяннее», поэтому прилагательное относительное.",
                   "Но решает значение в сочетании, а не слово само по себе: «железный гвоздь» — относительное, «железная "
                   "воля» — качественное."],
                  ["A quality can be turned up like volume; a wooden table cannot be «more wooden».",
                   "The meaning in the phrase decides, not the word on its own: «железный гвоздь» (an iron nail) is relative, «железная воля» (iron will) is qualitative."]),
        correct=["смелый поступок — качественное", "деревянный стол — относительное", "лисий хвост — притяжательное"],
        wrong=[("железная воля — относительное", "качественное (переносное значение)")],
        steps=(["Определите значение прилагательного в сочетании.", "Проверьте: можно ли сказать «более/очень»?",
                "Вопрос «чей?» — притяжательное."],
               ["Find the meaning in the phrase.", "Can you add «более/очень»?", "«чей?» → possessive."]),
        sources=["grammar1980"],
    ),
    "function-words": dict(
        rule=(["Предлог, союз и частица — служебные части речи: они не являются членами предложения и выражают отношения "
               "между словами, частями предложения или оттенки значения.",
               "Производные предлоги совпадают по звучанию со знаменательными словами: благодаря (чему?) поддержке — "
               "предлог; благодаря (кого?) хозяев — деепричастие; вокруг дома — предлог; вокруг было тихо — наречие."],
              ["Prepositions, conjunctions and particles are function words; they are not sentence parts.",
               "Derived prepositions look like content words: благодаря поддержке (preposition) vs благодаря хозяев "
               "(verbal adverb); вокруг дома (preposition) vs вокруг было тихо (adverb)."]),
        exceptions=(["Слово меняет часть речи в зависимости от употребления — решает зависимое слово и вопрос."],
                    ["The use decides: look for a dependent word."]),
        everyday=(["Предлог похож на крючок: на нём обязательно что-то «висит» — существительное или местоимение (вокруг "
                   "дома). Наречие — самостоятельная деталь, которой крючок не нужен (вокруг было тихо).",
                   "Проверка «есть ли зависимое слово» надёжна, но смотрите на смысл: «благодаря хозяев» — это действие "
                   "(благодарить), а не причина, поэтому деепричастие."],
                  ["A preposition is a hook: something must hang on it. An adverb stands alone.",
                   "The «dependent word» test is reliable, but also check the meaning: «благодаря хозяев» is an action (to thank the hosts), not a cause, so it is a verbal adverb."]),
        correct=["вокруг дома — предлог", "вокруг было тихо — наречие", "благодаря поддержке — предлог"],
        wrong=[("после уроков — наречие", "после уроков — предлог")],
        steps=(["Найдите слово, к которому относится выделенное.", "Есть зависимое существительное/местоимение? → предлог.",
                "Слово отвечает на вопрос и является членом предложения? → наречие; обозначает действие? → деепричастие."],
               ["Find the dependent word.", "Noun/pronoun depends on it → preposition.", "A sentence part → adverb; an action → "
                "verbal adverb."]),
        sources=["grammar1980"],
    ),
    "verb-aspect": dict(
        rule=(["Глаголы совершенного вида отвечают на вопрос «что сделать?» и обозначают законченное действие или его "
               "результат (решить, крикнуть); несовершенного вида — «что делать?» и обозначают процесс, повторение "
               "(решать, кричать)."],
              ["Perfective verbs answer «что сделать?» (result, completion); imperfective «что делать?» (process, repetition)."]),
        exceptions=(["Двувидовые глаголы (жениться, казнить, использовать) в тренажёре не проверяются: их вид зависит от "
                     "контекста."],
                    ["Biaspectual verbs are not tested."]),
        everyday=(["Совершенный вид — фотография результата («решил»), несовершенный — видеозапись процесса («решал»).",
                   "Вопрос «что сделать?» надёжнее приставки: «посидеть» — совершенный вид, хотя «сидеть» — "
                   "несовершенный; приставка сама по себе вид не определяет."],
                  ["Perfective is a photo of the result; imperfective is a video of the process.",
                   "The question «что сделать?» is more reliable than a prefix: «посидеть» is perfective although «сидеть» is imperfective; a prefix alone does not define the aspect."]),
        correct=["решить — совершенный", "решать — несовершенный", "посидеть — совершенный"],
        wrong=[("говорить — совершенный", "говорить — несовершенный")],
        steps=(["Поставьте глагол в начальную форму.", "Задайте вопрос «что делать?» или «что сделать?».", "Определите вид."],
               ["Use the infinitive.", "Ask the question.", "Name the aspect."]),
        sources=["grammar1980", "opencorpora"],
    ),
}
