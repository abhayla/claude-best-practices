# 5.5 Final Lint Pass

### 5.5 Final Lint Pass

After all cleanup:

```bash
npx eslint src/ tests/ --max-warnings=0
npx tsc --noEmit
npm test
```

All three must pass before proceeding to PR creation.

---

