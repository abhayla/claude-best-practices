# Pipeline Optimization & Common Anti-Patterns

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
