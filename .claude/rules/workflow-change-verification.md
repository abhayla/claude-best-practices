---
description: >
  Verify facts, cite sources, and flag confidence when modifying workflows.
globs:
  - "core/.claude/**"
  - ".claude/skills/**"
  - ".claude/rules/**"
  - "config/workflow-groups.yml"
  - "registry/patterns.json"
  - "scripts/generate_workflow_docs.py"
---

# Workflow Change Verification

Before creating, modifying, or connecting any workflow component, verify
independently — do not assume from memory or pattern-match from similar work.

## Core Principle: Read Before Claiming

When stating facts about a workflow ("this skill produces X", "this connects
to Y", "this goes in core/.claude/"), MUST verify by reading the actual file.
Do not rely on cached knowledge or inference from similar patterns.

When uncertain, state confidence level explicitly:
- **Verified** — read the file and confirmed
- **Inferred** — based on naming convention or similar pattern, not confirmed
- **Unknown** — need to check before proceeding

Cite the source when making claims: "per implement/SKILL.md Step 5" or
"based on workflow-groups.yml line 12" — not "this skill calls fix-loop."

## 1. Placement Verification

Before writing any skill, agent, or rule file, confirm its destination:

| Question | If YES | If NO |
|----------|--------|-------|
| Would a downstream project need this? | `core/.claude/` + registry entry | `.claude/` (hub-only, no registry entry) |
| Does it manage hub infrastructure (scanning, syncing, doc generation)? | `.claude/` (hub-only) | `core/.claude/` (distributable) |

MUST verify by reading CLAUDE.md "Critical: Two .claude/ Directories" before
placing files. Do not rely on where similar patterns were placed previously.

When moving a pattern between locations (e.g., `core/.claude/` → `.claude/`),
verify the old location is fully removed — including empty directories. Empty
dirs left behind cause validator failures.

## 2. Reference Integrity Before Committing

When a workflow change adds or modifies `Skill()`, `Agent()`, or `/skill-name`
references:

- Verify every referenced skill directory exists — read the filesystem, do not assume
- Verify every referenced agent file exists
- Verify names in `config/workflow-groups.yml` match actual filenames
- If a reference target is missing, flag it — do not silently skip

When deleting or renaming a pattern, also update `config/workflow-groups.yml` —
stale seeds silently produce incomplete workflow docs (the script skips missing
seeds without error).

## 3. Registry Consistency

When modifying distributable patterns in `core/.claude/`:
- Verify the pattern has a matching entry in `registry/patterns.json`
- Verify the version in frontmatter matches the registry version
- When changing a pattern, bump the version in BOTH frontmatter AND registry
  together — follow `pattern-structure.md` SemVer policy (major: breaking,
  minor: new features, patch: fixes)

When modifying hub-only patterns in `.claude/`:
- Verify there is NO entry in `registry/patterns.json`

## 4. Artifact Convention Compliance

When adding or modifying a skill that produces test results:
- Verify it writes to `test-results/{skill-name}.json` — not a custom path
- Verify the JSON schema matches the canonical format (result, summary, failures, duration_ms)
- If consuming upstream artifacts, read the upstream skill to confirm it actually produces that file

## 5. External Grounding

When adding patterns that reference external tools, frameworks, or conventions:
- Verify current API/CLI syntax via web search — do not rely on training data for tool versions
- When claiming something is "industry standard" or "best practice," cite the source (framework docs, RFC, OWASP, etc.)
- Flag when a pattern assumes a specific tool version that may have changed

## 6. Mandatory Validation Before Committing

After any workflow-related change, run these commands before committing:

```bash
# Pattern quality check (frontmatter, portability, cross-references)
PYTHONPATH=. python scripts/validate_patterns.py

# Regenerate workflow docs (picks up new connections, artifacts, steps)
PYTHONPATH=. python scripts/generate_workflow_docs.py

# Regenerate dashboard (after core/.claude/ changes only)
python scripts/generate_docs.py
```

Do not commit if `validate_patterns.py` fails. The workflow doc and dashboard
regeneration ensures documentation stays in sync with the changes.
