# Changelog

All notable pattern additions, updates, and removals.

## [Unreleased]

### 2026-06-10 — Tier 3: new Hono + Prisma + Vuetify-E2E stack rules from firekaro-planner

Tier 3 of the hub-promotion pass (see `plans/hub-promotion-firekaro.md`). New dependency-gated stack rules + a `vue.md` enrichment. Source: `project:firekaro-planner`. Wiring: `recommend.py` `DEP_PATTERN_MAP` (hono→hono-conventions, prisma→prisma-conventions, vuetify→vue-e2e) + `RESOURCE_STACK_REQUIREMENTS` empty-set gates (mirroring `bun-elysia`). No `bootstrap.py` `STACK_PREFIXES` change needed — these detect via project dependencies, not stack prefixes.

- **added** rule `hono-conventions` (globs: server/api TS) — `new Hono()` + global auth + `export default`; inline Zod (`.partial()` updates); `findFirst` ownership; POST for state-changing actions; discriminated `{success,data}` response envelope; opt-in pagination on `?page=`; rate-limit middleware factory. Seeds a `hono-*` rule set (hub previously had none).
- **added** rule `prisma-conventions` (globs: schema.prisma + prisma TS) — cuid PKs + timestamps; `onDelete: Cascade` + `@@index`; `findFirst` (not `findUnique`) for ownership; `upsert` singletons; `Promise.all` parallel reads; dev-mode `globalThis` client singleton. Seeds a `prisma-*` rule set.
- **added** rule `vue-e2e` (globs: E2E) — Vuetify + Playwright: `networkidle` navigation, component animation timing, `workers:1` for data-dependent suites, and the vee-validate `fill()` gotcha (`pressSequentially` + `blur`).
- **updated** rule `vue` (v1.1.0) — + `ref()`-over-`reactive()` & Pinia-vs-Vue-Query lifetime split, URL↔query-param sync, two-tier form validation, API response unwrapping (pairs with `hono-conventions` envelope).
- **changed** `recommend.py` — `DEP_PATTERN_MAP`: `prisma`/`@prisma/client` → +`prisma-conventions`, `hono` → +`hono-conventions`, new `vuetify` → `{vue, vue-e2e}`; `RESOURCE_STACK_REQUIREMENTS`: added empty-set gates for the 3 new rules.

### 2026-05-28 — Port 4 skills from mattpocock/skills (category: core, tier: must-have)

- **added** skill `improve-codebase-architecture` — Ousterhout deep-modules lens: surface architectural friction, propose deepening opportunities, produce an HTML report with before/after Mermaid diagrams, then drop into a grilling loop. References: `LANGUAGE.md`, `HTML-REPORT.md`, `DEEPENING.md`, `INTERFACE-DESIGN.md`. Adapted from upstream (no auto-open, Agent-tool dispatch at T0, references/ layout).
- **added** skill `grill-with-docs` — docs-aware grilling session: one question at a time, challenges plan against `CONTEXT.md` glossary + `docs/adr/`, updates docs inline. Required companion to `improve-codebase-architecture`. References: `CONTEXT-FORMAT.md`, `ADR-FORMAT.md`.
- **added** skill `zoom-out` — 3-step "go up a layer, name the surrounding modules in domain vocabulary" map. Tiny, high-value habit nudge.
- **added** skill `to-prd` — synthesize a PRD from current conversation + codebase understanding (no interview). Inverse direction of existing `/prd-parser`. Looks for deep-module opportunities during module sketching.

Source: <https://github.com/mattpocock/skills/tree/main/skills/engineering>.
