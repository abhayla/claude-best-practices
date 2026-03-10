---
name: contribute-practice
description: >
  Push a pattern from your project to the best practices hub.
  Validates pattern structure, checks for duplicates, and creates a PR.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<pattern-path>"
---

# Contribute Practice — Submit Pattern to Hub

Validate a local pattern and submit it to the best practices hub as a PR.

**Pattern path:** $ARGUMENTS

---

## STEP 1: Validate Pattern

Read the pattern file and check:

1. **Structure** — Valid YAML frontmatter (for skills/agents) or valid markdown
2. **Required fields** — name, description present
3. **No secrets** — Scan for API keys, tokens, credentials, passwords
4. **No project-specific content** — Flag hardcoded paths, project names, etc.

## STEP 2: Detect Category

Determine pattern type and category:
- Skills: has `SKILL.md` with frontmatter
- Agents: has agent `.md` with frontmatter
- Rules: has `.md` with optional path frontmatter
- Hooks: shell scripts with specific naming

## STEP 3: Check for Duplicates

Compare against hub registry:
1. Content hash comparison
2. Name similarity check
3. Description similarity check

If duplicate found, report and suggest updating existing pattern instead.

## STEP 4: Create PR

1. Fork/clone the hub repo
2. Add the pattern to the appropriate directory
3. Update `registry/patterns.json`
4. Create PR with pattern description

```bash
gh pr create --title "feat: add {pattern-name} {pattern-type}" \
  --body "## New Pattern\n- **Name:** {name}\n- **Type:** {type}\n- **Description:** {description}"
```

## Report

```
Contribute Practice:
  Pattern: {name} ({type})
  Validation: PASSED/FAILED
  Duplicate check: UNIQUE/DUPLICATE
  PR: #{number} — {url}
```
