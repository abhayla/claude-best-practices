---
name: get-work-done
description: Central work dispatcher ("mother hub" front door) for the GetWorkDone fleet. EVERY task gets a contract + T-id; owner-present tasks run in-session in a worktree of the target repo (default), else a background worker on the cheapest-correct model lands via CI-gated PR (v0.10). Grills to >95% confidence at intake, one question per turn. Use for "/get-work-done fix X in IPODhan", intake mode, status, or "cancel T-042". SSOT: plans/get-work-done-dispatcher.md.
---

# /get-work-done - central work dispatcher (v0.10, 2026-08-27)

**v0.10 = procedure only.** Incident narratives live VERBATIM in `references/incident-log.md`
(`I-01 ... I-37`); a rule's `[log: I-nn]` cites the WHY, never a step to run. `references/` also
holds the fast-lane runbook + routing table. **GWD** = this machine's state root
(`GWD/settings.json` -> `fleet_home`): `D:/Abhay/GetWorkDone/` here, `C:/Abhay/GetWorkDone` on
the VPS. Contract format = the goal-creator shape (`plugins/loop-engineering/skills/goal-creator/SKILL.md`) + STEP 5 fields.

## Mode router

| Invocation | Mode |
|---|---|
| `/get-work-done <task>` | INTAKE (steps 1-7) |
| `/get-work-done intake` | Standing intake loop: next task, steps 1-6, return to "ready" IMMEDIATELY. A fast-lane task (STEP 3) session-executes after queueing; else dispatches. Never freelances outside a T-id |
| `/get-work-done status` | Fleet state from `GWD/queue/` + `GWD/heartbeats/` + LEDGER tail, plus host pressure (commit % + live workers via `preflight-guard.ps1 -HostMemoryStatus`); re-rendered every 15 min while live [log: I-22] |
| `/get-work-done cancel <T-id>` | Read `GWD/heartbeats/<id>.hb` -> kill PID tree; rename `<id>.cancelled.md` with a reason; `gh pr close --delete-branch` any PR it opened; ledger it. `cancel all` = all claimed |
| `/get-work-done sweep` | Promote/reject `GWD/inbox/` per the P17 table, run INTAKE 4-7 on promoted items, then claim + dispatch unclaimed `*.queued.md`. DISPATCH-FIRST: claiming is every tick's first duty, never satisfied by watching claimed tasks |

## SCOPE (owner 2026-08-27)

Owner-present work runs IN-SESSION: a worktree of the target repo, T-id + contract still
required, Opus/Sonnet `Agent` implements, a fresh Opus reviews, Fable lands. `/get-work-done`
is ONLY for unattended/hands-off app-repo work - overnight, VPS batches, clear-spec app tasks
the owner is not watching. Fleet-core (bus scripts, this skill/tests) is FROZEN - never a fleet
worker, in-session only when an app task is blocked. Weekly measure app vs fleet landed
(`fleet-ratio.py` on the bus); under ~2:1 by 2026-09-10 -> GWD becomes a thin launcher. Every
task keeps its T-id + contract + LEDGER line + registry flips regardless of mode.

## Prerequisites

`git`, an authenticated `gh` (PR/label/merge-state calls), `python` and PowerShell on PATH, a
writable bus checkout at `GWD` (queue, heartbeats, settings.json, guard scripts). Fast-lane also
needs `GWD/fast-lane-gate.py` + `GWD/fast-lane-check.py`.

## STEP 0: Preflight

Verify every prerequisite NOW, report ALL missing items in one stop - never discover a missing
tool mid-run, never improvise a fallback (an unreachable bus means no T-id, no safe degraded
mode).

## STEP 1 - INTAKE: parse the ask

Split the input into tasks (may span repos). Resolve each target against `GWD/settings.json` ->
`repo_registry` - the ONLY source of repo paths [log: I-04]. A repo not in the registry, or
ambiguous, is an intake question, never a guess.

**PORTFOLIO REGISTRATION GATE** [log: I-04]: also check the target against `PORTFOLIO.yml` on
5wealths `main`. A repo absent from it, or a task creating a NEW project folder, cannot queue
until a registration row (name, pillar, machines) exists. Carry it into STEP 4; never skip it
silently.

## STEP 2 - SCOUT (~1 min per task)

In the target repo: `git remote get-url origin` (must equal the registry's `remote` - a mismatch
aborts intake with a question), branch state, does the named area exist, do tests exist, which
paths the task will touch. Ground the gate in looked-at reality, never the prompt alone.

## STEP 3 - GATE: every task gets a contract + T-id; SIZE picks the lane

**A get-work-done task with no T-id is a defect** [log: I-01]. Every task is contracted (STEP 5),
then FAST-LANED or DISPATCHED (STEP 6); old carve-outs are subsumed by those two paths. Blast
radius (auth, payments, config, migrations, deploy) informs model tier, budget, `deploy_tier`
and lane eligibility.

**Repo identity is by REGISTRY KEY, never path or folder name:** resolve cwd and target via
`git remote get-url origin` -> key; no key is foreign, same-key tasks still get their own
worktree. An artifact whose source of truth lives elsewhere (template copy, map cards, Deluge
specs) resolves its repo by `ssot_artifacts`; the session relays owner approvals, never authors
the text.

### FAST LANE (owner decision A [log: I-01]; DEFAULT when the owner is present, per SCOPE)

Session-executed under a T-id in a worktree of the TARGET repo, with `context_docs` and a
checker - the DEFAULT whenever the owner is present; STEP 6's background worker is the
unattended path.

**ELIGIBILITY** = ALL of: `deliverable: content|mechanical` * <=5 files in `files:` * <=300
changed lines at PR time * no path matching the sensitive-path denylist in
`GWD/fast-lane-gate.py` * no unknowns after scout. `code` is NOT eligible in v1; revisit after
10 clean runs.

**FLOW:** gate -> stage-stamp -> worktree edit -> PR -> diff gate -> `fast-lane-check.py` -> merge
on green -> LEDGER line, detailed in `references/fast-lane-runbook.md`. SLO <=20 min
launched->merged (`settings.fast_lane_slo_minutes`), a miss = `FAST-LANE-SLO-MISS` via
`lesson.py status`. A `lane: fast` contract at WORKER dispatch is preflight exit 14.

## STEP 3.5 - ROOT-CAUSE GATE: the SECOND occurrence fixes the MECHANISM

[log: I-02] - eight workers died at their turn cap; the fix was always a firmer prose mandate,
and it failed every time.

A first occurrence may be fixed as an instance. From the SECOND occurrence of the same failure SHAPE
(same symptom class, not the same file or repo) an instance fix alone is NOT acceptable on its own -
fix the MECHANISM that permits it or record in `status_log`, with the reason, why a mechanism fix is
impossible - silence is not an exemption.
**PROSE IS NOT A MECHANISM**: a mechanism is CODE, a GUARD, a HOOK, a SCHEMA CONSTRAINT or a TEST
THAT FAILS when the defect returns - the eight-times-failed prose mandate is why. Before
calling it done, SWEEP the repo (and the estate, where the shape travels) and REPORT the count - "fixed 1 of N found" / "swept, no other instances" - and
append a `LESSON(CODIFIED -> <where>)` line to `GWD/PATTERNS-SEEN.md` plus a row in
`GWD/MECHANISM-DUE.md` (`python GWD/lesson.py`); the learning-debt gate (exit 11) reads it.

## STEP 4 - CLARIFY: resolve everything at intake, one question per turn

**NON-SKIPPABLE** - "run it" / "go ahead" means PROCEED, not skip [log: I-03]. (a) **DETERMINE,
don't ask** anything you can scout ("compare IPODhan's data" -> the app's OWN DB/API, not its
public site); asking what you can determine is itself a defect. (b) For a GENUINE material unknown
(2+ valid answers changing the OUTCOME, unscoutable) -> the 95%-gate: **ONE question per turn**,
`*Sync-check:*` opener, **recommended answer + one-line justification**, until confidence exceeds
95%. "Decide-don't-ask" governs reversible EXECUTION detail only.

**FAIL AT INTAKE, NOT AT MIDNIGHT:** run every abort-capable check now - registry/remote identity,
branch protection + secret-scan gate (`gh api`), credentials/tools present, deploy tier, and the
permission surface (any unattended worker/checker on a no-prompt path, verified now - never
discovered mid-run with the owner away).

| Deploy situation | Tier |
|---|---|
| Re-deploy of a live app, same domain/infra | AUTO (Tier 1) - no question |
| New app onto the owner-granted sandbox domain (`settings.json` `_sandbox_note`) | AUTO (Tier 1) - pre-authorized |
| First deploy / DNS / new domain / auth or payment surface | HOLD (Tier 2) - collect the yes/no NOW |

A portfolio-registration flag from STEP 1 IS a material unknown - resolve it here; determine the
pillar yourself when knowable. AUTO-tier deploys run via `GWD/deploy-site.sh`: capture
KNOWN-GOOD -> niced build -> swap -> `nginx -t` gate -> probe live URL -> restore known-good on
failure [log: I-05]. Nothing answerable from GLOBAL.md, the repo, or the registry may be asked.

## STEP 5 - CONTRACT

Build the goal-creator contract from the task + answers, add the dispatcher fields, write it via
`bus-write.ps1` to `GWD/queue/T-<nnn>-<slug>.queued.md` (T-384, the one bus write path). Each rule
below is normative in CRITICAL RULES; full v0.9 text + incident at [log: I-06 ... I-14].

1. **T-ID** [log: I-06]: `git pull` the bus -> `python GWD/next-task-id.py <GWD>` -> on a
   non-fast-forward push rejection, pull and RE-RUN the allocator. Never invent an id; never
   reuse one seen historically.
2. **DEDUP** [log: I-07]: read EVERY open contract in `GWD/queue/` for the same repo. Duplicate ->
   don't queue, name the existing T-id. Overlapping -> `related: [T-xxx]`. Supersedes -> rename the
   old one `.superseded-by-T-<new>.md`.
3. **BATCH** [log: I-08]: same-repo trivia from one intake -> ONE contract, one `dod:` item each,
   same `deliverable:` only. **WAVE-CHAIN** [log: I-09]: a wave contract's `related:` names the
   earlier wave T-id it depends on.
4. **CONTEXT DOCS** [log: I-10]: copy `repo_registry.<key>.context_docs` (repo-relative) into the
   contract; prompt opens "Before ANY work, read these files at the repo root: <list>. If any is
   missing, STOP and report it." CLAUDE.md is never listed; the repo wins over a stale doc.
5. **MANDATES**: the three standing mandates live VERBATIM in `GWD/worker-mandates.txt` - never
   hand-copied or paraphrased [log: I-11, I-12, I-14]. The DISPATCHER prepends that file to every
   prompt today; T-372 makes `worker-wrapper.ps1` do it instead (not landed - `grep -c
   worker-mandates GWD/worker-wrapper.ps1` = 0 until it does). Mandate 3 (T-209, PR #580): `[skip ci]`
   matches ANYWHERE in a commit message, headline or body; a REQUIRED check that never reports
   leaves the PR blocked forever, per PRs #577/#579 under T-191. Add the HOLD-LABEL line
   (`gh pr edit <n> --add-label hold`)
   whenever the `dod:` needs the PR to stay open [log: I-13] - not merging is not enough to stop
   this repo's auto-landing hooks.
6. **LANDING BATCH** [log: I-14]: same-repo same-day contracts default to ONE branch/PR/CI-run;
   exceptions are P1 break-fixes, conflicting file scopes, and a checker FAIL on separable hunks.

```yaml
repo: <registry key>            # path + remote resolved from the registry
origin: <session-id>@<machine> <project-dir>   # owns all reporting
related: []                     # T-ids sharing scope in the same repo
context_docs: []                # copied VERBATIM from the registry
model: haiku|sonnet|opus        # + MANDATORY one-line rationale (lint-enforced)
deliverable: code|deploy|content|claude-resource|data|mechanical
lane: normal|fast               # fast needs content|mechanical + files:/checks: (STEP 3)
priority: P1|P2|P3              # dispatcher-assigned - never ask the owner to rank
deploy_tier: none|auto|hold-approved|hold-denied
approvals: [<granted at intake>]
budget: {max_turns: <sized floor, 6.8c>, wall_clock_hours: 4}
evidence: required              # checker-written, never worker-written
dod:                            # CHECKABLE predicates, dod-verbs discipline
  - <ACTION + COMPLETENESS BAR, verifiable by a stranger>
status_log: []
```

`dod:` items state the ACTION **and** the completeness bar ("documents the per-partner pattern
INCLUDING the two fallbacks", not "update the doc") - a worker satisfies the weakest literal
reading, the checker verifies only what is written as a predicate.

**Routing:** haiku = mechanical/classification, sonnet = DEFAULT for any briefed machine-checkable
job, opus = deep design + preemptively all security work, Fable/Mythos = NEVER a worker (exit 4).
Full table: `references/model-routing-table.md`. When torn pick the cheaper tier - escalation
recovers a wrong cheap pick; a wrong expensive one is never detected.

## STEP 6 - DISPATCH: one background worker, guarded

1. **Same-repo scan** [log: I-15]: `git pull` the bus, scan for ANY `*.claimed.*.md` on the same
   registry key from ANY machine; one exists -> do not dispatch unless `related:`-linked with
   declared-disjoint file scopes. Preflight exit 8 is the backstop; keep them in sync.
2. **Atomic claim**: rename `...queued.md` -> `...claimed.<session-id>.md`; failed -> skip.
3. **Contract lint FIRST**: `python GWD/contract-lint.py <claimed contract>` - non-zero -> park
   with its stderr as the reason. Runs before preflight so nothing is cloned for a bad contract.
4. **Preflight gate**:
   `powershell -NoProfile -ExecutionPolicy Bypass -File GWD/preflight-guard.ps1 -ContractPath <c> -RepoPath <workspace> -ExpectedRemote <remote> -TaskId <T-NNN|T-NNNC*|T-NNNF*> -PromptPath GWD/heartbeats/<id>.prompt.txt -MaxTurns <cap>`
   - non-zero BLOCKS; park with the reason. `-TaskId` sizes exit 12's kind (build/checker/fix_round);
   a checker/fix round launches against its PARENT's contract, so omitting it prices as build.
   The script header table is the SSOT:

   | Code | Gate |
   |---|---|
   | exit 0 | OK to dispatch |
   | exit 1 | `-SelfTest` failure only; never from a gate run |
   | exit 2 | contract missing |
   | exit 3 | no `model:` field |
   | exit 4 | model not an allowed worker tier (Fable/Mythos) |
   | exit 5 | workspace path missing |
   | exit 6 | repo identity mismatch |
   | exit 7 | a `context_docs:` entry is absolute or missing from the workspace |
   | exit 8 | same-repo contract already claimed, not `related:` |
   | exit 9 | prompt file references a foreign-machine path |
   | exit 10 | HOST-MEMORY (T-312): commit charge over 75%, or at `settings.fleet.max_concurrent_workers` |
   | exit 11 | LEARNING-DEBT (T-323): `MECHANISM-DUE.md` row occurrences >= 2, not claimed/done, >48h, no `lesson_class:`; malformed FAILS CLOSED |
   | exit 12 | TURN-BUDGET (T-345): `-MaxTurns` under `settings.worker_defaults.max_turns_by_deliverable` |
   | exit 13 | FIX-ROUND PROMPT-LINT (T-336): `T-<n>F*` prompt's first step omits honesty/PR-body/STATUS.md duties |
   | exit 14 | FAST-LANE contract at worker dispatch (T-351): set `lane: normal`, re-lint |
   | exit 15 | KEEPER-LIVENESS (T-363): no reconciler tick on THIS host in 2x `settings.fleet_keeper_tick_minutes` |
   | exit 16 | HOST-MEMORY-UNKNOWN (T-364): commit/worker query returned nothing - fails CLOSED |
   | exit 17 | SETTINGS-READ-FAILURE (T-364): settings.json unreadable/malformed/non-integer - blocks |
   | exit 18 | ROUND-CAP-EXCEEDED (T-367): round suffix over `settings.max_rounds_by_kind` - park QUALITY/SCOPE-SUSPECT |
   | exit 19 | DISPATCH-CEILING (T-369): today's `heartbeats/*.prompt.txt` >= `settings.max_dispatches_per_day` |

5. **Workspace** [log: I-16]: clone FRESH (`git clone --filter=blob:none`) unless one inside
   `settings.workspaces.retention_days` exists AND is clean. Janitor deletes idle workspaces only
   when provably clean; dirty ones escalate.
6. **LAUNCH - the one recipe** [log: I-21]. Write `GWD/heartbeats/T-<id>.prompt.txt` FIRST, then:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File GWD/worker-wrapper.ps1 `
     -TaskId T-<id> -RepoPath <workspace> -Model <tier> -MaxTurns <cap> -StateRoot <GWD>
   ```
   The wrapper passes the prompt as an **argv pointer** (STDIN abandoned - invisible to
   console-less processes), writes `T-<id>.hb` (PID + tick) and the result JSON; the dispatcher,
   not yet the wrapper, prepends `GWD/worker-mandates.txt` to that prompt (T-372). `-StateRoot`
   is MANDATORY off the VPS. A same-repo-as-dispatcher contract orders the worker into its own
   worktree. Workers run tests/builds in the FOREGROUND only, never `run_in_background` (T-393).
7. **Terminal state** [log: I-18]: parse `stop_reason` - a refusal is NOT success. Refusal on
   haiku/sonnet -> reroute to opus (edit `model:`, append `status_log`, re-lint, re-preflight,
   relaunch); on opus -> PARK, no second reroute. Error -> one retry same tier; a 2nd failure:
   environmental -> park, capability/quality -> escalate ONE tier (max one). Keeper deaths are
   environmental: re-queue once, park on the second.
8. **Post-exit PR-state check** [log: I-19]: `gh pr view <PR> --json state,mergedBy,mergedAt` on
   every PR named. Merged inside the run window = a task FAILURE line in `status_log` +
   `GWD/LEDGER.md` + an owner card.
9. **Lanes + ceilings** [log: I-20]: up to `settings.fleet.max_concurrent_workers` concurrently
   (exit 10 enforces it); same-repo serializes, others parallel; P1 > P2 > P3, a P1 always
   admitted; reprioritize by REORDERING only, never preempting. `settings.max_dispatches_per_day`
   + `settings.daily_token_ceiling` -> pause + ping once, never retry-storm.
   `GWD/state/ci-hold.flag` => only P1 proceeds.
10. **Queue ack + watcher, same turn as the launch** [log: I-22]. Ack: render T-id, repo, tier,
   priority, budget, one-line DoD on screen in the origin session. Watcher: a `Monitor`
   until-loop (or sized `ScheduleWakeup`) breaking on **every** terminal state - a NON-EMPTY
   result JSON (the wrapper pre-creates it at 0 bytes), an `EXITED` heartbeat, or one older than
   `settings.heartbeat_stale_after_seconds` - after which the origin session renders the status
   card (outcome, PR, verdict, evidence path, tier) automatically. **OWNER STATUS CADENCE** [log:
   I-22]: while any session-origin task is live, run a PERSISTENT 15-minute ticker (never a fixed timeout - the 2026-08-20 20:30 lapse: a
   timeout-armed ticker stopped and nobody noticed until the owner asked twice). Every tick
   opens with the CURRENT TIME IN IST, e.g.
   `[20:45 IST]` - a tick with no timestamp does not satisfy the cadence. CONTENT FLOOR per tick:
   what changed since the last tick, what is running, the estimate - an explicit "NOTHING changed"
   tick, never a skipped one, and never fabricated progress.
11. **Budget from task shape** [log: I-23]: `max_turns` from
   `settings.worker_defaults.max_turns_by_deliverable`, floored by
   `settings.worker_defaults.max_turns_by_tier`. A DoD running a full suite, rebuilding assets,
   writing docs AND driving a PR is >=70 turns however small the diff. A turn-cap death resumes
   into the SAME worktree at a raised budget - never redo finished work from origin/main.
12. **Reconcile (keeper duty, every tick)** [log: I-24]: per claimed contract read its `.hb` -
   fresh tick -> leave alone; `EXITED` -> CHECK; stale/dead PID -> kill remnant, append
   `status_log`, re-queue ONCE, park + card on a second death. Foreign-machine claims have no
   local `.hb` by design - require one before calling a task dead, else wait out
   `budget.wall_clock_hours`. Run the janitor here too. `error_max_turns` is NOT a death: raise
   `budget.max_turns` to min(2x current, 200), relaunch into the SAME worktree; lifetime THREE
   runs, then park `QUALITY/SCOPE-SUSPECT`. Reconcile must RUN on this host or exit 15 blocks
   the next dispatch.

**SWEEP RECONCILIATION** [log: I-25] - newest signal wins (status_log + bus git log); a live
origin's activity blocks reclaim except the provably-dead-origin rescue; an unmerged PR blocks
`.done`.

**BUDGET PRE-APPROVAL** [log: I-26]: retries/resumes/raises/reroutes are pre-approved within
plan + daily-ceiling limits, which pause + notify rather than ask. New recurring 3rd-party spend
stays owner-gated.

**INVOCATION LOG** [log: I-27]: end EVERY intake turn with one `GWD/INVOCATIONS.log` line:
`<UTC ISO> | <session-id>@<machine> | cwd-repo=<key|none> | tasks_parsed=<n> | tids=<value>`;
only `tids=none` is the inline defect.

## STEP 7 - CHECK + REPORT: maker != checker

1. **Reporting affinity** [log: I-28]: the contract's `origin:` session owns all in-session
   reporting; another session may LIST a foreign-origin task but never check, report, retry or
   park it. Exceptions: a keeper/sweep rescue of a provably-dead origin and an explicit owner ask
   elsewhere (answer, change nothing).
2. **Checker launch** [log: I-29, I-30]: mandatory, auto-chained, HEADLESS - `worker-wrapper.ps1`,
   `bypassPermissions`, heartbeat `T-<id>C.hb`, watcher armed same turn. Tier = opus when the
   contract is opus, else sonnet - never weaker than the maker. In-session `Agent()` only with the
   owner present and said so. The worker itself runs in the TARGET repo's dir, never the hub's, or
   hub governance leaks into its machine-parsed JSON.
3. **Tier receipt** [log: I-31]: `python GWD/verify-model-tier.py <contract> GWD/heartbeats/<id>.result.json`
   - tier-as-run must equal tier-as-contracted; non-zero = a task FAILURE line, never a silent pass.
4. **Merge-guard predicate**: re-derive item 8 of STEP 6 independently, before scoring any dod.
5. **Verify every `dod:` predicate** by the `deliverable:` procedure:

| `deliverable:` | Checker procedure (re-derivation, never review-and-agree) |
|---|---|
| `code` | Re-run the project's OWN full test gate from scratch; CI green on the PR; diff inspected against the dod predicates |
| `deploy` | verify-effect-at-destination: probe the LIVE URL, capture the screenshot, config-validity gate |
| `content` | Trace EVERY claim to its source (code, PR diff, captured data) - no source row = a FINDING; check placement, structure, each dod predicate. Sample floor: ALL claims <=10, else 10 + every number. `lane: fast` -> `fast-lane-check.py` instead |
| `mechanical` | `fast-lane-check.py` (deterministic) or the repo's own lint - never review-and-agree |
| `claude-resource` | Run `/skill-evaluator` (output mode min; full for a new skill) from the hub; if the target repo can't, execute the resource's own trigger + one scenario end-to-end, capture the transcript |
| `data` | Re-pull a sample from `data_source:` independently and re-derive the headline numbers |

6. **Evidence = re-derivation artifacts, not attestations** [log: I-32]:
   `GWD/evidence/<date>-T-<id>/` holds the raw proof (test output / probe screenshot / claim-source
   table / eval report or transcript / re-pulled sample + recomputation) plus SHA + PR URL, AND the
   `GWD/LEDGER.md` line with tier + costUSD from the receipt. An opinion with no artifact is no
   verdict; the WORKER NEVER writes evidence.
7. **ROOT-CAUSE CLOSE-OUT** [log: I-33]: not done until the verdict carries the SWEEP result for
   every defect fixed and, on a second-occurrence shape, names the MECHANISM installed plus its
   `PATTERNS-SEEN.md` lesson line. New prose alone is INCOMPLETE.
8. **Report + lessons** [log: I-34]: per task - outcome, PR link, evidence path, cost tier, plus
   anything parked and why. Append the shape signature to `GWD/PATTERNS-SEEN.md` (3rd occurrence
   -> a PROPOSED codify card) and every failure/park/reroute/refutation as `LESSON(OPEN):
   <mistake> -> <root cause> -> <rule>`; lifecycle OPEN -> CODIFIED -> ARCHIVED; intake reads
   only the newest 20 OPEN lines. Fleet-mechanics lessons only - hub lessons stay in
   `.claude/tasks/lessons.md`.
9. **Cards** [log: I-35]: the origin session's on-screen render is PRIMARY; `GWD/notify-owner.ps1`
   fires only when that session is dead at terminal time. Origin-less tasks use the card as
   primary; silence is never success. Non-VPS: the ping reaches the relay only after a bus push.
   **Parked digest** [log: I-36]: `GWD/parked-digest.ps1` (weekly) cards every `*.parked.md` with
   age + reason; owner replies `<T-id> retry`/`drop` - parked is never lost.

## ARTIFACT PLACEMENT

[log: I-37] By WHAT the artifact is, not where the fleet runs: project-SPECIFIC -> that repo via
a PR (never bus or hub); fleet-GENERIC machinery -> hub/bus scripts; fleet runtime STATE -> bus.

## CRITICAL RULES

Each bullet carries `gate:<id>` resolving in `config/gwd-gates.yml` (hub). `gate:PROSE-ONLY`
means no machine enforces it yet.

- MUST resolve every repo through `GWD/settings.json` `repo_registry` and assert `git remote
  get-url origin` matches before any edit. gate:PREFLIGHT-REPO-IDENTITY-MISMATCH
- MUST give EVERY task a contract + T-id - owner-present tasks fast-lane under it in a worktree
  of the target repo (SCOPE), everything else dispatches; never the cwd checkout, and authoring
  SSOT-owned artifact text outside a T-id is the same defect. gate:PREFLIGHT-CONTRACT-MISSING
- MUST keep the lanes separate: a `lane: fast` contract is session-executed and checked by
  `fast-lane-check.py`, never handed to a worker. gate:PREFLIGHT-FAST-LANE-AT-WORKER-DISPATCH
- MUST NOT dispatch into a host whose claim reconciler has not ticked inside 2x
  `settings.fleet_keeper_tick_minutes`. gate:PREFLIGHT-KEEPER-LIVENESS
- MUST NOT dispatch past host pressure (commit charge over the limit, or live workers at
  `settings.fleet.max_concurrent_workers`), and MUST fail CLOSED when the host or settings read
  fails rather than reading 0.0%/0. gate:PREFLIGHT-HOST-MEMORY-GATE
- MUST serialize same-repo work fleet-wide (any machine) unless `related:`-linked with disjoint
  file scopes. gate:PREFLIGHT-SAME-REPO-ALREADY-CLAIMED
- MUST copy the registry's `context_docs` into every contract and open the worker prompt with the
  read-these-first mandate. gate:PREFLIGHT-CONTEXT-DOCS-MISSING
- MUST route models cheapest-correct (sonnet default, haiku mechanical, opus deep + security),
  never Fable as a worker, editing tier before any reroute. gate:PREFLIGHT-MODEL-TIER-NOT-ALLOWED
- MUST carry a routing rationale on `model:`, a `data_source:` on a data-reading task, `evidence:
  required`, and a `dod:` of checkable predicates. gate:CONTRACT-LINT-BLOCK
- MUST size `max_turns` from task shape and auto-resume an `error_max_turns` death into the SAME
  worktree at double budget, lifetime THREE runs, then park `QUALITY/SCOPE-SUSPECT`; budget is
  standing pre-approved, never an owner question. gate:PREFLIGHT-TURN-BUDGET-GATE
- MUST open every fix-round prompt with its honesty / PR-body / STATUS.md duties.
  gate:PREFLIGHT-FIX-ROUND-PROMPT-LINT
- MUST apply the ROOT-CAUSE GATE: a SECOND occurrence is fixed at the MECHANISM or the
  impossibility recorded; every fix swept with the count reported; every class fix appends its
  `LESSON(CODIFIED -> ...)` line and `MECHANISM-DUE.md` row. gate:PREFLIGHT-LEARNING-DEBT-GATE
- MUST keep this skill conformant with the live fleet - paths resolve, settings keys exist, every
  preflight exit code documented, one launch recipe, shrink-only byte ratchet.
  gate:GWD-SKILL-CONFORMANCE-TEST
- MUST carry a `gate:<id>` on every rule here; an unmapped MUST is red in CI.
  gate:GWD-SKILL-MUSTS-HAVE-GATES-TEST
- MUST NOT write a worker prompt naming a path that belongs to another machine.
  gate:PREFLIGHT-FOREIGN-MACHINE-PROMPT-PATH
- MUST inject the three standing mandates from `GWD/worker-mandates.txt` - never hand-copied,
  never paraphrased - into every worker, checker and fix-round prompt. gate:PROSE-ONLY (mechanism
  in flight: T-372)
- MUST add the HOLD-LABEL line whenever a `dod:` needs the PR to stay open. gate:PROSE-ONLY
  (mechanism queued: T-372)
- MUST land ALL work via a PR gated on the repo's CI, and the WORKER never merges or closes any
  PR on any repo: PUBLIC repos arm auto-merge, PRIVATE ones (free plan, no branch protection)
  never do - the worker ends at `gh pr checks --watch`, dispatcher/checker merges. Dod boilerplate
  telling a worker to merge is a DEFECT. gate:PROSE-ONLY (mechanism queued: T-372)
- MUST verify PR-state post-run for every task - a PR merged inside the worker's run window is a
  task FAILURE independent of work quality, checked by dispatcher AND checker.
  gate:PROSE-ONLY (mechanism queued: post-run-pr-check.ps1, T-372)
- MUST run the pre-queue dedup gate over ALL open contracts for the repo before queueing.
  gate:PROSE-ONLY
- MUST batch same-repo trivia from one intake into ONE contract (one T-id, one PR).
  gate:PROSE-ONLY
- MUST pass the PORTFOLIO REGISTRATION GATE before queueing, and create project folders only under
  the work root. gate:PROSE-ONLY
- MUST run every abort-capable check at INTAKE while the owner is present, and grill to >95%
  confidence of WHAT is asked; MUST NOT ask what GLOBAL.md, the repo or the registry answers.
  gate:PROSE-ONLY
- MUST run no fleet actor (worker or checker) unattended under interactive permissions.
  gate:PROSE-ONLY
- MUST keep maker != checker: evidence + LEDGER are checker-written only, a self-reported pass is
  never proof, a verdict with no re-derivation artifact is no verdict, and a missing evidence
  folder is a task FAILURE. gate:PROSE-ONLY
- MUST branch on `stop_reason` - a refusal is not success; reroute to opus once, then park.
  gate:PROSE-ONLY
- MUST honor origin-session reporting affinity: only the origin session, or a labeled keeper rescue
  of a provably-dead origin, reports or acts on a task. gate:PROSE-ONLY
- MUST show the owner a queue ack at dispatch AND the terminal status card when the watcher fires,
  and MUST apply the OWNER STATUS CADENCE: a PERSISTENT IST-stamped 15-minute ticker while work
  is live. gate:PROSE-ONLY
- MUST send a terminal-state card as FALLBACK for session-origin tasks and PRIMARY for origin-less
  ones - and on a non-VPS machine push the bus (via `bus-write.ps1`, T-384) after writing the
  ping. gate:PROSE-ONLY
- MUST reprioritize by REORDERING only - a running worker is never preempted. gate:PROSE-ONLY
- MUST honor the deploy tier computed from the ACTUAL merged diff - auth/payment/DNS/migration
  force-upgrades to HOLD. gate:PROSE-ONLY
- MUST append the INVOCATIONS.log line at the end of every intake turn using the defined `tids=`
  tokens - only `tids=none` is the inline defect. gate:PROSE-ONLY

