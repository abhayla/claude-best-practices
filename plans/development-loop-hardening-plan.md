# Implementation Plan: Make `/development-loop` foolproof & 100% usable for any downstream project

**Created:** 2026-06-15
**Owner role:** Architect → (per phase) Delivery PM / Full-Stack / QA
**Approval gate:** user approves THIS plan, then execution runs autonomously through PR + merge (basic approvals waived by user).
**Companion files:** `development-loop-hardening-findings.md`, `development-loop-hardening-progress.md`

---

## Goal contract (Definition of Done)

`/development-loop` is "done" when ALL hold:

1. A **freshly provisioned** sample downstream project (created on disk, NOT pre-seeded by the hub) can run `/development-loop "<small feature>"` and reach a **PASSED** verdict with a real commit — with **zero manual fixups** to the provisioned `.claude/`.
2. It works on **≥2 structurally different stacks** (primary: Node+TS/vitest; cross-check: Python/pytest) — proving genericity, not just one happy path. No hub-specific or single-stack assumption remains (no hardcoded `src/`, no hub paths).
3. Every dependency the skill dispatches (`plan-executor-agent`, `planner-researcher-agent`, sub-skills `brainstorm`/`writing-plans`/`auto-verify`/`post-fix-pipeline`) is **declared correctly** and **co-provisioned** as a closure; a missing worker is caught by a **preflight BLOCK**, never a silent mid-run failure.
4. All hub CI gates green (`dedup_check --validate-all`, `--secret-scan`, `workflow_quality_gate_validate_patterns`, `pytest`), docs regenerated.
5. Merged to `main` via PR using best practices (branch, conventional commits, <400-line-focused commits, green CI).

**Co-tested skill (per user, 2026-06-15):** the sandbox is provisioned through the **`/synthesize-project` skill** — the real downstream provisioning path — NOT a raw `recommend.py` call. This makes `/synthesize-project` a **second unit-under-test**: any defect it surfaces is (a) fixed in-hub if it BLOCKS the development-loop validation (reversible/clear), and (b) **reported to the user** regardless (blocking or not), since synthesize-project is its own skill with its own correctness bar.

**Out of scope:** the other 7 workflows (verified later, separately); rewriting auto-verify's runner detection beyond what's needed for the 2 test stacks; deep synthesize-project hardening beyond what this validation surfaces (non-blocking synthesize-project issues are reported, not necessarily fixed in this PR).

---

## Phase structure

Known-cause fixes are enumerated (Phase 0–1). The validation loop (Phase 2–3) is **discovery-driven** — exact fixes emerge from running the workflow — so it's specified as a protocol with a DoD, not pre-faked task IDs (honest planning: we cannot list bugs we haven't reproduced yet).

```
Phase 0  Setup & branch ............... critical path start
Phase 1  Fix known issues (5 fixes) ... depends on P0
Phase 2  Build sample downstream ...... depends on P1
Phase 3  Run → fix → re-provision LOOP  depends on P2  (the heart)
Phase 4  Genericity cross-check (2nd stack) ... depends on P3 green
Phase 5  CI green + docs + PR + merge .. depends on P4
```

---

## Phase 0 — Setup

### Task 0.1: Branch + todo + progress log
- **Files:** none (git) ; append to `plans/development-loop-hardening-progress.md`
- **Do:** `git stash` the 2 in-flight doc edits OR fold them in; create branch `chore/harden-development-loop`.
- **Verify:** `git branch --show-current` = `chore/harden-development-loop`; `git status` clean except plan files.
- **Estimate:** O2/E3/P6 — **Rollback:** `git checkout main && git branch -D chore/harden-development-loop`

### Task 0.2: Map the `/synthesize-project` provisioning path + closure mechanism (resolves Finding #4)
- **Files (read):** `core/.claude/skills/synthesize-project/SKILL.md`, `scripts/recommend.py`, `scripts/bootstrap.py`, `scripts/third_party_skills.py`
- **Do:** Read what `/synthesize-project --local` actually does end-to-end (hub-provision + project-specific synthesis), and whether it co-provisions a skill's dependency closure and from which source (registry `dependencies` vs live scan). Record verdict + any synthesize-project smell in findings.
- **Verify:** written conclusion in `findings.md` with file:line evidence; note `--repo`/`--local` requirement when run from the hub.
- **Estimate:** O8/E15/P30 — **Rollback:** n/a (read-only)

---

## Phase 1 — Fix known issues

### Task 1.1: Correct the registry dependency closure (Finding #1)
- **Files:** `registry/patterns.json` (`development-loop.dependencies`)
- **Do:** Replace `["development-loop-master-agent","brainstorm","writing-plans","executing-plans","auto-verify","post-fix-pipeline"]` with the TRUE runtime closure: `["brainstorm","writing-plans","auto-verify","post-fix-pipeline","plan-executor-agent","planner-researcher-agent"]`. Remove deprecated master-agent + unused executing-plans.
- **Verify:** `python -c "import json;d=json.load(open('registry/patterns.json',encoding='utf-8'));print(d['development-loop']['dependencies'])"` shows the corrected list; `dedup_check --validate-all` passes.
- **Estimate:** O2/E4/P8 — **Rollback:** `git checkout HEAD -- registry/patterns.json`

### Task 1.2: Add PREFLIGHT step to the skill (Finding #2)
- **Files:** `core/.claude/skills/development-loop/SKILL.md` (new `## STEP 0.5: PREFLIGHT`, bump version 2.0.0→2.1.0)
- **Do:** Before IDEATE, probe that required sub-skills + worker agents are runtime-dispatchable; BLOCK with `WORKER_REGISTRY_NOT_LOADED` + a one-line provisioning hint (`/update-practices` then restart) if any are missing. Mirror the `/test-pipeline` early-probe pattern.
- **Verify:** SKILL renders the step; `workflow_quality_gate_validate_patterns.py` passes (frontmatter + cross-refs); manual: simulate a missing agent → BLOCK message appears.
- **Estimate:** O8/E15/P30 — **Rollback:** `git checkout HEAD -- core/.claude/skills/development-loop/SKILL.md`

### Task 1.3: De-assume `src/` in the contract (Finding #3)
- **Files:** `config/workflow-contracts.yaml` (`development-loop.steps[execute].artifacts_out.source.path`)
- **Do:** Change binding `"src/"` to a project-detected source root (or mark descriptive/non-binding). Confirm no gate expression depends on the literal `src/`.
- **Verify:** `python -c "import yaml;d=yaml.safe_load(open('config/workflow-contracts.yaml',encoding='utf-8'));print(d['workflows']['development-loop']['steps'][2]['artifacts_out'])"`; validator passes.
- **Estimate:** O3/E6/P12 — **Rollback:** `git checkout HEAD -- config/workflow-contracts.yaml`

### Task 1.4: Provisioning ships closure + gitignores runtime dirs (Findings #4/#5)
- **Files:** depends on 0.2 verdict — likely `scripts/recommend.py`/`bootstrap.py` (closure provisioning) + a `.gitignore` template for `.workflows/`, `test-results/`, `test-evidence/`
- **Do:** Ensure provisioning a skill pulls its corrected closure (agents+sub-skills) AND adds runtime-artifact dirs to the target `.gitignore`. Minimal change — only if 0.2 shows a gap.
- **Verify:** add/extend a `scripts/tests/` unit test asserting closure provisioning for `development-loop`; `pytest scripts/tests/ -k provision`.
- **Estimate:** O10/E25/P60 — **Rollback:** `git checkout HEAD -- <touched scripts>`

### Task 1.5: Commit Phase 1
- **Verify:** all 4 hub gates green locally. **Rollback:** `git reset --soft HEAD~1`

---

## Phase 2 — Build the sample downstream project

### Task 2.1: Create sandbox on disk (NOT inside the hub working tree)
- **Path:** `../dev-loop-sandbox-node/` (sibling dir, its own git repo) — **Assumption:** sibling dir keeps hub diff clean; if undesirable, `sandboxes/` (gitignored) is the fallback.
- **Do:** `git init` a minimal Node+TS project: one pure-logic module with an intentionally tiny gap + vitest wired (`npm test`). Real, runnable on Windows.
- **Verify:** `npm test` runs and reports (a failing/placeholder test is fine pre-feature).
- **Estimate:** O10/E20/P45 — **Rollback:** `rm -rf ../dev-loop-sandbox-node`

### Task 2.2: Provision the sandbox via the `/synthesize-project` SKILL (per user)
- **Do:** Invoke `Skill("/synthesize-project", args="--local ../dev-loop-sandbox-node --skip-synthesis"-or-full)` from this hub T0 session — the REAL downstream path a user runs. No manual hand-copying of `.claude/`. Capture every synthesize-project step + any error/oddity to `progress.md`.
- **Verify:** sandbox `.claude/` contains development-loop + corrected closure (both agents + 4 sub-skills); `.gitignore` has runtime dirs. Record whether closure travelled correctly (validates Task 1.4 through the real skill).
- **On synthesize-project defect:** if it BLOCKS provisioning → root-cause + fix in `core/`, re-run; **always** add the finding to the "synthesize-project issues" report for the user.
- **Estimate:** O8/E20/P50 — **Rollback:** delete sandbox `.claude/`

---

## Phase 3 — Run → fix → re-provision LOOP (the heart)

**Protocol (repeat until DoD #1 met, max 8 iterations then escalate):**

1. From T0, run `/development-loop "<the small feature>"` against the sandbox.
2. Observe EVERY step (INIT→PREFLIGHT→IDEATE→PLAN→EXECUTE→VERIFY→COMMIT→REPORT). Capture the failing step + exact error to `progress.md`.
3. Root-cause in the **hub** (never patch the sandbox `.claude/` directly — that hides the real defect; fix in `core/`, re-provision).
4. Re-provision the sandbox from the hub; re-run.
5. Each fix: if mechanically enforceable, add a hub test/validator so it can't regress (learnings-routing: prefer a gate over prose).
6. Stop when a full run reaches **PASSED** with a real sandbox commit, zero manual `.claude/` edits.

- **Verify (exit):** `test-results/development-loop-verdict.json` in sandbox shows `result: PASSED`; `git -C ../dev-loop-sandbox-node log` shows the feature commit; re-run is idempotent/clean.
- **Estimate:** O30/E90/P240 (discovery-bound) — **Rollback:** revert hub fix commits per iteration (each iteration is its own checkpoint commit).

---

## Phase 3.5 — Coverage matrix (prove ALL paths, not one happy path)

Runs after the first PASSED happy-path run (Phase 3 exit), in the same Node sandbox.

### Task 3.5.1: Complexity-router + flag matrix
- **Do:** Run `/development-loop` for a **Simple** task (expect EXECUTE→VERIFY→COMMIT, ideate+plan skipped), a **Medium** task (expect PLAN→…), a **Complex** task (all 5 steps), and once with `--no-commit` (stops after VERIFY).
- **Verify:** each run's `development-loop-verdict.json` `steps_executed`/`steps_skipped` matches the expected routing; `--no-commit` leaves no commit.
- **Estimate:** O15/E35/P90 — **Rollback:** reset sandbox git.

### Task 3.5.2: PREFLIGHT-BLOCK negative test (proves the safety net fires)
- **Do:** Provision development-loop into a scratch sandbox with `plan-executor-agent` deliberately ABSENT; run `/development-loop`.
- **Verify:** it BLOCKs at STEP 0.5 with `WORKER_REGISTRY_NOT_LOADED` + the provisioning hint — NOT a silent inline run or a mid-EXECUTE crash.
- **Estimate:** O8/E15/P30 — **Rollback:** delete scratch sandbox.

### Task 3.5.3: Re-run idempotency
- **Do:** Run the same feature twice; confirm distinct `run_id`s, clean state, no double-commit/corruption.
- **Verify:** second run starts clean; state file + events.jsonl consistent.
- **Estimate:** O5/E10/P20 — **Rollback:** reset sandbox git.

## Phase 4 — Genericity cross-check

### Task 4.1: Second stack (Python/pytest) sandbox, same loop
- **Do:** Repeat Phase 2–3 with `../dev-loop-sandbox-py/` (pytest), **also provisioned via `/synthesize-project --local`**. Confirms no Node-specific assumption leaked in AND that synthesize-project provisions correctly for a second stack.
- **Verify:** PASSED verdict + commit in the Python sandbox with the SAME provisioned skill.
- **Estimate:** O20/E45/P120 — **Rollback:** delete sandbox.

### Task 4.1b: `/update-practices` upgrade-path check (hub→project update path)
- **Do:** In a sandbox holding the PRE-fix development-loop, run `/update-practices` to pull the corrected closure from the hub.
- **Verify:** the corrected closure (real workers, no deprecated master-agent) lands; the restart-required warning fires (agent registry session-pinning); a subsequent run reaches PASSED. Validates the real downstream UPGRADE experience, not just first-provision.
- **Estimate:** O8/E18/P40 — **Rollback:** delete sandbox `.claude/`.

### Task 4.2: Static portability audit
- **Do:** `/pattern-quality` on the changed skill/contract; grep the skill+contract for any hub/stack-specific literal.
- **Verify:** pattern-quality clean; no hardcoded path/stack reference.
- **Estimate:** O5/E10/P20 — **Rollback:** n/a

---

## Phase 5 — Land it

### Task 5.1: Full local CI replication + docs
- **Do:** run the 4 gate commands + `generate_docs.py` + `generate_workflow_docs.py`.
- **Verify:** all green; docs diff is only the intended changes.
### Task 5.2: PR + merge
- **Do:** push branch, open PR (motivation/approach/test-plan/rollback), ensure CI green, squash-merge to main (user pre-authorized the merge).
- **Verify:** PR merged; `main` CI green.
- **Estimate:** O10/E20/P45 — **Rollback:** `git revert` the squash commit.

---

## Dependency graph & critical path

```
0.1 → 0.2 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 2.1 → 2.2 → [P3 loop] → 4.1 → 4.2 → 5.1 → 5.2
                    └ 1.1/1.2/1.3 are parallelizable after 0.2 (independent files)
```
Critical path ≈ Phase 3 loop (discovery-bound). Expected wall-clock dominated by P3/P4; the rest ~2–3h.

## Top risks
- **R1 — auto-verify can't detect the sandbox test runner** → development-loop can't verify generically. Mitigation: pick stacks auto-verify already supports (vitest, pytest); if it fails, that's an in-scope hub fix surfaced by the loop.
- **R2 — provisioning doesn't co-provision closures at all** (0.2 may reveal). Then 1.4 grows from "fix list" to "add closure provisioning" — still in scope, flagged here.
- **R3 — running development-loop at T0 dispatches real workers that edit the sandbox**; ensure all writes are confined to the sandbox dir, never the hub. Supervisor-verification gate on every worker return.
- **R4 — discovery loop exceeds 8 iterations** → escalate with an honest status (don't fake green).
- **R5 — `/synthesize-project` itself is broken** (it's now the provisioning vehicle). A blocking synthesize-project bug stalls the whole validation. Mitigation: fix blocking synthesize-project defects in-hub (reversible, clear) to proceed; collect ALL synthesize-project findings (blocking + non-blocking) into a **"synthesize-project issues" report** delivered to the user at the end, per the user's explicit ask. Non-blocking fixes are proposed, not bundled into this PR (keeps the PR single-purpose per git-collaboration.md).
