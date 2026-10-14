"""APK identity/version, permanent subject certificate and Android project identity."""
import contextlib
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_apk_update as update  # noqa: E402
import check_signature as signature  # noqa: E402
import subject  # noqa: E402

MATH_CERT = "B2:BD:B4:D1:26:B8:88:C7:D8:AF:50:80:F6:7E:CF:E1:E4:3F:EB:F2:8E:5D:1A:E6:61:D6:D7:AE:70:C5:14:65"
RUSSIAN_CERT = "DE:65:1A:CC:E1:DB:76:9B:DC:A8:DB:EB:04:5C:94:9F:39:7F:85:7A:E6:DB:12:EE:D1:32:38:A0:83:B6:6A:3D"


class ApkVersionTests(unittest.TestCase):
    def test_version_counter(self):
        self.assertEqual(261001, update.version_code("2026.10.1"))
        self.assertGreater(update.version_code("2026.11.0"), update.version_code("2026.10.99"))
        self.assertGreater(update.version_code("2027.1.0"), update.version_code("2026.12.99"))
        for bad in ("1.0.0", "2026.13.1", "2026.0.1", "2026.10.100", "2026.10.x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                update.version_code(bad)

    def test_package_is_the_subject_package(self):
        self.assertEqual("by.ziv.ctrussian", update.PACKAGE)
        actual = update.parse_badging("package: name='by.ziv.ctrussian' versionCode='261001' versionName='2026.10.1' "
                                      "compileSdkVersion='34'\nother: value")
        update.validate(actual, "2026.10.1", dict(name=update.PACKAGE, versionCode=261000, versionName="2026.10.0"))
        for previous in (dict(name="by.ziv.ctmaths", versionCode=1), dict(name="by.ziv.ctrussian.debug", versionCode=1),
                         dict(name=update.PACKAGE, versionCode=261001), dict(name=update.PACKAGE, versionCode=261002)):
            with self.subTest(previous=previous), self.assertRaises(ValueError):
                update.validate(actual, "2026.10.1", previous)
        for bad in (dict(actual, name="by.ziv.ctmaths"), dict(actual, name="by.ziv.ctrussian.debug"),
                    dict(actual, versionCode=1), dict(actual, versionName="1.0.0")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                update.validate(bad, "2026.10.1")

    def test_missing_metadata(self):
        with self.assertRaises(ValueError):
            update.parse_badging("error: no package")


class SubjectCertificateTests(unittest.TestCase):
    def test_own_permanent_certificate_is_pinned_and_not_the_math_key(self):
        pinned = subject.CERTIFICATE_FILE.read_text(encoding="utf-8").strip()
        self.assertEqual(RUSSIAN_CERT, pinned)
        self.assertNotEqual(signature.normalize(MATH_CERT), signature.normalize(pinned))
        self.assertTrue(subject.KEYSTORE.is_file())
        self.assertFalse((ROOT / "android/keystore/ctmaths-release.p12").exists(), "the math key must not sign this app")
        properties = (ROOT / "android/keystore/keystore.properties").read_text(encoding="utf-8")
        self.assertIn("storeFile=ctrussian-release.p12", properties)
        self.assertIn("keyAlias=ctrussian", properties)

    def test_keystore_matches_the_pin(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = signature.check_keystore(subject.CERTIFICATE_FILE, subject.KEYSTORE, "ctrussian2026", required=True)
        self.assertEqual(0, code)


class SignatureGateTests(unittest.TestCase):
    def run_gate(self, result):
        with tempfile.TemporaryDirectory() as temp:
            apk = Path(temp) / "test.apk"
            apk.write_bytes(b"fake APK - subprocess is mocked")
            with patch.object(sys, "argv", ["check_signature.py", "--require", "--apk", str(apk)]), \
                 patch.object(signature, "find_apksigner", return_value="apksigner"), \
                 patch.object(signature.subprocess, "run", return_value=result), \
                 contextlib.redirect_stdout(io.StringIO()):
                return signature.main()

    def test_verified_permanent_certificate(self):
        output = subprocess.CompletedProcess([], 0, f"Signer #1 certificate SHA-256 digest: {RUSSIAN_CERT}", "")
        self.assertEqual(0, self.run_gate(output))

    def test_math_certificate_is_rejected(self):
        output = subprocess.CompletedProcess([], 0, f"Signer #1 certificate SHA-256 digest: {MATH_CERT}", "")
        self.assertEqual(1, self.run_gate(output))

    def test_failed_verification_is_not_accepted_even_with_expected_digest(self):
        output = subprocess.CompletedProcess([], 1, f"Signer #1 certificate SHA-256 digest: {RUSSIAN_CERT}", "DOES NOT VERIFY")
        self.assertEqual(1, self.run_gate(output))

    def test_required_check_cannot_skip_missing_apk(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sys, "argv", ["check_signature.py", "--require", "--apk", str(Path(temp) / "missing.apk")]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, signature.main())


class ProjectIdentityTests(unittest.TestCase):
    def test_gradle_manifest_and_sources_use_the_subject_package(self):
        gradle = (ROOT / "android/app/build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn('namespace = "by.ziv.ctrussian"', gradle)
        self.assertIn('applicationId = "by.ziv.ctrussian"', gradle)
        self.assertIn('applicationIdSuffix = ".debug"', gradle)
        self.assertIn('rootProject.name = "CTRussianTutor"', (ROOT / "android/settings.gradle.kts").read_text(encoding="utf-8"))
        sources = list((ROOT / "android/app/src").rglob("*.kt"))
        self.assertTrue(sources)
        for path in sources:
            text = path.read_text(encoding="utf-8")
            self.assertIn("package by.ziv.ctrussian", text, path)
            # tests may name the mathematics package as a NEGATIVE fixture; shipped code may not
            if "/src/main/" in path.as_posix():
                self.assertNotIn("ctmaths", text.lower(), path)
        for path in (ROOT / "android/app/src").rglob("*.xml"):
            self.assertNotIn("CTMaths", path.read_text(encoding="utf-8"), path)

    def test_generated_strings_name_the_russian_tutor(self):
        values = (ROOT / "android/app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
        russian = (ROOT / "android/app/src/main/res/values-ru/strings.xml").read_text(encoding="utf-8")
        self.assertIn('<string name="app_name">CT Russian Tutor</string>', values)
        self.assertIn('<string name="app_name">Репетитор ЦТ: Русский язык</string>', russian)
        for text in (values, russian):
            for match in re.finditer(r'<string name="([a-z_]+)">(.*?)</string>', text):
                if not match.group(1).endswith("_fmt"):
                    self.assertNotRegex(match.group(2), r"(?<!%)%(?!%)", match.group(1))


if __name__ == "__main__":
    unittest.main()
