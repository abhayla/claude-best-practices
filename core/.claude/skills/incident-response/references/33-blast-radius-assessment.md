# 3.3 Blast Radius Assessment

### 3.3 Blast Radius Assessment

Map the dependency graph of the affected service:

1. **Direct dependencies** — what does the broken service call?
2. **Reverse dependencies** — what calls the broken service?
3. **Shared resources** — database, cache, message queue, shared storage
4. **Cross-region impact** — is the issue isolated to one region or global?

Document the blast radius visually if possible:
```
[Affected Service] --> [DB: impacted] --> [Service B: degraded]
                  --> [Cache: healthy]
                  --> [Service C: healthy]
[Service D] --> [Affected Service] --> [degraded]
[Service E] --> [Affected Service] --> [degraded]
```

---

