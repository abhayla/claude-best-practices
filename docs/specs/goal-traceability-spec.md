# Goal Traceability Spec — every file knows the goal it serves

- **Author:** Claude Code (governance architect)
- **Date:** 2026-06-21
- **Status:** DRAFT (brainstorm output — not yet approved for build)
- **Version:** 0.1
- **Anchors to:** Goal 1 (distribute patterns), Goal 4 (thin layer / governance on deterministic hooks), Goal 5 (autonomy via auditable trust)

---

## 1. Problem statement

The hub has a clear, canonical **vision and goals** (README Goals 1–5 + the Goal 5 charter in
`docs/goals/2026-06-20-autonomous-software-development-machine.md`) and a rule that every
*decision* must name a goal (`core/.claude/rules/goal-anchored-decisions.md`). But there is **no
thread from an individual file back to the goal it serves**, and nothing keeps that thread from
breaking. A new pattern, script, or rule can land with no declared reason-for-existing, and no gate
notices. We want: (a) CLAUDE.md to point at the vision/goals and the file index, and (b) every
contributing file to be traceable to a goal — **enforced, not just documented** — in the hub **and**
in downstream projects provisioned from `core/.claude/`.

This is a **wiring** task, not a greenfield one — the anchor, the registry, and the CI gate already
exist and are extensible.

## 2. Research basis (why this design, not another)

External best-practice sweep (15 sources incl. Anthropic CLAUDE.md guidance, Neal Ford's *Building
Evolutionary Architectures* fitness functions, Backstage `catalog-info.yaml`, llms.txt, RTM
practice) + internal hub-asset map. The convergent findings that drove the design:

1. **Granularity that survives = per-file frontmatter `goals:` + a 5–7-term controlled vocabulary.**
   Per-line/per-function tagging is abandoned within months; README-only is too vague for 273 files.
2. **Enforce binary invariants in CI, never debatable categorization.** Fitness functions that
   hard-gate *opinion* ("does this *really* serve G3?") create friction and get disabled rule-by-rule.
   Gate **presence of a valid goal ID**; keep "is the mapping *right*?" as an advisory report.
3. **Traceability that lives outside the dev flow rots** (~40% stale within a year). The link must be
   visible where engineers/agents already look: in the file, in CI output, in generated docs.
4. **CLAUDE.md stays a pointer, never an inlined map** (Anthropic: "would removing this line cause a
   mistake? if not, cut it"). Vision stays in README; CLAUDE.md references it.

## 3. Chosen approach — B: frontmatter `goals:` + registry mirror + CI presence-gate + advisory report

Rejected alternatives: **A (registry-only map)** — link invisible to the file editor, drifts
silently; **C (full fitness-functions hard-gating goal content + mandatory hook injection)** — the
documented enforcement-fatigue failure mode.

### 3.1 The controlled goal vocabulary (taxonomy)

A new SSOT file `config/goals.yml` (hub) defines the 5-term vocabulary, mirrored from the README so
README stays the human apex and `goals.yml` is the machine-readable taxonomy:

```yaml
# config/goals.yml — SSOT for the goal vocabulary. README is the human-facing source.
version: "1.0.0"
last_reviewed: "2026-06-21"
goals:
  G1: { title: "Distribute reusable patterns",        readme_anchor: "goal-1" }
  G2: { title: "Create & maintain reusable workflows", readme_anchor: "goal-2" }
  G3: { title: "Idea → production-deployed app",       readme_anchor: "goal-3" }
  G4: { title: "Thin layer on the latest platform",    readme_anchor: "goal-4" }
  G5: { title: "Autonomous self-improving machine (north-star, composes G1–G4)", readme_anchor: "goal-5" }
non_goals:
  - "Reimplementing what the Claude Code platform ships natively (G4)."
  - "Speculative generality / patterns with no concrete caller (YAGNI)."
```

> **Drift guard:** a tiny check (added to `workflow_quality_gate_validate_patterns.py`) asserts the
> `Gn` titles in `config/goals.yml` still match the README goal headings, so the two cannot diverge.

### 3.2 Per-file declaration

Every **pattern** (skill / agent / rule / hook with YAML frontmatter) adds a `goals:` list keyed to
the vocabulary. Example (a skill):

```yaml
---
name: vps-deploy
description: ...
goals: [G3]          # this skill exists to take an idea to a production-deployed app
---
```

- `goals:` is a non-empty list of valid IDs from `config/goals.yml`.
- An optional one-line `# why` is allowed beside it but **not** required (research: mandatory prose
  rationale is the first thing to rot — keep it optional).
- **Scripts/`*.py` and other non-frontmatter files** carry the link via the registry (§3.3) plus a
  one-line module docstring; they are **not** force-fit into frontmatter.

### 3.3 Registry mirror (the queryable map)

`registry/patterns.json` gains a `goals` array per entry, mirroring the file's frontmatter (validated
to match). This makes the mapping queryable for dashboards/reports without parsing every file, and is
the home for goal links of scripts that have no frontmatter.

### 3.4 CLAUDE.md pointer (the anchor + index)

Add ONE short section to root `CLAUDE.md` (pointer pattern — no inlined detail):

```markdown
## Vision & Goals (what every file here serves)
This hub's vision and Goals 1–5 are stated in `README.md` (apex) with the Goal 5 charter in
`docs/goals/2026-06-20-autonomous-software-development-machine.md`. The machine-readable goal
vocabulary is `config/goals.yml`. Every pattern declares the goal(s) it serves via a `goals:`
frontmatter list (mirrored in `registry/patterns.json`); `goal-anchored-decisions.md` ties every
non-trivial *decision* to the same vocabulary. To see the file→goal map, run
`python scripts/generate_docs.py` → goal-coverage report.
```

### 3.5 Enforcement (tiered — gate the invariant, report the judgment)

| Layer | Mechanism | Strength | What it checks |
|---|---|---|---|
| **Hard gate** | extend `workflow_quality_gate_validate_patterns.py` (already in `validate-pr.yml`) | **Fails PR** | every registered pattern has a non-empty `goals:` with IDs valid in `config/goals.yml`; frontmatter `goals` == registry `goals`; `goals.yml` titles == README |
| **Advisory report** | new section in `generate_docs.py` output | Non-blocking | goal→pattern distribution, orphan goals (no patterns), coverage gaps, patterns claiming G5 without G1–G4 |
| **Optional telemetry** (deferred, not MVP) | `.claude/.goal-misses.log` via existing Stop-hook pattern | Non-blocking | turns that produced a new pattern without a goal link |

The hard gate is a **binary invariant** (presence of a valid ID) — cheap, non-debatable, survives.
"Is this the *right* goal?" stays advisory, because hard-gating opinion is the failure mode.

### 3.6 Downstream propagation

- Ship the convention downstream: `core/.claude/config/goals.yml` (a **template** — project fills its
  own goals), the `goals:` frontmatter convention, and the validator (already distributed with
  `workflow_quality_gate_validate_patterns.py`).
- At provision time, `recommend.py` / `/synthesize-project` scaffolds a starter `config/goals.yml`
  from the target project's own vision (or a TODO stub) and seeds a CLAUDE.md "Vision & Goals"
  pointer. Each downstream project **owns its own taxonomy**; the validator enforces *presence* the
  same way the hub does. This is classified in `config/dual-home-resources.yml` as a **`shared`**
  resource (skeleton synced; the goal list itself is `DOWNSTREAM-ONLY`).

## 4. Requirement tiers (MoSCoW)

### Must (MVP)
- REQ-M1: `config/goals.yml` SSOT created from README Goals 1–5 + non-goals.
- REQ-M2: `goals:` frontmatter added to all registered patterns; `goals` array added to
  `registry/patterns.json` entries.
- REQ-M3: `workflow_quality_gate_validate_patterns.py` extended to gate presence + valid IDs +
  frontmatter↔registry match + `goals.yml`↔README title match. Failing test written first (TDD).
- REQ-M4: CLAUDE.md "Vision & Goals" pointer section added.
- REQ-M5: `core/.claude/config/goals.yml` template + `config/dual-home-resources.yml` classification
  (`shared`) so the convention is distributable and drift-guarded.

### Should (v1.1)
- REQ-S1: goal-coverage report in `generate_docs.py` (distribution, orphans, gaps).
- REQ-S2: provision-time scaffold in `recommend.py` / `/synthesize-project`.

### Could (future)
- REQ-C1: `.claude/.goal-misses.log` advisory telemetry hook.
- REQ-C2: a `goal_delivery_confidence` signal feeding `config/trust-score.yml` (does the shipped work
  match the goal it claimed?). Genuinely useful for Goal 5 but out of scope for traceability MVP.

### Won't (explicitly out of scope)
- REQ-W1: per-line / per-function goal tags (abandoned-in-months failure mode).
- REQ-W2: hard-gating goal *correctness* / categorization (enforcement-fatigue failure mode).
- REQ-W3: a Backstage-style catalog service (disproportionate for 273 files).

## 5. Risks & mitigations
- **One-time annotation of ~273 patterns** is the bulk of the work → do it as a single mechanical
  pass (a helper that proposes a `goals:` per pattern from its directory/stack + registry tags for a
  human to confirm), not hand-edit-by-hand.
- **Taxonomy debate** ("is this G1 or G2?") → the gate only checks *presence*, so debate never blocks
  a PR; the advisory report is where mappings get refined.
- **README/goals.yml divergence** → the title-match check in REQ-M3 prevents silent drift.
- **Downstream friction** → downstream gate is opt-in via provisioning; presence-only keeps it light.

## 6. Success criteria
- 100% of registered patterns carry a valid `goals:` (CI-enforced; PR fails otherwise).
- `config/goals.yml` titles provably match README (CI-enforced).
- `generate_docs.py` emits a file→goal coverage report with zero orphan goals.
- A downstream project provisioned after this ships gets a `goals.yml` stub + the presence gate.
- CLAUDE.md gains exactly one pointer section (no inlined map; no line-budget regression > ~12 lines).

## 7. Open questions
- (none blocking) — taxonomy is fixed to the existing Goals 1–5; enforcement strength is decided
  (presence-gate). Confirm before build: do you want the MVP to annotate **all 273 patterns now**, or
  gate **new/changed patterns only** first (grandfather existing, backfill incrementally)? Both are
  viable; incremental is lower-risk, full is more complete. Recommended: **incremental gate on
  changed files + a tracked backfill issue**, so the gate lands without a 273-file mega-PR.

---

## Handoff
- **Next:** `/writing-plans` to turn REQ-M1..M5 into bite-sized TDD tasks (failing validator test
  first), or `/adversarial-review` to pressure-test this spec before planning.
- **Build order:** REQ-M1 (goals.yml) → REQ-M3 (validator + failing test) → REQ-M2 (annotate, gated
  incrementally) → REQ-M4 (CLAUDE.md pointer) → REQ-M5 (distributable + dual-home class).
