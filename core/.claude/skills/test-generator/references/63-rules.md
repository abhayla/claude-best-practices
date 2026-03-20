# 6.3 Rules

### 6.3 Rules

- Test functions use `@pytest.mark.skip` (Python) or `test.skip()` (JS) — NOT empty bodies without skip markers
- Each skip includes `reason="E2E stub — fill in at Stage 8"`
- Page Object classes are fully defined with locators and actions
- One test file per user flow, one Page Object per page/screen
- Test IDs in the test matrix use status `STUB` (not `RED`) for E2E tests

---

