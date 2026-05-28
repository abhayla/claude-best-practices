---
name: to-prd
description: >
  Generate a PRD by synthesizing the current conversation context and codebase
  understanding — no interview, just write up what is already known. Optionally
  publish to the project issue tracker with a ready-for-agent label. Use when
  the user wants to convert the running conversation into a tracked PRD, or
  needs the inverse direction of /prd-parser (which parses an existing PRD).
type: workflow
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[optional: issue tracker target, e.g. github | linear | local-file]"
version: "1.0.0"
---

# To-PRD

Turn the current conversation context into a PRD.

**Publication target:** $ARGUMENTS (default: local file at `docs/prds/`)

**Do NOT interview the user** — synthesize what you already know from the conversation and the codebase. If genuinely critical information is missing, ask ONE consolidated question at the end, not a stream of clarifiers.

For the inverse direction (parsing an existing PRD into structured form), use `/prd-parser`. For breaking the resulting PRD into tracked issues, use `/plan-to-issues` after this skill completes.

---

## STEP 1: Explore the Repo

Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary (`CONTEXT.md` or `CONTEXT-MAP.md`) throughout the PRD, and respect any ADRs in `docs/adr/` touching the area.

If neither `CONTEXT.md` nor `docs/adr/` exists, use the names the code itself uses — do not invent generic labels like "service layer".

---

## STEP 2: Sketch the Modules

Sketch out the major modules to be built or modified to complete the implementation. Actively look for opportunities to extract **deep modules** that can be tested in isolation.

A **deep module** (as opposed to a shallow module) encapsulates significant functionality behind a simple, testable interface that rarely changes. For the full deep-vs-shallow framework, see `/improve-codebase-architecture` (`references/LANGUAGE.md` and `references/DEEPENING.md`).

Check with the user that these modules match their expectations. Check which modules they want tests written for.

---

## STEP 3: Write the PRD

Write the PRD using the template below. If a publication target was specified, push it there with the `ready-for-agent` triage label — no need for additional triage. Otherwise save to `docs/prds/<slug>.md` (create the directory if it doesn't exist).

### PRD Template

```md
## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories in the format:

1. As an <actor>, I want a <feature>, so that <benefit>

Example:
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending.

This list MUST be extensive — cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions made during synthesis. Can include:

- Modules to be built or modified
- Interfaces of those modules (in glossary terms — see /improve-codebase-architecture)
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets — they go stale fast.

**Exception:** if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts.

## Testing Decisions

A list of testing decisions made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (similar types of tests already in the codebase)

## Out of Scope

The things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.
```

---

## MUST DO

- Synthesize from existing conversation context — do not run a fresh interview
- Use `CONTEXT.md` vocabulary when it exists
- Respect `docs/adr/` — do not propose changes that contradict an accepted ADR without flagging
- Look for deep-module opportunities during module sketching
- Confirm the module sketch with the user before writing the PRD body
- Tag with `ready-for-agent` if publishing to an issue tracker

## MUST NOT DO

- MUST NOT interview the user as the first step — that's `/grill-with-docs` or `/brainstorm`
- MUST NOT include file paths or code snippets in the Implementation Decisions section — except for the prototype-snippet exception
- MUST NOT auto-publish to a remote tracker without confirming the target — show the user the rendered PRD first
- MUST NOT skip the testing decisions section — it's load-bearing for downstream `/plan-to-issues`
- MUST NOT invent generic labels ("service layer") where the codebase uses domain names
