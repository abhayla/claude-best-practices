# How Claude Uses Your Skill at Runtime

Understanding the runtime model shapes every authoring decision.

## The 4-Layer Loading Model

| Layer | When Loaded | Token Cost | Implication |
|-------|-------------|------------|-------------|
| **Metadata** (name + description) | Agent startup | Always loaded | Description carries entire triggering burden |
| **SKILL.md body** | When skill becomes relevant | Competes with conversation | Every token displaces conversation history |
| **Reference files** | When Claude follows a link | On-demand only | Bundle comprehensive resources penalty-free |
| **Scripts** | When executed via Bash | Output only (not source) | Prefer scripts over inline code generation |

## Authoring Implications

1. **Description quality determines activation.** If description is vague,
   the skill never triggers — no matter how good the body is.

2. **SKILL.md competes for context.** The body shares the context window with
   conversation history, other skills' metadata, and the system prompt.
   500 lines is the budget, not a target.

3. **References are free until read.** Bundle complete API docs, extensive
   examples, large datasets in reference files. No penalty until Claude
   actually reads them.

4. **Scripts are executed, not loaded.** Only the script's OUTPUT consumes
   tokens. A 500-line validation script costs only its stdout in context.

## How On-Demand Loading Works in Practice

When a user asks about revenue, Claude reads SKILL.md, sees a pointer
to `reference/finance.md`, and reads just that file. The other reference
files (`sales.md`, `product.md`) stay on the filesystem consuming zero
context tokens:

```text
bigquery-skill/
├── SKILL.md              → loaded (points to reference/)
└── reference/
    ├── finance.md        → loaded (user asked about revenue)
    ├── sales.md          → NOT loaded (irrelevant to this query)
    └── product.md        → NOT loaded (irrelevant to this query)
```

This is why organizing by domain matters — it lets Claude load only
the relevant slice of your knowledge base.

## Execute vs Read Distinction

Make clear whether Claude should run a script or read it as reference:

- **Execute:** "Run `analyze_form.py` to extract fields" (most common)
- **Read as reference:** "See `analyze_form.py` for the extraction algorithm"
- When both are valid, default to execute — more reliable, saves context tokens.

## Visual Analysis

When inputs can be rendered as images (PDFs, UI screenshots, diagrams),
convert to images first and let Claude's vision analyze structure and layout.

```bash
python scripts/pdf_to_images.py form.pdf
```

Claude can identify field locations, layout patterns, and structural issues
visually — sometimes more effectively than parsing raw data.

## File Organization for Discovery

- **Name files descriptively:** `form_validation_rules.md` not `doc2.md`
- **Organize by domain:** `reference/finance.md`, `reference/sales.md`
- **Use forward slashes always** — even on Windows: `scripts/helper.py`
- **Test file access patterns** — verify Claude navigates your directory
  structure by testing with real requests
