# cbp-build-test-workflows pilot validation — 2026-07-12

Evidence record for **#187 cluster 2** (owner-approved improvement-loop cycle 3):
`cbp-build-test-workflows` v0.1.0, the hub's 7th marketplace plugin — `development-loop` +
`test-pipeline` with their universal dispatch closure (15 sub-skills, 7 worker agents).

## Boundary decisions (this cluster's load-bearing calls)

- **Stack-pack boundary enacted:** `pytest-dev`, `jest-dev`, `vitest-dev`,
  `fastapi-run-backend-tests`, `fastapi-api-tester-agent` are dispatch targets of
  `test-pipeline` but are **excluded** — they are per-stack (Tier-2) and stay provisioned by
  stack detection. The downstream E2E (below) proves the pipeline degrades gracefully without
  them (universal `python -m pytest` path).
- **Companion, not duplicate:** `code-review-workflow` (ships in `cbp-workflows`) and
  `debugging-loop` (ships in `loop-engineering`) are direct dispatch targets but whole
  workflows are never re-shipped across plugins; the README declares the companion installs.
  Shared **sub-skills** directly dispatched (e.g. `fix-loop`, `review-gate`) ARE included —
  the cycle-1 self-containment rule (namespaced, cannot collide).
- **Bundled default config (new pattern this cluster):** the hub's `test-pipeline` BLOCKs
  when `.claude/config/test-pipeline.yml` is absent. An installed plugin can't assume
  provisioned config, so the plugin copy ships `test-pipeline.default.yml` inside the skill
  directory and its STEP 2 is patched to fall back to it (project config, when present,
  always wins). This is the first deliberate plugin-copy divergence from the core template —
  documented here and in the README.

## Validation evidence (all gates green, 2026-07-12)

| Gate | Result |
|---|---|
| `claude plugin validate` | PASS |
| `validate_plugin_cleanroom.py cbp-build-test-workflows` | **PASS** — all 17 skills served from the plugin alone |
| Full hub gate (dedup, secret scan, quality gate, pytest) | PASS — 1787 passed / 0 failed |
| **Real second-project install + E2E** | PASS — see method |

### Second-project method

Fresh throwaway project (`D:/Abhay/VibeCoding/cbp7-test`: `pricing.py` + a 3-test pytest
suite, own `git init`, **no `.claude/` at all**). Isolated `CLAUDE_CONFIG_DIR` →
`claude plugin marketplace add` → `claude plugin install cbp-build-test-workflows@claude-best-practices`
(v0.1.0, enabled) → headless run of the installed `test-pipeline`.

Observed, in order:
1. **Config fallback proven:** no project `test-pipeline.yml` → the skill used the bundled
   `test-pipeline.default.yml` (schema 2.0.0, all keys) instead of BLOCKing.
2. **Concurrency guard proven (accidental bonus):** the first headless attempt died on a
   transient API drop after acquiring the pipeline lock; the retry correctly refused with
   `PIPELINE_IN_PROGRESS` (lock age < 90-min budget) and wrote the BLOCKED verdict — then the
   `--force` remediation overrode the stale lock exactly as the skill prescribes.
3. **Pipeline E2E:** SCOUT classified 3 tests (functional-only); WAVE 1 ran them via the
   universal `python -m pytest` path (no stack packs installed — graceful degradation
   proven); JOIN reconciled 3/3, `PASSED / ci_gate PASSED`; lock released; evidence under
   `test-evidence/` + `test-results/pipeline-verdict.json`.

Status vocabulary: **serve-validated AND second-project-install-exercised on day one**;
formal graduation-sweep entry (skeptic refutation pass) can be added at the next sweep.

## Remaining #187 expansion (future cycles)

1. Learning + session clusters (respecting the branch-lifecycle overlap rule).
2. Repurpose `recommend.py` from copy-provisioner to plugin recommender (#187 end-state) —
   including recommending stack packs alongside these workflow plugins.
