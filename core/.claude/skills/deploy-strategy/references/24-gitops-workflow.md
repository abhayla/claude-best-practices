# 2.4 GitOps Workflow

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

