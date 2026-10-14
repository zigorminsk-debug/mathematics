#!/usr/bin/env python3
"""tools/subject_english.py — постоянная идентичность предмета «Английский язык».

Самостоятельный тренажёр «Репетитор ЦТ: Английский язык» живёт в этом же
репозитории рядом с математикой и физикой, но у него **своя** личность: subject,
семья тегов ``english-vYYYY.M.P``, Android-пакет, имена EXE, каталог данных и
профиль браузера Windows, постоянный ключ подписи и отдельная очередь публикации.
Общие инструменты выбирают этот профиль через ``CT_SUBJECT=english``.

Правила изоляции те же, что у физики (см. ``docs/subjects/README.md``):

* релизы публикуются с ``make_latest=false`` — общий ``releases/latest``
  репозитория продолжает отдавать математику;
* клиент обновлений читает только теги своей семьи и никогда глобальный
  ``/releases/latest/download``;
* ключ подписи фиксируется до первого APK и не меняется никогда, иначе
  обновление «поверх» перестанет устанавливаться;
* готовый предметный банк помечается ``subject=english``/``package=by.ziv.ctenglish``,
  и чужой банк (математический или физический) отвергается.

Предметное дерево — ``english/`` (как отдельная папка, чтобы позже её можно было
вынести в собственную ветку/репозиторий без переноса чужого кода).
"""

from __future__ import annotations

from pathlib import Path
import re

#: Идентификатор предмета в manifest/audit; клиент отвергает чужой subject.
SUBJECT = "english"

#: Человеческое название приложения (Android label, Windows title, Release).
TITLE = {"ru": "Репетитор ЦТ: Английский язык", "en": "CT English Tutor"}

#: Семья тегов и версий: `english-vYYYY.M.P`, никогда не общая `vYYYY.M.P`.
TAG_PREFIX = "english-v"

#: Android: release и debug пакеты ставятся рядом и не считаются обновлением.
ANDROID_PACKAGE = "by.ziv.ctenglish"
ANDROID_DEBUG_PACKAGE = "by.ziv.ctenglish.debug"

#: Windows: имена EXE совпадают с тем, что публикует CI и ожидает пользователь.
WINDOWS_BINARY = "CTEnglishTutor"
WINDOWS_DATA_DIR = "%APPDATA%\\CTEnglishTutor"
WINDOWS_EDGE_PROFILE = "ctenglish-window"

#: Отдельная очередь публикации: английский не блокирует физику и математику.
CONCURRENCY_LOCK = "ctenglish-release-pipeline"

#: Подпись: собственный постоянный ключ английского, зафиксированный до первого APK.
KEYSTORE = "android/keystore/ctenglish-release.p12"
KEYSTORE_ENV = "CTENGLISH_KEYSTORE_FILE"
EXPECTED_CERT = "android/keystore/expected-cert-sha256.txt"

#: Канал обновления контента: только теги этой семьи, никогда глобальный latest.
RELEASES_PAGE = 100

#: Имя файла APK в релизе. Внутренняя сборка Gradle остаётся app-release.apk,
#: а переименование делает publish-шаг CI, чтобы имя в релизе было ровно одно.
APK_ASSET = "engtutor.apk"

#: Где Gradle кладёт подписанный release-APK (относительно SUBJECT_ROOT).
GRADLE_APK = "android/app/build/outputs/apk/release/app-release.apk"


def installers() -> set[str]:
    """Имена публикуемых native-файлов, включая release APK."""
    return {APK_ASSET,
            f"{WINDOWS_BINARY}-amd64.exe",
            f"{WINDOWS_BINARY}-arm64.exe"}


def tag(version: str) -> str:
    return TAG_PREFIX + version


def release_version(tag_name: str) -> str | None:
    """Версия из тега этой семьи; чужой тег (математика/физика) → None."""
    if not isinstance(tag_name, str) or not tag_name.startswith(TAG_PREFIX):
        return None
    candidate = tag_name[len(TAG_PREFIX):]
    if not re.fullmatch(r"20\d{2}\.\d{1,2}\.\d{1,2}", candidate):
        return None
    return candidate


def content_base_url(repo: str, version: str) -> str:
    """Immutable URL конкретного выпуска — у английского нет `/latest/download`."""
    return f"https://github.com/{repo}/releases/download/{tag(version)}"


def manifest_identity() -> dict:
    """Поля manifest/audit, по которым клиент отличает английский от соседей."""
    return {"subject": SUBJECT, "package": ANDROID_PACKAGE,
            "app": WINDOWS_BINARY, "tagPrefix": TAG_PREFIX}


#: ----------------------------------------------------------------------------
#: Пути предметного дерева и цели синхронизации (см. tools/sync_assets.py).
#: ----------------------------------------------------------------------------

#: Корень предметного дерева: `english/` рядом с математическим корнем.
SUBJECT_ROOT = Path(__file__).resolve().parents[1] / "english"

#: Файлы предметного контента в ``dist/content`` (``version.json`` строится отдельно).
#: Английский не «формулы», а «правила»: файл справки называется ``rules.json``.
CONTENT_FILES = {"bank.json", "analogous.json", "topics.json", "rules.json",
                 "ui_strings.json", "mistakes.json", "answer_vectors.json"}

#: Название файла и подпись справочника — «Правила», не «Формулы».
REFERENCE_FILE = "rules.json"
REFERENCE_LABEL = {"ru": "Правила", "en": "Rules"}

#: Куда ``tools/sync_assets.py`` раскладывает ``webapp/`` и ``dist/content/``.
SYNC_TARGETS = (
    ("windows", SUBJECT_ROOT / "windows" / "web"),
    ("android", SUBJECT_ROOT / "android" / "app" / "src" / "main" / "assets" / "webapp"),
)

#: Копии общих банков и векторов для нативных unit-тестов Android.
ANDROID_TEST_RESOURCES = SUBJECT_ROOT / "android" / "app" / "src" / "test" / "resources"

#: Дополнительные файлы синхронизации: пары (источник, назначение).
SYNC_EXTRA = (
    (SUBJECT_ROOT / "dist" / "content" / "answer_vectors.json",
     ANDROID_TEST_RESOURCES / "answer_vectors.json"),
    (SUBJECT_ROOT / "dist" / "content" / "bank.json",
     ANDROID_TEST_RESOURCES / "bank.json"),
    (SUBJECT_ROOT / "dist" / "content" / "analogous.json",
     ANDROID_TEST_RESOURCES / "analogous.json"),
)
