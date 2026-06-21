# Atlas — G1 Design Mockups (`/atlas explain`)

- **Author:** Claude Code (UI/UX Design)
- **Date:** 2026-06-21
- **Gate:** G1 (human-approval) — present multiple mockups; user picks one before any build.
- **Decisions locked into this design:** #1 both actors (agent + dev), bottom-up `explain` first ·
  #2 Committed Index · #3 Python-first parser.
- **Audit D2 baked in:** every view shows **confidence** and a **confirm/correct** affordance — an
  inferred goal is never rendered as a clean fact.

The primary surface is `/atlas explain <file>` (the bottom-up "what is this file for?" both the agent
and the developer share). Three distinct layout philosophies below; pick one for G1.

---

## Variant A — Compact card (dense, table-aligned)

```
scripts/recommend.py
──────────────────────────────────────────────────
 Purpose   Main provisioning entry point — detects
           stacks, copies matching patterns.
 Goal      G1 · Distribute patterns          ◐ inferred
 Helps by  turns the hub library into a per-project
           .claude/ install
 Calls     bootstrap.py · third_party_skills.py
 Used by   recommend.yml (weekly cron)
──────────────────────────────────────────────────
 ◐ goal inferred ·  [c] confirm   [e] correct   [m] map
```

## Variant B — Sectioned (scannable blocks + confidence bar)

```
▌ scripts/recommend.py

  WHAT     Main provisioning entry point.
           Detects stacks, copies matching patterns.

  GOAL     ● G1  Distribute patterns
           confidence  ◐◐◐○○   inferred · unconfirmed

  HELPS    Turns the hub's pattern library into a
           per-project .claude/ install.

  WIRING   → calls    bootstrap.py, third_party_skills.py
           ← used by  recommend.yml (weekly cron)

  [c]onfirm goal   [e]dit goal   [m]ap the Constellation →
```

## Variant C — Minimal inline (terse, agent-first)

```
scripts/recommend.py — provisioning entry point   [G1 · inferred ⚠]
  helps  : hub pattern library → per-project .claude/ install
  calls  : bootstrap.py, third_party_skills.py
  usedby : recommend.yml
  ⚠ goal inferred — `/atlas confirm scripts/recommend.py` to lock
```
*(Variant C doubles as the structured form injected into the agent at file-open.)*

---

## Top-down companion — `/atlas goal G3` (same for any chosen variant)

```
G3 · Idea → production-deployed app            12 files · ◐ 4 unconfirmed
──────────────────────────────────────────────────
 core/.claude/skills/vps-deploy/SKILL.md        ● confirmed
 scripts/collect_signals.py                     ◐ inferred
 core/.claude/skills/deploy-strategy/SKILL.md   ● confirmed
 …  + 9 more                                    [show all]
──────────────────────────────────────────────────
 ⚠ bus-factor: 1 file carries 60% of G3's edges  ·  [m] Constellation
```

## Confidence legend (shared)
`●` confirmed (human-verified) · `◐` inferred (LLM/heuristic, unconfirmed) · `○` unknown.
Every inferred value is advisory and reversible — confirm locks it; correct re-maps it.

## What G1 approval covers
Layout + information shown for `/atlas explain` (and the goal view). NOT in G1 scope: the dashboard
(A5), adapters (A9/A10), and the embed mode — those are post-G1 surfaces.
