# __PROJECT_NAME__

FastAPI service with GET /health and POST /greet accepting {"name":"Ada"}.
Blank/oversized names are rejected with HTTP 422. No database, auth, CORS,
deployment, secrets or production-service policy is implied.

## Preview and setup

Use Python 3.12 and uv. Exact direct pins are proposed but unverified; uv.lock
is deliberately absent until an approved resolution. Obtain explicit user
approval before the following dependency activity, with runtime downloads off:

```sh
UV_PYTHON_DOWNLOADS=never uv lock
UV_PYTHON_DOWNLOADS=never uv sync --locked --no-build
uv run --no-sync --offline ruff format .
uv run --no-sync --offline python scripts/check.py
uv run --no-sync --offline uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Review and commit uv.lock. The check runs non-mutating Ruff formatting/lint,
ty, and a real uvicorn HTTP startup/health/greeting/invalid-input smoke with
bounded shutdown. No unit suite is bundled. Repeat a locked install and checks
in a disposable copy without .venv, Git, outputs or secrets before claiming
readiness. --no-build rejects source builds rather than running arbitrary build
backends; review any necessary exceptions separately. No runtime is downloaded.
Keep .repo-setup.json; reruns preserve edits and recreate missing starter files.
Anti-slop does not cover Python. No CI, remote or license has been chosen.
