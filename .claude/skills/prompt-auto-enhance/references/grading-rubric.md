# Prompt Grading Rubric

Score prompts across 6 weighted dimensions before diagnosing weaknesses.
Only dimensions scoring below 4 are diagnosed — this prevents over-constraint.

## Score Formula

`Overall = Sum(weight_i x score_i)` — Range 1.0-5.0

## Dimension Definitions and Scoring Anchors

### 1. Intent Clarity (Weight: 0.25)

Can there be only one interpretation of what must be done?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | Multiple interpretations, no action verb | "Do something about the auth" |
| 2 | Vague intent, reader must guess what "done" looks like | "Improve the login flow" |
| 3 | Clear intent but minor ambiguity in scope | "Fix the login bug" (which bug?) |
| 4 | Specific action + object, minor gaps only | "Fix the 500 error on POST /login" |
| 5 | Single interpretation, explicit action + object + success criteria | "Fix the 500 error on POST /login when password is empty — should return 422 with validation message" |

### 2. Context Sufficiency (Weight: 0.20)

Does the prompt provide all background needed to act?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | Assumes knowledge not provided (files, decisions, domain) | "Update the handler like we discussed" |
| 2 | Key context missing, must infer from codebase | "Fix the auth bug" (which file? which auth system?) |
| 3 | Most context present, 1-2 gaps inferrable | "Fix the JWT validation in auth.py" (missing: which validation?) |
| 4 | Context sufficient for action, minor gaps fillable | "Fix the JWT expiry check in auth.py that returns 401 for valid tokens" |
| 5 | All context explicit — files named, prior state clear | "Fix auth.py:42 — the JWT expiry check uses `<` instead of `<=`, causing valid tokens expiring this second to return 401" |

### 3. Constraint Precision (Weight: 0.20)

Are limitations measurable and non-contradictory?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | No constraints, or vague ("be thorough", "high quality") | "Make the code better" |
| 2 | Aspirational constraints that cannot be verified | "Make it fast and clean" |
| 3 | Some measurable constraints, 1-2 vague | "Response under 200ms, make it clean" |
| 4 | Most constraints pass measurability test | "Response under 200ms, no N+1 queries, max 3 DB calls" |
| 5 | All constraints pass "Can a reviewer verify this?" test, no conflicts | "Response under 200ms p95, no N+1 queries, max 3 DB calls, zero breaking API changes" |

### 4. Output Specification (Weight: 0.15)

Is the expected result format defined?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | No format specified, output shape up to model | "Analyze this code" |
| 2 | Vague format hint ("give me a list") | "List the problems you find" |
| 3 | General format mentioned without structure | "Return JSON with the results" |
| 4 | Format specified with field names | "Return JSON with fields: file, line, severity, message" |
| 5 | Locked template with sections, types, length bounds | "Return JSON: {file: string, line: int, severity: 'high'|'medium'|'low', message: string max 100 chars}" |

### 5. Role & Framing (Weight: 0.10)

Is there a persona or domain frame that shapes the response?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | No role, generic request | "Review this code" |
| 2 | Implied role from task context | "Review this PR" (implies reviewer) |
| 3 | General role stated | "As a code reviewer, review this" |
| 4 | Specific role with expertise area | "As a security-focused code reviewer, review this auth module" |
| 5 | Explicit role with expertise, perspective, and failure modes | "As a security auditor focused on OWASP Top 10, review this auth module — flag injection, broken auth, and data exposure" |

Note: For coding prompts where Claude already has an implicit developer role,
scores of 1-2 are acceptable and do not warrant strengthening unless the task
requires specialized domain expertise.

### 6. Example Grounding (Weight: 0.10)

Are input/output examples provided for complex tasks?

| Score | Anchor | Example |
|-------|--------|---------|
| 1 | No examples for a complex task | "Parse the logs and extract errors" (no format shown) |
| 2 | Referenced but not shown | "Format like the other endpoints" |
| 3 | One partial example | "e.g., ERROR: connection timeout" |
| 4 | 1-2 complete input/output examples | "Input: 'ERROR: timeout at 14:30' -> Output: {level: 'ERROR', msg: 'timeout', time: '14:30'}" |
| 5 | 3+ diverse examples covering edge cases | Multiple examples including happy path, error case, and edge case |

Note: Simple, unambiguous tasks (rename, delete, run tests) do not need
examples. Score 1 on this dimension is acceptable when the task is
self-explanatory.

## Grade Thresholds

| Grade | Score | Action |
|-------|-------|--------|
| **A** | 4.0-5.0 | Skip strengthening, execute as-is |
| **B** | 3.0-3.9 | Strengthen ONLY dimensions scoring < 4 |
| **C** | 2.0-2.9 | Full strengthening (all weak dimensions) |
| **D** | 1.5-1.9 | Full strengthening with heavy warning |
| **F** | 1.0-1.4 | Suggested rewrite with intent-drift caveats |

## Floor Rule

Regardless of overall score:
- If **any** dimension scores 1: grade capped at B (3.9 max)
- If **Intent Clarity** or **Context Sufficiency** scores 1: auto-escalate to Grade F
- If more than 5 Critical issues diagnosed: auto-escalate to Grade F

## Dimension -> Category Mapping

| Dimension | Maps to Diagnosis Categories | When Dimension < 3 |
|-----------|------------------------------|-------------------|
| Intent Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE | Mandatory diagnosis |
| Context Sufficiency | MISSING_CONTEXT, IMPLICIT_ASSUMPTIONS | Mandatory diagnosis |
| Constraint Precision | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS, OVER_SCOPED | Mandatory diagnosis |
| Output Specification | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE | Mandatory diagnosis |
| Role & Framing | MISSING_ROLE | Mandatory diagnosis |
| Example Grounding | MISSING_EXAMPLES | Mandatory diagnosis |
