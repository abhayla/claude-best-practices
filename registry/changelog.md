# Changelog

All notable pattern additions, updates, and removals.

## [Unreleased]

### 2026-06-10 — Tier 4: `autonomous-contract` skill from firekaro-planner goal-creator

Tier 4 (final) of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). Source: `project:firekaro-planner`. Brainstorm spec: `docs/specs/autonomous-contract-skill-spec.md`.

- **added** skill `autonomous-contract` (workflow, category: core, tier: nice-to-have) — authors a dense, zero-open-questions contract to hand to an autonomous executor (Claude Code's built-in `/goal`, or `/loop` / routines / headless) that runs unattended until a Definition of Done. Generalized + executor-anchored-on-`/goal` from firekaro's `goal-creator`. Full apparatus: interview-first Clarification Gate (scoped by `decision-authority`), idempotency preflight, worktree+lock+commit-gate isolation (points to `git-worktrees`), cross-session progress log, DONE/PENDING/BLOCKED/NEXT summary, DoD-verb precision (`dod-verbs`), and blast-radius verification gates that **point to** the Tier 1–3 hub rules (`supervisor-verification`, `independent-test-verification`, `output-plausibility-verification`, `e2e-persistence-verification`, `bug-triage-discipline`) rather than inlining them (`configuration-ssot`). References: `contract-template.md`, `baked-in-rules.md`, `example-contract.md`. Authors and stops — never runs the executor, never commits; Mode B folds run learnings back (PROPOSE-only, per `learnings-routing`).

### 2026-05-28 — Port 4 skills from mattpocock/skills (category: core, tier: must-have)

- **added** skill `improve-codebase-architecture` — Ousterhout deep-modules lens: surface architectural friction, propose deepening opportunities, produce an HTML report with before/after Mermaid diagrams, then drop into a grilling loop. References: `LANGUAGE.md`, `HTML-REPORT.md`, `DEEPENING.md`, `INTERFACE-DESIGN.md`. Adapted from upstream (no auto-open, Agent-tool dispatch at T0, references/ layout).
- **added** skill `grill-with-docs` — docs-aware grilling session: one question at a time, challenges plan against `CONTEXT.md` glossary + `docs/adr/`, updates docs inline. Required companion to `improve-codebase-architecture`. References: `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`.
- **added** skill `zoom-out` — 3-step "go up a layer, name the surrounding modules in domain vocabulary" map. Tiny, high-value habit nudge.
- **added** skill `to-prd` — synthesize a PRD from current conversation + codebase understanding (no interview). Inverse direction of existing `/prd-parser`. Looks for deep-module opportunities during module sketching.

Source: <https://github.com/mattpocock/skills/tree/main/skills/engineering>.
