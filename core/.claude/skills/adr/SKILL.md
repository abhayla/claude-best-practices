---
name: adr
description: >
  Create and manage Architecture Decision Records (ADRs). Initialize an ADR directory,
  create new ADRs from the Michael Nygard template, list existing decisions, supersede
  or deprecate old ADRs, and generate an ADR index. Supports both interactive and
  argument-driven usage.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<new \"Decision Title\" | list | index | supersede <ADR-number> | deprecate <ADR-number>>"
version: "1.0.0"
---

# Architecture Decision Records (ADR)

Create, manage, and index Architecture Decision Records following the Michael Nygard
template. ADRs capture the context, decision, and consequences of architecturally
significant choices.

**Arguments:** $ARGUMENTS

---

## STEP 1: Parse Command

| Command | Action |
|---------|--------|
| `new "Decision Title"` | Create a new ADR |
| `list` | List all existing ADRs with status |
| `index` | Generate or update `docs/decisions/index.md` |
| `supersede <N>` | Mark ADR-N as superseded, prompt for replacement ADR |
| `deprecate <N>` | Mark ADR-N as deprecated |
| No argument | Interactive — ask what the user wants to do |

---

## STEP 2: Initialize ADR Directory (If Needed)

Check if the ADR directory exists. The default location is `docs/decisions/`. When
using `/doc-structure-enforcer` with pipeline stages, ADRs belong in
`docs/stages/stage-2-plan/output/` instead — check `.doc-structure.yml` for the
configured location.

```bash
# Default location (standalone projects)
mkdir -p docs/decisions

# Or pipeline-aligned location (when using doc-structure-enforcer)
# mkdir -p docs/stages/stage-2-plan/output
```

If the ADR directory already exists, scan for existing ADRs and determine the next
sequence number:

```bash
# Works for either location — adjust path as needed
ls docs/decisions/[0-9]*.md 2>/dev/null | sort -V | tail -1
```

Extract the highest number and increment by 1 for the next ADR.

---

## STEP 3: Create New ADR (`new`)

### 3.1 Generate Filename

Format: `NNNN-kebab-case-title.md` where NNNN is zero-padded sequence number.

Example: `0001-use-postgresql-for-persistence.md`

### 3.2 Gather Context

Before writing, gather information by asking or inferring:

| Field | Source |
|-------|--------|
| **Title** | From the argument |
| **Date** | Today's date |
| **Status** | `Accepted` (default), or `Proposed` if the user indicates it's a draft |
| **Context** | Ask the user, or infer from recent code changes and discussions |
| **Decision** | Ask the user for the chosen approach |
| **Alternatives** | Ask the user what was considered and rejected |
| **Consequences** | Derive from the decision — what becomes easier, what becomes harder |

### 3.3 Write ADR Using Michael Nygard Template

```markdown
# N. Title

**Date:** YYYY-MM-DD

**Status:** Accepted

## Context

What is the issue that we're seeing that is motivating this decision or change?
Describe the forces at play — technical, political, social, project constraints.

## Decision

What is the change that we're proposing and/or doing?
State the decision in full sentences, with active voice: "We will..."

## Consequences

What becomes easier or more difficult to do because of this change?
List both positive and negative consequences. Be honest about trade-offs.

### Positive
- ...

### Negative
- ...

### Neutral
- ...
```

### 3.4 Extended Template Fields (Optional)

If the decision warrants it, include additional sections:

```markdown
## Alternatives Considered

### Alternative 1: <Name>
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

### Alternative 2: <Name>
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

## References
- [Link to relevant discussion, RFC, or issue]
- [Link to prototype or proof of concept]
```

---

## STEP 4: List ADRs (`list`)

Scan the ADR directory and produce a status table:

```bash
# Extract title and status from each ADR file
for f in docs/decisions/[0-9]*.md; do
  number=$(basename "$f" | grep -oP '^\d+')
  title=$(head -1 "$f" | sed 's/^# //')
  status=$(grep -oP '(?<=\*\*Status:\*\* ).*' "$f" | head -1)
  echo "| $number | $title | $status |"
done
```

Output format:

```markdown
## Architecture Decision Records

| # | Decision | Status | Date |
|---|----------|--------|------|
| 0001 | Use PostgreSQL for persistence | Accepted | 2025-06-15 |
| 0002 | Adopt event sourcing for orders | Superseded by 0005 | 2025-07-01 |
| 0003 | Use JWT for API authentication | Accepted | 2025-08-10 |
| 0004 | Migrate from REST to GraphQL | Deprecated | 2025-09-01 |
| 0005 | Use CQRS for order management | Accepted | 2025-10-15 |
```

---

## STEP 5: Supersede or Deprecate (`supersede` / `deprecate`)

### Supersede

1. Read the target ADR
2. Update its status: `**Status:** Superseded by [ADR-NNNN](NNNN-new-decision.md)`
3. Create the replacement ADR (triggers Step 3) with context referencing the old decision:
   `"This supersedes [ADR-N](NNNN-old-decision.md) because..."`

### Deprecate

1. Read the target ADR
2. Update its status: `**Status:** Deprecated`
3. Add a note at the top explaining why:
   `> **Note:** This decision has been deprecated as of YYYY-MM-DD. Reason: ...`

In both cases, update the ADR index (Step 6) after modification.

---

## STEP 6: Generate Index (`index`)

Create or update `docs/decisions/index.md`:

```markdown
# Architecture Decision Records

This directory contains the Architecture Decision Records (ADRs) for this project.

ADRs capture architecturally significant decisions along with their context and
consequences. They are numbered sequentially and never deleted — superseded or
deprecated decisions remain for historical context.

## Decisions

| # | Decision | Status | Date |
|---|----------|--------|------|
| [0001](0001-use-postgresql.md) | Use PostgreSQL for persistence | Accepted | 2025-06-15 |
| [0002](0002-event-sourcing.md) | Adopt event sourcing for orders | Superseded by [0005](0005-cqrs.md) | 2025-07-01 |

## Statuses

| Status | Meaning |
|--------|---------|
| **Proposed** | Under discussion, not yet decided |
| **Accepted** | Decision made and in effect |
| **Superseded** | Replaced by a newer decision (linked) |
| **Deprecated** | No longer relevant, kept for history |

## Creating a New ADR

Use `/adr new "Decision Title"` to create a new ADR from the standard template.
```

---

## STEP 7: Verify Integrity

After any create/modify operation, run these checks:

1. **Sequential numbering** — No gaps or duplicates in ADR numbers
2. **Status consistency** — Superseded ADRs link to an existing replacement
3. **Cross-references** — All `[ADR-N]` links resolve to existing files
4. **Index freshness** — `index.md` matches the actual ADR files on disk

Report any issues found.

---

## MUST DO

- MUST use sequential numbering starting from 0001
- MUST use the Michael Nygard template structure (Context, Decision, Consequences)
- MUST never delete ADRs — supersede or deprecate instead, preserving history
- MUST include the date and status in every ADR
- MUST update the index after every create/supersede/deprecate operation
- MUST link superseded ADRs to their replacement bidirectionally
- MUST write decisions in active voice ("We will..." not "It was decided...")
- MUST document both positive and negative consequences honestly

## MUST NOT DO

- MUST NOT delete or overwrite existing ADRs — append, supersede, or deprecate only
- MUST NOT reuse ADR numbers — even if an ADR is deprecated, its number is retired
- MUST NOT create ADRs for trivial decisions — reserve for architecturally significant choices
- MUST NOT backdate ADRs — use the actual date the decision was recorded
- MUST NOT leave the Consequences section empty — every decision has trade-offs
- MUST NOT mix multiple decisions into one ADR — one decision per record

## See Also

- `/doc-structure-enforcer` — When using pipeline stages, ADRs belong in `docs/stages/stage-2-plan/output/` instead of `docs/decisions/`
- `/diataxis-docs` — ADRs belong in the "explanation" Diataxis category; use this to integrate ADRs into the broader docs structure
- `/doc-staleness` — Detect stale ADR references after restructuring or when linked decisions change
- `/changelog-contributing` — Major architectural decisions often correspond to changelog entries
- `/api-docs-generator` — API design decisions captured as ADRs often reference API documentation
- `docs-manager-agent` — Orchestrates documentation updates, can delegate ADR creation to this skill
