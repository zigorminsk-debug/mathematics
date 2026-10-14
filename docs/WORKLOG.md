# WORKLOG — журнал работ по физике

Записи ведутся по датам, фактам и проверкам. Формат: что сделано → чем проверено →
что осталось. Никаких «готово» без команды, которую можно повторить.

## 2026-10-14 — сессия Arena: изоляция предмета и полный контент

### Исходная точка

* Ветка сессии: `arena/f7b88593-mathematics`, база — merge `f485a56`
  (старый `main` `22547d6` + handoff-коммит `b261274` = `v2026.10.8`).
  **Старый `main` как база не подходит**: в нём нет `docs/subjects`,
  теории/схем и истории автопубликации.
* Проверенная математическая база (не трогать): `aa46e76558e389f3fb64564f6ce4ea45aeab32a0`
  = `v2026.10.7`, versionCode `261007`, 13 ассетов, сертификат `B2:BD:…:65`.
* Задача: «Репетитор ЦТ: Физика» — самостоятельное приложение (APK + 2 EXE),
  авторские варианты, RU/EN, офлайн-теория, проверка физических величин,
  автопубликация с `make_latest=false` и неизменной математикой.

### Сделано и проверено

1. **Формат экзамена сверен с источником** (не унаследован от математики):
   перечень РИКЗ для ЦЭ/ЦТ/РЦЭ 2025 — физика: 10 заданий части A + 20 части B,
   всего 30, 210 минут; проверено 2026-10-14, записано в `content_src/periods.py`
   и `docs/CONTENT.md`. Математические 18A+12B/180 минут сюда не переносились.
2. **Изоляция предмета в коде**: `tools/subject.py` — источник правды
   (`subject=physics`, теги `physics-v*`, `by.ziv.ctphysics`, `CTPhysicsTutor`,
   `%APPDATA%\CTPhysicsTutor`, профиль `ctphysics-window`, отдельная очередь
   `ctphysics-release-pipeline`). `release_plan.py` видит только физическую семью
   тегов, `publish_release.py` ставит `make_latest=false` и падает, если
   repository latest изменился, `check_apk_update.py` знает пакет физики,
   workflow-файлы переименованы на физические артефакты и ключ.
3. **Подпись зафиксирована до первого APK**: новый постоянный ключ
   `android/keystore/ctphysics-release.p12` (alias `ctphysics`), отпечаток
   записан в `android/keystore/expected-cert-sha256.txt` и проверяется CI:
   `A3:55:CB:12:F5:22:E9:A7:F6:FE:E3:A6:6C:E9:15:1D:73:23:40:58:A9:85:FA:57:19:CD:28:3E:63:21:35:83`.
4. **Ядро физических величин** `content_src/quantities.py` (1130 строк):
   белый список единиц СИ и школьных внесистемных, приставки, °C со смещением,
   точная арифметика `Fraction`, парсер школьной записи (`12,5`, `1,5·10⁻³`,
   `1.5e-3`, `3·10⁵`), размерности, `check_answer` с причинами
   (`empty/unit/dimension/missing_unit/value`), модель-парсер формул
   (целые степени, включая отрицательные; дробные запрещены). Проверено:
   `python3 -m unittest tests.test_quantities` → **32 теста OK**.
5. **Инструментарий автора** `content_src/kit.py`: `calc_task`/`calc_choice_task`
   выводят ответ из модели точной арифметикой, проверяют размерность формулы и
   единиц, домены, наличие объяснений у неверных вариантов; реализованы
   **постоянные задания** (g, ρ, k, h, c): значение попадает в «Дано», а не в
   «магическое число» внутри формулы; добавлен страж незаполненных подстановок
   `{symbol}`. 15 общих векторов ответов (`ANSWER_VECTORS`) для Python/JS/Kotlin.
6. **Банк 2021–2026**: 6 вариантов × 30 заданий = **180 заданий**, каждое
   проверено ядром. 2021 написан руками (`task_bank_2021.py`), 2022–2026 —
   движок `variants.py`: рецепты с числами по годам, дистракторы выводятся из
   **моделей типичных ошибок** (забыт ½, потерян g, не переведены единицы), а
   совпадение дистрактора с верным ответом роняет сборку.
7. **Аналогичные задания** `templates.py`: 39 детерминированных заданий,
   покрытие **всех 13 тем** программы; проверено `tools/build_content.py`.
8. **Теория и наглядность**: 37 двуязычных уроков (`theory.py`) — определение,
   условия применимости, разобранный пример, «бытовое» объяснение с честными
   границами модели; 26 схем (`diagrams.py`) — типизированный SVG 420×280 без
   raw SVG/CDN/eval, с проверками геометрии и подписей.
9. **Конспекты, формулы, типичные ошибки**: 13 конспектов «что открыть после
   ошибки», 13 групп формул со ссылками на уроки, 52 тега типичных ошибок —
   всё связано проверками сборки (нет висячих ссылок и недостижимых уроков).
10. **Строки интерфейса** `ui_strings.py`: 213 надписей RU/EN; 40 значений
    заданы именно для физики (название, дисклеймер, подсказка ответа с единицей,
    правила экзамена 10A+20B, «Единицы и размерности», разбор причин ошибок),
    остальные — общие платформенные. Сборка падает, если интерфейс использует
    ключ, которого нет в файле.
11. **Конвейер контента** `tools/build_content.py` (переписан под физику):
    собирает `dist/content/{bank,analogous,topics,formulas,mistakes,ui_strings,
    answer_vectors,version}.json` (bank 180, analogous 39, уроков 37, схем 26),
    проверяет: полный состав вариантов по `periods.py`, покрытие 13 тем,
    параллельность ru/en, ссылки теории/конспектов/формул, оценку векторов
    ядром, отсутствие «чужих» предметных названий, ключи интерфейса; копирует
    фид в ассеты Android и Windows и генерирует `strings.xml`. Проверено:
    `python3 tools/build_content.py` — успешно, `--check` — успешно.
12. **Имя APK**: по просьбе пользователя публикуемый APK называется
    **`phyzics.apk`**: сборка Gradle остаётся `app-release.apk`, переименование
    делает шаг публикации (`publish.yml`), а инвентарь релиза и проверка
    обновления используют `subject.APK_ASSET = "phyzics.apk"`.
13. **Документация**: `AGENTS.md`, `docs/{WORKLOG,CONTENT,RELEASE,ARCHITECTURE}.md`
    переписаны под физику, включая честный статус и порядок работ.

### Чего ещё нет (важно для следующего агента)

* `webapp/`, `android/`, `windows/` — **всё ещё математические**: интерфейс
  использует математический чекер, Kotlin-пакет `by.ziv.ctmaths`, Go-приложение
  `CTMathsTutor`. До их портирования CI физики **не может** дойти до публикации.
* Математические тесты (`test_release.py`, `test_theory.py`, `test_diagrams.py`,
  `test_android_build.py`) и JS-смоуки не переписаны.
* Ни одного тега `physics-v*`, ни одного релиза физики; install-test на реальном
  телефоне/Windows **не проводился** и не должен упоминаться как проведённый.

### Что дальше (проверяемый план)

1. `webapp/core.js`: §3 «проверка ответов» заменить физическим чекером по
   контракту `spec`; добавить инструмент «Единицы» (белый список из
   `quantities.units_payload()`); экраны — под `given/unit/dimension/model`.
2. `tests/answer_parity.js` — гонять `dist/content/answer_vectors.json` через JS
   и сравнивать с Python (причины ошибок тоже); `content_schema.js` — под
   физическую схему; смоуки — под физические тексты.
3. `android/`: пакет/лейбл/ресурсы `by.ziv.ctphysics`, `AnswerChecker.kt` по тому
   же контракту и векторам, unit-тесты как у Python.
4. `windows/`: `CTPhysicsTutor`, `%APPDATA%\CTPhysicsTutor`, профиль
   `ctphysics-window`, subject-scoped обновление через Releases API.
5. Первый trusted push → дождаться **фактического** CI → проверить Release
   (tag `physics-v…`, `make_latest=false`, инвентарь с `phyzics.apk` и двумя EXE,
   SHA256SUMS, audit), убедиться, что математический latest не изменился, и
   записать результат сюда.

## 2026-10-14 — первый автозапуск CI физики (фактический результат)

* Push ветки `arena/f7b88593-mathematics`, коммит `1fff615`.
* Run [38548137521](https://github.com/zigorminsk-debug/mathematics/actions/runs/38548137521)
  — итог `failure`, и это **ожидаемое** состояние середины миграции:
  * «Resolve effective build version» — **success**: планировщик отработал по
    физической семье тегов и не тронул математическую;
  * «Content & web (verify, parity, assets)» — **failure на шаге
    «Answer-checker parity (Python ↔ JS ↔ Kotlin vectors)»**; до него успешно
    прошли `tools/build_content.py`, `tools/sync_assets.py --check`,
    `git diff --exit-code` по ассетам, `--apply-version` и `node --check`;
  * «Windows app (Go)» — **success** (`go vet`, `go test`, сборки amd64/arm64);
    важно: в дереве пока математический Go-код, поэтому такой успех **не**
    означает готовности физики;
  * «Android app (APK)» — **failure на шаге «Unit tests (answer checker parity,
    Kotlin)»**: математический тест векторов ещё читает старый формат векторов;
  * «Publish verified builds automatically» — **skipped**: релиза физики нет.
* Математика не затронута: repository latest по-прежнему `v2026.10.8`
  (13 ассетов, опубликован 2026-10-14T09:09:31Z), тегов `physics-v*` не существует.

### Следующие ворота (в порядке прохождения CI)

1. `webapp/core.js`: физический чекер по `spec` + `tests/answer_parity.js` на
   `dist/content/answer_vectors.json` → шаг парности перестанет падать.
2. `tests/content_schema.js` и `python3 -m unittest discover -s tests` — под
   физическую схему и `tools/subject.py`.
3. `webapp/app.js` + `tests/*_smoke.js` — экраны под `given/unit/spec/model`.
4. `android/` (пакет, лейбл, `AnswerChecker.kt`, ресурсы) и `windows/`
   (идентичность, каталоги данных, subject-scoped обновление).
5. Только после этого — первый `physics-v*` Release с `make_latest=false`, два
   EXE и `phyzics.apk`, и проверка, что математический latest не изменился.

---

## 2026-10-14 (продолжение): красный CI разобран, порт завершён

Красная сборка (runs 38548137521, 38548422293) падала **не из-за контента**, а
из-за половинчатого коммита: в дереве уже были физические `content_src/kit.py`,
`webapp/core.js` и `dist/content/*.json`, но `tests/answer_parity.js` и
`android/…/AnswerCheckerTest.kt` оставались в математическом формате векторов.
Локально это не воспроизводилось только потому, что нужные правки лежали
незакоммиченными. Вывод для следующего агента: **перед пушем прогонять
`python3 tools/build_content.py` на чистом worktree** (`git worktree add --detach`)
— CI собирает `dist/` заново и видит ровно то, что запушено.

### Что исправлено в этом коммите

* `tests/answer_parity.js` + `tests/unit_vectors.json` — физический формат
  векторов (`{cases:[{id, spec, cases[…]}]}`), 92 единицы и 16 векторов,
  сверка причины отказа (`empty|unit|dimension|missing_unit|value`);
* `android/app/src/main/.../by/ziv/ctphysics/AnswerChecker.kt` — три настоящих
  дефекта паритета, найденных локальным стендом Kotlin (JDK + `kotlinc` через
  `jdk4py`/npm, см. ниже): надстрочная степень без десятки ломала `2,7·10⁷ Дж`,
  `splitNumberUnit` слева-направо превращал «0,05» в «0» плюс «,05»,
  `normalize` не срезал букву варианта («б) 2,5 м»), плюс «пусто» вместо
  «неверное значение» для неразобранной записи и приоритет `dimension` над `unit`;
* `android/app/src/main/.../by/ziv/ctphysics/ReleaseFeed.kt` (новый) —
  предметный канал обновления: Releases API, только теги `physics-v*`, чужой
  манифест отвергается; `NativeBridge.kt` больше **не** читает общий
  `/releases/latest/download`; 7 новых юнит-тестов;
* `windows/store.go` — тот же предметный резолвер (`ResolveFeed`, `FeedForTag`,
  отвержение чужого `subject`/`package`) и два новых Go-теста;
* `windows/main.go`, `build.sh`, `build.ps1` — имя, каталог данных
  `%APPDATA%\CTPhysicsTutor`, профиль окна `ctphysics-window`;
* `webapp/index.html`, `styles.css`, `icon.svg`, debug-строки Android —
  заголовок, описание и подпись под предмет физики;
* `README.md` — полностью переписан под физику (формат ЦТ 10A+20B/210 минут,
  `phyzics.apk`, идентификаторы, что именно проверяется автоматически);
* удалены оставшиеся математические исходники `android/.../by/ziv/ctmaths/`
  (иначе в APK попадали бы два пакета сразу).

### Локальный прогон всех ворот CI (2026-10-14)

| Ворота CI | Локальная проверка | Результат |
|---|---|---|
| `tools/build_content.py` | `python3 tools/build_content.py` | 180 заданий, 39 генераторов, 37 уроков, 26 схем, 213 строк, 16 векторов |
| ассеты | `python3 tools/sync_assets.py --check` | копии совпадают |
| JS | `node --check webapp/{core,app}.js` | синтаксис чист |
| парность | `node tests/answer_parity.js` | 92 единицы, 180 заданий, 39 аналогичных |
| схема контента | `node tests/content_schema.js` | ✓ |
| Python-тесты | `.venv/bin/python -m unittest discover -s tests` | **104 теста, OK** |
| синтаксис | `.venv/bin/python tools/check_syntax.py --require` | 15 файлов, 0 ошибок |
| интерфейс | `node tests/{ui,native,theory}_smoke.js` (jsdom) | ✓ три прогона |
| Windows | `go vet`, `go test`, сборка amd64+arm64 | vet/test OK, оба EXE собраны (9,1 МБ / 8,3 МБ) |
| Android (юниты) | стенд Kotlin: `kotlinc` 2.4.21 + JDK 25 (`jdk4py`) | **21 тест, OK** (`AnswerChecker`, `ContentVersions`, `ReleaseFeed`) |
| подпись | `python3 tools/check_signature.py --require --keystore …` | отпечаток совпал |

Стенд Kotlin (в песочнице нет Android SDK и Gradle, поэтому используется
компилятор + минимальные заглушки `org.json`/`org.junit` вне репозитория):

```bash
python3 -m pip download jdk4py go-bin            # JDK и Go из PyPI
npm install --no-save kotlin-compiler@2.4.21     # компилятор Kotlin
# shim org.json/org.junit + Runner.kt вне репозитория, затем kotlinc и java
```

Ограничения стенда: `MainActivity.kt` и `NativeBridge.kt` используют Android
API и локально не компилируются (в CI их собирает Gradle); APK локально не
пересобирается, поэтому факт сборки APK подтверждается только раном CI.

---

## 2026-10-14 (продолжение 2): ЗЕЛЁНЫЙ прогон и первый выпуск физики

Run **[38562589780](https://github.com/zigorminsk-debug/mathematics/actions/runs/38562589780)**
(commit `3fa04f8e`, ветка `arena/f7b88593-mathematics`, событие `push`) —
**success**, все пять jobs:

| Job | Результат |
|---|---|
| Resolve effective build version | success (`physics-v2026.10.1`) |
| Content & web (verify, parity, assets) | success |
| Windows app (Go) | success |
| Android app (APK) | success (юнит-тесты, debug, подписанный release, проверка подписи и versionCode) |
| Publish verified builds automatically | success |

### Выпуск

* **`physics-v2026.10.1`** опубликован 2026-10-14T12:19:00Z с **13 ассетами**
  (7 JSON контента + `version.json` + `release-info.json` + `SHA256SUMS.txt` +
  `phyzics.apk` + `CTPhysicsTutor-amd64.exe` + `CTPhysicsTutor-arm64.exe`),
  `draft=false`, `prerelease=false`, **`make_latest=false`**;
* APK: пакет `by.ziv.ctphysics`, versionCode **261001**, отпечаток сертификата
  `A3:55:CB:…:35:83` (постоянный ключ физики), гейт «подпись и возрастающий
  versionCode относительно предыдущего опубликованного APK» — пройден;
  ассет `phyzics.apk`, 5 172 973 байт,
  `sha256:2e76888230c2cb7f2ad43e9f15c9990c1f750230e12e81266a00844e3de935eb`;
* EXE: `CTPhysicsTutor-amd64.exe` 7 299 072 байт,
  `sha256:190ff6a6f2aa37b366c43a6ab3af2190645c735d99bf0ef3ecba2c8cd4c2f427`;
  `CTPhysicsTutor-arm64.exe` 6 918 144 байт,
  `sha256:f30fc93bb75b35bd69d54243363f03737b53ce6120ed2e243564d5b6686e860f`;
* `release-info.json` (в метаданных релиза он продублирован в `<details>`, чтобы
  читался через API): subject `physics`, package `by.ziv.ctphysics`,
  sourceCommit `3fa04f8e…`, run 38562589780, три проверки со статусом success,
  `publication.repositoryLatestBefore = v2026.10.8`.

### Изоляция математики проверена после публикации

* repository latest остаётся **`v2026.10.8`** (published 2026-10-14T09:09:31Z,
  13 ассетов) — выпуск физики его не переключил;
* ключевые ассеты математики на момент проверки (для сверки в будущем):
  `app-release.apk` sha256 `8b56d02c…1dc9` (5 255 485 Б),
  `CTMathsTutor-amd64.exe` `d1e68182…fbd7`, `CTMathsTutor-arm64.exe`
  `71f9da51…c916`, `SHA256SUMS.txt` `c56b4df2…09f5` — не изменялись;
* у физики собственный тег-семейство, свой пакет, свой ключ, свой банк и своя
  статистика; в интерфейсе не осталось математических терминов (проверено
  поиском по поставляемым `webapp/*.js|html`).

### Что дальше автоматически

Любой следующий доверенный push в рабочую ветку снова пройдёт все ворота и
выпустит **следующую** версию (`physics-v2026.10.2`, …) — так устроена
автопубликация. Ручных шагов для выпуска нет; тег `physics-v*` можно также
поставить вручную (`workflow_dispatch` в `release.yml`).

### Остаётся непроверенным (честный список)

* установка APK на реальный телефон и его запуск (в песочнице нет устройства);
* запуск `CTPhysicsTutor-*.exe` на Windows (в песочнице нет Windows; бинарники
  собраны и залиты, go vet/test зелёные);
* локальная пересборка APK: Gradle и Android SDK отсутствуют, поэтому подпись и
  метаданные подтверждаются **раном CI**, а не локально;
* `MainActivity.kt`/`NativeBridge.kt` локально не компилируются (Android API) —
  их собирает Gradle в CI; юнит-тесты Kotlin прогнаны на локальном стенде
  (21 тест: `AnswerChecker`, `ContentVersions`, `ReleaseFeed`).
