---
name: get-work-done
description: Central work dispatcher (the "mother hub" front door). Hand it one or many tasks — any project, code or deploy — and it sizes each honestly, asks ALL questions in one upfront batch (including approvals), writes a contract per task, dispatches an autonomous background worker in the target repo's OWN directory on the cheapest-correct model, has an independent checker verify + capture evidence, and lands everything via PR + CI-gated auto-merge. Use when the owner hands work to the fleet ("/get-work-done fix X in IPODhan, add Y to calculatekaro"), asks for fleet state ("status"), or wants a running task stopped ("cancel T-042"). Design SSOT: plans/get-work-done-dispatcher.md (all 22 points owner-locked 2026-07-15) — read it before changing ANY behavior here.
---

# /get-work-done — central work dispatcher (Phase 1: sequential, v0.1)

State root: `D:\Abhay\VibeCoding\GetWorkDone\` (**GWD** below) — settings + verified repo
registry in `GWD\settings.json`. The contract format is `/goal-creator`'s, extended with
dispatcher fields. Phase 1 scope: ONE background worker at a time; parallel lanes, heartbeat
reconciliation, pings, and VPS pools arrive in later phases (see the plan's lock ledger).

## Mode router

| Invocation | Mode |
|---|---|
| `/get-work-done <task text …>` | INTAKE (steps 1–7) |
| `/get-work-done status` | STATUS: render fleet state from `GWD\queue\` + `GWD\heartbeats\` + LEDGER tail |
| `/get-work-done cancel <T-id>` | CANCEL: kill worker PID (heartbeat file), mark contract `cancelled: <reason>`, close+delete its PR/branch via `gh` |
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
2. **Last-line re-checks** (cheap; intake already passed them): registry path exists, remote
   matches. Mismatch → abort + park with a question (should be near-impossible after STEP 4).
3. Launch via background Bash, IN the target repo's directory so its own CLAUDE.md/plugins load.
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
4. On exit, parse the JSON **`stop_reason` — a refusal is NOT success** (exit code lies):
   refusal → re-route once to opus (append `status_log`), continue. Error → one retry, then
   park with the error text.
5. Phase 1 is SEQUENTIAL: wait for this worker (background Bash notifies) before dispatching
   the next task; report progress to the owner between tasks.

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
- MUST land ALL work via PR + CI-gated auto-merge — never direct-to-main, never manual merge.
- MUST route models cheapest-correct (sonnet default, haiku mechanical, opus deep/security);
  Fable is NEVER dispatched as a worker.
- MUST honor the deploy-tier table computed from the ACTUAL diff at check time (G9) — a task
  whose merged diff touches auth/payment/DNS/migration paths force-upgrades to HOLD regardless
  of intake classification.
- MUST stop a trivial-gated task that turns deep and re-enter intake — never limp on.
- MUST write an evidence-folder failure as a task FAILURE (G20), never skip it.
