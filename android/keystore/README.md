# Ключ подписи Android / Android signing key — «Репетитор ЦТ: Русский язык»

```
ctrussian-release.p12      постоянный ключ приложения by.ziv.ctrussian (PKCS#12, RSA 3072, до 2056 года)
keystore.properties        пароль и псевдоним (используется сборкой и CI)
expected-cert-sha256.txt   эталонный отпечаток сертификата (зафиксирован ДО первого выпуска)
```

```
Owner:   CN=CT Russian Tutor, OU=Android release, O=Zakharevich Igor, L=Minsk, C=BY
SHA-256: DE:65:1A:CC:E1:DB:76:9B:DC:A8:DB:EB:04:5C:94:9F:39:7F:85:7A:E6:DB:12:EE:D1:32:38:A0:83:B6:6A:3D
Создан:  2026-10-14 (до первой публикации russian-v…)
```

**Отдельный ключ.** Это не ключ математики (`by.ziv.ctmaths`, отпечаток `B2:BD:B4:…:14:65`
остаётся только в своей ветке и не меняется). `tests/test_android_build.py` проверяет,
что отпечаток русского ключа не совпадает с математическим и что APK подписан именно им.

**Почему ключ лежит в репозитории.** Так же устроен ключ математики: распространение —
через GitHub Releases (sideload), а секреты Actions из сессии сборки записать нельзя
(API вернул 403). Ключ в Git публичен: любой, у кого есть доступ к репозиторию, технически
может подписать APK тем же сертификатом. Перед публикацией в магазинах приложений
нужен приватный ключ в секретах (`ANDROID_KEYSTORE_FILE`, `ANDROID_KEYSTORE_PASSWORD`,
`ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`) — но смена ключа после первого выпуска ломает
обновление «поверх» (на Android 9+ возможна только ротация через APK Signature Scheme v3).
Решение о такой миграции принимает владелец; см. `docs/RELEASE.md`.

**Не меняйте этот ключ** у уже распространяемого APK: CI сверяет и сам ключ
(`python3 tools/check_signature.py --keystore android/keystore/ctrussian-release.p12`),
и подпись каждого собранного APK с `expected-cert-sha256.txt`.
