"""Subject release isolation, version policy, fail-closed publication and workflow contracts.

No network, native SDK or real GitHub mutations. The shared repository already
publishes the mathematics tutor (tags v…, it owns /releases/latest); these
tests prove the Russian pipeline can never touch that channel.
"""
import argparse
import contextlib
from copy import deepcopy
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import publish_release as pub  # noqa: E402
import release_plan as plan  # noqa: E402
import subject  # noqa: E402

SHA = "a" * 40
REPO = "zigorminsk-debug/mathematics"
TODAY = date(2026, 10, 14)
MATH_ASSETS = ["analogous.json", "answer_vectors.json", "app-release.apk", "bank.json", "CTMathsTutor-amd64.exe",
               "CTMathsTutor-arm64.exe", "formulas.json", "mistakes.json", "release-info.json", "SHA256SUMS.txt",
               "topics.json", "ui_strings.json", "version.json"]


def release(version, sha="b" * 40, *, draft=False, prerelease=False, family="russian-v", assets=None):
    tag = family + version
    return {"id": 10, "tag_name": tag, "target_commitish": sha, "draft": draft, "prerelease": prerelease,
            "html_url": f"https://github.com/{REPO}/releases/tag/{tag}",
            "assets": [{"name": name} for name in (assets or plan.RELEASE_FILES)]}


def math_release(version, sha="c" * 40):
    return release(version, sha, family="v", assets=MATH_ASSETS)


def jobs(prefix=""):
    return [{"name": prefix + name, "conclusion": "success", "id": index} for index, name in enumerate(plan.BUILD_JOBS, 1)]


def make_staging(root, version="2026.10.5", subject_id="russian", package="by.ziv.ctrussian"):
    staging = root / "staging"
    for name in ("content", "windows", "android"):
        (staging / name).mkdir(parents=True)
    for name in plan.CONTENT_FILES:
        payload = {"meta": {"subject": subject_id, "package": package}} if name in ("bank.json", "analogous.json") else {}
        (staging / "content" / name).write_text(json.dumps(payload) + "\n", encoding="utf-8")
    files = {name: pub.metadata(staging / "content" / name) for name in sorted(plan.CONTENT_FILES)}
    pub.write_json(staging / "content" / "version.json", {
        "schema": 2, "subject": subject_id, "package": package, "contentProtocol": 2, "contentVersion": version,
        "files": files})
    for name in plan.INSTALLERS:
        (staging / ("android" if name.endswith(".apk") else "windows") / name).write_bytes(b"fake native artifact")
    return staging


class SubjectConfigTests(unittest.TestCase):
    def test_explicit_identities(self):
        self.assertEqual("russian", subject.SUBJECT)
        self.assertEqual("russian-v", subject.TAG_PREFIX)
        self.assertEqual("by.ziv.ctrussian", subject.PACKAGE)
        self.assertEqual("by.ziv.ctrussian.debug", subject.DEBUG_PACKAGE)
        self.assertEqual(("CTRussianTutor-amd64.exe", "CTRussianTutor-arm64.exe"), subject.WINDOWS_EXES)
        self.assertEqual("ctrussian-release-pipeline", subject.PIPELINE_LOCK)
        self.assertEqual({"app-release.apk", *subject.WINDOWS_EXES}, plan.INSTALLERS)
        self.assertNotIn("formulas.json", plan.CONTENT_FILES)

    def test_unsafe_configurations_are_rejected(self):
        good = json.loads((ROOT / "subject.json").read_text(encoding="utf-8"))
        mutations = [
            lambda c: c["release"].update(makeLatest=True), lambda c: c.update(tagPrefix="v"),
            lambda c: c.update(tagPrefix="russian"), lambda c: c["android"].update(applicationId="by.ziv.ctmaths.x1"),
            lambda c: c["android"].update(debugApplicationId="by.ziv.ctrussian"),
            lambda c: c["release"].update(foreignPackages=["by.ziv.ctrussian"]), lambda c: c.update(contentProtocol=1),
        ]
        subject.validate(deepcopy(good))
        for mutate in mutations:
            broken = deepcopy(good)
            mutate(broken)
            with self.assertRaises(ValueError):
                subject.validate(broken)


class ReleasePlanTests(unittest.TestCase):
    def test_first_subject_release_ignores_math_and_sibling_releases(self):
        releases = [math_release("2026.10.8"), math_release("2026.10.7"), release("2026.10.9", family="physics-v")]
        result = plan.choose_version("2026.10.1", releases, SHA, TODAY)
        self.assertEqual("2026.10.1", result["version"])
        self.assertEqual("russian-v2026.10.1", result["tag"])
        self.assertEqual("", result["previous_tag"], "the first release is not compared with the math APK")
        self.assertFalse(result["already_published"])
        self.assertEqual("russian", result["subject"])

    def test_counter_and_previous_are_per_subject(self):
        releases = [math_release("2026.10.20"), release("2026.10.3"), release("2026.10.2")]
        result = plan.choose_version("2026.10.1", releases, SHA, TODAY)
        self.assertEqual("2026.10.4", result["version"])
        self.assertEqual("russian-v2026.10.3", result["previous_tag"])

    def test_foreign_and_non_canonical_tags_are_not_this_family(self):
        for tag in ("v2026.10.8", "physics-v2026.10.1", "russian-v2026.10.01", "russian-2026.10.1", "xrussian-v2026.10.1"):
            self.assertIsNone(plan.release_version({"tag_name": tag}), tag)
        self.assertEqual("2026.10.1", plan.release_version({"tag_name": "russian-v2026.10.1"}))
        self.assertEqual([], plan.stable_releases([math_release("2026.10.8")]))

    def test_math_release_of_the_same_commit_is_not_idempotent_success(self):
        result = plan.choose_version("2026.10.1", [dict(math_release("2026.10.8"), _source_sha=SHA)], SHA, TODAY)
        self.assertFalse(result["already_published"])
        self.assertEqual("russian-v2026.10.1", result["tag"])

    def test_every_new_source_increases_version(self):
        result = plan.choose_version("2026.10.1", [release("2026.10.8")], SHA, TODAY)
        self.assertEqual("2026.10.9", result["version"])
        self.assertEqual(261009, plan.version_code(result["version"]))

    def test_calendar_floor_uses_current_month(self):
        self.assertEqual("2026.10.0", plan.choose_version("2026.9.5", [], SHA, TODAY)["version"])

    def test_patch_and_year_boundaries(self):
        for current, expected in (("2026.10.99", "2026.11.0"), ("2026.12.99", "2027.1.0")):
            self.assertEqual(expected, plan.next_version(current))
        with self.assertRaises(ValueError):
            plan.next_version("2099.12.99")

    def test_prerelease_and_draft_do_not_become_stable(self):
        releases = [release("2026.10.2"), release("2026.10.8", prerelease=True), release("2026.12.5", draft=True)]
        result = plan.choose_version("2026.10.1", releases, SHA, TODAY)
        self.assertEqual("2026.10.3", result["version"])
        self.assertEqual("russian-v2026.10.2", result["previous_tag"])

    def test_different_source_draft_is_skipped_and_own_draft_resumed(self):
        self.assertEqual("2026.10.2", plan.choose_version("2026.10.1", [release("2026.10.1", draft=True)], SHA, TODAY)["version"])
        resumed = plan.choose_version("2026.10.1", [release("2026.10.1", SHA, draft=True)], SHA, date(2026, 11, 1))
        self.assertEqual("2026.10.1", resumed["version"])

    def test_rerun_of_published_commit_is_idempotent(self):
        entry = dict(release("2026.10.6", "main"), _source_sha=SHA)
        result = plan.choose_version("2026.10.1", [entry], SHA, TODAY)
        self.assertTrue(result["already_published"])
        self.assertIn("russian-v2026.10.6", result["release_url"])

    def test_incomplete_published_release_is_not_silently_repaired(self):
        broken = release("2026.10.5", SHA)
        broken["assets"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete assets"):
            plan.choose_version("2026.10.1", [dict(broken, _source_sha=SHA)], SHA, TODAY)

    def test_explicit_tag_must_equal_allocated_version(self):
        plan.choose_version("2026.10.1", [], SHA, TODAY, "russian-v2026.10.1")
        for bad in ("v2026.10.1", "russian-v2026.10.0"):
            with self.assertRaisesRegex(ValueError, "must be"):
                plan.choose_version("2026.10.1", [], SHA, TODAY, bad)

    def test_reservations_only_list_this_family(self):
        calls = []

        def fake(arguments, **kwargs):
            calls.append(arguments)
            return "russian-v2026.10.1\n"
        with patch.object(plan.subprocess, "check_output", side_effect=fake), \
             patch.object(plan, "git_commit", return_value=SHA):
            reservations = plan.unpublished_tag_reservations([])
        self.assertEqual(["git", "tag", "--list", "russian-v*"], calls[0])
        self.assertEqual("russian-v2026.10.1", reservations[0]["tag_name"])

    def test_runner_only_apply_cannot_downgrade(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "VERSION"
            path.write_text("2026.10.1\n")
            plan.apply_version(path, "2026.10.2")
            with self.assertRaises(ValueError):
                plan.apply_version(path, "2026.10.0")
            self.assertEqual("2026.10.2\n", path.read_text())

    def test_stale_branch_cannot_publish_over_newer_history(self):
        with patch.object(plan, "git_commit", return_value="b" * 40), \
             patch.object(plan.subprocess, "run", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(ValueError, "does not descend"):
                plan.check_lineage(release("2026.10.5"), SHA)


class PublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.run = {"repository": {"full_name": REPO}, "head_sha": SHA, "event": "push"}

    def test_exact_source_and_all_three_build_gates_are_required(self):
        tag = "russian-v2026.10.5"
        self.assertEqual(3, len(pub.validate_run(self.run, jobs(), REPO, SHA, "refs/heads/arena/x", tag)))
        for index in range(3):
            for state in ("failure", "cancelled", "skipped", None):
                broken = jobs()
                broken[index]["conclusion"] = state
                with self.subTest(index=index, state=state), self.assertRaises(ValueError):
                    pub.validate_run(self.run, broken, REPO, SHA, "refs/heads/arena/x", tag)

    def test_pr_fork_wrong_commit_and_foreign_tag_cannot_publish(self):
        tag = "russian-v2026.10.5"
        for run, sha, ref in ((dict(self.run, event="pull_request"), SHA, "refs/pull/4/merge"),
                              (dict(self.run, repository={"full_name": "someone/fork"}), SHA, "refs/heads/main"),
                              (self.run, "b" * 40, "refs/heads/main"), (self.run, SHA, "refs/tags/v2026.10.5"),
                              (self.run, SHA, "refs/tags/russian-v2026.10.4"), (self.run, SHA, "refs/heads/")):
            with self.subTest(ref=ref), self.assertRaises(ValueError):
                pub.validate_run(run, jobs(), REPO, sha, ref, tag)
        manual = dict(self.run, event="workflow_dispatch")
        self.assertEqual(3, len(pub.validate_run(manual, jobs("Build, verify and release / "), REPO, SHA,
                                                 "refs/tags/" + tag, tag)))

    def test_manifest_is_subject_scoped_with_tag_specific_urls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = pub.assemble(make_staging(root), root / "release", "2026.10.5", REPO)
            self.assertEqual("russian-v2026.10.5", manifest["tag"])
            self.assertTrue(manifest["baseUrl"].endswith("/releases/download/russian-v2026.10.5"))
            self.assertNotIn("latest", json.dumps(manifest))
            self.assertEqual(("russian", "by.ziv.ctrussian", 2), (manifest["subject"], manifest["package"], manifest["schema"]))
            for name, entry in manifest["files"].items():
                self.assertEqual(pub.digest(root / "release" / name), entry["sha256"])
                self.assertIn("/download/russian-v2026.10.5/", entry["url"])

    def test_foreign_or_broken_payload_fails_closed(self):
        for fault in ("version", "checksum", "missing", "debug", "math-manifest", "math-bank"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                staging = make_staging(root, subject_id="mathematics" if fault == "math-manifest" else "russian")
                expected = "2026.10.6" if fault == "version" else "2026.10.5"
                if fault == "checksum":
                    (staging / "content" / "topics.json").write_text('{"changed":true}')
                elif fault == "missing":
                    (staging / "windows" / "CTRussianTutor-arm64.exe").unlink()
                elif fault == "debug":
                    (staging / "android" / "app-debug.apk").write_bytes(b"not a release APK")
                elif fault == "math-bank":
                    bank = staging / "content" / "bank.json"
                    bank.write_text('{"meta":{"subject":"mathematics","package":"by.ziv.ctmaths"}}\n')
                    manifest = json.loads((staging / "content" / "version.json").read_text())
                    manifest["files"]["bank.json"] = pub.metadata(bank)
                    pub.write_json(staging / "content" / "version.json", manifest)
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

    def test_publication_keeps_math_latest(self):
        calls = self.simulate_publication("ok")
        posts = [fields for method, path, fields in calls if method == "POST" and path.endswith("/releases")]
        patches = [fields for method, path, fields in calls if method == "PATCH" and path.endswith("/releases/11")]
        self.assertEqual("false", posts[0]["make_latest"], "make_latest=false is explicit on create")
        self.assertTrue(any(f.get("draft") is False and f.get("make_latest") == "false" for f in patches),
                        "make_latest=false is explicit on the promote PATCH")
        self.assertFalse(any(f and f.get("make_latest") == "true" for _, _, f in calls))
        latest_reads = [path for method, path, _ in calls if method == "GET" and path.endswith("/releases/latest")]
        self.assertEqual(2, len(latest_reads), "latest is compared before and after, never used to confirm")

    def test_incomplete_draft_is_never_published(self):
        self.simulate_publication("incomplete")

    def test_latest_hijack_is_reverted_and_fails(self):
        calls = self.simulate_publication("hijack")
        restore = [(path, fields) for method, path, fields in calls if method == "PATCH" and path.endswith("/releases/412525779")]
        self.assertEqual([("repos/%s/releases/412525779" % REPO, {"make_latest": "true"})], restore)

    def simulate_publication(self, mode):
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "VERSION").write_text("2026.10.1\n")
            cert = root / "android/keystore/expected-cert-sha256.txt"
            cert.parent.mkdir(parents=True)
            cert.write_text("DE:65:fake-test-only\n")
            staging = make_staging(root, "2026.10.1")
            output = root / "release"
            args = argparse.Namespace(repo=REPO, version="2026.10.1", source_version="2026.10.1", run_id="99",
                                      staging=staging, output=output)
            state = {"tag": None, "draft": True, "uploaded": False, "promoted": False}
            math_latest = {"id": 412525779, "tag_name": "v2026.10.8"}

            def api(path, *, method="GET", fields=None, **kwargs):
                calls.append((method, path, fields))
                if path.endswith("/actions/runs/99"):
                    return self.run
                if path.endswith("/git/refs"):
                    state["tag"] = fields["sha"]
                    return {}
                if path.endswith("/releases/latest"):
                    hijacked = mode == "hijack" and state["promoted"]
                    return {"id": 11, "tag_name": "russian-v2026.10.1"} if hijacked else math_latest
                if path.endswith("/releases") and method == "POST":
                    self.assertTrue(fields["draft"])
                    return dict(release("2026.10.1", SHA, draft=True), id=11)
                if path.endswith("/releases/412525779") and method == "PATCH":
                    return math_latest
                if path.endswith("/releases/11"):
                    if method == "PATCH" and fields.get("draft") is False:
                        self.assertTrue(state["uploaded"])
                        self.assertNotEqual("incomplete", mode)
                        state["draft"], state["promoted"] = False, True
                    assets = [{"name": p.name, "state": "uploaded", "size": p.stat().st_size,
                               "digest": "sha256:" + pub.digest(p)} for p in output.iterdir()]
                    if mode == "incomplete":
                        assets.pop()
                    return dict(release("2026.10.1", SHA, draft=state["draft"]), id=11, assets=assets)
                self.fail("unexpected API request: " + path)

            def upload(arguments):
                self.assertEqual(["release", "upload", "russian-v2026.10.1"], arguments[:3])
                self.assertTrue(state["draft"])
                state["uploaded"] = True
                return ""

            env = {"GITHUB_SHA": SHA, "GITHUB_RUN_ID": "99", "GITHUB_REF": "refs/heads/arena/339e10e8-mathematics",
                   "GITHUB_STEP_SUMMARY": ""}
            pages = lambda path: jobs() if "/jobs?" in path else [math_release("2026.10.8")]  # noqa: E731
            with patch.object(pub, "ROOT", root), patch.object(pub, "git_commit", return_value=SHA), \
                 patch.object(pub, "check_lineage") as lineage, patch.object(pub, "gh_json", side_effect=api), \
                 patch.object(pub, "gh_pages", side_effect=pages), \
                 patch.object(pub, "tag_commit", side_effect=lambda repo, tag: state["tag"]), \
                 patch.object(pub, "gh", side_effect=upload), patch.dict(os.environ, env), \
                 contextlib.redirect_stdout(io.StringIO()):
                if mode == "ok":
                    pub.publish(args)
                    lineage.assert_called_once_with(None, SHA)  # first release: no math lineage
                    info = json.loads((output / "release-info.json").read_text())
                    self.assertEqual(("russian", "by.ziv.ctrussian", "russian-v2026.10.1"),
                                     (info["subject"], info["package"], info["tag"]))
                    self.assertFalse(info["publication"]["makeLatest"])
                    self.assertEqual({"id": 412525779, "tag": "v2026.10.8"}, info["publication"]["repositoryLatestBefore"])
                    self.assertIsNone(info["previousStableTag"])
                    self.assertEqual(261001, info["android"]["versionCode"])
                    for line in (output / "SHA256SUMS.txt").read_text().splitlines():
                        expected, name = line.split("  ")
                        self.assertEqual(expected, hashlib.sha256((output / name).read_bytes()).hexdigest())
                else:
                    with self.assertRaises(ValueError):
                        pub.publish(args)
                    if mode == "incomplete":
                        self.assertFalse(state["promoted"])
        return calls


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
        cls.recovery = yaml.load((ROOT / ".github/workflows/release.yml").read_text(), Loader=yaml.BaseLoader)
        cls.publisher = yaml.load((ROOT / ".github/workflows/publish.yml").read_text(), Loader=yaml.BaseLoader)
        cls.texts = {name: (ROOT / f".github/workflows/{name}.yml").read_text() for name in ("ci", "release", "publish")}

    def test_subject_lock_never_shares_the_math_lock(self):
        self.assertIn(subject.PIPELINE_LOCK, self.ci["concurrency"]["group"])
        self.assertEqual(subject.PIPELINE_LOCK, self.recovery["concurrency"]["group"])
        for text in self.texts.values():
            self.assertNotIn("ctmaths-release-pipeline", text)
        self.assertEqual("max", self.ci["concurrency"]["queue"])
        self.assertEqual("false", self.ci["concurrency"]["cancel-in-progress"])
        self.assertIn("ci-release-child-", self.ci["concurrency"]["group"])

    def test_tag_entry_points_are_subject_family_only(self):
        self.assertEqual(["russian-v*"], self.recovery["on"]["push"]["tags"])
        self.assertIn("refs/tags/russian-v", self.recovery["jobs"]["build_verify_publish"]["if"])
        condition = self.ci["jobs"]["prepare"]["steps"][-1]["env"]["ALLOW_PUBLICATION"]
        self.assertIn("refs/tags/russian-v", condition)
        self.assertNotIn("'refs/tags/v'", condition)
        self.assertIn("github.event_name != 'pull_request'", condition)
        self.assertIn(REPO, condition)

    def test_publication_needs_every_gate(self):
        job = self.ci["jobs"]["publish"]
        self.assertEqual({"prepare", "content", "windows", "android"}, set(job["needs"]))
        self.assertIn("success()", job["if"])
        self.assertIn("already_published != 'true'", job["if"])
        self.assertEqual("read", self.ci["permissions"]["contents"])
        self.assertEqual("write", job["permissions"]["contents"])

    def test_builds_use_subject_artifacts_and_key(self):
        windows = "\n".join(step.get("run", "") for step in self.ci["jobs"]["windows"]["steps"])
        for exe in subject.WINDOWS_EXES:
            self.assertIn("../dist/" + exe, windows)
        self.assertNotIn("CTMathsTutor", self.texts["ci"])
        android = "\n".join(step.get("run", "") for step in self.ci["jobs"]["android"]["steps"])
        self.assertIn("android/keystore/ctrussian-release.p12", android)
        previous = [step for step in self.ci["jobs"]["android"]["steps"] if "--previous previous-release" in step.get("run", "")][0]
        self.assertIn("env.PREVIOUS_TAG != ''", previous["if"])
        for key, name in zip(("content", "windows", "android"), plan.BUILD_JOBS):
            self.assertEqual(name, self.ci["jobs"][key]["name"])
            self.assertTrue(any("--apply-version" in step.get("run", "") for step in self.ci["jobs"][key]["steps"]))
        self.assertIn("rules_smoke.js", self.texts["ci"])

    def test_publisher_reuses_same_run_artifacts_never_debug(self):
        self.assertEqual({"workflow_call"}, set(self.publisher["on"]))
        steps = self.publisher["jobs"]["publish"]["steps"]
        downloads = [step for step in steps if step.get("uses", "").startswith("actions/download-artifact@")]
        self.assertEqual({"content-bank", "windows-exe", "android-release-apk"}, {step["with"]["name"] for step in downloads})
        self.assertFalse(any("run-id" in step["with"] for step in downloads))
        self.assertFalse(any("gradle" in step.get("run", "") or "go build" in step.get("run", "") for step in steps))

    def test_client_code_never_uses_repository_latest(self):
        for path in ("windows/store.go", "windows/main.go", "android/app/src/main/java/by/ziv/ctrussian/NativeBridge.kt",
                     "android/app/src/main/java/by/ziv/ctrussian/UpdateFeed.kt", "webapp/core.js", "webapp/app.js",
                     "tools/build_content.py"):
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn("releases/latest/download", text, path)


if __name__ == "__main__":
    unittest.main()
