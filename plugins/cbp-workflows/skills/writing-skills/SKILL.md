---
name: writing-skills
description: >
  Author new Claude Code skills or update existing ones. Covers YAML frontmatter,
  step structure, trigger design, quality validation, testing, hub promotion,
  and a full template library. Use when creating, updating, or refining skills
  for the .claude/skills/ directory.
triggers:
  - write-skill
  - create-skill
  - skill-author
  - how to write a skill
  - new skill
  - author skill
  - update skill
  - modify skill
  - improve skill
  - edit skill
  - refine skill
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<skill-name or 'from-session' to extract from conversation>"
type: workflow
version: "3.2.0"
---

# Writing Skills — The Skill Authoring Guide

Author new Claude Code skills or update existing ones — from scratch, from observed patterns, or from session analysis.

**Request:** $ARGUMENTS

---

> Aligned with Anthropic's [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and [Skills for Enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise) as of 2026-04.

## STEP 1: Determine Authoring Mode

Parse `$ARGUMENTS` to choose the path:

| Input | Mode | Starting Point |
|-------|------|----------------|
| `from-session` | **From Session** (recommended) | Start at Step 3 — best skills come from real tasks |
| A skill name or description | **From Scratch** or **Update** | Check if skill exists → Update (Step 1.3) or create (Step 2) |
| A URL or file path to existing workflow | **From Reference** | Start at Step 2, pre-fill from reference |
| Empty / vague | **Interactive** | Ask: "What repeated task do you want to automate?" |

**Auto-detect Update mode:** When `$ARGUMENTS` names an existing skill (directory exists in `.claude/skills/` or `core/.claude/skills/`), switch to Update mode (Step 1.3). Do not treat updates as new skill creation.


**Read:** `references/determine-authoring-mode.md` for detailed step 1: determine authoring mode reference material.

## STEP 2: Skill Authoring — From Scratch

<role>Act as a Claude skill architect who designs prompts with built-in failure prevention from the start.</role>

Build a minimal skill that addresses the gaps identified in Step 1.1.
Write only what's needed to pass the eval scenarios from Step 1.2 — you'll
iterate in Step 6. Focus on failure prevention from the start.


**Read:** `references/skill-authoring-from-scratch.md` for detailed step 2: skill authoring — from scratch reference material.

## STEP N: Action Verb + Object

Brief explanation of WHY this step exists (1-2 sentences max).


**Read:** `references/step-n-action-verb-object.md` for detailed step n: action verb + object reference material.

## MUST DO

- Always complete Step 1 before proceeding — skipping it causes cascading errors
- Always verify output before reporting completion
- Always clean up temporary files created during execution
- Run the dedup check if skill will be promoted to the hub

## MUST NOT DO

- MUST NOT skip the verification step — unverified output is unreliable
- MUST NOT modify files outside the specified scope
- MUST NOT proceed if prerequisites are not met — ask the user instead
- MUST NOT output partial results as final — either complete the task or report what is missing
```

#### XML Tags Within Steps (Optional)

Use XML tags to separate content types within a step when the step mixes instructions, context, data, and constraints. This improves Claude's parsing accuracy — per [Anthropic's prompt engineering guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags), XML tags reduce misinterpretation in multi-part prompts.

**When to use:** Steps that mix 3+ content types (instructions + context + constraints + data). Skip for simple steps with only instructions.

**When NOT to use:** Do not replace the skill's top-level markdown structure (YAML frontmatter, `## STEP N:` headings, `## MUST DO` sections) with XML. XML tags are for *within-step* content separation only.

Recommended tags (names are flexible — pick what's semantically clear):

| Tag | Purpose | Example |
|---|---|---|
| `<context>` | Background info the step needs | `<context>Read the user's $ARGUMENTS and classify input type.</context>` |
| `<constraints>` | Guardrails for this specific step | `<constraints>MUST NOT proceed if input is empty.</constraints>` |
| `<input>` | Variable data being processed | `<input>$ARGUMENTS</input>` |
| `<output>` | Expected output format for this step | `<output>JSON with {result, summary, failures} fields</output>` |
| `<examples>` | Few-shot examples within a step | Wrap 2-3 input/output pairs |

Example of a step using XML tags:

```markdown
## STEP 2: Classify the Input

Determine the input type to route to the correct processing path.

<context>
The user provides either a file path, a URL, or a natural language description.
Each type requires different validation and processing.
</context>

<constraints>
- MUST detect input type before processing — wrong classification causes silent failures
- MUST reject inputs that match none of the 3 types with a clear error message
</constraints>

<output>
One of: `file_path`, `url`, or `description` — stored for use in Step 3.
</output>
```

**Key rules for XML tag usage:**
- Use consistent tag names throughout all steps in one skill — do not mix `<constraints>` and `<rules>` for the same purpose
- Reference tags by name when pointing to them: "Using the context in `<context>` tags..." not "the context above"
- No canonical "magic" tag names exist — Claude treats all XML tag names equally (per Anthropic docs)

Rules for writing MUST DO / MUST NOT DO:
- 4-8 items per section (fewer is better — only include non-obvious rules)
- Each item MUST have a `— Why:` suffix explaining the consequence of violation (e.g., "Always validate input before processing — Why: unvalidated input caused silent data corruption in downstream steps")
- Every constraint must have a reason — no rules without purpose. If you cannot articulate why a rule exists, do not include it
- MUST NOT items always state what to do instead
- Do not repeat what the steps already say — these are for edge cases and guardrails
- Constraints from the failure mode analysis (Step 2.3) MUST appear here with their mapped preventions

#### Instruction Writing Patterns

Eleven patterns improve instruction quality within steps.

**Read:** `references/instruction-writing-patterns.md` for calibrating control, gotchas sections, validation loops, plan-validate-execute, defaults over menus, procedures over declarations, script design for agentic use, checklists, input/output examples, conditional workflow routing, and install-then-use patterns.

### 2.6 Embed Reference Self-Update Mechanism

Every skill that uses `references/` MUST include a **Reference Completeness Check** as its final substantive step. This makes skills iteratively self-improving — each invocation can grow the skill's knowledge base.

#### How It Works

The protocol file `references/self-update-protocol.md` defines the complete workflow:
runtime mode detection (FULL vs STANDALONE), structured entry format, admission gate,
independent scoring, consolidation triggers, and version bump.

**During skill authoring:**

1. **Copy** `references/self-update-protocol.md` from this skill's references into the new skill's `references/` directory
2. **Add this step** to the new skill (as the last step before any commit/output step):

```markdown
## STEP N: Reference Completeness Check

Check whether this invocation surfaced knowledge not yet in references.

**Read:** `references/self-update-protocol.md` for the full detection,
scoring, gating, and consolidation workflow.
```

3. **Create** an empty `references/CHANGELOG.jsonl` in the new skill's references

#### When to Skip

- Skills with no `references/` directory (simple skills under 200 lines)
- Skills that are read-only / analysis-only with no domain knowledge accumulation
- Skills that already persist knowledge through another mechanism (e.g., `learnings.json`)

#### Entry Format Summary

Each knowledge entry uses a structured 13-field format with type taxonomy
(`gotcha`, `pattern`, `fix`, `pitfall`, `decision`, `preference`), state lifecycle
(`CANDIDATE → ACTIVE → CONSOLIDATED → DEPRECATED`), numeric confidence (0.70–1.00),
scope globs, and supersession pointers. Full schema is in the protocol file.

### 2.7 Validate Before Saving

Before writing the skill file, run through the quality checklist in Step 5.

---

## STEP 3: Session Log Analysis

Extract skill candidates from the current conversation by identifying repeated workflows.


**Read:** `references/session-log-analysis.md` for detailed step 3: session log analysis reference material.

## STEP 4: Naming and Organization


**Read:** `references/naming-and-organization.md` for detailed step 4: naming and organization reference material.

## STEP 5: Quality Checklist

Before saving the skill, validate every item. Do NOT skip this step.


**Read:** `references/quality-checklist.md` for detailed step 5: quality checklist reference material.

# Check for trigger overlap
grep -r "triggers:" core/.claude/skills/*/SKILL.md -A 8

# Check for name similarity
ls core/.claude/skills/

# Check for description overlap
grep -r "description:" core/.claude/skills/*/SKILL.md -A 3
```

If overlap is found:
- **Same triggers, different purpose** — Rename triggers to be more specific
- **Different triggers, same purpose** — Consolidate into one skill
- **Partial overlap** — Consider whether extending the existing skill is better than creating a new one

### 5.4 Length Validation

| Length | Assessment |
|--------|-----------|
| <50 lines | Suspiciously short — verify it's not a stub. May belong as a rule instead of a skill. |
| 50-200 lines | Acceptable for simple, focused skills |
| 200-500 lines | Ideal range for standard skills |
| 500-1000 lines | Warning zone — consider splitting reference material into `references/` subdirectory |
| >1000 lines | Too long — MUST split into smaller skills or extract reference material into `skill-name/references/*.md` |

For skills with extensive reference material, use this directory structure:
```
skill-name/
  SKILL.md           # Core workflow (under 500 lines)
  references/        # Supplementary knowledge (loaded on-demand)
    setup-guide.md
    api-reference.md
  templates/         # Reusable templates
    config.yaml
```

### 5.5 Model Compatibility

If the skill will be used across model tiers, test with the smallest
target model. What works for Opus may need more guidance for Haiku:
- **Haiku:** Does the skill provide enough guidance for the task?
- **Sonnet:** Is the skill clear and efficient?
- **Opus:** Does the skill avoid over-explaining?

---

## STEP 6: Evaluate and Iterate with /skill-evaluator

Invoke `/skill-evaluator` via the Agent tool. The entire evaluate-fix-re-evaluate loop runs autonomously with one human approval at the end.

**Read:** `references/iterative-development.md` for the full Claude A/B
development methodology — how to test with fresh instances, diagnose issues
from observation, and gather team feedback.

**Before formal eval:** Run the skill informally against one real task. Read the execution trace (not just output). Fix obvious issues first.


**Read:** `references/evaluate-and-iterate-with-skill-evaluator.md` for detailed step 6: evaluate and iterate with /skill-evaluator reference material.

## Failure Prevention Map: <skill-name>

| # | Failure Mode | Prevention | Step Where Embedded | Constraint (MUST DO/MUST NOT DO) |
|---|---|---|---|---|
| 1 | <from Step 2.3> | <validation/gate/check> | Step N | "Always X — Why: Y" |
| 2 | <from Step 2.3> | <validation/gate/check> | Step N | "MUST NOT X — do Y instead" |
| 3 | <from Step 2.3> | <validation/gate/check> | Step N | "Always X — Why: Y" |

Output format locked: <YES with template / NO — flag for fix>
Stress test score: <N%> (from Step 6.3)
```

Present this map to the user alongside the skill draft. The map makes failure prevention layers visible and auditable — without it, guardrails are buried in the skill body and easy to miss during review.

---


**Read:** `references/failure-prevention-map-skill-name.md` for detailed failure prevention map: <skill-name> reference material.

## STEP 7: Hub Promotion Workflow

If the skill is valuable enough to share across projects via the hub.

### 7.1 Pre-Promotion Checklist

| Check | Action |
|-------|--------|
| Quality checklist passes (Step 5) | All items green |
| Tested with 5 scenarios (Step 6.1) | All pass |
| Stress tested with 10 adversarial inputs (Step 6.3) | Score >= 90% |
| Not a duplicate | Run: `PYTHONPATH=. python scripts/dedup_check.py` |
| Follows naming conventions (Step 4) | Directory and name match, correct prefix if stack-specific |
| `version` field present | SemVer format in frontmatter |
| `type` field present | `workflow` or `reference` declared |
| `allowed-tools` is least-privilege | Read-only skills don't include Write/Edit/Bash |
| No project-specific hardcoded paths | Replace with `$ARGUMENTS` or documented placeholders |
| Team feedback gathered (if applicable) | At least one teammate has used the skill on a real task |
| No placeholder markers | No TODO/FIXME HTML comment markers or stub content |
| Under size limit | SKILL.md under 1000 lines; use `references/` for supplementary material |
| No secrets or credentials | Scan for API keys, tokens, passwords |

### 7.2 Add to Registry

After placing the skill in `core/.claude/skills/<name>/SKILL.md`, update the registry:

1. Add an entry to `registry/patterns.json` with: name, type, category, version, hash, dependencies
2. Run: `python scripts/generate_docs.py` to update the dashboard
3. Verify the skill appears in `docs/DASHBOARD.md`

### 7.3 Submit via Contribution Flow

If contributing from a downstream project:

1. Invoke `/contribute-practice` to validate and package the skill
2. The contribution flow handles PR creation, dedup verification, and registry updates

---


## STEP 8: Post-Promotion Lifecycle

What happens after a skill ships: security vetting, deployment governance,
monitoring, version management, deprecation, and scaling considerations.

**Read:** `references/post-promotion-lifecycle.md` for the full lifecycle
covering security review gates (8.1), deployment governance with registry
requirements (8.2), monitoring and drift detection (8.3), version management
with rollback plans (8.4), deprecation lifecycle (8.5), and scaling
considerations including recall limits and consolidation triggers (8.6).

**Also read:** `references/security-review.md` for the detailed risk tier
assessment and 8-step review checklist referenced by Step 8.1.

---

## STEP 9: Template Library

Pre-built starting skeletons for common skill types. Copy the appropriate template and fill in the placeholders.

> **Reference:** See [references/skill-templates.md](references/skill-templates.md) for the full template library (Templates A-G: Workflow, Analysis, Generation, Testing, Deployment, Migration, Reference).

---

## Anti-Patterns

> **Reference:** See [references/anti-patterns.md](references/anti-patterns.md) for 9 common skill anti-patterns to avoid.

---


## MUST DO

- Always read at least 2 existing skills before authoring a new one — pattern-match from working examples
- Always validate with the quality checklist (Step 5) before saving
- Always check for trigger overlap with existing skills
- Always include MUST DO and MUST NOT DO sections in every skill
- Always include a verification step in skills that modify state
- Always use concrete, actionable language in steps — verbs, not adjectives
- Always present the draft to the user for review before saving
- Always test the skill with 5 scenarios from Step 6 (3 happy-path + 2 edge-case)
- Always complete failure mode analysis (Step 2.3) before writing constraints — prevention beats diagnosis
- Always include a `— Why:` justification on every MUST DO / MUST NOT DO item
- Always lock the output format with a code block template for skills that produce structured output — Why: ambiguous output formats cause inconsistent behavior across invocations
- Always produce a failure prevention map (Step 6.5) before hub promotion — Why: makes guardrails visible and auditable during review
- Always evaluate multi-phase decomposition (Step 2.4) when a prompt covers a full end-to-end workflow — Why: monolithic skills exceeding 400 lines become hard to test, reuse, and maintain
- Always run domain pattern review (Step 6.6) for agents and orchestration patterns before hub promotion — Why: structural gates pass patterns that violate orchestration best practices; domain review catches substance violations
- Always invoke `/skill-evaluator` via Agent tool for evaluation — do not evaluate inline
- Always apply auto-fix routing for FIX/FAIL verdicts — do not ask user what to fix
- Always present final skill + eval report for user approval before hub promotion
- Always use gerund or action-oriented naming for skill names — Why: consistent naming improves discoverability and professionalism across the skill library
- Always keep reference files one level deep from SKILL.md — Why: Claude partially reads deeply nested files, resulting in incomplete information
- Always copy `references/self-update-protocol.md` into every authored skill that has a `references/` directory — Why: the protocol is the single source of truth for the self-update mechanism; without it, the Reference Completeness Check step has no instructions to follow
- Always embed a Reference Completeness Check step pointing to the protocol in skills with `references/` — Why: skills that don't self-update become stale as their domain evolves; each invocation is an opportunity to capture new knowledge
- Always create an empty `references/CHANGELOG.jsonl` alongside the protocol file — Why: the audit sidecar enables rollback, mode detection, and mode upgrade (STANDALONE → FULL) when learn-n-improve is later installed
- Always require user approval before writing reference updates — Why: unreviewed auto-updates can introduce incorrect or low-quality content into the knowledge base
- Always verify the protocol file's admission gate filters generic knowledge — Why: without filtering, references accumulate noise that degrades rather than improves future invocations

## MUST NOT DO

- MUST NOT create a skill for something that should be a rule — if it has no steps, use `.claude/rules/`
- MUST NOT use vague step language ("consider", "think about", "ensure quality") — use specific actions instead
- MUST NOT create skills with >10 steps — split into sub-skills or use delegation
- MUST NOT add tools to `allowed-tools` that the skill does not use
- MUST NOT create skills with overlapping triggers — check existing skills first
- MUST NOT save a skill without running the quality checklist
- MUST NOT create skills that duplicate existing ones — extend or consolidate instead
- MUST NOT skip the MUST DO / MUST NOT DO sections — they are mandatory guardrails
- MUST NOT ask user to manually invoke `/skill-evaluator` — invoke it autonomously via Agent tool
- MUST NOT proceed to Step 7 without user approval of the final skill + eval report
- MUST NOT write descriptions in first or second person ("I analyze...", "You can use...") — always third person ("Analyzes...") because descriptions are injected into the system prompt and inconsistent POV causes discovery problems
- MUST NOT chain reference files (SKILL.md → ref1.md → ref2.md) — keep one level deep from SKILL.md
- MUST NOT include time-sensitive content ("before August 2025") — use collapsible "Old patterns" section instead
- MUST NOT be the sole reviewer of your own skill for hub promotion — Why: separation of duties prevents blind spots and catches adversarial patterns the author may overlook (see Step 8.1)
- MUST NOT auto-update references without user approval — present findings and wait for confirmation before writing — Why: unreviewed writes can introduce incorrect knowledge that persists across all future invocations
- MUST NOT add generic programming knowledge to references — only domain-specific patterns, edge cases, and gotchas per the admission gate in the protocol — Why: generic entries (use try/catch, validate inputs) add noise without value
- MUST NOT skip the Reference Completeness Check for skills with `references/` — the step is what makes skills self-improving rather than static — Why: each skipped invocation is lost domain knowledge that could have improved future runs
- MUST NOT write reference entries with confidence below 0.70 — the admission gate rejects insufficient evidence — Why: low-confidence entries degrade trust in the reference base and require costly cleanup later
