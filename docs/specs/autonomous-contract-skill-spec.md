# Spec: `autonomous-contract` skill

**Status:** DRAFT (brainstorm output) · **Date:** 2026-06-10 · **Tier 4** of `plans/hub-promotion-firekaro.md`
**Source:** generalized from firekaro-planner `goal-creator` (v1.5.2)

## 1. Problem statement

Claude Code ships `/goal` — a built-in command that runs **autonomously across
turns** until a completion condition is met, with no mid-run user input. A long
unattended run is only as good as the brief it starts with: a single unresolved
decision baked into that brief becomes hours of work building the wrong thing.

The hub has no skill for **authoring** that brief. `writing-plans` produces an
interactive, commit-per-task plan executed step-by-step with a human in the
loop; `executing-plans` runs such a plan with review checkpoints. Neither
targets the distinct genre: a **single self-contained, zero-open-questions
contract** handed to an autonomous executor that will not pause to ask.

## 2. Chosen approach

A **new standalone skill** `autonomous-contract` (not a `writing-plans` mode —
the genre, interview discipline, and "zero mid-run input" invariant are
materially different). It is an **authoring** skill: it interviews to resolve
every fork, writes a contract to `docs/contracts/`, and stops. It never runs
the contract and never commits — execution and commit are the user's.

The skill **anchors on the real built-in `/goal`** as the canonical executor
(verified built-in, [docs](https://code.claude.com/docs/en/goal.md)), and names
`/loop`, routines, and headless (`claude -p`) as alternative autonomous runners.

**Full apparatus ported** (de-firekaro'd, generalized):
- Interview-first authoring with a **mechanical zero-open-questions gate**
- **Idempotency preflight** (read a coverage ledger + code + `git log` → skip done → build only the delta)
- **Worktree + lock + commit-gate isolation** for the background run
- **Cross-session progress log** (append-only, gitignored, readable via `git worktree list`)
- **DONE / PENDING / BLOCKED / NEXT** run-end summary
- **DoD-verb precision** (ACTION + COMPLETENESS BAR)
- **Blast-radius verification gating** baked into every contract

### Why baked-in rules are POINTERS, not inlined text (Claude-Code-expert call)

The firekaro source inlined rule 24/25/26/… text into every contract. In the
hub that would duplicate content and risk drift, violating `configuration-ssot`.
Decision: **hybrid — point to the hub rule by name + a one-line gist of what it
gates.** Global rules auto-load into the executor's session transitively, so a
pointer is sufficient *and* SSOT-compliant; the one-line gist gives the contract
reader the intent without opening every file. The firekaro Rules map cleanly:

| firekaro rule | hub rule (pointer target) |
|---|---|
| 24 UI screenshot verification | `supervisor-verification` (drive-the-UI loop) |
| 25 UI→persistence | `e2e-persistence-verification` |
| 26 post-phase independent + cross-page sweep | `supervisor-verification` + `independent-test-verification` |
| 29 independent implementation review | `supervisor-verification` (independent reviewer) |
| 31 output plausibility | `output-plausibility-verification` |
| 32 interactive functionality | `e2e-best-practices` (drive + interact) |
| 33 blind independent test verification | `independent-test-verification` |
| 15/17/20/23 | `claude-behavior.md` (same rule numbers exist in hub) |
| §0.1 worktree isolation + lock + commit-gate | `git-worktrees` (background-run isolation, Tier 2) |
| DoD verbs | `dod-verbs` (Tier 2) |
| test placement | `testing.md` + `e2e-best-practices` |
| bug miss-analysis + sibling audit | `bug-triage-discipline` (Tier 1) |

## 3. Design sections

### SKILL.md (`type: workflow`, `allowed-tools: "Read Write Edit Grep Glob Bash"`)
- Cardinal rules preamble: never run `/goal`; never commit; interview-first; default to a NEW contract file (never edit a possibly-running one); every contract is idempotent.
- **STEP 0 Load context** — read `references/contract-template.md` + `references/baked-in-rules.md`; identify the target tree + persistence/verification mode.
- **STEP 1 Map the fork inventory** — privately enumerate every decision the contract must pin (mission, scope boundary, goal type, context-to-read, pre-made design decisions, stage breakdown, verification gates, failure budgets, commit policy, DoD, final report, guardrails).
- **STEP 2 Interview (Clarification Gate)** — one genuine fork at a time, each with a recommended answer; **scoped by `decision-authority`** (grill only genuine forks, decide reversible defaults — do NOT over-ask). Read code before asking.
- **STEP 3 Confirm output path** — in-flight check (new delta vs edit-in-place); slug → `docs/contracts/YYYY-MM-DD-<slug>.md`.
- **STEP 4 Write the contract** from the template: paste the §0.1/§0.2/§0.3 opening blocks + the baked-in-rules pointer block (adapt mechanics, keep the mandate); concrete paths/commands, zero abstractions.
- **STEP 4.5 Zero-open-questions gate** — mechanical grep for placeholders/forks/un-pasted markers; must come back clean before handoff.
- **STEP 5 Hand off, don't execute** — print the path + the `/goal docs/contracts/<file>.md` invocation line + the "not committed; you run it" note. Stop.
- **Mode B Fold-back** — after a completed run, classify learnings (GENERIC vs PRODUCT-SPECIFIC per `learnings-routing`), PROPOSE rule/skill edits (never auto-apply — `claude-behavior` rule 5).
- **CRITICAL RULES** section.

### references/
- `contract-template.md` — the portable skeleton (generalized from firekaro's; neutral example resources, `docs/contracts/.run/<slug>-PROGRESS.md` progress path).
- `baked-in-rules.md` — the §0.1/§0.2/§0.3 opening blocks + the hub-rule pointer+gist table + the blast-radius conditional-gating table + the failure-recovery budget block.
- `example-contract.md` — one short worked example (a neutral build contract) so the format is concrete.

### Provisioning / registry
- New skill registry entry (`type: skill`, `category: core` or `need-basis`?, `tier`). Universal authoring skill → **core / nice-to-have** (like `writing-plans` is must-have, but this is a more specialized genre → nice-to-have is defensible; decide at author time by comparing to `writing-plans`/`executing-plans` tiers).
- changelog + `_meta.total_patterns` bump (the Tier-1/2 lesson).

## 4. Requirement tiers (MoSCoW)

**Must:** new standalone SKILL.md with STEP 0–5 + Mode B; `references/contract-template.md` + `references/baked-in-rules.md`; executor-anchored on `/goal` with alternatives; baked-in-rules as hub-rule pointers+gist; zero-open-questions mechanical gate; `docs/contracts/` convention; registry+changelog+`_meta`; passes all validators + full pytest; `/skill-evaluator` before merge.

**Nice:** `references/example-contract.md` worked example; a `triggers:` list tuned for "create a goal / autonomous contract / unattended run"; cross-link from `writing-plans` STEP 7 (when to use autonomous-contract vs executing-plans).

**Out of scope:** building any executor; a deterministic run-completion gate/hook (firekaro tracks this as a candidate — note it, don't build it); editing `/goal` itself; firekaro domain content.

## 5. Open questions
- Skill tier: `nice-to-have` vs `must-have` (resolve by comparing to `writing-plans`/`executing-plans` registry tiers at author time).
- Does the skill need a `Bash`-driven date/grep helper inline, or keep those as documented commands? (Lean: documented commands, matching `writing-plans`.)

## 6. Success criteria
- A user can run `/autonomous-contract`, answer only genuine forks, and get a `docs/contracts/<slug>.md` that `/goal` can execute with zero mid-run questions.
- The contract's verification section points to the hub rules (no inlined duplication) and the executor loads them transitively.
- `/skill-evaluator full` passes (trigger reliability, output quality, no conflicts with `writing-plans`/`executing-plans`/`brainstorm`).
- All hub validators + full `pytest scripts/tests/` green; registry `_meta` synced.

## Next step
Author the skill via `/writing-skills` (SKILL.md + references), then `/skill-evaluator` before the Tier-4 PR.
