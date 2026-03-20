# 10.2 JavaScript/TypeScript (Stryker)

### 10.2 JavaScript/TypeScript (Stryker)

```json
// stryker.conf.json
{
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts"],
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 50
  }
}
```

