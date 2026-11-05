---
description: Review updates to Pi and its installed extensions using their own changelogs
argument-hint: "[package names...]"
---
Review available updates to Pi itself and the Pi extensions/packages installed in my setup, such as pi-codex-conversion. This is not a system-wide package audit: exclude OS packages, unrelated global tools, and transitive dependencies unless I explicitly request them.

Requested scope: ${@:-all installed Pi components}.

If specific package names are supplied, review only those components. Treat the names as a space-separated list. If a name is ambiguous or does not match an installed component, report that rather than silently expanding the scope.

Identify each installed Pi component with an available update and show its installed and proposed versions. Read that component's own changelog or release notes for the intervening versions. Explain its user-facing features, fixes, behavior changes, configuration changes, and required migrations. For example, report what changes in pi-codex-conversion itself, not what changes in the libraries it depends on. If its release notes are unavailable, say so rather than substituting dependency changelogs.

Recommend update, hold, or ignore for each component. Prioritize security, compatibility with my Pi version and other installed extensions, and migrations relevant to my configuration. Mention a dependency change only when it creates a concrete security or compatibility consequence for an installed Pi component; explain that consequence briefly within the component's entry, not as a separate dependency update report.

Group routine component updates together while retaining their names and a brief summary of their own changes. Expand research beyond their release notes only when it could change the recommendation or clarify a relevant component-level change. Distinguish confirmed effects from possible interactions. Do not install or update anything.
