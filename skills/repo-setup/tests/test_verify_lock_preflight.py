"""Preview verification must not scaffold without an existing regular lock.

All locks here are deliberately inert fixtures, not reviewed dependency locks.
Tool shims record calls and never install dependencies or run project commands.
"""
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
SPEC = importlib.util.spec_from_file_location("bootstrap_locks", SCRIPT)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)
PREVIEW_LOCKS = {"react-web": "bun.lock", "bun-monorepo": "bun.lock", "fastapi": "uv.lock"}


class VerificationLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-locks-")
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls.jsonl"
        for name, version in [("node", "v24.22.1"), ("bun", "1.3.11"), ("uv", sys.executable)]:
            tool = self.bin / name
            tool.write_text(
                f"#!{sys.executable}\n"
                "import json, pathlib, sys\n"
                f"with pathlib.Path({str(self.calls)!r}).open('a') as log:\n"
                f"    log.write(json.dumps([{name!r}, *sys.argv[1:]]) + '\\n')\n"
                f"if sys.argv[1:] == ['--version'] or ({name!r} == 'uv' and sys.argv[1:3] == ['python', 'find']):\n"
                f"    print({version!r})\n"
                "    sys.exit(0)\n"
                "print('Verification shim reached; no project command executed', file=sys.stderr)\n"
                "sys.exit(91)\n"
            )
            tool.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_setup(self, recipe, *flags):
        env = {**os.environ, "PATH": str(self.bin)}
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root / recipe),
                               "--recipe", recipe, *flags], env=env, text=True,
                              capture_output=True, check=False, timeout=10)

    def scaffold(self, recipe):
        result = self.run_setup(recipe, "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.root / recipe

    def calls_recorded(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def assert_no_project_commands(self):
        for call in self.calls_recorded():
            self.assertTrue(call == ["node", "--version"] or call[:3] == ["uv", "python", "find"], call)

    def snapshot(self, target):
        return {str(p.relative_to(target)): p.read_bytes() for p in target.rglob("*")
                if p.is_file() and not p.is_symlink()}

    def test_missing_preview_lock_refuses_new_directory_before_writes(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertFalse((self.root / recipe).exists())
        self.assert_no_project_commands()

    def test_missing_preview_lock_keeps_existing_empty_directory_empty(self):
        for recipe in PREVIEW_LOCKS:
            with self.subTest(recipe=recipe):
                target = self.root / recipe
                target.mkdir()
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(target.iterdir()), [])
        self.assert_no_project_commands()

    def test_missing_preview_lock_prevents_git_initialization(self):
        for recipe in PREVIEW_LOCKS:
            with self.subTest(recipe=recipe):
                target = self.root / recipe
                argv = [str(SCRIPT), str(target), "--recipe", recipe, "--apply", "--verify", "--git"]
                with patch.object(sys, "argv", argv), patch.object(BOOTSTRAP, "preflight"), patch.object(BOOTSTRAP, "git_initialization_needed") as git_check, patch.object(BOOTSTRAP, "run") as run:
                    self.assertEqual(BOOTSTRAP.main(), 1)
                    git_check.assert_not_called()
                    run.assert_not_called()
                self.assertFalse(target.exists())

    def test_missing_preview_lock_does_not_restore_rerun_files(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                (target / "README.md").unlink()
                (target / ".editorconfig").write_text("Keep my edit\n")
                before = self.snapshot(target)
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertEqual(self.snapshot(target), before)
        self.assert_no_project_commands()

    def test_symlink_preview_locks_are_refused_without_following_or_writes(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                external = self.root / (recipe + "-external-lock")
                external.write_text("External fixture, not a reviewed lock\n")
                (target / lock).symlink_to(external)
                (target / "README.md").unlink()
                before = self.snapshot(target)
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertEqual(self.snapshot(target), before)
                self.assertEqual(external.read_text(), "External fixture, not a reviewed lock\n")
                self.assertTrue((target / lock).is_symlink())
        self.assert_no_project_commands()

    def test_dangling_preview_locks_are_refused_before_writes(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                (target / lock).symlink_to(self.root / "missing-lock")
                (target / "README.md").unlink()
                before = self.snapshot(target)
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertEqual(self.snapshot(target), before)
        self.assert_no_project_commands()

    def test_directory_preview_locks_are_refused_before_writes(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                (target / lock).mkdir()
                (target / "README.md").unlink()
                before = self.snapshot(target)
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertEqual(self.snapshot(target), before)
                self.assertTrue((target / lock).is_dir())
        self.assert_no_project_commands()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO support required")
    def test_special_preview_locks_are_refused_before_writes(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                os.mkfifo(target / lock)
                (target / "README.md").unlink()
                before = self.snapshot(target)
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(lock, result.stderr)
                self.assertEqual(self.snapshot(target), before)
        self.assert_no_project_commands()

    def test_regular_preview_locks_preserve_recovery_and_reach_existing_verifier(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                (target / lock).write_text("Inert lock fixture; no dependency-resolution claim\n")
                (target / "README.md").unlink()
                (target / ".editorconfig").write_text("Keep my edit\n")
                result = self.run_setup(recipe, "--apply", "--verify")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Verification shim reached", result.stderr)
                self.assertTrue((target / "README.md").is_file())
                self.assertEqual((target / ".editorconfig").read_text(), "Keep my edit\n")
                self.assertEqual((target / lock).read_text(), "Inert lock fixture; no dependency-resolution claim\n")

    def test_lock_is_rechecked_after_scaffold_before_project_command(self):
        for recipe, lock in PREVIEW_LOCKS.items():
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                (target / lock).write_text("Inert lock fixture\n")
                original_apply = BOOTSTRAP.apply
                def remove_lock_after_apply(*args):
                    original_apply(*args)
                    (target / lock).unlink()
                argv = [str(SCRIPT), str(target), "--recipe", recipe, "--apply", "--verify"]
                with patch.object(sys, "argv", argv), patch.object(BOOTSTRAP, "preflight"), patch.object(BOOTSTRAP, "apply", side_effect=remove_lock_after_apply), patch.object(BOOTSTRAP, "run") as run:
                    self.assertEqual(BOOTSTRAP.main(), 1)
                    run.assert_not_called()

    def test_bundled_baseline_locks_remain_recoverable(self):
        for recipe, lock in [("typescript-web", "package-lock.json"), ("python-cli", "uv.lock")]:
            with self.subTest(recipe=recipe):
                target = self.scaffold(recipe)
                expected = (target / lock).read_bytes()
                (target / lock).unlink()
                argv = [str(SCRIPT), str(target), "--recipe", recipe, "--apply", "--verify"]
                with patch.object(sys, "argv", argv), patch.object(BOOTSTRAP, "preflight"), patch.object(BOOTSTRAP, "run") as run:
                    self.assertEqual(BOOTSTRAP.main(), 0)
                    self.assertTrue(run.called)
                self.assertEqual((target / lock).read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
