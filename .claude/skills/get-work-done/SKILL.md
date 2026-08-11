---
name: get-work-done
description: Central work dispatcher (the "mother hub" front door). Hand it one or many tasks — any project, code or deploy — and it sizes each honestly, grills the owner to >95% confidence at intake (ONE question per turn, each with a recommended answer + one-line justification — the owner's 95%-gate, grill-me style; supersedes the old one-batch format 2026-08-09), writes a contract per task, dispatches an autonomous background worker in the target repo's OWN directory on the cheapest-correct model, has an independent checker verify + capture evidence, and lands everything via PR + CI-gated auto-merge. `/get-work-done intake` runs the standing intake-only mode: the session only grills/contracts/queues/dispatches and NEVER executes work inline, so the owner can hand over new tasks at any time without being blocked. Use when the owner hands work to the fleet ("/get-work-done fix X in IPODhan, add Y to calculatekaro"), asks for fleet state ("status"), or wants a running task stopped ("cancel T-042"). Design SSOT: plans/get-work-done-dispatcher.md (all 22 points owner-locked 2026-07-15) — read it before changing ANY behavior here.
---

# /get-work-done — central work dispatcher (Phase 2: parallel fleet, v0.7 — origin-session affinity + dedup gate + on-screen status, cards fallback-only 2026-08-10)

State root (per machine, `settings.json fleet_home`): local mirror `D:\Abhay\VibeCoding\GetWorkDone\`,
fleet home `C:\Abhay\GetWorkDone` on the Windows VPS (**GWD** below = whichever this machine uses).
Contract format = `/goal-creator`'s, extended with dispatcher fields. Phase 2 scope: PARALLEL
dispatch with priority lanes, worker heartbeats via `GWD\worker-wrapper.ps1`, keeper
reconciliation, full `cancel`, and a daily dispatch ceiling. Pings + VPS pools = later phases.

## Mode router

| Invocation | Mode |
|---|---|
| `/get-work-done <task text …>` | INTAKE (steps 1–7) |
| `/get-work-done intake` | INTAKE-ONLY standing mode (owner directive 2026-08-09): loop — take the owner's next task, run steps 1–6 (grill → contract → queue → dispatch), then return to "ready for your next task" IMMEDIATELY. NEVER executes a task inline (trivial included — dispatch on haiku instead); STEP 7 check/report arrives via the armed watcher, between intakes. The owner is never blocked from handing over work |
| `/get-work-done status` | STATUS: render fleet state from `GWD\queue\` + `GWD\heartbeats\` + LEDGER tail |
| `/get-work-done cancel <T-id>` | CANCEL (Phase 2, full): read `GWD\heartbeats\<id>.hb` → kill that PID tree; rename contract to `<id>.cancelled.md` with reason; `gh pr close --delete-branch` any PR it opened; ledger a cancelled line. `cancel all` = every claimed task |
| `/get-work-done sweep` | SWEEP: promote/reject `GWD\inbox\` items per the P17 authorization table, then run INTAKE steps 4–7 on promoted items; then claim + dispatch (steps 6.1–6.8) any unclaimed `*.queued.md` a dead/interrupted session left behind — queued work must never sit undispatched (always-available guarantee, 2026-08-09). DISPATCH-FIRST (live defect 2026-08-10: a sweep tick spent itself "waiting on a watcher" while 4 dispatchable contracts sat queued): claiming+dispatching unclaimed queued work is the FIRST duty of every sweep tick and is never satisfied by watching/waiting on already-claimed tasks; a tick that dispatches nothing MUST state per queued contract why it was not claimable (ceiling / same-repo serialization / lint-block) |

## STEP 1 — INTAKE: parse the ask

Split the input into individual tasks (they may span different repos). For each task resolve
the target repo against `GWD\settings.json → repo_registry` — the ONLY source of repo paths
(it encodes the calculatekaro→`calculator` and algochanakya-vs-OFO traps). A repo not in the
registry, or an ambiguous reference ("the calculator app"?) → that's an intake question, not
a guess.

## STEP 2 — SCOUT (~1 min per task)

In the target repo: `git remote get-url origin` (must equal the registry's `remote` — mismatch
aborts intake with a question), current branch state, does the named area exist, do tests
exist, which paths the task will plausibly touch. Ground the gate in looked-at reality, never
in the prompt alone.

## STEP 3 — GATE: blast radius, not file count (P2/P16-gate)

**Trivial** = touches NO sensitive path (auth, payments, config, DB migration, deploy surface)
AND zero unknowns after the scout → do it NOW in this session (normal branch + PR discipline),
skip to STEP 7 report. **Fable-session exception (fix #4, 2026-07-27):** if THIS dispatching
session runs on Fable/Mythos, do NOT execute the task inline — the cheapest work must not burn
the priciest model (plan risk #4). Dispatch it as a normal contract on haiku/sonnet instead
(the contract ceremony costs less than Fable executing the edit). Everything else → full
contract. A "trivial" task that turns deep mid-flight STOPS and re-enters here as a full
contract — it never limps on. **Intake-mode exception (2026-08-09):** in `/get-work-done intake`
mode NOTHING executes inline — even a trivial task is contracted + dispatched (haiku), because
the intake session's one job is staying free for the owner's next task.

## STEP 4 — CLARIFY: one batch, everything, while the owner is present

**NON-SKIPPABLE (defect fix 2026-07-18):** "run it" / "go ahead" means PROCEED — it does NOT mean skip
this step. A non-trivial task ALWAYS resolves its material unknowns before dispatch. TWO layers:
(a) DETERMINE, don't ask, anything you can scout — e.g. "compare IPODhan's data" → the authoritative
source is the app's OWN DB/API, NOT scraping its public site; scout the data layer and use it. Asking
what you can determine is itself a defect. (b) For a GENUINE material unknown (2+ valid answers that
change the OUTCOME, unscoutable) → ask it in the upfront batch. Applying "decide-don't-ask" to a
material outcome-changing unknown (as happened on T-013: assumed public-scrape, hit a WAF, asked after)
is a MISAPPLICATION — that rule is for reversible EXECUTION details only, never for what-to-build /
which-source intent. If in doubt whether an unknown is material: it is → resolve at intake.

FAIL AT INTAKE, NOT AT MIDNIGHT (locked principle): run every abort-capable check NOW —
registry/remote identity (done in scout), branch protection + secret-scan gate on the target
(P4 audit re-check via `gh api`), needed credentials/tools present, deploy tier per the table
below. Then resolve the genuine unknowns via the owner's **95%-confidence gate** (global
CLAUDE.md standing rule 2026-08-07; re-ratified for fleet intake 2026-08-09 — supersedes the
old one-batch format): do NOT queue or dispatch a task below >95% confidence of WHAT is being
asked. Ask **ONE question per turn**, opening with `*Sync-check:*` (grill-me style), each with
a **recommended answer FIRST + a one-line justification**; keep going until confidence exceeds
95%. Approval-class items (deploy tier below) are asked the same way, as their own question.
The fail-at-intake principle is unchanged — every unknown is still resolved while the owner is
present, only the question FORMAT changed (serialized, not batched):

| Deploy situation | Tier |
|---|---|
| Re-deploy of a live app, same domain/infra | AUTO (Tier 1) — no question |
| New app onto a `sandbox_domains` subdomain | AUTO (Tier 1) — pre-authorized by the grant |
| First deploy / DNS / new domain / auth or payment surface | HOLD (Tier 2) — collect the yes/no NOW |

**Deploy execution (Phase 4, P12/P13):** when a task's tier resolves to AUTO, the deploy runs via
`GWD\deploy-site.sh` ON the Hostinger VPS (where nginx/certbot/webroots live; bus-driven like the
relay). It captures the current webroot as KNOWN-GOOD first, builds niced (never starves live sites),
swaps in the new build, `nginx -t`-gates the reload, PROBES the live URL, and on any probe/​config
failure RESTORES the known-good + reloads (revert-first, P13) — the forward-fix is a separate P1 task.
NEW-APP subdomains (P12): the dispatcher first creates the `<app>.<sandbox>` DNS A-record via the
GoDaddy/Cloudflare API (GLOBAL.env), then the runner adds the vhost + certbot TLS. **Requires a granted
`settings.sandbox_domains` entry — until the owner provides one, new-app auto-deploy stays Tier-2 (HOLD).**

Nothing answerable from GLOBAL.md, the repo, or the registry may be asked.

## STEP 5 — CONTRACT: via /goal-creator, extended

Invoke `/goal-creator` with the task + answers; extend its contract with the dispatcher
fields and write to `GWD\queue\T-<nnn>-<slug>.queued.md`:

**T-ID ALLOCATION (MANDATORY, live triple-collision 2026-08-10 — T-063/T-064/T-068 each
allocated to TWO different tasks by independent sessions, and the T-068 pair's shared
`T-068.hb` heartbeat filename cross-contaminated both tasks' death-detection):** never invent
the next id. (1) `git pull` the bus, (2) run `python GWD\next-task-id.py <GWD>` and use its
answer, (3) if the bus push of the contract is rejected non-fast-forward, pull and RE-RUN the
allocator before retrying — another session may have taken the id in the race window. An id
seen ANYWHERE historically (queue, archive, LEDGER) is never reused.

**PRE-QUEUE DEDUP GATE (owner requirement 2026-08-10 — MANDATORY, runs before writing the
contract):** read EVERY open contract in `GWD\queue\` (`*.queued.md`, `*.claimed.*.md`,
`*.parked.md`) for the same target repo and compare scope (goal, files/area the task will
touch). Three outcomes, recorded in the new contract or intake reply:
- **Duplicate** (same outcome already queued/claimed) → do NOT queue; tell the owner the
  existing T-id instead. Two sessions asking for the same thing must converge on ONE task.
- **Overlapping/related** (different outcome, shared area) → queue it with a
  `related: [T-xxx]` line; same-repo serialization already prevents file interference, the
  link makes the checker aware of the sibling.
- **Supersedes** (new task makes an open one obsolete) → rename the old contract
  `.superseded-by-T-<new>.md` with a one-line note; never leave both live.
The queue is the SHARED cross-session truth — a session must never queue from only its own
memory of what it dispatched.

```yaml
repo: <registry key>            # path + remote resolved from settings.json at dispatch
origin: <session-id>@<machine> <project-dir-name>   # WHO took this task from the owner (owner requirement 2026-08-10): in-session progress/result reporting belongs to THIS session ONLY
related: []                      # T-ids sharing scope in the same repo (dedup gate above)
model: haiku|sonnet|opus        # + MANDATORY one-line rationale on this line (lint-enforced)
deliverable: code|deploy|content|claude-resource|data   # lint-enforced (fix V2 2026-07-27) — selects the checker procedure
priority: P1|P2|P3               # dispatcher-assigned AUTONOMOUSLY (owner 2026-08-09): P1 prod-broken/blocking/owner-says-urgent, P2 normal feature/fix, P3 cleanup/nice-to-have — never ask the owner to rank
deploy_tier: none|auto|hold-approved|hold-denied
approvals: [<granted at intake>]
budget: {max_turns: <settings.worker_defaults.max_turns_by_tier[model], fallback max_turns>, wall_clock_hours: 4}
evidence: required              # checker-written, never worker-written
dod:                            # lint-enforced (fix V2): CHECKABLE completion predicates, dod-verbs discipline
  - <ACTION + COMPLETENESS BAR, verifiable by a stranger — never "write good docs">
status_log: []
```

`dod:` items follow /goal-creator's dod-verbs rule: state the ACTION **and** the completeness
bar ("contract doc documents the per-partner pattern INCLUDING the two fallbacks", not
"update the doc") — an autonomous worker satisfies the weakest literal reading, and the
CHECKER can only verify what is written as a predicate.

**WORKER-MERGE GUARD (mandatory standing line, live double-breach 2026-08-11 — T-099's worker
merged a foreign PR to resolve references, T-101's worker merged its own gate-2 PR mid-run
against an explicit contract prohibition):** every worker prompt MUST carry this standing
mandate line verbatim, regardless of `deliverable:` or model tier: "You NEVER merge or close
ANY pull request — yours, a foreign one, or anyone else's — and you NEVER push to `main`.
Landing (merge-on-green, closing, deleting a branch) is dispatcher/checker-owned, not yours."
Prose-only prohibition proved insufficient twice; STEP 6 and STEP 7 below back it with a
deterministic post-run PR-state check so a breach is CAUGHT, not just discouraged.

**Routing table (fix #5, 2026-07-27 — inlined so NON-hub dispatch sessions, e.g. via the
global pointer skill, don't depend on the hub-only rule being loaded; SSOT remains
`D:\Abhay\VibeCoding\claude-best-practices\.claude\rules\model-routing.md`):**

| Tier | Contract it for |
|---|---|
| `haiku` | rubric scoring, classification, extraction, format checks, mechanical single-file edits |
| `sonnet` (DEFAULT) | any explicit brief + machine-checkable gate: code edits per plan, tests, research, docs |
| `opus` | deep debugging, architecture, multi-file design freedom — AND **preemptively for ALL security-category work** (security scan/audit, vulnerability analysis, exploit-adjacent, authz, prompt-injection; fix #8 — avoids the refusal round-trip; contract-lint BLOCKS security-on-cheaper-tier) |
| Fable/Mythos | NEVER a worker (preflight-guard exit 4) |

When torn, pick the cheaper tier — the escalation rule (STEP 6.6) recovers a wrong cheap
pick after evidence; a wrong expensive pick is never detected.

## STEP 6 — DISPATCH: one background worker, guarded

1. **Atomic claim**: rename `…queued.md → …claimed.<session-id>.md`. Rename failed → another
   session owns it; skip.
2. **Contract lint (deterministic, runs FIRST — T-020 2026-07-20):** run
   `python GWD\contract-lint.py <claimed contract path>` — exit 0 = clean to dispatch; non-zero
   BLOCKS (reason on stderr: missing/empty required field, unresolved assumption language, a
   data-reading task with no declared `data_source:`, a `model:` line with no routing rationale,
   or a security-category task on a non-opus tier — fixes #6/#8 2026-07-27). Blocked → park the contract with the
   lint's stderr as the reason, never dispatch it. This runs BEFORE the preflight gate so a
   malformed contract is rejected before any workspace is cloned. The gate was dead prose until
   this call site existed (`check_fleet_script_health.py` dead-gate finding); `SKILL.md` is the
   canonical caller — keep this step and the script in sync or the health gate re-fires.
3. **Deterministic preflight gate (Phase 2, P3/G18 + owner Q2):** run
   `powershell -NoProfile -ExecutionPolicy Bypass -File GWD\preflight-guard.ps1 -ContractPath <c> -RepoPath <workspace> -ExpectedRemote <registry remote>` —
   exit 0 = OK; non-zero BLOCKS (model not haiku|sonnet|opus incl. Fable-as-worker → exit 4; repo
   identity mismatch → exit 6). This makes cheapest-correct routing + wrong-repo protection
   machine-enforced, not prose-dependent. Blocked → park with the reason, never dispatch.
4. **Workspace (owner design 2026-07-16, clone-on-demand):** on the fleet-home box, the target
   repo is cloned FRESH at dispatch (`git clone --filter=blob:none`, per-machine path from
   settings.json) unless a workspace from the retention window already exists AND is clean. The
   keeper's janitor deletes workspaces idle past `workspaces.retention_days` ONLY when provably
   clean (no uncommitted changes, no unpushed branches) — dirty workspaces are escalated to the
   owner, NEVER deleted (live save 2026-07-16: pre-existing IPODhan WIP). Permanent exceptions:
   the bus, the hub clone (keeper engine), GLOBAL.md/GLOBAL.env scp-copies (never in git).
5. Launch via background Bash, IN the workspace directory so the repo's own CLAUDE.md/plugins load.
   The prompt goes via STDIN — never as an argument (a contract starting with `---` frontmatter
   is parsed as a CLI flag; live failure 2026-07-15):
   ```bash
   # prompt file = contract body + worker mandate + required JSON output shape
   cd <registry path> && claude -p --model <tier> --max-turns <cap> \
     --permission-mode bypassPermissions --output-format json \
     < GWD\heartbeats\T-<id>.prompt.txt > GWD\heartbeats\T-<id>.result.json
   ```
   Same-repo-as-dispatcher tasks: the contract MUST order the worker into its own git worktree
   (two sessions must never share one checkout).
6. On exit, parse the JSON **`stop_reason` — a refusal is NOT success** (exit code lies).
   Terminal-state rules (fixes #2/#3/#7, 2026-07-27):
   - **Refusal on haiku/sonnet → reroute to opus via the FULL procedure**, never a bare
     relaunch: (a) EDIT the contract's `model:` to `opus  # rerouted: refusal on <tier>`,
     (b) append the reroute to `status_log`, (c) re-run contract-lint + preflight-guard,
     (d) relaunch. Skipping (a) records the wrong tier in LEDGER/evidence and corrupts the
     cost audit (P21) — the contract must always state the tier that actually runs.
   - **Refusal on opus (original or rerouted) → PARK immediately** with an owner card
     carrying the refusal category. There is NO second reroute, ever.
   - **Error → one retry on the SAME tier** (most errors are environmental). A **2nd
     failure** on the same task: classify it — environmental (missing tool/auth/network/
     trust-dialog/OOM) → park with the error text as before; **capability/quality class
     (worker ran fine but produced wrong/insufficient work) → escalate ONE tier**
     (haiku→sonnet→opus) via the same edit-contract + re-lint + re-preflight procedure,
     record the routing lesson in `status_log`, and relaunch once; already at opus → park
     (model-routing.md: "escalate ONE tier after 2 supervised failures"). Max ONE
     escalation per task — if the escalated relaunch also fails, PARK; never chain
     haiku→sonnet→opus on one task.
   - Keeper DEATHS stay un-escalated (STEP 6.9): a dead PID is environmental by
     definition — re-queue once at the same tier, park on the second death.
6a. **WORKER-MERGE GUARD — post-exit PR-state check (mandatory, live double-breach
   2026-08-11):** after parsing the result JSON (item 6 above), check the state of EVERY PR
   the contract references — its own gate PR plus any PR the worker's JSON reports touching —
   via `gh pr view <PR> --json state,mergedBy,mergedAt`. A PR that shows `state: MERGED` with
   `mergedAt` inside the worker's run window (dispatch timestamp → result JSON timestamp) is a
   task FAILURE line in `status_log` + `GWD\LEDGER.md` + an owner card — regardless of how good
   the work is. This runs for EVERY task, not just ones that look suspicious; a worker that
   merged nothing produces a clean, fast check.
7. **Parallel lanes (Phase 2, P6/P12):** dispatch up to `settings.soft_concurrency_cap`
   workers concurrently — SAME-repo tasks always serialize; different repos run in parallel.
   Priority P1 > P2 > P3; a P1 is ALWAYS admitted even at the cap. Exceeding the soft cap is
   allowed only for mechanical, independent tasks. **Reprioritization (owner 2026-08-09):**
   when a NEW task arrives, the dispatcher re-judges priority across the whole QUEUE on its
   own — a more urgent task is queued ahead (edit the contracts' `priority:` fields; same-repo
   serialization still holds). REORDER ONLY: a running worker is NEVER preempted or killed for
   priority (cancel stays owner-only); urgency is served by P1 always-admitted, not by killing
   in-flight work. Before each dispatch check the DAILY
   CEILINGS (both, fix #10 2026-07-27): (a) dispatches today >= `settings.max_dispatches_per_day`,
   OR (b) the keeper's failures log (`GWD\heartbeats\keeper-tick-failures.log`) shows a
   CEILING-EXCEEDED line dated today (written by `cost-rollup.py --check-ceiling` against the
   numeric `settings.daily_token_ceiling`) → pause new dispatches, ping the owner once
   (fleet-paused), never retry-storm.
8. **Heartbeat dispatch (P7):** on Windows machines launch via the wrapper —
   `powershell -File GWD\worker-wrapper.ps1 -TaskId <id> -RepoPath <workspace> -Model <tier> -MaxTurns <cap> -StateRoot <GWD>`
   — `-StateRoot` is MANDATORY off the VPS: its default is the VPS fleet home
   `C:\Abhay\GetWorkDone`, so omitting it on the local PC fails with "prompt file
   missing" (live misfire T-038, 2026-08-01). Pass THIS machine's GWD path.
   (prompt file at `GWD\heartbeats\<id>.prompt.txt` first). The wrapper writes
   `<id>.hb` (PID + tick, ~60s) and the result JSON.
8a-bis. **ON-SCREEN QUEUE ACK (owner requirement 2026-08-10):** the moment a task is queued or
   dispatched, RENDER a visible confirmation in the origin session's chat — T-id, target repo,
   model tier, priority, budget, one-line DoD summary. The owner must SEE on screen that the
   task entered the fleet, in the same session where they gave it — a silent queue insert is a
   defect.
8b. **ARM A WATCHER IN THE SAME TURN AS THE LAUNCH (fix #13, 2026-08-08 — owner-reported).**
   A worker launched **detached** (PowerShell `Start-Process`, `nohup`, anything the harness holds
   no handle on) emits **NO completion notification** — nothing tells the dispatcher it died. In
   the SAME turn as the dispatch, arm a `Monitor` until-loop (or a `ScheduleWakeup` tick sized to
   the expected run) that breaks on **every terminal state, not just success**: result JSON
   written, `.hb` reading `EXITED`, or heartbeat older than
   `settings.heartbeat_stale_after_seconds`. Silence is not success — a filter that only matches
   the happy path is indistinguishable from a crash. The terminal test MUST require a
   **NON-EMPTY** result JSON (the wrapper pre-creates the file at 0 bytes — a live-fire watcher
   false-positived on the empty placeholder 2026-08-10 and declared a running worker finished;
   `EXITED` heartbeat and true staleness are the other two valid terminal signals).
   **Live incident:** 2026-08-08 T-056 — relaunched detached to survive shell reaping (the known
   background-Bash trap), hit its turn cap 9 minutes later, and the failure sat **unnoticed for
   35 minutes** until the owner asked "everything done?". Recovery must never wait on the owner.
   The two traps are a pair: background Bash gets reaped and kills its child; detached survives
   but goes dark. Use detached **AND** a watcher, never one alone.
   **ON-SCREEN COMPLETION STATUS (owner requirement 2026-08-10):** when the watcher fires on a
   terminal state, the origin session AUTOMATICALLY renders the task's status card on screen in
   that session's chat — outcome (DONE/PARKED/FAILED), PR link, checker verdict, evidence path,
   tier — without the owner having to ask. Queue ack (8a-bis) + this completion render are the
   PRIMARY owner-facing reporting for session-origin tasks.

8c. **BUDGET FROM TASK SHAPE, NOT TIER DEFAULT (fix #14, same incident).** `max_turns` is set at
   intake from what the task must actually DO, not from `worker_defaults`. Any contract whose DoD
   includes running a full test suite, rebuilding assets, writing docs AND driving a PR to merge
   is a **≥70-turn** task however small its diff — the PR/CI/merge tail alone costs 10-15 turns.
   T-056 was a ~40-line fix budgeted at 40 turns; it wrote correct code and died one turn short of
   running the suite. On a turn-cap death, RESUME INTO THE SAME WORKTREE with a raised budget
   (the prompt must name the branch, the uncommitted files, and forbid restarting from scratch) —
   never relaunch from origin/main and redo finished work.

9. **Reconcile (keeper duty, every tick):** for each `claimed` contract read its `.hb` —
   fresh tick + live PID → leave alone (slow ≠ dead); `EXITED` → route to CHECK; stale (> 
   `settings.heartbeat_stale_after_seconds`) or dead PID → kill remnant, append status_log,
   re-queue ONCE; a SECOND death on the same task → park + owner card.
   **FOREIGN-MACHINE CLAIMS ARE NOT DEAD (live defect 2026-08-09, T-060 double-dispatch):**
   heartbeats are machine-local (gitignored), so a contract claimed by ANOTHER machine's
   session has NO local `.hb` BY DESIGN. Before treating a claimed contract as dead, require
   a local dispatch artifact (`.hb` or `.prompt.txt`) proving it was launched FROM THIS
   machine. A claim with no local artifact is FOREIGN: leave it alone until the contract's
   `budget.wall_clock_hours` has elapsed since the claim rename (bus git log dates it), and
   even then re-queue only with a status_log note naming the foreign session id. Also run the JANITOR
   here (workspaces idle past retention, clean-only delete, dirty → escalate).
   **Turn-cap AUTO-RESUME (owner-approved 2026-08-09):** a result JSON with subtype
   `error_max_turns` is NOT routed to CHECK and NOT treated as a death — AUTO-RESUME once:
   (a) edit the contract's `budget.max_turns` to min(2x current, 200) with a one-line note,
   (b) append the resume to `status_log`, (c) relaunch INTO THE SAME WORKTREE with a prompt
   that names the branch + the uncommitted files and FORBIDS restarting from scratch (8c).
   ONE auto-resume per task, ever — a second cap death parks with an owner card. (T-056
   would have self-healed instead of sitting dead 35 min.)

## STEP 7 — CHECK + REPORT: maker ≠ checker (P5)

**ORIGIN-SESSION REPORTING AFFINITY (owner requirement 2026-08-10):** the contract's `origin:`
session owns ALL in-session progress/result reporting for that task — the owner hears about a
task in the session where they gave it, nowhere else. Every other session treats foreign-origin
tasks as read-only context: `status` mode may LIST them, but MUST NOT check, report, retry,
park, or otherwise act on them. Exactly two exceptions: (a) the KEEPER/SWEEP rescuing a task
whose origin session is provably dead (reconcile rules, STEP 6.9) — the rescue is then reported
via the owner card channel with a "rescued from <origin>" note, never as another session's own
work; (b) an explicit owner ask in another session ("what happened to T-061?") — answer it, but
change nothing. Cross-session meddling with a live origin's tasks is the 2026-08-09/10
interference class — a defect, not initiative.

**AUDIT-GAP FIXES 2026-07-18 (from the T-014 self-review):**
- **Worker cwd:** launch the worker in the TARGET repo's dir (or a neutral working dir like the app's
  deploy path) — NEVER the hub repo dir. Running in the hub made a worker inherit hub governance and
  emit the `*Enhanced:*` ceremony in its report (leak). The dispatch cwd is the target, not `claude-best-practices`.
- **Checker is MANDATORY and AUTO-CHAINED, never manual.** STEP 7 is not optional and not owner-triggered:
  every task with `evidence: required` (all non-trivial) automatically spawns a SEPARATE checker agent (in a
  neutral dir) that re-verifies a sample from SOURCE before the task is reported done. On T-014 the checker
  CONFIRMED a real bug (a duplicate DB row) AND REFUTED a false one (worker claimed "price data missing" —
  it was present under a differently-named column). A worker report without a checker verdict is INCOMPLETE.
- **Evidence = raw pulls + report + checker verdict**, all saved to `GWD\evidence\<date>-<id>\` — not just the
  final prose. The raw data is what lets the checker (and owner) independently re-examine claims later.

The worker's "done" claim is input, not truth. Dispatch a CHECKER (separate `Agent()`; tier =
**opus when the contract's model is opus, sonnet otherwise** — fix #11: the checker is never
weaker than the maker) against the worker's output. FIRST run the deterministic tier receipt
`python GWD\verify-model-tier.py <contract> GWD\heartbeats\<id>.result.json` (fix #1 — asserts
tier-as-run == tier-as-contracted from `modelUsage`; non-zero = a task FAILURE line in
status_log + LEDGER, never a silent pass). **Then run the WORKER-MERGE GUARD check (mandatory
predicate, same as STEP 6a — the checker re-derives it independently rather than trusting the
dispatcher's pass):** `gh pr view` on every PR the contract/result JSON references; any PR
merged inside the worker's run window is a task FAILURE regardless of `deliverable:` type —
record it in the checker verdict before scoring any other dod predicate. Then verify **every
`dod:` predicate** via the
procedure for the contract's `deliverable:` type (fixes V1/V3/V4, 2026-07-27 — before this
table only code/deploy had a defined procedure; content and skills could pass on checker
opinion):

| `deliverable:` | Checker procedure (re-derivation, never review-and-agree) |
|---|---|
| `code` | Re-run the project's OWN full test gate from scratch; CI green on the PR; diff inspected against dod predicates |
| `deploy` | verify-effect-at-destination: probe the LIVE URL, capture the screenshot, config-validity gate |
| `content` (docs/reports/research) | Trace EVERY factual/technical claim in the deliverable to its source (code, PR diff, captured data) — a claim with no source row is a FINDING; check placement + structure against the repo's conventions; check each dod predicate individually. Sample floor: ALL claims when ≤10, else 10 + every number |
| `claude-resource` (skill/agent/rule/hook) | Run the hub's `/skill-evaluator` (output mode minimum; full for new skills) from the hub checkout; if the target repo can't run it, execute the resource's own trigger + one real scenario end-to-end and capture the transcript. An unexercised skill is UNVERIFIED, never done |
| `data` | Independently re-pull a sample from the contract's `data_source:` and re-derive the worker's headline numbers (T-014 precedent: checker CONFIRMED a real dup-row bug AND REFUTED a false "missing data" claim) |

**Evidence = re-derivation artifacts, not attestations (fix V4):** the evidence folder
`GWD\evidence\<date>-T-<id>\` must contain the checker's raw proof (test output / probe
screenshot / claim→source table / eval report or scenario transcript / re-pulled sample +
recomputation) plus SHA + PR URL, AND the `GWD\LEDGER.md` line — including the tier +
costUSD from the receipt, so the P21 cost audit reads receipts, not claims. A checker
verdict consisting of an opinion ("reviewed, looks correct") with no re-derivation artifact
is INCOMPLETE — treat it as no verdict. The WORKER NEVER writes evidence. Foolproof it is
not (a checker can err) — but every verdict leaves auditable raw evidence a later session
or the owner can re-examine, and CI re-gates anything code-shaped at merge. Then report to the owner: per task —
outcome, PR link, evidence path, cost tier used; plus anything parked and why. Append the
task's shape signature to `GWD\PATTERNS-SEEN.md` (3rd occurrence → file a PROPOSED codify
card, P20).

**TERMINAL-STATE CARDS — FALLBACK-ONLY for session-origin tasks (owner pick 2026-08-10,
supersedes the 2026-08-09 always-card rule):** for a task with a session `origin:`, the
PRIMARY report is the origin session's on-screen render (8a-bis + 8b watcher). The
Telegram/WhatsApp card via `GWD\notify-owner.ps1` fires ONLY when the origin session is
dead/closed at terminal time (keeper/sweep detects no live origin — the card then opens
with "origin session gone"). Tasks with NO session origin (inbox promotions, keeper break-fix)
keep the card as their primary channel — DONE (P3→info: outcome + PR link + tier) / PARKED or
FAILED (P2: reason). The invariant is unchanged: silence is never success; the owner must
never have to ask "everything done?" (T-056 sat dead 35 min because nothing fired).
Delivery trap on a NON-VPS machine: `notify-owner.ps1` only writes the ping file to the
local bus `pings\` outbox — the Hostinger relay reads the BUS REPO, so after writing the
card you MUST commit+push the bus or the card never delivers (a written-but-unpushed ping
is the detect-then-discard defect class).

**PARKED DIGEST (owner-approved 2026-08-09):** parked must never mean forgotten. The
deterministic weekly `GWD\parked-digest.ps1` (keeper-tick step, self-gated like the
feature sweep) cards the owner every `*.parked.md` with age + reason. The owner replies
`<T-id> retry` (SWEEP re-queues at the same tier) or `<T-id> drop` (SWEEP renames to
`<T-id>.dropped.md`); the sweep processes these replies like any owner answer.

## ARTIFACT PLACEMENT (rule 2026-07-18 — owner question)
Where a created artifact lives is determined by WHAT it is, not where the fleet runs:
- **Project-SPECIFIC artifact** (a tool/script/config for ONE app — e.g. an IPODhan audit tool) → lands
  IN that project's repo via a PR (versioned with the app, discoverable by its team, covered by its CI).
  NEVER the bus or hub. (Defect fixed: ipo-audit.py was wrongly put in the bus → moved to IPODhan #112.)
- **Fleet-GENERIC machinery** (dispatcher, keeper, contract-lint, bus-sync, guards) → the hub / bus scripts.
- **Fleet runtime STATE** (queue, ledger, evidence, questions) → the GetWorkDone bus only.
Litmus test before saving: "would the target project's team want this in their repo?" If yes → their repo.

## CRITICAL RULES

- MUST resolve every repo through `GWD\settings.json repo_registry` and assert
  `git remote get-url origin` matches BEFORE any edit — the registry encodes real traps
  (calculatekaro=`calculator`; OFO shares algochanakya's remote — never dispatch into OFO).
- MUST run every abort-capable check at INTAKE while the owner is present; runtime re-checks
  are last-line guards, never first detection.
- MUST run the pre-queue dedup gate (scan ALL open contracts for the target repo) before
  queueing; duplicates converge on the existing T-id, overlaps carry `related:`, supersedes
  rename the old contract — two sessions must never independently queue the same work.
- MUST honor origin-session reporting affinity: every contract carries `origin:`; only the
  origin session (or a keeper rescue of a provably-dead origin, labeled as such) reports or
  acts on a task — all other sessions are read-only toward it.
- MUST grill at intake to >95% confidence of WHAT is asked (owner standing rule): ONE
  question per turn, `*Sync-check:*` opener, recommended answer + one-line justification on
  each, until the gate passes — no queueing/dispatch below it. MUST NOT ask anything
  answerable from GLOBAL.md / the repo / the registry.
- MUST keep the intake surface always available: in `intake` mode nothing executes inline
  (contract + dispatch everything, return to ready immediately); SWEEP claims + dispatches
  any unclaimed `*.queued.md` so queued work never sits.
- MUST reprioritize by REORDERING the queue only — a running worker is never preempted for
  priority.
- MUST show the owner on-screen, in the origin session: a queue ack at dispatch AND the
  terminal status card when the watcher fires (8a-bis/8b) — the owner never has to ask.
- MUST send a terminal-state card (DONE/PARKED/FAILED) as FALLBACK for session-origin tasks
  (only when the origin session is dead at terminal time, labeled "origin session gone") and
  as PRIMARY for origin-less tasks — and on a non-VPS machine MUST push the bus after writing
  the ping or the card never delivers.
- MUST auto-resume an `error_max_turns` death exactly ONCE (doubled budget, same worktree,
  no restart-from-scratch); a second cap death parks with an owner card.
- MUST branch on `stop_reason` from the worker's JSON — refusal ≠ success; reroute to opus.
- MUST keep maker ≠ checker: evidence + LEDGER are checker-written only; a worker's
  self-reported pass is never recorded as proof.
- MUST land ALL work via PR gated on the repo's CI. PUBLIC repos: arm auto-merge (protection
  enforces the check). PRIVATE repos (free plan — NO branch protection possible; live finding
  2026-07-15: IPODhan, RealFuelPrices, calculatekaro): NEVER arm auto-merge (it merges
  instantly regardless of CI) — the worker `gh pr checks --watch`es until the gate is SUCCESS
  and only then merges; red = never merged, no exceptions.
- MUST route models cheapest-correct (sonnet default, haiku mechanical, opus deep AND
  preemptively for security-category); Fable is NEVER dispatched as a worker. The `model:`
  line carries its rationale (lint-blocked otherwise); every reroute/escalation EDITS the
  contract tier before relaunch; the checker verifies the tier receipt (verify-model-tier.py)
  — a tier the contract didn't state, or a receipt that contradicts it, is a task FAILURE.
- MUST honor the deploy-tier table computed from the ACTUAL diff at check time (G9) — a task
  whose merged diff touches auth/payment/DNS/migration paths force-upgrades to HOLD regardless
  of intake classification.
- MUST stop a trivial-gated task that turns deep and re-enter intake — never limp on.
- MUST write an evidence-folder failure as a task FAILURE (G20), never skip it.
- MUST verify PR-state post-run for every task (STEP 6a + STEP 7): `gh pr view` on every PR
  the contract or result JSON references; a PR merged by the worker during its own run window
  is a task FAILURE, independent of work quality — checked by both the dispatcher and the
  checker, never trusted from the worker's self-report.
