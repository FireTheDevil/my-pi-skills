# Development instructions

Use Python 3.12 and uv; install with `uv sync --locked`.

- Application: `src/app/`; tests: `tests/`
- Run: `uv run --locked app Ada`
- Before handing off: `uv run --locked python scripts/check.py`
- Format intentionally with `uv run --locked ruff format .`
- Keep dependencies locked and in `.venv`; review explicit upgrades
- Add meaningful behavior tests; do not weaken checks to obtain a pass
- Keep secrets and generated outputs out of Git

Anti-slop is a JS/TS-only optional integration and is not applied to this recipe.
