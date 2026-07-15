# /get-work-done — the "mother hub" central work dispatcher

**Status:** APPROVED design (gap-audited), phased build pending owner go
**Skill name:** `/get-work-done` (plain-English naming rule; renamed from working title `/task-intake`, 2026-07-15)

**Owner decisions locked (2026-07-15):**
1. No hard quota cap (Max plan). Invariant = cheapest **correct** model per task (`.claude/rules/model-routing.md`). Soft concurrency default 6 — priority-laned, not global (see mitigations).
2. ALL downstream work lands via **PR + CI-gated auto-merge** (branch-lifecycle plugin already installed in all 5 downstream repos). Never direct-to-main.
3. Daytime = **09:00–21:00 IST**. Blocker questions ping via **Notifier gateway → WhatsApp** (P2, deduped; `GLOBAL.md` §2). Outside window → queue silently for morning.
4. Deploy gate two-tier: **auto-deploy re-deploys** of already-live apps; **hold for one-line approval** on first deploys / DNS / new domains / auth-payment surfaces. Approval-class items collected **UPFRONT** in the intake question batch. Tier is enforced from the ACTUAL diff, not the worker's claim (mitigation G9).

**Research basis (fetched 2026-07-15; reports in session):** background subagents GA + default (CC v2.1.198); `claude --bg`/`claude agents` fleet (research preview, local-only); headless `claude -p` run **in the target repo's dir** loads that repo's own CLAUDE.md/plugins (`--add-dir` grants file access only, NOT config); Routines = cloud, cannot touch this machine's disk; pricing Haiku $1/$5 · Sonnet $2/$10 (→$3/$15 Sep 1) · Opus $5/$25 · Fable $10/$50 per MTok; MSR '26 (33,596 agent PRs): Claude Code 59% merge rate → PR+CI gating is load-bearing; context-rot mitigation = fresh session per task + on-disk state (ralph pattern).

## Intake sources — one central queue, four origins

Every task enters the SAME queue via a producer-agnostic inbox (anything that can write a file can file work — Cowork sessions, cron, hooks, monitors, a human note).

| Source | Example | Authorization |
|---|---|---|
| **A. Owner ask** | "/get-work-done add X to IPODhan" | Approvals batched at intake (decision 4) |
| **B. Break-fix** | live app down / CI red / standing-goal predicate fails | **Pre-authorized** — auto-dispatch P1 fix contract (debounced, deduped, loop-capped — G5/G7/G17); PR + evidence still required; FYI ping |
| **C. Cowork scout → feature for existing app** | scheduled task proposes an enhancement | `PROPOSED` → owner one-line approval (daytime ping / morning digest) → contract |
| **D. Cowork scout → new app** | scheduled task proposes a new product | `PROPOSED` → full strategic gate: BA discovery + owner approval BEFORE any build (standing rule) |

Break-detection feeds (wired progressively): Gatus health checks (VPS portfolio), `standing-goals.yml` sentinel, CI-red PRs from `auto-pr-reconcile`, Notifier-relayed alerts.

## On-disk state — ALL outside every git repo (G19)

Root: `D:\Abhay\VibeCoding\GetWorkDone\` (sibling of the repos, like GLOBAL.md — durable, un-committable, single-writer-friendly):
- `inbox/` — incoming items (`source`, `repo`, `type`, `evidence` frontmatter)
- `queue/` — one contract file per task; **atomic claim by rename** `<id>.queued.md → <id>.claimed.<session>.md` before any dispatch (G2)
- `OWNER-QUESTIONS.md` — parked blockers: `[task-id] question · recommended answer · what unblocks`
- `PATTERNS-SEEN.md` — repetition tally (3× → skill-factory proposal)
- `heartbeats/` — per-worker PID + last-tick file (G3)

Evidence store: `D:\Abhay\VibeCoding\GetWorkDone\evidence\<YYYY-MM-DD>-<task-id>\` + append-only `LEDGER.md`. Retention: prune >90 days; an evidence-write failure is a HARD task failure, never a skip (G20).

## Cross-cutting principle — FAIL AT INTAKE, NOT AT MIDNIGHT (owner directive 2026-07-15)

Every precondition verifiable early is verified DURING INTAKE while the owner is present — repo path + remote identity, branch protection + secret-scan gates on the target, credentials/tools present on the executing machine, deploy-tier approvals, anything abort-capable. Questions raised by these checks are asked IMMEDIATELY in the intake batch. The same checks re-run at dispatch/runtime only as a cheap last-line guard against state that changed since intake — runtime must never be the FIRST time a knowable problem surfaces. Applies to every guard in this plan, present and future.

## Architecture

- **`/get-work-done`** (`.claude/skills/get-work-done/SKILL.md`, hub-only) — the front door: INTAKE → GATE → CLARIFY (batched, incl. approval-class) → CONTRACT → DISPATCH → CHECK (maker≠checker) → REPORT.
- **Complexity gate = blast radius, not file count** (G16): trivial = no auth/payment/config/migration/deploy paths touched AND no unknowns → do now; else decompose. A "trivial" task that turns deep mid-flight re-enters intake as a full contract.
- **Contract** fields: DoD, target repo **path + expected `git remote` URL** (asserted before dispatch — abort on mismatch, G18; incl. the known trap calculatekaro → `..\calculator`), model tier + rationale, budget caps (turns/time), priority (P1 break-fix > P2 owner > P3 proposals), deploy tier, approvals granted, status log.
- **Dispatch** = background Bash wrapper: `cd <target-repo> && claude -p "<contract>" --model <tier> --max-turns <cap> --output-format json`, wrapper writes heartbeat ticks. Parse `stop_reason` from JSON — a refusal is NOT success; reroute to opus and continue (G15). Same-repo tasks serialize; different repos parallelize. **P1 always admitted** even at the soft cap (G12).
- **Model routing:** haiku = classification/extraction · sonnet = DEFAULT (explicit brief + machine-checkable gate) · opus = deep debugging/architecture + preemptive for security-category · Fable NEVER dispatched for routine work. Escalate one tier after 2 supervised failures.
- **Maker≠checker (G4):** the worker never writes its own ledger entry. The dispatcher (or a checker agent) re-runs the gate against the worker's PR, executes the verify-effect-at-destination probe, captures the screenshot, and writes LEDGER. CI is the merge arbiter; the checker is the evidence arbiter.
- **Merge serialization per repo (G13):** downstream branch protection requires up-to-date branches (or merge queue); a second green PR re-runs CI against the post-merge base before its auto-merge arms.
- **Stuck protocol:** budget caps → 2 structured attempts (/fix-loop → /systematic-debugging) → PARK: escalation report + OWNER-QUESTIONS.md + daytime ping; fleet continues. **`cancel` verb** (G11): mark contract cancelled, kill worker PID via heartbeat wrapper, close its PR.
- **Reconciliation at every hub-session start (G3):** contracts `claimed/dispatched` with a dead PID or stale heartbeat → provably terminate, then re-dispatch; live PID → leave alone (idle ≠ dead).
- **Fleet budget circuit breaker (G10):** daily aggregate token/USD ceiling checked at dispatch admission (cost_ledger data); on rate-limit responses, central backoff — no per-worker retry storms.
- **Deploy safety (G6/G9 — G9 LOCKED 2026-07-15, owner-delegated):** contract records the pre-deploy known-good ref; post-deploy destination probe; a break right after an auto-deploy → REVERT to recorded ref first, forward-fix second. Dispatcher computes deploy tier from the PR diff (auth/payment/DNS/migration paths → forced hold) regardless of intake classification — policy enforced by the controller from observed artifacts, never agent self-attestation.
- **Break-fix guards:** debounce = 2 consecutive failed probes before filing (G17); task-level dedup key repo+failure-signature at inbox promotion (G5); circuit breaker = 2 auto-fixes on the same target in 24h → freeze target, escalate P1 park (G7).
- **Answer return path (G1):** every ping carries the task-id; answers land via (a) any hub session, or (b) the morning sweep reading WhatsApp replies through the Wati MCP (`wati_get_messages`) and appending to OWNER-QUESTIONS.md. A park resolves only when an answer is IN the file.
- **WhatsApp question format (owner requirement 2026-07-15):** every question rendered like a Cowork/AskUserQuestion card — numbered options, the recommended one FIRST and marked `(Recommended — <one-line why>)`, single- or multi-select stated per question. Reply protocol is deterministic: `<task-id> <option-number(s)>` (e.g. `42 1` or `42 1,3` for multi); free text after the number = "Other" with notes. Template:
  `[T-042 · IPODhan · blocker]`
  `Q: Which auth provider for login?`
  `1. Firebase Auth (Recommended — already used in KKB, free tier)`
  `2. Supabase Auth`
  `3. Custom JWT`
  `Reply: 42 <n>  (this one: pick ONE)`
  v1 = plain text numbered list via Notifier; OPTIONAL later upgrade to Wati interactive list/button messages (max 3 buttons / 10 rows) only if text replies prove error-prone (YAGNI).
- **Secrets (G14):** contracts reference secrets by path only (never inline); secret-scan inbox/queue/evidence before any indexing; verify each downstream repo's secret-scan gate as a Phase-1 prerequisite check.
- **Unattended operation (G8, revised 2026-07-15 owner input):** the sweeper is a dedicated **fleet-keeper session running `/loop`** (built-in) — `/loop 20m /get-work-done sweep`; each tick sweeps the inbox (**inbox files ARE the flag** — no separate flag state), claims atomically, dispatches. Task Scheduler keeps ONE job: restart the fleet-keeper at boot. Cloud Routines remain notification/filing only (cannot reach local disk). Idle ticks cost a few tokens — acceptable; pause the loop when the queue has been empty > N hours (resume at next session or boot).
- **Worker pools (owner addition 2026-07-15) — run workers where nothing sleeps:**
  | Pool | Machine | Routed work |
  |---|---|---|
  | L | Local Windows PC | default while attended |
  | W | Windows VPS `103.118.16.189` | IPODhan/AlgoChanakya tasks (apps hosted there) + unattended hours |
  | H | Hostinger VPS `72.61.240.224` | firekaro/RFP/calculatekaro/static-site tasks + unattended hours; Notifier local |
  Routing: app hosted on a VPS → prefer that pool; overnight → VPS pools by default. Dispatch transport: SSH from the fleet-keeper (existing keys); heartbeats per pool, fetched over SSH. Per-VPS one-time setup: Claude Code CLI + **owner-entered auth token (`claude setup-token` — named human step)**, repo clones (fetch-fresh at dispatch), headless Chromium (Linux), per-project `.env` (largely present — apps already run there). Local-PC sleep stops mattering; do NOT force the PC awake (YAGNI).

## Phases

**Phase 1 — MVP front door (~1 session)**
- [ ] `/get-work-done` SKILL.md v1: sequential single-worker flow end-to-end (intake→gate→clarify→contract→dispatch→check→report), atomic claim, repo-identity assert, refusal branch.
- [ ] `D:\Abhay\VibeCoding\GetWorkDone\` + contract template + inbox convention; `GetWorkDone\evidence\` + LEDGER.
- [ ] Downstream prerequisite audit: branch protection (up-to-date-branch requirement) + secret-scan gate per repo.
- [ ] Eval per check_eval_coverage ratchet (new skill ⇒ evals day one).
- Verify: dry-run a synthetic 2-task brief (one hub, one calculatekaro); worker lands a real PR; checker (not worker) writes the LEDGER entry. **Biggest unknown retired first: headless permission walls in downstream repos.**

**Phase 2 — Parallel fleet**
- [ ] Multi-task dispatch (soft cap 6, P1 lane), heartbeat wrapper + session-start reconciliation, `cancel` verb, fleet budget admission check, TaskCreate/TaskList tracking.
- Verify: 2 concurrent repos land green PRs, zero cross-contamination; a killed worker is detected and re-dispatched exactly once; cancel kills PID + closes PR.

**Phase 3 — Question queue + pings + answer path**
- [ ] Notifier client (`projects.claude-hub`), 09–21 IST window, per-task dedupeKey, morning sweep incl. Wati-inbound answer reading.
- [ ] Question-card formatter (numbered options, Recommended-first, single/multi marker) + reply parser (`<task-id> <n[,n]>`, free text = Other).
- Verify: forced blocker → WhatsApp card arrives with numbered options (destination probe); replies `42 1`, `42 1,3`, and `42 2 use staging first` all parse correctly and unpark; night blocker → queued, no ping.

**Phase 4 — Deploy tiers + break-fix guards**
- [ ] Diff-computed deploy tier, pre-deploy ref capture + revert-first rule, debounce, dedup key, 24h fix-loop circuit breaker.
- Verify: re-deploy of a live static site auto-lands with evidence; a diff touching an auth path forces a hold despite "re-deploy" intake class; injected flapping alert files ONE task.

**Phase 5 — Multi-source intake live**
- [ ] Inbox sweep at session start + fleet-keeper `/loop` sweeper (Task Scheduler = boot-restart only, NOT a cloud Routine); break-fix bridges (standing-goals, CI-red, Gatus→inbox); Cowork drop convention documented in GLOBAL.md; PROPOSED approval flow (morning digest + daytime ping).
- Verify: one synthetic item per source A–D routes to the correct authorization path; break-fix auto-dispatches, proposals wait; fleet-keeper tick dispatches with no interactive session open.

**Phase 5b — VPS worker pools (pilot)**
- [ ] Pool H first (Hostinger — Notifier local, most sites hosted there): CLI install, owner auth token (human step, batched), repo clones, headless Chromium, SSH dispatch + remote heartbeat readback. Then Pool W (Windows VPS) same recipe.
- [ ] Routing rule in dispatch: app-hosted-on-VPS → that pool; unattended hours → VPS pools.
- Verify: one real task dispatched over SSH to Pool H lands a green PR with checker-written evidence while the local PC is OFF (the actual failure mode this phase exists to kill).

**Phase 6 — Codify + dogfood + graduate**
- [ ] PATTERNS-SEEN 3× trigger → skill-factory proposal; dogfood 3 real owner tasks end-to-end; /learn-n-improve capture; then (owner-approved) consider G6 plugin packaging — NOT before dogfood proves it.

## Gap audit (2026-07-15 — self-review + context-blind opus red-team, 20 findings, all HIGH/MED accepted)

Mitigations are baked into the architecture above, keyed G1–G20: G1 answer return path · G2 atomic queue claim · G3 heartbeat/liveness + reconcile · G4 maker≠checker evidence · G5 break-task dedup · G6 revert-first rollback · G7 fix-loop circuit breaker · G8 local (not cloud) unattended sweeper · G9 diff-enforced deploy tier · G10 fleet budget breaker · G11 cancel verb · G12 priority lanes · G13 per-repo merge serialization · G14 secrets discipline · G15 refusal ≠ success · G16 blast-radius gate · G17 alert debounce · G18 repo-identity assert · G19 queue outside git · G20 evidence retention + write-failure = task failure.

## Point-by-point lock ledger (owner walkthrough, 22 steps — 2026-07-15)
- **P1 LOCKED:** state root = `D:\Abhay\VibeCoding\GetWorkDone\` (single folder: inbox/queue/heartbeats/evidence + ledgers), local machine, outside all git repos; VPSes join as workers at 5b; queue→private-git earmarked only if a VPS fleet-keeper is wanted.
- **P2 LOCKED:** /get-work-done front-door flow (scout → blast-radius gate → ONE upfront question batch incl. approvals → contract → dispatch → report); trivial-turned-deep re-enters intake; contracts authored via the EXISTING `/goal-creator` skill (loop-engineering plugin) extended with dispatcher fields — one contract format hub-wide (owner-confirmed).
- **P3 LOCKED (amended):** day-one guards — repo-identity check, refusal≠success, atomic claim — PLUS the fail-at-intake principle: all abort-capable verifications run at INTAKE while the owner is present (questions asked immediately); dispatch-time re-checks are last-line guards only, never first detection.
- **P4 LOCKED:** downstream guard-rail verification (branch protection + required CI check + up-to-date-branch + secret-scan gate) — one-time Phase-1 audit across all 5 repos, then a cheap re-check at every intake; reversible config gaps fixed autonomously, capability gaps become intake questions.
- **P5 LOCKED:** Phase-1 exit test = two real tasks (hub + calculatekaro) through the FULL chain with checker-written evidence, zero manual interventions; permission walls found are fixed as setup (fail-at-intake).
- **P6 LOCKED:** parallel fleet — soft cap 6 (exceedable for mechanical independent work), lanes P1 break-fix > P2 owner > P3 proposals with P1 always admitted, same-repo serialized / cross-repo free, `/get-work-done status` fleet view.
- **P7 LOCKED:** heartbeat liveness — PID + ~60s tick per worker; fresh+live → hands off (slow ≠ dead); stale/dead → provable terminate + re-dispatch exactly once; 2 deaths on one task → park + escalate.
- **P8 LOCKED:** `cancel <id>`/`cancel all` (kill PID via heartbeat, close PR, record reason) + daily fleet token ceiling checked at dispatch admission (calibrated from cost_ledger data in week one), central backoff on rate limits.
- **P9 LOCKED:** Phase-2 exit = staged sabotage: (1) 2 concurrent repos, green PRs, zero cross-contamination (diff-audited); (2) mid-task kill → stale heartbeat detected, terminate, re-dispatch ONCE, auditable death→restart→done log; (3) cancel → dead within a tick, PR closed, branch deleted, nothing merges.
- **P10 LOCKED (amended):** Notifier wiring per GLOBAL.md §2 recipe (`projects.claude-hub` + thin client), Cowork-style option cards, per-task dedupeKey + batch-into-one, P2 blockers / P3 FYIs; ping windows CONFIGURABLE + MULTI-WINDOW in `GetWorkDone\settings.json` — default `["09:00-21:00"]` IST, owner may set e.g. `["09:00-11:00","14:00-18:00"]` by editing or asking; settings.json is the single fleet knobs file (windows, soft cap, daily ceiling, heartbeat interval).
- **P18 LOCKED:** producers' contract documented in GLOBAL.md (new section: inbox path + 4-field template + reply protocol + answer locations) — Cowork scheduled tasks and any future surface integrate by reading the one cross-project SSOT; no separate integration doc.
- **P17 LOCKED:** per-source authorization — owner ask → intake+dispatch; break → pre-authorized P1 + FYI; Cowork feature proposal → PROPOSED → one-line yes; Cowork new-app → PROPOSED → full BA + explicit approval; proposals EXPIRE after 14 days unapproved (archived + FYI); repeat-rejected proposal shapes fed back to the scouts.
- **P16 LOCKED:** fleet-keeper — dedicated local session on /loop (~20-min self-paced tick): sweep → reconcile heartbeats → dispatch (lanes+budget) → check finished → ping/read answers in-window; inbox files ARE the flag; pauses after N idle hours; ONE Task Scheduler job = restart-at-boot only; keeper is a cheap-tier conductor, never a worker; fully resumable from disk state.
- **P15 LOCKED:** multi-source inbox — dumb file contract (source/repo/type/evidence frontmatter), any producer may FILE (owner/monitors/Cowork/future bridges); authorization applied at PROMOTION per source rules; malformed items → one FYI + `rejected\` subfolder, never silently a task.
- **P14 LOCKED:** break-fix noise guards — debounce (2 consecutive failed probes before filing), dedup (one contract per app+failure-signature; later detections attach as evidence), circuit breaker (2nd auto-fix on one app within 24h → freeze at known-good + P1 escalation card, never a 3rd blind attempt).
- **P13 LOCKED:** rollback — last-known-good (git ref + artifact) recorded BEFORE every auto-deploy; failed probe or fresh break on that app → REVERT first, root-cause second (P1 task); forward-fix re-runs the full chain; no direct-on-server patch path; deploy + revert both ledgered.
- **P12 LOCKED (amended — sandbox domain):** two-tier deploy gate live; tier computed from the ACTUAL merged diff (G9), destination probe + evidence on every auto-deploy. NEW: owner grants sandbox domain(s) (recorded in settings.json `sandbox_domains` + GLOBAL.md when given) — the grant pre-authorizes new-app first deploys as `<app>.{sandbox}` subdomains incl. their DNS records → Tier 1 auto. Auth/payment surfaces stay Tier 2 everywhere; graduation to a dedicated domain = separate owner-initiated process. Until a sandbox domain is provided, new-app deploys remain Tier 2.
- **P11 LOCKED (amended — channel-agnostic answers):** OWNER-QUESTIONS.md is the single answer ledger; adapters: (1) any LOCAL Claude session writes directly; (2) WhatsApp via Wati sweep; (3) Telegram via the Notifier bot (same sweep pattern, added on demand); (4) Claude mobile app / claude.ai / GitHub app via a tiny PRIVATE GitHub repo mirroring OWNER-QUESTIONS.md two-way at every sweep (slice of the queue-git upgrade pulled forward into Phase 3). Same reply protocol everywhere; first answer wins across channels; unparseable replies get ONE clarify-ping, never a guess; night answers read by the morning sweep.

## Pre-mortem (top residual risks)
1. **Headless permission walls** in downstream repos — Phase 1 dry-run exists to hit this first; per-repo `settings.local.json` allowlists kept minimal (over-broad allowlists are their own loophole).
2. **Dispatcher context rot** — all state on disk; any session resumes the fleet from `GetWorkDone\queue\`.
3. **Machine-awake dependency** — largely retired by Phase 5b VPS pools; residual: the fleet-keeper's own host. Mitigation: run a second fleet-keeper on a VPS pool once 5b lands (dispatcher redundancy via atomic claims — G2 already makes double-keepers safe).
4. **Fable burning tokens on routine work** — hard-coded dispatch tiers + weekly `cost_ledger.py --report` audit.
