#!/usr/bin/env python3
"""tools/subject_physics.py — постоянная идентичность предмета (физика).

Один источник правды для контента, приложений, релизов и каналов обновления.
Это ветка **физики**: другой subject, другая семья тегов, другой Android-пакет,
другие каталоги данных и браузерный профиль Windows и собственный ключ подписи.
Математика остаётся в своей ветке/релизах; физика публикуется как «не latest»
(`make_latest=false`) и никогда не читает глобальный `/releases/latest/download`.

Любой инструмент, который раньше был жёстко привязан к `ctmaths`/`vYYYY.M.P`,
импортирует значения отсюда. Тесты (`tests/test_release.py`,
`tests/test_isolation.py`) проверяют, что строка `mathematics` не утекает в
предметные константы, а группы concurrency не пересекаются.
"""

from __future__ import annotations

from pathlib import Path
import re

#: Идентификатор предмета в manifest/audit; клиент отвергает чужой subject.
SUBJECT = "physics"

#: Человеческое название приложения (Android label, Windows title, Release).
TITLE = {"ru": "Репетитор ЦТ: Физика", "en": "CT Physics Tutor"}

#: Семья тегов и версий: `physics-vYYYY.M.P`, никогда не общая `vYYYY.M.P`.
TAG_PREFIX = "physics-v"

#: Android: release и debug пакеты ставятся рядом и не считаются обновлением.
ANDROID_PACKAGE = "by.ziv.ctphysics"
ANDROID_DEBUG_PACKAGE = "by.ziv.ctphysics.debug"

#: Windows: имена EXE совпадают с тем, что публикует CI и ожидает пользователь.
WINDOWS_BINARY = "CTPhysicsTutor"
WINDOWS_DATA_DIR = "%APPDATA%\\CTPhysicsTutor"
WINDOWS_EDGE_PROFILE = "ctphysics-window"

#: Отдельная очередь публикации: физика не блокирует математический pipeline.
CONCURRENCY_LOCK = "ctphysics-release-pipeline"

#: Подпись: собственный постоянный ключ физики, зафиксированный до первого APK.
KEYSTORE = "android/keystore/ctphysics-release.p12"
KEYSTORE_ENV = "CTPHYSICS_KEYSTORE_FILE"
EXPECTED_CERT = "android/keystore/expected-cert-sha256.txt"

#: Имена заданий physics-CI (`ci.yml`): публикатор сверяет их с
#: фактическим запуском (см. tools/publish_release.py).
BUILD_JOBS = ("Content & web (verify, parity, assets)",
              "Windows app (Go)", "Android app (APK)")

#: Канал обновления контента: только теги этой семьи, никогда глобальный latest.
RELEASES_PAGE = 100

#: Имя файла APK в релизе. Пользователь назвал его «phyzics»; внутренняя сборка
#: Gradle остаётся app-release.apk, а переименование делает publish-шаг CI, чтобы
#: имя в релизе было ровно одно и не зависело от настроек Gradle.
APK_ASSET = "phyzics.apk"

#: Где Gradle кладёт подписанный release-APK (путь для проверок CI).
GRADLE_APK = "android/app/build/outputs/apk/release/app-release.apk"


def installers() -> set[str]:
    """Имена публикуемых native-файлов, включая release APK."""
    return {APK_ASSET,
            f"{WINDOWS_BINARY}-amd64.exe",
            f"{WINDOWS_BINARY}-arm64.exe"}


def tag(version: str) -> str:
    return TAG_PREFIX + version


def release_version(tag_name: str) -> str | None:
    """Версия из тега этой семьи; чужой тег (например математический `v…`) → None."""
    if not isinstance(tag_name, str) or not tag_name.startswith(TAG_PREFIX):
        return None
    candidate = tag_name[len(TAG_PREFIX):]
    if not re.fullmatch(r"20\d{2}\.\d{1,2}\.\d{1,2}", candidate):
        return None
    return candidate


def content_base_url(repo: str, version: str) -> str:
    """Immutable URL конкретного выпуска — у физики нет `/latest/download`."""
    return f"https://github.com/{repo}/releases/download/{tag(version)}"


def manifest_identity() -> dict:
    """Поля manifest/audit, по которым клиент отличает физику от математики."""
    return {"subject": SUBJECT, "package": ANDROID_PACKAGE,
            "app": WINDOWS_BINARY, "tagPrefix": TAG_PREFIX}


#: ----------------------------------------------------------------------------
#: Пути предметного дерева. У физики предметное дерево — корень репозитория
#: (историческое расположение), у английского тренажёра — каталог ``english/``.
#: Общие инструменты (release_plan, publish_release, sync_assets) берут отсюда
#: ``VERSION``, ``webapp/``, ``dist/`` и цели синхронизации, поэтому второй
#: предмет переиспользует ту же проверенную машинерию релизов.
#: ----------------------------------------------------------------------------

#: Корень предметного дерева.
SUBJECT_ROOT = Path(__file__).resolve().parents[1]

#: Файлы предметного контента в ``dist/content`` (``version.json`` строится отдельно).
CONTENT_FILES = {"bank.json", "analogous.json", "topics.json", "formulas.json",
                 "ui_strings.json", "mistakes.json", "answer_vectors.json"}

#: Название файла и подпись справочника — у физики это «Формулы».
REFERENCE_FILE = "formulas.json"
REFERENCE_LABEL = {"ru": "Формулы", "en": "Formulas"}

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
    (SUBJECT_ROOT / "tests" / "unit_vectors.json",
     ANDROID_TEST_RESOURCES / "unit_vectors.json"),
)
