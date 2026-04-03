---
name: ci-cd-setup
description: >
  Set up CI/CD pipelines for GitHub Actions or GitLab CI. Covers workflow syntax,
  pipeline stages, caching, artifacts, secrets, deployment stages, matrix builds,
  notifications, and optimization. Use when creating, improving, or debugging CI/CD
  pipelines. NOT for full project scaffolding (use /project-scaffold) or deployment
  strategy design (use /deploy-strategy).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<platform: github-actions|gitlab-ci> [options: stages, caching, secrets, deploy, matrix, notifications]"
version: "1.1.0"
type: workflow
triggers:
  - ci cd setup
  - github actions
  - gitlab ci
  - pipeline setup
  - ci pipeline
---

# CI/CD Pipeline Setup

Set up or improve CI/CD pipelines for the project.
**Scope:** GitHub Actions and GitLab CI only. For other CI platforms (CircleCI,
Azure Pipelines, Bitbucket Pipelines), adapt patterns manually.
ALWAYS set timeouts on every job. NEVER log secrets. ALWAYS pin action versions.

If `$ARGUMENTS` is empty, ask the user which platform (GitHub Actions or GitLab CI) and whether they need a new pipeline, optimization of an existing one, or debugging a broken one. Do not proceed without at least a platform.

**Request:** $ARGUMENTS

---

## STEP 1: Assess Current State

1. Check for existing CI/CD configuration:
   - `.github/workflows/*.yml` for GitHub Actions
   - `.gitlab-ci.yml` for GitLab CI
2. Identify the project language, framework, and build tool
3. Check for existing `Dockerfile`, `docker-compose.yml`, or deployment configs
4. Review build tool configs for build/test commands: `package.json`, `pyproject.toml`, `Makefile`, `Cargo.toml`, `build.gradle(.kts)`, `pom.xml`, `go.mod`. If no build tool is detected, ask the user for build/test commands before proceeding
5. Check for existing secrets documentation or `.env.example`
6. If existing CI config is found: check for syntax errors. Offer to **fix** the existing config or **replace** it — ask user preference

## STEP 2: Choose Platform and Structure

Select the CI/CD platform based on the user's request or repository host. If unspecified, default to GitHub Actions for GitHub repos and GitLab CI for GitLab repos.


### Platform References

- **GitHub Actions:** `references/github-actions-reference.md` — workflow structure, triggers, jobs, matrix builds, reusable workflows, caching, secrets/OIDC, notifications, status badges
- **GitLab CI:** `references/gitlab-ci-reference.md` — file structure, jobs, rules/conditional execution, caching, includes for splitting large pipelines

### Design References

- **Pipeline stages & caching:** `references/pipeline-stages-and-caching.md` — standard stage order, gate enforcement, cache key design by language, cache policy rules, artifact management
- **Secrets & deployment:** `references/secrets-and-deployment.md` — secret management principles, environment-specific secrets, secret scanning, environment progression, rollback, blue-green/canary
- **Optimization & anti-patterns:** `references/optimization-and-anti-patterns.md` — conditional execution, concurrency control, skip patterns, parallel test splitting, common anti-patterns table

---
## STEP 3: Create Pipeline Configuration

Based on the assessment from Step 1 and the platform chosen in Step 2:

1. Create the workflow file(s) using the patterns above
2. Configure stages in the correct order with gates between them
3. Add caching for all dependency types detected in the project
4. Set timeouts on every job
5. Add failure notifications
6. **Monorepo projects:** Use path-filtered triggers (`paths`/`paths-ignore`) to run only affected package pipelines. For Turborepo/Nx, use `--filter=...[HEAD^]` for affected-only builds. See `/monorepo` for workspace-specific patterns.

## STEP 4: Configure Secrets

1. List all secrets the pipeline needs (API keys, deploy tokens, registry credentials)
2. Document which secrets to add in the CI/CD settings
3. Prefer OIDC for cloud provider authentication
4. Add secret scanning to the pipeline

## STEP 5: Test the Pipeline

1. Create a test branch and push to trigger the pipeline
2. Verify each stage runs correctly
3. Verify caching works (second run should be faster)
4. Verify failure notifications trigger on intentional failure
5. Verify deployment gates require approval

## STEP 6: Verification

Confirm the following checklist:

| Check | Status |
|-------|--------|
| All stages have timeouts | |
| Dependencies are cached | |
| Secrets are not logged | |
| Failure notifications configured | |
| Concurrency control enabled | |
| Path filters avoid unnecessary runs | |
| Artifacts have retention policies | |
| Deploy requires manual approval for production | |
| Status badge added to README | |
| Secret scanning enabled | |

---

## CRITICAL RULES

### MUST DO
- MUST set `timeout-minutes` (GitHub) or `timeout` (GitLab) on every job — Why: runaway jobs consume CI minutes and block queues
- MUST use lock-file-based installs (`npm ci`, `pip install --no-deps`, `poetry install --no-root`) — Why: non-lockfile installs produce non-reproducible builds
- MUST add failure notifications to every pipeline — Why: silent failures are invisible; teams miss broken builds for days
- MUST use concurrency groups to cancel redundant pipeline runs — Why: queued runs waste CI minutes and delay feedback
- MUST set artifact retention policies — Why: unbounded storage grows indefinitely and hits provider quotas
- MUST pin action/image versions to specific tags or SHA hashes — Why: unpinned versions break builds without code changes (supply chain risk)
- MUST use OIDC over stored credentials for cloud provider access when available — Why: stored credentials can be exfiltrated; OIDC tokens are short-lived and scoped
- MUST keep pipeline files DRY via reusable workflows (GitHub) or includes (GitLab) — Why: duplicated config drifts across repos

### MUST NOT DO
- MUST NOT echo, print, or log secrets — use environment variables exclusively — Why: logged secrets persist in CI logs accessible to anyone with repo access
- MUST NOT use `continue-on-error: true` to mask flaky tests — fix the tests instead — Why: masked failures hide real regressions
- MUST NOT use `latest` tag for actions or Docker images — pin to SHA or version tag — Why: mutable tags are a supply-chain attack vector
- MUST NOT skip CI gates with `[skip ci]` or `--no-verify` to work around failures — Why: bypassed gates mask broken code that reaches production
