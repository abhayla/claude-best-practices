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

Root: `D:\Abhay\VibeCoding\tasks\` (sibling of the repos, like GLOBAL.md — durable, un-committable, single-writer-friendly):
- `inbox/` — incoming items (`source`, `repo`, `type`, `evidence` frontmatter)
- `queue/` — one contract file per task; **atomic claim by rename** `<id>.queued.md → <id>.claimed.<session>.md` before any dispatch (G2)
- `OWNER-QUESTIONS.md` — parked blockers: `[task-id] question · recommended answer · what unblocks`
- `PATTERNS-SEEN.md` — repetition tally (3× → skill-factory proposal)
- `heartbeats/` — per-worker PID + last-tick file (G3)

Evidence store: `D:\Abhay\VibeCoding\task-evidence\<YYYY-MM-DD>-<task-id>\` + append-only `LEDGER.md`. Retention: prune >90 days; an evidence-write failure is a HARD task failure, never a skip (G20).

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
- **Deploy safety (G6/G9):** contract records the pre-deploy known-good ref; post-deploy destination probe; a break right after an auto-deploy → REVERT to recorded ref first, forward-fix second. Dispatcher computes deploy tier from the PR diff (auth/payment/DNS/migration paths → forced hold) regardless of intake classification.
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
- **Unattended operation (G8):** the sweeper that runs with no session open is a **local Windows Task Scheduler job** launching `claude -p` (machine must be awake — stated constraint). Cloud Routines are notification/filing only; they cannot reach this disk.

## Phases

**Phase 1 — MVP front door (~1 session)**
- [ ] `/get-work-done` SKILL.md v1: sequential single-worker flow end-to-end (intake→gate→clarify→contract→dispatch→check→report), atomic claim, repo-identity assert, refusal branch.
- [ ] `D:\Abhay\VibeCoding\tasks\` + contract template + inbox convention; `task-evidence\` + LEDGER.
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
- [ ] Inbox sweep at session start + local Task Scheduler unattended sweep (NOT a cloud Routine); break-fix bridges (standing-goals, CI-red, Gatus→inbox); Cowork drop convention documented in GLOBAL.md; PROPOSED approval flow (morning digest + daytime ping).
- Verify: one synthetic item per source A–D routes to the correct authorization path; break-fix auto-dispatches, proposals wait.

**Phase 6 — Codify + dogfood + graduate**
- [ ] PATTERNS-SEEN 3× trigger → skill-factory proposal; dogfood 3 real owner tasks end-to-end; /learn-n-improve capture; then (owner-approved) consider G6 plugin packaging — NOT before dogfood proves it.

## Gap audit (2026-07-15 — self-review + context-blind opus red-team, 20 findings, all HIGH/MED accepted)

Mitigations are baked into the architecture above, keyed G1–G20: G1 answer return path · G2 atomic queue claim · G3 heartbeat/liveness + reconcile · G4 maker≠checker evidence · G5 break-task dedup · G6 revert-first rollback · G7 fix-loop circuit breaker · G8 local (not cloud) unattended sweeper · G9 diff-enforced deploy tier · G10 fleet budget breaker · G11 cancel verb · G12 priority lanes · G13 per-repo merge serialization · G14 secrets discipline · G15 refusal ≠ success · G16 blast-radius gate · G17 alert debounce · G18 repo-identity assert · G19 queue outside git · G20 evidence retention + write-failure = task failure.

## Pre-mortem (top residual risks)
1. **Headless permission walls** in downstream repos — Phase 1 dry-run exists to hit this first; per-repo `settings.local.json` allowlists kept minimal (over-broad allowlists are their own loophole).
2. **Dispatcher context rot** — all state on disk; any session resumes the fleet from `tasks\queue\`.
3. **Machine-awake dependency** for unattended sweeps — stated constraint; revisit cloud execution only if it bites in practice (YAGNI).
4. **Fable burning tokens on routine work** — hard-coded dispatch tiers + weekly `cost_ledger.py --report` audit.
