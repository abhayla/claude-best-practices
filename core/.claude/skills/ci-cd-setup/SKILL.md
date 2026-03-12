---
name: ci-cd-setup
description: >
  Set up CI/CD pipelines for GitHub Actions or GitLab CI. Covers workflow syntax,
  pipeline stages, caching, artifacts, secrets, deployment strategies, matrix builds,
  notifications, and optimization. Use when user needs to create, improve, or debug
  CI/CD pipelines.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<platform: github-actions|gitlab-ci> [options: stages, caching, secrets, deploy, matrix, notifications]"
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

---

## GitHub Actions

### Workflow File Structure

GitHub Actions workflows live in `.github/workflows/`. Each file defines an independent workflow.

```yaml
# .github/workflows/ci.yml
name: CI

# --- TRIGGERS ---
on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
  schedule:
    # Run nightly at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

# --- PERMISSIONS ---
permissions:
  contents: read
  pull-requests: write
  id-token: write  # Required for OIDC

# --- CONCURRENCY ---
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# --- ENVIRONMENT VARIABLES ---
env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

### Triggers Reference

| Trigger | Use Case | Notes |
|---------|----------|-------|
| `push` | Run on commits to specific branches | Use `paths` / `paths-ignore` to filter |
| `pull_request` | Run on PR events | `types` controls which PR actions trigger |
| `schedule` | Cron-based runs | Use for nightly builds, dependency checks |
| `workflow_dispatch` | Manual trigger with inputs | Good for deploys, one-off tasks |
| `workflow_call` | Reusable workflow (called by others) | Define `inputs` and `secrets` |
| `release` | Run on release creation | Use for publish/deploy workflows |
| `repository_dispatch` | External event trigger | Triggered via API, enables cross-repo flows |

### Job Structure

```yaml
jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

      - name: Check formatting
        run: npm run format:check

  test:
    name: Test
    needs: lint  # Gate: lint must pass first
    runs-on: ubuntu-latest
    timeout-minutes: 20
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb

      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/
          retention-days: 7

  build:
    name: Build
    needs: test
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 5
```

### Matrix Builds

Run tests across multiple versions, operating systems, or configurations simultaneously:

```yaml
  test-matrix:
    name: Test (${{ matrix.os }}, Node ${{ matrix.node-version }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    strategy:
      fail-fast: false  # Don't cancel other matrix jobs on failure
      max-parallel: 4
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        exclude:
          # Skip Node 18 on macOS (not needed)
          - os: macos-latest
            node-version: 18
        include:
          # Add an experimental build
          - os: ubuntu-latest
            node-version: 23
            experimental: true

    continue-on-error: ${{ matrix.experimental || false }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci
      - run: npm test
```

### Reusable Workflows

Define a workflow that other workflows can call:

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image-tag:
        required: true
        type: string
    secrets:
      DEPLOY_TOKEN:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy to ${{ inputs.environment }}
        run: |
          echo "Deploying ${{ inputs.image-tag }} to ${{ inputs.environment }}"
          # deployment commands here
        env:
          TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

Call the reusable workflow:

```yaml
# .github/workflows/cd.yml
jobs:
  deploy-staging:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      image-tag: ${{ github.sha }}
    secrets:
      DEPLOY_TOKEN: ${{ secrets.STAGING_DEPLOY_TOKEN }}
```

### GitHub Actions Caching

```yaml
      # Node.js — built-in cache via setup-node
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      # Python — built-in cache via setup-python
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      # Generic cache action (Gradle example)
      - name: Cache Gradle packages
        uses: actions/cache@v4
        with:
          path: |
            ~/.gradle/caches
            ~/.gradle/wrapper
          key: gradle-${{ runner.os }}-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
          restore-keys: |
            gradle-${{ runner.os }}-

      # Docker layer caching
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build with cache
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Secrets and OIDC

```yaml
      # Using repository secrets
      - name: Deploy
        run: ./deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}
          # NEVER echo or log secrets
          # NEVER use secrets in if: conditions (they appear in logs)

      # OIDC for AWS (no long-lived credentials)
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: us-east-1

      # OIDC for GCP
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/github/providers/my-repo'
          service_account: 'deploy@my-project.iam.gserviceaccount.com'

      # OIDC for Azure
      - name: Azure Login
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Notifications

```yaml
  notify:
    name: Notify
    needs: [lint, test, build, deploy]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Slack notification on failure
        if: contains(needs.*.result, 'failure')
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "Pipeline FAILED for ${{ github.repository }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Pipeline Failed* :red_circle:\n*Repo:* ${{ github.repository }}\n*Branch:* ${{ github.ref_name }}\n*Commit:* ${{ github.sha }}\n*Author:* ${{ github.actor }}\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Run>"
                  }
                }
              ]
            }

      - name: Deployment success notification
        if: needs.deploy.result == 'success'
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "Deployed ${{ github.repository }} to production :rocket:"
            }
```

### Status Badges

Add to your `README.md`:

```markdown
![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)
![Deploy](https://github.com/OWNER/REPO/actions/workflows/cd.yml/badge.svg?branch=main)
```

---

## GitLab CI

### File Structure

GitLab CI uses a single `.gitlab-ci.yml` at the repo root. For large pipelines, split into includes.

```yaml
# .gitlab-ci.yml

# --- GLOBAL DEFAULTS ---
default:
  image: node:20-alpine
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure
  timeout: 15 minutes
  interruptible: true

# --- VARIABLES ---
variables:
  NPM_CONFIG_CACHE: '$CI_PROJECT_DIR/.npm'
  PIP_CACHE_DIR: '$CI_PROJECT_DIR/.pip-cache'
  FF_USE_FASTZIP: 'true'

# --- STAGES (execution order) ---
stages:
  - lint
  - test
  - build
  - security
  - deploy

# --- GLOBAL CACHE ---
cache:
  key:
    files:
      - package-lock.json
  paths:
    - .npm/
    - node_modules/
  policy: pull
```

### Jobs

```yaml
# --- LINT STAGE ---
eslint:
  stage: lint
  script:
    - npm ci --prefer-offline
    - npm run lint
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - .npm/
      - node_modules/
    policy: pull-push  # First job populates cache

format-check:
  stage: lint
  script:
    - npm ci --prefer-offline
    - npm run format:check

# --- TEST STAGE ---
unit-tests:
  stage: test
  services:
    - name: postgres:16
      alias: db
      variables:
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
        POSTGRES_DB: testdb
  variables:
    DATABASE_URL: 'postgres://test:test@db:5432/testdb'
  script:
    - npm ci --prefer-offline
    - npm test -- --coverage
  coverage: '/All files.*\|.*\s+([\d.]+)%/'
  artifacts:
    when: always
    reports:
      junit: junit-report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    paths:
      - coverage/
    expire_in: 7 days

# --- BUILD STAGE ---
build:
  stage: build
  script:
    - npm ci --prefer-offline
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 3 days

docker-build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: '/certs'
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build --cache-from $CI_REGISTRY_IMAGE:latest -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Rules and Conditional Execution

```yaml
# Run only on merge requests
merge-request-only:
  stage: test
  script: echo "MR pipeline"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# Run only on main branch, skip drafts
production-deploy:
  stage: deploy
  script: ./deploy.sh production
  rules:
    - if: $CI_COMMIT_BRANCH == "main" && $CI_MERGE_REQUEST_TITLE !~ /^Draft:/
      when: manual
      allow_failure: false

# Path-based triggers
frontend-tests:
  stage: test
  script: npm run test:frontend
  rules:
    - changes:
        - 'src/frontend/**/*'
        - 'package.json'

# Scheduled pipelines
dependency-audit:
  stage: security
  script: npm audit
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### GitLab CI Caching

```yaml
# Per-branch cache with fallback
cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - node_modules/
    - .npm/
  fallback_keys:
    - $CI_DEFAULT_BRANCH
    - default

# Multiple caches
test-with-caches:
  stage: test
  cache:
    - key:
        files:
          - package-lock.json
      paths:
        - node_modules/
      policy: pull
    - key:
        files:
          - requirements.txt
      paths:
        - .pip-cache/
      policy: pull
```

### GitLab Includes (Splitting Large Pipelines)

```yaml
# .gitlab-ci.yml
include:
  # Local files
  - local: '.gitlab/ci/lint.yml'
  - local: '.gitlab/ci/test.yml'
  - local: '.gitlab/ci/deploy.yml'

  # Remote templates
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

  # From another project
  - project: 'devops/ci-templates'
    ref: main
    file: '/templates/docker-build.yml'
```

---

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

---

## Secrets Management

### Principles

1. **NEVER** hardcode secrets in pipeline files
2. **NEVER** echo or print secrets in logs
3. **NEVER** use secrets in `if:` conditions (GitHub Actions logs condition values)
4. **NEVER** pass secrets as command-line arguments (visible in process listings)
5. Use environment variables to pass secrets to processes
6. Rotate secrets regularly; use short-lived credentials where possible
7. Prefer OIDC over stored credentials for cloud providers

### Environment-Specific Secrets

```yaml
# GitHub Actions — use environments
jobs:
  deploy:
    environment: production  # Requires approval, has its own secrets
    steps:
      - run: ./deploy.sh
        env:
          DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}

# GitLab CI — use protected variables + environments
deploy-production:
  stage: deploy
  environment:
    name: production
    url: https://app.example.com
  variables:
    DB_PASSWORD: $PROD_DB_PASSWORD  # Set in GitLab CI/CD settings, protected
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

### Secret Scanning

Add secret scanning to your pipeline to catch accidental commits:

```yaml
# GitHub Actions
secret-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    - uses: trufflesecurity/trufflehog@main
      with:
        extra_args: --only-verified

# GitLab CI — built-in template
include:
  - template: Security/Secret-Detection.gitlab-ci.yml
```

---

## Deployment Strategies

### Environment Progression

```
feature branch → dev (auto) → staging (auto on main) → production (manual approval)
```

### Rollback Triggers

Build automated rollback into your deploy step:

```yaml
deploy-production:
  steps:
    - name: Deploy
      id: deploy
      run: |
        ./deploy.sh ${{ github.sha }}
        echo "previous_version=$(cat .deployed-version)" >> $GITHUB_OUTPUT

    - name: Smoke test
      id: smoke
      run: |
        curl --fail --retry 3 --retry-delay 5 https://app.example.com/health

    - name: Rollback on failure
      if: failure() && steps.deploy.outcome == 'success'
      run: |
        echo "Smoke test failed, rolling back..."
        ./deploy.sh ${{ steps.deploy.outputs.previous_version }}
```

### Blue-Green / Canary (Conceptual)

```yaml
# Canary deploy pattern
deploy-canary:
  steps:
    - name: Deploy canary (10% traffic)
      run: ./deploy.sh --canary --weight 10

    - name: Monitor error rate (5 minutes)
      run: |
        sleep 300
        ERROR_RATE=$(curl -s https://monitoring.example.com/api/error-rate)
        if (( $(echo "$ERROR_RATE > 1.0" | bc -l) )); then
          echo "Error rate too high: $ERROR_RATE%"
          exit 1
        fi

    - name: Promote to full deployment
      run: ./deploy.sh --promote

    - name: Rollback canary on failure
      if: failure()
      run: ./deploy.sh --rollback-canary
```

---

## Pipeline Optimization

### Conditional Execution

Only run jobs when relevant files change:

```yaml
# GitHub Actions — path filters
on:
  push:
    paths:
      - 'src/**'
      - 'tests/**'
      - 'package.json'
    paths-ignore:
      - '**.md'
      - '.github/ISSUE_TEMPLATE/**'

# GitLab CI — changes keyword
frontend-tests:
  rules:
    - changes:
        - 'src/frontend/**'
        - 'package.json'
```

### Concurrency Control

Prevent redundant pipeline runs:

```yaml
# GitHub Actions
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# GitLab CI
workflow:
  auto_cancel:
    on_new_commit: interruptible
```

### Skip Patterns

```yaml
# GitHub Actions — skip via commit message
jobs:
  build:
    if: |
      !contains(github.event.head_commit.message, '[skip ci]') &&
      !contains(github.event.head_commit.message, '[ci skip]')

# GitLab CI — built-in support for [skip ci] in commit messages
```

### Parallel Test Splitting

```yaml
# Split tests across parallel runners
test:
  strategy:
    matrix:
      shard: [1, 2, 3, 4]
  steps:
    - run: |
        npx jest --shard=${{ matrix.shard }}/4
```

---

## Common Anti-Patterns

### What to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No `timeout-minutes` | Stuck jobs run indefinitely, burn minutes | Set timeout on every job |
| No caching | Every run installs from scratch (slow, flaky) | Cache dependencies by lock file hash |
| Secrets in logs | `echo $SECRET` or `--password=$SECRET` | Use env vars, mask in settings |
| No failure notifications | Team unaware of broken builds for hours | Add Slack/email on failure |
| `npm install` instead of `npm ci` | Non-deterministic installs, ignores lock file | Always use `ci` / `--frozen-lockfile` |
| No concurrency limits | 10 pushes = 10 redundant pipeline runs | Use concurrency groups, cancel in-progress |
| Hardcoded versions | `runs-on: ubuntu-20.04` breaks silently | Pin action versions, use `.tool-versions` |
| Fetch entire history | `actions/checkout` with full clone | Use `fetch-depth: 1` (default) unless needed |
| No artifact retention | Artifacts accumulate, storage grows unbounded | Set `retention-days` / `expire_in` |
| Tests not in CI | "Works on my machine" | Run the same test command locally and in CI |
| Manual deploy with no gate | Accidental production deploys | Require environment approval |
| Ignoring flaky tests | `continue-on-error: true` hides real failures | Fix flaky tests; use retry only for infra issues |

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
