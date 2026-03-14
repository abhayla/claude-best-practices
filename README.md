# Claude Best Practices Hub

A curated collection of battle-tested agents, skills, rules, and hooks for Claude Code.

## Quick Start

```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

That's it. Delete what you don't need (e.g., `rm .claude/agents/fastapi-*` if not using FastAPI).

## What's Inside

| Component | Count | Description |
|-----------|-------|-------------|
| **Agents** | 16 | Sub-agents for code review, debugging, testing, git, planning, docs |
| **Skills** | 76 | Slash-command workflows: `/implement`, `/fix-loop`, `/status`, and more |
| **Rules** | 14 | Scoped coding rules for workflow, testing, FastAPI, Android, etc. |
| **Hooks** | — | Example hooks (auto-format, test verification, workflow logging) |

See [`core/.claude/README.md`](core/.claude/README.md) for the full catalog.

## Alternative: Bootstrap with Stack Filtering

If you only want patterns for specific stacks:

```bash
# Remote bootstrap (one command)
curl -sL https://raw.githubusercontent.com/abhayla/claude-best-practices/main/bootstrap.sh | \
  bash -s -- --stacks fastapi-python,android-compose --target /path/to/project

# Or locally
python scripts/bootstrap.py --stacks fastapi-python --target /path/to/project
```

### Available Stacks

| Stack | Prefix | What it adds |
|-------|--------|-------------|
| `fastapi-python` | `fastapi-*` | API testing agent, DB admin agent, migration/deploy/test skills, backend rules |
| `android-compose` | `android-*` | Compose agent, ADB testing/test runner skills, Android rules |
| `ai-gemini` | `ai-gemini-*` | Gemini API reference skill |
| `firebase-auth` | `firebase-*` | Firebase dev, AI, Data Connect skills |
| `react-nextjs` | `react-*` | React Native dev and E2E skills |

## Repository Structure

```
core/.claude/               # Copy this to your project
  agents/                   # 16 specialized sub-agents
  skills/                   # 76 slash-command workflows
  rules/                    # 14 scoped coding rules
  hooks/                    # Hook examples (README only)
  README.md                 # Self-documenting index
  settings.json             # Minimal defaults
  CLAUDE.md.template        # Template for project CLAUDE.md
  CLAUDE.local.md.template  # Template for local overrides

.claude/                    # Hub-only operational config
  skills/scan-repo/         # Scan downstream repos for patterns
  skills/scan-url/          # Scan internet for patterns
  settings.json             # Hub settings

config/                     # Hub configuration (repos, URLs, settings)
registry/                   # Pattern index (patterns.json)
scripts/                    # Bootstrap, sync, docs generation
docs/                       # Dashboard, getting started, architecture
```

## Skills

| Skill | Description |
|-------|-------------|
| `/implement` | Structured feature implementation (TDD workflow) |
| `/fix-issue` | Analyze and fix GitHub issues |
| `/fix-loop` | Iterative fix cycle until tests pass |
| `/continue` | Resume work from previous session |
| `/status` | Quick project health snapshot |
| `/update-practices` | Pull latest patterns from hub |
| `/contribute-practice` | Submit a pattern to hub |

See [`core/.claude/README.md`](core/.claude/README.md) for all 76 skills.

## Sync Architecture

Projects bootstrapped from the hub can stay updated:

1. Run `/update-practices` — compares local files against hub registry
2. Reviews diffs and applies updates you approve
3. Run `/contribute-practice` — submit local patterns back to the hub

See [docs/SYNC-ARCHITECTURE.md](docs/SYNC-ARCHITECTURE.md) for the full protocol.

## Contributing

Found a pattern that works well? Submit it:

1. Add it to `core/.claude/` (with appropriate prefix for stack-specific patterns)
2. Run `/contribute-practice` or open a PR

## License

MIT
