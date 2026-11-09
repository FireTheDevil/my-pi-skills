"""Recipe prerequisites fail before writing; no registry access or installations."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_preflight", SCRIPT)
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOTSTRAP)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-preflight-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "demo"
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def tool(self, name, output, code=0):
        executable = self.bin / name
        executable.write_text(
            f"#!{sys.executable}\n"
            "import json, pathlib, sys\n"
            f"with pathlib.Path({str(self.calls)!r}).open('a') as log:\n"
            f"    log.write(json.dumps([{name!r}, *sys.argv[1:]]) + '\\n')\n"
            f"if sys.argv[1:] == ['--version'] or ({name!r} == 'uv' and 'find' in sys.argv):\n"
            f"    print({output!r})\n"
            f"    sys.exit({code})\n"
            "print('Unexpected install/verify call', file=sys.stderr)\n"
            "sys.exit(91)\n"
        )
        executable.chmod(0o755)

    def setup_command(self, recipe, *flags):
        env = os.environ.copy()
        env["PATH"] = str(self.bin)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.target), "--recipe", recipe, *flags],
            text=True, capture_output=True, env=env, check=False,
        )

    def recorded_calls(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_incompatible_npm_fails_before_new_project_writes(self):
        self.tool("node", "v24.22.1")
        self.tool("npm", "10.9.4")
        result = self.setup_command("typescript-web", "--apply", "--install", "--approve-install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("npm 11.x", result.stderr)
        self.assertFalse(self.target.exists())
        self.assertNotIn(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], self.recorded_calls())

    def test_incompatible_npm_does_not_restore_missing_rerun_files(self):
        self.assertEqual(self.setup_command("typescript-web", "--apply").returncode, 0)
        (self.target / "README.md").unlink()
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.tool("node", "v24.22.1")
        self.tool("npm", "12.0.0")
        result = self.setup_command("typescript-web", "--apply", "--verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("npm 11.x", result.stderr)
        self.assertEqual(before, {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()})

    def test_missing_python_fails_before_new_project_writes(self):
        self.tool("uv", "No interpreter found for Python 3.12", code=2)
        result = self.setup_command("python-cli", "--apply", "--install", "--approve-install")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.12", result.stderr)
        self.assertFalse(self.target.exists())
        self.assertFalse(any(call[1:2] in (["sync"], ["run"]) for call in self.recorded_calls()))

    def test_missing_python_does_not_restore_missing_rerun_files(self):
        self.assertEqual(self.setup_command("python-cli", "--apply").returncode, 0)
        (self.target / "README.md").unlink()
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.tool("uv", "No interpreter found for Python 3.12", code=2)
        result = self.setup_command("python-cli", "--apply", "--verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.12", result.stderr)
        self.assertEqual(before, {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()})

    def test_scaffold_without_install_or_verify_does_not_need_tools(self):
        for recipe in BOOTSTRAP.RECIPES:
            with patch.object(BOOTSTRAP.shutil, "which", return_value=None), patch.object(BOOTSTRAP.subprocess, "check_output") as probe:
                BOOTSTRAP.preflight(recipe, False, False, False)
                probe.assert_not_called()

    def test_dry_run_without_tools_does_not_probe_or_write(self):
        for recipe in BOOTSTRAP.RECIPES:
            result = self.setup_command(recipe)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(self.target.exists())
            self.assertEqual(self.recorded_calls(), [])

    def test_accepts_declared_npm_series_for_install_and_verify(self):
        for install, verify in [(True, False), (False, True), (True, True)]:
            with patch.object(BOOTSTRAP.shutil, "which", return_value="/tool"), patch.object(BOOTSTRAP.subprocess, "check_output", side_effect=["v24.22.1\n", "11.9.0\n"]) as probe:
                BOOTSTRAP.preflight("typescript-web", install, verify, False)
                self.assertEqual([c.args[0] for c in probe.call_args_list], [["node", "--version"], ["npm", "--version"]])

    def test_rejects_malformed_or_unsupported_npm_versions(self):
        for version in ["10.9.4", "12.0.0", "11", "v11.9.0", "11.9.0-beta.1", "warning\n11.9.0", ""]:
            with self.subTest(version=version), patch.object(BOOTSTRAP.shutil, "which", return_value="/tool"), patch.object(BOOTSTRAP.subprocess, "check_output", side_effect=["v24.22.1", version]):
                with self.assertRaisesRegex(BOOTSTRAP.SetupError, "npm 11.x"):
                    BOOTSTRAP.preflight("typescript-web", True, False, False)

    def test_python_probe_is_explicit_offline_and_cannot_download(self):
        with patch.object(BOOTSTRAP.shutil, "which", return_value="/tool"), patch.object(BOOTSTRAP.subprocess, "check_output", return_value="/usr/bin/python3.12\n") as probe:
            BOOTSTRAP.preflight("python-cli", True, False, False)
            command = probe.call_args.args[0]
            self.assertEqual(command[:3], ["uv", "python", "find"])
            for option in ("--no-project", "--no-config", "--system", "--no-python-downloads", "--offline", "--no-cache", "3.12"):
                self.assertIn(option, command)

    def test_missing_tool_stops_before_probe(self):
        for recipe in BOOTSTRAP.RECIPES:
            with patch.object(BOOTSTRAP.shutil, "which", return_value=None), patch.object(BOOTSTRAP.subprocess, "check_output") as probe:
                with self.assertRaisesRegex(BOOTSTRAP.SetupError, "Required tool missing"):
                    BOOTSTRAP.preflight(recipe, True, False, False)
                probe.assert_not_called()

    def test_bun_previews_do_not_require_or_probe_npm(self):
        for recipe in ("react-web", "bun-monorepo"):
            with self.subTest(recipe=recipe), patch.object(BOOTSTRAP.shutil, "which", return_value="/tool") as which, patch.object(BOOTSTRAP.subprocess, "check_output", return_value="v24.22.1\n") as probe:
                BOOTSTRAP.preflight(recipe, False, True, False)
                self.assertEqual([call.args[0] for call in which.call_args_list], ["bun", "node"])
                self.assertEqual([call.args[0] for call in probe.call_args_list], [["node", "--version"]])

    def test_fastapi_missing_python_fails_before_verification_writes(self):
        self.tool("uv", "No interpreter found for Python 3.12", code=2)
        result = self.setup_command("fastapi", "--apply", "--verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.12", result.stderr)
        self.assertFalse(self.target.exists())
        self.assertEqual(len(self.recorded_calls()), 1)
        self.assertEqual(self.recorded_calls()[0][:3], ["uv", "python", "find"])

    def test_fastapi_missing_python_preserves_missing_rerun_files(self):
        self.assertEqual(self.setup_command("fastapi", "--apply").returncode, 0)
        (self.target / "README.md").unlink()
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.tool("uv", "No interpreter found for Python 3.12", code=2)
        result = self.setup_command("fastapi", "--apply", "--verify")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Python 3.12", result.stderr)
        self.assertEqual(before, {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()})

    def test_install_without_approval_stops_before_probing_or_writing(self):
        for recipe in BOOTSTRAP.RECIPES:
            with self.subTest(recipe=recipe):
                result = self.setup_command(recipe, "--apply", "--install")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("requires --approve-install", result.stderr)
                self.assertFalse(self.target.exists())
                self.assertEqual(self.recorded_calls(), [])

    def test_preview_install_with_approval_still_stops_before_probing(self):
        for recipe in BOOTSTRAP.PREVIEWS:
            with self.subTest(recipe=recipe):
                result = self.setup_command(recipe, "--apply", "--install", "--approve-install")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Preview has no reviewed lock", result.stderr)
                self.assertFalse(self.target.exists())
                self.assertEqual(self.recorded_calls(), [])

    @unittest.skipUnless(shutil.which("uv"), "uv is required for caller-config integration")
    def test_python_probe_ignores_unrelated_caller_config(self):
        command = ["uv", "python", "find", "--no-project", "--no-config", "--system",
                   "--no-python-downloads", "--offline", "--no-cache", "3.12"]
        available = subprocess.run(command, text=True, capture_output=True, check=False)
        if available.returncode:
            self.skipTest("An installed Python 3.12 is required for caller-config integration")
        cwd = Path.cwd()
        try:
            os.chdir(self.root)
            for content in ['python-preference = "only-managed"\n', 'invalid TOML [\n']:
                with self.subTest(config=content):
                    (self.root / "uv.toml").write_text(content)
                    BOOTSTRAP.preflight("python-cli", True, False, False)
                    self.assertFalse(self.target.exists())
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
