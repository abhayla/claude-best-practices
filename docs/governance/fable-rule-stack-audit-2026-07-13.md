# Fable rule-stack audit — contradictions, weak-model rules, and injected-prompt volume (2026-07-13)

Session A of the owner-approved Fable-harvest plan (`plans/fable-harvest-window.md`).
Auditor: Claude Fable 5, reading the full governance surface end-to-end (both CLAUDE.md files,
all 5 hub rules, the core SSOT rules, the distilled core, and the live per-prompt hook payloads).
**Nothing here is applied.** Every proposed change is owner-gated (claude-behavior rule 5).
Composes with the telemetry-based `lint_rule_compliance.py` DEMOTE work (Group A landed PR #347);
this pass adds the SEMANTIC layer telemetry cannot see.

External grounding: Anthropic cut Claude Code's own system prompt ~80% because "Fable 5 models
want a smaller system prompt" — over-specification and examples now DEGRADE frontier output
(the-decoder + MindStudio, corroborated; captured in the 2026-07-13 external scan report).

## 1. Volume measurement (the #6 audit)

Measured with `wc -w` unless marked (est.).

| Injected surface | When | Words |
|---|---|---|
| Project `CLAUDE.md` | every session | 5,308 |
| Hub `.claude/rules/` (5 global rules) | every session | 3,590 |
| `fable-operating-manual` distilled core | every session (hook) | 949 |
| Global `~/.claude/CLAUDE.md` | every session | ~1,000 (est.) |
| superpowers `using-superpowers` injection | every session | ~700 (est.) |
| Session banners (governance, goal pulse, reaper, handoff) | every session | ~600 (est.) |
| **Session-start baseline** | | **~12,100 (~16k tokens, est.)** |
| `prompt-enhance-reminder.sh` payload | EVERY substantive prompt | ~1,392 (from hook source) |
| `ba-usecase-discovery-reminder.sh` payload | when its detector fires | ~250 |
| Core SSOT rules the pipeline cites (decision-authority, engineering-roles, supervisor-verification, plan-before-coding, independent-test-verification, git-collaboration, configuration-ssot) | on demand | 7,294 |

Two hard observations from this very session:

- **A 20-prompt session re-injects ~28k words of the same reminder text** (~1,400 × 20) — none of
  it new information after prompt 1.
- **Reading 2 core rule files auto-injected ~30 additional full core rule files** (~25k words,
  est.) into context in one shot — the path-scoped loading is far coarser than its design intent.
- The hub's own `rule-writing-meta.md` budgets project CLAUDE.md at **≤80 lines** and global at
  **≤30 lines**. The project file is ~5,300 words — several multiples over the budget the hub
  ships to downstream projects. The hub does not pass its own lint.

**Proposed experiment (#6, owner-gated):** A/B one week of normal hub work with (a) the enhance
reminder collapsed to 2 lines after the session's first prompt, and (b) the distilled core as the
only per-session injection for Fable/Opus-driven sessions. Measure enhance-miss rate + subjective
correction rate. Evidence bar: Anthropic's 80% cut + this file's volume table.

## 2. Contradictions found (rule vs rule, rule vs enforcement, rule vs platform)

| # | Finding | Evidence | Class |
|---|---|---|---|
| C1 | `claude-behavior.md` rule 14(2) "**Check in with user before starting implementation**" directly contradicts `decision-authority.md` ("MUST NOT ask permission-to-start when intent is clear") and the DECIDE-DON'T-ASK hook injected every prompt | Both texts in force simultaneously, every session | **REWRITE** — delete the check-in clause, defer to decision-authority |
| C2 | `claude-behavior.md` rule 6 "uncommitted changes → **ask the user to commit or stash first**" contradicts the autonomous branch lifecycle (auto-git commits per turn; branch-choice gate owns the decision; owner feedback: routine git is autonomous) | Rule text vs CLAUDE.md "Autonomous Branch Lifecycle" + owner memory | **REWRITE** — replace with a pointer to the branch lifecycle |
| C3 | `claude-behavior.md` rule 1 (plan mode for any non-trivial task) is a **shadow copy** of `plan-before-coding.md`, and is stricter (plan MODE) than the SSOT (plan mode OR contract OR inline block) — violating `configuration-ssot.md`'s own no-shadow-copies rule | Both files in force; SSOT explicitly says "cross-reference, never copy" | **REWRITE** — rule 1 becomes a one-line pointer |
| C4 | `model-routing.md` "set `model` explicitly on EVERY dispatch — inheriting is never a default" contradicts the platform Workflow-tool guidance "**Default to omitting model** — the agent inherits the main-loop model, which is almost always correct" | Hub rule vs platform tool description, both loaded | **REWRITE** — scope the hub rule: explicit model on `Agent()` dispatch; Workflow `agent()` calls omit unless routing down |
| C5 | The **machine-origin exemption is not honored by enforcement**: `prompt-auto-enhance.md` says a task-notification turn "gets at most a one-line banner", but `no-overask-guard.sh` BLOCKED a machine-origin task-notification turn this session demanding the full reviewer card | Live Stop-hook block observed 2026-07-13 (~17:50 IST) on a task-notification turn | **BUG** (per Manual §9.1: symptom contradicts documented default = drift, not design) — fix `turn-origin.sh` classification or the guard's use of it |
| C6 | The **BA-gate detector misfires**: fired this session on "compare these two manuals" (analysis), on "web-search what others do" (research), and on machine-origin task notifications — the rule text itself says pure-technical/research turns need no offer | 3 live misfires observed 2026-07-13 | **BUG/REWRITE** — tighten `ba-usecase-discovery-reminder.sh` trigger; each misfire costs ~250 words and trains ignoring |
| C7 | "**Codex will review your output**" (claude-behavior.md, bold callout) is a false premise — no Codex review runs on this repo's output. A rule that motivates via a fictional auditor is the Manual's "teach by bad example" class and contradicts its never-attest/no-fiction discipline | No Codex integration exists in repo config/CI (checked: no codex workflow, no hook) | **DELETE** |
| C8 | The **enhance ceremony mandate** (visible transcript + grade card + blind-reviewer dispatch on every weak human prompt) conflicts with (a) Manual §7.5 "verification happens off-stage; only its results appear" (effort theater), (b) Anthropic's smaller-prompt finding, (c) its own telemetry: 425 recorded misses, 24 in the last 7 days — a rule chronically missed at this rate is over-broad, per `rule-curation.md`'s own reactive standard | `.claude/.enhance-misses.log` counts in session banner; Manual §7.5 | **REWRITE** (the big one) — adopt the dormancy predicate (fires when a number/irreversible/outward/memory-sourced stake exists); render RESULTS (grade + what changed), not process; keep the blind reviewer for genuinely weak prompts only. Compose with the pending post-#332 telemetry re-measure (~2026-07-19) |
| C9 | `claude-behavior.md` rule 2 "task requires changes to **more than 3 files → stop and break it up**" is weak-model babysitting at frontier tier and contradicts standing full-autonomy directives (rule 23, owner memory) — mid-task stopping is exactly what the owner has corrected against | Rule text vs rule 23 + `feedback_full_autonomy_default` | **DEMOTE** to advisory heuristic, or scope to cheaper-model dispatches |
| C10 | superpowers `using-superpowers` "if there is even a **1% chance** a skill applies you MUST invoke it" contradicts KISS/YAGNI (rule 16/21), decision-authority, and Manual §3 dormancy ("discipline that fires on everything gets turned off") | Both injected every session | **FLAG** — third-party plugin text, can't edit; consider disabling its SessionStart injection or an explicit precedence note |
| C11 | Rule 14's todo.md protocol overlaps three other tracking surfaces (platform TaskCreate, `.remember/`, `.claude/sessions/`) with no precedence order — in practice the Work Queue + .remember are the live ones | Four surfaces, no arbiter named | **REWRITE** — name todo.md (Work Queue) as SSOT, others as views |

## 3. What is HEALTHY (verified, no action)

The core SSOT set (decision-authority, plan-before-coding, supervisor-verification,
independent-test-verification, configuration-ssot, git-collaboration) is internally consistent,
properly cross-referenced, and non-duplicative — the pointer discipline works where it was applied.
The dual-home sync gate, the trust-score rulebook, and the Manual v2.0 have no contradictions with
the rule stack. The contradictions cluster almost entirely in the OLDEST file
(`claude-behavior.md`, which predates the SSOT extraction) and in HOOK DETECTOR PRECISION — not in
the newer architecture.

## 4. Recommended sequence (all owner-gated)

1. **Fix the two bugs first** (C5 machine-origin exemption, C6 BA-gate precision) — they are
   enforcement drift, not rule changes; still proposed here because hooks are governance surface.
2. **One `claude-behavior.md` cleanup PR** (C1, C2, C3, C7, C9, C11) — six edits, one review.
3. **`model-routing.md` scoping line** (C4) — one paragraph.
4. **Enhance-ceremony rewrite** (C8) — the highest-value, highest-blast-radius change; do it WITH
   the ~2026-07-19 telemetry re-measure so the decision is evidence-carrying, and bump the
   prompt-auto-enhance plugin per `/plugin-lifecycle` if its settings change.
5. **Volume experiment** (§1 proposal) — cheap A/B; its result feeds a possible CLAUDE.md
   budget-compliance extraction pass (a separate, larger decision).

**Risk lines:** volume estimates marked (est.) are unmeasured composites — the measured rows alone
already make the case. C5/C6 diagnoses are from single-session observations; reproduce each once
before patching the hooks (per Manual §8). C8's rewrite touches the owner's most-reinforced visible
ritual — do not apply any part of it without explicit sign-off on the exact new firing predicate.
