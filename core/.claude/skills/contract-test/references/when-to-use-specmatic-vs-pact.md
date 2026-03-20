# When to Use Specmatic vs Pact

### When to Use Specmatic vs Pact

| Criteria | Specmatic | Pact |
|----------|-----------|------|
| Contract source | OpenAPI/AsyncAPI spec | Consumer-generated expectations |
| Test code needed | None | Yes (consumer + provider) |
| Supports | REST, gRPC, GraphQL, Kafka | REST, GraphQL, messages |
| Breaking change detection | Built-in backward compatibility check | Via Pact broker `can-i-deploy` |
| Best for | API-first teams with maintained specs | Teams without formal API specs |

---

