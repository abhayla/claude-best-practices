# Task-Intake Dispatcher — the "mother hub" front door

**Status:** APPROVED design, phased build pending owner go
**Owner decisions locked (2026-07-15):**
1. No hard quota cap (Max plan). Invariant = cheapest **correct** model per task (`.claude/rules/model-routing.md`). Soft concurrency default 6 (review-throughput, not quota) — dispatcher may exceed for independent mechanical tasks.
2. ALL downstream work lands via **PR + CI-gated auto-merge** (branch-lifecycle plugin already installed in all 5 downstream repos). Never direct-to-main.
3. Daytime = **09:00–21:00 IST**. Blocker questions ping via **Notifier gateway → WhatsApp** (P2, deduped; `GLOBAL.md` §2). Outside window → queue silently for morning.
4. Deploy gate two-tier: **auto-deploy re-deploys** of already-live apps (rollback-reversible) once full gate + evidence passes; **hold for one-line approval** on first deploys / DNS / new domains / auth-payment surfaces. **Approval-class items are collected UPFRONT in the intake question batch** so runs never stall on them mid-flight.

**Research basis (fetched 2026-07-15, both agents' reports in session):** background subagents GA + default (CC v2.1.198); nested depth 5; per-subagent `model:`/`isolation: worktree`; `claude --bg`/`claude agents` fleet (research preview); headless `claude -p` run **in the target repo's dir** loads that repo's own CLAUDE.md/plugins (`--add-dir` grants file access only, NOT config — so dispatch = spawn in the child's home); Routines for recurring cloud jobs (min 1h cadence); pricing Haiku $1/$5 · Sonnet $2/$10 (intro→$3/$15 Sep 1) · Opus $5/$25 · Fable $10/$50 per MTok. MSR '26 (33,596 agent PRs): Claude Code 59% merge rate → PR+CI gating is load-bearing. Context-rot mitigation: fresh session per task, on-disk state (ralph-loop pattern).

## Architecture (what gets built)

One hub-only skill + three on-disk stores + reuse of everything that exists:

- **`/task-intake`** (`.claude/skills/task-intake/SKILL.md`, hub-only) — the single front door. Steps: INTAKE → GATE → CLARIFY(batched, incl. approval-class) → CONTRACT → DISPATCH → VERIFY+EVIDENCE → REPORT.
- **Task contracts** — `tasks/queue/<id>-<slug>.md` (hub repo, one file per task): DoD, target repo path, model tier + rationale, budget caps (turns/time), verification requirement, deploy tier, approvals granted at intake, status log. Extends the loop-engineering goal-contract shape with `repo:` + `evidence:` fields — do NOT invent a parallel format.
- **Evidence store** — `D:\Abhay\VibeCoding\task-evidence\<YYYY-MM-DD>-<task-id>\` (OUTSIDE all repos): screenshots + test output + git SHA + PR URL + timestamp, indexed in `task-evidence/LEDGER.md` (append-only).
- **Owner question queue** — `tasks/OWNER-QUESTIONS.md` (hub repo): every parked blocker appends `[task-id] question · recommended answer · what unblocks`. Daytime → Notifier ping; morning sweep answers → unpark.

### Dispatch mechanism (the cross-project key)
Worker = background Bash: `cd <target-repo> && claude -p "<contract prompt>" --model <tier> --max-turns <cap> --output-format json` (background Bash tool → survives across turns, notifies on exit). The worker session loads the TARGET repo's own CLAUDE.md/plugins/hooks — the mother visits the kid's house, never reaches in through the wall. Same-repo tasks serialize (or worktree-isolate); different-repo tasks parallelize freely.

### Model routing at dispatch (per model-routing.md, restated for workers)
haiku = classification/extraction/format checks · sonnet = DEFAULT (explicit brief + machine-checkable gate) · opus = deep debugging/architecture/design freedom · Fable NEVER dispatched for routine work. Escalate ONE tier after 2 supervised failures. Security-category work → opus preemptively.

### Stuck protocol (owner point: "what when you get stuck")
Per worker: budget caps in the contract. On failure → max 2 structured attempts (/fix-loop → /systematic-debugging). Still stuck → PARK: write escalation-report, append to OWNER-QUESTIONS.md, Notifier ping if 09–21 IST, mark contract `parked`, **continue other tasks**. Never silent spin, never mask, never block the fleet on one child.

### Codification trigger (owner point 5)
`tasks/PATTERNS-SEEN.md` tally: task shape seen 3× → auto-propose a skill/workflow via skill-factory (proposal, owner approves per rule 5).

## Phases

**Phase 1 — MVP front door (this repo, ~1 session)**
- [ ] `/task-intake` SKILL.md v1: intake → complexity gate (trivial = ≤1 file, no deploy, no unknowns → do now; else decompose) → batched clarification incl. approval-class → contract file → SEQUENTIAL dispatch (one background worker) → evidence check → report.
- [ ] `tasks/` dir + contract template + `OWNER-QUESTIONS.md` skeleton; `task-evidence/` + LEDGER.md.
- [ ] Eval per check_eval_coverage ratchet (new skill ⇒ evals from day one).
- Verify: dry-run on a synthetic 2-task brief (one hub task, one calculatekaro task); worker lands a real PR; evidence folder populated.

**Phase 2 — Parallel fleet**
- [ ] Multi-task dispatch (soft cap 6), TaskCreate/TaskList tracking, per-worker completion notifications, same-repo serialization rule.
- Verify: 2 tasks in 2 different downstream repos run concurrently, both land green PRs, zero cross-contamination.

**Phase 3 — Question queue + daytime pings**
- [ ] Notifier client drop-in (per GLOBAL.md §2 recipe, `projects.claude-hub` block), 09–21 IST window logic, dedupeKey per task, morning unpark sweep in /task-intake.
- Verify: forced blocker → WhatsApp ping received (probe destination, not sender); night blocker → queued, no ping.

**Phase 4 — Stuck protocol + deploy tiers wired**
- [ ] Budget caps in dispatch cmd; park flow; two-tier deploy gate in contract template (re-deploy autonomy needs: app already live + same domain/infra + full gate + evidence).
- Verify: injected failing task parks after 2 structured attempts and fleet continues; re-deploy of a live static site auto-lands with screenshots.

**Phase 5 — Codification + dogfood + graduate**
- [ ] PATTERNS-SEEN tally + 3× trigger → skill-factory proposal.
- [ ] Dogfood: run 3 real owner tasks through the full pipeline; capture lessons (/learn-n-improve).
- [ ] Then consider G6 packaging as a plugin (owner-approved, one-at-a-time rule) — NOT before dogfood proves it.

## Risks (pre-mortem)
1. **Headless workers hit permission walls** in downstream repos (no interactive prompts) → contracts must carry `--allowedTools`/settings; mitigate with per-repo settings.local.json baked by Phase 1 dry-run. Biggest unknown — test first.
2. **Context rot in the dispatcher** on long intake sessions → contracts are on-disk; any session can resume the fleet from `tasks/queue/` (ralph pattern). Never depend on the mother's conversation memory.
3. **Evidence theater** — screenshot exists but wrong thing verified → LEDGER entry requires SHA + test output + the verify-effect-at-destination probe, not screenshot alone.
4. **Fable burning tokens on routine work** (owner's explicit fear) → dispatch table hard-codes tiers; session-level routing rule already forbids it; cost_ledger.py `--report` audits weekly.
