# STEP 8: Diff-Aware Analysis Patterns

### 8.1 New Files (Added)

For files with status `A`:

1. **Full file scan** — apply all applicable rules to every line
2. **Structure check** — verify the file follows project conventions:
   - Has required file header/license if project uses one
   - Follows naming convention (file name matches class/module name)
   - Has appropriate imports organized per project convention
3. **Boilerplate check** — if the file looks like it was copied from another file, flag unchanged placeholder text (e.g., "TODO: replace this")

### 8.2 Modified Files (Changed Lines Only)

For files with status `M`:

1. **Changed lines only** — apply pattern rules to added/modified lines only
2. **Context-aware rules** — for rules that need surrounding code (e.g., "must be in try/except"), read 10 lines of context around each changed line
3. **Removed code check** — if a function/class was removed, verify no other changed files still reference it
4. **Changed signature check** — if a function signature was modified, verify all callers in changed files use the new signature

### 8.3 Deleted Files

For files with status `D`:

1. **Dangling reference check** — search all other changed files for imports or references to the deleted file
2. **No content analysis** — do not apply code quality rules to deleted files

```bash
