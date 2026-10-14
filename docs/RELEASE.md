# Выпуск обновлений / Releasing updates

## Постоянный ключ (почему обновления ставятся «поверх»)

Android устанавливает новый APK поверх установленного **только если он подписан тем же
сертификатом**. Поэтому в репозитории лежит постоянный ключ проекта:

```
android/keystore/ctmaths-release.p12      контейнер PKCS#12 (срок действия до 2056 года)
android/keystore/keystore.properties      storeFile / storePassword / keyAlias / keyPassword
```

* `applicationId = by.ziv.ctmaths` — менять нельзя, иначе система сочтёт это другим приложением.
* `versionCode` выводится в Gradle из файла `VERSION` (`2026.10.4` → `261004`) и потому
  одинаков в локальной, CI- и релизной сборках и монотонно растёт с каждым выпуском.
  Раньше кодом был `github.run_number` у релизного workflow, а в CI и локально — `1`:
  APK из разных каналов могли иметь меньший код, чем уже установленный, и Android
  отказывал в установке поверх (`INSTALL_FAILED_VERSION_DOWNGRADE`). Тег релиза обязан
  совпадать с `VERSION` — workflow проверяет это до сборки.
* В релиз входит только `app-release.apk`. `app-debug.apk` (пакет
  `by.ziv.ctmaths.debug`) ставится рядом, а не поверх, и больше в релиз не публикуется;
  в CI он подписан тем же постоянным ключом, чтобы хотя бы debug поверх debug вставал.
* Отпечаток ключа проверяйте командой:

  ```bash
  keytool -list -v -keystore android/keystore/ctmaths-release.p12 -storetype PKCS12 -storepass ctmaths2026
  ```

Ключ из репозитория демонстрационный и публичный. **Не заменяйте его у уже
распространяемого приложения без согласованной миграции подписи**: это нарушит обновление
поверх. Для нового приложения до первой публикации в Google Play нужен собственный
приватный ключ. Его параметры задаются через `keystore.properties` или переменные
`ANDROID_KEYSTORE_FILE`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
`ANDROID_KEY_PASSWORD`; приватный файл хранится в секретах, не в репозитории.
Эталон сертификата должен оставаться совместимым с уже установленными APK.

Windows-сборка не требует подписи для установки «поверх»: достаточно заменить `CTMathsTutor-*.exe`.
Для подписи Authenticode добавьте сертификат и шаг `signtool` в `.github/workflows/release.yml`
(структура workflow уже это допускает).

## Как выпустить релиз

1. Обновите версию банка заданий в файле `VERSION` (например `2026.10.4`) — от неё же выведется `versionCode` APK.
2. Убедитесь, что всё собирается локально:

   ```bash
   python3 tools/build_content.py && python3 tools/sync_assets.py
   node tests/answer_parity.js
   (cd windows && go test ./...)
   (cd android && gradle testDebugUnitTest)
   ```

3. Запустите workflow **Release** (Actions → Release → Run workflow) или поставьте тег:

   ```bash
   git tag v2026.10.4 && git push origin v2026.10.4
   ```

4. Перед публикацией workflow проверяет подпись APK
   (`python3 tools/check_signature.py` — сверка с `android/keystore/expected-cert-sha256.txt`).
   Если подпись отличается, релиз не выпускается: такое обновление не установилось бы
   поверх предыдущей версии.

5. Workflow соберёт и опубликует:
   * `CTMathsTutor-amd64.exe`, `CTMathsTutor-arm64.exe` — Windows-приложения;
   * `app-release.apk` (подписан постоянным ключом; CI дополнительно сверяет пакет
     `by.ziv.ctmaths` и `versionCode`/`versionName` собранного APK с `VERSION`);
   * `bank.json`, `analogous.json`, `formulas.json`, `mistakes.json`, `ui_strings.json`,
     `topics.json`, `version.json` — банк заданий и манифест с SHA-256.

Эталонный отпечаток ключа можно посмотреть и проверить локально:

```bash
python3 tools/check_signature.py          # сверить собранный APK с эталоном
cat android/keystore/expected-cert-sha256.txt
```

## Как приложения получают новую базу

Манифест публикуется по стабильному адресу
`https://github.com/zigorminsk-debug/mathematics/releases/latest/download/version.json`.

* **Android** — `NativeBridge.checkUpdatesAsync()`: запускает сетевую проверку в фоне,
  сравнивает `contentVersion`, проверяет SHA-256 и размеры файлов. Полностью проверенный
  пакет вместе с `version.json` устанавливается в `filesDir/content` целиком.
* **Windows** — `Store.CheckUpdates()`: то же самое в `%APPDATA%\CTMathsTutor\data\content`.
* На обеих платформах проверка запускается при старте (если включено автообновление)
  или кнопкой «Проверить обновления». После ручного обновления новые годы видны сразу.
* Скачанная версия имеет приоритет только если она **не старше встроенной**. Поэтому
  после установки нового APK/EXE прежний скачанный банк не скрывает вариант 2026.
  Более старая версия в `releases/latest` также не откатывает банк нового приложения.
* Файлы сначала скачиваются и проверяются во временной папке; только целый пакет
  заменяет прежний. При ошибке сети или последней контрольной суммы прежняя база
  остаётся нетронутой. Папки прогресса, настроек и текущего задания не затрагиваются.
* Перед публикацией `tools/check_apk_update.py` сравнивает пакет и `versionCode` нового
  APK с **предыдущим опубликованным APK**, а `check_signature.py --require` проверяет
  подписи обоих. Релиз блокируется, если новый пакет/подпись другие или код не вырос.

## Проверка перед публикацией

* [ ] `python3 tools/build_content.py` — все проверки заданий пройдены.
* [ ] `python3 tools/sync_assets.py --check` — копии интерфейса и банка синхронны.
* [ ] `node tests/answer_parity.js` — алгоритм проверки ответов совпадает во всех реализациях.
* [ ] `go test ./...` и `gradle testDebugUnitTest` — зелёные.
* [ ] `VERSION` увеличен, если банк заданий изменился (иначе не вырастет и `versionCode` APK).
* [ ] Тег релиза совпадает с `VERSION` (`v` + версия), в релиз попал только `app-release.apk`.
* [ ] В релиз попали оба EXE, APK и все JSON-файлы банка.
