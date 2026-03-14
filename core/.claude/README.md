# .claude/ — Claude Code Configuration

This directory contains agents, skills, rules, and hooks for Claude Code. Copy it to any project:

```bash
cp -r core/.claude/ /path/to/your/project/.claude/
```

## Agents (19)

| Agent | Description |
|-------|-------------|
| `code-reviewer` | Code quality assessment (readability, security, performance) |
| `context-reducer` | Compress context mid-session while preserving critical info |
| `debugger` | Systematic debugging, log analysis, performance optimization |
| `docs-manager` | Keep project documentation accurate and up-to-date |
| `git-manager` | Secure git operations with secret scanning |
| `parallel-worktree-orchestrator` | Coordinate parallel workstreams using git worktrees |
| `plan-executor` | Parse and execute multi-step implementation plans |
| `planner-researcher` | Technical research, architecture design, task decomposition |
| `quality-gate-evaluator` | Evaluate code/content against quality criteria with pass/fail verdicts |
| `security-auditor` | Security review, STRIDE threat modeling, OWASP checks |
| `session-summarizer` | Auto-generate session summaries for handoff |
| `tester` | Run tests, analyze coverage, validate builds |
| `test-failure-analyzer` | Diagnose test failures and suggest targeted fixes |
| `web-research-specialist` | Web research for docs, API references, and technical fact-finding |
| `fastapi-api-tester` | FastAPI endpoint testing and validation |
| `fastapi-database-admin` | Database tasks — queries, migrations, schema management |
| `android-build-fixer` | Android build error diagnosis and fix |
| `android-compose` | Jetpack Compose UI — screens, state, design system |
| `android-kotlin-reviewer` | Kotlin code review with Android best practices |

## Skills (105)

### Pipeline & Orchestration
| Skill | Description |
|-------|-------------|
| `/pipeline-orchestrator` | DAG-based multi-stage PRD-to-Production pipeline coordinator |
| `/brainstorm` | Socratic exploration before planning — produces PRD spec |
| `/prd-parser` | Parse/normalize PRDs from markdown, Notion, Jira, Google Docs (IEEE 830) |
| `/writing-plans` | Generate detailed implementation plans with tasks and verification |
| `/executing-plans` | Execute plans step-by-step with wave-based task dispatch |
| `/subagent-driven-dev` | Orchestrate parallel development across multiple subagents |

### Implementation & Quality
| Skill | Description |
|-------|-------------|
| `/implement` | Structured feature implementation workflow |
| `/tdd` | Strict red-green-refactor TDD cycle |
| `/fix-issue` | Analyze and fix a GitHub issue |
| `/fix-loop` | Iterative fix cycle until tests pass |
| `/code-quality-gate` | Complexity, duplication, SOLID, Clean Architecture, logging checks |
| `/feature-flag` | Feature toggles (LaunchDarkly, Unleash, env-var) with cleanup |
| `/systematic-debugging` | Structured diagnosis: reproduce, isolate, hypothesize, fix |
| `/batch` | Batch operations across multiple files |

### Testing
| Skill | Description |
|-------|-------------|
| `/test-generator` | Auto-generate tests from requirements (BDD, property-based, mutation) |
| `/contract-test` | Consumer-driven contract testing with Pact |
| `/playwright` | Playwright E2E testing with Page Object Model |
| `/perf-test` | k6 + Lighthouse + bundle analysis with baseline comparison |
| `/a11y-audit` | WCAG 2.1 AA accessibility audit (axe-core + Lighthouse) |
| `/auto-verify` | Post-change verification with targeted tests |
| `/verify-screenshots` | Visual regression testing and screenshot validation |
| `/test-knowledge` | Testing knowledge base — patterns, fixtures, platform quirks |

### Security
| Skill | Description |
|-------|-------------|
| `/security-audit` | SAST with CodeQL + Semgrep, SARIF triage, variant analysis |
| `/dast-scan` | DAST with ZAP + Nuclei, header audit, session testing, API fuzzing |
| `/supply-chain-audit` | Dependency vulnerabilities, typosquatting, license compliance |
| `/semgrep-rules` | Create and test custom Semgrep rules |
| `/chaos-resilience` | Chaos engineering — failure injection, graceful degradation, gameday |

### Architecture & Schema
| Skill | Description |
|-------|-------------|
| `/architecture-fitness` | Dependency direction, circular deps, coupling metrics, ADR review |
| `/schema-designer` | ER modeling, normalization, PII, evolution strategy, API alignment |
| `/db-migrate` | Stack-neutral migrations (Prisma, Knex, Django, TypeORM, Drizzle, Alembic) |
| `/project-scaffold` | Full project scaffolding with CI, linting, security baseline, Docker |

### Code Review & PR
| Skill | Description |
|-------|-------------|
| `/adversarial-review` | Multi-persona adversarial code review |
| `/request-code-review` | Create review-optimized pull requests |
| `/receive-code-review` | Triage and act on code review feedback |
| `/pr-standards` | Enforce team standards against PR diffs |
| `/change-risk-scoring` | Quantified risk score for deploy go/no-go decisions |
| `/merge-strategy` | Squash/merge/rebase guidance by branch type |
| `/branching` | Full branch lifecycle — creation through merge and cleanup |
| `/post-fix-pipeline` | Post-fix regression tests, docs update, and commit |

### DevOps & Deployment
| Skill | Description |
|-------|-------------|
| `/ci-cd-setup` | CI/CD pipelines for GitHub Actions or GitLab CI |
| `/docker-optimize` | Dockerfile optimization — multi-stage, caching, security |
| `/k8s-deploy` | Kubernetes manifests, Helm, probes, HPA, RBAC |
| `/iac-deploy` | Infrastructure as Code (Terraform/Pulumi) |
| `/deploy-strategy` | GitOps + progressive delivery + zero-downtime DB migrations |
| `/monitoring-setup` | Prometheus, Grafana, golden signals, SLOs, tracing |
| `/incident-response` | Detection, triage, mitigation, post-mortem, on-call |
| `/disaster-recovery` | DR planning with RTO/RPO, backup, failover, DR drills |

### Documentation
| Skill | Description |
|-------|-------------|
| `/api-docs-generator` | Auto-generate OpenAPI docs from code annotations |
| `/diataxis-docs` | Organize docs into Diátaxis framework (tutorials, how-to, reference, explanation) |
| `/changelog-contributing` | Generate CHANGELOG.md + CONTRIBUTING.md |
| `/handover` | Structured session handover document |
| `/learn-n-improve` | Session reflection and learning capture |
| `/html-prototype` | Single-file HTML prototypes with design tokens and Nielsen's heuristics |

### Session & Project Management
| Skill | Description |
|-------|-------------|
| `/continue` | Resume work from previous session |
| `/status` | Quick project health snapshot |
| `/plan-to-issues` | Parse markdown plan into GitHub Issues |
| `/claude-guardian` | Validate CLAUDE.md config files |
| `/skill-factory` | Detect repeated workflows, create skills |
| `/skill-master` | Route requests to the right skill dynamically |
| `/strategic-architect` | Project diagnostics, bottleneck identification, roadmap |
| `/writing-skills` | Author new Claude Code skills from scratch |
| `/git-worktrees` | Manage git worktrees for isolated parallel development |
| `/scan-discovery-report` | Report generator for scan results |

### Hub Sync
| Skill | Description |
|-------|-------------|
| `/update-practices` | Pull latest patterns from hub |
| `/contribute-practice` | Submit a pattern to hub |

### UI/UX & Visualization
| Skill | Description |
|-------|-------------|
| `/ui-ux-pro-max` | UI/UX design intelligence (50+ styles, palettes, fonts) |
| `/d3-viz` | D3.js data visualization — charts, graphs, maps |
| `/compose-ui` | Jetpack Compose UI patterns, Material3, navigation |
| `/xml-to-compose` | Convert Android XML layouts to Jetpack Compose |

### FastAPI
| Skill | Description |
|-------|-------------|
| `/fastapi-db-migrate` | Alembic migrations with import location tracking |
| `/fastapi-deploy` | Backend deployment orchestration |
| `/fastapi-run-backend-tests` | pytest with short-name resolution |
| `/pg-query` | PostgreSQL read-only queries, EXPLAIN ANALYZE, diagnostics |

### Android
| Skill | Description |
|-------|-------------|
| `/android-arch` | Clean Architecture, Hilt DI, ViewModel, offline-first, coroutines |
| `/android-gradle` | Gradle convention plugins, version catalogs, build optimization |
| `/android-mvi-scaffold` | Scaffold MVI feature modules (Contract, ViewModel, Screen, DI) |
| `/android-adb-test` | E2E testing via ADB (uiautomator, screencap, input) |
| `/android-run-tests` | Android test runner with class name resolution |
| `/android-run-e2e` | E2E tests by feature group with auto-fix |
| `/android-test-patterns` | Test writing: JUnit 5, Compose UI, Espresso, Room, coroutines |

### Mobile (Cross-Platform)
| Skill | Description |
|-------|-------------|
| `/react-native-dev` | React Native — components, navigation, state, performance |
| `/flutter-dev` | Flutter — widgets, Riverpod/BLoC, GoRouter, Material3 |
| `/flutter-e2e-test` | Flutter E2E testing across platforms |
| `/expo-dev` | Expo — Router, EAS Build, push notifications |

### Web Frameworks
| Skill | Description |
|-------|-------------|
| `/nuxt-dev` | Nuxt 4.3+ — server routes, SSR/SSG, NuxtHub, Nuxt UI |
| `/vue-dev` | Vue 3.5+ — Composition API, Reka UI, VueUse, Vitest |
| `/web-quality` | Core Web Vitals, a11y, SEO, performance budgets |
| `/remotion-video` | Programmatic video with React/Remotion |

### Firebase
| Skill | Description |
|-------|-------------|
| `/firebase-dev` | Firebase core — Auth, Firestore, CLI |
| `/firebase-ai` | Firebase AI Logic (Gemini API) integration |
| `/firebase-data-connect` | Firebase Data Connect, Hosting, App Hosting |

### Blockchain
| Skill | Description |
|-------|-------------|
| `/solidity-audit` | Solidity security auditing, Foundry/Hardhat, gas optimization |

### Platform Skills
| Skill | Description |
|-------|-------------|
| `/github` | GitHub search and discovery — repos, code, deep inspect |
| `/twitter-x` | Twitter/X — read, compose, score, search, post, monitor |
| `/reddit` | Reddit — read, compose, analyze, search, post, monitor |
| `/obsidian` | Obsidian vault management — notes, decisions, knowledge |
| `/redis-patterns` | Redis 7+ patterns — caching, vector search, streams |
| `/mcp-server-builder` | Build MCP servers for Claude Code |
| `/ai-gemini-api` | Google Gemini API reference and patterns |

## Rules (14)

### Universal
| Rule | Scope | Description |
|------|-------|-------------|
| `claude-behavior.md` | All files | Task approach, git hygiene, code comments, file structure |
| `context-management.md` | All files | Progressive disclosure, scratchpad, subagent delegation |
| `rule-writing-meta.md` | `.claude/**`, `CLAUDE.md` | RFC 2119, instruction budget, hooks vs rules vs skills |
| `workflow.md` | All files | 7-step development workflow |
| `testing.md` | Test files | Test isolation, AAA, fixtures, flaky test prevention |
| `tdd.md` | Test + source files | Red-green-refactor TDD cycle |

### Quality Standards
| Rule | Scope | Description |
|------|-------|-------------|
| `pattern-portability.md` | `.claude/**/*.md` | No hardcoded paths, least-privilege tools, no project-specific refs |
| `pattern-structure.md` | `.claude/**/*.md` | Frontmatter schema, SemVer, type classification, deprecation |
| `pattern-self-containment.md` | `.claude/**/*.md` | No placeholders, size limits, cross-reference integrity |

### Stack-Specific
| Rule | Scope | Description |
|------|-------|-------------|
| `fastapi-backend.md` | `backend/**/*.py` | FastAPI patterns and anti-patterns |
| `fastapi-database.md` | `backend/**/models/**` | Database and migration rules |
| `android.md` | `android/**/*.kt` | Android/Kotlin conventions |
| `android-compose-ui.md` | `**/presentation/**/*.kt` | Compose UI patterns |
| `android-kotlin.md` | `**/*.kt` | Kotlin language conventions |

## Hooks

See `hooks/README.md` for hook examples you can adapt for your project.

## Customization

- **Remove what you don't need:** Delete stack-specific files (e.g., `fastapi-*` if not using FastAPI)
- **Add rules:** Create `.md` files in `rules/` with optional `paths:` frontmatter for scoping
- **Add skills:** Create `skill-name/SKILL.md` in `skills/` with YAML frontmatter
- **Add agents:** Create `.md` files in `agents/` with YAML frontmatter
