# Eval-Driven Iteration

How to test skill output quality using structured evaluations, assertions, and systematic iteration.

## Test Case Design

A test case has three parts:
- **Prompt:** a realistic user message (varied phrasing, detail, formality)
- **Expected output:** human-readable description of what success looks like
- **Input files** (optional): files the skill needs to work with

Store in `evals/evals.json` inside the skill directory. Start with 2-3 test cases — expand after first results.

**Tips:** Include at least one edge case (malformed input, unusual request, ambiguous instruction). Use realistic context — real users mention file paths (`data/sales_2025.csv`), column names, personal context ("my manager asked me to..."). Prompts like "process this data" are too vague to test anything.

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "realistic user message here",
      "expected_output": "description of success",
      "files": ["evals/files/input.csv"],
      "assertions": [
        "output includes a summary table",
        "all columns are labeled"
      ]
    }
  ]
}
```

## Workspace Structure

```
skill-name-workspace/
└── iteration-1/
    ├── eval-<name>/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── timing.json    # {total_tokens, duration_ms}
    │   │   └── grading.json   # {assertion_results, summary}
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json          # aggregated stats
```

**You author** `evals/evals.json` by hand. The other files (`grading.json`, `timing.json`, `benchmark.json`) are produced during the eval process — by the agent, scripts, or you.

## Running Evals

- Each run MUST start with clean context (subagent isolation)
- No leftover state from previous runs or skill development
- For each test case: run with-skill AND without-skill (or old version for `--baseline`)
- Capture timing: `{"total_tokens": N, "duration_ms": N}`

## Assertions

Write assertions AFTER the first run — you often don't know what "good" looks like until the skill has run.

**Good assertions:** specific, verifiable
- "The output file is valid JSON"
- "The chart has labeled axes"
- "The report includes at least 3 recommendations"

**Weak assertions:** vague or brittle
- "The output is good" (too vague to grade)
- "Uses exactly the phrase 'Total Revenue: $X'" (too brittle)

Not everything needs an assertion — style and "feel" are caught in human review.

## Grading

Grade each assertion PASS or FAIL with **specific evidence** (quote the output, reference file paths).

For assertions checkable by code (valid JSON, correct row count, file exists), use a verification script — scripts are more reliable than LLM judgment for mechanical checks and reusable across iterations. Use LLM grading for subjective assertions.

```json
{
  "assertion_results": [
    {"text": "The output includes a chart image file", "passed": true, "evidence": "Found chart.png (45KB) in outputs/"},
    {"text": "Both axes are labeled", "passed": false, "evidence": "Y-axis labeled 'Revenue ($)' but X-axis has no label"}
  ],
  "summary": {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5}
}
```

**Grading principles:**
- **Require concrete evidence for PASS** — don't give benefit of the doubt. If an assertion says "includes a summary" and the output has a "Summary" section with one vague sentence, that's a FAIL — the label is there but substance isn't.
- **Review assertions themselves** during grading:
  - Always pass in both configs? → too easy, remove or tighten
  - Always fail in both? → broken assertion or impossible task, fix it
  - Unverifiable from output alone? → replace with something checkable

## Blind Comparison (for version upgrades)

When comparing old vs new skill versions:
- Present both outputs to a judge without revealing which is which
- Judge scores holistic qualities: organization, formatting, usability, polish
- Complements assertion grading — two outputs can pass all assertions but differ significantly in overall quality

## Aggregating Benchmarks

Compute summary stats per configuration and save to `benchmark.json`:

```json
{
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.83, "stddev": 0.06},
      "time_seconds": {"mean": 45.0, "stddev": 12.0},
      "tokens": {"mean": 3800, "stddev": 400}
    },
    "without_skill": {
      "pass_rate": {"mean": 0.33, "stddev": 0.10},
      "time_seconds": {"mean": 32.0, "stddev": 8.0},
      "tokens": {"mean": 2100, "stddev": 300}
    },
    "delta": {"pass_rate": 0.50, "time_seconds": 13.0, "tokens": 1700}
  }
}
```

The **delta** tells you what the skill costs (more time, more tokens) and what it buys (higher pass rate). A skill that adds 13 seconds but improves pass rate by 50 points is worth it. A skill that doubles tokens for a 2-point gain may not be.

**Note:** `stddev` is only meaningful with multiple runs per eval. In early iterations with 2-3 test cases and single runs, focus on raw pass counts and delta.

## Pattern Analysis

After computing benchmarks:
- **Remove assertions that always pass in both configs** — inflating pass rate without measuring skill value
- **Investigate always-fail in both** — broken assertion, too-hard test, or wrong check
- **Study skill-only-pass** — where skill clearly adds value. Understand WHY — which instructions or scripts made the difference?
- **Tighten for inconsistent results** (high stddev) — the skill's instructions may be ambiguous. Add examples or more specific guidance
- **Check time/token outliers** — if one eval takes 3x longer, read its execution transcript to find the bottleneck

## Execution Trace Review

Read the full trace of what the agent did, not just the final output. Three diagnostic patterns:

| Trace Pattern | Root Cause | Fix |
|---|---|---|
| Agent tries multiple approaches before finding one that works | Instructions too vague | Be more specific about which approach to use |
| Agent follows instructions that don't apply to the current task | Too many instructions, no conditional gating | Add "only if X" conditions, or move to reference with conditional read |
| Agent spends time choosing between options | Too many equal options, no default | Pick a default, mention alternatives briefly |

## Adversarial Categories

10 categories for stress testing — pick most realistic for the skill's domain:

1. **Ambiguous request** — could trigger 2+ different paths
2. **Off-topic query** — valid but outside skill's scope
3. **Conflicting constraints** — contradictory requirements
4. **Oversized input** — very long argument, huge file
5. **Minimal/empty input** — "", whitespace, no argument
6. **Partial prerequisite** — some required files missing
7. **Repeated invocation** — same target twice
8. **Malformed format** — wrong type, invalid JSON, typos in flags
9. **Stale context** — outdated input, state has changed
10. **Adversarial phrasing** — same intent, confusing wording

**Severity:** CRITICAL (wrong output, data loss) > MAJOR (partial, misleading) > MINOR (cosmetic, vague error) > PASS (handled correctly)

## Human Review

- Review actual outputs alongside grades for each test case
- Record specific, actionable feedback per case (not "looks bad")
- Empty feedback = output passed review
- Save as `feedback.json` alongside eval directories

## The Iteration Loop

Three signal sources feed each iteration:
1. **Failed assertions** → specific gaps (missing step, unclear instruction)
2. **Human feedback** → broader quality issues (wrong approach, unhelpful structure)
3. **Execution traces** → WHY things went wrong (not just what)

Feed all three + current SKILL.md → propose improvements with these guidelines:

- **Generalize from feedback** — fix underlying issues broadly, not narrow patches for specific test cases
- **Keep the skill lean** — fewer, better instructions outperform exhaustive rules. If pass rates plateau despite adding more rules, try REMOVING instructions
- **Explain the why** — "Do X because Y causes Z" works better than "ALWAYS do X, NEVER do Y"
- **Bundle repeated work** — if every run independently builds similar helper logic, write a tested script in `scripts/`

## Stop Criteria

Stop iterating when:
- Satisfied with results across all test cases
- Human feedback is consistently empty
- No meaningful improvement between iterations
- 5 iterations completed without convergence → escalate to user
