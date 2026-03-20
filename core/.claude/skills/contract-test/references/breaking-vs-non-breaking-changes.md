# Breaking vs Non-Breaking Changes

### Breaking vs Non-Breaking Changes

| Change | Breaking | Why |
|--------|----------|-----|
| Remove field | Yes | Existing queries will fail |
| Remove type | Yes | Dependent queries/mutations break |
| Change field type | Yes | Client deserialization breaks |
| Add optional field | No | Existing queries unaffected |
| Add new type | No | No existing queries reference it |
| Deprecate field | No | Field still works, warns consumers |
| Add required argument | Yes | Existing mutations missing the arg |

