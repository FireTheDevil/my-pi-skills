# Before / After Examples

## Part 1 — Sentence-Level Examples

These examples illustrate this skill's flexible, STE-inspired guidance. They are not official examples or verified dictionary-compliant text. See the [writing rules and sources](../references/writing-rules.md) for background.

| Rule | Before | After | Why |
|---|---|---|---|
| Consistent terminology | "Open the settings panel. Close the preferences panel when you finish." (Both names refer to the same panel.) | "Open the settings panel. Close the settings panel when you finish." | Use one term for one component. Do not merge terms for different concepts. |
| One part of speech per word | "Oil the valve." | "Apply oil to the valve." | If "oil" is approved only as a noun, using it as a verb breaks the one-word-one-role guarantee. |
| Precise verb meaning | "Follow the safety instructions." | "Obey the safety instructions." | "Follow" can mean "come after" or "obey" — STE picks the unambiguous one. |
| Preserve uncertainty | "It is possible that the request has failed." | "The request may have failed." | Remove filler without turning a possible failure into a confirmed failure. Keep the compound form needed to preserve meaning. |
| Verb, not noun | "Perform an inspection of the filter." | "Inspect the filter." | The noun form hides the action and adds a filler verb that carries no meaning. |
| No phrasal verbs | "Take off the access panel." | "Remove the access panel." | "Take off" also means "depart" and "deduct" — the two words together do not predict the meaning. |

## Part 2 — Rewrites and User-Facing Communication

These fictional examples show how to rewrite prose and communicate with the user. They cover explanations, answers, progress updates, and recommendations. Reported checks belong to the examples; they are not claims about checks performed in the current conversation.

Each rewrite preserves the supplied meaning. Additional recommendations are labelled separately and are not part of the rewritten text. Sentence-length targets are guides, not pass/fail limits.

### Example A — Tool description

**Given context:** Manual review applies to every unresolved conflict. If this context is missing, clarify what "or otherwise" covers before choosing a fallback condition.

**Before:**
> This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review.

**Violations flagged:**
- Two instructions in one sentence (sync + resolve/surface).
- Present perfect in the relative clauses ("have been configured", "has been set").
- 44 words, far over the 25-word descriptive cap.

Note what is *not* flagged: "will attempt to" and "may resolve". Those are hedges, not violations. The tool is not promised to succeed, and the rewrite must not promise it either.

**After:**
> The tool tries to synchronize state across the configured backends. If it detects a conflict, it may resolve it automatically, depending on the configured strategy. If the conflict remains unresolved, the tool reports it for manual review.

The rewrite uses the supplied fallback condition. It does not invent an implementation step, such as reading a strategy file.

### Example B — Error message

**Before:**
> An error may have occurred while processing your request due to a possible mismatch in the expected data format, which could be caused by an outdated client version.

**Violations flagged:**
- One sentence carrying three separate claims (an error occurred, a format mismatch, a client version).
- 28 words, over the descriptive cap.

Not flagged: "may have occurred" and "could be caused by". The message is written by a system that does not know what went wrong. Both hedges are accurate reporting of that ignorance.

**After:**
> Your request may have failed. The cause may be a data format that does not match what the server expects. An outdated client can cause this mismatch. Check your client version.

**This example is the reason the modality rule exists.** An earlier version of this file rewrote the first sentence as "The request failed", and the third as "an outdated client **is the most common cause**". Both read better. Both are wrong: the first asserts a failure the system only suspects, and the second invents a frequency claim that appears nowhere in the input. A rewrite that supplies a cause, a frequency, or a mechanism has stopped being a rewrite.

Note also that "may have failed" keeps a compound verb form that the simple-tense rule would otherwise remove. **When the tense rule and the modality rule conflict, modality wins** — dropping the auxiliary here would delete the uncertainty along with the tense.

### Example C — Inter-agent instruction

**Before:**
> Once the upstream job has completed and assuming no errors were raised, the downstream agent should proceed to consume the output artifact, though it is worth noting that partial artifacts are sometimes produced under timeout conditions.

**Violations flagged:**
- Present perfect ("has completed") and subordinate-clause stacking ("assuming...", "though it is worth noting...").
- One sentence, three separate facts (completion condition, next action, edge-case warning).
- 36 words, over the 20-word instruction cap.

**After:**
> Wait for the upstream job to finish with no errors. Then read the output artifact. Warning: a timeout can produce a partial artifact. Check that the artifact is complete before you use it.

Two deliberate calls worth stating rather than hiding:
- "should proceed to consume" became the imperative "read". STE permits this for instructions, where a recommendation addressed to the executing agent is a command. Do not make the same move in descriptive text.
- The final sentence is **new**. The original warned about partial artifacts without saying what to do about it. Adding the check makes the warning actionable, but it is added content, so it is called out here rather than passed off as a rewrite. If the source's silence was deliberate, drop the sentence.

### Example D — README prose (STE-flavored mode)

**Before:**
> Our caching layer is designed to slot seamlessly into your existing stack with minimal friction and no vendor lock-in; it leverages semantic similarity to dramatically reduce the cache misses that traditionally plague LLM workloads.

**Violations flagged:**
- Marketing adjectives and claims without measurement ("seamlessly", "minimal friction", "dramatically").
- Semicolon joining two separate ideas.
- Nominalization and soft phrasing ("is designed to slot into", "leverages").
- 34 words, over the 25-word descriptive cap.

**After:**
> A normal cache matches requests by exact text, so a small change in wording causes a cache miss. This cache compares the meaning of a new prompt against the prompts it already holds. It runs alongside your current stack and stores no data outside it.

The rewrite retains the source's product claims without the unsupported claims about ease or degree of improvement. Rewriting does not verify those product claims. "No vendor lock-in" does not establish where data is stored. The source also does not specify how the cache implements semantic similarity.

**Additional recommendation, not part of the rewrite:** Verify the vendor-lock-in and cache-miss claims before publication. Add a measured improvement only if evidence supports it.

### Example E — Direct answer without headings

**User asks:** Do I need to restart the app after changing this setting?

**Before:**
> That's a good question. The important thing to know here is that, yes, a restart of the app is required for the new setting to take effect.

**After:**
> Yes. Restart the app to apply the setting.

The answer comes first. A short answer does not need a heading, checklist, or closing offer.

### Example F — Progress update with an unverified expectation

**Before:**
> I have changed the parser to handle empty input and the build has passed, so this should fix the crash, although I have not tested the empty-input case yet. I will check that case next.

**After:**
> I changed the parser to handle empty input. The build passed. I expect this to fix the crash, but I have not tested the empty-input case. Next, I will check that case.

The build result is verified in this scenario; the crash fix is not. The update preserves the planned next check instead of claiming the task is complete.

### Example G — Recommendation with an exception

**Before:**
> Unless your organization requires automatic updates, you should consider disabling them during the investigation because they may change the version under test.

**After:**
> Updates may change the version under test. Unless your organization requires automatic updates, you should consider disabling them during the investigation.

Keep "may", "should consider", and the exception. Put the risk and condition before the suggested action. "Disable automatic updates" would lose both the exception and the recommendation's original strength.

## How to Read These Examples

Part 1 shows the actual rules this skill is built on. Part 2 shows the transfer: the same discipline — one meaning per word, active voice, simple tense, one instruction per sentence, explicit conditions instead of buried subordinate clauses — makes machine-to-machine and cross-language text safer to parse, not just aircraft manuals.
