---
name: contribute-practice
description: >
  Push a pattern from your project to the best practices hub.
  Validates pattern structure, checks for duplicates, and creates a PR.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<pattern-path>"
type: workflow
version: "2.0.0"
---

# Contribute Practice — Submit Pattern to Hub

Validate a local pattern and submit it to the best practices hub as a PR.

**Pattern path:** $ARGUMENTS

---

## STEP 1: Validate Pattern

Read the pattern file and check:

1. **Structure** — Valid YAML frontmatter (for skills/agents) or valid markdown
2. **Required fields** — name, description, version, type (for skills), model (for agents)
3. **Version field** — Must be valid SemVer format (`"1.0.0"`)
4. **Type field** (skills only) — Must be `workflow` or `reference`
5. **Scope** (rules only) — Must have `globs:` in frontmatter or `# Scope: global` in first 5 lines
6. **No placeholders** — Reject patterns with `<!-- TODO: -->`, `<!-- FIXME: -->`, or body under 30 lines
7. **Size check** — Warn if SKILL.md exceeds 500 lines, reject if over 1000 lines
8. **Least-privilege tools** — Flag if `allowed-tools` includes `Write`/`Edit`/`Bash` but skill body never uses them
9. **No secrets** — Scan for API keys, tokens, credentials, passwords
10. **No project-specific content** — Flag hardcoded absolute paths, project names, specific IPs

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
