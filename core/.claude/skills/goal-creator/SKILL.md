---
name: goal-creator
description: >
  Author a "contract" — a dense, zero-open-questions markdown spec — to hand to
  an autonomous executor (Claude Code's built-in `/goal`, or `/loop`, a routine,
  or headless `claude -p`) that runs unattended until a Definition of Done is met.
  Use when the user wants to CREATE / DRAFT / WRITE a goal, autonomous contract,
  or unattended-run spec — "create a goal to…", "draft a contract for /goal",
  "set up an autonomous run that…". Interview-first: resolve every fork BEFORE
  the run, because an autonomous run never pauses to ask. This skill AUTHORS the
  contract and stops — it never runs the executor and never commits. NOT for
  interactive step-by-step plans (use /writing-plans), executing an existing
  plan (use /executing-plans), or requirements exploration (use /brainstorm).
type: workflow
allowed-tools: "Read Write Edit Grep Glob Bash"
argument-hint: "[one-line description of the goal, optional]"
version: "2.0.0"
triggers:
  - goal creator
  - create a goal
  - goal contract
  - autonomous contract
  - create a goal contract
  - draft a /goal contract
  - goal contract for an unattended run
  - contract for /goal
  - unattended run
  - autonomous run spec
---

# Autonomous Contract — author a zero-input spec for an unattended run

`/goal` is a built-in Claude Code command that runs **autonomously across turns**
until a completion condition is met — with **no mid-run user input**. (`/loop`,
routines, and headless `claude -p` are alternative autonomous runners.) A long
unattended run is only as good as the brief it starts with: **a single
unresolved decision baked into the contract becomes hours of work building the
wrong thing.**

This skill's only job is to **author that contract**. It is interview-first:
front-load every question, resolve every fork, and write a contract in which
literally every decision is pre-made. It does **not** run the executor and does
**not** commit — those are the user's.

**Goal:** $ARGUMENTS

> **Scope guard.** This skill ONLY authors a contract for an *unattended* run.
> If the request is an interactive step-by-step plan → `/writing-plans`;
> executing an existing plan → `/executing-plans`; exploring what to build →
> `/brainstorm`; or it isn't about authoring an autonomous-run contract at all →
> decline and route accordingly. Do not stretch this skill to fit.

## Cardinal rules (read before anything)

1. **Never run the executor.** Author the contract and stop. The user runs
   `/goal` (or their chosen runner) themselves.
2. **Never commit.** Write the file and stop. Committing the contract is the user's call.
3. **Interview-first, always.** Resolve every genuine fork (STEP 2) before
   writing a line. The output must be zero-user-input.
4. **Default to a NEW contract file. NEVER edit a contract that may already be
   running.** An autonomous run loads its contract at launch — editing a live
   contract is useless (the in-flight run never sees the edit) and dangerous (a
   later re-run of the mutated file duplicates finished work). For a change to an
   existing goal, write a SEPARATE delta contract covering only the net-new work.
5. **Every contract is idempotent.** Its first action is the §0.2 preflight (read
   the coverage ledger + code + `git log` → skip done work → build only the delta).

---

## STEP 0: Load context

Ground yourself before interviewing so your recommended answers are real, not guesses.

1. **Read `references/contract-template.md`** (the skeleton you will fill) and
   **`references/baked-in-rules.md`** (the §0.1/§0.2/§0.3 opening blocks + the
   hub-rule pointer table + the failure-budget block you will paste).
2. **If the project already has authored contracts** (`docs/contracts/*.md`),
   skim one to match its house format and density.
3. **Identify the target tree + how the app persists/verifies** — which
   directory/service the run touches, and what signal proves a write landed
   (a DB/API read-back, a localStorage round-trip, a file on disk). The
   contract's persistence-verification gate must match the mode the run exercises.

If the user gave a one-line goal as an argument, seed the interview with it —
don't re-ask what they already told you.

---

## STEP 1: Map the fork inventory

Before asking anything, privately enumerate every decision the contract must pin
down (the "enumerate before you ask" discipline). A complete contract resolves at
minimum:

- **Mission** — the one-paragraph objective. What does "done" look like?
- **Target tree + scope boundary** — which dirs/files are in vs out; which boundary contracts apply.
- **Goal type** — fresh build, propagation/refactor, bug-fix loop, migration, audit.
- **Context-to-read-first** — exact files/modules the run must study, with import paths and gotchas.
- **Pre-made design decisions** — every fork the run must NOT pause on (the bulk of a build interview). Each is a decision, not a menu.
- **Stage breakdown** — how the work splits into stages, and per-stage acceptance.
- **Verification gates** — static gates (type-check/test/build) + the baked-in verification rules adapted to the tree (see `references/baked-in-rules.md`), gated by blast radius.
- **Failure-recovery budgets** — per-task fix budget, tool-hang recovery, hard-halt list.
- **Commit + push policy** — commit granularity, message format, branch, push target, what NOT to stage.
- **Definition of Done** — the checkbox list that gates completion. **DoD verbs are load-bearing** (`core/.claude/rules/dod-verbs.md`): an autonomous run satisfies the LITERAL checkbox and stops. State the ACTION + the COMPLETENESS BAR explicitly — "**report** X" yields a report, not closed gaps; "every layer **represented**" yields one example, not the exhaustive matrix. Never write "each X" when you mean "a representative X".
- **Final report** — what the closing report must contain.
- **Guardrails** — hard stops (no new deps, no design reinvention, no fabricated data).

Answer what you can by reading the codebase (STEP 0) — don't ask those. Only the
genuine forks go to the interview.

---

## STEP 2: Interview (Clarification Gate)

Grill the user **one genuine fork at a time**, each with an explicit
**recommended answer**, until every fork is resolved.

This interview is the legitimate exception to `core/.claude/rules/decision-authority.md`'s
anti-over-ask rule — because the run is unattended, a wrong assumption costs
hours, so converging on intent up front is correct. But still apply that rule's
discipline: **only genuine forks** (irreversible / materially different valid
builds / no clear best-practice winner). **Decide reversible defaults yourself**
and state them as assumptions to confirm — do not turn decidable defaults into
questions.

- **One question per turn.** Never batch. Wait for the answer before the next.
- **Always recommend.** "Should X be A or B? Recommended: A, because Y." A good recommendation makes the interview fast.
- **Read code before asking.** If the codebase answers it, state the answer as an assumption to confirm.
- **Highest-leverage first.** Ask the fork that constrains the most downstream decisions first (target tree → goal type → mission → scope → design decisions).
- **No padding, no early stop.** Keep going until confident; stop when confident. Don't invent questions to hit a count.
- **Track the authorization trail.** Note each resolved decision; the contract records it (template's "Authorization trail" table) so the run — and the user later — can see what was decided and why.

When the tree is resolved, **summarize the resolved decisions back as a final
checkpoint** and get a go-ahead before writing. If new forks surface mid-write,
return here — never paper over a gap with a guess.

---

## STEP 3: Confirm the output path

**In-flight check (cardinal rule 4) first.** If this work extends or overlaps an
existing contract, determine whether that contract is running or has run (ask, or
infer from a parallel session / matching commits in `git log`):
- **Running / has run → author a SEPARATE delta file.** Do NOT edit in place. The delta covers only net-new work and relies on the §0.2 preflight to skip what's done.
- Edit an existing contract in place ONLY when the user confirms it has never run and is not running.

Then derive a kebab-case slug and propose the path (get the date with `date +%Y-%m-%d`):

```
docs/contracts/YYYY-MM-DD-<kebab-slug>.md      # delta: <base-slug>-delta.md
```

Confirm the exact path — a one-line confirmation, not a question round.

---

## STEP 4: Write the contract

Fill `references/contract-template.md` with the resolved decisions. **Paste the
§0.1 (worktree isolation + lock), §0.2 (idempotency preflight), §0.3 (live
progress log) blocks as the contract's opening three sections**, then paste the
**baked-in-rules pointer block** from `references/baked-in-rules.md`, adapting
only the tree-specific mechanics (the right static-gate commands, ports/paths,
and the persistence-verification signal). Adapt the *mechanics*; keep the *mandate*.
Name the progress log `docs/contracts/.run/<slug>-PROGRESS.md`.

Quality bar (this is what separates a good contract from a vague one):

- **Zero open questions.** Every fork is a stated decision. If you wrote "decide whether to…", you failed — go decide (re-interview if it's a genuine fork).
- **Concrete, not abstract.** Real file paths, real module/import names, real commands with the right working directory. Naming each component + its import + its props is strong; "use the shared components" is weak.
- **Verification is load-bearing, not decorative.** The baked-in rules appear as MANDATORY per-stage gates with explicit pass criteria and the exact tool calls — gated by blast radius of the changed surface (the conditional-gating table in `references/baked-in-rules.md`), not a hand-wave.
- **Provision the env for every mandated check.** Don't mandate a check the run's own environment can't reach (e.g. an auth-OFF test inside an auth-ON sweep) — give it its own sub-run with its own setup, and mark security/data-integrity gates non-deferrable.
- **"Tested via the UI" means hand-entry through the real forms, not a seed/fixture load.** A seed proves *render*, not *entry* — never let it satisfy a build/journey requirement.
- **Honest defaults.** No synthetic/fake data; surface uncertainty as an explicit `**Assumption:** X`, never as fiction.
- **Self-contained.** The run should not need this skill or any chat history — everything is in the contract plus the rule files it names (which load transitively). List those references explicitly — and **verify every cited file exists at drafting time** (`ls` each referenced path, especially cross-repo ones and style-reference files). A stale citation forces the executor to improvise mid-run; the contract MUST instead either cite a real file or state the fallback ("if X is absent, use Y").

Length here buys an unattended run that builds the right thing — be dense on purpose.

---

## STEP 4.5: Self-validate (mechanical zero-open-questions gate)

The whole promise is a **zero-user-input** contract. A residual fork or
un-pasted block is a defect that becomes an hours-long wrong run. Before handoff,
mechanically check the file you wrote:

```bash
# 1) No unresolved forks / placeholders:
grep -nE '<[a-z _-]+>|[Dd]ecide whether|[Cc]hoose (between|whether)|\bTBD\b|TODO\(decide\)|\?\?\?|PASTE' docs/contracts/<file>.md
# 2) The opening blocks (§0.1/§0.2/§0.3) and verification gates were actually pasted (not left as markers):
grep -nE '§0\.1|§0\.2|§0\.3' docs/contracts/<file>.md   # expect the three real sections, no "← PASTE …"
```

Grep #1 MUST come back clean (the only tolerated hits are literals inside a
quoted code sample — eyeball them). Any `decide whether…` / `TBD` / surviving
`<…>` placeholder / leftover `PASTE` marker is a BUG: resolve it (re-interview if
a genuine fork — STEP 2) and re-run. Do not hand off a contract that fails this gate.

---

## STEP 5: Stop — hand off, don't execute

Print, then stop:

1. The path you wrote, e.g. `docs/contracts/2026-06-10-<slug>.md`.
2. The ready-to-paste invocation line for the chosen executor:
   ```
   /goal docs/contracts/2026-06-10-<slug>.md
   ```
   (or the user's `/loop` / routine / headless equivalent).
   For UNATTENDED / headless runs, launch the executor in **Auto mode**
   (`claude --permission-mode auto -p …`, or start the session in Auto mode) per the
   ratified S7 policy in `decision-authority.md` — the harness then deterministically
   hard-denies the irreversible class when no human is watching. Interactive runs are
   unchanged.
3. A one-line note: the contract is written but **not committed** (committing is
   theirs to trigger), and **they run the executor** when ready.

Do **not** run `/goal`. Do **not** `git add` / `git commit`. Do **not** start
building. The deliverable is the contract file and the invocation line — nothing more.

---

## Mode B: Fold run learnings back (post-run self-improvement)

STEP 0–5 is **Mode A — author a contract**. **Mode B folds a COMPLETED run's
learnings back** so the same mistake isn't repeated. Use it when a run has
finished, or offer it at the end of a session where a run just completed. NEVER
mid-run (cardinal rule 4 — the in-flight run already loaded its contract).

1. **Read the run's learnings** — its `docs/contracts/.run/<slug>-PROGRESS.md` (defects, "X not working + what I did" events, decisions, recoveries) and the committed final report's "LEARNINGS TO FOLD BACK" section.
2. **Classify + route each learning per `core/.claude/rules/learnings-routing.md`** — GENERIC (process/tooling) → a skill or process rule; PRODUCT-SPECIFIC → a product rule (if a recurring class) or the contract itself. Prefer a deterministic gate over prose. One canonical home; dedup before adding.
3. **PROPOSE, then apply on approval.** Skill/rule/contract edits are governance edits (`claude-behavior.md` rule 5) → show the diffs and apply only on go-ahead. A one-line lessons-log entry is the only auto-write.
4. **Honor cardinal rule 4** — if the target contract may be re-run, generalize or write a delta; don't edit it in place.

---

## CRITICAL RULES

- **NEVER run the executor and NEVER commit.** Author the contract, print the invocation line, stop.
- **NEVER edit a contract that may be running — default to a new delta file.** Editing a live contract is ineffective and causes duplication on re-run.
- **Interview-first, one genuine fork at a time, each with a recommended answer**, until every fork is resolved — but decide reversible defaults yourself (`decision-authority.md`); do not over-ask. The contract must be zero-user-input.
- **Every contract opens with §0.1 (worktree isolation + lock — see `git-worktrees`), §0.2 (idempotency preflight), §0.3 (live cross-session progress log)** from `references/baked-in-rules.md`.
- **Bake in the verification rules as POINTERS, gated by blast radius** (`references/baked-in-rules.md`): `supervisor-verification`, `independent-test-verification`, `output-plausibility-verification`, `e2e-persistence-verification`, `dod-verbs`, `bug-triage-discipline`, plus `testing.md` / `e2e-best-practices` for placement. Adapt mechanics, keep the mandate; never inline-duplicate the rule text (`configuration-ssot.md`).
- **DoD verbs are load-bearing** (`dod-verbs.md`) — state ACTION + COMPLETENESS BAR; an autonomous run satisfies the weakest literal reading.
- **Pass the STEP 4.5 zero-open-questions gate** before handoff — "decide whether to…" in a finished contract is a bug.
- **Mode B only PROPOSES rule/skill/contract edits** for approval (`claude-behavior.md` rule 5); route learnings per `learnings-routing.md`.
