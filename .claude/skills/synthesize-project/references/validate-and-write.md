# STEP 7: Validate and Write

### Local mode: write directly

1. **Write patterns** to the project's `.claude/` directory:
   - Rules → `.claude/rules/[convention-name].md`
   - Skills → `.claude/skills/[skill-name]/SKILL.md`
   - Agents → `.claude/agents/[agent-name].md`

### Remote mode (`--repo`): create SEPARATE PRs per tier

**CRITICAL:** ALWAYS create separate PRs for each tier. NEVER combine tiers into a single PR. NEVER skip a tier. NEVER make arbitrary decisions about which resources to include or exclude. Every confirmed pattern MUST appear in exactly one PR based on its tier.

**Tier classification for synthesized patterns:**
- **Must-have (high confidence):** Patterns with `confidence: high` — correctness/safety conventions that prevent bugs
- **Nice-to-have (medium confidence):** Patterns with `confidence: medium` — consistency/style conventions
- **Enhanced (hub-improved):** Patterns where a hub pattern exists but the project-specific version adds value

2. **For EACH tier with patterns**, create a separate branch and PR:

   ```bash
   # Branches — one per tier
   # synthesize-project/must-have     — high-confidence patterns
   # synthesize-project/nice-to-have  — medium-confidence patterns
   # synthesize-project/enhanced      — project refinements of hub patterns

   # Use the default branch captured in Step 0 (gh repo view --json defaultBranchRef)
   DEFAULT_BRANCH=$(gh repo view owner/name --json defaultBranchRef --jq '.defaultBranchRef.name')
   DEFAULT_SHA=$(gh api repos/owner/name/git/refs/heads/$DEFAULT_BRANCH --jq '.object.sha')
   gh api repos/owner/name/git/refs \
     -f ref="refs/heads/synthesize-project/TIER_NAME" \
     -f sha="$DEFAULT_SHA"
   ```

3. **Push pattern files** to the appropriate tier branch.

4. **Push `synthesis-config.yml`** to the must-have branch if it doesn't exist.

5. **Create a PR for EACH tier** (must-have, nice-to-have, enhanced). Skip tiers with zero patterns. Each PR title MUST include the tier name and count. Nice-to-have PR should use checkboxes for individual pattern selection.

### Remote mode error handling

Before creating branches and PRs, handle common failure modes:

1. **Existing branch:** Before creating a branch, check if it exists:
   ```bash
   gh api repos/owner/name/git/refs/heads/synthesize-project/TIER_NAME --silent 2>/dev/null
   ```
   If it exists, prompt: "Branch `synthesize-project/TIER_NAME` already exists. Delete and recreate, or push to existing? [recreate/existing]"

2. **Existing PR:** Check for open PRs from the synthesis branch:
   ```bash
   gh pr list --repo owner/name --head synthesize-project/TIER_NAME --state open --json number,title
   ```
   If found, prompt: "An open PR already exists (#[N]: [title]). Update it with new patterns, or create a new PR? [update/new]"
   If updating, push to the existing branch and add a comment to the PR noting the update.

3. **API errors:** If branch creation or file push fails:
   - 403 (permissions): "Insufficient permissions to create branches on owner/name. Ensure the GitHub token has `repo` scope."
   - 422 (validation): "Branch name conflict or invalid ref. Try a different tier name suffix."
   - 404 (not found): "Repository not found or not accessible. Verify `--repo owner/name` is correct."
   - Other: Print the full API error and stop. Do not proceed to PR creation with partial branches.
