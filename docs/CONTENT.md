# Content model — «Репетитор ЦТ: Русский язык»

## Verified exam structure (not inherited from mathematics)

Spec: «Спецификация экзаменационной (тестовой) работы по учебному предмету «Русский язык»
для проведения ЦЭ и ЦТ в 2026 году», approved 03.11.2025, published by RIKZ 05.11.2025,
<https://rikc.by/ru/specification/2026/01.pdf>, read **2026-10-14**:

- 40 tasks: part A — 18 closed tasks (choose **several** correct answers out of five),
  part B — 22 open tasks (a word, several digits, or letters + digits); **120 minutes**;
- sections and quotas: орфография 13, пунктуация 9, лексика 2, культура речи 3,
  фонетика 1, состав слова/образование слов 2, морфология 4, синтаксис 3, текст 3;
- difficulty levels I-4, II-10, III-16, IV-6, V-4.

The slot themes of the authored blueprint (A1…A18, B1…B22) were cross-checked with
Adukar's list of the 2025 test themes (read 2026-10-14). The six variants labelled
2021–2026 are **authored practice sets that all follow the 2026 structure**; the year is
only a name, nothing is an official RIKZ material. The app counts correct tasks and does
not simulate the official primary→test score conversion.

## Sources of truth (`content_src/`)

| File | Purpose |
|---|---|
| `kit.py` | 13 study areas, 9 RIKZ sections with quotas, 54 rule ids, 40-slot blueprint and levels, `task()` / `validate_task()` |
| `checker.py` | the subject answer checker (reference) and its check-object contract |
| `vectors.py` | 123 hand-written checker vectors (minimal pairs) shared with JS and Kotlin |
| `pools_spelling.py` | gap pools (letters/Н-НН/Ь/Ъ/prefixes…) and bracket pools (НЕ, hyphen, conjunctions) with reason codes |
| `pools_punctuation.py` | sentences with braced tested marks, direct-speech statements, numbered B13 sentences |
| `pools_language.py` | phonetics (transcriptions), stress, vocabulary, idioms, paronyms, pleonasms, numerals, grammar norms, morphology, syntax, morphemes, word formation |
| `texts.py` | original short texts with sentence-by-sentence cohesion annotations, styles, types, statements, subtopics |
| `generate.py` | builds 6 × 40 variant tasks and 193 analogous exercises (seeded, deterministic) |
| `rules_a.py`, `rules_b.py`, `rules.py` | 54 rule cards, study lists per area, the «Правила» reference |
| `diagrams.py` | 49 figures: 14 typed SVG schemes, 26 semantic tables, 9 decision trees |
| `mistakes.py` | a typical-error diagnosis per rule + exam checklist |
| `sources.py` | normative sources with an honest status (checked / automated / reference) |
| `ui_strings.py` | all RU/EN interface strings |
| `periods.py` | the six authored periods, the specification record and the disclaimer |

## Task schema

Every task: `id`, `kind` (variant/analog), `topic` (area), `rule` + `rules`, optional
`itemRules` (rule per option — remediation by the misjudged options), bilingual
`instruction`, **Russian material** `text` / `items` (plain strings, never translated),
optional bilingual `choices` (metalanguage options), `check`, bilingual `solution`
(worked analysis, ≥2 steps) and `hints`, `src: authored`; variant tasks also `year`,
`part`, `n`, `section`, `level`.

`check` declares explicitly: `type` (multi | single | numbers | word | stress | match |
integer), `scoring: exact`, `order` (unordered/ordered/by-label/n/a) and for words
`case`, `yo` (strict | e-equals-yo), `hyphen` (strict | typographic), `accept` +
`acceptWhy` (justified alternatives only). Contract details: docstring of `checker.py`.
Key rules: a significant space/hyphen is never removed; a run of whitespace becomes one
space; only U+2010/U+2011 may become "-"; stress/grave marks in a word answer never
match; extra/missing/duplicate selections never match; concatenated digits only while
`max ≤ 9`; no keyword or regex leniency.

## Gates

`tools/build_content.py` fails on: invalid task/check contract, canonical answer rejected
by the checker, blueprint/quota/level/part violations, text tasks not sharing one text,
missing rule cards/links, < 3 analogs for a rule, non-NFC strings, invisible/bidi/control
characters, a vector graded differently than expected. Tests add independent derivations:

- `tests/test_content.py` — B13 sentences rebuilt from their comma positions must equal
  the authored correct sentence; transcriptions agree with the е/ё/ю/я rule (count of [й']);
  stress marks single and on vowels; texts fully annotated; paronym sets have one error;
  no maths leftovers; every interface key exists;
- `tests/test_lexicon.py` — OpenCorpora (pymorphy3): every correct spelling exists, every
  wrong completion is unknown unless listed in `HOMONYMS`/`FORM_POOLS` (stale allowances
  fail), bracket spellings exist, numerals equal pymorphy's inflection, verb aspect and
  noun declension agree with dictionary tags. This gate found real authoring errors
  (отрасль, загорелый, тротуар, ясный, разливается) before the first release;
- `tests/test_checker.py`, `answer_parity.js`, `AnswerCheckerTest.kt` — the vector corpus
  in Python, JavaScript and Kotlin.

Disputed norms are excluded instead of being made artificially unambiguous (stress words
with two accepted variants, disputed word-formation derivations, «в обнимку» etc.).
The only accepted alternative (`восемью`/`восьмью`) cites its checked source.

## Adding content

1. Add items to a pool (with a reason code) or a text/rule card; keep RU/EN parallel.
2. `python3 tools/build_content.py` and `python3 -m unittest tests.test_content tests.test_lexicon`.
3. If a wrong completion is a real word, either disambiguate the item with context or add
   it to `HOMONYMS` with a reason; never weaken the gate.
4. `python3 tools/sync_assets.py`, then the JS journeys. Commit sources and generated copies.
