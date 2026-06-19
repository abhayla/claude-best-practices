# Getting Started

## Quick Start

### Option A: Copy Everything
```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

### Option B: Bootstrap with Stack Filtering
```bash
python scripts/bootstrap.py --stacks ai-gemini,android-compose --target /path/to/project
```

### Option C: Remote Bootstrap
```bash
curl -sL https://raw.githubusercontent.com/abhayla/claude-best-practices/main/bootstrap.sh | bash -s -- --stacks ai-gemini,android-compose
```

## Available Stacks

| Stack | Description |
|-------|-------------|
| `ai-gemini` | Gemini API integration patterns |
| `android-compose` | Jetpack Compose, Hilt, Room |
| `fastapi-python` | FastAPI, SQLAlchemy, pytest, Alembic |
| `firebase-auth` | Firebase dev, AI, Data Connect |
| `react-nextjs` | React Native dev, E2E testing |

## What's Included

| Component | Count | Description |
|-----------|-------|-------------|
| Agents | 35 | Specialized sub-agents for code review, debugging, testing, etc. |
| Skills | 165 | Slash-command workflows like `/implement`, `/fix-loop`, `/status` |
| Rules | 52 | Scoped coding rules that activate based on file paths |
| Hooks | 13 | Example hooks you can adapt (see `hooks/README.md`) |

## Customization

Delete files you don't need. For example, if you're not using FastAPI:
```bash
rm .claude/agents/fastapi-*
rm -r .claude/skills/fastapi-*
rm .claude/rules/fastapi-*
```

### Avoiding skill collisions with Claude Code's bundled skills

The hub provisions its own skills into `.claude/skills/`. Claude Code also ships **bundled** skills,
workflows, and built-in commands. If a hub skill's name or trigger overlaps a bundled one, you can hide
the bundled set so the hub's version wins, via the `disableBundledSkills` setting (or the
`CLAUDE_CODE_DISABLE_BUNDLED_SKILLS` environment variable) — added in Claude Code v2.1.166–176 (W24, 2026-06).

```jsonc
// .claude/settings.json
{ "disableBundledSkills": true }
```

Verify against the current [settings reference](https://code.claude.com/docs) before relying on it; this
is opt-in — leave it off unless you actually observe a collision.
