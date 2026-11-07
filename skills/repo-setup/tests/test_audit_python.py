"""Read-only Python declaration checks; never execute or import audited code."""
import builtins
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit.py"
SPEC = importlib.util.spec_from_file_location("audit_python", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)
HAS_TOMLLIB = importlib.util.find_spec("tomllib") is not None


@unittest.skipUnless(HAS_TOMLLIB, "TOML parsing requires Python 3.11+")
class PythonAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-python-audit-")
        self.target = Path(self.tmp.name) / "project"
        self.target.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def report(self, source):
        (self.target / "pyproject.toml").write_text(source, encoding="utf-8")
        return AUDIT.audit(self.target)

    def manifest(self, report):
        return next(x for x in report["inventory"] if x["path"] == "pyproject.toml")

    def gap(self, report, area="workspace declaration"):
        return next(x for x in report["gaps"] if x["area"] == area)

    def test_invalid_workspace_containers_are_not_evidence(self):
        for value in ['"packages/*"', 'false', '42', '[]', '["packages/*"]']:
            with self.subTest(value=value):
                r = self.report(f"[tool.uv]\nworkspace = {value}\n")
                self.assertFalse(r["complete_inventory"])
                self.assertIsNone(self.manifest(r)["uv_workspace"])
                self.assertTrue(self.manifest(r)["errors"])
                self.assertEqual(self.gap(r)["status"], "not verified")
                self.assertEqual(self.gap(r)["evidence"], [])

    def test_invalid_workspace_patterns_are_not_evidence(self):
        for key in ["members", "exclude"]:
            for value in ['"packages/*"', 'false', '42', '{}', '[false]', '[42]', '[""]', '["   "]', '[["packages/*"]]']:
                with self.subTest(key=key, value=value):
                    r = self.report(f"[tool.uv.workspace]\n{key} = {value}\n")
                    self.assertFalse(r["complete_inventory"])
                    self.assertIsNone(self.manifest(r)["uv_workspace"])
                    self.assertIn(f"tool.uv.workspace.{key}", self.manifest(r)["errors"][0])
                    self.assertEqual(self.gap(r)["evidence"], [])

    def test_valid_workspace_declarations_include_empty_tables_and_arrays(self):
        for source, expected in [
            ("[tool.uv.workspace]\n", {}),
            ("[tool.uv.workspace]\nmembers=[]\nexclude=[]\n", {"members": [], "exclude": []}),
            ('[tool.uv.workspace]\nmembers=["packages/*"]\nexclude=["packages/private"]\n',
             {"members": ["packages/*"], "exclude": ["packages/private"]}),
        ]:
            with self.subTest(source=source):
                r = self.report(source)
                self.assertTrue(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["uv_workspace"], expected)
                self.assertEqual(self.gap(r)["status"], "present")
                self.assertEqual(self.gap(r)["evidence"], ["pyproject.toml"])

    def test_absent_workspace_is_not_invented(self):
        for source in ["", "[tool]\n", "[tool.uv]\n", "[project]\n"]:
            with self.subTest(source=source):
                r = self.report(source)
                self.assertTrue(r["complete_inventory"])
                self.assertIsNone(self.manifest(r)["uv_workspace"])
                self.assertEqual(self.gap(r)["status"], "not applicable")

    def test_unknown_workspace_fields_are_not_copied_or_validated(self):
        unknown = 'future=2026-11-07\nwhen=12:00:00\nnested={timestamp=2026-11-07T12:00:00Z}\ncustom="uninterpreted"\n'
        for known, expected in [("", {}), ('members=["packages/*"]\nexclude=[]\n', {"members": ["packages/*"], "exclude": []})]:
            with self.subTest(known=known):
                source = '[project.scripts]\ncli="app:main"\n[tool.uv.workspace]\n' + known + unknown
                r = self.report(source)
                self.assertTrue(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["uv_workspace"], expected)
                self.assertEqual(self.manifest(r)["project_scripts"], {"cli": "app:main"})
                self.assertEqual(self.gap(r)["status"], "present")
                json.dumps(r)
                cli = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")), str(self.target), "--audit"],
                                     capture_output=True, text=True, check=False)
                self.assertEqual(cli.returncode, 0, cli.stderr)
                self.assertEqual(self.manifest(json.loads(cli.stdout))["uv_workspace"], expected)

    def test_invalid_project_preserves_valid_workspace(self):
        for value in ['false', '"bad"', '[]', '42']:
            with self.subTest(value=value):
                r = self.report(f"project={value}\n[tool.uv.workspace]\n")
                self.assertFalse(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["project_scripts"], {})
                self.assertEqual(self.manifest(r)["tool_sections"], ["uv"])
                self.assertEqual(self.gap(r)["status"], "present")

    def test_invalid_tool_containers_preserve_valid_scripts(self):
        for value in ['false', '"bad"', '[]', '42']:
            with self.subTest(value=value):
                r = self.report(f'tool={value}\n[project.scripts]\ncli="app:main"\n')
                self.assertFalse(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["project_scripts"], {"cli": "app:main"})
                self.assertEqual(self.manifest(r)["tool_sections"], [])
                self.assertIsNone(self.manifest(r)["uv_workspace"])

    def test_invalid_uv_container_does_not_hide_other_tool_names(self):
        for value in ['false', '"bad"', '[]', '42']:
            with self.subTest(value=value):
                r = self.report(f"[tool]\nuv={value}\n[tool.ruff]\n")
                self.assertFalse(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["tool_sections"], ["ruff", "uv"])
                self.assertIsNone(self.manifest(r)["uv_workspace"])
                self.assertEqual(self.gap(r)["status"], "not verified")

    def test_invalid_scripts_containers_are_not_inventory_evidence(self):
        for value in ['false', '"bad"', '[]', '42']:
            with self.subTest(value=value):
                r = self.report(f"[project]\nscripts={value}\n[tool.uv.workspace]\n")
                self.assertFalse(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["project_scripts"], {})
                self.assertEqual(self.gap(r)["status"], "present")

    def test_invalid_script_entries_preserve_valid_siblings(self):
        for value in ['false', '42', '[]', '{}', '""', '"   "']:
            with self.subTest(value=value):
                r = self.report(f'[project.scripts]\nbad={value}\ncli="app:main"\n')
                self.assertFalse(r["complete_inventory"])
                self.assertEqual(self.manifest(r)["project_scripts"], {"cli": "app:main"})
                self.assertIn("project.scripts.bad", self.manifest(r)["errors"][0])

    def test_blank_script_names_are_rejected(self):
        r = self.report('[project.scripts]\n""="app:main"\n" "="app:main"\ncli="app:main"\n')
        self.assertFalse(r["complete_inventory"])
        self.assertEqual(self.manifest(r)["project_scripts"], {"cli": "app:main"})
        self.assertEqual(len(self.manifest(r)["errors"]), 2)

    def test_entry_points_do_not_claim_runtime_or_test_commands(self):
        r = self.report('[project.scripts]\ntest="does_not_exist:main"\ncli="app:main"\n[tool.ruff]\n[tool.uv.workspace]\nmembers=["missing/*"]\n')
        self.assertTrue(r["complete_inventory"])
        self.assertEqual(self.manifest(r)["project_scripts"], {"test": "does_not_exist:main", "cli": "app:main"})
        self.assertEqual(self.gap(r, "test command")["status"], "not verified")
        self.assertEqual(self.gap(r, "command correctness / clean install / runtime behavior")["status"], "not verified")
        self.assertEqual(self.gap(r)["status"], "present")

    def test_invalid_workspace_preserves_scripts_and_other_package_evidence(self):
        (self.target / "package.json").write_text('{"scripts":{"test":"node --test"}}')
        r = self.report('[project.scripts]\ncli="app:main"\n[tool.uv.workspace]\nmembers=false\nexclude=42\n')
        self.assertFalse(r["complete_inventory"])
        self.assertEqual(len(self.manifest(r)["errors"]), 2)
        self.assertEqual(self.manifest(r)["project_scripts"], {"cli": "app:main"})
        self.assertEqual(self.gap(r, "test command")["status"], "present")

    def test_invalid_toml_and_oversized_manifests_remain_partial(self):
        for source in ['[project', '#'+('x'*AUDIT.MAX_BYTES)]:
            with self.subTest(source=source[:20]):
                r = self.report(source)
                self.assertFalse(r["complete_inventory"])
                self.assertIn("error", self.manifest(r))

    def test_cli_returns_partial_json_without_mutating_or_running_project(self):
        source = '[project.scripts]\ncli="trap:main"\nbad=false\n[tool.uv]\nworkspace="packages/*"\n'
        self.report(source)
        (self.target / "trap.py").write_text('raise AssertionError("Project imported")\n')
        (self.target / ".env").write_text("PRIVATE=do-not-read-fixture\n")
        before = {p.name: p.read_bytes() for p in self.target.iterdir()}
        r = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")), str(self.target), "--audit"],
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout)["complete_inventory"])
        self.assertNotIn("do-not-read-fixture", r.stdout)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.target.iterdir()})

    def test_missing_tomllib_keeps_explicit_unverified_fallback(self):
        original = builtins.__import__
        def without_tomllib(name, *args, **kwargs):
            if name == "tomllib":
                raise ImportError("Simulated Python 3.10")
            return original(name, *args, **kwargs)
        with patch("builtins.__import__", without_tomllib):
            r = self.report("[tool.uv.workspace]\n")
        self.assertFalse(r["complete_inventory"])
        self.assertIn("Python 3.11+", self.manifest(r)["parse_status"])
        self.assertEqual(self.gap(r)["status"], "not verified")


if __name__ == "__main__":
    unittest.main()
