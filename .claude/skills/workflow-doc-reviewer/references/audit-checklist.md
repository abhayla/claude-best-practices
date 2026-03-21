# Workflow Audit Checklist

Reference material for `/workflow-doc-reviewer --review` mode.

## Seed Existence Checks

For each entry in `config/workflow-groups.yml`:

| Pattern Type | Expected Location | Fallback Location |
|-------------|-------------------|-------------------|
| Skill | `core/.claude/skills/{name}/SKILL.md` | `.claude/skills/{name}/SKILL.md` |
| Agent | `core/.claude/agents/{name}.md` | `.claude/agents/{name}.md` |
| Rule | `core/.claude/rules/{name}.md` | `.claude/rules/{name}.md` |

## Cross-Reference Patterns to Detect

The audit scans pattern bodies for these reference patterns:

| Pattern | Regex | Example |
|---------|-------|---------|
| Skill invocation | `Skill\(["']([a-z0-9_-]+)["']\)` | `Skill("fix-loop")` |
| Slash command | `` `/([a-z0-9_-]+)` `` | `/fix-loop` |
| Agent dispatch | `Agent\(["']([a-z0-9_-]+)["']\)` | `Agent("tester-agent")` |
| Delegation | `delegates?\s+to\s+/([a-z0-9_-]+)` | `delegates to /learn-n-improve` |
| Invocation | `(?:invokes?\|runs?)\s+/([a-z0-9_-]+)` | `invokes /post-fix-pipeline` |

## Health Indicators

### Healthy Workflow
- All seeds exist as files
- Cross-references resolve to existing patterns
- At least 50% of edges are bidirectional
- No orphan patterns in the workflow's domain

### Warning Signs
- One-way edges (A references B but B doesn't reference A)
- Seeds pointing to non-existent patterns
- Workflow group with 0 discovered edges (seeds are disconnected)
- Patterns with high in-degree but 0 out-degree (sinks)

### Critical Issues
- Broken `Skill()` or `Agent()` calls (target doesn't exist)
- Circular dependencies creating infinite loops
- Workflow group with all seeds missing (dead group)

## Coverage Thresholds

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Assigned / Total patterns | >70% | 50-70% | <50% |
| Bidirectional edge ratio | >60% | 40-60% | <40% |
| Broken references | 0 | 1-3 | >3 |
| Orphan patterns | <20% | 20-40% | >40% |
