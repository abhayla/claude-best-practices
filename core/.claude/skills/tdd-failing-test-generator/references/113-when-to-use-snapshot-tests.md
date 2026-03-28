# 11.3 When to Use Snapshot Tests

### 11.3 When to Use Snapshot Tests

- **API response shapes** — Lock down JSON structure to catch unintended changes
- **Serialized domain entities** — Ensure serialization format doesn't drift
- **Configuration output** — Generated config files, migration SQL
- **Visual regression** — Delegate to `verify-screenshots` skill (already covered)

Skip snapshot tests for:
- Frequently changing output (timestamps, IDs) — use selective snapshots
- Large binary output — use hash comparison instead

---

