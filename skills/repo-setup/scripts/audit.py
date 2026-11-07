"""Bounded, read-only evidence inventory. Never imports or executes project code."""
from __future__ import annotations

import json
import os
from pathlib import Path

SKIP = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".next", ".cache"}
MANIFESTS = {"package.json", "pyproject.toml", "requirements.txt", "setup.cfg", "setup.py", "Cargo.toml", "go.mod"}
LOCKS = {"bun.lock", "bun.lockb", "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum"}
INSTRUCTIONS = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
WORKSPACES = {"pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json", "bunfig.toml"}
LIMIT = 10000
MAX_BYTES = 256000


def audit(raw: Path) -> dict:
    if ".." in raw.parts:
        raise ValueError("Audit target must not contain .. components")
    target = Path(os.path.abspath(raw.expanduser()))
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("Audit target path must not contain symlinks")
    if not target.is_dir():
        raise ValueError("Audit needs an existing directory")
    inventory = []
    scripts = {}
    notes = []
    count = 0
    incomplete = False

    def add(path: Path, kind: str) -> None:
        nonlocal incomplete
        if path.is_symlink():
            notes.append(f"Skipped symlink: {path}")
            incomplete = True
            return
        item = {"path": str(path.relative_to(target)) if path.is_relative_to(target) else str(path), "kind": kind}
        try:
            if not path.is_file():
                return
            item["bytes"] = path.stat().st_size
            if kind == "manifest" and path.name == "package.json":
                if item["bytes"] > MAX_BYTES:
                    raise ValueError("manifest exceeds read limit")
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("manifest is not an object")
                item["package_manager"] = data.get("packageManager")
                item["workspaces"] = None
                errors = []
                if "workspaces" in data:
                    workspaces = data["workspaces"]
                    # npm/Bun use an array; Yarn also supports {packages: [...]}.
                    patterns = workspaces.get("packages") if isinstance(workspaces, dict) else workspaces
                    if isinstance(patterns, list) and all(isinstance(p, str) and p.strip() for p in patterns):
                        item["workspaces"] = workspaces
                    else:
                        errors.append("workspaces must be an array of nonempty strings or an object with a packages array")
                commands = data.get("scripts", {})
                if not isinstance(commands, dict):
                    errors.append("scripts is not an object")
                    commands = {}
                valid_commands = {}
                for name, command in commands.items():
                    if not name.strip() or not isinstance(command, str) or not command.strip():
                        errors.append(f"scripts.{name} must have a nonempty name and string command")
                    else:
                        valid_commands[name] = command
                scripts[item["path"]] = valid_commands
                item["scripts"] = valid_commands
                if errors:
                    item["errors"] = errors
                    incomplete = True
            elif kind == "manifest" and path.name == "pyproject.toml":
                # tomllib is optional: helper remains usable with Python 3.10.
                try:
                    import tomllib
                except ImportError:
                    incomplete = True
                    item["parse_status"] = "not verified: Python 3.11+ required for TOML parsing"
                else:
                    if item["bytes"] > MAX_BYTES:
                        raise ValueError("manifest exceeds read limit")
                    data = tomllib.loads(path.read_text(encoding="utf-8"))
                    errors = []
                    project = data.get("project", {})
                    if not isinstance(project, dict):
                        errors.append("project must be a table")
                        project = {}
                    commands = project.get("scripts", {})
                    if not isinstance(commands, dict):
                        errors.append("project.scripts must be a table")
                        commands = {}
                    item["project_scripts"] = {}
                    for name, command in commands.items():
                        if not name.strip() or not isinstance(command, str) or not command.strip():
                            errors.append(f"project.scripts.{name} must have a nonempty name and string entry point")
                        else:
                            item["project_scripts"][name] = command
                    tool = data.get("tool", {})
                    if not isinstance(tool, dict):
                        errors.append("tool must be a table")
                        tool = {}
                    item["tool_sections"] = sorted(tool)
                    uv = tool.get("uv", {})
                    if not isinstance(uv, dict):
                        errors.append("tool.uv must be a table")
                        uv = {}
                    item["uv_workspace"] = None
                    if "workspace" in uv:
                        workspace = uv["workspace"]
                        workspace_errors = []
                        if not isinstance(workspace, dict):
                            workspace_errors.append("tool.uv.workspace must be a table")
                        else:
                            for key in ("members", "exclude"):
                                if key in workspace:
                                    patterns = workspace[key]
                                    if not isinstance(patterns, list) or not all(isinstance(p, str) and p.strip() for p in patterns):
                                        workspace_errors.append(f"tool.uv.workspace.{key} must be an array of nonempty strings")
                        if workspace_errors:
                            errors.extend(workspace_errors)
                        else:
                            # Inventory only the fields we understand. Other TOML
                            # values can include non-JSON dates/times and are not
                            # validated workspace evidence.
                            item["uv_workspace"] = {key: workspace[key] for key in ("members", "exclude") if key in workspace}
                    if errors:
                        item["errors"] = errors
                        incomplete = True
        except (OSError, ValueError, UnicodeError, AttributeError, TypeError) as exc:
            item["error"] = str(exc)
            incomplete = True
        inventory.append(item)

    # Ancestor instructions and workspace boundaries, without traversing outside target.
    for parent in reversed(target.parents):
        for name in sorted(INSTRUCTIONS | MANIFESTS | LOCKS | WORKSPACES):
            path = parent / name
            if path.exists() or path.is_symlink():
                add(path, "ancestor instruction" if name in INSTRUCTIONS else "ancestor project boundary")

    def walk_error(exc: OSError) -> None:
        nonlocal incomplete
        notes.append(str(exc))
        incomplete = True

    for root, dirs, files in os.walk(target, followlinks=False, onerror=walk_error):
        base = Path(root)
        kept = []
        for directory in sorted(dirs):
            if (base / directory).is_symlink():
                notes.append(f"Skipped symlink directory: {base / directory}")
                incomplete = True
            elif directory not in SKIP:
                kept.append(directory)
        dirs[:] = kept
        for name in sorted(files):
            count += 1
            if count > LIMIT:
                incomplete = True
                notes.append(f"Inventory truncated at {LIMIT} files")
                break
            path = base / name
            relative = path.relative_to(target)
            if name in INSTRUCTIONS:
                add(path, "instruction")
            elif name in MANIFESTS:
                add(path, "manifest")
            elif name in LOCKS:
                add(path, "lock")
            elif name in WORKSPACES or name.endswith(".code-workspace"):
                add(path, "workspace")
            elif (".github" in relative.parts and "workflows" in relative.parts) or name in {".gitlab-ci.yml", "Jenkinsfile", ".circleci/config.yml"} or (".circleci" in relative.parts and name == "config.yml"):
                add(path, "CI")
            elif name.startswith(("README", ".prettier", ".oxlint", "eslint", ".eslintrc", "vite.config", "tsconfig", "ruff", "pytest", ".python-version", ".node-version")) or name in {"Makefile", "justfile", "tox.ini", ".editorconfig"} or (relative.parts[0] == "scripts" and path.suffix in {".py", ".sh", ".mjs", ".ts"}):
                add(path, "configuration / command evidence")
        if count > LIMIT:
            break

    local = [x for x in inventory if not x["kind"].startswith("ancestor")]
    gaps = []

    def gap(area: str, evidence: list[str], proposal: str, applicable: bool = True) -> None:
        status = "present" if evidence else "not verified" if incomplete else "not applicable" if not applicable else "missing"
        gaps.append({"area": area, "status": status, "evidence": evidence,
                     "proposal": "Complete skipped/truncated inventory before proposing additions" if incomplete and not evidence else proposal if not evidence and applicable else "Review existing evidence; preserve choices" if evidence else "No addition proposed"})

    gap("project manifest", [x["path"] for x in local if x["kind"] == "manifest"], "Identify the project and add only its appropriate manifest")
    gap("dependency lock", [x["path"] for x in local if x["kind"] == "lock"], "Ask approval to resolve a lock with the existing package manager", any(x["kind"] == "manifest" for x in local))
    gap("project instructions", [x["path"] for x in inventory if "instruction" in x["kind"]], "Document existing run/check conventions")
    gap("workspace declaration", [x["path"] for x in local if x["kind"] == "workspace" or x.get("workspaces") is not None or x.get("uv_workspace") is not None], "Confirm whether discovered package roots should share a workspace before adding one", len({str(Path(x["path"]).parent) for x in local if x["kind"] == "manifest"}) > 1)
    gap("CI configuration", [x["path"] for x in local if x["kind"] == "CI"], "Ask whether CI is wanted before choosing a provider")
    for label, names in {
        "format command": {"format", "format:check"},
        "lint command": {"lint"},
        "type command": {"typecheck", "types"},
        "test command": {"test"},
        "build command": {"build"},
        "startup command": {"dev", "start", "serve"},
    }.items():
        evidence = [f"{path} scripts.{key}: {value}" for path, commands in scripts.items() for key, value in commands.items() if key in names]
        # Python tool configuration is evidence, not proof of an executable command.
        python = [x["path"] for x in local if x["path"].endswith("pyproject.toml")]
        if not evidence and python:
            gaps.append({"area": label, "status": "not verified", "evidence": python,
                         "proposal": "Read Python tool configuration, README and check scripts to identify the smallest missing command"})
        else:
            gap(label, evidence, "Inspect existing configuration and README before proposing a command")
    gaps.append({"area": "command correctness / clean install / runtime behavior", "status": "not verified",
                 "evidence": [], "proposal": "Review commands first; obtain approval before dependencies, then run focused checks"})
    return {"target": str(target), "mode": "read-only; no project scripts, Git hooks, imports or package managers executed",
            "limits": {"max_files": LIMIT, "max_manifest_bytes": MAX_BYTES, "excluded_directories": sorted(SKIP)},
            "complete_inventory": not incomplete, "inventory": inventory, "gaps": gaps, "notes": notes,
            "interpretation": "Present means a file or declared command exists, not that it works. Missing means absent from this bounded inventory, not absent functionality. Review referenced instructions and scripts; custom commands may cover gaps."}
