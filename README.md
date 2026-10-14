# Репетитор ЦТ: Математика · CT Maths Tutor

Математический тренажёр для подготовки к **централизованному тестированию (ЦТ) по математике в Республике Беларусь** — Android-приложение и Windows-приложение с HTML-интерфейсом, собранные из одного общего ядра.

**Разработчик / Developer:** Захаревич Игорь (Zakharevich Igor) — [ziv@csl.by](mailto:ziv@csl.by) — [+3753371412](tel:+3753371412) — [WhatsApp](https://wa.me/3753371412)

[![CI](https://github.com/zigorminsk-debug/mathematics/actions/workflows/ci.yml/badge.svg)](https://github.com/zigorminsk-debug/mathematics/actions/workflows/ci.yml)
[Последняя автоматическая публикация](https://github.com/zigorminsk-debug/mathematics/releases/latest) · [Инструкции агентам](AGENTS.md) · [Журнал действий](docs/WORKLOG.md)

---

## Что умеет программа

| Требование | Реализация |
|---|---|
| База на основе заданий ЦТ за 6 лет | 6 полных вариантов экзаменационного формата **2021–2026**: по 18 заданий части А (выбор из пяти) и 12 заданий части В (краткий ответ) = **180 заданий** |
| Математический тренажёр | Режим тренировки (проверка сразу), экзаменационный режим (таймер 180 минут, без подсказок), бесконечная тренировка по темам (**552 однотипных задания** в 25 семействах) |
| Полный разбор ошибок | Для каждого неверного ответа: ваш ответ ↔ правильный ответ, **типичная причина ошибки** (каталог 106 диагнозов по тегам заданий), пошаговое решение, чек-лист самопроверки и **сразу открывающаяся тема для изучения** (конспект и формулы темы, экран «Изучение» с разобранными примерами) |
| Изучение определений и теорем | **56 подробных двуязычных материалов** для всех 18 тем: нажмите пункт «Что повторить», название раздела или любую из 116 формул — откроются определения, правила/теоремы с условиями применения и разобранный пример. В каждом материале есть бытовое объяснение; **52 графика/геометрические схемы** в 51 материале можно увеличить и прокрутить. Всё офлайн; «Назад» сохраняет задание, ответ, поиск и место чтения |
| Закрепление на аналогичных примерах | К каждой ошибке автоматически подбираются однотипные задания того же раздела с ответом и полным решением; на экране результата кнопка **«Закрепить похожими заданиями»** собирает отдельный прогон по всем ошибкам |
| Инструменты для решения | Калькулятор с клавиатурой (без `eval`), сборник формул с поиском (14 разделов, 116 формул), черновик с сохранением по заданию, построитель графиков функций, подсказки, сетка всех заданий варианта, отметки «вернуться», символы `√ π ² −` и ввод дробей |
| Статистика и прогресс | Пройдено вариантов, решено заданий, точность, время занятий, среднее время на задание, диаграммы по темам и годам, календарь активности, серия дней, цель на день, слабые темы с переходом в тренировку, экспорт отчёта в HTML |
| Наполнение базы новыми заданиями | `tools/build_content.py` проверяет и публикует банк, приложения обновляют его **поверх установленного** из `releases/latest/download` (манифест со SHA-256), прогресс не теряется |
| Подпись постоянным ключом | `android/keystore/ctmaths-release.p12` — постоянный ключ: каждый новый APK устанавливается поверх предыдущего без удаления и без потери статистики |
| Windows на Go с GUI и HTML | `windows/` — Go (только стандартная библиотека), HTML/CSS/JS интерфейс встроен в EXE через `go:embed`, окно открывается в режиме приложения (Edge/Chrome `--app`) |
| Автосборка и автопубликация | Каждый push запускает полный CI; после успеха **автоматически публикуются APK, оба Windows EXE и банк**. Номер версии повышается автоматически; PR/fork не публикуют. В Release входят журнал `release-info.json` и контрольные суммы |
| Контакты кликабельны | Экраны «О программе» и подвал: `mailto:`, `tel:`, WhatsApp, ссылка на исходный код (на Android открываются системными приложениями) |
| Переключение языка | Русский ⇄ English одной кнопкой в шапке: 188 строк интерфейса, условия, варианты, подсказки, разборы и отчёт — на двух языках (заодно технический английский) |
| Оформление | Светлая/тёмная тема (по системе или вручную) и три размера шрифта заданий — для работы при ярком свете и вечером |

---

## Как установить готовую сборку

1. Откройте [последний релиз](https://github.com/zigorminsk-debug/mathematics/releases/latest).
2. **Android** — скачайте `app-release.apk` и установите (разрешите установку из этого
   источника). Каждое следующее обновление ставится **поверх** без удаления приложения и
   без потери статистики: APK подписан постоянным ключом проекта, пакет один и тот же
   (`by.ziv.ctmaths`), а `versionCode` растёт с автоматически выделенной версией
   (`VERSION` задаёт исходный минимум; CI сверяет
   подпись с эталоном и пакет/версию собранного APK). Ставить нужно именно
   `app-release.apk`: в релиз он теперь входит один. Debug-сборка
   (`by.ziv.ctmaths.debug`) — отдельное приложение и устанавливается рядом с релизом.
   **Не удаляйте установленное приложение при ошибке установки**: это удалит его
   локальную статистику. Сначала выясните точный текст ошибки и какой APK был
   установлен. Если прежний APK подписан другим ключом, обновить его поверх без
   исходного ключа или корректной миграции подписи невозможно.
3. **Windows** — скачайте `CTMathsTutor-amd64.exe` (или `arm64` для ARM-устройств) и
   запустите: приложение работает офлайн, прогресс хранится в `%APPDATA%\CTMathsTutor`.
4. **База заданий** обновляется из того же релиза: в настройках нажмите
   «Проверить обновления» (или включите автообновление) — новые варианты и однотипные
   задания подтягиваются поверх установленных, статистика остаётся. Старый скачанный
   банк не перекрывает более новый встроенный банк APK/EXE; канал обновлений не
   может откатить его назад. На Android проверка выполняется в фоне, без блокировки интерфейса.

## Быстрый старт

### Android

```bash
# собрать подписанный APK (нужны JDK 17 и Android SDK 34)
cd android
gradle testDebugUnitTest        # проверка ответов (паритет Python ↔ JS ↔ Kotlin)
gradle assembleRelease          # app/build/outputs/apk/release/app-release.apk
```

`app-debug.apk` получается командой `gradle assembleDebug` (пакет `by.ziv.ctmaths.debug`,
устанавливается рядом с релизной версией отдельно).

### Windows

```powershell
# PowerShell, из корня репозитория
powershell -ExecutionPolicy Bypass -File windows\build.ps1            # dist\CTMathsTutor-amd64.exe
powershell -ExecutionPolicy Bypass -File windows\build.ps1 -Arch arm64
```

или просто запустить `go run .` в каталоге `windows/` — приложение поднимет локальный сервер,
откроет окно и будет хранить прогресс в `%APPDATA%\CTMathsTutor` (`--portable` — рядом с EXE).

### Контент и проверки

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt  # test/YAML + native syntax tools
python3 tools/build_content.py     # проверить все ответы точной арифметикой и собрать банк
python3 tools/sync_assets.py       # разложить интерфейс и банк по приложениям (--check в CI)
.venv/bin/python tools/check_syntax.py --require  # синтаксис Go и Kotlin (tree-sitter; --require в CI)
node tests/answer_parity.js        # паритет проверки ответов (Python ↔ JS) и статистики
node tests/content_schema.js       # структура банка, тем для изучения и манифеста периодов
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'  # APK, учебные материалы, release policy/workflow gates
# необязательно: сквозные тесты интерфейса в jsdom
npm install --no-save jsdom
node tests/ui_smoke.js             # прогон интерфейса: вариант → разбор → закрепление → статистика
node tests/native_smoke.js         # тот же интерфейс через мост Android (поддельный CTNative)
node tests/theory_smoke.js         # все кликабельные пункты/формулы, RU/EN, офлайн, возврат и сохранение ввода
```

## Структура репозитория

```
content_src/       исходники заданий (Python): kit.py (модель и проверка ответов), periods.py
                   (годы ЦТ), task_bank_2021…2026.py, templates.py, templates_extra.py,
                   formulas.py, ui_strings.py, mistakes.py, study.py и theory.py (конспекты и теория),
                   intuition.py (бытовые объяснения), diagrams.py (точные локальные схемы)
tools/             build_content.py (проверка + сборка банка), sync_assets.py (единый интерфейс),
                   check_syntax.py (синтаксис Go/Kotlin), release_plan.py (автоверсия),
                   publish_release.py (checked artifacts → verified draft → latest)
dist/content/      собранный банк (генерируется, в git не хранится): bank.json, analogous.json,
                   formulas.json, ui_strings.json, mistakes.json, topics.json,
                   answer_vectors.json и version.json — манифест с SHA-256, периодами
                   и дисклеймером
webapp/            общий интерфейс (index.html, styles.css, core.js, app.js) — одна кодовая база
                   для Android WebView и для Windows
android/           приложение Android (Gradle, Kotlin), src/main/assets/webapp — копия интерфейса,
                   keystore/ — постоянный ключ подписи
windows/           приложение Windows на Go (main.go, store.go), go:embed web/
tests/             answer_parity.js (проверка ответов и статистики), content_schema.js,
                   ui_smoke.js, native_smoke.js и theory_smoke.js (интерфейс, офлайн SVG/zoom),
                   test_theory.py, test_diagrams.py (схемы, математика, безопасные примитивы)
AGENTS.md          правила и handoff для любого следующего агента
docs/              ARCHITECTURE.md, CONTENT.md, RELEASE.md, WORKLOG.md
.github/workflows/ ci.yml (полная проверка + автопубликация), publish.yml (same-run artifacts),
                   release.yml (tag/manual recovery с теми же полными gates)
```

## Как это работает

1. **Задания** описываются в Python: условие, варианты, ответ, пошаговое решение и подсказки — на русском и английском. Каждое задание обязано иметь `check()` — проверку ответа **точной арифметикой** (дроби, корни, тригонометрия). Сборка падает, если хоть один ответ неверен.
2. **Банк** собирается в JSON и попадает и в APK, и в EXE. Оба приложения офлайн-первичны: все задания хранятся на устройстве.
3. **Проверка ответов** реализована трижды — Python (авторство), JavaScript (интерфейс), Kotlin (нативный код Android) — и сверяется общими векторами `answer_vectors.json`.
4. **Обновление базы**: приложение обращается к `.../releases/latest/download/version.json`, сравнивает версию, проверяет SHA-256 каждого файла и кладёт новую базу рядом с установленной; при следующем запуске используется она, а прогресс остаётся нетронутым.
5. **Однотипные задания**: генераторы `templates.py` и `templates_extra.py` детерминированно создают 552 задания 25 семейств; они используются и для закрепления ошибок, и в режиме бесконечной тренировки.
6. **Годы ЦТ** описаны одним списком в `content_src/periods.py`: состав частей, время на вариант и подписи попадают в `version.json`, поэтому новый год добавляется одной записью, а не правками в интерфейсе.

Подробности — в [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), как добавлять задания — в
[docs/CONTENT.md](docs/CONTENT.md), как работают автоматические выпуски — в [docs/RELEASE.md](docs/RELEASE.md).
Для продолжения работы агентом — [AGENTS.md](AGENTS.md) и [docs/WORKLOG.md](docs/WORKLOG.md).

## Дисклеймер

Задания составлены автором по мотивам открытых материалов ЦТ соответствующих лет и **не являются**
официальными материалами РИКЗ. Проект — учебное пособие для самоподготовки.

## Лицензия

MIT (см. [LICENSE](LICENSE)) — свободно используйте для подготовки к экзамену.

---

## English summary

A maths trainer for the Belarusian centralised testing (CT) exam, built as **one shared
offline web interface** running inside an Android WebView and inside a Go/Windows shell:

* 6 full exam-format variants (2021–2026, 180 tasks) written by the author in the CT style,
  plus deterministic generators with 552 analogous tasks for consolidation;
* every wrong answer gets a full analysis: your answer vs. the correct one, the typical cause
  of the mistake, the step-by-step solution, the automatically opened study topic (summary,
  formulas and worked examples) and similar tasks with worked solutions;
* 56 offline bilingual lessons with definitions, rules/theorems, worked examples and
  everyday explanations (shopping, fractions, ladders, clocks, speed); 52 local vector
  graphs/geometry diagrams in 51 lessons support zoom/pan without CDN or downloads,
  opened by tapping a revision point, a formula section or any formula; Back preserves
  the task, answer and formula search;
* exam mode with a 180-minute timer, practice mode, endless topic drilling;
* tools available during a test: calculator, searchable formula sheet, scratchpad,
  function plotter, hints;
* statistics: accuracy by topic and by year, streaks, daily goal, weak topics, HTML report;
* Russian ⇄ English switch (188 interface strings) covers statements, hints, every solution step
  and the exported report; light/dark theme and three task font sizes;
* the task bank updates itself in place from the GitHub release feed (SHA-256 verified),
  and the Android release is signed with a constant key so updates install over the old
  build (CI compares the APK certificate with the committed fingerprint and checks that the
  package and the VERSION-derived versionCode of the built APK are the expected ones).

Tests: `node tests/answer_parity.js`, `node tests/content_schema.js`, and the jsdom journeys
`node tests/ui_smoke.js` / `node tests/native_smoke.js`.
Build: `cd android && gradle assembleRelease` · `windows/build.ps1`.
Every trusted repository push automatically publishes the checked release APK, both EXEs
and content after all gates pass. Effective versions increase without manual VERSION bumps;
PR/fork builds never publish. Each release includes an immutable machine-readable audit
(`release-info.json`) and checksums; see `AGENTS.md` and `docs/WORKLOG.md` for agent handoff.
