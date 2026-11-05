# Install and use repo-setup (expanded preview)

This source tree includes the historically verified locked npm/TypeScript and
uv/Python CLI recipes, plus **unverified** React/Bun, FastAPI/uv and Bun workspace
previews. New previews have no dependency locks: approved resolution/install and
end-to-end verification are still required. See references/recipes.md.

## Local skill placement

Review SKILL.md, scripts/, references/ and assets/. Copy the complete directory
to ~/.agents/skills/repo-setup only when you choose to install it. If it already
exists, stop and compare rather than overwriting. In Pi use /reload or restart;
verify discovery of /skill:repo-setup. No Pi settings have been changed here.
Pi documentation:
https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md

Use one POSIX/WSL environment, not mixed Windows/WSL runtimes. The helper needs
Python 3.10+; TOML audit parsing needs 3.11+. Python recipes need installed Python
3.12 and uv; new JS/TS previews propose Bun 1.3.11 and Node 24.x. The legacy npm
recipe needs Node 24.x/npm 11.x. No runtime is automatically installed.

Before `--install` or `--verify` writes starter files, including missing files on
reruns, the helper checks Node 24 for JS/TS, npm 11 for the legacy npm recipe,
and an existing Python 3.12 for both Python recipes. Python discovery is offline,
cannot download a runtime, and ignores unrelated caller projects/configuration.
Bun previews do not require npm. Plans and scaffold-only `--apply` do not need
recipe tools. Passing preflight does not establish installation or runtime readiness.

## Use

Examples in Pi:

```text
/skill:repo-setup set up this directory for React with Bun
/skill:repo-setup set up a FastAPI backend using uv
/skill:repo-setup set up a Bun monorepo with React and a shared TypeScript package
/skill:repo-setup audit this existing repository without changing it
```

An unspecified stack prompts a question. Bun is preferred for new JS/TS, not a
silent replacement for existing npm. Authorized scaffolding does not authorize
dependency installations: the agent must ask first.

Direct helper examples:

```sh
SKILL_DIR="$HOME/.agents/skills/repo-setup"
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/existing --audit
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/new-app --recipe react-web
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/new-app --recipe react-web --apply
```

Audit only reads bounded evidence and prints JSON; it never runs unknown project
scripts. Plans do not write. Apply writes scaffold files, not dependencies.
Preview --install is blocked until reviewed locks exist through the separately
approved recipe procedure. --verify uses existing dependencies without sync.
Do not label preview scaffolds ready-to-code.

For a locked baseline, only **after explicit installation approval**:

```sh
python3 "$SKILL_DIR/scripts/bootstrap.py" /absolute/my-cli --recipe python-cli --apply --install --approve-install --verify
```

Optional --git initializes local main, not a remote or commit. No CI, hooks,
license, credentials, deployment, global setting or runtime is installed.

## Reruns, composition and validation

Same recipe/name/revision reruns preserve edited files and recreate missing ones.
Do not rerun after intentional deletions. Nonempty unrecognized repositories,
parent repositories/workspaces and symlinks stop scaffolding. Use audit instead.
Legacy revision stays 1.1.0; preview revision is 1.2.0-preview. No force overwrite,
automatic upgrade, global install or reset exists.

With `--git`, an empty `.git` left by interrupted initialization is recovered.
Nonempty invalid Git metadata is refused before missing starter files are written;
inspect that metadata instead of deleting it to force setup. Existing valid
repositories and linked worktrees are preserved, and initialization is verified.

Read the installed install-anti-slop skill before JS/TS composition. Ask approval
for its dependencies and rerun checks/smoke afterward. Baseline Oxlint alone is
not anti-slop. Optional security-contract guidance does not install gdp-ts.

Offline validation:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/verify.py --scaffold-only
```

Integration installs require separate approval and registry access:

```sh
python3 scripts/verify.py --recipe typescript-web --approve-install
python3 scripts/verify.py --recipe python-cli --approve-install
```

Preview full integration is intentionally blocked pending real reviewed locks.
Historical tests/evidence results apply only to the baseline. No browser, remote
CI, user Pi/WSL install or anti-slop integration result is claimed for this update.
