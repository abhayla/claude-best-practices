# App Development Lifecycle — Coverage Map

> What this repo provides at each phase, and what's missing.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APP DEVELOPMENT LIFECYCLE                            │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐    ┌────────────────┐  │
│  │  1. IDEATE   │───▶│  2. PLAN    │───▶│ 3. DESIGN│───▶│ 4. IMPLEMENT   │  │
│  │  & SCOPE     │    │             │    │          │    │                │  │
│  └─────────────┘    └─────────────┘    └──────────┘    └───────┬────────┘  │
│        ⚠️                ✅                ✅                    ✅          │
│                                                                 │          │
│                                                                 ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐    ┌────────────────┐  │
│  │ 8. MONITOR  │◀───│ 7. DEPLOY   │◀───│ 6. REVIEW│◀───│  5. TEST       │  │
│  │ & MAINTAIN  │    │             │    │          │    │  & DEBUG       │  │
│  └─────────────┘    └─────────────┘    └──────────┘    └────────────────┘  │
│        ❌                ⚠️                ✅                   ✅          │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────┐    │
│  │ 9. LEARN    │    │10. SESSION  │    │ 11. HUB SYNC (meta)         │    │
│  │ & IMPROVE   │    │ MANAGEMENT  │    │                              │    │
│  └─────────────┘    └─────────────┘    └──────────────────────────────┘    │
│        ✅                ✅                          ✅                     │
└─────────────────────────────────────────────────────────────────────────────┘

  ✅ = Well covered    ⚠️ = Partially covered    ❌ = Gap
```

---

## Phase-by-Phase Breakdown

### 1. IDEATE & SCOPE ⚠️

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/strategic-architect` | Skill | Project diagnostics, bottleneck identification, roadmap |
| `planner-researcher` | Agent | Technical research, architecture design |

**What's missing:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| Requirements gathering | No skill to capture/structure requirements from user input | `/gather-requirements` skill — interactive Q&A to produce structured requirements doc |
| User story generation | No way to break down ideas into user stories | `/user-stories` skill — generate user stories with acceptance criteria from requirements |
| Feasibility analysis | No technical feasibility or effort estimation | `/estimate` skill — rough effort estimation based on codebase complexity |

---

### 2. PLAN ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/strategic-architect` | Skill | Strategic diagnostics and roadmap creation |
| `/plan-to-issues` | Skill | Parse markdown plan into GitHub Issues |
| `/implement` | Skill | Structured implementation workflow (requirements → tests → code) |
| `planner-researcher` | Agent | Architecture design, task decomposition |
| `plan-executor` | Agent | Parse plans into tracked steps with dependencies |
| `workflow.md` | Rule | 7-step development workflow |

**Minor gaps:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| ADR (Architecture Decision Records) | No structured way to capture architecture decisions | `/adr` skill — create/manage Architecture Decision Records |

---

### 3. DESIGN ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/ui-ux-pro-max` | Skill | 50+ styles, 97 palettes, 57 font pairings, 9 framework stacks |
| `android-compose-ui.md` | Rule | Compose UI structure, ViewModel patterns, design system |
| `android-compose` | Agent | Jetpack Compose screens, state, design system |
| `react-nextjs.md` | Rule | ⚠️ Placeholder — no actual content |

**Minor gaps:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| API design | No OpenAPI/schema-first API design tooling | `/design-api` skill — generate OpenAPI spec from requirements |
| Database schema design | No ER diagram or schema design from requirements | `/design-schema` skill — generate SQL/ORM models from requirements |

---

### 4. IMPLEMENT ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/implement` | Skill | Full TDD workflow: requirements → tests → code → verify |
| `/fix-issue` | Skill | Analyze and fix GitHub Issues end-to-end |
| `/fix-loop` | Skill | Iterative fix cycle until tests pass |
| `/fastapi-db-migrate` | Skill | Alembic migration generation |
| `/ai-gemini-api` | Skill | Gemini API integration reference |
| `fastapi-database-admin` | Agent | DB queries, migrations, schema management |
| `fastapi-backend.md` | Rule | SQLAlchemy patterns, services architecture |
| `fastapi-database.md` | Rule | PostgreSQL config, Alembic workflows |
| `android.md` | Rule | Gradle, architecture, coroutines, testing |
| `android-compose-ui.md` | Rule | Compose patterns and anti-patterns |

**Minor gaps:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| Scaffolding / boilerplate | No code generation for common patterns (CRUD, endpoints, models) | `/scaffold` skill — generate boilerplate for endpoint/model/screen |
| Dependency management | No help adding/updating packages safely | `/add-dependency` skill — add package with compatibility check |

---

### 5. TEST & DEBUG ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/auto-verify` | Skill | Post-change verification with smart test mapping |
| `/fastapi-run-backend-tests` | Skill | pytest with short-name resolution |
| `/android-run-tests` | Skill | Android tests with class name resolution |
| `/android-run-e2e` | Skill | Android E2E by feature group |
| `/android-adb-test` | Skill | Manual ADB-based E2E testing |
| `/verify-screenshots` | Skill | Visual content validation |
| `/test-knowledge` | Skill | Self-improving testing knowledge base |
| `/fix-loop` | Skill | Iterative debug cycle |
| `/post-fix-pipeline` | Skill | Regression tests + full suite + commit |
| `tester` | Agent | Test execution, coverage analysis, build validation |
| `test-failure-analyzer` | Agent | Diagnose failures, classify root causes |
| `debugger` | Agent | Log analysis, performance investigation |
| `testing.md` | Rule | Testing principles, fixtures, failure handling |

**Minor gaps:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| Test generation | No skill to auto-generate test cases from code | `/generate-tests` skill — analyze function/endpoint and generate test cases |
| Coverage reporting | No coverage threshold enforcement | `/coverage` skill — run coverage, flag regressions, suggest missing tests |
| Load/performance testing | No performance test tooling | `/perf-test` skill — basic load testing for API endpoints |
| Frontend testing | No React/Vue/web test runner skills | `/run-frontend-tests` skill — Jest/Vitest/Playwright runner |

---

### 6. REVIEW ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `code-reviewer` | Agent | Code quality, type safety, security, performance review |
| `/claude-guardian` | Skill | Validate CLAUDE.md config files |
| `git-manager` | Agent | Secret scanning during git operations |

**Minor gaps:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| PR review workflow | No skill to review a PR holistically (all commits, tests, docs) | `/review-pr` skill — fetch PR, review all changes, post summary |
| Security audit | No dedicated security scanning beyond secret detection | `/security-scan` skill — OWASP checks, dependency vulnerabilities |

---

### 7. DEPLOY ⚠️

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/fastapi-deploy` | Skill | FastAPI deployment: migrations, seeds, restart, health check |
| `git-manager` | Agent | Secure git push with secret scanning |

**What's missing:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| Frontend deployment | No deployment for React/Next.js/web apps | `/deploy-frontend` skill — build, deploy to Vercel/Netlify/S3 |
| Android deployment | No APK/AAB build and Play Store upload | `/android-deploy` skill — build, sign, upload to Play Console |
| Docker/container | No container build/push workflow | `/docker-deploy` skill — build image, push to registry, deploy |
| CI/CD pipeline setup | No skill to generate/update CI configs | `/setup-ci` skill — generate GitHub Actions workflow for project |
| Environment management | No env variable or secret management | `/manage-env` skill — validate .env files, sync with CI secrets |
| Release management | No versioning, changelog, or release creation | `/release` skill — bump version, generate changelog, create GitHub release |

---

### 8. MONITOR & MAINTAIN ❌

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/status` | Skill | Git status, test status, open work (local only) |

**What's missing:**
| Gap | Description | Suggested Addition |
|-----|-------------|-------------------|
| Error tracking | No integration with Sentry/Crashlytics/error services | `/check-errors` skill — fetch recent errors from monitoring service |
| Uptime/health monitoring | No production health checking | `/health-check` skill — hit health endpoints, report status |
| Dependency updates | No automated dependency freshness checking | `/update-deps` skill — check outdated packages, create update PR |
| Log analysis | No production log analysis | `/analyze-logs` skill — fetch and analyze recent production logs |
| Performance monitoring | No APM integration | `/check-perf` skill — fetch response time metrics, flag regressions |
| Database maintenance | No production DB health checks | `/db-health` skill — check slow queries, index usage, table sizes |

---

### 9. LEARN & IMPROVE ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/learn-n-improve` | Skill | Session analysis, memory updates, pattern detection |
| `/test-knowledge` | Skill | Self-improving testing knowledge base |
| `/skill-factory` | Skill | Detect repeated workflows, create new skills |
| `session-summarizer` | Agent | Auto-generate session summaries for handoff |
| `context-reducer` | Agent | Compress context mid-session |

---

### 10. SESSION MANAGEMENT ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/continue` | Skill | Resume from previous session with full context |
| `/status` | Skill | Quick project health snapshot |
| `session-summarizer` | Agent | Session summaries for handoff |
| `context-reducer` | Agent | Context compression |
| `docs-manager` | Agent | Keep docs accurate |

---

### 11. HUB SYNC (Meta) ✅

**What exists:**
| Resource | Type | What it does |
|----------|------|-------------|
| `/update-practices` | Skill | Pull latest patterns from hub |
| `/contribute-practice` | Skill | Submit patterns to hub |
| `/scan-repo` | Skill (hub-only) | Scan repos for patterns |
| `/scan-url` | Skill (hub-only) | Scan internet for patterns |

---

## Coverage Summary

```
Phase               Coverage    Agents  Skills  Rules
─────────────────────────────────────────────────────
1. Ideate & Scope     ⚠️          1       1       0
2. Plan               ✅          2       3       1
3. Design             ✅          1       1       2*
4. Implement          ✅          2       5       4
5. Test & Debug       ✅          3       9       1
6. Review             ✅          2       1       0
7. Deploy             ⚠️          1       1       0
8. Monitor & Maintain ❌          0       1       0
9. Learn & Improve    ✅          2       3       0
10. Session Mgmt      ✅          2       2       0
11. Hub Sync          ✅          0       4       0
─────────────────────────────────────────────────────
TOTAL                           13+3*   26+2*   6+4*

* includes placeholders     + hub-only variants
```

## Priority Gaps (Recommended Additions)

### High Priority
| # | Skill | Phase | Why |
|---|-------|-------|-----|
| 1 | `/review-pr` | Review | Every team needs PR review — most frequent workflow |
| 2 | `/generate-tests` | Testing | Auto-generating tests massively accelerates TDD |
| 3 | `/release` | Deploy | Version bumping + changelog is universal need |
| 4 | `/setup-ci` | Deploy | CI/CD config is needed by every project |
| 5 | `/gather-requirements` | Ideate | Structured intake prevents wasted implementation time |

### Medium Priority
| # | Skill | Phase | Why |
|---|-------|-------|-----|
| 6 | `/security-scan` | Review | Security is critical but often skipped |
| 7 | `/coverage` | Testing | Coverage regressions silently degrade quality |
| 8 | `/update-deps` | Maintain | Outdated deps are a security and maintenance risk |
| 9 | `/scaffold` | Implement | Boilerplate generation saves significant time |
| 10 | `/design-api` | Design | API-first design prevents integration issues |

### Low Priority (nice-to-have)
| # | Skill | Phase | Why |
|---|-------|-------|-----|
| 11 | `/docker-deploy` | Deploy | Only needed for containerized projects |
| 12 | `/check-errors` | Monitor | Requires external service integration |
| 13 | `/perf-test` | Testing | Specialized — not every project needs it |
| 14 | `/adr` | Plan | Useful for larger teams/projects |
| 15 | `/run-frontend-tests` | Testing | Stack-specific (React/Vue projects) |

### Rules to Fill In
| Rule | Status | Priority |
|------|--------|----------|
| `react-nextjs.md` | Placeholder | High — React/Next.js is widely used |
| `firebase-auth.md` | Placeholder | Medium — needed for Firebase projects |
| `ai-gemini.md` | Placeholder | Medium — needed for AI-powered apps |
| `superpowers.md` | Placeholder | Low — advanced/meta patterns |
