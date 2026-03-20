# 13.3 Gate Decision

### 13.3 Gate Decision

| Condition | Result |
|-----------|--------|
| All non-skipped tests FAIL or ERROR (missing import) | ✅ PASS — proceed to Step 14 |
| Any test PASSES | ❌ FAIL — investigate and fix the passing test |
| Test files have syntax errors | ❌ FAIL — fix syntax errors |
| Test collection fails entirely | ❌ FAIL — fix framework configuration |

---

