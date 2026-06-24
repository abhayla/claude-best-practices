# E2E Auth Patterns

### Login-Once, Reuse State

| Approach | Speed | Reliability | Use When |
|----------|-------|-------------|----------|
| UI login every test | Slow | Low | Only when testing the login flow itself |
| Saved auth state (cookies/tokens) | Fast | High | Default for all non-auth tests |
| API-generated token | Fastest | Highest | When the app supports token-based auth |

### Multi-User Scenarios

For tests where user A interacts with user B's data:
1. Create both users via API (UUID-based, unique per test run)
2. Authenticate both in separate browser contexts
3. User A creates shared resource → User B verifies access
4. Teardown: delete both users and shared resources

### Role-Based Access Testing

Test each role's permissions in E2E, not just the happy path:

| Role | Test | Expected |
|------|------|----------|
| Admin | Access admin panel | 200, panel visible |
| Regular user | Access admin panel | Redirect to home or 403 |
| Unauthenticated | Access protected page | Redirect to login |

### Token Refresh in Long E2E Runs

If auth tokens expire during a test suite (common with 30+ minute nightly runs):
- Use long-lived test tokens (set token expiry to 24h in test environment)
- Or implement token refresh in the test fixture (refresh before each test)
- Never hardcode tokens in test files — load from environment or fixture

### OAuth/SSO in CI

Real OAuth flows require browser redirects that are fragile in CI. Options:
1. **Mock the OAuth provider** — Return a valid token without the redirect flow
2. **Use test-specific auth bypass** — A `/test/login` endpoint that accepts
   a secret header and returns a session (disabled in production)
3. **Pre-authenticated session** — Create session via API, inject cookies

---

