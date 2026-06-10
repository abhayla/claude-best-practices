# Claude Best Practices Hub — Dashboard
> Last updated: 2026-06-10 03:58 UTC (auto-generated)

## At a Glance
| Metric | Value |
|--------|-------|
| Total Patterns | 256 |
| Core (universal) | 185 |
| Stack-specific | 71 |
| Agents | 39 |
| Configs | 2 |
| Hooks | 9 |
| Rules | 43 |
| Skills | 163 |

## Pattern Inventory

### Core Patterns

| Name | Type | Version | Source | Dependencies |
|------|------|---------|--------|--------------|
| adr | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| adversarial-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| agent-evaluator | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| agent-orchestration | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| android | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| android-compose-ui | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| anthropic-agent-orchestration-guide | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| anthropic-multi-agent-research-system-skill | skill | 1.0.0 | hub:abhayla/claude-best-practices | anthropic-agent-orchestration-guide |
| anthropic-multi-agent-reviewer-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | anthropic-multi-agent-research-system-skill |
| api-docs-generator | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| architecture-fitness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-format | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| auto-verify | skill | 4.1.0 | hub:abhayla/claude-best-practices | regression-test, tester-agent |
| autonomous-contract | skill | 1.0.0 | project:firekaro-planner | — |
| batch | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| brainstorm | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| branching | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| bug-triage-discipline | rule | 1.0.0 | project:firekaro-planner | — |
| bun-elysia | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| change-risk-scoring | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| changelog-contributing | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ci-cd-setup | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| claude-behavior | rule | 1.3.0 | hub:abhayla/claude-best-practices | — |
| claude-guardian | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| code-quality-gate | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-readability | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| code-review-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| code-review-workflow | skill | 2.0.0 | hub:abhayla/claude-best-practices | code-review-master-agent, review-gate, request-code-review, receive-code-review |
| code-reviewer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| configuration-ssot | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-management | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-reducer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-monitor | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| context-window-statusline-hook | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| continue | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| contribute-practice | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| coverage-analysis | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| create-github-issue | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| dangerous-command-blocker | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| db-migrate | skill | 1.0.0 | hub:abhayla/claude-best-practices | schema-designer |
| db-migrate-verify | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| debugger-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| debugging-loop | skill | 2.0.0 | hub:abhayla/claude-best-practices | debugging-loop-master-agent, systematic-debugging, fix-loop, auto-verify, learn-n-improve |
| debugging-loop-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| decision-authority | rule | 1.0.0 | project:firekaro-planner | — |
| deploy-strategy | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup, k8s-deploy |
| design-principles | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| design-ssot | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| development-loop | skill | 2.0.0 | hub:abhayla/claude-best-practices | development-loop-master-agent, brainstorm, writing-plans, executing-plans, auto-verify, post-fix-pipeline |
| development-loop-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| diataxis-docs | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| doc-staleness | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| doc-structure-enforcer | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| docs-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| documentation-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| documentation-workflow | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| dod-verbs | rule | 1.0.0 | project:firekaro-planner | — |
| e2e-best-practices | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| e2e-conductor-agent | agent | 2.2.0 | hub:abhayla/claude-best-practices | test-scout-agent, visual-inspector-agent, test-healer-agent |
| e2e-persistence-verification | rule | 1.0.0 | project:firekaro-planner | — |
| e2e-pipeline | config | 1.0.0 | hub:abhayla/claude-best-practices | — |
| e2e-readiness-signal | rule | 1.0.0 | project:firekaro-planner | — |
| e2e-test-writing | rule | 1.0.0 | hub:abhayla/claude-best-practices | e2e-best-practices |
| e2e-visual-run | skill | 5.0.0 | hub:abhayla/claude-best-practices | fix-loop, verify-screenshots |
| environment-validation | rule | 1.0.0 | project:firekaro-planner | — |
| error-handling | rule | 1.1.0 | hub:abhayla/claude-best-practices | — |
| escalation-report | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| executing-plans | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| failure-triage-agent | agent | 1.1.0 | hub:abhayla/claude-best-practices | — |
| fastapi-api-tester-agent | agent | 1.2.0 | hub:abhayla/claude-best-practices | — |
| fastapi-backend | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| fastapi-database-admin-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| feature-flag | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| firebase | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| five-advisors | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| fix-github-issue | skill | 3.0.0 | hub:abhayla/claude-best-practices | fix-loop, post-fix-pipeline |
| fix-loop | skill | 1.4.0 | hub:abhayla/claude-best-practices | test-failure-analyzer-agent |
| flutter | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| flutter-dart-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| git-collaboration | rule | 1.0.1 | hub:abhayla/claude-best-practices | — |
| git-manager-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| git-worktrees | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| github-issue-manager-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | create-github-issue |
| grill-me | skill | 1.0.0 | scan:mattpocock/skills | — |
| grill-with-docs | skill | 1.0.0 | upstream:mattpocock/skills@engineering/grill-with-docs | adr |
| handover | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| hono-conventions | rule | 1.0.0 | project:firekaro-planner | — |
| implement | skill | 2.2.0 | hub:abhayla/claude-best-practices | fix-loop, post-fix-pipeline, learn-n-improve |
| improve-codebase-architecture | skill | 1.0.0 | upstream:mattpocock/skills@engineering/improve-codebase-architecture | grill-with-docs, adr |
| independent-test-verification | rule | 1.0.0 | project:firekaro-planner | — |
| integration-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| learn-n-improve | skill | 2.3.0 | hub:abhayla/claude-best-practices | — |
| learning-self-improvement | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| learning-self-improvement-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| learnings-routing | rule | 1.0.0 | project:firekaro-planner | — |
| merge-strategy | skill | 1.0.0 | hub:abhayla/claude-best-practices | branching |
| monorepo | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| orchestrator-responsibility-allowlist | config | 1.0.0 | hub:abhayla/claude-best-practices | — |
| output-plausibility-verification | rule | 1.0.0 | project:firekaro-planner | — |
| parallel-worktree-orchestrator-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-portability | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-self-containment | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| pattern-structure | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| perf-test | skill | 1.2.0 | hub:abhayla/claude-best-practices | web-quality |
| pipeline-fix-pr | skill | 1.0.0 | hub:abhayla/claude-best-practices | serialize-fixes |
| pipeline-orchestrator | skill | 2.0.0 | hub:abhayla/claude-best-practices | project-manager-agent |
| plan-executor-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| plan-to-issues | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| planner-researcher-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| playwright | skill | 1.1.2 | hub:abhayla/claude-best-practices | — |
| post-fix-pipeline | skill | 3.1.0 | hub:abhayla/claude-best-practices | learn-n-improve, auto-verify |
| pr-standards | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| prd-parser | skill | 1.0.0 | hub:abhayla/claude-best-practices | brainstorm |
| prisma-conventions | rule | 1.0.0 | project:firekaro-planner | — |
| project-manager-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | agent-orchestration |
| project-scaffold | skill | 1.0.0 | hub:abhayla/claude-best-practices | ci-cd-setup |
| prompt-auto-enhance | skill | 3.2.0 | hub:abhayla/claude-best-practices | writing-skills, claude-guardian, skill-author |
| prompt-auto-enhance-rule | rule | 3.0.0 | hub:abhayla/claude-best-practices | prompt-auto-enhance |
| prompt-enhance-reminder | hook | 2.0.0 | hub:abhayla/claude-best-practices | — |
| prompt-logger | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| quality-gate-evaluator-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| react-nextjs | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| receive-code-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| regression-test | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| request-code-review | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| research-mode | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| review-gate | skill | 2.0.0 | hub:abhayla/claude-best-practices | code-quality-gate, architecture-fitness, security-audit, adversarial-review, change-risk-scoring, pr-standards |
| rule-curation | rule | 1.0.0 | hub:abhayla/claude-best-practices | pattern-portability, pattern-structure, pattern-self-containment |
| rule-writing-meta | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| save-session | skill | 1.2.0 | hub:abhayla/claude-best-practices | — |
| schema-designer | skill | 1.0.0 | hub:abhayla/claude-best-practices | pg-query, fastapi-db-migrate |
| secret-scanner | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-auditor-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| security-baseline | rule | 1.1.0 | hub:abhayla/claude-best-practices | — |
| semgrep-rules | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| serialize-fixes | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| session-continuity | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| session-continuity-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| session-reminder | hook | 1.0.0 | hub:abhayla/claude-best-practices | — |
| session-summarizer-agent | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-author-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | writing-skills, pattern-structure |
| skill-authoring-master-agent | agent | 1.0.1 | hub:abhayla/claude-best-practices | — |
| skill-authoring-workflow | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| skill-evaluator | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| skill-factory | skill | 3.0.0 | hub:abhayla/claude-best-practices | — |
| skill-master | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| ssot-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | configuration-ssot |
| start-session | skill | 1.1.0 | hub:abhayla/claude-best-practices | save-session |
| status | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| strategic-architect | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| subagent-driven-dev | skill | 1.1.0 | hub:abhayla/claude-best-practices | — |
| supervisor-verification | rule | 1.0.0 | project:firekaro-planner | — |
| supply-chain-audit | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| systematic-debugging | skill | 1.1.0 | hub:abhayla/claude-best-practices | test-knowledge |
| tdd | skill | 1.0.1 | hub:abhayla/claude-best-practices | — |
| tdd-failing-test-generator | skill | 2.0.0 | hub:abhayla/claude-best-practices | tdd, playwright |
| tdd-rule | rule | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-data-management | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-failure-analyzer-agent | agent | 2.3.0 | hub:abhayla/claude-best-practices | — |
| test-healer-agent | agent | 2.3.0 | hub:abhayla/claude-best-practices | fix-loop, test-failure-analyzer-agent |
| test-knowledge | skill | 2.0.0 | hub:abhayla/claude-best-practices | — |
| test-maintenance | skill | 1.0.0 | hub:abhayla/claude-best-practices | — |
| test-pipeline | skill | 3.0.0 | hub:abhayla/claude-best-practices | test-pipeline-agent, fix-loop, auto-verify, post-fix-pipeline |
| test-pipeline-agent | agent | 4.4.0 | hub:abhayla/claude-best-practices | — |
| test-scout-agent | agent | 2.1.0 | hub:abhayla/claude-best-practices | — |
| tester-agent | agent | 3.0.0 | hub:abhayla/claude-best-practices | — |
| testing | rule | 2.2.0 | hub:abhayla/claude-best-practices | — |
| testing-pipeline-master-agent | agent | 3.1.0 | hub:abhayla/claude-best-practices | — |
| to-prd | skill | 1.0.0 | upstream:mattpocock/skills@engineering/to-prd | improve-codebase-architecture, plan-to-issues |
| ui-ux-pro-max | skill | 2.1.0 | hub:abhayla/claude-best-practices | — |
| update-practices | skill | 1.2.1 | hub:abhayla/claude-best-practices | — |
| verify-screenshots | skill | 2.2.0 | hub:abhayla/claude-best-practices | — |
| visual-inspector-agent | agent | 3.0.0 | hub:abhayla/claude-best-practices | verify-screenshots |
| vue | rule | 1.1.0 | hub:abhayla/claude-best-practices | — |
| vue-e2e | rule | 1.0.0 | project:firekaro-planner | — |
| web-research-specialist-agent | agent | 1.0.0 | hub:abhayla/claude-best-practices | — |
| workflow | rule | 2.0.0 | hub:abhayla/claude-best-practices | — |
| workflow-master-template | agent | 2.0.0 | hub:abhayla/claude-best-practices | — |
| writing-plans | skill | 1.3.0 | hub:abhayla/claude-best-practices | — |
| writing-skills | skill | 2.8.0 | hub:abhayla/claude-best-practices | skill-evaluator |
| zoom-out | skill | 1.0.0 | upstream:mattpocock/skills@engineering/zoom-out | — |

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
