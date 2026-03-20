# Secrets Management & Deployment Strategies


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
