# STEP 9: Performance Tuning

### Volume Strategies

| Type | Use Case | Syntax |
|------|----------|--------|
| Bind mount | Dev: live code reload | `./src:/app/src` |
| Named volume | Data persistence (DB, uploads) | `pgdata:/var/lib/postgresql/data` |
| tmpfs | Temporary/sensitive data, faster I/O | `tmpfs: /tmp` |
| Anonymous volume | Preserve container-only dirs | `/app/node_modules` |

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
    # OOM settings
    mem_swappiness: 0
    oom_kill_disable: false
```

### Build Performance

```bash
