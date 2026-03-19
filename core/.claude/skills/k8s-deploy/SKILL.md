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

### Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
  labels:
    app: my-app
    version: v1.2.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        version: v1.2.0
    spec:
      containers:
        - name: my-app
          image: registry.example.com/my-app:v1.2.0
          ports:
            - containerPort: 8080
              name: http
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

### Deployment Strategies

**Rolling Update** (default, zero-downtime):
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # max pods above desired count during update
      maxUnavailable: 0    # zero downtime — always keep all replicas up
```

**Recreate** (kill all, then create — use for stateful apps that cannot run multiple versions):
```yaml
spec:
  strategy:
    type: Recreate
```

### Resource Requests and Limits

| Field | Purpose | Guideline |
|-------|---------|-----------|
| `requests.cpu` | Scheduling guarantee | Set to observed P50 usage |
| `requests.memory` | Scheduling guarantee | Set to observed P90 usage |
| `limits.cpu` | Throttle ceiling | 2-5x the request, or omit to avoid throttling |
| `limits.memory` | OOMKill ceiling | 1.5-2x the request |

Rules:
- MUST set memory requests and limits on every container. Without limits, a single pod can OOMKill the node.
- CPU limits are debated. Omitting CPU limits avoids throttling but risks noisy-neighbor problems. Set them unless you have cluster-level resource quotas.
- Use `LimitRange` at the namespace level as a safety net (see Section 8).

### Pod Disruption Budgets

PDBs protect availability during voluntary disruptions (node drains, cluster upgrades):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2          # OR use maxUnavailable: 1
  selector:
    matchLabels:
      app: my-app
```

Rules:
- MUST create a PDB for any production deployment with 2+ replicas.
- Use `minAvailable` when you know the minimum healthy count. Use `maxUnavailable` when you want to allow a percentage to drain.
- Never set `minAvailable` equal to replica count — it blocks all node drains.

---

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

### Basic Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    # nginx ingress controller
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    # cert-manager TLS automation
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls-cert
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-app
                port:
                  number: 80
```

### Path-Based Routing

```yaml
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /v1/users
            pathType: Prefix
            backend:
              service:
                name: user-service
                port:
                  number: 80
          - path: /v1/orders
            pathType: Prefix
            backend:
              service:
                name: order-service
                port:
                  number: 80
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 80
```

### Common Annotations

**Nginx Ingress Controller:**
```yaml
nginx.ingress.kubernetes.io/rewrite-target: /$2
nginx.ingress.kubernetes.io/use-regex: "true"
nginx.ingress.kubernetes.io/rate-limit: "10"
nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
nginx.ingress.kubernetes.io/affinity: "cookie"
nginx.ingress.kubernetes.io/cors-allow-origin: "https://app.example.com"
```

**Traefik Ingress Controller:**
```yaml
traefik.ingress.kubernetes.io/router.entrypoints: websecure
traefik.ingress.kubernetes.io/router.middlewares: default-rate-limit@kubernetescrd
traefik.ingress.kubernetes.io/router.tls: "true"
```

### TLS with cert-manager

1. Install cert-manager
2. Create a `ClusterIssuer`:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
```
3. Add annotation `cert-manager.io/cluster-issuer: letsencrypt-prod` to your Ingress.
4. cert-manager automatically provisions and renews certificates.

---

## 4. ConfigMaps and Secrets

### ConfigMap — Creation and Usage

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  LOG_LEVEL: "info"
  config.yaml: |
    server:
      port: 8080
      workers: 4
```

**Mount as environment variables:**
```yaml
spec:
  containers:
    - name: my-app
      envFrom:
        - configMapRef:
            name: app-config
```

**Mount as files:**
```yaml
spec:
  containers:
    - name: my-app
      volumeMounts:
        - name: config-volume
          mountPath: /etc/config
          readOnly: true
  volumes:
    - name: config-volume
      configMap:
        name: app-config
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  DB_PASSWORD: cGFzc3dvcmQxMjM=    # base64-encoded, NOT encrypted
  API_KEY: c2VjcmV0LWtleQ==
```

**Mount as environment variables:**
```yaml
spec:
  containers:
    - name: my-app
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: DB_PASSWORD
```

Rules:
- NEVER commit plain Kubernetes Secret manifests to version control. Base64 is encoding, not encryption.
- Use Sealed Secrets or External Secrets Operator for GitOps workflows.

### Sealed Secrets (Bitnami)

```bash
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

### CPU-Based Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Memory-Based Autoscaling

```yaml
metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Custom Metrics (Prometheus Adapter)

```yaml
metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 100
```

Requires Prometheus + Prometheus Adapter or KEDA for event-driven scaling.

### Scaling Behavior

Control how fast scaling happens to prevent flapping:

```yaml
spec:
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60      # add max 2 pods per minute
        - type: Percent
          value: 50
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300   # wait 5 min before scaling down
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120     # remove max 1 pod per 2 minutes
```

### Guidelines

- MUST set `minReplicas: 2` for production (HA requires at least 2 pods).
- Set `maxReplicas` based on budget and downstream capacity (DB connections, etc.).
- Scale-down should be slower than scale-up to avoid flapping.
- Combine CPU and memory metrics — use `max` policy so either can trigger scaling.
- HPA requires resource requests to be set on the target deployment.
- For event-driven workloads (queue depth, Kafka lag), use KEDA instead of HPA.

---

## 7. RBAC

### ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: production
automountServiceAccountToken: false   # opt-in, not opt-out
```

### Role (namespace-scoped)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]
```

### ClusterRole (cluster-wide)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-reader
rules:
  - apiGroups: [""]
    resources: ["nodes", "pods", "services"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["metrics.k8s.io"]
    resources: ["pods", "nodes"]
    verbs: ["get", "list"]
```

### RoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-binding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: my-app-sa
    namespace: production
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

### Least Privilege Rules

- MUST create dedicated ServiceAccounts per workload. Never use the `default` SA.
- Set `automountServiceAccountToken: false` on ServiceAccounts and only enable it on pods that need API access.
- Use `Role` (namespaced) instead of `ClusterRole` unless the workload genuinely needs cluster-wide access.
- Never grant `*` (wildcard) verbs or resources. Enumerate exactly what is needed.
- Audit RBAC periodically: `kubectl auth can-i --list --as=system:serviceaccount:production:my-app-sa`.

---

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
