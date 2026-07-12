# Failure Prevention Map: <skill-name>

### 6.6 Domain Pattern Review

When the authored pattern is an agent or orchestration-related skill, validate it against
domain-specific reference patterns — not just structural quality gates.

### When to Trigger

| Authored Pattern Type | Domain References to Check |
|----------------------|---------------------------|
| Agent (any `agents/*.md`) | `agent-orchestration.md` rule (tier model, responsibilities, state) |
| Orchestration agent or skill | `anthropic-agent-orchestration-guide` (5 workflow patterns, decision framework) |
| Multi-agent system pattern | `anthropic-multi-agent-research-system-skill` (8 principles, evaluation, production) |
| Non-orchestration skill or rule | **SKIP** — domain review is not applicable |

### How to Review

1. **Identify the authored pattern type** from the table above
2. **Read the matched reference pattern(s)** — these are the audit baseline
3. **Spawn `anthropic-multi-agent-reviewer-agent`** with the authored pattern and matched references:
   ```
   Agent(subagent_type="anthropic-multi-agent-reviewer-agent",
         prompt="Review this pattern against the 8 principles: <pattern content>")
   ```
4. **Evaluate the gap report:**
   - **Grade A-B** → PASS — proceed to Step 7
   - **Grade C** → WARN — present gaps to user, fix if user agrees, then proceed
   - **Grade D-F** → FAIL — must fix before hub promotion

### Why This Step Exists

Structural quality gates (Step 5) check *shape* — does the pattern have frontmatter, steps,
MUST DO sections? Domain review checks *substance* — does the orchestrator follow the
8 principles? Does it scale effort appropriately? Does it have evaluation infrastructure?

A pattern can pass every structural gate while violating every orchestration best practice.
This step closes that gap.

---

