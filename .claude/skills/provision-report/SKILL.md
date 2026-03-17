---
name: provision-report
description: >
  Reference guide for the canonical provision summary format used by recommend.py
  and /synthesize-project. Defines the 4-section tabular layout with Type, Name,
  Action, and Reason columns. Consult when building or modifying any provisioning
  output to ensure format consistency.
type: reference
allowed-tools: "Read Grep Glob"
version: "1.0.0"
---

# Provision Report Format Standard

Reference specification for the provision summary output format. All provisioning
operations (`recommend.py --provision`, `/synthesize-project`, `/synthesize-hub`)
MUST produce output conforming to this format.

## Origin

This format was created after the 3-layer tiering upgrade (2026-03-16) when
`recommend.py --provision` against AlgoChanakya produced output that lacked
visibility into WHY each pattern was selected or skipped. The user requested
Type, Name, Action, and Reason columns to make provisioning decisions reviewable
and auditable. The format is now enforced by `tier_resource_with_reason()` in
`scripts/recommend.py`.

---

## Report Structure

Every provision report has 4 sections printed in this order:

1. **Tier tables** — one per non-empty tier (must-have, improved, nice-to-have, skip)
2. **Config status** — CLAUDE.md, settings.json (local mode only)
3. **PR links** — with action hints (remote mode only)
4. **Totals** — single-line count per tier

## Tier Table Format

Each tier section uses a fixed-width tabular layout:

```
--- MUST-HAVE (N) ---
  Type     Name                                     Action                 Reason
  ----     ----                                     ------                 ------
  skill    tailwind-dev                             add (new)              dependency detected in project
  skill    vue-dev                                  add (new)              dependency detected in project
  rule     context-management                       add (new)              core rule
```

### Column Definitions

| Column | Width | Content |
|--------|-------|---------|
| Type | 8 chars, left-aligned | One of: `skill`, `agent`, `rule`, `hook` |
| Name | 40 chars, left-aligned | Pattern name (kebab-case) |
| Action | 22 chars, left-aligned | What will happen to this pattern |
| Reason | variable | Why this tier was assigned |

### Action Values

| Tier | Action Value | Meaning |
|------|-------------|---------|
| must-have | `add (new)` | New pattern, not in project yet |
| improved | `upgrade (hub newer)` | Hub has a newer version, overwrites existing |
| nice-to-have | `optional` | Available but not auto-applied |
| skip | `skip` | Not relevant to this project |

### Reason Values

Reasons explain WHY a pattern was placed in its tier. Every item MUST have a non-empty reason.

| Reason | Meaning |
|--------|---------|
| `dependency detected in project` | `DEP_PATTERN_MAP` matched a project dependency (e.g., vue in package.json promoted vue-dev) |
| `matches detected stack` | Stack prefix matches auto-detected stack (e.g., fastapi-db-migrate for fastapi-python stack) |
| `core workflow skill` | In `CORE_WORKFLOW_SKILLS` set (implement, fix-loop, tdd, etc.) |
| `core rule` | In `MUST_HAVE_RULES` set (context-management, rule-writing-meta) |
| `core agent` | In `MUST_HAVE_AGENTS` set (security-auditor-agent) |
| `essential safety hook` | In `MUST_HAVE_HOOKS` set (dangerous-command-blocker, secret-scanner) |
| `useful but optional` | In `NICE_TO_HAVE_UNIVERSAL_SKILLS` set |
| `optional skill/rule/agent/hook` | Universal pattern not in any priority list |
| `stack override (not essential)` | In `NICE_TO_HAVE_STACK_OVERRIDES` (matches stack but downgraded) |
| `wrong stack` | Stack-prefixed pattern that doesn't match project's stacks |
| `always-skip list` | In `ALWAYS_SKIP` set (meta skills, wrong-domain) |
| `hub vX.Y.Z > project vA.B.C` | Improved tier: hub version is newer |
| `project has no version, hub has vX.Y.Z` | Improved tier: project pattern lacks version |
| `same version (X.Y.Z) but different content` | Improved tier: content diverged at same version |

## Config Status Section (Local Mode)

```
--- CONFIG ---
  CLAUDE.md:     created|replaced|appended|skipped
  settings.json: created|merged|skipped

  Files copied: N
```

## PR Links Section (Remote Mode)

```
--- PRs CREATED ---
  must-have      https://github.com/owner/repo/pull/N (merge confidently)
  improved       https://github.com/owner/repo/pull/N (review diffs)
  nice-to-have   https://github.com/owner/repo/pull/N (check boxes, comment /apply)
```

If a PR was skipped (empty tier or PR already exists):
```
  improved       (skipped)
```

## Totals Line

Always the last line before the closing ruler:

```
TOTAL: N must-have, N improved, N nice-to-have, N skip
====================================================================================================
```

## Sort Order

Within each tier table, items are sorted by:
1. **Type** (alphabetical: agent, hook, rule, skill)
2. **Name** (alphabetical within type)

## Implementation Reference

The canonical implementation lives in `scripts/recommend.py`:

- `tier_resource_with_reason()` — returns `(tier, reason)` tuples
- `analyze_gaps()` — populates `reason` field on every gap item
- `main()` Step 6b — prints the summary using the format above

Any new provisioning pathway (new scripts, skills, or agents that produce provision output)
MUST call these functions or replicate this exact format.

## Validation Checklist

When reviewing provision output, verify:

- [ ] Every tier section has the 4-column header (Type, Name, Action, Reason)
- [ ] No pattern appears in more than one tier
- [ ] Reason is never empty — every item has an explanation
- [ ] Sort order is type-then-name alphabetical
- [ ] Totals line counts match the actual items listed
- [ ] Remote mode shows PR URLs; local mode shows config status
- [ ] Dep-promoted patterns show "dependency detected in project" as reason
- [ ] Improved patterns show version comparison as reason

## MUST DO

- MUST include all 4 columns (Type, Name, Action, Reason) in every tier table
- MUST provide a non-empty Reason for every pattern — never leave it blank
- MUST sort by type then name alphabetically within each tier
- MUST show the totals line matching actual counts
- MUST use the exact Action values from the table above (not freeform text)
- MUST show PR URLs in remote mode with action hints in parentheses

## MUST NOT DO

- MUST NOT omit the Reason column or use generic reasons like "recommended"
- MUST NOT mix patterns from different tiers in the same table section
- MUST NOT show config status (CLAUDE.md, settings.json) in remote mode output
- MUST NOT show PR links in local mode output
- MUST NOT change column widths without updating this spec (breaks alignment for scripts parsing the output)
- MUST NOT add new Action values without updating both `recommend.py` and this reference
