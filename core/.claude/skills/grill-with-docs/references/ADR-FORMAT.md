# ADR Format

ADRs live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.

Create the `docs/adr/` directory lazily — only when the first ADR is needed.

For multi-step ADR lifecycle work (supersession, deprecation, indexing, batch authoring), delegate to the hub's `/adr` skill. This file documents the minimal in-grilling format only.

## Template

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

That's it. An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why* — not in filling out sections.

## Optional Sections

Add these only when they add load-bearing information that the 1–3 sentence summary cannot carry:

- **Status** — `Proposed` / `Accepted` / `Deprecated` / `Superseded by ADR-NNNN`
- **Context** — the constraints or pressures that forced the decision
- **Alternatives considered** — what else was on the table, and one sentence per alternative on why it lost
- **Consequences** — second-order effects, both positive and negative

If the 3-sentence summary already captures all of these, do not pad with empty section headers.

## When to Promote a Note into an ADR

In a grilling session, only offer to record an ADR when ALL THREE hold:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, the decision belongs in code comments, a commit message, or nowhere at all — not in `docs/adr/`.
