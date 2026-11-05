# My Pi skills and prompts

The maintained parts of my personal Pi toolkit:

- `skills/asd-ste100-with-adhd`: clear, focused communication guidance.
- `skills/repo-setup`: repository scaffolding and read-only setup audits.
- `prompts/restate.md`: restate the goal, constraints, and agreed decisions.
- `prompts/pi-package-updates.md`: package-update prompt template.

## Live Pi setup

This repository is the canonical source for these resources on this machine:

- `~/.pi/agent/skills/asd-ste100-with-adhd` links to this repo's skill directory.
- Pi's `settings.json` explicitly includes this repo's `skills/repo-setup` path.
- Both files in `~/.pi/agent/prompts/` link to this repo's prompt templates.

Edit the files here to keep the source and live configuration aligned. Run
`/reload` in an existing Pi session, or restart Pi, to load changes. If this
repository moves, update those links and the configured repo-setup path.

Other skills and extensions are maintained in separate installations and are
not vendored here. This repository contains no credentials or Pi session state.

## Verification

Run the offline scaffold checks without installing dependencies:

```sh
python3 skills/repo-setup/scripts/verify.py --scaffold-only
```

React/Bun, FastAPI, and Bun monorepo recipes remain previews. Scaffold checks
do not demonstrate dependency compatibility or runtime readiness. See the
repo-setup installation guide and validation report for their limitations.

## Provenance and licenses

Original contributions are licensed under the [MIT License](LICENSE),
copyright (c) 2026 FireTheDevil. Third-party material retains its existing
licenses and attribution; the root license does not replace those notices.

Extracted from the local `myskills` repository at commit
`8f057f9`, preserving the selected files, existing license notices, and
attributions. The original repository remains a local history archive.
Bundled validation reports predate this extraction unless stated otherwise.
See the communication skill's `LICENSE` and repo-setup's
`references/provenance.md` and bundled license notices for attribution.
