# Development instructions

Use Node 24.x and npm 11.x. Install with `npm ci --ignore-scripts --no-audit --no-fund`.

- Source and behavior tests: `src/`
- Startup smoke check: `scripts/smoke.mjs`
- Before handing off: `npm run check` and `npm run smoke`
- Format intentionally with `npm run format`; `check` must not auto-fix code
- Preserve `package-lock.json`; explicitly review dependency upgrades
- Keep TypeScript strict and add tests for behavior changes
- Do not suppress lint/type failures to make checks pass
- Keep secrets and generated outputs out of Git

If anti-slop is installed, preserve its provenance, vendored licenses, and local
customizations. Use its installed skill for updates; do not add a second linter.
