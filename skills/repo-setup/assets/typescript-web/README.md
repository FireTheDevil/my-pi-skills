# __PROJECT_NAME__

Minimal TypeScript web app using Vite. Replace the counter with your first feature.

## Requirements and setup

Use Node 24.x and npm 11.x. Tested with Node 24.19.0 and npm 11.9.0.
In WSL, run Node, npm, and all commands inside the same WSL environment.

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm run check
npm run smoke
npm run dev
```

The dev server binds to localhost; use the URL printed by Vite.

## Commands

- `npm run dev`: development server
- `npm run build`: type check and production build in `dist/`
- `npm run preview`: serve the production build locally
- `npm run format`: format owned files
- `npm run format:check`: non-mutating formatting check
- `npm run lint`: Oxlint, treating warnings as failures
- `npm run typecheck`: TypeScript without emitting files
- `npm test`: run the behavior tests once
- `npm run check`: formatting, lint, types, tests, and build; stops on failure
- `npm run smoke`: prove the dev server serves the HTML and transforms the entry module

Source lives in `src/`; behavior tests are next to the code. The smoke check proves
startup and HTTP serving, not browser interaction. Add browser tests when required.

## Repository conventions

Commit `package-lock.json` and use `npm ci`. Direct dependencies are exactly pinned
and transitive resolutions are locked. Dependency lifecycle scripts are disabled
during installation; reassess this when adding a dependency that requires one.
Keep local secrets in ignored `.env` files. No environment variables are required.

`.repo-setup.json` records the scaffold revision. Rerunning the same recipe
preserves edited files and recreates missing template files; review the plan first.
Do not rerun to intentionally delete generated starter files. No license, remote,
commit, deployment, or CI provider has been chosen.

Anti-slop is composed separately by the repo-setup skill when the installed
`install-anti-slop` skill is available; baseline Oxlint alone is not anti-slop.
