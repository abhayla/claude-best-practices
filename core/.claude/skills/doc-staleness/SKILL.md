---
name: doc-staleness
description: >
  Detect documentation that has drifted from the codebase. Compares docs against
  recent code changes to find stale references, outdated examples, missing modules,
  and broken links. Produces a prioritized staleness report with fix suggestions.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[docs-directory] [--since <commit-or-date>] [--fix]"
version: "1.0.0"
---

# Documentation Staleness Detector

Find documentation that has drifted from the codebase — stale references, outdated
examples, missing modules, and broken internal links.

**Arguments:** $ARGUMENTS

---

## STEP 1: Identify Documentation Files

Scan the project for all documentation files:

```bash
# Find all doc files (exclude vendored/generated dirs)
find . -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) \
  | grep -iv "node_modules\|vendor\|\.git\|dist\|build\|\.next\|__pycache__" | sort
```

Also check for inline doc sources:
- `README.md` at project root and in subdirectories
- `docs/` directory
- `CLAUDE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
- JSDoc/docstring-heavy source files (if `--deep` flag)

Record the file list and line counts before proceeding.

---

## STEP 2: Determine Change Window

Identify which code files changed in the relevant time window:

| Scenario | Range |
|----------|-------|
| `--since <commit>` provided | `<commit>..HEAD` |
| `--since <date>` provided | Commits after that date |
| No flag provided | Last 30 days or last 50 commits (whichever is smaller) |

```bash
# Get changed files in the window
git diff --name-only <range> -- '*.py' '*.ts' '*.js' '*.go' '*.kt' '*.java' '*.rs'

# Get deleted files (may still be referenced in docs)
git diff --name-only --diff-filter=D <range>

# Get renamed files (docs may reference old names)
git diff --name-only --diff-filter=R <range>
```

Build a change manifest: added files, deleted files, renamed files, and significantly modified files (>30% of lines changed).

---

## STEP 3: Extract Documentation References

For each documentation file, extract references to code artifacts:

### 3.1 File Path References

Scan docs for paths that look like source file references:

```
src/services/auth.ts
app/models/user.py
cmd/server/main.go
```

Cross-check each against the current file tree. Flag any that:
- Reference a file that no longer exists
- Reference a file that was renamed (match against rename manifest from Step 2)
- Use an outdated directory structure

### 3.2 Symbol References

Scan docs for function names, class names, and method names:

```bash
# Extract backtick-quoted identifiers from markdown
grep -oP '`[A-Za-z_][A-Za-z0-9_.()]*`' docs/**/*.md | sort -u
```

For each symbol, verify it still exists in the codebase. Flag symbols that:
- No longer exist anywhere in the source
- Were renamed (check git log for the old name)
- Exist but moved to a different file/module

### 3.3 Command References

Scan docs for shell commands and verify they still work:

```bash
# Extract code blocks with bash/shell markers
grep -A5 '```bash\|```shell\|```sh' docs/**/*.md
```

Flag commands that reference:
- Scripts that no longer exist
- CLI flags that were removed
- Package manager commands for uninstalled packages

### 3.4 Internal Links

Check markdown links between documentation files:

```bash
# Extract markdown links
grep -oP '\[.*?\]\((?!http).*?\)' docs/**/*.md
```

Verify each relative link target exists. Flag broken links.

---

## STEP 4: Detect Undocumented Changes

Compare the change manifest (Step 2) against documentation coverage:

### 4.1 New Modules Without Docs

Identify newly added directories or major files that have no corresponding documentation:

| Signal | Staleness type |
|--------|---------------|
| New `src/payments/` directory, no mention in architecture docs | **Undocumented module** |
| New API endpoint added, not in API reference | **Undocumented endpoint** |
| New config option added, not in config reference | **Undocumented config** |
| New environment variable required, not in setup guide | **Undocumented prerequisite** |

### 4.2 Changed Behavior Without Doc Updates

Check if files with significant changes have corresponding doc updates in the same commit range:

```bash
# Files with major changes (>30% delta)
git diff --stat <range> | grep -E '\d+ insertions.*\d+ deletions' | awk '{print $1}'

# Check if any .md files were updated in commits that touched these files
git log --name-only <range> -- <changed-file> | grep '\.md$'
```

If a major source file changed but no documentation was updated in that commit or nearby commits, flag it.

---

## STEP 5: Generate Staleness Report

Produce a prioritized report:

```markdown
## Documentation Staleness Report

**Scan window:** <range>
**Files scanned:** <N> docs, <M> source files changed
**Generated:** <timestamp>

### Critical (Broken References)
| Doc File | Line | Reference | Issue |
|----------|------|-----------|-------|
| `docs/setup.md` | 42 | `src/config/db.ts` | File deleted in abc1234 |
| `README.md` | 15 | `UserService.create()` | Renamed to `UserService.register()` |

### High (Undocumented Changes)
| Changed File | Change Type | Missing From |
|-------------|-------------|--------------|
| `src/payments/` | New module | Architecture docs |
| `POST /webhooks` | New endpoint | API reference |

### Medium (Likely Stale)
| Doc File | Last Modified | Related Code Last Modified | Delta |
|----------|--------------|---------------------------|-------|
| `docs/deploy.md` | 2025-08-01 | 2026-02-15 (6 months newer) | ⚠️ |

### Low (Cosmetic)
| Doc File | Issue |
|----------|-------|
| `docs/api.md` | Uses old package name `@org/legacy` → now `@org/core` |

### Broken Internal Links
| Source | Target | Status |
|--------|--------|--------|
| `docs/setup.md:20` | `docs/advanced-config.md` | ❌ File not found |

### Summary
| Severity | Count |
|----------|-------|
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| Broken links | N |
```

---

## STEP 6: Suggest Fixes

For each critical and high severity issue, provide a concrete fix suggestion:

- **Deleted file reference** → Remove the reference or update to the replacement file
- **Renamed symbol** → Update to the new name (provide the exact replacement)
- **Undocumented module** → Draft a stub section to add to the relevant doc file
- **Broken link** → Provide the corrected link target

If `--fix` flag is set, apply the critical and high fixes automatically using Edit, then re-run the staleness scan to confirm resolution.

---

## MUST DO

- MUST check deleted and renamed files — these are the most common source of doc staleness
- MUST verify internal markdown links resolve to existing files
- MUST compare doc modification dates against related source file dates
- MUST report undocumented new modules, endpoints, and config options
- MUST prioritize findings by severity (broken > undocumented > stale > cosmetic)
- MUST provide concrete fix suggestions, not just "this is stale"

## MUST NOT DO

- MUST NOT modify documentation files unless `--fix` flag is explicitly set
- MUST NOT flag auto-generated docs (OpenAPI specs, typedoc output) — these update via their own pipelines
- MUST NOT treat vendored/third-party docs as project documentation
- MUST NOT report files in `.gitignore`d directories
- MUST NOT flag documentation that intentionally references historical names (e.g., migration guides, changelogs)
- MUST NOT assume every code change requires a doc update — use the severity heuristics to filter noise

## See Also

- `/diataxis-docs` — Restructure docs into the four Diataxis categories after fixing staleness issues
- `/api-docs-generator` — Regenerate API reference docs when stale API documentation is detected
- `/doc-structure-enforcer` — Enforce folder structure rules; run before staleness scan to ensure files are in expected locations
- `/changelog-contributing` — Update CHANGELOG.md when staleness scan reveals undocumented changes
- `/adr` — Architecture Decision Records may reference stale symbols or deleted files
- `docs-manager-agent` — Orchestrates documentation updates, can delegate staleness scanning to this skill
