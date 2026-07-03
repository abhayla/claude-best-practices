# Spike: migrate hub distribution from copy-provision to native plugins (issue #187)

Status: READ-ONLY feasibility spike. No plugin built, no distribution code touched.
Date: 2026-07-03.

## Q1 — Can a plugin ship auto-loaded `rules/*.md` with `globs:` path-scoping?

**Answer: NO — hard blocker.**

Evidence:
- `docs/claude-references/create-plugins.md` (Anthropic's own plugin-structure table, lines
  186–207) lists the ONLY recognized plugin root directories/files: `skills/`, `commands/`,
  `agents/`, `hooks/` (+ `hooks.json`), `.mcp.json`, `.lsp.json`, `monitors/`, `bin/`,
  `settings.json`. There is no `rules/` entry, no auto-load-by-glob mechanism, and no mention of
  path-scoped behavioral injection anywhere in the doc.
- The hub has already hit this wall and documented it verbatim in its own shipped plugins:
  - `plugins/prompt-auto-enhance/.claude-plugin/plugin.json` description: *"Auto-loaded rule is
    delivered via the hooks at runtime + shipped as an optional copy-in (no plugin-native rules
    concept, issue #187)."* — this IS the issue the spike is chartered to investigate.
  - `plugins/auto-google-analytics/README.md` (Components section): *"there is no plugin-native
    rule loading yet (issue #187), so **copy this into your project's `.claude/rules/` if you
    want it auto-loaded** as a salience layer; the skill enforces the same hard rules
    regardless."*
- Scale of the surface this blocks: `core/.claude/rules/*.md` has **27 files with `globs:`
  frontmatter** (path-scoped rules — e.g. `agent-orchestration.md`, `android.md`,
  `android-compose-ui.md`, `android-kotlin.md`, …), confirmed via `grep -l '^globs:'`. Plus the
  global-scope rules (`# Scope: global`) that are simpler but still need SOME auto-load path.
- Current workaround pattern (both existing plugins use it): ship the rule file inside the
  plugin as inert reference content, and rely on (a) the plugin's own skill enforcing the same
  behavior procedurally, and/or (b) a SessionStart hook nudge telling the user to copy the file
  into their project's real `.claude/rules/` if they want ambient auto-load. Neither is
  equivalent to native auto-load — both require either procedural re-enforcement in a skill, or
  a manual copy step that reintroduces the exact copy-drift problem plugins are meant to solve.

## Q2 — Hook wiring parity with the current hub hook model?

**Answer: YES, with parity — this is NOT a blocker.**

Evidence:
- `plugins/prompt-auto-enhance/hooks/hooks.json` wires `UserPromptSubmit` and `Stop` events using
  the exact same schema as a project's `settings.json` `hooks` block (`matcher` + `hooks: [{type:
  "command", command, timeout}]`), with `${CLAUDE_PLUGIN_ROOT}` resolving the plugin's own hook
  script path.
- `plugins/branch-lifecycle/hooks/` ships 8 hook scripts (`auto-git.sh`, `auto-pr.sh`,
  `auto-pr-reconcile.sh`, `branch-choice-gate.sh`, `session-concurrency-guard.sh`,
  `session-git-landing.sh`, `stale-branch-reaper.sh`) proving PreToolUse/SessionStart/SessionEnd
  style coverage already works end-to-end via a plugin.
- `docs/claude-references/create-plugins.md` explicitly documents this migration path (§"Migrate
  hooks", lines 437–458): copy the `hooks` object straight out of `settings.json` into
  `hooks/hooks.json` — "the format is the same."
- One documented gotcha (carried in this repo's own CLAUDE.md and memory
  `reference_cc_plugin_install_cache.md`): **never declare hooks in `plugin.json` itself** — they
  auto-load from `hooks/hooks.json` and double-declaring produces a duplicate-registration error.
  This is a plugin-authoring detail, not a parity gap.

## Q3 — Does the dual-home fenced model become unnecessary?

**Answer: PARTIAL — plugins eliminate drift for what they CAN carry; the dual-home gate still has
work to do for the parts plugins can't carry (chiefly rules, per Q1).**

Evidence:
- `config/dual-home-resources.yml` currently classifies dual-home resources into `synced` /
  `shared` / `divergent`. Under `synced:` today: 5 agents, 15 skills, **4 rules**
  (`claude-behavior.md`, `claude-docs-cache.md`, `context-management.md`, `workflow.md`), and 9
  hooks — all today kept identical by hand/CI (`test_dual_home_sync.py`) between `.claude/` and
  `core/.claude/`.
- For the **agents/skills/hooks** slice: a plugin install replaces "copy `core/.claude/X` into
  the downstream project and keep it in sync" with "install once, `/plugin update` on version
  bump" — this is a strict improvement and would let the dual-home gate DROP those categories
  once a resource is plugin-packaged (no more copy-drift because there's no copy — the plugin
  cache is the single source, per Q4).
- For the **rules** slice: per Q1, a plugin cannot natively auto-load `globs:`-scoped rules, so
  the hub's existing workaround (ship the rule file in the plugin + tell the user to copy it into
  `.claude/rules/` if they want auto-load) reintroduces exactly the "two copies that can drift"
  problem the dual-home gate exists to police. The gate does NOT become unnecessary for rules —
  if anything it would need a THIRD context (plugin-shipped copy vs. hub `core/` copy vs.
  downstream project's copied-in `.claude/rules/` copy).
- Net: the dual-home model shrinks in scope (no longer needed for plugin-packaged
  agents/skills/hooks) but does not disappear, because rules — a first-class distributable
  category today — have no native plugin carrier.

## Q4 — Upgrade/version-pinning ergonomics vs. copy-provision / `update-practices`

**Answer: YES — meaningfully better mechanics, with one operational catch already documented by
the hub itself.**

Evidence, from `docs/installing-plugins-in-downstream-projects.md` ("Updating a plugin — why a
source edit may not take effect" section) and memory `reference_cc_plugin_install_cache.md`:
- Installed plugins are copied into a **version-keyed cache**:
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Claude Code parses the CACHED
  `plugin.json`, never the live source under `plugins/…`, even for a local `directory`-source
  marketplace pointing at the hub working tree.
- Upgrade is a single command per project: `/plugin update <name>` — but it **only fires on a
  version bump** (or, absent an explicit `version`, a new git commit SHA). A same-version source
  edit is silently ignored by every already-installed copy — this is the load-bearing gotcha the
  hub's own `/plugin-lifecycle` skill was built to enforce (test-local → **version-bump** → land
  → installed-test sequence).
- Compared to today's `recommend.py --provision` / `sync_to_projects.py` copy-provision model:
  copy-provision has NO version concept at all — a downstream project's copied file just silently
  diverges from the hub source until someone reruns provisioning and manually resolves
  conflicts/overwrites. The plugin model's version-gate is objectively more disciplined (explicit,
  atomic, auditable via `plugin.json` `version` diffs) even though it adds one required step
  (remembering to bump) that copy-provision doesn't have.
- Rollback/pinning: a plugin install pins to a specific version per project (visible in the cache
  path itself); copy-provision has no equivalent pin — a project's copied file is whatever was
  last synced, with no record of which upstream version it came from.

## Hard blockers (summary)

1. **No native `rules/*.md` + `globs:` auto-load in the plugin model.** This blocks a 1:1
   migration of anything in `core/.claude/rules/` (27 path-scoped + several global-scope files)
   to plugin-native delivery. Workaround exists (ship as reference + procedural skill enforcement
   + optional manual copy) but is not equivalent and reintroduces copy-drift for the copied-in
   case.

No other hard blockers found — hooks (Q2) and versioning (Q4) are proven to parity or better by
the hub's own three already-shipped plugins.

## Migration-candidate triage

**Good candidates (identical-across-adopters, no rules dependency, or rules-light):**
- The 9 orchestrated workflows (`core/.claude/skills/<workflow>/SKILL.md` set) — these are
  skills, the plugin model's best-supported component. `loop-engineering` already proves this at
  scale (13-skill/2-agent dependency closure, second-project install-validated 2026-07-03 per
  memory `project_loop_engineering_plugin.md`).
- Universal (non-`globs`) rules that don't need path-scoping could ship as reference docs a
  skill reads, but genuinely ambient/global rules (`# Scope: global`, no `globs:`) are the
  *closest* rules candidate — still blocked by Q1, but the workaround (skill-enforced procedural
  equivalent) is least lossy for these since they apply everywhere anyway, unlike a `globs:`
  rule that must NOT fire outside its scope.
- Core agents (`core/.claude/agents/*.md`) — straightforward `agents/` directory, no blocker.

**Must stay copy-provisioned (project-owned, editable, or inherently non-shippable):**
- `goals.yml`, project-specific `CLAUDE.md` content, and any project rule meant to be *edited*
  by the downstream team after provisioning — a plugin is a versioned, centrally-updated
  artifact; a project needs to fork-and-own these, which the copy-provision model supports and
  a plugin install actively fights (an installed plugin's cache is not meant to be hand-edited).
- The 27 `globs:`-scoped path rules — blocked outright per Q1 until Anthropic ships a
  plugin-native rules mechanism.

## Recommendation: **GO-WITH-CAVEATS** — pilot ONE plugin (`cbp-workflows`, the 9 workflows)

Rationale: the hooks and versioning mechanics are already proven at hub scale by 3 shipped
plugins (including a 13-skill dependency closure, `loop-engineering`, already second-project
validated). The workflows are pure skills with no `globs:`-rule dependency, making them the
lowest-risk, highest-value migration target — and doing this pilot answers the outstanding
open question (does `synthesize-project`/`recommend.py` need to special-case "already
plugin-installed" so it doesn't double-provision a copy on top of an installed plugin — noted in
memory `project_loop_engineering_plugin.md`: "provisioned copies shadow installed plugins").
Do NOT attempt to migrate `core/.claude/rules/` in this pass — that requires either an upstream
Anthropic plugin-rules feature or accepting the lossy skill-enforced/manual-copy workaround, and
should be tracked as a separate, explicitly-scoped follow-up once Q1's blocker status changes.

### If GO: next 3 steps for the pilot

1. **Scaffold `plugins/cbp-workflows/`** via `/plugin-lifecycle` (create mode): register in
   `plugins/.claude-plugin/marketplace.json`, move/copy the 9 workflow skill directories
   (`test-pipeline`, `development-loop`, `debugging-loop`, `code-review-workflow`,
   `documentation-workflow`, `session-continuity` equivalent, `learning-self-improvement`,
   `skill-authoring-workflow`, `loop-engineering` — confirm whether `loop-engineering` stays a
   separate plugin per its existing G6 status or gets folded in; likely stays separate since it's
   already independently shipped and validated).
2. **Resolve the shadow-copy conflict**: decide + implement how `recommend.py --provision` /
   `bootstrap.py` detect an already-plugin-installed workflow and skip re-copying it into the
   target project's `core/.claude/skills/`, per the open note in
   `project_loop_engineering_plugin.md`. Without this, a project that both provisions AND installs
   the plugin gets duplicate/shadowed skill definitions.
3. **Second-project install validation** (the bar `loop-engineering` already cleared): install
   `cbp-workflows@claude-best-practices` into a clean-room project with no local `.claude/` copy,
   run one full workflow end-to-end (e.g. `/test-pipeline` or `/development-loop`), and confirm a
   full maker≠checker cycle completes to a verified commit — mirroring the loop-engineering
   validation methodology (2026-07-03, per memory) before declaring the pilot itself validated.
