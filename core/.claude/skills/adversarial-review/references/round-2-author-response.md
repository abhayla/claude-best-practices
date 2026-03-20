# STEP 4: Round 2 — Author Response

### 4.1 Author Response Format

For EVERY issue raised by the reviewer, the author MUST respond with one of these dispositions:

| Response | When to Use | Required Content |
|----------|-------------|-----------------|
| **Accept** | Issue is valid, will fix | Description of the fix to be applied |
| **Reject** | Issue is not valid | Evidence explaining why the issue does not apply — concrete counter-example, documentation reference, or proof |
| **Defer** | Valid issue but out of scope for this change | Tracking issue number or TODO with justification for deferral |
| **Partial** | Partially valid — will address some aspects | Which parts will be addressed and which will not, with reasoning for each |

### 4.2 Author Response Template

```
AUTHOR RESPONSE — ROUND 2
===========================

### R1: {Short title}
**Disposition:** ACCEPT
**Action:** {What will be changed and why the reviewer's concern is valid.}

### R2: {Short title}
**Disposition:** REJECT
**Evidence:** {Why this issue does not apply. Must include concrete proof — a test
that covers this case, a framework guarantee, a configuration that prevents it,
or a logical argument with specifics.}

### R3: {Short title}
**Disposition:** DEFER
**Tracking:** Created issue #{number} — "{issue title}"
**Justification:** {Why this can safely wait. What is the risk of deferring? Is
there a compensating control in the meantime?}

### R4: {Short title}
**Disposition:** PARTIAL
**Will address:** {What will be fixed and how.}
**Will not address:** {What will not be changed and why — with evidence.}
```

### 4.3 Author Response Rules

| Rule | Rationale |
|------|-----------|
| Every issue gets a response | Ignoring issues erodes the review process |
| Rejections require evidence | "I disagree" is not sufficient — prove it |
| Deferrals require a tracking issue | "We'll fix it later" without a ticket means it never gets fixed |
| Accepted items must describe the fix | The reviewer needs to verify the fix addresses their concern |
| No defensive responses | "That's by design" without explaining the design is dismissive |
| Acknowledge good catches | If the reviewer found a real bug, say so — it builds trust |

### 4.4 Apply Accepted Fixes

After completing the response, apply all accepted and partial fixes:

1. Make the code/plan changes for all ACCEPT and PARTIAL items
2. Run tests to verify fixes do not introduce regressions
3. For plan reviews: update the plan document with the changes

```bash
