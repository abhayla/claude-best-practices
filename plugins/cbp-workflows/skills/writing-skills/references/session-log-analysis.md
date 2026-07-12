# STEP 3: Session Log Analysis

### 3.1 Scan for Repeated Patterns

Review conversation history for multi-step sequences performed 2+ times:
1. **Steps that worked** — action sequence that led to success
2. **Corrections you made** — where you steered the agent's approach
3. **Input/output formats** — data shape going in and out
4. **Context you provided** — project-specific facts the agent didn't know
5. **Repeated tool call sequences** — same 3+ calls in same order
6. **Repeated file access patterns** — same files across tasks

### 3.1b Synthesize from Project Artifacts

**Warning:** Do NOT generate a skill from LLM general knowledge alone — the result is vague procedures ("handle errors appropriately"). Always ground in project-specific material:

- Internal documentation, runbooks, and style guides
- API specifications, schemas, and configuration files
- Code review comments and issue trackers
- Version control history, especially patches and fixes
- Real-world failure cases and their resolutions

### 3.2 Classify Candidates

For each detected pattern, classify it:

| Pattern | Times Seen | Steps | Parameterizable? | Skill Candidate? |
|---------|-----------|-------|-------------------|-------------------|
| {description} | {N} | {count} | Yes/No | Strong/Weak/No |

A **strong candidate** has:
- 3+ steps in a consistent order
- Appeared 2+ times in the session
- Variable parts that can be parameterized (file names, feature names, etc.)
- Not already covered by an existing skill

A **weak candidate** has:
- Only 2 steps, or appeared only once but is clearly reusable
- Investigate further before creating a skill

### 3.3 Present Findings to User

Present findings conversationally:

```
I noticed you performed this workflow 3 times this session:

  1. Search for files matching a pattern in src/
  2. Read each file and extract the interface definition
  3. Generate a mock implementation
  4. Write the mock to tests/mocks/

Want me to create a /generate-mock skill for this?
```

Wait for user approval before creating the skill. If approved, proceed to Step 2 with the extracted pattern as the starting point, parameterizing the variable parts (file pattern, source directory, output directory).

---

