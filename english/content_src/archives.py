"""Reviewed facsimiles from the user's Drive: one COMPLETE first variant per file.

No OCR draft is shipped as an English condition. The original question pages,
including reading passages and numbered/underlined fragments, are carried once
in bank.sourcePages. Tasks refer to them and are graded against the visually
reviewed printed key. Archives have separate IDs and never impersonate authored
sets or overwrite their statistics. 2024 is explicitly only a filename claim.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

import kit
from archive_text import TEXT

ROOT = Path(__file__).resolve().parent / 'archive'

# Topic guidance is authored by this app, not claimed to be in the printed key.
A_TAGS = {
    2021: ['tenses.present_perfect', 'tenses.past_continuous', 'tenses.past_continuous',
           'passive.past_simple', 'tenses.past_perfect', 'tenses.future_continuous',
           *['prepositions.collocation'] * 4, *['articles.definite'] * 3,
           'noun_adj_adv.participle_adjective', 'pronouns.possessive',
           *['gap_fill.collocation'] * 5, *['communication.replies'] * 4,
           *['communication.notice'] * 6],
    2022: ['tenses.present_perfect', 'passive.past_simple', 'tenses.past_perfect',
           'tenses.present_perfect_continuous', 'tenses.present_simple', 'passive.present_simple',
           *['prepositions.collocation'] * 4, *['articles.indefinite'] * 3,
           'noun_adj_adv.subject_verb', 'pronouns.possessive',
           *['gap_fill.collocation'] * 5, *['communication.replies'] * 4,
           *['communication.notice'] * 6],
    2023: ['tenses.present_perfect', 'tenses.present_simple', 'passive.present_simple',
           'tenses.future_continuous', 'noun_adj_adv.comparison', 'pronouns.numerals',
           'articles.geographical', 'articles.uncountable', *['gap_fill.collocation'] * 4,
           *['communication.replies'] * 2, *['communication.notice'] * 4],
    2024: ['tenses.present_simple', 'tenses.past_continuous', 'passive.past_simple',
           'tenses.future_continuous', 'pronouns.quantifiers', 'articles.zero',
           'pronouns.conjunctions', 'pronouns.conjunctions', *['gap_fill.collocation'] * 4,
           *['communication.replies'] * 2, *['communication.notice'] * 4],
    2025: ['passive.past_simple', 'tenses.present_simple', 'tenses.present_continuous',
           'passive.present_simple', 'articles.uncountable', 'pronouns.conjunctions',
           'pronouns.quantifiers', 'pronouns.numerals', *['gap_fill.collocation'] * 4,
           *['communication.replies'] * 2, *['communication.notice'] * 4],
}

# Exact transformations/collocations are written out; no regex/keyword grading.
B_NOTES = {
    2021: ['SCIENCE → scientific: adjective before name.', 'In addition to is a fixed expression.',
           'RAPID → rapidly: adverb modifying moving.', 'PREDICT → unpredictable: negative adjective describing the flight.',
           'CHARACTER → characteristics: plural noun after these.', 'THREAT → threaten: verb coordinated with generate.',
           *['Delete only the token specified in the printed key; read the corrected line in the whole passage.'] * 10,
           'Neither refers to neither of the two drinks offered.', 'Take into account is the fixed collocation.'],
    2022: ['SOLVE → solution: noun after perfect.', 'DANGER → endangered: species at risk.',
           'FORGET → unforgettable: memorable vacations.', 'REGULAR → regularly: adverb modifying patrols.',
           'The printed key explicitly permits both inconvenience and inconveniences.', 'RESPONSE → responsible: adjective describing holiday.',
           *['Delete only the token specified in the printed key; read the corrected line in the whole passage.'] * 10,
           "Someone else's: else takes the possessive apostrophe-s. The apostrophe is required.",
           'Take after is the phrasal verb for resembling a relative.'],
    2023: ['A cure for a disease.', 'Thankful for advice.', 'Divide into teams.', 'Neither of the two dresses suits you.',
           'Past passive with plural students: were informed.', 'Whose introduces the relative clause about the species’ habitat.',
           'DECIDE → decision: noun after a difficult.', 'RELIABLE → unreliable: a person children cannot count on.',
           'EXTREME → extremely: adverb before determined.', 'STRENGTH → strengthen: verb after need to.',
           *['Delete only the token specified in the printed key; read the corrected line in the whole passage.'] * 10,
           'From time to time and it is time to ... share time.', 'Make use of and make a wish share make.'],
    2024: ['Contribute to education.', 'Thanks to social media.', 'Provide someone with options.',
           'Fewer than introduces a numerical comparison.', 'Uncountable news takes is; passive is shared.',
           'No matter how busy introduces a concession about degree.', 'Common sense and make sense share sense.',
           'Break a record and take a break share break.',
           *['Delete only the token specified in the printed key; read the corrected line in the whole passage.'] * 10,
           'CONCLUDE → conclusions: plural after one of the most significant.', 'RELATE → relatively: adverb before easy.',
           'HARD → hardships: plural countable noun after many.', 'ABLE → enables: singular verb with unhappiness.'],
    2025: ['At risk is the fixed expression.', 'The printed key explicitly accepts prefer ... to and prefer ... over.',
           'Pouring with rain is the fixed expression.', 'Why not + bare infinitive makes a suggestion.',
           'Past question: How did you use to ...?', 'Negative rarely takes a positive question tag: do they?',
           'Have taken turns and was taken into consideration share taken.', 'Fell in love and fell asleep share fell.',
           *['Delete only the token specified in the printed key; read the corrected line in the whole passage.'] * 10,
           'SIMPLE → simplifies: singular Present Simple verb with technology.', 'DISASTER → disastrous: adjective before consequences.',
           'ENTIRE → entirely: adverb before focused.', 'REQUIRE → requirements: plural noun with include.'],
}
B_NOTES_RU = {
    2021: ['SCIENCE → scientific: признак перед name.', 'In addition to — устойчивое сочетание.',
           'RAPID → rapidly: наречие перед moving.', 'PREDICT → unpredictable: непредсказуемый полёт.',
           'CHARACTER → characteristics: множественное число после these.', 'THREAT → threaten: глагол, однородный с generate.',
           *['Удалите только слово из печатного ключа; проверьте восстановленную строку в контексте всего текста.'] * 10,
           'Neither — ни один из двух предложенных напитков.', 'Take into account — принимать во внимание.'],
    2022: ['SOLVE → solution: существительное после perfect.', 'DANGER → endangered: виды под угрозой исчезновения.',
           'FORGET → unforgettable: незабываемый отпуск.', 'REGULAR → regularly: наречие при patrols.',
           'В печатном ключе явно разрешены inconvenience и inconveniences.', 'RESPONSE → responsible: признак перед holiday.',
           *['Удалите только слово из печатного ключа; проверьте восстановленную строку в контексте всего текста.'] * 10,
           'Someone else’s — притяжательная форма else с обязательным апострофом.', 'Take after — походить на родственника.'],
    2023: ['A cure for — лекарство от заболевания.', 'Thankful for — благодарен за совет.', 'Divide into — разделить на команды.',
           'Neither — ни одно из двух платьев.', 'Прошедший пассив с students: were informed.', 'Whose связывает вид с его средой обитания.',
           'DECIDE → decision: существительное после a difficult.', 'RELIABLE → unreliable: на такого человека нельзя положиться.',
           'EXTREME → extremely: наречие перед determined.', 'STRENGTH → strengthen: глагол после need to.',
           *['Удалите только слово из печатного ключа; проверьте восстановленную строку в контексте всего текста.'] * 10,
           'From time to time и it is time to ... объединяет time.', 'Make use of и make a wish объединяет make.'],
    2024: ['Contribute to — вносить вклад в образование.', 'Thanks to — благодаря социальным сетям.', 'Provide with — предоставлять варианты.',
           'Fewer than — числовое сравнение.', 'News неисчисляемое: is shared.', 'No matter how busy — как бы занят ни был.',
           'Common sense и make sense объединяет sense.', 'Break a record и take a break объединяет break.',
           *['Удалите только слово из печатного ключа; проверьте восстановленную строку в контексте всего текста.'] * 10,
           'CONCLUDE → conclusions: множественное число после one of.', 'RELATE → relatively: наречие перед easy.',
           'HARD → hardships: множественное число после many.', 'ABLE → enables: глагол с единственным unhappiness.'],
    2025: ['At risk — под угрозой.', 'Печатный ключ явно разрешает prefer ... to и prefer ... over.',
           'Pouring with rain — льёт дождь.', 'Why not + инфинитив без to — предложение сделать что-то.',
           'Вопрос о прошлом: How did you use to ...?', 'Отрицательное rarely: положительный хвостик do they?',
           'Have taken turns и was taken into consideration объединяет taken.', 'Fell in love и fell asleep объединяет fell.',
           *['Удалите только слово из печатного ключа; проверьте восстановленную строку в контексте всего текста.'] * 10,
           'SIMPLE → simplifies: глагол с единственным technology.', 'DISASTER → disastrous: признак перед consequences.',
           'ENTIRE → entirely: наречие перед focused.', 'REQUIRE → requirements: множественное число с include.'],
}


def manifest():
    return json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))


def written_kind(year, n):
    if year < 2023:
        return 'form' if n <= 6 else 'extra' if n <= 16 else 'translate'
    if year == 2023:
        return 'gap' if n <= 6 or n >= 21 else 'form' if n <= 10 else 'extra'
    return 'gap' if n <= 8 else 'extra' if n <= 18 else 'form'


def page_for(year, part, n):
    if year < 2023:
        return 5 if part == 'B' else 2 if n <= 13 else 3 if n <= 24 else 4
    if year == 2023:
        return 7 if part == 'B' or n >= 17 else 5 if n <= 12 else 6
    if year == 2024:
        return 4 if part == 'B' or n >= 18 else 2 if n <= 12 else 3
    return (8 if n <= 8 else 9) if part == 'B' else 6 if n <= 10 else 7 if n <= 14 else 8


def payload():
    data = manifest()
    tasks, pages, variants = [], {}, []
    for source in data['variants']:
        key, year = source['id'], source['fileYear']
        if not source['reviewed'] or not source['answerKeyReviewed']:
            raise ValueError(f'{key}: unreviewed source cannot ship')
        proof = ROOT.parent.parent / source['keyProofFile']
        if hashlib.sha256(proof.read_bytes()).hexdigest() != source['keyProofSha256']:
            raise ValueError(f'{key}: altered printed key proof')
        answers = json.loads((ROOT / key / 'answers.json').read_text(encoding='utf-8'))
        if {p: len(v) for p, v in answers.items()} != source['parts']:
            raise ValueError(f'{key}: incomplete printed key')
        for page in source['pages']:
            if page['pdfPage'] == source['keyPdfPage']:
                raise ValueError(f'{key}: answer-key page must not be included in exam pages')
            raw = (ROOT / page['file']).read_bytes()
            if not raw.startswith(b'\xff\xd8\xff') or hashlib.sha256(raw).hexdigest() != page['sha256']:
                raise ValueError(f"{key}: altered source page {page['id']}")
            pages[page['id']] = {'data': 'data:image/jpeg;base64,' + base64.b64encode(raw).decode('ascii'),
                                 'pdfPage': page['pdfPage'], 'sourceId': key,
                                 'sha256': page['sha256'], 'width': page['width'], 'height': page['height']}
        variant = {k: v for k, v in source.items() if k not in ('pages', 'keyProofFile', 'keyProofSha256')}
        variant['pageIds'] = [p['id'] for p in source['pages']]
        variant['taskIds'] = []
        variant['title'] = {
            'ru': f"{year} · {source['examType']} · вариант 1" + (' (год по имени файла)' if year == 2024 else ''),
            'en': f"{year} · {source['examType']} · variant 1" + (' (year from filename)' if year == 2024 else '')}
        for part in ('A', 'B'):
            for n, key_value in enumerate(answers[part], 1):
                task_id = f'en-archive-{year}-v1-{part}{n}'
                if part == 'A':
                    tag = A_TAGS[year][n - 1]
                    if tag.startswith('tenses.'): tag = 'tenses.context'
                    if tag == 'communication.notice': tag = 'communication.reading'
                    topic = {'pronouns': 'pronouns_numerals'}.get(tag.split('.')[0], tag.split('.')[0])
                    count = 3 if year < 2023 and n >= 25 else 4 if year >= 2023 and n >= 15 else 5
                    if int(key_value) not in range(1, count + 1):
                        raise ValueError(f'{task_id}: key exceeds printed option count')
                    values = [key_value, *[str(i) for i in range(1, count + 1) if str(i) != key_value]]
                    task = kit.choice(task_id, topic=topic, text=f'Original task {part}{n}: which numbered option is correct?',
                                      answer=key_value, options=values, tags=[tag], source='archive',
                                      correction={'ru': f'По печатному ключу: вариант № {key_value}. Сопоставьте этот вариант с исходным контекстом и правилом ниже.',
                                                  'en': f'Printed key: option {key_value}. Compare this option with the original context and the rule below.'})
                    task['instruction'] = {'ru': 'Выберите номер ответа на исходной странице (нумерация сохранена).',
                                           'en': 'Choose the option number on the original page (original numbering preserved).'}
                else:
                    kind = written_kind(year, n)
                    topic = {'form': 'word_formation', 'extra': 'extra_word', 'gap': 'gap_fill', 'translate': 'communication'}[kind]
                    tag = {'form': 'word_formation.suffix', 'extra': 'extra_word.redundant',
                           'gap': 'gap_fill.context', 'translate': 'communication.translation'}[kind]
                    # suffix is a generic generator tag, but not in the mistake catalogue: use the noun/adjective group.
                    if kind == 'form': tag = 'word_formation.context'
                    text = (f'Переведите фрагмент в исходном задании B{n}.' if kind == 'translate' else
                            f'Original task B{n}: type the word required by the printed instruction.')
                    task = kit.typed(task_id, topic=topic, kind=kind, text=text,
                                     answer=key_value[0], accepted=key_value[1:], tags=[tag], source='archive',
                                     policy_overrides={'apostrophe': 'required'},
                                     correction={'ru': f"Печатный ключ: {' / '.join(key_value)}. {B_NOTES_RU[year][n-1]}",
                                                 'en': f"Printed key: {' / '.join(key_value)}. {B_NOTES[year][n-1]}"})
                task.update({'part': part, 'n': n, 'archiveId': key, 'archiveYear': year,
                             'sourcePage': f'{key}-p{page_for(year, part, n)}', 'sourceNumber': f'{part}{n}',
                             'sourceUrl': source['url'], 'sourceKey': key_value if isinstance(key_value, list) else [key_value],
                             'sourceKeyPdfPage': source['keyPdfPage'], 'sourceKeyColumn': 1})
                transcript = TEXT.get(task_id)
                if not transcript or transcript.get('reviewed') is not True or not transcript.get('condition', '').strip():
                    raise ValueError(f'{task_id}: missing or unreviewed transcription')
                instruction = transcript.get('instruction', 'Choose one of the offered answers.')
                task['conditionText'] = f'{part}{n}. {instruction}\n\n{transcript["condition"]}'
                task['text'] = task['conditionText']
                task['transcriptionReviewed'] = True
                task['transcriptionSha256'] = hashlib.sha256(json.dumps(transcript, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
                if part == 'A':
                    labels = transcript.get('options', {})
                    if set(labels) != set(task['options']) or not all(isinstance(v, str) and v.strip() for v in labels.values()):
                        raise ValueError(f'{task_id}: incomplete printed option transcription')
                    task['optionLabels'] = labels
                    # Old APK/EXE readers still receive a complete solvable text.
                    task['text'] += '\n\n' + '\n'.join(f'{i}) {labels[i]}' for i in sorted(labels, key=int))
                elif kind == 'form':
                    match = re.search(rf'\(B{n}\) \.\.\. \(([A-Z]+)\)', transcript['condition'])
                    if match is None:
                        match = re.search(r'\.\.\. \(([A-Z]+)\)', transcript['condition'])
                    if not match:
                        raise ValueError(f'{task_id}: missing word-formation stem')
                    task['given'] = match.group(1)
                task['instruction'] = {'ru': 'Выполните указанное задание. Исходная нумерация сохранена.',
                                       'en': 'Complete the indicated task. Original numbering is preserved.'}
                if task['sourcePage'] not in pages:
                    raise ValueError(f'{task_id}: missing original condition')
                variant['taskIds'].append(task_id)
                tasks.append(task)
        variants.append(variant)
    if set(TEXT) != {task['id'] for task in tasks}:
        raise ValueError('Orphan or missing archive transcriptions')
    return {'tasks': tasks, 'sourcePages': pages, 'variants': variants}
