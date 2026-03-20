# 4. ConfigMaps and Secrets

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
