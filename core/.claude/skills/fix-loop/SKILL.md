---
name: fix-loop
description: >
  Iterative fix cycle: analyze failures, apply minimal fixes, run code review gates,
  optionally retest. Full Loop mode (with retest command) iterates until resolved.
  Single Fix mode (no retest) does one pass. Thinking escalation (normal to ultrathink),
  debugger/code-reviewer agent delegation. Use when tests fail, build breaks, or runtime errors.
allowed-tools: "Bash Read Grep Glob Write Edit Task"
argument-hint: "[failure_output] [retest_command] [max_iterations]"
---

# Fix Loop

Iterative fix cycle that analyzes failures, applies minimal fixes, runs code review gates, and optionally retests. Supports two modes — Full Loop (with retest) and Single Fix (one pass). Uses thinking escalation, debugger delegation, and structured iteration logging. Fully project-agnostic.

**Arguments:** $ARGUMENTS

Read and follow this process using the parameters passed by the caller (via `$ARGUMENTS` or inline in the calling command).

**MANDATORY — NO EXCEPTIONS.** This process runs for ALL issues including known, pre-existing, or seemingly architectural ones. The budget limits (`max_iterations`, `max_attempts_per_issue`) are the ONLY valid exit conditions. Do NOT skip iterations or short-circuit based on your own judgment about issue complexity or familiarity.

---

## Execution Modes

You operate in one of two modes based on the presence of `retest_command`:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Full Loop** | `retest_command` is provided | Run full analyze -> fix -> review -> build -> retest cycle, iterating until resolved or budget exhausted |
| **Single Fix** | `retest_command` is absent | Run ONE analyze -> fix -> review -> build pass, then return results for the caller to retest externally |

---

## Input Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `failure_output` | string | Raw failure output (test errors, stack traces, assertion messages) |
| `failure_context` | string | What was tested and what was expected to happen |
| `files_of_interest` | string[] | File paths to read for understanding the code under test |

### Optional Parameters (with defaults)

| Parameter | Type | Default | Valid Values | Description |
|-----------|------|---------|-------------|-------------|
| `build_command` | string | null | Any shell command | Rebuild command after fix (null = skip rebuild) |
| `install_command` | string | null | Any shell command | Deploy/install command after build (e.g., install APK) |
| `retest_command` | string | null | Any shell command | **Present = Full Loop mode, absent = Single Fix mode** |
| `retest_timeout` | int | 300 | 60-600 | Retest timeout in seconds |
| `max_iterations` | int | 10 | 1-20 | Maximum total fix-build-test cycles |
| `max_attempts_per_issue` | int | 3 | 1-5 | Maximum attempts per discrete issue |
| `max_build_retries` | int | 3 | 1-5 | Build failures before reverting |
| `force_thinking_level` | string | null | `"normal"`, `"thinkhard"`, `"ultrathink"` | Override auto-escalation |
| `debugger_agent_name` | string | `"debugger"` | Any Agent name | Agent for deep root cause analysis (launched via Task tool) |
| `code_reviewer_agent_name` | string | `"code-reviewer"` | Any Agent name | Agent for quality gate reviews (launched via Task tool) |
| `prohibited_actions` | string[] | `[]` | Any action description | Actions you must NEVER take |
| `fix_target` | string | `"production"` | `"production"`, `"test"`, `"either"` | What to fix |
| `revert_on_critical_review` | bool | `true` | true/false | Revert on Critical code review findings |
| `log_dir` | string | `".claude/logs/fix-loop/"` | Any path | Directory for iteration log files |
| `session_id` | string | auto-generated | Any string | Session identifier for log subdirectory |
| `max_cascade_depth` | int | `2` | 1-5 | Maximum depth of cascading fix-loops |
| `current_cascade_depth` | int | `0` | 0+ | Current cascade depth |
| `auto_file_issue` | bool | `false` | true/false | When true AND outcome is UNRESOLVED, auto-create GitHub issue |
| `clear_flags` | string[] | `[]` | `["visualIssuesPending"]` | Workflow state flags to clear on RESOLVED |
| `structured_memory` | bool | `false` | true/false | Write iteration-memory.json alongside markdown logs |
| `thinking_granularity` | string | `"coarse"` | `"coarse"`, `"fine"` | `"coarse"` = existing 3-level. `"fine"` = 8-level (see below) |

### Failure Index Context (for auto-delegated invocations)

When invoked by auto-delegation, these additional parameters provide context from the failure index:

| Parameter | Type | Description |
|-----------|------|-------------|
| `failure_index_context` | object | Prior failure summaries: `{occurrences: N, prior_outcomes: [...], known_workaround: "...", target_files: [...]}` |

When `failure_index_context` is provided:
- Skip approaches already documented as failed in prior occurrences
- Start with the `known_workaround` if one exists
- Focus on `target_files` from fix-patterns.md
- Use the occurrence count to auto-set thinking level (2-3 -> thinkhard, 4+ -> ultrathink) unless `force_thinking_level` overrides

### Single Fix Mode Extras

These are used when `retest_command` is absent (caller retests externally):

| Parameter | Type | Description |
|-----------|------|-------------|
| `attempt_number` | int | Current attempt number for this issue (used for thinking escalation) |
| `previous_attempts_summary` | string | Summary of what was tried in prior attempts and why it failed |

---

For the detailed iteration algorithms (Full Loop and Single Fix mode pseudocode), see `references/iteration-algorithm.md`.

---

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| No `build_command` | Skip Step 5 rebuild entirely |
| Build fails `max_build_retries` times | Revert fix, mark FAILED_BUILD, move to next issue |
| Code reviewer returns Critical | Revert fix, re-attempt with rejection context |
| `max_iterations` exceeded | Stop all processing, return MAX_ITERATIONS_EXCEEDED |
| Fix creates a NEW issue | Add the new issue to the issue queue (increment cascade_depth if re-invoking) |
| Cascade depth exceeded | Return MAX_CASCADE_EXCEEDED immediately, do not process any issues |
| Retest times out | Treat as failure, proceed to next attempt |
| No `files_of_interest` | Infer relevant files via Grep/Glob on error messages |
| Debugger Agent returns nothing actionable | Fall back to direct analysis |
| All `prohibited_actions` violated by only fix | Mark issue UNRESOLVED, log reason |

---

## Output — Full Loop Mode

Return a structured report:

```markdown
## Fix Loop Results

### Status
- **Overall:** RESOLVED | PARTIALLY_RESOLVED | UNRESOLVED | MAX_ITERATIONS_EXCEEDED | MAX_CASCADE_EXCEEDED
- **Iterations used:** N / max_iterations
- **Cascade depth:** N / max_cascade_depth
- **Issues found:** N
- **Issues resolved:** N
- **Issues unresolved:** N

### Fixes Applied
1. [{file}:{line}] — Root cause: {description} -> Fix: {change}
2. [{file}:{line}] — Root cause: {description} -> Fix: {change}

### Unresolved Issues
1. {issue description} — Attempts: N, Last error: {message}
(Omit section if all resolved)

### Tracking Metrics
- Debugger invocations: N
- Code reviews: N (approved: N, flagged: N)
- Build failures: N
- Reverts: N

### Files Changed
- {file_path_1}
- {file_path_2}

### Flags Cleared
- {flag_name}: cleared (or "No flags to clear")

### Iteration Log Directory
{log_dir}/{session_id}/
```

---

## Output — Single Fix Mode

Return a structured report:

```markdown
## Single Fix Result

### Status
- **Fix applied:** true | false
- **Review verdict:** APPROVED | FLAGGED (details)
- **Build status:** PASSED | FAILED | SKIPPED (no build_command)
- **Revert applied:** true | false

### Fix Details
- **File:** {path}
- **Line:** {line}
- **Root cause:** {description}
- **Change:** {description}
- **Thinking level:** normal | thinkhard | ultrathink

### Code Review
- **Verdict:** {verdict}
- **Findings:** {list or "none"}

### Metrics
- Debugger invocations: N
- Code reviews: 1
- Build retries: N

### Iteration Log
{log_dir}/{session_id}/iteration-{NNN}.md
```

---

## Prohibited Actions Enforcement

Before applying ANY fix, verify it does not involve any action in the `prohibited_actions` list. Common prohibited actions include:
- Adding `@Ignore` or `@Disabled` annotations to tests
- Weakening assertions (e.g., changing `assertEquals` to `assertTrue`, removing assertions)
- Deleting or commenting out test methods
- Adding `Thread.sleep()` as a timing fix
- Creating "fix later" issues to bypass failures
- Skipping test groups or suites
- Classifying a screen/step as PASS when any issue was detected
- Downgrading issues to "observations", "findings", or "notes" to avoid fix-loop
- Skipping visual verification without setting visual_verified=false
- Bypassing the Pre-Classification Gate (E5.7)

If the ONLY viable fix would violate a prohibited action, mark the issue as UNRESOLVED with the reason "Only available fix violates prohibited action: {action}".

---

## Thinking Escalation (Canonical — ALL callers use this)

This is the **single source of truth** for thinking escalation. Callers (adb-test, run-e2e, implement, fix-issue) reference this table — they do NOT define their own escalation rules.

| Level | When | Approach |
|-------|------|----------|
| **normal** | Attempt 1 (or `force_thinking_level: "normal"`) | Analyze directly — read failure output, trace to source code, identify root cause |
| **thinkhard** | Attempt 2-3 (or `force_thinking_level: "thinkhard"`) | Launch debugger Agent (read-only, via Task tool) with extended thinking, all prior attempt logs, and systematic root cause enumeration |
| **ultrathink** | Attempt 4+ (or `force_thinking_level: "ultrathink"`) | Launch debugger Agent (read-only, via Task tool) with maximum thinking depth, complete history, re-examine all assumptions, explore unconventional fixes |

**Override:** The `force_thinking_level` parameter skips the attempt-based auto-escalation table above.

### Fine-Grained Thinking (when `thinking_granularity: "fine"`)

When `thinking_granularity` is set to `"fine"`, the 3-level escalation is expanded to 8 sub-levels:

| Attempt | Level | Sub-Strategy |
|---------|-------|-------------|
| 1 | normal | Direct: read error, trace to source, fix |
| 2 | normal+ | Broader scan: related files, recent git history |
| 3 | thinkhard | Debugger agent: focused failure analysis |
| 4 | thinkhard+ | Debugger agent: elimination matrix (ALL causes, eliminate each) |
| 5 | thinkhard++ | Debugger agent + knowledge.db: check historical strategies |
| 6 | ultrathink | Debugger agent: max depth, challenge all assumptions |
| 7 | ultrathink+ | Debugger + code-reviewer: independent parallel analysis |
| 8+ | ultrathink++ | Reframe: "is the bug in the TEST, not the code?" |

At attempt 5 (thinkhard++), if `.claude/knowledge.db` exists, query it:
```bash
python .claude/scripts/knowledge_db.py get-strategies --error "{error_signature}"
```
Use top strategy (score >= 0.6) before standard diagnosis.

When launching the debugger Agent (via Task tool), always include:
- Complete failure output
- All files of interest
- Summary of all previous fix attempts and why they failed
- The specific thinking level instruction

The debugger Agent returns analysis only — YOU (the main Claude session) apply the fixes directly.

---

## Iteration Log Format

Each iteration is written to disk at `{log_dir}/{session_id}/iteration-{NNN}.md`:

```markdown
# Iteration {NNN}

## Metadata
- Session: {session_id}
- Iteration: {NNN} / {max_iterations}
- Issue: {issue_description}
- Attempt: {M} / {max_attempts_per_issue}
- Thinking level: {normal | thinkhard | ultrathink}
- Mode: {full_loop | single_fix}
- Timestamp: {ISO 8601}

## Previous Iterations Summary
{2-3 line summary of each prior iteration}

## Failure Analysis
- Raw failure: {truncated failure output}
- Root cause: {description}
- File: {path}
- Line: {line_number}

## Fix Applied
- File: {path}
- Change: {description}
- Diff summary: {brief diff}

## Code Review
- Verdict: {APPROVED | FLAGGED}
- Findings: {list or "none"}

## Build Result
- Status: {PASSED | FAILED | SKIPPED}
- Attempts: {N}

## Retest Result
- Status: {PASSED | FAILED | TIMEOUT | PENDING_CALLER_RETEST}
```
