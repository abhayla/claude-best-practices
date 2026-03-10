# .claude/ (Hub Operations)

This directory contains skills specific to operating the claude-best-practices hub itself. These are **not** distributed to downstream projects.

## Skills

| Skill | Purpose |
|-------|---------|
| `scan-repo` | Scan registered downstream repos to extract patterns for the hub |
| `scan-url` | Scan internet sources to discover patterns for the hub |

## Distributable Patterns

All distributable patterns (agents, skills, rules, hooks) live in [`core/.claude/`](../core/.claude/). To copy them to a new project:

```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```
