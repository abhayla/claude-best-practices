# .claude/ — Claude Code Configuration

This directory contains agents, skills, rules, and hooks for Claude Code. Copy it to any project:

```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

## Agents (13)

| Agent | Description |
|-------|-------------|
| `code-reviewer` | Code quality assessment (readability, security, performance) |
| `context-reducer` | Compress context mid-session while preserving critical info |
| `debugger` | Systematic debugging, log analysis, performance optimization |
| `docs-manager` | Keep project documentation accurate and up-to-date |
| `git-manager` | Secure git operations with secret scanning |
| `plan-executor` | Parse and execute multi-step implementation plans |
| `planner-researcher` | Technical research, architecture design, task decomposition |
| `session-summarizer` | Auto-generate session summaries for handoff |
| `tester` | Run tests, analyze coverage, validate builds |
| `test-failure-analyzer` | Diagnose test failures and suggest targeted fixes |
| `fastapi-api-tester` | FastAPI endpoint testing and validation |
| `fastapi-database-admin` | Database tasks — queries, migrations, schema management |
| `android-compose` | Jetpack Compose UI — screens, state, design system |

## Skills (24)

### Universal Skills
| Skill | Usage | Description |
|-------|-------|-------------|
| `/implement` | `/implement <feature>` | Structured feature implementation workflow |
| `/fix-issue` | `/fix-issue #123` | Analyze and fix a GitHub issue |
| `/fix-loop` | `/fix-loop <error>` | Iterative fix cycle until tests pass |
| `/continue` | `/continue` | Resume work from previous session |
| `/auto-verify` | `/auto-verify` | Post-change verification with targeted tests |
| `/status` | `/status` | Quick project health snapshot |
| `/plan-to-issues` | `/plan-to-issues plan.md` | Parse markdown plan into GitHub Issues |
| `/claude-guardian` | `/claude-guardian audit` | Validate CLAUDE.md config files |
| `/test-knowledge` | `/test-knowledge search <query>` | Testing knowledge base |
| `/learn-n-improve` | `/learn-n-improve session` | Session reflection and learning capture |
| `/skill-factory` | `/skill-factory scan` | Detect repeated workflows, create skills |
| `/verify-screenshots` | `/verify-screenshots path/` | Visual content validation |
| `/post-fix-pipeline` | `/post-fix-pipeline` | Post-fix verification and commit |
| `/strategic-architect` | `/strategic-architect diagnose` | Project diagnostics and planning |
| `/ui-ux-pro-max` | `/ui-ux-pro-max` | UI/UX design intelligence (50+ styles) |

### Hub Sync Skills
| Skill | Description |
|-------|-------------|
| `/update-practices` | Pull latest patterns from hub |
| `/contribute-practice` | Submit a pattern to hub |

### FastAPI Skills
| Skill | Description |
|-------|-------------|
| `/fastapi-db-migrate` | Alembic migrations with import location tracking |
| `/fastapi-deploy` | Backend deployment orchestration |
| `/fastapi-run-backend-tests` | pytest with short-name resolution |

### Android Skills
| Skill | Description |
|-------|-------------|
| `/android-adb-test` | E2E testing via ADB |
| `/android-run-tests` | Android test runner with class resolution |
| `/android-run-e2e` | E2E tests by feature group |

### AI Skills
| Skill | Description |
|-------|-------------|
| `/ai-gemini-api` | Gemini API reference and patterns |

## Rules (10)

| Rule | Scope | Description |
|------|-------|-------------|
| `workflow.md` | All files | 7-step development workflow |
| `testing.md` | All files | Testing conventions |
| `fastapi-backend.md` | `backend/**/*.py` | FastAPI patterns and anti-patterns |
| `fastapi-database.md` | `backend/**/models/**` | Database and migration rules |
| `android.md` | `android/**/*.kt` | Android/Kotlin conventions |
| `android-compose-ui.md` | `**/presentation/**/*.kt` | Compose UI patterns |
| `react-nextjs.md` | `src/**/*.tsx` | React + Next.js (placeholder) |
| `firebase-auth.md` | — | Firebase Auth (placeholder) |
| `ai-gemini.md` | — | AI/Gemini (placeholder) |
| `superpowers.md` | — | Advanced patterns (placeholder) |

## Hooks

See `hooks/README.md` for hook examples you can adapt for your project.

## Customization

- **Remove what you don't need:** Delete stack-specific files (e.g., `fastapi-*` if not using FastAPI)
- **Add rules:** Create `.md` files in `rules/` with optional `paths:` frontmatter for scoping
- **Add skills:** Create `skill-name/SKILL.md` in `skills/` with YAML frontmatter
- **Add agents:** Create `.md` files in `agents/` with YAML frontmatter
