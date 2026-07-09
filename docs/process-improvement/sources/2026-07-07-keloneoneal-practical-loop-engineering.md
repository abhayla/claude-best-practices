Source: https://x.com/keloneoneal/status/2074484119845605379
Captured: 2026-07-08

# keloneoneal — "A Practical Guide To Loop Engineering Without Yourself"

**Author:** keloneoneal ([@keloneoneal](https://x.com/keloneoneal))
**Posted:** 2026-07-07 · **Engagement at capture:** 68 likes, 11 RTs, 21,921 views
**Format:** Single long-form X-native article (~8k chars).
**Nature:** **Third-party framework write-up** describing an external "loop-engineering" toolkit (`npx loop-audit`/`loop-init`/`loop-cost`/`loop-sync`/`loop-context`, plus `goal-audit` and `loop-mcp-server`). No Anthropic/Claude-model capability claims to verify — the tool/CLI names, npm packages, and readiness-score thresholds are the only concrete claims, and those are internal to the third-party repo (unverifiable from this note, low stakes either way).

---

## What it says

Frames "loop engineering" as replacing manual prompting with autonomous control systems that discover, execute, and verify work over time — eliminating **Intent Debt** (instructions decaying), **Comprehension Debt** (re-contextualizing per task / losing understanding of your own repo as loop PRs pile up), and **Cognitive Surrender** (accepting output without structured verification).

**Getting started:** three CLI tools — `loop-audit` (computes an L0–L3 "Readiness Score" from repo signals: STATE.md, MCP config, verifier skills), `loop-init` (scaffolds skills/state files/observability docs per tool: Grok, Claude, Codex, Opencode), `loop-cost` (estimates token budget by cadence + readiness level). Recommended entry point: **Daily Triage at L1 (report-only)** — no auto-fix in week one.

**Core cycle (6 steps):** Schedule → Triage → State Sync → Execute (isolated worktrees) → Verify (separate Checker agent) → Gate (high-risk pauses for human approval). **Six primitives:** Scheduling, Worktrees, Skills, Connectors (MCP), Sub-agents (Maker/Checker split), State (STATE.md + loop-run-log.md).

**Patterns registry:** seven production-ready patterns (Daily Triage, PR Babysitter, CI Sweeper, Dependency Sweeper, Post-Merge Cleanup, Changelog Drafter, + one more) with defined goal/cadence/risk; coordination rules prevent two patterns double-fixing the same branch.

**Safety/ops:** path denylists (never auto-edit `.env`, `auth/`, `payments/`), default auto-merge = none (only trivial allowlisted paths like doc typos), token budgeting, run logging, kill switches (`loop-pause-all` label). **11 named failure modes** — Infinite Fix Loop (weak verifier → attempt limit of 3), State Rot (no prune step → triage discipline), Token Burn (sub-minute cadence → daily caps), Over-Reach (no path restrictions → denylist), etc.

**Production stories** follow a Setup/What-Worked/What-Broke/Metrics/Lesson format; explicit rule that every story must include a failure or surprise. Named lessons: CI Sweeper needs kill switches + budget caps; "The Verifier Problem" — LLM-as-verifier overfits, needs numerical checkers in some domains; L1 report-only delivers value with zero regression risk; multi-loop collisions need explicit branch coordination.

---

## Relevance to this hub — LOW

This is the **fourth+ capture in the loop-engineering cluster** (see [ClaudeDevs first-party taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md), [0xCodila Karpathy/Bilevel](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md), [Raytar "Stop Being the Loop"](2026-06-23-raytar-stop-being-the-loop.md), [0x_kaize](2026-07-04-0xkaize-loop-engineering-prompting-to-looping.md), [0xChaseTM](2026-07-08-0xchasetm-build-your-own-loop-boris-method.md), [sairahul "New AI Stack"](2026-07-07-sairahul-new-ai-stack-harness-layers.md)). Every mechanic here already has a hub home:

| keloneoneal concept | Hub equivalent |
|---|---|
| Readiness Score L0–L3 / `loop-audit` | No direct hub analogue — closest is the trust-score subsystem (`config/trust-score.yml`, `scripts/trust_score.py`), but that scores RUN trustworthiness, not repo readiness-for-looping |
| 6-step cycle (Schedule→Triage→StateSync→Execute→Verify→Gate) | `loop-engineering` plugin's DISCOVER→PLAN→EXECUTE→VERIFY→(SHIP\|FEEDBACK) |
| Maker/Checker split | `agent-team-selection.md` + `independent-test-verification.md` (maker≠checker is already load-bearing hub doctrine) |
| STATE.md / loop-run-log.md | `.remember/` (`remember.md`/`now.md`/`recent.md`) + scratchpad discipline (`context-management.md`) |
| Worktrees | `git-branch-lifecycle` skill (`work` mode) + `superpowers:using-git-worktrees` |
| Path denylists / no auto-edit `.env`,`auth/` | Hub secret-scan gate (`dedup_check.py --secret-scan`) + `auto-git.sh` secret-scan gating |
| Kill switches / budget caps | `loop-engineering` plugin's hard budgets + escalation-report |
| "Verifier Problem" (LLM-as-verifier overfits) | Corroborates existing hub caution already encoded via hard gates in `config/trust-score.yml` (never let a soft weighted average out-vote a safety floor) |

The one mildly distinct idea — a standalone **numeric "Readiness Score" CLI gate** (exit code < 40 fails CI) as a pre-loop-adoption checklist — is a plausible pattern but not a novel mechanism the hub lacks; it would just be a differently-shaped restatement of DoD gating the hub already does per-workflow via `config/workflow-contracts.yaml` gate expressions. Not worth building.

**Verdict: no action.** Genuinely redundant with the existing loop cluster; nothing here clears the bar for a hub pattern, spec update, or new capture-worthy framing. Logged for completeness per the standing capture directive, not because it changes anything.
