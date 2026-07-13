# SKILL EVALUATION REPORT: dependency-migration-triage

Mode: full
Iteration: 1
Evaluated: 2026-07-13
Skill path: `core/.claude/skills/dependency-migration-triage/SKILL.md` (99 lines, no `references/`, no `evals/evals.json` prior to this report)

---

## STEP 0 — PRE-FLIGHT CHECKS

### 0.1 Registry Sync — **FAILURE (BLOCKING)**

`registry/patterns.json` has **no entry** for `dependency-migration-triage` at all — not a hash/version
mismatch, an outright missing key (confirmed: `grep -n "dependency-migration-triage" registry/patterns.json`
returns nothing; `python -c "json.load(...)['dependency-migration-triage']"` → `NOT FOUND`). The pattern is
only referenced in `docs/governance/fable-failure-archaeology-2026-07-13.md` (queue table, row: *"When a
dep bump/removal surfaces test failures: classify each (framework quirk masked vs latent real bug), work
classes not instances (KKB 4-PR chain)"*) — i.e. it is documented as a queued/landed idea but never
registered. Per `CLAUDE.md` "Registry maintenance" (add/remove in `core/.claude/`, update
`registry/patterns.json`, run `generate_docs.py`, run `workflow_quality_gate_validate_patterns.py`), this
skill is currently **undiscoverable via the registry** and would fail
`workflow_quality_gate_validate_patterns.py`'s cross-reference sync check.

Current SHA-256 of `SKILL.md`: `ff648621025236e22790e3cb328c838ac95815c63382810626aaa94cde60516e` (for
when the registry entry is authored).

### 0.2 Frontmatter Completeness

| Field | Status |
|---|---|
| `name` | PASS — `dependency-migration-triage`, matches directory, lowercase-hyphen, no reserved words |
| `description` | PASS — third-person, verb-first ("Triage the test failures..."), states what+when, 437 chars (well under 1024) |
| `type` | PASS — `workflow` |
| `triggers` | PASS — 4 entries (1 slash-command + 3 phrases), ≥3 required |
| `version` | PASS — `"1.0.0"`, valid SemVer |
| `allowed-tools` | **FIX — under-declared.** `Read, Grep, Glob, Bash` declared; body's STEP 4 ("Fix in Waves") explicitly directs editing test code and product code across waves, and STEP 3's "Genuine incompatibility" / "Structural coupling" treatments both require code edits ("Apply the documented migration pattern cluster-wide", "Refactor the shared layer once"). Per `pattern-portability.md`'s tool-grant table, a "workflow with modifications" skill's expected tool set is `Bash Read Write Edit Grep Glob`. `Write`/`Edit` are missing. |

### 0.3 Structural Integrity — all PASS

- Code fences: 2 fenced blocks (STEP 1 baseline template, STEP 5 report template), both balanced.
- No orphaned numbered lists (skill uses tables, not numbered sub-lists, inside steps).
- No "Step N" cross-references to nonexistent steps.
- No `/skill-name` or `*-agent` references in the body (skill is self-contained, no delegation) — nothing to validate as a dead reference.
- No placeholder markers (`TODO`/`FIXME`/`PLACEHOLDER`).
- Workflow skill has `## MUST DO` / `## MUST NOT DO` at the bottom (satisfies the "CRITICAL RULES or MUST DO/MUST NOT" structural requirement from `pattern-structure.md`); the preamble states the core discipline ("Triage first, and the waves become a plan instead of four surprises") — primacy+recency reinforcement present.
- No `references/` directory → reference-depth and TOC checks N/A.

### 0.4 Reference Self-Update Mechanism — **N/A**

No `references/` directory exists for this skill. All 10 sub-checks are not applicable.

---

## SKILL NECESSITY

Without skill: unassisted approach (fix file-by-file, easiest-first, no baseline, risk of weakening
"flaky-looking" assertions, latent bugs silently buried in the migration commit) vs. with skill (forced
baseline snapshot separating collection/import errors, signature-based clustering, explicit 4-way
classification before any fix, latent bugs filed as standalone tracked issues). **Delta: clear, meaningful
value-add** — the procedure encodes a non-obvious discipline (cluster-first, classify-before-fix) that
runs counter to default engineering instinct, and directly targets the failure mode the skill's own
preamble cites (a real migration that took 4 sequential PRs because classes were discovered one straggler
at a time).

---

## TRIGGER EVALUATION

| Check | Result |
|---|---|
| Should-trigger | 9/10 at clean 3/3 (100%); 1/10 borderline at 2/3 (query: "ripped out the old auth SDK, CI is a sea of red, want to figure out root causes before touching anything" — competes with `/systematic-debugging` since it doesn't say "tests" explicitly). Aggregate 29/30 = 96.7%. |
| Should-not-trigger | 9/10 clean at 0/3 (0%); 1/10 at 1/3 (33%) — "can you upgrade our lodash version to the latest" (the upgrade *action* itself, before any failures exist — ambiguous but under the ≤20% aggregate bar). |
| Cross-skill conflicts | **0 misroutes** across the 5 clearest contested queries tested against `systematic-debugging`, `fix-loop`, `test-pipeline`, `debugging-loop` — the skill's explicit "5+ failures" + "dependency/migration" framing keeps it out of their lane, and vice versa. |
| Missing reciprocal boundary | **Confirmed gap (MINOR).** Unlike `fix-loop`/`systematic-debugging` (which name their siblings and hand-off conditions in their own descriptions), `dependency-migration-triage`'s description has no explicit "not for X, see Y instead" pointer — it relies solely on its own scope specificity, which worked in this eval but is a drift risk as the skill catalog grows. |
| Rule overlap (`bug-triage-discipline.md`) | **No duplication** — the rule governs how an individual bug is *filed* (repro, why-missed, sibling audit, one tracker); the skill governs how a *mass* of test failures from one dependency event gets clustered and classified before fixing. They compose (a "latent real bug" cluster is explicitly handed to the rule's filing structure), neither restates the other. |
| Regressions (--baseline) | N/A — no prior version exists. |
| Trigger verdict | **PASS** (minor optimization: add reciprocal boundary language). |

---

## OUTPUT EVALUATION

### Scenarios (5: 3 happy-path, 2 edge)

| Scenario | A1 (baseline separates collection/assertion) | A2 (cluster by signature) | A3 (4-class) | A4 (report format) |
|---|---|---|---|---|
| 1. Mocking-framework removal, 51 failures | PASS | PASS | PASS | PASS |
| 2. SQLAlchemy 1.4→2.0, 87 failures | PASS | PASS | PASS | PASS |
| 3. moment.js → date-fns, 22 failures | PASS | PASS | PASS | PASS |
| 4. Only 4 failures (below stated "5+" threshold) | **GAP** — threshold is stated only in frontmatter `description`, never addressed in the STEP 1-5 body (no fallback, no "still fine, just lighter" note) | — | — | — |
| 5. 200+ collection errors ("unmask in waves") | PASS (STEP 1's masking language is explicit and actionable) | **Partial** — STEP 4 says work collection errors first and expect waves, but never says to apply STEP 2's clustering *recursively* inside the collection-error set itself, nor gives a stopping rule for "when to stop waving" | N/A (not reached in the walkthrough) | N/A |

Scenarios 1-3: 12/12 assertions PASS. Scenarios 4-5 surfaced two real content gaps (see Recommended Fixes).

### Stress Test (10 adversarial inputs)

| # | Input | Severity | Finding |
|---|---|---|---|
| 1 | Vague "some tests broke, not sure why" (no dep context) | MINOR | Skill *shouldn't* fire (no dep/migration signal) but has no active over-trigger guard beyond its own trigger phrasing |
| 2 | Misapplied to production-incident triage (not test failures) | **MAJOR** | No scope-guard anywhere in the body stating "test-suite triage only" — a caller could invoke it on PagerDuty alerts and get plausible-sounding-but-meaningless steps |
| 3 | "Just delete the failing tests, no time for waves" | PASS | Directly blocked, verbatim, by MUST NOT DO item 1 |
| 4 | 3,000 failures / 40 signatures | MINOR | Clustering mechanism scales fine conceptually, but STEP 4 gives no guidance for ranking 20+ leaf clusters against each other beyond the 3 coarse tiers |
| 5 | Exactly 1 cluster / 1 test | MINOR | No malfunction — degenerate case works, just ceremonial overhead; same root gap as Scenario 4's threshold silence |
| 6 | User jumps to STEP 3 without running STEP 1 first | **MAJOR** | STEP 1's "before touching anything" and the MUST DO baseline mandate are prose-only — nothing in the skill's structure prevents skipping straight to classification |
| 7 | Re-run at wave 1 and wave 3 of the same migration | PASS | STEP 4 explicitly instructs updating the snapshot's signature list each wave — prevents stale/duplicate reporting |
| 8 | Minified/obfuscated stack traces (degraded signal) | **MAJOR** | STEP 2's clustering mechanism assumes readable error type + message shape; nothing addresses collapsed/opaque signatures from a minified bundle |
| 9 | Re-triggering days later citing a stale snapshot as current | MINOR | STEP 1's "run the FULL suite once" is about not re-running the SAME baseline, not explicitly about rejecting a stale one |
| 10 | "Yolo, make CI green, weaken whatever's failing" | PASS | Directly blocked, verbatim, by MUST NOT DO item 1 |

Rollup: **3 PASS / 4 MINOR / 3 MAJOR / 0 CRITICAL** → 30% clean-pass rate, well under the ≥90% PASS bar for
output verdict PASS (MAJOR findings are content gaps, not correctness bugs — nothing produced a wrong or
harmful output, but the 3 MAJORs are all "the skill is silent where a real caller would need guidance").

### Output verdict: **FIX**

The 4/5 assertion-based scenarios and 2 of the 3 hardest adversarial pressures (assertion-weakening under
time pressure, tested twice) hold up cleanly — the skill's core classification mechanism and its strongest
guardrail are solid. But 3 MAJOR gaps (no scope-guard against non-test-suite misuse, STEP 1 prerequisite
unenforced beyond prose, no degraded-signal-quality fallback) plus the unaddressed sub-5-failure threshold
are real, fixable content gaps — not a fundamental design failure, but enough to withhold PASS.

---

## MODEL COVERAGE

Tested on: single model (sonnet, via 3 dispatched evaluation subagents simulating trigger/output judgment).
No model-matrix run (Haiku/Opus) was performed for this pass — note per STEP 3.3b: "Tested on sonnet only."

---

## OVERALL VERDICT: **FIX**

### Blocking issues
1. **Registry entry missing entirely** (`registry/patterns.json` has no `dependency-migration-triage` key) — the skill fails registry-sync validation and would fail `workflow_quality_gate_validate_patterns.py` in CI.

### Recommended fixes (prioritized, mapped to the routing/content location each targets)

| # | Fix | Maps to | Severity |
|---|---|---|---|
| 1 | Add a `dependency-migration-triage` entry to `registry/patterns.json` (type: skill, current SHA-256 above, version `1.0.0`, tier `core/`, dependencies: none) and run `generate_docs.py` + `workflow_quality_gate_validate_patterns.py` | Registry sync (0.1) | BLOCKING |
| 2 | Add `Write, Edit` to the `allowed-tools` frontmatter line — STEP 4's fix-in-waves treatments (refactor shared fixtures, apply migration patterns cluster-wide, rewrite test assertions) require them | Frontmatter (0.2) | FIX |
| 3 | Add one line to the `description` (or a preamble sentence) naming the boundary: "for a single test or an unclear root cause not tied to a dependency/migration event, use `/fix-loop` or `/systematic-debugging` instead" | Trigger routing table — reciprocal boundary | MINOR |
| 4 | Add an explicit scope-guard sentence: "This procedure is for test-suite failure triage only — not production incident/alert triage" | STEP 1 preamble or frontmatter description | MAJOR (stress test #2) |
| 5 | Address the sub-"5+ failures" case in the body, not just the frontmatter threshold: a one-line note that below ~5 failures clustering has little leverage — fix directly, or run the procedure anyway if signatures are still unclear | STEP 1 or new "Scope" subsection | scenario-4 gap / stress #1, #5 |
| 6 | Strengthen STEP 1 from prose-only to an explicit precondition statement — e.g. move "before touching anything" language into a MUST DO/MUST NOT DO bullet so it reads as a hard gate, not just a step title | STEP 1 / MUST DO section | MAJOR (stress test #6) |
| 7 | Add a STEP 2 fallback line for degraded signal quality: "when stack traces are opaque/minified, fall back to grouping by test name or file path, and flag the cluster as low-confidence" | STEP 2 | MAJOR (stress test #8) |
| 8 | Add guidance to STEP 4 on sub-clustering large collection-error sets recursively (apply STEP 2 within the collection-error tier itself) and a stopping rule ("a wave that surfaces zero new clusters ends the loop") | STEP 4 | scenario-5 gap / stress #4 |

Per the eval workflow's MUST NOT DO ("MUST NOT suggest fixes contradicting writing-skills best practices" /
"do not edit the SKILL.md" for this task): the above are **recommendations for the skill's author**, not
applied by this eval. No `SKILL.md` edits were made.
