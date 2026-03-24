# STEP 2: Skill Authoring — From Scratch

### Invoking Skill Authoring

Use this prompt to author a new skill with built-in failure prevention. The `<role>` tag sets the architect mindset — Claude will design with failure resistance from the start, not bolt it on after.

```markdown
<role>
Act as a Claude skill architect who designs prompts with built-in
failure prevention from the start.
</role>

<task>
Take the goal described in `$ARGUMENTS` and build a production-ready
Claude skill that eliminates the most common failure modes before
they happen.
</task>

<steps>
1. Clarify what the skill does, who uses it, and what it produces
2. Identify the 3 most likely failure modes for this type of task
3. Build the skill with constraints, output formats, and guardrails
   pre-loaded — every constraint must have a reason
4. Run it against 5 edge case inputs to stress test it
5. Deliver the final skill with a failure prevention map showing
   every guardrail and where it is embedded
</steps>

<rules>
- Prevention beats diagnosis — build failure resistance in from day one
- Every constraint must have a reason — no rules without purpose
- Edge cases must be tested before delivery, not after
- Output format must be locked — ambiguity is the enemy of consistency
- Report the failure prevention map alongside the skill draft
</rules>

<output>
Skill Draft → Failure Prevention Map → Edge Case Results → Production-Ready Skill
</output>
```

---

### 2.1 Define the YAML Frontmatter

Every skill requires a `SKILL.md` file with YAML frontmatter. Each field has specific requirements:

```yaml
---
name: lowercase-kebab-case-name
description: >
  One to three sentences explaining WHAT the skill does, WHEN to use it,
  and what it produces. Start with an action verb. Include the primary
  use case so Claude can match it from natural language requests.
triggers:
  - slash-command-name
  - natural language phrase 1
  - natural language phrase 2
  - natural language phrase 3
allowed-tools: "Tool1 Tool2 Tool3"
argument-hint: "<required-arg> [optional-arg]"
type: workflow
version: "1.0.0"
---
```

#### Field Reference

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | Lowercase kebab-case. Must match the directory name. 2-4 words max. |
| `description` | Yes | 1-3 sentences. Start with a verb. Include when to use it. Must fit in ~50 words. |
| `triggers` | Recommended | 3-6 entries. Mix of slash commands and natural language phrases. |
| `allowed-tools` | Yes | Space-separated list. Use the minimal set needed. Never include tools you do not use. |
| `argument-hint` | Yes | Show required args in `<angle-brackets>`, optional in `[square-brackets]`. Use descriptive placeholder names. |
| `type` | Yes | `workflow` (multi-step procedure with numbered STEP sections) or `reference` (knowledge base / lookup guide with organized sections, no step numbering required). |
| `version` | Yes | SemVer format (`"1.0.0"`). Bump MAJOR for breaking output/arg changes, MINOR for new optional content, PATCH for wording fixes. |

#### Allowed-Tools Selection Guide

Choose the minimal set. Each tool you add expands what the skill can do — and what can go wrong.

| Tool | Include When |
|------|-------------|
| `Read` | Skill reads existing files |
| `Write` | Skill creates new files from scratch |
| `Edit` | Skill modifies existing files |
| `Bash` | Skill runs commands (tests, builds, git) |
| `Grep` | Skill searches file contents |
| `Glob` | Skill searches for files by name pattern |
| `Skill` | Skill delegates to other skills |
| `Agent` | Skill needs subagent delegation for parallel or bulk work |
| `WebFetch` | Skill fetches content from URLs |
| `WebSearch` | Skill searches the internet |

**Rule of thumb:** If a step does not use a tool, do not include that tool. A read-only analysis skill should NOT include `Write` or `Edit`.

#### Trigger Design

Triggers determine when Claude activates the skill. Poor triggers cause false activations or missed activations.

**Good triggers:**
- Specific slash commands: `write-skill`, `create-skill`
- Natural language that uniquely identifies the task: `how to write a skill`, `author new skill`
- Problem-oriented phrases: `automate this workflow`, `make a reusable pattern`

**Bad triggers:**
- Too broad: `help`, `create`, `write` (matches too many unrelated requests)
- Too narrow: `create a fastapi database migration skill for postgres` (too specific to match)
- Overlapping with other skills: Check existing triggers before adding yours

To check for trigger overlap:
```bash
grep -r "triggers:" core/.claude/skills/*/SKILL.md
```

#### Argument-Hint Design

The argument hint appears in help text and teaches users what to provide.

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `<required>` | `<feature-description>` | Single required input |
| `<required> [optional]` | `<bug-description> [--verbose]` | Required with optional flags |
| `<mode> [details]` | `<scan\|propose\|create> [name]` | Multi-mode skills |
| `<file-or-description>` | `<path/to/file or natural language>` | Flexible input types |

### 2.2 Write the Title and Preamble

After the frontmatter, write a descriptive title and one-line purpose statement:

```markdown
