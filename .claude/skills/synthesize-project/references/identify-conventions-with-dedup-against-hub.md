# STEP 3: Identify Conventions (with Dedup Against Hub)

## Table of Contents
- [Rules](#rules--conventions-worth-encoding-as-always-on-constraints)
- [Skills](#skills--workflows-worth-encoding-as-on-demand-procedures)
- [Agents](#agents--tasks-worth-delegating-to-a-specialized-subagent)
- [NOT worth encoding](#not-worth-encoding-any-type)
- [Identification checklist](#identification-checklist)
- [Dedup against hub patterns](#dedup-against-hub-patterns)
- [Present findings to user](#present-findings-to-user-after-dedup)

### Rules — conventions worth encoding as always-on constraints

A convention is worth a **rule** when:
- It's a consistent pattern followed across multiple files
- Breaking it would cause bugs, inconsistency, or confusion
- A new developer (or AI) working on the project might not know about it
- It's specific to THIS project, not a generic best practice

### Skills — workflows worth encoding as on-demand procedures

A convention is worth a **skill** when:
- It's a multi-step procedure that developers repeat (e.g., "add a new DB model", "create a new feature module", "run and debug E2E tests")
- The steps are project-specific — not just "run tests" but "run tests in this specific order with these specific fixtures and this specific setup"
- Getting the steps wrong causes subtle bugs (e.g., forgetting one of 5 locations when adding a model)
- It involves coordination across multiple files or modules

### Agents — tasks worth delegating to a specialized subagent

A convention is worth an **agent** when:
- It's a review or analysis task that benefits from a dedicated persona (e.g., "review this meal generation output for dietary constraint violations")
- It requires reading many files and producing a structured assessment
- It's a recurring quality gate specific to this project's domain

### NOT worth encoding (any type)

- Already enforced by a linter, formatter, or type checker
- A language/framework default documented in official docs
- A one-off implementation detail in a single file
- A generic best practice (e.g., "write tests", "use descriptive names")

### Identification checklist

For each candidate, note:
1. **Name** — short descriptive name
2. **Hypothesis** — what you believe the convention is
3. **Evidence needed** — which specific source files to read to confirm (max 5 per convention)
4. **Category** — `correctness` | `safety` | `consistency` | `testing` | `deployment`
5. **Pattern type** — choose using this decision table:

   | Signal | Type |
   |--------|------|
   | "Always do X when working on Y files" | **rule** |
   | "When you need to do X, follow these N steps" | **skill** |
   | "Review/analyze X and produce a structured report" | **agent** |
   | Multi-step procedure across 3+ files | **skill** |
   | A constraint that applies to every edit in scope | **rule** |
   | A task that benefits from a dedicated persona/focus | **agent** |

6. **Confidence** — `high` (seen in 5+ files) | `medium` (seen in 2-4 files) | `low` (seen in 1 file)

**Aim for a mix of types.** A project with only rules is missing workflow automation. A project with only skills is missing guardrails. Target roughly: 40-60% rules, 30-50% skills, 0-20% agents.

Drop any candidate with `low` confidence immediately. A missing pattern is better than a wrong one.

### Dedup against hub patterns

Before presenting findings to the user, compare each candidate convention against the hub patterns copied in Step 1 (if Step 1 ran). If a hub pattern already covers the convention (even generically), check whether the project-specific version adds genuine value beyond what the hub provides. Drop conventions where the hub pattern is sufficient.

**Examples of "hub covers it":**
- Hub has `android-arch` skill covering clean architecture → don't generate `module-dependency-direction` rule unless project has non-standard dependency rules
- Hub has `testing.md` rule → don't generate test fixture rule unless project has unique fixture conventions

**Examples of "project-specific adds value":**
- Hub has generic `db-migrate` skill → project has 5-location model import rule (completely unique)
- Hub has generic `tdd` skill → project has specific `BaseViewModel<T : BaseUiState>` pattern

Print the dedup results:

```
Hub dedup: [N] conventions dropped (already covered by hub patterns):
- [name]: covered by hub's [pattern-name] ([reason])
- [name]: covered by hub's [pattern-name] ([reason])

Remaining after dedup: [N] conventions to investigate
```

**If `--update` mode:** Compare candidates against existing patterns using the staleness detection below. Only keep:
- New conventions not covered by existing patterns
- Stale patterns that need refreshing (will be regenerated in Steps 5-6)

#### Staleness detection (--update mode only)

For each existing pattern with `synthesized: true`:
1. Extract the evidence file paths mentioned in the pattern body
2. Check if those files still exist (local: `test -f`; remote: check against tree from Step 0)
3. If evidence files exist, read them and verify the convention still holds
4. Mark as **stale** if: evidence files are deleted/renamed, OR the convention no longer matches the code (>30% counter-evidence)
5. Mark as **intentionally removed** if: the pattern file itself was deleted by the user (not present in `.claude/` but was in a previous synthesis run — check git log if available)

Report staleness findings:

```
Update check:
  New conventions:  [N]
  Stale (refresh):  [N] — [list names and why]
  Current (skip):   [N] — already up to date
  Removed by user:  [N] — will not regenerate (intentional deletion)
```

### Present findings to user (after dedup)

Print the remaining candidate list as a table for the user to review:

```
Candidate Conventions after hub dedup ([N] remaining):

| # | Name | Type | Category | Confidence | Hypothesis |
|---|------|------|----------|------------|------------|
| 1 | ... | rule | correctness | high | ... |
| 2 | ... | skill | consistency | medium | ... |
| 3 | ... | agent | testing | medium | ... |

Type mix: [N] rules, [N] skills, [N] agents
```

Then list which conventions were dropped and why:

```
Dropped ([N]):
- [name]: low confidence (seen in 1 file only)
- [name]: already enforced by [linter/formatter]
- [name]: generic best practice, not project-specific
- [name]: covered by hub pattern [pattern-name]
```

**Wait for user acknowledgment** before proceeding to Step 4. The user may want to add, remove, or reprioritize conventions.
