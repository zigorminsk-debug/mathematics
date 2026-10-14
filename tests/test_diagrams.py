"""Typed visual aids: SVG primitives, semantic tables, decision trees; no markup/URLs."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "content_src"))
import diagrams  # noqa: E402
import kit  # noqa: E402


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.figures = diagrams.payload()

    def test_catalogue_is_valid_and_complete(self):
        diagrams.validate(self.figures)
        kinds = {figure["kind"] for figure in self.figures.values()}
        self.assertEqual({"svg", "table", "tree"}, kinds)
        self.assertEqual(set(kit.RULES), set(diagrams.LESSON_FIGURES))
        used = {fid for ids in diagrams.LESSON_FIGURES.values() for fid in ids}
        self.assertEqual(set(self.figures), used, "every figure is reachable from a rule card")

    def test_required_scheme_kinds_exist(self):
        # sentence base, decision trees, morpheme parsing/word chain, contrast tables,
        # complex sentence structure, stress highlighting (subject handoff list)
        for fid in ("sentence-base", "tree-ne", "morpheme-podokonnik", "chain-uchit", "table-tozhe",
                    "scheme-ssp-spp", "scheme-bsp", "stress-zvonit"):
            self.assertIn(fid, self.figures)

    def test_large_text_lives_in_html_tables_not_tiny_svg(self):
        for figure in self.figures.values():
            if figure["kind"] == "svg":
                labels = [item["text"]["ru"] for item in figure["drawing"] if item["kind"] == "text"]
                self.assertTrue(all(len(label) <= 60 for label in labels), figure["id"])

    def mutate(self, fid, change):
        figures = deepcopy(self.figures)
        change(figures[fid])
        with self.assertRaises(ValueError):
            diagrams.validate(figures)

    def test_unsafe_or_broken_figures_are_rejected(self):
        self.mutate("stress-zvonit", lambda f: f["drawing"].append({"kind": "image", "role": "text", "filled": False}))
        self.mutate("stress-zvonit", lambda f: f["drawing"][-1].update(onload="x"))
        self.mutate("stress-zvonit", lambda f: f["drawing"][0].update(x=float("nan")))
        self.mutate("stress-zvonit", lambda f: f["drawing"][0].update(role="script"))
        self.mutate("stress-zvonit", lambda f: f.update(width=999))
        self.mutate("table-tozhe", lambda f: f["rows"][0].append("лишняя ячейка"))
        self.mutate("table-tozhe", lambda f: f["rows"][0].__setitem__(0, "<b>тоже</b>"))
        self.mutate("table-tozhe", lambda f: f.update(caption={"ru": "см. https://example.com", "en": "x"}))
        self.mutate("table-tozhe", lambda f: f["columns"][0].pop("en"))
        self.mutate("tree-ne", lambda f: f["root"].pop("no"))
        self.mutate("tree-ne", lambda f: f["root"]["yes"].update(result={"ru": "javascript:alert(1)", "en": "x"}))
        self.mutate("tree-ne", lambda f: f.update(kind="html"))

    def test_bilingual_captions(self):
        for figure in self.figures.values():
            for lang in ("ru", "en"):
                self.assertTrue(figure["title"][lang].strip() and figure["caption"][lang].strip(), figure["id"])


if __name__ == "__main__":
    unittest.main()
