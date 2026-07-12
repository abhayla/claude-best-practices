# STEP 1: Determine Authoring Mode

### 1.1 Skill Necessity Check

Before authoring, verify the skill adds value over the agent's baseline:

1. **Auto-generate 3 representative tasks** from `$ARGUMENTS` — realistic prompts a user would type within the skill's intended scope
2. **Run each task WITHOUT a skill** in a subagent (clean context)
3. **Evaluate results:**

| Result | Action |
|--------|--------|
| Agent handles all 3 well | STOP — report "skill not needed" |
| Agent struggles on 1-2 | Capture gaps — these define the skill's value. Proceed |
| Agent fails on all 3 | Strong signal — use failure patterns to drive Step 2.3 |

The gaps captured here feed directly into the skill's instructions.

### 1.2 Design Initial Evaluations

Before authoring, formalize the gaps from 1.1 into 3 eval scenarios.
These become the acceptance criteria that drive Step 2.

1. **Convert each gap into a test case:** realistic user prompt + expected behavior
2. **Establish baseline:** the without-skill results from 1.1 ARE the baseline
3. **Store scenarios** for use in Step 6 (formal evaluation)

| Gap Identified | Eval Scenario | Expected Behavior |
|---|---|---|
| {from 1.1} | {realistic prompt} | {what success looks like} |

These scenarios drive what to include in Step 2 — write ONLY what's needed
to pass them. Resist comprehensive documentation until evals confirm value.

### 1.3 Update Mode — Modify an Existing Skill

When the target skill already exists, follow this workflow instead of creating from scratch.

1. **Read the existing skill** — load the full SKILL.md and any references
2. **Identify what needs to change** — based on user request, conversation context, or known gaps
3. **Classify the change scope** for SemVer bump:

| Change Type | Version Bump | Examples |
|---|---|---|
| Breaking: output format change, removed steps, renamed arguments | **MAJOR** | Changing JSON output schema, removing a step |
| Additive: new optional steps, new modes, expanded examples | **MINOR** | Adding an update mode, new decision table |
| Fix: typo, wording, formatting, bug fix | **PATCH** | Fixing a code block, clarifying a step |

4. **Apply changes** — edit the existing SKILL.md using the Edit tool (not rewrite)
5. **Bump the version** in frontmatter per the classification above
6. **Skip Steps 1.1–1.2 and Steps 2–3** — the skill's value is already proven
7. **Run Steps 4–5** — validate naming, organization, and quality checklist
8. **Run Step 6** with `--baseline` flag — evaluates the update against the previous version

---

