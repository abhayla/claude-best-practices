---
name: ci-cd-setup
description: >
  Set up CI/CD pipelines for GitHub Actions or GitLab CI. Covers workflow syntax,
  pipeline stages, caching, artifacts, secrets, deployment strategies, matrix builds,
  notifications, and optimization. Use when user needs to create, improve, or debug
  CI/CD pipelines.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<platform: github-actions|gitlab-ci> [options: stages, caching, secrets, deploy, matrix, notifications]"
version: "1.0.0"
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

**Request:** $ARGUMENTS

---

## STEP 1: Assess Current State

1. Check for existing CI/CD configuration:
   - `.github/workflows/*.yml` for GitHub Actions
   - `.gitlab-ci.yml` for GitLab CI
2. Identify the project language, framework, and build tool
3. Check for existing `Dockerfile`, `docker-compose.yml`, or deployment configs
4. Review `package.json` scripts, `Makefile`, `pyproject.toml`, or equivalent for build/test commands
5. Check for existing secrets documentation or `.env.example`

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

- ALWAYS set `timeout-minutes` (GitHub) or `timeout` (GitLab) on every job
- ALWAYS use `npm ci` / `pip install --no-deps` / lock-file-based installs in CI
- NEVER echo, print, or log secrets — use environment variables exclusively
- NEVER use `continue-on-error: true` to mask flaky tests — fix the tests
- ALWAYS add failure notifications — silent failures are invisible failures
- ALWAYS use concurrency groups to avoid redundant pipeline runs
- ALWAYS set artifact retention policies to prevent unbounded storage growth
- ALWAYS pin action/image versions to specific tags or SHA hashes, not `latest`
- Prefer OIDC over stored credentials for cloud provider access
- Keep pipeline files DRY — use reusable workflows (GitHub) or includes (GitLab)
