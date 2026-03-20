# STEP 5: Round 2 — Reviewer Follow-Up

### 5.1 Reviewer Follow-Up Protocol

For each issue, the reviewer evaluates the author's response:

| Author Response | Reviewer Action |
|----------------|----------------|
| **Accept** | Verify the fix actually addresses the issue. If the fix is incomplete or introduces a new problem, escalate with more evidence. |
| **Reject** | Evaluate the author's counter-evidence. If the rejection is well-supported, accept it. If the evidence is weak or missing, escalate. |
| **Defer** | Verify a tracking issue was created. If the deferral is risky (security, data integrity), escalate. |
| **Partial** | Verify the addressed portion is correct. Evaluate whether the unaddressed portion is acceptable. |

### 5.2 Reviewer Follow-Up Format

```
REVIEWER FOLLOW-UP — ROUND 2
==============================

### R1: {Short title}
**Author response:** ACCEPT
**Reviewer verdict:** SATISFIED — Fix correctly addresses the concern.

### R2: {Short title}
**Author response:** REJECT
**Reviewer verdict:** ESCALATE
**Additional evidence:** {New evidence or stronger argument for why this IS an
issue, addressing the author's counter-arguments point by point.}

### R3: {Short title}
**Author response:** DEFER
**Reviewer verdict:** SATISFIED — Tracking issue created, risk is low.

### R4: {Short title}
**Author response:** PARTIAL
**Reviewer verdict:** ESCALATE
**Concern:** {The unaddressed portion is higher risk than the author assessed.
Here is a scenario where it causes a real problem: ...}
```

### 5.3 Escalation Criteria

The reviewer SHOULD escalate (mark as ESCALATE instead of SATISFIED) only when:

| Criterion | Example |
|-----------|---------|
| Author's rejection lacks concrete evidence | "It's fine" without proof |
| Fix does not fully address the issue | Fixed SQL injection in one query but left another vulnerable |
| Deferral is risky | Deferring a security issue with no compensating control |
| New issue introduced by the fix | Fix for race condition introduces a deadlock |
| Critical issue with insufficient partial fix | Partial fix leaves a data corruption path open |

The reviewer MUST NOT escalate for:
- Style preferences the author disagreed with
- Minor issues the author reasonably deferred
- Issues where the author provided strong counter-evidence
- Disagreements about approach when both approaches are valid

---

