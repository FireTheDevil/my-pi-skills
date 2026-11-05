#!/usr/bin/env python3
"""Check scaffolds offline, or exercise approved baseline installs and real checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ["typescript-web", "python-cli"]
PREVIEWS = ["react-web", "fastapi", "bun-monorepo"]
IGNORED = {"node_modules", ".git", ".venv", "dist", "build", ".pytest_cache", ".ruff_cache", ".ty_cache", "__pycache__"}


def execute(command, cwd, fail=False, stage=""):
    print("$ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env["UV_PYTHON_DOWNLOADS"] = "never"
    env["UV_PROJECT_ENVIRONMENT"] = str(Path(cwd) / ".venv")
    result = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    print(result.stdout, end="", flush=True)
    if (not fail and result.returncode != 0) or (fail and result.returncode == 0):
        raise RuntimeError(f"Unexpected status {result.returncode}: {command}")
    if fail and stage and stage not in result.stdout:
        raise RuntimeError(f"Negative fixture failed before expected stage {stage!r}")
    return result.stdout


def snapshot(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob("*")
            if p.is_file() and not set(p.relative_to(path).parts).intersection(IGNORED)}


def verify_recipe(recipe, workspace):
    target = workspace / recipe
    bootstrap = [sys.executable, str(ROOT / "scripts/bootstrap.py"), str(target), "--recipe", recipe]
    execute(bootstrap, workspace)
    if target.exists():
        raise RuntimeError("Dry run wrote files")
    execute([*bootstrap, "--apply", "--install", "--approve-install", "--verify", "--git"], workspace)
    before = snapshot(target)
    execute([*bootstrap, "--apply", "--git"], workspace)
    if before != snapshot(target):
        raise RuntimeError("Second setup changed repository files")
    if execute(["git", "remote", "-v"], target).strip():
        raise RuntimeError("Unexpected Git remote")
    clean = workspace / (recipe + "-clean")
    shutil.copytree(target, clean, ignore=shutil.ignore_patterns(*IGNORED))
    if recipe == "typescript-web":
        install = ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"]
        check = ["npm", "run", "check"]
        formatter = ["npm", "run", "format"]
        smoke = ["npm", "run", "smoke"]
        fixtures = [
            ("lint", "src/counter.ts", lambda s: s + "\ndebugger;\n", "oxlint"),
            ("type", "src/counter.ts", lambda s: s + '\nexport const wrong: number = "wrong";\n', "tsc --noEmit"),
            ("test", "src/counter.test.ts", lambda s: s.replace('toBe("0 clicks")', 'toBe("incorrect")'), "vitest run"),
        ]
        format_path, format_bad = "src/style.css", "\nbody{color:red}\n"
    else:
        install = ["uv", "sync", "--locked"]
        check = ["uv", "run", "--locked", "python", "scripts/check.py"]
        formatter = ["uv", "run", "--locked", "ruff", "format", "."]
        smoke = ["uv", "run", "--locked", "app", "Developer"]
        fixtures = [
            ("lint", "src/app/__init__.py", lambda s: s + "\nimport os\n", "ruff check"),
            ("type", "src/app/__init__.py", lambda s: s + '\nWRONG: int = "wrong"\n', "ty check"),
            ("test", "tests/test_app.py", lambda s: s.replace('== "Hello, Ada!"', '== "incorrect"'), "pytest"),
        ]
        format_path, format_bad = "src/app/__init__.py", "\nFORMAT_ME= 1\n"
    execute(install, clean)
    execute(check, clean)
    execute(smoke, clean)
    if snapshot(clean) != before:
        raise RuntimeError("Locked install/check changed committed files")
    path = clean / format_path
    original = path.read_text()
    try:
        path.write_text(original + format_bad)
        execute(check, clean, fail=True)
    finally:
        path.write_text(original)
    for label, relative, mutate, stage in fixtures:
        path = clean / relative
        original = path.read_text()
        try:
            path.write_text(mutate(original))
            execute(formatter, clean)
            execute(check, clean, fail=True, stage=stage)
            print(f"PASS: {recipe} aggregate rejects {label} defect", flush=True)
        finally:
            path.write_text(original)
    execute(check, clean)
    execute(smoke, clean)
    if snapshot(clean) != before:
        raise RuntimeError("Restored fixtures changed committed files")
    if recipe == "python-cli":
        execute(["uv", "build", "--out-dir", str(workspace / "python-dist")], clean)
    return {"recipe": recipe, "fresh_setup": "passed", "clean_locked_install": "passed", "rerun": "byte-identical", "negative_checks": ["format", "lint", "type", "test"], "startup": "passed"}


def verify_scaffold(recipe, workspace):
    target = workspace / recipe
    command = [sys.executable, str(ROOT / "scripts/bootstrap.py"), str(target), "--recipe", recipe]
    execute(command, workspace)
    if target.exists():
        raise RuntimeError("Dry run wrote files")
    execute([*command, "--apply"], workspace)
    before = snapshot(target)
    execute([*command, "--apply"], workspace)
    if before != snapshot(target):
        raise RuntimeError("Rerun changed scaffold")
    readme = target / "README.md"
    readme.write_text("Preserve my edited README\n")
    removed = target / ".editorconfig"
    removed.unlink()
    execute([*command, "--apply"], workspace)
    if readme.read_text() != "Preserve my edited README\n" or not removed.is_file():
        raise RuntimeError("Edit preservation or partial recovery failed")
    return {"recipe": recipe, "dry_run": "read-only", "scaffold": "passed",
            "rerun": "byte-identical", "edited_files": "preserved",
            "missing_files": "recreated", "install_checks_startup": "not verified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", choices=["all", *BASELINES, *PREVIEWS], default="all")
    parser.add_argument("--approve-install", action="store_true", help="Explicit user approval for integration dependency activity")
    parser.add_argument("--scaffold-only", action="store_true", help="Offline file-generation/rerun checks only; no runtime readiness claim")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    recipes = BASELINES + PREVIEWS if args.recipe == "all" else [args.recipe]
    if not args.scaffold_only:
        if not args.approve_install:
            parser.error("Integration requires --approve-install after explicit user approval; use --scaffold-only offline")
        if any(recipe in PREVIEWS for recipe in recipes):
            parser.error("Preview integration blocked: reviewed locks and approved clean installs are pending. Select a baseline or --scaffold-only")
    try:
        with tempfile.TemporaryDirectory(prefix="repo-setup-integration-") as tmp:
            results = [verify_scaffold(recipe, Path(tmp)) if args.scaffold_only else verify_recipe(recipe, Path(tmp)) for recipe in recipes]
        report = {"status": "scaffold-only passed; runtime not verified" if args.scaffold_only else "passed", "results": results}
        if args.report:
            args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, RuntimeError) as error:
        print(f"VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
