---
name: repo-setup
description: Scaffold new React/Bun, FastAPI/uv, Bun workspace, or legacy TypeScript/npm and Python CLI projects; audit existing repositories read-only. Ask before dependency installation; distinguish preview scaffolds from historically verified locked recipes.
---

# Repo setup

Choose the user's project, not a template. Infer purpose, directory and package
manager from their request and files. If “set up this repo” leaves language or
framework undecided, ask. Prefer **Bun for new JS/TS** and **uv for Python**;
never switch an existing repository's manager silently.

Read [recipe contracts](references/recipes.md) before planning:

- `react-web`: React + Vite + Bun, preview without a lock
- `fastapi`: FastAPI + Python 3.12 + uv, preview without a lock
- `bun-monorepo`: Bun workspaces, React app + shared TypeScript package, preview
- `typescript-web`: legacy vanilla Vite + npm, locked; preserve compatibility
- `python-cli`: Python CLI + uv, locked

There is no separate vanilla Bun recipe: the legacy vanilla choice stays intact;
a new vanilla Bun request needs a reviewed adaptation, not an automatic npm
selection. Other frameworks, backend services, workspace layouts and retrofits
need a project-specific plan. New previews are useful source scaffolds, **not
verified ready-to-code recipes**. Do not call proposed pins or absent locks tested.

## Inspect and plan

Read relevant ancestor/project AGENTS.md and other local instructions. Inspect
Git status/history, parent repositories/workspaces, manifests, locks, existing
scripts and runtime versions. Preserve unrelated edits. The scaffold helper only
writes empty or recognized same-recipe/name/revision directories. Do not generate
over existing work.

For existing repositories, use the read-only audit (no recipe required):

```sh
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/existing-repo --audit
```

It inventories instruction paths, manifests, locks, workspace declarations,
declared npm/Bun scripts, Python tool sections, command/config evidence and CI.
It does not execute scripts, import project code, install anything, or choose a
retrofit. Read referenced instructions and commands yourself. Its JSON separates
**present**, **missing**, **not verified**, and **not applicable** and proposes
small additions; present is evidence of declaration only, not correctness.
Custom task runners and incomplete/skipped files require manual interpretation.
For package.json, command evidence requires nonempty string commands. Malformed
script entries and workspace declarations are reported as errors and make the
inventory incomplete; valid sibling declarations remain visible. Workspace
arrays and Yarn-style objects with a packages array are recognized, including
empty arrays. This checks declaration shape, not glob matches or executability.
For pyproject.toml, it also validates the tables it reads, nonempty string
project.scripts entries, and uv workspace members/exclude arrays. Malformed
declarations make the inventory incomplete without hiding valid sibling evidence;
an empty uv workspace table still counts as a declaration. Python entry points
are not treated as npm-style check commands. This is not full Python/uv schema,
entry-point syntax, importability, or workspace membership validation.
Only recognized uv workspace members/exclude fields are copied into the report;
other workspace fields are not validated and need manual review.
The inventory is bounded, skips symlinks and generated directories, and reports
limits/errors. It intentionally does not read secrets or Git configuration.
Audit may inspect a project inside a parent repo/workspace; scaffolding refuses it.

For new projects, preview deterministically without downloads:

```sh
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/project --recipe RECIPE --name project-name
```

Explain the selected recipe, status, exact pins, sources, proposed files and check/
run commands. Resolve target conflicts first. Sensitive TypeScript authorization,
ownership, tenancy or entitlement APIs additionally need
[security-contract guidance](references/security-contracts.md); runtime policy
checks remain authoritative. No gdp-ts is installed by default.

## Apply, approval, and verification

Authorized file creation is separate from dependency approval:

```sh
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/project --recipe RECIPE --apply
```

**Ask for explicit approval before any dependency resolution, lock generation,
installation, dependency build scripts, or runtime download.** A setup request or
`--apply` alone is not approval. This includes anti-slop dependency activity.
Do not install runtimes automatically.

After approval, locked baseline recipes support:

```sh
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/project --recipe RECIPE --apply --install --approve-install --verify
```

The confirmation flag records the operator's assertion of approval; it is not a
substitute for asking. npm lifecycle scripts are disabled; uv runtime downloads
are disabled. Preview `--install` is blocked because no reviewed locks are bundled.
For previews follow the recipe's explicit approved lock/install procedure, review
the real resulting lock and any script/build requirements, and only then verify.
Never fabricate a lock, silently fall back to an unlocked install, or weaken checks.
`--verify` executes project-controlled check scripts: inspect their current contents
and declared commands first, especially edited files on reruns. Do not execute
unknown scripts or commands that install dependencies without explicit approval.
The helper uses uv offline/no-sync and disables Bun auto-install, but these are
not a sandbox for arbitrary script subprocesses. Dependencies must already be
available. Preview verification requires a real lock.
Because preview locks are not bundled, `--verify` requires an existing regular
`bun.lock` or `uv.lock`, not a symlink, before writing/restoring scaffold files or
initializing Git. If absent, scaffold without `--verify` and complete the approved
lock/install procedure first. Baseline bundled-lock recovery is unchanged. Lock
presence/type is not proof of reviewed contents or installed dependencies; the
lock is checked again before verification, not protected from concurrent edits.

Before install or verification writes starter files, the helper checks Node 24
for JS/TS, npm 11 only for `typescript-web`, and an existing Python 3.12 for
`python-cli` and `fastapi`. Python discovery is offline, cannot download a runtime,
and ignores unrelated caller projects/configuration. A plan or scaffold-only
`--apply` does not need recipe tools. Passing preflight does not prove dependency
compatibility or that project checks will pass. Approval gates remain unchanged.

Optionally add `--git` to initialize local main only when wanted. No commit,
remote, push, license choice, hooks, CI, deployment, credentials or global setting
is added. Edited files print `KEEP EDITED` and are never replaced; missing starter
files are recreated after partial failures. Do not rerun after intentional
deletions. Reruns require the same recipe/name/revision. Legacy recipe revision
stays 1.1.0; previews use 1.2.0-preview. No force flag or automatic upgrade.

With `--git`, an empty `.git` left by interrupted initialization is recovered.
Nonempty invalid Git metadata stops setup before missing starter files are written.
Inspect it rather than deleting it to force a rerun. Valid repositories and linked
worktrees are preserved, and the resulting Git repository is verified.

For JS/TS, inspect and compose the actual installed `install-anti-slop` skill via
[the bridge](references/anti-slop.md), obtaining approval for its installs.
Baseline Oxlint is not anti-slop. Rerun full checks and smoke after integration.

Prove clean locked installation in an approved disposable copy without Git,
dependencies, outputs or secrets, then rerun the same checks. HTTP smoke is not
browser interaction coverage. Use browser-use for any browser verification, not
Playwright; defer honestly if the runtime/dependencies are unavailable.

## Validate this skill and hand off

Offline commands (no dependency activity):

```sh
python3 -m unittest discover -s tests -v
python3 scripts/verify.py --scaffold-only
```

[verify.py](scripts/verify.py) covers all five scaffold/rerun paths offline.
Baseline integration needs approval and tools/registry access; choose
`--recipe typescript-web` or `--recipe python-cli` plus `--approve-install`.
Preview integration is blocked pending approved locks and end-to-end review;
offline scaffolding does not promote it.

Give directory, recipe/status, changed files, exact pins, checks/results,
anti-slop status, blocked verification and the next command. State explicitly
whether locks, clean installs, browser behavior and startup were exercised.
Only say “ready to code” after installation, checks and startup actually pass.
Distinguish local evidence, historical baseline evidence and the user's Pi/WSL
installation. See [provenance](references/provenance.md).
