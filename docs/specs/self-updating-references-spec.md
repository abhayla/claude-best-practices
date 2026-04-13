# Spec: Self-Updating References for Skills

## Meta
- **Author:** Claude Code
- **Date:** 2026-04-13
- **Status:** DRAFT
- **Version:** 1.0

---

## 1. Problem Statement

Skills with `references/` directories become stale as their domain evolves. Each invocation surfaces new domain knowledge — edge cases, API quirks, gotchas, patterns — that is lost when the session ends. Currently, no mechanism exists for skills to capture this knowledge back into their own references for future reuse.

The 5 specific gaps (identified via web research across 7 production systems):
1. No structured entry format — entries are vague and resist automated processing
2. No decay/pruning mechanism — references grow unbounded, old entries contradict new ones
3. No independent scoring before persistence — users rubber-stamp plausible entries
4. No rollback capability — bad knowledge can't be surgically reverted
5. No self-evaluation — no way to measure whether accumulated knowledge improves performance

## 2. Chosen Approach

**Hybrid Approach C + B:** Full integration with learn-n-improve pipeline when available, graceful fallback to standalone scored mode when not.

### Why This Approach

- **Root cause fix:** Skills are disconnected from the learning pipeline that already exists. This connects them.
- **Self-sustaining:** Inherits learn-n-improve's 90-day staleness detection, reuse_count thresholds, and meta-mode self-evaluation.
- **Autonomous:** learn-n-improve already runs at session end; knowledge flows through the existing pipeline.
- **Universal:** Graceful degradation to standalone mode ensures every project benefits, even without the full learning stack.
- **Propagation-safe:** No hard dependency on learn-n-improve; skills detect their environment and adapt at runtime.

### Rejected Alternatives

- **Approach A (Lightweight template only):** No quality gate beyond user approval; research confirms this is insufficient.
- **Approach B (Standalone scored only):** Works everywhere but creates a parallel knowledge store that duplicates and eventually conflicts with learnings.json.
- **Approach C (Full integration only):** Technically superior but breaks in projects without learn-n-improve installed.

---

## 3. Design

### 3.1 Data Model — Structured Knowledge Entries

Every knowledge entry uses a unified format portable between FULL and STANDALONE modes.

**Markdown entry format:**

```markdown
### [TYPE] Brief title
- **ID:** L-<sequential>
- **State:** CANDIDATE | ACTIVE | CONSOLIDATED | DEPRECATED
- **Temporal:** STATIC | DYNAMIC | ATEMPORAL
- **Scope:** global | <glob-pattern>
- **Date:** YYYY-MM-DD
- **Context:** <one phrase — when this applies>
- **Observation:** <one sentence — what was found, with evidence inline>
- **Application:** <one sentence — what to do differently>
- **Confidence:** <0.70–1.00>
- **Applied-In:** []
- **Source:** <skill name>
- **Supersedes:** <entry-id> | null
- **Tags:** <comma-separated>
```

**Type taxonomy:** `gotcha` | `pattern` | `fix` | `pitfall` | `decision` | `preference`

**State lifecycle:**

```
CANDIDATE → ACTIVE → CONSOLIDATED → DEPRECATED
                                        ↑
                                   (when superseded)
```

**Confidence thresholds:**

| Score | Meaning | Action |
|---|---|---|
| 0.95+ | Confirmed working | Auto-promote at reuse threshold |
| 0.85–0.94 | Strong evidence | Standard lifecycle |
| 0.70–0.84 | Reasonable inference | Flag for confirmation on next use |
| Below 0.70 | Insufficient | Admission gate rejects — do not persist |

**Two-tier file structure:**

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

**JSONL audit sidecar** (`references/CHANGELOG.jsonl`):

```jsonl
{"id":"L-042","ts":"2026-04-13T14:30:00Z","action":"CREATE","file":"references/api-patterns.md","confidence":0.92,"source":"skill-name"}
{"id":"L-042","ts":"2026-04-20T09:15:00Z","action":"APPLY","applied_in":"sync fix"}
{"id":"L-042","ts":"2026-05-01T11:00:00Z","action":"CONSOLIDATE","reason":"applied_in.length >= 3"}
{"id":"L-031","ts":"2026-05-01T11:00:00Z","action":"DEPRECATE","superseded_by":"L-042"}
```

**Integration with learn-n-improve JSON schema:**

| Entry Field | learn-n-improve Field | Notes |
|---|---|---|
| ID | `id` | Direct map |
| Type + Observation | `lesson` | Combine |
| Context | `error.context` | Direct map |
| Application | `fix.description` | Direct map |
| Confidence | `confidence` (new) | Added to schema |
| Applied-In | `reuse_count` + `applied_in` (new) | Enhanced |
| Source | `tags[0]` | Convention |
| Supersedes | `supersedes` (new) | Added to schema |
| State | Derived from `reuse_count` | 0=CANDIDATE, 1+=ACTIVE, 3+=CONSOLIDATED |

### 3.2 Runtime Detection & Mode Switching

Skills detect their environment at the start of the Reference Completeness Check step:

| learn-n-improve present? | Mode | Behavior |
|---|---|---|
| Yes | **FULL** | Write to learnings.json → learn-n-improve handles validation → promotes to references at reuse_count ≥ 2 |
| No | **STANDALONE** | Score with haiku subagent → present to user → write directly to references on approval |

**FULL mode flow:**

```
Detect gap → format entry → write to learnings.json → log to CHANGELOG.jsonl
→ learn-n-improve increments reuse_count across sessions
→ at reuse_count ≥ 2, Step 5.5 proposes reference promotion
→ user approves → entry written to reference file (Consolidated section)
```

**STANDALONE mode flow:**

```
Detect gap → admission gate → format entry → score with haiku subagent
→ KEEP/REVIEW entries presented to user → user approves
→ write to reference file (Active Observations section) → log CHANGELOG.jsonl
→ consolidation check (if triggers fire)
```

**Scoring subagent prompt (STANDALONE mode):**

```
Score this knowledge entry for persistence:
Entry: "<entry text>"

Evaluate (yes/partial/no):
1. Specificity: Actionable for someone reading cold?
2. Reusability: Applies to future invocations, not a one-off?
3. Non-obvious: A competent developer would NOT already know this?

Verdict: KEEP | REVIEW | DISCARD
Reason: <one sentence>
```

**Mode upgrade path (STANDALONE → FULL):** When learn-n-improve is detected for the first time in a project with existing CHANGELOG.jsonl entries, import existing entries into learnings.json with reuse_count derived from Applied-In array length.

### 3.3 Admission Gate

Applied before scoring in both modes. Explicit exclusion criteria:

**DO NOT record:**
- Generic programming knowledge (use try/catch, validate inputs)
- Temporary workarounds for known bugs with fix dates
- User-specific paths, credentials, or environment details
- Information already in CLAUDE.md, `.claude/rules/`, or existing references
- Opinions without evidence
- One-time debugging artifacts (stack traces, log dumps)
- STATIC observations scoped to a single session

### 3.4 Consolidation Triggers (STANDALONE mode)

FULL mode inherits learn-n-improve's existing staleness detection and knowledge_test step. STANDALONE mode runs these triggers after writing entries:

| Trigger | Condition | Action |
|---|---|---|
| Count | CANDIDATE + ACTIVE entries > 50 per file | LLM consolidation pass |
| Staleness | DYNAMIC entry > 30 days with Applied-In empty | Flag `[REVIEW NEEDED]` |
| Conflict | Two ACTIVE entries contradict on same Scope | Surface for resolution |
| Promotion | Applied-In length ≥ 3 AND confidence ≥ 0.85 | Move to Consolidated Principles |
| Token budget | All ACTIVE entries in one file > ~2,000 tokens | Compress oldest entries |

### 3.5 The Protocol File

The full Reference Completeness Check protocol lives in a single reference file (`references/self-update-protocol.md`, ~120 lines) that writing-skills copies into each new skill's `references/` directory during authoring.

Protocol contains: mode detection → entry format → admission gate → scoring (both modes) → consolidation triggers → version bump.

Skills embed a compact pointer:

```markdown
## STEP N: Reference Completeness Check

Check whether this invocation surfaced knowledge not yet in references.

**Read:** `references/self-update-protocol.md` for the full detection,
scoring, gating, and consolidation workflow.
```

### 3.6 Files Modified

| File | Action | Version Change |
|---|---|---|
| `.claude/skills/writing-skills/SKILL.md` | Replace Step 2.6, update Step 5.1, MUST DO, MUST NOT DO | 3.1.0 → 3.2.0 |
| `.claude/skills/writing-skills/references/self-update-protocol.md` | **New file** — the full protocol | — |
| `.claude/skills/skill-evaluator/SKILL.md` | Replace Step 0.4, Step 3.4b, report template, MUST DO | 2.2.0 → 2.3.0 |
| `core/.claude/skills/writing-skills/SKILL.md` | Sync from `.claude/` | 3.2.0 |
| `core/.claude/skills/writing-skills/references/self-update-protocol.md` | Sync from `.claude/` | — |
| `core/.claude/skills/skill-evaluator/SKILL.md` | Sync from `.claude/` | 2.3.0 |

---

## 4. Requirement Tiers

### Must Have (this implementation)

- REQ-M001: Structured entry format with ID, State, Type, Confidence, Scope, Application, Applied-In, Supersedes
- REQ-M002: Runtime mode detection (FULL vs STANDALONE) based on learn-n-improve presence
- REQ-M003: Admission gate with explicit exclusion criteria
- REQ-M004: Haiku subagent scoring in STANDALONE mode (KEEP/REVIEW/DISCARD)
- REQ-M005: User approval gate before any reference file writes
- REQ-M006: CHANGELOG.jsonl audit sidecar for rollback and mode upgrade
- REQ-M007: Two-tier reference file structure (Consolidated Principles + Active Observations)
- REQ-M008: Protocol file (`self-update-protocol.md`) copied into every authored skill with references
- REQ-M009: Version bump (patch) after reference modifications
- REQ-M010: skill-evaluator pre-flight checks for protocol presence and correctness
- REQ-M011: skill-evaluator output evaluation testing both FULL and STANDALONE behavior

### Nice to Have (follow-up)

- REQ-N001: Dependency resolution in `recommend.py` — expand `dependencies` field during provisioning
- REQ-N002: Consolidation pass with LLM-driven merge/prune when triggers fire
- REQ-N003: Mode upgrade import (STANDALONE → FULL) when learn-n-improve is later installed
- REQ-N004: Token-budget consolidation trigger (requires token estimation utility)
- REQ-N005: Confidence field added to learn-n-improve's JSON schema
- REQ-N006: `applied_in` array added to learn-n-improve's JSON schema
- REQ-N007: `supersedes` field added to learn-n-improve's JSON schema

### Out of Scope

- Vector DB / semantic memory storage — too heavy for markdown-based skills
- Full telemetry/scoring infrastructure (singularity-claude level) — over-engineered
- Retroactively updating all 155 existing skills — only new skills authored via `/writing-skills` get the mechanism
- Bitemporal timestamps (Valid-From/Valid-Until) — git history suffices
- Statement-Type classification (FACT/OPINION/PREDICTION) — admission gate handles this
- `_shared/` directory for cross-skill references — each skill gets its own protocol copy

---

## 5. Open Questions

1. **learn-n-improve schema changes (REQ-N005/N006/N007):** Adding `confidence`, `applied_in`, and `supersedes` fields to the JSON schema is a breaking change. Should this be a separate PR with its own test coverage?

2. **CHANGELOG.jsonl in git:** Should the audit log be gitignored (ephemeral per-machine) or committed (shared across team)? Committing enables team-wide rollback but adds noise to diffs.

3. **Haiku availability:** STANDALONE mode requires spawning a haiku subagent. In environments where only one model tier is available, the scorer would use the same model as the skill — introducing the evaluator bias the research warned about. Acceptable trade-off?

4. **Existing skills with references:** Should writing-skills offer to retrofit the protocol into existing skills during update mode (Step 1.3)?

---

## 6. Success Criteria

| Criterion | Measurement | Target |
|---|---|---|
| Skills get smarter | Reference files grow with validated entries after invocations | ≥1 new entry per 5 invocations on average |
| No quality degradation | Consolidated Principles section contains only reuse-validated entries | 0 entries with Applied-In empty in Consolidated |
| Rollback works | Any reference update can be traced and reverted via CHANGELOG.jsonl + git | 100% of writes logged in CHANGELOG.jsonl |
| Noise filtered | Admission gate + scorer rejects generic/ephemeral entries | ≥50% of raw observations filtered before reaching user |
| Self-evaluation | FULL mode: learn-n-improve meta-mode reports learning effectiveness; STANDALONE mode: consolidated/total ratio tracked | Consolidated ratio increases over time |
| Propagation works | Updated skills function correctly in downstream projects with and without learn-n-improve | 0 failures from missing dependencies |
| skill-evaluator catches gaps | Pre-flight detects missing protocol; output eval tests both modes | All 10 pre-flight checks + 5 behavior tests pass |
