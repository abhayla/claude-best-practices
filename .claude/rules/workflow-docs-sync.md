---
description: >
  Remind to regenerate workflow docs after modifying skills, agents, or rules.
globs:
  - "core/.claude/skills/*/SKILL.md"
  - "core/.claude/agents/*.md"
  - "core/.claude/rules/*.md"
  - ".claude/skills/*/SKILL.md"
  - "config/workflow-groups.yml"
---

# Workflow Docs Sync Reminder

When you modify, add, or delete a skill, agent, or rule file, the workflow
documentation in `docs/workflows/` may become stale.

After making changes to any pattern file:

1. Run `/workflow-doc-reviewer --generate` to regenerate the workflow documentation
2. If the pattern is new, verify it appears in at least one workflow group
   in `config/workflow-groups.yml` — orphan patterns are flagged during generation
3. If cross-references changed (added/removed `Skill()`, `Agent()`, or
   `/skill-name` calls), verify the workflow diagrams updated correctly

Use `/workflow-doc-reviewer` (default mode) to preview status without writing files.
