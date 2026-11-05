# Optional security contracts for TypeScript

Use this guide only when the requested TypeScript work includes sensitive
APIs involving authorization, ownership, tenant isolation, or entitlements.
The bundled counter does not need this layer. Adopt proof-carrying arguments
only where they make a consequential precondition harder to omit; avoid turning
ordinary application code into a proof system. This follows the upstream
[scope guidance](https://github.com/rauchg/gdp-ts/blob/main/skills/gdp-ts/references/where-to-stop.md).

## Design the boundary first

[gdp-ts](https://github.com/rauchg/gdp-ts) is one optional library/linter pattern
for passing evidence of a check to the operation that needs it. It does not
choose the authorization policy. A conceptual contract is: an operation receives
the authenticated actor, the exact resource, and evidence that this actor may
perform this action on that resource. Include tenant identity and entitlements
when the policy depends on them; a bare `allowed: boolean` loses that relationship.

Identify who authenticates the actor, who performs the authoritative policy check,
and which small trusted module may construct the evidence. Reuse an existing
policy engine or server-side check. Require sensitive entry points to consume
evidence bound to the relevant values; do not accept client-supplied proof objects
or use a cast to manufacture authorization. The upstream
[skill workflow](https://github.com/rauchg/gdp-ts/blob/main/skills/gdp-ts/SKILL.md)
provides an adoption procedure, not an automatic repo-setup step.

## Runtime authority remains mandatory

TypeScript types disappear at runtime. Proof-shaped data, a passing linter, or a
client claim is not authority. Keep input validation, actual server-side policy
checks, database constraints, and runtime denial behavior. A check may become
stale before a mutation; use transaction boundaries or revalidation appropriate
to the operation. Do not carry trusted evidence across requests, jobs, or
serialization boundaries without establishing it again. Review the upstream
[limitations](https://github.com/rauchg/gdp-ts/blob/main/skills/gdp-ts/references/limits.md).

## Compatibility is not validation

As inspected on 6 October 2026, the
[upstream package metadata](https://github.com/rauchg/gdp-ts/blob/main/package.json)
for `@gdp-ts/core` 0.1.0 declares optional peers TypeScript >=5.4 and Oxlint >=1.86.
The recipe's TypeScript 6.0.2 and Oxlint 1.87.0 satisfy those ranges. That is a
metadata comparison only: this bundle has not installed gdp-ts or tested its
runtime, lint preset, or interaction with the user's anti-slop installation.
No gdp-ts dependency, preset, template code, or lockfile change is included.

## Published reports to check before adopting

Both issues below were open when inspected on 6 October 2026. They are upstream
reports, not exploits reproduced or independently confirmed by this package:

- [Issue #11](https://github.com/rauchg/gdp-ts/issues/11) reports that spreading a
  `Named` value and replacing its `.value` can retain the old compile-time identity
- [Issue #13](https://github.com/rauchg/gdp-ts/issues/13) reports strict-preset gaps
  involving non-null assertions and values typed `any` or `never`

Check their current resolution against the exact version proposed. Treat the
pattern as a compile-time guardrail, not a complete security guarantee.

## If adoption is requested

Propose one sensitive boundary first. Review and pin the selected package/source;
merge its lint configuration through the existing
[anti-slop composition workflow](anti-slop.md), preserving local choices.
Assertion rules are contextual: reconcile the actual presets and trusted-module
boundaries, rather than adding a universal cast ban or suppressing a conflict.
Never use an assertion to fake a proof or named identity.

Test allowed and denied runtime paths, wrong actor/resource/tenant combinations,
revoked or stale authority, malformed input, and the relevant published bypass
cases. Add negative type/lint fixtures and run the project's full locked checks.
Report exactly which safeguards were exercised before claiming the integration
works. This guide alone does not establish those results.
