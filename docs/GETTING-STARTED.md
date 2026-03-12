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
| `firebase-auth` | Firebase Authentication |
| `react-nextjs` | React + Next.js patterns |
| `superpowers` | Advanced Claude Code automation |

## What's Included

| Component | Count | Description |
|-----------|-------|-------------|
| Agents | 13 | Specialized sub-agents for code review, debugging, testing, etc. |
| Skills | 26 | Slash-command workflows like `/implement`, `/fix-loop`, `/status` |
| Rules | 10 | Scoped coding rules that activate based on file paths |
| Hooks | — | Example hooks you can adapt (see `hooks/README.md`) |

## Customization

Delete files you don't need. For example, if you're not using FastAPI:
```bash
rm .claude/agents/fastapi-*
rm -r .claude/skills/fastapi-*
rm .claude/rules/fastapi-*
```
