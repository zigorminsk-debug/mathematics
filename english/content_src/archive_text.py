"""Visually checked transcriptions of supplied variant 1 pages.

Spelling/grammar mistakes which are the subject of a question MUST remain.
Numbered square brackets replace underlining; line boundaries in extra-word
passages are explicit B labels. These are transcriptions, not new authored tasks.
Original source scans remain the audit reference. Public distribution rights
have not been independently established. The user requested publication with
source links; this is attribution, not a claim of a granted licence.
"""
from __future__ import annotations

TEXT = {}


def add(year, part, n, text, options=None, instruction=None):
    key = f'en-archive-{year}-v1-{part}{n}'
    if key in TEXT:
        raise ValueError(f'Duplicate transcription {key}')
    item = {'condition': text.strip(), 'reviewed': True}
    if options:
        item['options'] = dict(zip(map(str, range(1, len(options) + 1)), options))
    if instruction:
        item['instruction'] = instruction
    TEXT[key] = item


def choices(year, start, passage, rows):
    for n, row in enumerate(rows, start):
        add(year, 'A', n, passage, row.split('|'))


def extra(year, start, lines):
    passage = '\n'.join(f'B{n}. {line}' for n, line in enumerate(lines, start))
    for n in range(start, start + len(lines)):
        add(year, 'B', n, passage, instruction='Delete exactly ONE extra word from the indicated line. Keep the line boundaries shown below.')


def forms(year, start, count, passage):
    for n in range(start, start + count):
        add(year, 'B', n, passage, instruction='Change the word in brackets into a related word that fits the indicated gap. The given form must be changed.')


# 2025 — PDF pages 6–9 (printed pages 5–8), including the missing OCR line B12.
choices(2025, 1, """Last year, more than one billion kilos of chocolate (A1) ... around the world. Chocolate is made from the cacao plant. However, many cacao farmers (A2) ... enough money and can't afford food, medicine or clean water. In Africa, a typical cacao grower is paid less than a dollar a day. Now the international organisation called Fairtrade (A3) ... farmers to get fair prices. Farming organisations have been set up in African countries and every month some extra money (A4) ... in projects such as drinking water.""", [
    'are eaten|had eaten|were eating|ate|were eaten',
    "weren't earning|don't earn|won't be earned|weren't earned|hadn't earned",
    'helped|is helped|will be helped|was helped|is helping',
    'invests|has invested|is invested|has been investing|will invest',
])
add(2025, 'A', 5, 'Before we went on our adventure to climb ... Mount Elbrus, our guide gave us ... valuable advice about the best equipment to bring for the cold weather.', ['–, a', 'the, a', 'the, the', '–, –', 'a, a'])
add(2025, 'A', 6, '... of paying for four items on your website, I only received three in the post.', ['Although', 'As', 'Despite', 'So that', 'In spite'])
add(2025, 'A', 7, "[I went to the café] (1) to talk to the manager or the waiter but [none of them] (2) [could help me] (3) find the wallet [that] (4) I had lost [the day before] (5).", ['I went to the café', 'none of them', 'could help me', 'that', 'the day before'], 'Choose the number of the bracketed fragment containing an error. Brackets represent the original underlining.')
add(2025, 'A', 8, "Belovezhskaya Pushcha [is home to many ancient oak trees] (1) [dating back] (2) more than [five hundreds years] (3). [There are] (4) significant animal populations here, including [the world’s largest] (5) European bison.", ['is home to many ancient oak trees', 'dating back', 'five hundreds years', 'There are', 'the world’s largest'], 'Choose the number of the bracketed fragment containing an error. Brackets represent the original underlining.')
choices(2025, 9, """How would you feel about living on a desert island for a week? Could you (A9) ... after yourself and find your own food? This was the challenge that five teenagers from London were given. The first thing they had to find was fresh drinking water. They knew that seawater only leaves you feeling thirstier and isn't good for your health. So, they needed to locate fresh running water and soon found a waterfall. There was a (A10) ... range of fruit on the island and from their preparation lessons they knew how to recognise the ones which are good to eat. But they still had to go out in (A11) ... of them. Some of the students also tried to catch fish, but without a net this was much too difficult. Fortunately, they found a (A12) ... coconut trees, so they didn't go hungry.""", [
    'notice|watch|care|look|take', 'wide|long|high|deep|exciting',
    'look|search|discovery|hunt|catch', 'number|deal|amount|lot|few',
])
add(2025, 'A', 13, "Man: I'd like to take a trip down the coast this weekend.\nWoman: Me too.\nWhat does the woman mean?", ['She would like to take two trips rather than one.', "She doesn't think that a trip would be a good idea.", 'The trip would cost too much.', 'She would also like to take a trip.', "She's already taken a trip."])
add(2025, 'A', 14, 'Have you got this top in a bigger size?', ['I think so. Let me check.', "I'm afraid so.", 'No, go ahead.', "It's a pity.", "No, I'm afraid it isn't."], 'Choose the reply that fits the situation.')
TENNIS = """Play to win
16-year-old Harry Moore writes about his hobby, tennis.
§ 1. My parents have always loved tennis and they're members of a tennis club. My older brother was really good at it and they supported him – taking him to lessons all the time. So I guess when I announced that I wanted to be a tennis champion when I grew up I just intended for them to notice me. My mother laughed. She knew I couldn't possibly be serious, I was just a 4-year-old kid!
§ 2. Later, I joined the club's junior coaching group and eventually took part in my first proper contest, confident that my team would do well. We won, which was fantastic, but I wasn't so successful. I didn't even want to be in the team photo because I didn't feel I deserved to be. When my coach asked what happened in my final match, I didn't know what to say. I couldn't believe I'd lost – I knew I was the better player. But every time I attacked, the other player defended brilliantly. I couldn't explain the result.
§ 3. After that, I decided to listen more carefully to my coach because he had a lot of tips. I realised that you need the right attitude to be a winner. On court I have a plan but sometimes the other guy will do something unexpected so I'll change it. If I lose a point, I do my best to forget it and find a way to win the next one.
§ 4. At tournaments, it's impossible to avoid players who explode in anger. A lot of players can be negative – including myself sometimes. Once I got so angry that I nearly broke my racket! But my coach has helped me develop ways to control those feelings. After all, the judges have a hard job and you just have to accept their decisions.
§ 5. My coach demands that I train in the gym to make sure I'm strong right to the end of a tournament. I'm getting good results: my shots are more accurate and I'm beginning to realise that with hard work there's a chance that I could be a champion one day."""
for n, question, options in [
    (15, 'Harry thinks he said that he was going to be a tennis champion in order to ...', 'please his parents.|get some attention.|annoy his older brother.|persuade people that he was serious.'),
    (16, 'How did Harry feel after his first important competition?', 'confused about his defeat.|proud to be a member of the winning team.|ashamed of the way he treated the other player.|amazed that he had got so far in the tournament.'),
    (17, "What does Harry try to remember when he's on the court?", "Let the other player surprise you.|Follow your game plan.|Respect the other player.|Don't keep thinking about your mistakes."),
    (18, 'What does Harry say about his behaviour in tournaments?', 'He broke his racket every time he was angry.|He stays away from players who behave badly.|He tries to keep calm during the game.|He found it difficult to deal with one judge’s decisions.'),
]:
    add(2025, 'A', n, TENNIS + '\n\n' + question, options.split('|'), 'Read the passage and choose the answer consistent with its content.')
for n, sentence in enumerate([
    'The increasing use of plastic puts marine life and ocean ecosystems ... risk.',
    'He prefers playing soccer ... basketball because he finds it more exciting.',
    "Our company takes pride in ensuring that our deliveries are made on time, even when it's pouring ... rain.",
    "James can't afford to buy this car. Why ... look for a model that's cheap enough to meet his needs?",
    'How ... you use to organise your photos before digital cameras came along?',
    'They rarely go to the movies, ... they?',
    'The children have ... turns with the game console since their parents set limits on screen time.\nWhen we chose the venue, the budget was ... into consideration.',
    'They ... in love with the idea of starting their own business after attending a seminar.\nMary ... asleep on the train and woke up just in time to get off at her destination.',
], 1):
    add(2025, 'B', n, sentence, instruction=('Fill the gap with ONE preposition.' if n <= 3 else 'Fill the gap with ONE word (at most 15 characters).' if n <= 6 else 'Fill BOTH gaps with the SAME word in the SAME form. Write it only once.'))
extra(2025, 9, [
    "Today's grandparents who are joining their grandchildren on social media, but the",
    "different generations' online habits are such different. In the UK the over-55s are joining",
    "Facebook in increasing numbers, meaning that they will as soon be the site's second",
    "biggest user group. Sheila, aged 59, says us, ‘I joined to see what my grandchildren are",
    "doing, as my daughter posts lots videos and photos of them. It's a much better way to",
    "see what they're doing than have waiting for letters and photos in the post. That's how",
    "we did it when I was a child, but I think I'm enough lucky I get to see much more of their",
    "lives than my grandparents did itself.’ Ironically, Sheila's grandchildren are less likely",
    "to use Facebook themselves. Every children under 17 in the UK are leaving the site –",
    "only 2.2 million users are under 17 – but they're not going to far from their smartphones.",
])
forms(2025, 19, 4, """Technology addiction is when people find it hard to stop using their devices, like smartphones, tablets, and video games. Technology (B19) ... (SIMPLE) life in some ways and makes it easier to connect with friends and access information. However, it can have (B20) ... (DISASTER) consequences. Children and adults alike may find themselves (B21) ... (ENTIRE) focused on their devices, missing out on real-life activities, like spending time with family and friends or playing outside. It can affect sleep, cause stress, and even lead to problems with focus and learning. It's important to find a balance between screen time and other activities. The (B22) ... (REQUIRE) for healthy technology use include setting limits on screen time, taking regular breaks, and engaging in face-to-face interactions.""")

# 2021 — PDF pages 2–5.
choices(2021, 1, """Since 2015 I (A1) ... a dog called Maggie. I never like to stay away from home too long, because I know she will be waiting for me to return. You've seen my dog, haven't you? I think you (A2) ... her when I was at the office yesterday. She (A3) ... next to me when you came in. She is the whitest, most beautiful dog I have ever seen. She (A4) ... once, however. One day, when I was in the country with Maggie, someone I (A5) ... before grabbed her and angrily said to me that she was his dog, but I said to him that this dog was mine! This story was not funny then, but I laugh at it now. However, I (A6) ... careless with my dog because she is very precious to me. What I want is always to love and protect her. It is difficult for me to imagine life without her.""", [
    'have|have had|am having|was having|had', 'would see|had seen|were seeing|saw|were seen',
    'sits|would sit|had sat|has been sitting|was sitting',
    'would be almost stolen|had almost stolen|was almost stolen|was almost stealing|almost steals',
    'will never see|was never seeing|would never see|was never seen|had never seen',
    'will never again be|was never again being|had never again been|have never again being|never again was',
])
choices(2021, 7, """Sea lions are friendly-looking animals. Their round faces and whiskers remind people (A7) ... the faces of small dogs. The almond shape of their eyes gives them a look of intelligence. Whether it is true or not, sea lions often look as though they are thinking. They are often observed relaxing (A8) ... the sun on the shores or rocks. If you have been to a marine park, you may have watched sea lions. They can be taught many tricks. They can balance balls on their noses. They can jump through hoops. Their trainers give them fish to reward them (A9) ... doing tricks. Sea lions look very pleased (A10) ... themselves when they perform. They love fish, and they grow to love applause.""", [
    'over|of|off|from|–', 'with|to|on|at|in', 'for|on|with|by|in', 'at|in|with|of|over',
])
choices(2021, 11, """(A11) Nowadays ... ease with which we can wash our clothes is taken for granted. All we have to do is pop our laundry into the washing machine, put in some washing powder, make sure the settings are correct and switch on. However, this basic appliance has only become ... common feature of most households since the 1950s.
(A12) The first mechanical washing machines were in ... use as far back as the 1700s, but it wasn't until the early 1900s that they were taken seriously and developed. Eventually, the washing machine became ... status symbol because it was well outside the price range of the average family.
(A13) As soon as the washing machine became affordable, Monday, or “wash day”, changed completely. ... tiring job of washing clothes by ... hand disappeared forever and was transformed into the simple task it is today.""", ['–, the|the, a|–, a|an, the|an, –', 'the, the|a, the|a, a|–, a|the, –', 'A, the|–, –|The, the|A, a|The, –'])
add(2021, 'A', 14, 'A girl [in my class] (1) called Diana [took part in] (2) [an interested experiment] (3) recently – her family [had to give up TV] (4) [for a month] (5).', ['in my class', 'took part in', 'an interested experiment', 'had to give up TV', 'for a month'], 'Choose the number of the bracketed fragment containing an error.')
add(2021, 'A', 15, "When [I was at my parents’ house] (1) [on Thursday] (2) I [looked through my old album] (3), which was full of [photographs] (4) of people [which names] (5) I forgot.", ['I was at my parents’ house', 'on Thursday', 'looked through my old album', 'photographs', 'which names'], 'Choose the number of the bracketed fragment containing an error.')
choices(2021, 16, """Archaeologists (A16) ... that a perfectly preserved 5,500-year-old shoe has been discovered in a cave in Armenia in south-west Asia. It is (A17) ... to be the oldest leather shoe ever found. The shoe was made of a single piece of leather, stitched at the front and back, and was shaped to fit the wearer's foot. It had been stuffed with grasses, either for warmth or to make sure it kept its shape. ‘The shoe is relatively small but we can't say for (A18) ... whether it was worn by a man or a woman,’ says Dr Ron Pinhasi, an archaeologist on the research team. ‘We thought at first that it was about 600-700 years old because it was in such good shape.’ Shoes of this type from later periods have turned up in archaeological excavations in various places in Europe, and shoes of a very similar design were still being used on the Aran Islands off the west coast of Ireland as (A19) ... as the 1950s. It's obviously a style which (A20) ... popular for thousands of years.""", [
    'report|reveal|present|record|spread', 'valued|felt|guessed|believed|concerned',
    'clear|exact|true|sure|definite', 'recently|shortly|presently|immediately|soon', 'held|kept|remained|lasted|continued',
])
add(2021, 'A', 21, "Man: Everybody said this astronomy course would be easy.\nWoman: But it hasn't quite worked out that way, has it?\nWhat does the woman think about the course?", ["It's too long.", 'Few people took it.', 'The course is as easy as it may seem.', 'There are too many unfamiliar questions.', "It's unexpectedly difficult."])
add(2021, 'A', 22, "I don't do well in all the subjects, I'm afraid.", ["I don't feel like it.", "Don't lose heart.", "It's out of the question.", "Don't mention it.", 'None at all.'], 'Choose the reply that fits the situation.')
add(2021, 'A', 23, """1. Have I been giving you a lot of trouble?
2. Will they adopt this project?
3. Do you think the winter will be cold?
4. Will you remember to put in a word for me?
A. I expect so.
B. Nothing at all.
C. Very unlikely.
D. I can't promise.
E. Not in the least.""", ['1C 2B 3D 4A', '1E 2A 3B 4C', '1B 2D 3E 4C', '1E 2C 3A 4D', '1C 2E 3B 4D'], 'Match prompts 1–4 with replies A–E. One reply is extra.')
add(2021, 'A', 24, """A. You could come to drum lessons with me.
B. My parents wouldn't be pleased if I practised at home, though. I think the guitar would make a better option, so I'm going for that.
C. I'm thinking of starting drum lessons.
D. It takes time to become good at any musical instrument, but I found it fairly easy. And now I'm pretty good at it, it's time to have lessons on something else.
E. Really? I thought you wanted to learn the piano like me.
F. I do, but I think it'll be too difficult.""", ['BEAFDC', 'ABDECF', 'ECDFAB', 'CEFDAB', 'CDEFBA'], 'Put the lines in order to make a coherent dialogue.')
LONELY = """§ 1. Tony and Maureen Wheeler have spent more than forty years travelling and recording their experiences in one of the world's most popular guidebook series. The Lonely Planet books were the first of a new type of travel guide. The appeal for young travellers was clear: expensive hotels were not mentioned, which attracted those managing on a limited budget. The books also emphasised the importance of spending time in a country and taking the time to get to know other cultures.
§ 2. So how did it all start? Tony and Maureen decided to drive from London to Asia in 1972, and bought a second-hand van which, with all the repairs it required during the trip, reflects their approach to life: a tendency to make decisions spontaneously and a willingness to cheerfully adapt to the highs and lows of travel. The couple started writing down tips on where to stay and how to survive, often in places far away from big cities. Eventually, they realised people might pay for such information, and so they produced their first book.
§ 3. In the early days, the main selling point was that they produced guidebooks to places nobody else investigated, but times have changed. ‘We started doing guidebooks on Asian countries which in those days didn't get much attention. Today, when our writers cover almost everywhere, our size and experience are probably our main advantages,’ Tony explains.
§ 4. Lonely Planet also relies on reader feedback. According to Tony, ‘Complaints from readers are often beyond our control; prices go up, places close, standards drop (or sometimes improve). Keeping up to date is the key. If one of our researchers has been inaccurate, then we're going to have to improve that book. Complaints from hotels or restaurants may be because they don't like what we have written about them, although we try not to pull a place to pieces if we don't have to.’
§ 5. It is not surprising that the Wheelers have strong views on how to choose suitable holidays. ‘First of all, ask yourself what your interests are. If you are interested in culture, this will affect where you go. Then you might consider how much time you have and what the options are for getting there and travelling around. I think you need to honestly consider what level of stress you can stand – do you really want excitement or moments of discomfort? Some people just want to relax! And keep in mind that it's not always necessary to take long trips; you should only travel for as long as you're happy to be travelling.’"""
for n, question, options in [
    (25, 'According to the text, why were the Lonely Planet guides popular with young people?', 'They gave new information on other cultures.|They focused on those with little money.|They encouraged very long trips abroad.'),
    (26, 'When the Wheelers went on their first trip abroad,', 'they realised the value of reliable transport.|they tried to get practical advice in advance.|they enjoyed dealing with the unexpected.'),
    (27, 'In paragraph 3, the writer says that Lonely Planet was different because', 'it dealt with unusual locations.|it relied heavily on advertising.|it had such a big team of writers.'),
    (28, 'In paragraph 5, the Wheelers recommend that travellers should', 'concentrate on cultural activities on holiday.|think about how adventurous they want to be.|take the most convenient means of transport.'),
    (29, 'What does feedback mean in § 4?', 'response|payment|choice'),
    (30, 'What does inaccurate mean in § 4?', 'untidy|unpunctual|incorrect'),
]:
    add(2021, 'A', n, LONELY + '\n\n' + question, options.split('|'))
forms(2021, 1, 6, """Unlike popular rumours, bats are nothing to be scared of. Bats are great, indeed! Not only are they super cute, but they help us humans out in many ways. Without bats, no one would pollinate our avocados, mangoes, or bananas. Bat is the common name of this remarkable animal while Chiroptera is its (B1) ... (SCIENCE) name. Bats are small, fast-moving, capable of sudden changes in direction and active at night. In (B2) ... (ADD) to this, they have (B3) ... (RAPID) moving wings and an (B4) ... (PREDICT) way of flying. Given these (B5) ... (CHARACTER), and the fact that bats often find suitable hiding places around human dwellings, it is perhaps not surprising that human fears have been transformed into superstition and myth. Centuries of myths and misinformation still generate needless fears and (B6) ... (THREAT) bats and their habitats.""")
extra(2021, 7, [
    'I have visited many countries, but it was Brazil that impressed me rather more than any other.',
    'Having graduated from university with a degree in biology, I would wanted to travel and see',
    'either wild animals and plants in their natural habitat. People who had visited Brazil described',
    'how much beautiful it was and I discovered that what they had told me was true. First of all,',
    "approximately a quarter of the world's plant species they are found in the Amazon basin, so no",
    'other matter where you go, you see the most beautiful plants, including orchids. Whatever part of',
    "Brazil you go to it, you won't be disappointed. However, I believe the southern states can be the most",
    'magical and it is because I very love flowers that I enjoyed myself so much. Having lost my camera, I',
    "wasn't been able to take photos, but I saw a lot of the local fauna and flora. It was a wonderful experience,",
    'and, taking into my consideration the amount of time I had at my disposal, I managed to see a lot.',
])
add(2021, 'B', 17, "Tea or coffee? – (Ничего), thanks. I've got to go in a minute to catch my train.", instruction='Translate the Russian fragment in brackets into English.')
add(2021, 'B', 18, "I think you have to (принять) into account that he's a good deal younger than the rest of us.", instruction='Translate the Russian fragment in brackets into English.')

# 2022 — PDF pages 2–5. Preserve malformed grammar in error questions.
choices(2022, 1, """If someone asks you what the best way of travelling from London to Paris is, you could suggest flying, taking the ferry or going through the Channel Tunnel. The ‘Chunnel’, as it is known, opened in 1994, and more than 200 million people (A1) ... it. Since 2000, pets have also been able to travel. So how did one of the wonders of modern engineering come about? The first plan to connect mainland Britain with France via a tunnel (A2) ... in 1802 by a French engineer. He wanted horse-drawn carriages to carry people through. Napoleon III later considered a tunnel, but thought it was too expensive. He was right – the modern ‘Chunnel’ creators overspent by 80 per cent. The tunnels (two for trains and one for maintenance) (A3) ... six years to build and are 50.5 km long. High-speed trains (A4) ... since 2007. It (A5) ... 35 minutes to travel the length of the Channel Tunnel. On a cheerier note, around 12 million roses (A6) ... through the tunnel every year for Valentine's Day.""", [
    'had used|were used|were using|are used|have used',
    'has presented|presented|was presented|was presenting|had presented',
    'were taken|took|take|have been taking|are taking',
    'ran|are run|are running|have been running|had run',
    'was taking|has been taking|is taken|will be taken|takes',
    'deliver|have delivered|are delivering|are delivered|will deliver',
])
choices(2022, 7, """As a child, Zack had eaten a wide variety of food and it wasn't until he started secondary school that he became addicted (A7) ... pizza. American school meals have often been criticised for the large amount of fast food present (A8) ... the menu. At Zack's school, pizza was the star dish and he couldn't get enough of it. Furthermore, there was only one thing he wanted to spend his pocket money on: slices of pizza. Naturally, Zack's family were worried about their son's diet. It was low (A9) ... vitamins. So was Zack. In a desperate attempt to break his addiction, he agreed to appear on a TV programme. Its aim was to encourage food addicts to beat their addictions with the help of a psychologist and nutritionist. It wasn't easy, but Zack finally demonstrated that he had given (A10) ... eating pizza. Zack met the challenge and, according to the programme makers, he has never eaten pizza again.""", ['with|for|to|in|on', 'at|on|in|to|with', 'in|at|with|for|by', 'in|off|on|out|up'])
choices(2022, 11, """(A11) Have you ever thought of visiting ... city which combines stunning beauty and a long history? York, the attractive, historical, walled city in North Yorkshire in England, can be ... excellent choice.
(A12) The Romans built York in AD 71. It has many remarkable sights to see, all of which reflect its importance in history. If you stroll down to the city centre, Jorvik Viking Centre, situated in one of the oldest Viking Age cities, can offer you an amazing journey through Viking Age as soon as you step aboard a time car. In ... actual fact, it takes you through a bustling market, dark, smokey houses and a busy wharf. They have all been recreated in ... accurate detail so that you can experience in sight, sound and smell what it was like to live and work in the Vikings' city of Yorvik.
(A13) As for a walk through York's historic city centre with its narrow medieval streets and modern shops, it'll definitely be a memorable experience. You can see there how successfully the old and the modern worlds can co-exist. All in ... all, York, which still keeps its traditional style and cultural heritage down the centuries, is ... city to remember.""", ['a, an|–, –|–, the|–, an|the, –', 'an, the|–, an|an, an|the, –|–, –', 'an, a|the, the|–, a|–, –|the, a'])
add(2022, 'A', 14, 'We are well [used to the influence] (1) of changing trends [in fashion and beauty] (2) and, although not [everyone wishes to follow them] (3), [it is undeniable] (4) that [a large number of people does] (5).', ['used to the influence', 'in fashion and beauty', 'everyone wishes to follow them', 'it is undeniable', 'a large number of people does'], 'Choose the number of the bracketed fragment containing an error.')
add(2022, 'A', 15, 'Salt, [which qualities] (1) [have been known since prehistoric times] (2), is used in almost every dish [in the world] (3) and is [admired by] (4) millions of [people] (5).', ['which qualities', 'have been known since prehistoric times', 'in the world', 'admired by', 'people'], 'Choose the number of the bracketed fragment containing an error.')
choices(2022, 16, """What is the secret of long life? Reducing calorie intake by 30 per cent is thought to lead to a longer lifespan, but for many, this can mean (A16) ... a starvation-like diet. However, scientists are now developing a drug which they believe can switch on a particular gene that has the same effect without the pain. A recent (A17) ... of centenarians (долгожители) found, though, that many in the over-100 age group had led unhealthy lifestyles for a long period of their lives. For these people a long life is the (A18) ... of a longevity gene and scientists have been working on a drug that can imitate this gene. Or is it all down to the mind? Some scientists believe that if we ‘think’ younger our bodies will follow. Research has shown that by (A19) ... people imagine they are twenty years younger, many of the (A20) ... of ageing actually go into reverse.""", ['going|leading|making|following|keeping', 'finding|search|study|proof|research', 'cause|luck|reason|aim|result', 'making|getting|forcing|causing|allowing', 'looks|notices|views|signs|symbols'])
add(2022, 'A', 21, "Woman: Did you notice that Mark shaved off his beard over the summer?\nMan: Notice? I didn't even recognise him.\nWhat does the man mean?", ["He hadn't noticed any change in Mark.", 'Mark looks different without a beard.', 'He thinks Mark looked better with the beard.', "He hasn't seen Mark yet.", 'He would never recognise Mark with his beard.'])
add(2022, 'A', 22, 'Do you mind if I switch off the light?', ["I'm afraid I don't.", "I'll make up my mind.", 'Never mind.', 'Not in the least.', 'My pleasure.'], 'Choose the reply that fits the situation.')
add(2022, 'A', 23, """1. Can you tell me the way to the market square?
2. Sorry to keep you waiting.
3. Could you pass me the paper?
4. Please remind me to post the letters.
A. Sure, it's over there.
B. That's all right.
C. Here you are.
D. Not at all.
E. I will.""", ['1A 2D 3E 4C', '1C 2B 3E 4D', '1C 2D 3A 4B', '1A 2B 3C 4E', '1B 2E 3C 4D'], 'Match prompts 1–4 with replies A–E. One reply is extra.')
add(2022, 'A', 24, """A. Great. Let's do that.
B. OK, how about we ask people for some photos of themselves with Maria, and maybe ask them to include a personal message too?
C. You know Maria's moving to another city next month, don't you? Some of us were thinking about buying her a present.
D. Yes, OK. That would be a really nice present. I'll start contacting Maria's friends. And maybe you can check out ideas online.
E. Like a leaving present? That's a good idea. We should get her something that reminds her of all her friends here. But I've no idea what.
F. And we could collect them all and put them together to make a scrapbook.""", ['AEBFDC', 'CEBFDA', 'EDAFBC', 'CAFBDE', 'EBDAFC'], 'Put the lines in order to make a coherent dialogue.')
POLAR = """§ 1. In 2004, Pen Hadow became the first person to trek to the North Pole alone. That meant swimming through unimaginably cold waters, fighting frostbite and risking encounters with polar bears. Just eight months later, he made a similar trip to the South Pole. Now he is back in the Arctic again, preparing for an expedition he says is somewhat of a different kind. This time there is far more at stake. Pen and two colleagues will set out on a three-month, 1,000-kilometre trek to the North Pole, taking detailed measurements of the thickness and density of the ice. Nobody has ever done this before, and he knows the results will be of vital importance to the scientific community. This will be the truest picture yet of what global warming is doing to the ice that covers the polar region.
§ 2. Pen and his wife live in the country with their two children. ‘They were one and five when I last went, and I made a mistake in the way I said goodbye. I thought it would be a good idea to say to my son, “You're the man of the house now, look after your mum and your sister.” He absolutely took it to heart, asking his mum how she was all the time, but the strain eventually became too much. While it was well intentioned, it was an unfair thing to do.’ For similar reasons he is planning to have very little contact with them while in the Arctic. ‘If you call them, you remind them how far away you are.’
§ 3. He is spending these last days before departure preparing his kit. ‘Out on the ice, one is virtually incapable of mending things,’ he says. With him will be Ann Daniels, one of the world's leading polar explorers, and the expedition photographer, Martin Hartley. They will be supported by a crew of six, flying in supplies. Being part of a team is actually more stressful to someone with his mentality, says Pen, and something else is on his mind too. ‘I'm going to be 47 on Thursday. I've done far less training than I'm comfortable with.’ Why? ‘Organisational things always seem more urgent. So I'm almost fearful of what I'm going to ask of myself.’
§ 4. Pen believes his mission reconnects exploration with the search for knowledge that drove previous generations into the unknown. ‘Making it to the North Pole was ultimately a personal ambition,’ he admits, ‘and of limited value to anyone beyond the polar adventuring community. This time, scientists will profit from the data, and we're creating a platform in which to engage as many people as possible in what's happening in the Arctic Ocean.’"""
for n, question, options in [
    (25, "In paragraph 1, what do we learn about Pen Hadow's opinion of the new expedition?", 'He thinks it may be harder than his previous journeys.|He is aware of the huge significance of its aims.|He is looking forward to the scientific work it will involve.'),
    (26, 'When talking about leaving his children for long periods, Pen mentions feeling', 'guilty that he once added to the pressure caused by his absence.|sad that he is missing so much of their growing up.|sorry that he can’t telephone more often.'),
    (27, 'What is worrying Pen about the new expedition?', 'whether the equipment will work properly in icy conditions|whether he will be mentally prepared|whether he will still be fit enough to take part'),
    (28, 'When he compares the new expedition to his previous ones, Pen feels', 'pleased that more people will benefit from it.|doubtful about its long-term usefulness.|relieved that the general public will be more supportive.'),
    (29, 'What does eventually mean in § 2?', 'suddenly|finally|occasionally'),
    (30, 'What does value mean in § 4?', 'waste|expense|significance'),
]:
    add(2022, 'A', n, POLAR + '\n\n' + question, options.split('|'))
forms(2022, 1, 6, """Are you tired of lying on the beach all day and baking in the sun? Are you keen on saving our planet and meeting like-minded people? If so, then one of our eco-tourism packages is the perfect (B1) ... (SOLVE) for your upcoming holidays. The waiting lists are long, so make sure your arrangements are made well in advance. Some eco-holidays are dedicated to protecting (B2) ... (DANGER) species and helping them to reproduce. There are many ways to experience (B3) ... (FORGET) vacations. What about caring for whales and then windsurfing in your free time? Or why not be part of a group that (B4) ... (REGULAR) patrols the grounds of a Kenyan nature reserve? Whatever your choice, our organisation will ensure that you don't experience any major (B5) ... (CONVENIENCE). Combine your passion for nature and travel, and do something to support our world! With us, it's not just a holiday; it's a chance to take a (B6) ... (RESPONSE) holiday.""")
extra(2022, 7, [
    'The best thing about the job it is that you get to spend the whole summer outside, doing exciting',
    'activities like kayaking and climbing. What could be most better than that? I feel certain you will',
    'agree that this is would be an enjoyable way to spend the summer holidays. On the other hand, it',
    "can be quite stressful because you're dealing with kids the whole time, and they can be such difficult.",
    "Clearly, when working with young children can be challenging from time to time. They don't give",
    "you much time off, either. Staff who are expected to work upwards of fifty hours per week. So, there's",
    'virtually no downtime when you can just chill in the sunshine. Despite of these disadvantages, I would',
    "still recommend this job to you. You'd be far perfect for it, given that you're so active and sporty, and",
    "you'd be a big hit with the kids. Let me to know if you want any contact names – I'm sure I could find",
    "some email addresses for you. Please don't hesitate yourself to contact me if you require further help.",
])
add(2022, 'B', 17, 'Using someone (другого) personal information and pretending to be them is a form of identity theft.', instruction='Translate the Russian fragment in brackets into English.')
add(2022, 'B', 18, 'Does Sally (похожа) after her grandfather in her talent for design?', instruction='Translate the Russian fragment in brackets into English.')

# 2023 — PDF pages 5–7.
choices(2023, 1, """U2 and the Rolling Stones are among the bands that (A1) ... worldwide tours in recent years. Tickets were sold out within minutes, and the bands performed for audiences of hundreds of thousands of people. Tours don't just happen overnight. When a band (A2) ... to put on a new show, preparations can go on for months. Among the things that have to be created are the special effects that (A3) ... in most big rock shows these days, and the videos that are screened before and during the show. These bands are determined that their fans (A4) ... the concert a letdown, so they work hard to make sure to give concerts that are worth seeing.""", ['had had|are having|have had|will have|are had', 'had decided|was deciding|is decided|was decided|decides', 'use|are used|are using|used|have used', "aren't found|hadn't found|weren't found|won't be found|won't find"])
add(2023, 'A', 5, "Jason survived the plane crash. He's ... man in the world.", ['lucky', 'more luckier', 'the most luckiest', 'the luckiest', 'luckier'])
add(2023, 'A', 6, "My dad in his late ... did hardly any exercise and didn't have a particularly healthy diet.", ["sixty's", 'sixtieth', 'sixty', "sixties'", 'sixties'])
add(2023, 'A', 7, '... St Lawrence River connects the Great Lakes to ... Atlantic Ocean.', ['The, the', '–, –', 'The, –', 'A, the', '–, an'])
add(2023, 'A', 8, 'Patricia provided us with ... great deal of ... helpful advice.', ['a, –', 'the, a', '–, –', 'the, the', 'a, a'])
choices(2023, 9, """The Academy Awards, also (A9) ... as the Oscars, are prizes given by the American Academy of Motion Picture Arts and Science to people in the film business. Oscars are awarded to top professionals of all kinds, including directors, actors, writers and (A10) ... designers. There is a special ceremony every year where the awards are presented. The Oscars are the oldest event of this kind. The very first one took (A11) ... in the Hollywood Roosevelt Hotel in 1929. Although the Academy presents seven other types of award, the star of the show is the Academy Award of Merit. This famous gold statue usually goes by its nickname of Oscar, though how it got this name is not certain. According to one story, the Academy librarian, Margaret Herrick, said that it (A12) ... her of her Uncle Oscar!""", ['referred|called|known|familiar|aware', 'suit|uniform|coat|costume|hat', 'seat|place|space|charge|part', 'referred|recognised|recovered|reminded|remembered'])
add(2023, 'A', 13, "X: I'm having a washing machine delivered this evening.\nY: ...\nX: No, it's fine, thanks.", ['Can you give me a hand with it?', "I'd rather you didn't.", 'Do you need a hand?', "Well, couldn't be better.", 'That would be great!'], 'Complete the mini-dialogue with the reply that fits.')
add(2023, 'A', 14, 'Do you mind if I borrow some money?', ['Sure. Here they are.', 'Never mind.', 'Nothing at all.', 'Either is fine with me.', 'Not at all.'], 'Choose the reply that fits the situation.')
FRESHLY = """‘Freshly’ Restaurant
by Peter Newman
§ 1. Last week my parents and I visited Freshly, a modern British restaurant, in the centre of Brighton, Sussex. So it was the perfect opportunity to write a review for the school paper.
§ 2. All of the ingredients used in Freshly come from Sussex and the surrounding area. It was also the first restaurant in the world to be serving only English wine. Since opening in 2018 Freshly has won many awards. The owner and head chef at the restaurant is only 24 years old and she has been cooking three-course meals for her family since she was nine and still at junior school. Jane did an apprenticeship at the famous Grand Hotel, in Brighton, and later also went to catering school in London. She says this was one of the hardest courses she has ever done and sometimes she was so tired that she could hardly speak. Despite this, she never felt like giving up because she knew she was following her dream.
§ 3. Freshly is a small restaurant with a view over the back streets of Brighton where you can watch the world walk by. The staff are always welcoming. The head waiter is very informative about the food and how it is cooked and also from where all the ingredients have come from. The chefs are not scared to experiment, so the menu changes regularly. The chefs are lucky enough to be a team of good friends, and they try to eat out at different restaurants as often as they can. They take a lot of inspiration from their favourite chefs to make the Freshly experience as perfect as possible.
§ 4. One thing to remember, however, is that you are limited to what they have that day on the menu. Freshly, however, will always cater for people with special food needs and vegetarians. The food is beautifully prepared and comes in small tasty portions. Wonderful homemade bread, too. Very nice – but expensive. Four set menus with an extra cheeseboard, two bottles of water and 2 coffees will cost around £150 without a tip. So yes, fine dining; but at a price."""
for n, question, options in [
    (15, 'The food at Freshly ...', 'is grown by the staff.|comes from places in or close to Brighton.|comes from all over the world.|comes all over Britain.'),
    (16, 'Where did the owner start to train as a chef?', 'at junior school|at university|at home with the help of her family|in a hotel'),
    (17, 'How did Jane feel while she was training to be a chef?', "She was really tired but felt positive about the experience.|She wanted to give up because of the pressure.|She wasn't sure if she would be successful.|She found it quite easy to finish the training."),
    (18, 'What is said about Freshly restaurant?', 'The head waiter is in charge of the menu.|The staff have a very good relationship with each other.|It is a big and fancy restaurant with a great view.|The staff often change jobs because they like to do different things.'),
]:
    add(2023, 'A', n, FRESHLY + '\n\n' + question, options.split('|'))
for n, sentence in enumerate([
    'My cousin is a scientist and he is trying to find a cure ... cancer.',
    "I'm very thankful ... all the advice you gave me.", 'The students were divided ... two teams.',
    "You can wear ... of those two dresses. They don't suit you.",
    'All students ... informed about the new IT course last week.',
    'Scientists are doing research into this rare species ... natural habitat is the bottom of the ocean.',
], 1):
    add(2023, 'B', n, sentence, instruction='Fill the gap with ONE word (at most 15 characters).')
for n, sentence in enumerate([
    'We had to make a difficult ... (DECIDE) about the future of our fashion brand.',
    'Teaching is not an appropriate job for an ... (RELIABLE) person, as children count on you a lot.',
    "Ted is ... (EXTREME) determined to get what he wants; he's so pushy.",
    'We really need to ... (STRENGTH) this step or someone is going to fall through it.',
], 7):
    add(2023, 'B', n, sentence, instruction='Change the word in brackets into a related word that fits the gap (at most 15 characters). The given form must be changed.')
extra(2023, 11, [
    'Can you imagine life without both a computer, or music or even lights? Kelvin Doe',
    'is an inspiring young man who from Sierra Leone. When he was growing up, the',
    "electricity in his neighbourhood didn't always have work, so the lights only used",
    'to come on once a week. As a boy, Kelvin was interested in how every things worked',
    'and he used to get such excited about making things. While he was hanging out with',
    'his friends, Kelvin used to find much materials in the street and make useful things',
    'from them. He used old electronic items to repair its broken TVs and radios. At 13,',
    'he even was made a battery so that his family had lights at night. He also built',
    'a radio station and played lots music on the radio. People called him DJ Focus',
    'because he believes that when you focus on something, you can to do anything.',
])
add(2023, 'B', 21, "I only see James from ... to time. He lives quite far away and he's always working.\nIt's ... to slow down and enjoy life more.", instruction='Fill BOTH gaps with the SAME word. Write it only once.')
add(2023, 'B', 22, "Appreciate and ... use of any support offered, and don't be afraid to ask for help when in need.\nPeople say that if you ... a wish at the top of the hill, it always comes true.", instruction='Fill BOTH gaps with the SAME word. Write it only once.')

# 2024 (filename year only) — PDF pages 2–4.
choices(2024, 1, """Meet Alison Lapper. She paints pictures for a living. But she's no ordinary painter. To start with, she (A1) ... her hands when she paints. She uses her mouth! Alison was born without arms and she has very short legs. Her physical disabilities caused her to spend the first 17 years of her life in a hospital. But this didn't stop her from achieving her goals in life. She (A2) ... that even though she was disabled, there was no reason why she could not express herself. This was what got her to start drawing paintings. Her paintings are quite impressive and they do not look like they (A3) ... by someone who used her mouth. Alison continues to encourage others by telling them never to give up hope of becoming successful. Her positive attitude has inspired many disabled people throughout the world and (A4) ... to do so in the future.""", ["doesn't use|isn't used|hadn't used|won't be used|wasn't used", 'has realised|was realised|is realised|has been realising|realised', 'drew|were drawn|have drawn|draw|had drawn', 'will continue|was continued|will be continued|has continued|is continued'])
add(2024, 'A', 5, 'Fiona and Emma want to visit Mexico this summer because ... of them has been there before.', ['any', 'both', 'none', 'neither', 'either'])
add(2024, 'A', 6, 'Such ... lovely weather at ... sunrise inspired me to take a moment to appreciate the simple pleasures of nature.', ['the, a', 'a, the', '–, –', 'a, a', '–, the'])
add(2024, 'A', 7, 'Carlos never seems to be at a loss for words, ... ?', ["isn't he", "doesn't him", 'seems he', 'is he', 'does he'])
add(2024, 'A', 8, "... Michael isn't very athletic, he can run very fast.", ['In spite', 'So that', 'Despite', 'Although', 'Since'])
choices(2024, 9, """Fashion trends are endlessly recycled. Styles that were popular in the 80s, 70s, 60s and 50s and even earlier than this, continue to inspire today's designers. Even people (A9) ... in producing top fashion labels (A10) ... back to the clothes of the past. They often find their best ideas in things (A11) ... by the young people from previous generations, and reproduce these rather than creating something completely new. This means that if a style looked good and was popular before, there is every (A12) ... that it will be again. So take a look at photos of your parents or grandparents when they were your age. They might give you some ideas for your own wardrobe!""", ['referred|connected|focused|related|involved', 'see|watch|look|consider|notice', 'dressed|carried|approached|worn|appeared', 'danger|risk|chance|option|luck'])
add(2024, 'A', 13, 'X: Excuse me, have you got change for 5 pounds?\nY: ...\nX: Thanks, I need it for the parking meter (счётчик платы за парковку).', ["I'm afraid I do.", 'Certainly, here you are.', 'Sorry to trouble you.', 'Yes, I am, actually.', "I don't care if I do."], 'Complete the mini-dialogue with the reply that fits.')
add(2024, 'A', 14, 'Would you like me to carry that shopping for you?', ['May I do it a bit later?', "That's very kind of you.", 'No, go ahead.', "Thanks a lot, you've been really helpful.", "Sorry, but I can't do it now."], 'Choose the reply that fits the situation.')
ART = """Robert Taylor talks about his new art show
§ 1. Like all children, I was always getting myself and the kitchen table in a mess when I first took an interest in painting. Unlike many kids, who give up activities like art for other subjects when they go through school, I continued painting throughout my childhood. Now, after years of enjoyment, I've finally taken the scary decision to show off some of my favourite pieces of work by holding an exhibition at Glebe Street library. Inviting people to see my work is a new idea and one which I'm looking forward to.
§ 2. I've never had any formal art training. When I was trying to decide what I should study at university, art as a subject never entered my head. I always thought my parents wanted me to follow a subject that would be useful when I was looking for a job, so I ended up taking a business course. Looking back, my parents would probably have supported me whatever my decision, but I decided to do what I thought was best for everyone.
§ 3. And during my time at university, I rarely did much in the way of painting. It wouldn't have been easy to paint anyway as I lived in university accommodation and had very little space. I kept an interest in art though and visited local exhibitions whenever I could, but that was about it. It was later in my thirties while I was working that I discovered my love of the activity again. Since then I've made a point of spending at least one evening a week painting.
§ 4. However, my works have only ever been seen by trusted friends and relatives. They've always given me plenty of support and encouraged me to continue with my art. But I've always wondered what people who I didn't know would think, people who could give me an honest opinion of my ability. The library have been very helpful and offered me a room for the show. They've asked me to supply questionnaires about the event and I've included a section for visitors' comments about the works. I'm very much looking forward to reading these opinions."""
for n, question, options in [
    (15, 'What does Robert say about art?', 'Children usually continue doing it at school.|He had to give it up to do other subjects.|The thought of showing off his work is a little frightening.|He has often thought about letting people see his work.'),
    (16, 'When deciding what to study at university ...', "Robert didn't consider doing art.|his parents didn't want him to study art.|he thought he would need a job while he was studying.|Robert understood correctly what his parents wanted him to do."),
    (17, 'What happened while Robert was at university?', "He didn't do any painting.|He was still keen on art.|He discovered his love of painting again.|He painted at least one evening a week."),
    (18, 'Robert is holding the exhibition because ...', 'his friends and relatives encouraged him to do this.|the library asked him to.|he is interested in getting opinions from friends and relatives.|he wants to know what strangers think of his work.'),
]:
    add(2024, 'A', n, ART + '\n\n' + question, options.split('|'))
for n in range(1, 4):
    add(2024, 'B', n, """Technology has contributed (B1) ... education. For one thing, word processing helps you to write much faster and more neatly, instead of using messy handwriting. And spell-checks correct your work for you, which is good because then it's of a higher standard. In the world of work, computers have made job searching much easier. You can actually apply for a job directly on a company's website. And thanks (B2) ... social media, you can connect with employers in ways that were never possible before. For me, that's what it's all about – providing you (B3) ... options.""", instruction='Fill the indicated gap with ONE preposition.')
for n, sentence in enumerate([
    'Fewer ... 50 students applied for the course.',
    'The news ... shared on social media by individuals and news outlets nowadays.',
    "No matter ... busy I am, I'll make time for my family.",
    "It's really important to rely on your common ... in unfamiliar situations.\nIt doesn't make ... to buy such an expensive dress when it'll be out of fashion next year.",
    "The athlete hopes to ... a record in the upcoming track and field event.\nIt's time to take a ... and have a cup of tea in the afternoon.",
], 4):
    add(2024, 'B', n, sentence, instruction=('Fill the gap with ONE word (at most 15 characters).' if n <= 6 else 'Fill BOTH gaps with the SAME word. Write it only once.'))
extra(2024, 9, [
    'As a child grows up, should his parents sit by himself and do nothing if he makes bad choices',
    'or does something wrong? Or should parents can make sure their children make the right',
    "choices? Though parents may consider themselves wiser enough, do they always know what's",
    'best? While we frequently see programmes on TV about lots teenagers and their uncontrolled',
    'behaviour, according to scientists, the average family that actually has a much more peaceful',
    'experience. Many teenagers get on well with their parents, who find few time to listen to them.',
    'Teenagers often improve their relationship with their parents as they have grow up, taking',
    'on their ideas and values. While the teenage years may sometimes to be stressful for the',
    'whole family, this is certainly does not always the case. Parents often take pleasure in their',
    "children's achievements, and each teenagers continue to find the support in their parents.",
])
forms(2024, 19, 4, """I've spent years studying happiness and one of the most significant (B19) ... (CONCLUDE) is that there is hardly any correlation between the circumstances of people's lives and how happy they are. A moment's reflection should make this obvious. We all know people who have a (B20) ... (RELATE) easy life, yet are always miserable, and others who have suffered many (B21) ... (HARD) but remain essentially happy. The first secret is gratitude. Ungrateful people cannot be happy. We have a tendency to think that being unhappy (B22) ... (ABLE) people complain. It is truer to say that finding cause for complaining leads to one becoming unhappy. The second secret is the realisation that happiness is a by-product of activities that give our lives meaning.""")
