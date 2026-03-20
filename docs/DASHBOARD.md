# Claude Best Practices Hub — Dashboard
> Last updated: 2026-03-20 15:37 UTC (auto-generated)

## At a Glance
| Metric | Value |
|--------|-------|
| Total Patterns | 195 |
| Core (universal) | 190 |
| Stack-specific | 5 |
| Agents | 23 |
| Hooks | 8 |
| Rules | 22 |
| Skills | 142 |

## Pattern Inventory

### Core Patterns

| Name | Type | Version | Source | Dependencies |
|------|------|---------|--------|--------------|
| a11y-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | playwright |
| adr | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| adversarial-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| agent-orchestration | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ai-gemini-api | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-adb-test | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-arch | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-ui | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-gradle | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| android-run-e2e | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-run-tests | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-test-patterns | skill | 1.0.0 | hub:pipeline-audit | android-run-tests, android-run-e2e |
| anthropic-agent-orchestration-guide | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| api-docs-generator | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| apply-selections | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| architecture-fitness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-format | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-verify | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| batch | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| brainstorm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| branching | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| bun-elysia | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| bun-elysia-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| change-risk-scoring | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| changelog-contributing | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| chaos-resilience | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ci-cd-setup | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| claude-behavior | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| claude-guardian | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| code-quality-gate | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-reviewer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| compose-ui | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| configuration-ssot | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-management | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-reducer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-monitor | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline-hook | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| continue | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| contract-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| contribute-practice | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| coverage-analysis | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| cross-platform-visual | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| d3-viz | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| dangerous-command-blocker | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| dast-scan | skill | 1.0.0 | hub:abhayla/claude-best-practices | security-audit |
| db-migrate | skill | 1.0.0 | hub:abhayla/claude-best-practices | schema-designer |
| db-migrate-verify | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| debugger-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| deploy-strategy | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup, k8s-deploy |
| diataxis-docs | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| disaster-recovery | skill | 1.0.0 | hub:abhayla/claude-best-practices | monitoring-setup, incident-response |
| doc-staleness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| doc-structure-enforcer | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| docker-optimize | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| docs-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| drizzle-orm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| executing-plans | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| expo-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-api-tester-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-backend | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database-admin-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-db-migrate | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-deploy | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-run-backend-tests | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| feature-flag | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-ai | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-data-connect | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| fix-issue | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fix-loop | skill | 1.2.0 | hub:abhayla/claude-best-practices | — |
| flutter | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-dart-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-e2e-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| git-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| git-worktrees | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| github | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| handover | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| hono-backend | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| html-prototype | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| iac-deploy | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| implement | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| incident-response | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| integration-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| jest-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| k8s-deploy | skill | 1.0.2 | hub:abhayla/claude-best-practices | — |
| learn-n-improve | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| mcp-server-builder | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| merge-strategy | skill | 1.0.0 | hub:abhayla/claude-best-practices | branching |
| middleware-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| mobile-a11y-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| mock-server | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| monitoring-setup | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| monorepo | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| nextjs-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| node-backend-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| nuxt-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| obsidian | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| parallel-worktree-orchestrator-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-portability | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-self-containment | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-structure | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| perf-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | web-quality |
| pg-query | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pipeline-orchestrator | skill | 2.0.0 | hub:abhayla/claude-best-practices | project-manager-agent |
| plan-executor-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| plan-to-issues | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| planner-researcher-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| playwright | skill | 1.1.1 | hub:abhayla/claude-best-practices | — |
| pm2-deploy | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| post-fix-pipeline | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| pr-standards | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| prd-parser | skill | 1.0.0 | hub:abhayla/claude-best-practices | brainstorm |
| prisma-orm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| project-manager-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | agent-orchestration |
| project-scaffold | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup |
| prompt-auto-enhance | skill | 1.0.0 | hub:abhayla/claude-best-practices | writing-skills, claude-guardian, skill-author |
| prompt-auto-enhance-rule | rule | 1.0.0 | hub:abhayla/claude-best-practices | prompt-auto-enhance |
| prompt-enhance-reminder | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pytest-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| quality-gate-evaluator-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| react-native-dev | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| react-nextjs | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| react-test-patterns | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| receive-code-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| reddit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| redis-patterns | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| regression-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| remotion-video | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| request-code-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| review-gate | skill | 2.0.0 | hub:abhayla/claude-best-practices | code-quality-gate, architecture-fitness, security-audit, adversarial-review, change-risk-scoring, pr-standards |
| rule-curation | rule | 1.0.0 | hub:abhayla/claude-best-practices | pattern-portability, pattern-structure, pattern-self-containment |
| rule-writing-meta | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| save-session | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| scan-discovery-report | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| scan-repo | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| scan-url | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| schema-designer | skill | 1.0.0 | hub:abhayla/claude-best-practices | pg-query, fastapi-db-migrate |
| secret-scanner | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-auditor-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| semgrep-rules | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-reminder | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-summarizer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-author-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | writing-skills, pattern-structure |
| skill-factory | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-master | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| solidity-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ssot-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | configuration-ssot |
| start-session | skill | 1.0.0 | hub:abhayla/claude-best-practices | save-session |
| status | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| strategic-architect | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| subagent-driven-dev | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| supply-chain-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| synthesize-project | skill | 3.0.0 | hub:abhayla/claude-best-practices | — |
| systematic-debugging | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| tailwind-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| tdd | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-data-management | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-failure-analyzer-agent | agent | 1.1.1 | hub:abhayla/claude-best-practices | — |
| test-generator | skill | 1.0.0 | hub:abhayla/claude-best-practices | tdd, playwright |
| test-knowledge | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| test-maintenance | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-pipeline | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-pipeline-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| tester-agent | agent | 1.2.0 | hub:abhayla/claude-best-practices | — |
| testing | rule | 2.1.0 | hub:abhayla/claude-best-practices | — |
| trace-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| twitter-x | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ui-ux-pro-max | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| update-practices | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| verify-screenshots | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| vitest-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-quality | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-research-specialist-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-scraper | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| websocket-patterns | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| workflow | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| writing-plans | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| writing-skills | skill | 2.0.1 | hub:abhayla/claude-best-practices | — |
| xml-to-compose | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |

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
