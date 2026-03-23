---
name: changelog-contributing
description: >
  Generate CHANGELOG.md from conventional commits and create a project-specific
  CONTRIBUTING.md with development setup, commit format, and PR process. Use when
  preparing a release, onboarding contributors, or setting up changelog automation.
triggers:
  - changelog
  - contributing
  - generate changelog
  - generate contributing
  - changelog contributing
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[--changelog-only | --contributing-only] [--since <tag-or-date>] [--unreleased] [--output-dir <path>]"
version: "1.0.0"
type: workflow
---

# Changelog & Contributing Generator

Auto-generate CHANGELOG.md from conventional commits and create CONTRIBUTING.md with project-specific guidelines.

**Arguments:** $ARGUMENTS

---

## STEP 1: Detect Commit Convention and Project Context

Analyze the repository to determine the commit convention in use and gather project metadata.

```bash
# Check recent commits for conventional commit patterns
git log --oneline -50

# Detect package manager and project type
ls package.json pyproject.toml Cargo.toml go.mod build.gradle pom.xml 2>/dev/null

# Check for existing changelog or contributing files
ls CHANGELOG* CONTRIBUTING* changelog* contributing* 2>/dev/null

# Get latest tags for version history
git tag --sort=-v:refname | head -20

# Detect default branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
```

Identify the convention: `type(scope): description`, `type: description`, or freeform. If freeform, best-effort classify commits by keywords (add, fix, remove, update, docs, refactor).

## STEP 2: Parse Git Log

Determine the range of commits to include:

| Scenario | Range |
|----------|-------|
| `--since <tag>` provided | `<tag>..HEAD` |
| `--unreleased` flag | Latest tag to HEAD |
| Tags exist, no flag | Group by tag ranges, most recent first |
| No tags exist | All commits on the default branch |

```bash
# Get commits with hash, subject, and body
git log --pretty=format:"%H|%s|%b" <range>

# Get commit dates for section headers
git log --pretty=format:"%H|%ai|%s" <range>
```

Parse each commit subject against conventional commit pattern:

```
^(?<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(?:\((?<scope>[^)]+)\))?(?<breaking>!)?:\s(?<description>.+)$
```

Map commit types to Keep a Changelog sections:

| Commit Type | Changelog Section |
|-------------|-------------------|
| `feat` | Added |
| `fix` | Fixed |
| `perf` | Changed |
| `refactor` | Changed |
| `docs` | _(skip unless `--include-docs`)_ |
| `style` | _(skip)_ |
| `test` | _(skip)_ |
| `build`, `ci` | _(skip)_ |
| `chore` | _(skip)_ |
| `revert` | Removed |
| `BREAKING CHANGE` or `!` | separate "BREAKING CHANGES" callout at top of version |
| Anything with `deprecate` keyword | Deprecated |
| Anything with `security` keyword | Security |
| Anything with `remove`/`delete` keyword | Removed |

## STEP 3: Group and Deduplicate Entries

1. Group parsed commits by version (tag) or `[Unreleased]`
2. Within each version, group by changelog section (Added, Changed, etc.)
3. Deduplicate entries with identical descriptions
4. Sort sections in Keep a Changelog order: Added, Changed, Deprecated, Removed, Fixed, Security
5. If a commit has a scope, prefix the entry: `**scope:** description`

## STEP 4: Generate CHANGELOG.md

Write the changelog following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- New feature description ([abc1234])
### Fixed
- Bug fix description ([def5678])

## [1.2.0] - 2025-03-01
### Added
- ...

[Unreleased]: https://github.com/owner/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/owner/repo/compare/v1.1.0...v1.2.0
```

- Include comparison links at the bottom if the remote is GitHub/GitLab
- Use short commit hashes (7 chars) as references
- If an existing CHANGELOG.md exists, merge new entries — do not overwrite manually curated content

## STEP 5: Generate CONTRIBUTING.md

Detect project specifics (language, test framework, CI system, linter) and generate a CONTRIBUTING.md tailored to the project.

Template structure:

The CONTRIBUTING.md MUST include these sections, customized with detected project values:

1. **Development Setup** — fork/clone instructions, detected install command (`npm install`, `pip install -r requirements.txt`, etc.), detected test command
2. **Branch Naming** — `{type}/{short-description}` format with types: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`
3. **Commit Message Format** — conventional commits reference with `type(scope): description` pattern, list of valid types, `BREAKING CHANGE` footer usage
4. **Testing Requirements** — new features require tests, bug fixes require regression tests, detected test command to run before PR
5. **Pull Request Process** — branch from `{default branch}`, conventional commits, pass tests and lint, open PR, request review
6. **Code of Conduct** — reference to [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)

Replace all `{placeholders}` with actual detected values. If a value cannot be detected, insert a `TODO:` marker.

## STEP 6: CI Integration (Optional)

If the user requests CI integration, suggest a workflow that auto-updates the changelog on release:

Suggest a GitHub Actions workflow triggered on `release: [published]` that runs changelog generation and commits the updated CHANGELOG.md. Use `actions/checkout@v4` with `fetch-depth: 0` for full history.

Recommended tools by ecosystem:

| Ecosystem | Tool | Notes |
|-----------|------|-------|
| Node.js | `conventional-changelog-cli` | Lightweight, configurable |
| Node.js | `standard-version` | Bumps version + changelog + tag |
| Any | `semantic-release` | Fully automated releases with changelog |
| Any | `git-cliff` | Rust-based, fast, highly configurable |
| Python | `commitizen` | Python-native conventional commits tooling |

## STEP 7: Report

```
Changelog & Contributing: GENERATED
  CHANGELOG.md: {created | updated | skipped}
    Versions documented: N
    Entries added: M
    Breaking changes: B
  CONTRIBUTING.md: {created | updated | skipped}
    Sections: development setup, branch naming, commit format,
              testing requirements, PR process, code of conduct
  CI integration: {added | skipped}
```

---

## MUST DO

- MUST follow [Keep a Changelog](https://keepachangelog.com/) format exactly — sections ordered as Added, Changed, Deprecated, Removed, Fixed, Security
- MUST parse conventional commit types accurately — `feat` maps to Added, `fix` maps to Fixed, not the other way around
- MUST preserve existing manually written changelog entries when updating — merge, do not overwrite
- MUST detect project-specific tooling (test commands, install commands, linter) for CONTRIBUTING.md rather than using generic placeholders
- MUST include comparison links at the bottom of CHANGELOG.md when the remote URL is available
- MUST leave `TODO:` markers in CONTRIBUTING.md for any values that cannot be auto-detected

## MUST NOT DO

- MUST NOT include `docs`, `style`, `test`, `build`, `ci`, or `chore` commits in the changelog by default — these are internal and do not represent notable changes to users
- MUST NOT overwrite an existing CHANGELOG.md without merging — manually curated entries would be lost
- MUST NOT fabricate version numbers — use actual git tags or `[Unreleased]` for untagged commits
- MUST NOT generate a CONTRIBUTING.md that contradicts existing project conventions (check CLAUDE.md, .editorconfig, linter configs)
- MUST NOT hardcode tool-specific commands (e.g., `npm test`) without verifying the project actually uses that tool
- MUST NOT skip the `[Unreleased]` section — commits after the latest tag always go here

## See Also

- `/api-docs-generator` — Generate API reference docs alongside the changelog to give a complete picture of API evolution
- `/diataxis-docs` — Place the generated CHANGELOG.md and CONTRIBUTING.md into the Diataxis docs structure (reference category)
- `/doc-structure-enforcer` — CHANGELOG.md and CONTRIBUTING.md are root docs (allowed at project root, not enforced into `docs/`)
- `/doc-staleness` — Detect when changelog or contributing docs have drifted from actual project conventions
- `/adr` — Major architectural decisions often correspond to changelog entries
- `docs-manager-agent` — Orchestrates project-wide documentation updates, delegates changelog generation to this skill
