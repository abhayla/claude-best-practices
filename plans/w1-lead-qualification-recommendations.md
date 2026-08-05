# W1 (Lead Qualification & Follow-up) recommendations — autonomous implementation plan

**Status:** PENDING owner answers (upfront batch) → then fully autonomous execution
**Origin:** andreysuperior capture review, Workflow 1 deep-dive (2026-08-03 session; capture:
`docs/process-improvement/sources/2026-05-24-andreysuperior-7-claude-n8n-business-automations.md`)
**Program rule:** this is the per-workflow review program (W1 of 7); W2–W7 get their own review
turns and, if approved, their own plan sections appended here or sibling plan files.

## Scope (from the W1 recommendation table)

| Track | Item | Target repo (fleet registry key) | Verdict at review |
|---|---|---|---|
| A | H1+H2 — numeric relevance rubric (1–10, anchored) + threshold-gated Notifier alert for discoveries/captures | `claude-best-practices` | Adopt now |
| B | D1+D2 — 1–10 lead-scoring node + hot-lead owner alert (Notifier) in the PIFS phase-1 follow-up engine | `wati-project` | Adopt now |
| C | D4-measurement — first-response-lag measurement inside the 24h window (NO auto-reply) | `wati-project` | Adopt measurement now |
| D | D5-measurement — GoRefer lead-volume-vs-manual-capacity analysis (read-only; scoring node only if volume justifies) | `gorefer` | Adopt later, measure first |
| E | Deferred: D3 (Zoho CRM enrichment, post engine v1) · generic `inbound-triage` core pattern (promote at 2nd caller) · queue-SLA ladder (belongs to W3's review) | — | Not in this plan's execution scope |

## Execution route — how each track runs fully autonomously

Per the premium-session routing rule (this session = Fable; get-work-done STEP 3 Fable-session
exception), NOTHING executes inline here. Every track becomes a get-work-done contract:
intake → scout → contract (`/goal-creator` + dispatcher fields) → contract-lint →
preflight-guard → background worker in the target repo's own directory → independent checker
with re-derivation evidence → PR gated on CI.

Fleet mechanics verified this session (not assumed):
- `GWD\settings.json repo_registry` contains all three targets with paths + remotes (read 2026-08-04).
- Local dispatch uses `-StateRoot D:\Abhay\VibeCoding\GetWorkDone` (T-038 lesson — mandatory off the VPS).
- `wati-project` + `gorefer` are PRIVATE repos → workers watch `gh pr checks` and merge on green;
  never arm auto-merge (free-plan, no branch protection — standing finding).
- `wati-project` canonical source = fleet VPS `C:\Abhay\5Wealths\Wati-Project`; deploy = file-copy +
  restart scheduled task (no git on the box) — the contract must include the deploy leg explicitly.

### Track A — hub: rubric + threshold alert (model: sonnet)

Steps the worker executes:
1. Define the 1–10 relevance rubric with anchors (9–10 net-new mechanism; 7–8 additive to an
   existing pattern; 5–6 corroboration only; 3–4 tangential; ≤2 no engineering content) in
   `docs/process-improvement/README.md` (new section) and reference it from the INBOX header.
2. Add `relevance_threshold` (default 8) to the scan config (`config/settings.yml` or a scoped
   key in `config/topics.yml` — worker picks the config-SSOT-consistent spot).
3. Extend `scripts/discovery_to_issue.py`: when a discovery's score ≥ threshold, POST a P2 to the
   Notifier (`GLOBAL.env NOTIFIER_URL/NOTIFIER_KEY`; off-VPS = nginx proxy URL per GLOBAL.md §2).
   FAIL-OPEN: alert failure logs a warning, never fails the scan run (no-silent-failure ≠
   fail-closed on a side channel).
4. Wire secrets for CI: `gh secret set NOTIFIER_URL / NOTIFIER_KEY` on the hub repo (values from
   GLOBAL.env — agent-executable, never committed) + pass them in `scan-internet.yml` env.
5. Tests: unit tests for threshold gating + alert payload with HTTP mocked; below-threshold case
   asserts NO call. Full local CI replication before PR.

DoD predicates: rubric doc exists with 5 anchor bands; threshold read from config (not
hardcoded); alert fires in a mocked ≥threshold run and not below; scan run stays green when
Notifier is unreachable; secret-scan clean; CI green on PR.
Effect-at-destination probe (checker): one REAL dry-run POST to the Notifier with a test
dedupeKey, verified received (Notifier log/Telegram delivery), then cleaned up.
Rollback: revert PR; no data migration, no external state beyond idempotent gh secrets.

### Track B — Wati-PIFS: scoring node + hot-lead alert (model: sonnet)

Executed per owner's Q2 answer (route into the in-progress phase-1 engine build vs independent
dispatch vs hold). Content either way:
1. Add a `leadscore` design card to the PIFS conversation-map SSOT (same card discipline as
   `twhotlead`/`whstalled`): Claude scores each qualifying inbound lead 1–10 on the PIFS rubric
   (intent / product fit / urgency — final rubric text owner-approved via Q3 or during the
   engine's existing copy sign-off gate), score written to a Wati contact attribute
   (`lead_score`, `lead_score_at`).
2. Extend the `twhotlead` path: score ≥ threshold (Q3) → Notifier alert to owner (channel per Q3)
   carrying name, number, score, extracted intent line, and conversation link.
3. Engine-side implementation on the VPS engine codebase + file-copy deploy + scheduled-task
   restart; end-to-end test with a designated test contact (allowlist discipline from
   `wati-send-and-verify-delivery` — no real customer touched in testing).
4. NO customer-facing behavior change in this track (scoring + owner alert are internal); the
   engine's existing owner gates (EN+HI copy sign-off) stay untouched.

DoD predicates: design card present in the SSOT map + manifest; scoring runs on a test inbound
and writes the attribute (verified via `wati_get_contact`); a ≥threshold test lead produces an
owner alert verified DELIVERED at the channel (not HTTP-200-accepted); deploy leg completed
(file-copy + task restart + post-restart health check); no Wati dashboard flow edits required
(engine-side only) — if one becomes required, the task PARKS with an owner card (declared
contingency, see inventory below).
Rollback: file-copy restore of prior engine files (capture KNOWN-GOOD first, gorefer-style
revert-first discipline).

### Track C — Wati-PIFS: first-response-lag measurement (model: haiku|sonnet)

1. Script in `wati-project` pulling the last 30–60 days of conversations via the Wati API,
   computing first-inbound → first-outbound lag distribution (median/p90) per conversation
   within the 24h window.
2. Output: a small report committed to the repo + a one-time Notifier FYI with the headline
   numbers. Read-only against Wati; zero message sends.
DoD: report exists with per-band distribution + method note; numbers re-derived by the checker
from a re-pulled sample (data deliverable procedure).

### Track D — GoRefer: volume-vs-capacity measurement (model: haiku|sonnet)

1. Read-only analysis in `gorefer`: leads/week (excluding garbage-flagged), current manual
   triage throughput proxy (status-change timestamps), backlog age distribution.
2. Output: recommendation record in the repo (docs/) — "scoring node justified: yes/no + bar",
   honoring COORDINATION.md protocol (spec-first; ambiguity → QUESTION entry, never invent).
DoD: report with re-derivable numbers (checker re-pulls sample); NO code/schema changes.

## Owner-input inventory — COMPLETE, all needed NOW, nothing after kickoff

Decisions (the one question card, this turn):
1. **Scope** — which tracks run (recommend all four A–D).
2. **Track B route** — into the in-progress engine build vs independent get-work-done dispatch
   vs hold until engine v1 (recommend: queue into the engine build — avoids two actors on one
   mid-flight design).
3. **Hot-lead defaults** — threshold + alert channel (recommend 8/10 + Telegram, the fleet's
   proven card channel; WhatsApp available via Notifier if preferred).
4. **Track C posture** — measurement-only vs also draft a fast-ack template for future sign-off
   (recommend measurement-only; auto-ack is a customer-facing product decision + Meta template
   approval, deferred until data says it matters).

Declared contingencies (named blockers that COULD surface a mid-run owner card — listed now so
none is a surprise; each parks its task, never freezes the rest):
- **Wati dashboard-only wiring**: if Track B turns out to need a keyword/chatbot flow edit
  (dashboard-only surface, no API), the task parks with an owner card; VPS-Chrome automation is
  attempted first (owner-authorized surface per standing directive), manual click-through is the
  last resort.
- **Meta/WhatsApp template approval**: only if Q4 = draft template AND you later approve sending —
  approval latency is Meta's, not labor; flagged now.
- **GLOBAL.env sync**: no secret changes are expected; if one becomes necessary, per the standing
  fleet rule the owner syncs GLOBAL.env copies by hand (fleet never auto-edits them).
- **Credentials**: none needed from you — gh CLI authenticated; Notifier/Wati/Cloudflare keys
  already in GLOBAL.env/VPS `.env` per §2; Zoho NOT needed (D3 deferred).

## Verification & anti-regression (every track)

- maker ≠ checker: independent checker re-derives evidence per the deliverable-type procedure;
  evidence folder + LEDGER line; tier receipt via `verify-model-tier.py`.
- Effect-at-destination: alerts verified DELIVERED (Notifier log / channel), never HTTP-accepted;
  Wati attribute verified by re-reading the contact; deploys probed live post-restart.
- All landings PR + CI-gated; private repos watch-then-merge, never auto-merge armed.

## Standing self-improvement clause (owner directive 2026-08-04)

Any misfire during this program — routing, contract, worker, checker, OR a gap in the
get-work-done skill itself — gets, in the SAME session it is observed: (1) a
`mistake → root cause → rule` entry in `.claude/tasks/lessons.md`; (2) a concrete fix to the
skill/settings/lint/guard (not prose advice); (3) if the fix is in the hub skill body, it lands
via the normal PR gate. This extends the existing model-cost-routing misfire rule to the whole
implementation program.

## Execution order

1. Owner answers the 4-question card (this turn).
2. Dispatch Track A immediately (hub, no dependencies).
3. Dispatch Tracks C + D in parallel (read-only, different repos).
4. Track B per Q2 route (engine-build queue item or dispatched contract).
5. On completion: per-task report (outcome, PR, evidence path, tier/cost) + this plan updated
   with results; deferred items (E) stay parked until their trigger.
