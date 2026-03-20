# 1. Deployment Manifests

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

