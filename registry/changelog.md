# Changelog

All notable pattern additions, updates, and removals.

## [Unreleased]

### 2026-06-10 — Tier 2: merge firekaro-planner quick-wins into existing patterns + 2 new meta-rules

Tier 2 of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). Generalized merges into existing hub patterns + 2 new global rules. Source: `project:firekaro-planner`.

- **updated** rule `error-handling` (v1.1.0) — added "Numeric & Derived-Value Safety" (NaN/Infinity/division-by-zero guards on derived values) and "Fire-and-Forget Side Effects" (logged `.catch()` mandate, no bare-`void` discard). Fixed the firekaro `console.error`-in-catch inconsistency: routes logging through the project logger per `security-baseline`.
- **updated** rule `security-baseline` (v1.1.0) — added "Structured Logging as a Redaction Choke Point" (single logger, field-level redaction, never interpolate secrets into the message string — redaction covers fields, not the formatted message).
- **updated** skill `writing-plans` (v1.3.0) — added a mechanical zero-open-questions grep gate (STEP 4.1) + a DoD-verbs checklist item. (Also corrected a pre-existing registry/frontmatter version drift.)
- **updated** skill `e2e-best-practices` (v1.1.0) — added "Production: What NEVER Runs There, and What MUST Run After Every Deploy" + "Calculation Verification — use the API as the oracle" (tolerance compare, validate empty states, never `test.skip()`).
- **updated** skill `git-worktrees` (v1.1.0) — added "Background Autonomous-Run Isolation" (dedicated worktree + lock file + pre-commit run-token gate + cross-session progress log).
- **added** rule `dod-verbs` (global) — definition-of-done verbs are load-bearing: every acceptance criterion states an ACTION + COMPLETENESS BAR; elastic verbs get satisfied at the weakest reading.
- **added** rule `learnings-routing` (global) — type each learning GENERIC vs PRODUCT-SPECIFIC, route to one canonical home, prefer a deterministic gate over prose, dedup, rule-changes are PROPOSE-only.

### 2026-05-28 — Port 4 skills from mattpocock/skills (category: core, tier: must-have)

- **added** skill `improve-codebase-architecture` — Ousterhout deep-modules lens: surface architectural friction, propose deepening opportunities, produce an HTML report with before/after Mermaid diagrams, then drop into a grilling loop. References: `LANGUAGE.md`, `HTML-REPORT.md`, `DEEPENING.md`, `INTERFACE-DESIGN.md`. Adapted from upstream (no auto-open, Agent-tool dispatch at T0, references/ layout).
- **added** skill `grill-with-docs` — docs-aware grilling session: one question at a time, challenges plan against `CONTEXT.md` glossary + `docs/adr/`, updates docs inline. Required companion to `improve-codebase-architecture`. References: `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`.
- **added** skill `zoom-out` — 3-step "go up a layer, name the surrounding modules in domain vocabulary" map. Tiny, high-value habit nudge.
- **added** skill `to-prd` — synthesize a PRD from current conversation + codebase understanding (no interview). Inverse direction of existing `/prd-parser`. Looks for deep-module opportunities during module sketching.

Source: <https://github.com/mattpocock/skills/tree/main/skills/engineering>.
