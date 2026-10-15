"""Yearly author sets: completeness, unique content and exact-answer regression gates."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "content_src"))
import kit
import periods
import policy


def annual_tasks():
    return [task for name in periods.modules() for task in periods.load(name).tasks()]


class YearlySets(unittest.TestCase):
    def test_all_six_sets_are_complete(self):
        tasks = annual_tasks()
        self.assertEqual(periods.RELEASED_PERIODS, tuple(range(2021, 2027)))
        self.assertEqual(periods.PLANNED_PERIODS, ())
        self.assertEqual(len(tasks), 240)
        periods.validate_variants(tasks)
        for task in tasks:
            self.assertEqual(kit.verify(task), [], task['id'])

    def test_new_sets_are_not_relabelled_2026(self):
        tasks = annual_tasks()
        self.assertEqual(len({task['text'] for task in tasks}), 240)
        self.assertEqual(len({task['id'] for task in tasks}), 240)
        for year in range(2021, 2026):
            selected = [task for task in tasks if task['year'] == year]
            self.assertEqual(len(selected), 40)
            self.assertTrue(all(task['source'] == 'authored' for task in selected))
            self.assertEqual({task['type'] for task in selected}, {'choice', 'gap', 'extra', 'form'})

    def test_every_choice_has_four_rejected_decoys(self):
        for task in annual_tasks():
            if task['year'] < 2026 and task['type'] == 'choice':
                for decoy in task['options'][1:]:
                    self.assertFalse(policy.check(task, decoy)['ok'], (task['id'], decoy))

    def test_extra_word_is_an_exact_token_and_deletion_is_the_only_operation(self):
        for task in annual_tasks():
            if task['year'] < 2026 and task['type'] == 'extra':
                word = task['answer']['value']
                self.assertIn(word, task['text'].rstrip('.').split(), task['id'])
                for wrong in ('', word + 's', word + ' extra', 'extra ' + word):
                    self.assertFalse(policy.check(task, wrong)['ok'], (task['id'], wrong))
        # Gold regressions: deleting the answer, not replacing a faulty preposition.
        expected = {
            'en-2021-B9': 'This road is narrower than the main street.',
            'en-2022-B9': 'The audience listened carefully.',
            'en-2023-B14': 'Despite the wind, the ferry sailed on time.',
            'en-2024-B15': 'The speaker emphasised the main problem.',
            'en-2025-B15': 'We attended the concert on Saturday.',
        }
        by_id = {task['id']: task for task in annual_tasks()}
        for task_id, sentence in expected.items():
            task = by_id[task_id]
            words = task['text'].split()
            words.remove(task['answer']['value'])
            self.assertEqual(' '.join(words), sentence)

    def test_written_gold_answers_and_negative_forms(self):
        by_id = {task['id']: task for task in annual_tasks()}
        gold = {
            'en-2021-B19': ('decision', 'decide'),
            'en-2022-B20': ('dangerous', 'danger'),
            'en-2023-B21': ('patiently', 'patient'),
            'en-2024-B20': ('excited', 'exciting'),
            'en-2025-B19': ('difference', 'different'),
            'en-2025-B5': ('better', 'best'),
        }
        for task_id, (right, wrong) in gold.items():
            task = by_id[task_id]
            self.assertEqual(task['answer']['value'], right)
            self.assertTrue(policy.check(task, right)['ok'], task_id)
            for answer in (wrong, right + ' extra', 'extra ' + right, ''):
                self.assertFalse(policy.check(task, answer)['ok'], (task_id, answer))
        self.assertTrue(policy.check(by_id['en-2021-B1'], 'upon')['ok'])

    def test_missing_task_fails(self):
        with self.assertRaises(ValueError):
            periods.validate_variants(annual_tasks()[:-1])

    def test_missing_year_fails(self):
        with self.assertRaises(ValueError):
            periods.validate_variants([t for t in annual_tasks() if t['year'] != 2023])

    def test_duplicate_number_fails(self):
        tasks = deepcopy(annual_tasks())
        tasks[1]['n'] = 1
        with self.assertRaises(ValueError):
            periods.validate_variants(tasks)

    def test_duplicate_id_or_text_fails(self):
        for field in ('id', 'text'):
            tasks = deepcopy(annual_tasks())
            tasks[1][field] = tasks[0][field]
            with self.assertRaises(ValueError):
                periods.validate_variants(tasks)

    def test_wrong_source_part_or_year_fails(self):
        for field, wrong in [('source', 'official'), ('part', 'B'), ('year', 2020)]:
            tasks = deepcopy(annual_tasks())
            tasks[0][field] = wrong
            with self.assertRaises(ValueError):
                periods.validate_variants(tasks)


if __name__ == '__main__':
    unittest.main()
