"""Special-file audit evidence stays unknown, without opening or changing it."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit.py"
SPEC = importlib.util.spec_from_file_location("audit_special_files", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


@unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX/WSL file-type checks")
class SpecialFileAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-audit-special-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "project"
        self.target.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def fifo(self, name):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(path)
        return path

    def report(self):
        return AUDIT.audit(self.target)

    def gap(self, report, area):
        return next(item for item in report["gaps"] if item["area"] == area)

    def assert_unknown(self, report, path, area):
        self.assertFalse(report["complete_inventory"])
        self.assertIn(f"Skipped non-regular evidence file: {path}", report["notes"])
        self.assertNotIn(str(path.relative_to(self.target)) if path.is_relative_to(self.target)
                         else str(path), [item["path"] for item in report["inventory"]])
        gap = self.gap(report, area)
        self.assertEqual(gap["status"], "not verified")
        self.assertEqual(gap["evidence"], [])
        self.assertEqual(gap["proposal"], "Complete skipped/truncated inventory before proposing additions")

    def test_fifo_manifests_are_unknown_without_reads(self):
        for name in ("package.json", "pyproject.toml"):
            with self.subTest(name=name):
                path = self.fifo(name)
                with patch.object(Path, "read_text", side_effect=AssertionError("Evidence was opened")):
                    report = self.report()
                self.assert_unknown(report, path, "project manifest")
                self.assertTrue(stat.S_ISFIFO(path.lstat().st_mode))
                path.unlink()

    def test_fifo_lock_does_not_recommend_resolving_a_new_lock(self):
        (self.target / "package.json").write_text('{}', encoding="utf-8")
        path = self.fifo("package-lock.json")
        report = self.report()
        self.assert_unknown(report, path, "dependency lock")
        self.assertEqual(self.gap(report, "project manifest")["status"], "present")

    def test_other_recognized_fifo_evidence_is_reported(self):
        for name, area in (("AGENTS.md", "project instructions"),
                           ("pnpm-workspace.yaml", "workspace declaration"),
                           (".github/workflows/check.yml", "CI configuration"),
                           ("scripts/check.py", "test command"),
                           ("README.md", "startup command")):
            with self.subTest(name=name):
                path = self.fifo(name)
                self.assert_unknown(self.report(), path, area)
                path.unlink()

    @unittest.skipUnless(hasattr(os, "mknod"), "POSIX socket-mode fixture")
    def test_socket_mode_entry_is_not_regular_manifest_evidence(self):
        path = self.target / "package.json"
        # Inert filesystem fixture only; no socket is opened, bound or listened on.
        os.mknod(path, stat.S_IFSOCK | 0o600)
        report = self.report()
        self.assert_unknown(report, path, "project manifest")
        self.assertTrue(stat.S_ISSOCK(path.lstat().st_mode))

    def test_ancestor_special_evidence_makes_inventory_partial(self):
        path = self.root / "AGENTS.md"
        os.mkfifo(path)
        self.assert_unknown(self.report(), path, "project instructions")
        self.assertTrue(stat.S_ISFIFO(path.lstat().st_mode))

    def test_valid_sibling_commands_remain_visible(self):
        path = self.fifo("packages/broken/package.json")
        (self.target / "package.json").write_text('{"scripts":{"test":"node --test"}}', encoding="utf-8")
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertIn(f"Skipped non-regular evidence file: {path}", report["notes"])
        self.assertEqual(self.gap(report, "test command")["status"], "present")
        self.assertEqual(self.gap(report, "test command")["evidence"], ["package.json scripts.test: node --test"])
        self.assertEqual(self.gap(report, "lint command")["status"], "not verified")

    def test_generated_and_unrecognized_special_files_stay_out_of_scope(self):
        self.fifo("node_modules/package.json")
        self.fifo("unrelated.pipe")
        report = self.report()
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(report["notes"], [])
        self.assertEqual(report["inventory"], [])

    def test_regular_evidence_is_unchanged(self):
        (self.target / "package.json").write_text('{}', encoding="utf-8")
        (self.target / "package-lock.json").write_text('{}', encoding="utf-8")
        report = self.report()
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(report["notes"], [])
        self.assertEqual(self.gap(report, "project manifest")["status"], "present")
        self.assertEqual(self.gap(report, "dependency lock")["status"], "present")
        self.assertEqual(self.gap(report, "test command")["status"], "missing")

    def test_cli_returns_partial_json_without_reading_or_writing_fifo(self):
        path = self.fifo("package.json")
        before = path.lstat()
        result = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")),
                                 str(self.target), "--audit"], capture_output=True,
                                text=True, check=False, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assert_unknown(json.loads(result.stdout), path, "project manifest")
        after = path.lstat()
        self.assertEqual((before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns),
                         (after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns))
        self.assertEqual(list(self.target.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
