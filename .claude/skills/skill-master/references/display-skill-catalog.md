# STEP 3: Display Skill Catalog

### 3.1 Generate Catalog Output

For each category inferred in Step 1.3, list the skills belonging to it:

```
=== SKILL CATALOG ===
Discovered {N} skills across {M} categories.

--- Architecture ---
  /brainstorm          — Socratic questioning phase before planning or implementation
  /strategic-architect — <description from frontmatter>

--- Workflow ---
  /implement           — Implement a feature or fix following a structured workflow
  /executing-plans     — <description from frontmatter>
  /writing-plans       — <description from frontmatter>
  /fix-loop            — <description from frontmatter>
  /fix-issue           — <description from frontmatter>

--- Quality ---
  /systematic-debugging — <description from frontmatter>
  /security-audit       — <description from frontmatter>
  /supply-chain-audit   — <description from frontmatter>
  /auto-verify          — <description from frontmatter>

--- Collaboration ---
  /request-code-review  — <description from frontmatter>
  /receive-code-review  — <description from frontmatter>
  /branching        — <description from frontmatter>
  /contribute-practice  — <description from frontmatter>

--- Stack-Specific ---
  /fastapi-db-migrate   — <description from frontmatter>
  /android-run-tests    — <description from frontmatter>
  /flutter-dev          — <description from frontmatter>
  ... (all stack-prefixed skills)

--- Meta ---
  /writing-skills       — Guide for authoring new skills
  /skill-master         — This skill (dynamic router)
  /skill-factory        — <description from frontmatter>

--- Utility ---
  ... (remaining skills)

=== END CATALOG ===
```

Every description shown MUST come from the actual frontmatter read in Step 1.2 — never
from memory or hardcoded text.

### 3.2 Show Usage Hints

After the catalog, display:

```
USAGE:
  /skill-master <describe what you want>    — Route to the best skill
  /skill-master list                        — Show this catalog
  /skill-master --workflow <task>           — Suggest a multi-skill workflow
  /skill-master --chain <skill1,skill2>     — Execute skills in sequence
```

### 3.3 Show Quick Workflows

Scan all skill descriptions for handoff hints (phrases like "proceed with", "next step",
"feeds into", "then invoke", "follow up with"). Build a list of detected workflows:

```
DETECTED WORKFLOWS:
  Feature Development: /brainstorm -> /writing-plans -> /executing-plans -> /implement -> /branching
  Bug Fix: /systematic-debugging -> /fix-loop -> /auto-verify -> /branching
  Code Review: /request-code-review -> /receive-code-review -> /branching
  (workflows above are derived from skill descriptions — they update automatically)
```

These workflows MUST be derived by reading skill descriptions for handoff references,
not from a hardcoded list. If a new skill mentions "after this, invoke /deploy", that
link appears automatically.

---

