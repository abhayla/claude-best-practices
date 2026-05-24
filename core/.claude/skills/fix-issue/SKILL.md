---
name: fix-issue
description: Route deprecated /fix-issue invocations to the renamed /fix-github-issue skill. Use when any existing caller (downstream project, eval scenario, agent body) still references the old name; this stub forwards verbatim and prints a one-time migration notice. Removed at fix-github-issue v5.0.0.
type: workflow
deprecated: true
deprecated_by: fix-github-issue
deprecated_since: "2026-05-24"
removal_target: "fix-github-issue v5.0.0"
allowed-tools: "Skill"
argument-hint: "<forwarded to /fix-github-issue verbatim>"
version: "2.6.1"
---

# fix-issue (Deprecated)

This skill has been renamed to **`fix-github-issue`** to reflect that it is GitHub-specific.
The original name was ambiguous — it could plausibly mean any issue tracker.
The skill body has always been GitHub-only: it calls `gh issue view`, expects GitHub Issue URLs, and writes commit messages with `fix: resolve #N` referencing GitHub Issue numbers.

## STEP 1: Forward to the new skill

Forward `$ARGUMENTS` unchanged to the new skill:

```
Skill("fix-github-issue", args="$ARGUMENTS")
```

That single call performs every step of the original workflow.
The flow is unchanged — fetch issue, diagnose, implement, verify, finalize.
No argument transformation is required: the new skill accepts the same `<issue-number-or-url> [--diff-only]` shape.

## STEP 2: Print a one-line migration notice

After forwarding, print exactly:

```
NOTE: /fix-issue is deprecated — please use /fix-github-issue going forward.
```

The notice runs once per invocation.
It helps callers notice the rename without breaking the immediate workflow.

## STEP 3: Return whatever the new skill returns

Pass through the return contract from `/fix-github-issue` unchanged.
Existing callers (test-healer-agent, test-pipeline, downstream projects) keep working during the transition window.
Do not transform, filter, or augment the return — the stub is transparent.

## Removal lifecycle (per pattern-structure.md SemVer policy)

- **2026-05-24** — deprecated, this stub installed at v2.6.1
- **fix-github-issue v4.x.x** — stub still present; deprecation notice printed on every invocation
- **fix-github-issue v5.0.0** — stub removed; `/fix-issue` returns "skill not found"

Downstream projects should migrate during the v4.x.x window.
Run `/update-practices` to pull the new skill into your project's `.claude/`.
Then run `grep -r "fix-issue" .claude/` to find local references that need updating.
The CI validator (`workflow_quality_gate_validate_patterns.py`) will flag any remaining references at PR time.

## CRITICAL RULES

- MUST forward all arguments verbatim — the stub adds nothing of its own to the call
- MUST NOT duplicate the fix-github-issue body here — single source of truth lives at core/.claude/skills/fix-github-issue/SKILL.md
- MUST NOT remove this stub before fix-github-issue v5.0.0 — downstream consumers need the deprecation window
- MUST print the migration notice after forwarding so callers see the rename signal
