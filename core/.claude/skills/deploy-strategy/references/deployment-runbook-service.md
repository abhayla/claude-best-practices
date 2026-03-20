# Deployment Runbook: <service>

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

