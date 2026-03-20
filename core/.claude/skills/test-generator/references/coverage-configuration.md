# STEP 9: Coverage Configuration

### 9.1 Coverage Thresholds

Read coverage thresholds from these sources (in priority order):
1. **Plan file** — If Stage 2 plan specifies coverage targets, use those
2. **Project config** — `pyproject.toml` / `vitest.config.ts` existing thresholds
3. **Defaults** — Fall back to the targets below

Configure minimum coverage enforcement:

**Python (pyproject.toml):**
```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
]
```

**JavaScript (vitest.config.ts):**
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      thresholds: {
        lines: 80,
        branches: 70,
        functions: 80,
        statements: 80,
      },
    },
  },
});
```

### 9.2 Coverage Targets

| Metric | Minimum | Stretch Goal |
|--------|---------|-------------|
| Line coverage | 80% | 90% |
| Branch coverage | 70% | 85% |
| Function coverage | 80% | 90% |
| Domain layer | 90% | 95% |
| Infrastructure layer | 60% | 75% |

Domain logic (entities, use cases) MUST have higher coverage than infrastructure (DB adapters, external API clients).

---

