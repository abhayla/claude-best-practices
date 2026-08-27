# cbp-workflows pilot validation — 2026-07-12

Evidence record for the **#187 distribution pilot** (owner-approved 2026-07-12, PR #334):
`cbp-workflows` v0.1.0, the hub's 6th marketplace plugin, packaging the quality-trio
workflows (`code-review-workflow`, `documentation-workflow`, `skill-authoring-workflow`)
plus their level-1 dispatch closure (13 sub-skills, 4 worker agents) — *installed* into
downstream projects instead of *copied*.

## Scope decisions (load-bearing, made during the pilot)

- **Level-1 dispatch closure is the packaging cut.** The full transitive closure of just
  these 3 workflows measures **93 skills** — effectively the whole hub graph — so chasing
  transitive references is not a viable packaging rule. Level-1 (what a workflow directly
  dispatches) matches the loop-engineering precedent; deeper references degrade to
  see-also pointers.
- **No duplicate SSOT across plugins.** `session-continuity` was swapped out of the
  cluster because its dispatch deps (`start-session`, `end-session`, `continue`) already
  ship in the `branch-lifecycle` plugin. `fix-loop` IS duplicated (both here and in
  `loop-engineering`) because each plugin must be self-contained for its direct dispatch
  targets — plugin skills are namespaced, so the copies cannot collide at invocation time.
- **Stack-specific helpers stay provisioned** (pytest-dev, jest-dev, fastapi-*, android-*):
  the Tier-2 stack-pack boundary from #187's tier design, confirmed workable.

## Spike answers to #187's four open questions

1. **Rules-in-plugins: NO.** Plugin components are skills/commands/agents/hooks/MCP/LSP/
   monitors/bin/settings (cached doc `docs/claude-references/create-plugins.md`).
   Auto-loaded `rules/*.md` with `paths:` are not a plugin component — rules stay
   copy-provisioned, or hook-injected (the fable-operating-manual pattern).
2. **Dual-home fencing:** unaffected by this pilot (no rules shipped). The long-term
   answer is plugin-as-SSOT graduation (the prompt-auto-enhance precedent), which removes
   the dual-home copy entirely.
3. **Hook wiring parity:** already proven by `branch-lifecycle` (9 hooks auto-load from
   `hooks/hooks.json`); this pilot ships no hooks.
4. **Upgrade ergonomics:** version-pinned cache + `/plugin update` beats `update-practices`
   copy-sync; proven across the 5 pre-existing plugins.

## Validation evidence (all gates green, 2026-07-12)

| Gate | Result |
|---|---|
| `claude plugin validate ./plugins/cbp-workflows` | PASS |
| `validate_plugin_cleanroom.py cbp-workflows` (structural + CLI + headless serve probe) | **PASS** — all 16 skills + slash commands visible from the plugin alone (`cbp-workflows@inline`) |
| Full hub gate (dedup validate, secret scan, quality gate, pytest) | PASS — 1787 passed / 0 failed |
| **Real second-project install** | PASS — see method below |

### Second-project method (the heavier G6-bar shape)

A throwaway downstream project (`D:/Abhay/VibeCoding/cbp-plugin-test`, own `git init`,
a small `calc.py` + README, **no `.claude/` of its own**) was created outside the hub tree.
Using a fully **isolated `CLAUDE_CONFIG_DIR`** (fresh temp config — no pre-existing
marketplaces, plugins, or project state): `claude plugin marketplace add <hub>/plugins` →
`claude plugin install cbp-workflows@claude-best-practices` → `claude plugin list` showed
**v0.1.0, enabled**. A headless session in the test project then ran
`cbp-workflows:code-review-workflow` against a real uncommitted diff containing a planted
defect. The installed workflow followed its steps (quality gates, risk scoring, verdict
artifact `test-results/code-review-verdict.json`), **executed the code and caught the
planted bug** (`average([])` → `ZeroDivisionError`), and returned a structured
`APPROVED_WITH_CAVEATS` verdict with risk score 20/100 and the correct suggested guard.

Status vocabulary: this makes `cbp-workflows` **serve-validated AND
second-project-install-exercised on day one**. The formal G6-graduation sweep entry
(context-isolated skeptic refutation pass, per `docs/g6-graduation-2026-07-10.md`) can be
added at the next sweep.

## Expansion path (future improvement-loop cycles)

1. `test-pipeline` + `development-loop` cluster — requires designing the stack-pack
   boundary (their closures include per-stack helpers).
2. Learning + session clusters (respecting the branch-lifecycle overlap rule).
3. Repurpose `recommend.py` from copy-provisioner to plugin recommender (#187 end-state).
