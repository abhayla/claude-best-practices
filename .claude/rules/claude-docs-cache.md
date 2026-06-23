# Scope: global

# Claude Docs Local Cache (docs/claude-references/)

version: "1.1.0"

`docs/claude-references/` is a local cache of Claude Code / Anthropic documentation pages
(code.claude.com, and the docs.claude.com / docs.anthropic.com docs family). It exists so the
same page is not re-fetched repeatedly and so there is a stable, citable snapshot to reason from.
Each project keeps its OWN `docs/claude-references/` cache at its repo root.

## Check the cache BEFORE fetching

Before navigating to — or `WebFetch`-ing — any `code.claude.com` (or `docs.claude.com` /
`docs.anthropic.com`) page, FIRST look in `docs/claude-references/` for an already-saved copy and
read that. Only go to the network when the page is **absent**, or when the user explicitly needs the
**latest** and the cached copy's `Fetched:` date looks stale.

## Save EVERY such page you fetch

Whenever you DO fetch one of these pages — yourself, or via a dispatched research agent (read-only
agents have no `Write` tool, so save from the content they return) — write it to
`docs/claude-references/<slug>.md` (create the folder on first use if absent):

- **`<slug>`** = kebab-case of the page (its title, or the URL's last path segment), matching
  existing files — e.g. the "Create plugins" page → `create-plugins.md`.
- **Begin the file with two header lines** so staleness is visible and the source is citable:
  `Source: <full URL>` then `Fetched: <YYYY-MM-DD>`.
- If the slug already exists, **UPDATE** it (refresh content + `Fetched:` date) rather than creating a
  duplicate. **Never clobber hand-authored notes** in an existing file — preserve any unique content.

## CRITICAL RULES

- MUST check `docs/claude-references/` for a saved copy BEFORE fetching a Claude/Anthropic docs page.
- MUST save (or refresh) every such page fetched, with `Source:` + `Fetched:` headers; update, never duplicate.
- MUST NOT overwrite hand-authored content in an existing cache file — preserve unique notes.
- MUST cite the cached file (and its source URL) when using it.
- Applies to this repo AND any project that provisions this rule — each keeps its own
  `docs/claude-references/` cache at its repo root.
