# Third-Party Skills Auto-Provisioning

## Status: Proposed
## Date: 2026-03-17

---

## Problem Statement

The hub currently provisions its own curated patterns (agents, skills, rules) into target projects via recommend.py --provision. It detects stacks and dependencies, then copies matching patterns from core/.claude/.

However, the Claude Code ecosystem now includes a rich set of third-party agent skills (e.g., redis/agent-skills, hashicorp/agent-skills, vercel-labs/agent-skills) installable via npx skills add. These skills are maintained by their respective vendors and follow the open Agent Skills standard (SKILL.md format).

The hub should automatically detect when a target project uses technologies covered by third-party skills and install them during provisioning, extending the hub value beyond its own curated patterns.

## Design Decisions

### D1: Install via npx skills add, do NOT vendor into the hub

**Decision**: Run npx skills add in the target project during provisioning rather than copying third-party skill files into core/.claude/.

**Rationale**:
- Third-party skills are maintained by their authors. Vendoring creates a stale-on-arrival copy that drifts from upstream.
- npx skills add handles placement into .claude/skills/, symlink management, and multi-agent compatibility.
- Licensing is cleaner -- the hub never redistributes third-party content.
- Users get updates when they re-run npx skills add (or use symlink mode).

**Trade-off**: Requires npx (Node.js) to be available in the provisioning environment. For environments without Node.js, the feature gracefully degrades (warns and skips).

### D2: Registry lives in config/third-party-skills.yml

**Decision**: A new YAML file in config/ defines the mapping from dependency signals to third-party skill install commands.

**Rationale**:
- Follows the existing config convention (repos.yml, settings.yml, urls.yml).
- Separate from registry/patterns.json which tracks hub-owned patterns with hashes and versions.
- YAML is human-editable and diff-friendly for PRs.
- Machine-readable for automation.

### D3: Dependency-signal based matching (reuse existing parsers)

**Decision**: Reuse the existing detect_dependencies_from_dir / detect_dependencies_from_repo infrastructure and _DEP_FILE_PARSERS to detect which third-party skills apply.

**Rationale**:
- The hub already parses package.json, requirements.txt, pyproject.toml, build.gradle, pubspec.yaml, Cargo.toml, go.mod, and Gemfile.
- Adding a new mapping layer (dependency name -> third-party skill) is minimal work.
- Consistent with how DEP_PATTERN_MAP promotes hub patterns today.

---

## Registry Schema: config/third-party-skills.yml

```yaml
# Third-party agent skills auto-installed during provisioning.
#
# Each entry maps dependency signals to an installable skill package.
# Install command is always: npx skills add <repo> [--skill <name>]
#
# Fields:
#   repo:           GitHub owner/repo for npx skills add (required)
#   skill:          Specific skill name within the repo (optional, installs all if omitted)
#   description:    What the skill provides (required, for reporting)
#   dependencies:   List of dependency names that trigger this skill (required)
#                   ANY match triggers installation (OR logic).
#   ecosystems:     Restrict matching to specific ecosystems: npm, pip, gradle, pub, cargo, gem, go
#                   (optional, matches all ecosystems if omitted)
#   file_signals:   Glob patterns for files whose presence triggers the skill
#                   (optional, alternative to dependency matching)
#   tags:           Searchable tags (optional)

skills:
  - repo: redis/agent-skills
    skill: redis-development
    description: >
      Redis development best practices: data structures, query engine,
      vector search, caching, and performance optimization.
    dependencies:
      - redis
      - ioredis
      - redis-py
      - aioredis
      - bull
      - bullmq
      - "@redis/client"
    tags: [database, cache, redis]

  - repo: hashicorp/agent-skills
    skill: terraform
    description: >
      Write HCL code, build Terraform modules, develop providers, and run tests.
    dependencies:
      - "@cdktf/provider-aws"
      - cdktf
    file_signals:
      - "**/*.tf"
      - "**/terraform.tfvars"
    tags: [infrastructure, terraform, iac]

  - repo: hashicorp/agent-skills
    skill: packer
    description: >
      Build machine images on AWS, Azure, and Windows; integrate with HCP Packer registry.
    file_signals:
      - "**/*.pkr.hcl"
    dependencies: []
    tags: [infrastructure, packer, iac]

  - repo: vercel-labs/agent-skills
    description: >
      React, Next.js, and frontend design best practices from Vercel Engineering.
      Performance optimization, accessibility, and deployment guidelines.
    dependencies:
      - next
      - react
      - "@vercel/next"
    ecosystems: [npm]
    tags: [frontend, react, nextjs, vercel]

  - repo: vercel-labs/next-skills
    description: >
      Next.js-specific patterns including App Router, Server Components,
      and data fetching best practices.
    dependencies:
      - next
    ecosystems: [npm]
    tags: [frontend, nextjs]
```

### Schema Design Notes

1. **file_signals** (optional): Glob patterns that trigger the skill even without a dependency match. This covers tools like Terraform and Packer where .tf or .pkr.hcl files are the signal, not package dependencies.

2. **ecosystems** filter: Prevents false positives. A Python package named "redis" should match redis/agent-skills, but a Go package with a "redis" segment in its module path might not be the same thing. Ecosystem scoping keeps matching precise.

3. **skill** field: When a repo contains multiple skills (e.g., hashicorp/agent-skills has terraform and packer), each entry targets a specific skill. When omitted, npx skills add installs all skills from that repo.

---

## Architecture

### How It Fits Into the Existing Flow

The new logic integrates at two points in the existing recommend.py flow:

1. **Resolution phase** (after Step 1b -- detect dependencies): A new resolve_third_party_skills() function takes the same deps dict that resolve_dep_patterns uses and matches against the third-party registry.
2. **Provisioning phase** (Step 6b): After copying hub patterns, install_third_party_skills() runs npx skills add for each matched skill.

For remote repos (--repo mode), npx cannot be run, so the PR body includes copy-pasteable install commands as post-merge instructions.

### Integration Flow

- recommend.py --provision --local /path/to/project
  1. Detect stacks (existing)
  2. Detect dependencies (existing)
  3. Resolve hub patterns via DEP_PATTERN_MAP (existing)
  4. **NEW**: Resolve third-party skills via third-party-skills.yml
  5. Gap analysis and tiering (existing)
  6. Copy hub patterns (existing)
  7. **NEW**: Install matched third-party skills via npx skills add
  8. Generate CLAUDE.md, settings.json (existing)
  9. Report results including third-party skill install status

- If npx is unavailable: step 7 logs a warning and skips. The report still lists recommendations with manual commands.
- If --skip-third-party flag is set: steps 4 and 7 are skipped entirely.

---
## Implementation Plan

### Task 1: Create config/third-party-skills.yml

**New file**: config/third-party-skills.yml

- Define the schema as shown in the Registry Schema section above.
- Populate with 5 initial entries: redis/agent-skills, hashicorp/agent-skills (terraform, packer), vercel-labs/agent-skills, vercel-labs/next-skills.
- Follow existing config/ conventions (YAML with field comments at top).

**Complexity**: Low
**Dependencies**: None

### Task 2: Create scripts/third_party_skills.py

**New file**: scripts/third_party_skills.py

Functions to implement:

- load_third_party_registry(hub_root: Path) -> list[dict]: Load and validate config/third-party-skills.yml.
- resolve_third_party_skills(deps, project_dir, hub_root) -> list[dict]: Match detected dependencies (and file signals) against the registry. Returns list of matched skill entries with match reasons.
- check_npx_available() -> bool: Check if npx is on PATH.
- install_third_party_skills(target_dir, matched_skills, dry_run) -> dict[str, str]: Run npx skills add for each matched skill. Returns {skill_id: status_string}.
- detect_installed_third_party_skills(target_dir: Path) -> set[str]: Scan target .claude/skills/ for skills that match known third-party repos. Prevents re-installation.
- format_third_party_report(matched, install_results) -> str: Format a human-readable report section.

**Key behaviors**:
- resolve_third_party_skills uses the same deps dict that resolve_dep_patterns uses. It iterates over each registry entry, checks if any of the entry dependencies appear in the flattened dep list (optionally filtered by ecosystems), and also checks file_signals via glob matching on project_dir.
- install_third_party_skills runs npx skills add <repo> --skill <name> -y (with -y to skip prompts) via subprocess.run. Each install is independent; one failure does not block others.
- If npx is not available, the function logs a warning and returns all skills as skipped. The report still lists recommended skills with manual install commands.

**Complexity**: Medium
**Dependencies**: Task 1

### Task 3: Integrate into scripts/recommend.py

**Modified file**: scripts/recommend.py

Changes:

1. **Import**: Add from scripts.third_party_skills import ... at top.
2. **After Step 1b** (line ~2305): Call resolve_third_party_skills(deps, project_dir) and store the result.
3. **Report formatting** (the format_report function): Add a new Third-Party Skills section listing matched skills with skill name/description, match reason, and install command.
4. **provision_to_local function**: After the existing 4 steps (copy resources, CLAUDE.md, CLAUDE.local.md, settings.json), add Step 5: install third-party skills. Add results to the returned summary dict.
5. **provision_to_repo functions**: Add third-party skill install commands to the PR body as a Post-merge section with copy-pasteable commands.
6. **CLI args**: Add --skip-third-party flag to disable third-party skill installation during provisioning.
7. **JSON output** (--json): Include third_party_skills key in the output with matched skills and their status.

**Complexity**: Medium
**Dependencies**: Task 2

### Task 4: Add validation to scripts/validate_patterns.py

**Modified file**: scripts/validate_patterns.py

Add a validation check for config/third-party-skills.yml:
- Required fields present (repo, description, dependencies or file_signals)
- No duplicate entries (same repo + skill combo)
- dependencies is a list (can be empty if file_signals is provided)
- At least one trigger mechanism: non-empty dependencies OR non-empty file_signals
- ecosystems values are from the known set if provided: npm, pip, gradle, pub, cargo, gem, go

**Complexity**: Low
**Dependencies**: Task 1

### Task 5: Write tests

**New file**: scripts/tests/test_third_party_skills.py

Test cases:
- test_load_registry_valid: loads the YAML and validates schema
- test_load_registry_missing_file: returns empty list, no crash
- test_resolve_matches_redis: deps containing redis match redis/agent-skills
- test_resolve_matches_by_ecosystem: npm redis matches but pip redis does not when ecosystems: [npm]
- test_resolve_no_match: deps with no matching entries return empty
- test_resolve_file_signals: .tf files trigger terraform skill
- test_resolve_dedup: same repo not matched twice for different deps
- test_check_npx_available: mock subprocess to test both available and unavailable
- test_install_dry_run: dry_run=True does not call subprocess
- test_install_skip_already_installed: detects existing skills and skips
- test_format_report: produces readable output with install commands

**Complexity**: Medium
**Dependencies**: Task 2, Task 3

### Task 6: Update documentation

**Modified files**:
- CLAUDE.md: Add brief mention of third-party skills in Architecture / Key Directories section
- docs/SYNC-ARCHITECTURE.md (if exists): Add third-party skills as a new sync flow

**Complexity**: Low
**Dependencies**: Tasks 1-5
---

## Execution Order

Task 1 (config file) -> Task 2 (module) -> Task 3 (integration) -> Task 5 (tests)
                                         -> Task 4 (validation)  -> Task 5 (tests)
                                                                  -> Task 6 (docs)

Tasks 3 and 4 can run in parallel after Task 2. Task 5 depends on both 3 and 4. Task 6 can run last or in parallel with Task 5.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| npx not available in target environment | Third-party skills silently skipped | Graceful degradation: warn user, list manual install commands, do not fail provisioning |
| npx skills add fails (network, auth, repo gone) | One skill fails to install | Each install is independent. Failures are logged, others proceed. Summary shows status per skill |
| False positive: dep name collision across ecosystems | Wrong skill installed | ecosystems field restricts matching. Start conservative with unambiguous dependency signals |
| Third-party skill conflicts with hub pattern | Confusing duplicate guidance | detect_installed_third_party_skills checks before install. Report flags potential overlaps |
| Registry grows unwieldy | Hard to maintain | Keep entries curated (same reactive-not-speculative policy as hub patterns). Require evidence of active maintenance |
| Breaking changes in npx skills CLI | Install commands fail | Pin to known CLI behavior. Test in CI with a mock or real install of one skill |

---

## Success Criteria

1. Running recommend.py --provision --local /path/to/project on a project with redis in its package.json or requirements.txt installs redis/agent-skills automatically.
2. Running recommend.py --local /path/to/project (report mode) lists recommended third-party skills with install commands, even without --provision.
3. If npx is not available, provisioning completes successfully with a warning and manual install instructions.
4. validate_patterns.py catches malformed entries in config/third-party-skills.yml.
5. All new code has test coverage. Existing tests still pass.
6. The feature is opt-out (--skip-third-party) rather than requiring opt-in.

---

## Future Extensions (Out of Scope for v1)

- **Version pinning**: Support min_version / max_version in registry entries to match specific dependency versions.
- **Skill health checks**: Periodically verify that registered third-party repos still exist and their skills still install.
- **Automatic registry updates**: Scan skills.sh leaderboard or GitHub topics for new skill repos and propose additions.
- **Conflict detection**: Compare third-party skill content against hub patterns to detect overlapping guidance and warn users.
- **discover-skills mode**: A recommend.py --discover-skills mode that searches skills.sh for skills matching detected dependencies, even if not in the hub registry.
