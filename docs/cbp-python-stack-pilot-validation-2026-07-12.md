# cbp-python-stack pilot validation — 2026-07-12

Evidence record for the **second Tier-2 stack pack** (owner-approved improvement-loop
cycle 7a): `cbp-python-stack` v0.1.0, the hub's **10th** marketplace plugin — pytest-dev,
fastapi-run-backend-tests, fastapi-db-migrate, fastapi-deploy + fastapi-api-tester-agent,
fastapi-database-admin-agent. Covers the 2 FastAPI repos in the enrolled fleet (KKB,
AlgoChanakya).

## Boundaries

- `fastapi-backend` / `fastapi-database` rules stay provisioned (plugins can't ship rules).
- Pairs with `cbp-build-test-workflows`; mirrors the `cbp-react-stack` recipe.

## Validation evidence (all gates green, 2026-07-12)

| Gate | Result |
|---|---|
| `claude plugin validate` | PASS |
| `validate_plugin_cleanroom.py cbp-python-stack` | **PASS** — all 4 skills served from the plugin alone |
| Full hub gate | PASS — 1787 passed / 0 failed |
| **Composition E2E (with preserved evidence, per the 2026-07-12 graduation lesson)** | PASS — see method |

### Composition-E2E method

Fresh FastAPI project (`D:/Abhay/VibeCoding/cbp10-test`: items API + TestClient tests in a
venv, own `git init`, no `.claude/`) with a **genuine REST-convention bug committed**: the
POST route returned 200 while the test asserted 201. Isolated `CLAUDE_CONFIG_DIR`
(**preserved** at `%LOCALAPPDATA%/Temp/claude/grad-python-cfg`, credentials scrubbed) →
install of BOTH `cbp-build-test-workflows` and `cbp-python-stack` → headless installed
`test-pipeline` run with the transcript saved
(`cbp10-test/graduation-transcript.jsonl` — its init event lists both plugins with
marketplace sources).

Observed: bundled default config fallback engaged; the pipeline used the stack pack's
skills; the fix-loop made the correct **root-cause judgment call** — per REST convention it
fixed the *application* (`@app.post("/items", status_code=201)`), not the test; verdict
PASSED / ci_gate PASSED. Independently re-verified after the run: `pytest` → **2/2 passed**;
`git diff` shows exactly the one-line app fix.

Status: serve-validated AND composition-install-exercised with graduation-grade preserved
evidence on day one.

## #187 remaining

Only the end-state is left: the `recommend.py` → plugin-recommender repurpose (cycle 7b).
