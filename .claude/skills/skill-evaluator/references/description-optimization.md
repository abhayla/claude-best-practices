# Description Optimization

How to test and improve a skill's description for trigger reliability.

## How Triggering Works

- Agent loads only name + description at startup — description carries the entire triggering burden
- Agents typically only consult skills for tasks requiring knowledge beyond their baseline capability
- Simple one-step requests may not trigger even with a perfect description match — this is expected

## Writing Effective Descriptions

- **Imperative phrasing:** "Use this skill when..." not "This skill does..."
- **User intent focus:** describe what the user is trying to achieve, not internal mechanics
- **Err on being pushy:** explicitly list contexts, including cases where user doesn't name the domain
- **Concise:** a few sentences to a short paragraph. Hard limit: 1024 characters
- **Third person ONLY:** The description is injected into the system prompt.
  Inconsistent point-of-view causes discovery problems.
  - Good: "Processes Excel files and generates reports"
  - Bad: "I can help you process Excel files"
  - Bad: "You can use this to process Excel files"

### Before/After

```yaml
# Before — too vague
description: Process CSV files.

# After — specific scope + broad activation
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

## Designing Eval Queries

Create 20 queries: 10 should-trigger + 10 should-not-trigger. Store in `eval_queries.json`:

```json
[
  {"query": "I've got a spreadsheet with revenue in col C — can you add a profit margin column?", "should_trigger": true},
  {"query": "whats the quickest way to convert this json file to yaml", "should_trigger": false}
]
```

### Should-Trigger (10)

Vary along four axes:
- **Phrasing:** formal, casual, typos, abbreviations
- **Explicitness:** names domain directly vs describes the need without naming it
- **Detail:** terse one-liners vs context-heavy with file paths and column names
- **Complexity:** single-step vs multi-step where the skill is buried in a larger chain

Most valuable: queries where the skill helps but the connection isn't obvious.

### Should-Not-Trigger (10)

Must be **near-misses** — share keywords/concepts but need something different.

```
BAD negative: "Write a fibonacci function" (tests nothing)
GOOD negative: "write a script to upload CSV rows to postgres"
  (involves CSV but task is ETL, not analysis)
```

### Realistic Context

Real prompts contain: file paths (`~/Downloads/report_v2.xlsx`), personal context ("my manager asked..."), specific details (column names, values), casual language and typos. Include these.

## Testing Trigger Reliability

- Run each query 3 times (model nondeterminism)
- Each run in clean context (subagent)
- Compute trigger rate: triggers / runs
- Should-trigger passes if trigger rate ≥80%
- Should-not-trigger passes if trigger rate ≤20%

## Train/Validation Split

Split queries 60/40 to avoid overfitting:
- **Train (60%):** use failures to guide description revisions
- **Validation (40%):** held-out, only used to check generalization
- Both sets must have proportional should/shouldn't mix
- Keep split fixed across iterations
- **Only use train set failures to guide revisions** — keep validation results out of the process entirely, or you defeat the purpose of the split

## Optimization Loop

1. **Evaluate** current description on both train + validation sets
2. **Identify failures** in train set only:
   - Should-trigger failing → description too narrow, broaden scope
   - Should-not-trigger failing → description too broad, add specificity about what the skill does NOT do, or clarify the boundary between this skill and adjacent capabilities
3. **Revise description:**
   - Generalize from the category, DON'T add specific keywords from failed queries (overfitting)
   - If stuck after 3 incremental tweaks → try structurally different framing
   - Check description stays under 1024 characters
4. **Repeat** (max 5 iterations)
5. **Select best** by VALIDATION pass rate — may not be the last iteration
6. **If not improving:** the issue may be with the queries (too easy, too hard, or mislabeled), not the description. Review and fix the eval set before iterating further.

## Fresh Validation

After selecting the best description:
1. Write 5-10 fresh queries never used during optimization
2. Mix of should-trigger and should-not-trigger
3. Run through eval — this is the honest generalization check
4. If fresh queries fail → description is overfit to the eval set, revisit
