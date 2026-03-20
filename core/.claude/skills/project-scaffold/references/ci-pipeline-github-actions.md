# STEP 5: CI Pipeline (GitHub Actions)

## STEP 5: CI Pipeline (GitHub Actions)

Generate `.github/workflows/ci.yml` covering:

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - # Stack-specific lint setup
      - run: <lint command>

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      # DB services if needed (postgres, redis)
    steps:
      - uses: actions/checkout@v4
      - # Stack-specific test setup
      - run: <test command>
      - # Upload coverage report

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency audit
        run: <stack-specific audit command>
      - name: SAST scan
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/default
            p/owasp-top-ten

  build:
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    steps:
      - uses: actions/checkout@v4
      - run: <build command>
```

Stack-specific audit commands:

| Stack | Audit Command |
|-------|--------------|
| Python | `pip audit` or `safety check` |
| Node | `npm audit --audit-level=high` |
| Go | `govulncheck ./...` |
| Rust | `cargo audit` |
| Android | `./gradlew dependencyCheckAnalyze` (OWASP plugin) |

---

