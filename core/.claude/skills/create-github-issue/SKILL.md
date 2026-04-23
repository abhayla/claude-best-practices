---
name: create-github-issue
description: >
  Create a GitHub Issue from a structured failure profile (per spec test-pipeline-three-lane PR2).
  Use when the test pipeline (or any agent) needs to surface a failure as a tracked work item.
  Hard-fails the caller if GitHub is not connected — no silent skip. Includes 4 preflight checks
  (gh installed, gh authenticated, origin is github.com, token has write access). Honors
  3-field sha256 dedup (`test_id + category + failing_commit_sha_short`) over a 30-day window;
  comments on the existing Issue when a duplicate is detected. Builds a consolidated body
  template covering all 3 test pipeline lanes (functional/api/ui).
type: workflow
allowed-tools: "Bash Read"
argument-hint: "<failure-profile-json-path>"
version: "1.0.0"
---

# Create GitHub Issue — Universal Skill

Single source of truth for GitHub Issue creation in the three-lane test pipeline. Replaces
the inline step that lived in `testing-pipeline-master-agent` (T1) pre-PR2.

**Request:** $ARGUMENTS — path to a JSON file with the failure profile (see § Inputs below).

> Spec reference: `docs/specs/test-pipeline-three-lane-spec.md` v1.6 §3.7

---

## STEP 0: Preflight (HARD FAIL)

Run these 4 checks before any `gh` call. Any check fails → return structured `GITHUB_NOT_CONNECTED` contract immediately. Do NOT silently skip Issue creation; do NOT degrade gracefully — the caller MUST know.

| # | Check | Command | Failure remediation |
|---|---|---|---|
| 1 | `gh` installed | `command -v gh` | Install from https://cli.github.com/ |
| 2 | `gh` authenticated | `gh auth status` | Run: `gh auth login` |
| 3 | Origin remote is github.com | `git remote get-url origin \| grep -q github.com` | Add a github.com remote (or push the repo there); Issue creation requires GitHub |
| 4 | Token has Issue creation permission | `gh repo view --json viewerPermission -q .viewerPermission` must equal `WRITE` or `ADMIN` (or `MAINTAIN`/`TRIAGE`) | Token lacks Issue creation permission for this repo; obtain a token with `repo` scope |

On any failure, return:
```json
{
  "result": "BLOCKED",
  "blocker": "GITHUB_NOT_CONNECTED",
  "failed_check": "<which preflight check>",
  "remediation": "<actionable command>"
}
```

---

## STEP 1: Parse Inputs

Load the failure profile JSON from `$ARGUMENTS`. Required fields:

```json
{
  "test_id": "tests/api/test_users.py::test_create_user",
  "run_id": "2026-04-23T14-30-00Z_abc1234",
  "failing_commit_sha_short": "abc1234",
  "category": "SCHEMA_MISMATCH",
  "confidence": 0.91,
  "evidence_summary": "Pydantic UserCreate model expects 'full_name' but POST sends 'name'",
  "recommended_action": "AUTO_HEAL | ISSUE_ONLY | QUARANTINE | RETRY_INFRA",
  "failure_profile": {
    "functional": {"result": "FAILED|PASSED|n/a", "error": "...", "stack": "..."},
    "api":        {"result": "FAILED|PASSED|n/a", "error": "...", "stack": "..."},
    "ui":         {"result": "FAILED|PASSED|n/a", "screenshot_path": "...", "visual_review": "..."}
  }
}
```

Optional fields: `pact_diff`, `openapi_diff`, `expected_status_code`, `actual_status_code` (per category).

---

## STEP 2: Compute Dedup Hash + Check for Existing Issue

Compute the 3-field signature:

```bash
SIG=$(printf '%s|%s|%s' "$test_id" "$category" "$failing_commit_sha_short" | sha256sum | cut -c1-12)
```

Search open `pipeline-failure`-labeled Issues from the last 30 days for this signature in the body:

```bash
EXISTING=$(gh issue list \
  --label pipeline-failure \
  --state open \
  --search "in:body $SIG created:>$(date -d '30 days ago' +%Y-%m-%d)" \
  --json number --jq '.[0].number // empty')
```

If `EXISTING` non-empty → Go to STEP 4 (comment on existing). Otherwise → STEP 3 (create new).

---

## STEP 3: Create New Issue

Build the consolidated body using the template below (§ Body Template), then:

```bash
gh issue create \
  --title "{category}: {test_id}" \
  --body "$BODY" \
  --label "pipeline-failure,pipeline-run-{run_id},category-{category},lane-{f,a,u}"
```

(Lane labels: `lane-f` if functional failed, `lane-a` if api failed, `lane-u` if ui failed.)

Capture the new issue number from `gh issue create` stdout. Return:
```json
{"issue_number": <N>, "issue_url": "<url>", "deduped": false}
```

---

## STEP 4: Comment on Existing Issue (Dedup Hit)

Append a comment with the new run_id and timestamp:

```bash
gh issue comment "$EXISTING" --body "Re-occurred in run \`{run_id}\` at \`{timestamp}\`. Failure signature unchanged ($SIG). See pipeline run for fresh evidence."
```

Return:
```json
{"issue_number": <existing_N>, "issue_url": "<url>", "deduped": true}
```

Do NOT create a duplicate Issue. Do NOT close + reopen; just comment.

---

## Body Template

Empty fields render with placeholder text (NOT blank lines) per spec §3.7 G17 closure.

```markdown
# Test Failure: {test_id}

**Pipeline run:** {run_id}
**Failing commit:** `{failing_commit_sha_short}`
**Detected:** {timestamp}
**Category:** {category} (confidence {confidence})
**Recommended action:** {recommended_action}

## Lane Results
| Lane | Result | Details |
|------|--------|---------|
| Functional | {✅/❌/n/a} | {functional.summary or "Working fine" or "(no details captured)"} |
| API        | {✅/❌/n/a} | {api.summary or "Working fine" or "(no details captured)"} |
| UI         | {✅/❌/n/a} | {ui.summary or "Working fine" or "(no details captured)"} |

## Diagnosis
{evidence_summary or "(analyzer did not produce evidence summary)"}

## Failure Details
### Functional Lane (only if FAILED)
```
{functional.stack or "(no stderr captured)"}
```

### API Lane (only if FAILED)
```
{api.contract_diff or api.stack or "(no contract diff or stderr captured)"}
```

### UI Lane (only if FAILED)
{ui.visual_review or "(no visual review captured)"}
[Screenshot]({ui.screenshot_path or "n/a"})

## Reproduction
```bash
# Replay this exact failure (run from project root):
PYTHONPATH=. pytest {test_id} -v
```

## Auto-Fix Status
- {AUTO_HEAL → "Fixer agent dispatched — see commit linked below when fix lands"}
- {ISSUE_ONLY → "No auto-fix attempted — requires human review per auto-fix matrix in spec §3.6"}
- {QUARANTINE → "Tagged @flaky and continued — review weekly"}
- {RETRY_INFRA → "Treated as infrastructure flake; one retry attempted"}

---
**signature:** {SIG}
*Generated by `/create-github-issue` from `/test-pipeline` run `{run_id}`.*
```

---

## CRITICAL RULES

- MUST NOT silently skip Issue creation when preflight fails — return structured BLOCKED contract per STEP 0
- MUST NOT create a duplicate Issue when sha256 signature matches an open `pipeline-failure` Issue from last 30 days — comment instead per STEP 4
- MUST include `failing_commit_sha_short` in the dedup hash (3-field formula) — without it, refactors create false-duplicates per spec §3.7 G9
- MUST NOT modify any files outside the `gh` CLI invocations — read-only against the local filesystem (no `Write`/`Edit` in `allowed-tools`)
- MUST emit valid `gh issue create` labels per the convention: `pipeline-failure`, `pipeline-run-{run_id}`, `category-{category}`, `lane-{f,a,u}` per failed lane
- MUST render empty failure-profile fields with placeholder text, never as blank lines (per spec §3.7 G17)
- MUST NOT depend on any other PR2 component — this skill is the foundational primitive that `github-issue-manager-agent` and any other Issue-creating agent calls
