# RELEASE.md — релизы физики: как устроены и как проверяются

Физика живёт в том же репозитории, что и математика, поэтому главный риск —
случайно переключить глобальный latest на чужой APK. Ниже — контракт, который
реализован в коде и **обязан** оставаться таким.

## 1. Идентичность и канал

| Что | Физика | Математика (не трогать) |
|---|---|---|
| Теги | `physics-vYYYY.M.P` | `vYYYY.M.P` |
| `make_latest` | **`false`** всегда | `true` |
| Канал обновления | `https://github.com/<repo>/releases/download/physics-v<version>` через Releases API (пагинация, фильтр по family) | глобальный `/releases/latest/download` |
| APK | `phyzics.apk` (внутренняя сборка Gradle — `app-release.apk`) | `app-release.apk` |
| EXE | `CTPhysicsTutor-amd64.exe`, `CTPhysicsTutor-arm64.exe` | `CTMathsTutor-*.exe` |
| Пакет Android | `by.ziv.ctphysics` (`by.ziv.ctphysics.debug` для debug) | `by.ziv.ctmaths` |
| versionCode | `(Y−2000)*10000 + M*100 + P` из VERSION | то же правило |
| Сертификат | `android/keystore/ctphysics-release.p12`, отпечаток `A3:55:CB:12:F5:22:E9:A7:F6:FE:E3:A6:6C:E9:15:1D:73:23:40:58:A9:85:FA:57:19:CD:28:3E:63:21:35:83` | `B2:BD:…:65` |
| Очередь | `ctphysics-release-pipeline` | `ctmaths-release-pipeline` |

`tools/subject.py` — единственный источник этих значений. Любой инструмент,
который раньше был жёстко привязан к математике, импортирует их оттуда; тесты
изоляции проверяют, что строка `mathematics`/`ctmaths` не утекает в предметные
константы (кроме явных упоминаний «математика не меняется»).

## 2. Инвентарь релиза (ровно 13 файлов)

`tools/release_plan.py` → `RELEASE_FILES`:

* 7 файлов контента: `bank.json`, `analogous.json`, `topics.json`, `formulas.json`,
  `ui_strings.json`, `mistakes.json`, `answer_vectors.json`;
* `version.json` (манифест: subject/package/tagPrefix/updatePolicy/baseUrl + SHA-256
  и размеры всех файлов);
* `release-info.json` (audit: репозиторий, коммит, run id, версия, инвентарь);
* `SHA256SUMS.txt`;
* **`phyzics.apk`** (подписанный release APK);
* `CTPhysicsTutor-amd64.exe`, `CTPhysicsTutor-arm64.exe`.

Публикация проверяет, что в черновике оказались **ровно** эти файлы; debug-APK в
релиз не попадает никогда.

## 3. Как проходит сборка и публикация

```
push в рабочую ветку ─► prepare (release_plan: версия этой семьи, идемпотентность)
                         │
                         ├─ content  (build_content → --check → sync_assets → diff → версия →
                         │            node --check → answer_parity → content_schema → unittest →
                         │            check_syntax --require → jsdom-смоуки)
                         ├─ windows  (go vet/test, две архитектуры, SOURCE_DATE_EPOCH)
                         └─ android  (отпечаток ключа → unit-тесты → debug+release APK →
                                      проверка подписи → проверка versionCode/пакета →
                                      сравнение с прошлым APK физики)
                                      │
                                      ▼
                    publish (только в этом же run, только из push/ручного запуска,
                             никогда из PR/fork; make_latest=false;
                             abort, если глобальный latest изменился во время публикации)
```

Правила, которые нельзя ослаблять:

1. Публикуются **только проверенные в этом же run** артефакты: публикатор не
   пересобирает бинарники.
2. PR и fork не публикуют: `validate_run` требует точный репозиторий, коммит и
   событие `push`/`workflow_dispatch`; `ALLOW_PUBLICATION` в CI вычисляется явно.
3. Already-published коммит не перепубликуется (идемпотентность), теги и ассеты
   неизменяемы.
4. Планировщик ищет предыдущий стабильный релиз **только своей семьи** и никогда
   не берёт APK математики как «предыдущий» для физики.
5. Клиент проверяет subject/package манифеста и SHA-256 файлов и отвергает чужой
   банк (математика ↔ физика).

## 4. Как проверить релиз (чек-лист, который должен уметь любой агент)

```bash
# 1. Тег и коммит
gh release view physics-vYYYY.M.P --repo zigorminsk-debug/mathematics \
  --json tagName,targetCommitish,assets,isLatest,isPrerelease

# 2. Инвентарь и подписи файлов
gh release download physics-vYYYY.M.P --dir /tmp/phys --repo zigorminsk-debug/mathematics
cd /tmp/phys && sha256sum -c SHA256SUMS.txt

# 3. package/versionCode APK
"$ANDROID_HOME/build-tools/34.0.0/aapt2" dump badging phyzics.apk | head -3

# 4. Математика не пострадала
gh release view --repo zigorminsk-debug/mathematics \
  --json tagName,isLatest   # должен остаться математический latest
```

Ответ «релиз вышел» даётся только после шагов 1–4 на фактическом GitHub.
Локальная проверка синтаксиса релизом не является.

## 5. Что отмечать как «не проверено»

* Установка APK на реальный телефон и установка EXE на реальную Windows — в
  песочнице невозможны; писать `tested`/`not tested` раздельно и не заявлять
  непроверенное.
* Обновление «поверх предыдущей версии» проверяется CI только после появления
  первого релиза физики (сравнение подписи и versionCode с прошлым APK).
* Ручные действия (если понадобятся) не заменяют `make_latest=false` и не
  переключают глобальный latest.

## 6. Откат и ошибки

* Опубликованный тег и ассеты не перезаписываются: ошибка исправляется новым
  патч-релизом (`physics-vYYYY.M.P+1`).
* Если публикация упала после создания черновика, повторный запуск того же
  коммита продолжит свой черновик (`--clobber` действует только на собственный
  черновик) и не тронет чужие релизы.
* Если `prepare` не смог определить версию (нет прав, нет сети), публикация не
  начинается: сборка без версии не выпускается.
