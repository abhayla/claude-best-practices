# Prompt Grading Rubric

Score prompts across 6-7 weighted dimensions before diagnosing weaknesses.
Only dimensions scoring below 7 are diagnosed — this prevents over-constraint.

Scale: **1-10** (1 = worst, 10 = best). The 6 base dimensions apply to every
prompt. Tone Consistency is a 7th dimension that activates only for
prose / creative / UX prompts.

## Score Formula

`Overall = Sum(weight_i x score_i)` — Range 1.0-10.0

## Dimension Definitions and Scoring Anchors

### 1. Intent Clarity (Weight: 0.25)

Can there be only one interpretation of what must be done?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | Multiple interpretations, no action verb | "Do something about the auth" |
| 3-4   | Vague intent, reader must guess what "done" looks like | "Improve the login flow" |
| 5-6   | Clear intent but minor ambiguity in scope | "Fix the login bug" (which bug?) |
| 7-8   | Specific action + object, minor gaps only | "Fix the 500 error on POST /login" |
| 9-10  | Single interpretation, explicit action + object + success criteria | "Fix the 500 error on POST /login when password is empty — should return 422 with validation message" |

### 2. Context Sufficiency (Weight: 0.20)

Does the prompt provide all background needed to act?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | Assumes knowledge not provided (files, decisions, domain) | "Update the handler like we discussed" |
| 3-4   | Key context missing, must infer from codebase | "Fix the auth bug" (which file? which auth system?) |
| 5-6   | Most context present, 1-2 gaps inferrable | "Fix the JWT validation in auth.py" (missing: which validation?) |
| 7-8   | Context sufficient for action, minor gaps fillable | "Fix the JWT expiry check in auth.py that returns 401 for valid tokens" |
| 9-10  | All context explicit — files named, prior state clear | "Fix auth.py:42 — the JWT expiry check uses `<` instead of `<=`, causing valid tokens expiring this second to return 401" |

### 3. Constraint Precision (Weight: 0.20)

Are limitations measurable and non-contradictory?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | No constraints, or vague ("be thorough", "high quality") | "Make the code better" |
| 3-4   | Aspirational constraints that cannot be verified | "Make it fast and clean" |
| 5-6   | Some measurable constraints, 1-2 vague | "Response under 200ms, make it clean" |
| 7-8   | Most constraints pass measurability test | "Response under 200ms, no N+1 queries, max 3 DB calls" |
| 9-10  | All constraints pass "Can a reviewer verify this?" test, no conflicts | "Response under 200ms p95, no N+1 queries, max 3 DB calls, zero breaking API changes" |

### 4. Output Specification (Weight: 0.15)

Is the expected result format defined?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | No format specified, output shape up to model | "Analyze this code" |
| 3-4   | Vague format hint ("give me a list") | "List the problems you find" |
| 5-6   | General format mentioned without structure | "Return JSON with the results" |
| 7-8   | Format specified with field names | "Return JSON with fields: file, line, severity, message" |
| 9-10  | Locked template with sections, types, length bounds | "Return JSON: {file: string, line: int, severity: 'high'\|'medium'\|'low', message: string max 100 chars}" |

### 5. Role & Framing (Weight: 0.10)

Is there a persona or domain frame that shapes the response?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | No role, generic request | "Review this code" |
| 3-4   | Implied role from task context | "Review this PR" (implies reviewer) |
| 5-6   | General role stated | "As a code reviewer, review this" |
| 7-8   | Specific role with expertise area | "As a security-focused code reviewer, review this auth module" |
| 9-10  | Explicit role with expertise, perspective, and failure modes | "As a security auditor focused on OWASP Top 10, review this auth module — flag injection, broken auth, and data exposure" |

**Policy: never skip MISSING_ROLE.** When Role scores below 7, always add an
explicit role frame appropriate to the task class — see SKILL.md "Role
Selection Guide" for the task-class → role mapping. This replaces the
prior 1-5 era carve-out that allowed scores of 3-4 to pass for code
tasks; on the 1-10 scale, anything below 7 leaves measurable lift on the
table, regardless of domain. The implicit "AI assistant" role is the
weakest possible default — every prompt benefits from a sharper frame.

### 6. Example Grounding (Weight: 0.10)

Are input/output examples provided for complex tasks?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | No examples for a complex task | "Parse the logs and extract errors" (no format shown) |
| 3-4   | Referenced but not shown | "Format like the other endpoints" |
| 5-6   | One partial example | "e.g., ERROR: connection timeout" |
| 7-8   | 1-2 complete input/output examples | "Input: 'ERROR: timeout at 14:30' -> Output: {level: 'ERROR', msg: 'timeout', time: '14:30'}" |
| 9-10  | 3+ diverse examples covering edge cases | Multiple examples including happy path, error case, and edge case |

Note: Simple, unambiguous tasks (rename, delete, run tests) do not need
examples. Scoring 5-6 on this dimension (the 1-10 equivalent of the prior
1-5 era's "1-2 acceptable") is fine when the task is self-explanatory.
Examples remain Low severity — only fixed if budget remains after
Critical/High/Medium fills the 5-cap.

### 7. Tone Consistency (Conditional Weight)

**Active only when** the prompt targets prose, creative writing, marketing copy,
UX/UI text, or any output where voice and register matter to the user.
Detection signals: words like "write", "draft", "compose", "rewrite", "tone",
"voice", "audience", "copy"; output formats like email, blog post, tweet,
landing page, error message text.

How clearly is the expected voice, register, and persona maintained?

| Score | Anchor | Example |
|-------|--------|---------|
| 1-2   | No tone guidance — output voice is unpredictable | "Write something about our product" |
| 3-4   | Mixed signals (formal instructions but casual examples) | "Write a professional email — make it fun and casual" |
| 5-6   | Tone implied but not stated; could shift between invocations | "Write an onboarding email" |
| 7-8   | Tone is clear from context with minor inconsistency | "Write a friendly onboarding email — warm but professional" |
| 9-10  | Explicit persona with voice attributes (formal/casual, technical depth, audience) | "Write an onboarding email for first-time non-technical users — warm, second-person, no jargon, max 120 words, two short paragraphs + CTA" |

#### Weight Redistribution When Tone Is Active

When Tone applies, weights re-normalize so the sum stays 1.0:

| Dimension | Default Weight | With Tone Active |
|-----------|---------------|------------------|
| Intent Clarity | 0.25 | 0.25 |
| Context Sufficiency | 0.20 | 0.20 |
| Constraint Precision | 0.20 | 0.20 |
| Output Specification | 0.15 | 0.15 |
| Role & Framing | 0.10 | 0.05 |
| Example Grounding | 0.10 | 0.05 |
| Tone Consistency | 0.00 | 0.10 |
| **Sum** | **1.00** | **1.00** |

Role and Examples each give up 0.05 because their failure modes overlap
with Tone for prose tasks (a strong tone spec usually implies role +
examples).

## Grade Thresholds

| Grade | Score (1-10) | Action |
|-------|-------------|--------|
| **A** | 8.0-10.0 | Skip strengthening, execute as-is |
| **B** | 6.0-7.9 | Strengthen ONLY dimensions scoring below 7 |
| **C** | 4.0-5.9 | Full strengthening (all weak dimensions) |
| **D** | 3.0-3.9 | Full strengthening with heavy warning |
| **F** | 1.0-2.9 | Suggested rewrite with intent-drift caveats |

## Floor Rules (with explicit precedence)

Apply in order — first match wins:

1. If **Intent Clarity** or **Context Sufficiency** scores 1-2 → **Grade F** (overrides everything)
2. If more than 5 Critical issues are diagnosed → **Grade F**
3. If any other single dimension scores 1-2 → cap at **Grade B (max 7.9)**
4. Otherwise → use the threshold table above

This precedence resolves the prior conflict where "any 1 caps at B" and
"Intent/Context 1 forces F" could fire simultaneously without a winner.

## Verbose Mode (entry point: "score" / "evaluate" / "audit")

When the user explicitly asks to score, evaluate, or audit a prompt
(rather than triggering automatic strengthening), run the same rubric in
**verbose mode** — same dimensions, same weights, same thresholds, plus:

1. **Quote-as-evidence requirement**: every dimension score MUST cite a
   specific phrase from the user's prompt that justifies it. No quote → no score.
2. **Use case input**: ask the user to describe the use case before scoring.
   The same prompt scores differently for a CLI tool vs. a customer chatbot.
3. **Launch-risk flagging**: dimensions scoring below 7 are labeled "launch
   risks" with: the offending quote, the failure mode it will cause in
   production, and the concrete fix that would raise the score to 7+.
4. **No auto-strengthening**: verbose mode produces a report only. If the
   user asks to fix afterwards, feed the launch risks into Steps 1-5 of
   the strengthening pipeline.

This replaces the retired separate reliability-scoring flow.

## Dimension -> Category Mapping

| Dimension | Maps to Diagnosis Categories | When Dimension < 5 |
|-----------|------------------------------|-------------------|
| Intent Clarity | VAGUE_INTENT, AMBIGUOUS_SCOPE | Mandatory diagnosis |
| Context Sufficiency | MISSING_CONTEXT, IMPLICIT_ASSUMPTIONS | Mandatory diagnosis |
| Constraint Precision | UNDER_CONSTRAINED, CONFLICTING_CONSTRAINTS, OVER_SCOPED | Mandatory diagnosis |
| Output Specification | MISSING_OUTPUT_SPEC, MISSING_STRUCTURE | Mandatory diagnosis |
| Role & Framing | MISSING_ROLE | Mandatory diagnosis |
| Example Grounding | MISSING_EXAMPLES | Mandatory diagnosis |
| Tone Consistency | MISSING_TONE_FRAME | Mandatory diagnosis (when Tone is active) |
