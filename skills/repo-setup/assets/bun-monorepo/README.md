# __PROJECT_NAME__

Bun workspace with a React app in apps/web and a shared TypeScript package
in packages/shared. The app consumes @starter/shared through workspace:*; no
package publishing or backend is implied.

## Preview status and setup

Exact direct pins are proposed, not installation-tested. No bun.lock is bundled.
Use Bun 1.3.11 and Node 24.x in one POSIX/WSL environment. Obtain explicit user
approval before dependency activity. Only after approval:

```sh
bun install --ignore-scripts
bun run format
bun run check
bun run smoke
bun run dev
```

Review the resolved bun.lock and any blocked lifecycle scripts; never enable them
blanketly. Commit the reviewed lock. Reproduce in a disposable clean copy using
`bun install --frozen-lockfile --ignore-scripts`, then check and smoke again.
Formatting is explicit; check runs non-mutating format, Oxlint, strict types and
build checks. Smoke starts a localhost Vite server and checks HTML and entry
module transformation plus a shared-package import. It is not a browser interaction test or a unit-test suite.
Use browser-use to verify rendered counter interactions when available.
No behavior/unit suite is bundled; add coverage as application work is approved.

Anti-slop is separate: inspect the installed install-anti-slop skill, ask approval
before its dependency operations, merge configuration, and rerun all checks.
Keep .repo-setup.json; reruns preserve edits and recreate missing starter files.
No CI, license, remote, deployment or secrets have been selected.
