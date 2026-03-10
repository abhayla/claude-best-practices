# Claude Best Practices Hub — Dashboard
> Last updated: 2026-03-10 02:09 UTC (auto-generated)

## At a Glance
| Metric | Value |
|--------|-------|
| Total Patterns | 59 |
| Core (universal) | 43 |
| Stack-specific | 16 |
| Agents | 14 |
| Hooks | 10 |
| Rules | 6 |
| Skills | 29 |

## Pattern Inventory

### Core Patterns

| Name | Type | Version | Source | Dependencies |
|------|------|---------|--------|--------------|
| auto-format | hook | 1.0.0 | project:abhayla/KKB | — |
| auto-verify | skill | 1.0.0 | project:abhayla/KKB | — |
| claude-guardian | skill | 1.0.0 | project:abhayla/KKB | — |
| clean-pyc | skill | 1.0.0 | project:abhayla/KKB | — |
| code-reviewer | agent | 1.0.0 | project:abhayla/KKB | — |
| context-reducer | agent | 1.0.0 | project:abhayla/KKB | — |
| continue | skill | 1.0.0 | project:abhayla/KKB | — |
| contribute-practice | skill | 1.0.0 | project:abhayla/KKB | — |
| debugger | agent | 1.0.0 | project:abhayla/KKB | — |
| docs-manager | agent | 1.0.0 | project:abhayla/KKB | — |
| fix-issue | skill | 1.0.0 | project:abhayla/KKB | — |
| fix-loop | skill | 1.0.0 | project:abhayla/KKB | — |
| git-manager | agent | 1.0.0 | project:abhayla/KKB | — |
| hook-utils | hook | 1.0.0 | project:abhayla/KKB | — |
| implement | skill | 1.0.0 | project:abhayla/KKB | — |
| log-workflow | hook | 1.0.0 | project:abhayla/KKB | — |
| plan-executor | agent | 1.0.0 | project:abhayla/KKB | — |
| plan-to-issues | skill | 1.0.0 | project:abhayla/KKB | — |
| planner-researcher | agent | 1.0.0 | project:abhayla/KKB | — |
| post-anr-detection | hook | 1.0.0 | project:abhayla/KKB | — |
| post-fix-pipeline | skill | 1.0.0 | project:abhayla/KKB | — |
| post-screenshot | hook | 1.0.0 | project:abhayla/KKB | — |
| post-test-update | hook | 1.0.0 | project:abhayla/KKB | — |
| pre-skill-fixloop-unblock | hook | 1.0.0 | project:abhayla/KKB | — |
| reflect | skill | 1.0.0 | project:abhayla/KKB | — |
| resize_screenshot | hook | 1.0.0 | project:abhayla/KKB | — |
| scan-repo | skill | 1.0.0 | project:abhayla/KKB | — |
| scan-url | skill | 1.0.0 | project:abhayla/KKB | — |
| session-summarizer | agent | 1.0.0 | project:abhayla/KKB | — |
| skill-factory | skill | 1.0.0 | project:abhayla/KKB | — |
| status | skill | 1.0.0 | project:abhayla/KKB | — |
| strategic-architect | skill | 1.0.0 | project:abhayla/KKB | — |
| sync-check | skill | 1.0.0 | project:abhayla/KKB | — |
| test-failure-analyzer | agent | 1.0.0 | project:abhayla/KKB | — |
| test-knowledge | skill | 1.0.0 | project:abhayla/KKB | — |
| tester | agent | 1.0.0 | project:abhayla/KKB | — |
| testing | rule | 1.0.0 | project:abhayla/KKB | — |
| ui-ux-pro-max | skill | 1.0.0 | project:abhayla/KKB | — |
| update-practices | skill | 1.0.0 | project:abhayla/KKB | — |
| validate-workflow-step | hook | 1.0.0 | project:abhayla/KKB | — |
| verify-evidence-artifacts | hook | 1.0.0 | project:abhayla/KKB | — |
| verify-screenshots | skill | 1.0.0 | project:abhayla/KKB | — |
| workflow | rule | 1.0.0 | project:abhayla/KKB | — |

## How to Use
- **Bootstrap new project:** `python scripts/bootstrap.py --stacks android-compose,fastapi-python`
- **Update local practices:** Run `/update-practices` in any Claude Code session
- **Contribute a pattern:** Run `/contribute-practice .claude/skills/my-skill/`
- **Scan a URL:** `gh workflow run scan-internet.yml -f url="https://..."`
- **Scan a repo:** `gh workflow run scan-projects.yml -f repo="owner/repo"`
