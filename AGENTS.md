# AGENTS.md — «Репетитор ЦТ: Физика» (ветка физики репозитория `zigorminsk-debug/mathematics`)

Это **отдельное приложение по физике** для подготовки к ЦТ (Беларусь): Android APK
и два Windows-EXE (amd64/arm64), офлайн-теория, авторские тренировочные варианты,
проверка физических величин с единицами и размерностями, автопубликация релизов.

Читать в этом порядке: **AGENTS.md → docs/WORKLOG.md → docs/CONTENT.md →
docs/RELEASE.md → docs/ARCHITECTURE.md → docs/subjects/PHYSICS.md** (техзадание
пользователя) и `docs/subjects/README.md` (условия изоляции от математики).

## 1. Идентичность предмета (не менять без явной просьбы)

Один источник правды — `tools/subject.py`:

| Свойство | Значение физики | Математика (чужая, не трогать) |
|---|---|---|
| subject | `physics` | `mathematics` |
| теги релизов | `physics-vYYYY.M.P` | `vYYYY.M.P` |
| Android package | `by.ziv.ctphysics` (+ `.debug`) | `by.ziv.ctmaths` |
| Windows EXE | `CTPhysicsTutor-{amd64,arm64}.exe` | `CTMathsTutor-…` |
| Windows данные | `%APPDATA%\CTPhysicsTutor`, профиль Edge `ctphysics-window` | `CTMathsTutor` |
| APK в релизе | **`phyzics.apk`** (имя, которое просил пользователь; сборка Gradle остаётся `app-release.apk`, переименование делает шаг публикации) | `app-release.apk` |
| подпись | `android/keystore/ctphysics-release.p12`, отпечаток в `android/keystore/expected-cert-sha256.txt` | `ctmaths-release.p12` |
| очередь CI | `ctphysics-release-pipeline` | `ctmaths-release-pipeline` |
| канал обновления | `https://github.com/<repo>/releases/download/physics-v<version>` (через Releases API), **без** `/releases/latest/download` | глобальный `latest` |

Правила, которые нельзя нарушать:

1. Физика публикуется **только** как `make_latest=false`. Глобальный latest
   репозитория обязан оставаться математическим (`tools/publish_release.py`
   падает, если id `releases/latest` изменился во время публикации физики).
2. Ни одна команда не пишет в математические ветки/теги/пакеты и не переиспользует
   математический сертификат. Установленные приложения сосуществуют; статистика,
   настройки, профили WebView/Edge и загруженный банк — раздельные.
3. Авторские задания не выдаются за материалы РИКЗ: дисклеймер лежит в
   `content_src/periods.py`, попадает в `version.json` и в экран «О программе».
4. Формат варианта (не наследуется от математики!): **часть A — 10 заданий с
   выбором ответа, часть B — 20 заданий с кратким ответом, 210 минут** — перечень
   РИКЗ (см. `content_src/periods.py`, проверено 2026-10-14).
5. Не объявлять успех по одной проверке синтаксиса: релиз подтверждается реальным
   запуском CI и фактическим Release (tag, SHA, инвентарь, digests, math latest).

## 2. Состояние на 2026-10-14 (честно, проверено запуском команд)

| Часть | Состояние | Чем проверено |
|---|---|---|
| Контент-ядро (`content_src/quantities.py`, `kit.py`, `mistakes.py`) | **готово** | `python3 -m unittest tests.test_quantities` → 32 теста OK |
| Варианты 2021–2026 (по 30 заданий) | **готово**, 180/180 заданий | `python3 tools/build_content.py --check` |
| Генератор аналогичных заданий | **готово**, 39 заданий, 13 тем | там же |
| Теория (37 уроков RU/EN, бытовые объяснения и границы модели) | **готово** | `tools/build_content.py` проверяет структуру и ссылки на схемы |
| Схемы (26 типизированных SVG) | **готово** | `content_src/diagrams.py` + проверка в сборке |
| Конспекты, формулы, типичные ошибки | **готово** | проверки ссылок в `tools/build_content.py` |
| Контент-фид `dist/content/*.json` (8 файлов) | **собирается** | `python3 tools/build_content.py` (bank 180, analogous 39) |
| Изоляция релизов (planner/publisher/update resolver, workflow) | **готово в коде** | `tools/subject.py` + патчи в `release_plan.py`, `publish_release.py`, `check_apk_update.py`, `.github/workflows/*` |
| Подпись Android | **готова**: PKCS12, отпечаток `A3:55:CB:12:F5:22:E9:A7:F6:FE:E3:A6:6C:E9:15:1D:73:23:40:58:A9:85:FA:57:19:CD:28:3E:63:21:35:83` | `tools/check_signature.py --require --keystore android/keystore/ctphysics-release.p12` |
| **webapp (JS-интерфейс + проверка ответов)** | **НЕ портирован**: в `webapp/` лежит математический интерфейс (математический чекер, математические экраны) | `node --check` проходит, но логика чужая |
| **Android (Kotlin)** | **НЕ портирован**: `android/app/src/main/java/by/ziv/ctmaths/*` — математический пакет и математический `AnswerChecker` | `tests/test_android_build.py` ещё проверяет `ctmaths` |
| **Windows (Go)** | **НЕ портирован**: `windows/*.go` — `CTMathsTutor` и математические каталоги данных | `go` в песочнице отсутствует, проверка будет в CI |
| Тесты | портирован только `tests/test_quantities.py`; `test_release.py`, `test_theory.py`, `test_diagrams.py`, `test_android_build.py`, JS-смоуки — ещё математические | — |
| Релиз физики | **нет** (ни одного `physics-v*` тега) | — |

**Вывод для следующего агента:** контент и правила релиза готовы, приложения — нет.
CI на первом push физики пройдёт шаг `prepare` и большую часть `content`, но упадёт
на `node tests/answer_parity.js` / смоуках / нативных шагах, пока `webapp/`,
`android/`, `windows/` не переписаны под физику.

## 3. Команды (локально, всё выполнимо в песочнице без Go/JDK)

```bash
python3 tools/build_content.py            # собрать и проверить весь контент
python3 tools/build_content.py --check    # только проверить (режим CI)
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tools/check_signature.py --require --keystore android/keystore/ctphysics-release.p12
node --check webapp/core.js && node --check webapp/app.js
```

Чего в песочнице **нет** и что проверяется только CI: `go`, `java`, `gradle`,
`keytool`, `apksigner`, `aapt2`. Никогда не писать «собрано/протестировано
локально» про нативные артефакты: их собирает GitHub Actions.

## 4. Карта репозитория

```
content_src/            авторские модули (источник правды контента)
  quantities.py         единицы, размерности, парсер чисел, проверка ответа, модели
  kit.py                конструкторы заданий Task/calc_task/calc_choice_task + векторы ответов
  variants.py           движок вариантов 2022–2026 (рецепты + числа по годам)
  task_bank_2021.py …   шесть вариантов (2021 — руками, 2022–2026 — движок)
  templates.py          генератор аналогичных заданий (39, все 13 тем)
  theory.py             37 уроков: определения, условия, пример, «бытовое» + границы модели
  diagrams.py           26 схем: типизированный SVG (без raw SVG/eval/CDN)
  formulas.py, study.py, mistakes.py, periods.py, ui_strings.py
tools/
  subject.py            идентичность предмета (см. §1)
  build_content.py      конвейер: проверки → dist/content/*.json → ассеты приложений
  release_plan.py       версия/тег/lineage только physics-v*
  publish_release.py    публикация draft → Release с make_latest=false
  check_apk_update.py   пакет/versionCode/обновление поверх прошлого APK
  check_signature.py, check_syntax.py, sync_assets.py
dist/content/           собранный фид (в git не хранится; копируется в приложения)
webapp/ android/ windows/  интерфейс и нативные оболочки (ожидают портирования)
docs/                   WORKLOG.md, CONTENT.md, RELEASE.md, ARCHITECTURE.md, subjects/
```

## 5. Ближайшие шаги (порядок работ, см. docs/WORKLOG.md §«Что дальше»)

1. **webapp**: заменить математический чекер (`webapp/core.js` §3) на физический по
   контракту `spec` из `dist/content/answer_vectors.json`; экраны — под поля
   `given/unit/spec/dimension/model/distractors`; добавить инструмент «Единицы».
2. **tests**: переписать `answer_parity.js`, `content_schema.js`, смоуки, а также
   `test_release.py`, `test_theory.py`, `test_diagrams.py`, `test_android_build.py`
   под физику и `tools/subject.py`.
3. **android**: пакет `by.ziv.ctphysics`, label из `ui_strings`, `AnswerChecker.kt`
   по тому же контракту (те же векторы), ресурсы из `res/values{,-ru}`.
4. **windows**: `CTPhysicsTutor`, `%APPDATA%\CTPhysicsTutor`, профиль
   `ctphysics-window`, subject-scoped resolver (Releases API, без глобального latest).
5. Проверить `tools/sync_assets.py`, затем первый trusted push в
   `arena/f7b88593-mathematics` → дождаться настоящего CI → первый `physics-v*`
   Release с `make_latest=false`; убедиться, что математический latest не изменился.
6. Записать фактический run/release в `docs/WORKLOG.md` и машинный audit релиза.
