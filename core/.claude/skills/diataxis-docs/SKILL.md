---
name: diataxis-docs
description: >
  Organize project documentation into the Diataxis framework: tutorials, how-to guides,
  reference, and explanation. Audits existing docs, classifies them into the four categories,
  identifies gaps, generates templates for missing categories, and restructures the docs
  directory with a unified index.
triggers:
  - diataxis
  - diataxis-docs
  - organize docs
  - documentation structure
  - docs framework
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "[docs-directory-path] [--audit-only] [--skip-templates]"
version: "1.0.0"
type: workflow
---

# Diataxis Documentation Organization

Restructure project documentation into the four Diataxis categories. Audit what exists,
classify it, fill gaps, and produce a navigable docs directory.

**Target:** $ARGUMENTS

---

## The Four Diataxis Categories

| Category | Orientation | Purpose | User mindset |
|----------|-------------|---------|--------------|
| **Tutorials** | Learning-oriented | "Follow along to learn" | "I want to learn" |
| **How-to guides** | Task-oriented | "How to solve a specific problem" | "I need to do X" |
| **Reference** | Information-oriented | "Technical description of the machinery" | "I need to look up Y" |
| **Explanation** | Understanding-oriented | "Why things work this way" | "I want to understand why" |

**Key distinctions:**
- **Tutorial vs How-to**: Tutorials teach by doing (guided lesson); how-to guides solve a specific problem (recipe).
- **Reference vs Explanation**: Reference describes what things are (API signatures, config options); explanation describes why they exist.

---

## STEP 1: Audit Existing Documentation

Scan the project for all documentation files.

```bash
find . -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) \
  | grep -iv "node_modules\|vendor\|\.git\|dist\|build" | sort
```

For each file, record: file path, title, line count, and preliminary category (tutorial / how-to / reference / explanation / mixed). Output as a table before proceeding.

---

## STEP 2: Classify Into Four Categories

| Signal | Likely category |
|--------|----------------|
| Step-by-step with "you will learn" / "by the end" language | **Tutorial** |
| Numbered steps solving a specific problem, assumes prior knowledge | **How-to guide** |
| API docs, config tables, CLI flag lists, schema definitions | **Reference** |
| "Why we chose X", architecture decisions, design rationale | **Explanation** |
| Mixed content spanning multiple categories | **Needs splitting** |

If a document spans multiple categories, split it into separate files and cross-link them.

---

## STEP 3: Identify Gaps

| Category | Minimum expected |
|----------|-----------------|
| **Tutorials** | At least 1 getting-started tutorial |
| **How-to guides** | Guides for common tasks (deploy, debug, add a module) |
| **Reference** | API / config / CLI reference |
| **Explanation** | Architecture and design rationale |

List each gap with priority: **high** (blocks onboarding), **medium** (frequently asked), **low** (nice to have). If `--audit-only` is set, stop here.

---

## STEP 4: Generate Templates

Skip if `--skip-templates` is set. Create `_TEMPLATE.md` in each category directory.

### Tutorial template (`docs/tutorials/_TEMPLATE.md`)

Sections: Title, What you will learn (outcomes list), Prerequisites, Steps (numbered with explanation + code), What you learned (recap), Next steps (links to how-to/reference).

### How-to guide template (`docs/how-to/_TEMPLATE.md`)

Sections: Title ("How to [task]"), Problem (one sentence), Prerequisites, Steps (numbered actions), Verification (confirm success), Troubleshooting (symptom/cause/fix table), See also.

### Reference template (`docs/reference/_TEMPLATE.md`)

Sections: Title ("[Component] Reference"), Overview (one paragraph), API/Config/CLI entries (field tables: type, default, required, description), Examples (minimal code), See also.

### Explanation template (`docs/explanation/_TEMPLATE.md`)

Sections: Title ("[Topic]: Why and How"), Context (what prompted this), Background (history/constraints), How it works (conceptual, not step-by-step), Design decisions (decision/alternatives/rationale table), Trade-offs, Further reading.

---

## STEP 5: Restructure Docs Directory

### Target structure

```
docs/
├── index.md
├── tutorials/
│   ├── _TEMPLATE.md
│   └── getting-started.md
├── how-to/
│   ├── _TEMPLATE.md
│   └── deploy.md
├── reference/
│   ├── _TEMPLATE.md
│   ├── api.md
│   └── configuration.md
└── explanation/
    ├── _TEMPLATE.md
    └── architecture.md
```

### Migration steps

1. Create subdirectories: `mkdir -p docs/tutorials docs/how-to docs/reference docs/explanation`
2. Move each classified document to its category directory using `git mv`
3. Rename files for clarity (e.g., `ARCHITECTURE.md` becomes `docs/explanation/architecture.md`)
4. Update all internal cross-references and links
5. Place templates in each directory
6. Verify no broken links: scan for markdown link targets that no longer resolve

---

## STEP 6: Create Index

Generate `docs/index.md` with four sections mapping to Diataxis categories:

- **Learn** — links to tutorials (for newcomers)
- **Solve** — links to how-to guides (for practitioners)
- **Look up** — links to reference docs (for implementers)
- **Understand** — links to explanation docs (for the curious)

Each section uses a table with document title and one-line description.

---

## Migration Guide: Monolithic Docs to Diataxis

For projects with a single large README or monolithic doc:

1. Read the entire document and tag each section with its Diataxis category
2. Extract tutorials — "Getting Started", "Quick Start", "Your First X"
3. Extract how-to guides — "How to...", "Deploying", "Configuring"
4. Extract reference — API tables, config option lists, CLI usage
5. Extract explanation — "Architecture", "Design", "Why we..."
6. Leave a slim README pointing to `docs/index.md`
7. Use `git mv` to preserve history

---

## MUST DO

- MUST classify every document into exactly one category — if it spans two, split it
- MUST create the four-directory structure even if some categories start empty
- MUST update all internal links after moving files
- MUST keep a slim project-root README pointing to `docs/index.md`
- MUST use `git mv` when moving files to preserve history
- MUST cross-link between categories (tutorials link to reference, how-to links to explanation)

## MUST NOT DO

- MUST NOT put a document in multiple categories — pick the primary purpose, cross-link instead
- MUST NOT delete the project-root README — replace its content with a summary and docs link
- MUST NOT create empty documents without a title and purpose — use templates instead
- MUST NOT mix tutorial content into reference pages — tutorials guide learning, reference serves lookup
- MUST NOT force all four categories to be filled immediately — use the gap report to prioritize
- MUST NOT rename files arbitrarily — use descriptive, lowercase, hyphenated names matching the content

## See Also

- `/api-docs-generator` — Generates OpenAPI reference docs that belong in the `docs/reference/` Diataxis category
- `/changelog-contributing` — Generates CHANGELOG.md and CONTRIBUTING.md — classify these as reference docs in the Diataxis index
- `/doc-structure-enforcer` — Enforce stage-based folder structure before or after Diataxis restructuring
- `/doc-staleness` — Run after restructuring to verify no references were broken during the move
- `/adr` — ADRs belong in the `docs/explanation/` Diataxis category
- `docs-manager-agent` — Orchestrates broader documentation updates, delegates structural reorganization to this skill
