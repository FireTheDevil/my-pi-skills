# Provenance and validation limits

## Current expanded preview

This expansion adds authored React/Bun, FastAPI/uv and Bun workspace source
templates at recipe revision 1.2.0-preview, a stdlib read-only gap audit, and
explicit installation approval gates. No generator, dependency resolution,
installation, runtime download or lock generation was performed for these new
templates. Direct pins are proposals, not proven compatibility. No new lock,
unit suite, browser result or installed integration evidence is supplied.
React templates reuse the baseline Vite structure/configuration and retain its
bundled license. FastAPI source and workspace composition are authored here.

Legacy template bytes/locks and recipe revision 1.1.0 remain intact. Bootstrap and
verification tooling have changed, so historical executable-helper evidence is
not evidence for the modified helper; current offline checks must be reported
separately. The historical sections below refer only to the prior baseline.

## Historical baseline record

Package release 1.1.1 is documentation-only: optional TypeScript security-contract
guidance and cross-references were added on 6 October 2026. Executable recipes,
lockfiles, and template source remain unchanged at recipe revision 1.1.0.

Recipe revision: 1.1.0. Both recipes validated 6 October 2026 in a disposable Linux
cloud workspace, not in the user's local Pi/WSL installation.

## Official scaffold sources

TypeScript:

- Generator: `create-vite@9.2.1`, official npm package
- Command: `npm exec --yes --package=create-vite@9.2.1 -- create-vite ts-seed --template vanilla-ts --no-interactive`
- Tarball: https://registry.npmjs.org/create-vite/-/create-vite-9.2.1.tgz
- npm integrity: `sha512-nE710dPFzm9CavJw4PtpOLQpNBiOzFV+tGbwcmBdg1A3TWgFkqypDmjt44oV0jvvQEdGsvFAvQ5pUnKrdcwciw==`
- Generator succeeded. The bundled result keeps the Vite/TypeScript structure,
  replaces demo artwork and behavior with a minimal counter with authored test cases,
  enables strict TypeScript, and adds explicit quality commands and docs
- A renewed install on 6 October 2026 completed successfully with lifecycle scripts disabled
- The exact direct pins and resolved transitive graph are retained in package-lock.json
- Fresh/clean locked installs, formatting, lint, types, behavior tests, build, startup,
  reruns, and intentionally failing check fixtures all passed
- The generator's published license identifies template files as CC0 1.0;
  its full published license is retained in `create-vite-LICENSE.txt`

Python:

- Generator: preinstalled official uv 0.12.19
- Command: `uv init --package --name app --python 3.12 --no-workspace --vcs none py-seed`
- Documentation: https://docs.astral.sh/uv/guides/projects/
- Added typed greeting CLI, behavior/error tests, pinned Ruff/ty/pytest, check
  script, package name substitution, uv_build module mapping, and docs
- PyPI dependencies and lock were resolved and installed using uv; full verified
  tool versions and results are in `validation-report.txt`

## Anti-slop

Reference: https://github.com/dmmulroy/anti-slop/blob/main/skills/install-anti-slop/SKILL.md

Its workflow was inspected on the research/build date. No upstream assets were
copied and no source commit is represented as the user's installed revision.
The user's installed `install-anti-slop` skill was not accessible here. Composition
instructions require inspecting the actual installed copy before execution.
Neither that local integration nor a full JS/TS anti-slop check was validated.

## Portability

The helper uses Python's standard library and targets Linux/macOS-style local
filesystems, including WSL. It has not been executed in Pi or on Windows-native
Python. It does not install itself or any runtime globally. Pi skill discovery
must be verified after copying the folder to the user's chosen skill location.

Pi reference: https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md

No remote repository, cloud service, CI job, commit, license for the user's new
application, or deployed app was created.
