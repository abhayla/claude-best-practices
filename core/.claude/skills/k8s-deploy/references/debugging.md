# Debugging and Anti-Patterns Reference

Essential kubectl debugging commands, common failure patterns, and security best practices for Kubernetes workloads.

---

## Essential kubectl Commands

```bash
# Cluster overview
kubectl get nodes -o wide
kubectl top nodes
kubectl top pods -n production

# Deployment status
kubectl get deployments -n production
kubectl rollout status deployment/my-app -n production
kubectl rollout history deployment/my-app -n production

# Pod inspection
kubectl get pods -n production -o wide
kubectl describe pod <pod-name> -n production
kubectl get events -n production --sort-by='.lastTimestamp'

# Logs
kubectl logs <pod-name> -n production
kubectl logs <pod-name> -n production --previous     # crashed container
kubectl logs <pod-name> -n production -c <container>  # specific container
kubectl logs -l app=my-app -n production --tail=100   # by label

# Exec into pod
kubectl exec -it <pod-name> -n production -- /bin/sh

# Port forwarding
kubectl port-forward svc/my-app 8080:80 -n production
kubectl port-forward pod/<pod-name> 5432:5432 -n production

# Resource usage
kubectl top pods -n production --sort-by=memory
kubectl top pods -n production --sort-by=cpu
```

## Debugging CrashLoopBackOff

1. Check events: `kubectl describe pod <pod> -n <ns>`
2. Check previous logs: `kubectl logs <pod> --previous -n <ns>`
3. Common causes:
   - Failing liveness probe — check probe config and endpoint
   - OOMKilled — increase memory limits
   - Missing ConfigMap/Secret — check mounts
   - Permission denied — check RBAC and SecurityContext
   - Image pull error — check image name, tag, and pull secrets

## Debugging Pending Pods

1. Check events: `kubectl describe pod <pod> -n <ns>`
2. Common causes:
   - Insufficient resources — check node capacity vs requests
   - Node selector/affinity mismatch — check node labels
   - PVC not bound — check storage class and PV availability
   - Too many pods — check ResourceQuota

## Debugging Service Connectivity

```bash
# Verify endpoints exist
kubectl get endpoints my-app -n production

# Test DNS resolution from inside the cluster
kubectl run debug --rm -it --image=busybox -- nslookup my-app.production.svc.cluster.local

# Test connectivity
kubectl run debug --rm -it --image=busybox -- wget -qO- http://my-app.production.svc.cluster.local/healthz

# Check network policies
kubectl get networkpolicies -n production
```

## Debugging Ingress

```bash
# Check ingress status and assigned address
kubectl get ingress -n production
kubectl describe ingress my-app-ingress -n production

# Check ingress controller logs
kubectl logs -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx

# Test from inside the cluster
kubectl run debug --rm -it --image=curlimages/curl -- curl -H "Host: app.example.com" http://<ingress-controller-svc>/healthz
```

---

## Common Anti-Patterns

### MUST Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No resource limits | Pod can consume all node resources, causing OOMKill on co-located pods | Set `resources.requests` and `resources.limits` on every container |
| No probes | Dead containers keep receiving traffic; no automatic recovery | Add liveness, readiness, and startup probes |
| `image: my-app:latest` | Non-reproducible deployments, unclear what is running | Use immutable tags: `my-app:v1.2.3` or SHA digests |
| Secrets in plain YAML committed to Git | Credentials exposed in version history forever | Use SealedSecrets or ExternalSecrets Operator |
| No PDB | Cluster upgrades or node drains take down all replicas simultaneously | Create PodDisruptionBudget for every multi-replica deployment |
| Running as root | Container compromise gives root on the node | Set `securityContext.runAsNonRoot: true` |
| No network policies | Any pod can talk to any other pod | Default-deny ingress, allowlist specific traffic |
| Single replica in production | Any disruption causes downtime | Minimum 2 replicas with anti-affinity |
| No anti-affinity | All replicas on one node — node failure takes everything down | Use `podAntiAffinity` to spread across nodes |
| Hardcoded config | Config changes require rebuilds and redeployments | Use ConfigMaps and environment variables |
| No namespace isolation | All workloads in `default` namespace with no quotas | Use per-environment namespaces with ResourceQuotas |
| Liveness probe checks DB | DB outage causes cascade of pod restarts | Liveness checks app health only; readiness checks dependencies |

### Security Context Best Practices

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
    - name: my-app
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
```

### Pod Anti-Affinity (spread across nodes)

```yaml
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app: my-app
            topologyKey: kubernetes.io/hostname
```
