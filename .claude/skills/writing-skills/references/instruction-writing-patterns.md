# Instruction Writing Patterns

Eight patterns for writing effective instructions within skill steps.
Use the ones that fit your task — not every skill needs all of them.

## 1. Calibrating Control

Match specificity to fragility. Freedom when flexible, prescriptive when fragile.

**Give freedom** when multiple approaches are valid — explain WHY rather than prescribing exact steps. An agent that understands purpose makes better decisions.

**Be prescriptive** when operations are fragile, consistency matters, or a specific sequence must be followed.

Most skills have a mix. Calibrate each part independently.

```markdown
## Code review (flexible — describe what to look for)
1. Check database queries for SQL injection
2. Verify authentication on every endpoint
3. Look for race conditions in concurrent code

## Database migration (prescriptive — exact sequence)
Run exactly: `python scripts/migrate.py --verify --backup`
Do not modify the command or add flags.
```

## 2. Gotchas Sections

Environment-specific facts that defy reasonable assumptions. Not general advice ("handle errors appropriately") — concrete corrections to mistakes the agent WILL make.

**Placement:** Keep gotchas in SKILL.md where the agent reads them BEFORE encountering the situation. Reference files work only with explicit triggers: "Read `references/gotchas.md` before making any database queries."

**Iterative improvement:** When an agent makes a mistake you correct, add the correction to gotchas. This is the most direct way to improve a skill over time.

```markdown
## Gotchas
- The `users` table uses soft deletes. Queries MUST include
  `WHERE deleted_at IS NULL` or results include deactivated accounts.
- User ID is `user_id` in the DB, `uid` in auth, `accountId` in billing.
  All three refer to the same value.
- `/health` returns 200 even if the database is down. Use `/ready` for
  full service health.
```

## 3. Validation Loops

Pattern: do the work → run a validator → fix issues → repeat until clean.

The validator can be a script, a test suite, a linter, or a reference document the agent checks its work against before finalizing.

```markdown
1. Make your edits
2. Run validation: `python scripts/validate.py output/`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. Only proceed when validation passes
```

## 4. Plan-Validate-Execute

For batch or destructive operations: create plan → validate against source of truth → execute only after validation passes.

The key ingredient is the validation step with actionable errors: "Field 'signature_date' not found — available: customer_name, signature_date_signed."

```markdown
1. Extract form fields → form_fields.json
2. Create field_values.json mapping each field to its value
3. Validate: `scripts/validate_fields.py form_fields.json field_values.json`
4. If validation fails, revise field_values.json and re-validate
5. Fill the form: `scripts/fill_form.py input.pdf field_values.json output.pdf`
```

## 5. Defaults Over Menus

Pick one default, mention alternatives briefly. Don't present equal options — the agent wastes time choosing.

```markdown
<!-- Bad -->
You can use pypdf, pdfplumber, PyMuPDF, or pdf2image...

<!-- Good -->
Use pdfplumber for text extraction.
For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

## 6. Procedures Over Declarations

Teach HOW to approach a class of problems, not WHAT to produce for one instance. The approach should generalize even when details are specific.

Skills CAN include specific details — output templates, constraints like "never output PII", tool-specific instructions. The point is the approach itself should be reusable.

```markdown
<!-- Declarative — only works for this exact task -->
Join `orders` to `customers` on `customer_id`, filter region = 'EMEA'

<!-- Procedural — works for any analytical query -->
1. Read schema from `references/schema.yaml` to find relevant tables
2. Join tables using the `_id` foreign key convention
3. Apply filters from the user's request as WHERE clauses
4. Aggregate numeric columns as needed
```

## 7. Bundling and Designing Scripts

**When to bundle:** Agent reinvents the same logic across test runs (chart building, format parsing, output validation). Write a tested script once, bundle in `scripts/`.

**When NOT to:** One-off logic that varies per invocation. Use version-pinned commands instead (e.g., `uvx ruff@0.8.0 check .`). When a one-off command grows complex enough that it's hard to get right on first try, move it to a tested script.

**State prerequisites** in SKILL.md ("Requires Node.js 18+", "Requires uv") rather than assuming the agent's environment has them. For runtime-level requirements, use the `compatibility` frontmatter field.

**Agentic script design:**

| Principle | Why |
|---|---|
| No interactive prompts | Agents hang on TTY input — accept via flags/env/stdin |
| `--help` with examples | Primary way agent learns the interface |
| Helpful error messages | Say what went wrong, what was expected, what to try |
| Structured output (JSON/CSV) | Data to stdout, diagnostics to stderr |
| Idempotent operations | Agents retry — "create if not exists" is safer |
| Safe defaults for destructive ops | Require `--confirm` or `--force` flags |
| Dry-run support | `--dry-run` lets agent preview before committing |
| Meaningful exit codes | Distinct codes per failure type, documented in `--help` |
| Predictable output size | Default to summary; support `--offset` for pagination |
| Input constraints | Reject ambiguous input with clear error; use enums and closed sets |

**Referencing scripts from SKILL.md:**

Use relative paths from the skill directory root. List available scripts so the agent knows they exist, then instruct the agent to run them:

```markdown
## Available scripts
- **`scripts/validate.sh`** — Validates configuration files
- **`scripts/process.py`** — Processes input data

## Workflow
1. Run validation: `bash scripts/validate.sh "$INPUT_FILE"`
2. Process results: `python3 scripts/process.py --input results.json`
```

The same relative-path convention works in `references/*.md` files — script paths in code blocks are always relative to the skill directory root.

**Self-contained scripts with inline dependencies:** For reusable logic, bundle scripts that declare their own deps inline — no separate manifest needed. Python: PEP 723 with `uv run`. Deno: `npm:` imports. Bun: version-pinned imports. Ruby: `bundler/inline`.

**Justified constants (no "voodoo constants"):** Every magic number or
configuration parameter MUST have a comment explaining WHY that value.
If you don't know the right value, how will Claude determine it?

```python
# Good — self-documenting
# HTTP requests typically complete within 30 seconds
# Longer timeout accounts for slow connections
REQUEST_TIMEOUT = 30

# Bad — magic numbers
TIMEOUT = 47  # Why 47?
RETRIES = 5   # Why 5?
```

**Solve, don't punt:** Scripts should handle error conditions explicitly
rather than failing and leaving Claude to figure it out. Provide
fallbacks, create defaults for missing files, and return clear error
messages — don't just let exceptions propagate.

**Platform awareness:** Skills on claude.ai can install packages from
npm/PyPI and pull from GitHub. Skills via the Claude API have no network
access and no runtime package installation. List required packages in
SKILL.md and note any platform constraints.

Short templates inline in SKILL.md; longer templates in `assets/` or `references/` with conditional loading.

## 8. Checklists for Progress Tracking

An explicit checklist helps the agent track progress and avoid skipping steps, especially with dependencies or validation gates.

Use when a skill has 4+ sequential steps with dependencies.

```markdown
Progress:
- [ ] Step 1: Analyze input (run `scripts/analyze.py`)
- [ ] Step 2: Create mapping (edit `config.json`)
- [ ] Step 3: Validate mapping (run `scripts/validate.py`)
- [ ] Step 4: Execute (run `scripts/execute.py`)
- [ ] Step 5: Verify output (run `scripts/verify.py`)
```

## 9. Input/Output Examples for Quality Calibration

When output quality depends on seeing the expected format, provide 2-3
input/output pairs. These calibrate Claude's understanding of "good" more
effectively than prose descriptions.

**Use when:** the skill produces formatted output (commit messages, reports,
code transformations) where style and structure matter.

```markdown
## Commit message format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
fix(reports): correct date formatting in timezone conversion

Follow this style: type(scope): description, then detailed explanation.
```

Keep examples concrete and representative. 2-3 examples is enough —
more examples increase context cost without proportional quality gain.

## 10. Conditional Workflow Routing

Guide Claude through decision points that branch to different workflows.
Use when a skill handles multiple operation types that share setup but
diverge in execution.

```markdown
## Document modification workflow

1. Determine the modification type:

   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow:
   - Use the generation library
   - Build from template
   - Export to target format

3. Editing workflow:
   - Load existing document
   - Modify in place
   - Validate after each change
```

If sub-workflows grow large (>30 lines each), push them into separate
reference files and tell Claude to read the appropriate one.

## 11. Install-Then-Use for Dependencies

When a skill requires a package, show the install command before usage.
Don't assume the package is available — Claude may be in a fresh environment.

```markdown
Install required package: `pip install pypdf`

Then use it:
\`\`\`python
from pypdf import PdfReader
reader = PdfReader("file.pdf")
\`\`\`
```

For runtime-level dependencies (Node.js, Python, etc.), state them in
SKILL.md prerequisites rather than inline: "Requires Python 3.10+."
For platform-specific availability, note: "Available on claude.ai (can
install from PyPI). Not available via Claude API (no network access)."
