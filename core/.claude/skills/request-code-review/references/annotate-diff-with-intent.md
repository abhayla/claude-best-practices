# STEP 4: Annotate Diff with Intent

### 4.1 Intent Annotation Format

For each high-risk and medium-risk file, provide intent annotations:

```
FILE: src/auth/TokenService.ts

Line 42-55: Changed token refresh window from 5min to 15min
  WHY: Users on slow connections were getting logged out during page loads
       because the 5min window wasn't enough time for the refresh request
       to complete. 15min matches the P99 page load time from our metrics.
  RISK: Tokens are valid longer before refresh — increases window for
        stolen token use. Acceptable because we also added token binding
        to IP in this PR.

Line 78-92: Added IP-based token binding
  WHY: Compensating control for the extended refresh window above.
       If a token is used from a different IP than it was issued to,
       force a full re-authentication.
  RISK: Users on mobile networks with changing IPs may get logged out.
        Mitigated by only checking on sensitive operations, not every request.
```

### 4.2 When to Annotate

| Change Type | Annotate? | Reason |
|-------------|-----------|--------|
| New business logic | YES | Reviewer needs to understand the requirements |
| Bug fix | YES | Explain what was broken and why this fix is correct |
| Refactor | BRIEF | "Extracted to reduce duplication" is sufficient |
| Performance optimization | YES | Explain the bottleneck and why this approach helps |
| Security change | YES + RISK | Security changes always need threat model context |
| Test changes | BRIEF | "Added coverage for edge case X" |
| Config/build changes | ONLY IF NON-OBVIOUS | "Upgraded to Node 20 for native fetch support" |
| Formatting/style | NO | Should be self-evident |

---

