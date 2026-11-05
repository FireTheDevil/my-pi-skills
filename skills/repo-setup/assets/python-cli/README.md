# __PROJECT_NAME__

Small typed Python CLI. Replace the greeting with your first feature.

## Setup and run

Use Python 3.12 and uv. Tested with Python 3.12.14 and uv 0.12.19.
Run the runtime, package manager, and checks consistently inside WSL when using WSL.

```sh
uv sync --locked
uv run --locked python scripts/check.py
uv run --locked app Ada
```

The starter prints `Hello, Ada!`. No secrets or environment variables are required.

## Commands

- Run/dev: `uv run --locked app Ada`
- Format: `uv run --locked ruff format .`
- Format check: `uv run --locked ruff format --check .`
- Lint: `uv run --locked ruff check .`
- Typecheck: `uv run --locked ty check`
- Test: `uv run --locked pytest`
- Check all: `uv run --locked python scripts/check.py`
- Build: `uv build`

The aggregate command checks formatting, lint, types, behavior tests, and startup.
It stops on the first failure and never auto-fixes source. Tests also verify the
CLI output and its error exit status. Code lives in `src/app/`, tests in `tests/`.

Commit `uv.lock`; `--locked` fails rather than changing an outdated lockfile.
Keep dependencies in `.venv` and review explicit version upgrades. The `app`
module and command remain fixed when the repository is renamed; rename them
explicitly later if needed. The Python version is intentionally limited to the
3.12 series verified by this recipe.

`.repo-setup.json` records the scaffold revision. A rerun preserves user edits
and recreates missing template files. Review the plan before rerunning; do not
rerun to intentionally delete starter files. No license, remote, commit, CI,
or deployment provider has been chosen.
