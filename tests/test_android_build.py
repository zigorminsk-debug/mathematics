"""APK identity/version tests and fail-closed checks of the signature gate."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_apk_update as update
import check_signature as signature


class ApkVersionTests(unittest.TestCase):
    def test_version_counter(self):
        self.assertEqual(261003, update.version_code("2026.10.3"))
        self.assertGreater(update.version_code("2026.11.0"), update.version_code("2026.10.99"))
        self.assertGreater(update.version_code("2027.1.0"), update.version_code("2026.12.99"))
        for bad in ("1.0.0", "2026.13.1", "2026.0.1", "2026.10.100", "2026.10.x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                update.version_code(bad)

    def test_badging(self):
        actual = update.parse_badging("package: name='by.ziv.ctmaths' versionCode='261003' versionName='2026.10.3' compileSdkVersion='34' compileSdkVersionCodename='14'\nother: value")
        self.assertEqual(update.PACKAGE, actual["name"])
        update.validate(actual, "2026.10.3", dict(name=update.PACKAGE, versionCode=2, versionName="2026.10.2"))
        for previous in (dict(name="by.ziv.ctmaths.debug", versionCode=1),
                         dict(name=update.PACKAGE, versionCode=261003),
                         dict(name=update.PACKAGE, versionCode=261004)):
            with self.assertRaises(ValueError):
                update.validate(actual, "2026.10.3", previous)
        for bad in (dict(actual, name="by.ziv.ctmaths.debug"),
                    dict(actual, versionCode=1), dict(actual, versionName="1.0.0")):
            with self.assertRaises(ValueError):
                update.validate(bad, "2026.10.3")

    def test_missing_metadata(self):
        with self.assertRaises(ValueError):
            update.parse_badging("error: no package")


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
        digest = signature.EXPECTED.read_text().strip()
        output = subprocess.CompletedProcess([], 0, f"Signer #1 certificate SHA-256 digest: {digest}", "")
        self.assertEqual(0, self.run_gate(output))

    def test_failed_verification_is_not_accepted_even_with_expected_digest(self):
        digest = signature.EXPECTED.read_text().strip()
        output = subprocess.CompletedProcess([], 1, f"Signer #1 certificate SHA-256 digest: {digest}", "DOES NOT VERIFY")
        self.assertEqual(1, self.run_gate(output))

    def test_changed_certificate(self):
        output = subprocess.CompletedProcess([], 0, "Signer #1 certificate SHA-256 digest: " + "a" * 64, "")
        self.assertEqual(1, self.run_gate(output))

    def test_required_check_cannot_skip_missing_apk(self):
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sys, "argv", ["check_signature.py", "--require", "--apk", str(Path(temp) / "missing.apk")]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, signature.main())
