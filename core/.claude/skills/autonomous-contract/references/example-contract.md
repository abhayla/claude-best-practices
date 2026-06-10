# Example contract (a worked, neutral build contract)

A short, concrete example of a filled-in contract — neutral domain (a generic
"tags" feature on an `items` resource). Real contracts are usually longer; this
shows the shape and density, not the maximum size. The §0.1/§0.2/§0.3 and
verification blocks are abbreviated here with a pointer — in a real contract they
are pasted in full from `baked-in-rules.md`.

---

```markdown
# Contract: add tags to items (API + list UI)

**Executor:** /goal   ·   **Created:** 2026-06-10
**Mission:** Let a user attach freeform tags to an item and filter the items
list by tag. Done = tags persist via the API, render on the item row, and the
list filters by a selected tag — verified end-to-end on the default view.

## §0.1 Worktree isolation
[full §0.1 block from baked-in-rules.md — worktree `../app-run-item-tags`, branch
`feat/item-tags`, lock `.run-active.lock`, self-clean on success only]

## §0.2 Idempotency preflight
[full §0.2 block — ledger: docs/coverage.md; before building, grep `server/routes/items.ts`
and the schema for an existing `tags` field/route; skip what exists, build the delta]

## §0.3 Progress log
[full §0.3 block — docs/contracts/.run/2026-06-10-item-tags-PROGRESS.md]

## Scope boundary
- **In scope:** `server/routes/items.ts`, `prisma/schema.prisma`, `src/pages/ItemsList.vue`, `src/composables/useItems.ts`, `e2e/items.spec.ts`
- **Out of scope:** auth, billing, any other resource
- **Goal type:** fresh build

## Context to read first
- `server/routes/items.ts` — the existing item CRUD + response envelope helper (`apiSuccess`)
- `prisma/schema.prisma` — the `Item` model (add `tags String[]`)
- `src/composables/useItems.ts` — the TanStack query that unwraps the envelope

## Pre-made design decisions
1. Tag storage — `tags String[]` column on `Item` (not a join table). Why: small, freeform, no tag entity needed (YAGNI).
2. Filter transport — `?tag=<value>` query param synced to the URL (per vue.md URL↔query-sync). Why: deep-linkable, no new client state.
3. Create-tag UX — a Vuetify combobox on the existing item dialog; no separate screen. Why: lowest surface, reuses the form.

## Stages
### Stage A: schema + API
- **Do:** add `tags String[]` to `Item`; migrate; accept `tags` in the create/update Zod schema (`.partial()` for update); support `?tag=` filter in the list route via `where: { tags: { has: tag } }`.
- **Acceptance:** `curl` create with tags reads back the tags; `?tag=x` returns only items having `x`.
### Stage B: list UI + filter
- **Do:** render tags as chips on each item row; add a tag combobox to the item dialog; bind a tag filter to `?tag=` via a computed getter/setter.
- **Acceptance:** creating an item with a tag shows the chip after reload; selecting a tag filters the list and updates the URL.

## Verification gates
[full pointer block from baked-in-rules.md. Adapted mechanics:
 - static gates: `npm run type-check && npm run test:unit` (root) + `cd server && npm run type-check && npm run lint && npm run test:unit`
 - persistence signal: API read-back `curl http://localhost:3100/api/items/<id>` shows the tags (Stage A is a write path → persistence gate fires)
 - cross-page consumers for the sweep: ItemsList row chips + the filtered count]

## Failure-recovery budget
[full failure-budget block from baked-in-rules.md]

## Commit + push policy
- One commit per stage; Conventional Commits; branch `feat/item-tags` → PR.
- Do NOT stage unrelated untracked files in the working tree.

## Definition of Done
- [ ] An item created with tags **persists** them (API read-back confirms) and the chips **render** on its row after reload.
- [ ] Selecting a tag **filters** the list to only items having that tag AND updates the URL to `?tag=<value>`.
- [ ] Static gates green in both trees; persistence + supervisor + blind-test gates passed.
- [ ] Final report + DONE/PENDING/BLOCKED/NEXT summary written.

## Guardrails
- No new dependencies. No tag-entity table (decision 1). No synthetic data. Stay within the in-scope files.

## Authorization trail
| Fork | Decision | Why |
|---|---|---|
| tag storage | String[] column | small freeform set, YAGNI |
| filter transport | ?tag= URL param | deep-linkable, no new state |
| create-tag UX | combobox on existing dialog | lowest surface |

## References (load transitively)
- `core/.claude/rules/{supervisor-verification, independent-test-verification, output-plausibility-verification, e2e-persistence-verification, dod-verbs, bug-triage-discipline, testing, e2e-best-practices, git-worktrees, learnings-routing, hono-conventions, prisma-conventions, vue, vue-e2e}`
```
