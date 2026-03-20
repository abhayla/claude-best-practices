# STEP 9: Summary

## STEP 9: Summary

Print a summary showing both hub provisioning and synthesis results.

**Read `synthesis-config.yml`** to determine sharing status.

**If sharing is OFF (default):**

```
Provision complete:

Hub patterns:
  Must-have:     [N] new patterns
  Improved:      [N] hub upgrades to existing patterns
  Nice-to-have:  [N] optional (checkbox PR created in remote mode)
  Skipped:       [N]
  CLAUDE.md:     created|updated|appended|skipped
  settings.json: created|merged|skipped

Synthesized patterns:
  Rules generated:    [N]
  Skills generated:   [N]
  Agents generated:   [N]
  Skipped (overlap):  [N] (covered by hub patterns)
  Skipped (low conf): [N]

All patterns are local — nothing has been shared.

╭─ Synthesize Flywheel ──────────────────────────────────────────╮
│                                                                 │
│  Your patterns can improve over time via the hub, but it's a    │
│  two-way exchange:                                              │
│                                                                 │
│  • Share ON  → hub can learn from your patterns, AND you        │
│                receive new/improved patterns from the hub        │
│  • Share OFF → fully standalone, no data leaves, no updates     │
│                arrive (this is the default)                      │
│                                                                 │
│  To opt in:                                                     │
│    Set allow_hub_sharing: true in .claude/synthesis-config.yml  │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
```

**If sharing is ON:**

```
Provision complete:

Hub patterns:
  Must-have:     [N] new patterns
  Improved:      [N] hub upgrades to existing patterns
  Nice-to-have:  [N] optional (checkbox PR created in remote mode)
  Skipped:       [N]
  CLAUDE.md:     created|updated|appended|skipped
  settings.json: created|merged|skipped

Synthesized patterns:
  Rules generated:    [N]
  Skills generated:   [N]
  Agents generated:   [N]
  Skipped (overlap):  [N] (covered by hub patterns)
  Skipped (low conf): [N]

Hub sharing is ON — your patterns contribute to the hub, and you receive updates.
```

**If `--skip-hub` was set,** omit the "Hub patterns" section entirely.

**If `--skip-synthesis` was set,** omit the "Synthesized patterns" section entirely.

**If `--update` mode, also show:**

```
  Updated: [N] (stale patterns refreshed)
  New:     [N] (new conventions detected)
  Removed: [N] (conventions no longer present in codebase — files left for manual review)
```

**If `--repo` mode, also show:**

```
  PR created: https://github.com/owner/name/pull/[N]
  Branch:     synthesize-project/[date]

  The project owner should review the PR and merge patterns they agree with.
```

---

