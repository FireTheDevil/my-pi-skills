"""Directories occupying known evidence-file paths cannot prove absence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit.py"
SPEC = importlib.util.spec_from_file_location("audit_directories", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class DirectoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-audit-directory-")
        self.target = Path(self.tmp.name) / "project"
        self.target.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def gap(self, report, area):
        return next(item for item in report["gaps"] if item["area"] == area)

    def assert_unknown(self, report, path, area):
        self.assertFalse(report["complete_inventory"])
        self.assertIn(f"Skipped non-regular evidence file: {path}", report["notes"])
        self.assertNotIn(str(path.relative_to(self.target)), [item["path"] for item in report["inventory"]])
        gap = self.gap(report, area)
        self.assertEqual(gap["status"], "not verified")
        self.assertEqual(gap["evidence"], [])
        self.assertEqual(gap["proposal"], "Complete skipped/truncated inventory before proposing additions")

    def test_manifest_directories_are_unknown_without_file_reads(self):
        for name in sorted(AUDIT.MANIFESTS):
            with self.subTest(name=name):
                path = self.target / name
                path.mkdir()
                with patch.object(Path, "read_text", side_effect=AssertionError("Evidence was opened")):
                    report = AUDIT.audit(self.target)
                self.assert_unknown(report, path, "project manifest")
                self.assertTrue(path.is_dir())
                path.rmdir()

    def test_lock_directories_are_unknown(self):
        (self.target / "package.json").write_text('{"name":"fixture"}')
        for name in sorted(AUDIT.LOCKS):
            with self.subTest(name=name):
                path = self.target / name
                path.mkdir()
                self.assert_unknown(AUDIT.audit(self.target), path, "dependency lock")
                path.rmdir()

    def test_instruction_directories_are_unknown(self):
        for name in sorted(AUDIT.INSTRUCTIONS):
            with self.subTest(name=name):
                path = self.target / name
                path.mkdir()
                self.assert_unknown(AUDIT.audit(self.target), path, "project instructions")
                path.rmdir()

    def test_workspace_directories_are_unknown(self):
        for name in sorted(AUDIT.WORKSPACES | {"project.code-workspace"}):
            with self.subTest(name=name):
                path = self.target / name
                path.mkdir()
                self.assert_unknown(AUDIT.audit(self.target), path, "workspace declaration")
                path.rmdir()

    def test_nested_conflicts_preserve_valid_sibling_evidence(self):
        root = self.target / "packages" / "web"
        root.mkdir(parents=True)
        (root / "package.json").write_text('{"scripts":{"test":"node --test"}}')
        path = root / "package-lock.json"
        path.mkdir()
        report = AUDIT.audit(self.target)
        self.assert_unknown(report, path, "dependency lock")
        gap = self.gap(report, "test command")
        self.assertEqual(gap["status"], "present")
        self.assertEqual(gap["evidence"], ["packages/web/package.json scripts.test: node --test"])

    def test_conflicting_directory_is_still_traversed_without_writes(self):
        path = self.target / "package.json"
        path.mkdir()
        manifest = path / "package.json"
        manifest.write_text('{"scripts":{"test":"node --test"}}')
        sentinel = path / "keep.txt"
        sentinel.write_bytes(b"preserve this content\x00")
        before = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        report = AUDIT.audit(self.target)
        self.assertFalse(report["complete_inventory"])
        self.assertIn(f"Skipped non-regular evidence file: {path}", report["notes"])
        self.assertEqual(self.gap(report, "project manifest")["evidence"], ["package.json/package.json"])
        self.assertEqual(self.gap(report, "test command")["status"], "present")
        after = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_regular_evidence_and_ordinary_directories_remain_complete(self):
        (self.target / "package.json").write_text('{"scripts":{"test":"node --test"}}')
        (self.target / "package-lock.json").write_text('{}')
        (self.target / "AGENTS.md").write_text('Fixture instructions')
        (self.target / "project.code-workspace").write_text('{}')
        for name in ("src", "scripts", ".github/workflows", "README-examples", "ruff"):
            (self.target / name).mkdir(parents=True)
        report = AUDIT.audit(self.target)
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(report["notes"], [])
        for area in ("project manifest", "dependency lock", "project instructions", "workspace declaration", "test command"):
            with self.subTest(area=area):
                self.assertEqual(self.gap(report, area)["status"], "present")

    def test_excluded_generated_directories_remain_excluded(self):
        path = self.target / "node_modules" / "package.json"
        path.mkdir(parents=True)
        report = AUDIT.audit(self.target)
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(report["notes"], [])
        self.assertEqual(self.gap(report, "project manifest")["status"], "missing")

    def test_cli_serializes_unknown_directory_without_changing_it(self):
        path = self.target / "uv.lock"
        path.mkdir()
        sentinel = path / "keep.txt"
        sentinel.write_bytes(b"do not replace")
        result = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")), str(self.target), "--audit"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_unknown(json.loads(result.stdout), path, "dependency lock")
        self.assertEqual(sentinel.read_bytes(), b"do not replace")


if __name__ == "__main__":
    unittest.main()
