# Pattern Templates & Quality Checks

Reference material for Step 7 (Generate Patterns) of `/synthesize-project`.

## Rule Template

```yaml
---
description: >
  [1-2 sentence description of what this rule enforces and why]
globs: ["**/*.py", "**/*.ts"]  # Scope to relevant file types
synthesized: true
private: false  # Set to true if sensitive (auth, billing, secrets)
---

# [Convention Name]

[Body: what the convention is, why it matters, what to do and not do.
Include concrete examples from the project's actual code patterns.
Use MUST/MUST NOT for critical constraints.]
```

## Skill Template

```yaml
---
name: [kebab-case-name]
description: >
  [1-3 sentences starting with a verb]
type: workflow
allowed-tools: "[minimal tool set]"
argument-hint: "[required-arg] [--optional-flag]"
version: "1.0.0"
synthesized: true
private: false
---

# [Skill Title]

## STEP 1: [Verb Phrase]
[numbered instructions with concrete file paths and commands from THIS project]

## STEP 2: [Verb Phrase]
[numbered instructions]

## CRITICAL RULES
- [constraint 1]
- [constraint 2]
```

Skills MUST encode project-specific multi-step procedures. Each step should reference actual file paths, commands, or patterns from the codebase. Generic workflow skills (e.g., "run tests") add no value — the skill must capture the project-specific gotchas, ordering, and coordination.

## Agent Template

```yaml
---
name: [agent-name]
description: >
  When and why to use this agent. [1-3 sentences]
tools: ["Read", "Grep", "Glob"]  # JSON array, least-privilege
model: inherit
synthesized: true
private: false
---

# [Agent Title]

## Core Responsibilities
- [what this agent analyzes or reviews]
- [what domain knowledge it applies]

## Input
[what to pass to this agent]

## Output Format
[structured output: checklist, report, verdict]

## Decision Criteria
[project-specific rules this agent applies]
```

Agents MUST have a clear domain focus specific to this project. A generic "code reviewer" agent adds no value — an agent that reviews meal generation output for dietary constraint violations does.

## Quality Checks

Run these checks for each generated pattern before writing:

### Structure (pattern-structure.md)
- Does `version` field exist and follow SemVer format (e.g., `"1.0.0"`)?
- For skills: does it have `name`, `description`, `type`, `allowed-tools`, `argument-hint`, `version`?
- For skills: does it have a `## CRITICAL RULES` section at the end?
- For agents: does frontmatter include `tools` as a JSON array (e.g., `["Read", "Grep", "Glob"]`)?
- For agents: does body include `## Core Responsibilities` and `## Output Format` sections?
- For rules: does it have `globs:` in frontmatter OR `# Scope: global` in first 5 lines?

### Portability (pattern-portability.md)
- Is it specific to THIS project (not generic advice)?
- Are `allowed-tools` least-privilege (read-only skills don't include Write/Edit/Bash)?
- Are project-specific file paths used as concrete examples (good) not as hardcoded assumptions (bad)?

### Self-containment (pattern-self-containment.md)
- Does it contain at least 30 lines of actual content (not a stub)?
- Is it under 500 lines? If 500-1000, consider splitting. Over 1000 = must split.
- No placeholder markers (`<!-- TODO -->`, `<!-- FIXME -->`)?
- If it references another skill by name, does that skill exist in the project's `.claude/`?

### Language (rule-writing-meta.md)
- Does it use RFC 2119 language (MUST, MUST NOT, NEVER) for critical constraints?
- For rules: does it provide alternatives, not just prohibitions?

## Sensitivity Flagging

Scan each generated pattern for keywords: `auth`, `secret`, `token`, `credential`, `billing`, `payment`, `session`, `encryption`, `API key`, `password`, `private key`. If found, **flag the pattern and ask the user** whether to mark it `private: true`. Do not auto-flag silently — the user may intend for auth-related patterns to be shareable.
