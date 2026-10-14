# Два самостоятельных репетитора: передача в отдельные сессии Arena

**Статус (2026-10-14): подготовка, НЕ готовые приложения.** Пользователь запросил
отдельную ветку физики и отдельную ветку русского языка «аналогично математике».
После объяснения ограничения текущей сессии выбрал **отдельные сессии со своими
ветками**, а не каталоги двух приложений в математической ветке. Здесь новые
ветки/репозитории не создавались, Android/Windows приложения не клонировались.

## Как начать

1. Открыть две новые сессии Arena в `zigorminsk-debug/mathematics`: одна только
   для физики, другая только для русского языка.
2. Выбрать исходной историей текущую ветку `arena/d7e34c80-mathematics`, содержащую
   этот пакет инструкций. **Старый main не подходит**: PR #4 ещё не слит и нужные
   теория/схемы/автопубликация отсутствуют в его старой истории.
3. В каждой новой сессии работать только в её назначенной рабочей ветке.
   Не повторять старое имя математической сессии как имя новой; не переключаться,
   не создавать/отправлять сторонние ветки в обход ограничений активной сессии.
4. Передать соответствующий готовый запрос ниже. Прочитать `AGENTS.md`,
   `docs/WORKLOG.md`, `docs/RELEASE.md`, этот документ и предметное задание.
5. **До первого предметного push** сделать отдельный пакет/хранилище/канал,
   изменить planner/publisher/update resolver и пройти isolation tests.
   Все эти изменения должны войти в первую проверенную предметную отправку.
   Нельзя отправить переименованный APK с унаследованным math publisher.

Если новая сессия открылась от старого main, не ослаблять lineage gate и не
выдавать отсутствующую историю за независимое приложение: сначала обеспечить
правильную исходную историю на разрешённой ветке этой сессии.

## Проверенная база

- Реализация математики: **`aa46e76558e389f3fb64564f6ce4ea45aeab32a0`**,
  [v2026.10.7](https://github.com/zigorminsk-debug/mathematics/releases/tag/v2026.10.7),
  опубликован **2026-10-14T08:31:24Z**, code **261007**.
- Push [38535383529](https://github.com/zigorminsk-debug/mathematics/actions/runs/38535383529)
  и PR [38535390684](https://github.com/zigorminsk-debug/mathematics/actions/runs/38535390684)
  — SUCCESS; 13 assets/digests и immutable tag source подтверждены.
- Шесть **авторских тренировочных**, не официальных РИКЗ, вариантов 2021–2026;
  180 + 552 задания, 18 тем, 56 офлайн RU/EN уроков с бытовыми объяснениями,
  52 typed SVG схемы, nested zoom/pan/Back, сохранение ответов/статистики.
- Shared JS/HTML/CSS → Android Kotlin/WebView + Windows Go/Edge/Chrome.
- 59 Python tests, 732 task checks, 30 answer vectors, actual native CI;
  Chromium mobile RU/EN diagrams (52 × 2) проверены, физический телефон не тестировался.
- `VERSION = 2026.10.5` — **source floor**, НЕ current Release version.
  Документационный push этого handoff тоже автоматически выпускает математику.
  Проверять actual GitHub latest/source/audit, а не предполагать номер по этой записи.

## Границы: не испортить математику

| Свойство | Математика — оставить | Физика — предлагается | Русский — предлагается |
|---|---|---|---|
| subject ID | `mathematics` | `physics` | `russian` |
| Android package | `by.ziv.ctmaths` | `by.ziv.ctphysics` | `by.ziv.ctrussian` |
| debug package | `by.ziv.ctmaths.debug` | `by.ziv.ctphysics.debug` | `by.ziv.ctrussian.debug` |
| Windows binary stem | `CTMathsTutor` | `CTPhysicsTutor` | `CTRussianTutor` |
| Windows profile/data | `CTMathsTutor` / `ctmaths-window` | `CTPhysicsTutor` / `ctphysics-window` | `CTRussianTutor` / `ctrussian-window` |
| stable tag family | `vYYYY.M.P` | `physics-vYYYY.M.P` | `russian-vYYYY.M.P` |

Новые значения — **предлагаемая схема для реализации**, не существующие IDs,
теги, сертификаты или файлы. Не утверждать, что приложения уже доступны.
Ключ/сертификат математики не менять. Для каждого нового приложения определить
постоянную release-подпись **до первого выпуска**, зафиксировать fingerprint;
после публикации пакет/сертификат неизменны и versionCode строго растёт.
Секреты не размещать в чат/Git; следовать существующей signing policy и безопасной
конфигурации CI. Не пользоваться package математики для нового предмета.

Установленные приложения должны сосуществовать; статистика, настройки, sessions,
WebView/Edge profile, exports и загружаемый банк — отдельные. Не мигрировать/стирать
математическую статистику. Не рекомендовать uninstall для обновления.

## Критический риск: GitHub latest — общий на весь репозиторий

Текущий math updater читает `releases/latest/download/version.json`, а math
publisher делает `make_latest=true`. **Отдельная ветка НЕ изолирует Releases.**
Простое копирование workflows нового предмета заменит общий latest и приведёт
пользователя математики к чужому APK/банку. Это запрещено.

Рабочая схема для **того же репозитория с отдельными ветками**:

1. Physics/Russian имеют собственную tag family, VERSION/counter/reservations,
   lineage, permanent certificate, APK package и inventory.
2. Предметный publisher публикует non-draft release с `make_latest=false` и
   проверяет именно его tag/id/assets, **а не repo /releases/latest**. Math latest
   до/после должен совпадать и продолжать отдавать math files.
3. Предметный update resolver использует GitHub Releases API с пагинацией,
   выбирает подтверждённый stable release **только нужной family** и строит
   tag-specific download URLs. Нет глобального `/latest/download` у предметных
   клиентов. Выбирать по canonical version, не только по времени публикации;
   исключать draft/prerelease/чужой package/subject и неполный inventory.
4. Manifest и audit включают subject/package/schema; клиент до записи проверяет
   expected subject/package и file digests. Math банк отвергается физикой/русским
   и наоборот. Старый content protocol нужно расширить с тестами в Kotlin/Go/JS.
5. Planner ищет предыдущий stable APK/tag **этого subject**, не math и не sibling.
   Первый выпуск нового package не сравнивается как update математики; дальнейшие
   subject updates обязаны сохранить package/certificate и повысить code.
6. Counter/idempotency/tag ownership/ancestry и queue действуют per subject.
   Базовые проверки безопасности не отключаются. Namespaced locks не блокируют
   друг друга ошибочно; reusable caller/child locks остаются различными.
7. Publisher использует **same-run проверенные** APK/две EXE/feed; PR/fork не
   публикуют, failed/skipped gates блокируют release. Audit + checksums + body JSON
   сохраняют итог каждой сборки. Ветка определяется контекстом текущей сессии,
   но subject — явной конфигурацией, не угадывается по `arena/...` имени.

Вариант с отдельными репозиториями тоже технически изолирует latest, но пользователь
выбрал **ветки в отдельных сессиях**: не создавать новые repositories без согласия.
Конкретные subject download URLs появятся после первой реальной публикации;
не выдумывать их сейчас.

## Что переиспользовать / что заменить

Переиспользовать общую навигацию, варианты/экзамен/тренировку, подсказки/разбор,
wrong-answer → study, статистику/streak/goal, settings/themes/large text, RU/EN,
offline typed SVG viewer, сохранение sessions/Back/focus/search, native bridges,
atomic/checksummed updates, надёжный verified-release pipeline.

**Не ограничиваться сменой названия.** Заменить syllabus, tasks/analogs, accepted
answers/parser, topic/rule/lesson links, typical errors, simulations/diagrams,
report text, disclosure, package/resources/native tests, binaries/data directories,
release planner/publisher/contracts и предметный update resolver.
Не оставлять математические задания/формулы как контент нового предмета.

Формат 18A + 12B и 180 минут относится к текущей математике. Для каждого предмета
отдельно сверить актуальную структуру ЦТ/ЦЭ/программу и сохранить источник/дату.
Не выдавать неподтверждённую структуру/задания за официальный экзамен. До проверки
можно выпускать честно названный авторский тренировочный набор, не «точный ЦТ 2026».

## Этапы и приемка

1. Инвентаризация math-specific identifiers и предметный content/schema design.
2. Package/storage/update channel/publication isolation + negative tests.
3. Полноценный первый банк: темы, theory/everyday visuals, solved tasks/analogues,
   hints/diagnoses, periods/config; никаких заглушек для «готовой» публикации.
4. Предметные checker/vectors и генераторы с независимыми checks.
5. Общий UI/native адаптирован под предмет и синхронизирован в обе платформы.
6. Schema/unit/parity/UI/offline/native/signature/version/update/cross-subject tests,
   реальный mobile Chromium с RU/EN, dark/large text, Back/zoom/focus.
7. Первый trusted push → actual Go/Kotlin/APK/EXE jobs → автоматический предметный
   Release → verify tag/SHA/inventory/digests/audit and math latest unchanged.
8. Durable AGENTS/CONTENT/RELEASE/WORKLOG соответствуют **предмету этой ветки**;
   PR/CI/Release identities и реальные ограничения записаны. Main/чужие ветки
   не менять и PR не сливать без отдельного запроса.

## Готовые запросы для новых сессий

### Физика

> Создай самостоятельное приложение «Репетитор ЦТ: Физика» аналогично математике.
> Работай только в назначенной этой новой сессии ветке. Исходная история — ветка
> arena/d7e34c80-mathematics с docs/subjects, не старый main. Сначала прочитай
> AGENTS.md, docs/subjects/README.md и docs/subjects/PHYSICS.md. Реализуй предметные
> банк/проверку единиц/теорию с бытовыми объяснениями и схемами, APK и обе Windows
> EXE. До первого предметного push изолируй package/storage/release/update channel:
> physics-v…, make_latest=false, не трогай math latest/статистику/подпись. Все
> проверенные изменённые сборки публикуй автоматически, каждое действие документируй.
> Не выдавай авторские задания за РИКЗ; не объявляй успешный выпуск до actual CI.

### Русский язык

> Создай самостоятельное приложение «Репетитор ЦТ: Русский язык» аналогично
> математике. Работай только в назначенной этой новой сессии ветке. Исходная
> история — arena/d7e34c80-mathematics с docs/subjects, не старый main. Прочитай
> AGENTS.md, docs/subjects/README.md и docs/subjects/RUSSIAN.md. Реализуй реальные
> языковые упражнения, rule lookup/разбор/исключения/бытовые объяснения и наглядные
> схемы, отдельные APK/Windows EXE. До первого предметного push изолируй package/
> storage/release/update channel: russian-v…, make_latest=false, math latest
> не менять. Пунктуацию, пробелы, дефисы, ё и ударение проверяй по типу задания,
> не математическим normalizer. RU/EN UI не переводит проверяемый русский текст.
> Автоматически публикуй только проверенные сборки и веди durable журнал действий.
