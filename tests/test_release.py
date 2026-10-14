"""Release policy, fail-closed publication and reusable workflow contracts.

No network, native SDK or real GitHub release mutations in these tests.
Native APK identity/certificate/update tests are still required by Android CI.
"""
import argparse
import contextlib
import io
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import release_plan as plan
import publish_release as pub

SHA = "a" * 40
REPO = "zigorminsk-debug/mathematics"
TODAY = date(2026, 10, 14)


def release(version, sha="b" * 40, *, draft=False, prerelease=False):
    return {"id": 10, "tag_name": "v" + version, "target_commitish": sha,
            "draft": draft, "prerelease": prerelease, "html_url": f"https://github.com/{REPO}/releases/tag/v{version}",
            "assets": [{"name": name} for name in plan.RELEASE_FILES]}


def jobs(prefix=""):
    return [{"name": prefix + name, "conclusion": "success", "id": index}
            for index, name in enumerate(plan.BUILD_JOBS, 1)]


def make_staging(root, version="2026.10.5"):
    staging = root / "staging"
    for name in ("content", "windows", "android"):
        (staging / name).mkdir(parents=True)
    for name in plan.CONTENT_FILES:
        (staging / "content" / name).write_text('{}\n', encoding="utf-8")
    files = {name: pub.metadata(staging / "content" / name) for name in sorted(plan.CONTENT_FILES)}
    pub.write_json(staging / "content" / "version.json", {"contentVersion": version, "files": files})
    for name in plan.INSTALLERS:
        (staging / ("android" if name.endswith(".apk") else "windows") / name).write_bytes(b"fake native artifact; CI gates mocked")
    return staging


class ReleasePlanTests(unittest.TestCase):
    def test_initial_release_respects_source_floor(self):
        result = plan.choose_version("2026.10.5", [release("2026.10.2")], SHA, TODAY)
        self.assertEqual("2026.10.5", result["version"])
        self.assertEqual("v2026.10.2", result["previous_tag"])
        self.assertFalse(result["already_published"])

    def test_every_new_source_increases_version_without_manual_bump(self):
        result = plan.choose_version("2026.10.5", [release("2026.10.8")], SHA, TODAY)
        self.assertEqual("2026.10.9", result["version"])
        self.assertEqual(261009, plan.version_code(result["version"]))

    def test_calendar_floor_uses_current_month(self):
        result = plan.choose_version("2026.9.5", [], SHA, TODAY)
        self.assertEqual("2026.10.0", result["version"])

    def test_patch_and_year_boundaries_do_not_wrap_or_duplicate_codes(self):
        for current, expected in (("2026.10.99", "2026.11.0"), ("2026.12.99", "2027.1.0")):
            self.assertEqual(expected, plan.next_version(current))
            self.assertGreater(plan.version_code(expected), plan.version_code(current))
        with self.assertRaises(ValueError):
            plan.next_version("2099.12.99")

    def test_prerelease_unrelated_and_draft_do_not_become_stable(self):
        releases = [release("2026.10.2"), release("2026.10.8", prerelease=True),
                    release("2026.12.5", draft=True), dict(tag_name="preview", draft=False)]
        result = plan.choose_version("2026.10.5", releases, SHA, TODAY)
        self.assertEqual("2026.10.5", result["version"])
        self.assertEqual("v2026.10.2", result["previous_tag"])

    def test_different_source_draft_or_tag_is_not_overwritten(self):
        result = plan.choose_version("2026.10.5", [release("2026.10.5", draft=True)], SHA, TODAY)
        self.assertEqual("2026.10.6", result["version"])

    def test_same_source_draft_is_resumed_even_after_month_boundary(self):
        result = plan.choose_version("2026.10.5", [release("2026.10.5", SHA, draft=True)], SHA, date(2026, 11, 1))
        self.assertEqual("2026.10.5", result["version"])
        self.assertFalse(result["already_published"])

    def test_rerun_of_published_commit_is_idempotent(self):
        for target in (SHA, "main", "b" * 40):
            entry = dict(release("2026.10.6", target), _source_sha=SHA)
            result = plan.choose_version("2026.10.5", [entry], SHA, TODAY)
            self.assertEqual("2026.10.6", result["version"])
            self.assertTrue(result["already_published"])
            self.assertIn("v2026.10.6", result["release_url"])


    def test_incomplete_published_release_is_not_silently_repaired(self):
        broken = release("2026.10.5", SHA)
        broken["assets"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete assets"):
            plan.choose_version("2026.10.5", [broken], SHA, TODAY)

    def test_explicit_tag_must_equal_allocated_version(self):
        plan.choose_version("2026.10.5", [], SHA, TODAY, "v2026.10.5")
        with self.assertRaisesRegex(ValueError, "must be"):
            plan.choose_version("2026.10.5", [], SHA, TODAY, "v2026.10.2")

    def test_source_floor_and_canonical_versions(self):
        self.assertEqual("2026.1.5", plan.canonical("2026.01.05"))
        for bad in ("1.0.0", "v2026.10.5", "2026.13.5", "2026.10.100", "2026.10.5\n"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                plan.canonical(bad)

    def test_runner_only_apply_cannot_downgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "VERSION"
            path.write_text("2026.10.5\n")
            plan.apply_version(path, "2026.10.6")
            self.assertEqual("2026.10.6\n", path.read_text())
            with self.assertRaises(ValueError):
                plan.apply_version(path, "2026.10.4")
            self.assertEqual("2026.10.6\n", path.read_text())

    def test_stale_branch_cannot_publish_over_newer_history(self):
        import subprocess
        with patch.object(plan, "git_commit", return_value="b" * 40), \
             patch.object(plan.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(ValueError, "does not descend"):
                plan.check_lineage(release("2026.10.5"), SHA)


class PublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.run = {"repository": {"full_name": REPO}, "head_sha": SHA, "event": "push"}

    def test_exact_source_and_all_three_build_gates_are_required(self):
        self.assertEqual(3, len(pub.validate_run(self.run, jobs(), REPO, SHA, "refs/heads/arena/test", "v2026.10.5")))
        for index in range(3):
            for state in ("failure", "cancelled", "skipped", None):
                broken = jobs()
                broken[index]["conclusion"] = state
                with self.subTest(index=index, state=state), self.assertRaises(ValueError):
                    pub.validate_run(self.run, broken, REPO, SHA, "refs/heads/main", "v2026.10.5")
        with self.assertRaises(ValueError):
            pub.validate_run(self.run, jobs()[1:], REPO, SHA, "refs/heads/main", "v2026.10.5")

    def test_reusable_job_names_and_manual_tag_are_supported(self):
        run = dict(self.run, event="workflow_dispatch")
        self.assertEqual(3, len(pub.validate_run(run, jobs("Build, verify and release / "), REPO,
                                                SHA, "refs/tags/v2026.10.5", "v2026.10.5")))

    def test_pr_fork_wrong_commit_and_wrong_tag_cannot_publish(self):
        for run, sha, ref in ((dict(self.run, event="pull_request"), SHA, "refs/pull/4/merge"),
                              (dict(self.run, repository={"full_name": "someone/fork"}), SHA, "refs/heads/main"),
                              (self.run, "b" * 40, "refs/heads/main"),
                              (self.run, SHA, "refs/tags/v2026.10.4"),
                              (self.run, SHA, "refs/heads/")):
            with self.subTest(run=run, ref=ref), self.assertRaises(ValueError):
                pub.validate_run(run, jobs(), REPO, sha, ref, "v2026.10.5")

    def test_duplicate_job_name_cannot_fake_a_pass(self):
        with self.assertRaises(ValueError):
            pub.validate_run(self.run, jobs() + jobs()[:1], REPO, SHA, "refs/heads/main", "v2026.10.5")

    def test_complete_same_version_payload_has_immutable_manifest_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = pub.assemble(make_staging(root), root / "release", "2026.10.5", REPO)
            self.assertEqual("2026.10.5", manifest["appVersion"])
            self.assertIn("/download/v2026.10.5", manifest["baseUrl"])
            self.assertNotIn("latest", manifest["baseUrl"])
            for name, entry in manifest["files"].items():
                self.assertEqual(pub.digest(root / "release" / name), entry["sha256"])
                self.assertTrue(entry["url"].endswith("/" + name))

    def test_wrong_version_bad_checksum_missing_and_debug_assets_fail_closed(self):
        for fault in ("version", "checksum", "missing", "debug"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                staging = make_staging(root)
                if fault == "version":
                    expected = "2026.10.6"
                else:
                    expected = "2026.10.5"
                if fault == "checksum":
                    (staging / "content" / "bank.json").write_text('{"changed":true}')
                elif fault == "missing":
                    (staging / "windows" / "CTMathsTutor-arm64.exe").unlink()
                elif fault == "debug":
                    (staging / "android" / "app-debug.apk").write_bytes(b"not a release APK")
                with self.assertRaises(ValueError):
                    pub.assemble(staging, root / "release", expected, REPO)

    def test_uploaded_inventory_checks_server_digest_and_completeness(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in plan.RELEASE_FILES:
                (root / name).write_bytes(b"payload")
            assets = [{"name": name, "state": "uploaded", "size": 7, "digest": "sha256:" + pub.digest(root / name)}
                      for name in plan.RELEASE_FILES]
            pub.validate_inventory({"assets": assets}, root)
            for bad in (assets[:-1], assets + [dict(name="app-debug.apk", state="uploaded", size=7)],
                        [dict(asset, digest="sha256:" + "0" * 64) for asset in assets],
                        [dict(asset, state="new") for asset in assets]):
                with self.assertRaises(ValueError):
                    pub.validate_inventory({"assets": bad}, root)

    def test_atomic_publication_and_audit_with_mocked_github(self):
        self.simulate_publication(fault=False)

    def test_incomplete_draft_never_becomes_public_or_latest(self):
        self.simulate_publication(fault=True)

    def simulate_publication(self, fault):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "VERSION").write_text("2026.10.5\n")
            cert = root / "android/keystore/expected-cert-sha256.txt"
            cert.parent.mkdir(parents=True)
            cert.write_text("B2:BD:fake-test-only\n")
            staging = make_staging(root)
            output = root / "release"
            args = argparse.Namespace(repo=REPO, version="2026.10.5", source_version="2026.10.5",
                                      run_id="99", staging=staging, output=output)
            state = {"tag": None, "draft": True, "uploaded": False, "promoted": False}

            def api(path, *, method="GET", fields=None, **kwargs):
                if path.endswith("/actions/runs/99"):
                    return self.run
                if path.endswith("/git/refs"):
                    self.assertEqual(SHA, fields["sha"])
                    state["tag"] = SHA
                    return {}
                if path.endswith("/releases") and method == "POST":
                    self.assertEqual(SHA, state["tag"])
                    self.assertTrue(fields["draft"])
                    return dict(release("2026.10.5", SHA, draft=True), id=11)
                if path.endswith("/releases/11") or path.endswith("/releases/latest"):
                    if method == "PATCH" and fields.get("draft") is False:
                        self.assertTrue(state["uploaded"])
                        self.assertFalse(fault)
                        state["draft"], state["promoted"] = False, True
                    assets = [{"name": p.name, "state": "uploaded", "size": p.stat().st_size,
                               "digest": "sha256:" + pub.digest(p)} for p in output.iterdir()]
                    if fault:
                        assets.pop()
                    return dict(release("2026.10.5", SHA, draft=state["draft"]), id=11, assets=assets)
                self.fail("unexpected API request: " + path)

            def upload(arguments):
                self.assertEqual(["release", "upload", "v2026.10.5"], arguments[:3])
                self.assertTrue(state["draft"])
                state["uploaded"] = True
                return ""

            env = {"GITHUB_SHA": SHA, "GITHUB_RUN_ID": "99", "GITHUB_REF": "refs/heads/main", "GITHUB_STEP_SUMMARY": ""}
            with patch.object(pub, "ROOT", root), patch.object(pub, "git_commit", return_value=SHA), \
                 patch.object(pub, "check_lineage"), patch.object(pub, "gh_json", side_effect=api), \
                 patch.object(pub, "gh_pages", side_effect=lambda path: jobs() if "/jobs?" in path else [release("2026.10.4")]), \
                 patch.object(pub, "tag_commit", side_effect=lambda repo, tag: state["tag"]), \
                 patch.object(pub, "gh", side_effect=upload), patch.dict(os.environ, env), \
                 contextlib.redirect_stdout(io.StringIO()):
                if fault:
                    with self.assertRaises(ValueError):
                        pub.publish(args)
                    self.assertFalse(state["promoted"])
                    self.assertTrue(state["draft"])
                else:
                    pub.publish(args)
                    self.assertTrue(state["promoted"])
                    info = json.loads((output / "release-info.json").read_text())
                    self.assertEqual(SHA, info["sourceCommit"])
                    self.assertEqual(261005, info["android"]["versionCode"])
                    self.assertEqual(3, len(info["checks"]))
                    for line in (output / "SHA256SUMS.txt").read_text().splitlines():
                        expected, name = line.split("  ")
                        self.assertEqual(expected, hashlib.sha256((output / name).read_bytes()).hexdigest())
                    self.assertEqual(len(plan.RELEASE_FILES) - 1, len((output / "SHA256SUMS.txt").read_text().splitlines()))


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # BaseLoader preserves `on` (YAML 1.2 used by Actions), unlike SafeLoader's
        # YAML 1.1 boolean conversion of `on` to True.
        cls.ci = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
        cls.recovery = yaml.load((ROOT / ".github/workflows/release.yml").read_text(), Loader=yaml.BaseLoader)
        cls.publisher = yaml.load((ROOT / ".github/workflows/publish.yml").read_text(), Loader=yaml.BaseLoader)

    def test_ci_triggers_and_queue_preserve_successive_pushes(self):
        self.assertEqual(["**"], self.ci["on"]["push"]["branches"])
        self.assertIn("pull_request", self.ci["on"])
        self.assertEqual("max", self.ci["concurrency"]["queue"])
        self.assertEqual("false", self.ci["concurrency"]["cancel-in-progress"])
        self.assertEqual("bash", self.ci["defaults"]["run"]["shell"])
        for job in self.ci["jobs"].values():
            if "runs-on" in job:
                self.assertEqual("ubuntu-24.04", job["runs-on"])
        self.assertEqual("ubuntu-24.04", self.publisher["jobs"]["publish"]["runs-on"])
        self.assertIn("ctmaths-release-pipeline", self.ci["concurrency"]["group"])
        self.assertEqual("ctmaths-release-pipeline", self.recovery["concurrency"]["group"])
        self.assertEqual("max", self.recovery["concurrency"]["queue"])

    def test_recovery_uses_complete_ci_and_avoids_nested_lock_deadlock(self):
        recovery = self.recovery["jobs"]["build_verify_publish"]
        self.assertEqual("./.github/workflows/ci.yml", recovery["uses"])
        self.assertEqual("true", recovery["with"]["release_request"])
        self.assertIn("ci-release-child-", self.ci["concurrency"]["group"])
        self.assertIn("inputs.release_request", self.ci["concurrency"]["group"])

    def test_publication_needs_every_gate_and_is_not_enabled_for_prs(self):
        job = self.ci["jobs"]["publish"]
        self.assertEqual({"prepare", "content", "windows", "android"}, set(job["needs"]))
        self.assertIn("success()", job["if"])
        self.assertIn("already_published != 'true'", job["if"])
        self.assertEqual("read", self.ci["permissions"]["contents"])
        self.assertEqual("write", job["permissions"]["contents"])
        condition = self.ci["jobs"]["prepare"]["steps"][-1]["env"]["ALLOW_PUBLICATION"]
        self.assertIn(REPO, condition)
        self.assertIn("github.event_name != 'pull_request'", condition)

    def test_all_builds_apply_the_exact_same_effective_version(self):
        for key, name in zip(("content", "windows", "android"), plan.BUILD_JOBS):
            job = self.ci["jobs"][key]
            self.assertEqual(name, job["name"])
            self.assertEqual("prepare", job["needs"])
            self.assertEqual("${{ needs.prepare.outputs.version }}", job["env"]["BUILD_VERSION"])
            self.assertTrue(any("--apply-version" in step.get("run", "") for step in job["steps"]))
        names = [step.get("name", "") for step in self.ci["jobs"]["content"]["steps"]]
        self.assertLess(names.index("Ensure the committed assets match the sources"),
                        names.index("Apply the effective version to the verified content"))
        android = "\n".join(step.get("run", "") for step in self.ci["jobs"]["android"]["steps"])
        self.assertIn("--previous previous-release/app-release.apk", android)
        self.assertIn("--require --apk previous-release/app-release.apk", android)
        previous = [step for step in self.ci["jobs"]["android"]["steps"] if "--previous previous-release" in step.get("run", "")][0]
        self.assertIn("already_published != 'true'", previous["if"])

    def test_publisher_reuses_same_run_artifacts_never_debug(self):
        self.assertEqual({"workflow_call"}, set(self.publisher["on"]))
        steps = self.publisher["jobs"]["publish"]["steps"]
        downloads = [step for step in steps if step.get("uses", "").startswith("actions/download-artifact@")]
        self.assertEqual({"content-bank", "windows-exe", "android-release-apk"}, {step["with"]["name"] for step in downloads})
        self.assertFalse(any("run-id" in step["with"] or "repository" in step["with"] for step in downloads))
        self.assertFalse(any("gradle" in step.get("run", "") or "go build" in step.get("run", "") for step in steps))
        self.assertTrue(any(step.get("with", {}).get("name") == "release-audit" for step in steps))


if __name__ == "__main__":
    unittest.main()
