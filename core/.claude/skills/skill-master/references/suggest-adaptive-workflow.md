# STEP 5: Suggest Adaptive Workflow

### 5.1 Classify Task Type

Read the user's description and classify the task:

| Task Signal | Detected Type | Notes |
|-------------|--------------|-------|
| "bug", "error", "failing", "broken", "crash" | Bug Fix | Start with diagnosis |
| "new feature", "add", "build", "create" (large scope) | New Feature | Full planning pipeline |
| "quick fix", "small change", "tweak", "typo" | Quick Fix | Minimal pipeline |
| "review", "PR", "pull request", "feedback" | Code Review | Review pipeline |
| "security", "vulnerability", "CVE", "audit" | Security | Audit pipeline |
| "deploy", "ship", "release", "publish" | Deployment | Deploy pipeline |
| "refactor", "clean up", "restructure" | Refactoring | Analysis + implementation |
| "test", "coverage", "failing tests" | Testing | Test-focused pipeline |
| Stack-specific technology mentioned | Stack Task | Route to stack skill |

### 5.2 Build Workflow from Discovered Skills

For the detected task type, scan the catalog built in Step 1 and assemble a workflow.

**Algorithm:**
1. Identify the "entry" skill — the one whose description best matches the starting action for this task type
2. Read that skill's full content and look for handoff suggestions (references to other skills like "proceed with `/implement`" or "next step: `/branching`")
3. Follow the handoff chain, reading each referenced skill to find the next link
4. If the chain breaks (a skill has no handoff), fill gaps by matching category to task phase:
   - Analysis phase: look for Quality/Architecture category skills
   - Implementation phase: look for Workflow category skills
   - Verification phase: look for Quality category skills
   - Delivery phase: look for Collaboration category skills

### 5.3 Define Entry/Exit Criteria

For each step in the workflow, define what must be true before starting (entry) and what the step must produce (exit). This prevents skipping phases or moving forward prematurely.

| Phase | Entry Criteria | Exit Criteria |
|-------|---------------|---------------|
| Research/Brainstorm | Clear problem statement from user | Research brief + spec document with chosen approach |
| Planning | Approved spec/approach | Plan with tasks, verification commands, dependency graph |
| Execution | Approved plan saved to file | All tasks completed, tests passing, code committed |
| Standards check | Implementation complete, tests green | Standards report with 0 critical violations |
| Code review | Standards check passed | PR created with risk analysis and review questions |
| Review feedback | Review comments received | All must-fix addressed, re-review requested |
| Finish | PR approved, CI green | Merged, verified, branch cleaned up |

When presenting a workflow, include entry/exit criteria so the user knows what each phase requires and produces.

**Present the workflow:**

```
SUGGESTED WORKFLOW for: "{user's task description}"
Task type: New Feature

  Step 1: /brainstorm — Explore approaches and write a spec
    Entry: clear problem statement | Exit: spec document with chosen approach
  Step 2: /writing-plans — Break the spec into a task plan
    Entry: approved spec | Exit: plan with tasks + verification commands
  Step 3: /executing-plans — Execute each task in the plan
    Entry: approved plan | Exit: all tasks done, tests passing
  Step 4: /pr-standards — Check against team standards
    Entry: implementation complete | Exit: 0 critical violations
  Step 5: /request-code-review — Get review feedback
    Entry: standards passed | Exit: PR created with risk analysis
  Step 6: /receive-code-review — Apply review feedback
    Entry: review comments | Exit: all must-fix addressed
  Step 7: /branching finish — Merge and cleanup
    Entry: PR approved, CI green | Exit: merged, verified, cleaned up

  Estimated steps: 7
  Note: Steps were derived from skill handoff hints in descriptions.
        This workflow updates automatically when skills change.

  Start this workflow? (Y/n/modify)
```

### 5.3 Allow Workflow Modification

If the user says "modify" or suggests changes:

1. Show the full catalog filtered to relevant categories
2. Let the user add, remove, or reorder skills
3. Validate the modified workflow: check that each skill exists in the catalog
4. Confirm the final workflow before starting

---

