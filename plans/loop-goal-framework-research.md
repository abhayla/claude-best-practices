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

### 2.5b Known gotchas / limitations (practitioner-reported — capture, not yet judged)

Recurring cautions across community write-ups (treat as reported, verify against official docs
before relying on any one):

- **No native per-goal token budget cap.** A long `/goal` run can consume an order of magnitude
  more tokens than expected; it runs until the condition is met or `Ctrl+C`/`/goal clear`. Simplest
  mitigation = a **turn/time clause in the condition** ("…or stop after 20 turns"). *(Maps onto the
  hub's `--max-cycles` + global retry budget in `/loop-engineering`.)*
- **Context-window compaction mid-run.** Long sessions summarize earlier work to stay in the window,
  so early context can be compressed/lost. *(Note: this is also how a stated auto-mode boundary can
  be dropped — see `permission-modes.md`.)*
- **Evaluator blind spots.** The evaluator only reads the transcript (no tool calls), so a vague
  condition ("until the code is clean") leaves it guessing — it churns or quietly declares done.
  Conditions must flip from a "no" to a "yes" on something **Claude's own output demonstrates**.
- **Don't leave an open-ended goal running overnight without Auto mode.** Without auto mode a `/goal`
  run stalls waiting for per-write approvals; **Auto mode + `/goal` is the combination that makes
  unattended runs practical** (auto mode = per-tool approval, `/goal` = per-turn). For scheduled/
  headless work use `claude -p`.
- **Compound objectives overwhelm it.** "Redesign auth, add OAuth, write tests, update docs" is too
  much for one goal — break into **sequential goals**, each with its own verifiable end state.

### 2.5c Origin / notable framing (capture, not yet judged)

- **Lineage (the real origin chain):** **Ralph Loop** (Geoffrey Huntley, mid-2025) — a bare bash
  loop `while :; do cat PROMPT.md | claude-code ; done` that re-ran a prompt with NO stop condition,
  working because each iteration inherited file state + git history. Huntley's maxim: **"sit on the
  loop, not in it"** (supervise from above). → June 2026 Anthropic **productized it** into native
  `/loop`+`/goal` with proper stop conditions + tooling. `/goal` is described as **"the Ralph loop,
  built in."**
- **"Loop engineering"** the name was coined by **Addy Osmani (Google)** — the hub's
  `/loop-engineering` already cites his "a loop running unattended is a loop making mistakes
  unattended" line.
- **Boris Cherny (creator of Claude Code):** *"I'm not prompting Claude anymore. I'm building
  loops"* — claims 100% of his recent contributions came via Claude Code loops, no hand-editing
  since November (community-quoted; primary source not yet verified).
- **Recommended patterns (community consensus):** persistent `CLAUDE.md` as memory (record mistakes
  so the loop stops repeating them); 3–5 git worktrees each with its own session; **adversarial
  verification** (agents whose only job is to find faults, so the loop can't game weak conditions);
  structure work around **verifiable goals** (tests pass, lint clean, e2e checks) not prompt-perfecting.
- **Criticisms / risks (capture):** *"A loop is exactly as good as the success condition you can
  write."* — verification problem; **self-deception/gaming** (satisfies the letter, not the spirit,
  of a weak condition → mitigation: genuinely strong tests + adversarial review); **scope** (loops
  shine on mechanically-checkable work — migrations, upgrades, test suites — and struggle on
  underspecified, taste-driven work); **model-vs-method** (stronger models, Opus 4.8 / Fable 5,
  reduce iteration need, so some credit is capability not loop philosophy). The thesis: the
  appreciating skill is now **verification-harness design**, not prompt craft.
  *(NB: this independently validates the hub's `/loop-engineering` maker≠checker + verifiable-DoD +
  worktree design — a convergence to capture for the brainstorm, not yet a decision.)*
- **Predecessor tool:** `github.com/jthack/claude-goal` — a "Codex-style `/goal` command for Claude
  Code" built before the native command shipped (historical; not yet inspected).

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

_(The four official pages cached 2026-06-27 + the community sources below were proactively pulled
by me; the user's own links are still awaited and will be appended here as they arrive.)_

### C1 · Community sweep (proactive, 2026-06-27) — Reddit/HN/blog sentiment + gotchas

Captured neutrally. Practitioner content is mostly vendor/blog explainers + a few opinion pieces;
no raw Reddit/HN thread text was directly retrievable in this pass (search-indexed only).

- **Webcoda — "The Loop People Were Right: Anthropic Shipped Their Argument as a Feature"**
  (https://ai-checker.webcoda.com.au/articles/loop-driven-development-claude-code-loops-goals-2026):
  best single history. Ralph Loop (Huntley, mid-2025) → native June 2026. `/loop` = scheduler (state
  in files+git, no stop logic); `/goal` = evaluator ("the Ralph loop, built in"). Patterns: CLAUDE.md
  memory, 3–5 worktrees, adversarial verification, verifiable goals. Criticisms: "a loop is exactly
  as good as the success condition you can write"; gaming/self-deception; mechanical-task scope;
  model-vs-method. Thesis: verification-harness design is the new core skill. (Key claims folded into
  §2.5b/§2.5c above.)
- **MindStudio blog series** (multiple URLs) — explainers on `/goal`+`/loop` for autonomous long-
  running tasks; the "second smaller model reads the transcript, yes/no" evaluator description.
- **xda-developers — "I finally understood Claude Code's /goal command after realizing I was using it
  completely wrong"** (https://www.xda-developers.com/finally-understood-claude-code-goal-command/) —
  the "vague condition = loop guessing / churns or quietly quits" gotcha.
- **Apiyi blog — "goal mode: 6 key points"** (https://help.apiyi.com/en/claude-code-goal-mode-keep-working-until-done-guide-en.html).
- **DeskTheory — "When to use /goal vs /loop"** (https://desktheory.com/workflows/goal-vs-loop-claude-code) —
  `/goal` = get something done; `/loop` = keep an eye on something.
- **Avi Chawla — "Claude Code's /goal Command"** (https://blog.dailydoseofds.com/p/claude-codes-goal-command).
- **Jason Croucher — "Claude Code /goal: A Field Guide with Games"** (https://medium.com/@jason.croucher/claude-code-goal-a-field-guide-with-games-f6f3b617ce5b).
- **aifromthefield — "I spent a full day saying keep going"** (https://aifromthefield.substack.com/p/i-spent-a-full-day-saying-keep-going) — `/goal` vs the manual "keep going" nudge, Claude vs Codex.
- **Threads not yet inspected (queued for deeper pass if wanted):** `github.com/jthack/claude-goal`
  (predecessor repo); Geoffrey Huntley's original Ralph write-up; primary sources for the Osmani
  "loop engineering" coinage + the Boris Cherny quotes.

### User-supplied links

#### L1 · @Raytar tweet → X article "Stop Being the Loop" (sent 2026-06-27; tweet dated 2026-06-23)

- **Link as sent:** https://x.com/i/status/2069212188619805179
- **The tweet itself** (via X syndication endpoint): author **@Raytar** ("Raytar"), 2026-06-23, body is
  just a t.co link to an X long-form **article**: **"Stop Being the Loop. Here's How to Make Claude
  Work While You Sleep"** (`x.com/i/article/2052792872672415744`). Preview line: *"The person who
  built Claude Code at Anthropic stopped prompting Claude. His name is Boris Cherny."* (318 likes, 2
  replies at capture).
- **Article body:** NOT retrievable — X long-form articles are login-walled (HTTP 402). Captured the
  title + preview + the primary sources it traces to (below) instead. _(Flag for the user: paste the
  article text if you want its exact wording captured.)_

**Primary sources this article traces to** (fetched directly, since the article was walled):

- **Addy Osmani — "Loop Engineering"** (https://addyosmani.com/blog/loop-engineering/ — the canonical
  coinage). Verbatim definition: *"Loop engineering is replacing yourself as the person who prompts
  the agent. You design the system that does it instead."* Quotes **Peter Steinberger** (June 8 2026):
  *"You shouldn't be prompting coding agents anymore. You should be designing loops that prompt your
  agents."* and **Boris Cherny**: *"I don't prompt Claude anymore. I have loops running that prompt
  Claude and figuring out what to do. My job is to write loops."* **Five components:** (1) Automations
  (scheduled discovery/triage), (2) Worktrees (parallel isolation), (3) Skills (`SKILL.md` codified
  knowledge), (4) Plugins/Connectors (MCP), (5) Sub-agents (separate verification, anti self-grading)
  — plus persistent **state** (markdown/Linear) since models forget between runs. Maps to CC: `/loop`
  (cadence), `/goal` (runs until a verifiable condition; a different model grades), `git worktree`,
  `.claude/agents/`. **Three warnings:** verification burden stays yours (unattended loops make
  unattended mistakes); comprehension debt grows; cognitive-surrender temptation. Closer: *"Build the
  loop. But build it like someone who intends to stay the engineer, not just the person who presses go."*
- **"How Boris Uses Claude Code"** (https://howborisusesclaudecode.com/) — concrete practices:
  - **Verification is #1:** *"give Claude a way to verify its work. If Claude has that feedback loop,
    it will 2-3x the quality."* (frontend → Chrome extension; backend → Claude starts + tests the
    server e2e).
  - **`/loop`** for recurring unattended tasks running **up to 3 days locally** — e.g. *"babysit all
    my PRs. Auto-fix build issues and when comments come in, use a worktree agent to fix them"*; every
    5 min for code review, 30-min cycles for feedback.
  - **`/goal`** sets completion conditions that prevent premature exit (test suite passes, lint clean).
  - **`/loop` + `/goal` + `/schedule`** paired: `/schedule` = cloud recurring (survives laptop close),
    `/goal` = hard completion bar, `/loop` = local shorter intervals.
  - **Budget:** caps token spend in the prompt itself — *"use 50k tokens"*; runs `/usage` to find which
    skills/MCPs over-consume on long runs.
  - **"Write it down":** *"Every single time Claude makes a mistake, I don't tell it to do it
    differently. I tell it to write it to the CLAUDE.md"* (compounds across sessions).
  - **Context minimalism:** abandoned plan mode for 4.6+ models (*"The newer models don't actually need
    a planning step"* — auto mode handles implicit planning); minimal system prompts, Claude fetches
    context via files/MCP on demand.
  - **Nested subagents** (depth up to 5) to keep parent contexts clean.

  _(NB for the brainstorm — capture, not judgment: several of these touch hub conventions to discuss —
  the hub's `plan-before-coding.md` vs Boris's "no plan step on 4.6+"; the hub's single-level-dispatch
  convention vs Boris's depth-5 nesting; "write it down to CLAUDE.md" vs the hub's `learnings-routing.md`
  + lessons.md; budget-in-prompt vs the hub's `--max-cycles`/retry budgets. Osmani's 5 components ≈ the
  hub's existing loop-engineering spine. NOT decided — flagged for our discussion.)_

#### L2 · @AnatoliKopadze tweet → X article "Loops explained: Claude, GPT, Mira and what actually works" (sent 2026-06-27; tweet dated 2026-06-20)

- **Link as sent:** https://x.com/i/status/2068328135611822149
- **The tweet** (via syndication): author **@AnatoliKopadze** ("Anatoli Kopadze"), 2026-06-20, body is a
  t.co link to the X **article** **"Loops explained: Claude, GPT, Mira and what actually works"**
  (`x.com/i/article/2068024770029932544`). Preview: *"AI has been in everyone's hands for years. Most
  people who use it every day still use it the slowest way there is: type a request, wait, fix it, ask
  again, all by hand…"* (4,973 likes, 145 replies at capture).
- **Article body:** login-walled (HTTP 402); the YouMind tracker mirror 404'd. Substance recovered via
  search (capture, not verbatim):
  - **AI loop = plan → execute → verify**: "an agent looks at the current state, chooses the next
    action, does it, checks the result, and decides what to do next."
  - **The shift framing**: *"ChatGPT answers, Mira acts. You do not ask it to write the email, you tell
    it to send the email. You do not get a draft ticket, you get a real one in Linear with the owner
    assigned."* (loops/agents as actors, not responders).
  - Repeats the Boris Cherny *"my job is to write loops"* thesis; covers technical implementation, cost
    management, and applications across models (Claude / GPT / Mira).
  - _(Flag for the user: paste the article text if you want its exact wording.)_

- **Notable adjacent posts by the same author** (surfaced in search; capture-worthy quotes, primary
  X sources login-walled so quotes are as-reported):
  - *"Anthropic engineers just showed how they build a full app from scratch, using a loop of agents —
    40 minutes from the team behind Claude Code. They used three agents: one to plan, one to build, one
    to judge, cycling until the app actually works."* (`x.com/AnatoliKopadze/status/2068690663919530207`)
    — the **plan→build→judge** loop = the hub's maker≠checker pattern with an explicit planner.
  - **Boris Cherny:** *"Every night I have hundreds, sometimes thousands of agents running in loops for
    5, 10, 20 hours straight. This is just how engineering is done now."*
    (`x.com/AnatoliKopadze/status/2069433889278288126`)
  - **Jensen Huang (NVIDIA CEO):** *"Nobody writes prompts anymore. The new job is to write and handle
    loops."* (`x.com/AnatoliKopadze/status/2068360095562420529`)
- **Additional primary sources on "loop engineering" surfaced (not yet fetched — queued):**
  Louis Bouchard (https://www.louisbouchard.ai/loop-engineering/), Cobus Greyling
  (https://cobusgreyling.substack.com/p/loop-engineering), Lushbinary
  (https://lushbinary.com/blog/loop-engineering-ai-coding-agents-guide/).

#### L3 · @vicky_grok tweet → X article "How to Build Self-Improving AI Agents with Loop Engineering" (sent 2026-06-27; tweet dated 2026-06-23)

- **Link as sent:** https://x.com/i/status/2069392437337018445
- **The tweet** (via syndication): author **@vicky_grok** ("Vikas gupta"), 2026-06-23, t.co link to the
  X **article** **"How to Build Self-Improving AI Agents with Loop Engineering"**
  (`x.com/i/article/2069386620164567040`). Preview: *"Most AI agents do not fail because the model is
  weak. They fail because the system around the model is weak."* (67 likes, 5 replies at capture).
- **Article body:** login-walled (402); substance recovered via search (capture, not verbatim):
  - **Loop engineering** = "building small automated control systems — loops — that drive AI coding
    agents on your behalf, instead of prompting turn by turn."
  - **Self-improving loop**: "does its task, checks its own result, learns from what happened, writes
    down useful lessons, stores them in memory, and applies them next time."
  - **The system around the model**: control structures, validation gates, state management; closed-loop
    cycles named **Discover → Plan → Execute → Verify → Iterate**.
  - **Foundational rule**: *"Build the verifier first, separate from the agent. This is the part most
    beginners skip and the part that prevents silent failures."*
  - _(Flag for the user: paste the article text for exact wording.)_
- **Adjacent source surfaced (queued):** Plaban Nayak — "Loop Engineering: Building Self-Improving AI
  Agents with **Four Nested Loops**" (https://nayakpplaban.medium.com/loop-engineering-building-self-improving-ai-agents-with-four-nested-loops-c0f4a1437d4f)
  — a more elaborate structural model worth a look for the brainstorm. Others: Analytics Vidhya,
  Codersarts ("self-running AI coding agents 2026 guide").

  _(NB for the brainstorm — capture, not judgment: this article's **Discover→Plan→Execute→Verify→
  Iterate** cycle + **"build the verifier first, separate from the agent"** + **self-improving
  (learn→store→apply)** are an almost exact description of the hub's existing `/loop-engineering`
  skill (DISCOVER→PLAN→EXECUTE→VERIFY→SHIP|FEEDBACK, maker≠checker, `/learn-n-improve` each cycle).
  Strong external convergence with what the hub already built — flagged, not decided.)_

#### L4 · @RohOnChain tweet → X article "How To Use Loop Engineering To Build A Self-Improving Quant Trading System" (sent 2026-06-27; tweet dated 2026-06-22)

- **Link as sent:** https://x.com/i/status/2069056530960490835
- **The tweet** (via syndication): author **@RohOnChain** ("Roan"), 2026-06-22, t.co link to the X
  **article** **"How To Use Loop Engineering To Build A Self-Improving Quant Trading System"**
  (`x.com/i/article/2067524770175057920`). Preview: *"I will break down exactly how to build the loops
  that run an entire quant trading system on their own…"*
- **Article body:** login-walled (402); substance recovered via search (capture, not verbatim) — note
  this is a **domain-application** piece, thinner on new framework theory:
  - Loop engineering applied to a vertical: a **self-improving, autonomous system via a ~six-part
    architecture** running an "entire quant trading system on their own," framed as the shift from
    manual prompting to loop engineering.
  - **Self-improvement loop instance**: the agent **critiques its own prompts/strategies and retests
    within a controlled simulator** — i.e. the simulator IS the verifier (a domain instance of L3's
    "build the verifier first, separate from the agent").
  - "Own the full loop from idea to live capital" with risk discipline between signal and execution.
  - _(Flag for the user: paste the article text for exact wording.)_
- **Academic anchor surfaced (real research, not blog — queued):** **QuantAgent** — "Seeking Holy Grail
  in Trading by Self-Improving Large Language Model" (https://arxiv.org/pdf/2402.03755) — self-improvement
  loops that critique prompts + strategies and retest in a simulator. (Also generic LLM-agent-loop
  survey material: self-debug / self-correct / self-refine within a single task.)

  _(NB — capture, not judgment: same self-improve + simulator-as-verifier pattern as L3, instantiated
  in a vertical. Value for the brainstorm = evidence the loop pattern generalizes to domain apps, and
  a citable academic grounding (QuantAgent) for the self-critique-and-retest mechanism.)_

#### L5 · @0x_rody tweet → X article "How to Move From Writing Code to Orchestrating Agents" (sent 2026-06-27; tweet dated 2026-06-26)

- **Link as sent:** https://x.com/i/status/2070440208248496260
- **The tweet** (via syndication): author **@0x_rody** ("rody", blue-verified), 2026-06-26, t.co link to
  the X **article** **"How to Move From Writing Code to Orchestrating Agents (Full Breakdown Inside)"**
  (`x.com/i/article/2070435793785532416`). Preview: *"The best engineers barely write code by hand
  anymore… They moved up a level. Now they direct agents that write it, and just verify what comes back."*
- **Article body:** login-walled (402); substance recovered via search (capture, not verbatim) — the
  richest verification/stop-condition articulation in the set so far:
  - **The shift**: "the bottleneck shifts from authorship to orchestration. When the model can write the
    code, the scarce skill is designing the cycle that keeps it correct and pointed at the goal."
  - **Engineer's new role**: "define the task, provide context, set boundaries, create checks, review the
    work, decide the next move" — evaluate whether the agent solved the RIGHT problem + prevent
    architectural drift + orchestrate how multiple agent-built components fit.
  - **Verification is the fastest-growing sub-theme** (after Steinberger's tweet): *"Half of loop
    engineering is design; the other half is something that can say no. A loop that writes → runs →
    reads the result → corrects is what actually works in production."*
  - **Convergent recipe for long unattended agents** (quote): *"specify the desired end state, the
    evidence required to prove success, the constraints that must not be violated, and a hard ceiling on
    turns or budget. The agent stays the executor; you write the acceptance test it has to pass before it
    is allowed to claim done."*
  - _(Flag for the user: paste the article text for exact wording.)_
- **Higher-signal sources surfaced (queued — better than the blog explainers):**
  **O'Reilly Radar — "Loop Engineering"** (https://www.oreilly.com/radar/loop-engineering/);
  **Thoughtworks — "Supervisory engineering: orchestrating software's 'middle loop'"**
  (https://www.thoughtworks.com/insights/blog/agile-engineering-practices/supervisory-engineering-orchestrating-software-middle-loop);
  **Arize — "Closing the Loop: Coding Agents, Telemetry, and the Path to Self-Improving Software"**
  (https://arize.com/blog/closing-the-loop-coding-agents-telemetry-and-the-path-to-self-improving-software/);
  **LangChain — "Agentic Engineering"** (https://www.langchain.com/blog/agentic-engineering-redefining-software-engineering).

  _(NB — capture, not judgment: the "end state · evidence · constraints · hard turn/budget ceiling ·
  acceptance-test-before-done" recipe is, almost line-for-line, the hub's `goal-creator` contract +
  `dod-verbs.md` (ACTION + COMPLETENESS BAR) + `output-plausibility-verification.md` +
  `supervisor-verification.md` + `--max-cycles`/retry budgets. "Something that can say no" = the hub's
  maker≠checker. This is the densest external corroboration of the hub's design — flagged for the brainstorm.)_

_(append further user links below)_

