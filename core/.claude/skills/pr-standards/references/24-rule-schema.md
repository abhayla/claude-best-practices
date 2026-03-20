# 2.4 Rule Schema

### 2.4 Rule Schema

Each rule (custom or built-in) has these fields:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Unique rule identifier (kebab-case) |
| `description` | Yes | string | Human-readable explanation |
| `severity` | Yes | `critical` / `warning` / `info` | Violation severity level |
| `pattern` | Yes | regex string | Pattern to search for in changed lines |
| `check` | No | string | Additional context-aware check to perform |
| `auto-fix` | No | boolean | Whether this violation can be auto-fixed |
| `fix-pattern` | No | string | Regex pattern to match for replacement (required if auto-fix) |
| `fix-replacement` | No | string | Replacement text (required if auto-fix) |
| `languages` | No | list | Limit rule to specific file extensions |
| `exclude-paths` | No | list | Paths where this rule does not apply |
| `message` | Yes | string | Message shown when violation is detected |

---

