# Workflow Verification Checklist

## Core Principle: Read Before Claiming

When stating facts about a workflow, MUST verify by reading the actual file.
State confidence level: **Verified**, **Inferred**, or **Unknown**.

## Placement Verification

| Question | YES | NO |
|----------|-----|-----|
| Would a downstream project need this? | `core/.claude/` + registry entry | `.claude/` (hub-only, NO registry) |
| Hub infrastructure (scanning, syncing, docs)? | `.claude/` (hub-only) | `core/.claude/` (distributable) |

## Reference Integrity

When adding/modifying `Skill()`, `Agent()`, or `/skill-name` references:
- Verify every referenced skill directory exists on disk
- Verify every referenced agent file exists
- Verify names in `config/workflow-groups.yml` match filenames
- If a reference target is missing, flag it — do not silently skip
- When deleting/renaming, update `config/workflow-groups.yml`

## Registry Consistency

For `core/.claude/` patterns:
- MUST have matching entry in `registry/patterns.json`
- Frontmatter version MUST match registry version
- Bump version in BOTH locations together (SemVer)

For `.claude/` patterns:
- MUST NOT have entry in `registry/patterns.json`

## Artifact Conventions

Skills producing test results MUST write to `test-results/{skill-name}.json`
with canonical schema: `result`, `summary`, `failures`, `duration_ms`.

## Mandatory Validation Commands

```bash
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
PYTHONPATH=. python scripts/generate_workflow_docs.py
python scripts/generate_docs.py
```

Do not commit if the validator fails.

## Workflow Docs Sync

After modifying any pattern file:
1. Run `/workflow-doc-reviewer --generate` to regenerate workflow docs
2. Verify new patterns appear in `config/workflow-groups.yml`
3. If cross-references changed, verify workflow diagrams updated
