---
name: documentation-workflow
description: >
  Orchestrate project documentation maintenance end-to-end as a skill-at-T0
  orchestrator (Phase 3.5 of subagent-dispatch-platform-limit remediation).
  The skill body IS the orchestrator — runs in the user's T0 session and
  drives: ADR creation → API docs generation → structure enforcement →
  staleness audit. Invokes sub-skills (/adr, /api-docs-generator,
  /doc-structure-enforcer, /doc-staleness) via Skill(); optionally
  dispatches the docs-drafting worker via Agent() at T0 for bulk content
  generation when the structure audit reveals substantial missing content.
  Use after architecture decisions, PR merges, or on a scheduled cadence.
type: workflow
triggers:
  - update documentation
  - documentation workflow
  - generate docs
  - doc maintenance
  - docs pipeline
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "[scope: 'all' | 'adr' | 'api' | 'structure' | 'staleness']"
version: "2.0.0"
---

# /documentation-workflow — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The retired `documentation-master-agent` is NOT dispatched (deprecated
Phase 3.5, 2026-04-25); its orchestration lives here.

**Why skill-at-T0:** Platform constraint documented in Phases 3.1–3.4 —
dispatched subagents don't receive the `Agent` tool
([Anthropic docs](https://code.claude.com/docs/en/sub-agents)).

**Input:** `$ARGUMENTS` — optional scope. Default is `all`.

---

## CLI Signature

```
/documentation-workflow [scope] [--dry-run] [--skip-staleness]
```

| Argument / Flag | Default | Meaning |
|-----------------|---------|---------|
| `scope` | `all` | `all` \| `adr` \| `api` \| `structure` \| `staleness` |
| `--dry-run` | off | Produce proposed changes without writing them |
| `--skip-staleness` | off | Skip the staleness audit (STEP 5) |

---

## STEP 1: INIT

1. **Parse args.** Normalize `scope` to one of the 5 values.
2. **Read config** `config/workflow-contracts.yaml` → `workflows.documentation`.
   `master_agent` should be null; `sub_orchestrators` empty.
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state** at `.workflows/documentation/state.json` (schema
   2.0.0) with step_status for all steps, `dispatches_used: 0`,
   `scope: "<arg>"`, `dry_run: <bool>`.
5. **Detect context.** Git log for architecture-relevant commits since last
   doc update; presence of `openapi.yaml`/`openapi.json` signals API lane.
6. Append INIT event.

---

## STEP 2: ADR (skip if scope ∉ {all, adr} OR no architecture decisions detected)

```
Skill("/adr", args="create-from-recent-commits")
```

Scans recent commits for ADR-worthy changes (new dependencies, schema
migrations, API contract changes, architectural patterns). Writes to
`docs/adr/`. Honors `--dry-run`. If no candidates: mark SKIPPED.

Capture paths into `state.artifacts.adrs`.

---

## STEP 3: API_DOCS (skip if scope ∉ {all, api} OR no OpenAPI spec)

```
Skill("/api-docs-generator", args="<project root>")
```

Extracts API annotations, regenerates OpenAPI spec + Redoc/Swagger UI
under `docs/api/`. Validates against API tests.

---

## STEP 4: STRUCTURE (skip if scope ∉ {all, structure})

```
Skill("/doc-structure-enforcer", args="audit")
```

Verifies docs follow Diataxis or project layout (`docs/.structure.yml`).
`audit` reports without moves; `enforce` mode does `git mv`. If
`--dry-run`, always `audit`. Otherwise, prompt user before transitioning
to `enforce`. Never auto-mv without confirmation.

### Optional: docs-manager-agent dispatch (bulk content drafting)

If audit reveals substantial missing content:

```
Agent(subagent_type="docs-manager-agent", prompt="""
## Workflow: documentation
## Run ID: <run_id>
## Audit report: <structure audit path>
## Scope: <list of missing doc targets>
## Dry-run: <bool>

Generate draft content for each missing target following the project's
doc structure. Return a contract listing produced drafts for user review.
""")
```

Increment `dispatches_used` by 1. Drafts go to `docs-drafts/`; nothing
is promoted to `docs/` without user review.

---

## STEP 5: STALENESS (skip if scope ∉ {all, staleness} OR --skip-staleness)

```
Skill("/doc-staleness", args="audit --since-last-sync")
```

Diffs code vs docs, flags references to removed/renamed symbols, broken
links, stale examples. Severity-ranked report to
`test-results/doc-staleness.json`.

Gate: if `critical_stale_count > 0`, transition to `step_status.STALENESS
= warned` (NOT blocked — docs lag is common; surface but don't halt).

---

## STEP 6: REPORT

1. **Finalize state.** Write `test-results/documentation-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "COMPLETED | WARNED",
     "scope": "<...>",
     "steps_executed": [...],
     "steps_skipped": [...],
     "artifacts": { "adrs": [...], "api_docs": [...],
                    "structure_moves": [...], "staleness_report": "<path>" },
     "staleness": { "critical": <n>, "moderate": <n>, "minor": <n> },
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Documentation Workflow: <COMPLETED | WARNED>
     Run ID: <run_id>
     Scope: <scope>
     ADRs created: <N>
     API docs regenerated: <YES | SKIPPED>
     Structure moves: <N>
     Staleness: <critical>/<moderate>/<minor>
   ============================================================
   ```
3. **Handoff:** critical staleness → suggest `/fix-issue` for each;
   structure moves → suggest `/code-review-workflow` to surface the
   rename diff in a PR.

---

## CRITICAL RULES

- MUST run at T0 — dispatching this as a worker strips `Agent` at runtime
  and the optional STEP 4 docs-manager-agent dispatch silently inlines.
- MUST NOT dispatch `documentation-master-agent` (deprecated 2026-04-25,
  2-cycle window).
- MUST NOT auto-execute `doc-structure-enforcer` in enforce mode without
  user confirmation — file moves are disruptive.
- MUST NOT treat staleness as hard block — it's warning-only.
- MUST respect `--dry-run` across all steps — no file writes.
- MUST write `.workflows/documentation/state.json` + `events.jsonl`
  after every step transition.
