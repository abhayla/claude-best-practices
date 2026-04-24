---
name: skill-authoring-workflow
description: >
  Author, validate, and register new skills, agents, and rules end-to-end
  as a skill-at-T0 orchestrator (Phase 3.8 of subagent-dispatch-platform-limit
  remediation — the final workflow-master retirement). The skill body IS
  the orchestrator — runs in the user's T0 session and drives: overlap-check →
  author → validate → register. Invokes sub-skills (/writing-skills,
  /claude-guardian, /skill-master) via Skill(); optionally dispatches
  skill-author-agent via Agent() at T0 for richer draft generation. Use
  when creating new patterns from scratch or converting session learnings
  into skills.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<skill name, learning reference, or pattern description>"
version: "2.0.0"
---

# /skill-authoring-workflow — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `skill-authoring-master-agent` is NOT dispatched (deprecated
Phase 3.8, 2026-04-25 — the last workflow-master retirement); its
orchestration lives here.

**Why skill-at-T0:** Same platform constraint Phases 3.1–3.7 — dispatched
subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents)). Legacy
`skill-authoring-master-agent` → `skill-author-agent` (T2) dispatch
silently inlined.

**Critical:** Validation is BLOCKING — no pattern ships without passing all
quality checks. Overlap detection MUST run BEFORE authoring begins.

**Input:** `$ARGUMENTS` — skill name, learning reference (e.g., `proposal-4`
pointing at `.claude/skill-proposals/`), or free-form pattern description.

---

## CLI Signature

```
/skill-authoring-workflow <name | proposal-ref | description>
                          [--type=workflow|reference|rule|agent]
                          [--dry-run] [--force-overlap]
```

| Argument / Flag | Default | Meaning |
|-----------------|---------|---------|
| input | (required) | Skill name, `.claude/skill-proposals/<id>` reference, or description |
| `--type` | workflow | `workflow` \| `reference` (skill types) \| `rule` \| `agent` |
| `--dry-run` | off | Draft + validate, don't write anywhere |
| `--force-overlap` | off | Proceed with authoring even if overlap check flags similar existing patterns |

---

## STEP 1: INIT + OVERLAP_CHECK

1. **Parse args.** Resolve `input` to one of: concrete name, proposal path, or description.
2. **Read config.** `config/workflow-contracts.yaml` → `workflows.skill-authoring`.
   `master_agent` should be null; `sub_orchestrators` empty (Phase 3.8).
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state** at `.workflows/skill-authoring/state.json` (schema 2.0.0):
   `step_status`, `dispatches_used: 0`, `target_type: "<workflow|...>"`,
   `overlap_flags: []`.
5. **Overlap check (MUST run before authoring).** Scan existing
   `core/.claude/skills/`, `core/.claude/agents/`, `core/.claude/rules/` and
   `registry/patterns.json` for similar names + descriptions. Use description
   similarity (substring + keyword matching) + file structure comparison.
   - If overlaps found AND `--force-overlap` NOT set: report matches,
     recommend enhancing existing pattern instead of creating new. User
     must explicitly approve new authoring to proceed.
   - If `--force-overlap`: record in state but proceed.
6. Append INIT + OVERLAP_CHECK events.

---

## STEP 2: AUTHOR

### 2a: Optional skill-author-agent dispatch for richer drafts

If input is a proposal reference with substantial evidence OR the description
is complex enough to warrant deeper investigation:

```
Agent(subagent_type="skill-author-agent", prompt="""
## Workflow: skill-authoring
## Run ID: <run_id>
## Target type: <workflow|reference|rule|agent>
## Input: <resolved input>
## Overlap findings: <list>
## Project context: <stack + conventions>

Draft the full pattern body per pattern-structure.md. Apply the 6-step
/writing-skills protocol. Return structured contract:
{ "gate": "PASSED|FAILED", "draft_path": "<staging path>",
  "frontmatter": {...}, "body_sections": [...], "self_contained": <bool>,
  "summary": "<line>" }
""")
```

Increment `dispatches_used` by 1. Merge the draft contract into state.

### 2b: /writing-skills protocol (always runs)

```
Skill("/writing-skills", args="author <resolved-input> --type=<type>")
```

`/writing-skills` implements the 6-step authoring protocol: frontmatter
design, step skeletons, trigger design, quality checks, size limits,
self-containment verification. Writes draft to
`core/.claude/skills/<name>/SKILL.md` (or agents/ / rules/ based on `--type`).

Capture draft path into `state.artifacts.draft`.

---

## STEP 3: VALIDATE (BLOCKING)

```
Skill("/claude-guardian", args="validate <draft path> --strict")
```

`/claude-guardian --strict` runs all pattern quality gates:
- pattern-structure.md (required frontmatter fields)
- pattern-portability.md (no hardcoded paths, least-privilege tools)
- pattern-self-containment.md (no placeholders, size limits, cross-refs)
- Registry fit (overlap + tier assignment)

Produces `test-results/skill-authoring-validation.json`.

Gate: if `verdict != "PASSED"` → `step_status.VALIDATE = blocked`,
transition to STEP 5 REPORT with BLOCKED verdict. No silent FAIL → ship path.
User can iterate: fix the draft, re-run STEP 3 only.

If `--dry-run`: always stop after validate, regardless of outcome.

---

## STEP 4: REGISTER

Skip if STEP 3 was blocked OR `--dry-run`.

```
Skill("/skill-master", args="register <draft path>")
```

`/skill-master register` does:
- Add entry to `registry/patterns.json` with hash, type, tier, etc.
- Append an entry to `registry/changelog.md`
- Register triggers if any
- Update docs dashboard (regenerate via `generate_docs.py`)

Capture registry entry into `state.artifacts.registered`.

---

## STEP 5: REPORT

1. **Finalize state.** Write `test-results/skill-authoring-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "PUBLISHED | BLOCKED | DRY_RUN_OK | DRY_RUN_FAILED",
     "target_type": "<workflow|reference|rule|agent>",
     "artifacts": {
       "draft": "<path>",
       "validation": "<path>",
       "registered": <bool>
     },
     "overlap_check": { "matches": <n>, "forced": <bool> },
     "validation_verdict": "PASSED | WARNED | FAILED",
     "quality_score": <0-100>,
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Skill Authoring Workflow: <PUBLISHED | BLOCKED | DRY_RUN_OK>
     Run ID: <run_id>
     Target: <type> <name>
     Overlap matches: <N>
     Validation: <PASSED | WARNED | FAILED>
     Quality score: <N>/100
     Registry: <added | SKIPPED>
   ============================================================
   ```
3. **Handoff suggestions:**
   - If PUBLISHED: `Next: commit the new pattern + /code-review-workflow`
   - If BLOCKED: surface specific validation failures + suggest fixes
   - If DRY_RUN_OK: `Next: re-run without --dry-run to publish`

---

## CRITICAL RULES

- MUST run at T0 — skill body is injected into user's session. Dispatching
  this as a worker strips `Agent` at runtime and STEP 2a dispatch silently
  inlines.
- MUST NOT dispatch `skill-authoring-master-agent` (deprecated 2026-04-25,
  2-cycle window — the final workflow-master retirement).
- MUST run OVERLAP_CHECK (STEP 1 sub-step 5) BEFORE authoring. Creating
  duplicate skills fragments knowledge (rule-curation.md, pattern-self-
  containment.md).
- MUST NOT bypass VALIDATE (STEP 3) — quality gates are mandatory and
  BLOCKING. No silent FAIL → ship path.
- MUST use `/writing-skills` for the authoring step — never direct file
  write. The 6-step protocol catches frontmatter + structural errors early.
- MUST NOT auto-register a pattern that failed validation — unvalidated
  patterns corrupt the registry and the downstream sync pipeline.
- MUST respect `--dry-run` — no file writes or registry changes when set.
- MUST write `.workflows/skill-authoring/state.json` + `events.jsonl`
  after every step transition.
