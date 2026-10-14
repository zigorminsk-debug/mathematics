# Автоматический выпуск / Automatic releases

## Постоянное правило

После **каждого push в исходный репозиторий** `zigorminsk-debug/mathematics`
GitHub Actions проверяет контент/интерфейс, собирает Windows amd64 + arm64 и Android
и **сам публикует** APK, оба EXE и банк заданий. Отдельный ручной запуск, тег от
агента или разрешение пользователя перед каждым выпуском не нужны. Это прямо
запрошено пользователем 2026-10-14; не возвращайте публикацию к ручной схеме.

Конфигурация сейчас внесена в `arena/d7e34c80-mathematics` / PR #4. Ветки должны
содержать новые workflow файлы. Пока PR #4 не слит, `main`/ветки от старого main
содержат прежний CI и сами не унаследуют эту автоматизацию. Публикации рабочей
ветки уже могут обновлять общий Releases/latest. Слияние PR требует отдельного
решения пользователя; в этой работе main не меняется напрямую.

PR (включая PR из самого репозитория) и fork выполняют проверки, но **не публикуют**.
Таким образом, push исходной ветки и его PR — не два одинаковых публичных выпуска.
Изменения документации тоже являются новым push и публикуются после проверок.

## Один проверенный pipeline

- `.github/workflows/ci.yml`: подготовка версии → три параллельных обязательных
  jobs → публикация. Тесты контента, арифметики, JS/schema/parity, Python, native
  syntax, UI/native/theory journeys, Go vet/tests, Kotlin tests, сборки APK/EXE.
- `.github/workflows/publish.yml`: reusable workflow, получает **артефакты этого
  же запуска** `content-bank`, `windows-exe`, `android-release-apk`; не пересобирает
  APK/EXE и не скачивает чужие PR-артефакты.
- `.github/workflows/release.yml`: необязательные tag/manual recovery entry points;
  вызывают **тот же полный CI**, а не укороченную отдельную сборку.
- Только job публикации имеет `contents: write`; проверочные jobs и планировщик —
  `contents: read`. Для проверки результата jobs publisher имеет `actions: read`.
  Runner закреплён на `ubuntu-24.04`, не `ubuntu-latest`: проверенная среда не
  сменится автоматически на Ubuntu 26 (migration warning на 2026-10-19).
  У tag/manual wrapper есть write ceiling для nested reusable publisher.

Publisher дополнительно через API сверяет repository, SHA/run/event/ref и
успешное завершение **всех трёх** обязательных build jobs. Failed, cancelled,
skipped или отсутствующий job блокирует выпуск. Переименование job требует
синхронизации `BUILD_JOBS` в `tools/release_plan.py`; это покрыто тестами.

## Автоматический номер — не забывайте о VERSION floor

`VERSION` (исходный минимум сейчас `2026.10.5`) **не равен обязательно** текущему
публичному номеру. `tools/release_plan.py` выбирает effective version:

1. Не ниже исходного `VERSION` и текущего месяца по `Europe/Moscow`.
2. Для нового source SHA — строго выше максимальной стабильной опубликованной
   версии, даже если агент не изменил `VERSION`.
3. Чужие зарезервированные draft/tag номера пропускаются, не перезаписываются.
   Прерванную резервацию того же SHA можно продолжить, если она выше stable.
4. Уже опубликованный source SHA с полным набором assets — идемпотентный rerun:
   тот же номер, без новой публикации/замены публичных файлов.
   SHA уже выпущенного source определяется по неизменяемому тегу, а не по
   подвижному branch name, который GitHub иногда сохраняет в `target_commitish`.
5. При patch 99 следующий номер — первый patch следующего месяца; после декабря
   следующий год. Формат `YYYY.month.patch`, patch 0–99, year 2000–2099.
   При большом числе выпусков месяц номера может опередить календарный месяц.

Подготовленный номер передаётся во все jobs. Они временно применяют его к
`VERSION` **только в checkout runner** и регенерируют встраиваемые банки. APK
`versionName`, code и банк EXE/feed используют один номер. Source `VERSION` и
сгенерированные копии в Git остаются исходным минимумом; нет bot commits и цикла
автопубликации. До применения effective version Content job проверяет также,
что исходные сгенерированные assets уже синхронизированы/закоммичены.

Код APK: `(year-2000)*10000 + month*100 + patch`, например
`2026.10.5` → **261005**, `2026.10.6` → **261006**. CI проверяет фактические
метаданные через `aapt2`, а также рост относительно предыдущего опубликованного
APK (не только относительно тега). Для already-published rerun строгий previous
comparison пропускается: code закономерно равен тому же release; self
package/version/certificate gates остаются включёнными, повторная публикация выключена.

Публикующая ветка обязана **содержать историю последнего стабильного release**.
Если другая ветка выпустила более новый код, старую нельзя выдать за новое
обновление только увеличением номера. Планировщик и publisher проверяют ancestry
тега; при ошибке нужно интегрировать опубликованную историю в разрешённую рабочую
ветку. Сама версия не заменяет проверку происхождения кода.

## Очередь и безопасная публикация

Все доверенные branch CI и tag/manual Release используют общий outer lock
`ctmaths-release-pipeline` **от выбора версии до публикации**. `queue: max`,
`cancel-in-progress: false` сохраняют до **100** ожидающих запусков, вместо
обычной очереди из одного места, которая отменяла бы промежуточные pushes.
GitHub обрабатывает очередь по времени начала ожидания, не гарантирует порядок
самих dispatch событий; ancestry gate защищает от отката при обгоне/разных ветках.
Сверх 100 ожидающих запусков действует лимит платформы — проверьте Actions и
повторите отменённый запуск. Дочерний reusable CI из Release использует другой
lock (`ci-release-child-<run id>`), иначе возникла бы взаимная блокировка.

Publisher:

1. Проверяет полный набор файлов, версии JSON, SHA-256 и размеры контента.
2. Резервирует неизменяемый `v<effective version>` на **точном source SHA**
   через Actions token; затем создаёт private draft. Непубличный тег-резервация
   позволяет следующему read-only планировщику обойти прерванный чужой номер.
3. Загружает все assets в draft, сверяет точный inventory, uploaded state/размер
   и server digest (когда GitHub отдаёт digest).
4. Только после полной проверки **одним API PATCH** снимает draft и делает release
   latest. Затем проверяет API latest и полный inventory.

Если upload/проверка до финального PATCH не прошли, прежний latest/feed остаётся
нетронутым. `--clobber` разрешён **только для draft того же SHA** при восстановлении.
Публичные releases/assets и чужие теги/черновики не перезаписываются. Tags,
созданные `GITHUB_TOKEN`, не запускают второй release workflow: нет рекурсии.

## Публичные файлы и автоматический журнал

Каждый новый Release содержит **13 assets**:

- `app-release.apk`;
- `CTMathsTutor-amd64.exe`, `CTMathsTutor-arm64.exe`;
- `bank.json`, `analogous.json`, `topics.json`, `formulas.json`, `ui_strings.json`,
  `mistakes.json`, `answer_vectors.json`;
- `version.json` — версия, SHA-256/размеры и immutable version-specific URLs;
- `release-info.json` — source commit/floor/effective version, run/attempt/URL,
  результаты и время трёх обязательных jobs, сертификат/code, предыдущий stable
  tag, SHA-256/размеры payloads и стратегия публикации;
- `SHA256SUMS.txt` — контрольные суммы всех остальных 12 файлов, включая журнал.

`verifiedAt` — время проверки, не обещание публикации; фактические `draft=false`,
`published_at` и latest проверяются по Release API. Статус и адрес опубликованного
релиза также записываются в Actions summary. `release-audit` содержит manifest,
журнал и суммы даже при прерванной публикации, если файлы уже были подготовлены.
Тот же JSON-журнал продублирован в свёрнутом блоке Release body: агент может
прочитать его через `gh api .../releases/latest --jq .body`, даже если скачивание
бинарных assets в sandbox запрещено.
Человеческий журнал команд/решений/ошибок — [WORKLOG.md](WORKLOG.md); инструкции
новому агенту — [../AGENTS.md](../AGENTS.md).

Стабильные ссылки для пользователя:

- [Последний release](https://github.com/zigorminsk-debug/mathematics/releases/latest)
- [Android APK](https://github.com/zigorminsk-debug/mathematics/releases/latest/download/app-release.apk)
- [Windows amd64](https://github.com/zigorminsk-debug/mathematics/releases/latest/download/CTMathsTutor-amd64.exe)
- [Windows arm64](https://github.com/zigorminsk-debug/mathematics/releases/latest/download/CTMathsTutor-arm64.exe)
- [Банк: version.json](https://github.com/zigorminsk-debug/mathematics/releases/latest/download/version.json)
- [Автоматический журнал](https://github.com/zigorminsk-debug/mathematics/releases/latest/download/release-info.json)

## Подпись и обновление поверх существующего приложения

Не менять `applicationId = by.ziv.ctmaths`, постоянный
`android/keystore/ctmaths-release.p12` и ожидаемый отпечаток
`android/keystore/expected-cert-sha256.txt`:

```
B2:BD:B4:D1:26:B8:88:C7:D8:AF:50:80:F6:7E:CF:E1:E4:3F:EB:F2:8E:5D:1A:E6:61:D6:D7:AE:70:C5:14:65
```

CI требует `check_signature.py --require` для ключа/нового APK и предыдущего
публичного APK; `check_apk_update.py --previous` сверяет один пакет и строго
возрастающий code. Другой сертификат/пакет либо равный/меньший code блокируют
публикацию. Ключ в Git демонстрационный и публичный; не менять его у уже
распространяемого приложения без согласованной миграции. Для совершенно нового
приложения до первой публикации нужен собственный приватный ключ в секретах.

В новый public Release входит **только `app-release.apk`**. Debug-пакет
`by.ziv.ctmaths.debug` остаётся development artifact, устанавливается рядом и не
является обновлением стабильного приложения. Старые releases .1/.2 исторически
содержат debug — не предлагайте его пользователю и не переписывайте старые assets.

**Устанавливать release APK поверх, не удаляя приложение**: удаление стирает
локальную статистику. При проблеме получить точный текст ошибки и параметры
установленного APK. CI-проверка совместимости не является тестом на физическом
телефоне. Windows EXE заменяется без удаления `%APPDATA%\CTMathsTutor`.

## Обновление базы внутри приложений

Стабильный канал:
`https://github.com/zigorminsk-debug/mathematics/releases/latest/download/version.json`.

Android `NativeBridge` и Windows `Store.CheckUpdates()` сравнивают
`contentVersion`, проверяют SHA-256/размеры и устанавливают только целиком
проверенный временный пакет. Статистика/настройки не затрагиваются; старая
скачанная база не скрывает более новую встроенную. Автопроверка зависит от
настройки приложения; ручная кнопка — «Проверить обновления».

Manifest содержит version-specific URLs; нынешние native клиенты получают файлы
из выбранного base URL и проверяют суммы. Если latest сменился во время загрузки,
проверка не позволит установить смесь выпусков: предыдущая база сохранится,
повторная проверка загрузит новую. Публикация APK не означает автоматическую
установку APK на телефоне: это по-прежнему установка скачанного release APK поверх.

## Проверить результат / восстановить после ошибки

```bash
# Поменяйте branch только на разрешённую текущей сессией; здесь она фиксирована.
gh run list --workflow ci.yml --branch arena/d7e34c80-mathematics --limit 8 \
  --json databaseId,headSha,event,status,conclusion,url
gh run view <run-id> --json jobs,conclusion,url
gh api repos/zigorminsk-debug/mathematics/releases/latest \
  --jq '{tag: .tag_name, source: .target_commitish, draft: .draft, published: .published_at, assets: [.assets[] | {name, size, digest}]}'
gh api repos/zigorminsk-debug/mathematics/git/ref/tags/<published-tag> --jq '.object'
```

Не заменяйте `<run-id>`/`<published-tag>` выдуманным ID: возьмите из предыдущих
ответов API. Сверьте source SHA с push, все gates SUCCESS, 13 assets, отсутствие
`app-debug.apk`, effective version/code в журнале. При ошибке изучите check-run
annotations; полный лог/бинарные redirects в Arena могут быть недоступны.

- **Проверки красные:** исправить причину, регенерировать/sync, выполнить локальные
  gates, записать результат в worklog, push текущей ветки. Не выпускать принудительно.
- **Публикация прервана:** rerun **всего CI**, не только job публикации: он заново
  проверит источник и сформирует outputs/artifacts. Тот же SHA продолжит draft/tag,
  если номер ещё выше stable; новый SHA получит свободный более высокий номер.
  Если rerun permission в Arena отсутствует, исправляющий push автоматически
  запускает CI; старый draft остаётся непубличным, latest не ломается.
- **Ancestry error в shallow checkout:** сначала `git rev-parse --is-shallow-repository`;
  если `true`, `git fetch --unshallow origin`, затем повторить plan. Такой локальный
  false negative уже был обнаружен/устранён; CI checkout использует fetch-depth 0.
- **Старый branch не содержит latest source:** интегрировать историю в разрешённую
  рабочую ветку; не повышать номер поверх старого кода и не менять тег.
- **403 при manual dispatch / git/gh auth:** reconnect GitHub в Arena с нужными
  правами. Не запрашивать токены/пароли/2FA и не подменять auth-конфиг.
  2026-10-14 manual `gh workflow run release.yml` уже вернул 403; обычный push
  разрешён, автоматический publisher использует отдельный Actions `GITHUB_TOKEN`.
- **Already published:** не менять release и его assets; проверить готовый URL.

Дополнительный manual entry point (обычно не нужен): Actions → Release → Run
workflow на рабочей ветке, `tag` оставить пустым для автонумерации. Или
`gh workflow run release.yml --ref arena/d7e34c80-mathematics` при наличии Actions
write permissions. Не создавать вручную тег со старым `VERSION` floor: точный
requested tag должен равняться автоматически выделенному номеру.

Для **локального APK для обновления телефона** сначала получить актуальный номер
через `tools/release_plan.py --repo zigorminsk-debug/mathematics` (нужны gh/git и
история/теги), временно `--apply-version <effective-version>`, затем build/sync и
native gates. Не ставить локальный floor APK поверх более высокого public code.
Runner-only версии не нужно коммитить; исходные copies перед следующим commit
регенерировать для исходного VERSION floor. Проще и надёжнее скачать checked latest APK.

## Документация GitHub для queue: max

Поддержка multi-pending concurrency подтверждена официальным `github/docs`
(commit `ba6f6f9b9b31c4f0a991fbcb1005080526424804`, проверено 2026-10-14):
[actions-group-concurrency.md](https://github.com/github/docs/blob/ba6f6f9b9b31c4f0a991fbcb1005080526424804/data/reusables/actions/actions-group-concurrency.md).
Feature `actions-nga` включён для GitHub.com (`fpt`, `ghec`);
`queue: max` нельзя сочетать с `cancel-in-progress: true`.
