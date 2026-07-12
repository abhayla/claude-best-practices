# STEP 5: Quality Checklist

### 5.1 Structure Validation

| Check | Pass Criteria |
|-------|---------------|
| YAML frontmatter is valid | All required fields present, YAML parses without error |
| `name` matches directory name | `name: foo-bar` lives in `skills/foo-bar/SKILL.md` |
| `description` starts with a verb | "Debug...", "Generate...", "Analyze..." |
| `type` is declared | `workflow` or `reference` — determines required body structure |
| `version` is valid SemVer | Format: `"1.0.0"` — required for version tracking |
| `triggers` has 3-6 entries | Mix of slash commands and natural language |
| `allowed-tools` is minimal | No unused tools listed. Read-only skills MUST NOT include `Write`, `Edit`, or `Bash` |
| No high-risk indicators without justification | Scripts, MCP refs, network access, or broad file access are documented and necessary (see `references/security-review.md` risk tiers) |
| `argument-hint` uses `<>` and `[]` correctly | Required in angle brackets, optional in square brackets |
| No placeholder markers | No TODO/FIXME/PLACEHOLDER HTML comment markers in the body |
| Reference self-update mechanism present | Skills with `references/` include: (1) `references/self-update-protocol.md` copied from this skill, (2) a Reference Completeness Check step pointing to it, (3) an empty `references/CHANGELOG.jsonl` |

### 5.2 Content Validation

| Check | Pass Criteria |
|-------|---------------|
| Steps are numbered sequentially | STEP 1, STEP 2, STEP 3... |
| Each step starts with a verb | "Analyze", "Run", "Create" — not "Analysis", "Running", "Creation" |
| Steps have concrete actions | Commands, file paths, or specific instructions — not "consider" or "think about" |
| Conditional logic uses tables | No nested if/else bullet points |
| Output format is templated | Expected outputs shown in code blocks |
| MUST DO section has 4-8 items | Each explains the consequence of skipping |
| MUST NOT DO section has 4-8 items | Each states what to do instead |
| No vague language | No "consider", "maybe", "try to", "think about" |
| No Windows-style paths | All file paths use forward slashes (`/`), even on Windows |
| Install-then-use for deps | Package usage shows install command before import |

### 5.3 Overlap Check

Scan existing skills for trigger and purpose overlap:

```bash
