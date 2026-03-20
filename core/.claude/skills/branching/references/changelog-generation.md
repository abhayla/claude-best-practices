# Changelog Generation

Auto-generate a changelog entry from the PR metadata.

## 3.1 Parse PR Information

```bash
# Extract PR metadata
PR_TITLE=$(gh pr view "$PR_NUMBER" --json title --jq '.title')
PR_BODY=$(gh pr view "$PR_NUMBER" --json body --jq '.body')
PR_LABELS=$(gh pr view "$PR_NUMBER" --json labels --jq '[.labels[].name] | join(",")')
PR_URL=$(gh pr view "$PR_NUMBER" --json url --jq '.url')
PR_AUTHOR=$(gh pr view "$PR_NUMBER" --json author --jq '.author.login')
```

## 3.2 Determine Category

```bash
# Determine category from PR title
if echo "$PR_TITLE" | grep -qi '^feat'; then
  CATEGORY="Added"
elif echo "$PR_TITLE" | grep -qi '^fix'; then
  CATEGORY="Fixed"
elif echo "$PR_TITLE" | grep -qi '^refactor\|^perf\|^improve'; then
  CATEGORY="Changed"
elif echo "$PR_TITLE" | grep -qi '^remove\|^breaking\|BREAKING'; then
  CATEGORY="Removed"
elif echo "$PR_TITLE" | grep -qi '^security'; then
  CATEGORY="Security"
else
  CATEGORY="Changed"
fi
```

## 3.3 Generate the Entry

```bash
# Format: - <description> ([#<number>](<url>))
CHANGELOG_ENTRY="- ${PR_TITLE#*: } ([#${PR_NUMBER}](${PR_URL}))"
echo "$CHANGELOG_ENTRY"
```

Example output:

```
- Add user registration with input validation ([#142](https://github.com/org/repo/pull/142))
```

## 3.5 Changelog Entry Examples

```markdown
## [Unreleased]

### Added
- Add user registration with input validation ([#142](https://github.com/org/repo/pull/142))
- Add email verification flow ([#138](https://github.com/org/repo/pull/138))

### Fixed
- Fix crash on login when email is null ([#140](https://github.com/org/repo/pull/140))

### Changed
- Improve database query performance for user lookups ([#139](https://github.com/org/repo/pull/139))
```
