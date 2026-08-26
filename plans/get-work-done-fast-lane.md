# /get-work-done — FAST LANE for small tasks (fix the fixed-ceremony overhead)

**Status:** OPEN — handoff written 2026-08-26 19:20 IST by the firekaro-planner Fable session
(f233f7b0) after the owner cancelled T-349. Owner verdict, verbatim: *"just because I'm using get
work done skill is not acceptable … fifteen minute work goes beyond one hour … something is really
broken and it needs fix."*

**One-line problem:** the fleet charges the SAME per-task ceremony whether the task is a 5-line
docs edit or a multi-file feature. A 15-minute edit was priced at ~2 hours. Overhead is fixed, not
scaled to blast radius, and per-stage wall time is never measured — so nobody saw it.

## 1. The incident (T-349, all artifacts already on the bus)

| Artifact | Where |
|---|---|
| Contract (cancelled, with status_log) | `GWD\queue\T-349-firekaro-planner-claude-md-trim.cancelled.md` |
| Worker prompt as launched | `GWD\heartbeats\T-349.prompt.txt` |
| Worker's partial diff at kill time (422 lines, 2 files, 0 commits) | `GWD\evidence\2026-08-26-T-349\worker-partial-after-15min.patch` |
| LEDGER line | `GWD\LEDGER.md` (T-349, 2026-08-26T13:41Z) |
| Registry row (learning debt, 1st occurrence) | `GWD\MECHANISM-DUE.md` → class `trivial-task-pays-full-fleet-ceremony` |
| Lesson | `GWD\PATTERNS-SEEN.md` → `LESSON(OPEN): T-349 2026-08-26 …` |
| Fleet-registered the repo (kept; owner-approved) | `GWD\settings.json → repo_registry.firekaro-planner`; 5wealths `PORTFOLIO.yml` row → active/pc |
| Dirty worktree left for the owner | `D:\Abhay\Ventures\firekaro-planner-wt-t349` (branch `docs/T-349-claude-md-trim`) |

The task: 5 numbered doc improvements to firekaro-planner's `CLAUDE.md` (move two blocks into
rules, one pointer to README, fix two stray `#` lines, hoist 3 invariants). Hand-edit time ≈ 15 min.

**Measured timeline (IST, 2026-08-26):**

| Stage | Clock | Minutes | Needed for a 5-line docs edit? |
|---|---|---|---|
| Intake by the dispatching session: registry row (repo was unregistered), worktree, contract, prompt, contract-lint, preflight | 18:42 → 18:54 (+ ~8 min earlier scouting) | ~20 | Registry = one-time. The rest is per-task ceremony |
| Worker read phase: contract + 2 `context_docs` + CLAUDE.md (342 lines) + **74 rule files (556 KB) auto-loaded every turn** | 18:54 → ~19:04 | ~10 | No — governance weight, not task weight |
| Worker editing (had 2 files / 422 diff lines at min 15; **0 commits, 0 PR** — ignored docs-first + push-first mandates) | ~19:04 → 19:09 (killed) | 5–10 | Yes — the actual work |
| Projected: docs-first PR + full CI (frontend + backend suites for a docs diff) | — | ~15 | No |
| Projected: checker = a SECOND full LLM run re-reading everything from a clean checkout | — | 30–45 | No — a script (stat every path, diff moved paragraphs) does it in seconds |
| Projected: dispatcher reads verdict, merges, reports | — | 5 | Yes |
| **Total priced** | | **~120** | **Ceremony ≈ 85–90 %** |

Same-day context: 9 workers died at their turn cap on 2026-08-26; the `build` kind floor forced
`max_turns: 120` on a docs task (preflight exit 12 blocks anything lower).

## 2. Root cause — two SSOTs contradict each other

1. `plans/get-work-done-dispatcher.md` **G16 (owner-LOCKED, P2):** *"Complexity gate = blast
   radius, not file count: trivial = no auth/payment/config/migration/deploy paths touched AND no
   unknowns → **do now**; else decompose."*
2. `.claude/skills/get-work-done/SKILL.md` **STEP 3 (v0.8, 2026-08-15):** *"The inline-execution
   path is DELETED … Every task handed to /get-work-done — however trivial — is contracted and
   dispatched … a get-work-done task with no T-id is a defect."*

v0.8 was a reaction to a real incident (a GoRefer session did Wati/Zoho work in the wrong
directory with the wrong context). The fix was right about **context** (never author in the wrong
repo, always a T-id + checker) and wrong about **size**: it removed the cheap lane without adding a
size-proportional one. The global `~/.claude/CLAUDE.md` rule of 2026-08-15 ("fleet-shaped work is
NEVER done inline … even when the task sounds trivial") encodes the same over-correction.
"Trivial tasks are made cheap by BATCHING" (STEP 5) does not help a single small task.

Secondary causes (each multiplies the fixed cost):
- **No per-stage timing.** Nothing stamps launch → first commit → PR open → CI done → checker
  verdict. Waste is invisible; only the owner asking surfaced it.
- **Checker is always a second LLM run** (`deliverable: content` procedure = trace every claim),
  even where a deterministic script is a stronger check (path existence, moved-paragraph diff).
- **Turn-budget floors by kind** (`build` = 120) apply to docs edits because a bare `T-NNN` is
  always "build".
- **Full CI on docs-only diffs** — downstream repos have no `paths-ignore`/docs-only short-circuit.
- **Worker context weight** is the target repo's problem (firekaro: 74 rules, 342-line CLAUDE.md)
  but the fleet pays it on every turn of every worker; there is no worker-mode slim context.
- **Workers ignore docs-first/push-first** (0 commits at 15 min despite three verbatim mandates —
  prose, again, is not a mechanism; see MECHANISM-DUE `uncommitted-work-lost-at-turn-cap`).

## 3. The fix — mechanisms, not prose (Learn-or-block rule, owner 2026-08-26)

Owner's bar: **a 15-minute task must not take > 1 hour; target ≤ 20 min end-to-end.**

1. **FAST LANE (size-gated, in `SKILL.md` STEP 3 + `contract-lint.py` + `preflight-guard.ps1`).**
   Eligibility = ALL of: ≤ 5 files · `deliverable: content|mechanical` · no path under
   auth/payment/config-secrets/migration/deploy · no unknowns after scout. Flow: contract + T-id
   still written (2 min — the audit invariant "no task without a T-id" stays true) → the
   **dispatching session itself** edits in its own worktree of the TARGET repo (never the cwd
   repo, never the bus) and opens the PR → **checker = deterministic script**
   (`GWD\fast-lane-check.py`: every backtick path in touched files exists; every removed
   paragraph appears elsewhere in the diff; line-count / grep predicates from the contract's dod
   run as commands) → merge on green. Reconcile G16 and v0.8 in the plan text: the wrong-context
   incident is prevented by the *worktree-of-target-repo* rule, not by banning inline edits.
2. **Per-stage timestamps** in `worker-wrapper.ps1` → `.hb` + LEDGER: `launched`, `first_commit`,
   `pr_opened`, `ci_done`, `checker_verdict`. `lesson.py status` flags any task whose
   (total − edit) / edit ratio > 3 as `CEREMONY-RATIO` learning debt. This is the detector that
   makes the class visible without an owner complaint.
3. **Docs-only CI short-circuit** for downstream repos: `paths-ignore: ['**/*.md', 'docs/**',
   '.claude/**']` on the heavy jobs (or a first job that exits early on docs-only diffs) — one
   template in the hub, provisioned via `/synthesize-project`.
4. **Kind floor override**: contract `deliverable: content|mechanical` → kind = `mechanical`
   (floor 40), not `build` (120). `preflight-guard.ps1` reads deliverable before the T-id suffix.
5. **Slim worker context** (optional, biggest lever for heavy repos): wrapper launches with a
   worker-mode `CLAUDE.md` overlay / `--disallowed-rules` for path-scoped rules the task's file
   list cannot touch. Measure first (stage timestamps will show the read-phase cost).
6. **Push-first as a mechanism, not a mandate**: wrapper's 15-min autosave already exists
   (T-323/T-333); add "no commit within 8 min of launch → wrapper commits + pushes WIP itself".

## 4. Acceptance (red-then-green, checker-verified)

- Re-run **T-349's exact contract** through the fast lane: end-to-end ≤ 20 min wall clock, PR
  merged, all 8 dod predicates green, `fast-lane-check.py` output in evidence.
- A fast-lane request that touches `server/src/middleware/auth.ts` is REFUSED by the gate (exit
  code named in the README table) and routed to the normal lane.
- `lesson.py status` shows `CEREMONY-RATIO` for a synthetic task with edit=5 min, total=40 min.
- `MECHANISM-DUE.md` row `trivial-task-pays-full-fleet-ceremony` flipped to `done` via
  `lesson.py done --tid <T-id>` only after the checker verifies items 1, 2, 4.
- Global `~/.claude/CLAUDE.md` "fleet-shaped work is NEVER done inline" paragraph amended to
  name the fast lane (owner-approved wording — it is his standing rule).

## 5. Read-first list for the fixing session

1. This file.
2. `GWD\MECHANISM-DUE.md` row `trivial-task-pays-full-fleet-ceremony` + `PATTERNS-SEEN.md` tail.
3. `.claude/skills/get-work-done/SKILL.md` STEP 3 (the v0.8 deletion) + STEP 5 batching + STEP 7
   checker table.
4. `plans/get-work-done-dispatcher.md` G16 (the locked decision v0.8 silently overrode).
5. `GWD\preflight-guard.ps1` turn-budget gate (kind floors) + `GWD\worker-wrapper.ps1` autosave.
6. `GWD\queue\T-349-…cancelled.md` + `GWD\evidence\2026-08-26-T-349\`.
