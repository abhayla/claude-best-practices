# Baked-in rules block (paste into every contract)

These are the standing blocks every autonomous contract carries. Paste the three
opening blocks (§0.1–§0.3) as the contract's first sections, then paste the
verification pointer block into its "Verification gates" section, adapting **only
the mechanics** to the target tree. Keep the mandate intact — the reason these
contracts produce *proven-working* output (not *claimed-working*) is that the
verification gates are non-negotiable, not advisory prose.

The verification rules below live in `core/.claude/rules/`. The contract names
them so they load transitively into the run's session — **point to them, do not
copy their text** (`configuration-ssot.md`: one canonical home, no duplication).

## Contents

- §0.1 Worktree isolation (paste FIRST)
- §0.2 Idempotency preflight (paste second)
- §0.3 Progress log (paste third)
- Verification gates — POINTER block (paste into the contract's gates section)
- Failure-recovery budget block
- Persistence-verification mechanics

---

## §0.1 Worktree isolation — run in a DEDICATED worktree, claim it with a lock (paste FIRST)

Paste as the contract's very first action. It prevents a background autonomous
run from colliding with the user's interactive session (switching their branch
mid-session, landing stray commits). Full mechanism: `core/.claude/skills/git-worktrees`
("Background Autonomous-Run Isolation").

> **First action of the run, before §0.2 and any stage. Non-negotiable.** This run MUST execute
> in a **dedicated git worktree**, never the user's primary interactive checkout.
>
> 1. **Isolate:** `root=$(git rev-parse --show-toplevel)`. If `root` is the user's primary
>    checkout (not an already-dedicated run worktree), create and switch to one before any
>    stage: `git worktree add ../<repo>-run-<slug> -b <feature-branch>` and run every stage there.
> 2. **Claim it:** export a unique `RUN_TOKEN` (e.g. `<branch>-<nonce>`) and write the lock:
>    `printf '%s\n' "$RUN_TOKEN" > "$(git rev-parse --show-toplevel)/.run-active.lock"`. A
>    `pre-commit` hook HARD-BLOCKS any commit whose `RUN_TOKEN` does not match the lock, so a
>    concurrent interactive session physically cannot commit into this run's worktree.
> 3. **Release on exit:** the run's FINAL action (after merge/push, OR on any halt/defer) removes
>    the lock: `rm -f "$(git rev-parse --show-toplevel)/.run-active.lock"`. `.run-active.lock` is gitignored.
> 4. **Self-clean ON SUCCESS ONLY:** after the branch is merged + pushed + the lock released, `cd`
>    to the primary repo root and `git worktree remove --force ../<repo>-run-<slug> ; git branch -D
>    <feature-branch> ; git worktree prune`. On DEFER/HALT, do NOT remove the worktree or branch —
>    they are needed to resume (only the lock is released).

---

## §0.2 Preflight — read the coverage ledger FIRST (idempotency · no duplication)

Paste as the contract's first numbered section. It makes the contract safe to run
at any time, even while a parallel session implements part of it.

> **First action after §0.1, before ANY stage. Non-negotiable.** A parallel session may already
> have implemented part of this contract. This contract must be **safe to run at any time without
> redoing finished work.**
>
> 1. **Read the project's coverage/gap ledger** — the doc tracking COVERED vs DEFERRED (name it
>    explicitly in the contract, e.g. `docs/<gap-ledger>.md`). It is the single source of truth for
>    what is already done across all sessions. (If the project has no ledger, fall back to code + `git log`.)
> 2. **For every item, check the ledger + the actual code + `git log` before building it.** If it's
>    COVERED or the code already implements it (grep/read to confirm — don't trust the ledger blindly),
>    SKIP the build, do a verify-only pass, move on. If partially done, build only the missing delta.
> 3. **Record every skip** in the final report's "skipped (already covered)" list.

---

## §0.3 Progress Log — live, cross-session-trackable + a learning trail (paste THIRD)

Paste as the contract's third opening section. A long autonomous run is otherwise
a black box to every other session.

> **Maintain an append-only progress log for the entire run. Update it BEFORE moving on from each
> stage/event** — so a crash or context-out leaves it current.
>
> 1. **Location:** `docs/contracts/.run/<slug>-PROGRESS.md` (in THIS run's worktree). `.run/` is
>    gitignored → no commit churn, no cross-run conflicts. Read cross-session via `git worktree list`
>    → read each worktree's `docs/contracts/.run/*-PROGRESS.md`.
> 2. **First line:** slug · branch · worktree · start time · contract path · one-line mission.
> 3. **Append a SHORT entry (≤2 lines) at:** stage start; stage done (with gate result); every major
>    defect; every "something not working" event **+ what you did about it**; each independent-review
>    outcome; each defer/skip; each blocker/halt; the final result. Terse heartbeat + learning trail, not a transcript.
> 4. **Entry format:** `[YYYY-MM-DD HH:MM] <STAGE|PROGRESS|DEFECT|EVENT|DECISION|RECOVERY|BLOCKER|DONE> — <≤2-line summary>`.
> 5. **At run-end, derive learnings and route them per `core/.claude/rules/learnings-routing.md`**
>    (GENERIC → skill/process rule; PRODUCT-SPECIFIC → product rule or this contract; prefer a gate
>    over prose; one canonical home, dedup). Auto-write only the one-line lessons-log entry; everything
>    else is PROPOSE-only for the user's approval (`claude-behavior.md` rule 5).
> 6. **Run-end SUMMARY** (in the final PROGRESS entry AND the committed final report): **DONE**
>    (verified-green stages) · **PENDING** (the deferred entries + one-line reason — no silent skips) ·
>    **BLOCKED** (the approval-gated subset + why) · **NEXT** (the single next action + who owns it).

---

## Verification gates — POINTER block (paste into the contract's "Verification gates" section)

Carry this block verbatim, then adapt only the mechanics (the static-gate commands, the
persistence-verification signal, the screens/routes named). Each gate is a MANDATORY per-stage
check, not advisory prose. Full rule text lives at the named path and loads transitively.

> **All global rules in `.claude/rules/` are operative for this run.** The verification gates below
> are the load-bearing ones for an unattended run. **Test by BLAST RADIUS of the changed surface** —
> full depth in every layer the change touches, not "all types always" and not "render-only". Test
> *placement* (which type runs in which environment) follows `core/.claude/rules/testing.md` +
> `core/.claude/rules/e2e-best-practices.md`.

| Gate | Hub rule (loads transitively) | What it gates | Fires when |
|---|---|---|---|
| **Supervisor verification** | `supervisor-verification.md` | Reproduce the claimed gate + inspect output substance; for UI, drive the running app (screenshot + ARIA + console + interact), don't accept code-inspection | every dispatched-worker output; UI rows when the diff touches UI |
| **Blind test verification** | `independent-test-verification.md` | Any test verdict re-checked by a SEPARATE context-blind agent given the same inputs + raw evidence | whenever any test verdict is produced (non-skippable) |
| **Output plausibility** | `output-plausibility-verification.md` | Computed user-facing values are domain-SANE on the DEFAULT path, not just green | the diff reaches a user-facing/computed value |
| **Persistence verification** | `e2e-persistence-verification.md` | A create/update/delete actually persisted (per-iteration in loops; reload + assert) — a closed dialog is not a saved row | the diff introduces a UI write path |
| **Bug-triage discipline** | `bug-triage-discipline.md` | A fixed bug carries a "why was this missed?" + repo-wide sibling-class audit before close | any bug-fix stage |
| **DoD verbs** | `dod-verbs.md` | Every DoD criterion states ACTION + COMPLETENESS BAR | the DoD is authored (in this skill's STEP 1/4) |
| **Static gates** | project-specific | type-check + lint + unit tests green for every tree the change touches | every code stage |

**Evidence-handoff note:** browser-automation tools may write screenshots to the *session/primary*
worktree, not the run's worktree. Before handing evidence paths to the blind verifier, copy or
absolute-path the artifacts INTO the run worktree's evidence dir and `ls`-confirm each exists — a
missing-path dissent is not a real defect, just a wasted reconciliation cycle.

---

## Failure-recovery budget block (carry forward; tune the numbers per goal)

- **Per-task fix budget:** ~15 attempts (≈5 inline → `/fix-loop` → `/systematic-debugging`) → then DEFER the task and continue; do NOT halt the whole run.
- **Tool-hang recovery (browser/MCP):** 3 cycles — (1) wait + retry; (2) close + re-open the tool; (3) kill + restart the background dev server (captured PID) + retry. All 3 fail → log DEFERRED + mark `completed (deferred)` + continue.
- **Hard halt conditions ONLY:** dependency install failure; a decision contradiction inside the contract; an irrecoverable build break after the full fix budget; an OS permission denial; a missing required credential. **Context-budget anxiety is NOT a halt** — hand off via a one-line continuation note, never fake-complete.

---

## Persistence-verification mechanics (adapt the signal to how the app persists)

The `e2e-persistence-verification` gate needs a real persistence signal — pick the one matching the
mode the run exercises and name it concretely in the contract:

| Persistence mode | Persistence signal |
|---|---|
| Server/API + database | independent API read-back (`curl`/HTTP GET the just-written resource); wait out any write debounce first |
| Client-only (localStorage/IndexedDB) | round-trip read of the storage key via the browser-automation eval |
| File/disk | re-read the written file and assert its contents |

A dialog close, a toast, or an optimistic UI update is **not** a persistence signal.
