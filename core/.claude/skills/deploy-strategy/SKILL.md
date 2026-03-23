---
name: deploy-strategy
description: >
  Design deployment strategies including GitOps (ArgoCD/Flux), progressive delivery
  (canary/blue-green), zero-downtime DB migrations, and mobile app deployment via
  Fastlane. Use when planning production deployments or setting up delivery pipelines.
triggers:
  - deploy strategy
  - gitops
  - canary deploy
  - progressive delivery
  - blue green
  - zero downtime
  - db migration deploy
  - production readiness
  - secret rotation
  - cdn caching
  - play store deploy
  - app store deploy
  - mobile deploy
  - fastlane
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<deployment target description, or 'review current strategy'>"
version: "1.0.0"
type: workflow
---

# Deploy Strategy — GitOps, Progressive Delivery & Zero-Downtime Migrations

Configure advanced deployment strategies for production-grade releases.

**Input:** $ARGUMENTS

---

## STEP 1: Assess Current State

Determine what deployment infrastructure already exists:

```bash
# Check for existing deployment configs
ls -la .github/workflows/deploy* k8s/ helm/ argocd/ flux/ 2>/dev/null

# Check for database migration setup
ls -la migrations/ alembic/ prisma/ 2>/dev/null

# Check current deployment method
grep -l "deploy\|release\|publish" .github/workflows/*.yml 2>/dev/null
```

Present the current state and recommended strategy:

```markdown
## STEP 2: GitOps Setup

### 2.1 Choose GitOps Tool

| Tool | Best For | Complexity |
|------|---------|-----------|
| ArgoCD | Teams wanting a UI, multi-cluster | Medium |
| Flux | GitOps-purist, lightweight | Low |
| Neither | Simple apps, not on K8s | — |

### 2.2 ArgoCD Configuration

```yaml
# argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: <app-name>
  namespace: argocd
spec:
  project: default
  source:
    repoURL: <git-repo-url>
    targetRevision: main
    path: k8s/overlays/production  # or helm/
  destination:
    server: https://kubernetes.default.svc
    namespace: <app-namespace>
  syncPolicy:
    automated:
      prune: true        # Remove resources deleted from git
      selfHeal: true      # Revert manual cluster changes
    syncOptions:
      - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 2.3 Flux Configuration

```yaml
# flux/kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: <app-name>
  namespace: flux-system
spec:
  interval: 5m
  path: ./k8s/overlays/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: <app-name>
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: <app-name>
      namespace: <app-namespace>
  timeout: 3m
```

## STEP 3: Progressive Delivery

### 3.1 Strategy Selection

| Strategy | Risk | Complexity | Best For |
|----------|------|-----------|----------|
| Rolling Update | Medium | Low | Simple apps, no traffic splitting |
| Blue/Green | Low | Medium | Instant rollback needed |
| Canary | Very Low | High | High-traffic, metric-driven releases |
| A/B Testing | Feature-dependent | High | UX experiments |

### 3.2 Canary with Flagger (Istio/Nginx)

```yaml
# flagger/canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: <app-name>
  namespace: <namespace>
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <app-name>
  progressDeadlineSeconds: 600
  service:
    port: 80
    targetPort: 8000
  analysis:
    interval: 30s           # Check every 30s
    threshold: 5             # Max failed checks before rollback
    maxWeight: 50            # Max traffic to canary (%)
    stepWeight: 10           # Increase canary traffic by 10% each step
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99            # Rollback if success rate < 99%
        interval: 30s
      - name: request-duration
        thresholdRange:
          max: 500           # Rollback if p99 latency > 500ms
        interval: 30s
    webhooks:
      - name: smoke-test
        type: pre-rollout
        url: http://flagger-loadtester/
        metadata:
          cmd: "curl -s http://<app-name>-canary/health"
```

### 3.3 Canary with Argo Rollouts

```yaml
# k8s/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: <app-name>
spec:
  replicas: 3
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 2m}     # Observe metrics
        - setWeight: 30
        - pause: {duration: 5m}
        - setWeight: 50
        - pause: {duration: 5m}
        - setWeight: 100
      canaryMetadata:
        labels:
          role: canary
      stableMetadata:
        labels:
          role: stable
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 2
        args:
          - name: service-name
            value: <app-name>
  revisionHistoryLimit: 3
```

### 3.4 Blue/Green Deployment

```yaml
# k8s/rollout-bluegreen.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: <app-name>
spec:
  strategy:
    blueGreen:
      activeService: <app-name>-active
      previewService: <app-name>-preview
      autoPromotionEnabled: false   # Manual promotion after verification
      prePromotionAnalysis:
        templates:
          - templateName: smoke-test
      postPromotionAnalysis:
        templates:
          - templateName: success-rate
```

---

## STEP 4: Zero-Downtime Database Migrations


**Read:** `references/zero-downtime-database-migrations.md` for detailed step 4: zero-downtime database migrations reference material.

# CI/CD pipeline migration step
jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - name: Run pre-deploy migrations
        run: |
          # Only EXPAND migrations (additive, backward-compatible)
          alembic upgrade head
          # Verify: old code still works with new schema
          curl -f http://staging/health

  deploy:
    needs: migrate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy new code
        run: <deploy command>

  post-migrate:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Run post-deploy migrations
        run: |
          # CONTRACT migrations (cleanup, add constraints)
          alembic upgrade head
```

### 4.4 Rollback Strategy

```markdown
## STEP 5: Production Readiness Review (PRR)

Before the first production deploy, complete this checklist:


**Read:** `references/production-readiness-review-prr.md` for detailed step 5: production readiness review (prr) reference material.

## STEP 6: Deployment Runbook

Generate a deployment runbook:

```markdown
## Deployment Runbook: <service>


**Read:** `references/deployment-runbook-service.md` for detailed deployment runbook: <service> reference material.

## STEP 7: Secret Rotation Strategy


**Read:** `references/secret-rotation-strategy.md` for detailed step 7: secret rotation strategy reference material.

# Terraform: AWS Secrets Manager with auto-rotation
resource "aws_secretsmanager_secret" "db_password" {
  name = "${local.name_prefix}-db-password"
}

resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_lambda_arn = aws_lambda_function.secret_rotation.arn

  rotation_rules {
    automatically_after_days = 30
  }
}
```

### 7.3 Kubernetes Secret Management

```yaml
# External Secrets Operator (ESO) — sync vault secrets to K8s
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h        # Re-sync from vault every hour
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: db-credentials      # K8s secret name
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: prod/db-password
        property: password
```

# Dual-read example: accept both JWT signing keys
CURRENT_KEY = get_secret("jwt-signing-key-current")
PREVIOUS_KEY = get_secret("jwt-signing-key-previous")

def verify_token(token: str) -> Claims:
    try:
        return jwt.decode(token, CURRENT_KEY)
    except jwt.InvalidSignatureError:
        return jwt.decode(token, PREVIOUS_KEY)  # Accept old key during rotation
```

## STEP 8: CDN & Edge Caching Strategy


**Read:** `references/cdn-edge-caching-strategy.md` for detailed step 8: cdn & edge caching strategy reference material.

# CI/CD: invalidate CDN on deploy
- name: Invalidate CloudFront
  run: |
    aws cloudfront create-invalidation \
      --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
      --paths "/index.html" "/api/*"
```

## STEP 9: Mobile App Deployment

### 9.1 Android — Play Store Deployment

```bash
# Build release APK/AAB
./gradlew bundleRelease  # Produces .aab (preferred over .apk)

# Sign with keystore
jarsigner -keystore release-keystore.jks \
  -storepass $KEYSTORE_PASSWORD \
  app/build/outputs/bundle/release/app-release.aab \
  release-key-alias
```

**Fastlane setup:**

```ruby
# fastlane/Fastfile
platform :android do
  desc "Deploy to Play Store internal track"
  lane :deploy_internal do
    gradle(task: "bundleRelease")
    upload_to_play_store(
      track: "internal",
      aab: "app/build/outputs/bundle/release/app-release.aab",
      skip_upload_metadata: true,
      skip_upload_changelogs: false
    )
  end

  desc "Promote internal to beta"
  lane :promote_beta do
    upload_to_play_store(
      track: "internal",
      track_promote_to: "beta"
    )
  end

  desc "Promote beta to production (staged rollout)"
  lane :promote_production do
    upload_to_play_store(
      track: "beta",
      track_promote_to: "production",
      rollout: "0.1"  # 10% staged rollout
    )
  end
end
```

**CI/CD (GitHub Actions):**

```yaml
# .github/workflows/android-deploy.yml
name: Android Deploy
on:
  push:
    tags: ['v*']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
      - name: Decode keystore
        run: echo "${{ secrets.KEYSTORE_BASE64 }}" | base64 -d > release-keystore.jks
      - name: Build release bundle
        run: ./gradlew bundleRelease
        env:
          KEYSTORE_PASSWORD: ${{ secrets.KEYSTORE_PASSWORD }}
          KEY_ALIAS: ${{ secrets.KEY_ALIAS }}
          KEY_PASSWORD: ${{ secrets.KEY_PASSWORD }}
      - uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_SERVICE_ACCOUNT_JSON }}
          packageName: com.example.app
          releaseFiles: app/build/outputs/bundle/release/app-release.aab
          track: internal
```

### 9.2 iOS — App Store Deployment

```ruby
# fastlane/Fastfile
platform :ios do
  desc "Deploy to TestFlight"
  lane :deploy_testflight do
    build_app(
      scheme: "MyApp",
      export_method: "app-store"
    )
    upload_to_testflight(
      skip_waiting_for_build_processing: true
    )
  end

  desc "Submit to App Store Review"
  lane :submit_review do
    deliver(
      submit_for_review: true,
      automatic_release: false,  # Manual release after approval
      force: true
    )
  end
end
```

## MUST DO

- Always assess current deployment state before recommending changes
- Always use the expand-contract pattern for schema changes
- Always separate pre-deploy and post-deploy migrations
- Always configure metric-based rollback for canary deployments
- Always complete the PRR checklist before first production deploy
- Always generate a deployment runbook
- Always define a secret rotation schedule for every secret type used
- Always configure CDN caching headers for static assets and API responses
- Always use staged rollout for mobile app production releases (never 100% immediately)
- Always use Play App Signing (Android) and Match (iOS) for signing key management

## MUST NOT DO

- MUST NOT run migrations and deploy code in a single atomic step — they must be separate
- MUST NOT skip the PRR for "simple" services — every production service needs it
- MUST NOT recommend GitOps for non-Kubernetes deployments — use push-based CI/CD instead
- MUST NOT mark irreversible migrations as "rollback safe"
- MUST NOT deploy canary without automated rollback metrics
- MUST NOT duplicate CI/CD setup that `ci-cd-setup` already handles — this skill adds GitOps and progressive delivery on top
- MUST NOT store signing keys, keystores, or service account credentials in git — use CI secrets with runtime decoding
- MUST NOT skip the dual-read phase during secret rotation — revoke old secret only after all instances use the new one
- MUST NOT set `max-age` on HTML pages — use `must-revalidate` or ETag-based caching
- MUST NOT release mobile apps to 100% production without monitoring crash rate at lower rollout percentages first
