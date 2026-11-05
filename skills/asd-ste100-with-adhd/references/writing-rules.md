# ASD-STE100 Writing Rules — Summary and Sources

This background summary draws on the official and secondary sources below. It paraphrases ASD-STE100 (Simplified Technical English) rule categories, not all their conditions and exceptions. It does not include the official dictionary and cannot establish compliance. For authoritative rules and word meanings, [request the standard](https://www.asd-ste100.org/request.html).

## What ASD-STE100 Is

ASD-STE100 is a controlled natural language, first released in 1986 (as AECMA Document PSC-85-16598) by what is now ASD (the AeroSpace and Defense Industries Association of Europe). It was developed to make aircraft maintenance documentation easier to understand, particularly for readers whose first language is not English. The standard is maintained by the Simplified Technical English Maintenance Group (STEMG) and has been free to download since Issue 6 (2013). This summary refers to Issue 9 (January 2025).

## Structure

- **53 writing rules across 9 sections** covering word choice, grammar, sentence structure, and style.
- **A dictionary** of roughly 900 approved words, each restricted to one meaning and one part of speech, plus roughly 1,200 words to avoid with suggested replacements.
- **A terminology allowance**: organizations may define their own dictionary of approved technical nouns and verbs beyond the base ~900 words, for domain-specific vocabulary the base dictionary can't cover.

## Rule Categories (Paraphrased)

**Word choice**
- Use approved words only in their approved meaning and part of speech.
- Each word maps to exactly one meaning — don't rely on context to disambiguate a word that has several dictionary senses.
- Prefer the plainer, shorter, more common word over a formal or rare synonym.
- Use an approved verb for an action, not a noun derived from that verb (Rule 3.7).
- Do not make phrasal verbs by putting a verb and a preposition together (Rule 9.3). Their meaning is not predictable from the parts, and non-native readers and translation systems both mishandle them.

**Verb forms**
- STE uses infinitives, imperatives, simple present, simple past, and simple future. Past participles can be adjectives or form passive constructions where permitted (see Voice below).
- STE restricts perfect and progressive verb forms. This is not a blanket ban on auxiliaries: simple future can use "will", and passive constructions use forms of "be".
- "-ing" forms are permitted only as a technical noun or as part of a technical noun, not as a verb form.

For this skill's flexible adaptation, retain a compound form when a simpler form would change time, duration, or uncertainty. "May have occurred" must not become "occurred".

**Voice**
- Active voice is required for procedures and instructions.
- Passive voice is allowed only in descriptive text, and only when the actor performing the action is genuinely unknown or irrelevant to the reader.

**Sentence structure**
- One instruction per sentence.
- Maximum ~20 words per sentence for procedures and instructions. Maximum ~25 words for descriptive text.
- Do not omit sentence parts (verb, subject, article) just to shorten the sentence — the standard explicitly warns that this creates ambiguity rather than clarity.
- Noun clusters (strings of nouns stacked as a modifier) are capped at 3 words.
- Semicolons are not permitted at all (Rule 8.1): "You can use all standard English punctuation marks but not the semicolon (;)." Write separate sentences instead. Every other standard mark, including the em dash, remains permitted.

**Paragraph and document structure**
- One topic per paragraph.
- Maximum ~6 sentences per paragraph.
- Use vertical (numbered or bulleted) lists for sequences, conditions, or complex enumerations instead of burying them in prose.

**Safety instructions**
- Safety-critical instructions must open with a clear command or condition, not be buried mid-sentence.

## Why This Skill Repurposes STE for Agent Output and User Communication

STE was designed to eliminate ambiguity for a reader who cannot ask a follow-up question — a technician on a tarmac, working from a manual, with no author to call. An AI agent parsing another agent's output, a tool description, or a system message is in the same position: no back-channel to resolve "does this passive-voice sentence mean the caller does X, or the callee does X?" The same rule set that protects an airline mechanic from a misread torque spec protects a downstream agent from a misread instruction.

## Sources

- [ASD-STE100 official site](https://www.asd-ste100.org/)
- [ASD-STE100 — About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe — Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English — Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe — ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary — Simplified Technical English (STE)](https://skybrary.aero/articles/simplified-technical-english-ste)
