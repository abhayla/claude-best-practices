# STEP 6: Round 3 — Final Resolution (If Needed)

### 6.1 Round 3 Trigger Check

```
Escalated items from Round 2: {count}
  Critical escalations: {count}
  Major escalations: {count}
  Minor escalations: {count}

Round 3 required: {YES if any escalations, NO if all satisfied}
```

### 6.2 Round 3 Protocol

For each escalated item, attempt final resolution:

**Author's final response options:**

| Option | When to Use |
|--------|-------------|
| **Concede** | Reviewer's additional evidence is convincing — apply the fix |
| **Compromise** | Find a middle ground that addresses the reviewer's concern differently |
| **Escalate to Human** | Genuine disagreement that requires human judgment |

**Reviewer's final response options:**

| Option | When to Use |
|--------|-------------|
| **Accept resolution** | Author's concession or compromise adequately addresses the concern |
| **Maintain objection** | Issue remains unresolved — flag for human review |

### 6.3 Round 3 Format

```
FINAL RESOLUTION — ROUND 3
============================

### R2: {Short title}
**Author:** COMPROMISE — Will implement {alternative approach} that addresses the
  security concern without the performance overhead of the reviewer's suggestion.
**Reviewer:** ACCEPT RESOLUTION — The compromise adequately mitigates the risk.

### R4: {Short title}
**Author:** ESCALATE TO HUMAN — Genuine design disagreement about {topic}.
  Author position: {summary}
  Reviewer position: {summary}
**Reviewer:** MAINTAIN OBJECTION — This is a {severity} issue that should not ship
  without human review.
```

### 6.4 Human Escalation Protocol

If any items remain unresolved after Round 3:

```
HUMAN REVIEW REQUIRED
======================

The following issues could not be resolved through adversarial review:

1. R4: {title}
   Severity: {Critical | Major}
   Author position: {summary}
   Reviewer position: {summary}
   Risk if shipped as-is: {concrete description}

Action needed: Human reviewer should evaluate both positions and make a decision.
The adversarial review is BLOCKED until these items are resolved.
```

Present this to the user and WAIT for their decision before proceeding. Do NOT auto-resolve human-escalated items.

---

