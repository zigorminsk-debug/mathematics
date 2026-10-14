# Архитектура / Architecture — «Репетитор ЦТ: Русский язык»

Один общий интерфейс (`webapp/`) работает и в Android (WebView), и в Windows (Go-сервер на
loopback + окно Edge/Chrome `--app`); различия платформ — за мостом: `window.CTNative`
(Kotlin) и локальный HTTP API `/api/...` (Go).

```
content_src/*.py  (пулы материала, тексты, правила, схемы, чекер, векторы)
        │  tools/build_content.py  — план 40 заданий, квоты РИКЗ 2026, Unicode, связи, векторы
        ▼
dist/content/*.json (bank, analogous, topics, rules, ui_strings, mistakes, answer_vectors, version)
        │  tools/sync_assets.py  — точное зеркало (лишние файлы удаляются)
   ┌────┴─────────────────────────┐
   ▼                              ▼
windows/web/ (go:embed)      android/app/src/main/assets/webapp/
windows/main.go, store.go    MainActivity.kt, NativeBridge.kt, UpdateFeed.kt, AnswerChecker.kt
   └────────────┬─────────────────┘
                ▼
webapp/core.js — мост, i18n, ПРЕДМЕТНЫЙ ЧЕКЕР, загрузка только своего банка, аналитика
webapp/app.js  — экраны, элементы ответа по типам, карточки правил, схемы, «Правила», отчёт
```

## Content (`content_src/`, `tools/`)

See `docs/CONTENT.md`. The builder produces language-neutral Russian material plus
bilingual instructions/explanations; Russian text is never translated (EN switches only
the interface/explanations). Android string resources are generated from `ui_strings.py`.

## Answer checking

`checker.py` (reference) = `CT.answer.checkSpec` (core.js) = `AnswerChecker.check` (Kotlin).
Types: multi (part A, several of five), single, numbers (unordered set / ordered sequence),
word (explicit case/ё/hyphen policy, significant spaces), stress (acute or capitalised
vowel), match (А1Б2…), integer. Parity: `answer_vectors.json` (123 hand-written vectors)
in all three implementations, plus every canonical task answer in JS.

## Interface (`webapp/app.js`)

- Screens: home, variants, exam (120 min timer, no checking/hints), run (training with
  analysis after each answer), result, mistakes (by rule, reinforcement with analogs),
  practice by area, study by area (rule list → cards), **«Правила»** (search over all
  cards), statistics (areas, weakest rules), tools (rule search, memos, scratchpad with
  ё/«»/—/stress mark), settings (RU/EN, theme, text 0.9–1.3, exam minutes, goal), about.
- Answer controls: option toggles (several selections), numbered chips + input (order
  badges for sequences), word input with autocorrect/spellcheck/capitalisation off,
  stress letter buttons, match selects, numeric input.
- Remediation is rule-specific: misjudged options of a set answer → their `itemRules` →
  typical-error diagnosis, rule cards and analogous exercises of those rules.
- Visuals: typed SVG (viewer: zoom 100–300 %, internal pan, one-level Back restoring
  DOM/scroll/focus), semantic HTML tables (caption/th, focusable scroll region) and decision
  trees (nested lists with Да/Нет). No raw markup/URLs/eval anywhere (validated at build
  and again in the renderer).
- Calculator, plotter and maths formula sheets are removed.

## Native shells

- Android (`by.ziv.ctrussian`): WebViewAssetLoader host, Back delegated to the page,
  text zoom follows the system font scale, private storage per package (statistics are
  separate from the mathematics app), subject-scoped updates (`UpdateFeed.kt`).
- Windows (`CTRussianTutor-*.exe`): stdlib-only Go server on 127.0.0.1, data in
  `%APPDATA%\CTRussianTutor`, browser profile `ctrussian-window`, subject-scoped updates
  (`store.go`), atomic content packs, foreign/stale overlays ignored.

## Release

See `docs/RELEASE.md` (family `russian-v…`, `make_latest=false`, latest verified unchanged).
