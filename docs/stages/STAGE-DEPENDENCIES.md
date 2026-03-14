# Pipeline Stage Dependencies — External Tools & Services

> **Purpose:** Quick reference of external tools, services, and CLIs required by each pipeline stage. Use this to verify a target environment has everything installed before running the pipeline.
> **Last Updated:** 2026-03-14

---

## Per-Stage Dependencies

### Stage 0: Master Orchestrator
| Tool | Purpose |
|------|---------|
| Git | Checkpoints (tags), rollback (revert), state tracking |

### Stage 1: PRD
| Tool | Purpose |
|------|---------|
| `gh` CLI | Fetch GitHub Issue details (when input is an issue URL) |

### Stage 2: Plan
| Tool | Purpose |
|------|---------|
| `gh` CLI | Create epics + task issues via `plan-to-issues` skill |

### Stage 3: Scaffolding
| Tool | Purpose |
|------|---------|
| Docker | Dev environment (`docker-compose.yml`) |
| Package manager (npm/pip/gradle/cargo/go) | Initialize project, install dependencies, generate lockfile |
| commitlint | Enforce conventional commit messages (commit-msg hook) |
| semantic-release | Automated versioning |
| Semgrep | SAST baseline in CI skeleton |
| Dependabot / Renovate | Automated dependency updates config |

### Stage 4: HTML Demo
| Tool | Purpose |
|------|---------|
| Playwright | Screenshot capture for visual verification |
| axe-core (via `@axe-core/playwright`) | Automated WCAG 2.1 AA accessibility audit |
| Lighthouse | Performance budget + accessibility scoring |
| `npx serve` | Local HTTP server for axe-core/Lighthouse audits on `.html` files |

> **Note:** Stage 4 uses vanilla CSS + JS only (no Tailwind, Alpine, or other frameworks). CDN imports are limited to fonts (e.g., Google Fonts). This keeps the prototype dependency-free and portable.

### Stage 5: Schema
| Tool | Purpose |
|------|---------|
| Database engine (PostgreSQL/MySQL/SQLite) | Schema creation, query plan analysis (via Docker or local) |
| ORM migration tool | Migration file generation — one of: Alembic, Prisma, Knex, Django migrations, TypeORM, Drizzle |
| Docker | Run database service for migration testing |

### Stage 6: Pre-Tests (TDD Red Phase)
| Tool | Purpose |
|------|---------|
| Test framework (pytest / Jest / Vitest / JUnit 5) | Unit + API test stubs |
| Playwright | E2E test skeletons (Page Object Model) |
| k6 | Performance test stubs |
| Pact | Consumer-driven contract test setup |
| Hypothesis / fast-check | Property-based test templates |
| mutmut / Stryker | Mutation testing configuration |

### Stage 7: Implementation (TDD Green Phase)
| Tool | Purpose |
|------|---------|
| Linter (ruff / ESLint / Biome / golangci-lint) | Code style enforcement |
| Type checker (mypy / tsc / pyright) | Static type verification |
| jscpd / pylint | Code duplication detection (< 3% threshold) |
| radon / eslint / gocyclo | Cyclomatic complexity measurement (< 10 per function) |
| Git | One commit per task, checkpoint tags |

### Stage 8: Post-Tests (E2E, Perf, Security)
| Tool | Purpose |
|------|---------|
| Playwright | E2E tests (Chromium, Firefox, WebKit) |
| k6 | Load / performance testing against running app |
| OWASP ZAP / Nuclei | DAST — runtime security scanning |
| Semgrep / CodeQL | SAST — static security analysis |
| axe-core | Accessibility E2E testing |
| Docker | Chaos/resilience testing (kill services, simulate failures) |

### Stage 9: Review & Quality Gates
| Tool | Purpose |
|------|---------|
| `gh` CLI | Create PR, create tech debt issues, check CI status, resolve review threads |
| Git | Merge strategy execution (squash / merge / rebase), diff analysis, churn metrics |
| radon / eslint / gocyclo / detekt | Cyclomatic complexity measurement (via `code-quality-gate`) |
| jscpd / pylint | Code duplication detection (via `code-quality-gate`) |
| madge / pydeps / importlab | Circular dependency detection (via `architecture-fitness`) |
| Semgrep / CodeQL | Static security analysis (via `security-audit`) |
| diff-cover | Diff coverage analysis (via `code-quality-gate`) |

### Stage 10: Deployment & Monitoring
| Tool | Purpose |
|------|---------|
| Docker | Build production image |
| Kubernetes (kubectl / helm) | Deploy manifests, probes, HPA, RBAC |
| Terraform / Pulumi | Infrastructure as Code provisioning |
| ArgoCD / Flux | GitOps reconciliation |
| Flagger / Argo Rollouts | Canary / blue-green progressive delivery |
| Prometheus + Grafana | Monitoring dashboards, alerting, SLO tracking |
| GitHub Actions (CI/CD runner) | Pipeline execution |

### Stage 11: Documentation & Handover
| Tool | Purpose |
|------|---------|
| Git | Read conventional commits for CHANGELOG generation |
| spectral | OpenAPI spec linting / validation |
| Redoc / Swagger UI | Human-readable API docs from OpenAPI spec |

---

## Cross-Stage Frequency

Tools needed by 3+ stages, listed by how often they appear:

| Tool | Stages | Count |
|------|--------|-------|
| **Git** | 0, 1, 2, 3, 7, 9, 10, 11 | 8 |
| **Docker** | 3, 5, 8, 10 | 4 |
| **Playwright** | 4, 6, 8 | 3 |
| **`gh` CLI** | 1, 2, 9 | 3 |
| **Semgrep** | 3, 8 | 2 |
| **axe-core** | 4, 8 | 2 |
| **k6** | 6, 8 | 2 |
| **Test runners** (pytest/Jest/Vitest) | 6, 7, 8 | 3 |

---

## Minimum Environment Checklist

For a full pipeline run, ensure these are installed:

```bash
# Core (all stages)
git --version
gh --version
docker --version
docker compose version

# Testing (stages 6-8)
# Python stack:
pytest --version
playwright --version
k6 version

# Security (stages 3, 8)
semgrep --version

# Deployment (stage 10)
kubectl version --client
terraform version   # or: pulumi version
helm version

# Documentation (stage 11)
npx @stoplight/spectral-cli --version  # OpenAPI linting
```

> **Note:** Not all tools are needed for every project. Stage 4 (HTML Demo) is skippable for CLI projects. Stage 10 tools depend on deployment target (K8s vs serverless vs static). ORM migration tools depend on the chosen database stack.
