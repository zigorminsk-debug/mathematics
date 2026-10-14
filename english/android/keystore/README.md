# Ключ подписи английского тренажёра (`english/android/keystore/`)

Здесь лежит **постоянная** подпись Android-приложения «Репетитор ЦТ: Английский
язык» (`by.ziv.ctenglish`). Она зафиксирована до первого выпуска: после публикации
первого APK пакет и сертификат менять нельзя, иначе обновление не установится
поверх уже установленного приложения.

| Файл | Назначение |
|---|---|
| `ctenglish-release.p12` | PKCS#12-хранилище release-подписи (alias `ctenglish`) |
| `keystore.properties` | путь/alias/пароли для Gradle (`storeFile`, `storePassword`, `keyAlias`, `keyPassword`, `storeType`) |
| `expected-cert-sha256.txt` | SHA-256 отпечаток сертификата, который сверяет CI |

Отпечаток сертификата:

```
5F:70:75:90:3B:9A:AA:9E:AB:B6:64:40:5E:A7:05:05:92:25:CA:9C:34:75:19:79:53:DE:B2:7E:13:97:98:25
```

## Как это проверяется

```bash
CT_SUBJECT=english python3 tools/check_signature.py --require \
  --keystore english/android/keystore/ctenglish-release.p12
```

В CI тот же инструмент запускается перед сборкой и по собранному APK
(`.github/workflows/english-ci.yml`, задание `android`):

```bash
CT_SUBJECT=english python3 ../../tools/check_signature.py --require \
  --apk app/build/outputs/apk/release/app-release.apk \
  --tool "$ANDROID_HOME/build-tools/34.0.0/apksigner"
```

Дополнительно CI скачивает APK **предыдущего** английского релиза
(свойство `needs.prepare.outputs.previous_tag`) и требует, чтобы новая сборка была
подписана тем же сертификатом и имела строго больший `versionCode`
(`tools/check_apk_update.py --previous`). Математический и физический APK в эту
проверку не попадают никогда: `previous_tag` берётся только из семьи `english-v*`.

## Правила

1. **Не менять ключ.** Ротация возможна только вместе с новым пакетом (например
   `by.ziv.ctenglish2`) и явным решением пользователя; иначе обновление сломается.
2. **Не хранить пароли в чате.** Секреты можно передать через переменные CI
   (`CTENGLISH_KEYSTORE_FILE`, `CTENGLISH_KEYSTORE_PASSWORD`, `CTENGLISH_KEY_ALIAS`,
   `CTENGLISH_KEY_PASSWORD`, `CTENGLISH_KEYSTORE_TYPE`); `app/build.gradle.kts`
   читает сначала их, затем исторические `ANDROID_*`, и только потом локальный
   `keystore.properties`. Файл `keystore.properties` содержит локальные значения и
   не должен попадать в чужие ветки.
3. **Чужие ключи не переиспользуются.** Математика (`B2:BD:…:65`, `ctmaths-release.p12`)
   и физика (`A3:55:CB:…:35:83`, `ctphysics-release.p12`) имеют собственные ключи;
   подписать английский APK их сертификатом запрещено контрактом изоляции
   (см. `docs/subjects/ENGLISH.md` и `tests/test_subject_profiles.py`).
4. **Debug-подпись не публикуется.** В релиз попадает только release-APK,
   переименованный в `engtutor.apk`; `app-debug.apk` остаётся артефактом
   разработки и использует отдельный пакет `by.ziv.ctenglish.debug`.

## Если ключ потерян

Публикация обновлений «поверх» становится невозможной: пользователям придётся
ставить приложение заново. Поэтому перед первым релизом файл дублируют в защищённом
хранилище (внешний сейф/менеджер секретов). В репозитории хранится только текущая
копия и отпечаток.
