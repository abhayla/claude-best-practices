# Pipeline Stages, Caching & Artifacts

## Pipeline Stages (Platform-Agnostic Design)

### Standard Stage Order

```
lint → test → build → security-scan → deploy-staging → integration-test → deploy-production
```

| Stage | Purpose | Gate Condition |
|-------|---------|----------------|
| **Lint** | Code style, formatting, static analysis | Must pass before test |
| **Test** | Unit tests, coverage thresholds | Must pass before build |
| **Build** | Compile, bundle, containerize | Must pass before deploy |
| **Security Scan** | SAST, dependency audit, secret scanning | Must pass before deploy |
| **Deploy Staging** | Deploy to staging environment | Automatic on main branch |
| **Integration Test** | E2E tests against staging | Must pass before production |
| **Deploy Production** | Production deployment | Manual approval required |

### Gate Enforcement

- Each stage MUST depend on the previous stage passing
- Security scan failures MUST block deployment
- Production deploys MUST require manual approval
- Integration test failures MUST block production deployment

---

## Caching Strategies

### Cache Key Design

The cache key determines when the cache is invalidated. Use file hashes for dependency caches:

| Language | Cache Path | Key Based On |
|----------|-----------|--------------|
| Node.js | `node_modules/`, `.npm/` | `package-lock.json` |
| Python | `.pip-cache/`, `.venv/` | `requirements.txt`, `pyproject.toml` |
| Java/Kotlin | `~/.gradle/caches/` | `*.gradle*`, `gradle-wrapper.properties` |
| Go | `~/go/pkg/mod/` | `go.sum` |
| Rust | `~/.cargo/`, `target/` | `Cargo.lock` |
| Ruby | `vendor/bundle/` | `Gemfile.lock` |

### Cache Policy Rules

1. **First job in pipeline**: Use `pull-push` policy (populate cache)
2. **Subsequent jobs**: Use `pull` policy (read-only, faster)
3. **Never cache**: Build outputs, test results, secrets, `.env` files
4. **Invalidation**: Tie keys to lock files so cache refreshes on dependency changes

---

## Artifact Management

### What to Artifact

| Artifact Type | Retention | Purpose |
|---------------|-----------|---------|
| Build outputs (`dist/`, `build/`) | 3-7 days | Pass between stages, download |
| Test reports (JUnit XML) | 30 days | Trend analysis, PR annotations |
| Coverage reports (Cobertura) | 30 days | Coverage tracking, PR diffs |
| Docker images | Tagged by version | Deployment |
| Logs on failure | 7 days | Debugging |

### What NOT to Artifact

- `node_modules/` or dependency directories (use cache instead)
- Entire source trees
- Temporary build intermediates
- Secrets or credentials
