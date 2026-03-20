# STEP 3: Round 1 — Reviewer Critique

### 3.1 Structured Critique Format

The reviewer MUST produce findings in this exact format. Each issue is a separate entry:

```
ADVERSARIAL REVIEW — ROUND 1
==============================

Review Mode: {PLAN REVIEW | CODE REVIEW}
Target: {file path, plan name, or PR number}
Reviewer: {model name or "subagent"}

---

### R1: {Short title}

| Field | Value |
|-------|-------|
| Issue ID | R1 |
| Category | {Security | Performance | Correctness | Design | Edge Case | Maintainability} |
| Severity | {Critical | Major | Minor} |
| Location | {file:line for code, section name for plan} |

**Evidence:**
{Concrete scenario or proof of why this is a problem. NOT "this might be an
issue" — show exactly how it fails, what input triggers it, or what the
consequence is.}

**Suggested Fix:**
{Specific, actionable recommendation. NOT "consider improving this" — provide
the exact change, pattern, or approach to use.}

---

### R2: {Short title}

| Field | Value |
|-------|-------|
| Issue ID | R2 |
| Category | ... |
| Severity | ... |
| Location | ... |

**Evidence:**
...

**Suggested Fix:**
...

---

(continue for all issues found)
```

### 3.2 Severity Definitions

The reviewer MUST use these severity levels consistently:

| Severity | Definition | Examples | Action Required |
|----------|-----------|----------|----------------|
| **Critical** | Will cause data loss, security breach, or system failure if shipped. Blocks proceeding. | SQL injection, auth bypass, data corruption, unhandled null in critical path, race condition causing duplicate payments | MUST fix before proceeding |
| **Major** | Significant quality or reliability issue. Should be fixed before shipping. | Missing pagination on unbounded query, no error handling on external call, N+1 query in hot path, missing input validation | SHOULD fix — defer only with tracking issue and justification |
| **Minor** | Improvement that would make the code better but is not blocking. | Suboptimal algorithm (but works), missing edge case test, naming inconsistency, missing code comment on complex logic | NICE TO FIX — can defer without tracking |

### 3.3 Category Definitions

| Category | Scope | Examples |
|----------|-------|---------|
| **Security** | Authentication, authorization, injection, data exposure, cryptography | Missing auth check, XSS in user input rendering, PII in logs |
| **Performance** | Speed, memory, scalability, resource usage | N+1 queries, unbounded loops, missing indices, memory leaks |
| **Correctness** | Logic errors, wrong behavior, data integrity | Off-by-one, null handling, race conditions, wrong return type |
| **Design** | Architecture, patterns, abstractions, API shape | Tight coupling, wrong abstraction level, leaky abstraction, god class |
| **Edge Case** | Boundary conditions, unusual inputs, failure modes | Empty list, max integer, concurrent modification, network timeout |
| **Maintainability** | Readability, testability, documentation, complexity | Magic numbers, duplicated logic, untestable design, missing docs |

### 3.4 Minimum Review Standards

The reviewer MUST NOT submit a critique with:
- Fewer than 3 issues for medium+ changes (look harder)
- Only minor issues for security-sensitive code (check security dimensions explicitly)
- Vague evidence ("this could be a problem") — every issue needs a concrete scenario
- Vague fixes ("consider improving") — every fix needs a specific recommendation
- Duplicate issues (same root cause reported multiple times)

If the reviewer genuinely finds fewer than 3 issues, they MUST explicitly state which criteria they checked and found clean:

```
Verified clean:
- Security: Checked for injection, auth bypass, data exposure — none found
- Performance: Checked for N+1, unbounded queries, blocking I/O — none found
- Correctness: Checked for off-by-one, null handling, race conditions — none found
```

---

