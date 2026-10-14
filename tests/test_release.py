"""Контракт выпуска физики: отдельный канал, отдельные файлы, отдельный пакет.

Физика живёт в том же репозитории, что и математика, поэтому главное здесь —
доказать, что выпуск физики **не может** задеть математику: свой префикс тега,
``make_latest=false``, свой APK и свои EXE, свой канал обновления. Если этот
тест падает, публикацию запускать нельзя.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_apk_update  # noqa: E402
import publish_release  # noqa: E402
import release_plan  # noqa: E402
import subject  # noqa: E402

REPO = "zigorminsk-debug/mathematics"


class PhysicsIdentity(unittest.TestCase):

    def test_names_do_not_overlap_with_mathematics(self):
        self.assertEqual(subject.SUBJECT, "physics")
        self.assertEqual(subject.TAG_PREFIX, "physics-v")
        self.assertEqual(subject.ANDROID_PACKAGE, "by.ziv.ctphysics")
        self.assertEqual(subject.ANDROID_DEBUG_PACKAGE, "by.ziv.ctphysics.debug")
        self.assertEqual(subject.WINDOWS_BINARY, "CTPhysicsTutor")
        self.assertTrue(subject.WINDOWS_DATA_DIR.endswith("CTPhysicsTutor"))
        self.assertIn("%APPDATA%", subject.WINDOWS_DATA_DIR)
        self.assertEqual(subject.WINDOWS_EDGE_PROFILE, "ctphysics-window")
        self.assertEqual(check_apk_update.PACKAGE, subject.ANDROID_PACKAGE)
        for value in (subject.ANDROID_PACKAGE, subject.WINDOWS_BINARY,
                      subject.WINDOWS_EDGE_PROFILE, subject.APK_ASSET,
                      subject.GRADLE_APK, subject.KEYSTORE):
            self.assertNotIn("ctmaths", value.lower())
            self.assertNotIn("ctmathstutor", value.lower())

    def test_apk_is_published_under_the_requested_name(self):
        """Пользователь просил «apk назови phyzics» — так он и называется."""
        self.assertEqual(subject.APK_ASSET, "phyzics.apk")
        self.assertEqual(subject.GRADLE_APK,
                         "android/app/build/outputs/apk/release/app-release.apk")
        self.assertTrue(subject.GRADLE_APK.endswith("app-release.apk"))
        self.assertIn(subject.APK_ASSET, subject.installers())
        self.assertEqual(subject.installers(),
                         {"phyzics.apk", "CTPhysicsTutor-amd64.exe",
                          "CTPhysicsTutor-arm64.exe"})

    def test_math_tags_are_not_mistaken_for_physics(self):
        self.assertIsNone(subject.release_version("v2026.10.8"))
        self.assertIsNone(subject.release_version("v2026.10.7"))
        self.assertEqual(subject.release_version("physics-v2026.10.1"), "2026.10.1")
        self.assertEqual(subject.tag("2026.10.1"), "physics-v2026.10.1")

    def test_update_channel_is_subject_scoped(self):
        url = subject.content_base_url(REPO, "2026.10.1")
        self.assertEqual(
            url,
            "https://github.com/zigorminsk-debug/mathematics"
            "/releases/download/physics-v2026.10.1")
        self.assertNotIn("/latest/", url)
        identity = subject.manifest_identity()
        self.assertEqual(identity["subject"], "physics")
        self.assertEqual(identity["package"], "by.ziv.ctphysics")
        self.assertEqual(identity["tagPrefix"], "physics-v")

    def test_release_inventory(self):
        self.assertEqual(len(release_plan.RELEASE_FILES), 13)
        self.assertEqual(len(release_plan.CONTENT_FILES), 7)
        self.assertEqual(release_plan.RELEASE_FILES, release_plan.CONTENT_FILES | {
            "version.json", "release-info.json", "SHA256SUMS.txt",
            "phyzics.apk", "CTPhysicsTutor-amd64.exe", "CTPhysicsTutor-arm64.exe"})
        self.assertEqual(release_plan.INSTALLERS, subject.installers())


class ReleasePolicy(unittest.TestCase):
    """Чистая политика нумерации — то, что нельзя проверять «на живом» релизе."""

    def releases(self, *entries):
        return list(entries)

    def release(self, tag, *, draft=False, prerelease=False, commit="other",
                assets=None, sha_field="_source_sha"):
        entry = {"tag_name": tag, "draft": draft, "prerelease": prerelease,
                 "target_commitish": commit, "html_url": "https://example.invalid/r/" + tag,
                 "assets": [{"name": name} for name in (assets or [])]}
        if sha_field:
            entry[sha_field] = commit
        return entry

    def test_first_release_starts_from_the_repository_floor(self):
        plan = release_plan.choose_version("2026.10.1", [], "a" * 40, date(2026, 10, 14))
        self.assertEqual(plan["version"], "2026.10.1")
        self.assertEqual(plan["tag"], "physics-v2026.10.1")
        self.assertTrue(plan["publish"])
        self.assertFalse(plan["already_published"])
        self.assertEqual(plan["previous_tag"], "")

    def test_new_month_raises_the_floor(self):
        plan = release_plan.choose_version("2026.10.1", [], "a" * 40, date(2026, 12, 3))
        self.assertEqual(plan["version"], "2026.12.0")

    def test_previous_physics_release_moves_the_version_forward(self):
        previous = self.release("physics-v2026.10.1", commit="b" * 40,
                                assets=release_plan.RELEASE_FILES)
        plan = release_plan.choose_version("2026.10.1", [previous], "a" * 40,
                                           date(2026, 10, 14))
        self.assertEqual(plan["version"], "2026.10.2")
        self.assertEqual(plan["previous_tag"], "physics-v2026.10.1")
        self.assertEqual(plan["previous_version"], "2026.10.1")

    def test_mathematics_releases_are_invisible_to_the_physics_counter(self):
        maths = self.release("v2026.10.8", commit="c" * 40, assets=release_plan.RELEASE_FILES)
        plan = release_plan.choose_version("2026.10.1", [maths], "a" * 40,
                                           date(2026, 10, 14))
        self.assertEqual(plan["version"], "2026.10.1")
        self.assertEqual(plan["previous_tag"], "")

    def test_republishing_the_same_commit_is_idempotent(self):
        commit = "d" * 40
        published = self.release("physics-v2026.10.1", commit=commit,
                                 assets=release_plan.RELEASE_FILES)
        plan = release_plan.choose_version("2026.10.1", [published], commit,
                                           date(2026, 10, 14))
        self.assertTrue(plan["already_published"])
        self.assertEqual(plan["version"], "2026.10.1")
        self.assertEqual(plan["release_url"], published["html_url"])

    def test_incomplete_published_assets_are_refused(self):
        commit = "d" * 40
        published = self.release("physics-v2026.10.1", commit=commit,
                                 assets=release_plan.RELEASE_FILES - {"phyzics.apk"})
        with self.assertRaises(ValueError):
            release_plan.choose_version("2026.10.1", [published], commit,
                                        date(2026, 10, 14))

    def test_requested_tag_cannot_be_rewritten(self):
        with self.assertRaises(ValueError):
            release_plan.choose_version("2026.10.1", [], "a" * 40, date(2026, 10, 14),
                                        requested_tag="physics-v2026.9.0")

    def test_draft_of_another_commit_does_not_capture_the_version(self):
        other = self.release("physics-v2026.10.1", draft=True, commit="e" * 40)
        plan = release_plan.choose_version("2026.10.1", [other], "a" * 40,
                                           date(2026, 10, 14))
        self.assertFalse(plan["already_published"])
        self.assertNotEqual(plan["tag"], "physics-v2026.10.1")

    def test_version_numbering(self):
        self.assertEqual(release_plan.canonical("2026.10.01"), "2026.10.1")
        self.assertEqual(release_plan.canonical("2026.9.0"), "2026.9.0")
        self.assertEqual(release_plan.next_version("2026.10.98"), "2026.10.99")
        self.assertEqual(release_plan.next_version("2026.10.99"), "2026.11.0")
        self.assertEqual(release_plan.next_version("2026.12.99"), "2027.1.0")


class PublisherSource(unittest.TestCase):
    """Публикатор обязан оставаться «слепым» к математике."""

    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "tools" / "publish_release.py").read_text(encoding="utf-8")

    def test_publication_never_touches_the_global_latest(self):
        """Ни одна исполняемая строка публикатора не строит URL общего latest-фида.

        Упоминания ``/releases/latest/download`` законны только там, где это
        документация: в docstring модуля и в текст релиза («не используется»).
        """
        source = self.source
        module_doc_end = source.index('"""', source.index('"""') + 3) + 3
        notes_start = source.index("def release_notes(")
        notes_end = source.index("def publish(")
        code = source[module_doc_end:notes_start] + source[notes_end:]
        self.assertNotIn("releases/latest/download", code,
                         "client banks must be fetched from the version-specific tag")
        self.assertIn("make_latest", source, "make_latest flag must be set explicitly")
        self.assertIn('"false"', source, "the release must not become repository latest")
        self.assertIn("content_base_url(", code,
                      "URLs come from the subject-scoped resolver")

    def test_publisher_refuses_when_the_repository_latest_moved(self):
        self.assertIn("releases/latest", self.source)
        self.assertIn("ValueError", self.source)

    def test_inventory_uses_the_subject_asset_names(self):
        self.assertIn("subject.APK_ASSET", self.source, "APK is staged under its subject name")
        self.assertIn("INSTALLERS", self.source, "installers come from the shared inventory")
        self.assertIn("CONTENT_FILES", self.source, "content files come from the shared inventory")

    def test_release_title_is_the_physics_one(self):
        self.assertIn("subject.TITLE", self.source, "release name must use the physics title")
        self.assertNotIn("CT Maths Tutor", self.source)
        self.assertNotIn("CTMaths", self.source)

    def test_notes_mention_the_subject_and_the_disclosure(self):
        notes = publish_release.release_notes("2026.10.1", "a" * 40,
                                              "https://example.invalid/run", 261001)
        self.assertIn("2026.10.1", notes)
        self.assertIn(subject.ANDROID_PACKAGE, notes)
        self.assertIn(subject.APK_ASSET, notes)
        self.assertNotIn("{subject.", notes)

    def test_run_validation_requires_every_build_job(self):
        jobs = [{"name": name, "conclusion": "success", "id": index + 1}
                for index, name in enumerate(release_plan.BUILD_JOBS)]
        publish_release.validate_run(
            {"event": "push", "head_sha": "a" * 40,
             "repository": {"full_name": REPO}},
            jobs, REPO, "a" * 40, "refs/heads/arena/f7b88593-mathematics", "")
        broken = [dict(job) for job in jobs]
        broken[2]["conclusion"] = "failure"
        with self.assertRaises(ValueError):
            publish_release.validate_run({"event": "push", "head_sha": "a" * 40,
                                          "repository": {"full_name": REPO}},
                                         broken, REPO, "a" * 40,
                                         "refs/heads/arena/f7b88593-mathematics", "")
        # публикация из pull request запрещена
        with self.assertRaises(ValueError):
            publish_release.validate_run({"event": "pull_request", "head_sha": "a" * 40,
                                          "repository": {"full_name": REPO}},
                                         jobs, REPO, "a" * 40, "refs/heads/main", "")


class WorkflowGuards(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.workflows = {
            name: (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
            for name in ("release.yml", "ci.yml", "publish.yml")
        }

    def test_no_mathematics_names_left_in_the_physics_pipeline(self):
        for name, text in self.workflows.items():
            lowered = text.lower()
            self.assertNotIn("ctmaths", lowered, name)
            self.assertNotIn("ctmathstutor", lowered, name)
            self.assertNotIn("ctmaths-window", lowered, name)

    def test_release_workflow_builds_the_physics_binaries(self):
        release = self.workflows["release.yml"]
        # release.yml вызывает общий ci.yml (без пересборки «своими руками»)
        self.assertIn("./.github/workflows/ci.yml", release)
        self.assertIn("physics-v", release)
        ci = self.workflows["ci.yml"]
        self.assertIn("CTPhysicsTutor-amd64.exe", ci)
        self.assertIn("CTPhysicsTutor-arm64.exe", ci)

    def test_publish_workflow_renames_the_apk(self):
        publish = self.workflows["publish.yml"]
        # Имя файла берётся из профиля предмета, а не из захардкоженной строки:
        # у физики это phyzics.apk, английский тренажёр переименует свой APK сам.
        self.assertIn("mv staging/android/app-release.apk", publish)
        self.assertIn("subject.APK_ASSET", publish)
        self.assertIn("make_latest=false", publish)
        # общий публикатор вызывается с явным предметом и по умолчанию физикой
        self.assertIn("default: 'physics'", publish)

    def test_publish_workflow_keeps_the_physics_default(self):
        publish = self.workflows["publish.yml"]
        self.assertIn("CT_SUBJECT: ${{ inputs.subject }}", publish)
        self.assertEqual(subject.APK_ASSET, "phyzics.apk")

    def test_ci_downloads_the_previous_physics_apk_only(self):
        ci = self.workflows["ci.yml"]
        self.assertIn("phyzics.apk", ci)
        self.assertNotIn("--pattern app-release.apk", ci)


class Keystore(unittest.TestCase):

    def test_permanent_key_fingerprint_is_pinned(self):
        fingerprint = (ROOT / subject.EXPECTED_CERT).read_text(encoding="utf-8").strip()
        parts = fingerprint.split(":")
        self.assertEqual(len(parts), 32)
        for part in parts:
            self.assertRegex(part, r"^[0-9A-F]{2}$")
        self.assertNotIn("B2:BD", fingerprint, "математический сертификат не подходит физике")

    def test_keystore_properties_match_the_subject(self):
        properties = (ROOT / "android" / "keystore" / "keystore.properties").read_text(
            encoding="utf-8")
        values = dict(line.split("=", 1) for line in properties.splitlines() if "=" in line)
        self.assertEqual(values["keyAlias"], "ctphysics")
        self.assertEqual(values["storeType"], "PKCS12")
        self.assertTrue(values["storeFile"].endswith("ctphysics-release.p12"))
        self.assertEqual(pathlib.Path(values["storeFile"]).name,
                         pathlib.Path(subject.KEYSTORE).name)
        self.assertTrue((ROOT / subject.KEYSTORE).exists())
        self.assertEqual(subject.KEYSTORE_ENV, "CTPHYSICS_KEYSTORE_FILE")


if __name__ == "__main__":
    unittest.main()
