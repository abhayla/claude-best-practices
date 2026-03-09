# Claude Best Practices Hub

A curated collection of battle-tested patterns, templates, and automation for Claude Code projects. Extracted from real-world production use across multiple tech stacks.

## What This Repo Does

The Hub serves three roles:

| Role | Description |
|------|-------------|
| **Template** | Provides a parameterized `CLAUDE.md` template and stack-specific configurations to bootstrap new projects in minutes. |
| **Knowledge Base** | Collects proven patterns (hooks, skills, agents, rules) organized by tech stack, so you never re-discover the same solution twice. |
| **Auto-Sync** | Keeps downstream projects up-to-date via a sync mechanism that merges hub improvements into your project's `.claude/` directory. |

## Quick Start

### Option 1: Start a New Project from Template

Copy the `CLAUDE.md` template and fill in the `{{VARIABLES}}`:

```bash
cp core/CLAUDE.md.template /path/to/your/project/CLAUDE.md
# Edit the file and replace {{PROJECT_NAME}}, {{PLATFORM}}, etc.
```

### Option 2: Bootstrap an Existing Project

Use the bootstrap script to select stacks and generate a tailored `.claude/` directory:

```bash
./scripts/bootstrap.sh /path/to/your/project --stacks fastapi-python,android-compose
```

### Option 3: Copy Individual Pieces

Browse `stacks/` and copy only the hooks, skills, or rules you need:

```bash
# Example: copy FastAPI testing rules
cp stacks/fastapi-python/rules/testing.md /path/to/project/.claude/rules/
```

## Repository Structure

| Directory | Purpose |
|-----------|---------|
| `core/` | Base `CLAUDE.md` template, shared rules, and universal patterns that apply to all projects. |
| `stacks/` | Stack-specific configurations, rules, hooks, and examples (one subdirectory per stack). |
| `config/` | Sync configuration, stack registry metadata, and version tracking. |
| `registry/` | Machine-readable index of all available patterns, skills, and hooks with tags and descriptions. |
| `scripts/` | Bootstrap, sync, and maintenance scripts. |
| `docs/` | Architecture documentation, contribution guide, and sync protocol specification. |
| `internet-sources/` | Curated external references and scraped best-practice content. |

## Available Stacks

| Stack | Directory | Description |
|-------|-----------|-------------|
| **FastAPI + Python** | `stacks/fastapi-python/` | Async backend patterns: SQLAlchemy, Pydantic, pytest fixtures, Alembic migrations. |
| **Android + Compose** | `stacks/android-compose/` | Jetpack Compose UI, Hilt DI, Room DB, Gradle/KSP build config, E2E testing. |
| **Firebase Auth** | `stacks/firebase-auth/` | Phone OTP auth, debug bypass patterns, token management, multi-environment setup. |
| **AI / Gemini** | `stacks/ai-gemini/` | Gemini structured output, prompt engineering, generation tracking, retry strategies. |
| **React + Next.js** | `stacks/react-nextjs/` | Next.js App Router, server components, Tailwind, Prisma, Playwright testing. |
| **Superpowers** | `stacks/superpowers/` | Advanced Claude Code patterns: workflow hooks, session analysis, automation extraction. |

## Skills

| Skill | Description |
|-------|-------------|
| `/update-practices` | Pull latest patterns from the hub into your project's `.claude/` directory. |
| `/contribute-practice` | Package a local pattern and submit it back to the hub. |
| `/scan-url` | Scrape a URL for Claude Code best practices and add them to the knowledge base. |
| `/scan-repo` | Analyze a repository's `.claude/` setup and extract reusable patterns. |

## Sync Architecture

Projects that bootstrap from the hub can stay up-to-date by running `/update-practices`. The sync mechanism:

1. Compares local `.claude/` files against the hub registry
2. Identifies new or updated patterns relevant to your selected stacks
3. Merges changes with conflict detection (local overrides are preserved)

See [docs/SYNC-ARCHITECTURE.md](docs/SYNC-ARCHITECTURE.md) for the full protocol specification.

## Contributing

Found a pattern that saved you hours? Extracted a hook that catches common mistakes?

1. Add it to the appropriate `stacks/` directory
2. Register it in `registry/`
3. Open a PR

## License

MIT
