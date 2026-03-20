# Breaking Change Rules

### Breaking Change Rules

| Change | Breaking | Safe Alternative |
|--------|----------|-----------------|
| Remove field | Yes | Mark as reserved, keep field number |
| Rename field | Yes | Add new field, deprecate old |
| Change field type | Yes | Add new field with new type |
| Change field number | Yes | Never reuse field numbers |
| Remove service/RPC | Yes | Deprecate first, remove in next major |
| Add required field | Yes (proto3: all optional) | All fields optional in proto3 |

