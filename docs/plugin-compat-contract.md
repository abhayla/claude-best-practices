# Plugin Compatibility Contract (v1)

**What this is.** The promise every plugin in this hub's marketplace
(`plugins/.claude-plugin/marketplace.json`) makes to the projects that install it: which surfaces
are stable, what each version-number change is allowed to mean, and how renames/removals must be
staged. It exists because downstream projects now consume capabilities by `/plugin install`
(the #187 end-state) — an update that silently breaks a downstream workflow is a distribution
regression, not a local edit.

**Who it binds.** The hub (producer obligations) and downstream projects (consumer expectations).
All plugin work already routes through `/plugin-lifecycle`; this contract is the compatibility
rulebook that skill enforces by convention.

---

## 1. The stable surfaces (what downstream may rely on)

| Surface | Stable means |
|---|---|
| **Skill / slash-command names** | `/name` keeps resolving; its argument contract (documented `argument-hint` forms) keeps working |
| **Skill behavior contract** | The documented modes/outputs of a SKILL.md (its "Mode router" rows, MUST/MUST-NOT lists) |
| **Hook effects** | The event a hook fires on and the effect it delivers (e.g. "SessionStart + SubagentStart inject the operating core") — not the script's internals |
| **Settings files** | Keys and defaults of a shipped `*.default.json`; a project's local overrides keep meaning what they meant |
| **Agent names** | Agents shipped by the plugin remain dispatchable by name |
| **Marketplace identity** | `name` and `source` in marketplace.json never change for a living plugin |

Internals are NOT surface: file layout inside the plugin, helper scripts, prose in manuals/docs,
eval batteries. These may change in any release (a manual's *content* may change in MINOR;
see §2 — its *path* is surface only if a hook or skill references it).

## 2. What each version bump may mean (SemVer per surface)

| Bump | Allowed changes | Examples (real precedents) |
|---|---|---|
| **PATCH** (0.0.x) | Bug fixes; internal refactors; doc/prose edits; no surface added or changed | `fable-operating-manual` 0.1.0→0.1.1 (hookEventName fix) |
| **MINOR** (0.x.0) | Additive surface: new skill/hook/agent/setting **with a safe default**; expanded content behind the same surfaces; new optional arguments | `fable-operating-manual` 0.1.1→0.2.0 (manual v2, new traps — same skills/hooks) |
| **MAJOR** (x.0.0) | Anything in §3 (breaking). Requires the deprecation staging in §4 to have run first where a rename/removal is involved | none yet — first one must cite this contract in its PR |

Pre-1.0 note: the ecosystem is pre-1.0, so MINOR carries the "could break in theory" SemVer
caveat — this contract removes that ambiguity: **even pre-1.0, breaking changes require the §4
staging and a MAJOR-style callout in the changelog + PR body.** Version numbers are cheap;
broken downstream workflows are not.

## 3. Breaking changes (never silent, never in PATCH/MINOR)

- Removing or renaming a skill, slash command, or agent.
- Changing a skill's argument contract incompatibly (an argument that used to work stops working).
- Removing a hook, changing its event/matcher, or removing the effect downstream relies on.
- Changing a settings key's name, type, or the *meaning* of an existing value; changing a default
  in a way that flips behavior for existing installs.
- Changing marketplace `name`/`source` (this orphans every install).
- Declaring hooks in `plugin.json` (auto-load + declaration = duplicate-load error — always a bug,
  contract-level because it breaks *every* install on update; hub lesson PR #244).

## 4. Deprecation staging (the rename/removal path)

Precedents: `/save-session` → `/end-session`, `/cc-adoption-scout` → `/review-new-claude-features`.

1. **Release N (MINOR):** the new name ships; the old name remains as a thin alias stub whose
   description says DEPRECATED and routes to the new name.
2. **Grace window:** the alias lives **≥2 version cycles** (or ≥60 days, whichever is longer).
3. **Release N+k (MAJOR):** the alias may be removed; changelog + PR body name the removal
   explicitly.

Settings keys follow the same pattern: new key ships reading the old key as fallback for the
grace window; removal of the fallback is MAJOR.

## 5. Propagation mechanics (why the bump is load-bearing)

- Installed plugins are served from a **version-pinned cache**
  (`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`). An unbumped source edit reaches
  **no one** — this is enforced by the CI version-bump gate (PR #349): plugin source changes
  without a `plugin.json` version bump fail `validate`.
- Downstream applies updates explicitly:
  `claude plugin update "<plugin>@claude-best-practices" --scope project`
  (the qualified name AND scope are required — bare names fail "not found"). Restart applies.
- Hub-side release checklist = `/plugin-lifecycle` STEPS 5–8 (test-local → bump → land → verify
  the installed copy serves the new version).

## 6. Coexistence rule (plugin vs project-local copies)

When a project ships its own copy of a guard/hook that a plugin also ships, **the project copy
wins and the plugin copy stands down** (precedent: enhance-guard coexistence stand-down,
prompt-auto-enhance v0.3.1/PR #348, branch-lifecycle 0.1.2). Plugins that ship potentially
duplicated governance MUST carry a stand-down check rather than double-firing. Conversely,
`config/dual-home-resources.yml` governs hub-internal duplication — a capability graduating to
plugin-as-SSOT thins its `core/` copy to a pointer (precedent: prompt-auto-enhance).

## 7. Producer obligations per release (checklist)

- [ ] Version bumped per §2; changelog entry states the surface delta.
- [ ] No §3 item present unless this is a staged MAJOR with §4 satisfied.
- [ ] `claude plugin validate` + clean-room serve probe pass (`validate_plugin_cleanroom.py`).
- [ ] If a hook's *effect* changed: an installed-context probe verifies the effect at the
      consumer (manual §13 — the artifact is not the effect).
- [ ] PR body names any deprecations started or completed.

## 8. Consumer expectations (downstream projects)

- Pin nothing: take PATCH/MINOR updates freely; read the changelog before a MAJOR.
- Treat alias-stub warnings as migration deadlines (≥2 cycles, not forever).
- Report a broken-by-update surface as a hub bug citing this contract — silent breakage is a
  contract violation regardless of version arithmetic.

## 9. Enforcement today vs later

Today (mechanical): the version-bump CI gate (#349) + `claude plugin validate` + clean-room
structural checks. The §3 breaking-change classification is convention enforced by
`/plugin-lifecycle` + PR review.

Deferred (YAGNI until a real violation or a second marketplace consumer appears): a contract-lint
that diffs a plugin's surface manifest (skills/hooks/settings/agents) between versions and blocks
a breaking diff without a MAJOR bump. If/when built, it slots into `validate-pr.yml` beside the
version-bump gate. Do not build it speculatively — record the need here and revisit on first
violation.
