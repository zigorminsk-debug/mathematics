# AGENTS.md — репозиторий `zigorminsk-debug/mathematics`: три самостоятельных репетитора

В одном репозитории живут **три независимых приложения** для подготовки к ЦТ
(Беларусь). У каждого — свой банк заданий, свой Android-пакет, свои Windows-EXE,
свой ключ подписи, своя семья тегов и свой канал обновления. Общая только
проверенная машинерия релизов.

| Приложение | Дерево | subject | Теги | Android | EXE |
|---|---|---|---|---|---|
| «Репетитор ЦТ: Математика» — **не трогать** | корень репозитория (`webapp/`, `android/`, `windows/`, `content_src/` до 2026-10-14 — физические, см. ниже) | `mathematics` | `vYYYY.M.P` (глобальный `latest`) | `by.ziv.ctmaths` | `CTMathsTutor-*.exe` |
| «Репетитор ЦТ: Физика» | корень репозитория (`content_src/`, `webapp/`, `android/`, `windows/`) | `physics` | `physics-vYYYY.M.P` | `by.ziv.ctphysics` | `CTPhysicsTutor-*.exe` |
| «Репетитор ЦТ: Английский язык» | `english/` | `english` | `english-vYYYY.M.P` | `by.ziv.ctenglish` | `CTEnglishTutor-*.exe` |

Математика физически осталась в **другой ветке/релизах** (`v2026.10.8`,
`by.ziv.ctmaths`, `CTMathsTutor`, отпечаток `B2:BD:…:65`); её релизы и статистика
не меняются: любая предметная публикация обязана иметь `make_latest=false`, и
`tools/publish_release.py` падает, если глобальный `releases/latest` уехал.
Английский и физика используют **общий** корень репозитория только там, где дерево
не пересекается: физика — в корневых каталогах, английский — целиком в `english/`.

Читать в этом порядке: **AGENTS.md → docs/WORKLOG.md (последнее «продолжение») →
docs/subjects/README.md → docs/subjects/PHYSICS.md /
[docs/subjects/ENGLISH.md](docs/subjects/ENGLISH.md)**.

## 1. Идентичность предметов (не менять без явной просьбы пользователя)

Один источник правды — `tools/subject.py` + `tools/subject_<имя>.py`; какой предмет
обслуживают инструменты, выбирает переменная `CT_SUBJECT` (`physics` по умолчанию).

| Свойство | Физика | Английский язык | Математика (чужая, не трогать) |
|---|---|---|---|
| subject | `physics` | `english` | `mathematics` |
| теги релизов | `physics-vYYYY.M.P` | `english-vYYYY.M.P` | `vYYYY.M.P` |
| Android package | `by.ziv.ctphysics` (+ `.debug`) | `by.ziv.ctenglish` (+ `.debug`) | `by.ziv.ctmaths` |
| Windows EXE | `CTPhysicsTutor-{amd64,arm64}.exe` | `CTEnglishTutor-{amd64,arm64}.exe` | `CTMathsTutor-…` |
| Windows данные / профиль | `%APPDATA%\CTPhysicsTutor`, Edge `ctphysics-window` | `%APPDATA%\CTEnglishTutor`, Edge `ctenglish-window` | `CTMathsTutor` |
| APK в релизе | `phyzics.apk` | `engtutor.apk` | `app-release.apk` |
| подпись | `android/keystore/ctphysics-release.p12`, `A3:55:CB:…:35:83` | `english/android/keystore/ctenglish-release.p12`, `5F:70:75:…:98:25` | `ctmaths-release.p12`, `B2:BD:…:65` |
| очередь CI | `ctphysics-release-pipeline` | `ctenglish-release-pipeline` | `ctmaths-release-pipeline` |
| канал обновления | Releases API, только `physics-v*` | Releases API, только `english-v*` | глобальный `latest` |

Правила, которые нельзя нарушать:

1. Публикация любого предмета — **только** `make_latest=false`. Глобальный
   `latest` репозитория остаётся математическим.
2. Ни одна команда не пишет в чужие теги/пакеты/сертификаты и не переиспользует
   чужой ключ подписи; установленные приложения сосуществуют, статистика,
   настройки, профили WebView/Edge и загруженный банк — раздельные.
3. Авторские задания не выдаются за материалы РИКЗ: дисклеймер лежит в
   `content_src/periods.py` (физика) и `english/content_src/` (английский),
   попадает в `version.json` и на экран «О программе».
4. Форматы вариантов **не наследуются** друг от друга и подтверждаются источником:
   физика — 10 A + 20 B, 210 минут (перечень РИКЗ, 2026-10-14); английский —
   18 A + 22 B, 120 минут (`result.rikc.by/.../rce_2025/form__3.pdf`, 2026-10-14).
5. Не объявлять успех по одной проверке: релиз подтверждается фактическим запуском
   CI и фактическим Release (тег, SHA, инвентарь, дайджесты, чужой `latest`).
6. Физический телефон и установка на Windows **не тестировались** — так и писать.

## 2. Состояние на 2026-10-14

**Физика — выпущена.** `physics-v2026.10.1 … 10.5`; 180 заданий в вариантах
2021–2026 (по 30), 39 аналогичных, 13 тем, 37 уроков RU/EN с бытовыми
объяснениями, 26 типизированных SVG-схем, 52 диагноза ошибок, 213 надписей UI
(190 используются). Приложения портированы на физику целиком: `webapp/` (JS),
`android/` (Kotlin, `by.ziv.ctphysics`), `windows/` (Go, `CTPhysicsTutor`).
Проверки: `python3 tools/build_content.py`, `python3 -m unittest discover -s tests`,
`node tests/{content_schema,answer_parity}.js`, jsdom-смоуки, `make_icon.py --check`
(иконка — атом), Go/Kotlin-сборки в CI.

**Английский — собран, выпуск делает CI.** Дерево `english/` (см.
[docs/subjects/ENGLISH.md](docs/subjects/ENGLISH.md)): 305 заданий (шесть авторских наборов 2021–2026 —
по 18 A + 22 B, 40 заданий, 120 минут; 65 в тематических пулах), 39 аналогичных,
13 тем/уроков/разделов правил (14 карточек), 5 типизированных схем, 76 диагнозов,
108 надписей UI, 1082 вектора ответов. Годы — метки авторских наборов в
современной тренировочной структуре, не архивы официальных экзаменов.
`english/tests/test_periods.py` — 10 регрессионных тестов полноты/уникальности
и строгой проверки ответа; конвейер обязан загружать все `periods.modules()`. Проверки:
`CT_SUBJECT=english python3 english/tools/build_content.py`, `english/tests/*`
(parity, схема, jsdom-смоук, тест иконки-облака «EN»), 15 Kotlin-тестов на
JVM-стенде, Go `vet/test`, `check_syntax.py --require`. Опубликованы
`english-v2026.10.1` и `english-v2026.10.3` (13 вложений, `engtutor.apk`, обе EXE,
feed, audit, sums; `make_latest=false`); тег `english-v2026.10.2` — резерв
прерванной публикации без релиза (разбор в `docs/WORKLOG.md`, «продолжение 8»).
Публикует `.github/workflows/english-ci.yml` на каждом доверенном push.

**Русский язык — не начат** (задание: `docs/subjects/RUSSIAN.md`).

## 3. Команды

```bash
# физика (CT_SUBJECT по умолчанию = physics)
python3 tools/build_content.py && python3 tools/sync_assets.py
python3 -m unittest discover -s tests -p 'test_*.py'
node tests/content_schema.js && node tests/answer_parity.js

# английский: та же машинерия, свой предмет
CT_SUBJECT=english python3 english/tools/build_content.py
CT_SUBJECT=english python3 tools/sync_assets.py --check
python3 english/tests/test_icon.py && python3 english/tools/make_icon.py --check
node english/tests/answer_parity.js && node english/tests/content_schema.js
npm install --no-save jsdom && node english/tests/ui_smoke.js
CT_SUBJECT=english .venv/bin/python tools/check_syntax.py --require
```

Чего в песочнице **нет** и что проверяется только CI: `go`, `gradle`, `aapt2`,
`apksigner` (JVM-стенд на шимах — вспомогательный, см. `docs/WORKLOG.md`,
«продолжение 6»). Никогда не писать «собрано/протестировано локально» про
артефакты, которых локально нет: APK и EXE собирает GitHub Actions.

## 4. Карта репозитория

```
content_src/ webapp/ android/ windows/   физика (корневые каталоги)
  android/keystore/                      постоянный ключ физики
english/                                 английский тренажёр целиком
  README.md                              вход для человека: возможности, формат, идентичность, сборка
  content_src/                           авторские задания, правила, уроки, политика ответов
  tools/{build_content.py,make_icon.py}  сборка банка и иконки (облако «EN»)
  webapp/ windows/ android/ dist/ tests/ интерфейс, Go-хост, Kotlin-приложение, тесты
  android/keystore/                      постоянный ключ английского
tools/                                   общая машинерия
  subject.py, subject_physics.py, subject_english.py
  build_content.py                       сборка контента физики
  release_plan.py, publish_release.py    версия/тег/lineage/публикация (по CT_SUBJECT)
  check_apk_update.py, check_signature.py, check_syntax.py, sync_assets.py
.github/workflows/
  ci.yml, release.yml, publish.yml       физика (+ общий параметризованный публикатор)
  english-ci.yml, english-release.yml    английский
docs/  docs/subjects/{README,PHYSICS,ENGLISH,RUSSIAN}.md, docs/WORKLOG.md
tests/                                   общие Python-тесты (включая изоляцию предметов)
```

## 5. Ближайшие шаги

1. **Английский:** дождаться зелёного прогона `english-ci.yml` на доверенном push,
   проверить `english-v2026.10.1` (13 вложений, `engtutor.apk`, две EXE, feed, audit,
   sums), убедиться, что математический `latest` не изменился, и записать факт в
   `docs/WORKLOG.md`.
2. **Английский:** второй прогон проверяет ветку «обновление поверх предыдущего
   APK» (`--previous engtutor.apk`) — она включается только при наличии предыдущего
   английского тега.
3. **Русский язык:** по `docs/subjects/RUSSIAN.md`, тем же способом (`tools/subject_russian.py`,
   дерево `russian/`, семья `russian-v*`, отдельный ключ подписи до первого APK).
4. Не сливать PR #4, не менять чужие ветки и не публиковать предмет под чужим тегом
   без явного запроса пользователя.
