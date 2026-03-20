# Contract Evolution: Handling Breaking Changes

### Non-Breaking Changes (Safe)

| Change | Why Safe |
|--------|----------|
| Add a new optional field to response | Existing consumers ignore unknown fields |
| Add a new endpoint | No consumer depends on it yet |
| Widen an accepted input type | Existing inputs still valid |

### Breaking Changes (Require Coordination)

| Change | Migration Path |
|--------|---------------|
| Remove a response field | 1. Deprecate field, 2. Update all consumers, 3. Remove field |
| Rename an endpoint | 1. Add new endpoint, 2. Migrate consumers, 3. Remove old endpoint |
| Change field type | 1. Add new field with new type, 2. Migrate consumers, 3. Remove old field |
| Remove an endpoint | 1. Verify no consumer pacts reference it, 2. Remove |

### Versioning Strategy

- Tag every Pact with the git SHA and branch name
- Use broker environments (`dev`, `staging`, `production`) to track deployed versions
- Use `record-deployment` / `record-release` to tell the broker what is deployed where

---

