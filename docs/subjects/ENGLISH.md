# «Репетитор ЦТ: Английский язык» — состояние и передача

Третий самостоятельный тренажёр в этом репозитории (после математики и физики).
Живёт в каталоге `english/`, использует **общую проверенную машинерию** релизов
(`tools/subject.py` → `tools/subject_english.py`, `tools/release_plan.py`,
`tools/publish_release.py`, `tools/sync_assets.py`) и публикуется под собственной
семьёй тегов `english-v*` с `make_latest=false`.

Статус на **2026-10-14**: дерево `english/` собрано и проверено локально, все
предметные тесты зелёные; предметные workflow (`english-ci.yml`,
`english-release.yml`) написаны. **Физический телефон и установка на Windows не
тестировались** — это отдельная строка в таблице приёмки ниже. Первый публичный
выпуск делает CI на доверенном push (см. «Как продолжить»).

## Цель и границы

Самостоятельный тренажёр для подготовки к ЦТ/ЦЭ по английскому языку: Android APK
и обе Windows EXE (amd64/arm64), авторские варианты и аналогичные задания,
экзамен/тренировка, RU/EN-интерфейс, офлайновый справочник правил с бытовыми
объяснениями, языковые (а не числовые) упражнения и схемы, разбор ошибок → правило
→ однотипные задания, статистика, типизированный SVG-просмотрщик и автоматические
проверенные релизы GitHub Actions.

Границы: математику и физику не переназывать и не публиковать под их тегами; их
`latest`, дайджесты, статистика и подписи не меняются; установленные приложения
сосуществуют (разные пакеты, каталоги данных, профили браузера и ключи подписи).
Авторские тренировочные задания **не выдаются за официальные задания РИКЗ** — в
манифесте, интерфейсе и теле релиза стоит оговорка.

## Постоянные идентификаторы (зафиксированы до первого APK)

| Свойство | Значение |
|---|---|
| subject | `english` |
| Android package / debug | `by.ziv.ctenglish` / `by.ziv.ctenglish.debug` |
| Windows EXE | `CTEnglishTutor-amd64.exe`, `CTEnglishTutor-arm64.exe` |
| имя APK в релизе | `engtutor.apk` (внутренняя сборка Gradle — `app-release.apk`) |
| data / Edge profile | `%APPDATA%\CTEnglishTutor` / `ctenglish-window` |
| семья тегов | `english-vYYYY.M.P` (`make_latest=false`) |
| очередь публикации | `ctenglish-release-pipeline` |
| ключ подписи | `english/android/keystore/ctenglish-release.p12`, alias `ctenglish` |
| отпечаток сертификата | `5F:70:75:90:3B:9A:AA:9E:AB:B6:64:40:5E:A7:05:05:92:25:CA:9C:34:75:19:79:53:DE:B2:7E:13:97:98:25` |
| env-переменные ключа | `CTENGLISH_KEYSTORE_FILE|_PASSWORD`, `CTENGLISH_KEY_ALIAS|_PASSWORD`, `CTENGLISH_KEYSTORE_TYPE` |
| первый выпуск | `english-v2026.10.1` (`english/VERSION = 2026.10.1`) |

Проверка изоляции от соседей — `tests/test_subject_profiles.py`: у каждого предмета
свои теги, пакеты, имена EXE, каталоги данных, профили, ключи, имя APK и очередь.

## Формат экзамена: источник и дата

Взято не из математики и не «по памяти», а из официального документа:

* `https://result.rikc.by/ru/documents/filesofregpunkts/rce_2025/form__3.pdf`
  (проверено 2026-10-14): строка **07 Английский язык · АНГ · часть A — 18 заданий,
  часть B — 22 задания, всего 40 заданий, 120 минут**.
* ДРТ на `https://result.rikc.by/ru/` — тот же предметный код и время (120 минут).

Форма `form__3.pdf` за 2026 год на дату проверки отсутствовала (404), поэтому
использована последняя опубликованная и проверенная. Числа 18A + 22B и 120 минут
зашиты в контент и тесты: `english/dist/content/version.json` →
`parts = {A: 18, B: 22}`, `minutes = 120`; `english/tests/content_schema.js`
падает, если структура перестанет совпадать.

Состав частей (по открытым разборам и спецификации 2022 года, ссылки в
`docs/WORKLOG.md`): A — времена, местоимения/артикли/разделительные вопросы/союзы/
степени сравнения, инфинитив и герундий, фрагменты с ошибкой, лексика, реплики,
социокультурные вопросы, чтение; B — предлог, пропущенное слово/фраза, «лишнее
слово», словообразование, перевод фрагмента. Аудирования нет.

## Контент

`english/content_src/*.py` — источник; `english/tools/build_content.py` собирает
`english/dist/content/*.json` и раскладывает копии в Windows и Android.

| Файл | Что внутри |
|---|---|
| `version.json` | `contentVersion 2026.10.1`, `schema 1`, subject/package/app, `parts`, `minutes 120`, оговорка об авторстве |
| `bank.json` | 105 заданий: 40 в варианте 2026 (18 A + 22 B) и 65 в тематических пулах |
| `analogous.json` | 39 однотипных заданий для разбора ошибок |
| `topics.json` | 13 тем, порядок, типы, инструменты, уроки, схемы, правила, периоды 2021–2026 |
| `rules.json` | 13 разделов справочника (14 карточек), у каждой карточки — формулировка и бытовое объяснение на RU/EN |
| `mistakes.json` | 76 диагнозов типичных ошибок (`title/why/fix/rule`) и памятка из 5 пунктов |
| `ui_strings.json` | 108 надписей интерфейса на RU/EN (переводится интерфейс, не проверяемый английский текст) |
| `answer_vectors.json` | 480 проверочных векторов: Python, JS и Kotlin обязаны проверять ответы одинаково |

Темы/уроки: `adjective-adverb`, `articles-basic`, `conditionals`, `extra-word-strategy`,
`gap-strategy`, `gerund-vs-infinitive`, `modal-meaning`, `passive-forms`,
`prepositions-collocation`, `present-simple`, `quantifiers`, `replies`, `suffixes`.
Схемы (`topics.figures`, 5 штук) — только типизированные `tree|timeline|flow`,
рисуются в `english/webapp/app.js` (`UI.diagramSvg`), без raw SVG и без CDN.

## Проверка ответов: контракт английского языка

Отдельный контракт, не математический `normalize`. Один и тот же алгоритм живёт в
трёх местах и сверяется векторами:

* `english/content_src/policy.py` (эталон),
* `english/webapp/core.js` → `CT.answer` (браузер/WebView),
* `english/android/app/src/main/java/by/ziv/ctenglish/AnswerChecker.kt` (Kotlin).

Политика по умолчанию: `case: insensitive`, `article: checked`, `apostrophe: ignore`,
`hyphen: significant`, `space: significant`, `stress: significant`, `empty: reject`.
Нормализация: nbsp → пробел, тире → дефис, апострофы → `'`, диакритика → буквы,
пробелы сжимаются, обрезка, нижний регистр, удаление артиклей **только** когда
политика задания это разрешает, повторное сжатие пробелов. Пустой ответ —
прочерк «—», если задание этого требует.

Причина отказа честно называется словом: `ok`, `empty`, `case`, `apostrophe`,
`hyphen`, `space`, `article`, `stress`, `near`, `exact`. «Почти верно» (`near`) —
только подсказка для разбора, оно **не** принимается как верный ответ. Форму
слова проверяем буквально: предлог, артикль, форма глагола и производное слово —
это и есть ответ, поэтому политика каждого задания описана явно, а не «на глаз».
Альтернативы (`an honest man` для `honest man`) допускаются только там, где
задание это объявляет.

## Дерево `english/`

| Путь | Что это |
|---|---|
| `english/VERSION` | source floor версии (`2026.10.1`), планировщик выдаёт следующую по тегам `english-v*` |
| `english/content_src/` | авторские задания, правила, уроки, диагнозы, политика ответов, генераторы векторов |
| `english/tools/build_content.py` | сборка банка: проверки схемы, покрытия тем, политики, генерация векторов |
| `english/tools/make_icon.py` | **иконка рисуется кодом**: облако с «EN», варианты `full/round/foreground`, `--android`, `--check` |
| `english/webapp/` | общий интерфейс: `index.html`, `styles.css`, `core.js`, `app.js`, `icon.svg`, `icon.png` |
| `english/windows/` | Go-хост (`CTEnglishTutor`), встроенный `web/` через `go:embed`, Resolver релизов английской семьи |
| `english/android/` | Kotlin/WebView приложение `by.ziv.ctenglish`, собственные иконки лаунчера, отдельный ключ подписи |
| `english/dist/content/` | собранные JSON (в git не попадают; копии синхронизируются в приложения) |
| `english/tests/` | `answer_parity.js`, `content_schema.js`, `ui_smoke.js` (jsdom), `test_icon.py` |

Обновление контента в приложениях: клиент читает Releases API, берёт **только**
релизы семьи `english-v*`, отвергает чужой `subject`/`package` и никогда не
обращается к глобальному `/releases/latest/download` (он отдаёт математику).

## Что проверяется автоматически

Локально (обязательно перед push):

```bash
CT_SUBJECT=english python3 english/tools/build_content.py
CT_SUBJECT=english python3 tools/sync_assets.py
CT_SUBJECT=english python3 tools/sync_assets.py --check
python3 english/tools/make_icon.py --check
python3 english/tests/test_icon.py
node english/tests/answer_parity.js
node english/tests/content_schema.js
npm install --no-save jsdom && node english/tests/ui_smoke.js
python3 -m unittest discover -s tests -p 'test_*.py'
CT_SUBJECT=english .venv/bin/python tools/check_syntax.py --require
```

В `.github/workflows/english-ci.yml` те же проверки выполняются на каждом push:
сборка контента, изоляция «английская сборка не трогает деревья математики и
физики», идемпотентность физической сборки, иконка, синхронизация ассетов,
parity и схема, общие тесты, синтаксис, jsdom-путешествие по экранам; затем Go
(`go vet`, `go test`, обе EXE) и Android (unit-тесты Kotlin, debug и signed-release
APK, проверка подписи, `versionCode` и обновления «поверх» предыдущего английского
APK). Ни один шаг не пропускается и не «мягко» игнорируется.

Общий набор `tests/` описывает машинерию **физики** и проверяет изоляцию
предметов сам (`tests/test_subject_profiles.py` запускает профили в отдельных
процессах), поэтому его запускают **без** `CT_SUBJECT` — иначе тесты физики увидят
английский профиль (в `english-ci.yml` у шага «Repository tests» явно снят
`CT_SUBJECT`). Английские проверки живут в `english/tests/`.

Kotlin-тесты можно прогнать и без Gradle — см. `docs/WORKLOG.md`, раздел
«продолжение 6»: в песочнице Arena поднимался JVM-стенд с шимами `org.json`/JUnit
и те же 15 тестов (`AnswerCheckerTest`, `ReleaseFeedTest`, `ContentVersionsTest`)
проходили зелёными.

## Релиз и канал обновления

* `english-ci.yml` — обычный push: планирует версию, проверяет всё и при успехе
  вызывает `publish.yml` с `subject: english`. Публикация только из этого
  репозитория, только не из PR, только после зелёных заданий.
* `english-release.yml` — теги `english-v*` и ручной запуск (восстановление):
  вызывает тот же полный CI с `publish: true` и `release_request: true`, поэтому
  публикуется ровно то, что проверено, без пересборки «на стороне».
* `publish.yml` параметризован предметом: тег берётся из профиля, APK переименован
  в `engtutor.apk`, релиз создаётся с `make_latest=false` и своим audit
  (`release-info.json`, `version.json`, `SHA256SUMS.txt`).
* Проверки публикатора: 13 файлов инвентаря на месте, дайджесты посчитаны,
  lineage (родитель — предыдущий английский тег) подтверждён, чужой `latest` не
  трогается, повторная публикация существующего тега запрещена.

**Опубликовано:** `english-v2026.10.1` (2026-10-14T18:29:00Z) и
`english-v2026.10.3` (2026-10-14T18:40:49Z) — по 13 вложений, включая
`engtutor.apk`. Тег `english-v2026.10.2` — резерв прерванной публикации без
релиза: `publish_release.py` читал только что созданный ref и получал 404
(гонка GitHub «чтение после записи»); исправлено повторным чтением, разбор — в
`docs/WORKLOG.md`, «продолжение 8». Ручные способы спасти выпуск из песочницы
недоступны (`gh run rerun` → «cannot be rerun», `gh workflow run` → 403:
у интеграции нет `actions: write`).

## Приёмка

| Требование | Состояние |
|---|---|
| Авторские банк/аналогичные задания, 18 A + 22 B, 120 минут | сделано, проверяется `content_schema.js` |
| Языковые упражнения и схемы, а не числовые | сделано (`policy.py` + 5 типизированных схем) |
| RU/EN интерфейс, проверяемый английский текст не переводится | сделано, проверяется в `ui_smoke.js` |
| Разбор ошибки → правило → однотипные задания | сделано (`mistakes.json` 76 диагнозов, `analogous.json`) |
| Статистика, экзамен/тренировка, офлайн-справочник | сделано, проверяется дымовыми тестами |
| Новая иконка (облако «EN»), одинаковая на всех платформах | сделано, `python3 english/tools/make_icon.py --check` |
| Изоляция пакета/данных/подписи/канала обновления | сделано, `tests/test_subject_profiles.py` + Kotlin/Go-тесты |
| Автопубликация APK + 2 EXE + feed + audit + sums | выполнено CI после первого доверенного push (см. WORKLOG) |
| Установка на реальный телефон / Windows | **не тестировалось** (нет физического устройства в песочнице) |

## Как продолжить

1. Прочитать `AGENTS.md`, `docs/WORKLOG.md` (последнее «продолжение»),
   этот файл и `docs/subjects/README.md`.
2. Проверить состояние: `git status`, `git log --oneline -5`,
   `gh run list --limit 10`, `gh release list --limit 10`.
3. Никогда не менять `english/android/keystore/*` и идентификаторы из таблицы
   выше: после первого выпуска это ломает обновления. Тег `english-v*` повторно не
   публикуется — только новый номер версии.
4. Любую правку контента заканчивать командой
   `CT_SUBJECT=english python3 english/tools/build_content.py && CT_SUBJECT=english python3 tools/sync_assets.py`,
   иначе CI остановится на шаге «Ensure the committed assets match the sources».
5. Релиз не объявлять успешным, пока не проверены реальный run Actions, тег, состав
   ассетов и дайджесты: `gh run view <id>`, `gh release view english-v<версия>`.
   Публикация одного предмета **не должна** менять `releases/latest` репозитория —
   там по-прежнему математика.
