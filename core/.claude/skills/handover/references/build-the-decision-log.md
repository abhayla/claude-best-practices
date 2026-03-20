# STEP 3: Build the Decision Log

### 3.1 Decision Categories

| Category | Examples |
|----------|---------|
| **Architecture** | "Used event-driven approach instead of polling" |
| **Library/Tool choice** | "Chose pydantic over dataclasses for validation" |
| **Algorithm** | "Used binary search instead of linear scan — data is always sorted" |
| **Workaround** | "Used env var override because config system doesn't support per-env values yet" |
| **Scope** | "Skipped edge case X — not in the current requirements" |
| **Testing strategy** | "Mocked the external API instead of using the sandbox — sandbox is unreliable" |
| **Trade-off** | "Accepted O(n) memory for O(1) lookup — dataset is small enough" |

### 3.2 Decision Record Format

For session-level decisions (tactical), use the summary table:

```markdown
| Decision | Reasoning | Alternatives Considered | Reversible? |
|----------|-----------|------------------------|-------------|
| Used SQLite for local cache | Low overhead, no server needed | Redis (overkill), file-based JSON (too slow for queries) | Yes — swap storage backend |
| Pinned dependency X to v2.3 | v3.0 has breaking change in API we use | Upgrade and refactor (too risky mid-sprint) | Yes — upgrade later |
```

### 3.3 Architecture Decision Records (ADR)

For architecture-level decisions (strategic, long-lasting), use the full ADR format. These persist beyond a single session and should be saved to `docs/decisions/` for the team.

```markdown
