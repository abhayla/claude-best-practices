# STEP 4: Document Pitfalls

### 4.1 Pitfall Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Environment** | Setup/config surprises | "Docker must be running before test suite — no helpful error if it isn't" |
| **Documentation lies** | Docs that are wrong or misleading | "API docs say rate limit is 1000/min — actual limit is 100/min" |
| **Hidden dependencies** | Implicit requirements | "Build script assumes Node 18+ — fails silently on Node 16" |
| **Ordering traps** | Things that must happen in sequence | "Must run migrations before seeding — seed script doesn't check" |
| **Naming confusion** | Misleading names in codebase | "`user.active` doesn't mean currently online — it means account not deleted" |
| **Side effects** | Unexpected consequences of actions | "Don't modify config.yml directly — overwritten by build script on deploy" |
| **Timing issues** | Race conditions or sequencing bugs | "CI flakes if test A and test B run in parallel — shared temp directory" |
| **Data quirks** | Unexpected data characteristics | "Customer names can contain emoji — breaks CSV export if not handled" |

### 4.2 Pitfall Format

For each pitfall:

```markdown
**Pitfall:** [Short description]
**Context:** [When/how you encountered it]
**Impact:** [What went wrong or how much time was wasted]
**Prevention:** [How to avoid it next time]
**Permanent fix:** [If applicable — how to fix the root cause so it's not a pitfall anymore]
```

### 4.3 Real-World Examples

Here are examples of well-documented pitfalls to use as templates:

```markdown
