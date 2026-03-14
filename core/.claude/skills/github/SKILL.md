---
name: github
description: >
  Comprehensive GitHub search and discovery skill: search repositories by stars/topic/language/owner,
  search code across GitHub by filename/extension/content, and deep-inspect repos to extract and
  analyze specific files. Fully generic — works for any content type (skills, agents, CLAUDE.md,
  code in any language, configs, patterns). Use when user wants to search or discover anything on GitHub.
triggers:
  - github search
  - github repos
  - search github
  - find repos
  - github discover
  - top repos
  - search code github
  - github inspect
  - github explore
  - find on github
  - github.com
allowed-tools: "Bash Read Write Edit Grep Glob WebFetch WebSearch Agent"
argument-hint: "<action> [options] — e.g., 'search repos for claude skills --stars \">100\"', 'search code \"allowed-tools\" --filename SKILL.md', 'inspect owner/repo --files \"*.md\"'"
version: "1.0.0"
type: workflow
---

# GitHub Search & Discovery Skill

**Request:** $ARGUMENTS

---

Determine which mode to use based on the user's request, then follow that section.

---

## STEP 0: AUTH CHECK

Before any operation, verify GitHub CLI authentication:

```bash
gh auth status
```

If this fails, tell the user to run `gh auth login` first and stop.

---

## MODE 1: SEARCH REPOS

Search GitHub repositories by keywords, stars, topics, language, owner, and more.

### Argument Parsing

Extract from user's natural language or explicit flags:

| Param | Flag | Default | Description |
|-------|------|---------|-------------|
| query | (positional) | *(required)* | Keywords or phrase to search |
| stars | `--stars` | *(none)* | Star filter (e.g., ">50", "100..500") |
| language | `--language` | *(none)* | Programming language filter |
| topic | `--topic` | *(none)* | GitHub topic filter (comma-separated) |
| owner | `--owner` | *(none)* | Filter by owner/org |
| sort | `--sort` | `stars` | Sort by: stars, forks, updated, best-match |
| order | `--order` | `desc` | Sort order: asc, desc |
| limit | `--limit` | `20` | Max results (1-100) |
| created | `--created` | *(none)* | Creation date filter (e.g., ">2024-01-01") |
| updated | `--updated` | *(none)* | Last update filter |
| archived | `--archived` | `false` | Include archived repos |

### Execution

```bash
gh search repos "<query>" \
  --stars "<stars>" \
  --language "<language>" \
  --topic "<topics>" \
  --owner "<owner>" \
  --sort "<sort>" \
  --order "<order>" \
  --limit <limit> \
  --archived=<archived> \
  --json fullName,description,stargazersCount,language,updatedAt,url,forksCount,license \
  --jq '.[] | {fullName, description, stars: .stargazersCount, language, updated: .updatedAt, url, forks: .forksCount, license: .license.key}'
```

Only include flags the user specified — omit unset optional params. Never pass empty values.

### Output Format

```
## GitHub Repo Search: "<query>"
Filters: stars:<stars> | language:<language> | topic:<topic> | sort:<sort>
Results: N found

| # | Repository | ⭐ Stars | Language | Updated | Description |
|---|-----------|---------|----------|---------|-------------|
| 1 | owner/repo | 12.3K | Python | 2026-03-01 | Short description... |
| 2 | ... | ... | ... | ... | ... |

Use `/github inspect <repo>` to explore any repository.
```

### Natural Language Examples

| User Says | Parsed As |
|-----------|-----------|
| "find top python repos for FastAPI testing" | query="FastAPI testing", language=python, sort=stars |
| "search repos about claude code skills with 100+ stars" | query="claude code skills", stars=">100", sort=stars |
| "github repos for rust error handling updated this year" | query="rust error handling", updated=">2025-01-01", sort=stars |
| "find android compose libraries by google" | query="android compose", owner=google, sort=stars |
| "search repos for machine learning in go" | query="machine learning", language=go, sort=stars |
| "find react component libraries with 1000+ stars" | query="react components", language=javascript, stars=">1000" |

---

## MODE 2: SEARCH CODE

Search for specific code, files, or patterns across all GitHub repositories.

### Argument Parsing

Extract from user's natural language or explicit flags:

| Param | Flag | Default | Description |
|-------|------|---------|-------------|
| query | (positional) | *(required)* | Code content to search for |
| filename | `--filename` | *(none)* | Filter by filename (e.g., "SKILL.md", "CLAUDE.md") |
| extension | `--extension` | *(none)* | Filter by file extension (e.g., "py", "rs", "md") |
| language | `--language` | *(none)* | Filter by language (e.g., python, rust, markdown) |
| owner | `--owner` | *(none)* | Filter by owner/org |
| repo | `--repo` | *(none)* | Filter within specific repo(s) |
| path | `--path` | *(none)* | Filter by file path (e.g., ".claude/skills/") |
| size | `--size` | *(none)* | Filter by file size in bytes (e.g., ">1000") |
| limit | `--limit` | `20` | Max results (1-100) |

### Execution

```bash
gh search code "<query>" \
  --filename "<filename>" \
  --extension "<extension>" \
  --language "<language>" \
  --owner "<owner>" \
  --repo "<repo>" \
  --limit <limit> \
  --json path,repository,url,textMatches \
  --jq '.[] | {path, repo: .repository.fullName, url, matches: [.textMatches[].fragment]}'
```

Only include flags the user specified — omit unset optional params. Never pass empty values.

### Output Format

```
## GitHub Code Search: "<query>"
Filters: filename:<filename> | language:<language> | owner:<owner>
Results: N found

| # | Repository | File Path | Match Preview |
|---|-----------|-----------|---------------|
| 1 | owner/repo | .claude/skills/foo/SKILL.md | ...matching text fragment... |
| 2 | owner/repo2 | agents/bar.md | ...matching text fragment... |

Use `/github inspect <repo> --files "<path>"` to read full file contents.
```

### Natural Language Examples

| User Says | Parsed As |
|-----------|-----------|
| "search github for SKILL.md files with allowed-tools" | query="allowed-tools", filename="SKILL.md" |
| "find CLAUDE.md files in popular repos" | query="CLAUDE.md", filename="CLAUDE.md" |
| "search for FastAPI dependency injection patterns in python" | query="Depends FastAPI", language=python |
| "find rust error handling with thiserror crate" | query="thiserror", language=rust, extension=rs |
| "search for android compose navigation code" | query="NavHost composable", language=kotlin |
| "find go interfaces for database drivers" | query="interface Driver", language=go |
| "search for Dockerfile best practices" | query="HEALTHCHECK", filename="Dockerfile" |
| "find terraform modules for AWS Lambda" | query="aws_lambda_function", extension=tf |

### Limitations

If results seem incomplete, inform the user:
- GitHub code search uses a legacy engine via API — results may differ from github.com
- Regex is not supported via the API
- Only indexed files are searchable (very large or binary files are excluded)
- Suggest running with `gh search code "<query>" --web` to open results in browser for full search capabilities

---

## MODE 3: DEEP INSPECT

After finding repositories via Mode 1 or Mode 2, inspect them to extract and analyze specific files.

### Argument Parsing

| Param | Flag | Default | Description |
|-------|------|---------|-------------|
| repo | (positional) | *(required)* | Repository as `owner/repo` or full GitHub URL |
| depth | `--shallow` / `--deep` | targeted | Inspection depth level |
| files | `--files` | *(none)* | Specific files/patterns to fetch (targeted mode) |
| grep | `--grep` | *(none)* | Search pattern for deep mode |
| glob | `--glob` | *(none)* | File glob pattern for deep mode |
| branch | `--branch` | default branch | Branch to inspect |
| output | `--output` | *(none)* | Path to write results as markdown file |

### Input Normalization

Accept various repo formats:
- `owner/repo` → use directly
- `https://github.com/owner/repo` → extract `owner/repo`
- `https://github.com/owner/repo/tree/main/path` → extract repo + path as `--files` hint

### Depth Level: SHALLOW

Fetch repo metadata and README only. Fastest option.

```bash
# Metadata
gh api repos/OWNER/REPO --jq '{
  name: .full_name,
  description: .description,
  stars: .stargazers_count,
  forks: .forks_count,
  language: .language,
  license: .license.key,
  topics: .topics,
  created: .created_at,
  updated: .pushed_at,
  open_issues: .open_issues_count,
  default_branch: .default_branch,
  archived: .archived
}'

# README
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d
```

**Output:**
```
## Repo: owner/repo
⭐ 12.3K | 🍴 450 | Language: Python | License: MIT
Topics: claude-code, skills, ai-agents
Created: 2025-01-15 | Last push: 2026-03-10
Open issues: 23 | Archived: No

### README (truncated to first 100 lines)
[README content]
```

### Depth Level: TARGETED (default)

Fetch specific files by path or pattern. Uses GitHub Contents API — no cloning required.

**Step 1 — List repository tree:**
```bash
gh api repos/OWNER/REPO/git/trees/BRANCH?recursive=1 \
  --jq '.tree[] | select(.type=="blob") | .path'
```

**Step 2 — Match files against user's `--files` patterns:**

Filter the tree listing using the user's patterns. Patterns support:
- Exact paths: `SKILL.md`, `.claude/settings.json`
- Wildcards: `*.md`, `agents/*.md`, `**/*.py`
- Directory prefixes: `.claude/skills/` (matches all files under it)

If no `--files` specified, auto-detect interesting files based on the search context:
- If user searched for skills → look for `**/SKILL.md`
- If user searched for agents → look for `**/agents/*.md`
- If user searched for CLAUDE.md → look for `**/CLAUDE.md`
- If user searched for code patterns → look for files matching the search language/extension
- Otherwise → show the tree listing and ask the user what to inspect

**Step 3 — Fetch matched files:**
```bash
# For each matched file
gh api repos/OWNER/REPO/contents/FILE_PATH?ref=BRANCH --jq '.content' | base64 -d
```

**Rate limit awareness:** If more than 30 files match, warn the user and ask to narrow the pattern. Fetch max 30 files per invocation to avoid hitting API rate limits.

**Output:**
```
## Inspecting: owner/repo (targeted)
Branch: main | Matched files: 5/342 total

### File: .claude/skills/implement/SKILL.md (2.1 KB)
[full file content]

### File: .claude/skills/fix-loop/SKILL.md (1.8 KB)
[full file content]

---
Inspected 5 files from owner/repo.
```

### Depth Level: DEEP

Shallow clone the repo and run local search across all files.

```bash
# Clone with depth 1 (minimal history)
TMPDIR=$(mktemp -d)
gh repo clone OWNER/REPO "$TMPDIR/repo" -- --depth 1 --branch BRANCH 2>/dev/null
```

Then use Glob and Grep tools on `$TMPDIR/repo/` to find files matching `--glob` and `--grep` patterns:

```
# Find files by glob
Glob: pattern="**/*.md" path="$TMPDIR/repo"

# Search content by grep
Grep: pattern="allowed-tools" path="$TMPDIR/repo" glob="*.md"
```

Read matched files with the Read tool, then clean up:
```bash
rm -rf "$TMPDIR"
```

**Output:** Same format as Targeted, but potentially more files since full repo is searchable.

**Size guard:** Before cloning, check repo size:
```bash
gh api repos/OWNER/REPO --jq '.size'
```
If >500000 KB (500 MB), warn the user and ask for confirmation before proceeding.

### Multi-Repo Inspect

When the user wants to inspect multiple repos (e.g., "inspect the top 5 from my last search"):

1. Use the Agent tool to launch parallel subagents — one per repo
2. Each subagent runs the inspect workflow independently
3. Aggregate results into a single comparison report:

```
## Multi-Repo Comparison: "claude code skills"
Inspected 5 repositories

| Repo | Stars | Files Found | Notable Patterns |
|------|-------|-------------|-----------------|
| owner/repo1 | 12.3K | 24 skills | Comprehensive, mode-based |
| owner/repo2 | 3.1K | 8 skills | Focused, minimal |
| ... | ... | ... | ... |

### Detailed Results
[Per-repo output as above]
```

If the user requests >5 repos, confirm before launching parallel inspections.

### Natural Language Examples

| User Says | Parsed As |
|-----------|-----------|
| "inspect anthropics/skills" | repo=anthropics/skills, depth=targeted, auto-detect files |
| "read all SKILL.md files from owner/repo" | repo=owner/repo, depth=targeted, files="\*\*/SKILL.md" |
| "deep inspect this repo for python patterns" | repo=..., depth=deep, glob="\*\*/\*.py" |
| "show me the README of owner/repo" | repo=owner/repo, depth=shallow |
| "inspect the top 3 repos from my last search" | multi-repo, depth=targeted |
| "clone owner/repo and search for error handling" | repo=owner/repo, depth=deep, grep="error handling" |
| "look at the kotlin files in owner/repo" | repo=owner/repo, depth=targeted, files="\*\*/\*.kt" |
| "what's in the .claude directory of owner/repo" | repo=owner/repo, depth=targeted, files=".claude/\*\*" |

### File Export

When `--output <path>` is specified, write the full results as a markdown file:
```bash
Write: file_path="<path>" content="<formatted results>"
```

Report: `Results written to <path>`

---

## CRITICAL RULES

1. **No hardcoded content types** — This skill searches for ANY content on GitHub. Never assume the user is searching for skills, agents, or Claude-specific files. Parse their actual query.
2. **Rate limit awareness** — GitHub API has rate limits (5000 requests/hour authenticated, 60/hour unauthenticated). If `gh api` returns 403/rate-limit errors, report to the user and suggest `gh auth login` or waiting.
3. **Auth check first** — Before any operation, verify `gh auth status`. If unauthenticated, tell the user to run `gh auth login`.
4. **No credential exposure** — Never log or display tokens, API keys, or auth headers.
5. **Respect --limit** — Never fetch more results than requested. Default 20 for search, max 100. Max 30 files for targeted inspect.
6. **Clean up deep clones** — Always remove temp directories after deep inspect completes, even on errors.
7. **Confirm before bulk operations** — If multi-repo inspect would hit >5 repos or deep inspect targets a repo >500 MB, confirm with the user first.
8. **Preserve search context** — When the user says "inspect the top 3" or "look at the first one", reference results from the most recent Mode 1/Mode 2 output in this session.
9. **Omit unused flags** — Only include `gh` CLI flags the user specified. Never pass empty values — this causes search errors.
10. **Suggest next steps** — After Mode 1/2 results, suggest `/github inspect <repo>`. After Mode 3, suggest what the user can do with the extracted content.

---

## QUICK REFERENCE

| User Says | Mode |
|-----------|------|
| "search github repos for..." / "find top repos..." / "github repos about..." | Mode 1: Search Repos |
| "search github code for..." / "find files containing..." / "search for SKILL.md files" | Mode 2: Search Code |
| "inspect owner/repo" / "read files from..." / "clone and search..." / "show me the README" | Mode 3: Deep Inspect |
| "inspect the top N from my search" / "compare these repos" | Mode 3: Multi-Repo Inspect |
