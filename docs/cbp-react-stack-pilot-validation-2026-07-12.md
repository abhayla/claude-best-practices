# cbp-react-stack pilot validation — 2026-07-12

Evidence record for the **first Tier-2 stack pack** of the #187 distribution pilot
(owner-approved improvement-loop cycle 5): `cbp-react-stack` v0.1.0, the hub's **9th**
marketplace plugin — the React-family toolbox (vitest-dev, jest-dev, nextjs-dev,
react-test-patterns, react-native-dev, react-native-e2e).

## Why React first

Fleet evidence (`config/repos.yml`): 3 of 5 enrolled downstream repos are React-family
(IPODhan + RealFuelPricesinIndia on Next.js, calculatekaro on Vite+React) vs 2 Python — the
pack upgrades the majority of real downstream users.

## Boundary decisions

- **The `react-nextjs` rule is excluded:** plugins cannot ship auto-loaded `rules/*.md`
  (#187 spike answer) — path-scoped rules stay on the provisioning path.
- **No React agents:** none exist in `core/` (the `react-fixer-agent` token in older docs is
  not a real file); nothing to ship.
- **A toolbox is parts, not process:** pairs with `cbp-build-test-workflows` — documented in
  the README and proven by the composition E2E below.

## Validation evidence (all gates green, 2026-07-12)

| Gate | Result |
|---|---|
| `claude plugin validate` | PASS |
| `validate_plugin_cleanroom.py cbp-react-stack` | **PASS** — all 6 skills served from the plugin alone |
| Full hub gate (dedup, secret scan, quality gate, pytest) | PASS — 1787 passed / 0 failed |
| **Real two-plugin composition E2E** | PASS — see method (the pilot's most complete downstream test yet) |

### Composition-E2E method (workflow plugin + stack pack together)

Fresh Vite + React + TS + Vitest project (`D:/Abhay/VibeCoding/cbp9-test`, scaffolded with
`npm create vite`, own `git init`, **no `.claude/`**), containing a `Counter` component and
two Testing-Library tests — one of which **genuinely failed** with the classic framework
gotcha: without `globals: true` or a `setupFiles` cleanup, React Testing Library never
registers `afterEach(cleanup)`, so renders leak across tests and the second test found two
buttons.

Isolated `CLAUDE_CONFIG_DIR` → marketplace add → **both** `/plugin install
cbp-build-test-workflows` and `/plugin install cbp-react-stack` → headless run of the
installed `test-pipeline`. Observed:

1. **Cross-plugin skill resolution works:** the pipeline (from one plugin) invoked
   `cbp-react-stack:vitest-dev` and `cbp-react-stack:react-test-patterns` (from the other)
   by name.
2. **Bundled default config fallback** engaged again (no project pipeline config).
3. **Root-cause fix, not symptom patch:** the fix-loop diagnosed the missing test-isolation
   configuration (not the query, not the component) and applied the canonical stack-pack
   fix — `src/test/setup.ts` with `afterEach(cleanup)` + `@testing-library/jest-dom/vitest`
   wiring, registered via `setupFiles` in `vitest.config.ts`.
4. **Independently re-verified** after the run: `npx vitest run` → 2/2 passed; the setup
   file and config edit exist on disk as described. Verdict: `PASSED / ci_gate PASSED`.

Status vocabulary: **serve-validated AND composition-install-exercised on day one**; formal
graduation-sweep entry can be added at the next sweep.

## G6 milestone

With this plugin the marketplace holds **9 plugins — the G6 DoD count bar (≥9)**. Remaining
#187 expansion: `cbp-python-stack` (covers the 2 FastAPI repos), then the `recommend.py` →
plugin-recommender repurpose (end-state).
