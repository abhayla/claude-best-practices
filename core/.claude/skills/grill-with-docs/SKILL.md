---
name: grill-with-docs
description: >
  Run a grilling session that challenges a plan against the project's existing
  domain model, sharpens terminology, and updates documentation (CONTEXT.md,
  ADRs) inline as decisions crystallise. Use when the user wants to stress-test
  a plan against their project's language and documented decisions — the
  docs-aware variant of /grill-me.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "[plan or decision to grill]"
version: "1.0.0"
---

# Grill With Docs

Interview the user relentlessly about every aspect of their plan until shared understanding is reached. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide a recommended answer.

**What to grill:** $ARGUMENTS

Ask questions **one at a time**, waiting for feedback on each before continuing. If a question can be answered by exploring the codebase, explore the codebase instead — do not ask what you can resolve yourself.

---

## STEP 1: Locate the Domain Model

During codebase exploration, also look for existing documentation. Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

**Create files lazily** — only when there is something concrete to write. If no `CONTEXT.md` exists, create one when the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is needed.

---

## STEP 2: Grill — Single-Question Loop

Drive the conversation through these moves. Use one per turn, not all at once.

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. *"Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"*

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. *"You're saying 'account' — do you mean the Customer or the User? Those are different things."*

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: *"Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"*

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in `references/CONTEXT-FORMAT.md`.

`CONTEXT.md` MUST be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Only offer to create an ADR when ALL THREE are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in `references/ADR-FORMAT.md`. For multi-step ADR lifecycle work (creation, supersession, indexing), delegate to `/adr` after the user accepts.

---

## MUST DO

- Ask exactly one question per turn — wait for the answer before the next
- Recommend an answer to every question — don't leave the user to fill in the blanks
- Explore the codebase BEFORE asking what you can resolve yourself
- Update `CONTEXT.md` inline the moment a term crystallises — do not batch
- Use `references/CONTEXT-FORMAT.md` and `references/ADR-FORMAT.md` for file formats

## MUST NOT DO

- MUST NOT ask multiple questions in one turn — that creates noise and the user can only answer one well
- MUST NOT add implementation details to `CONTEXT.md` — glossary only
- MUST NOT offer an ADR unless all three criteria (hard-to-reverse + surprising + real-trade-off) hold
- MUST NOT batch `CONTEXT.md` updates — capture each term as it resolves, in the same turn
- MUST NOT skip the codebase cross-check when the user states behaviour — verify against code first
