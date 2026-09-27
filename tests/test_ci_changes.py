"""Exercise build selection and whitespace checks against real Git histories."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci-changes.py"
spec = importlib.util.spec_from_file_location("ci_changes", SCRIPT)
changes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changes)


class SelectionTests(unittest.TestCase):
    def test_known_lightweight_paths(self):
        paths = ["README.md", "docs/release-checklist.md", "tests/test_scripts.py",
                 ".github/ISSUE_TEMPLATE/build_failure.yml", ".github/dependabot.yml",
                 ".github/workflows/watch-upstream.yml"]
        self.assertFalse(changes.requires_build("pull_request", "refs/pull/1/merge", paths))
        self.assertFalse(changes.requires_build("push", "refs/heads/main", paths))

    def test_packaging_workflow_and_unknown_paths_force_build(self):
        for path in ["rpi-imager.spec", "patches/fix.patch", "scripts/build-rpm.sh",
                     "scripts/smoke-test-rpm.sh", "scripts/ci-changes.py",
                     "scripts/prepare-release.py", "scripts/update-version.py",
                     ".github/workflows/build-rpm.yml", "new-config.yml", ".gitattributes"]:
            with self.subTest(path=path):
                self.assertTrue(changes.requires_build("pull_request", "refs/pull/1/merge",
                                                       ["README.md", path]))

    def test_tags_manual_and_unknown_events_force_build(self):
        for event, ref in [("push", "refs/tags/rpm-v2.0.11.1-2"),
                           ("workflow_dispatch", "refs/heads/main"),
                           ("unexpected", "refs/heads/main"), ("push", "unknown")]:
            with self.subTest(event=event, ref=ref):
                self.assertTrue(changes.requires_build(event, ref, ["README.md"]))
                self.assertTrue(changes.requires_build(event, ref, []))


class GitDiffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.write("README.md", "Initial documentation\n")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-c", "user.name=CI Test", "-c", "user.email=ci@example.invalid",
             "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
            cwd=self.repo, text=True, stderr=subprocess.STDOUT).strip()

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "Test change")
        return self.git("rev-parse", "HEAD")

    def run_check(self, event_name, event, ref="refs/heads/main"):
        event_file = self.root / "event.json"
        output = self.root / "output"
        event_file.write_text(json.dumps(event))
        output.write_text("")
        env = dict(os.environ, GITHUB_EVENT_NAME=event_name, GITHUB_REF=ref,
                   GITHUB_EVENT_PATH=str(event_file), GITHUB_OUTPUT=str(output))
        result = subprocess.run([sys.executable, str(SCRIPT)], cwd=self.repo, env=env,
                                text=True, capture_output=True)
        return result, output.read_text()

    def push(self, before, after):
        return self.run_check("push", {"ref": "refs/heads/main", "before": before, "after": after})

    def test_push_covers_every_commit_not_just_last(self):
        self.write("rpi-imager.spec", "Version: 1.0\n")
        self.commit()
        self.write("README.md", "Documentation update\n")
        head = self.commit()
        result, output = self.push(self.base, head)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "full_build=true\n")

    def test_pr_uses_merge_base_and_ignores_unrelated_main_changes(self):
        self.git("switch", "-qc", "feature")
        self.write("README.md", "Documentation update\n")
        head = self.commit()
        self.git("switch", "-q", "main")
        self.write("rpi-imager.spec", "Unrelated main change with whitespace  \n")
        base = self.commit()
        result, output = self.run_check("pull_request", {
            "pull_request": {"base": {"sha": base}, "head": {"sha": head}}}, "refs/pull/1/merge")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "full_build=false\n")

    def test_committed_whitespace_fails_with_clean_worktree(self):
        self.write("README.md", "Trailing spaces  \n")
        head = self.commit()
        self.assertEqual(self.git("status", "--porcelain"), "")
        result, output = self.push(self.base, head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout)
        self.assertEqual(output, "")

    def test_renaming_packaging_file_to_documentation_still_builds(self):
        self.write("packaging.conf", "packaging\n")
        base = self.commit()
        (self.repo / "docs").mkdir()
        self.git("mv", "packaging.conf", "docs/packaging.md")
        result, output = self.push(base, self.commit())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "full_build=true\n")

    def test_deleting_packaging_file_still_builds(self):
        self.write("rpi-imager.spec", "Version: 1.0\n")
        base = self.commit()
        self.git("rm", "rpi-imager.spec")
        result, output = self.push(base, self.commit())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "full_build=true\n")

    def test_unavailable_base_fails_without_skip_output(self):
        result, output = self.push("f" * 40, self.base)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output, "")

    def test_new_branch_compares_entire_tree(self):
        self.write("rpi-imager.spec", "Version: 1.0\n")
        result, output = self.push("0" * 40, self.commit())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output, "full_build=true\n")

    def test_manual_and_tag_runs_build_even_for_root_documentation_commit(self):
        for event_name, ref in [("workflow_dispatch", "refs/heads/main"),
                                ("push", "refs/tags/rpm-v1.0-1")]:
            result, output = self.run_check(event_name, {}, ref)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output, "full_build=true\n")


if __name__ == "__main__":
    unittest.main()
