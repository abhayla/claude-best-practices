---
name: feature-flag
description: >
  Feature toggle patterns for gradual rollout and incomplete feature management.
  Covers LaunchDarkly, Unleash, and simple env-var flags. Includes flag type
  selection, implementation patterns per language (Python, TypeScript, Kotlin),
  dual-path testing, and a cleanup checklist to prevent flag debt.
triggers:
  - feature-flag
  - feature-toggle
  - gradual-rollout
  - flag management
  - feature gate
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<feature-name> [--type release|experiment|ops|permission] [--provider env|launchdarkly|unleash|custom]"
---

# Feature Flag Implementation

Implement feature flags for gradual rollout, experimentation, or incomplete feature management.

**Request:** $ARGUMENTS

---

## STEP 1: Assess Flag Need

Before adding a flag, determine whether one is actually warranted.

### 1.1 Decision Logic

Answer these questions in order — stop at the first YES:

1. **Is this a one-time migration or deploy step?** → NO FLAG. Use a migration script or deploy step instead. Stop.
2. **Is this a config value that rarely changes?** → NO FLAG. Use an environment variable directly. Stop.
3. **Is this work-in-progress that will be complete before merge?** → NO FLAG. Use a feature branch. Stop.
4. **Does this need gradual rollout to % of users?** → YES: release toggle.
5. **Does this need A/B testing with metrics?** → YES: experiment toggle.
6. **Is this a circuit breaker or kill switch?** → YES: ops toggle.
7. **Is this role-based or tier-based access?** → YES: permission toggle.

### 1.2 Reference Table

| Scenario | Use a Flag? | Alternative |
|----------|-------------|-------------|
| Gradual rollout to % of users | Yes (release toggle) | — |
| A/B test with metrics | Yes (experiment toggle) | — |
| Circuit breaker for external service | Yes (ops toggle) | — |
| Role-based access to a feature | Yes (permission toggle) | — |
| Work-in-progress behind a branch | No | Use a feature branch and merge when ready |
| One-time migration switch | No | Use a deploy script or migration step |
| Config that rarely changes | No | Use environment variables directly |

If no flag is needed, recommend the alternative and stop — do NOT proceed to Step 2.

## STEP 2: Choose Flag Type

| Type | Lifespan | Owner | Example |
|------|----------|-------|---------|
| **Release** | Days to weeks | Engineering | Ship dark code, enable for 5% of users, ramp to 100%, remove flag |
| **Experiment** | Weeks to months | Product | A/B test checkout flow, measure conversion, pick winner, remove flag |
| **Ops** | Long-lived | Infrastructure | Circuit breaker for payment gateway, kill switch for expensive computation |
| **Permission** | Long-lived | Product | Premium features, beta access, internal tooling |

Set the flag type explicitly — it determines naming, ownership, and cleanup schedule.

## STEP 3: Implement the Flag

### Naming Convention

Use a consistent naming pattern across the codebase:

```
<type>.<domain>.<feature>

release.checkout.new-payment-flow
experiment.onboarding.simplified-signup
ops.payments.stripe-circuit-breaker
permission.analytics.advanced-dashboard
```

### Option A: Environment Variable Flags (Simple)

Best for: small teams, ops toggles, single-service deployments.

**Python:**

```python
import os

def is_feature_enabled(flag_name: str, default: bool = False) -> bool:
    return os.getenv(f"FF_{flag_name.upper()}", str(default)).lower() in ("true", "1", "yes")

# Usage
if is_feature_enabled("new_checkout"):
    return new_checkout_flow(cart)
else:
    return legacy_checkout_flow(cart)
```

**TypeScript:**

```typescript
function isFeatureEnabled(flagName: string, defaultValue = false): boolean {
  const val = process.env[`FF_${flagName.toUpperCase()}`];
  return val ? ["true", "1", "yes"].includes(val.toLowerCase()) : defaultValue;
}

// Usage
const result = isFeatureEnabled("new_checkout")
  ? newCheckoutFlow(cart)
  : legacyCheckoutFlow(cart);
```

**Kotlin:**

```kotlin
fun isFeatureEnabled(flagName: String, default: Boolean = false): Boolean {
    val value = System.getenv("FF_${flagName.uppercase()}") ?: return default
    return value.lowercase() in listOf("true", "1", "yes")
}

// Usage
val result = if (isFeatureEnabled("new_checkout")) {
    newCheckoutFlow(cart)
} else {
    legacyCheckoutFlow(cart)
}
```

### Option B: LaunchDarkly SDK

Best for: percentage rollouts, user targeting, experiment toggles with analytics.

**Python:**

```python
import ldclient
from ldclient.config import Config

ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))
client = ldclient.get()

def get_flag(flag_key: str, user_context: dict, default: bool = False) -> bool:
    context = ldclient.Context.builder(user_context["key"]).name(user_context.get("name", "")).build()
    return client.variation(flag_key, context, default)
```

**TypeScript:**

```typescript
import * as LaunchDarkly from "@launchdarkly/node-server-sdk";

const client = LaunchDarkly.init(process.env.LAUNCHDARKLY_SDK_KEY!);

async function getFlag(flagKey: string, userContext: { key: string; name?: string }, defaultValue = false): Promise<boolean> {
  await client.waitForInitialization();
  const context = { kind: "user", key: userContext.key, name: userContext.name };
  return client.variation(flagKey, context, defaultValue);
}
```

### Option C: Unleash SDK

Best for: self-hosted, open-source flag management with activation strategies.

**Python:**

```python
from UnleashClient import UnleashClient

client = UnleashClient(
    url=os.getenv("UNLEASH_URL"),
    app_name="my-app",
    custom_headers={"Authorization": os.getenv("UNLEASH_API_KEY")},
)
client.initialize_client()

enabled = client.is_enabled("new-checkout", context={"userId": user.id})
```

**TypeScript:**

```typescript
import { initialize } from "unleash-client";

const unleash = initialize({
  url: process.env.UNLEASH_URL!,
  appName: "my-app",
  customHeaders: { Authorization: process.env.UNLEASH_API_KEY! },
});

const enabled = unleash.isEnabled("new-checkout", { userId: user.id });
```

### Option D: Custom Flag Service

Best for: teams needing full control, database-backed flags with admin UI.

```python
# Minimal flag service backed by a database table
# Schema: flags(name TEXT PK, enabled BOOLEAN, rollout_pct INT, allowed_users JSON, updated_at TIMESTAMP)

class FlagService:
    def __init__(self, db):
        self.db = db
        self._cache: dict[str, dict] = {}
        self._cache_ttl = 30  # seconds

    def is_enabled(self, flag_name: str, user_id: str | None = None) -> bool:
        flag = self._get_flag(flag_name)
        if not flag or not flag["enabled"]:
            return False
        if user_id and flag.get("allowed_users") and user_id in flag["allowed_users"]:
            return True
        if flag.get("rollout_pct", 100) < 100:
            return hash(f"{flag_name}:{user_id}") % 100 < flag["rollout_pct"]
        return True
```

## STEP 4: Test Both Paths

Every feature flag introduces a branch — both branches MUST be tested.

**Python (pytest):**

```python
@pytest.mark.parametrize("flag_on", [True, False])
def test_checkout_flow(monkeypatch, flag_on):
    monkeypatch.setenv("FF_NEW_CHECKOUT", str(flag_on))
    result = process_checkout(cart)
    if flag_on:
        assert result.uses_new_flow
    else:
        assert result.uses_legacy_flow
```

**TypeScript (Jest):**

```typescript
describe.each([true, false])("checkout flow (flag=%s)", (flagOn) => {
  beforeEach(() => {
    process.env.FF_NEW_CHECKOUT = String(flagOn);
  });
  it("processes checkout correctly", () => {
    const result = processCheckout(cart);
    expect(result.usesNewFlow).toBe(flagOn);
  });
});
```

**Kotlin (JUnit 5):**

```kotlin
@ParameterizedTest
@ValueSource(booleans = [true, false])
fun `checkout flow respects flag`(flagOn: Boolean) {
    setEnv("FF_NEW_CHECKOUT", flagOn.toString())
    val result = processCheckout(cart)
    assertEquals(flagOn, result.usesNewFlow)
}
```

## STEP 5: Document the Flag

Every flag MUST be registered in a flags inventory. Create or update a `flags.yml` (or equivalent) at the project root:

```yaml
flags:
  - name: release.checkout.new-payment-flow
    type: release
    owner: payments-team
    created: 2026-03-13
    cleanup_by: 2026-04-13
    description: New Stripe-based payment flow with 3DS support
    default: false
    jira: PAY-1234

  - name: ops.payments.stripe-circuit-breaker
    type: ops
    owner: platform-team
    created: 2026-01-15
    cleanup_by: null  # long-lived ops toggle
    description: Circuit breaker for Stripe API failures
    default: true
```

## STEP 6: Plan Cleanup

Release and experiment flags MUST be removed after rollout completes. Use this checklist:

### Flag Cleanup Checklist

```
Flag: {flag_name}
Type: {release|experiment}
Cleanup deadline: {date}

[ ] Verify flag is 100% enabled in production for at least 1 week
[ ] Remove flag checks from application code
[ ] Remove the losing code path (keep the winning path only)
[ ] Update tests — remove flag parameterization, keep only the winning-path tests
[ ] Remove flag from flags inventory (flags.yml)
[ ] Remove flag from flag provider (LaunchDarkly / Unleash / env vars)
[ ] Remove any flag-specific monitoring or dashboards
[ ] Deploy and verify no regressions
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| **Long-lived release flags** | Dead code accumulates, increases complexity | Set a cleanup deadline at creation; enforce with CI checks |
| **Nested flags** | `if flag_a and flag_b` creates 4 code paths, `if a and b and c` creates 8 | Combine into a single flag or redesign the feature boundary |
| **Flag dependencies** | Flag B only works when flag A is on | Document the dependency; prefer a single flag that enables both |
| **Flags in tight loops** | Remote flag evaluation in hot loops adds latency | Cache flag values; evaluate once per request, not per iteration |
| **No default value** | Missing env var or provider outage crashes the app | Always provide a safe default (usually `false` for release flags) |
| **Flag naming chaos** | `new_checkout`, `CHECKOUT_V2`, `use-new-checkout` in same codebase | Enforce the naming convention from Step 3 in code review |
| **Testing only one path** | Untested code path ships to production when flag flips | Always test both on and off paths (Step 4) |

---

## MUST DO

- MUST test both flag-on and flag-off code paths before merging
- MUST provide a safe default value for every flag (service stays functional if provider is down)
- MUST register every flag in the flags inventory with owner, type, and cleanup deadline
- MUST remove release and experiment flags within their cleanup deadline
- MUST use consistent naming convention across the entire codebase
- MUST cache remote flag evaluations — never call the provider in a tight loop

## MUST NOT DO

- MUST NOT nest more than one flag check in a single code path — combine flags or redesign instead
- MUST NOT create release flags without a cleanup deadline — flags without deadlines become permanent
- MUST NOT use feature flags as a substitute for proper configuration management
- MUST NOT leave dead code behind after removing a flag — remove both the check and the losing path
- MUST NOT evaluate remote flags synchronously in request-critical paths without caching
- MUST NOT skip testing the default/fallback path — provider outages will exercise it in production
