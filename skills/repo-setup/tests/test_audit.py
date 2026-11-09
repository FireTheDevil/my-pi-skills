"""Read-only audit regression tests. No project commands or dependencies run."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/audit.py"
SPEC = importlib.util.spec_from_file_location("audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="repo-setup-audit-")
        self.root = Path(self.tmp.name)
        self.target = self.root / "project"
        self.target.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def package(self, data, path="package.json"):
        return self.write(path, json.dumps(data))

    def report(self):
        return AUDIT.audit(self.target)

    def gap(self, report, area):
        return next(x for x in report["gaps"] if x["area"] == area)

    def manifest(self, report, path="package.json"):
        return next(x for x in report["inventory"] if x["path"] == path)

    def test_non_string_and_empty_commands_are_not_present(self):
        for value in [None, False, True, 0, 3.5, [], {}, ["pytest"], "", " \t\n"]:
            with self.subTest(value=value):
                self.package({"scripts": {"test": value}})
                report = self.report()
                self.assertFalse(report["complete_inventory"])
                self.assertEqual(self.manifest(report)["scripts"], {})
                self.assertTrue(self.manifest(report)["errors"])
                self.assertEqual(self.gap(report, "test command")["status"], "not verified")
                self.assertEqual(self.gap(report, "test command")["evidence"], [])

    def test_valid_sibling_commands_survive_invalid_entries(self):
        self.package({"scripts": {"test": False, "lint": "oxlint .", "build": {}}})
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertEqual(self.manifest(report)["scripts"], {"lint": "oxlint ."})
        self.assertEqual(len(self.manifest(report)["errors"]), 2)
        self.assertEqual(self.gap(report, "lint command")["status"], "present")
        self.assertEqual(self.gap(report, "build command")["status"], "not verified")

    def test_blank_script_names_mark_inventory_incomplete(self):
        self.package({"scripts": {" ": "echo hi", "": "echo hi", "test": "node --test"}})
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertEqual(self.manifest(report)["scripts"], {"test": "node --test"})
        self.assertEqual(self.gap(report, "test command")["status"], "present")

    def test_invalid_scripts_containers_are_not_present(self):
        for value in [None, False, 1, "test", [], ["test"]]:
            with self.subTest(value=value):
                self.package({"scripts": value, "workspaces": ["packages/*"]})
                report = self.report()
                self.assertFalse(report["complete_inventory"])
                self.assertEqual(self.gap(report, "test command")["status"], "not verified")
                self.assertEqual(self.gap(report, "workspace declaration")["status"], "present")

    def test_valid_commands_are_declaration_evidence_only(self):
        commands = {"format:check": "prettier --check .", "lint": "oxlint .",
                    "typecheck": "tsc --noEmit", "test": "node --test",
                    "build": "vite build", "dev": "vite"}
        self.package({"scripts": commands})
        report = self.report()
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(self.manifest(report)["scripts"], commands)
        for area in ["format command", "lint command", "type command", "test command", "build command", "startup command"]:
            self.assertEqual(self.gap(report, area)["status"], "present")
        self.assertEqual(self.gap(report, "command correctness / clean install / runtime behavior")["status"], "not verified")

    def test_absent_scripts_are_missing_not_invalid(self):
        for data in [{}, {"scripts": {}}]:
            with self.subTest(data=data):
                self.package(data)
                report = self.report()
                self.assertTrue(report["complete_inventory"])
                self.assertEqual(self.gap(report, "test command")["status"], "missing")

    def test_invalid_workspace_shapes_are_not_present(self):
        for value in [None, False, 1, "packages/*", {}, {"packages": "packages/*"},
                      {"packages": [None]}, [1], [False], [""], ["   "], [["packages/*"]]]:
            with self.subTest(value=value):
                self.package({"workspaces": value, "scripts": {"test": "node --test"}})
                report = self.report()
                self.assertFalse(report["complete_inventory"])
                self.assertIsNone(self.manifest(report)["workspaces"])
                self.assertEqual(self.gap(report, "workspace declaration")["status"], "not verified")
                self.assertEqual(self.gap(report, "test command")["status"], "present")

    def test_workspace_arrays_and_yarn_objects_preserve_declarations(self):
        for value in [["packages/*"], [], {"packages": ["packages/*"], "nohoist": ["**/example"]}, {"packages": []}]:
            with self.subTest(value=value):
                self.package({"workspaces": value})
                report = self.report()
                self.assertTrue(report["complete_inventory"])
                self.assertEqual(self.manifest(report)["workspaces"], value)
                self.assertEqual(self.gap(report, "workspace declaration")["status"], "present")

    def test_invalid_manifest_does_not_hide_other_package_evidence(self):
        self.package({"scripts": {"test": False}}, "packages/broken/package.json")
        self.package({"scripts": {"test": "node --test"}}, "packages/valid/package.json")
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertEqual(self.gap(report, "test command")["evidence"],
                         ["packages/valid/package.json scripts.test: node --test"])

    def test_manifest_parse_errors_are_partial_reports(self):
        for content in ["{", "[]", "null", "false", '"not an object"']:
            with self.subTest(content=content):
                self.write("package.json", content)
                report = self.report()
                self.assertFalse(report["complete_inventory"])
                self.assertIn("error", self.manifest(report))
                self.assertEqual(self.gap(report, "test command")["status"], "not verified")

    def test_oversized_manifest_is_not_parsed(self):
        path = self.package({"scripts": {"test": "x" * AUDIT.MAX_BYTES}})
        original = Path.read_text
        def guarded_read(candidate, *args, **kwargs):
            self.assertNotEqual(candidate, path, "Oversized manifest was read")
            return original(candidate, *args, **kwargs)
        with patch.object(Path, "read_text", guarded_read):
            report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertIn("read limit", self.manifest(report)["error"])

    def test_invalid_utf8_manifest_is_partial(self):
        (self.target / "package.json").write_bytes(b"\xff")
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertIn("error", self.manifest(report))

    def test_symlink_files_and_directories_are_not_followed(self):
        external = self.root / "external"
        external.mkdir()
        (external / "package.json").write_text('{"scripts":{"test":"external-secret-command"}}')
        (self.target / "package.json").symlink_to(external / "package.json")
        (self.target / "linked").symlink_to(external, target_is_directory=True)
        report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertNotIn("external-secret-command", json.dumps(report))
        self.assertEqual(self.gap(report, "test command")["evidence"], [])

    def test_generated_directories_are_not_inventory_sources(self):
        for directory in AUDIT.SKIP:
            self.package({"scripts": {"test": "ignored-command"}}, f"{directory}/package.json")
        report = self.report()
        self.assertTrue(report["complete_inventory"])
        self.assertNotIn("ignored-command", json.dumps(report))

    def test_truncation_avoids_missing_claims(self):
        self.write("a.txt", "first")
        self.package({"scripts": {"test": "node --test"}})
        with patch.object(AUDIT, "LIMIT", 1):
            report = self.report()
        self.assertFalse(report["complete_inventory"])
        self.assertEqual(self.gap(report, "test command")["status"], "not verified")
        self.assertTrue(any("truncated" in note for note in report["notes"]))

    def test_ancestor_commands_do_not_fill_local_gaps(self):
        (self.root / "package.json").write_text('{"scripts":{"test":"ancestor-command"}}')
        (self.root / "AGENTS.md").write_text("Read-only fixture")
        report = self.report()
        self.assertTrue(report["complete_inventory"])
        self.assertEqual(self.gap(report, "test command")["status"], "missing")
        self.assertEqual(self.gap(report, "project instructions")["status"], "present")

    def test_cli_is_read_only_and_does_not_execute_project_code(self):
        marker = self.target / "executed.txt"
        dangerous = f'{sys.executable} -c "from pathlib import Path; Path(\'{marker}\').touch()"'
        self.package({"scripts": {"test": dangerous, "postinstall": dangerous}})
        self.write("setup.py", f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        self.write(".env", "SECRET=must-not-appear-in-report\n")
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        result = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")), str(self.target), "--audit"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["complete_inventory"])
        self.assertFalse(marker.exists())
        self.assertNotIn("must-not-appear-in-report", result.stdout)
        after = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_cli_returns_partial_report_for_invalid_declarations(self):
        self.package({"scripts": {"test": False}, "workspaces": "packages/*"})
        result = subprocess.run([sys.executable, str(SCRIPT.with_name("bootstrap.py")), str(self.target), "--audit"],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["complete_inventory"])
        self.assertEqual(self.gap(report, "test command")["status"], "not verified")


if __name__ == "__main__":
    unittest.main()
