# STEP 7: Integrate External Sources

### 7.1 Scratchpad Integration

If `scratchpad.md` or `.claude/scratchpad.md` exists:

1. **Read the scratchpad** and identify entries from this session
2. **Extract and deduplicate:**
   - Gotchas → merge into Pitfalls section (avoid duplication)
   - Judgment calls → merge into Decisions section
   - Questions answered → include answer in relevant section
   - Questions unanswered → add to Next Steps as research items
   - File discovery notes → include in Current State if relevant
3. **Reference for depth:** Add a pointer to the scratchpad for raw details:
   > "For full exploration notes and intermediate findings, see `scratchpad.md`"
4. **Do NOT copy the entire scratchpad** — curate and summarize. The handover
   should be a refined distillation, not a raw dump.

### 7.2 Learn-n-Improve Integration

If `/learn-n-improve` was run during this session or learning files exist:

1. **Extract session learnings** from memory files (entries with today's date)
2. **Categorize learnings:**

   | Type | Example | Action |
   |------|---------|--------|
   | **Fix pattern** | "Null check needed before `.email` access on legacy users" | Include in Pitfalls + Learnings |
   | **Testing lesson** | "Mock SMTP server with `smtplib.SMTP` not `aiosmtplib`" | Include in Learnings |
   | **Skill gap** | "Need to learn project's migration framework" | Include in Next Steps as research |
   | **Process improvement** | "Run integration tests before pushing — CI is slow" | Include in Learnings |

3. **Reference learning files:**
   > "Session learnings have been saved to `.claude/memory/`. Key entries:
   > - `fix-patterns.md`: 2 new patterns added
   > - `testing-lessons.md`: 1 new lesson added"

### 7.3 Specification / Issue Integration

If working from a spec, issue, or ticket:

1. **Link to the source:** Include the issue URL, spec file path, or ticket ID
2. **Map progress:** Which requirements/acceptance criteria are met vs remaining
3. **Note deviations:** Where the implementation differs from the spec and why

```markdown
### Spec Progress: Issue #67 — Token Refresh
- [x] Implement refresh endpoint (`POST /auth/refresh`)
- [x] Validate refresh token signature
- [ ] Handle expired refresh tokens (in progress)
- [ ] Rate limit refresh requests (not started)
- [ ] Add audit logging for refresh events (not started)

**Deviation:** Spec says "return 403 for expired tokens" but the team convention
(see `src/auth/login.py`) uses 401. Using 401 for consistency — flag for review.
```

---

