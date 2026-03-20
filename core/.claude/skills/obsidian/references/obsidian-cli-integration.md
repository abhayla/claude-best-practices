# STEP 4: Obsidian CLI Integration

### File Operations
```bash
obsidian read "$VAULT" "path/to/note.md"
obsidian create "$VAULT" "path/to/note.md" --content "# Title"
obsidian append "$VAULT" "path/to/note.md" --content "New line"
obsidian prepend "$VAULT" "path/to/note.md" --content "Top line"
obsidian move "$VAULT" "old/path.md" "new/path.md"
obsidian rename "$VAULT" "path/to/note.md" "New Name"
obsidian delete "$VAULT" "path/to/note.md" --trash  # Move to .trash
```

### Daily Notes
```bash
obsidian daily-note append "$VAULT" --content "- $(date +%H:%M) Log entry"
obsidian daily-note read "$VAULT"
obsidian daily-note prepend "$VAULT" --content "## Priority Tasks"
```

### Search & Metadata
```bash
obsidian search "$VAULT" --query "search term" --format json
obsidian properties get "$VAULT" "path/to/note.md"
obsidian properties set "$VAULT" "path/to/note.md" --key status --value done
obsidian tags list "$VAULT"
obsidian tasks list "$VAULT" --incomplete
```

### Graph & Links
```bash
obsidian backlinks "$VAULT" "path/to/note.md"
obsidian unresolved-links "$VAULT"       # Find broken wikilinks
obsidian orphans "$VAULT"                 # Find unlinked notes
```

### Fallback (No CLI)

When Obsidian CLI is not available, fall back to direct file manipulation:

```bash
