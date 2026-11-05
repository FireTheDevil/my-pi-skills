# Compose with install-anti-slop

This skill intentionally does not vendor Dillon Mulroy's anti-slop rules or
reimplement its installer. The baseline TypeScript recipe installs Oxlint, but
anti-slop remains a separate integration step run by the agent.

## Local composition

1. Find the actual installed `install-anti-slop` skill using the agent's skill
   discovery. In Pi this may be under a user/project skill directory; do not
   assume the installed path or that it matches upstream main.
2. Read its SKILL.md and the scripts/references relevant to the selected operation.
   Inspect the repository and its existing plugin entries. Reuse an existing
   installation rather than copying another one.
3. Follow that installed skill's fresh-install or update workflow inside the
   selected repository, within the user's authorization. Obtain explicit approval
   before any dependency resolution, lock generation or installation; scaffolding
   permission alone is insufficient. Compare its interface
   with upstream if compatibility is unclear. Do not automatically download or
   run a different skill to bypass a missing/incompatible local copy.
4. Preserve the single `.oxlintrc.json` configuration. Merge, do not replace,
   existing rules, plugins, and ignores. Match `@oxlint/plugins` exactly to the
   installed Oxlint version if required by the actual installed skill. The
   baseline pins Oxlint 1.87.0; an upgrade requires an explicit reviewed change
   to the pair and lockfile, not a floating latest install.
5. Respect the installed skill's vendored licenses and provenance record. Record
   the actual source revision or recoverable snapshot; do not substitute today's
   upstream HEAD for the installed source identity.
6. Keep vendored plugin and installed agent assets out of ordinary formatting
   and linting only as directed by that skill, preserving other ignores. Enable
   Effect rules only for a direct Effect dependency or explicit user request.
7. Run `bun run check` and `bun run smoke` for Bun recipes, or `npm run check`
   and `npm run smoke` for the legacy npm recipe, again. When formatting/fixes are
   authorized, run the prescribed fix/format cycle twice and confirm stability.

If the skill is missing or cannot be read, finish and verify the baseline; report
“anti-slop not integrated” and explain that the local installed skill must be
loaded. Do not label baseline Oxlint as anti-slop, manufacture its test results,
or assert that the user's installed version is compatible without examining it.

## Reference checked during creation

The reviewed upstream workflow has a `scripts/install.mjs` helper, vendored rule
assets, matching Oxlint/plugin dependencies, structured configuration merges,
optional Effect rules, and provenance requirements. This is a reference to check
against, not a frozen copy or permission to execute unreviewed source:

https://github.com/dmmulroy/anti-slop/blob/main/skills/install-anti-slop/SKILL.md

The user's local installation was not accessible in the build environment; this
bridge is documented agent composition, not a tested local installation.

## Optional sensitive-API contracts

For TypeScript authorization, ownership, tenant isolation, or entitlement APIs,
see [security contracts](security-contracts.md). If a gdp-ts integration is
separately requested, reuse this version-checking and config-merging workflow.
Reconcile its actual assertion rules with the installed anti-slop rules and the
reviewed trusted boundary; do not infer that every assertion must be banned,
copy a competing configuration, or disable rules just to obtain a pass. Neither
metadata compatibility nor this cross-reference is an integration test result.
