# 7.4 Zero-Downtime Secret Rotation

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
