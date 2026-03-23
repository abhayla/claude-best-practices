---
name: contribute-practice
description: >
  Push a pattern from your project to the best practices hub by validating
  structure, checking for duplicates, and creating a PR. Use when you have a
  battle-tested pattern worth sharing with other projects.
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

## STEP 4: Sanitize Pattern

Strip project-specific identifiers before submission to make the pattern portable.

1. **Read `synthesis-config.yml`** (if it exists) for the `strip_before_sharing` list. Default categories: `file_paths`, `class_names`, `env_vars`.

2. **Scan and replace** project-specific references:

   | Category | Example before | Example after |
   |----------|---------------|---------------|
   | `file_paths` | `src/core/result.py` | `<module_path>` |
   | `class_names` | `ApiResult` | `<ClassName>` |
   | `env_vars` | `DATABASE_URL` | `$VARIABLE_NAME` |
   | Private pattern refs | `rules/internal-auth-flow.md` | `<private-pattern>` |

3. **Check `private_patterns` list** — if the pattern being contributed is listed in `private_patterns` or has `private: true` in frontmatter, **STOP and warn the user**:
   ```
   WARNING: This pattern is marked private. Remove it from private_patterns
   or set private: false before contributing.
   ```

4. **Show sanitization preview** to the user before proceeding:

   ```
   The following pattern will be submitted to the hub:

     {pattern-path}

     Project-specific details that will be stripped:
     - src/core/result.py → <module_path>
     - ApiResult → <ClassName>
     - DATABASE_URL → $VARIABLE_NAME

     Preview of sanitized pattern:
     [show first 30 lines of sanitized content]

     Continue with submission? [y/n]
   ```

5. Wait for user confirmation. If denied, stop.

## STEP 5: Create PR

1. Fork/clone the hub repo
2. Add the **sanitized** pattern to the appropriate directory
3. Update `registry/patterns.json`
4. Create PR with pattern description

```bash
gh pr create --title "feat: add {pattern-name} {pattern-type}" \
  --body "$(cat <<'EOF'
## New Pattern

- **Name:** {name}
- **Type:** {type}
- **Description:** {description}
- **Source:** Contributed from downstream project via /contribute-practice
- **Sanitized:** Yes — project-specific paths, class names, and env vars replaced with placeholders

## Sanitization Summary

{list of replacements made}

## Review Checklist

- [ ] Pattern is portable (no project-specific references remain)
- [ ] Pattern is not a stub (>30 lines of content)
- [ ] No sensitive information (auth, secrets, billing)
EOF
)"
```

## Report

```
Contribute Practice:
  Pattern: {name} ({type})
  Validation: PASSED/FAILED
  Duplicate check: UNIQUE/DUPLICATE
  Sanitization: {N} replacements made
  PR: #{number} — {url}
```
