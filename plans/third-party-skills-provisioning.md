# Third-Party Skills Auto-Provisioning

## Status: Completed (2026-03-17, commit cf4f507)
## Date: 2026-03-17

---

## Problem Statement

The hub provisions its own curated patterns into target projects via `recommend.py --provision`. The Claude Code ecosystem now includes third-party agent skills (e.g., `redis/agent-skills`, `hashicorp/agent-skills`) installable via `npx skills add`.

The hub should detect when a target project uses technologies covered by third-party skills and **recommend them** during provisioning.

## Philosophy

**The hub facilitates, it does not own.** Third-party skills are maintained by their authors. The hub's role is:

1. **Detect** — scan the target project's dependencies
2. **Match** — look up which third-party skills apply
3. **Recommend** — show the user what to install, why, and how
4. **Optionally install** — run `npx skills add` if the user confirms

Everything else (updates, rollback, version management, troubleshooting) is the project owner's responsibility. The hub adds no wrappers, no lockfiles, no caching, no conflict resolution. It just points you in the right direction.

---

## Design Decisions

### D1: Recommend-first, install-optional

The hub always shows recommendations with copy-pasteable install commands. Actual installation only happens during `--provision` and only if `npx` is available. If not, the user gets the commands and handles it themselves.

### D2: Registry in `config/third-party-skills.yml`

A YAML file maps dependency signals to skill repos. Follows existing config conventions (`repos.yml`, `settings.yml`). Separate from `registry/patterns.json` which tracks hub-owned patterns.

### D3: Reuse existing dependency parsers

The hub already parses `package.json`, `requirements.txt`, `pyproject.toml`, `build.gradle`, `pubspec.yaml`, `Cargo.toml`, `go.mod`, and `Gemfile`. The new feature just adds a mapping layer on top.

---

## Registry Schema: `config/third-party-skills.yml`

```yaml
# Third-party agent skills recommended during provisioning.
#
# The hub does NOT own these skills. It detects matching dependencies
# and recommends installation. The project owner manages updates/removal.
#
# Fields:
#   repo:           GitHub owner/repo (required)
#   skill:          Specific skill name within the repo (optional)
#   description:    What the skill provides (required)
#   dependencies:   Dependency names that trigger this recommendation (OR logic)
#   ecosystems:     Restrict to specific ecosystems (optional)
#   file_signals:   File glob patterns that trigger this recommendation (optional)
#   url:            Link to docs/README for the user (optional)
#   prerequisites:  What the user needs to install this (optional, shown in report)
#   tags:           Searchable tags (optional)

skills:
  - repo: redis/agent-skills
    skill: redis-development
    description: >
      Redis best practices: data structures, query engine,
      vector search, caching, and performance.
    dependencies:
      - redis
      - ioredis
      - redis-py
      - aioredis
      - bull
      - bullmq
      - "@redis/client"
    url: https://github.com/redis/agent-skills
    prerequisites: "Node.js (npx)"
    tags: [database, cache, redis]

  - repo: hashicorp/agent-skills
    skill: terraform
    description: >
      HCL code, Terraform modules, providers, and testing.
    dependencies:
      - cdktf
      - "@cdktf/provider-aws"
    file_signals:
      - "**/*.tf"
      - "**/terraform.tfvars"
    url: https://github.com/hashicorp/agent-skills
    prerequisites: "Node.js (npx)"
    tags: [infrastructure, terraform, iac]

  - repo: hashicorp/agent-skills
    skill: packer
    description: >
      Machine images for AWS, Azure, Windows; HCP Packer registry.
    dependencies: []
    file_signals:
      - "**/*.pkr.hcl"
    url: https://github.com/hashicorp/agent-skills
    prerequisites: "Node.js (npx)"
    tags: [infrastructure, packer, iac]

  - repo: vercel-labs/agent-skills
    description: >
      React, Next.js, and frontend best practices from Vercel.
    dependencies:
      - next
      - react
      - "@vercel/next"
    ecosystems: [npm]
    url: https://github.com/vercel-labs/agent-skills
    prerequisites: "Node.js (npx)"
    tags: [frontend, react, nextjs, vercel]
```

---

## Integration Flow

```
recommend.py --provision --local /path/to/project
  1. Detect stacks (existing)
  2. Detect dependencies (existing)
  3. Resolve hub patterns (existing)
  4. NEW: Match third-party skills from registry
  5. Gap analysis and tiering (existing)
  6. Copy hub patterns (existing)
  7. NEW: Print third-party skill recommendations
     - If npx available: attempt install, report results
     - If npx unavailable: print install commands for user
  8. Generate CLAUDE.md, settings.json (existing)
```

Report-only mode (`--local` without `--provision`) includes recommendations in the output but does not install anything.

### Example Report Output

```
══════════════════════════════════════════════════
  RECOMMENDED THIRD-PARTY SKILLS
══════════════════════════════════════════════════

  Skill                    Matched On       Install Command
  ─────                    ──────────       ───────────────
  redis-development        redis (pip)      npx skills add redis/agent-skills --skill redis-development
  terraform                *.tf files       npx skills add hashicorp/agent-skills --skill terraform

  Prerequisites: Node.js (npx) required for installation.
  These skills are maintained by their respective authors.
  Docs: https://github.com/redis/agent-skills
        https://github.com/hashicorp/agent-skills

  To install manually:
    cd /path/to/project
    npx skills add redis/agent-skills --skill redis-development
    npx skills add hashicorp/agent-skills --skill terraform
```

---

## Implementation Plan

### Task 1: Create `config/third-party-skills.yml`

New file with the registry schema above. Populate with initial entries.

**Complexity**: Low | **Dependencies**: None

### Task 2: Create `scripts/third_party_skills.py`

Minimal module with:

- `load_registry(hub_root) -> list[dict]` — load and validate YAML
- `resolve_skills(deps, project_dir, hub_root) -> list[dict]` — match deps/files against registry, return matches with reasons
- `format_recommendations(matched) -> str` — format the report section with install commands
- `try_install(target_dir, matched) -> dict[str, str]` — attempt `npx skills add` for each match, return status per skill. If npx unavailable, return all as "skipped".

**Complexity**: Low-Medium | **Dependencies**: Task 1

### Task 3: Integrate into `scripts/recommend.py`

- Import from `scripts.third_party_skills`
- After dep detection: call `resolve_skills()`
- In report formatting: append recommendations section
- In `provision_to_local`: call `try_install()` after hub pattern copy
- In `provision_to_repo`: add install commands to PR body
- Add `--skip-third-party` flag

**Complexity**: Medium | **Dependencies**: Task 2

### Task 4: Add validation to `scripts/workflow_quality_gate_validate_patterns.py`

Validate `config/third-party-skills.yml`:
- Required fields present (`repo`, `description`)
- At least one trigger (`dependencies` or `file_signals` non-empty)
- No duplicate `repo` + `skill` combos
- `ecosystems` values from known set if provided

**Complexity**: Low | **Dependencies**: Task 1

### Task 5: Write tests

`scripts/tests/test_third_party_skills.py`:
- `test_load_registry_valid` / `test_load_registry_missing_file`
- `test_resolve_matches_redis` / `test_resolve_no_match`
- `test_resolve_by_ecosystem` / `test_resolve_file_signals`
- `test_format_recommendations`
- `test_try_install_npx_unavailable` (mocked)

**Complexity**: Low-Medium | **Dependencies**: Tasks 2-3

### Task 6: Update docs

- CLAUDE.md: mention `config/third-party-skills.yml` in Key Directories
- Brief note in Architecture about the facilitation model

**Complexity**: Low | **Dependencies**: Tasks 1-5

---

## Execution Order

```
Task 1 ──→ Task 2 ──→ Task 3 ──→ Task 5
                  └──→ Task 4 ──→ Task 5
                                    └──→ Task 6
```

---

## What the Hub Does NOT Do

- **No version pinning** — the user installs whatever version is current
- **No rollback** — the user removes skills themselves (`rm -rf .claude/skills/<name>`)
- **No caching** — every install fetches from upstream
- **No conflict detection** — if a hub pattern overlaps with a third-party skill, both coexist
- **No health monitoring** — if a third-party repo goes offline, the install command fails and the user sees the error
- **No auto-updates** — re-run provisioning or `npx skills add` manually

The hub is a **matchmaker**, not a **package manager**.

---

## Success Criteria

1. `recommend.py --local /path/to/project` lists matching third-party skills with install commands
2. `recommend.py --provision --local /path/to/project` attempts installation and reports results
3. If npx is unavailable, provisioning succeeds with manual commands printed
4. `workflow_quality_gate_validate_patterns.py` catches malformed registry entries
5. All new code has tests. Existing tests pass.
