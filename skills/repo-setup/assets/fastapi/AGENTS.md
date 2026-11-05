# Development instructions

Preview: no lock or installed-check evidence is bundled. Use Python 3.12 and uv.
Obtain explicit approval before resolving or installing dependencies; review and
commit uv.lock, then use uv sync --locked --no-build. No runtime downloads.
Run uv run --no-sync --offline python scripts/check.py and the HTTP smoke before
handoff. Do not weaken checks or claim unperformed verification. Keep local
secrets and generated outputs out of Git.
