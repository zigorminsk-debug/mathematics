"""Content gates: blueprint, rule links, never-translated material and independent
derivations that do not trust the generator (reconstruction, counting, rules)."""
from collections import Counter
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content_src"))
sys.path.insert(0, str(ROOT / "tools"))
import build_content as build  # noqa: E402
import generate  # noqa: E402
import kit  # noqa: E402
import periods  # noqa: E402
import pools_language as PL  # noqa: E402
import pools_punctuation as PP  # noqa: E402
import rules  # noqa: E402
import texts as TX  # noqa: E402
import ui_strings  # noqa: E402

VOWELS = "аеёиоуыэюя"


def quiet(function, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return function(*args)


class BankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank, cls.analogous = quiet(build.build_tasks)

    def test_six_variants_follow_the_2026_specification(self):
        self.assertEqual(240, len(self.bank))
        spec = periods.SPECIFICATION
        self.assertEqual((40, {"A": 18, "B": 22}, 120), (spec["tasks"], spec["parts"], spec["minutes"]))
        self.assertTrue(spec["url"].startswith("https://rikc.by/"))
        quotas = {key: count for key, (_, count) in kit.SECTIONS.items()}
        self.assertEqual({"orthography": 13, "punctuation": 9, "lexis": 2, "speech": 3, "phonetics": 1, "word": 2,
                          "morphology": 4, "syntax": 3, "text": 3}, quotas)
        for year in periods.years():
            tasks = [t for t in self.bank if t["year"] == year]
            self.assertEqual(Counter(quotas), Counter(t["section"] for t in tasks))
            self.assertTrue(all(t["check"]["type"] == "multi" and t["check"]["options"] == 5 for t in tasks if t["part"] == "A"))

    def test_math_structure_is_not_inherited(self):
        blob = json.dumps(periods.payload(), ensure_ascii=False)
        self.assertNotIn("180", blob)
        self.assertNotIn("12B", blob)
        self.assertIn("120", blob)

    def test_variants_are_labelled_authored_not_rikz(self):
        for period in periods.PERIODS:
            self.assertIn("авторский", period["label"]["ru"])
        self.assertIn("не официальные материалы РИКЗ", periods.DISCLAIMER["ru"])

    def test_every_rule_has_concrete_analogs(self):
        per_rule = Counter(t["rule"] for t in self.analogous)
        for rule in kit.RULES:
            self.assertGreaterEqual(per_rule[rule], 3, rule)
        for task in self.bank + self.analogous:
            self.assertIn(task["rule"], task["rules"])
            if "itemRules" in task:
                self.assertEqual(len(task["items"]), len(task["itemRules"]))

    def test_russian_material_is_never_translated(self):
        for task in self.bank + self.analogous:
            for field in ("text", "items"):
                value = task.get(field)
                if value is not None:
                    self.assertFalse(isinstance(value, dict), f"{task['id']}.{field} must not be bilingual")
            self.assertNotEqual(task["instruction"]["ru"], task["instruction"]["en"])
            self.assertRegex(task["instruction"]["ru"], "[А-Яа-яЁё]")

    def test_mutations_are_rejected(self):
        task = deepcopy(self.bank[0])
        task["items"] = {"ru": task["items"], "en": task["items"]}
        with self.assertRaises(ValueError):
            kit.validate_task(task)
        task = deepcopy(self.bank[0])
        task["solution"]["en"].append("untranslated")
        with self.assertRaises(ValueError):
            kit.validate_task(task)
        task = deepcopy(self.bank[0])
        task["rule"] = "missing-rule"
        with self.assertRaises(ValueError):
            kit.validate_task(task)
        task = deepcopy(self.bank[0])
        task["check"]["answer"] = [1, 2, 3, 4, 5]
        with self.assertRaises(ValueError):
            kit.validate_task(task)
        broken = [t for t in self.bank if not (t["year"] == 2026 and t["part"] == "B" and t["n"] == 22)]
        with self.assertRaises(SystemExit):
            build.check_variants(broken)

    def test_answers_derive_from_material(self):
        for task in self.bank:
            if task["check"]["type"] in ("multi", "numbers") and task.get("items") and task.get("itemRules"):
                solution = "\n".join(task["solution"]["ru"])
                for index in task["check"]["answer"]:
                    self.assertIn(f"{index}) ", solution)


class MaterialTests(unittest.TestCase):
    def test_numbered_sentences_rebuild_exactly(self):
        for text, commas, correct, notes_ru, notes_en in PP.NUMBERED:
            places = [int(n) for n in re.findall(r"\((\d+)\)", text)]
            self.assertEqual(list(range(1, len(places) + 1)), places)
            self.assertTrue(set(commas) <= set(places))
            rebuilt = re.sub(r"\s*\((\d+)\)\s*", lambda m: ", " if int(m.group(1)) in commas else " ", text)
            self.assertEqual(correct, rebuilt, text)
            self.assertEqual(len(notes_ru), len(notes_en))

    def test_mark_items_restore_their_correct_sentence(self):
        for pool_name in PP.MARK:
            for item in generate.mark_items(pool_name):
                self.assertNotIn("{", item["display"] + item["correct"])
                if item["marks"]:
                    self.assertNotEqual(item["display"], item["correct"])
                else:
                    self.assertEqual(item["display"], item["correct"])

    def test_bracket_category_is_derived(self):
        seen = Counter()
        for pool_name in ("ne-parts", "hyphen", "prep-conj"):
            for item in generate.bracket_items(pool_name):
                seen[item["category"]] += 1
                self.assertNotIn("(", item["corrected"])
                self.assertEqual(item["category"] == "separate", " " in item["full"])
                self.assertEqual(item["category"] == "hyphen", "-" in item["full"])
        self.assertTrue(all(seen[key] >= 10 for key in ("solid", "separate", "hyphen")))

    def test_transcriptions_agree_with_the_e_yo_yu_ya_rule(self):
        for word, sounds in PL.PHONETICS:
            tokens = sounds.split()
            expected_j = len(generate.two_sound_letters(word)) + word.count("й")
            self.assertEqual(expected_j, tokens.count("й'"), word)
            self.assertFalse(any(token in ("ь", "ъ") for token in tokens), word)
            self.assertEqual(sum(1 for c in word if c in VOWELS), sum(1 for t in tokens if t in "аоуыиэ"), word)

    def test_stress_marks_are_single_and_on_vowels(self):
        for stressed in PL.STRESS:
            self.assertEqual(1, stressed.count("\u0301"), stressed)
            self.assertIn(stressed[stressed.index("\u0301") - 1], VOWELS, stressed)
            self.assertGreaterEqual(generate.syllable(stressed), 1)
            self.assertNotIn("ё", stressed)

    def test_texts_are_fully_annotated(self):
        for text in TX.TEXTS:
            self.assertEqual(len(text["sentences"]), len(text["links"]))
            self.assertEqual([], text["links"][0])
            for links in text["links"]:
                self.assertTrue(set(links) <= set(TX.MEANS))
            for key in ("statements", "subtopics"):
                truths = sum(1 for _, truth in text[key] if truth)
                self.assertTrue(2 <= truths <= 4, (text["id"], key))
            self.assertIn(text["style"], TX.STYLES)
            self.assertIn(text["type"], TX.TYPES)
        self.assertEqual(set(TX.VARIANT_TEXTS), set(periods.years()))

    def test_paronym_sets_have_one_capitalised_error(self):
        for sentences, wrong, answer, pair_ru, pair_en in PL.PARONYM_SETS:
            self.assertEqual(4, len(sentences))
            self.assertTrue(1 <= wrong <= 4)
            for sentence in sentences:
                self.assertEqual(1, len(re.findall(r"\b[А-ЯЁ]{2,}\b", sentence)), sentence)
            self.assertNotIn(answer.upper(), sentences[wrong - 1])

    def test_statement_fixes_differ(self):
        for text, fix, code in PP.STATEMENTS:
            self.assertEqual(fix is None, code.startswith("ok-"))
            if fix:
                self.assertNotEqual(text, fix)


class CardsAndInterfaceTests(unittest.TestCase):
    def test_cards_are_complete_and_reachable(self):
        lessons = rules.lessons()
        self.assertEqual(set(kit.RULES), set(lessons))
        study = rules.study()
        self.assertEqual(set(lessons), {rid for entry in study.values() for rid in entry["lessons"]})
        reference = rules.reference()
        self.assertEqual(set(lessons), {item["rule"] for group in reference["groups"] for item in group["items"]})
        for lesson in lessons.values():
            self.assertGreaterEqual(len(lesson["everyday"]["ru"]), 2)
            self.assertTrue(lesson["correct"] and lesson["wrong"] and lesson["sources"])

    def test_card_mutations_are_rejected(self):
        broken = deepcopy(rules.CARDS)
        broken["tsya"]["everyday"] = (["коротко"], ["short"])
        with patch.object(rules, "CARDS", broken), self.assertRaises(ValueError):
            rules.lessons()
        broken = deepcopy(rules.CARDS)
        broken["tsya"]["sources"] = ["unknown-source"]
        with patch.object(rules, "CARDS", broken), self.assertRaises(ValueError):
            rules.lessons()

    def test_every_interface_key_used_by_the_app_exists(self):
        app = (ROOT / "webapp/app.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\bt\('([a-z_]+)'", app))
        strings = ui_strings.payload()
        self.assertFalse(used - set(strings), sorted(used - set(strings)))

    def test_no_mathematics_leftovers(self):
        texts = [(ROOT / "webapp" / name).read_text(encoding="utf-8") for name in ("app.js", "core.js", "index.html")]
        texts += [json.dumps(ui_strings.payload(), ensure_ascii=False)]
        pattern = re.compile(r"калькулятор|calculator|CT\.math|plotter|\bформул[аыу]\b|\bformula\b|Математика\b|Maths Tutor",
                             re.IGNORECASE)
        for text in texts:
            self.assertIsNone(pattern.search(text.replace("Репетитором ЦТ: Математика", "")), pattern.search(text))
        for name in ("task_bank_2021.py", "templates.py", "formulas.py", "theory.py"):
            self.assertFalse((ROOT / "content_src" / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
