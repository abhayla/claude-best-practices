# Contract Test Decision Criteria

## Contract Test Decision Criteria

Use the `contract-test` skill (Pact) when:
- **Multi-service architecture** — 2+ services communicating via HTTP/gRPC/messaging
- **Separate deploy cycles** — Consumer and provider deploy independently
- **Cross-team API boundaries** — Different teams own consumer vs provider

Skip contract tests for:
- **Monoliths** — Single deployable unit with no service boundaries
- **Internal modules** — Modules within the same service (use unit tests instead)
- **Third-party APIs** — You don't control the provider (use integration tests with recorded responses)

---

