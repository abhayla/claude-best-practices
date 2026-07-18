---
name: get-work-done
description: Central work dispatcher (the "mother hub" front door). Hand it one or many tasks — any project, code or deploy — and it sizes each honestly, asks ALL questions in one upfront batch (including approvals), writes a contract per task, dispatches an autonomous background worker in the target repo's OWN directory on the cheapest-correct model, has an independent checker verify + capture evidence, and lands everything via PR + CI-gated auto-merge. Use when the owner hands work to the fleet ("/get-work-done fix X in IPODhan, add Y to calculatekaro"), asks for fleet state ("status"), or wants a running task stopped ("cancel T-042"). Design SSOT: plans/get-work-done-dispatcher.md (all 22 points owner-locked 2026-07-15) — read it before changing ANY behavior here.
---

# /get-work-done — central work dispatcher (Phase 2: parallel fleet, v0.2)

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
skip to STEP 7 report. Everything else → full contract. A "trivial" task that turns deep
mid-flight STOPS and re-enters here as a full contract — it never limps on.

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
model: haiku|sonnet|opus        # + one-line rationale (model-routing.md; Fable NEVER)
priority: P1|P2|P3
deploy_tier: none|auto|hold-approved|hold-denied
approvals: [<granted at intake>]
budget: {max_turns: <from settings.worker_defaults>, wall_clock_hours: 4}
evidence: required              # checker-written, never worker-written
status_log: []
```

## STEP 6 — DISPATCH: one background worker, guarded

1. **Atomic claim**: rename `…queued.md → …claimed.<session-id>.md`. Rename failed → another
   session owns it; skip.
2. **Deterministic preflight gate (Phase 2, P3/G18 + owner Q2):** run
   `powershell -NoProfile -ExecutionPolicy Bypass -File GWD\preflight-guard.ps1 -ContractPath <c> -RepoPath <workspace> -ExpectedRemote <registry remote>` —
   exit 0 = OK; non-zero BLOCKS (model not haiku|sonnet|opus incl. Fable-as-worker → exit 4; repo
   identity mismatch → exit 6). This makes cheapest-correct routing + wrong-repo protection
   machine-enforced, not prose-dependent. Blocked → park with the reason, never dispatch.
3. **Workspace (owner design 2026-07-16, clone-on-demand):** on the fleet-home box, the target
   repo is cloned FRESH at dispatch (`git clone --filter=blob:none`, per-machine path from
   settings.json) unless a workspace from the retention window already exists AND is clean. The
   keeper's janitor deletes workspaces idle past `workspaces.retention_days` ONLY when provably
   clean (no uncommitted changes, no unpushed branches) — dirty workspaces are escalated to the
   owner, NEVER deleted (live save 2026-07-16: pre-existing IPODhan WIP). Permanent exceptions:
   the bus, the hub clone (keeper engine), GLOBAL.md/GLOBAL.env scp-copies (never in git).
4. Launch via background Bash, IN the workspace directory so the repo's own CLAUDE.md/plugins load.
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
5. On exit, parse the JSON **`stop_reason` — a refusal is NOT success** (exit code lies):
   refusal → re-route once to opus (append `status_log`), continue. Error → one retry, then
   park with the error text.
6. **Parallel lanes (Phase 2, P6/P12):** dispatch up to `settings.soft_concurrency_cap`
   workers concurrently — SAME-repo tasks always serialize; different repos run in parallel.
   Priority P1 > P2 > P3; a P1 is ALWAYS admitted even at the cap. Exceeding the soft cap is
   allowed only for mechanical, independent tasks. Before each dispatch check the DAILY
   CEILING: dispatches today >= `settings.max_dispatches_per_day` → pause new dispatches, ping
   the owner once (fleet-paused), never retry-storm.
7. **Heartbeat dispatch (P7):** on Windows machines launch via the wrapper —
   `powershell -File GWD\worker-wrapper.ps1 -TaskId <id> -RepoPath <workspace> -Model <tier> -MaxTurns <cap>`
   (prompt file at `GWD\heartbeats\<id>.prompt.txt` first). The wrapper writes
   `<id>.hb` (PID + tick, ~60s) and the result JSON.
8. **Reconcile (keeper duty, every tick):** for each `claimed` contract read its `.hb` —
   fresh tick + live PID → leave alone (slow ≠ dead); `EXITED` → route to CHECK; stale (> 
   `settings.heartbeat_stale_after_seconds`) or dead PID → kill remnant, append status_log,
   re-queue ONCE; a SECOND death on the same task → park + owner card. Also run the JANITOR
   here (workspaces idle past retention, clean-only delete, dirty → escalate).

## STEP 7 — CHECK + REPORT: maker ≠ checker (P5)

The worker's "done" claim is input, not truth. Dispatch a CHECKER (separate `Agent()`, sonnet)
against the worker's PR: re-run the project's test gate, run the verify-effect-at-destination
probe (deploy tasks: probe the LIVE URL), capture the screenshot, and write BOTH the evidence
folder `GWD\evidence\<date>-T-<id>\` (screenshot + test output + SHA + PR URL) AND the
`GWD\LEDGER.md` line. The WORKER NEVER writes evidence. Then report to the owner: per task —
outcome, PR link, evidence path, cost tier used; plus anything parked and why. Append the
task's shape signature to `GWD\PATTERNS-SEEN.md` (3rd occurrence → file a PROPOSED codify
card, P20).

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
- MUST route models cheapest-correct (sonnet default, haiku mechanical, opus deep/security);
  Fable is NEVER dispatched as a worker.
- MUST honor the deploy-tier table computed from the ACTUAL diff at check time (G9) — a task
  whose merged diff touches auth/payment/DNS/migration paths force-upgrades to HOLD regardless
  of intake classification.
- MUST stop a trivial-gated task that turns deep and re-enter intake — never limp on.
- MUST write an evidence-folder failure as a task FAILURE (G20), never skip it.
