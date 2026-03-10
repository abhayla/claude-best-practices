# Getting Started

## Quick Start

### Option A: GitHub Template
1. Click **"Use this template"** on [abhayla/claude-best-practices](https://github.com/abhayla/claude-best-practices)
2. Clone your new repo
3. Run bootstrap:
```bash
python scripts/bootstrap.py --stacks ai-gemini,android-compose
```

### Option B: Bootstrap Existing Project
```bash
curl -sL https://raw.githubusercontent.com/abhayla/claude-best-practices/main/bootstrap.sh | bash -s -- --stacks ai-gemini,android-compose
```

## Available Stacks

| Stack | Description |
|-------|-------------|
| `ai-gemini` | See stack-config.yml for details |
| `android-compose` | See stack-config.yml for details |
| `fastapi-python` | See stack-config.yml for details |
| `firebase-auth` | See stack-config.yml for details |
| `react-nextjs` | See stack-config.yml for details |
| `superpowers` | See stack-config.yml for details |

## Skills Included

| Skill | Purpose |
|-------|---------|
| `/update-practices` | Pull latest from hub |
| `/contribute-practice` | Push pattern to hub |
| `/scan-url` | Trigger internet scan |
| `/scan-repo` | Trigger project scan |
