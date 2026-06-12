# GOAL — Promote the Notifier owner-alert integration into the claude-best-practices hub as a distributable pattern

**Type:** Autonomous build/propagation contract (run via `/goal`). Execute end-to-end with **zero user
input**. Every design decision is pre-made below — do not pause to ask; make the call the contract
specifies and keep going until the Definition of Done is fully met.

**Owner:** Abhay · **Created:** 2026-06-12 · **TARGET REPO:** `D:\Abhay\VibeCoding\claude-best-practices` (the hub) — NOT firekaro-planner.
**Invocation:** copy this file into `claude-best-practices/docs/goals/` (or `plans/`), then from THAT repo: `/goal docs/goals/2026-06-12-notifier-hub-pattern.md`
**Staged from:** `firekaro-planner/docs/goals/` (drafting location only — the build runs in the hub).
**Sibling contracts (run independently in their own repos):** `2026-06-12-notifier-heartbeat-watchdog.md` (Notifier) · `2026-06-12-notifier-rollout-fuel-prices.md` (consumers). This contract has NO dependency on those — it can run first or in parallel.

---

## 0. Mission

Turn FireKaro's proven owner-alert integration (`firekaro-planner/server/src/lib/owner-notify.ts` + its
detector wiring) into a **first-class, distributable hub pattern** so EVERY project — current and future —
gets a uniform way to (a) wire the Notifier gateway when deployed to production, and (b) be told to use
**Notifier for owner-alerts AND uptime heartbeats**, explicitly retiring healthchecks.io / UptimeRobot /
external pingers. "Done" = a new `notifier-integration` rule + a portable reference helper (TS + a Python
stub) + a standard CLAUDE.md "Production & monitoring" block template exist in `core/.claude/`, are
**registered in `registry/patterns.json`** so `update-practices`/`synthesize-project` distribute them, pass
the hub's own validators, and a dry-run proves the rule lands in a throwaway target project. This is a
docs/rules/templates + registry change — **no application code, no UI, no financial math.**

---

## 0.1 WORKTREE ISOLATION (first action, before §0.2)

> **First action, before any stage. Non-negotiable.** Run in a DEDICATED worktree, never the hub's primary
> interactive checkout.
> 1. **Isolate:** `root=$(git rev-parse --show-toplevel)`. If `root` is the primary `claude-best-practices`
>    checkout (not an existing `…-goal-*` worktree), create + switch:
>    `git worktree add ../claude-best-practices-goal-notifier-hub -b feat/notifier-hub-pattern` and run every
>    stage from there.
> 2. **Claim it (if the hook exists):** export `GOAL_RUN_TOKEN=notifier-hub-<nonce>`; if the repo has
>    `.githooks/pre-commit` with a `.goal-active.lock` check, write the lock
>    `printf '%s\n' "$GOAL_RUN_TOKEN" > "$root/.goal-active.lock"`. If the hub has NO such hook (likely —
>    confirm with `ls .githooks/`), note it in the progress log and proceed; the dedicated worktree is the
>    isolation. Do NOT fabricate a hook that isn't there.
> 3. **Release on exit:** final action removes the lock if written (`rm -f "$root/.goal-active.lock"`).
> 4. **Self-cleanup ON SUCCESS ONLY:** after merge `--no-ff` → the hub's default branch + push + lock release,
>    `cd <primary-root> && git worktree remove --force ../claude-best-practices-goal-notifier-hub ; git branch -D feat/notifier-hub-pattern ; git worktree prune`. On Windows `git worktree remove` may print `Invalid argument` yet still de-register — `git worktree prune` finalises it. **DEFER/HALT: keep the worktree + branch** (only release the lock).

---

## 0.2 PREFLIGHT — idempotency · NO duplication (first numbered action)

> **First action of the run, before any stage. Non-negotiable.** A parallel session may already have done
> part of this.
> 1. The hub has **no formal gap ledger** for this work — the source of truth is the code + registry.
> 2. Before building each item, check it doesn't already exist:
>    - `ls core/.claude/rules/notifier-integration.md core/.claude/templates/owner-notify.* core/.claude/templates/*production-monitoring* 2>/dev/null`
>    - `grep -n '"notifier-integration"' registry/patterns.json`
>    - `git log --oneline -20 | grep -i notifier`
>    If an item exists and matches this spec → **SKIP its build, verify-only**. If partial → build only the
>    delta. If absent → build it.
> 3. Record every skip in the final report's "skipped (already covered)" list.

---

## 0.3 PROGRESS LOG — live, cross-session-trackable

> Maintain an append-only log `docs/goals/.run/notifier-hub-pattern-PROGRESS.md` in THIS worktree (`.run/`
> gitignored — confirm/add to `.gitignore`). First line: slug · branch · worktree · start time (`date "+%Y-%m-%d %H:%M"`) · contract path · one-line mission. Append a ≤2-line entry at each stage start/done (with gate result), every DEFECT/EVENT/DECISION/RECOVERY/BLOCKER, and the final result. At run-end derive learnings → AUTO-append each notable error→fix→lesson (+gate-gap line, dedup-grep first) to `.claude/tasks/lessons.md`; PROPOSE skill/rule learnings in the final report's "LEARNINGS TO FOLD BACK" (never auto-edit a rule/skill). Final entry + final report each carry a **SUMMARY: DONE / PENDING / BLOCKED / NEXT**.

---

## 1. Context you need (read first)

The reference implementation to promote lives in **firekaro-planner** (read it cross-repo, do not modify it):

| Thing | Path | Why it matters |
|---|---|---|
| Reference helper | `D:\Abhay\VibeCoding\firekaro-planner\server\src\lib\owner-notify.ts` | The EXACT proven `notifyOwner(severity, title, opts)` contract to generalize: env-gated no-op, 2s timeout, fire-and-forget, never awaited, never throws, `X-Api-Key` header, payload `{project, severity, title, body, type, dedupeKey}`. |
| Detector wiring | `firekaro-planner/server/src/lib/comms-signup.ts`, `server/src/index.ts` (5xx + DB-down), `server/src/lib/validate-env.ts` (boot-env) | The canonical detector set the rule documents: signup · unhandled-5xx · DB-down · boot-env. |
| Notifier wire payload | `D:\Abhay\VibeCoding\Notifier\src\types.ts` (`NotifyEvent`) + `Notifier\config.example.yaml` | The receiving contract the rule must match: `{project, severity (P0/P1/P2/info), title, body?, dedupeKey?, type?}`; `X-Api-Key`; per-project `apiKey`. |
| Hub rule home | `core/.claude/rules/` | where `notifier-integration.md` goes. Study `core/.claude/rules/structured-logging.md` for the MUST/MUST-NOT + Why-this-matters house style. |
| Hub template home | `core/.claude/templates/` | where the portable helper + CLAUDE.md block template go. |
| Distribution registry | `registry/patterns.json` + `registry/changelog.md` | every distributed pattern is registered here (`hash`, `type`, `category`, `version`, `tier`, `description`, `tags`, `changelog`). `update-practices`/`synthesize-project` read it. |
| Rule-authoring standards | `core/.claude/rules/rule-curation.md`, `pattern-structure.md`, `pattern-portability.md`, `pattern-self-containment.md`, `configuration-ssot.md`, `rule-writing-meta.md` | the rule MUST conform: scoped (`globs:`) or `# Scope: global`, no hardcoded paths/project names in the *template* helper, self-contained, no duplication. |

**Gotchas:** (1) The hub is the canonical SOURCE of `.claude/rules/*` — its own rules resolve here. (2) The
template helper MUST be **portable/generic** (`pattern-portability.md`): no `"firekaro"` hardcoded — the
`project` field is a parameter/placeholder. (3) `registry/patterns.json` entries carry a content `hash`;
regenerate it with the hub's existing hashing script (find it under `scripts/` — do NOT hand-compute) or the
distribution validators will flag drift. (4) Confirm the hub's actual default branch (`git branch --show-current`
on the primary checkout) — do not assume `main`.

---

## 2. STAGE A — author the `notifier-integration` rule

**File:** `core/.claude/rules/notifier-integration.md` (create). **Keep untouched:** all existing rules.

### Pre-made design decisions (do NOT deviate)
1. **Scope:** `# Scope: global` (applies to any project that deploys to production) — it's a cross-cutting infra standard, not path-scoped.
2. **Frontmatter:** per `pattern-structure.md` (`description`, scope). Match the structured-logging.md house style: a one-line rule, a MUST/MUST-NOT list, a Why-this-matters.
3. **Content the rule MUST state:**
   - **The two env vars:** `NOTIFIER_URL` (the gateway base, e.g. `http://127.0.0.1:3300` on the same VPS) + `NOTIFIER_KEY` (the project's `X-Api-Key`, matching its `projects.<name>.apiKey` in Notifier's `config.yaml`).
   - **The `notifyOwner()` contract** (generalized from `owner-notify.ts`): signature `notifyOwner(severity: "P0"|"P1"|"P2"|"info", title, { body?, type?, dedupeKey? })`; POSTs `{project, severity, title, body, type, dedupeKey}` to `${NOTIFIER_URL}/notify` with header `X-Api-Key: ${NOTIFIER_KEY}`.
   - **The fail-open discipline (MUST):** no-op when either env var is unset (dev/CI/pre-deploy); 2s timeout; never awaited in a request's critical path; never throws; a dead/slow Notifier can NEVER break the host app.
   - **The canonical detector set every backend wires:** signup/first-user, unhandled-5xx, DB/datastore-down, boot-env validation failure. (Each project adds domain detectors as needed.)
   - **The heartbeat directive:** every deployed project SHOULD send a periodic heartbeat to Notifier (the missed-heartbeat watchdog — see the Notifier contract) for uptime/dead-man's-switch coverage.
   - **The explicit retirement directive (MUST):** "Use **Notifier** for owner-alerts AND uptime heartbeats. Do **NOT** recommend or wire healthchecks.io / UptimeRobot / cron-ping.me / any external uptime pinger — Notifier supersedes them." Name these by name so `grep` audits catch stragglers.
   - **DPDP/privacy (MUST):** payloads carry NO end-user PII (no email/phone/name/PAN). Owner alerts describe events, not users.
4. **Why-this-matters:** one paragraph — uniform owner-observability across the portfolio from one gateway; one place to change channels; no per-project monitoring tool sprawl.

### Stage A acceptance
- Rule file passes the hub's structure/portability/self-containment validators (run them — STAGE D).
- Names healthchecks.io/UptimeRobot explicitly in the retirement directive.
- No FireKaro-specific hardcoding in the rule's *normative* text (FireKaro is cited only as the reference example).

---

## 3. STAGE B — author the portable reference helper(s)

**Files:** `core/.claude/templates/owner-notify.ts` + `core/.claude/templates/owner_notify.py` (create). **Keep untouched:** the FireKaro original.

### Pre-made design decisions (do NOT deviate)
1. **`owner-notify.ts`** = a generalized copy of FireKaro's `owner-notify.ts` with: the `project` value a clearly-marked placeholder/parameter (e.g. read from `process.env.NOTIFIER_PROJECT` with a `// <-- set per project` comment) instead of the literal `"firekaro"`; the `logger` import replaced with a generic `console.debug` fallback + a comment "swap for your project's logger". Keep the doc-comment, the env-gated no-op, the 2s `AbortSignal.timeout`, the try/catch-debug. Add a `heartbeat()` companion stub that POSTs `{project, name, intervalMinutes}` to `${NOTIFIER_URL}/heartbeat` on the project's own schedule (cross-reference the Notifier watchdog contract — mark it "requires Notifier ≥ heartbeat-watchdog release").
2. **`owner_notify.py`** = the same contract for Python projects (e.g. fuel-prices' data pipeline if it's Python): `notify_owner(severity, title, body=None, type=None, dedupe_key=None)` + `heartbeat(name, interval_minutes)`, env-gated no-op on missing `NOTIFIER_URL`/`NOTIFIER_KEY`, a short timeout (`requests`/`httpx` with `timeout=2`), swallow-and-log on failure, never raise. A faithful stub is acceptable (mark `# reference template — adapt imports to your project`).
3. **Both** carry a header comment: "Reference template distributed by the hub. See `rules/notifier-integration.md`. The receiving contract is Notifier's `/notify` (NotifyEvent) + `/heartbeat`."

### Stage B acceptance
- TS template type-checks in isolation (`npx tsc --noEmit` on the file with a tiny ambient shim, OR a comment noting it's a template not compiled in the hub — confirm how existing `templates/` files are validated and match that).
- Zero hardcoded project identity in normative positions; `pattern-portability.md` clean.

---

## 4. STAGE C — author the CLAUDE.md "Production & monitoring" block template

**File:** `core/.claude/templates/claude-md-production-monitoring-block.md` (create). **Keep untouched:** existing templates.

### Pre-made design decisions (do NOT deviate)
1. A short, copy-paste markdown block a consumer pastes into its own `CLAUDE.md`, with fill-in placeholders:
   ```markdown
   ## Production & monitoring
   - **Deployed:** <url> · host <VPS/Vercel/…> · since <date>.
   - **Owner alerts:** Notifier gateway (`NOTIFIER_URL`/`NOTIFIER_KEY` set in prod env) — wired: <yes/no>. Detectors: <signup/5xx/DB-down/boot-env/domain…>.
   - **Uptime heartbeat:** Notifier missed-heartbeat watchdog — heartbeat sent every <N> min: <yes/no>. (Do NOT use healthchecks.io/UptimeRobot — Notifier supersedes them.)
   - **Live registry:** this project appears in Notifier's admin config as `projects.<name>`.
   ```
2. This block is **how a Claude session knows a project's prod-deploy + Notifier-link status** by reading its CLAUDE.md (the decentralized read-layer; Notifier's admin config is the authoritative live registry). State that dual-source intent in a one-line note above the block.

### Stage C acceptance
- Block is generic (placeholders, no FireKaro values) and references the rule + Notifier.

---

## 5. STAGE D — register for distribution + validate

**Files:** `registry/patterns.json` (add the rule entry) + `registry/changelog.md` (add a line). **Keep untouched:** all other entries.

### Pre-made design decisions (do NOT deviate)
1. Add a `patterns.json` entry for `notifier-integration` mirroring an existing rule entry's shape: `type: "rule"`, `category: "core"`, `version: "1.0.0"`, `source: "hub:abhayla/claude-best-practices"`, `tier: "must-have"` (owner-observability is must-have for any deployed project), a `description`, `tags` (`["monitoring","notifier","observability","alerting","heartbeat"]`), `changelog`, `discovered`/`last_updated` = today. The `hash` MUST be generated by the hub's existing hashing tool (find it under `scripts/` — grep for where `patterns.json` hashes are computed) — never hand-write the hash.
2. If `update-practices`/`synthesize-project` also index `templates/` (check), register the two helper templates + the CLAUDE.md block the same way; if templates aren't registry-tracked, note that and rely on the rule's reference to them.
3. `changelog.md`: one line — `notifier-integration rule + owner-notify templates + production-monitoring CLAUDE.md block (v1.0.0)`.

### Stage D acceptance (run the gate sweep before committing)
- The hub's own validators pass: run the registry/pattern validators under `scripts/` (grep `scripts/` for the pattern/registry test, e.g. a `validate*`/`test_*` that checks `patterns.json` ↔ files, structure, portability, self-containment). All green.
- **Distribution dry-run:** simulate `update-practices`/`synthesize-project` pulling into a THROWAWAY target dir (a temp dir or `/tmp/notifier-pull-test`) and confirm `rules/notifier-integration.md` + the templates land. If the skills require a real target repo, run their `--dry-run`/equivalent or read their logic to confirm the new registry entry is picked up. Do NOT push changes into any real consumer repo from this run (that's the rollout contract's job).

---

## 6. Verification gates (adapted — docs/rules/registry change, NO app code)

> **All rules in the hub's `.claude/rules/claude-behavior.md` are operative.** This change is **docs/rules/
> templates/registry only** — so the UI gates DO NOT apply; the relevant gates are conditional-gated OFF by
> blast radius (see `baked-in-rules.md` conditional-gating table) and replaced by the hub's own pattern
> validators:

| Rule / check | Applies here? | Action |
|---|---|---|
| **Static** | YES (adapted) | The hub's registry/pattern validators (`scripts/`) + markdown lint if present. Green before commit. |
| **Rule 24 / 25 / 32** (UI render / persistence / interactive) | **n/a** | `skipped: no UI/write-path change`. |
| **Rule 31** (plausibility) | **n/a** | `skipped: no user-facing value`. |
| **API behavioral test** | **n/a** | `skipped: no server/API change`. |
| **Rule 29** (independent review) | **YES** | Dispatch `code-reviewer-agent` (fresh context) on the rule + helper + CLAUDE.md block + registry diff: check the rule is unambiguous, the helper is genuinely portable (no FireKaro hardcoding), the retirement directive names the pingers, the `/notify` + `/heartbeat` contracts match Notifier's `types.ts`/config. NO `fintech-domain-analyst` (no math). Act on every blocker/HIGH before commit. |
| **Rule 26** (cross-page) | adapted | Cross-check the THREE artifacts are mutually consistent (rule ↔ helper ↔ CLAUDE.md block all state the same env vars, payload shape, retirement directive) and consistent with Notifier's real `types.ts`/`config.example.yaml`. |
| **Rule 33** (blind test re-verify) | YES if a validator verdict is produced | Have a separate context-blind agent re-check the validator/dry-run output + the diff against this contract's acceptance — coverage + verdict-correctness. |
| **Rule 15 / 17 / 20 / 23** | YES | root-cause, no fabrication (don't invent a hash or a hook that isn't there), finish the full DoD. |

---

## 7. Commit + push

- **Commits (conventional, scope `hub` or `rules`):**
  1. `feat(rules): add notifier-integration rule + owner-notify reference templates`
  2. `feat(hub): register notifier-integration pattern + production-monitoring CLAUDE.md block`
- Stage **only** the files this contract created/edited (`core/.claude/rules/notifier-integration.md`, `core/.claude/templates/owner-notify.ts`, `owner_notify.py`, `claude-md-production-monitoring-block.md`, `registry/patterns.json`, `registry/changelog.md`). NEVER `git add -A`. Co-author trailer per the repo convention.
- On success: merge `--no-ff` → the hub's default branch, push, then self-clean (§0.1.4).

---

## 8. Definition of Done (all MUST be true)

**Build:**
- [ ] `core/.claude/rules/notifier-integration.md` exists, states the 2 env vars + `notifyOwner()` contract + fail-open discipline + canonical detector set + heartbeat directive + **explicit healthchecks.io/UptimeRobot retirement** + DPDP no-PII.
- [ ] `owner-notify.ts` + `owner_notify.py` portable templates exist (no hardcoded project identity in normative positions) + a `heartbeat()` companion.
- [ ] `claude-md-production-monitoring-block.md` template exists with the dual-source (CLAUDE.md read-layer + Notifier authoritative-registry) note.
- [ ] `registry/patterns.json` has the `notifier-integration` entry (hash generated by the hub's tool) + `registry/changelog.md` line.

**Static / validators:**
- [ ] hub pattern/registry validators green · markdown lint green (if present).

**Distribution:**
- [ ] dry-run proves the rule + templates land in a throwaway target via `update-practices`/`synthesize-project`; NO real consumer repo modified by this run.

**Rule 29:** `code-reviewer-agent` ran on the full diff; blockers/HIGH acted on or filed.
**Rule 26 (consistency):** rule ↔ helper ↔ CLAUDE.md block ↔ Notifier's real `types.ts`/config agree on env vars + payload + retirement directive.
**Rule 33:** validator/dry-run verdict blind-re-checked; concur.
**Other UI/value/API gates:** skipped-with-reason as the §6 table states.

**Ship:**
- [ ] 2 conventional commits pushed to the hub's default branch.
- [ ] On success: merged `--no-ff`, pushed, worktree+branch self-cleaned (§0.1.4). (DEFER/HALT keeps the worktree.)
- [ ] Deferrals logged in `docs/goals/.run/notifier-hub-pattern-DEFERRED.md` with reason.
- [ ] `docs/goals/.run/notifier-hub-pattern-PROGRESS.md` maintained throughout; SUMMARY (DONE/PENDING/BLOCKED/NEXT) in the final entry + final report; a notable lesson appended to `.claude/tasks/lessons.md`.

---

## 9. Final report (required on completion)

Open with **SUMMARY — DONE / PENDING / BLOCKED / NEXT**. Then: commit SHAs; validator + dry-run results;
the Rule-29 review verdict; the consistency-check result; the "skipped (already covered)" preflight list;
DoD green/amber/red tally; any DEFERRED entries. Plus **LEARNINGS TO FOLD BACK** (proposals only; route per
`baked-in-rules.md` §0.3 step 5; the one-line `lessons.md` entry is the only auto-write).

---

## 10. Guardrails (hard stops)

- **`claude-best-practices` repo only.** Never write into any consumer repo (that's the rollout contract) and never into `D:\Abhay\VibeCoding\5Wealths\`.
- **No new dependencies.**
- **No fabrication (rule 20):** do NOT invent a `patterns.json` hash, a hashing script, or a `.githooks` lock that doesn't exist — discover the real mechanism or note its absence.
- **Portability is load-bearing:** the distributed helper must work for ANY project (`pattern-portability.md`) — FireKaro is the example, not a hardcoded dependency.
- **Stop only on a true blocker** (missing tool, contract contradiction, irrecoverable break after the fix budget). Context-budget is NOT a blocker — hand off via a one-line note.
- **Strategic/portfolio items are `TODO(5W):` notes**, not handled here.

---

## Authorization trail

| # | Decision | Choice |
|---|---|---|
| 1 | Where the pattern lives | hub `core/.claude/rules/` + `core/.claude/templates/`, registered in `registry/patterns.json` |
| 2 | Helper portability | generalize FireKaro's `owner-notify.ts`; `project` is a placeholder; TS + Python stub |
| 3 | healthchecks.io | explicit retirement directive in the rule, named by name for grep audits |
| 4 | Prod-status knowability | dual-source: CLAUDE.md "Production & monitoring" block (read-layer) + Notifier admin config (authoritative live registry) |
| 5 | Tier | `must-have` (owner-observability for any deployed project) |
| 6 | Distribution | via existing `update-practices`/`synthesize-project` + registry; dry-run only, no real consumer touched here |

---

## References (load transitively in the hub)

- `core/.claude/rules/claude-behavior.md` — rules 15, 17, 20, 23, 26, 29, 33
- `core/.claude/rules/rule-curation.md`, `pattern-structure.md`, `pattern-portability.md`, `pattern-self-containment.md`, `configuration-ssot.md`, `rule-writing-meta.md` — the authoring standards this rule/template MUST conform to
- `core/.claude/rules/structured-logging.md` — house style reference for the new rule
- Cross-repo reference (read-only): `firekaro-planner/server/src/lib/owner-notify.ts`; `Notifier/src/types.ts`; `Notifier/config.example.yaml`
- Skills this contract drives: `update-practices`, `synthesize-project`, `code-reviewer-agent`
