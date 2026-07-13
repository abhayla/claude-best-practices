# Getting Started

## Quick Start

### Option A: Copy Everything
```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

### Option B: Smart Provisioning (recommended)
Auto-detects your project's tech stacks and copies only matching patterns:
```bash
PYTHONPATH=. python scripts/recommend.py --local /path/to/your/project --provision
```
See the full walkthrough (including Option C, full synthesis) in the main [README](../README.md#getting-started).

### Advanced / low-level (bootstrap.py — legacy stack-filter installer)
`bootstrap.py` and its remote wrapper `bootstrap.sh` copy patterns for explicitly-named stacks with no auto-detection. `bootstrap.py` prints its own DEPRECATED notice pointing at `recommend.py --provision` / `/synthesize-project` — prefer Option B above unless you need this low-level control (e.g. scripted CI provisioning of a fixed stack list):
```bash
# Local
python scripts/bootstrap.py --stacks ai-gemini,android-compose --target /path/to/project

# Remote
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
| Agents | 29 | Specialized sub-agents for code review, debugging, testing, etc. |
| Skills | 174 | Slash-command workflows like `/implement`, `/fix-loop`, `/status` |
| Rules | 55 | Scoped coding rules that activate based on file paths |
| Hooks | 22 | Example hooks you can adapt (see `hooks/README.md`) |

## Customization

Delete files you don't need. For example, if you're not using FastAPI:
```bash
rm .claude/agents/fastapi-*
rm -r .claude/skills/fastapi-*
rm .claude/rules/fastapi-*
```

### Avoiding bundled-skill collisions

Claude Code ships its own bundled skills. If a hub skill's name or trigger collides with a bundled one, set `disableBundledSkills: true` in your project `.claude/settings.json` (or export `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`) to hide the bundled skills so the hub's adopted skills win.
