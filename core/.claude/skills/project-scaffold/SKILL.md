---
name: project-scaffold
description: >
  Initialize a fully configured project skeleton with build, lint, test, CI,
  Docker, security baseline, 12-factor compliance, and conventional commits.
  Multi-stack: Python, Node/TypeScript, Android, React/Next.js, Go, Rust.
triggers:
  - scaffold project
  - init project
  - project setup
  - new project
  - bootstrap project
  - project skeleton
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<stack name and project description, or PRD file path>"
version: "1.0.0"
type: workflow
---

# Project Scaffold — Full Project Initialization

Initialize a production-ready project skeleton with build, lint, test, CI, security, and dev environment — all configured and verified.

**Input:** $ARGUMENTS

---

## STEP 1: Determine Stack & Scope

**Read:** `references/determine-stack-scope.md` for detailed step 1: determine stack & scope reference material.

## STEP 2: Generate Project Structure

Create the folder structure following Clean Architecture layer separation:


**Read:** `references/generate-project-structure.md` for detailed step 2: generate project structure reference material.

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname  # Connection string (12-Factor III)

# Server
PORT=8000            # Bind port (12-Factor VII)
HOST=0.0.0.0         # Bind address
LOG_LEVEL=info       # Structured log level (12-Factor XI)
LOG_FORMAT=json      # json | text

# External Services
REDIS_URL=redis://localhost:6379  # Cache/queue backing service (12-Factor IV)

# Security
SECRET_KEY=change-me-in-production  # NEVER commit real secrets
```

---

## STEP 3: Linter & Formatter Configuration

Configure the stack-appropriate linter and formatter:

| Stack | Linter | Formatter | Type Checker |
|-------|--------|-----------|-------------|
| Python | ruff (lint) | ruff (format) | mypy / pyright |
| Node/TS | ESLint 9+ (flat config) or Biome | Prettier or Biome | tsc --noEmit |
| Android | ktlint / detekt | ktlint | Kotlin compiler |
| Go | golangci-lint | gofmt / goimports | go vet |
| Rust | clippy | rustfmt | cargo check |

Include the linter config file with sensible defaults. Enable strict mode where available.

---

## STEP 4: Git Hooks & Conventional Commits


**Read:** `references/git-hooks-conventional-commits.md` for detailed step 4: git hooks & conventional commits reference material.

# .git/hooks/commit-msg or .husky/commit-msg
commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,72}$'
if ! grep -qE "$commit_regex" "$1"; then
  echo "ERROR: Commit message must follow Conventional Commits format."
  echo "  Example: feat(auth): add OAuth2 login flow"
  exit 1
fi
```

### 4.3 Semantic Versioning

For libraries or services with releases, set up version management:

**Node** — Add to `package.json`:
```json
{
  "version": "0.1.0",
  "scripts": {
    "release": "semantic-release"
  }
}
```

**Python** — Add to `pyproject.toml`:
```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
branch = "main"
```

---

## STEP 5: CI Pipeline (GitHub Actions)

**Read:** `references/ci-pipeline-github-actions.md` for detailed step 5: ci pipeline (github actions) reference material.

## STEP 6: Security Baseline

### 6.1 Dependabot Configuration

Generate `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "<stack ecosystem>"  # pip, npm, gomod, cargo, gradle
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
    reviewers:
      - "<team or user>"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 6.2 .gitignore Audit

Verify these secret patterns are in `.gitignore`:
```
# Secrets & credentials
.env
.env.local
.env.*.local
*.pem
*.key
*.p12
credentials.json
service-account*.json
*-secret.yml

# IDE
.idea/
.vscode/settings.json
*.swp

# OS
.DS_Store
Thumbs.db

# Build artifacts
dist/
build/
*.egg-info/
node_modules/
__pycache__/
target/
```

### 6.3 Semgrep Configuration

Generate `.semgrepconfig.yml` or add to CI:
```yaml
rules:
  - p/default
  - p/owasp-top-ten
  - p/secrets
```

### 6.4 Security Gate

The CI pipeline MUST fail if:
- Any dependency has a CRITICAL or HIGH vulnerability
- Semgrep finds any HIGH-confidence finding
- Secrets are detected in committed files

---

## STEP 7: Docker & Dev Environment

### 7.1 Dockerfile (multi-stage)

```dockerfile
# Build stage
FROM <base-image> AS builder
WORKDIR /app
COPY <manifest-files> .
RUN <install-dependencies>
COPY . .
RUN <build-command>

# Production stage
FROM <slim-base-image>
WORKDIR /app
COPY --from=builder /app/<build-output> .
EXPOSE ${PORT:-8000}
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1
CMD ["<start-command>"]
```

### 7.2 Docker Compose

```yaml
services:
  app:
    build: .
    ports:
      - "${PORT:-8000}:${PORT:-8000}"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app  # Dev hot-reload

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME:-app}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASS:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

Adjust services based on the stack's backing services (Redis, MongoDB, etc.).

---

## STEP 8: Health Endpoint

**Read:** `references/health-endpoint.md` for detailed step 8: health endpoint reference material.

## STEP 9: 12-Factor Compliance Check

After generating all files, audit against all 12 factors:

| # | Factor | Check | How |
|---|--------|-------|-----|
| I | Codebase | One repo, many deploys | Verify single git repo with no vendored deps |
| II | Dependencies | Explicitly declared & isolated | Verify manifest file + lockfile exist |
| III | Config | Store in environment | Verify all config reads from env vars, no hardcoded values |
| IV | Backing Services | Treat as attached resources | Verify DB/cache URLs are env vars, not hardcoded hosts |
| V | Build, Release, Run | Strictly separate stages | Verify Dockerfile has separate build and run stages |
| VI | Processes | Stateless & share-nothing | Verify no local file storage for session/state |
| VII | Port Binding | Export services via port | Verify PORT env var used for binding |
| VIII | Concurrency | Scale via process model | Verify no in-process state that prevents horizontal scaling |
| IX | Disposability | Fast startup, graceful shutdown | Verify signal handling (SIGTERM) in entrypoint |
| X | Dev/Prod Parity | Keep gaps small | Verify docker-compose mirrors production topology |
| XI | Logs | Treat as event streams | Verify structured logging to stdout, no file writes |
| XII | Admin Processes | Run as one-off | Verify migrations/seeds run as separate commands, not on startup |

Report any violations and fix them before completing.

---

## STEP 10: License & README

### 10.1 License

Ask the user which license to use. Default to MIT for open source, or add a copyright header for proprietary:

```
Available licenses: MIT, Apache-2.0, GPL-3.0, BSD-3-Clause, proprietary
Which license? [MIT]:
```

### 10.2 README

Generate a minimal README:
```markdown
# <Project Name>

<One-line description from PRD or user input>

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd <project>
cp .env.example .env

# Start dev environment
docker compose up -d

# Run tests
<test command>
```

## Development

- **Lint:** `<lint command>`
- **Test:** `<test command>`
- **Build:** `<build command>`

## Architecture

<Brief description of folder structure and layer responsibilities>
```

---

## STEP 11: Verify & Gate

Run the scaffold gate check using the stack-specific commands:

### Stack-Specific Gate Commands

| Check | Python | Node/React | Android | Go | Rust |
|-------|--------|-----------|---------|-----|------|
| Build | `python -m py_compile src/**/*.py` | `npm run build` | `./gradlew assembleDebug` | `go build ./...` | `cargo build` |
| Lint | `ruff check .` | `npx eslint .` | `./gradlew ktlintCheck` | `golangci-lint run` | `cargo clippy -- -D warnings` |
| Test | `pytest tests/ -x` | `npm test` | `./gradlew testDebugUnitTest` | `go test ./...` | `cargo test` |
| Lockfile | `requirements.txt` or `uv.lock` | `package-lock.json` | `gradle.lockfile` (optional) | `go.sum` | `Cargo.lock` |
| Health | `curl localhost:8000/health` | `curl localhost:3000/api/health` | `adb shell am broadcast` (if applicable) | `curl localhost:8080/health` | `curl localhost:8080/health` |

### Gate Check Script

```bash
# 1. Build succeeds
<build command>

# 2. Linter passes
<lint command>

# 3. Tests pass (smoke test at minimum)
<test command>

# 4. Docker builds (skip for Android)
docker build -t <project>:dev .

# 5. .gitignore covers secrets
grep -q ".env" .gitignore && echo "PASS: .env in .gitignore"

# 6. Lockfile exists
test -f <lockfile> && echo "PASS: Lockfile exists"

# 7. Health endpoint responds (skip for Android if no HTTP server)
docker compose up -d && curl -s http://localhost:${PORT:-8000}/health
```

All 7 checks MUST pass before the scaffold is considered complete.

Report results:
```
Scaffold Gate:
  ✅ Build:     PASS
  ✅ Lint:      PASS
  ✅ Tests:     PASS (1 smoke test)
  ✅ Docker:    PASS
  ✅ Secrets:   PASS (.env in .gitignore)
  ✅ Lockfile:  PASS
  ✅ Health:    PASS (HTTP 200)
  ✅ 12-Factor: 12/12 compliant
```

---

## STEP 12: Suggest Next Steps

After scaffold completion, recommend:

- **`/writing-plans`** — Break the feature into implementation tasks
- **`/ci-cd-setup`** — Extend the CI pipeline with deployment stages
- **`/security-audit`** — Run a deeper security assessment
- **Stage 4 (HTML Prototype)** — Build a clickable demo if UI is involved
- **Stage 5 (Schema Design)** — Design the database schema

---

## MUST DO

- Always confirm the stack before generating files
- Always generate .editorconfig, .gitignore, .env.example, and LICENSE
- Always include a security job in CI (dependency audit + SAST)
- Always run the 12-factor compliance check (Step 9)
- Always verify the scaffold with the gate check (Step 11)
- Always set up commitlint or a commit-msg hook for conventional commits
- Always configure Dependabot for automated dependency updates
- Always include a health endpoint

## MUST NOT DO

- MUST NOT generate files without confirming the stack first
- MUST NOT skip the security baseline — every project gets dependency audit + SAST from day 0
- MUST NOT hardcode configuration values — all config MUST come from environment variables
- MUST NOT create a scaffold without a working smoke test
- MUST NOT commit .env files — only .env.example
- MUST NOT skip the 12-factor audit even for simple projects
- MUST NOT begin implementation during this skill — this skill produces a skeleton, not feature code
