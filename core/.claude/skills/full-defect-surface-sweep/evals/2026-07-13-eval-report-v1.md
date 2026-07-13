SKILL EVALUATION REPORT: full-defect-surface-sweep
=====================================
Mode: full
Iteration: 1

SKILL NECESSITY
  Without skill: partial coverage (naive re-grep + prose "sibling-audit" per bug-triage-discipline.md)
  With skill:    structurally more rigorous — CLASS/DETECTABLE-BY abstraction catches
                 consumer/inheritance cases naive re-grep misses; STEP 3's 3-way
                 classification (same defect / same risk / clean) prevents the common
                 binary found/not-found collapse; STEP 5's locked SURFACE SWEEP block is
                 a genuine auditability gain over a prose "I checked, looks fine."
  Delta: NOT pure restatement of the rule — adds value, but see PRE-FLIGHT FAILURE below.

PRE-FLIGHT FAILURE (blocking)
  0.1 Registry Sync: FAILED. `registry/patterns.json` has NO entry for
    `full-defect-surface-sweep` (confirmed via direct key lookup and a repo-wide grep
    for "defect" — zero hits). Consequences:
      - No description/hash/version to cross-check for drift.
      - `workflow_quality_gate_validate_patterns.py` (the CI cross-reference validator)
        cannot confirm this pattern is registered — likely FAILS CI if run.
      - Per `rule-curation.md` / `pattern-self-containment.md`, a distributed pattern
        under `core/.claude/skills/` MUST have a registry entry; this is a gap in the
        pattern's own compliance, independent of trigger/output quality.
  0.2 Frontmatter completeness: PASS — name matches directory (39 chars, kebab-case,
    no reserved words), description is third-person/verb-first and describes what+when,
    type: workflow with 5 numbered STEP sections, triggers: 4 (>=3 required),
    allowed-tools (Read/Grep/Glob/Bash) matches actual body usage (grep/structural
    sweeps, no Agent/Skill calls to under/over-declare), version "1.0.0" is valid SemVer.
  0.3 Structural integrity: PASS — code fences balanced (3 fenced blocks, all closed),
    no orphaned numbered-list items, no dead "Step N" cross-references, no dead
    skill/agent name references (body names no other skill/agent by name), no
    placeholder markers, MUST DO / MUST NOT DO section present at the bottom
    (satisfies the required CRITICAL RULES equivalent).
  0.4 Reference self-update: N/A — no `references/` directory exists for this skill.

TRIGGER EVALUATION
  Should-trigger:    ~8.5/10 activated (~80-85% rate) — 8 High confidence, 2 Medium
  Should-not:        8/10 clean (Low risk); 2/10 Low-Medium risk (queries #6 "find the
                     root cause before fixing it" and #9 "did we fix the bug from
                     yesterday's report?" — partial keyword overlap on "root cause" /
                     "did we fix", both still net Low-Medium not high-risk)
  Cross-skill:       1 conflict class identified — see below
  Regressions:       N/A (no --baseline; this is v1.0.0, first eval)
  Fresh validation:  N/A (not run — no description optimization triggered, verdict is FIX
                     for a different reason: cross-reference gap, not trigger-rate failure)
  Trigger verdict:   FIX

  Cross-skill conflict detail: `bug-triage-discipline.md` is an ALWAYS-LOADED global rule
  whose sibling-audit requirement ("Class N: ..." + repo-wide search + safe/filed/flagged
  disposition per hit) substantially overlaps this skill's STEP 1-5 body. The skill's
  description does NOT cross-reference the rule, `systematic-debugging`, or
  `debugging-loop` — no bidirectional signposting. Real risk: an agent already
  rule-compliant satisfies the sibling-audit requirement passively while filing a bug and
  never invokes this skill via its natural-language triggers (only the explicit
  `/full-defect-surface-sweep` slash-command path is trigger-immune to this). The skill's
  genuine differentiator — sweeps invoked independent of formal issue-filing, or
  mid-diagnosis before an issue exists — is never stated, so the distinction is invisible
  to both the router and the reader.

OUTPUT EVALUATION
  Scenarios:         3.5/5 passed (3 full PASS: multi-sibling code defect, data-defect
                     full-dataset case, zero-siblings case; 1 conditional PASS: subtle
                     ungreppable logic class — degrades only by inference, not by
                     explicit text; 1 FAIL: 50+-hit monorepo scaling — STEP 4's "file
                     one issue per coherent residual" never defines grouping granularity)
  Stress test:       1 PASS / 3 MAJOR / 1 MINOR (60% MAJOR-or-worse)
                       - urgent-hotfix-vs-sweep-discipline: PASS (explicit MUST NOT line)
                       - ambiguous "did we get everything" pre-diagnosis: MAJOR (no
                         precondition guard — STEP 1 assumes a root cause already exists)
                       - invoked before root cause isolated: MAJOR (same gap; risks a
                         false CLASS CLOSED verdict on a misdiagnosed bug)
                       - repeated invocation on same class: MAJOR (no dedup check before
                         filing a residual issue — unlike sibling `create-github-issue`
                         skill's explicit sha256/30-day dedup)
                       - stale context after residuals filed: MINOR (no re-verification
                         trigger noted; lower severity, issue tracker carries state forward)
  Assertions:        4/5 (80%)
                       1. States explicit CLASS distinct from instance — PASS (STEP 1)
                       2. Sweeps code+tests+configs+scripts+CI, not just report site — PASS (STEP 2)
                       3. Classifies every hit via fixed 3-way taxonomy — PASS (STEP 3)
                       4. Ends in the locked SURFACE SWEEP block — PASS (STEP 5)
                       5. Gates premature invocation + prevents duplicate residual filing
                          on repeat runs — FAIL (no precondition check, no dedup/idempotency
                          language anywhere in the file)
  Baseline delta:    N/A (no --baseline; v1.0.0)
  Output verdict:    FIX

MODEL COVERAGE
  Tested on:         reasoning-based evaluation (sonnet-driven subagents simulating
                     trigger judgment + scenario walkthroughs); no live multi-session
                     Claude Code trigger-firing harness was available in this environment
                     to fire literal test prompts — reasoning was grounded in the exact
                     frontmatter/body text, not vibes. Divergent-model testing (Haiku vs
                     Opus) was NOT run — flagged as an untested dependency, not a false FAIL.

TRAP CERTIFICATION
  Not requested (mode: full, not trap) — N/A.

OVERALL VERDICT: FIX
Blocking issues:
  1. [PRE-FLIGHT — BLOCKING] No `registry/patterns.json` entry exists for this skill.
     Register it (description, hash, version, dependencies: none) before this pattern
     can be considered CI-compliant; run `generate_docs.py` and
     `workflow_quality_gate_validate_patterns.py` after.
  2. [TRIGGER] No cross-reference / bidirectional signposting between this skill's
     description and `bug-triage-discipline.md` (the overlapping always-on rule) or
     `systematic-debugging`/`debugging-loop` — creates a dead-pattern risk where
     rule-compliant agents never invoke the skill via natural language.
  3. [OUTPUT] No STEP 0 precondition guard — the skill's own trigger phrase
     ("did we fix all instances") can fire before a root cause is actually isolated,
     risking a false CLASS CLOSED verdict on a misdiagnosed bug.
  4. [OUTPUT] No dedup/idempotency guidance in STEP 4 for repeated invocations — risks
     duplicate residual issues on re-runs of the same class sweep.
  5. [OUTPUT] No scaling/grouping heuristic in STEP 4 for high-hit-count sweeps (50+) —
     "file one issue per coherent residual" is undefined at scale.

Recommended fixes (prioritized, mapped to the routing table):
  Priority 1 (registry — blocking CI compliance):
    - Add a `full-defect-surface-sweep` entry to `registry/patterns.json` with a
      description matching the frontmatter, the SHA-256 hash of the current SKILL.md
      (`cd6e0f3952397f62431cf2cce1ad543bb1c5ee321f249049f3141ca51f191576`), version
      "1.0.0", and an empty/`[]` dependencies list (the body calls no other skill/agent
      by name). Run `python scripts/generate_docs.py` and
      `PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py` to confirm sync.

  Priority 2 (trigger — cross-skill signposting, description-only fix):
    - Add one clause to the `description` field distinguishing this skill's scope from
      `bug-triage-discipline.md`'s passive sibling-audit requirement — e.g., name the
      case where a sweep is needed independent of formal issue-filing, or explicitly
      mid-diagnosis before an issue exists. Consider naming `systematic-debugging` as
      the predecessor step for cases where root cause isn't yet isolated (also closes
      finding 3).

  Priority 3 (output — STEP additions, body-only fix, no frontmatter/registry impact):
    - Add a STEP 0 (or a leading clause in STEP 1) precondition check: "If the root
      cause is not yet isolated/confirmed, STOP and run `/systematic-debugging` first —
      this skill assumes a diagnosed class, not a suspected one."
    - Amend STEP 4 with an existing-issue lookup before filing a residual (avoid
      duplicate residual issues on repeat invocations of the same class).
    - Amend STEP 4 with a grouping heuristic for high-hit-count sweeps (e.g., "group by
      module/owning-team when hits exceed ~10-15, rather than one issue per hit").

Note: findings 2-5 are reported per the eval-workflow mandate ("report findings instead"
of editing SKILL.md) — no changes were made to the skill file itself during this evaluation.
