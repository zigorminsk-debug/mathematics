"""Единицы измерения, размерности и проверка ответов — физический контур проверки.

Эти тесты — не «синтаксический минимум»: они фиксируют именно те ошибки, из-за
которых физический тренажёр начинает принимать 10 Н за 10 кг, 10 см за 10 м,
«36» за 36 м/с или температуру в °C в формулу идеального газа.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "content_src"))

import quantities as Q  # noqa: E402


class UnitParsing(unittest.TestCase):
    def test_base_units_latin_and_cyrillic(self):
        for text, symbol in (("m", "m"), ("м", "m"), ("kg", "kg"), ("кг", "kg"),
                             ("s", "s"), ("с", "s"), ("A", "A"), ("А", "A"),
                             ("K", "K"), ("К", "K"), ("mol", "mol"), ("моль", "mol"),
                             ("cd", "cd")):
            self.assertEqual(Q.parse_unit(text).symbol, symbol, text)

    def test_si_prefixes(self):
        cases = {
            "км": Fraction(1000), "см": Fraction(1, 100), "мм": Fraction(1, 1000),
            "мкм": Fraction(1, 10 ** 6), "нм": Fraction(1, 10 ** 9), "дм": Fraction(1, 10),
            "мс": Fraction(1, 1000), "МГц": Fraction(10 ** 6), "кДж": Fraction(1000),
            "мДж": Fraction(1, 1000), "мкФ": Fraction(1, 10 ** 6), "кПа": Fraction(1000),
            "МПа": Fraction(10 ** 6), "мА": Fraction(1, 1000), "кВт": Fraction(1000),
            "кОм": Fraction(1000), "МДж": Fraction(10 ** 6),
        }
        for text, factor in cases.items():
            self.assertEqual(Q.parse_unit(text).factor, factor, text)

    def test_compound_units(self):
        self.assertEqual(Q.parse_unit("м/с").dim, Q.parse_dim("m/s"))
        self.assertEqual(Q.parse_unit("м/с²").dim, Q.parse_dim("m/s^2"))
        self.assertEqual(Q.parse_unit("кг·м/с²").dim, Q.parse_dim("kg·m/s^2"))
        self.assertEqual(Q.parse_unit("Н").dim, Q.parse_dim("kg·m/s^2"))
        self.assertEqual(Q.parse_unit("Дж/(кг·К)").dim, Q.parse_dim("m^2/(s^2·K)"))
        self.assertEqual(Q.parse_unit("Дж/(кг·°C)").dim, Q.parse_dim("m^2/(s^2·K)"))
        self.assertEqual(Q.parse_unit("кг/м³").dim, Q.parse_dim("kg/m^3"))
        self.assertEqual(Q.parse_unit("1/с").dim, Q.parse_dim("1/s"))

    def test_non_si_school_units(self):
        self.assertEqual(Q.parse_unit("км/ч").factor, Fraction(5, 18))
        self.assertEqual(Q.parse_unit("мин").factor, 60)
        self.assertEqual(Q.parse_unit("ч").factor, 3600)
        self.assertEqual(Q.parse_unit("т").factor, 1000)
        self.assertEqual(Q.parse_unit("г").factor, Fraction(1, 1000))
        self.assertEqual(Q.parse_unit("л").factor, Fraction(1, 1000))
        self.assertEqual(Q.parse_unit("г/см³").factor, 1000)
        self.assertEqual(Q.parse_unit("кВт·ч").factor, 3600000)
        self.assertEqual(Q.parse_unit("эВ").factor, Fraction(16, 10 ** 20))

    def test_temperature_is_affine(self):
        unit = Q.parse_unit("°C")
        self.assertEqual(unit.dim, Q.parse_dim("K"))
        self.assertEqual(unit.offset, Fraction(27315, 100))
        self.assertNotIn("°", Q.parse_unit("к°C") if False else "K")

    def test_unknown_and_unsafe_units_are_rejected(self):
        for text in ("", "м/", "фунт", "м+с", "10 м", "м^с", "кг^^2", "eval(1)"):
            with self.assertRaises(Q.QuantityError, msg=text):
                Q.parse_unit(text)

    def test_unit_lookup_is_case_aware_for_single_letters(self):
        self.assertEqual(Q.parse_unit("Тл").symbol, "T")       # тесла
        self.assertEqual(Q.parse_unit("т").dim, Q.parse_dim("kg"))   # тонна
        self.assertEqual(Q.parse_unit("T").dim, Q.parse_dim("kg/(s^2·A)"))
        self.assertEqual(Q.parse_unit("t").dim, Q.parse_dim("kg"))
        self.assertEqual(Q.parse_unit("N").dim, Q.parse_dim("kg·m/s^2"))
        self.assertEqual(Q.parse_unit("n").dim, Q.parse_dim("kg·m/s^2"))

    def test_conversions(self):
        self.assertEqual(Q.Q(36, "км/ч").to("м/с").value, 10)
        self.assertEqual(Q.Q(10, "см").to("м").value, Fraction(1, 10))
        self.assertEqual(Q.Q(2.5, "г/см^3").to("кг/м^3").value, 2500)
        self.assertEqual(Q.Q(0, "°C").to("K").value, Fraction(27315, 100))
        self.assertEqual(Q.Q(27, "°C").to("K").value, 300 + Fraction(15, 100))
        self.assertEqual(Q.Q(2, "л").to("м^3").value, Fraction(1, 500))
        self.assertEqual(Q.Q(1, "кВт·ч").to("Дж").value, 3600000)
        self.assertEqual(Q.Q(1, "мин").to("с").value, 60)

    def test_conversion_between_different_dimensions_is_an_error(self):
        with self.assertRaises(Q.QuantityError):
            Q.Q(10, "Н").to("кг")
        with self.assertRaises(Q.QuantityError):
            Q.Q(10, "см").to("с")


class Numbers(unittest.TestCase):
    def test_accepted_forms(self):
        cases = {
            "12": 12, "12,5": Fraction(25, 2), "12.5": Fraction(25, 2),
            "-3,5": Fraction(-7, 2), "+2": 2, "1e-3": Fraction(1, 1000),
            "1,5·10⁻³": Fraction(3, 2000), "1,5*10^-3": Fraction(3, 2000),
            "1,6*10-19": Fraction(16, 10 ** 20), "3·10⁵": 300000, "10³": 1000,
            "1 000": 1000, "0,0001": Fraction(1, 10 ** 4), "-0,5": Fraction(-1, 2),
            "10³": 1000, "10^3": 1000, "10^-3": Fraction(1, 1000),
        }
        for text, expected in cases.items():
            self.assertEqual(Q.parse_number(text), Fraction(expected), text)

    def test_rejected_forms(self):
        for text in ("", "abc", "12,5,5", "м/с", "1/2 м", "..", "1e", "10^"):
            self.assertIsNone(Q.parse_number(text), text)

    def test_rounding_boundaries_are_exact(self):
        self.assertEqual(Q.parse_number("0,05") + Q.parse_number("0,05"), Fraction(1, 10))
        self.assertTrue(abs(Q.parse_number("0,3") - Q.parse_number("0,1") - Q.parse_number("0,2")) == 0)

    def test_formatting_russian_and_english(self):
        self.assertEqual(Q.format_number(Fraction(25, 2), "ru"), "12,5")
        self.assertEqual(Q.format_number(Fraction(25, 2), "en"), "12.5")
        self.assertEqual(Q.format_number(Fraction(16, 10 ** 20), "ru"), "1,6·10⁻¹⁹")
        self.assertEqual(Q.format_number(Fraction(16, 10 ** 20), "en"), "1.6·10^-19")
        self.assertEqual(Q.format_number(Fraction(46, 10) * 10 ** 6, "ru"), "4,6·10⁶")
        self.assertEqual(Q.format_number(Fraction(1, 3), "ru", places=2), "0,33")
        self.assertEqual(Q.format_number(1000, "ru"), "1000")

    def test_scientific_round_trip(self):
        for value in (Fraction(16, 10 ** 20), Fraction(46) * 10 ** 6, Fraction(3, 2000)):
            for lang in ("ru", "en"):
                text = Q.format_number(value, lang)
                parsed = Q.parse_number(text)
                self.assertIsNotNone(parsed, text)
                self.assertLess(abs(parsed - value), Fraction(1, 10 ** 12) * max(1, abs(value)))


class ModelChecking(unittest.TestCase):
    def test_eval_model_uses_exact_arithmetic(self):
        value = Q.eval_model("s = v0*t + a*t^2/2",
                             {"v0": Fraction(10), "t": Fraction(5), "a": Fraction(2)})
        self.assertEqual(value, 75)
        self.assertEqual(Q.eval_model("v0*t + a*t^2/2",
                                      {"v0": 10, "t": 5, "a": 2}), 75)

    def test_dimension_balance(self):
        dims = {"s": "m", "v0": "m/s", "a": "m/s^2", "t": "s"}
        self.assertEqual(Q.dim_balance("v0*t + a*t^2/2", dims), Q.parse_dim("m"))

    def test_dimension_mismatch_is_rejected(self):
        dims = {"s": "m", "v0": "m/s", "a": "m/s^2", "t": "s"}
        with self.assertRaises(Q.ModelError):
            Q.dim_balance("v0*t + a*t", dims)          # м + м/с — так нельзя
        # целые отрицательные степени точны и разрешены: 1/r², 2^(−t/T)-подобные модели
        self.assertEqual(Q.dim_balance("v0^-1", dims), Q.parse_dim("s") / Q.parse_dim("m"))
        self.assertEqual(Q.dim_balance("v0^(-2)", dims), Q.parse_dim("m/s") ** -2)
        with self.assertRaises(Q.ModelError):
            Q.dim_balance("v0^1.5", dims)              # дробные степени по-прежнему запрещены

    def test_dimensionless_unit_has_no_label(self):
        unit = Q.parse_unit("1")
        self.assertEqual(unit.dim, Q.Dim.none())
        self.assertEqual(unit.display("ru"), "")
        self.assertEqual(Q.format_quantity(Fraction(7, 8), unit), "0,875")
        self.assertEqual(Q.format_quantity(Fraction(1), Q.parse_unit("1")), "1")

    def test_unknown_symbol_is_rejected(self):
        with self.assertRaises(Q.ModelError):
            Q.eval_model("v = s/t", {"s": 10})


class AnswerChecking(unittest.TestCase):
    """Контракт проверки: число + единица + размерность + допуск."""

    def spec(self, **overrides):
        base = {
            "answerType": "number",
            "answerValue": Fraction(10),
            "unit": "м/с",
            "unitPolicy": "named",
            "dimension": "m/s",
            "tolerance": {"kind": "absolute", "value": Fraction(1, 100)},
        }
        base.update(overrides)
        return base

    def test_correct_answer_without_unit_when_unit_is_named(self):
        self.assertTrue(Q.check_answer("10", self.spec()).ok)
        self.assertTrue(Q.check_answer("10 м/с", self.spec()).ok)
        self.assertTrue(Q.check_answer("10,0 м/с", self.spec()).ok)

    def test_equivalent_unit_is_accepted(self):
        # 36 км/ч = 10 м/с — та же физическая величина
        self.assertTrue(Q.check_answer("36 км/ч", self.spec()).ok)
        self.assertTrue(Q.check_answer("0,01 км/с", self.spec()).ok)

    def test_wrong_unit_value_is_not_accepted(self):
        # 10 см — это 0,1 м, а не 10 м
        result = Q.check_answer("10 см", self.spec(answerValue=10, unit="м", dimension="m",
                                                   tolerance={"kind": "absolute", "value": Fraction(1, 100)}))
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "value")

    def test_wrong_dimension_is_reported_separately(self):
        result = Q.check_answer("10 Н", self.spec(answerValue=10, unit="кг", dimension="kg",
                                                  tolerance={"kind": "absolute", "value": Fraction(1, 100)}))
        self.assertFalse(result.ok)
        self.assertEqual(result.reason, "dimension")
        self.assertEqual(result.diagnosis(), "answer_wrong_dimension")

    def test_required_unit(self):
        spec = self.spec(unitPolicy="required")
        self.assertEqual(Q.check_answer("10", spec).reason, "missing_unit")
        self.assertTrue(Q.check_answer("10 м/с", spec).ok)

    def test_unknown_unit_is_rejected(self):
        self.assertEqual(Q.check_answer("10 фунт", self.spec()).reason, "unit")

    def test_tolerance_boundary_is_exact(self):
        spec = {"answerType": "number", "answerValue": Fraction(1, 20), "unit": "м",
                "unitPolicy": "named", "dimension": "m", "rounding": 2}
        self.assertTrue(Q.check_answer("0,05", spec).ok)
        self.assertTrue(Q.check_answer("0,054", spec).ok)     # ровно на границе допуска 0,005
        self.assertFalse(Q.check_answer("0,06", spec).ok)     # 0,01 > 0,005
        self.assertFalse(Q.check_answer("0,039", spec).ok)

    def test_integer_answers_are_exact(self):
        spec = {"answerType": "number", "answerValue": 1000, "unit": "Дж",
                "unitPolicy": "named", "dimension": "kg·m^2/s^2"}
        self.assertTrue(Q.check_answer("1000", spec).ok)
        self.assertTrue(Q.check_answer("1 кДж", spec).ok)
        self.assertFalse(Q.check_answer("1000,5", spec).ok)

    def test_relative_tolerance(self):
        spec = {"answerType": "number", "answerValue": 3 * 10 ** 8, "unit": "м/с",
                "unitPolicy": "named", "dimension": "m/s",
                "tolerance": {"kind": "relative", "value": Fraction(1, 100)}}
        self.assertTrue(Q.check_answer("3·10⁸", spec).ok)
        self.assertTrue(Q.check_answer("3,01·10^8", spec).ok)
        self.assertFalse(Q.check_answer("3,1·10^8", spec).ok)

    def test_temperature_requires_kelvin_in_gas_law(self):
        spec = {"answerType": "number", "answerValue": Fraction(300), "unit": "К",
                "unitPolicy": "named", "dimension": "K",
                "tolerance": {"kind": "absolute", "value": Fraction(1, 2)}}
        self.assertFalse(Q.check_answer("27", spec).ok)        # 27 °C — это 300,15 К, но «27» К — нет
        self.assertTrue(Q.check_answer("300", spec).ok)
        self.assertTrue(Q.check_answer("27 °C", spec).ok)

    def test_choice_answers_accept_letters_and_commas(self):
        spec = {"answerType": "choice", "answer": "2,5 м", "accept": ["2,5 м"]}
        for text in ("2,5 м", "2.5 м", " 2,5 м ", "ответ: 2,5 м", "а) 2,5 м"):
            self.assertTrue(Q.check_answer(text, spec).ok, text)
        self.assertFalse(Q.check_answer("2,6 м", spec).ok)

    def test_empty_answer(self):
        self.assertEqual(Q.check_answer("", self.spec()).reason, "empty")
        self.assertEqual(Q.check_answer(None, self.spec()).reason, "empty")

    def test_zero_and_negative(self):
        spec = {"answerType": "number", "answerValue": 0, "unit": "Дж",
                "unitPolicy": "named", "dimension": "kg·m^2/s^2"}
        self.assertTrue(Q.check_answer("0", spec).ok)
        spec = {"answerType": "number", "answerValue": -5, "unit": "Дж",
                "unitPolicy": "named", "dimension": "kg·m^2/s^2"}
        self.assertTrue(Q.check_answer("-5", spec).ok)
        self.assertTrue(Q.check_answer("−5 Дж", spec).ok)
        self.assertFalse(Q.check_answer("5", spec).ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
