# Журнал действий и handoff / Worklog

**Правило пользователя от 2026-10-14:** автоматически публиковать все новые
проверенные сборки сразу после изменений и документировать работу для любого
следующего агента. Разрешение распространяется на APK, оба Windows EXE и банк.

Этот файл — **датированные снимки и выполненные действия**, не live latest.
Актуальные SHA/run/release всегда получать из Git и GitHub API. Каждый будущий
выпуск сам записывает immutable `release-info.json`, тот же JSON в Release body,
`SHA256SUMS.txt` и Actions summary/audit. Так журнал не требует бесконечных bot commits.
Порядок работы/команды — [../AGENTS.md](../AGENTS.md), релизный runbook — [RELEASE.md](RELEASE.md).

## Исходная точка (до запроса автопубликации, 2026-10-14)

- Repository: `zigorminsk-debug/mathematics`, рабочая Arena-ветка
  **`arena/d7e34c80-mathematics`**, PR **[#4](https://github.com/zigorminsk-debug/mathematics/pull/4)**
  открыт против `main`; base `22547d665402c45743b50a948f65d5ae21ab339a`.
- `bbfef44`: добавлен авторский вариант 2026, изучение после ошибок, совместимый
  release APK. `f4d9fa2`: диагностика отказа APK metadata gate через annotations.
  `ca42e3d`: parser не путает package name с `compileSdkVersionCodename`.
- `ac2ef16b3dd72866434e0b2b682a160718eabf36`: кликабельные определения/теоремы,
  source **2026.10.4**, APK code **261004**. 56 офлайн RU/EN уроков для 18 тем,
  54 пункта повторения, 14 групп/116 формул. Back/язык сохраняют ответ, поиск,
  состояние, прокрутку и фокус; `nav_home` исправлен.
- 6 **авторских, не официальных РИКЗ** вариантов 2021–2026: 180 экзаменационных
  + 552 аналогичных = **732** задания; 2026 содержит 18 A + 12 B. 30 answer vectors,
  179 UI strings, 106 диагнозов ошибок.
- Все прежние gates прошли: arithmetic/schema/parity/sync, syntax, UI/native/theory,
  **15** Python tests, native Go/Kotlin/APK builds. Реальный мобильный Chromium
  (393×851, DPR 1.8, touch, RU/EN, dark/large text, Back/focus/search) проверен
  дважды; это **не** тест установки на физическом телефоне.
- Push CI [38520312916](https://github.com/zigorminsk-debug/mathematics/actions/runs/38520312916)
  и PR CI [38520316386](https://github.com/zigorminsk-debug/mathematics/actions/runs/38520316386)
  — SUCCESS, все 3 build jobs. Release APK .4 находился лишь в Actions artifact
  [11873287857](https://github.com/zigorminsk-debug/mathematics/actions/runs/38520312916/artifacts/11873287857).
  Другие artifacts: debug `11873098108`, Windows `11873102856`, content `11873806059`.
- PR body обновлён REST PATCH; `gh pr edit` локально не работает из-за deprecated
  Projects(classic) GraphQL. Scratch preview сброшен в RU; scratch файлы не handoff.
- Последний **публичный** release в этот момент — **v2026.10.2**, опубликован
  `2026-10-14T04:09:11Z`. .3/.4 были CI artifacts, не Releases. Нельзя утверждать
  публикацию .4 или проверку установки на телефоне.

## 2026-10-14 — новый запрос и диагностика доступа

**Выполнено:**

1. Проверены branch/status/log, текущие workflows, Gradle, APK checker,
   `docs/RELEASE.md`, PR #4, releases и последние CI. HEAD `ac2ef16`, дерево чистое.
   `AGENTS.md` отсутствовал. CI только загружал artifacts; Release был tag/manual
   и отдельной пересборкой с неполными web/UI gates.
2. `gh api repos/zigorminsk-debug/mathematics/actions/permissions` → **403**
   `Resource not accessible by integration`. Не требуется для реализации push CI.
3. Попытка выпустить .4:
   ```bash
   gh workflow run release.yml --ref arena/d7e34c80-mathematics \
     -f tag=v2026.10.4 -f release_name='CT Maths Tutor'
   ```
   → **HTTP 403**, workflow id `383915025`, endpoint `/dispatches`.
   **Ни run, ни tag, ни release не созданы.** Не повторять без изменения прав.
4. Пользователю сообщён недостаток manual Actions permissions и необходимость
   reconnect GitHub в Arena для ручных запусков; никаких credentials не запрошено.
   Выбран push-triggered CI с собственным scoped Actions `GITHUB_TOKEN`.

## 2026-10-14 — реализация автопубликации и долговременного журнала

**Выполненные изменения (локально, до первого push):**

- Source floor `VERSION` поднят до **2026.10.5**; build/sync обновили все
  встраиваемые generated copies. Нельзя использовать floor как live latest.
- `tools/release_plan.py`: effective version выше stable, source/calendar floor,
  безопасные patch/month/year переходы; idempotent published rerun; own draft/tag
  recovery; чужие резервации не перезаписываются. Проверка ancestry последнего
  public tag. Source SHA берётся из immutable тега, не подвижного API
  `target_commitish` branch name. VERSION применяется только в runner checkout.
- CI: prepare outputs → неизменённые полные content/windows/android gates →
  reusable publisher с `needs` всех jobs. Проверены исходные committed assets
  **до** effective-version regeneration. Explicit bash/pipefail не маскирует
  отказ `go vet` выходным кодом `sed`. В native jobs передаётся тот же номер.
  Android дополнительно скачивает previous stable APK, проверяет его сертификат
  и строго возрастающий фактический package/code нового APK. Already-published
  rerun пропускает строгий previous comparison (code равен тому же release),
  но self package/version/certificate checks остаются; новая публикация выключена.
- `publish.yml` + `tools/publish_release.py`: same-run artifacts; проверка run/SHA/
  event/repository и результатов обязательных jobs; точные inventories; проверка
  JSON/hash/bytes; tag на source SHA → draft → загрузка всех 13 assets → проверка
  server digest/inventory → один publish/make_latest PATCH → подтверждение latest.
  Debug исключён. Public assets/tags неизменяемы; повторная загрузка только в own draft.
- Release tag/manual entry points теперь вызывают **полный reusable CI**, без
  отдельной непроверенной пересборки. Child lock отличается от outer lock.
- Общая concurrency queue `queue: max`, `cancel-in-progress: false`: до 100
  pending runs вместо отмены промежуточных pushes. Поддержка проверена по
  официальному `github/docs` commit
  `ba6f6f9b9b31c4f0a991fbcb1005080526424804` через GitHub Contents API.
  FIFO по началу ожидания, не по dispatch; ancestry gate защищает от старой ветки.
- Автоматический audit: `release-info.json`, `SHA256SUMS.txt`, Release notes +
  API-readable копия JSON в body, Actions summaries, `release-audit` artifact.
  Нет bot commits, которые сами запускали бы бесконечные новые releases.
- Созданы `AGENTS.md`, этот journal, pinned `requirements-dev.txt`;
  переписан `docs/RELEASE.md`, обновлён README; ignored release/staging/previous-APK
  output. Нативный код/пакет/постоянный ключ и учебные материалы не менялись.

**Команды и результаты локальной проверки (до 06:54 UTC / 09:54 MSK):**

```text
python3 -m venv .venv
.venv/bin/python -m pip install PyYAML==6.0.3 tree-sitter tree-sitter-go tree-sitter-kotlin
python3 tools/build_content.py                 SUCCESS: 732 tasks, 56 lessons, 30 vectors
python3 tools/sync_assets.py                   SUCCESS
python3 tools/sync_assets.py --check           SUCCESS
node --check webapp/core.js / webapp/app.js     SUCCESS
node tests/answer_parity.js                    SUCCESS: 30 vectors, 180 stored answers
node tests/content_schema.js                  SUCCESS: 180 + 552, 179 strings, 56 lessons
node tests/ui_smoke.js                         SUCCESS
node tests/native_smoke.js                     SUCCESS
node tests/theory_smoke.js                     SUCCESS: 108 points / 28 groups / 232 formulas RU/EN
.venv/bin/python -m unittest discover ...       SUCCESS: 42 tests
.venv/bin/python tools/check_syntax.py --require SUCCESS: 12 Go/Kotlin/DSL files
python3 tools/release_plan.py --local           floor .5, publish=false, no API mutations
 git diff --check                              SUCCESS
```

Tests include counters without manual bump, calendar/99/year boundaries, idempotency,
wrong explicit tag, interrupted/different-source drafts, stale ancestry, PR/fork/
wrong SHA rejection, all three required job conclusions, missing/debug/corrupt
artifacts, server digests, atomic draft promotion with **mocked** GitHub and
workflow/YAML contracts. The mock initially printed `Published: ...v2026.10.5` (stdout is now isolated), which is **not**
an actual release; real publication must be verified separately after push.

**Ограничения / отвергнутые пути:**

- Локальных Go/JDK/Gradle нет: новые native tests/builds и реальная publication
  должны быть подтверждены новым CI, не подменены предыдущим зелёным .4 запуском.
- Попытка установить `actionlint-py==1.7.12.25` не удалась: скачивание GitHub binary
  redirect → TLS EOF. Повтор без изменения среды не нужен. Зависимости отдельно
  установлены в ignored venv. Actionlint v1.7.12 parser не знает новый `queue` key;
  YAML/contracts проверены PyYAML, фактическая Actions validation — новым run.
- Нельзя скачивать старые/full logs/artifacts повторно тем же способом, если
  redirect блокируется sandbox. API metadata/annotations доступны; runners и
  user-browser download links имеют доступ.
- Исходная ошибка установки APK на конкретном телефоне по-прежнему не воспроизведена.
  Не удалять приложение и не обещать устройство-тест по результату CI.

**Статус этого снимка:** implementation/local gates готовы; реальный push,
его run ID и опубликованный effective version **ещё не подтверждены** в момент
записи раздела. PR #4 пока не слит; main сохраняет старый CI, автоматизация
доступна в этой рабочей ветке и её потомках. Слияние не выполняется без запроса.
Следующая запись фиксирует фактический результат. Для live state
выполнить команды из `AGENTS.md` и прочитать release audit через API body.

## 2026-10-14 07:12 UTC / 10:12 MSK — первая настоящая автопубликация подтверждена

**Commit/push и устранённый false negative:**

1. Изменения закоммичены **`142e3d0308fe318a00026004aadd4060a390aaa2`**,
   `ci: автоматически публиковать проверенные сборки и вести журнал` (26 files).
2. Первый pre-push `python3 tools/release_plan.py --repo ...` остановил цепочку
   **до push**: ancestry v2026.10.2 (`280bf7d23bd8a5158c8b0f1903799077076eae14`)
   казалась отсутствующей. `git log --graph` показал `(grafted)` у base `22547d6`.
   Причина — **shallow local checkout**, не разошедшиеся ветки.
3. `git rev-parse --is-shallow-repository` → `true`;
   **`git fetch --unshallow origin`**; `git merge-base --is-ancestor v2026.10.2 HEAD`
   → SUCCESS. Никакие ветки не переключались/не создавались; ненужный merge
   не выполнялся, ancestry gate не ослаблялся. Plan → effective `.5`, previous `.2`.
4. `git push origin arena/d7e34c80-mathematics` → SUCCESS. Автоматически стартовали
   push CI **[38526230618](https://github.com/zigorminsk-debug/mathematics/actions/runs/38526230618)**
   и PR CI **[38526235621](https://github.com/zigorminsk-debug/mathematics/actions/runs/38526235621)**.
   `gh run watch ... --exit-status` для обоих завершился **0**.

**Реальные CI / Release результаты:**

- Оба CI — **SUCCESS** на `142e3d0`. Prepare, content, Windows и Android зелёные.
  Push Android: Kotlin tests, обе APK сборки, подпись, actual package/name/code,
  **previous stable APK signature + строго выросший code** — SUCCESS.
  Windows: actual `go vet`, `go test`, amd64 + arm64 builds — SUCCESS.
- Push publisher — **SUCCESS**, same-run artifacts. PR publisher — **SKIPPED**,
  что дополнительно подтверждено Jobs API; PR не создал второй Release.
- **[v2026.10.5](https://github.com/zigorminsk-debug/mathematics/releases/tag/v2026.10.5)**,
  release ID **412430555**, `published_at = 2026-10-14T07:08:54Z`,
  `draft=false`, `prerelease=false`, latest. Git ref тега точно
  `142e3d0308fe318a00026004aadd4060a390aaa2`.
- API-readable audit: source floor **2026.10.5**, effective/content/APK name
  **2026.10.5**, APK code **261005**, run **38526230618**, previous stable **v2026.10.2**;
  все 3 записанных job conclusions — SUCCESS, permanent certificate unchanged.
- Подтверждены **все 13 assets**, debug отсутствует. Каждый из 11 payload
  server digests/bytes совпал с audit. Из API body независимо восстановлены
  `release-info.json` и `SHA256SUMS.txt`: их длины и SHA-256 также совпали с
  двумя оставшимися server assets. Бинарные скачивания sandbox не требовались.
- Actual APK size **5,108,409 bytes**, SHA-256
  `6a8857ade7ccab5f097275637df3eaf468e3bb4280d0330b463311628b381730`;
  EXE amd64 **7,379,968**, arm64 **6,999,552** bytes. Прогресс на телефоне
  не удалять; установка на самом устройстве здесь по-прежнему не проверена.
- Реальный read-only повтор `python3 tools/release_plan.py --repo ...` на том же
  clean SHA → `.5`, **`already_published=true`**, готовый release URL. Это проверка
  реальной идемпотентности планировщика, **не** ручной Actions rerun (dispatch
  permissions всё ещё не предоставлены/не обходились).

**Финализация журналов / следующий автоматический push этого снимка:**

- Добавлены эти фактические SHA/run/release/check результаты, shallow recovery
  в AGENTS/runbook. В ветке остаётся source floor **2026.10.5**, он **не повышается**.
- CI предупредил о переходе `ubuntu-latest` на Ubuntu 26 с **2026-10-19**.
  Все build/publisher runners закреплены на **`ubuntu-24.04`** для предсказуемости;
  stdlib-only Go cache выключен (без go.sum он давал только warning).
- Node20 actions forced to Node24 warnings были **неблокирующими**. Массовое
  обновление major versions Actions не выполнялось; текущие native builds прошли.
- Перед следующим push повторно **SUCCESS**: 42 Python/workflow tests, native
  syntax (12 файлов), 732 task checks/30 vectors, sync, JS/schema/parity,
  UI/native/theory journeys и diff gate. Его ожидаемый effective номер —
  **2026.10.6/code261006** без изменения VERSION floor: это реальная проверка
  автоматического роста. **Ещё не объявлять этот номер опубликованным** по данному
  снимку: окончательные SHA/run/статус этой отправки автоматически запишутся в
  Release audit/API body, если все проверки и publisher пройдут.
- PR #4 остаётся OPEN, `main` не сливался/не менялся напрямую. Автопубликация
  уже работает для текущей ветки; старый main унаследует её после слияния PR.
  Следующему агенту начинать с актуальной опубликованной истории и API state.

## Как добавлять следующую запись (любой агент)

1. UTC timestamp и при необходимости MSK; исходные branch/SHA/VERSION floor,
   user request и конкретный scope.
2. Изменённые исходники и правила/решения, особенно подпись/версия/content data.
3. Реально выполненные команды, результат и различие local / CI / mock / device.
4. Commit SHA, PR, Actions run URL/event/conclusion; published tag/source/assets
   или явное «не опубликовано» с причиной. Не выдавать artifacts за Release.
5. Ошибки/права/ограничения, что **не повторять**, что осталось и следующий шаг.

Запись результата и её push сами создают следующий автоматический выпуск. Это
нормально: source floor можно не менять, версия повысится по latest. Не писать
bot commit после каждого автоматического журнала; immutable Release audit уже
фиксирует окончательный результат этого documentation push.
