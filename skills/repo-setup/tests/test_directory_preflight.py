"""Reject blocked scaffold directories before planning writes or running tools."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_directory", SCRIPT)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)


class DirectoryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-directory-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "demo"

    def tearDown(self):
        self.tmp.cleanup()

    def setup_command(self, recipe, *flags):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.target), "--recipe", recipe, *flags],
            text=True, capture_output=True, timeout=5, check=False,
        )

    def scaffold(self, recipe):
        result = self.setup_command(recipe, "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)

    def snapshot(self):
        result = {}
        for path in [self.root, *self.root.rglob("*")]:
            st = path.lstat()
            result[str(path.relative_to(self.root))] = (
                st.st_mode, st.st_ino, st.st_size, st.st_mtime_ns,
                path.read_bytes() if path.is_file() and not path.is_symlink() else None,
                str(path.readlink()) if path.is_symlink() else None,
            )
        return result

    def block_directory(self, relative):
        path = self.target / relative
        shutil.rmtree(path)
        path.write_text("Keep this file.\n")
        (self.target / ".gitignore").unlink()
        (self.target / "README.md").write_text("Keep my edits.\n")

    def assert_rejected(self, recipe, error):
        before = self.snapshot()
        for flags in ((), ("--apply",)):
            with self.subTest(flags=flags):
                result = self.setup_command(recipe, *flags)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(error, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn("CREATE", result.stdout)
                self.assertEqual(self.snapshot(), before)

    def test_top_level_conflict_rejects_dry_run_and_apply_for_every_recipe(self):
        for recipe in BOOTSTRAP.RECIPES:
            with self.subTest(recipe=recipe):
                self.scaffold(recipe)
                self.block_directory("scripts")
                self.assert_rejected(recipe, "Expected a directory:")
                shutil.rmtree(self.target)

    def test_nested_conflicts_reject_dry_run_and_apply(self):
        for relative in ("apps/web", "apps/web/src", "packages/shared/src"):
            with self.subTest(relative=relative):
                self.scaffold("bun-monorepo")
                self.block_directory(relative)
                self.assert_rejected("bun-monorepo", "Expected a directory:")
                shutil.rmtree(self.target)

    def test_new_target_with_file_ancestor_is_rejected(self):
        blocker = self.root / "blocker"
        blocker.write_text("Keep ancestor.\n")
        for relative in ("demo", "missing/demo"):
            with self.subTest(relative=relative):
                self.target = blocker / relative
                self.assert_rejected("python-cli", "Expected a directory:")

    def test_conflicts_stop_before_apply_runtime_commands_and_git(self):
        self.scaffold("python-cli")
        self.block_directory("scripts")
        before = self.snapshot()
        args = [str(SCRIPT), str(self.target), "--recipe", "python-cli", "--apply",
                "--install", "--approve-install", "--verify", "--git"]
        with patch.object(sys, "argv", args), \
                patch.object(BOOTSTRAP, "preflight") as preflight, \
                patch.object(BOOTSTRAP, "git_initialization_needed") as git, \
                patch.object(BOOTSTRAP, "apply") as apply, \
                patch.object(BOOTSTRAP, "run") as run, \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(BOOTSTRAP.main(), 1)
        for mock in (preflight, git, apply, run):
            mock.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_missing_directories_recover_and_edits_and_state_survive(self):
        for recipe in BOOTSTRAP.RECIPES:
            with self.subTest(recipe=recipe):
                self.scaffold(recipe)
                files = BOOTSTRAP.templates(recipe, "demo")
                state = (self.target / BOOTSTRAP.STATE).read_bytes()
                missing = "apps/web" if recipe == "bun-monorepo" else "scripts"
                shutil.rmtree(self.target / missing)
                (self.target / "README.md").write_text("Keep my edits.\n")
                before = self.snapshot()
                result = self.setup_command(recipe)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("CREATE", result.stdout)
                self.assertIn("KEEP EDITED", result.stdout)
                self.assertEqual(self.snapshot(), before)
                self.scaffold(recipe)
                for relative, data in files.items():
                    if relative.startswith(missing + "/"):
                        self.assertEqual((self.target / relative).read_bytes(), data)
                self.assertEqual((self.target / "README.md").read_text(), "Keep my edits.\n")
                self.assertEqual((self.target / BOOTSTRAP.STATE).read_bytes(), state)
                shutil.rmtree(self.target)

    def test_directory_symlink_remains_rejected(self):
        self.scaffold("python-cli")
        outside = self.root / "outside"
        (self.target / "scripts").rename(outside)
        (self.target / "scripts").symlink_to(outside, target_is_directory=True)
        (self.target / ".gitignore").unlink()
        self.assert_rejected("python-cli", "Refusing symlink:")

    def test_file_symlink_remains_rejected(self):
        self.scaffold("python-cli")
        outside = self.root / "outside.txt"
        (self.target / "README.md").rename(outside)
        (self.target / "README.md").symlink_to(outside)
        (self.target / ".gitignore").unlink()
        self.assert_rejected("python-cli", "Refusing symlink:")

    def test_directory_at_file_destination_remains_rejected(self):
        self.scaffold("python-cli")
        (self.target / "README.md").unlink()
        (self.target / "README.md").mkdir()
        self.assert_rejected("python-cli", "Expected a file:")


if __name__ == "__main__":
    unittest.main()
