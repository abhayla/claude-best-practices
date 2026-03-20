# GitHub Actions Reference


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
