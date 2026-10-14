# ARCHITECTURE.md — архитектура приложения физики

## 1. Поток данных

```
content_src/*.py            авторские модули (источник правды)
        │  python3 tools/build_content.py
        ▼
dist/content/*.json         языконезависимый фид (ru+en рядом)
        │  tools/sync_assets.py / шаг сборки
        ├───────────────► android/app/src/main/assets/content/   (WebView-ассеты)
        ├───────────────► windows/web/content/                    (встроенный веб)
        └───────────────► android/app/src/main/res/values{,-ru}/strings.xml
        ▼
Android (Kotlin + WebView)      Windows (Go + Edge/Chrome WebView2)
        │                                   │
        └──────────► webapp/*.js (общий интерфейс) ◄──────────┘
```

Правило: **JSON руками не правят**. Любая правка контента — в `content_src/`,
затем `python3 tools/build_content.py` (и `tools/sync_assets.py`, если он
копирует ассеты отдельно от сборки).

## 2. Три реализации одного чекера

Проверка ответа существует в трёх местах и обязана совпадать:

| Реализация | Где | Как проверяется |
|---|---|---|
| Python (эталон) | `content_src/quantities.py::check_answer` | `tools/build_content.py` прогоняет векторы при сборке |
| JavaScript | `webapp/core.js` → `CT.answer.grade(user, spec)` | `node tests/answer_parity.js` |
| Kotlin | `android/…/AnswerChecker.kt` | `gradle testDebugUnitTest` (+ тест векторов) |

Общий набор случаев — `content_src/kit.py::ANSWER_VECTORS` → `dist/content/answer_vectors.json`.
Вектор — это `spec` + список записей `{input, ok, reason}`; сверяется и вердикт, и
**причина** отказа (`empty`, `unit`, `dimension`, `missing_unit`, `value`), потому
что именно причина управляет подсказкой после ошибки.

## 3. Контракт задачи (то, что видит интерфейс)

```json
{
  "id": "phys-2024-a8",
  "year": 2024, "part": "A", "n": 8, "topic": "electrostatics", "difficulty": 3,
  "answerType": "choice",
  "text": {"ru": "…", "en": "…"},
  "options": {"ru": ["…"], "en": ["…"]},
  "distractors": {"ru": ["типичная ошибка"], "en": ["…"]},
  "answer": {"ru": "…", "en": "…"},
  "accept": ["…", "…"],
  "solution": {"ru": ["шаг", "шаг"], "en": ["…"]},
  "hints": {"ru": ["Формула: …"], "en": ["…"]},
  "tools": ["calc", "sheet", "units", "scratch"],
  "src": "авторское тренировочное задание…; не материалы РИКЗ",
  "tags": ["закон Кулона"],
  "spec": {"answerType": "quantity", "answerValue": "60", "unit": "Н", "dimension": "kg·m/s^2", "tolerance": {…}},
  "unit": {"ru": "Н", "en": "N"},
  "given": [{"symbol": "q1", "name": "заряд", "value_ru": "2", "value_en": "2", "unit": {"ru": "мкКл", "en": "µC"}}],
  "model": {"formula": "F = k·q₁·q₂/r²", "dim": "…", "vars": {…}, "ask": "F"}
}
```

Тексты уже отрендерены: подстановки `{symbol}` заменены значениями в записи языка
(запятая в русском, точка в английском), поэтому интерфейс ничего не форматирует
сам и не может «поплыть» между языками.

## 4. Границы платформ

* **Мост.** Android: `window.CTNative` (Kotlin `NativeBridge`). Windows: `fetch`
  к локальному HTTP API Go (`api/state|blob|content|update|report|open-folder|quit`).
  Интерфейс один и тот же: `webapp/core.js` + `webapp/app.js`.
* **Хранилище.** Отдельное у физики: Android — внутренний каталог приложения,
  Windows — `%APPDATA%\CTPhysicsTutor`; браузерный профиль Edge —
  `ctphysics-window`. Статистика, настройки, черновик и загруженный банк не
  пересекаются с математикой.
* **Обновление контента.** Клиент обращается к Releases API, выбирает релиз
  **только** семьи `physics-v*`, сверяет `subject`, `package` и `sha256` файлов из
  `version.json`, пишет в оверлей и не трогает установленный APK/EXE. Глобальный
  `/releases/latest/download` у физики не используется вообще.
* **Схемы.** Просмотрщик допускает только
  `{line, circle, ellipse, rect, polyline, polygon, text}` в системе координат
  420×280 с zoom/pan/Back; никакого `innerHTML` из данных и никаких внешних
  ресурсов.

## 5. Релизная машинерия

* `tools/release_plan.py` — версия: пол = `VERSION`, не ниже `сегодня.Y.M.0`,
  строго выше предыдущего стабильного релиза своей семьи, идемпотентность по
  коммиту, отказ при неполном инвентаре; `--apply-version` пишет версию в
  checkout раннера.
* `tools/publish_release.py` — проверка run/commit/события, инвентарь staging,
  черновик → загрузка → публикация с `make_latest=false` → повторная проверка,
  что глобальный latest не переключился.
* `tools/check_apk_update.py` — пакет, versionCode из VERSION, сравнение с прошлым
  APK физики; `tools/check_signature.py` — подпись (`apksigner`/`keytool`).
* `.github/workflows/{ci,release,publish}.yml` — очередь
  `ctphysics-release-pipeline`, ручной запуск с `publish: true/false`,
  переиспользуемый publish-child с отдельной очередью.

## 6. Что переиспользуется у математики, а что заменяется

Переиспользуется (это одна и та же программа): навигация и экраны, разметка,
темы, крупный шрифт, статистика/streak/цель, RU/EN, офлайн-просмотрщик схем,
мост к платформе, атомарные обновления контента, контракты CI.

Заменяется (предметное): чекер ответов и разбор ошибок, банк и генераторы,
единицы/размерности, теория/схемы/конспекты/формулы, дисклеймер, идентификаторы
пакета/данных/профиля, подпись, релизный планировщик и канал обновления.
