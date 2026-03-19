# Helm Charts Reference

Chart structure, templating patterns, values management, and common Helm commands for Kubernetes deployments.

---

## Chart Structure

```
my-chart/
  Chart.yaml              # chart metadata, version, dependencies
  values.yaml             # default configuration values
  values-staging.yaml     # environment override
  values-production.yaml  # environment override
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    hpa.yaml
    configmap.yaml
    secrets.yaml           # ExternalSecret or SealedSecret, never plain
    serviceaccount.yaml
    pdb.yaml
    _helpers.tpl           # template helpers (naming, labels)
    NOTES.txt              # post-install instructions
    tests/
      test-connection.yaml
  charts/                  # dependency sub-charts
```

## Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: My application Helm chart
type: application
version: 1.0.0            # chart version — bump on chart changes
appVersion: "2.3.1"       # application version — bump on app changes
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

## values.yaml

```yaml
replicaCount: 3

image:
  repository: registry.example.com/my-app
  tag: ""                   # overridden by CI/CD, defaults to appVersion
  pullPolicy: IfNotPresent

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: app.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: app-tls
      hosts:
        - app.example.com

probes:
  liveness:
    path: /healthz
    initialDelaySeconds: 15
  readiness:
    path: /ready
    initialDelaySeconds: 5
```

## Templating Patterns

**_helpers.tpl:**
```yaml
{{- define "my-app.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "my-app.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}
```

## Helm Commands

```bash
# Install or upgrade a release
helm upgrade --install my-app ./my-chart \
  -n production \
  -f values-production.yaml \
  --set image.tag=v2.3.1 \
  --wait --timeout 5m

# Dry run to preview manifests
helm template my-app ./my-chart -f values-production.yaml

# Lint the chart
helm lint ./my-chart -f values-production.yaml

# Run chart tests
helm test my-app -n production

# Rollback to previous release
helm rollback my-app 1 -n production

# View release history
helm history my-app -n production
```

## Chart Testing

```yaml
# templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "my-app.fullname" . }}-test"
  annotations:
    "helm.sh/hook": test
spec:
  restartPolicy: Never
  containers:
    - name: test
      image: busybox
      command: ['wget', '--spider', 'http://{{ include "my-app.fullname" . }}:80/healthz']
```
