Source: https://x.com/ClaudeDevs/status/2074208949205881033
Captured: 2026-07-08

# Claude Code team — "Getting started with loops" (the OFFICIAL loop taxonomy)

**Author:** @ClaudeDevs — *article written by [@delba_oliveira](https://x.com/delba_oliveira), on the Claude Code team* (**this is a first-party Anthropic source**, not a third-party influencer take)
**Posted:** 2026-07-06 · **Engagement at capture:** 16,955 likes, 2,078 RTs, 310 replies, 5.56M views
**Format:** Single long-form X-native article (~7.8k chars) + linked Claude Code docs.
**Nature:** **Authoritative first-party definition.** No product claims to verify — this IS the vendor defining its own primitives. Highest-authority item in the whole loop-capture cluster: when the hub's `loop-engineering` doctrine needs to cite "what Anthropic officially means by a loop," this is the source.

---

## The official definition + taxonomy

> "On the Claude Code team, we define **loops as agents repeating cycles of work until a stop condition is met.**"

Categorized by: **how triggered / how stopped / which Claude Code primitive / what task suits it.** Four types:

| Loop type | Primitive | Triggered by | Stops when | Best for |
|---|---|---|---|---|
| **Turn-based** (the "agentic loop") | a user prompt | you, each turn | Claude judges task done / needs context | short, non-recurring tasks |
| **Goal-based** | `/goal` | a manual real-time prompt | goal met (evaluator model checks) OR max turns | tasks with **verifiable exit criteria** |
| **Time-based** | `/loop` (local), `/schedule` (cloud routine) | a time interval | you cancel, or work completes (PR merges / queue empty) | recurring work; interfacing with external systems |
| **Proactive** | `/schedule` + auto mode + dynamic workflows | event/schedule, no human in real time | each task exits at its goal; routine runs until turned off | recurring streams: bug reports, triage, migrations, dep upgrades |

Key mechanics stated:
- **Turn-based:** encode your manual verification steps as a `SKILL.md` so Claude self-verifies end-to-end — *"the more quantitative the checks, the easier it is for Claude to self-verify."*
- **Goal-based:** *"an evaluator model checks your condition and sends it back to work until the goal is met or a turn cap is reached"* — which is why **deterministic criteria (tests passed, score threshold) are so effective** and stop Claude ending "good enough" early.
- **Time-based:** `/loop` runs on your machine (turn it off → it stops); move to cloud via `/schedule` (a "routine").
- **Proactive:** compose `/schedule` + `/goal` + skills + **dynamic workflows** (research preview, orchestrate agents at scale) + **auto mode** (runs without asking permission) into long-running work.

## Two operational discipline lists (verbatim value)

**Maintaining code quality in a loop** — *"the quality of a loop's output depends on the system around it":*
1. Keep the codebase clean (Claude follows existing conventions).
2. Give Claude a way to **verify its own work** (encode "good" as skills).
3. Make docs easy to reach.
4. **Use a second agent for code review** — *"a reviewer with fresh context is less biased and not influenced by the main agent's reasoning"* (`/code-review` or GitHub Code Review).
5. When a result misses the standard, **don't just fix the instance — encode the fix to improve the system for all future iterations.**

**Managing token usage** — *"loops should have clear boundaries":*
- Choose the right primitive **and model** for the job (small tasks don't need multi-agent; some tasks use cheaper/faster models).
- Define clear success/stop criteria.
- **Pilot before a large run** (dynamic workflows can spawn hundreds of agents — gauge on a slice first).
- **Use scripts for deterministic work** (running a script is cheaper than re-reasoning the steps).
- Don't run routines more often than the watched thing changes.
- Review usage: `/usage` (by skills/subagents/MCPs), `/goal` (turns + tokens), `/workflows` (per-agent tokens, stop any agent).

**Getting started:** look at work where *you* are the bottleneck; ask which piece you can hand off (can you write the verification check? is the goal clear? does work arrive on a schedule?); run, observe where it stalls/over-reaches, iterate.

---

## Relevance to this hub — VERY HIGH (first-party validation of the hub's entire loop model; adopt the vocabulary)

This is the **authoritative anchor** the hub's loop doctrine has been asserting without an official citation. Nearly every hub loop mechanic is confirmed here by its vendor. Map:

| ClaudeDevs official mechanic | Existing hub analogue |
|---|---|
| Loop = "cycles until a **stop condition**"; every loop needs an exit / turn cap | `loop-engineering` DISCOVER→PLAN→EXECUTE→VERIFY→SHIP under **hard budgets** + `/escalation-report` on exhaustion |
| **Goal-based `/goal`** with an **evaluator model** + deterministic criteria | `goals.yml` machine-checkable DoDs; trust-score `threshold`/hard-gates; `/goal-creator` contract |
| **Second agent for review, fresh context, less biased** | `independent-test-verification.md` + `supervisor-verification.md` (**maker ≠ checker**) — *the single most-emphasized point in both the official article and the hub* |
| **Encode the fix to improve the system, not just the instance** | `learning-self-improvement` / `lessons.md`; `claude-behavior.md` #5 (self-improving rules) |
| **Time/Proactive loops** `/loop` (local) → `/schedule` (cloud routine) | the hub's `ScheduleWakeup`/loop cadence + `scan-*.yml` scheduled workflows; `cc-adoption-scout` free-in-session vs paid-scheduled distinction |
| **Route routines to smaller models, capable model for judgment** | `model-routing.md` "cheapest sufficient model per dispatch" — **verbatim agreement** |
| **Pilot before a large run** (dynamic workflows spawn hundreds) | Workflow-tool budget guards; `parallel()`/`pipeline()` concurrency caps |
| **Scripts for deterministic work > re-reasoning** | `claude-behavior.md` #16 KISS; the "use a script not an agent for deterministic steps" instinct |

**Genuine adoption actions (higher-confidence than the influencer captures because this is first-party):**
1. **Adopt the official 4-type taxonomy (Turn / Goal / Proactive / Time) as the naming spine** of `docs/specs/loop-engineering-spec.md` — the hub currently names its own loop stages but does not classify loops against Anthropic's own four types. This gives the hub's spec an authoritative, forward-compatible vocabulary and a clean mapping from each hub workflow to a native primitive (`/goal`, `/loop`, `/schedule`, dynamic workflows, auto mode).
2. **Evaluate native `/goal` + evaluator-model** against the hub's hand-rolled DoD/trust-score gating — this is exactly the `cc-adoption-scout` "adopt vs keep-hand-rolled" decision, and it's now first-party GA, so it warrants a migration issue rather than a MEASURE-FIRST.
3. **`/usage`, `/goal` (no args), `/workflows` token-introspection commands** — confirm these are surfaced in the hub's loop-budget guidance; they're the native equivalent of the Workflow tool's `budget.spent()`.

**Cross-links:** the influencer-level restatements of this same material — [0xCodila Karpathy/Bilevel loop](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md), [sairahul 20 loop patterns](2026-07-01-sairahul-20-loop-design-patterns.md) + [New AI Stack](2026-07-07-sairahul-new-ai-stack-harness-layers.md), [Andrew Ng 3 loops](2026-06-30-andrew-ng-3-product-development-loops.md), [Karpathy field notes](2026-karpathy-loops-md-field-notes.md). **This is the primary source they all orbit** — cite THIS when the hub needs the canonical definition. **No verification prerequisite** (first-party).
