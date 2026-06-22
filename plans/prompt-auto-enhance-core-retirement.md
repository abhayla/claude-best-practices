# Plan — Retire core/ copy of prompt-auto-enhance in favor of the plugin (Option A)

**Owner-approved 2026-06-22.** Decision: the `prompt-auto-enhance` capability is now distributed
as the installable plugin (`plugins/prompt-auto-enhance/`, marketplace `claude-best-practices`).
The `core/.claude/` distributable copy retires to a **thin pointer** (owner chose option (a) — no
silent capability loss). Backed by official Anthropic guidance: *"After migrating, remove the
original files from `.claude/` to avoid duplicates"* (code.claude.com/docs/en/plugins).

## Scope (this pass)
Retire the **distributable** (`core/.claude/`) copy only. KEEP the hub's own `.claude/` operational
copy working (it carries the governance-tail hook the plugin deliberately omits). Do NOT migrate the
hub to consume its own plugin — separate, riskier decision.

## Three trees after this change
- `.claude/` — hub operational (full skill + rule + governance hook). **Unchanged.**
- `core/.claude/` — **thin pointer skill only**; rule + hook deleted.
- `plugins/prompt-auto-enhance/` — the single distributable source. **Unchanged.**

## Steps
1. **Core skill → pointer.** Rewrite `core/.claude/skills/prompt-auto-enhance/SKILL.md` as a short
   pointer redirecting to `/plugin install prompt-auto-enhance@claude-best-practices`. Delete
   `core/.claude/skills/prompt-auto-enhance/references/` (5 files).
2. **Core rule → retire.** Delete `core/.claude/rules/prompt-auto-enhance-rule.md`; remove the
   `prompt-auto-enhance-rule` registry entry.
3. **Core hook → retire.** Delete `core/.claude/hooks/prompt-enhance-reminder.sh`; remove the
   `prompt-enhance-reminder` registry entry; remove it from `synced.hooks` in dual-home config.
4. **Registry skill entry.** Keep `prompt-auto-enhance`; bump version, rewrite description to the
   pointer purpose, resync `hash` to the new file (`hash_pattern` in dedup_check.py), add changelog.
   Update `_meta` count if present; append to `registry/changelog.md`.
5. **Dual-home config.** Move `prompt-auto-enhance` skill from `synced.skills` → `divergent.skills`
   (core pointer ≠ hub full copy, intentionally). Remove `prompt-enhance-reminder.sh` from `synced.hooks`.
6. **Validator guard.** (Optional) add stems to HUB_ONLY_* only if a gate needs it — prefer not to.
7. **Docs + CLAUDE.md.** Regenerate docs; update the G6 section to note the first capability graduated
   core→plugin, and the dual-home note.
8. **Gates (all must pass):** `dedup_check.py --validate-all`, `--secret-scan`,
   `workflow_quality_gate_validate_patterns.py`, `pytest scripts/tests/` (esp. test_dual_home_sync,
   test_prompt_enhance_plugin, registry tests).

## Rollback
All changes are on-branch and git-tracked; `git checkout` restores the deleted core/ files.
