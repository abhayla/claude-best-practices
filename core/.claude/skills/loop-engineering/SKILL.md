---
name: loop-engineering
description: >
  POINTER to the installable loop-engineering plugin — this capability graduated from a
  copied core/ template to plugin-as-SSOT (#346 stage 2, plugins-first-only). Use
  this pointer when provisioning: install the plugin instead of copying. Original
  purpose: Run a repeatable, autonomous feedback loop — DISCOVER → PLAN → EXECUTE → VERIFY → (SHIP | FEEDBACK) — as a skill-at-T0 orchestrator. The skill body IS the orchestrator: it runs in the user's T0 sessio
type: reference
allowed-tools: "Read"
argument-hint: "(no arguments — informational pointer)"
version: "2.0.0"
---

# loop-engineering — now ships as a plugin

This capability is **no longer distributed as a copied template**. It ships in the
loop-engineering plugin (G6-validated 2026-07-12) so there is **one source of truth** instead
of a template copy that drifts. This file is a pointer left in `core/` so provisioning
surfaces the redirect rather than silently dropping the capability (#346 stage 2,
plugins-first-only — owner decision 2026-07-14; recipe:
`plans/core-skills-thin-pointer-retirement.md`).

## How to get it

```
/plugin marketplace add abhayla/claude-best-practices
/plugin install loop-engineering@claude-best-practices
/reload-plugins
```

## What it does (so provisioning can decide without installing)

Run a repeatable, autonomous feedback loop — DISCOVER → PLAN → EXECUTE → VERIFY → (SHIP | FEEDBACK) — as a skill-at-T0 orchestrator. The skill body IS the orchestrator: it runs in the user's T0 session, dispatches a MAKER worker (default plan-executor-agent) and a SEPARATE CHECKER (default code-reviewer-agent) via Agent() so the author never grades its own work, and self-heals on failure by looping through /fix-loop or /debugging-loop under hard budgets. Self-verifying (maker≠checker), self-healing (feedback arm), self-learning (/learn-n-improve each cycle), self-feedback (/escalation-report on budget exhaustion).

After install the skill resolves as `loop-engineering:loop-engineering` (invokable as `/loop-engineering` when no
shadowing copy exists). Historical `references/` and `evals/` directories are retained
here for evidence; the LIVE copies ship inside the plugin.

## Structure of the plugin copy (from the retired template, for orientation)

- INIT
- 5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)
- DISCOVER (the automation heartbeat)
- PLAN
- EXECUTE — the MAKER (isolated)
- Workflow: loop-engineering
- Run ID: <run_id>   Cycle: <n>
- Plan file: <latest entry of state.artifacts.plans>
- DoD: <one-sentence DoD>
- Upstream decisions: <key decisions so far>
- Original request: <input>
- VERIFY — the CHECKER (independent; maker ≠ checker)

Original invocation shape: `<goal / Definition of Done, issue URL, or triage source> [--max-cycles N] [--no-ship]`.
The plugin copy is the LIVE version — its steps, gates, and worker dispatches may
have evolved past this snapshot; always trust the installed skill over this list.

## Why it moved

- **Single source of truth** — plugin updates reach every project via
  `/plugin update loop-engineering`; copied templates drift silently.
- **Closure completeness** — the plugin bundles its full sub-skill + agent closure, so
  an install never hits a missing-worker preflight block.
- **Shadowing trap** — a provisioned copy of a same-named skill SHADOWS the installed
  plugin's version, so plugin-covered skills are excluded from copy-provision
  (`config/plugin-recommendations.yml` is the SSOT `recommend.py` consults).
