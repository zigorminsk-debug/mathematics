"""Offline archive: source integrity, historical structure, printed-key regressions.

Only standard library; source PDF/OCR/download access is never needed by CI.
The key proof images are repository audit material, not shipped exam pages.
"""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'content_src'))
import archives
import archive_text
import re
import kit
import policy


class Archives(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = archives.payload()
        cls.by_id = {t['id']: t for t in cls.data['tasks']}

    def test_five_complete_first_variants(self):
        self.assertEqual(len(self.data['tasks']), 216)
        self.assertEqual(len(self.data['sourcePages']), 18)
        self.assertEqual(len(self.data['variants']), 5)
        for source in self.data['variants']:
            tasks = [self.by_id[id] for id in source['taskIds']]
            year = source['fileYear']
            self.assertEqual(source['parts'], {'A': 30, 'B': 18} if year < 2023 else {'A': 18, 'B': 22})
            self.assertEqual(len(tasks), sum(source['parts'].values()))
            for part in ('A', 'B'):
                section = [t for t in tasks if t['part'] == part]
                self.assertEqual([t['n'] for t in section], list(range(1, source['parts'][part] + 1)))
            self.assertTrue(all('year' not in t and t['source'] == 'archive' for t in tasks))

    def test_every_task_has_complete_checked_plain_text(self):
        self.assertEqual(set(archive_text.TEXT), set(self.by_id))
        for task in self.data['tasks']:
            with self.subTest(task=task['id']):
                self.assertTrue(task['transcriptionReviewed'])
                self.assertGreater(len(task['conditionText']), 50)
                self.assertNotIn('Original task', task['text'])
                self.assertNotIn('scanned condition required', task['text'])
                if task['type'] == 'choice':
                    self.assertEqual(set(task['optionLabels']), set(task['options']))
                    for number, label in task['optionLabels'].items():
                        self.assertIn(f'{number}) {label}', task['text'])
                elif task['type'] == 'extra':
                    line = next(line for line in archive_text.TEXT[task['id']]['condition'].splitlines() if line.startswith(f"B{task['n']}. "))
                    self.assertRegex(line.lower(), r"\b" + re.escape(task['answer']['value']) + r"\b")
                elif task['type'] == 'form':
                    self.assertRegex(task['given'], r'^[A-Z]+$')
                    self.assertIn('(' + task['given'] + ')', task['conditionText'])

    def test_shared_context_cross_page_and_intentional_errors_are_preserved(self):
        for year, word in ((2021, 'Lonely Planet'), (2022, 'Pen Hadow'),
                           (2023, 'Freshly'), (2024, 'Glebe Street'), (2025, 'Harry Moore')):
            last_a = 30 if year < 2023 else 18
            self.assertIn(word, self.by_id[f'en-archive-{year}-v1-A{last_a}']['conditionText'])
        self.assertIn('five hundreds years', self.by_id['en-archive-2025-v1-A8']['text'])
        self.assertIn('B12. biggest user group. Sheila', self.by_id['en-archive-2025-v1-B12']['text'])
        self.assertIn('CONVENIENCE', self.by_id['en-archive-2022-v1-B5']['text'])
        self.assertIn('which names', self.by_id['en-archive-2021-v1-A15']['text'])

    def test_missing_or_incomplete_transcription_fails_closed(self):
        for bad in ({}, {**archive_text.TEXT, 'en-archive-2025-v1-A1': {'condition':'bad', 'reviewed':False}}):
            with patch.object(archives, 'TEXT', bad), self.assertRaises(ValueError):
                archives.payload()

    def test_original_key_column_regressions(self):
        # Independent transcription checkpoints from the proof photographs.
        expected = {
            2021: ('2', '3', 'scientific', 'neither', 'take'),
            2022: ('5', '3', 'solution', "else's", 'take'),
            2023: ('3', '2', 'for', 'time', 'make'),
            2024: ('1', '4', 'to', 'hardships', 'enables'),
            2025: ('5', '3', 'at', 'entirely', 'requirements'),
        }
        for year, values in expected.items():
            end_a, end_b = (30, 18) if year < 2023 else (18, 22)
            ids = [f'A1', f'A{end_a}', 'B1', f'B{end_b-1}', f'B{end_b}']
            for number, answer in zip(ids, values):
                task = self.by_id[f'en-archive-{year}-v1-{number}']
                self.assertEqual(task['answer']['value'], answer, task['id'])
                self.assertTrue(policy.check(task, answer)['ok'])

    def test_all_tasks_pass_contract_and_all_decoys_fail(self):
        for task in self.data['tasks']:
            self.assertEqual(kit.verify(task), [], task['id'])
            self.assertEqual(task['sourceKey'], task['accepted'], task['id'])
            self.assertFalse(policy.check(task, '')['ok'], task['id'])
            if task['type'] == 'choice':
                for option in task['options'][1:]:
                    self.assertFalse(policy.check(task, option)['ok'], task['id'])
            else:
                answer = task['answer']['value']
                for wrong in (answer + ' extra', 'extra ' + answer, answer + 's'):
                    self.assertFalse(policy.check(task, wrong)['ok'], (task['id'], wrong))

    def test_original_option_counts_no_fake_distractors(self):
        for year in range(2021, 2026):
            task = self.by_id[f'en-archive-{year}-v1-A{25 if year<2023 else 15}']
            self.assertEqual(set(task['options']), set('123' if year < 2023 else '1234'))
        authored = dict(task_id='test', topic='tenses', text='Which form ___?', answer='a',
                        options=['a', 'b', 'c'], correction={'ru':'x','en':'x'}, tags=['tenses.present_simple'])
        with self.assertRaises(ValueError):
            kit.choice(**authored)  # Authored sets still require five, not padded source choices.

    def test_only_printed_alternatives_and_required_apostrophe(self):
        prefer = self.by_id['en-archive-2025-v1-B2']
        for value in ('to', 'over'):
            self.assertTrue(policy.check(prefer, value)['ok'])
        for value in ('than', 'to over', 'over to'):
            self.assertFalse(policy.check(prefer, value)['ok'])
        inconveniences = self.by_id['en-archive-2022-v1-B5']
        self.assertEqual(inconveniences['accepted'], ['inconveniences', 'inconvenience'])
        possessive = self.by_id['en-archive-2022-v1-B17']
        self.assertTrue(policy.check(possessive, "else's")['ok'])
        self.assertFalse(policy.check(possessive, 'elses')['ok'])
        self.assertFalse(policy.check(possessive, 'else')['ok'])

    def test_source_images_are_safe_jpegs_with_verified_hashes(self):
        for id, page in self.data['sourcePages'].items():
            raw = base64.b64decode(page['data'].split(',', 1)[1], validate=True)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), page['sha256'], id)
            self.assertTrue(raw.startswith(b'\xff\xd8\xff'), id)
            self.assertGreaterEqual(page['width'], 1500)
        for task in self.data['tasks']:
            self.assertEqual(self.data['sourcePages'][task['sourcePage']]['sourceId'], task['archiveId'])

    def test_no_answer_key_photograph_in_exam_payload(self):
        for source in self.data['variants']:
            numbers = [self.data['sourcePages'][id]['pdfPage'] for id in source['pageIds']]
            self.assertNotIn(source['keyPdfPage'], numbers)
            self.assertEqual(set(source['pageIds']), {t['sourcePage'] for t in self.data['tasks'] if t['archiveId']==source['id']})
        for source in archives.manifest()['variants']:
            proof = Path(__file__).resolve().parents[1] / source['keyProofFile']
            self.assertEqual(hashlib.sha256(proof.read_bytes()).hexdigest(), source['keyProofSha256'])

    def test_2024_year_and_unstated_durations_are_not_invented(self):
        for source in self.data['variants']:
            year = source['fileYear']
            self.assertEqual(source['verifiedYear'], None if year == 2024 else year)
            self.assertEqual(source['minutes'], 120 if year in (2023, 2025) else None)
            if year == 2024:
                self.assertIn('filename', source['title']['en'])

    def test_unreviewed_source_or_key_cannot_publish(self):
        for field in ('reviewed', 'answerKeyReviewed'):
            data = deepcopy(archives.manifest())
            data['variants'][0][field] = False
            with patch.object(archives, 'manifest', return_value=data), self.assertRaises(ValueError):
                archives.payload()

    def test_changed_page_or_incomplete_key_cannot_publish(self):
        data = deepcopy(archives.manifest())
        data['variants'][0]['pages'][0]['sha256'] = 'bad hash'
        with patch.object(archives, 'manifest', return_value=data), self.assertRaises(ValueError):
            archives.payload()
        data = deepcopy(archives.manifest())
        data['variants'][0]['parts']['A'] -= 1
        with patch.object(archives, 'manifest', return_value=data), self.assertRaises(ValueError):
            archives.payload()


if __name__ == '__main__':
    unittest.main()
