# Development instructions

Preview scaffold: no lock or installed-check evidence is bundled. Use Bun 1.3.11
and Node 24.x. Ask before resolving or installing dependencies. After approval,
review and commit bun.lock; use bun install --frozen-lockfile --ignore-scripts
for repeat installs. Never fabricate a lock or report unrun checks as passing.

Run bun run check and bun run smoke after dependencies are available. Checks
never auto-fix. Format explicitly with bun run format. Preserve strict typing,
user edits, one Oxlint configuration and anti-slop provenance when integrated.
No secrets or generated outputs belong in Git.
