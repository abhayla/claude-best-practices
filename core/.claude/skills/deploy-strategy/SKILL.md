---
name: deploy-strategy
description: >
  Advanced deployment strategies: GitOps (ArgoCD/Flux), progressive delivery
  (canary/blue-green with Flagger/Argo Rollouts), zero-downtime DB migrations
  (expand-contract), production readiness review, secret rotation strategy,
  CDN/edge caching, and mobile app deployment (Play Store/App Store via Fastlane).
  Use before first production deploy.
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
## Current Deployment State

| Component | Status | Tool |
|-----------|--------|------|
| CI pipeline | ✅ | GitHub Actions |
| Container build | ✅ | Docker multi-stage |
| K8s manifests | ✅ | Raw YAML / Helm |
| GitOps reconciliation | ❌ | None |
| Progressive delivery | ❌ | Rolling update only |
| DB migration ordering | ❌ | No deploy-time strategy |
| Production readiness | ❌ | No PRR checklist |
```

---

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

### 2.4 GitOps Workflow

```
Developer → PR → Review → Merge to main
                                  ↓
                        ArgoCD/Flux detects change
                                  ↓
                        Sync cluster to desired state
                                  ↓
                        Health check passes → Done
                        Health check fails → Alert + auto-rollback
```

Key principle: **Git is the source of truth.** No `kubectl apply` or `helm install` outside of GitOps.

---

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

### 4.1 The Expand-Contract Pattern

Every schema change follows three phases:

```
Phase 1: EXPAND (pre-deploy migration)
  ┌─────────────────────────────────────┐
  │ Add new column/table (nullable)     │
  │ No constraints yet                  │
  │ Old code continues to work          │
  └─────────────────────────────────────┘
                    ↓
Phase 2: DEPLOY (new code)
  ┌─────────────────────────────────────┐
  │ Deploy code that writes to BOTH     │
  │ old and new columns                 │
  │ Reads from new column with fallback │
  └─────────────────────────────────────┘
                    ↓
Phase 3: CONTRACT (post-deploy migration)
  ┌─────────────────────────────────────┐
  │ Backfill data from old to new       │
  │ Add NOT NULL constraints            │
  │ Drop old column (separate deploy)   │
  └─────────────────────────────────────┘
```

### 4.2 Migration Deployment Ordering

```yaml
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

### 4.3 Migration Safety Rules

| Rule | Why |
|------|-----|
| Never rename a column in one step | Old code references old name → crash |
| Never change a column type in one step | Old code expects old type → error |
| Never add NOT NULL without a default | Old code inserts without the column → crash |
| Never drop a column that's still read | Old instances read the column → error |
| Always separate DDL and DML migrations | Large data migrations lock tables |
| Always test migrations on a production-size dataset | Migrations that take seconds on dev take hours on prod |

### 4.4 Rollback Strategy

```markdown
### Migration Rollback Plan

| Migration | Rollback Command | Data Loss? |
|-----------|-----------------|-----------|
| 001_add_column | `alembic downgrade -1` | No |
| 002_backfill_data | Manual: restore from backup | Yes — backfill is one-way |
| 003_add_constraint | `alembic downgrade -1` | No |
| 004_drop_old_column | ❌ IRREVERSIBLE | Yes — data lost |
```

**Rule:** Mark any migration that drops data as IRREVERSIBLE and require explicit approval.

---

## STEP 5: Production Readiness Review (PRR)

Before the first production deploy, complete this checklist:

### 5.1 Reliability

- [ ] Health endpoint returns 200 when ready
- [ ] Readiness probe configured (K8s)
- [ ] Liveness probe configured (K8s)
- [ ] Graceful shutdown handles SIGTERM
- [ ] Request timeouts configured
- [ ] Circuit breaker on external dependencies
- [ ] Retry with exponential backoff on transient failures

### 5.2 Observability

- [ ] Structured logging to stdout
- [ ] Prometheus metrics endpoint (`/metrics`)
- [ ] Request duration histogram
- [ ] Error rate counter
- [ ] Custom business metrics
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Dashboard in Grafana
- [ ] Alert rules for SLO violation

### 5.3 Security

- [ ] Secrets in vault / sealed secrets (not env vars in manifests)
- [ ] Network policies restrict pod-to-pod communication
- [ ] Container runs as non-root
- [ ] Read-only filesystem where possible
- [ ] Resource limits set (CPU, memory)
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] DAST scan passed

### 5.4 Data

- [ ] Database backup schedule configured
- [ ] Point-in-time recovery tested
- [ ] Migration rollback tested
- [ ] Seed data for staging environment
- [ ] PII handling documented

### 5.5 Operations

- [ ] Runbook for common incidents
- [ ] On-call rotation defined
- [ ] SLOs defined with error budgets
- [ ] Incident response process documented
- [ ] Rollback procedure documented and tested

### 5.6 Report

```markdown
## Production Readiness Review

**Service:** <name>
**Date:** <date>
**Reviewer:** Claude Code

| Category | Score | Status |
|----------|-------|--------|
| Reliability | 7/7 | ✅ Ready |
| Observability | 8/8 | ✅ Ready |
| Security | 6/6 | ✅ Ready |
| Data | 4/5 | ⚠️ PII doc missing |
| Operations | 5/5 | ✅ Ready |

**Verdict:** READY for production (1 minor item)
```

---

## STEP 6: Deployment Runbook

Generate a deployment runbook:

```markdown
## Deployment Runbook: <service>

### Pre-deploy
1. Verify all tests pass on main
2. Run pre-deploy migrations against staging
3. Smoke test staging with new schema + old code
4. Create release tag: `git tag v<version>`

### Deploy
1. Push tag → triggers deploy pipeline
2. ArgoCD/Flux syncs new manifests
3. Canary starts at 10% traffic
4. Monitor error rate and latency for 5 minutes
5. If metrics healthy → auto-promote to 50%, then 100%
6. If metrics degrade → auto-rollback to previous version

### Post-deploy
1. Run post-deploy migrations (contract phase)
2. Verify health endpoint on all pods
3. Check Grafana dashboard for anomalies
4. Run smoke tests against production
5. Notify team in Slack: "v<version> deployed successfully"

### Rollback
1. `kubectl argo rollouts undo <app-name>` (Argo Rollouts)
2. Or: revert git commit → ArgoCD auto-syncs old version
3. Run `alembic downgrade -1` if migration rollback needed
4. Verify health endpoint returns 200
5. Create incident ticket if rollback was due to a bug
```

---

## STEP 7: Secret Rotation Strategy

### 7.1 Rotation Schedule

| Secret Type | Rotation Period | Method |
|-------------|----------------|--------|
| API keys (third-party) | 90 days | Regenerate in provider dashboard, update vault |
| Database credentials | 30 days | Automated via vault or cloud secrets manager |
| JWT signing keys | 7 days (access), 30 days (refresh) | Dual-key rotation (accept old+new during transition) |
| TLS certificates | Auto (Let's Encrypt) or 365 days | cert-manager (K8s) or ACM (AWS) auto-renewal |
| Service-to-service tokens | 90 days | OIDC federation preferred (no static tokens) |
| Encryption keys (KMS) | 365 days | Cloud KMS auto-rotation (AWS/GCP/Azure) |

### 7.2 Vault Integration Patterns

| Provider | Tool | Config |
|----------|------|--------|
| HashiCorp Vault | Vault Agent / CSI Provider | Dynamic secrets with TTL, auto-renewal |
| AWS | Secrets Manager | `rotation_lambda_arn` + `rotation_rules { automatically_after_days = 30 }` |
| GCP | Secret Manager | Version-based, `replication { automatic {} }` |
| Azure | Key Vault | `rotation_policy` block with auto-rotation |

```hcl
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

### 7.4 Zero-Downtime Secret Rotation

Dual-read pattern — accept both old and new secrets during rotation window:

```
Phase 1: Generate new secret, store as "pending"
Phase 2: Update app to accept BOTH old and new (dual-read)
Phase 3: Roll out new app version (canary/rolling)
Phase 4: Verify all traffic uses new secret
Phase 5: Revoke old secret
```

```python
# Dual-read example: accept both JWT signing keys
CURRENT_KEY = get_secret("jwt-signing-key-current")
PREVIOUS_KEY = get_secret("jwt-signing-key-previous")

def verify_token(token: str) -> Claims:
    try:
        return jwt.decode(token, CURRENT_KEY)
    except jwt.InvalidSignatureError:
        return jwt.decode(token, PREVIOUS_KEY)  # Accept old key during rotation
```

### 7.5 Secret Hygiene Checklist

- [ ] No secrets in environment variables visible via `/proc` or `docker inspect`
- [ ] No secrets in Docker image layers (use multi-stage builds or runtime injection)
- [ ] No secrets in git history (use `git-secrets` or `trufflehog` pre-commit hook)
- [ ] All secrets have an owner and rotation schedule documented
- [ ] Rotation can be performed without application downtime
- [ ] Secret access is logged and auditable
- [ ] Break-glass procedure exists for emergency secret revocation

---

## STEP 8: CDN & Edge Caching Strategy

### 8.1 CDN Provider Setup

| Provider | Best For | IaC Resource |
|----------|---------|-------------|
| CloudFront | AWS-native, S3 origins | `aws_cloudfront_distribution` |
| Cloudflare | Multi-cloud, DDoS protection, Workers | `cloudflare_zone` + `cloudflare_record` |
| Fastly | Real-time purge, VCL customization | `fastly_service_vcl` |
| Cloud CDN (GCP) | GCP-native, Cloud Storage origins | `google_compute_backend_bucket` |

### 8.2 Cache-Control Strategy

| Content Type | Cache-Control Header | TTL | Rationale |
|-------------|---------------------|-----|-----------|
| Static assets (JS/CSS with hash) | `public, max-age=31536000, immutable` | 1 year | Content-hash in filename = safe to cache forever |
| Static assets (no hash) | `public, max-age=86400` | 1 day | May change, moderate cache |
| HTML pages | `public, max-age=0, must-revalidate` | 0 (ETag) | Always check freshness |
| API responses (public) | `public, max-age=60, stale-while-revalidate=300` | 1 min + 5 min stale | Fresh data with fallback |
| API responses (private) | `private, no-store` | None | User-specific, never cache |
| Images/media | `public, max-age=604800` | 7 days | Rarely change |
| Fonts | `public, max-age=31536000, immutable` | 1 year | Never change |

### 8.3 Cache Invalidation

| Strategy | When to Use | How |
|----------|------------|-----|
| **Content-hash filenames** | JS/CSS bundles | Webpack/Vite adds hash to filename — new deploy = new URL |
| **Purge on deploy** | HTML, API responses | CI/CD step: `aws cloudfront create-invalidation --paths "/*"` |
| **Stale-while-revalidate** | API data that tolerates brief staleness | `Cache-Control: max-age=60, stale-while-revalidate=300` |
| **Tag-based purge** | Granular invalidation (Fastly, Cloudflare) | Surrogate-Key header + purge by tag |

```yaml
# CI/CD: invalidate CDN on deploy
- name: Invalidate CloudFront
  run: |
    aws cloudfront create-invalidation \
      --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} \
      --paths "/index.html" "/api/*"
```

### 8.4 Edge Functions (optional)

| Provider | Technology | Use Cases |
|----------|-----------|-----------|
| Cloudflare | Workers | A/B testing, auth at edge, URL rewrites, geolocation routing |
| AWS | Lambda@Edge / CloudFront Functions | Header manipulation, origin selection, auth |
| Vercel | Edge Middleware | Auth, redirects, feature flags, geolocation |

---

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

### 9.3 Versioning Strategy

| Platform | Version Field | Auto-Increment | Example |
|----------|--------------|----------------|---------|
| Android | `versionCode` (int) + `versionName` (string) | CI build number for versionCode | `versionCode=142`, `versionName="2.3.1"` |
| iOS | `CFBundleVersion` (build) + `CFBundleShortVersionString` (marketing) | CI build number for CFBundleVersion | `1.2.3 (142)` |

```kotlin
// build.gradle.kts — auto-increment versionCode from CI
android {
    defaultConfig {
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "2.3.1"
    }
}
```

### 9.4 Signing Key Management

| Item | Storage | Access |
|------|---------|--------|
| Android keystore (`.jks`) | CI secrets (base64 encoded) | Decode at build time, delete after |
| Play Store service account JSON | CI secrets | Upload only, no read access to store |
| iOS distribution certificate | Match (Fastlane) or manual in CI | Stored in encrypted git repo or CI secrets |
| iOS provisioning profiles | Match (Fastlane) auto-manages | Synced from Apple Developer Portal |

**Critical rules:**
- NEVER commit keystores or signing keys to git
- MUST use Play App Signing (Google manages upload key → signing key)
- MUST back up keystores separately — lost keystore = cannot update app
- Use Fastlane `match` for iOS to share signing identities across team

### 9.5 Staged Rollout

| Track/Phase | Audience | Purpose |
|-------------|----------|---------|
| Internal (Android) / TestFlight (iOS) | Team only | Smoke testing |
| Closed beta / TestFlight external | Selected users | Beta testing |
| Open beta / Public TestFlight | Opt-in users | Pre-release validation |
| Production 10% → 50% → 100% | Staged | Gradual rollout with crash monitoring |

Monitor crash rate (Firebase Crashlytics / Sentry) at each rollout stage. Halt rollout if crash rate exceeds baseline by >2x.

---

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
