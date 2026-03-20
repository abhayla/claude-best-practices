# STEP 6: Optimize Execution

### 6a. Recommend parallelization

- **Python:** Check for `pytest-xdist` (`pip show pytest-xdist`). If not installed, recommend `pip install pytest-xdist` and `python -m pytest -n auto` (uses all CPU cores). For CI, use a fixed worker count: `-n 4`.
- **JavaScript:** Jest parallelizes per-file by default. For tuning: `npx jest --maxWorkers=4` or `--maxWorkers=50%`.

### 6b. Fixture scoping improvements

**Python:** Audit fixture scopes and recommend promotions:

| Current scope | Candidate for promotion when... | New scope |
|--------------|--------------------------------|-----------|
| `function` (default) | Fixture is read-only and expensive to create | `module` or `session` |
| `module` | Fixture is identical across all modules | `session` |

NEVER promote fixtures that modify state — mutable fixtures MUST stay `function`-scoped.

### 6c. Test splitting for CI

Recommend splitting test suites into parallel CI jobs by type (unit / integration / e2e).
For large suites, recommend sharding:
- **Python:** `pytest --splits N --group G` (pytest-split) or `pytest-xdist`
- **JavaScript:** `jest --shard=1/3`, `jest --shard=2/3`, `jest --shard=3/3`

---

