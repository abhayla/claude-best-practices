# GitLab CI Reference

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
