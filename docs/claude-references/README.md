# Claude docs — local cache

Local snapshots of Claude Code / Anthropic documentation pages (code.claude.com,
docs.claude.com, docs.anthropic.com), so they can be referenced without re-fetching
and cited from a stable copy.

**Convention (SSOT):** `.claude/rules/claude-docs-cache.md` — check here *before* fetching a
Claude docs page; save *every* fetched page here as `<slug>.md` with `Source:` + `Fetched:`
header lines (update, don't duplicate; never clobber hand-authored notes).
