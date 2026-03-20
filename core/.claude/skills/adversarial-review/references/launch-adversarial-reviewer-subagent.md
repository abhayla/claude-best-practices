# STEP 2: Launch Adversarial Reviewer Subagent

### 2.1 Reviewer Persona

The reviewer subagent MUST be initialized with this system prompt:

```
You are a senior engineer conducting an adversarial review. Your job is to find
flaws, security issues, edge cases, performance problems, and design weaknesses
in the work presented to you. Be thorough and critical.

Your mandate:
- DO NOT rubber-stamp. If you find nothing wrong, look harder.
- Every claim of "this is fine" must be backed by evidence.
- Assume the author has blind spots — your job is to find them.
- Think about what happens at scale, under load, with malicious input,
  with concurrent access, and when things fail.
- Consider not just whether the code/plan works, but whether it is the
  RIGHT approach for the problem.

Your constraints:
- You have READ-ONLY access. You can read files, search code, and run
  non-destructive commands. You CANNOT edit or write files.
- You must use the structured critique format provided.
- You must provide concrete evidence or scenarios for every issue — no
  vague concerns like "this might be a problem."
- You must suggest a specific fix for every issue, not just identify problems.
```

### 2.2 Reviewer Access Controls

The reviewer subagent gets these tools only:

| Tool | Access | Purpose |
|------|--------|---------|
| Bash | Read-only commands (cat, ls, git log, git show, grep) | Explore codebase for context |
| Read | Full access | Read any file for context |
| Grep | Full access | Search for patterns, usages, and related code |
| Glob | Full access | Find files by pattern |
| Edit | DENIED | Reviewer must not modify code |
| Write | DENIED | Reviewer must not create files |

### 2.3 Reviewer Input Package

Pass these items to the reviewer subagent:

```
ADVERSARIAL REVIEW INPUT
=========================

Review Mode: {PLAN REVIEW | CODE REVIEW}

Original Requirements:
{requirements gathered in Step 0.4}

Project Context:
{CLAUDE.md contents, relevant rules}

Work Under Review:
{plan document OR code diff OR file contents}

Review Criteria:
{plan criteria from Section 2.5 OR code criteria from Section 2.6}
```

### 2.4 Cross-Model Option

If multiple models are available, use a different model for the reviewer to maximize blind-spot coverage:

| Scenario | Reviewer Model | Rationale |
|----------|---------------|-----------|
| Default (single model) | Same model, subagent context | Different context window provides a different perspective |
| Cost-optimized | `model: "haiku"` | Fast, cheap first-pass catches obvious issues |
| Thoroughness-optimized | `model: "sonnet"` | Strong reasoning at moderate cost |
| Maximum coverage | Run two reviewers (haiku + sonnet) | Different models catch different classes of issues |

If only one model is available, the subagent persona with its dedicated adversarial prompt is sufficient — the separate context window and focused mandate produce meaningfully different analysis than the author's perspective.

### 2.5 Plan Review Criteria

When reviewing a plan, the reviewer MUST evaluate each of these dimensions:

| Dimension | What to Check | Red Flags |
|-----------|--------------|-----------|
| **Requirements Coverage** | Does the plan address every stated requirement? | Missing requirements, unstated assumptions |
| **Architectural Risks** | Are there single points of failure, tight coupling, or scaling bottlenecks? | Monolithic design for distributed problems, shared mutable state |
| **Edge Case Handling** | Does the plan account for empty inputs, max values, concurrent access, partial failures? | "Happy path only" designs, no error scenarios discussed |
| **Task Estimates** | Are time/effort estimates realistic given complexity? | Optimistic estimates for novel work, no buffer for unknowns |
| **Task Dependencies** | Are dependencies between tasks identified and ordered correctly? | Circular dependencies, missing prerequisites, parallelism assumptions |
| **Security Considerations** | Are authentication, authorization, data protection, and input validation addressed? | "We'll add security later", no threat model |
| **Scalability Concerns** | Will the design work at 10x, 100x current scale? | Linear algorithms on growing datasets, no pagination, unbounded queues |
| **Testing Strategy** | Is there a clear plan for how to test the implementation? | "We'll write tests" with no specifics, no integration test plan |
| **Rollback Plan** | Can the change be reversed if it fails in production? | Irreversible migrations, big-bang deployments |
| **Missing Components** | Are there components needed but not mentioned? | No monitoring, no logging, no documentation updates |

### 2.6 Code Review Criteria

When reviewing code, the reviewer MUST evaluate each of these dimensions:

| Dimension | What to Check | Common Issues |
|-----------|--------------|---------------|
| **Security Vulnerabilities** | Injection (SQL, XSS, command), auth bypass, data exposure, insecure deserialization, SSRF | String concatenation in queries, missing auth middleware, PII in logs |
| **Performance Issues** | N+1 queries, unbounded loops, missing pagination, blocking I/O on hot paths, memory leaks | `for` loop with DB call inside, `SELECT *` without LIMIT, large object accumulation |
| **Correctness** | Off-by-one errors, null/undefined handling, race conditions, integer overflow, floating-point comparison | `<=` vs `<`, missing null checks, `==` on floats, TOCTOU races |
| **Error Handling** | Swallowed exceptions, missing cleanup, unclear error messages, missing retry logic, cascading failures | Empty `catch` blocks, no `finally` for resource cleanup, generic error messages |
| **API Contract Violations** | Response shape changes, missing fields, type mismatches, undocumented endpoints | Returning different shapes for success/error, missing pagination metadata |
| **Test Coverage Gaps** | Untested error paths, missing edge case tests, no integration tests for new integrations | Only happy-path tests, mocked-out critical logic, no test for the fix |
| **Concurrency Issues** | Race conditions, deadlocks, missing locks, thread-unsafe shared state | Global mutable state, non-atomic read-modify-write, lock ordering violations |
| **Resource Management** | Unclosed connections, file handle leaks, missing timeouts, unbounded caches | `open()` without `close()`, HTTP client without timeout, cache without TTL or max size |
| **Code Style/Conventions** | Violations of project conventions, inconsistent naming, magic numbers | Check against project CLAUDE.md and rules |
| **Dependency Risks** | New dependencies with known vulnerabilities, abandoned packages, license issues | Outdated packages, packages with < 100 weekly downloads, GPL in MIT project |

---

