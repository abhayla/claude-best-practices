# Scope: global

# Product Incubation & Graduation (hub-as-factory operating model)

version: "1.0.0"

When this hub is used to BUILD A PRODUCT (not to develop the hub's own
patterns/machine), the product code MUST NOT live inside the hub's git tree.
Incubate it in an ISOLATED SIBLING folder operated from the hub session, then
GRADUATE it to its own repo as soon as it outgrows incubation.

A **sibling folder** is a directory at the same parent level as the hub — e.g.
the hub is `…/VibeCoding/claude-best-practices/`, so a product goes in
`…/VibeCoding/<product>/` with its OWN `.git`, OUTSIDE the hub's folder and git
tree (the hub's `git status`, CI, and secret-scan never see it).

## First: is this even a product, or factory R&D?

- **Factory R&D** — a new pattern, skill, agent, rule, workflow, or the
  autonomous-machine infra itself → this is hub work; it belongs IN the hub.
- **A product** — an app/tool the machine builds → it belongs in a sibling,
  per this rule. When unsure, ask: "does this ship as a hub pattern, or as its
  own deployable artifact?"

## Why never inside the hub tree

- **Two-`.claude/` boundary** collision — a product's `.claude/` breaks the
  hub-only vs distributable invariant (CLAUDE.md "Two `.claude/` Directories").
- **Hub CI scans the WHOLE tree** (`validate-pr`, `dedup_check --validate-all`,
  `--secret-scan`) — product code trips the gates, or forces exclusions that
  weaken them.
- **Flywheel/telemetry assume hub ≠ product** — in-tree product work pollutes
  the adoption + trust-score calibration signals the north-star depends on.
- **Graduation from in-tree is a painful git-history extraction** that gets
  perpetually deferred → the hub silently rots into a monorepo of unrelated apps.

## The model

1. **INCUBATE** — create the product as a sibling dir OUTSIDE the hub
   (`../<product>/`), provision patterns with
   `PYTHONPATH=. python scripts/recommend.py --local ../<product> --provision`.
   Operate it from the hub session while small. Nothing product-related touches
   the hub git tree.
2. **GRADUATE** — when ANY trigger below fires, RECOMMEND moving it to its own
   repo: `git init` + add remote, then `/bootstrap-dogfood-project ../<product>`
   to wire the project→hub feedback loop. Cheap, because it was never entangled.

## Graduation triggers (ANY one fires → recommend graduating)

- \> ~15 source files OR > ~500 LOC of product code, OR
- needs its own CI or a deploy target, OR
- needs secrets / deploy credentials, OR
- gains a second contributor, OR
- gets its first real user, OR
- has survived > 7 days of active work (no longer a throwaway).

The recommendation to graduate is not optional housekeeping — surface it the
moment a trigger trips, so the move happens while it is still cheap.

## Anchor

Serves Goals 1 & 4 (clean distributable + thin layer) and the
autonomous-software-development-machine north-star — graduated downstream
projects are what generate the clean dogfood + trust-score calibration data that
autonomy depends on (`docs/goals/2026-06-20-autonomous-software-development-machine.md`).
Composes with `goal-anchored-decisions.md` (anchor the build/defer call to the
goal + user) and `rule-curation.md`. Building a product inside the hub is the
anti-pattern this rule kills.
