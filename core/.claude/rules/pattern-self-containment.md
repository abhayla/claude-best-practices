---
description: Self-containment and completeness standards for patterns. Prevents placeholders, oversized files, and broken dependencies.
globs: [".claude/**/*.md"]
---

# Pattern Self-Containment Standards

## Complete Before Merging

MUST NOT contain placeholder markers (`<!-- TODO: -->`, `<!-- FIXME: -->`, `<!-- PLACEHOLDER -->`). Every pattern distributed via `core/.claude/` must be complete and usable as-is. If content is not ready, do not add the pattern — wait until it has real, battle-tested content.

## Self-Contained Execution

Each skill MUST be executable without reading any other skill's documentation. If a skill delegates to another skill (via `Skill()` calls):
- Include enough context in the delegation step that the workflow is understandable even if the target skill doesn't exist in the user's project
- MUST NOT use phrases like "see the other skill for details" or "refer to X rule for instructions"

## Size Limits

| Lines | Assessment | Action |
|---|---|---|
| < 50 | Suspiciously short | Verify it's not a stub — may belong as a rule instead of a skill |
| 50–500 | Ideal range | No action needed |
| 500–1000 | Warning zone | Consider splitting reference material into `references/` subdirectory |
| > 1000 | Too large | MUST split into smaller skills or extract reference material. Use `skill-name/references/*.md` for supplementary docs |

For skills with extensive reference material, use the directory structure:
```
skill-name/
  SKILL.md           # Core workflow (under 500 lines)
  references/        # Supplementary knowledge (loaded on-demand)
    setup-guide.md
    api-reference.md
  templates/         # Reusable templates
    config.yaml
```

## No Stub Patterns

A pattern with fewer than 30 lines of actual content (excluding frontmatter and headings) is a stub. Stubs MUST NOT be added to `core/.claude/` — they violate the reactive-not-speculative curation policy. Every distributed pattern must contain actionable, tested content.

## Cross-Reference Integrity

If a skill references another skill by name (e.g., "delegate to `/fix-loop`"), the referenced skill MUST exist in the registry. The CI validator checks this — dead references block the PR.
