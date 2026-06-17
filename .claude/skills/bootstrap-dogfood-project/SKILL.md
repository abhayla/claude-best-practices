---
name: bootstrap-dogfood-project
description: >
  Wire a downstream/dogfood app repo into the hub's feedback loop and VERIFY all
  five preconditions are green before the app is declared "set up". Closes the
  silent loophole where an app improves locally but nothing flows back to the
  hub. Use right after creating/synthesizing a new app repo that should feed
  patterns + telemetry back to this hub, before its first feature commit.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<owner/app-repo or /path/to/app> [--verify-only]"
version: "1.0.0"
---

# /bootstrap-dogfood-project — wire + verify the project→hub feedback loop

This is a **hub-only** operational skill: it edits the hub's `config/repos.yml`
and inspects a downstream app repo. It is NOT distributed to projects (it has no
meaning inside a consumer project). Its STEP 6 gate is the deterministic
replacement for the prose checklist in `plans/idea-to-deploy-readiness.md` —
the app is NOT "set up" until all five preconditions verify green.

**Why it exists:** the four project→hub feedback flows (`/contribute-practice`,
`collate.py`, `aggregate_telemetry.py`, `/synthesize-hub`) each assume
preconditions that, if unset at project birth, silently sever the loop — the app
gets better locally and the hub learns nothing. This skill sets them and refuses
to pass until they hold.

**Input:** `$ARGUMENTS` — the app repo (`owner/name` for a GitHub repo, or a
local path). `--verify-only` checks without mutating.

---

## STEP 1: INIT

1. Resolve the **hub root** (`git rev-parse --show-toplevel` from this repo) and
   confirm `config/repos.yml` exists — if not, this is not the hub; STOP.
2. Resolve the **app repo**: GitHub slug `owner/name`, or a local path. Capture
   both the slug and (if local) the working dir.
3. Initialize a verdict accumulator: five checks, each `unset → pass|fail`.

## STEP 2: GitHub remote (the app must be API-visible)

The hub's aggregators (`collate.py`, `aggregate_telemetry.py`) read the app via
the **GitHub API** — a local-only repo is invisible.

- Verify the app has a pushed GitHub remote: `gh repo view <owner/name>`.
- **If missing:** creating/pushing a repo is an outward action — BLOCK this
  check with the one-line instruction to `gh repo create` + push, and record
  `github_remote: fail`. Do not fabricate the repo silently.

## STEP 3: Enroll in the hub's `config/repos.yml`

- Read `config/repos.yml`; if the app slug is absent, add its entry (match the
  existing schema of neighboring entries — do not invent fields).
- `--verify-only` → only report presence, do not edit.
- Record `enrolled: pass|fail`.

## STEP 4: Committed, non-ignored `.claude/learnings.json`

The hub reads the **committed** learnings file; a gitignored one emits ZERO
signal (loop-engineering's #1 silent failure).

- In the app repo: confirm `.claude/learnings.json` exists (seed `{"learnings": []}`
  if not), is NOT matched by any `.gitignore` rule, and is tracked by git
  (`git ls-files --error-unmatch .claude/learnings.json`).
- A gitignored or untracked learnings file is a **hard fail** — record
  `learnings_committed: fail` with the exact reason.

## STEP 5: `allow_hub_sharing: true` in the app's `.claude/synthesis-config.yml`

- Ensure the app's `.claude/synthesis-config.yml` sets `allow_hub_sharing: true`
  (required for `/synthesize-hub` to pull its `synthesized: true` patterns).
- Record `hub_sharing: pass|fail`.

## STEP 6: Routing discipline declared

- Confirm the app's `CLAUDE.md` (or a rule) states the `learnings-routing.md`
  split: GENERIC learnings flow hub-ward, PRODUCT-SPECIFIC stay local. Add a
  one-line pointer if absent.
- Record `routing_declared: pass|fail`.

## STEP 7: VERIFY GATE (the deterministic close)

Re-check all five. Emit a verdict and **refuse to declare ready on any fail**:

```
============================================================
Dogfood bootstrap: <READY | BLOCKED>
  app: <owner/name>
  [✓|✗] github_remote       [✓|✗] enrolled (config/repos.yml)
  [✓|✗] learnings_committed [✓|✗] hub_sharing
  [✓|✗] routing_declared
  Blockers: <list or none>
============================================================
```

`READY` only when all five are `✓`. On any `✗`, output `BLOCKED` with the exact
fix per blocker and STOP — the feedback loop is not wired until they are green.

---

## CRITICAL RULES

- MUST verify all five preconditions; MUST output `BLOCKED` (never `READY`) if any fails.
- MUST treat a gitignored or untracked `.claude/learnings.json` as a hard fail — it is the silent-loophole root cause.
- MUST NOT silently create/push the app's GitHub repo — that outward action is escalated to the user with a one-line instruction.
- MUST match the existing `config/repos.yml` entry schema when enrolling — do not invent fields.
- MUST run only from the hub repo (where `config/repos.yml` lives); this skill is hub-only and MUST NOT be distributed to consumer projects.
- MUST re-run cleanly (idempotent): an already-wired repo verifies `READY` without duplicate edits.
