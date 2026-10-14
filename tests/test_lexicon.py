"""Independent dictionary gate (OpenCorpora via pymorphy3), separate from the
technical answer vectors: the language material itself is checked here.

* every correct spelling of a gap item is a known word form, every wrong
  completion is unknown unless it is an explicitly listed real word/form;
* bracket spellings consist of known words;
* numerals in part-B answers are declined exactly as pymorphy inflects them;
* verb aspect and noun declension agree with the dictionary tags;
* stress/phonetics/word-formation words exist.
Required in CI (pymorphy3 is pinned in requirements-dev.txt).
"""
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content_src"))
import generate  # noqa: E402
import pools_language as PL  # noqa: E402
import pools_spelling as PS  # noqa: E402

try:
    import pymorphy3
    MORPH = pymorphy3.MorphAnalyzer()
except ImportError:  # pragma: no cover - CI installs the pinned dependency
    if os.environ.get("CI"):
        raise
    MORPH = None

WORD = re.compile(r"[А-Яа-яЁё]*\.\.[А-Яа-яЁё]*")
CASES = {"родительный": "gent", "дательный": "datv", "творительный": "ablt", "предложный": "loct"}
NUMBERS = {
    "754": "семьсот пятьдесят четыре", "490": "четыреста девяносто", "870": "восемьсот семьдесят",
    "260": "двести шестьдесят", "365": "триста шестьдесят пять", "1500": "тысяча пятьсот",
    "548": "пятьсот сорок восемь", "690": "шестьсот девяносто", "1999": "тысяча девятьсот девяносто девять",
}


@unittest.skipIf(MORPH is None, "pymorphy3 is not installed (pip install -r requirements-dev.txt)")
class LexiconTests(unittest.TestCase):
    def known(self, word):
        return MORPH.word_is_known(word.lower())

    def wrong_completions(self, pool, fill):
        alts = pool["alts"]
        if alts == "double":
            return [fill[0]] if len(fill) == 2 else [fill * 2]
        if alts == "silent":
            return [""] if fill else ["т"]
        if alts == "soft":
            return [""] if fill else ["ь"]
        return [letter for letter in alts if letter != fill]

    def test_gap_items_against_the_dictionary(self):
        used = set()
        for name, pool in PS.GAP.items():
            for raw in pool["items"]:
                masked, fill = raw[0], raw[1]
                token = WORD.search(masked).group(0)
                with self.subTest(pool=name, item=masked):
                    self.assertTrue(self.known(token.replace("..", fill)), token.replace("..", fill))
                if name in PS.FORM_POOLS:
                    continue
                for alt in self.wrong_completions(pool, fill):
                    wrong = token.replace("..", alt).lower()
                    if self.known(wrong):
                        with self.subTest(pool=name, wrong=wrong):
                            self.assertIn(wrong, PS.HOMONYMS, "a wrong completion is a real word: list it or fix the item")
                        used.add(wrong)
        self.assertEqual(set(), PS.HOMONYMS - used, "stale homonym allowances")

    def test_bracket_spellings_are_real_words(self):
        for name in PS.BRACKET:
            for item in generate.bracket_items(name):
                for word in re.findall(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?", item["full"]):
                    parts = [word] if self.known(word) else word.split("-")
                    with self.subTest(pool=name, word=word):
                        self.assertTrue(all(self.known(part) for part in parts), word)

    def inflect(self, word, case):
        for parse in MORPH.parse(word):
            if parse.tag.POS in ("NUMR", "NOUN"):
                form = parse.inflect({case})
                if form:
                    return form.word
        return None

    def test_numeral_answers_match_independent_inflection(self):
        for sentence, digits, case_ru, case_en, answer, accept, why in PL.NUMERAL_WORDS:
            words = NUMBERS[digits].split()
            expected = " ".join(self.inflect(word, CASES[case_ru]) for word in words)
            with self.subTest(digits=digits):
                self.assertIn(expected, [answer, *accept])
                self.assertIn(digits, sentence)

    def test_verb_aspects_agree_with_the_dictionary(self):
        for verb, aspect in PL.ASPECT:
            with self.subTest(verb=verb):
                self.assertEqual(aspect, MORPH.parse(verb)[0].tag.aspect)

    def test_declension_classes_agree_with_gender_and_ending(self):
        heteroclite = {"время", "имя", "пламя", "знамя", "бремя", "вымя", "семя", "стремя", "темя", "племя", "путь"}
        for noun, declension in PL.DECLENSION:
            parse = next(p for p in MORPH.parse(noun) if p.tag.POS == "NOUN")
            if noun in heteroclite:
                derived = "razn"
            elif "Fixd" in parse.tag:
                derived = "fixed"
            elif noun[-1] in "ая" and parse.tag.gender in ("femn", "masc"):
                derived = 1
            elif parse.tag.gender == "femn" and noun.endswith("ь"):
                derived = 3
            else:
                derived = 2
            with self.subTest(noun=noun):
                self.assertEqual(declension, derived)

    def test_other_material_exists_in_the_dictionary(self):
        words = [stressed.replace("\u0301", "") for stressed in PL.STRESS]
        words += [word for word, _ in PL.PHONETICS] + [word for word, _, _ in PL.FORMATION if "-" not in word]
        words += [phrase.split()[-1] for phrase, _ in PL.ADJECTIVES] + [word for word, *_ in PL.ZERO_ENDINGS]
        for word in words:
            with self.subTest(word=word):
                self.assertTrue(self.known(word), word)


if __name__ == "__main__":
    unittest.main()
