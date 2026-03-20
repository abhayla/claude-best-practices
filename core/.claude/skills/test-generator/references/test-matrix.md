# Test Matrix

## Test Matrix

| Requirement | Test Type | Test ID | Description | Status |
|-------------|-----------|---------|-------------|--------|
| AC-001 | Unit | UT-001 | Validate email format | RED |
| AC-002 | API | AT-001 | POST /users returns 201 | RED |
| AC-003 | E2E | ET-001 | User can sign up | STUB |
| NFR-002 | Perf | PT-001 | p95 < 200ms under 100rps | STUB |
| NFR-006 | Security | ST-001 | Auth required on /users/me | RED |
```

Every AC and NFR MUST map to at least one test. If a requirement has no corresponding test, flag it.

Wait for confirmation of the test matrix before generating test files.

---

