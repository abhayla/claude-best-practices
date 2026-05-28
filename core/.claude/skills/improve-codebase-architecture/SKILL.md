---
name: improve-codebase-architecture
description: >
  Analyze architectural friction and propose deepening opportunities —
  refactors that turn shallow modules into deep ones (Ousterhout lens).
  Use when the user asks to improve architecture, find refactoring
  opportunities, consolidate tightly-coupled modules, or make a codebase
  more testable and AI-navigable.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "[area or module path to focus on]"
version: "1.0.0"
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

**Scope:** $ARGUMENTS

This skill is _informed_ by the project's domain model. The domain language (`CONTEXT.md` or `CONTEXT-MAP.md` — see `/grill-with-docs`) gives names to good seams; ADRs in `docs/adr/` record decisions the skill MUST NOT re-litigate.

---

## Glossary (Use These Terms Exactly)

Use these terms verbatim in every suggestion. Don't drift into "component", "service", "API", or "boundary". Consistent language IS the point. Full definitions in `references/LANGUAGE.md`.

- **Module** — anything with an interface and an implementation (function, class, package, slice).
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** — the code inside.
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary".)
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers get from depth.
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles (full list in `references/LANGUAGE.md`):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

---

## STEP 1: Explore

Read the project's domain glossary (`CONTEXT.md` or `CONTEXT-MAP.md`) and any ADRs in the area being touched (`docs/adr/`) first. If neither exists, proceed without — but flag that future iterations would benefit from `/grill-with-docs` to bootstrap them.

Then dispatch an exploration via the Agent tool (use the `Explore` agent type if available, otherwise a general-purpose subagent) to walk the codebase. Don't follow rigid heuristics — explore organically and note where friction lives:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything suspected of being shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

---

## STEP 2: Present Candidates as an HTML Report

Write a self-contained HTML file to the OS temp directory so nothing lands in the repo. Resolve the temp dir from `$TMPDIR`, falling back to `/tmp` on Unix or `%TEMP%` on Windows, and write to `<tmpdir>/architecture-review-<timestamp>.html` so each run gets a fresh file.

**Tell the user the absolute path so they can open it.** Do NOT shell out to `xdg-open` / `open` / `start` automatically — print the path in the chat and let the user decide (CI-friendly, sandbox-friendly, and matches how downstream hub tooling reports artifact paths).

The report uses **Tailwind via CDN** for layout and styling, and **Mermaid via CDN** for diagrams where a graph/flow/sequence reliably communicates the structure. Mix Mermaid with hand-crafted CSS/SVG visuals. Each candidate gets a **before/after visualisation**. Be visual.

For each candidate, render a card with:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and how tests would improve
- **Before / After diagram** — side-by-side, custom-drawn, illustrating the shallowness and the deepening
- **Recommendation strength** — one of `Strong`, `Worth exploring`, `Speculative`, rendered as a badge

End the report with a **Top recommendation** section: which candidate to tackle first and why.

**Use `CONTEXT.md` vocabulary for the domain, and `references/LANGUAGE.md` vocabulary for the architecture.** If `CONTEXT.md` defines "Order", talk about "the Order intake module" — not "the FooBarHandler", and not "the Order service".

**ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly in the card (e.g. a warning callout: *"contradicts ADR-0007 — but worth reopening because…"*). Don't list every theoretical refactor an ADR forbids.

See `references/HTML-REPORT.md` for the full HTML scaffold, diagram patterns, and styling guidance.

**Do NOT propose interfaces yet.** After the file is written, ask the user: "Which of these would you like to explore?"

---

## STEP 3: Grilling Loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

For the grilling protocol itself, prefer `/grill-with-docs` (Socratic, one question at a time, docs-aware) over generic `/grill-me`. The docs-aware variant is what this skill assumes.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md` right there. Same discipline as `/grill-with-docs` — see `core/.claude/skills/grill-with-docs/references/CONTEXT-FORMAT.md`. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR via `/adr`, framed as: *"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"* Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See `references/INTERFACE-DESIGN.md` (Ousterhout's "Design It Twice" — parallel sub-agent pattern).

For how dependency categories drive the test strategy across the new seam (in-process, local-substitutable, remote-but-owned, true external), see `references/DEEPENING.md`.

---

## MUST DO

- Read `CONTEXT.md` (or `CONTEXT-MAP.md`) and `docs/adr/` BEFORE exploring
- Use the glossary terms verbatim — never substitute "component", "service", "boundary"
- Apply the deletion test to every shallow-suspect module
- Write the HTML report to the OS temp directory, never into the repo
- Print the absolute path to the user — do not auto-open
- Use `Strong` / `Worth exploring` / `Speculative` for recommendation strength
- Stop after the report and ask which candidate to explore — do NOT propose interfaces in STEP 2

## MUST NOT DO

- MUST NOT write the HTML report into the repo working tree
- MUST NOT auto-shell `xdg-open` / `open` / `start` — print the path instead
- MUST NOT use "component", "service", "API surface", "boundary", or "layer" where glossary terms apply
- MUST NOT propose every theoretical refactor an ADR forbids — only surface ADR conflicts when the friction is real
- MUST NOT propose interfaces during STEP 2 — that is STEP 3's job
- MUST NOT skip STEP 1 exploration even when the user names a specific candidate — the surrounding modules give context the user can't supply
