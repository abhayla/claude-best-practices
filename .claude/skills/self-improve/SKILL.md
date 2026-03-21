---
name: self-improve
description: >
  Run the full self-improvement cycle: scan external sources (GitHub, Reddit,
  Twitter), classify discoveries, check against registry, capture session
  learnings, and propose new patterns. Use when starting a session, after
  completing work, or when you want to pull in external best practices.
type: workflow
allowed-tools: "Bash Read Grep Glob Write Edit Skill Agent"
argument-hint: "[--scan] [--learn] [--review] [--full]"
version: "1.0.0"
---

# Self-Improve — Autonomous Learning & Discovery Pipeline

Single entry point for the hub's self-improvement system. Combines external
discovery, session learning, and pattern proposal into one workflow.

**Arguments:** $ARGUMENTS

## Modes

| Mode | Flag | What It Does |
|------|------|-------------|
| **Review** | *(default)* | Show pending discoveries, session stats, and improvement suggestions |
| **Scan** | `--scan` | Search external sources (GitHub, Reddit, Twitter) for new patterns |
| **Learn** | `--learn` | Capture learnings from current session + check failure logs |
| **Full** | `--full` | Run scan + learn + review in sequence |

---

## STEP 1: Parse Mode

Read `$ARGUMENTS` and determine mode:

- `--full` → run Steps 2, 3, 4, 5 in sequence
- `--scan` → run Step 2 only
- `--learn` → run Step 3 only
- No flag or `--review` → run Step 4 only

---

## STEP 2: External Discovery Scan

Search for Claude Code patterns from external sources.

### 2A: GitHub Search

Use the `/github` skill to search for patterns:

```
Skill("github", args="search code SKILL.md path:.claude/skills language:markdown stars:>10")
```

For each result, extract name, type, content preview, and whether it has
proper frontmatter.

### 2B: Reddit Scan

Use the `/reddit` skill to search r/ClaudeAI for recent tips:

```
Skill("reddit", args="search r/ClaudeAI claude code tips sort:new limit:10")
```

Extract actionable patterns from high-engagement posts (upvotes > 10).

### 2C: Register Discoveries

For each finding, register via the discovery adapter:

```bash
PYTHONPATH=. python scripts/discovery_adapter.py --add '{
  "name": "<pattern-name>",
  "type": "<skill|agent|rule|hook>",
  "source": "<github:owner/repo|reddit:r/subreddit|twitter:@handle>",
  "source_trust": "<high|medium|low>",
  "content": "<first 200 chars>",
  "has_frontmatter": true,
  "has_steps": false,
  "community_signal": 15
}'
```

Report: how many new discoveries, how many duplicates, how many already in registry.

---

## STEP 3: Session Learning Capture

### 3A: Run Learn-n-Improve

Invoke the learning skill to capture session outcomes:

```
Skill("learn-n-improve", args="session")
```

### 3B: Check Failure Logs

Read the post-failure capture log for this session:

```bash
SESSION_ID=${CLAUDE_SESSION_ID:-default}
cat "${TMPDIR:-/tmp}/claude-failure-log/session-$SESSION_ID.jsonl" 2>/dev/null
```

If failures exist, feed them into the learning database as error-fix-lesson
triples (even if the fix hasn't been found yet — the error context is valuable).

### 3C: Wire Test Knowledge

If test-related learnings were captured, also feed them into `/test-knowledge`:

```
Skill("test-knowledge", args="add <learning-summary>")
```

---

## STEP 4: Review Pending Improvements

### 4A: Discovery Pipeline Status

```bash
PYTHONPATH=. python scripts/discovery_adapter.py --stats
```

### 4B: Auto-Queue Candidates

```bash
PYTHONPATH=. python scripts/discovery_adapter.py --auto-queue
```

If auto-queue candidates exist (>=85 confidence, high trust), present them
to the user with a recommendation to import.

### 4C: Convergent Evolution

```bash
PYTHONPATH=. python scripts/discovery_adapter.py --convergent
```

Patterns found in 3+ independent sources are strong candidates for hub
promotion. Highlight these prominently.

### 4D: Learning Pattern Alerts

Check `.claude/learnings.json` for pattern detection triggers:
- Tags appearing in >30% of learnings → systemic issue
- Files with 3+ learnings → fragile code hotspot
- Workflow patterns seen 3+ times → skill promotion candidate

### 4E: Source Health Check

Check `config/urls.yml` for degraded or expired sources:

```bash
PYTHONPATH=. python scripts/check_freshness.py
```

Report any expired or degraded sources that need attention.

---

## STEP 5: Propose Improvements

Based on findings from Steps 2-4, propose concrete actions:

| Finding | Proposed Action |
|---------|----------------|
| Auto-queue candidate (>=85, high trust) | "Import pattern X — run `/skill-factory create <name>`" |
| Convergent pattern (3+ sources) | "Promote to hub — pattern X found in N independent sources" |
| Systemic learning tag (>30%) | "Create rule for <tag> — run `/claude-guardian`" |
| Workflow pattern (3+ repeats) | "Create skill — run `/writing-skills`" |
| Degraded source | "Review source <url> — trust downgraded due to <reason>" |
| Expired source | "Re-verify or remove <url> — expired <N> days ago" |

Present findings as a prioritized list. Each proposal requires user approval
before execution.

---

## CRITICAL RULES

- MUST NOT auto-import patterns without user approval — auto-queue only PRESENTS candidates
- MUST NOT degrade source trust without evidence (test failure, user correction, or pattern rejection)
- MUST run discovery adapter dedup before registering any finding — never create duplicate entries
- MUST cite the source for every discovery: "found in github:owner/repo" or "seen on reddit:r/ClaudeAI"
- Session learning capture (Step 3) MUST run even if external scan is skipped
- Default mode is review (read-only) — scanning and learning require explicit flags
