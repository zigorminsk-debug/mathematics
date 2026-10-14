#!/usr/bin/env python3
"""Два предмета в одном репозитории: профили не пересекаются.

Общая машинерия релизов (``tools/release_plan.py``, ``tools/publish_release.py``,
``tools/sync_assets.py``) работает по профилю предмета из ``tools/subject.py``.
Тест фиксирует договор между предметами: у каждого своя семья тегов, пакет EXE,
каталог данных, очередь публикации, ключ подписи и имя APK. Если профили
начнут делить хотя бы одно из этих значений, обновление одного приложения
сможет увести пользователя другого (или подменить глобальный `latest`).

Профили читаются в отдельном процессе: ``CT_SUBJECT`` выбирает файл профиля,
и мы хотим видеть ровно то, что увидят инструменты в CI.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import subject  # noqa: E402  (активный профиль: CT_SUBJECT)

ROOT = Path(__file__).resolve().parents[1]

FIELDS = """
import json, sys
sys.path.insert(0, 'tools')
import subject as s
print(json.dumps({
    'subject': s.SUBJECT,
    'title': s.TITLE,
    'tag': s.TAG_PREFIX,
    'packages': [s.ANDROID_PACKAGE, s.ANDROID_DEBUG_PACKAGE],
    'binary': s.WINDOWS_BINARY,
    'data': s.WINDOWS_DATA_DIR,
    'edge': s.WINDOWS_EDGE_PROFILE,
    'lock': s.CONCURRENCY_LOCK,
    'keystore': s.KEYSTORE,
    'keystore_env': s.KEYSTORE_ENV,
    'cert': s.EXPECTED_CERT,
    'apk': s.APK_ASSET,
    'root': str(s.SUBJECT_ROOT),
    'content': sorted(s.CONTENT_FILES),
    'reference': s.REFERENCE_FILE,
    'installers': sorted(s.installers()),
    'build_jobs': list(s.BUILD_JOBS),
}, ensure_ascii=False))
"""

#: Разделяемые значения: у двух предметов они обязаны различаться.
EXCLUSIVE = ("subject", "tag", "binary", "data", "edge", "lock", "keystore",
             "keystore_env", "apk", "title", "packages", "installers")


def profile(name: str = "") -> dict:
    env = dict(os.environ)
    env.pop("CT_SUBJECT", None)
    if name:
        env["CT_SUBJECT"] = name
    result = subprocess.run([sys.executable, "-c", FIELDS], cwd=ROOT, env=env,
                            text=True, capture_output=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class Profiles(unittest.TestCase):

    def test_the_shared_suite_is_physics_scoped(self):
        """Общий набор тестов (`tests/`) описывает машинерию физики.

        Английские проверки живут в `english/tests/`, а изоляция предметов —
        здесь же, в отдельном процессе. Если запустить этот файл с
        `CT_SUBJECT=english`, тесты физики увидят чужой профиль и упадут
        загадочными assert'ами; поэтому падаем сразу и понятно.
        """
        self.assertEqual(
            subject.PROFILE_NAME, "physics",
            "общий tests/ рассчитан на профиль physics: запускайте его без "
            "CT_SUBJECT (например, `env -u CT_SUBJECT python3 -m unittest "
            "discover -s tests -p 'test_*.py'`), а английские проверки — "
            "`python3 english/tests/...` и CI-задание «CI (English)»")


    def test_default_profile_is_still_physics(self):
        """Историческое поведение: без CT_SUBJECT инструменты работают с физикой."""
        default = profile()
        self.assertEqual(default["subject"], "physics")
        self.assertEqual(Path(default["root"]), ROOT)
        self.assertEqual(default["tag"], "physics-v")
        self.assertEqual(default["apk"], "phyzics.apk")

    def test_english_profile_has_its_own_identity(self):
        english = profile("english")
        self.assertEqual(english["subject"], "english")
        self.assertEqual(english["packages"], ["by.ziv.ctenglish", "by.ziv.ctenglish.debug"])
        self.assertEqual(english["binary"], "CTEnglishTutor")
        self.assertEqual(english["tag"], "english-v")
        self.assertEqual(english["lock"], "ctenglish-release-pipeline")
        self.assertEqual(english["apk"], "engtutor.apk")
        self.assertEqual(english["edge"], "ctenglish-window")
        self.assertEqual(Path(english["root"]), ROOT / "english")
        self.assertEqual(sorted(english["installers"]),
                         ["CTEnglishTutor-amd64.exe", "CTEnglishTutor-arm64.exe", "engtutor.apk"])
        # справочник английского — «Правила», а не «Формулы»
        self.assertEqual(english["reference"], "rules.json")
        self.assertIn("rules.json", english["content"])
        self.assertNotIn("formulas.json", english["content"])

    def test_subjects_share_no_release_or_storage_identity(self):
        physics, english = profile("physics"), profile("english")
        for field in EXCLUSIVE:
            with self.subTest(field=field):
                self.assertNotEqual(physics[field], english[field],
                                    f"предметы делят {field!r}: {physics[field]!r}")

    def test_neither_subject_reuses_mathematics(self):
        for name in ("", "english"):
            current = profile(name)
            # `root` — это путь внутри репозитория, который сам называется
            # «mathematics»; проверяем идентичность, а не расположение дерева.
            text = json.dumps({key: value for key, value in current.items() if key != "root"},
                              ensure_ascii=False).lower()
            for forbidden in ("mathematics", "ctmaths", "ctmathstutor", "ctmaths-window"):
                with self.subTest(subject=current["subject"], forbidden=forbidden):
                    self.assertNotIn(forbidden, text)

    def test_keystores_and_fingerprints_live_in_their_own_tree(self):
        physics, english = profile("physics"), profile("english")
        self.assertEqual(Path(physics["keystore"]), Path("android/keystore/ctphysics-release.p12"))
        self.assertEqual(Path(english["keystore"]), Path("android/keystore/ctenglish-release.p12"))
        self.assertEqual(english["cert"], "android/keystore/expected-cert-sha256.txt")

    def test_content_files_stay_subject_specific(self):
        physics, english = profile("physics"), profile("english")
        shared = set(physics["content"]) & set(english["content"])
        self.assertEqual(shared, {"bank.json", "analogous.json", "topics.json",
                                  "ui_strings.json", "mistakes.json", "answer_vectors.json"})


if __name__ == "__main__":
    unittest.main()


class BuildJobNames(unittest.TestCase):
    """Имена заданий CI у предмета и в workflow совпадают.

    Публикатор останавливает релиз, если задание из профиля не найдено среди
    успешных job'ов запуска (``tools/publish_release.py``). Опечатка в имени —
    это упавшая публикация после успешной сборки, поэтому сверяем здесь.
    """

    WORKFLOWS = {"physics": "ci.yml", "english": "english-ci.yml"}

    def test_every_expected_job_exists_in_the_subject_workflow(self):
        for name, workflow in self.WORKFLOWS.items():
            with self.subTest(subject=name):
                data = profile(name)
                text = (ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
                for job in data["build_jobs"]:
                    self.assertIn(f"name: {job}", text,
                                  f"{workflow}: нет задания «{job}» из профиля {name}")
                self.assertNotIn("name: Publish", "\n".join(data["build_jobs"]))

    def test_subjects_do_not_share_job_names_by_accident(self):
        physics, english = profile("physics"), profile("english")
        # у английского контент-джоб назван иначе, иначе профиль не отличить
        self.assertNotEqual(physics["build_jobs"][0], english["build_jobs"][0])
        for name in ("physics", "english"):
            self.assertGreaterEqual(len(profile(name)["build_jobs"]), 3)
