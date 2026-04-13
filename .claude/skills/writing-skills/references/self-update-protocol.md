# Self-Update Protocol: Reference Completeness Check

This protocol is copied into your skill's `references/` directory by `/writing-skills`.
It defines the workflow for detecting and persisting new domain knowledge during skill invocations.

## N.1 Detect Pipeline Mode

1. Check if `.claude/skills/learn-n-improve/SKILL.md` exists in the project
2. Check if this skill's `references/CHANGELOG.jsonl` exists

| learn-n-improve? | CHANGELOG.jsonl? | Mode |
|---|---|---|
| Yes | * | **FULL** — knowledge flows through learnings.json |
| No | * | **STANDALONE** — knowledge scored and persisted directly |

Create `references/CHANGELOG.jsonl` if it does not exist.

## N.2 Scan Execution Context

Review the conversation for knowledge worth capturing:

| Scan For | Example |
|---|---|
| Domain patterns discovered | "All endpoints require X header" |
| Edge cases encountered and resolved | "Timeout at 30 items, batch at 10" |
| API behaviors differing from docs | "v2 flag required, undocumented" |
| Corrections to assumptions in existing references | "Reference says X, but Y is true now" |
| Recurring failure patterns | "This error always means Z" |

## N.3 Admission Gate

**DO NOT record:**
- Generic programming knowledge (use try/catch, validate inputs)
- Temporary workarounds for known bugs with fix dates
- User-specific paths, credentials, or environment details
- Information already in CLAUDE.md, `.claude/rules/`, or existing references
- Opinions without evidence
- One-time debugging artifacts (stack traces, log dumps)
- STATIC observations scoped to a single session

If nothing passes the gate → report "References are up to date" → skip to next step.

## N.4 Format Entries

For each observation that passes the gate, format as:

```markdown
### [TYPE] Brief title
- **ID:** L-<next-sequential>
- **State:** CANDIDATE
- **Temporal:** STATIC | DYNAMIC | ATEMPORAL
- **Scope:** global | <glob-pattern matching affected files>
- **Date:** <today YYYY-MM-DD>
- **Context:** <one phrase — when this applies>
- **Observation:** <one sentence — what was found, with evidence inline>
- **Application:** <one sentence — what to do differently>
- **Confidence:** <0.70–1.00>
- **Applied-In:** []
- **Source:** <this skill's name>
- **Supersedes:** <ID of entry this replaces, or null>
- **Tags:** <comma-separated>
```

**Type taxonomy:**

| Type | When to Use |
|---|---|
| `gotcha` | Edge case / surprising behavior that causes failures |
| `pattern` | Reusable approach that works consistently |
| `fix` | Bug resolution pattern |
| `pitfall` | Common mistake to avoid |
| `decision` | Architectural choice with rationale |
| `preference` | Team/project convention (not a universal truth) |

**Confidence thresholds:**

| Score | Meaning | Action |
|---|---|---|
| 0.95+ | Confirmed working | Auto-promote at reuse threshold |
| 0.85–0.94 | Strong evidence | Standard lifecycle |
| 0.70–0.84 | Reasonable inference | Flag for confirmation on next use |
| Below 0.70 | Insufficient | Admission gate rejects — do not persist |

**State lifecycle:** `CANDIDATE → ACTIVE → CONSOLIDATED → DEPRECATED`

## N.5 Score and Gate

### FULL Mode (learn-n-improve present)

1. Map each entry to learn-n-improve JSON schema:
   - `lesson` ← Type + ": " + Observation
   - `error.context` ← Context
   - `fix.description` ← Application
   - `tags` ← Tags array + Source
   - `reuse_count` ← 0
2. Write to `.claude/learnings.json`
3. Log `CREATE` action to `references/CHANGELOG.jsonl`:
   ```jsonl
   {"id":"L-042","ts":"2026-04-13T14:30:00Z","action":"CREATE","file":"references/domain.md","confidence":0.92,"source":"skill-name"}
   ```
4. Report: "N entries captured in learnings.json — will promote to references after reuse_count ≥ 2."
5. **Do NOT write to reference files yet** — learn-n-improve handles promotion via Step 5.5 constraint injection

### STANDALONE Mode (learn-n-improve absent)

1. Score each entry with a haiku subagent:
   ```
   Agent(model="haiku", prompt="Score this knowledge entry for persistence
   in a skill's reference file.

   Entry: {entry_text}

   Evaluate (yes/partial/no):
   1. Specificity: Actionable for someone reading cold?
   2. Reusability: Applies to future invocations, not a one-off?
   3. Non-obvious: A competent developer would NOT already know this?

   Verdict: KEEP | REVIEW | DISCARD
   Reason: <one sentence>")
   ```

2. Filter results:

   | Verdict | Action |
   |---|---|
   | KEEP | Include in presentation to user |
   | REVIEW | Include with scorer's concern flagged |
   | DISCARD | Drop — report reason to user |

3. Present surviving entries to user:
   ```
   ## Proposed Reference Updates

   | # | Type | Title | Target File | Action | Score |
   |---|---|---|---|---|---|
   | 1 | gotcha | API v2 flag | references/api-patterns.md | Append | KEEP |
   | 2 | pattern | Batch at 10 | references/performance.md | New file | KEEP |

   Discarded (scored below threshold):
   - "Use descriptive names" → DISCARD: generic programming knowledge

   Proceed with updates? [y/n/select]
   ```

4. **Wait for user approval.** Do NOT write without confirmation.

5. On approval:
   - Write approved entries to target reference file (Active Observations section)
   - If entry supersedes an existing entry: set old entry State to `DEPRECATED`, add `Superseded-By` pointer
   - Log all actions to `references/CHANGELOG.jsonl`

**Two-tier reference file structure:**

```markdown
## Consolidated Principles
<!-- State: CONSOLIDATED. Proven across 3+ applications. -->
- <standing rules derived from validated entries>

## Active Observations
<!-- State: CANDIDATE or ACTIVE. Under evaluation. -->
### [type] Title
- **ID:** L-042
- ...
```

## N.6 Consolidation Check (STANDALONE mode only)

FULL mode inherits learn-n-improve's existing staleness detection. STANDALONE mode checks these triggers after writing entries:

| Trigger | Condition | Action |
|---|---|---|
| Count | CANDIDATE + ACTIVE entries > 50 per file | LLM consolidation pass |
| Staleness | DYNAMIC entry > 30 days with Applied-In empty | Flag `[REVIEW NEEDED]` |
| Conflict | Two ACTIVE entries contradict on same Scope | Surface for resolution |
| Promotion | Applied-In length ≥ 3 AND confidence ≥ 0.85 | Move to Consolidated Principles |
| Token budget | All ACTIVE entries in one file > ~2,000 tokens | Compress oldest entries |

If any trigger fires:
1. Run consolidation: promote, merge, flag, or deprecate as appropriate
2. Present proposed changes to user before applying
3. Log all actions to `references/CHANGELOG.jsonl`

If no triggers fire → skip.

## N.7 Version Bump

If any reference files were modified in this step:
- Bump the skill's **patch version** in SKILL.md frontmatter (e.g., 1.2.3 → 1.2.4)
- Log `VERSION_BUMP` in CHANGELOG.jsonl
