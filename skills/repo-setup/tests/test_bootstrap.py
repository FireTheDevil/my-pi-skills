"""Filesystem safety and rerun tests. No dependency installation or network."""
import json
import importlib.util
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap.py"
SPEC = importlib.util.spec_from_file_location("bootstrap", SCRIPT)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)
VERIFY_SPEC = importlib.util.spec_from_file_location("verify", SCRIPT.with_name("verify.py"))
VERIFY = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-unit-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "demo"

    def tearDown(self):
        self.tmp.cleanup()

    def run_setup(self, *args, recipe="python-cli", target=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(target or self.target), "--recipe", recipe, *args],
            capture_output=True, text=True, check=False,
        )

    def scaffold(self, **kwargs):
        result = self.run_setup("--apply", **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def snapshot(self):
        return {str(p.relative_to(self.target)): p.read_bytes()
                for p in self.target.rglob("*") if p.is_file()}

    def test_empty_git_directory_recovers_after_interrupted_init(self):
        self.scaffold()
        (self.target / ".git").mkdir()
        result = self.run_setup("--apply", "--git")
        self.assertEqual(result.returncode, 0, result.stderr)
        git = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=self.target,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(git.returncode, 0, git.stderr)
        self.assertEqual(Path(git.stdout.strip()).resolve(), self.target.resolve())

    def test_invalid_git_directory_is_refused_before_file_creation(self):
        self.scaffold()
        (self.target / ".git").mkdir()
        (self.target / ".git/config").write_text("# preserve this partial configuration\n")
        (self.target / "README.md").unlink()
        before = self.snapshot()
        result = self.run_setup("--apply", "--git")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git metadata", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_git_file_is_refused_before_file_creation(self):
        self.scaffold()
        (self.target / ".git").write_text("gitdir: missing-git-directory\n")
        (self.target / "README.md").unlink()
        before = self.snapshot()
        result = self.run_setup("--apply", "--git")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git metadata", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_valid_git_repository_is_unchanged_on_rerun(self):
        self.scaffold()
        result = self.run_setup("--apply", "--git")
        self.assertEqual(result.returncode, 0, result.stderr)
        before = self.snapshot()
        result = self.run_setup("--apply", "--git")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_valid_linked_git_worktree_is_preserved(self):
        self.scaffold()
        origin = self.root / "origin"
        worktree = self.root / "linked"
        subprocess.run(["git", "init", "--initial-branch=main", "--template=", str(origin)], check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "test"], cwd=origin, check=True, capture_output=True)
        subprocess.run(["git", "worktree", "add", "--detach", str(worktree)], cwd=origin, check=True, capture_output=True)
        shutil.copytree(self.target, worktree, dirs_exist_ok=True)
        before = {str(p.relative_to(worktree)): p.read_bytes() for p in worktree.rglob("*") if p.is_file()}
        result = self.run_setup("--apply", "--git", "--name", "demo", target=worktree)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((worktree / ".git").is_file())
        self.assertEqual(before, {str(p.relative_to(worktree)): p.read_bytes() for p in worktree.rglob("*") if p.is_file()})

    def test_git_init_success_without_metadata_is_not_reported_complete(self):
        args = [str(SCRIPT), str(self.target), "--recipe", "python-cli", "--apply", "--git"]
        with patch.object(sys, "argv", args), patch.object(BOOTSTRAP, "run") as run:
            self.assertEqual(BOOTSTRAP.main(), 1)
        run.assert_called_once_with(["git", "init", "--initial-branch=main", "--template="], self.target)
        self.assertTrue((self.target / "README.md").is_file())
        self.assertFalse((self.target / ".git").exists())

    def test_invalid_git_metadata_preserves_preview_rerun_files(self):
        for recipe in BOOTSTRAP.PREVIEWS:
            with self.subTest(recipe=recipe):
                self.target = self.root / recipe
                self.scaffold(recipe=recipe)
                (self.target / ".git").write_text("gitdir: missing-git-directory\n")
                (self.target / "README.md").unlink()
                before = self.snapshot()
                result = self.run_setup("--apply", "--git", recipe=recipe)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Git metadata", result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_refuses_git_environment_redirection(self):
        foreign = self.root / "foreign-git"
        with patch.dict(os.environ, {"GIT_DIR": str(foreign)}):
            result = self.run_setup("--apply", "--git")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())
        self.assertFalse(foreign.exists())

    def test_git_init_ignores_inherited_hooks_template(self):
        template = self.root / "git-template"
        (template / "hooks").mkdir(parents=True)
        hook = template / "hooks/post-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        with patch.dict(os.environ, {"GIT_TEMPLATE_DIR": str(template)}):
            result = self.run_setup("--apply", "--git")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / ".git/HEAD").is_file())
        self.assertFalse((self.target / ".git/hooks/post-commit").exists())

    def test_rejects_dotdot_before_path_normalization(self):
        real = self.root / "other/deep"
        real.mkdir(parents=True)
        (self.root / "alias").symlink_to(real, target_is_directory=True)
        result = self.run_setup("--apply", target=self.root / "alias/../demo")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not contain ..", result.stderr)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.root / "other/demo").exists())

    def test_rejects_external_runtime_directory(self):
        self.scaffold()
        outside = self.root / "outside-venv"
        outside.mkdir()
        (self.target / ".venv").symlink_to(outside, target_is_directory=True)
        result = self.run_setup("--apply", "--install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("runtime or Git", result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_rechecks_directory_links_during_apply(self):
        self.target.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        files = {"nested/file.txt": b"content"}
        plan = BOOTSTRAP.plan_files(self.target, files)
        (self.target / "nested").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            BOOTSTRAP.apply(self.target, "python-cli", "demo", files, plan, {})
        self.assertEqual(list(outside.iterdir()), [])

    def test_state_publication_failure_can_resume(self):
        files = {"README.md": b"content"}
        plan = BOOTSTRAP.plan_files(self.target, files)
        with patch.object(BOOTSTRAP.os, "link", side_effect=OSError("simulated interruption")):
            with self.assertRaises(OSError):
                BOOTSTRAP.apply(self.target, "python-cli", "demo", files, plan, None)
        self.assertFalse((self.target / ".repo-setup.json").exists())
        self.assertEqual(list(self.target.iterdir()), [])
        BOOTSTRAP.apply(self.target, "python-cli", "demo", files, plan, None)
        self.assertEqual(json.loads((self.target / ".repo-setup.json").read_text())["name"], "demo")

    def test_verifier_environment_is_disposable(self):
        completed = subprocess.CompletedProcess([], 0, stdout="")
        with patch.dict(os.environ, {"UV_PROJECT_ENVIRONMENT": str(self.root / "foreign")}):
            with patch.object(VERIFY.subprocess, "run", return_value=completed) as call:
                VERIFY.execute(["uv", "sync", "--locked"], self.target)
        self.assertEqual(call.call_args.kwargs["env"]["UV_PROJECT_ENVIRONMENT"], str(self.target / ".venv"))

    def test_uv_install_environment_is_local(self):
        completed = subprocess.CompletedProcess([], 0)
        with patch.dict(os.environ, {"UV_PROJECT_ENVIRONMENT": str(self.root / "foreign")}):
            with patch.object(BOOTSTRAP.subprocess, "run", return_value=completed) as call:
                BOOTSTRAP.run(["uv", "sync", "--locked"], self.target)
        self.assertEqual(call.call_args.kwargs["env"]["UV_PROJECT_ENVIRONMENT"], str(self.target / ".venv"))

    def test_rejects_unreviewed_file_in_assets(self):
        skill = self.root / "skill"
        (skill / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, skill / "scripts/bootstrap.py")
        assets = skill / "assets/python-cli"
        assets.mkdir(parents=True)
        (assets / "README.md").write_text("reviewed")
        (assets / ".env").write_text("UNEXPECTED=content")
        (skill / "assets/template-files.json").write_text(json.dumps({"python-cli": ["README.md"]}))
        result = subprocess.run(
            [sys.executable, str(skill / "scripts/bootstrap.py"), str(self.target), "--recipe", "python-cli", "--apply"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("reviewed manifest", result.stderr)
        self.assertFalse(self.target.exists())

    def test_rejects_generated_artifact_in_assets(self):
        skill = self.root / "skill"
        (skill / "scripts").mkdir(parents=True)
        shutil.copy2(SCRIPT, skill / "scripts/bootstrap.py")
        assets = skill / "assets/python-cli/node_modules"
        assets.mkdir(parents=True)
        (assets / "vendor.js").write_text("generated dependency")
        result = subprocess.run(
            [sys.executable, str(skill / "scripts/bootstrap.py"), str(self.target), "--recipe", "python-cli", "--apply"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Generated dependency", result.stderr)
        self.assertFalse(self.target.exists())

    def test_typescript_scaffolds_without_preview_flag(self):
        result = self.run_setup("--apply", recipe="typescript-web")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.target / "package-lock.json").is_file())

    def test_typescript_lock_matches_project_name_and_exact_dependencies(self):
        self.scaffold(recipe="typescript-web")
        package = json.loads((self.target / "package.json").read_text())
        lock = json.loads((self.target / "package-lock.json").read_text())
        self.assertEqual(package["name"], "demo")
        self.assertEqual(lock["name"], "demo")
        self.assertEqual(lock["packages"][""]["name"], "demo")
        self.assertEqual(lock["packages"][""]["devDependencies"], package["devDependencies"])

    def test_dry_run_creates_nothing(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY RUN", result.stdout)
        self.assertFalse(self.target.exists())

    def test_both_recipes_scaffold(self):
        for recipe in ("typescript-web", "python-cli"):
            target = self.root / recipe
            self.scaffold(recipe=recipe, target=target)
            self.assertTrue((target / "README.md").is_file())
            self.assertTrue((target / ".repo-setup.json").is_file())
            self.assertIn(recipe, (target / ".repo-setup.json").read_text())

    def test_second_run_is_byte_identical(self):
        self.scaffold()
        before = self.snapshot()
        result = self.scaffold()
        self.assertEqual(before, self.snapshot())
        self.assertNotIn("CREATE", result.stdout)

    def test_preserves_user_edits_and_extras(self):
        self.scaffold()
        (self.target / "README.md").write_text("My own edited README\n")
        (self.target / "my-work.txt").write_text("Keep this\n")
        before = self.snapshot()
        result = self.scaffold()
        self.assertEqual(before, self.snapshot())
        self.assertIn("KEEP EDITED", result.stdout)

    def test_recovers_missing_files_after_partial_setup(self):
        self.scaffold()
        (self.target / "README.md").unlink()
        (self.target / "src/app/__init__.py").write_text("# user work\n")
        result = self.scaffold()
        self.assertIn("CREATE       README.md", result.stdout)
        self.assertEqual((self.target / "src/app/__init__.py").read_text(), "# user work\n")

    def test_nonempty_unrecognized_directory_is_unchanged(self):
        self.target.mkdir()
        (self.target / "README.md").write_text("Existing repository")
        before = self.snapshot()
        result = self.run_setup("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, self.snapshot())
        self.assertIn("Nonempty", result.stderr)

    def test_existing_git_repository_is_unchanged(self):
        self.target.mkdir()
        (self.target / ".git").mkdir()
        (self.target / ".git/config").write_text("[core]\n")
        before = self.snapshot()
        self.assertNotEqual(self.run_setup("--apply", "--git").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_refuses_parent_repository(self):
        (self.root / ".git").mkdir()
        (self.root / ".git/HEAD").write_text("ref: refs/heads/main\n")
        result = self.run_setup("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_refuses_parent_workspace(self):
        (self.root / "package.json").write_text('{"private":true}')
        result = self.run_setup("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_refuses_symlink_target(self):
        real = self.root / "real"
        real.mkdir()
        self.target.symlink_to(real, target_is_directory=True)
        result = self.run_setup("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(real.iterdir()), [])

    def test_refuses_symlink_generated_file(self):
        self.scaffold()
        readme = self.target / "README.md"
        readme.unlink()
        outside = self.root / "outside"
        outside.write_text("Untouched")
        readme.symlink_to(outside)
        self.assertNotEqual(self.run_setup("--apply").returncode, 0)
        self.assertEqual(outside.read_text(), "Untouched")

    def test_refuses_symlink_state(self):
        self.target.mkdir()
        outside = self.root / "outside"
        outside.write_text("{}")
        (self.target / ".repo-setup.json").symlink_to(outside)
        self.assertNotEqual(self.run_setup("--apply").returncode, 0)
        self.assertEqual(outside.read_text(), "{}")

    def test_refuses_recipe_or_name_change(self):
        self.scaffold()
        before = self.snapshot()
        self.assertNotEqual(self.run_setup("--apply", recipe="typescript-web").returncode, 0)
        self.assertNotEqual(self.run_setup("--apply", "--name", "renamed").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_refuses_unknown_revision(self):
        self.scaffold()
        path = self.target / ".repo-setup.json"
        state = json.loads(path.read_text())
        state["version"] = "future"
        path.write_text(json.dumps(state))
        before = self.snapshot()
        self.assertNotEqual(self.run_setup("--apply").returncode, 0)
        self.assertEqual(before, self.snapshot())

    def test_rejects_invalid_name_without_writing(self):
        result = self.run_setup("--apply", "--name", "../oops")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.target.exists())

    def test_side_effect_flags_require_apply(self):
        for flag in ("--install", "--verify", "--git"):
            self.assertNotEqual(self.run_setup(flag).returncode, 0)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
