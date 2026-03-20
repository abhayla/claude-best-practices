---
name: k8s-deploy
description: >
  Kubernetes deployment skill covering manifests, services, ingress, secrets,
  probes, autoscaling, RBAC, namespaces, Helm charts, and debugging.
  Use when deploying, configuring, or troubleshooting Kubernetes workloads.
allowed-tools: "Read Grep Glob"
argument-hint: "<deployment-task-or-question>"
version: "1.0.2"
type: reference
triggers:
  - kubernetes deploy
  - k8s deploy
  - kubectl
  - helm chart
  - k8s manifests
---

# Kubernetes Deployment

Deploy, configure, and troubleshoot Kubernetes workloads.

**Request:** $ARGUMENTS

---

## 1. Deployment Manifests


**Read:** `references/1-deployment-manifests.md` for detailed 1. deployment manifests reference material.

## 2. Services

### ClusterIP (default — internal only)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 8080
      protocol: TCP
```

### NodePort (expose on every node's IP)

```yaml
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080       # 30000-32767 range
```

Use NodePort only for development or bare-metal clusters without a load balancer controller.

### LoadBalancer (cloud provider integration)

```yaml
spec:
  type: LoadBalancer
  ports:
    - port: 443
      targetPort: 8080
  # Cloud-specific annotations:
  # AWS: service.beta.kubernetes.io/aws-load-balancer-type: nlb
  # GCP: cloud.google.com/neg: '{"ingress": true}'
```

### Headless Service (for StatefulSets, direct pod DNS)

```yaml
spec:
  type: ClusterIP
  clusterIP: None          # headless — no virtual IP
  selector:
    app: my-db
  ports:
    - port: 5432
```

Each pod gets a stable DNS entry: `<pod-name>.<service-name>.<namespace>.svc.cluster.local`.

### Service Mesh Basics

When using Istio, Linkerd, or similar:
- Inject sidecars via namespace label: `istio-injection: enabled`
- Use `VirtualService` and `DestinationRule` instead of raw Ingress for traffic management
- Enable mTLS between services for zero-trust networking
- Use `ServiceEntry` for external service access control

---

## 3. Ingress


**Read:** `references/3-ingress.md` for detailed 3. ingress reference material.

## 4. ConfigMaps and Secrets


**Read:** `references/4-configmaps-and-secrets.md` for detailed 4. configmaps and secrets reference material.

# Install kubeseal CLI
# Encrypt a secret — only the cluster can decrypt it
kubeseal --format yaml < my-secret.yaml > my-sealed-secret.yaml
```

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-secrets
spec:
  encryptedData:
    DB_PASSWORD: AgBy3i4OJSWK+PiTySYZZA9rO...
```

Sealed Secrets are safe to commit to Git. The controller in-cluster decrypts them into regular Secrets.

### External Secrets Operator

Pull secrets from AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, Azure Key Vault:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: app-secrets
  data:
    - secretKey: DB_PASSWORD
      remoteRef:
        key: prod/my-app/db-password
```

---

## 5. Probes

### Liveness Probe

Restarts the container if it fails. Use for deadlock detection.

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
  successThreshold: 1
```

### Readiness Probe

Removes the pod from service endpoints if it fails. Use for dependency checks.

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Startup Probe

Disables liveness/readiness checks until the app has started. Use for slow-starting apps.

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 0
  periodSeconds: 5
  failureThreshold: 30     # 30 * 5s = 150s max startup time
```

### Probe Types

| Type | Use Case | Example |
|------|----------|---------|
| `httpGet` | HTTP endpoints | `path: /healthz, port: 8080` |
| `tcpSocket` | TCP port check | `port: 5432` (database) |
| `exec` | Custom command | `command: ["/bin/sh", "-c", "pg_isready"]` |
| `grpc` | gRPC health | `port: 50051` (requires k8s 1.24+) |

### Configuration Guidelines

| Parameter | Liveness | Readiness | Startup |
|-----------|----------|-----------|---------|
| `initialDelaySeconds` | App boot time | Short (5s) | 0 |
| `periodSeconds` | 10-30s | 5-10s | 5-10s |
| `timeoutSeconds` | 3-5s | 3-5s | 3-5s |
| `failureThreshold` | 3 | 3 | High (30+) |

Rules:
- MUST configure at least readiness and liveness probes for production containers.
- Liveness endpoint MUST NOT check external dependencies (DB, cache). If the DB is down, restarting your app will not fix it — it will cause a crash loop.
- Readiness endpoint SHOULD check external dependencies. This removes the pod from traffic when it cannot serve requests.
- Use startup probes for JVM apps, ML model loading, or anything with >30s boot time.

---

## 6. HPA Autoscaling


**Read:** `references/6-hpa-autoscaling.md` for detailed 6. hpa autoscaling reference material.

## 7. RBAC


**Read:** `references/7-rbac.md` for detailed 7. rbac reference material.

## 8. Namespace Management

### Resource Quotas

Prevent a single namespace from consuming all cluster resources:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
```

### Limit Ranges

Set defaults and constraints for individual containers:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
    - type: Container
      default:
        cpu: 200m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      max:
        cpu: "2"
        memory: 2Gi
      min:
        cpu: 50m
        memory: 64Mi
```

### Network Policies

Default deny all ingress, then allow specific traffic:

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
---
# Allow traffic from frontend to backend
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - port: 8080
          protocol: TCP
```

### Namespace Strategy

| Environment | Namespace Pattern | Notes |
|-------------|------------------|-------|
| Production | `production` | Strict quotas, network policies, PDBs |
| Staging | `staging` | Mirrors production config, lower quotas |
| Development | `dev-<team>` | Per-team, relaxed quotas |
| CI/CD | `ci-<pipeline-id>` | Ephemeral, auto-cleanup |

---

## 9. Helm Charts

> **Reference:** See [references/helm-charts.md](references/helm-charts.md) for chart structure, values management, templating patterns, and Helm commands.

---

## 10. Debugging & Anti-Patterns

> **Reference:** See [references/debugging.md](references/debugging.md) for kubectl debugging commands, common failure troubleshooting, and anti-patterns to avoid.

---

## Workflow

When deploying a new service to Kubernetes:

1. **Define the Deployment** with resource requests/limits, probes, and security context
2. **Create a Service** (ClusterIP for internal, LoadBalancer for external)
3. **Configure Ingress** if the service needs external HTTP(S) access
4. **Add ConfigMaps/Secrets** using SealedSecrets or External Secrets Operator
5. **Create a PDB** for production deployments
6. **Set up HPA** for autoscaling based on load
7. **Apply RBAC** with dedicated ServiceAccount and least-privilege Role
8. **Add Network Policies** for namespace isolation
9. **Package as Helm chart** for repeatable, environment-specific deployments
10. **Test** with `helm lint`, `helm template`, and `helm test`

---

## CRITICAL RULES

- MUST set resource requests and limits on every container
- MUST configure liveness and readiness probes for production workloads
- MUST use immutable image tags (never `latest` in production)
- MUST NOT commit plain Kubernetes Secrets to version control
- MUST create PodDisruptionBudgets for multi-replica production deployments
- MUST use dedicated ServiceAccounts with least-privilege RBAC
- MUST run containers as non-root with `readOnlyRootFilesystem` where possible
- MUST use namespaces with ResourceQuotas and LimitRanges
- MUST default-deny network ingress and allowlist specific traffic
- MUST spread replicas across nodes using pod anti-affinity
