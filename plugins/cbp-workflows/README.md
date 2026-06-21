# cbp-workflows — Goal 6 pilot plugin

**Status: PILOT / proof-of-concept** (Goal 6 — package the hub's capabilities as installable, cross-project plugins). Tracking: [issue #187](https://github.com/abhayla/claude-best-practices/issues/187).

## What this proves
A minimal, structurally-valid Claude Code plugin demonstrating the **verified split-distribution design**: the hub's workflow patterns ship as a **native plugin** (central updates, version-pinnable, no per-repo drift) instead of being copied into each project.

Packaged here (all plugin-native per the #187 spike):
- **`skills/`** — `goal-pulse` (one real skill, proof).
- **`hooks/hooks.json`** — a `SessionStart` hook (proves full hook-event parity).
- **`.claude-plugin/plugin.json`** — the manifest; listed in the marketplace at `plugins/.claude-plugin/marketplace.json`.

## What is deliberately NOT here (the verified constraint)
**Auto-loaded `rules/*.md` with `globs:`** — Claude Code plugins have **no native rules concept** (verified against the plugin docs, #187). So the hub's 52 path-scoped rules stay a `.claude/rules/` **copy-in** step; only the code/workflow parts (skills/agents/hooks/MCP) become plugins. This split is the whole finding of the spike.

## Remaining for full Goal 6 (not done in this pilot)
- Verify install end-to-end (`/plugin marketplace add` + `/plugin install cbp-workflows`) in a real CC session.
- Package the remaining 8 workflows + their agents.
- Repoint `recommend.py` to *recommend which plugins to install* (keep its stack-detection brain) + keep the rules copy-in.
- Owner sign-off before the migration proper (strategic — it reshapes the hub's distribution).
