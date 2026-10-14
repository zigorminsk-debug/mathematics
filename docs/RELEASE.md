# Выпуск обновлений / Releasing updates

## Постоянный ключ (почему обновления ставятся «поверх»)

Android устанавливает новый APK поверх установленного **только если он подписан тем же
сертификатом**. Поэтому в репозитории лежит постоянный ключ проекта:

```
android/keystore/ctmaths-release.p12      контейнер PKCS#12 (срок действия до 2056 года)
android/keystore/keystore.properties      storeFile / storePassword / keyAlias / keyPassword
```

* `applicationId = by.ziv.ctmaths` — менять нельзя, иначе система сочтёт это другим приложением.
* `versionCode` растёт автоматически в CI (`github.run_number`), `versionName` — из тега.
* Отпечаток ключа проверяйте командой:

  ```bash
  keytool -list -v -keystore android/keystore/ctmaths-release.p12 -storetype PKCS12 -storepass ctmaths2026
  ```

**Перед публикацией в Google Play** замените демонстрационный ключ на свой приватный:
положите новый `.p12` рядом, обновите `keystore.properties` **или** задайте секреты репозитория
`ANDROID_KEYSTORE_FILE`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
`ANDROID_KEY_PASSWORD` — `android/app/build.gradle.kts` предпочтёт переменные окружения.
Файл ключа в таком случае храните в секретах (base64), а не в репозитории.

Windows-сборка не требует подписи для установки «поверх»: достаточно заменить `CTMathsTutor-*.exe`.
Для подписи Authenticode добавьте сертификат и шаг `signtool` в `.github/workflows/release.yml`
(структура workflow уже это допускает).

## Как выпустить релиз

1. Обновите версию банка заданий в файле `VERSION` (например `2026.10.2`).
2. Убедитесь, что всё собирается локально:

   ```bash
   python3 tools/build_content.py && python3 tools/sync_assets.py
   node tests/answer_parity.js
   (cd windows && go test ./...)
   (cd android && gradle testDebugUnitTest)
   ```

3. Запустите workflow **Release** (Actions → Release → Run workflow) или поставьте тег:

   ```bash
   git tag v2026.10.2 && git push origin v2026.10.2
   ```

4. Перед публикацией workflow проверяет подпись APK
   (`python3 tools/check_signature.py` — сверка с `android/keystore/expected-cert-sha256.txt`).
   Если подпись отличается, релиз не выпускается: такое обновление не установилось бы
   поверх предыдущей версии.

5. Workflow соберёт и опубликует:
   * `CTMathsTutor-amd64.exe`, `CTMathsTutor-arm64.exe` — Windows-приложения;
   * `app-release.apk` (подписан постоянным ключом) и `app-debug.apk`;
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

* **Android** — `NativeBridge.checkUpdates()`: скачивает манифест, сравнивает `contentVersion`,
  проверяет SHA-256 каждого файла и кладёт пакет в `filesDir/content`. Прогресс не затрагивается.
* **Windows** — `Store.UpdateContent()`: то же самое в `%APPDATA%\CTMathsTutor\data\content`,
  запускается автоматически при старте (если включено автообновление) или кнопкой
  «Проверить обновления».
* Скачанная версия банка имеет приоритет над встроенной; при ошибке проверки контрольной суммы
  обновление отклоняется, приложение продолжает работать на прежней базе.

## Проверка перед публикацией

* [ ] `python3 tools/build_content.py` — все проверки заданий пройдены.
* [ ] `python3 tools/sync_assets.py --check` — копии интерфейса и банка синхронны.
* [ ] `node tests/answer_parity.js` — алгоритм проверки ответов совпадает во всех реализациях.
* [ ] `go test ./...` и `gradle testDebugUnitTest` — зелёные.
* [ ] `VERSION` увеличен, если банк заданий изменился.
* [ ] В релиз попали оба EXE, APK и все JSON-файлы банка.
