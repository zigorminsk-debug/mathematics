"""Контент физики: предмет, величины, разбор ответа и полнота банка.

Проверяется то, что нельзя проверить «на глаз»: каждый ответ части B — это
физическая величина с размерностью, каждая задача части A имеет ровно один
верный вариант из пяти, а банк не содержит следов другого предмета.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content_src"))
sys.path.insert(0, str(ROOT / "tools"))

import quantities as Q  # noqa: E402

DIST = ROOT / "dist" / "content"
TOPIC_ORDER = ["measurements", "kinematics", "dynamics", "workenergy", "statics",
               "molecular", "thermo", "electrostatics", "current", "magnetism",
               "oscillations", "optics", "quantum"]
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
#: Имена другого приложения/предмета. Физические слова («геометрическая
#: оптика», «логарифмическая шкала») сюда не попадают: они законны.
FOREIGN = ("mathemat", "ctmaths", "ctmathstutor")


def load(name: str) -> dict:
    path = DIST / f"{name}.json"
    if not path.exists():
        raise unittest.SkipTest("нет dist/content — запустите tools/build_content.py")
    return json.loads(path.read_text(encoding="utf-8"))


class Manifest(unittest.TestCase):
    """Манифест выпуска обязан называть предмет явно."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load("version")

    def test_subject_identity(self):
        self.assertEqual(self.manifest["subject"], "physics")
        self.assertEqual(self.manifest["package"], "by.ziv.ctphysics")
        self.assertEqual(self.manifest["app"], "CTPhysicsTutor")

    def test_counts_match_the_content(self):
        counts = self.manifest["counts"]
        bank = load("bank")["tasks"]
        analogous = load("analogous")["tasks"]
        self.assertEqual(counts["bank"], len(bank))
        self.assertEqual(counts["analogous"], len(analogous))
        self.assertEqual(counts["choice"], sum(1 for task in bank if task["answerType"] == "choice"))
        self.assertEqual(counts["quantity"], sum(1 for task in bank if task["answerType"] == "quantity"))
        self.assertEqual(counts["lessons"], len(load("topics")["lessons"]))
        self.assertEqual(counts["figures"], len(load("topics")["figures"]))

    def test_years_and_disclosure(self):
        self.assertEqual(list(self.manifest["years"]), YEARS)
        disclosure = self.manifest["disclosure"]
        # пользователь не должен принять авторские задания за официальные
        self.assertIn("авторск", disclosure["ru"].lower())
        self.assertIn("рикз", disclosure["ru"].lower())
        self.assertIn("authored", disclosure["en"].lower())
        self.assertIn("rikz", disclosure["en"].lower())


class Bank(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tasks = load("bank")["tasks"]

    def test_exam_structure(self):
        self.assertEqual(len(self.tasks), 180)
        for year in YEARS:
            part_a = [t for t in self.tasks if t["year"] == year and t["part"] == "A"]
            part_b = [t for t in self.tasks if t["year"] == year and t["part"] == "B"]
            self.assertEqual(len(part_a), 10, year)
            self.assertEqual(len(part_b), 20, year)
            self.assertEqual(sorted(t["n"] for t in part_a), list(range(1, 11)), year)
            self.assertEqual(sorted(t["n"] for t in part_b), list(range(1, 21)), year)

    def test_identifiers_and_topics(self):
        identifiers = [task["id"] for task in self.tasks]
        self.assertEqual(len(set(identifiers)), len(identifiers))
        for task in self.tasks:
            self.assertIn(task["topic"], TOPIC_ORDER, task["id"])
            self.assertIn(task["difficulty"], (1, 2, 3), task["id"])
            for lang in ("ru", "en"):
                self.assertTrue(task["text"][lang].strip(), f"{task['id']}.{lang}")
                self.assertTrue(task["solution"][lang], f"{task['id']}.{lang}")

    def test_part_a_has_exactly_one_correct_option_of_five(self):
        tested = 0
        for task in self.tasks:
            if task["part"] != "A":
                continue
            tested += 1
            self.assertEqual(task["answerType"], "choice", task["id"])
            for lang in ("ru", "en"):
                options = task["options"][lang]
                self.assertEqual(len(options), 5, task["id"])
                self.assertEqual(len(set(options)), 5, task["id"])
                self.assertEqual(options[0], task["answer"][lang], task["id"])
            reasons = task["distractors"]["ru"]
            self.assertEqual(len(reasons), 5, task["id"])
            self.assertIsNone(reasons[0], f"{task['id']}: у верного варианта нет ошибки")
            for reason in reasons[1:]:
                self.assertTrue(reason and reason.strip(), task["id"])
        self.assertEqual(tested, 60)

    def test_part_b_is_a_physical_quantity(self):
        tested = 0
        for task in self.tasks:
            if task["part"] != "B":
                continue
            tested += 1
            spec = task["spec"]
            self.assertIn(task["answerType"], ("quantity", "number"), task["id"])
            self.assertIn(spec["unitPolicy"], ("named", "optional", "required"), task["id"])
            dimension = Q.parse_dim(spec["dimension"])
            self.assertEqual(len(dimension.exps), 7, task["id"])
            self.assertIsNotNone(Q.unit_of(spec["unit"]), f"{task['id']}: {spec['unit']}")
            self.assertTrue("tolerance" in spec or "rounding" in spec,
                            f"{task['id']}: не задан допуск сравнения")
            for lang in ("ru", "en"):
                result = Q.check_answer(task["answer"][lang], spec)
                self.assertTrue(result.ok, f"{task['id']} ({lang}): {result.reason}")
        self.assertEqual(tested, 120)

    def test_given_data_is_bilingual_and_unit_bearing(self):
        for task in self.tasks:
            self.assertTrue(task["given"], task["id"])
            for entry in task["given"]:
                self.assertTrue(entry["value_ru"].strip() and entry["value_en"].strip(), task["id"])
                self.assertTrue(entry["symbol"].strip(), task["id"])
                # у безразмерной величины (например, коэффициента μ) единицы нет:
                # либо подпись есть, либо её нет ни в одном языке
                self.assertEqual(bool(entry["unit"]["ru"].strip()),
                                 bool(entry["unit"]["en"].strip()), task["id"])
                self.assertEqual(bool(entry["unit"]["ru"].strip()),
                                 bool(entry["unit_symbol"].strip()), task["id"])
                self.assertIsNotNone(Q.parse_number(entry["value_ru"]), task["id"])
                self.assertIsNotNone(Q.parse_number(entry["value_en"]), task["id"])

    def test_no_other_subject_leaked_into_the_texts(self):
        """Ни задание, ни подпись не должны говорить о другом предмете.

        Ссылка на репозиторий (``…/mathematics``) — это адрес исходников, а не
        содержимое курса, поэтому из проверки она исключается.
        """
        for name in ("bank", "analogous", "topics", "mistakes", "formulas"):
            text = json.dumps(load(name), ensure_ascii=False).lower()
            text = text.replace("github.com/zigorminsk-debug/mathematics", "")
            for word in FOREIGN:
                self.assertTrue(word not in text, f"{name}: встречается «{word}»")


class AnswerForms(unittest.TestCase):
    """Ответ — величина: формы записи обязаны приниматься одинаково."""

    def spec(self, **kwargs):
        spec = {"answerType": "quantity", "answerValue": "10", "unit": "м/с",
                "unitPolicy": "named", "dimension": "m/s"}
        spec.update(kwargs)
        return spec

    def test_speed_in_different_units(self):
        spec = self.spec()
        self.assertTrue(Q.check_answer("10", spec).ok)
        self.assertTrue(Q.check_answer("10 м/с", spec).ok)
        self.assertTrue(Q.check_answer("36 км/ч", spec).ok)
        self.assertFalse(Q.check_answer("36", spec).ok)
        self.assertFalse(Q.check_answer("10 км/ч", spec).ok)

    def test_decimals_fractions_and_scientific_notation(self):
        spec = self.spec(answerValue="0.5", dimension="1", unit="1")
        for text in ("0,5", "0.50", "1/2", "5·10⁻¹", "5e-1"):
            self.assertTrue(Q.check_answer(text, spec).ok, text)
        self.assertFalse(Q.check_answer("3/4", spec).ok)
        self.assertFalse(Q.check_answer("1/0", spec).ok)
        big = self.spec(answerValue="300000000", dimension="m/s", unit="м/с")
        for text in ("3·10⁸ м/с", "3*10^8 м/с", "3e8 м/с"):
            self.assertTrue(Q.check_answer(text, big).ok, text)

    def test_wrong_unit_is_a_dimension_error_not_a_precision_error(self):
        spec = {"answerType": "quantity", "answerValue": "10", "unit": "кг",
                "unitPolicy": "named", "dimension": "kg"}
        result = Q.check_answer("10 Н", spec)
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "dimension")
        missing = self.spec(unitPolicy="required")
        self.assertEqual(Q.check_answer("10", missing).reason, "missing_unit")
        self.assertEqual(Q.check_answer("", spec).reason, "empty")

    def test_temperature_offset_and_prefixes(self):
        # 27 °C = 300,15 К: смещение шкалы учитывается, а не игнорируется
        kelvin = {"answerType": "quantity", "answerValue": "300.15", "unit": "К",
                  "unitPolicy": "named", "dimension": "K"}
        self.assertTrue(Q.check_answer("27 °C", kelvin).ok)
        self.assertFalse(Q.check_answer("27 К", kelvin).ok, "шкала Цельсия ≠ кельвины")
        kilo = {"answerType": "quantity", "answerValue": "2000", "unit": "м",
                "unitPolicy": "named", "dimension": "m"}
        self.assertTrue(Q.check_answer("2 км", kilo).ok)
        self.assertEqual(Q.check_answer("2 кг", kilo).reason, "dimension")


class TheoryAndTools(unittest.TestCase):

    def test_topics_cover_thirteen_areas(self):
        topics = load("topics")
        self.assertEqual(list(topics["order"]), TOPIC_ORDER)
        self.assertEqual(sorted(topics["topics"]), sorted(TOPIC_ORDER))
        self.assertEqual(sorted(topics["counts"]), sorted(TOPIC_ORDER))
        # в counts попадают и задания банка, и однотипные: так интерфейс
        # показывает объём тренировки по разделу
        bank = load("bank")["tasks"]
        analogous = load("analogous")["tasks"]
        expected = {}
        for task in bank + analogous:
            expected[task["topic"]] = expected.get(task["topic"], 0) + 1
        self.assertEqual(topics["counts"], expected)
        self.assertEqual(sum(topics["counts"].values()), len(bank) + len(analogous))

    def test_study_points_lead_to_existing_lessons(self):
        topics = load("topics")
        lessons = topics["lessons"]
        self.assertEqual(len(lessons), 37)
        for topic, entry in topics["study"].items():
            for lang in ("ru", "en"):
                self.assertGreaterEqual(len(entry[lang]), 2, topic)
                self.assertEqual(len(entry[lang]), len(entry["lessons"]), topic)
            for lesson_id in entry["lessons"]:
                self.assertIn(lesson_id, lessons, topic)

    def test_formulas_reference_existing_lessons(self):
        formulas = load("formulas")
        lessons = load("topics")["lessons"]
        self.assertEqual(len(formulas["groups"]), 13)
        items = 0
        for group in formulas["groups"]:
            self.assertTrue(group["items"], group.get("id"))
            for item in group["items"]:
                items += 1
                self.assertIn(item["lesson"], lessons, item.get("id") or item.get("formula"))
                self.assertTrue(item["name"]["ru"].strip() and item["name"]["en"].strip())
        self.assertGreaterEqual(items, 50)

    def test_error_catalogue_is_bilingual(self):
        mistakes = load("mistakes")
        self.assertGreaterEqual(len(mistakes["errors"]), 40)
        for tag, text in mistakes["errors"].items():
            self.assertTrue(text["ru"].strip(), tag)
            self.assertTrue(text["en"].strip(), tag)
        self.assertGreaterEqual(len(mistakes["checklist"]), 5)

    def test_interface_strings_are_complete(self):
        strings = load("ui_strings")["strings"]
        self.assertGreaterEqual(len(strings), 200)
        for key, value in strings.items():
            for lang in ("ru", "en"):
                self.assertTrue(str(value[lang]).strip(), f"{key}.{lang}")
            if key.endswith("_fmt"):
                self.assertEqual(str(value["ru"]).count("%s"), str(value["en"]).count("%s"), key)

    def test_analogous_tasks_are_verified(self):
        tasks = load("analogous")["tasks"]
        self.assertGreaterEqual(len(tasks), 39)
        for task in tasks:
            for lang in ("ru", "en"):
                self.assertTrue(Q.check_answer(task["answer"][lang], task["spec"]).ok, task["id"])
            spec = task["spec"]
            self.assertIsNotNone(Q.unit_of(spec["unit"]), task["id"])


if __name__ == "__main__":
    unittest.main()
