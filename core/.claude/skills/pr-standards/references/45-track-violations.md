# 4.5 Track Violations

### 4.5 Track Violations

Maintain a structured list of all violations found:

```
violation:
  id: V001
  rule: no-debugger
  severity: critical
  file: src/routes/users.py
  line: 45
  column: 5
  matched_text: "    debugger"
  message: "Debugger statement found. Remove before merging."
  auto_fixable: true
  fix_description: "Remove the debugger line"
  context:
    before: "    user = get_user(user_id)"
    matched: "    debugger"
    after: "    return jsonify(user)"
```

---

