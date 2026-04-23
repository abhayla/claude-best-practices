# Claude Best Practices Hub — Dashboard
> Last updated: 2026-04-23 16:06 UTC (auto-generated)

## At a Glance
| Metric | Value |
|--------|-------|
| Total Patterns | 237 |
| Core (universal) | 232 |
| Stack-specific | 5 |
| Agents | 39 |
| Configs | 2 |
| Hooks | 8 |
| Rules | 29 |
| Skills | 159 |

## Pattern Inventory

### Core Patterns

| Name | Type | Version | Source | Dependencies |
|------|------|---------|--------|--------------|
| a11y-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | playwright |
| adr | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| adversarial-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| agent-evaluator | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| agent-orchestration | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ai-gemini-api | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-adb-test | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-arch | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-ui | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-gradle | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| android-run-e2e | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| android-run-tests | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| android-test-patterns | skill | 1.0.0 | hub:pipeline-audit | android-run-tests, android-run-e2e |
| anthropic-agent-orchestration-guide | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| anthropic-multi-agent-research-system-skill | skill | 1.0.0 | hub:abhayla/claude-best-practices | anthropic-agent-orchestration-guide |
| anthropic-multi-agent-reviewer-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | anthropic-multi-agent-research-system-skill |
| api-docs-generator | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| apply-selections | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| architecture-fitness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-format | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-verify | skill | 4.1.0 | hub:abhayla/claude-best-practices | regression-test, tester-agent |
| batch | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| brainstorm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| branching | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| bun-elysia | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| bun-elysia-test | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| change-risk-scoring | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| changelog-contributing | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| chaos-resilience | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ci-cd-setup | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| claude-behavior | rule | 1.2.0 | hub:abhayla/claude-best-practices | — |
| claude-guardian | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| code-quality-gate | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-readability | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-review-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-review-workflow | skill | 1.1.0 | hub:abhayla/claude-best-practices | code-review-master-agent, review-gate, request-code-review, receive-code-review |
| code-reviewer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| compose-ui | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| configuration-ssot | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-management | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-reducer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-monitor | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline-hook | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| continue | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| contract-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| contribute-practice | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| coverage-analysis | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| create-github-issue | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| cross-platform-visual | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| d3-viz | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| dangerous-command-blocker | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| dast-scan | skill | 1.0.0 | hub:abhayla/claude-best-practices | security-audit |
| db-migrate | skill | 1.0.0 | hub:abhayla/claude-best-practices | schema-designer |
| db-migrate-verify | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| debugger-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| debugging-loop | skill | 1.1.0 | hub:abhayla/claude-best-practices | debugging-loop-master-agent, systematic-debugging, fix-loop, auto-verify, learn-n-improve |
| debugging-loop-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| deploy-strategy | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup, k8s-deploy |
| design-principles | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| development-loop | skill | 1.1.0 | hub:abhayla/claude-best-practices | development-loop-master-agent, brainstorm, writing-plans, executing-plans, auto-verify, post-fix-pipeline |
| development-loop-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| diataxis-docs | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| disaster-recovery | skill | 1.0.0 | hub:abhayla/claude-best-practices | monitoring-setup, incident-response |
| doc-staleness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| doc-structure-enforcer | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| docker-optimize | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| docs-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| documentation-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| documentation-workflow | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| drizzle-orm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| e2e-best-practices | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| e2e-conductor-agent | agent | 2.1.0 | hub:abhayla/claude-best-practices | test-scout-agent, visual-inspector-agent, test-healer-agent |
| e2e-pipeline | config | 1.0.0 | hub:abhayla/claude-best-practices | — |
| e2e-test-writing | rule | 1.0.0 | hub:abhayla/claude-best-practices | e2e-best-practices |
| e2e-visual-run | skill | 4.0.0 | hub:abhayla/claude-best-practices | fix-loop, verify-screenshots |
| error-handling | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| escalation-report | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| executing-plans | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| expo-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| failure-triage-agent | agent | 1.1.0 | hub:abhayla/claude-best-practices | — |
| fastapi-api-tester-agent | agent | 1.2.0 | hub:abhayla/claude-best-practices | — |
| fastapi-backend | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database-admin-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-db-migrate | skill | 1.1.0 | hub:abhayla/claude-best-practices | db-migrate-verify |
| fastapi-deploy | skill | 1.1.0 | hub:abhayla/claude-best-practices | fastapi-db-migrate, db-migrate-verify |
| fastapi-run-backend-tests | skill | 2.2.0 | hub:abhayla/claude-best-practices | fix-loop |
| feature-flag | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-ai | skill | 1.0.2 | hub:abhayla/claude-best-practices | — |
| firebase-data-connect | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase-dev | skill | 1.0.2 | hub:abhayla/claude-best-practices | — |
| firebase-test | skill | 1.1.1 | hub:abhayla/claude-best-practices | — |
| fix-issue | skill | 2.6.0 | hub:abhayla/claude-best-practices | fix-loop, post-fix-pipeline |
| fix-loop | skill | 1.4.0 | hub:abhayla/claude-best-practices | test-failure-analyzer-agent |
| flutter | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-dart-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-e2e-test | skill | 1.2.1 | hub:abhayla/claude-best-practices | — |
| git-collaboration | rule | 1.0.1 | hub:abhayla/claude-best-practices | — |
| git-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| git-worktrees | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| github | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| github-issue-manager-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | create-github-issue |
| handover | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| hono-backend | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| html-prototype | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| iac-deploy | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| implement | skill | 2.2.0 | hub:abhayla/claude-best-practices | fix-loop, post-fix-pipeline, learn-n-improve |
| incident-response | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| integration-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| jest-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| k8s-deploy | skill | 1.0.2 | hub:abhayla/claude-best-practices | — |
| learn-n-improve | skill | 2.3.0 | hub:abhayla/claude-best-practices | — |
| learning-self-improvement | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| learning-self-improvement-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
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
| orchestrator-responsibility-allowlist | config | 1.0.0 | hub:abhayla/claude-best-practices | — |
| parallel-worktree-orchestrator-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-portability | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-self-containment | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-structure | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| perf-test | skill | 1.2.0 | hub:abhayla/claude-best-practices | web-quality |
| pg-query | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pipeline-fix-pr | skill | 1.0.0 | hub:abhayla/claude-best-practices | serialize-fixes |
| pipeline-orchestrator | skill | 2.0.0 | hub:abhayla/claude-best-practices | project-manager-agent |
| plan-executor-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| plan-to-issues | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| planner-researcher-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| playwright | skill | 1.1.2 | hub:abhayla/claude-best-practices | — |
| pm2-deploy | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| post-fix-pipeline | skill | 3.1.0 | hub:abhayla/claude-best-practices | learn-n-improve, auto-verify |
| pr-standards | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| prd-parser | skill | 1.0.0 | hub:abhayla/claude-best-practices | brainstorm |
| prisma-orm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| project-manager-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | agent-orchestration |
| project-scaffold | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup |
| prompt-auto-enhance | skill | 2.0.0 | hub:abhayla/claude-best-practices | writing-skills, claude-guardian, skill-author |
| prompt-auto-enhance-rule | rule | 2.0.0 | hub:abhayla/claude-best-practices | prompt-auto-enhance |
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
| research-mode | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| review-gate | skill | 2.0.0 | hub:abhayla/claude-best-practices | code-quality-gate, architecture-fitness, security-audit, adversarial-review, change-risk-scoring, pr-standards |
| rule-curation | rule | 1.0.0 | hub:abhayla/claude-best-practices | pattern-portability, pattern-structure, pattern-self-containment |
| rule-writing-meta | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| save-session | skill | 1.2.0 | hub:abhayla/claude-best-practices | — |
| scan-discovery-report | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| scan-repo | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| scan-url | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| schema-designer | skill | 1.0.0 | hub:abhayla/claude-best-practices | pg-query, fastapi-db-migrate |
| secret-scanner | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-auditor-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-baseline | rule | 1.0.1 | hub:abhayla/claude-best-practices | — |
| semgrep-rules | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| serialize-fixes | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| session-continuity | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-continuity-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-reminder | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-summarizer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-author-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | writing-skills, pattern-structure |
| skill-authoring-master-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| skill-authoring-workflow | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| skill-evaluator | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| skill-factory | skill | 3.0.0 | hub:abhayla/claude-best-practices | — |
| skill-master | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| solidity-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ssot-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | configuration-ssot |
| start-session | skill | 1.1.0 | hub:abhayla/claude-best-practices | save-session |
| status | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| strategic-architect | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| subagent-driven-dev | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| supply-chain-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| systematic-debugging | skill | 1.1.0 | hub:abhayla/claude-best-practices | test-knowledge |
| tailwind-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| tdd | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| tdd-failing-test-generator | skill | 2.0.0 | hub:abhayla/claude-best-practices | tdd, playwright |
| tdd-rule | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-data-management | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-failure-analyzer-agent | agent | 2.2.0 | hub:abhayla/claude-best-practices | — |
| test-healer-agent | agent | 2.3.0 | hub:abhayla/claude-best-practices | fix-loop, test-failure-analyzer-agent |
| test-knowledge | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| test-maintenance | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-pipeline | skill | 1.0.0 | hub:abhayla/claude-best-practices | test-pipeline-agent, fix-loop, auto-verify, post-fix-pipeline |
| test-pipeline-agent | agent | 4.3.0 | hub:abhayla/claude-best-practices | — |
| test-scout-agent | agent | 2.1.0 | hub:abhayla/claude-best-practices | — |
| tester-agent | agent | 2.1.0 | hub:abhayla/claude-best-practices | — |
| testing | rule | 2.2.0 | hub:abhayla/claude-best-practices | — |
| testing-pipeline-master-agent | agent | 3.0.0 | hub:abhayla/claude-best-practices | — |
| testing-pipeline-workflow | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| trace-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| twitter-x | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ui-ux-pro-max | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| update-practices | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| verify-screenshots | skill | 2.2.0 | hub:abhayla/claude-best-practices | — |
| visual-inspector-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | verify-screenshots |
| vitest-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue-dev | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| vue-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-quality | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-research-specialist-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| web-scraper | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| websocket-patterns | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| workflow | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| workflow-master-template | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| writing-plans | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| writing-skills | skill | 2.8.0 | hub:abhayla/claude-best-practices | skill-evaluator |
| xml-to-compose | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |

## Research & References

- [QA Agent Ecosystem — GitHub Research](QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md)
- [Claude Code Skills Research — Twitter/X + Reddit Combined Results](SKILL-RESEARCH-by-Twitter-x-and-redit-skills 2026-03-11.md)

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
