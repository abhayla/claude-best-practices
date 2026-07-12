# Skill Anti-Patterns and Deprecation Workflow

Common mistakes when authoring skills, and the process for deprecating old skills.

## Deprecation Workflow

When a skill is being replaced by a better version:

1. **Add deprecation fields** to the old skill's frontmatter:
   ```yaml
   deprecated: true
   deprecated_by: replacement-skill-name
   ```

2. **Keep the deprecated skill** for 2 version cycles — downstream projects may still reference it

3. **Update the replacement skill's description** to mention it replaces the old one

4. **After 2 cycles**, remove the deprecated skill and update the registry

MUST NOT delete a skill without the deprecation lifecycle. Abrupt removal breaks downstream projects that depend on it.

---

## Common Skill Anti-Patterns

### Anti-Pattern 1: The Disguised Rule

**What it looks like:** A "skill" with no steps — just a list of do/don't instructions.

**Why it fails:** Rules load automatically, skills load on-demand. If the guidance should always be active, it belongs in `.claude/rules/`, not `.claude/skills/`.

**Fix:** Move it to `core/.claude/rules/{name}.md` with appropriate `globs:` frontmatter.

### Anti-Pattern 2: The Vague Advisor

**What it looks like:** Steps contain phrases like "consider the implications", "think carefully about", "ensure quality".

**Why it fails:** Claude cannot execute vague instructions reliably. "Consider" is not an action — "Run X and check the output for Y" is.

**Fix:** Replace every vague phrase with a concrete action, command, or decision table.

### Anti-Pattern 3: The Kitchen Sink

**What it looks like:** A skill with 12+ steps that tries to handle every possible scenario.

**Why it fails:** Long skills exceed useful context. Claude loses track of where it is in the process. Users lose patience.

**Fix:** Split into 2-3 focused skills, or use a primary skill that delegates to sub-skills.

### Anti-Pattern 4: The Trigger Hog

**What it looks like:** Triggers include broad terms like "help", "fix", "code", "build".

**Why it fails:** The skill activates for unrelated requests, annoying users and wasting time.

**Fix:** Use specific, multi-word triggers. Test by asking: "Would someone say this ONLY when they want this specific skill?"

### Anti-Pattern 5: The Copy-Paste Trap

**What it looks like:** Two skills that share 70%+ of their steps, with minor variations.

**Why it fails:** Maintenance burden doubles. Fixes to shared logic must be applied twice. They drift apart over time.

**Fix:** Consolidate into one skill with modes (see `skill-factory` for an example of mode-based skills).

### Anti-Pattern 6: The Unverified Optimist

**What it looks like:** A skill that performs actions but has no verification step. It reports success after executing commands without checking results.

**Why it fails:** Commands can fail silently. Files can be written with wrong content. Tests can be skipped. Without verification, the skill produces false confidence.

**Fix:** Every skill that modifies state MUST have a verification step that checks the actual outcome.

### Anti-Pattern 7: The Tool Hoarder

**What it looks like:** `allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill WebFetch WebSearch"`

**Why it fails:** Listing every tool signals to Claude that all are expected to be used, increasing the chance of unnecessary actions. It also makes the skill harder to reason about.

**Fix:** List only the tools actually used in the skill's steps. A read-only analysis skill should NOT include `Write` or `Edit`.

### Anti-Pattern 8: The Missing Handoff

**What it looks like:** A skill that ends with "Done!" but does not tell the user what to do next.

**Why it fails:** Skills are often part of larger workflows. Without a handoff, the user has to figure out the next step themselves.

**Fix:** End with a clear next-step recommendation: "Proceed with `/implement`" or "Review the report and decide whether to fix or defer."

### Anti-Pattern 9: The Backslash Bug

**What it looks like:** File paths in skill content use backslashes:
`scripts\helper.py`, `reference\guide.md`

**Why it fails:** Claude may interpret backslashes as escape characters
or generate OS-specific paths. Forward slashes work on all platforms.

**Fix:** Always use forward slashes: `scripts/helper.py`, `reference/guide.md`.
This applies to paths in SKILL.md body, reference files, and script arguments.

