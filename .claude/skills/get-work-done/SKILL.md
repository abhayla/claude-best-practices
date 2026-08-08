---
name: get-work-done
description: Central work dispatcher (the "mother hub" front door). Hand it one or many tasks — any project, code or deploy — and it sizes each honestly, asks ALL questions in one upfront batch (including approvals), writes a contract per task, dispatches an autonomous background worker in the target repo's OWN directory on the cheapest-correct model, has an independent checker verify + capture evidence, and lands everything via PR + CI-gated auto-merge. Use when the owner hands work to the fleet ("/get-work-done fix X in IPODhan, add Y to calculatekaro"), asks for fleet state ("status"), or wants a running task stopped ("cancel T-042"). Design SSOT: plans/get-work-done-dispatcher.md (all 22 points owner-locked 2026-07-15) — read it before changing ANY behavior here.
---

# /get-work-done — central work dispatcher (Phase 2: parallel fleet, v0.3 — routing-gap hardening 2026-07-27)

State root (per machine, `settings.json fleet_home`): local mirror `D:\Abhay\VibeCoding\GetWorkDone\`,
fleet home `C:\Abhay\GetWorkDone` on the Windows VPS (**GWD** below = whichever this machine uses).
Contract format = `/goal-creator`'s, extended with dispatcher fields. Phase 2 scope: PARALLEL
dispatch with priority lanes, worker heartbeats via `GWD\worker-wrapper.ps1`, keeper
reconciliation, full `cancel`, and a daily dispatch ceiling. Pings + VPS pools = later phases.

## Mode router

| Invocation | Mode |
|---|---|
| `/get-work-done <task text …>` | INTAKE (steps 1–7) |
| `/get-work-done status` | STATUS: render fleet state from `GWD\queue\` + `GWD\heartbeats\` + LEDGER tail |
| `/get-work-done cancel <T-id>` | CANCEL (Phase 2, full): read `GWD\heartbeats\<id>.hb` → kill that PID tree; rename contract to `<id>.cancelled.md` with reason; `gh pr close --delete-branch` any PR it opened; ledger a cancelled line. `cancel all` = every claimed task |
| `/get-work-done sweep` | SWEEP: promote/reject `GWD\inbox\` items per the P17 authorization table, then run INTAKE steps 4–7 on promoted items |

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
contract — it never limps on.

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
below. Then ask ALL resulting questions in ONE batch of numbered option cards (recommended
option FIRST with a one-line why; single/multi-select stated). Include approval-class items:

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

```yaml
repo: <registry key>            # path + remote resolved from settings.json at dispatch
model: haiku|sonnet|opus        # + MANDATORY one-line rationale on this line (lint-enforced)
deliverable: code|deploy|content|claude-resource|data   # lint-enforced (fix V2 2026-07-27) — selects the checker procedure
priority: P1|P2|P3
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
7. **Parallel lanes (Phase 2, P6/P12):** dispatch up to `settings.soft_concurrency_cap`
   workers concurrently — SAME-repo tasks always serialize; different repos run in parallel.
   Priority P1 > P2 > P3; a P1 is ALWAYS admitted even at the cap. Exceeding the soft cap is
   allowed only for mechanical, independent tasks. Before each dispatch check the DAILY
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
8b. **ARM A WATCHER IN THE SAME TURN AS THE LAUNCH (fix #13, 2026-08-08 — owner-reported).**
   A worker launched **detached** (PowerShell `Start-Process`, `nohup`, anything the harness holds
   no handle on) emits **NO completion notification** — nothing tells the dispatcher it died. In
   the SAME turn as the dispatch, arm a `Monitor` until-loop (or a `ScheduleWakeup` tick sized to
   the expected run) that breaks on **every terminal state, not just success**: result JSON
   written, `.hb` reading `EXITED`, or heartbeat older than
   `settings.heartbeat_stale_after_seconds`. Silence is not success — a filter that only matches
   the happy path is indistinguishable from a crash.
   **Live incident:** 2026-08-08 T-056 — relaunched detached to survive shell reaping (the known
   background-Bash trap), hit its turn cap 9 minutes later, and the failure sat **unnoticed for
   35 minutes** until the owner asked "everything done?". Recovery must never wait on the owner.
   The two traps are a pair: background Bash gets reaped and kills its child; detached survives
   but goes dark. Use detached **AND** a watcher, never one alone.

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
   re-queue ONCE; a SECOND death on the same task → park + owner card. Also run the JANITOR
   here (workspaces idle past retention, clean-only delete, dirty → escalate).

## STEP 7 — CHECK + REPORT: maker ≠ checker (P5)

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
status_log + LEDGER, never a silent pass). Then verify **every `dod:` predicate** via the
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
- MUST ask all questions in ONE upfront batch of numbered option cards (recommended first);
  MUST NOT ask anything answerable from GLOBAL.md / the repo / the registry.
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
