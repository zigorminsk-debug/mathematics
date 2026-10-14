"""Everyday explanation coverage, typed SVG safety and diagram mathematics."""
from copy import deepcopy
import contextlib
from fractions import Fraction
import io
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build_content as build
import diagrams
import intuition
import theory


class EverydayTests(unittest.TestCase):
    def test_every_lesson_has_parallel_concrete_explanations(self):
        self.assertEqual(set(theory.LESSONS), set(intuition.payload()))
        for key, entry in intuition.payload().items():
            with self.subTest(key=key):
                self.assertEqual(len(entry["ru"]), len(entry["en"]))
                self.assertGreaterEqual(len(entry["ru"]), 2)
                self.assertTrue(all(len(text) > 70 for text in entry["ru"] + entry["en"]))
                self.assertEqual(entry, theory.payload()[key]["everyday"])

    def test_missing_translation_and_paragraph_are_blocked(self):
        for mutation in (None, [], ["Untranslated extra paragraph"]):
            lessons = deepcopy(theory.payload())
            lessons["fractions"]["everyday"]["en"] = mutation
            with patch.object(theory, "payload", return_value=lessons), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                build.build_theory()

    def test_everyday_numbers_and_units(self):
        # Independent exact checks of the authored stories (not float rounding).
        self.assertEqual(18, 3 * (4 + 2))
        self.assertEqual(Fraction(21, 2), Fraction(5, 2) * Fraction(42, 10))
        self.assertEqual(6, math.gcd(18, 24))
        self.assertEqual(24, math.lcm(6, 8))
        self.assertEqual(49, 25 + 10 + 10 + 4)
        self.assertEqual(6, (17 - 5) / 2)
        self.assertEqual(3, 1 * (4 - 1))
        self.assertEqual(Fraction(2), 1 / (Fraction(1, 6) + Fraction(1, 3)))
        self.assertEqual(88, Fraction(100) * Fraction(8, 10) * Fraction(11, 10))
        self.assertEqual(100, sum([10, 15, 20, 25, 30]))
        self.assertEqual(31, sum([1, 2, 4, 8, 16]))
        self.assertEqual(Fraction(1), Fraction(3, 5)**2 + Fraction(4, 5)**2)
        self.assertEqual(Fraction(9, 25), Fraction(3, 5)**2)
        self.assertEqual(Fraction(3, 10), Fraction(3, 5) * Fraction(2, 4))
        self.assertEqual(24, math.factorial(4))
        self.assertEqual(6, math.comb(4, 2))
        # Critical qualifications are present, not just optimistic analogies.
        self.assertIn("равновероятном", intuition.payload()["probability"]["ru"][0])
        self.assertIn("постоянные", intuition.payload()["motion-work"]["ru"][1])
        self.assertIn("0 < p < 4", intuition.payload()["parameters"]["ru"][1])
        self.assertIn("не гарантирует", intuition.payload()["extrema"]["ru"][1])


class DiagramContractTests(unittest.TestCase):
    def test_complete_linked_offline_catalogue(self):
        figures = diagrams.validate(diagrams.payload())
        self.assertEqual(52, len(figures))
        self.assertEqual(51, len(diagrams.LESSON_FIGURES))
        used = {ref for refs in diagrams.LESSON_FIGURES.values() for ref in refs}
        self.assertEqual(set(figures), used)
        for key in ("functions", "trig", "planimetry", "stereometry", "derivative", "research", "vectors", "param"):
            for lesson in theory.STUDY_LESSONS[key]:
                self.assertTrue(diagrams.LESSON_FIGURES.get(lesson), (key, lesson))
        for key, figure in figures.items():
            self.assertEqual((420, 280), (figure["width"], figure["height"]))
            self.assertTrue(figure["title"]["ru"] and figure["title"]["en"])
            self.assertGreater(len(figure["caption"]["ru"]), 60)
            self.assertGreater(len(figure["caption"]["en"]), 60)

    def test_missing_duplicate_and_unreachable_figures_are_rejected(self):
        for refs in (["missing"], ["fraction-bar", "fraction-bar"]):
            lessons = deepcopy(theory.payload())
            lessons["fractions"]["figures"] = refs
            with patch.object(theory, "payload", return_value=lessons), \
                 contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                build.build_theory()
        figures = diagrams.payload()
        figures["unreachable"] = dict(deepcopy(figures["fraction-bar"]), id="unreachable")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            build.build_theory(figures)

    def test_raw_markup_attributes_and_external_resources_are_forbidden(self):
        for bad in ({"kind": "script", "role": "text", "filled": False},
                    dict(diagrams.line(1, 1, 2, 2), onclick="alert(1)"),
                    dict(diagrams.line(1, 1, 2, 2), href="https://external.example/a"),
                    dict(diagrams.line(1, 1, 2, 2), style="display:none")):
            figures = diagrams.payload()
            figures["fraction-bar"]["drawing"].append(bad)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                diagrams.validate(figures)
        figures = diagrams.payload()
        figures["fraction-bar"]["svg"] = '<svg onload="alert(1)"></svg>'
        with self.assertRaises(ValueError):
            diagrams.validate(figures)

    def test_nonfinite_negative_out_of_bounds_and_boolean_coordinates_are_rejected(self):
        for bad in (float("nan"), float("inf"), -1, 500, True):
            figures = diagrams.payload()
            figures["fraction-bar"]["drawing"][0]["x"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                diagrams.validate(figures)
        for field, value in (("width", 0), ("y", 300)):
            figures = diagrams.payload()
            figures["fraction-bar"]["drawing"][0][field] = value
            with self.assertRaises(ValueError):
                diagrams.validate(figures)

    def test_labels_and_captions_cannot_lose_a_language(self):
        for field in ("title", "caption"):
            figures = diagrams.payload()
            figures["fraction-bar"][field].pop("en")
            with self.assertRaises(ValueError):
                diagrams.validate(figures)
        figures = diagrams.payload()
        next(item for item in figures["fraction-bar"]["drawing"] if item["kind"] == "text")["text"].pop("ru")
        with self.assertRaises(ValueError):
            diagrams.validate(figures)

    def test_pipeline_checks_diagram_safety(self):
        figures = diagrams.payload()
        figures["sphere"]["drawing"].append({"kind": "foreignObject"})
        with patch.object(diagrams, "payload", return_value=figures), self.assertRaises(SystemExit):
            build.build_diagrams()


class DiagramMathTests(unittest.TestCase):
    def test_every_plotted_coordinate_matches_its_function(self):
        points_checked = 0
        for key, figure in diagrams.payload().items():
            model = figure.get("model", {})
            if model.get("type") != "plot":
                continue
            xmin, xmax, ymin, ymax = model["bounds"]
            left, top, width, height = model["frame"]
            for series in model["series"]:
                curves = [item for item in figure["drawing"] if item["kind"] == "polyline" and item["role"] == series["role"]]
                self.assertEqual(series["segments"], len(curves), key)
                self.assertGreater(len(curves), 0, key)
                for curve in curves:
                    last_x = float("-inf")
                    for px, py in curve["points"]:
                        x = xmin + (px-left)/width*(xmax-xmin)
                        y = ymax - (py-top)/height*(ymax-ymin)
                        self.assertGreaterEqual(x, last_x)
                        last_x = x
                        expected = diagrams.FUNCTIONS[series["function"]](x)
                        self.assertAlmostEqual(expected, y, delta=1e-5, msg=(key, x, y))
                        points_checked += 1
        self.assertGreater(points_checked, 2400)

    def test_hyperbola_does_not_bridge_its_asymptote(self):
        figure = diagrams.FIGURES["hyperbola"]
        curves = [item for item in figure["drawing"] if item["kind"] == "polyline" and item["role"] == "primary"]
        self.assertEqual(2, len(curves))
        zero = 48 + 324/2
        self.assertTrue(all(point[0] < zero for point in curves[0]["points"]))
        self.assertTrue(all(point[0] > zero for point in curves[1]["points"]))

    def test_trig_projections_arc_and_two_solution_angles(self):
        circle = diagrams.FIGURES["unit-circle"]["model"]
        x, y = circle["point"]
        self.assertAlmostEqual(1, x*x + y*y)
        self.assertAlmostEqual(math.sqrt(3)/2, x)
        self.assertAlmostEqual(.5, y)
        arc = diagrams.FIGURES["radian-arc"]["model"]
        self.assertAlmostEqual(arc["length"], arc["radius"]*arc["angle"])
        solutions = diagrams.FIGURES["circle-two-solutions"]["model"]
        for angle in solutions["angles"]:
            self.assertAlmostEqual(solutions["height"], math.sin(angle))

    def test_triangle_scale_median_altitude_and_bisector(self):
        figure = diagrams.FIGURES["ladder-triangle"]
        model = figure["model"]
        self.assertEqual(model["hypotenuse"]**2, sum(leg**2 for leg in model["legs"]))
        triangle = next(item for item in figure["drawing"] if item["kind"] == "polygon")["points"]
        a, b, c = triangle
        self.assertAlmostEqual(model["legs"][1]*model["scale"], math.dist(a,b))
        self.assertAlmostEqual(model["legs"][0]*model["scale"], math.dist(a,c))
        self.assertAlmostEqual(model["hypotenuse"]*model["scale"], math.dist(b,c))
        m = diagrams.FIGURES["triangle-lines"]["model"]
        a,b,c = m["vertices"]
        self.assertEqual([(a[0]+b[0])/2,(a[1]+b[1])/2], m["median"])
        self.assertEqual(c[0], m["altitude"][0])
        d=m["bisector"]
        self.assertAlmostEqual(math.dist(a,d)/math.dist(d,b),math.dist(c,a)/math.dist(c,b))
        self.assertEqual(3,len({tuple(m[field]) for field in ("median","altitude","bisector")}))

    def test_circle_angles_and_tangent_are_mathematical_not_eyeballed(self):
        model=diagrams.FIGURES["circle-angles"]["model"]
        p,q,v = model["points"]
        o=model["centre"]
        for point in (p,q,v):
            self.assertAlmostEqual(model["radius"],math.dist(o,point))
        def angle(a,b,c):
            u=[a[i]-b[i] for i in range(2)]; w=[c[i]-b[i] for i in range(2)]
            cosine=sum(u[i]*w[i] for i in range(2))/(math.hypot(*u)*math.hypot(*w))
            return math.degrees(math.acos(cosine))
        self.assertAlmostEqual(model["central"],angle(p,o,q))
        self.assertAlmostEqual(model["inscribed"],angle(p,v,q))
        self.assertEqual(model["central"],2*model["inscribed"])
        tangent=diagrams.FIGURES["circle-tangent"]["model"]
        self.assertEqual(tangent["centre"][0],tangent["contact"][0])
        self.assertEqual(tangent["lineY"],tangent["contact"][1])
        self.assertEqual(tangent["radius"],math.dist(tangent["centre"],tangent["contact"]))

    def test_similar_figures_and_solid_measurements(self):
        models={key:figure["model"] for key,figure in diagrams.FIGURES.items()}
        m=models["similar-triangles"]
        self.assertEqual([2,2,2],[b/a for a,b in zip(m["small"],m["large"])])
        self.assertEqual(4,m["areas"][1]/m["areas"][0])
        m=models["prism-box"]; self.assertEqual(m["volume"],math.prod(m["base"])*m["height"])
        m=models["cylinder"]; self.assertEqual(m["volumePi"],m["radius"]**2*m["height"])
        m=models["pyramid"]; self.assertEqual(m["volume"],m["baseArea"]*m["height"]/3)
        m=models["cone"]; self.assertEqual(m["volumePi"],m["radius"]**2*m["height"]/3)
        self.assertEqual(m["slant"]**2,m["radius"]**2+m["height"]**2)
        m=models["sphere"]; self.assertEqual(m["areaPi"],4*m["radius"]**2)
        self.assertEqual(m["volumePi"],Fraction(4,3)*m["radius"]**3)
        m=models["cube"]; self.assertEqual(m["volume"],m["edge"]**3)
        self.assertEqual(m["area"],6*m["edge"]**2)
        self.assertAlmostEqual(m["diagonal"],m["edge"]*math.sqrt(3))

    def test_vectors_projection_midpoint_and_dot_product(self):
        m=diagrams.FIGURES["vector-displacement"]["model"]
        self.assertEqual(m["length"],math.hypot(*m["coordinates"]))
        self.assertEqual(m["routeLength"],sum(m["coordinates"]))
        m=diagrams.FIGURES["dot-perpendicular"]["model"]
        self.assertEqual(0,sum(x*y for x,y in zip(m["a"],m["b"])))
        m=diagrams.FIGURES["midpoint"]["model"]
        self.assertEqual(m["midpoint"],[(x+y)/2 for x,y in zip(m["a"],m["b"])])
        m=diagrams.FIGURES["three-perpendiculars"]["model"]
        self.assertEqual(0,sum(x*y for x,y in zip(m["height"],m["projection"])))
        for vector in (m["projection"], [x+y for x,y in zip(m["height"],m["projection"])]):
            self.assertEqual(0,sum(x*y for x,y in zip(vector,m["lineDirection"])))
        project=lambda vector: [m["screenOrigin"][axis]+sum(vector[i]*m["screenBasis"][i][axis] for i in range(3)) for axis in range(2)]
        self.assertEqual([150,51],project(m["height"]))
        self.assertEqual([286,214],project(m["projection"]))

    def test_discrete_sequences_counts_and_endpoint_conventions(self):
        for key in ("arithmetic-dots","geometric-dots"):
            self.assertFalse(diagrams.FIGURES[key]["model"]["joined"])
        arithmetic=diagrams.FIGURES["arithmetic-dots"]["model"]["values"]
        self.assertEqual([5]*4,[b-a for a,b in zip(arithmetic,arithmetic[1:])])
        geometric=diagrams.FIGURES["geometric-dots"]["model"]["values"]
        self.assertEqual([2]*4,[b/a for a,b in zip(geometric,geometric[1:])])
        self.assertEqual([{"x":-2,"closed":False},{"x":1,"closed":True}],diagrams.FIGURES["interval-signs"]["model"]["marks"])
        m=diagrams.FIGURES["counting-roles"]["model"]
        self.assertEqual(m["ordered"],math.perm(m["n"],m["k"]))
        self.assertEqual(m["unordered"],math.comb(m["n"],m["k"]))
        m=diagrams.FIGURES["clock-cycle"]["model"]
        self.assertEqual(m["result"],(m["start"]+m["increment"])%m["modulus"])


if __name__ == "__main__":
    unittest.main()
