# Research: Anthropic's `/goal` + `/loop` Autonomous Loop Framework

> **Status:** Research notes — feeds a brainstorm (hub adoption + downstream propagation).
> **Authored:** 2026-06-27 · **Mode:** research only, NOT a build plan yet.
> **Role:** Developer-tooling Researcher.
> Primary sources are the cached official docs (`docs/claude-references/goal.md`,
> `docs/claude-references/scheduled-tasks.md`, fetched 2026-06-23); community framing is
> secondary and flagged as such. Sources listed at the bottom.

---

## 1. Executive summary (the answer)

There is **no single "loop workflow" command**. What Anthropic shipped is a small set of
**complementary primitives** for "keep the session running between prompts," which compose into
autonomous long-running work. The two the user is thinking of:

- **`/goal <condition>`** — sets a **completion condition**. After every turn, a small fast model
  (Haiku by default) checks whether the condition holds against the transcript; if **not**, Claude
  **starts another turn automatically** instead of returning control. The goal clears itself the
  moment the condition is met. It is a wrapper around a **session-scoped prompt-based Stop hook**.
  Requires Claude Code **v2.1.139+**.
- **`/loop [interval] [prompt]`** — **re-runs a prompt on a time interval** (fixed cron, or a
  Claude-chosen dynamic delay), or runs a built-in maintenance prompt / your `loop.md`. Session-scoped,
  **7-day expiry**. Requires **v2.1.72+**.

The **"combination that makes it run automatically"** is:

> **`/goal` (a verifiable finish line) + Auto mode (unattended tool approval) → Claude works turn
> after turn until a fresh evaluator model confirms the condition is met.**
> `/loop` is the interval-driven sibling for polling/maintenance; a **Stop hook** is the
> customizable, persistent version of the same after-every-turn idea.

The community has named the *discipline* of designing these loops **"loop engineering"** — and
**this hub already ships a `/loop-engineering` skill and a `/goal-creator` skill** built around
exactly these primitives. So a large part of this work is **gap analysis** (native vs. what we
already built), not greenfield.

---

## 2. The native primitives (authoritative — from cached official docs)

### 2.1 `/goal` — run until a condition is met

| Property | Detail |
|---|---|
| What starts the next turn | The previous turn **finishing** |
| What stops it | A model **confirms the condition is met** (or `/goal clear`) |
| Mechanism | Wrapper around a **session-scoped prompt-based Stop hook**; condition + transcript → small fast model (Haiku) → yes/no + short reason. "No" → another turn, the reason guides it. "Yes" → clears, records an achieved entry. |
| Evaluator limits | **Does NOT call tools** — judges only what Claude has **surfaced in the transcript**. So conditions must be provable by Claude's own output (e.g. "`npm test` exits 0" works because the result lands in the transcript). |
| Scope | One goal per session; setting a goal **starts a turn immediately**; `◎ /goal active` indicator. |
| Bounding | Put a turn/time clause **in the condition** ("…or stop after 20 turns"). Condition ≤ 4,000 chars. |
| Status / clear | `/goal` (no arg) shows condition, runtime, turns, token spend, last evaluator reason. `/goal clear` (aliases: stop/off/reset/none/cancel) cancels; `/clear` also clears. |
| Resume | An active goal is restored on `--resume`/`--continue` (condition carries; turn/timer/token baselines reset). |
| Headless | `claude -p "/goal …"` runs the loop to completion in one invocation. Ctrl+C interrupts. |
| Cost | Evaluator tokens billed on the small fast model — "typically negligible vs main-turn spend." |
| Requirements | Trusted workspace (evaluator is part of hooks); unavailable if `disableAllHooks` / `allowManagedHooksOnly`. |

**Writing an effective condition** (load-bearing): one **measurable end state** (test result, exit
code, file count, empty queue) + a **stated check** (how Claude proves it) + **constraints that
must hold** (what must not change). This maps 1:1 onto the hub's `dod-verbs.md` ("ACTION +
COMPLETENESS BAR") and `/goal-creator`'s zero-open-questions contract.

### 2.2 `/loop` — re-run on an interval

| What you provide | Example | Behavior |
|---|---|---|
| Interval + prompt | `/loop 5m check the deploy` | Prompt runs on a **fixed cron** schedule |
| Prompt only | `/loop check the deploy` | Prompt runs at a **Claude-chosen dynamic** delay (1 min–1 hr, short while active, long when quiet; may use the **Monitor tool** for streaming instead of polling) |
| Interval only / nothing | `/loop` | Runs the **built-in maintenance prompt**, or your **`loop.md`** if present |

- Can re-run another command: `/loop 20m /review-pr 1234`.
- **Built-in maintenance prompt** (bare `/loop`): continue unfinished work → tend the current
  branch's PR (review comments, failed CI, merge conflicts) → cleanup passes (bug hunts,
  simplification). Does **not** start new initiatives; irreversible actions only continue something
  the transcript already authorized.
- **`loop.md`** (`.claude/loop.md` project-level wins over `~/.claude/loop.md`) replaces the default
  prompt; plain Markdown, edits apply next iteration, ≤25 KB.
- **Stop**: `Esc` while waiting; self-paced loops can end themselves by not scheduling the next
  wakeup; fixed-interval loops run until stopped or **7-day expiry**.
- **Scheduling tools under the hood**: `CronCreate` / `CronList` / `CronDelete` (5-field cron,
  ≤50 tasks/session, jitter, 7-day expiry). Disable all via `CLAUDE_CODE_DISABLE_CRON=1`.

### 2.3 The three "keep the session running" approaches (from `goal.md`)

| Approach | Next turn starts when | Stops when |
|---|---|---|
| **`/goal`** | previous turn finishes | a model confirms the condition is met |
| **`/loop`** | a time interval elapses | you stop it, or Claude decides work is done |
| **Stop hook** | previous turn finishes | your own script or prompt decides |

**Auto mode** is orthogonal: it approves **tool calls within a turn** but does **not** start a new
turn. `/goal` + auto mode are **complementary** — auto mode removes per-tool prompts; `/goal`
removes per-turn prompts. Together = unattended turn-after-turn execution to a verifiable end.

### 2.4 Scheduling that survives session close (the durable tier)

`/loop` and `/goal` are **session-scoped** (only fire while Claude Code is running + idle; cleared
on a fresh conversation; restored on `--resume` if unexpired). For automation that runs **without an
open session**, the durable options are **Cloud Routines** (Anthropic-managed, ≥1 hr min, no local
files), **Desktop scheduled tasks** (local machine, local files), and **GitHub Actions** (`schedule`
trigger). The hub's own durable crons (scan-internet, aggregate-telemetry) correctly stay on GitHub
Actions for exactly this reason.

### 2.5 `/batch` (adjacent, community-cited — unverified against official docs)

Community articles list **`/batch`** alongside `/goal`/`/loop` as "manages large-scale refactors by
deploying parallel agents across isolated worktrees." **Unverified** from official docs in this pass.
Note the hub already ships a `/batch` skill (parallel codebase-wide changes across worktrees) — so
if a native `/batch` exists, that's another native-vs-hand-rolled overlap to check.

---

## 3. How they compose into an autonomous workflow

The canonical autonomous-run recipe (synthesised from the docs + the hub's own S7 policy):

1. **Author a zero-open-questions contract** (the brief) — every fork pre-decided, because an
   unattended run never pauses to ask. (Hub: `/goal-creator`.)
2. **Launch the executor in Auto mode** so the irreversible-action deny-class is deterministic when
   no human is watching: `claude --permission-mode auto -p "/goal <condition>"`.
3. **The loop runs**: turn → evaluator checks condition against transcript → not met → next turn
   (guided by the evaluator's reason) → … → met → goal clears.
4. **Bound it**: turn/time clause in the condition; the run terminates or escalates on budget.
5. **For interval/maintenance work** instead of run-to-condition, use `/loop` (or a `loop.md`).
6. **For durable, session-independent** automation, graduate to Cloud Routines / GitHub Actions.

### Community "loop engineering" framing (secondary)

"Loop engineering" = *"designing the LOOP that runs an AI (do the work, check it, repeat) instead of
typing each prompt yourself."* sabrina.dev's 6-part framework: **Automations** (scheduled triggers),
**Worktrees** (isolated work envs), **Skills** (saved instructions), **Connectors** (tools/APIs),
**Sub-agents** (separate doer & checker), **Memory** (external progress tracking). Stop-condition
emphasis: clear verifiable end states + always cap with turn limits + plain-language guardrails
("do not delete anything"). Tagline: *"AI Leverage = Your Skill × Your Clarity."* Note: sabrina.dev
pairs `/goal` with **Routines** (durable), where the user's framing pairs it with **`/loop`**
(in-session) — both are valid, different durability tiers.

---

## 4. What the hub ALREADY has (gap-analysis baseline)

This is the critical input to the brainstorm — we are **not** starting from zero.

| Hub asset | Location | What it already does | Native overlap |
|---|---|---|---|
| **`/loop-engineering` skill** | `core/.claude/skills/loop-engineering/SKILL.md` (v1.1.0, distributable) | Full **DISCOVER → PLAN → EXECUTE → VERIFY → SHIP\|FEEDBACK** meta-loop at T0: maker (`plan-executor-agent`) ≠ checker (`code-reviewer-agent`), self-heals via `/fix-loop`·`/debugging-loop`, learns via `/learn-n-improve`, bounded by `--max-cycles`/retry budgets, emits hub-ward telemetry. Explicitly "triggered by /loop, /goal, cron, or a PR." | Overlaps the *orchestration* layer native `/goal`+`/loop` leave to the user. Native gives the **turn-driver**; the hub skill gives the **verified, self-healing, learning structure** around it. |
| **`/goal-creator` skill** | `core/.claude/skills/goal-creator/SKILL.md` (v2.0.0, distributable) | Interview-first authoring of a **zero-open-questions contract** to hand to `/goal` (or `/loop`/routine/headless `claude -p`). Bakes in §0.1 worktree isolation, §0.2 idempotency preflight, §0.3 progress log, verification-rule pointers, DoD-verbs discipline, Mode B fold-back. | Directly the "write an effective condition" guidance the native docs call load-bearing — but far richer. |
| **S7 Auto-mode policy** | `core/.claude/rules/decision-authority.md` ("Harness enforcement") | Ratified 2026-06-20: **autonomous/headless runs (`/goal`, `/loop`, routines, `claude -p`) default to `--permission-mode auto`**; interactive sessions unchanged. Native Auto mode hard-denies the irreversible class. | This is exactly the native `/goal` + auto-mode composition, already adopted as policy. |
| **`goals.yml` + Atlas Goal Pulse** | repo root + SessionStart banner | Host-owned G0–G6 goal SSOT with machine-checkable DoDs. A *project/portfolio*-level goal vocabulary. | Different altitude from native session-scoped `/goal` (which is a per-run completion condition) — but conceptually aligned (verifiable done-states). |
| **Autonomous branch lifecycle** | `.claude/hooks/auto-git.sh`, `auto-pr.sh`, `auto-pr-reconcile.sh` + `/git-branch-lifecycle` | edit → commit → push → PR → merge-on-green → prune, hands-off. | The native bare-`/loop` maintenance prompt (tend the current PR: review comments, failed CI, conflicts) **mirrors** `auto-pr-reconcile` + `/git-branch-lifecycle cleanup`. Possible consolidation/`loop.md` opportunity. |
| **Trust-score / walk-phase MVP** | `config/trust-score.yml`, `scripts/trust_score.py`, … | Shadow-mode gate deciding whether an autonomous run is trustworthy enough to auto-land vs escalate; hard gates + per-stage graduation. | The "should this loop's output auto-ship?" decision native `/goal` does NOT make — the hub's differentiator. |
| **`cc-adoption-scout` skill** | `.claude/skills/cc-adoption-scout` | The hub's own doctrine for deciding ADOPT / KEEP-hand-rolled / REJECT / MEASURE-FIRST on new CC features. | This is the *exact* decision framework to run `/goal`+`/loop` through in the brainstorm. |

**Headline:** the hub independently built the *structured, verified, self-healing* layer
("loop engineering") on top of the same primitives Anthropic has now surfaced as first-class
`/goal`/`/loop`. The brainstorm question is **how much of our hand-rolled orchestration to delegate
to the native primitives** vs. keep, per our own adoption doctrine.

---

## 5. Open questions for the brainstorm (hub + downstream)

Decisions to make *with* the user — not pre-decided here:

1. **Adopt vs keep-hand-rolled** — run native `/goal`+`/loop`+auto-mode through
   `cc-adoption-scout`'s ADOPT / KEEP / REJECT / MEASURE-FIRST. Where does native *replace* our
   orchestration, where does it *compose under* it, where do we keep ours?
2. **`/loop-engineering` ↔ native `/goal`** — should the meta-loop's turn-driver become native
   `/goal` (let the Haiku evaluator drive turns) while we keep the maker≠checker / trust-score /
   learning structure? Or keep the skill's own loop control?
3. **`loop.md` for the hub** — do we ship a `.claude/loop.md` encoding the hub's maintenance pass
   (reconcile PRs, run the gate, adoption-scout), replacing/complementing `auto-pr-reconcile`?
4. **`/goal-creator` alignment** — does it need updates now that native `/goal` is GA (the
   4,000-char limit, the transcript-only evaluator constraint, the `…or stop after N turns` clause)?
5. **Downstream propagation** — `/loop-engineering` + `/goal-creator` are already distributable.
   What's the *minimum* a downstream project needs to safely use native `/goal`/`/loop` (Auto-mode
   default, deny-rules, trust-gate, version floors v2.1.139 / v2.1.72)? A provisioning bundle?
6. **Durability tiering** — codify when to use session-scoped `/loop` vs durable Routines vs GitHub
   Actions, so downstream projects don't put durable automation on a 7-day-expiring `/loop`.
7. **Safety** — the evaluator judges only the transcript (can't run tools); how do we keep our
   independent-verification + output-plausibility gates as the real proof, not the Haiku yes/no?

---

## 6. Sources

**Authoritative (cached official docs — cite these first):**
- `docs/claude-references/goal.md` — Source: https://code.claude.com/docs/en/goal (fetched 2026-06-23)
- `docs/claude-references/scheduled-tasks.md` — Source: https://code.claude.com/docs/en/scheduled-tasks (fetched 2026-06-23)
- `docs/claude-references/permission-modes.md` — auto/acceptEdits/plan/dontAsk/bypass modes, the auto-mode classifier + default block-list + 3-in-a-row/20-total fallback + protected paths (fetched 2026-06-27)
- `docs/claude-references/auto-mode-config.md` — `autoMode.environment`/`allow`/`soft_deny`/`hard_deny` config + four-tier precedence (fetched 2026-06-27)
- `docs/claude-references/routines.md` — the durable cloud tier: schedule/API/GitHub triggers, `/schedule`, ≥1-hr min, no permission picker (fetched 2026-06-27)
- `docs/claude-references/model-config.md` — small-fast-model (Haiku) for the evaluator/classifier, effort levels + `ultracode`, Fable-5+`/goal` pairing, auto-mode model floors (fetched 2026-06-27)
- `docs/claude-references/headless.md`, `docs/claude-references/hooks-guide.md` — already cached (prior sessions).
- All seven above proactively cached so the framework's full surface is captured before processing the user's incoming links.

**Community / secondary (framing + sentiment — treat as opinion, not spec):**
- sabrina.dev — "AI Loop Engineering: Build Autonomous Agents with Claude Code /goal + Routines":
  https://www.sabrina.dev/p/loop-engineering-claude-code-goal-routines
- MindStudio blog series on `/goal` + `/loop` autonomous workflows:
  https://www.mindstudio.ai/blog/claude-code-goal-loop-commands-autonomous-tasks ·
  https://www.mindstudio.ai/blog/claude-code-goal-auto-mode-autonomous-workflows ·
  https://www.mindstudio.ai/blog/claude-code-5-workflow-patterns-explained
- Rick Hightower (Towards AI) — "The Autonomous Commands That Finish Work While You Sleep
  (/goal, /loop, /batch, etc.)": https://medium.com/@richardhightower/claude-code-the-autonomous-commands-that-finish-work-while-you-sleep-goal-loop-batch-etc-7acb82bf46b1
  *(login-walled on fetch; only the search abstract captured — `/batch` claim is UNVERIFIED.)*
- Avi Chawla — "Claude Code's /goal Command": https://blog.dailydoseofds.com/p/claude-codes-goal-command

**Gaps / honesty notes:**
- No substantive **Reddit / Hacker News** discussion surfaced in this pass — community signal is
  mostly vendor/blog explainers, not raw practitioner debate. (Twitter/X + Reddit skills available
  if deeper sentiment is wanted; not yet run.)
- `/batch` as a native command is **unverified** — only community-claimed.
- Official docs are 4 days old (2026-06-23 cache); refresh `goal.md`/`scheduled-tasks.md` before
  finalizing any implementation if exactness matters.

---

## 7. Raw link captures (append-only — neutral, not yet judged)

> Each link the user sends is logged here verbatim/neutrally: URL · fetched date · extracted
> content/claims, with NO accept/reject judgment (analysis happens in our later discussion).
> Claude/Anthropic docs pages are additionally cached under `docs/claude-references/`.
> New entries appended at the bottom.

_(Awaiting the user's links — none captured yet. The four official pages cached on 2026-06-27,
listed in §6, were proactively pulled by me, not user-supplied.)_

