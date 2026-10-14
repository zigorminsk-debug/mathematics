# Ключ подписи Android / Android signing key

```
ctmaths-release.p12        постоянный ключ проекта (PKCS#12, срок действия до 2056 года)
keystore.properties        пароль и псевдоним (используется сборкой и CI)
expected-cert-sha256.txt   эталонный отпечаток сертификата
```

```
Owner:   CN=CT Maths Tutor, OU=Android release, O=Zakharevich Igor, C=BY, L=Minsk
SHA-256: B2:BD:B4:D1:26:B8:88:C7:D8:AF:50:80:F6:7E:CF:E1:E4:3F:EB:F2:8E:5D:1A:E6:61:D6:D7:AE:70:C5:14:65
```

**Почему ключ лежит в репозитории.** Android ставит новый APK поверх старой версии
только при совпадении подписи. Пока ключ один и тот же, каждое обновление
устанавливается «поверх» без удаления приложения и без потери статистики ученика.
CI сверяет собранный APK с `expected-cert-sha256.txt`
(`python3 tools/check_signature.py`) и падает, если подпись изменилась.

**Перед публикацией в Google Play** (или если ключ нужно сменить) положите свой
`.p12` рядом, обновите `keystore.properties` и `expected-cert-sha256.txt` **или**
задайте секреты репозитория `ANDROID_KEYSTORE_FILE`, `ANDROID_KEYSTORE_PASSWORD`,
`ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD` — `android/app/build.gradle.kts` предпочтёт
переменные окружения. В таком случае файл ключа храните в секретах (base64), а не
в репозитории.
