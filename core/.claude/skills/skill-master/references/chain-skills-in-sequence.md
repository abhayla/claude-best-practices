# STEP 6: Chain Skills in Sequence

### 6.1 Parse the Chain

Accept chain input in these formats:

| Format | Example |
|--------|---------|
| Comma-separated names | `brainstorm,writing-plans,executing-plans` |
| Slash-command list | `/brainstorm /writing-plans /executing-plans` |
| Workflow from Step 5 | User confirmed a suggested workflow |

Validate every skill name against the catalog from Step 1. If any skill is not found:

```
ERROR: Skill "{name}" not found in catalog.
Available skills: {list of all discovered skill names}
Did you mean: {closest name match}?
```

### 6.2 Initialize Progress Tracker

Create a progress display:

```
WORKFLOW PROGRESS: {workflow-name or "Custom Chain"}
  [x] /brainstorm — completed (output: spec written to docs/specs/feature-spec.md)
  [ ] /writing-plans — in progress
  [ ] /executing-plans — pending
  [ ] /request-code-review — pending
  [ ] /branching — pending

  Current: Step 2 of 5
```

### 6.3 Execute Each Skill

For each skill in the chain:

1. **Pre-check** — Read the skill's frontmatter to verify prerequisites
2. **Invoke** — Call `Skill("<name>", args="<context from previous skill>")`:
   - For the first skill: pass the user's original request as args
   - For subsequent skills: pass a summary of the previous skill's output as args
3. **Capture output** — Record what the skill produced (files created, decisions made, artifacts)
4. **Update progress** — Mark the skill as completed in the tracker
5. **Checkpoint** — Between skills, ask the user:
   ```
   /brainstorm completed. Output: spec written to docs/specs/feature-spec.md
   Next: /writing-plans — Break spec into task plan
   Continue? (Y/skip/stop)
   ```

| User Response | Action |
|---------------|--------|
| Y / yes / enter | Proceed to next skill |
| skip | Skip this skill, move to the next one |
| stop | Halt the chain, preserve progress state |
| modify | Show remaining skills, allow reordering |

### 6.4 Handle Chain Failures

If a skill fails or produces an error during chaining:

| Failure Type | Action |
|-------------|--------|
| Skill not found at runtime | Re-scan filesystem (skill may have been deleted), report if still missing |
| Skill errors during execution | Capture error, ask user: retry / skip / stop |
| User cancels mid-chain | Save progress state, offer to resume later |
| Context too large | Summarize previous outputs, trim to essential context |

### 6.5 Chain Completion Report

After all skills in the chain complete (or the chain is stopped):

```
WORKFLOW COMPLETE
  Skills executed: 5/6
  Skills skipped: 1 (request-code-review — skipped by user)

  Artifacts produced:
    - docs/specs/feature-spec.md (from /brainstorm)
    - docs/plans/feature-plan.md (from /writing-plans)
    - 3 files modified (from /executing-plans)
    - Branch ready for PR (from /branching)

  Suggested follow-up:
    - /request-code-review (was skipped — run when ready)
    - /learn-n-improve session (capture learnings)
```

---

