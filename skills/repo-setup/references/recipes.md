# Recipe contracts and evidence

Choose the user's project first. Bun is preferred for new JS/TS; uv for Python.
Preserve existing package managers and the legacy npm recipe. Templates are
bundled source, never a moving latest generator. Exact pins are not verification.

## Preview recipes: no locks, no installed verification

All three previews use revision `1.2.0-preview`. Source generation and safe reruns
can be checked offline. No dependency resolution, clean install, formatter, lint,
type checker, build, running service or browser result is claimed for them.
No unit-test suites are added in this expansion; do not confuse HTTP smoke with
full behavior coverage. Review and add appropriate coverage under later scope.

### react-web

React 19.2.0 + React DOM 19.2.0, Vite 8.3.2, TypeScript 6.0.2, Oxlint 1.87.0,
Prettier 3.9.9, @types/react and @types/react-dom 19.2.2.
Bun 1.3.11 and Node 24.x are proposed tooling. React JSX uses the automatic
runtime via tsconfig and Vite; no React plugin/Fast Refresh is configured.
The actual app renders a stateful counter; no backend/router is implied.

### bun-monorepo

The same tool pins, with Bun workspaces `apps/*` and `packages/*`:
`apps/web` is a React app and `packages/shared` exports a typed greeting function.
The app imports `@starter/shared` via `workspace:*`. Root checks include both
packages; Vite builds the app, consuming source TypeScript from the private shared
package. No publishing pipeline, service, orchestrator or extra package manager.

### Approved Bun dependency procedure

After explicit user approval only, in the generated project:

```sh
bun install --ignore-scripts
bun run format
bun run check
bun run smoke
bun run dev
```

Review and commit the real `bun.lock`, inspect blocked lifecycle scripts (do not
enable them indiscriminately), then repeat in a clean disposable copy with
`bun install --frozen-lockfile --ignore-scripts`. Run check/smoke there too.
`check` is non-mutating formatting, lint, strict types and production build.
`smoke` serves localhost HTML and transforms the entry module; the monorepo
also imports the shared package. Neither proves rendered counter interactions.
Browser-use can verify actual rendering/interactions after dependencies exist.
Anti-slop is separate and unverified; see [the bridge](anti-slop.md).

### fastapi

Python 3.12.x + uv (installed runtime only). FastAPI 0.115.12,
Pydantic 2.11.4, uvicorn 0.34.2, Ruff 0.16.10 and ty 0.0.84.
The service has `GET /health` and validated `POST /greet`.
No database, auth, CORS, production serving policy or deployment is implied.
The project uses `tool.uv.package = false`; no build backend is needed.

After explicit user approval only:

```sh
UV_PYTHON_DOWNLOADS=never uv lock
UV_PYTHON_DOWNLOADS=never uv sync --locked --no-build
uv run --no-sync --offline ruff format .
uv run --no-sync --offline python scripts/check.py
uv run --no-sync --offline uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Review and commit the real `uv.lock`. `--no-build` refuses dependency source builds;
review necessary exceptions separately. Repeat a clean locked install and checks
in a disposable copy. Checks run format/lint/types and HTTP health, successful
greeting, invalid-input rejection and bounded server shutdown. Anti-slop does not
supply Python rules.

## Historically verified baseline recipes

These retain their source and lockfiles and revision `1.1.0`; historical passing
evidence is in tests/evidence and validation-report.txt, not evidence for previews.

### typescript-web (legacy npm compatibility)

Vanilla browser app only, not React. Node 24.x, npm 11.x; historically tested with
24.19.0 / 11.9.0. Vite 8.3.2, TypeScript 6.0.2, Vitest 5.0.3, Oxlint 1.87.0,
Prettier 3.9.9. Exact pins plus package-lock.json.
After install approval use `npm ci --ignore-scripts --no-audit --no-fund`.
`npm run check` runs format/lint/types/behavior tests/build; `npm run smoke`
checks startup/HTTP; `npm run dev` starts Vite on localhost.
`npm run format` is explicitly mutating. scripts/*.mjs is linted, not TS-checked.
No automatic migration to Bun or separate vanilla Bun variant is provided.

### python-cli

Python 3.12.x, uv; historically tested with 3.12.14 / 0.12.19.
Ruff 0.16.10, ty 0.0.84, pytest 9.1.1, uv_build 0.12.19 plus uv.lock.
After approval install with `uv sync --locked`, runtime downloads disabled.
Run `uv run --locked app Ada`; aggregate:
`uv run --locked python scripts/check.py`.
Six existing behavior/CLI tests plus format/lint/types/startup are bundled.
Explicit format: `uv run --locked ruff format .`; build: `uv build`.
The fixed import/command is app; no app dependencies or secrets are needed.

## Existing / unsupported repositories

Use `bootstrap.py PATH --audit` then read referenced instructions, configuration
and scripts. Declarations are present, execution remains not verified. Preserve
history, framework, locks, edits, remotes and checker choices; propose only the
smallest missing additions. Ask before retrofits or any dependency activity.
A gap report is never a claim that setup was applied or commands work.
