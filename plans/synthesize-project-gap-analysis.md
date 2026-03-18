# Gap Analysis: /synthesize-project Skill Workflow

**Date:** 2026-03-17
**Scope:** Full workflow analysis of SKILL.md (Steps 0-10), recommend.py, CLAUDE.md.template, registry/patterns.json
**Trigger:** Downstream projects receiving CLAUDE.md files that reference non-existent rule files (dangling references)

---

## Executive Summary

The /synthesize-project skill has **3 high-severity gaps** and **8 medium-severity gaps**. The most critical issue is a split-brain problem between CLAUDE.md.template (hardcoded rules table) and recommend.py (dynamic rules table generator). On fresh provision, the template stale hardcoded table is used instead of the dynamic one, causing dangling file references.

---

## Per-Step Analysis

### STEP 0: Determine Source

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-01 | No hub freshness check | Low | SKILL.md | No check for uncommitted changes or stale hub |

### STEP 1: Provision Hub Patterns

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-02 | **Hardcoded rules table on fresh provision** | **HIGH** | recommend.py | Case 1 in provision_claude_md() renders template as-is. The hub_section (dynamic) is computed on line 1600 but never used in Case 1. Template lines 81-122 contain a stale hardcoded rules table. |
| G-03 | **rule-writing-meta.md in template but not on disk** | **HIGH** | template | Template references rules/rule-writing-meta.md which does not exist in core/.claude/rules/ or registry. |
| G-04 | Hardcoded counts in template | Medium | template | 99 skills, 16 agents, 14 rules -- stale numbers, not actual copy counts. |
| G-05 | Hardcoded skills table in template | Medium | template | Skills listed may not be in must-have tier and may not be copied. |
| G-06 | recommend.py warnings not captured | Low | SKILL.md | WARNING output for missing rules not parsed by the skill. |

### STEP 2: Audit CLAUDE.md Sections

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-07 | **Heading-only audit misses file references** | **HIGH** | SKILL.md | Step 2 compares ## headings only. Does NOT validate rules table entries point to actual files. |
| G-08 | No rules table vs filesystem reconciliation | Medium | SKILL.md | Rules table may list rules not copied due to tiering. No cross-check. |
| G-09 | Hub-managed section treated as opaque | Medium | SKILL.md | Step 2b skips hub marker content. recommend.py only fixes Cases 2/3, not Case 1. |

### STEP 3: Map the Project

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-10 | No stale rules table detection in --update | Low | SKILL.md | Previous provision dangling references persist undetected. |

### STEP 4: Identify Conventions

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-11 | Dedup by concept not file existence | Medium | SKILL.md | Hub rule may not be copied yet still suppresses a candidate. |
| G-12 | No dedup against hardcoded skills table | Low | SKILL.md | CLAUDE.md claims may overlap with synthesized candidates. |

### STEPS 5-6: Evidence / Reference Material

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-14 | Hub-only rule paths referenced | Low | SKILL.md | Step 6 paths point to .claude/rules/ (hub-only), not core/.claude/rules/. |

### STEP 7: Generate Patterns

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-15 | Quality checks skip CLAUDE.md consistency | Medium | SKILL.md | Individual pattern checks, no holistic CLAUDE.md validation. |

### STEP 8: Validate and Write

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-16 | No post-write CLAUDE.md reconciliation | Medium | SKILL.md | Synthesized rules not added to CLAUDE.md rules table. |
| G-17 | No filesystem integrity check | Low | SKILL.md | No verification that CLAUDE.md references match disk. |

### STEP 10: Summary

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-19 | No warnings in summary format | Medium | SKILL.md | No place to surface dangling references or integrity issues. |

---

## Cross-Cutting Gaps

### A. Root Cause: Split-Brain

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-20 | **Two sources of truth for hub section** | **HIGH** | recommend.py + template | (1) CLAUDE.md.template lines 81-122 for Case 1. (2) generate_hub_practices_section() lines 1543-1583 for Cases 2/3. Not kept in sync. |

### B. Failure Scenarios

**Scenario 1: Rule in template but NOT on disk** (exact bug)
- Case 1 renders template as-is, rule-writing-meta.md appears in table
- apply_to_local() never copies it (does not exist)
- Result: **Dangling reference**

**Scenario 2: Rule copied but not in template** (e.g., tdd.md)
- Case 1 shows only 5 hardcoded rules; tdd.md invisible in CLAUDE.md
- Result: **Missing reference** (Cases 2/3 are correct)

**Scenario 3: Rule in template but tiered as nice-to-have**
- claude-behavior.md not in MUST_HAVE_RULES, may not be copied
- Template always lists it
- Result: **Dangling reference on must-have-only provisions**

### C. Registry Consistency

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-21 | rule-writing-meta absent from registry | Medium | registry + template | Template references it, registry and disk do not have it. |
| G-22 | MUST_HAVE_RULES too narrow | Medium | recommend.py | Only context-management is must-have. Template presents 5 rules as core. |

### D-E. Dedup and Quality Gaps

| # | Gap | Severity | Component | Description |
|---|-----|----------|-----------|-------------|
| G-23 | Dedup by concept not file presence | Medium | SKILL.md | False negative if hub rule was not copied. |
| G-24 | No end-to-end integrity validation | Medium | SKILL.md | No holistic check of CLAUDE.md vs disk state. |

---

## Recommended Fix Priority

1. **G-02 + G-03 + G-20** (root cause): Make provision_claude_md() always use the dynamic generator, even in Case 1. Template should have a placeholder, not hardcoded hub content.

2. **G-07 + G-08**: Add file-reference validation to Step 2. Check every path in the rules table against .claude/ directory.

3. **G-16 + G-24**: Add post-write reconciliation. Validate CLAUDE.md rules table after all writes complete.

4. **G-04 + G-05**: Make template skills table and counts dynamic.

---

## Files Involved

- **SKILL.md**: .claude/skills/synthesize-project/SKILL.md
- **CLAUDE.md.template**: core/.claude/CLAUDE.md.template (lines 81-122)
- **recommend.py**: scripts/recommend.py (lines 1543-1643)
- **registry/patterns.json**: registry/patterns.json