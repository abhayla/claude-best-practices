# Iteration Algorithms

Detailed pseudocode for Full Loop and Single Fix iteration modes. Referenced from the main `fix-loop` SKILL.md.

---

## Algorithm — Full Loop Mode

```
INITIALIZE:
  If current_cascade_depth >= max_cascade_depth:
    Return immediately with status: MAX_CASCADE_EXCEEDED
    Log: "Cascade depth {current_cascade_depth} >= max {max_cascade_depth}. Stopping to prevent infinite cascading."

  Create {log_dir}/{session_id}/ directory
  Parse failure_output into discrete issues
  Sort issues by severity (crashes > assertion failures > warnings)
  total_iterations = 0
  cascade_depth = current_cascade_depth
  results = { issues_found: N, issues_resolved: 0, fixes: [], unresolved: [], cascadeDepth: cascade_depth }
  metrics = { debugger_invocations: 0, code_reviews: 0, approved: 0, flagged: 0, build_failures: 0, reverts: 0 }

FOR each issue (while total_iterations < max_iterations):
  FOR attempt = 1 to max_attempts_per_issue:
    total_iterations++
    if total_iterations > max_iterations: break with MAX_ITERATIONS_EXCEEDED

    STEP 1: READ PREVIOUS LOGS
      Read all iteration-*.md files from {log_dir}/{session_id}/
      Understand what was tried, what worked, what didn't

    STEP 2: ANALYZE ROOT CAUSE
      Determine thinking level:
        - If force_thinking_level is set: use it
        - Else auto-escalate: attempt 1 -> normal, 2-3 -> thinkhard, 4+ -> ultrathink

      normal: Analyze directly — read failure, trace to code, identify root cause
      thinkhard: Launch debugger Agent (read-only, via Task tool) with extended thinking instruction and all prior attempt logs
      ultrathink: Launch debugger Agent (read-only, via Task tool) with maximum depth instruction and complete history

      The debugger Agent returns a root cause analysis report.
      YOU (main Claude session) then apply fixes based on that analysis.

      OPTIONAL KNOWLEDGE PRE-CHECK (if .claude/knowledge.db exists):
        Run: python .claude/scripts/knowledge_db.py get-strategies --error "{error_signature}"
        If strategies with success_rate > 0.6 exist: try top strategy FIRST
        Record all attempts via: python .claude/scripts/knowledge_db.py record-attempt --error-id {id} --strategy-id {sid} --outcome {success|failure}

      Respect fix_target:
        - "production": only fix source/production code
        - "test": only fix test code
        - "either": fix whichever is actually wrong

    STEP 3: APPLY MINIMAL FIX
      Before applying, verify the fix does NOT involve any prohibited_actions
      Make the smallest change that addresses the root cause
      Record: { file, line, root_cause, change_description }

    STEP 4: CODE REVIEW GATE
      Launch code-reviewer Agent (read-only, via Task tool) with:
        - The git diff of changes
        - The failure context and root cause
        - Instruction: "Review for regressions, weakened assertions, prohibited patterns, security issues. Categorize findings as Critical/High/Medium/Low. Return APPROVED or FLAGGED."

      The code-reviewer Agent returns a review report.
      YOU (main Claude session) handle the result:
        - FLAGGED with Critical finding + revert_on_critical_review:
          -> Revert fix (git checkout -- <files>)
          -> Log the rejection reason
          -> Re-attempt with rejection context (same attempt counter)
          -> metrics.reverts++
        - FLAGGED with non-Critical findings:
          -> Log findings, proceed
          -> metrics.flagged++
        - APPROVED:
          -> Proceed
          -> metrics.approved++
      metrics.code_reviews++

    STEP 5: REBUILD (if build_command provided)
      Run build_command
      If build fails:
        build_retry_count++
        If build_retry_count >= max_build_retries:
          -> Revert fix, mark issue as FAILED_BUILD, break to next issue
          -> metrics.build_failures++, metrics.reverts++
        Else:
          -> Analyze build error, apply build fix, retry
      If build succeeds AND install_command provided:
        Run install_command

    STEP 6: RETEST (Full Loop only)
      Run retest_command with retest_timeout
      If exit code 0 -> issue RESOLVED -> break to next issue
      If non-zero -> analyze new failure output, continue to next attempt
      If timeout -> treat as failure

    STEP 7: LOG ITERATION + EVIDENCE ARTIFACT
      Write iteration-{NNN}.md to {log_dir}/{session_id}/ with:
        - Metadata (session, iteration, issue, attempt, thinking_level, timestamp)
        - Previous iterations summary
        - Failure analysis (raw output, root cause, file, line)
        - Fix applied (file, change, diff summary)
        - Code review result (verdict, findings)
        - Build result (status, attempts)
        - Retest result (PASSED / FAILED / PENDING_CALLER_RETEST)

      OPTIONAL ITERATION MEMORY (if structured_memory: true):
        Write/update {log_dir}/{session_id}/iteration-memory.json with:
        {
          "iterations": [
            {
              "number": NNN,
              "thinkingLevel": "normal|thinkhard|ultrathink",
              "hypothesis": "what we thought was wrong",
              "actionTaken": "what fix was applied",
              "filesChanged": ["file1.py", "file2.kt"],
              "outcome": "PASSED|FAILED|TIMEOUT",
              "kbStrategyUsed": null or { "id": N, "name": "...", "score": 0.7 }
            }
          ],
          "cumulativeUnderstanding": "1-3 sentence synthesis of all iterations so far"
        }

      MANDATORY evidence artifact (JSON):
        {log_dir}/{session_id}/evidence-{NNN}.json
        ```json
        {
          "iteration": NNN,
          "mode": "full_loop|single_fix",
          "issue": "{issue_description}",
          "fixApplied": { "file": "...", "line": N, "change": "..." },
          "rootCause": "...",
          "codeReviewVerdict": "APPROVED|FLAGGED",
          "buildResult": "PASSED|FAILED|SKIPPED",
          "retestResult": "PASSED|FAILED|TIMEOUT|PENDING_CALLER_RETEST",
          "timestamp": "ISO8601"
        }
        ```
  END attempt loop

  If issue not resolved after max_attempts_per_issue:
    Mark as UNRESOLVED, add to results.unresolved
END issue loop

Determine overall status:
  - All issues resolved -> RESOLVED
  - Some resolved, some not -> PARTIALLY_RESOLVED
  - None resolved -> UNRESOLVED
  - Budget exhausted with remaining issues -> MAX_ITERATIONS_EXCEEDED
  - Cascade depth exceeded at init -> MAX_CASCADE_EXCEEDED

FINALIZE:
  Write summary evidence artifact:
    {log_dir}/{session_id}/summary-evidence.json
    ```json
    {
      "overallStatus": "RESOLVED|PARTIALLY_RESOLVED|UNRESOLVED|MAX_ITERATIONS_EXCEEDED",
      "iterationsUsed": N,
      "issuesFound": N,
      "issuesResolved": N,
      "fixesApplied": [ { "file": "...", "line": N, "description": "..." } ],
      "unresolvedIssues": [ "..." ],
      "metrics": { ... },
      "timestamp": "ISO8601"
    }
    ```

  AUTO-FILE ISSUE (if auto_file_issue=true):
    If overall status is UNRESOLVED or MAX_ITERATIONS_EXCEEDED:
      For each unresolved issue:
        1. Duplicate check: `gh issue list --search "{issue description}" --state open --limit 5`
        2. If no duplicate:
           ```bash
           gh issue create \
             --title "Fix-loop: {brief issue description}" \
             --body "## Auto-Filed from Fix-Loop\n\n**Context:** {failure_context}\n**Iterations:** {N}/{max}\n**Unresolved:** {description}\n**Session:** {session_id}\n\n## Fix Attempts\n{summary of all attempts}\n\n---\n*Auto-filed by fix-loop (auto_file_issue=true)*" \
             --label "bug,fix-loop,unresolved,auto-filed"
           ```
        3. Record filed issue in summary-evidence.json under `autoFiledIssues`

  CLEAR FLAGS (if clear_flags is non-empty AND overallStatus is RESOLVED):
    For each flag in clear_flags:
      Set flag to false in workflow-state.json
      Clear associated details field:
        - visualIssuesPending -> also clear visualIssuePendingDetails = null
      Log: "Cleared flag {flag} after RESOLVED fix-loop"

RETURN structured results (see Output section in SKILL.md)
```

---

## Algorithm — Single Fix Mode

Runs exactly ONE iteration (Steps 1-5 + 7, no Step 6 retest).

Uses `attempt_number` and `previous_attempts_summary` from the caller to determine thinking level and build on prior context.

Returns the fix details for the caller to evaluate and retest externally.
