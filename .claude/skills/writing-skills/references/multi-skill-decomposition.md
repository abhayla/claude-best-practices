# Multi-Skill Decomposition — Turning One Prompt into a Skill System

Reference material for STEP 2.5: when a single prompt covers a full end-to-end
workflow, decompose it into connected skills with explicit handoffs and checkpoints.

## When to Trigger Decomposition

| Signal | Action |
|--------|--------|
| Prompt has 4+ distinct phases (input, processing, validation, output) | Decompose into one skill per phase |
| Single prompt exceeds ~400 lines when converted to a skill | Split — it will violate the 500-line SKILL.md limit |
| Phases can be reused independently in other workflows | Split — reusable phases are more valuable as standalone skills |
| All phases are tightly coupled and share state heavily | Keep as one skill — forced decomposition adds complexity without benefit |

## Decomposition Workflow

### Phase 1: Map the Workflow

Ask the user to provide their current prompt and describe the full workflow it
sits inside. Then map the workflow into distinct phases:

<phases>
<phase name="input">
  Collect, validate, and normalize all inputs the workflow needs.
  Output: a validated input artifact (JSON, structured data, or file list).
</phase>
<phase name="processing">
  Transform inputs into the core deliverable. This is where the main
  logic lives — code generation, analysis, refactoring, etc.
  Output: the primary artifact (code, report, config).
</phase>
<phase name="validation">
  Verify the processing output meets quality standards. Run tests,
  linters, type checks, or domain-specific validators.
  Output: a pass/fail verdict with details.
</phase>
<phase name="output">
  Format, present, and persist the final deliverable. Write files,
  generate reports, update registries, or create PRs.
  Output: the user-facing result.
</phase>
</phases>

Not every workflow has all 4 phases. Some have 3, some have 5+. Map what
actually exists — do not force-fit into exactly 4.

### Phase 2: Define Handoff Contracts

Each phase boundary MUST have an explicit handoff contract — the output of
phase N is the exact input of phase N+1.

<handoff-contract>
<rule>Output of phase N MUST be a concrete artifact (file, JSON, structured text) — not implicit state or "context from the conversation".</rule>
<rule>Each handoff artifact MUST have a defined schema or format so the receiving skill can validate it before proceeding.</rule>
<rule>If phase N fails, it MUST produce an error artifact with the same schema but a `result: "FAILED"` field — the receiving phase checks this before starting work.</rule>
</handoff-contract>

Example handoff contract between input and processing phases:

```json
{
  "handoff": "input → processing",
  "artifact": "validated-input.json",
  "schema": {
    "source_prompt": "string — the original user prompt",
    "workflow_phases": ["string[] — identified phases"],
    "constraints": ["string[] — user-specified constraints"],
    "result": "VALIDATED | FAILED"
  }
}
```

### Phase 3: Write Phase Skills

For each phase, create a standalone skill following the standard authoring
process (STEP 2 of writing-skills). Each phase skill MUST:

<skill-requirements>
<requirement>Work independently — callable on its own without the other phases.</requirement>
<requirement>Accept the upstream handoff artifact as its `$ARGUMENTS` or as a file path argument.</requirement>
<requirement>Produce the downstream handoff artifact as its output.</requirement>
<requirement>Validate the incoming handoff artifact before starting work — reject malformed or FAILED inputs.</requirement>
</skill-requirements>

### Phase 4: Connect with Checkpoints

Between each phase, insert a checkpoint that catches failures before they
propagate downstream.

<checkpoint-pattern>
<step>Read the handoff artifact from the previous phase.</step>
<step>Validate the artifact schema — reject if malformed.</step>
<step>Check the `result` field — if FAILED, stop and report which phase failed and why.</step>
<step>If VALIDATED/PASSED, invoke the next phase skill with the artifact as input.</step>
</checkpoint-pattern>

Checkpoints can be:
- **Inline** — validation logic at the top of each phase skill (simpler, recommended for 2-3 phases)
- **Orchestrator** — a parent skill or agent that sequences phases and handles checkpoints (recommended for 4+ phases, see agent-orchestration rules)

### Phase 5: End-to-End Testing

Test the full system, not just individual skills. Run 3 real use cases through
the entire pipeline:

<test-protocol>
<case type="happy-path">A straightforward input that should pass all phases cleanly. Verify the final output matches expectations.</case>
<case type="mid-pipeline-failure">An input that passes validation but fails during processing. Verify the checkpoint catches it and reports the correct failure phase.</case>
<case type="malformed-handoff">Manually corrupt a handoff artifact between phases. Verify the receiving phase rejects it with a clear error instead of producing garbage output.</case>
</test-protocol>

## Example: Decomposing a Code Review Prompt

Original prompt: "Review this PR for quality, security, and performance, then
generate a summary report."

<decomposition-example>
<phase name="input" skill="pr-reader">
  Fetch PR diff, read changed files, collect metadata (author, branch, labels).
  Handoff: `pr-context.json` with file list, diff hunks, PR metadata.
</phase>
<phase name="processing" skill="code-analyzer">
  Run quality checks, security scan, performance analysis on each changed file.
  Handoff: `analysis-results.json` with findings per file, severity levels.
</phase>
<phase name="validation" skill="review-gate">
  Check if any findings are blocking (critical security, failing tests).
  Handoff: `review-verdict.json` with pass/fail, blocking findings list.
</phase>
<phase name="output" skill="review-reporter">
  Format findings into a PR comment or markdown report.
  Handoff: the formatted review comment (posted or written to file).
</phase>
</decomposition-example>

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| God skill | One skill does input + processing + validation + output in 800 lines | Decompose into phase skills |
| Invisible handoffs | Phase 2 reads "whatever phase 1 left in context" | Define explicit handoff artifacts with schemas |
| No checkpoint validation | Phase 3 assumes phase 2 always succeeds | Add result-field check at every phase boundary |
| Over-decomposition | 2-step workflow split into 5 micro-skills | Only split when phases are genuinely independent or reusable |
| Shared mutable state | All phases read/write the same global file | Each phase takes immutable input, produces new output |

## CRITICAL RULES

- Each phase skill MUST work independently — no phase should depend on another to function
- Handoffs MUST be explicit artifacts — output of phase N is the exact input of phase N+1
- Checkpoints MUST catch failures before they move downstream — validate result fields at every boundary
- Test the full system end-to-end, not just individual skills — include happy-path, mid-pipeline-failure, and malformed-handoff cases
- For 4+ phase systems, use an orchestrator agent (not a skill) per agent-orchestration rules
