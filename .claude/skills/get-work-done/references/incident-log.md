# /get-work-done — incident log (verbatim archive of the v0.9 narratives)

Every section below is copied **VERBATIM** out of `SKILL.md` v0.9 (the 66,296-byte
version, hub commit `a8a5c16b`, 2026-08-27) when T-371 split the skill into
procedure (SKILL.md) + incident history (this file). Nothing was reworded, shortened
or dropped: the line ranges cited are the v0.9 line numbers the text came from, so any
reader can `git show a8a5c16b:.claude/skills/get-work-done/SKILL.md | sed -n '<a>,<b>p'`
and diff it against the block here.

SKILL.md keeps the RULE; this file keeps the STORY that justifies it. Each rule in
SKILL.md carries a one-line back-reference of the form `[log: I-nn]` pointing at the
matching anchor below.

| Anchor | Incident / rule origin | v0.9 lines |
|---|---|---|
| [I-01](#i-01) | Inline execution deleted — the GoRefer wrong-context incident (2026-08-15) | 49-58 |
| [I-02](#i-02) | Root-cause gate — the eight turn-cap deaths (2026-08-20) | 71-99 |
| [I-03](#i-03) | Clarify at intake — T-013 (WAF), T-141 (permission stall), deploy-tier table | 101-134 |
| [I-04](#i-04) | Portfolio registration gate (migration Phase 4b, 2026-08-12) | 32-38 |
| [I-05](#i-05) | Portfolio registration at clarify time + deploy execution (P12/P13) | 136-153 |
| [I-06](#i-06) | T-id allocation — the 2026-08-10 triple collision (T-063/T-064/T-068) | 160-166 |
| [I-07](#i-07) | Pre-queue dedup gate (owner requirement 2026-08-10) | 168-180 |
| [I-08](#i-08) | Trivial-task batching (2026-08-15) | 182-190 |
| [I-09](#i-09) | Wave-chaining for sequential same-repo waves (2026-08-17, gorefer 3x) | 192-205 |
| [I-10](#i-10) | Context docs — the "details already provided earlier" fix (2026-08-15) | 207-214 |
| [I-11](#i-11) | WORKER-MERGE GUARD — the 2026-08-11 double breach (T-099, T-101) | 238-248 |
| [I-12](#i-12) | FOREGROUND-ONLY EXECUTION — T-152 backgrounded pytest (2026-08-16) | 250-258 |
| [I-13](#i-13) | HOLD-LABEL INSTRUCTION — PR #558 / PR #560 auto-merged (2026-08-16) | 260-270 |
| [I-14](#i-14) | CI-minutes discipline — measured on PR #580 (2026-08-19) | 272-310 |
| [I-15](#i-15) | Cross-machine same-repo gate — T-141/T-142 vs T-143/T-144/T-145 (2026-08-16) | 328-340 |
| [I-16](#i-16) | Workspace + janitor (owner design 2026-07-16; the IPODhan dirty-WIP save) | 360-366 |
| [I-17](#i-17) | DELETED launch recipe — the STDIN form the fleet abandoned 2026-08-12 | 367-377 |
| [I-18](#i-18) | Terminal-state rules — refusal, error, escalation (fixes #2/#3/#7, 2026-07-27) | 378-397 |
| [I-19](#i-19) | Post-exit PR-state check (2026-08-11) | 398-404 |
| [I-20](#i-20) | Parallel lanes, reprioritization, daily ceilings, actions-minutes hold | 406-422 |
| [I-21](#i-21) | Heartbeat dispatch via the wrapper — the T-038 -StateRoot misfire (2026-08-01) | 424-434 |
| [I-22](#i-22) | Watcher + on-screen status + 15-min cadence — T-056 (2026-08-08), the empty-JSON false positive (2026-08-10), the 2026-08-20 ticker lapse | 436-474 |
| [I-23](#i-23) | Budget from task shape, not tier default (T-056) | 476-483 |
| [I-24](#i-24) | Reconcile, foreign-machine claims (T-060), turn-cap auto-resume (T-179) | 485-508 |
| [I-25](#i-25) | Sweep reconciliation rules — T-178 / T-179 (2026-08-18) | 510-526 |
| [I-26](#i-26) | Standing budget pre-approval (owner 2026-08-17) | 528-537 |
| [I-27](#i-27) | Invocation log semantics (v0.8.1, verifier finding MEDIUM-6) | 539-550 |
| [I-28](#i-28) | Origin-session reporting affinity (owner requirement 2026-08-10) | 554-563 |
| [I-29](#i-29) | Audit-gap fixes from the T-014 self-review (2026-07-18) | 565-579 |
| [I-30](#i-30) | Checkers must be headless — the T-141 90-minute stall (2026-08-16) | 581-601 |
| [I-31](#i-31) | Tier receipt + merge-guard check + the deliverable checker table | 603-622 |
| [I-32](#i-32) | Evidence = re-derivation artifacts, not attestations (fix V4) | 624-635 |
| [I-33](#i-33) | Root-cause close-out (STEP 3.5 enforced at check time) | 637-641 |
| [I-34](#i-34) | Lessons live in PATTERNS-SEEN.md (owner 2026-08-15) | 643-651 |
| [I-35](#i-35) | Terminal-state cards — fallback-only for session-origin tasks (2026-08-10) | 653-665 |
| [I-36](#i-36) | Parked digest (owner-approved 2026-08-09) | 667-671 |
| [I-37](#i-37) | Artifact placement (rule 2026-07-18) | 673-680 |

## I-01

**Inline execution deleted — the GoRefer wrong-context incident (2026-08-15)** — verbatim, v0.9 lines 49-58:

**The inline-execution path is DELETED (owner-approved 2026-08-15; live defect: a GoRefer
session did Wati/Zoho work itself, inline, in the wrong directory with the wrong context — no
T-id, no contract, no checker).** Every task handed to /get-work-done — however trivial — is
contracted (STEP 5) and dispatched (STEP 6). The old carve-outs (trivial-inline, the Fable
exception, the intake-mode exception) are all subsumed: there is ONE behavior now. The binary
invariant any audit can check: **a get-work-done task with no T-id is a defect.**

Blast radius (sensitive paths: auth, payments, config, DB migration, deploy surface) still gets
assessed here — but it now informs ONLY model tier, budget, and deploy_tier, never
inline-vs-dispatch. Trivial tasks are made cheap by BATCHING (STEP 5), not by inline execution.

## I-02

**Root-cause gate — the eight turn-cap deaths (2026-08-20)** — verbatim, v0.9 lines 71-99:

## STEP 3.5 — ROOT-CAUSE GATE: the SECOND occurrence must fix the MECHANISM

Owner rule 2026-08-20, his words: fix things so "the issues do not happen again", because
re-fixing instances "will take a lot of time". The evidence it exists: eight workers (T-204,
T-205, T-210, T-218, T-223, T-225, T-227, T-228) finished correct engineering, then died at
their turn cap with everything UNCOMMITTED — each rescued by hand at ~20 min, ~2.5 hours in
one day. The response every single time was a firmer prose mandate; it failed all eight times.
The mechanism fix (worker-wrapper autosaves a dirty tree on exit, T-231) was filed only after
the owner challenged it.

- **First occurrence** of a failure may be fixed as an instance.
- **From the SECOND occurrence of the same failure SHAPE** (same symptom class — not the same
  file, task or repo), the instance fix is NOT acceptable on its own: fix the MECHANISM that
  permits the shape, or record in the contract's `status_log`, explicitly and with the reason,
  why a mechanism fix is impossible. Silence is not an exemption.
- **PROSE IS NOT A MECHANISM.** A stronger instruction — in a worker prompt, a mandate block,
  a contract, or this skill — does NOT count as a class fix: one "COMMIT EARLY AND OFTEN"
  mandate line failed eight consecutive times. A mechanism is CODE, a GUARD, a HOOK, a SCHEMA
  CONSTRAINT, or a TEST THAT FAILS when the defect returns. If the fix you are about to ship
  is words, it is an instance fix wearing a class fix's clothes.
- **SWEEP before a task is called done.** A fixed defect is searched for across the repo (and
  the estate, where the shape travels) BEFORE completion, and the search result is REPORTED:
  "fixed 1 of N found" or "swept, no other instances". Done right on 2026-08-20: the em-dash
  fix swept 14 lines AND added a pre-commit guard; the Windows path guard fixed all 11 files
  AND added a regression test; the stopwatch-test sweep found a SECOND instance.
- **SELF-IMPROVEMENT.** Every recurrence-triggered class fix appends its lesson to
  `GWD\PATTERNS-SEEN.md` in mechanism-fix form — `LESSON(CODIFIED → <where>): <symptom> →
  <shape> → <mechanism installed>` — so the next dispatcher inherits the guard instead of
  re-deriving the story (same lesson lifecycle as STEP 7; no new store).

## I-03

**Clarify at intake — T-013 (WAF), T-141 (permission stall), deploy-tier table** — verbatim, v0.9 lines 101-134:

## STEP 4 — CLARIFY: resolve everything at intake, one question per turn, while the owner is present

**NON-SKIPPABLE (defect fix 2026-07-18):** "run it" / "go ahead" means PROCEED — it does NOT mean skip
this step. A non-trivial task ALWAYS resolves its material unknowns before dispatch. TWO layers:
(a) DETERMINE, don't ask, anything you can scout — e.g. "compare IPODhan's data" → the authoritative
source is the app's OWN DB/API, NOT scraping its public site; scout the data layer and use it. Asking
what you can determine is itself a defect. (b) For a GENUINE material unknown (2+ valid answers that
change the OUTCOME, unscoutable) → ask it via the 95%-gate below, one question per turn. Applying "decide-don't-ask" to a
material outcome-changing unknown (as happened on T-013: assumed public-scrape, hit a WAF, asked after)
is a MISAPPLICATION — that rule is for reversible EXECUTION details only, never for what-to-build /
which-source intent. If in doubt whether an unknown is material: it is → resolve at intake.

FAIL AT INTAKE, NOT AT MIDNIGHT (locked principle): run every abort-capable check NOW —
registry/remote identity (done in scout), branch protection + secret-scan gate on the target
(P4 audit re-check via `gh api`), needed credentials/tools present, deploy tier per the table
below. **Tool-permission surface (2026-08-16, T-141 stall):** any actor — worker OR checker —
that will run unattended MUST be on a no-prompt path (`bypassPermissions` or pre-allowlisted
tools only); verify this NOW, at intake, never discovered mid-run when the owner is away. An
unattended dispatch whose permission mode is unverified is itself an abort-capable finding —
park it rather than launch and hope no tool call trips a dialog. Then resolve the genuine
unknowns via the owner's **95%-confidence gate** (global
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

## I-04

**Portfolio registration gate (migration Phase 4b, 2026-08-12)** — verbatim, v0.9 lines 32-38:

**PORTFOLIO REGISTRATION GATE (migration Phase 4b, 2026-08-12):** also check the task's target
repo against the 5wealths PORTFOLIO registry — `PORTFOLIO.yml` on 5wealths `main` once it
exists; until then the `PORTFOLIO-ALIGNMENT-NOTES.md` candidate-registry-rows table is the
interim registry. A task targeting a repo absent from that registry, or a task that would
create a NEW project folder, cannot be queued until a registration row (name, pillar,
machines) exists for it — carry this as an open item into STEP 4, it is never silently
skipped.

## I-05

**Portfolio registration at clarify time + deploy execution (P12/P13)** — verbatim, v0.9 lines 136-153:

**Portfolio registration (migration Phase 4b, 2026-08-12):** if STEP 1's PORTFOLIO REGISTRATION
GATE flagged the target repo as unregistered (or the task creates a new project folder), that
IS a material unknown — resolve it here, same `*Sync-check:*` format, before queueing. If the
pillar is knowable from context/GLOBAL.md, determine it and write the registration row
yourself (name, pillar, machines) into the interim registry; only ask when the pillar is
genuinely ambiguous (one question, recommended pillar + one-line justification). Never queue
the task un-registered.

**Deploy execution (Phase 4, P12/P13):** when a task's tier resolves to AUTO, the deploy runs via
`GWD\deploy-site.sh` ON the Hostinger VPS (where nginx/certbot/webroots live; bus-driven like the
relay). It captures the current webroot as KNOWN-GOOD first, builds niced (never starves live sites),
swaps in the new build, `nginx -t`-gates the reload, PROBES the live URL, and on any probe/​config
failure RESTORES the known-good + reloads (revert-first, P13) — the forward-fix is a separate P1 task.
NEW-APP subdomains (P12): the dispatcher first creates the `<app>.<sandbox>` DNS A-record via the
GoDaddy/Cloudflare API (GLOBAL.env), then the runner adds the vhost + certbot TLS. **Requires a granted
`settings.sandbox_domains` entry — until the owner provides one, new-app auto-deploy stays Tier-2 (HOLD).**

Nothing answerable from GLOBAL.md, the repo, or the registry may be asked.

## I-06

**T-id allocation — the 2026-08-10 triple collision (T-063/T-064/T-068)** — verbatim, v0.9 lines 160-166:

**T-ID ALLOCATION (MANDATORY, live triple-collision 2026-08-10 — T-063/T-064/T-068 each
allocated to TWO different tasks by independent sessions, and the T-068 pair's shared
`T-068.hb` heartbeat filename cross-contaminated both tasks' death-detection):** never invent
the next id. (1) `git pull` the bus, (2) run `python GWD\next-task-id.py <GWD>` and use its
answer, (3) if the bus push of the contract is rejected non-fast-forward, pull and RE-RUN the
allocator before retrying — another session may have taken the id in the race window. An id
seen ANYWHERE historically (queue, archive, LEDGER) is never reused.

## I-07

**Pre-queue dedup gate (owner requirement 2026-08-10)** — verbatim, v0.9 lines 168-180:

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

## I-08

**Trivial-task batching (2026-08-15)** — verbatim, v0.9 lines 182-190:

**TRIVIAL-TASK BATCHING (2026-08-15 — what keeps the no-inline rule usable):** multiple small
tasks from ONE intake targeting the SAME repo are written as **ONE contract** with one `dod:`
item per task — one T-id, one worker, one PR — never N serialized contracts each paying
clone + lint + preflight + checker + PR. (Without this, 5 small Wati edits = hours of
serialized ceremony, and the owner routes around the fleet — reintroducing the inline defect.)
The dedup gate's "overlapping/related" branch MERGES same-intake trivia into one contract
instead of linking siblings. Batches are SAME-`deliverable:` only — a code fix and a doc
update need different checker procedures, so a mixed batch is split into one contract per
deliverable type (verifier finding LOW-8).

## I-09

**Wave-chaining for sequential same-repo waves (2026-08-17, gorefer 3x)** — verbatim, v0.9 lines 192-205:

**WAVE-CHAINING FOR SEQUENTIAL SAME-REPO WAVES (2026-08-17 — 3rd-occurrence codification;
see `GWD\PATTERNS-SEEN.md` ~L72-73, gorefer eight-lens-review waves backed up the same-repo
gate 3x on 2026-08-16 17:07/19:08 and 2026-08-17 01:34 with `related: []` on every contract):**
when queueing a WAVE of same-repo contracts at intake that are sequential/dependent by design
(e.g. a later contract's own body states it "runs LAST" or depends on an earlier one in the
wave), the LATER contract's `related:` field MUST list the immediately-prior wave T-id(s) it
depends on — chaining the dependency at queue time — instead of leaving `related: []` and
relying on the CROSS-MACHINE SAME-REPO GATE (STEP 6) to silently re-block it every sweep tick.
This does not change STEP 6's gate logic: a same-repo block on a non-related contract still
produces a fresh non-actionable diagnosis every sweep; with wave-chaining, the same block
becomes an EXPECTED/silent hold instead, because the gate's own `related:`-check already treats
a named relation as informative, not blocking-different. Same mechanism as the dedup gate's
"overlapping/related" outcome above — this is that same `related:[T-xxx]` convention applied at
wave-queueing time specifically for designed sequential dependency, not incidental scope overlap.

## I-10

**Context docs — the "details already provided earlier" fix (2026-08-15)** — verbatim, v0.9 lines 207-214:

**CONTEXT DOCS (2026-08-15 — the "details already provided earlier" fix):** copy the
registry's `context_docs` list for the target repo (`GWD\settings.json →
repo_registry.<key>.context_docs`, **repo-relative paths only**) into the contract, and the
worker prompt MUST open with: "Before ANY work, read these files at the repo root: <list>.
If any is missing, STOP and report it — do not proceed without it." CLAUDE.md is never
listed (it auto-loads from the worker's cwd). If a listed doc contradicts the code, the
repo wins. `preflight-guard.ps1` BLOCKS dispatch (exit 7) when a listed doc is missing from
the workspace — a missing context doc is never a shrug-and-continue.

## I-11

**WORKER-MERGE GUARD — the 2026-08-11 double breach (T-099, T-101)** — verbatim, v0.9 lines 238-248:

**WORKER-MERGE GUARD (mandatory standing line, live double-breach 2026-08-11 — T-099's worker
merged a foreign PR to resolve references, T-101's worker merged its own gate-2 PR mid-run
against an explicit contract prohibition):** every worker prompt MUST carry this standing
mandate line verbatim, regardless of `deliverable:` or model tier: "You NEVER merge or close
ANY pull request — yours, a foreign one, or anyone else's — and you NEVER push to `main`.
Landing (merge-on-green, closing, deleting a branch) is dispatcher/checker-owned, not yours."
Prose-only prohibition proved insufficient twice; STEP 6 and STEP 7 below back it with a
deterministic post-run PR-state check so a breach is CAUGHT, not just discouraged. This exact
line also doubles as the machine-origin marker `plugins/prompt-auto-enhance`'s `turn-origin.sh`
classifier keys on to skip the enhance ceremony on headless `claude -p` workers (T-134, live
defect: the ceremony leaked into a worker's machine-parsed JSON result) — never reword or drop it.

## I-12

**FOREGROUND-ONLY EXECUTION — T-152 backgrounded pytest (2026-08-16)** — verbatim, v0.9 lines 250-258:

**FOREGROUND-ONLY EXECUTION (mandatory standing line, SECOND line of the WORKER-MERGE GUARD
mandate — live defect 2026-08-16, T-152: a headless worker backgrounded its pytest run then
ended its turn; in `claude -p` ending a turn KILLS the process, so the task died silently
mid-run with a `success` subtype and no result JSON):** every worker prompt MUST ALSO carry
this standing mandate line verbatim, in addition to (never in place of) the merge-guard line
above: "Run EVERY command in the FOREGROUND and wait for it; NEVER run anything in the
background - in headless claude -p, ending your turn kills your process and orphans the task."
Both lines are mandatory and verbatim; the merge-guard line above is never reworded, reordered,
or dropped to make room for this one.

## I-13

**HOLD-LABEL INSTRUCTION — PR #558 / PR #560 auto-merged (2026-08-16)** — verbatim, v0.9 lines 260-270:

**HOLD-LABEL INSTRUCTION (mandatory second line, live double-breach 2026-08-16 — T-144's PR #558
auto-merged 84s post-creation, T-143's PR #560 auto-merged ~7min post-creation, neither worker ran
`gh pr merge`):** the WORKER-MERGE GUARD line above only constrains the WORKER's own actions — it
says nothing about this repo's OWN `auto-pr-reconcile.sh`/`session-git-landing.sh` automation,
which auto-lands any open, green, non-`hold`-labeled PR regardless of who opened it or whether they
ever ran a merge command. For ANY contract whose `dod:` requires the PR to stay open (e.g. "leaves
the PR OPEN"), the dispatcher MUST include a SECOND, separate worker-prompt line — never merged
into or replacing the verbatim WORKER-MERGE GUARD line above — instructing the worker to apply the
`hold` label immediately after opening the PR: `gh pr edit <n> --add-label hold`. This is the actual
mechanism that stops the repo's ambient automation from landing it; refraining from merging is not
sufficient on its own.

## I-14

**CI-minutes discipline — measured on PR #580 (2026-08-19)** — verbatim, v0.9 lines 272-310:

**CI-MINUTES DISCIPLINE (owner Decision 2, 2026-08-18; WORKER PUSH RULE corrected 2026-08-19 —
T-209, evidence PR #580):** the fleet-side half of the CI-quota fix (T-190 is the repo-side
half) — two codified rules:

1. **WORKER PUSH RULE.** Every worker, checker, and fix-round prompt's standing mandates gain a
   THIRD verbatim line, additive to (never replacing) the WORKER-MERGE GUARD and FOREGROUND-ONLY
   EXECUTION lines above: "Intermediate commits (WIP, docs-only, fix-round iterations) carry
   `[skip ci]` ANYWHERE in the commit message — GitHub matches the whole message, headline or
   body, there is no safe placement for a push that still needs CI. ONLY the final
   ready-for-verification push carries the marker NOWHERE — not the headline, not the body, not
   even quoted while describing this convention." Copy this line VERBATIM into every dispatch —
   dispatchers do not paraphrase it. **Measured on PR #580, 2026-08-19, same branch, two
   consecutive pushes:** push 1 carried the marker as the LAST LINE OF THE BODY (headline clean)
   — result: ZERO workflow runs started, `gh pr checks` reported "no checks reported", PR
   BLOCKED. Push 2 was an empty commit with the marker NOWHERE — result: `Validate PR` and
   `Tests` both started within 45s and passed. The quota was not the cause (Validate PR runs had
   completed successfully the day before). **A prior belief that "the marker is safe in the
   body, only the headline suppresses CI" is FALSE** — GitHub's skip-ci match is a substring
   search over the ENTIRE commit message, not the headline alone; a fleet convention that relied
   on that belief has been suppressing the CI it was meant to preserve on every push that
   followed it. **The consequence is why this matters:** this repo's `validate` check is
   REQUIRED — a push that carries the marker anywhere, on a commit that was meant to be
   validated, leaves the PR with NO checks to ever report; branch protection blocks the merge
   forever and auto-merge never fires. That is exactly what stalled PRs #577/#579 under the
   T-191 incident, whose headline-only diagnosis treated the symptom and left the substring-match
   cause in place. Without the push-rule line at all, each fix-round push burns a full PR CI run
   on top of the eventual real one; applied correctly (marker truly absent, not just absent from
   the headline, on the final push), a task costs at most ONE CI run plus the merge's own check.
2. **SAME-REPO LANDING BATCHING.** Same-repo tasks whose contracts are written within the same
   calendar day default to ONE shared branch/PR/CI-run — extending the existing TRIVIAL-TASK
   BATCHING (STEP 5 above) and WAVE-CHAINING (STEP 5 above) conventions; the PRE-QUEUE DEDUP
   GATE's "overlapping/related" outcome is the mechanism that merges them. Named exceptions:
   P1 break-fixes land solo (urgency beats batching economics); tasks with conflicting
   file-scopes split into separate contracts (a shared PR can't safely hold two workers editing
   the same files); a checker FAIL on one batched task holds only that task's hunks if they are
   separable from the rest of the batch's diff, otherwise the whole batch re-rounds together.
   **Projected effect (stated honestly, not guaranteed):** fix-loops drop from 2-4 CI runs to 1
   per task; same-repo same-day batching further reduces the PR count itself, not just the
   per-PR run count.

## I-15

**Cross-machine same-repo gate — T-141/T-142 vs T-143/T-144/T-145 (2026-08-16)** — verbatim, v0.9 lines 328-340:

**CROSS-MACHINE SAME-REPO GATE (mandatory, live incident 2026-08-16 — T-141/T-142 ran on
itsab-PC while the VPS sweep concurrently ran T-143/T-144/T-145 against the same hub repo; no
bus-level repo lock existed, and the run survived only by luck of disjoint file-sets, not by
design):** before claiming or dispatching ANY task, `git pull` the bus and scan the GWD queue
for ANY `*.claimed.*.md` contract targeting the SAME registry repo key, from ANY machine. If
one exists, do NOT dispatch the new task unless (a) it is `related:`-linked to that claimed
contract AND (b) the two contracts' file-scopes are declared disjoint. Same-repo serialization
is a whole-fleet invariant, not a same-machine one — a machine-local queue view is not proof no
other machine is working the repo. This prose gate is backed by a deterministic preflight
backstop, `preflight-guard.ps1` exit 8 (SAME-REPO ALREADY-CLAIMED GATE, landed via the related
bus task T-155): it blocks dispatch outright when a same-repo sibling `*.claimed.*.md` contract
exists and this contract's `related:` list doesn't name it — keep this paragraph and that gate
in sync.

## I-16

**Workspace + janitor (owner design 2026-07-16; the IPODhan dirty-WIP save)** — verbatim, v0.9 lines 360-366:

4. **Workspace (owner design 2026-07-16, clone-on-demand):** on the fleet-home box, the target
   repo is cloned FRESH at dispatch (`git clone --filter=blob:none`, per-machine path from
   settings.json) unless a workspace from the retention window already exists AND is clean. The
   keeper's janitor deletes workspaces idle past `workspaces.retention_days` ONLY when provably
   clean (no uncommitted changes, no unpushed branches) — dirty workspaces are escalated to the
   owner, NEVER deleted (live save 2026-07-16: pre-existing IPODhan WIP). Permanent exceptions:
   the bus, the hub clone (keeper engine), GLOBAL.md/GLOBAL.env scp-copies (never in git).

## I-17

**DELETED launch recipe — the STDIN form the fleet abandoned 2026-08-12** — verbatim, v0.9 lines 367-377:

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

> **DO NOT USE THIS RECIPE.** It is archived here only because it was the
> documented path for months. `worker-wrapper.ps1` abandoned STDIN on
> 2026-08-12 (Claude Code 2.1.227: stdin is invisible to console-less
> processes), so a worker launched this way starts with NO PROMPT and the
> host-memory worker counter cannot see it. The one live recipe is in
> SKILL.md STEP 6.

## I-18

**Terminal-state rules — refusal, error, escalation (fixes #2/#3/#7, 2026-07-27)** — verbatim, v0.9 lines 378-397:

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

## I-19

**Post-exit PR-state check (2026-08-11)** — verbatim, v0.9 lines 398-404:

6a. **WORKER-MERGE GUARD — post-exit PR-state check (mandatory, live double-breach
   2026-08-11):** after parsing the result JSON (item 6 above), check the state of EVERY PR
   the contract references — its own gate PR plus any PR the worker's JSON reports touching —
   via `gh pr view <PR> --json state,mergedBy,mergedAt`. A PR that shows `state: MERGED` with
   `mergedAt` inside the worker's run window (dispatch timestamp → result JSON timestamp) is a
   task FAILURE line in `status_log` + `GWD\LEDGER.md` + an owner card — regardless of how good
   the work is. This runs for EVERY task, not just ones that look suspicious; a worker that

## I-20

**Parallel lanes, reprioritization, daily ceilings, actions-minutes hold** — verbatim, v0.9 lines 406-422:

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
   (fleet-paused), never retry-storm. **ACTIONS-MINUTES HOLD (budget plan part c, owner Decision
   2 2026-08-18):** before dispatching a task whose landing will trigger private-repo CI, check
   `GWD\state\ci-hold.flag` — present means only P1 tasks proceed, others queue with a status
   note (prose rule; a preflight-guard exit code is the codify-later follow-up in

## I-21

**Heartbeat dispatch via the wrapper — the T-038 -StateRoot misfire (2026-08-01)** — verbatim, v0.9 lines 424-434:

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

## I-22

**Watcher + on-screen status + 15-min cadence — T-056 (2026-08-08), the empty-JSON false positive (2026-08-10), the 2026-08-20 ticker lapse** — verbatim, v0.9 lines 436-474:

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
   **15-MINUTE SCOREBOARD CADENCE (owner order 2026-08-16 13:53):** while ANY task from a
   session-origin intake is live (claimed/running, including checker and fix rounds), the origin
   session renders the full task scoreboard table (T-id, task, state, PR, round) on screen every
   15 minutes — armed as a ticker in the SAME turn as the first dispatch (piggyback the existing
   `Monitor`/`ScheduleWakeup` watcher above, or a second tick at the same cadence), stopped only
   when the queue drains. A silent gap longer than 15 minutes while work is running is a defect.
   **OWNER STATUS CADENCE (owner directive 2026-08-20 23:53 IST):** this is a SKILL obligation,
   not a per-plan promise — a plan-level cadence evaporates with the plan; a skill rule inherits
   into every future dispatching session. Every tick OPENS WITH THE CURRENT TIME IN IST (e.g.
   `[21:46 IST]`) so the owner always knows when the last update was dropped — a tick with no
   timestamp does not satisfy the cadence. CONTENT FLOOR, one line: what changed since the last
   tick (landed/failed/dispatched), what is running now, and the current estimate if one was
   given; if NOTHING changed, say so explicitly with the time rather than skipping the tick.
   MECHANISM: the ticker MUST be PERSISTENT for the session, never a fixed timeout that silently
   expires — the 2026-08-20 20:30 lapse was exactly this failure shape, a ticker armed with a
   timeout instead of as persistent, going dark for an hour inside the same session that spent
   two days fixing that failure shape elsewhere. It reports real state, never fabricated
   progress. When no fleet work is active, no ticker is required.

## I-23

**Budget from task shape, not tier default (T-056)** — verbatim, v0.9 lines 476-483:

8c. **BUDGET FROM TASK SHAPE, NOT TIER DEFAULT (fix #14, same incident).** `max_turns` is set at
   intake from what the task must actually DO, not from `worker_defaults`. Any contract whose DoD
   includes running a full test suite, rebuilding assets, writing docs AND driving a PR to merge
   is a **≥70-turn** task however small its diff — the PR/CI/merge tail alone costs 10-15 turns.
   T-056 was a ~40-line fix budgeted at 40 turns; it wrote correct code and died one turn short of
   running the suite. On a turn-cap death, RESUME INTO THE SAME WORKTREE with a raised budget
   (the prompt must name the branch, the uncommitted files, and forbid restarting from scratch) —
   never relaunch from origin/main and redo finished work.

## I-24

**Reconcile, foreign-machine claims (T-060), turn-cap auto-resume (T-179)** — verbatim, v0.9 lines 485-508:

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
   **Turn-cap AUTO-RESUME (owner-approved 2026-08-09; extended 2026-08-17):** a result JSON
   with subtype `error_max_turns` is NOT routed to CHECK and NOT treated as a death —
   AUTO-RESUME, no owner interaction: (a) edit the contract's `budget.max_turns` to
   min(2x current, 200) with a one-line note, (b) append the resume to `status_log`,
   (c) relaunch INTO THE SAME WORKTREE with a prompt that names the branch + the uncommitted
   files and FORBIDS restarting from scratch (8c). Auto-resume up to a **lifetime total of
   THREE runs per task** (initial run + two auto-resumes) — a THIRD cap-death parks the task
   labeled `QUALITY/SCOPE-SUSPECT` with an owner card: at that point the task is oversized or
   ill-scoped for its budget, not merely under-funded, so it stops for a scope rethink, never
   for a budget approval. (T-056 would have self-healed instead of sitting dead 35 min; T-179
   sat PARKED ~2h on 2026-08-17 waiting for a resume-budget approval on work that was ~90%
   done — this is the fix.)

## I-25

**Sweep reconciliation rules — T-178 / T-179 (2026-08-18)** — verbatim, v0.9 lines 510-526:

**SWEEP RECONCILIATION RULES (2026-08-18, 3-incident codification):** the fleet's lesson
lifecycle mandates a lesson recurring 3x becomes a deterministic rule, never a 4th prose
reminder — this class (a sweep flipping a task's queue state against the origin session's
newer, truer state) hit that bar in 24h. MUST rules for every sweep, before flipping ANY
contract's state (rename park/claim/done):
1. **Newest signal wins.** A sweep MUST read the contract's NEWEST timestamped `status_log`
   entry AND the bus git log for that file before acting — a stale body note never overrides
   a newer rename. Incident: T-179 was re-parked from a stale body note that overrode a newer
   claim rename.
2. **A live origin's activity blocks reclaim.** A sweep MUST NOT reclaim/re-state a contract
   whose origin session pushed bus activity within the last 2 hours, except the
   provably-dead-origin rescue path (STEP 7 exception (a) above). Incident: T-178 — a sweep
   claimed a live origin's deliberately-held task.
3. **Unmerged PR blocks `.done`.** A contract whose dod/status references an unmerged PR is
   NEVER renamed `.done` — work-complete-awaiting-land stays `.claimed` (or `.parked` with an
   external-blocker reason); `.done` REQUIRES the PR merged. Incident: T-179 was renamed done
   while its PR was still OPEN.

## I-26

**Standing budget pre-approval (owner 2026-08-17)** — verbatim, v0.9 lines 528-537:

**STANDING BUDGET PRE-APPROVAL (owner 2026-08-17):** retries, cap-resumes, budget raises, and
tier-escalation costs are pre-approved and never owner-gated — bounded only by (a) the
Anthropic plan's own weekly/monthly limits, which are not session-readable so the platform
itself enforces them, and (b) the existing daily spend ceilings, which pause + notify
automatically rather than ask. Never stop a task to ask "can I spend more?" — the only budget
question that still reaches the owner is the third-cap-death `QUALITY/SCOPE-SUSPECT` park
above, and that is a scope question, not a budget one. NEW recurring third-party spend (a new
paid API, a new subscription) and owner-set product budget ceilings (e.g. a $30/mo watchdog
cap) remain owner-gated — this grant covers running Anthropic-model work harder, not opening
new spend categories.

## I-27

**Invocation log semantics (v0.8.1, verifier finding MEDIUM-6)** — verbatim, v0.9 lines 539-550:

**INVOCATION LOG — a recurrence detector, not the only evidence (semantics fixed v0.8.1,
verifier finding MEDIUM-6):** at the end of EVERY intake turn (any mode), append ONE line to
`GWD\INVOCATIONS.log`: `<UTC ISO timestamp> | <session-id>@<machine> | cwd-repo=<registry key
or none> | tasks_parsed=<n> | tids=<value>`. The `tids=` field distinguishes legitimate
no-new-T-id outcomes from the defect: comma-separated T-ids (dispatched) · `dup:T-xxx`
(dedup gate converged on an existing task) · `gate-pending` (still inside the 95% grill,
one line per turn) · `none` (parsed a task, produced no T-id and no legitimate reason —
THIS alone is the inline-execution defect, findable with one grep). Known limit: a session
that never invokes the skill writes no line at all — the CLAUDE.md rule + guard hook are
the backstop for that path, this log only proves what invoked sessions did. The weekly
fleet audit greps for `tids=none`; a hit becomes a `LESSON(OPEN):` entry in
PATTERNS-SEEN.md.

## I-28

**Origin-session reporting affinity (owner requirement 2026-08-10)** — verbatim, v0.9 lines 554-563:

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

## I-29

**Audit-gap fixes from the T-014 self-review (2026-07-18)** — verbatim, v0.9 lines 565-579:

**AUDIT-GAP FIXES 2026-07-18 (from the T-014 self-review):**
- **Worker cwd:** launch the worker in the TARGET repo's dir (or a neutral working dir like the app's
  deploy path) — NEVER the hub repo dir. Running in the hub made a worker inherit hub governance and
  emit the `*Enhanced:*` ceremony in its report (leak). The dispatch cwd is the target, not `claude-best-practices`.
- **Checker is MANDATORY and AUTO-CHAINED, never manual.** STEP 7 is not optional and not owner-triggered:
  every task automatically spawns a SEPARATE checker agent (`evidence: required` is the ONLY accepted value since v0.8.1 — lint blocks anything else; a task too small to verify is batched, never unverified) (in a
  neutral dir) that re-verifies a sample from SOURCE before the task is reported done. On T-014 the checker
  CONFIRMED a real bug (a duplicate DB row) AND REFUTED a false one (worker claimed "price data missing" —
  it was present under a differently-named column). A worker report without a checker verdict is INCOMPLETE.
- **Evidence = raw pulls + report + checker verdict**, all saved to `GWD\evidence\<date>-<id>\` — not just the
  final prose. The raw data is what lets the checker (and owner) independently re-examine claims later.

The worker's "done" claim is input, not truth. Dispatch a CHECKER against the worker's output;
tier = **opus when the contract's model is opus, sonnet otherwise** — fix #11: the checker is
never weaker than the maker.

## I-30

**Checkers must be headless — the T-141 90-minute stall (2026-08-16)** — verbatim, v0.9 lines 581-601:

**CHECKERS MUST BE HEADLESS (owner-reported live defect 2026-08-16 — the T-141 stall):** the
unattended checker path is the SAME headless wrapper mechanics as a worker, never an in-session
`Agent()` — an in-session Agent renders a permission dialog on any tool call outside its
allowlist, and with the owner away that dialog blocks silently with no heartbeat and no timeout.
**Incident: on 2026-08-16, T-141's checker (dispatched as an in-session `Agent()`) stalled ~90
minutes on a permission dialog while the owner was away** — the fleet's fail-at-intake principle
(collect approvals while the owner is present, STEP 4) was silently violated because the checker
path was never covered by it; workers were already immune via headless `bypassPermissions`, but
checkers were not. Dispatch every unattended checker exactly like a worker:
- Launch via `claude -p --model <tier> --permission-mode bypassPermissions --output-format json`
  through `GWD\worker-wrapper.ps1` (same wrapper as STEP 6 item 8), writing a heartbeat file
  `T-<id>C.hb` (the `C` suffix distinguishes it from the worker's own `T-<id>.hb` so the two
  death-detection tracks never cross-contaminate, per the T-068 heartbeat-collision lesson).
- Arm a terminal-state watcher in the SAME turn as the checker launch (identical rule to STEP
  6.8b — non-empty result JSON, `EXITED` heartbeat, or staleness past
  `settings.heartbeat_stale_after_seconds`; silence is not success).
- The checker prompt carries the WORKER-MERGE GUARD standing line verbatim (STEP 5) — a checker
  re-deriving the WORKER-MERGE GUARD predicate (below) never merges or closes a PR itself either.
- **In-session `Agent()` is allowed ONLY when the owner is present and the dispatcher explicitly
  states so** (e.g. "running the checker in-session — owner online") — never as the silent
  default for an unattended run.

## I-31

**Tier receipt + merge-guard check + the deliverable checker table** — verbatim, v0.9 lines 603-622:

FIRST run the deterministic tier receipt
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

## I-32

**Evidence = re-derivation artifacts, not attestations (fix V4)** — verbatim, v0.9 lines 624-635:

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

## I-33

**Root-cause close-out (STEP 3.5 enforced at check time)** — verbatim, v0.9 lines 637-641:

**ROOT-CAUSE CLOSE-OUT (STEP 3.5, enforced here):** no task is reported done until the
checker verdict carries the SWEEP result for every defect fixed ("fixed 1 of N found" /
"swept, no other instances") and, on a second-occurrence shape, names the MECHANISM installed
plus its `PATTERNS-SEEN.md` lesson line. A close-out claiming a class fix whose only artifact
is new prose is INCOMPLETE.

## I-34

**Lessons live in PATTERNS-SEEN.md (owner 2026-08-15)** — verbatim, v0.9 lines 643-651:

**LESSONS LIVE IN PATTERNS-SEEN.MD (owner 2026-08-15 — deliberately NOT a separate
LESSONS.md; the bus already has enough logs):** every failure, park, reroute, or
checker-refutation appends a `LESSON(OPEN): <mistake> → <root cause> → <rule>` line to
`GWD\PATTERNS-SEEN.md`. Lifecycle: `LESSON(OPEN)` → `LESSON(CODIFIED → <where>)` when it
becomes a rule/gate → `LESSON(ARCHIVED)`. Intake sessions read ONLY the `LESSON(OPEN):`
lines, newest 20 max — never the whole file. A lesson recurring 3× MUST be codified into a
deterministic gate (`contract-lint.py` / `preflight-guard.ps1` / this skill), never left as
a 4th prose reminder. Scope boundary: fleet-mechanics lessons only — hub-repo lessons stay
in the hub's `.claude/tasks/lessons.md`.

## I-35

**Terminal-state cards — fallback-only for session-origin tasks (2026-08-10)** — verbatim, v0.9 lines 653-665:

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

## I-36

**Parked digest (owner-approved 2026-08-09)** — verbatim, v0.9 lines 667-671:

**PARKED DIGEST (owner-approved 2026-08-09):** parked must never mean forgotten. The
deterministic weekly `GWD\parked-digest.ps1` (keeper-tick step, self-gated like the
feature sweep) cards the owner every `*.parked.md` with age + reason. The owner replies
`<T-id> retry` (SWEEP re-queues at the same tier) or `<T-id> drop` (SWEEP renames to
`<T-id>.dropped.md`); the sweep processes these replies like any owner answer.

## I-37

**Artifact placement (rule 2026-07-18)** — verbatim, v0.9 lines 673-680:

## ARTIFACT PLACEMENT (rule 2026-07-18 — owner question)
Where a created artifact lives is determined by WHAT it is, not where the fleet runs:
- **Project-SPECIFIC artifact** (a tool/script/config for ONE app — e.g. an IPODhan audit tool) → lands
  IN that project's repo via a PR (versioned with the app, discoverable by its team, covered by its CI).
  NEVER the bus or hub. (Defect fixed: ipo-audit.py was wrongly put in the bus → moved to IPODhan #112.)
- **Fleet-GENERIC machinery** (dispatcher, keeper, contract-lint, bus-sync, guards) → the hub / bus scripts.
- **Fleet runtime STATE** (queue, ledger, evidence, questions) → the GetWorkDone bus only.
Litmus test before saving: "would the target project's team want this in their repo?" If yes → their repo.

