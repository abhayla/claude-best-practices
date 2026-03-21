# Synthesize Flywheel — LLM-Powered Pattern Compiler

## Overview

`/synthesize-project` is a proposed Claude Code skill that transforms the hub from a **static pattern library** into a **pattern compiler**. Instead of filtering pre-authored patterns by stack prefix, it reads a target project's actual codebase and generates bespoke `.claude/` configurations tailored to that specific project.

It runs entirely inside a Claude Code session — **zero API cost**. The developer's existing Claude Code session does the reasoning, file reading, and pattern generation. No standalone script, no separate Anthropic API calls.

The existing 133 skills, 21 agents, and 20 rules become few-shot examples and structural targets — not just things to copy, but training data for generating project-specific patterns.

### The core difference

| | Today (`recommend.py --provision`) | Proposed (`/synthesize-project`) |
|---|---|---|
| **Input** | Stack name (e.g., `fastapi-python`) | Actual project source code |
| **Logic** | Filter by prefix, copy matching patterns | Claude Code reads code, extracts conventions, generates patterns |
| **Output** | Generic hub patterns that match the stack | Project-specific patterns that encode the project's real conventions |
| **Cost** | Free (file copy) | Free (runs in existing Claude Code session) |
| **Example rule** | *"Use consistent error handling"* | *"All endpoints in `src/api/` must return `ApiResult[T]` from `src/core/result.py`. Never raise raw HTTPException — use `ApiResult.fail(code, msg)` so `middleware/errors.py` handles logging."* |

---

## Why this is the highest-leverage addition

1. **Changes the category of the project.** More skills, better dedup, telemetry, a web UI — all incremental. This makes the hub a compiler, not a catalog.
2. **Zero cost to the developer.** Runs inside their existing Claude Code session. No API keys, no billing, no setup.
3. **All infrastructure already exists.** Pattern format standards, validation pipeline (`workflow_quality_gate_validate_patterns.py`), structure/portability/self-containment rules, stack detection in `recommend.py`.
4. **Doesn't violate curation policy.** The reactive-not-speculative rule applies to patterns added to the hub. Synthesized patterns are generated for a specific project from its actual code — they originate from observed reality.
5. **Creates a self-improving flywheel** (detailed below).

---

## The flywheel

```
Project code → /synthesize-project → custom .claude/ → usage →
    ↓ (patterns that recur across projects)
    contribute back → hub grows smarter → better few-shot examples →
    better synthesis
```

### 5 stages

**Stage 1: Synthesize.** Point `/synthesize-project` at a real project. It reads the code, finds conventions, generates custom patterns. Three different FastAPI projects might produce three project-specific rules about API response wrapping — each encoding the same underlying idea in project-specific terms.

**Stage 2: Usage.** Synthesized patterns get used in their respective projects. Some prove valuable (developers keep them, they prevent bugs). Some turn out to be noise (developers delete them). Usage is the filter that separates signal from noise.

**Stage 3: Contribute back.** The existing `/contribute-practice` skill handles this. When a synthesized pattern survives real usage, it can be submitted to the hub — now with evidence: "this pattern was independently synthesized for 3 projects and kept by all 3."

**Stage 4: Hub grows smarter.** The hub doesn't just get one more pattern. Those three project-specific response-wrapper rules get deduplicated (3-level dedup infrastructure already exists) into a single, portable, generalized pattern earned from real codebases.

**Stage 5: Better synthesis.** When `/synthesize-project` generates patterns, it uses hub patterns as few-shot examples. More high-quality, battle-tested patterns in the hub → better examples → better synthesis output. The first synthesis run has 133 skills as examples. After 50 projects contribute back, it has richer, more diverse examples. After 500, synthesis quality is substantially better.

### Why "flywheel" not "feedback loop"

A feedback loop implies equilibrium. A flywheel implies **momentum** — each cycle is easier than the last:

- More hub patterns → better synthesis → more useful output → higher contribution rate
- Higher contribution rate → more hub patterns → (repeat)
- Each new project domain (e.g., first gRPC project) seeds an entirely new category of patterns

The hub currently grows linearly (manual authorship). The flywheel makes growth **superlinear** — every project that uses `/synthesize-project` is simultaneously a consumer and a potential contributor.

### Cold-start solution

The 133 existing manually-curated skills ARE the cold-start fuel. They provide the initial kinetic energy for the first synthesis to be good enough to be useful, which kicks off the cycle.

---

## Functional walkthrough: all scenarios

### Actors

1. **Hub** — this repo (`claude-best-practices`), maintained by the hub owner
2. **Downstream project** — any repo that consumes patterns from the hub
3. **`/synthesize-project`** — Claude Code skill, run by a developer in their project
4. **`/synthesize-hub`** — Claude Code skill, run by the hub maintainer in the hub repo

---

### Scenario 1: Brand new project, no `.claude/` yet

**Trigger:** Developer discovers the hub, wants to bootstrap their project.

```bash
# Single command does everything — run inside Claude Code in the project directory
/synthesize-project
```

**Step by step:**

1. Developer runs `/synthesize-project` in their Claude Code session while in the project directory
2. **Hub provisioning (Step 1):** Runs `recommend.py --provision` which auto-detects stacks (e.g., FastAPI + SQLAlchemy + Alembic + pytest), copies matching hub patterns, generates CLAUDE.md and settings.json
3. **Project mapping (Step 2):** Claude Code reads the project — source files, configs, CI, tests (using Read, Glob, Grep tools it already has)
4. **Convention identification (Step 3):** Identifies 10-20 candidate conventions, deduplicates against hub patterns just copied — drops any already covered by hub
5. **Evidence gathering (Step 4):** Reads source files to confirm/reject each convention
6. **Pattern generation (Steps 5-7):** Loads reference material, generates patterns, validates each against `workflow_quality_gate_validate_patterns.py`, writes passing patterns
7. Prints summary showing both hub patterns copied AND project-specific patterns synthesized, with flywheel onboarding box

**Cost:** Zero beyond the developer's existing Claude Code session. No separate API calls.

**Autonomous:** Steps 2-8, fully automated within the session.

**NOT autonomous:** Developer must review generated patterns before committing. Files are written to disk but not committed — same as `--provision` today.

**Risk:** Claude generates a rule that's wrong. It sees `ResponseModel` in 3 files and assumes it's a project-wide convention, but it's actually legacy code being migrated away.

**Mitigation:** Generated patterns get a `synthesized: true` frontmatter flag. Developer reviews them. Over time, patterns that survive review across many projects prove their reliability.

---

### Scenario 2: Existing project with `.claude/`, wants updates

**Trigger:** Project has hub patterns + synthesized patterns. Developer runs synthesis again after 3 months of development.

```bash
# Inside Claude Code, in the project directory
/synthesize-project --update
```

**What happens:**

1. Reads current `.claude/` directory — knows what patterns already exist
2. Reads the codebase again — it's changed in 3 months
3. Diffs current conventions against existing patterns
4. Identifies:
   - **Stale patterns** — code changed, pattern didn't
   - **New conventions** — emerged since last synthesis
   - **Accurate patterns** — no change needed
5. Generates only the delta — new patterns + updates to stale ones
6. Writes updates with `[UPDATED]` markers in the summary

**Autonomous:** Detection and generation.

**NOT autonomous:** Developer decides which updates to keep. A stale pattern might be stale because the code is wrong, not the pattern.

**Concrete example:** Project had a rule: *"All database queries go through `src/db/repository.py`"*. Then someone added a direct SQLAlchemy query in `src/api/users.py` as a quick fix. Synthesis detects the divergence but can't know if:

- (a) The rule is right and `users.py` has a bug → keep the rule
- (b) The team abandoned the repository pattern → delete the rule

It flags both options. Developer picks one.

---

### Scenario 3: Multiple downstream projects, hub wants to learn

**Trigger:** 20 projects have used `/synthesize-project`. Hub maintainer wants to discover recurring synthesized patterns.

```bash
# Inside Claude Code, in the hub repo directory
/synthesize-hub
```

**What happens:**

1. Hub maintainer runs `/synthesize-hub` in their Claude Code session while in the hub repo
2. Claude Code clones/fetches `.claude/` directories from registered repos in `config/repos.yml` (respecting bilateral consent)
3. Specifically looks for patterns with `synthesized: true` in frontmatter
4. Collects all synthesized patterns across all projects
5. Runs 3-level dedup — Levels 1-2 (hash + structural) are instant; Level 3 (semantic classification) is Claude Code reasoning within the same session
6. Groups similar patterns into clusters
7. For each cluster with 3+ independent occurrences, generates a **generalization candidate**

**Example output:**

```
CLUSTER: typed-api-response-envelope (5 projects)
  - project-a/.claude/rules/api-result-wrapper.md
  - project-b/.claude/rules/response-envelope.md
  - project-c/.claude/rules/typed-response.md
  - project-d/.claude/rules/api-envelope.md
  - project-e/.claude/rules/result-type.md

  Proposed generalized pattern:
  [draft shown here]

  → PR #47 created: hub/pulls/47
```

**Cost:** Zero — runs in the hub maintainer's Claude Code session.

**Autonomous:** Discovery, clustering, draft generation, **and PR creation**. The skill creates PRs via `gh pr create` at the end. No separate API calls.

**NOT autonomous:** Hub maintainer **reviews and merges** the PR. The PR is just a proposal sitting in the queue. The curation policy holds — but "evidence" is now concrete: "5 independent projects converged on this pattern."

**The human gate is merging, not creating.** PR creation is cheap and reversible (close it if it's bad). Merging into `core/.claude/` is the irreversible action that affects all downstream projects — that's where the human must be in the loop.

---

### Scenario 4: Hub gets a new generalized pattern, downstream projects benefit

**Trigger:** Hub maintainer approved the "typed API response envelope" pattern from Scenario 3. It's now in `core/.claude/rules/`.

**Sub-scenario 4a — Projects using sync (Flow 4):**

The existing `sync_to_projects.py` workflow runs weekly via GitHub Actions:
1. Detects the new pattern in the registry
2. Creates a PR on each registered downstream project
3. Project maintainer merges or rejects

Fully autonomous up to PR creation.

**Sub-scenario 4b — Projects not registered, using manual sync:**

Developer runs `/update-practices` or `/synthesize-project --update`. The new hub pattern appears as a recommendation. Developer decides whether to adopt it. Not autonomous.

**Sub-scenario 4c — The compounding effect (fully autonomous):**

Next time `/synthesize-project` runs on ANY project, it has this new battle-tested pattern in its few-shot examples. When it encounters a project that wraps API responses, it generates a better, more specific version because the example is sharper. This improvement happens without anyone doing anything — it's a side effect of the hub having better patterns.

---

### Scenario 5: Project in a stack the hub doesn't cover yet

**Trigger:** Someone runs `/synthesize-project` on a Rust + Axum project. The hub has zero Rust patterns.

**What happens:**

1. Stack detection finds no matching prefix
2. Hub patterns copied: only the 15 universal agents + universal rules + universal skills
3. Synthesis still runs — reads Rust code, generates Rust-specific patterns
4. But few-shot examples are all Python/TypeScript/Android, so quality is lower
5. Generated patterns might have wrong idioms (Python-style error handling for Rust)

**This is the cold-start problem for new stacks.**

**How it resolves:**

- 3 Rust projects use `/synthesize-project` → some patterns survive developer review
- `/synthesize-hub` finds 3+ recurring Rust patterns
- Hub maintainer approves → hub now has `rust-axum-*` patterns
- Next Rust project gets much better synthesis

**Timeline:** With 5+ projects contributing, approximately 2-3 cycles. Until then, synthesis output for new stacks needs heavier developer review.

---

### Scenario 6: Synthesized pattern is wrong and gets contributed back

**Trigger:** `/synthesize-project` generates a subtly wrong pattern. Developer doesn't catch it. Project uses it for months. `/contribute-practice` submits it to the hub.

**Defense layers:**

1. `workflow_quality_gate_validate_patterns.py` catches structural issues (missing frontmatter, bad format) → **blocked automatically**
2. If structurally valid but semantically wrong: PR reaches hub maintainer
3. `/synthesize-hub` clustering shows this pattern has NO matches in other projects → low confidence → flagged
4. Hub maintainer rejects the PR

**What if it slips through?** A bad pattern enters the hub. It becomes a few-shot example. Synthesis quality degrades for that specific case.

**Mitigations:**

- Semantic dedup (Level 3) detects when a candidate conflicts with existing patterns
- Patterns with `synthesized: true` + low adoption count get a lower trust score in the dashboard
- `check_freshness.py` finds patterns no downstream project actually uses → removal candidates

**This is the most dangerous scenario.** The curation bottleneck (hub maintainer reviewing PRs) is the firewall.

---

### Scenario 7: Two projects synthesize conflicting patterns

**Trigger:** Project A's synthesis: *"Always use class-based views"*. Project B's synthesis: *"Always use function-based views"*. Both valid for their respective projects.

**At contribution time:**

1. `/synthesize-hub` clusters these (semantically similar — both about view structure)
2. Detects they're **contradictory**, not reinforcing
3. Flags the cluster as "divergent" — not a candidate for generalization

**This is correct behavior.** Not every convention should be generalized. The hub absorbs patterns where projects converge, not where they diverge.

**What if 15 projects say class-based and 2 say function-based?** Still no generalization — the hub shouldn't impose style choices. Only patterns about correctness, safety, or consistency get generalized.

The clustering algorithm needs a **category filter**:

- **Generalizable:** Error handling, testing patterns, security rules, CI practices
- **Not generalizable:** Style choices, naming conventions, architecture preferences

---

## Autonomy map

| Step | Autonomous? | Cost | Why / why not |
|---|---|---|---|
| Synthesis (code → patterns) | **Yes** | Free | Runs in developer's Claude Code session |
| Writing to project disk | **Yes** | Free | Files written, not committed |
| Developer review of generated patterns | **No** | — | Only human knows if pattern matches intent |
| Using patterns in daily work | **Yes** | Free | Claude Code reads `.claude/` automatically |
| Detecting stale patterns on re-run | **Yes** | Free | Runs in developer's Claude Code session |
| Collecting synthesized patterns from projects | **Yes** | Free | Runs in hub maintainer's Claude Code session |
| Clustering recurring patterns | **Yes** | Free | Runs in hub maintainer's Claude Code session |
| Drafting generalized patterns | **Yes** | Free | Same session as clustering |
| Creating PRs for generalized patterns | **Yes** | Free | `gh pr create` from Claude Code |
| Merging generalized patterns to hub | **No** | — | Hub maintainer reviews and merges |
| Distributing new hub patterns to projects | **Yes** (registered) / **No** (manual) | Free | Sync Flow 4 vs manual |
| Improving synthesis from better hub | **Yes** | Free | Automatic — better examples = better output |

**Two human checkpoints:** developer reviews synthesized output, hub maintainer reviews contributed patterns. Everything else is autonomous.

**The flywheel is ~80% autonomous.** The 20% that isn't — developer review and hub curation — is where quality lives. Fully autonomous would mean trusting LLM output without review, which degrades quality within a few cycles. The two human checkpoints prevent the flywheel from becoming a garbage-in-garbage-out loop.

The compounding happens in the autonomous parts: better hub → better few-shot examples → better synthesis → more useful patterns → higher contribution rate. The human parts don't slow this down because they're lightweight (reviewing a diff, approving a PR) — they just prevent catastrophic quality collapse.

---

## Trust, consent, and communication

### The core principle: bilateral consent

Sharing is a **two-way exchange**, not charity. The hub gives you continuously improving patterns, and in return it learns from your synthesized patterns. If you don't share, you don't receive. This makes the value proposition clear and the consent model simple.

| Mode | You share with hub | Hub shares with you | How to enter |
|---|---|---|---|
| **Local-only** (default) | No | No | Do nothing — this is what you get |
| **One-off contribution** | One pattern at a time | No | Run `/contribute-practice` anytime |
| **Bilateral sync** | Yes — hub scans your patterns | Yes — hub pushes updates to you | Set `allow_hub_sharing: true` in `.claude/synthesis-config.yml` |

**Local-only** is the default and is fully functional. Synthesis works, patterns are generated, nothing ever leaves the project. But the project is standalone — it doesn't receive hub updates either.

**One-off contribution** lets a developer share a single pattern via `/contribute-practice` without committing to ongoing sync. They still don't receive auto-updates — the bilateral rule applies to the ongoing flywheel, not one-off gifts.

**Bilateral sync** is the full flywheel. The project's synthesized patterns are visible to hub scanning, AND the project receives new/improved patterns from the hub via automated PRs. Either side can revoke at any time.

### What data actually flows and when

| Event | What leaves the project | Who initiates | Project owner aware? |
|---|---|---|---|
| `/synthesize-project` | **Nothing** — runs entirely locally in Claude Code session | Developer | Yes — they ran it |
| Developer commits `.claude/` | **Nothing** — stays in project repo | Developer | Yes — their commit |
| `/contribute-practice` | Selected pattern files submitted as hub PR | Developer | **Yes** — explicit action, preview shown |
| `/synthesize-hub` | Pattern files read from bilateral-sync repos | Hub maintainer (on-demand) | **Yes** — requires their `allow_hub_sharing: true` |
| `sync_to_projects.py` | Hub patterns pushed as PR to project | Hub (weekly) | **Yes** — only for bilateral-sync repos |

No "maybe not" gaps. Every row where data moves requires the project owner's prior explicit consent.

### The config file: `.claude/synthesis-config.yml`

`/synthesize-project` generates this file on first run with sharing OFF and inline comments explaining the trade. The file is always present — a passive reminder that the option exists. Changing consent is editing one line.

```yaml
# .claude/synthesis-config.yml
#
# Synthesize Flywheel — consent configuration
#
# Sharing is bilateral: turn it ON to both contribute your synthesized
# patterns to the hub AND receive new/improved patterns from the hub.
# Turn it OFF (default) to keep everything local — synthesis still works,
# but you won't receive hub updates.
#
# You can change this at any time. Changes take effect on the next scan cycle.

allow_hub_sharing: false          # Set to true for bilateral sync with the hub

# Patterns listed here are NEVER shared, even when allow_hub_sharing is true.
# Use this for patterns that reveal internal architecture you want to keep private.
private_patterns: []
  # - rules/internal-auth-flow.md
  # - rules/billing-logic.md

# Project-specific details to strip from patterns before they leave.
# The sanitization pass replaces these with generic placeholders.
strip_before_sharing:
  - file_paths                    # src/core/result.py → <module_path>
  - class_names                   # ApiResult → <ClassName>
  - env_vars                      # DATABASE_URL → $VARIABLE_NAME

# Set to true to receive a .claude/scan-log.yml with full scan history.
# The log arrives via the same sync PR as pattern updates.
# Default: false (you still see attribution in sync PR descriptions).
scan_log: false
```

### Onboarding: how project owners learn about the flywheel

The primary touchpoint is **terminal output at the moment they interact with the tool**. No docs to discover, no issues to read — the information arrives exactly when it's relevant.

**On every `/synthesize-project` run, the output includes a status line:**

When sharing is OFF (default):

```
✓ Generated 8 patterns for your project
✓ All patterns are local — nothing has been shared

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

When sharing is ON:

```
✓ Generated 8 patterns for your project
✓ Hub sharing is ON — your patterns contribute to the hub, and you receive updates.
```

**On subsequent runs**, the full box is not repeated — just the one-liner status. The box only appears on first run or when `synthesis-config.yml` is first created.

**During `/contribute-practice`:**

Before submitting, the skill shows a sanitization preview:

```
The following pattern will be submitted to the hub:

  rules/typed-api-envelope.md

  Before submission, these project-specific details will be stripped:
  - src/core/result.py → <module_path>
  - ApiResult → <WrapperType>
  - middleware/errors.py → <error_handler_path>

  Preview of sanitized pattern:
  [shown here]

  Submit? [y/n]
```

### Consent changes and revocation

Consent can be changed at any time by editing `synthesis-config.yml`:

| Change | Effect | When it takes effect |
|---|---|---|
| `false` → `true` | Project joins bilateral sync — hub begins scanning, project begins receiving updates | Next hub scan cycle (weekly) |
| `true` → `false` | Project leaves bilateral sync — hub stops scanning, project stops receiving updates | Next hub scan cycle (weekly) |
| Add pattern to `private_patterns` | That specific pattern is excluded from sharing | Next hub scan cycle |
| Delete `synthesis-config.yml` entirely | Treated as `allow_hub_sharing: false` — local-only mode | Immediate |

No CLI command needed, no registration step, no PR to the hub. Edit the file, commit, done.

### Dual-consent for hub-side registration

For the hub to scan a project, **both sides must agree**:

**Hub side** — `config/repos.yml`:

```yaml
repositories:
  - repo: owner/project-a
    stacks: [fastapi-python]
    share_synthesized: true    # Hub wants to scan this repo
```

**Project side** — `.claude/synthesis-config.yml`:

```yaml
allow_hub_sharing: true          # Project agrees to be scanned
```

If either side is `false` or missing, no scanning occurs. Either side can veto independently.

`/synthesize-hub` checks both flags before extracting any patterns. If the hub has `share_synthesized: true` but the project's config says `false` (or doesn't exist), the repo is skipped silently.

### Visibility into what gets extracted

When the hub scans a bilateral-sync project, the project owner needs to know what was picked up. Two levels of visibility:

**Default: attribution in sync PRs.** When `sync_to_projects.py` pushes a new or updated pattern to the project, the PR body includes which of their patterns contributed to the generalization:

```
## New pattern: typed-api-response-envelope

This pattern was generalized from synthesized patterns across 5 projects,
including this one.

Your contributing patterns:
  - rules/typed-api-envelope.md → sanitized and clustered with 4 similar patterns

Patterns scanned but not used (no cluster match):
  - skills/db-migration-check/SKILL.md (unique to your project)
  - rules/retry-policy.md (only 1 other project matched — below 3-project threshold)
```

This is the minimum — project owners see what happened when something actionable arrives. Scans that produce no results generate no noise.

**Opt-in: scan log file.** For teams that want full auditability, add `scan_log: true` to `synthesis-config.yml`. After each scan cycle, `/synthesize-hub` includes a `.claude/scan-log.yml` update in the next sync PR:

```yaml
# .claude/scan-log.yml — auto-generated, do not edit
# Full history of hub scan interactions with this project

scans:
  - date: "2026-03-15"
    patterns_scanned: 12
    picked_up:
      - file: rules/typed-api-envelope.md
        cluster: response-wrapper
        cluster_size: 5
      - file: rules/retry-policy.md
        cluster: retry-patterns
        cluster_size: 3
    skipped_private:
      - rules/internal-auth-flow.md
      - rules/billing-logic.md
    skipped_no_match: 7

  - date: "2026-03-08"
    patterns_scanned: 10
    picked_up: []
    skipped_private: 2
    skipped_no_match: 8
```

The log arrives via the same PR mechanism as pattern updates — no extra notification channel. It lives in the project's own repo, reviewable in code review.

### Private patterns: 3-layer protection

Synthesized patterns can reveal internal architecture (e.g., *"auth tokens stored in Redis with prefix `sess:` and 24h TTL"*). Three layers prevent sensitive patterns from leaving the project:

**Layer 1: Auto-flagging by `/synthesize-project`.**

When `/synthesize-project` generates a pattern, it scans the content for sensitive keywords — auth, secret, token, credential, billing, payment, session, encryption, API key, password. If found, the pattern gets `private: true` in its frontmatter automatically:

```yaml
---
name: auth-token-rotation
description: Enforce auth token rotation policy
synthesized: true
private: true        # Auto-flagged — mentions auth/token
---
```

The developer can remove `private: true` if they're fine sharing it. Auto-flagging catches what developers forget — it's a safety net, not a lock.

**Layer 2: Manual `private_patterns` list in `synthesis-config.yml`.**

For patterns that don't trigger keyword detection but are still sensitive (e.g., a deployment pattern that reveals infrastructure topology):

```yaml
private_patterns:
  - rules/internal-auth-flow.md
  - rules/billing-logic.md
  - skills/deploy-pipeline/SKILL.md
```

**Layer 3: Reference stripping in sanitization.**

If a non-private pattern references a private pattern by name, the sanitization pass strips the reference before sharing:

```
Before: "ensure auth tokens are rotated per rules/internal-auth-flow.md"
After:  "ensure auth tokens are rotated per <private-pattern>"
```

This prevents private pattern names from leaking through cross-references in shared patterns.

**How the layers interact during `/synthesize-hub` scanning:**

```
For each pattern in project's .claude/:
  1. Is it in private_patterns list?          → SKIP (never shared)
  2. Does frontmatter have private: true?     → SKIP (auto-flagged or manually marked)
  3. Does it have synthesized: true?          → PROCEED to sanitization
  4. Sanitization strips:
     - File paths → <module_path>
     - Class names → <ClassName>
     - Env vars → $VARIABLE_NAME
     - References to private patterns → <private-pattern>
  5. Sanitized pattern enters clustering
```

A pattern must pass all checks to be shared. Any single layer can block it.

### Privacy guarantees

| Guarantee | Mechanism |
|---|---|
| Source code never leaves the project | `/synthesize-project` runs locally; only pattern files (not source) can be shared |
| Synthesized patterns stay local by default | No sharing without `allow_hub_sharing: true` or explicit `/contribute-practice` |
| Bilateral: you give to get | Hub updates only flow to projects that share back |
| Sensitive patterns auto-detected | `/synthesize-project` flags patterns mentioning auth/secrets/billing/payment as `private: true` |
| Project can mark patterns as private | `private_patterns` list in `synthesis-config.yml` + manual `private: true` in frontmatter |
| Private pattern references stripped | Sanitization replaces cross-references to private patterns with `<private-pattern>` |
| Project-specific details are stripped | Sanitization pass replaces paths, class names, env vars with placeholders |
| Dual consent for hub scanning | Hub `repos.yml` AND project `synthesis-config.yml` must both agree |
| Consent is revocable at any time | Edit one line — takes effect next scan cycle |
| Config file is always present | Generated on first `/synthesize-project` run with sharing OFF — passive reminder |

### What the hub NEVER receives

- Source code files
- Environment variables or secrets
- Git history or commit messages
- File contents beyond `.claude/` directory
- Patterns listed in `private_patterns`
- Anything from projects without explicit bilateral consent

---

## Skill pipeline: how `/synthesize-project` works

The `/synthesize-project` skill runs inside the developer's Claude Code session. It uses the same tools Claude Code already has (Read, Glob, Grep, Write, Bash) — no external API calls (except `recommend.py` for hub provisioning, which reads the local hub registry). The skill follows a **three-phase approach**: hub provisioning, convention discovery, and pattern generation.

### Phase 1: Hub Provisioning (Step 1)

**Goal:** Copy matching hub patterns and generate CLAUDE.md/settings.json for the project.

The skill calls `recommend.py --provision` via Bash. This auto-detects the project's stacks, compares its `.claude/` against the hub registry, and copies missing patterns. Skipped if `--skip-hub` or `--update` is set.

### Phase 2: Discovery (Steps 2-4)

**Goal:** Identify candidate conventions worth encoding as patterns, confirm them with evidence.

The skill's SKILL.md instructs Claude Code to:

1. **Map the project (Step 2):** Use `Glob` to map the file tree, `Read` to examine config files, entry points, and a representative test file
2. **Identify conventions (Step 3):** From the project map, identify 10-20 candidate conventions. Deduplicate against hub patterns copied in Phase 1 — drop any already covered generically by the hub. Track hub overlap count for the summary.
3. **Confirm with evidence (Step 4):** Read the source files identified as evidence. Confirm, reject, or refine each convention. Drop any with >30% counter-evidence.

**Convention identification criteria** (embedded in the skill):

A convention is WORTH encoding when:
- It's a consistent pattern followed across multiple files
- Breaking it would cause bugs, inconsistency, or confusion
- A new developer (or AI) working on the project might not know about it

A convention is NOT worth encoding when:
- It's already enforced by a linter, formatter, or type checker
- It's a language/framework default documented elsewhere
- It's a one-off implementation detail in a single file

### Phase 3: Generation (Steps 5-9)

**Goal:** Read reference material, generate actual patterns, validate, write, and summarize.

The skill instructs Claude Code to:

1. **Load references (Step 5):** Read pattern structure standards and 2-3 existing patterns as format examples — hub patterns are now local from Phase 1
2. **Generate patterns (Step 6):** For each confirmed convention, generate a complete pattern file with `synthesized: true` in frontmatter. Auto-flag sensitive patterns as `private: true`
3. **Validate and write (Step 7):** Run `workflow_quality_gate_validate_patterns.py` on each pattern, drop failures, write to `.claude/`
4. **Generate config (Step 8):** Create `synthesis-config.yml` with sharing OFF if it doesn't exist
5. **Summary (Step 9):** Print combined report showing both hub patterns copied AND project-specific patterns synthesized, with flywheel onboarding box

---

## Few-shot example selection

The quality of synthesized patterns depends heavily on the examples Claude sees. Too many examples waste context. Too few and Claude doesn't understand the format. Wrong examples lead to wrong patterns.

### Selection algorithm

```
select_few_shot_examples(detected_stacks, registry):

  examples = []

  # 1. Always include gold standards (5 patterns, manually curated)
  #    - 2 rules: 1 universal, 1 stack-specific (shows how to be project-specific)
  #    - 2 skills: 1 workflow type, 1 reference type
  #    - 1 agent
  examples += GOLD_STANDARD_PATTERNS

  # 2. Add stack-matched patterns (up to 3)
  for stack in detected_stacks:
      prefix = STACK_PREFIXES[stack]  # e.g., "fastapi-"
      stack_patterns = registry.filter(prefix=prefix)
      examples += stack_patterns[:3]  # first 3 alphabetically (v1)

  # 3. Deduplicate (gold standards might overlap with stack matches)
  examples = deduplicate(examples)

  # 4. Cap at 8 to control token budget (~12K tokens max)
  return examples[:8]
```

### Gold standard patterns

Manually curated list stored in `config/settings.yml`. Criteria for selection:

- Follows all structure standards perfectly (frontmatter, steps, critical rules sections)
- Between 100-300 lines (substantial but not bloated)
- Demonstrates **project-specific language** — not generic advice like "write tests" but specific like "all API endpoints must return through the typed response envelope"
- Includes clear "why" reasoning — not just "do this" but "do this because X causes Y"

For v1, the gold standard list is hardcoded. Later, it can be derived from adoption metrics (patterns used by the most downstream projects = best examples).

### Stack matching

Uses the same prefix detection from `recommend.py`. If the project is detected as `fastapi-python`, include up to 3 `fastapi-*` patterns as examples. This shows Claude what stack-specific patterns look like for the relevant technology.

**New stack (no matching patterns):** Falls back to gold standards only (5 patterns). This is the cold-start scenario — quality is lower but functional. As the flywheel brings in patterns for new stacks, the examples improve.

### Token budget for examples

| Examples | Avg lines per pattern | Tokens | % of Phase 2 input |
|---|---|---|---|
| 5 (gold only) | 200 | ~7K | ~10-14% |
| 8 (gold + stack) | 200 | ~12K | ~16-24% |

This leaves 75-90% of the context for source files and instructions — a good ratio.

---

## Clustering algorithm: `/synthesize-hub`

When the hub maintainer runs `/synthesize-hub` in their Claude Code session, the skill collects synthesized patterns from bilateral-sync projects and groups similar ones, then decides which are generalizable.

### The scale problem

20 projects × 10 patterns each = 200 patterns. Reading and comparing all of them in a single Claude Code session is feasible but needs structure to be effective.

**Solution:** Pre-filter with cheap deterministic operations (Levels 1-2 via Bash/Python), then have Claude Code reason about classification within the pre-filtered groups.

### Three-level pipeline

**Level 1 — Hash (Bash, instant):**

SHA256 of pattern content via a Python helper. Identical patterns across projects form instant clusters. Rare (projects customize) but handles exact copies.

**Level 2 — Structural grouping (Bash, O(n)):**

A Python helper reads frontmatter from all collected patterns and creates a signature: `(type, category, pattern_type)`. Groups patterns with matching signatures.

Example signatures:
- `(rule, correctness, error-handling)` → 12 patterns from 12 projects
- `(rule, consistency, naming)` → 8 patterns from 6 projects
- `(skill, testing, fixture-setup)` → 5 patterns from 5 projects

This typically produces 10-20 groups of 5-15 patterns each.

**Level 3 — Semantic classification (Claude Code reasoning, per group):**

For each structural group, the skill instructs Claude Code to read ALL patterns in the group and reason about them together. This is the key insight — batch comparison within groups, not pairwise across all patterns.

The skill instructs Claude Code to, for each group:

1. **GROUP** patterns into sub-clusters where patterns encode the same underlying convention (same idea expressed in different project-specific terms)
2. **CLASSIFY** each sub-cluster:
   - **GENERALIZABLE:** the principle is universal, breaking it causes real problems (bugs, security issues, test flakiness). Worth adding to hub.
   - **STYLE:** a legitimate preference that varies between projects (naming, file organization, syntax choices). Do NOT generalize.
   - **DIVERGENT:** projects prescribe opposing approaches to the same problem. Do NOT generalize.
3. **DRAFT** a generalized version for each GENERALIZABLE sub-cluster with 3+ projects
4. **FLAG** contradictions between patterns

**Why batch, not pairwise:** 12 patterns at ~150 lines each — Claude Code reads them all and reasons about the group holistically. No pairwise API calls needed.

### Generalizability signals

The LLM uses these signals to classify (included in the system prompt context, not shown above for brevity):

| Signal | Classification |
|---|---|
| Breaking the convention causes bugs | GENERALIZABLE |
| Breaking it causes security issues | GENERALIZABLE |
| Breaking it causes test flakiness | GENERALIZABLE |
| Breaking it causes confusion across team members | GENERALIZABLE |
| It's about naming (camelCase vs snake_case) | STYLE |
| It's about file/directory organization | STYLE |
| It's about syntax preference (class vs function) | STYLE |
| Projects prescribe opposite approaches | DIVERGENT |
| Only 1-2 projects share the convention | TOO RARE (skip) |

### Divergence detection

Divergence is the trickiest case. Two patterns can be about the same topic (high similarity) but prescribe opposite approaches (contradiction):

- Project A: *"Always use class-based views"*
- Project B: *"Always use function-based views"*

These are semantically similar (both about view structure) but contradictory. The batch prompt explicitly asks Claude to flag contradictions. If ANY pair within a sub-cluster contradicts, the entire sub-cluster is classified DIVERGENT.

**Even with strong majority (15 agree, 2 disagree):** Still DIVERGENT. The hub should not impose choices where reasonable disagreement exists. Only patterns where ALL projects converge get generalized.

---

## Cost

### Zero API cost — both skills run inside Claude Code

| Component | Where it runs | API calls | Cost |
|---|---|---|---|
| `/synthesize-project` | Developer's Claude Code session | None | **$0** — covered by their existing Claude Code subscription |
| `/synthesize-hub` | Hub maintainer's Claude Code session | None | **$0** — covered by their existing Claude Code subscription |

Both skills use Claude Code's built-in tools (Read, Glob, Grep, Write, Bash) to read files and reason about patterns. The LLM reasoning happens within the session context — no separate Anthropic API calls are made.

### Context window considerations

While there's no monetary cost, there is a **context budget** to manage within each Claude Code session:

| Skill | Approximate context usage | Concern |
|---|---|---|
| `/synthesize-project` (Step 1: Discovery) | ~15K tokens (file tree + configs + entry points) | Low — fits easily |
| `/synthesize-project` (Step 2: Extraction) | ~50-75K tokens (source files + few-shot examples + standards) | Medium — may need file batching for very large projects |
| `/synthesize-hub` (20 projects) | ~100-150K tokens (200 patterns at ~500 tokens each + reasoning) | Medium — structural pre-grouping keeps individual reads manageable |

**For large projects:** The skill processes conventions in batches if the project has many source files. Conventions that share files go in the same batch.

**For large-scale hub scanning:** The skill processes structural groups one at a time rather than loading all 200 patterns at once. Each group (5-15 patterns) fits comfortably in context.

### If automation is needed later

If the hub wants to run `/synthesize-hub` on a weekly schedule without a human initiating it, GitHub Actions can invoke Claude Code CLI:

```yaml
# .github/workflows/synthesize-hub.yml
- run: claude -p "run /synthesize-hub"
```

This does use API tokens under the hood (Claude Code CLI requires an API key in CI). Estimated cost at that point:

| Scale | Patterns | Estimated API cost per run |
|---|---|---|
| 20 projects, 200 patterns | ~200K context | ~$1-2 (Sonnet) |
| 100 projects, 1000 patterns | ~500K context | ~$5-7 (Sonnet) |

But this is a future optimization — not needed at launch. The hub maintainer running the skill manually is sufficient and free.

### Configuration

```yaml
# config/settings.yml
synthesis:
  max_conventions: 20              # Cap on conventions per project (keeps context manageable)

clustering:
  min_cluster_size: 3              # Minimum projects for generalization
```

---

## What already exists vs. what needs to be built

### Reusable (already built)

| Component | Location | Reuse |
|---|---|---|
| Stack detection | `recommend.py` | Reuse detection logic in Step 1 |
| Pattern validation | `workflow_quality_gate_validate_patterns.py` | Validate all generated output in Step 3 |
| Structure standards | `.claude/rules/pattern-structure.md` | Loaded by skill as reference for pattern generation |
| Portability standards | `.claude/rules/pattern-portability.md` | Loaded by skill as reference for pattern generation |
| Self-containment standards | `.claude/rules/pattern-self-containment.md` | Loaded by skill as reference for pattern generation |
| 3-level dedup (Levels 1-2) | `dedup_check.py` | Hash + structural dedup |
| Project sync | `sync_to_projects.py` | Flow 4 distribution |
| Pattern contribution | `/contribute-practice` skill | Stage 3 of flywheel |
| Freshness checks | `check_freshness.py` | Detect stale synthesized patterns |
| Registry | `registry/patterns.json` | Track synthesized patterns |
| Anthropic SDK | `requirements.txt` | Not needed for skills (only if CI automation is added later) |

### Build status

| Component | Status | Location / Notes |
|---|---|---|
| `/synthesize-project` skill (v2 unified flow) | **DONE** | `core/.claude/skills/synthesize-project/SKILL.md` — 10-step workflow (Steps 0-9), hub provision + synthesis, ~450 lines |
| `/synthesize-hub` skill | **DONE** | `.claude/skills/synthesize-hub/SKILL.md` — 9-step workflow, 261 lines, passes validation |
| Level 1-2 helpers | **Built into skill** | `/synthesize-hub` uses inline Bash commands for hash + structural grouping — no separate Python helpers needed |
| `synthesized: true` frontmatter flag | **Built into skill** | `/synthesize-project` Step 5 adds `synthesized: true` to all generated patterns |
| Gold standard pattern curation | **DONE** | 5 gold standard patterns configured in `config/settings.yml` under `synthesis.gold_standards` |
| Few-shot selection algorithm | **Built into skill** | `/synthesize-project` Step 5 loads stack-matched + universal examples, capped at 8 |
| Sensitive keyword auto-flagging | **Built into skill** | `/synthesize-project` Step 6 scans for auth/secret/billing/payment keywords, sets `private: true` |
| Sanitization pass | **DONE** | `/contribute-practice` Step 4 strips project-specific identifiers, shows preview before submission |
| `.claude/synthesis-config.yml` generation | **Built into skill** | `/synthesize-project` Step 8 generates config with `allow_hub_sharing: false` on first run |
| `share_synthesized` flag in `repos.yml` | **DONE** | Hub-side opt-in flag added to `repos.yml` schema with dual-consent documentation |
| Dual-consent check in `/synthesize-hub` | **Built into skill** | `/synthesize-hub` Step 1 verifies both hub-side and project-side flags |
| `/contribute-practice` sanitization step | **DONE** | Step 4 added: scan, replace, preview sanitized pattern, wait for user confirmation |
| Terminal onboarding output | **Built into skill** | `/synthesize-project` Step 9 prints flywheel box on first run, status line on subsequent |
| Sync PR attribution | **DONE** | `sync_to_projects.py` `build_pr_body()` includes which project patterns contributed to each generalization |
| Scan log (opt-in) | **DONE** | `/synthesize-hub` Step 9 generates `.claude/scan-log.yml` entries for projects with `scan_log: true` |

---

## Skill interface

### Developer-side (in any project directory)

```bash
# Full flow: hub provision + code synthesis — run inside Claude Code
/synthesize-project

# Hub patterns only (no code synthesis) — equivalent to recommend.py --provision
/synthesize-project --skip-synthesis

# Code synthesis only (no hub patterns) — old behavior
/synthesize-project --skip-hub

# Update existing synthesized patterns after codebase changes (skips hub provision)
/synthesize-project --update

# Dry run — show what would be generated without writing
/synthesize-project --dry-run

# Remote mode — fetch from GitHub, create PR
/synthesize-project --repo owner/name
```

### Hub-side (in the hub repo directory)

```bash
# Collect and cluster synthesized patterns from all bilateral-sync projects
/synthesize-hub

# Collect from a single project
/synthesize-hub owner/name
```

### Skill locations

| Skill | Location | Distributed? |
|---|---|---|
| `/synthesize-project` | `core/.claude/skills/synthesize-project/SKILL.md` | **Yes** — copied to downstream projects |
| `/synthesize-hub` | `.claude/skills/synthesize-hub/SKILL.md` | **No** — hub-only operational skill |
