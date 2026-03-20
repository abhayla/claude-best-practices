# STEP 7: Validate and Write

### Local mode: write directly

3. **Write patterns** to the project's `.claude/` directory:
   - Rules → `.claude/rules/[convention-name].md`
   - Skills → `.claude/skills/[skill-name]/SKILL.md`
   - Agents → `.claude/agents/[agent-name].md`

### Remote mode (`--repo`): create SEPARATE PRs per tier

**CRITICAL:** ALWAYS create separate PRs for each tier. NEVER combine tiers into a single PR. NEVER skip a tier. NEVER make arbitrary decisions about which resources to include or exclude. Every confirmed pattern MUST appear in exactly one PR based on its tier.

**Tier classification for synthesized patterns:**
- **Must-have (high confidence):** Patterns with `confidence: high` — correctness/safety conventions that prevent bugs
- **Nice-to-have (medium confidence):** Patterns with `confidence: medium` — consistency/style conventions
- **Enhanced (hub-improved):** Patterns where a hub pattern exists but the project-specific version adds value

3. **For EACH tier with patterns**, create a separate branch and PR:

   ```bash
   # Branches — one per tier
   # synthesize-project/must-have     — high-confidence patterns
   # synthesize-project/nice-to-have  — medium-confidence patterns
   # synthesize-project/enhanced      — project refinements of hub patterns

   DEFAULT_SHA=$(gh api repos/owner/name/git/refs/heads/main --jq '.object.sha')
   gh api repos/owner/name/git/refs \
     -f ref="refs/heads/synthesize-project/TIER_NAME" \
     -f sha="$DEFAULT_SHA"
   ```

4. **Push pattern files** to the appropriate tier branch.

5. **Push `synthesis-config.yml`** to the must-have branch if it doesn't exist.

6. **Create a PR for EACH tier** (must-have, nice-to-have, enhanced). Skip tiers with zero patterns. Each PR title MUST include the tier name and count. Nice-to-have PR should use checkboxes for individual pattern selection.

