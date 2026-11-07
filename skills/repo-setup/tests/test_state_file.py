"""Reject non-regular setup state without reading it or changing a project."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_state_file", SCRIPT)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)


class StateFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-state-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "demo"
        self.target.mkdir()
        self.state = self.target / BOOTSTRAP.STATE

    def tearDown(self):
        self.tmp.cleanup()

    def run_setup(self, recipe="python-cli", *flags):
        # A regression must fail promptly rather than hanging the test suite on
        # a FIFO. subprocess.run kills and waits for the child after a timeout.
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.target), "--recipe", recipe, *flags],
            text=True, capture_output=True, check=False, timeout=5,
        )

    def snapshot(self):
        result = {}
        for path in self.target.rglob("*"):
            st = path.lstat()
            result[str(path.relative_to(self.target))] = (
                st.st_mode, st.st_ino, st.st_size, st.st_mtime_ns,
                path.read_bytes() if path.is_file() and not path.is_symlink() else None,
            )
        return result

    def assert_rejected(self, recipe="python-cli", *flags):
        before = self.snapshot()
        result = self.run_setup(recipe, *flags)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("Setup state must be a regular file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_fifo_is_rejected_by_dry_run_for_every_recipe(self):
        os.mkfifo(self.state)
        for recipe in BOOTSTRAP.RECIPES:
            with self.subTest(recipe=recipe):
                self.assert_rejected(recipe)

    def test_fifo_is_rejected_before_apply_for_every_recipe(self):
        os.mkfifo(self.state)
        for recipe in BOOTSTRAP.RECIPES:
            with self.subTest(recipe=recipe):
                self.assert_rejected(recipe, "--apply")

    def test_fifo_is_rejected_before_runtime_or_git_preflight(self):
        os.mkfifo(self.state)
        args = [str(SCRIPT), str(self.target), "--recipe", "python-cli",
                "--apply", "--install", "--approve-install", "--verify", "--git"]
        with patch.object(sys, "argv", args), \
                patch.object(Path, "read_text", side_effect=AssertionError("state read")) as read, \
                patch.object(BOOTSTRAP, "preflight") as preflight, \
                patch.object(BOOTSTRAP, "apply") as apply:
            self.assertEqual(BOOTSTRAP.main(), 1)
        read.assert_not_called()
        preflight.assert_not_called()
        apply.assert_not_called()
        self.assertEqual([p.name for p in self.target.iterdir()], [BOOTSTRAP.STATE])

    def test_fifo_preserves_edited_and_missing_rerun_files(self):
        result = self.run_setup("python-cli", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.target / "README.md").write_text("Keep my edits.\n")
        (self.target / "pyproject.toml").unlink()
        self.state.unlink()
        os.mkfifo(self.state)
        self.assert_rejected("python-cli", "--apply", "--git")
        self.assertFalse((self.target / "pyproject.toml").exists())
        self.assertFalse((self.target / ".git").exists())

    def test_directory_state_is_rejected_and_preserved(self):
        self.state.mkdir()
        (self.state / "keep.txt").write_text("Preserve unknown state.\n")
        self.assert_rejected("python-cli", "--apply")

    def test_symlink_state_remains_rejected_without_reading_destination(self):
        outside = self.root / "outside.json"
        outside.write_text("Preserve me.\n")
        self.state.symlink_to(outside)
        with patch.object(Path, "read_text", side_effect=AssertionError("state read")):
            with self.assertRaisesRegex(BOOTSTRAP.SetupError, "State file is a symlink"):
                BOOTSTRAP.load_state(self.target, "python-cli", "demo")
        self.assertEqual(outside.read_text(), "Preserve me.\n")
        self.assertTrue(self.state.is_symlink())

    def test_regular_state_still_allows_recovery_without_overwriting_edits(self):
        result = self.run_setup("python-cli", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        before_state = self.state.read_bytes()
        (self.target / "README.md").write_text("Keep my edits.\n")
        manifest = self.target / "pyproject.toml"
        before_manifest = manifest.read_bytes()
        manifest.unlink()
        result = self.run_setup("python-cli", "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.state.read_bytes(), before_state)
        self.assertEqual((self.target / "README.md").read_text(), "Keep my edits.\n")
        self.assertEqual(manifest.read_bytes(), before_manifest)

    def test_regular_state_still_requires_valid_json_and_recipe_identity(self):
        for content in ("{", "[]", json.dumps({"schema": 1, "recipe": "fastapi", "name": "demo", "version": "1.2.0-preview"})):
            with self.subTest(content=content):
                self.state.write_text(content)
                before = self.snapshot()
                result = self.run_setup("python-cli", "--apply")
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
