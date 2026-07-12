# API Versioning

### Version Lifecycle
| Version | Status | End of Life |
|---------|--------|-------------|
| v1 | Current | — |
| v2 | Planning | — |

### Breaking Change Policy
- Breaking changes require a new major version
- Non-breaking additions (new fields, new endpoints) are backward-compatible
- Deprecated endpoints are marked with `Sunset` header and 6-month notice
- Migration guides published for each major version bump

### Deprecation Headers
```
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Deprecation: true
Link: <https://docs.example.com/migration/v1-to-v2>; rel="sunset"
```
```

---

