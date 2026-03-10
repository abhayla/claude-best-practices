# Claude Best Practices Hub — Dashboard
> Last updated: 2026-03-10 10:23 UTC (auto-generated)

## At a Glance
| Metric | Value |
|--------|-------|
| Total Patterns | 49 |
| Core (universal) | 49 |
| Stack-specific | 0 |
| Agents | 13 |
| Rules | 10 |
| Skills | 26 |

## Pattern Inventory

### Core Patterns

| Name | Type | Version | Source | Dependencies |
|------|------|---------|--------|--------------|
| ai-gemini | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| ai-gemini-api | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-adb-test | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-ui | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-run-e2e | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-run-tests | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| auto-verify | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| claude-guardian | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| code-reviewer | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| context-reducer | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| continue | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| contribute-practice | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| debugger | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| docs-manager | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-api-tester | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-backend | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database-admin | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-db-migrate | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-deploy | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-run-backend-tests | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-auth | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fix-issue | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fix-loop | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| git-manager | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| implement | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| learn-n-improve | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| plan-executor | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| plan-to-issues | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| planner-researcher | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| post-fix-pipeline | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| react-nextjs | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| scan-repo | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| scan-url | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| session-summarizer | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-factory | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| status | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| strategic-architect | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| superpowers | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| test-failure-analyzer | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| test-knowledge | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| tester | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| testing | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| ui-ux-pro-max | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| update-practices | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| verify-screenshots | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| workflow | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |

## Quick Start

Copy the `core/.claude/` directory to your project:
```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

Or use bootstrap for stack-specific filtering:
```bash
python scripts/bootstrap.py --stacks fastapi-python,android-compose --target /path/to/project
```

## How to Use
- **Update local practices:** Run `/update-practices` in any Claude Code session
- **Contribute a pattern:** Run `/contribute-practice .claude/skills/my-skill/`
- **Scan a URL:** `gh workflow run scan-internet.yml -f url="https://..."`
- **Scan a repo:** `gh workflow run scan-projects.yml -f repo="owner/repo"`
