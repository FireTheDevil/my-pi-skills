#!/usr/bin/env python3
"""Plan, safely scaffold, or read-only audit repository setup. Standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

VERSION = "1.1.0"
ROOT = Path(__file__).resolve().parents[1]
STATE = ".repo-setup.json"
PREVIEWS = ("react-web", "fastapi", "bun-monorepo")
RECIPES = ("typescript-web", "python-cli", *PREVIEWS)
GENERATED = {"node_modules", ".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".ty_cache", "dist", "build"}


def revision(recipe: str) -> str:
    return "1.2.0-preview" if recipe in PREVIEWS else VERSION


class SetupError(Exception):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str], target: Path, *, offline: bool = False) -> None:
    print("$ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env["UV_PYTHON_DOWNLOADS"] = "never"
    env["BUN_CONFIG_NO_AUTO_INSTALL"] = "1"
    if offline:
        env["UV_NO_SYNC"] = "1"
        env["UV_OFFLINE"] = "1"
    env["UV_PROJECT_ENVIRONMENT"] = str(target / ".venv")
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(key, None)
    result = subprocess.run(command, cwd=target, env=env, check=False)
    if result.returncode:
        raise SetupError(f"Command failed ({result.returncode}); generated files preserved. Rerun after fixing the cause.")


def check_path(target: Path) -> None:
    # Never follow directory or file symlinks while writing a scaffold.
    for path in (target, *target.parents):
        if path.is_symlink():
            raise SetupError(f"Symlink in target path: {path}")
    for generated in (".venv", "node_modules", ".git"):
        if (target / generated).is_symlink():
            raise SetupError(f"Refusing external/symlink runtime or Git directory: {target / generated}")
    if target.exists() and not target.is_dir():
        raise SetupError(f"Target is not a directory: {target}")
    for parent in target.parents:
        marker = parent / ".git"
        if marker.is_file() or (marker.is_dir() and any(marker.iterdir())):
            raise SetupError(f"Target is inside a parent Git repository ({parent}); use an independent directory or an explicit project-specific setup.")
        if any((parent / name).exists() for name in ("pnpm-workspace.yaml", "package.json", "pyproject.toml", "uv.lock")):
            raise SetupError(f"Parent workspace/project detected at {parent}; this new-project helper does not alter workspaces.")


def load_state(target: Path, recipe: str, name: str) -> dict | None:
    state_path = target / STATE
    if state_path.is_symlink():
        raise SetupError("State file is a symlink")
    if not state_path.exists():
        if target.exists() and any(target.iterdir()):
            raise SetupError("Nonempty unrecognized directory. Inspect it and report gaps; do not scaffold or overwrite it.")
        return None
    try:
        state = json.loads(state_path.read_text())
    except (OSError, ValueError) as exc:
        raise SetupError(f"Unreadable setup state: {exc}") from exc
    if not isinstance(state, dict) or state.get("schema") != 1:
        raise SetupError("Unrecognized setup state")
    if (state.get("recipe"), state.get("name"), state.get("version")) != (recipe, name, revision(recipe)):
        raise SetupError("Recipe, name, or revision differs from recorded setup. Automatic upgrades are not supported.")
    return state


def templates(recipe: str, name: str) -> dict[str, bytes]:
    result = {}
    for path in sorted((ROOT / "assets" / recipe).rglob("*")):
        if set(path.relative_to(ROOT / "assets" / recipe).parts).intersection(GENERATED) or path.suffix == ".pyc":
            raise SetupError(f"Generated dependency/cache/build artifact in template: {path}; use a clean skill bundle")
        if path.is_symlink():
            raise SetupError(f"Template symlink is not supported: {path}")
        if path.is_file():
            result[path.relative_to(ROOT / "assets" / recipe).as_posix()] = path.read_bytes().replace(b"__PROJECT_NAME__", name.encode())
    expected = json.loads((ROOT / "assets/template-files.json").read_text())[recipe]
    if set(result) != set(expected):
        raise SetupError(f"Template file list differs from the reviewed manifest for {recipe}; do not scaffold unreviewed files")
    if not result:
        raise SetupError(f"Missing recipe assets: {recipe}")
    return result


def plan_files(target: Path, files: dict[str, bytes]) -> list[tuple[str, str]]:
    plan = []
    for relative, data in files.items():
        path = target / relative
        for component in (path, *path.parents):
            if component == target.parent:
                break
            if component.is_symlink():
                raise SetupError(f"Refusing symlink: {component}")
        if path.exists():
            if not path.is_file():
                raise SetupError(f"Expected a file: {path}")
            action = "UNCHANGED" if path.read_bytes() == data else "KEEP EDITED"
        else:
            action = "CREATE"
        plan.append((action, relative))
    return plan


def preflight(recipe: str, install: bool, verify: bool, git: bool) -> None:
    git_redirects = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"}
    if git and any(key in os.environ for key in git_redirects):
        raise SetupError("Git repository-selection environment overrides are set; clear them before setup. Nothing was written.")
    required = (["npm", "node"] if recipe == "typescript-web" else ["bun", "node"] if recipe in ("react-web", "bun-monorepo") else ["uv"]) if install or verify else []
    if git:
        required.append("git")
    for tool in required:
        if not shutil.which(tool):
            raise SetupError(f"Required tool missing: {tool}. Install it separately from its official source; nothing was written.")
    if (install or verify) and recipe in ("typescript-web", "react-web", "bun-monorepo"):
        version = subprocess.check_output(["node", "--version"], text=True).strip()
        if not re.fullmatch(r"v24\.\d+\.\d+", version):
            raise SetupError(f"This recipe requires Node 24.x, found {version}. Select Node 24 before installing.")

    if (install or verify) and recipe == "typescript-web":
        version = subprocess.check_output(["npm", "--version"], text=True).strip()
        if not re.fullmatch(r"11\.\d+\.\d+", version):
            raise SetupError(f"This recipe requires npm 11.x, found {version!r}. Select npm 11 before setup; nothing was written.")
    if (install or verify) and recipe in ("python-cli", "fastapi"):
        # Check an already installed interpreter without discovering another
        # project, using its virtualenv, downloading Python, or persisting a cache.
        try:
            subprocess.check_output(
                ["uv", "python", "find", "--no-project", "--no-config", "--system",
                 "--no-python-downloads", "--offline", "--no-cache", "3.12"],
                text=True, stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            raise SetupError(
                "This recipe requires an installed Python 3.12 interpreter. "
                "uv could not find it offline; install or select Python 3.12 separately. "
                f"Nothing was written. uv reported: {exc.output.strip()}"
            ) from exc


def directory_fd(path: Path) -> int:
    """Open/create the absolute directory one component at a time without links."""
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            try:
                os.mkdir(part, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def require_verification_lock(target: Path, name: str) -> None:
    """Check lock presence/type only; review and installed dependencies are separate."""
    lock = target / name
    if lock.is_symlink() or not lock.is_file():
        raise SetupError(f"Verification requires an existing regular {name} (not a symlink). "
                         "Review the lock and install dependencies with approval before verification.")


def git_initialization_needed(target: Path) -> bool:
    """Recover an empty init attempt, but never rewrite unknown Git metadata."""
    marker = target / ".git"
    if not marker.exists() or (marker.is_dir() and not any(marker.iterdir())):
        return True
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=target,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode or Path(result.stdout.strip()).resolve() != target.resolve():
        raise SetupError("Existing Git metadata is not a valid worktree for this target. "
                         "It was left unchanged; inspect .git before retrying.")
    return False


def exclusive_file(root_fd: int, relative: str, data: bytes) -> None:
    fd = os.dup(root_fd)
    try:
        parts = Path(relative).parts
        for part in parts[:-1]:
            try:
                os.mkdir(part, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        output = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=fd)
        with os.fdopen(output, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)


def apply(target: Path, recipe: str, name: str, files: dict[str, bytes], plan: list[tuple[str, str]], state: dict | None) -> None:
    root_fd = directory_fd(target)
    try:
        if state is None:
            record = {"schema": 1, "version": revision(recipe), "recipe": recipe, "name": name,
                      "files": {key: digest(value) for key, value in files.items()}}
            temporary = ".repo-setup-state-" + uuid.uuid4().hex + ".tmp"
            try:
                exclusive_file(root_fd, temporary, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
                # Atomic exclusive publication: interrupted writes cannot corrupt state.
                os.link(temporary, STATE, src_dir_fd=root_fd, dst_dir_fd=root_fd, follow_symlinks=False)
            finally:
                try:
                    os.unlink(temporary, dir_fd=root_fd)
                except FileNotFoundError:
                    pass
        for action, relative in plan:
            if action == "CREATE":
                exclusive_file(root_fd, relative, files[relative])
    finally:
        os.close(root_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--recipe", choices=RECIPES)
    parser.add_argument("--audit", action="store_true", help="Read-only existing-repository JSON gap audit; never runs project commands")
    parser.add_argument("--approve-install", action="store_true", help="Confirm explicit user approval for dependency installation")
    parser.add_argument("--name", help="Lowercase project name; defaults to directory name")
    parser.add_argument("--apply", action="store_true", help="Write missing files; default is a read-only plan")
    parser.add_argument("--install", action="store_true", help="Install locked dependencies (requires --apply)")
    parser.add_argument("--verify", action="store_true", help="Execute reviewed project checks and smoke without dependency sync (requires --apply)")
    parser.add_argument("--git", action="store_true", help="Initialize local Git only (requires --apply)")
    args = parser.parse_args()
    if args.audit:
        if args.recipe or args.name or args.apply or args.install or args.verify or args.git or args.approve_install:
            parser.error("--audit cannot be combined with scaffold options")
        sys.dont_write_bytecode = True
        from audit import audit
        try:
            print(json.dumps(audit(args.target), indent=2))
            return 0
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    if not args.recipe:
        parser.error("--recipe is required unless --audit is selected")
    if (args.install or args.verify or args.git) and not args.apply:
        parser.error("--install, --verify, and --git require --apply")
    if ".." in args.target.parts:
        parser.error("Target must not contain .. components; supply the explicit intended directory")
    target = Path(os.path.abspath(args.target.expanduser()))
    name = args.name or target.name
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", name) or len(name) > 64:
        parser.error("Name must be 1–64 lowercase letters/digits with single internal hyphens, starting with a letter")
    try:
        check_path(target)
        if args.install and not args.approve_install:
            parser.error("--install requires --approve-install after explicit user approval")
        if args.install and args.recipe in PREVIEWS:
            parser.error("Preview has no reviewed lock: scaffold only, then explicitly approve lock resolution/install outside this helper")
        state = load_state(target, args.recipe, name)
        files = templates(args.recipe, name)
        plan = plan_files(target, files)
        print(f"{'APPLY' if args.apply else 'DRY RUN'}: {args.recipe} -> {target} (recipe {revision(args.recipe)})")
        for action, relative in plan:
            print(f"  {action:12s} {relative}")
        print("  Sources: bundled exact direct pins; npm registry or PyPI for dependencies")
        if args.recipe in PREVIEWS:
            print("  PREVIEW: no dependency lock or integration evidence; approved resolution/install and clean-copy checks pending")
        print("  No remote, commit, license choice, hooks, credentials, or global settings are created")
        if not args.apply:
            print("No files written. Use --apply to scaffold. Ask approval before any dependency resolution/install; legacy --install also requires --approve-install.")
            return 0
        preflight(args.recipe, args.install, args.verify, args.git)
        # Preview locks are never scaffolded. Fail before any file recovery or
        # Git initialization when verification cannot use an existing lock.
        if args.verify and args.recipe in PREVIEWS:
            require_verification_lock(target, "uv.lock" if args.recipe == "fastapi" else "bun.lock")
        initialize_git = args.git and git_initialization_needed(target)
        apply(target, args.recipe, name, files, plan, state)
        if initialize_git:
            run(["git", "init", "--initial-branch=main", "--template="], target)
        if args.git and git_initialization_needed(target):
            raise SetupError("Git initialization did not create valid repository metadata; "
                             "generated files were preserved.")
        check_path(target)
        if args.install:
            if args.recipe == "typescript-web":
                run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], target)
            else:
                run(["uv", "sync", "--locked"], target)
        if args.verify:
            if args.recipe == "typescript-web":
                run(["npm", "run", "check"], target, offline=True)
                run(["npm", "run", "smoke"], target, offline=True)
            elif args.recipe in ("react-web", "bun-monorepo"):
                require_verification_lock(target, "bun.lock")
                run(["bun", "run", "check"], target, offline=True)
                run(["bun", "run", "smoke"], target, offline=True)
            else:
                require_verification_lock(target, "uv.lock")
                run(["uv", "run", "--locked", "--no-sync", "--offline", "python", "scripts/check.py"], target, offline=True)
        print("Scaffold complete." + (" Checks and smoke passed." if args.verify else " Checks were not run; not yet verified ready to code."))
        return 0
    except (SetupError, OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
