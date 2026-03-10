# Auto-Verify Quick Checklist

Quick reference for the 8-step auto-verify algorithm.

---

## Checklist

- [ ] **Step 0: Prerequisites** — Clean screenshots, verify backend/emulator, ensure test-map fresh
- [ ] **Step 1: Identify Changes** — `git diff --name-only {base}`, filter + classify
- [ ] **Step 2: Map to Tests** — test-map.json lookup (P0), convention (P1), grep (P2), module (P3)
- [ ] **Step 2c: KB Pre-Check** — Query knowledge.db for known patterns, set strategy hints
- [ ] **Step 3: Run Tests** — Execute targeted tests, capture output to log
- [ ] **Step 4: Analyze** — Parse failures using automated diagnosis table
- [ ] **Step 5: Decide** — Pass → Step 7, Known pattern → fix, Same error 2x → fix-loop, 3x → ask user
- [ ] **Step 6: Fix + Iterate** — Auto-approved or approval checkpoint, then back to Step 3
- [ ] **Step 7: Regression** — Run adjacent tests, revert + escalate if regression found
- [ ] **Step 8: Record** — Update knowledge.db with outcomes and strategy scores

## Key Limits

| Limit | Value |
|---|---|
| Max test files per run | 20 |
| Max iterations | 5 (configurable) |
| Same error escalation | 2x → fix-loop, 3x → ask user |
| KB score auto-apply | >= 0.7 |
| KB score hint | 0.3 — 0.7 |
| Regression on failure | Revert + escalate |
