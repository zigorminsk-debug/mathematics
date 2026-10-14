# Репетитор ЦТ: Математика · CT Maths Tutor

Математический тренажёр для подготовки к **централизованному тестированию (ЦТ) по математике в Республике Беларусь** — Android-приложение и Windows-приложение с HTML-интерфейсом, собранные из одного общего ядра.

**Разработчик / Developer:** Захаревич Игорь (Zakharevich Igor) — [ziv@csl.by](mailto:ziv@csl.by) — [+3753371412](tel:+3753371412) — [WhatsApp](https://wa.me/3753371412)

[![CI](https://github.com/zigorminsk-debug/mathematics/actions/workflows/ci.yml/badge.svg)](https://github.com/zigorminsk-debug/mathematics/actions/workflows/ci.yml)
[![Release](https://github.com/zigorminsk-debug/mathematics/actions/workflows/release.yml/badge.svg)](https://github.com/zigorminsk-debug/mathematics/actions/workflows/release.yml)

---

## Что умеет программа

| Требование | Реализация |
|---|---|
| База на основе заданий ЦТ за 5 лет | 5 полных вариантов экзаменационного формата **2021–2025**: по 18 заданий части А (выбор из пяти) и 12 заданий части В (краткий ответ) = **150 заданий** |
| Математический тренажёр | Режим тренировки (проверка сразу), экзаменационный режим (таймер 180 минут, без подсказок), бесконечная тренировка по темам (**200 однотипных заданий**) |
| Полный разбор ошибок | Для каждого неверного ответа: ваш ответ ↔ правильный ответ, **типичная причина ошибки** (каталог 130+ диагнозов), пошаговое решение, чек-лист самопроверки |
| Закрепление на аналогичных примерах | К каждой ошибке автоматически подбираются 1–2 однотипных задания того же раздела с ответом и полным решением |
| Инструменты для решения | Калькулятор (без `eval`), сборник формул с поиском (11 разделов), черновик, построитель графиков функций, подсказки, навигация по заданиям, отметки «вернуться», возможность вводить `√ π / ² −` |
| Статистика и прогресс | Пройдено тестов, решено заданий, точность, среднее время на задание, диаграммы по темам и годам, серия дней, цель на день, слабые/сильные темы, экспорт отчёта в HTML |
| Наполнение базы новыми заданиями | `tools/build_content.py` проверяет и публикует банк, приложения обновляют его **поверх установленного** из `releases/latest/download` (манифест со SHA-256), прогресс не теряется |
| Подпись постоянным ключом | `android/keystore/ctmaths-release.p12` — постоянный ключ: каждый новый APK устанавливается поверх предыдущего без удаления и без потери статистики |
| Windows на Go с GUI и HTML | `windows/` — Go (только стандартная библиотека), HTML/CSS/JS интерфейс встроен в EXE через `go:embed`, окно открывается в режиме приложения (Edge/Chrome `--app`) |
| Автосборка на GitHub Actions | `.github/workflows/ci.yml` — сборка APK и EXE после каждого изменения; `release.yml` — публикация подписанного APK, EXE и обновляемого банка заданий |
| Контакты кликабельны | Экраны «О программе» и подвал: `mailto:`, `tel:`, WhatsApp, ссылка на исходный код (на Android открываются системными приложениями) |
| Переключение языка | Русский ⇄ English одним нажатием; формулировки и пошаговые решения на двух языках, включая технический английский |

---

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
python3 tools/build_content.py     # проверить все ответы точной арифметикой и собрать банк
python3 tools/sync_assets.py       # разложить интерфейс и банк по приложениям
node tests/answer_parity.js        # паритет алгоритма проверки ответов (Python ↔ JS)
```

## Структура репозитория

```
content_src/       исходники заданий (Python): kit.py, year2021…year2025.py, templates.py,
                   formulas.py, ui_strings.py, mistakes.py
tools/             build_content.py (проверка + сборка банка), sync_assets.py (единый интерфейс)
dist/content/      собранный банк: bank.json, analogous.json, formulas.json, ui_strings.json,
                   mistakes.json, topics.json, version.json (манифест с SHA-256)
webapp/            общий интерфейс (index.html, styles.css, core.js, app.js) — одна кодовая база
                   для Android WebView и для Windows
android/           приложение Android (Gradle, Kotlin), src/main/assets/webapp — копия интерфейса,
                   keystore/ — постоянный ключ подписи
windows/           приложение Windows на Go (main.go, store.go), go:embed web/
tests/             answer_parity.js — сверка алгоритма проверки ответов
docs/              ARCHITECTURE.md, CONTENT.md, RELEASE.md
.github/workflows/ ci.yml (автосборка), release.yml (релиз + обновляемый банк)
```

## Как это работает

1. **Задания** описываются в Python: условие, варианты, ответ, пошаговое решение и подсказки — на русском и английском. Каждое задание обязано иметь `check()` — проверку ответа **точной арифметикой** (дроби, корни, тригонометрия). Сборка падает, если хоть один ответ неверен.
2. **Банк** собирается в JSON и попадает и в APK, и в EXE. Оба приложения офлайн-первичны: все задания хранятся на устройстве.
3. **Проверка ответов** реализована трижды — Python (авторство), JavaScript (интерфейс), Kotlin (нативный код Android) — и сверяется общими векторами `answer_vectors.json`.
4. **Обновление базы**: приложение обращается к `.../releases/latest/download/version.json`, сравнивает версию, проверяет SHA-256 каждого файла и кладёт новую базу рядом с установленной; при следующем запуске используется она, а прогресс остаётся нетронутым.
5. **Однотипные задания**: генератор `templates.py` детерминированно создаёт 200 заданий 20 семейств; они используются и для закрепления ошибок, и в режиме бесконечной тренировки.

Подробности — в [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), как добавлять задания — в
[docs/CONTENT.md](docs/CONTENT.md), как выпускать обновления — в [docs/RELEASE.md](docs/RELEASE.md).

## Дисклеймер

Задания составлены автором по мотивам открытых материалов ЦТ соответствующих лет и **не являются**
официальными материалами РИКЗ. Проект — учебное пособие для самоподготовки.

## Лицензия

MIT (см. [LICENSE](LICENSE)) — свободно используйте для подготовки к экзамену.

---

## English summary

A maths trainer for the Belarusian centralised testing (CT) exam, built as **one shared
offline web interface** running inside an Android WebView and inside a Go/Windows shell:

* 5 full exam-format variants (2021–2025, 150 tasks) written by the author in the CT style,
  plus a deterministic generator with 200 analogous tasks for consolidation;
* every wrong answer gets a full analysis: your answer vs. the correct one, the typical cause
  of the mistake, the step-by-step solution and similar tasks with worked solutions;
* exam mode with a 180-minute timer, practice mode, endless topic drilling;
* tools available during a test: calculator, searchable formula sheet, scratchpad,
  function plotter, hints;
* statistics: accuracy by topic and by year, streaks, daily goal, weak topics, HTML report;
* Russian ⇄ English switch covers statements, hints and every solution step;
* the task bank updates itself in place from the GitHub release feed (SHA-256 verified),
  and the Android release is signed with a constant key so updates install over the old build.

Build: `cd android && gradle assembleRelease` · `windows/build.ps1` · CI does both automatically.
