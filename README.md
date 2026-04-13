# Claude Best Practices Hub

A curated knowledge hub of **224 battle-tested patterns** (agents, skills, rules, hooks) for [Claude Code](https://claude.ai/code). Copy them to your project, or let `/synthesize-project` analyze your codebase and generate project-specific patterns automatically.

---

## Getting Started

### Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed and working
- Git installed
- A project you want to add Claude Code patterns to

### Step-by-step setup

**Step 1: Clone this hub repo**

```bash
git clone https://github.com/abhayla/claude-best-practices.git
cd claude-best-practices
```

**Step 2: Install dependencies** (only needed for smart provisioning or synthesis)

```bash
pip install -r scripts/requirements.txt
```

**Step 3: Choose how to provision your project**

You have three options. Pick the one that fits your needs:

---

#### Option A: Copy everything (simplest, no dependencies needed)

```bash
# Copy all patterns to your project
cp -r core/.claude/ /path/to/your/project/.claude/
```

Then delete what you don't need:
```bash
# Example: remove Android patterns if you don't use Android
cd /path/to/your/project
rm -f .claude/rules/android-*
rm -rf .claude/skills/android-*
rm -f .claude/agents/android-*
```

---

#### Option B: Smart provisioning (recommended for most users)

This auto-detects your project's tech stacks and copies only matching patterns:

```bash
# Run from the hub repo directory
cd claude-best-practices
PYTHONPATH=. python scripts/recommend.py --local /path/to/your/project --provision
```

This will:
- Detect your stacks (e.g., FastAPI + Android + Firebase)
- Copy matching hub patterns to your project's `.claude/`
- Generate a `CLAUDE.md` and `settings.json` for your project
- Show you what was copied

---

#### Option C: Full synthesis (most powerful — hub patterns + project-specific patterns)

This does everything Option B does, PLUS reads your actual source code and generates patterns unique to YOUR codebase.

```bash
# Step C1: First, provision your project with hub patterns (this also copies /synthesize-project skill)
cd claude-best-practices
PYTHONPATH=. python scripts/recommend.py --local /path/to/your/project --provision

# Step C2: Now open Claude Code in YOUR project
cd /path/to/your/project
claude

# Step C3: Inside Claude Code, run the synthesis skill
/synthesize-project --skip-hub
```

`--skip-hub` skips the hub provisioning step (you already did it in C1) and goes straight to analyzing your code.

**What happens during synthesis:**
1. Claude Code reads your project's config files, entry points, and test files
2. Identifies 10-20 conventions specific to your codebase
3. **Shows you what it found** — you review and approve before anything is generated
4. Generates rules (constraints), skills (workflows), and agents (review personas)
5. Writes them to your `.claude/` directory

**For remote repos** (you don't need the code locally):

```bash
# Run from the hub repo directory — creates a PR on the target repo
cd claude-best-practices
claude
/synthesize-project --repo owner/repo-name
```

---

### After setup

Once your project has a `.claude/` directory, you can use all the skills directly:

```
/development-loop   Full build cycle: ideate → plan → implement → verify → commit
/implement          Build a feature with TDD workflow
/fix-issue 42       Fix GitHub issue #42
/fix-loop           Iterative fix until tests pass
/debugging-loop     Structured bug diagnosis → fix → verify → learn
/tdd                Strict red-green-refactor cycle
/continue           Resume from previous session
/skill-master       Find the right skill for any task
```

### Keeping updated

```bash
# Inside Claude Code in your project — pulls latest from hub
/update-practices
```

---

## What's Inside

| Component | Count | Description |
|-----------|-------|-------------|
| **Agents** | 37 | Sub-agents for code review, debugging, testing, git, planning, security, docs — including 8 workflow-master orchestrators |
| **Skills** | 155 | Slash-command workflows: `/implement`, `/fix-loop`, `/tdd`, `/synthesize-project`, `/development-loop`, and more |
| **Rules** | 24 | Scoped coding rules for workflow, testing, FastAPI, Android, Compose, Firebase, etc. |
| **Hooks** | 8 | Auto-format, secret scanning, dangerous command blocking, context monitoring |

See [`core/.claude/README.md`](core/.claude/README.md) for the full catalog with descriptions.

### Workflow Master Orchestration

Skills don't just run independently — they coordinate as teams. Each of the 8 workflow groups has a **master-agent** that orchestrates its skills end-to-end with shared context, artifact contracts, and verification gates:

```
┌───────────────────────────┬────────────────────────────────────────────────┬──────────────────────────────────┐
│         Workflow          │                     Agent                      │         Slash Command            │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Development Loop          │ development-loop-master-agent                  │ /development-loop                │
│   ideate → plan →         │   dispatches: plan-executor-agent,             │                                  │
│   implement → verify →    │   planner-researcher-agent                     │                                  │
│   commit                  │                                                │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Testing Pipeline          │ testing-pipeline-master-agent                  │ /testing-pipeline-workflow        │
│   TDD → fix-loop →        │   dispatches: test-pipeline-agent,             │                                  │
│   auto-verify → E2E →     │   e2e-conductor-agent, tester-agent,           │                                  │
│   quality gates           │   test-failure-analyzer-agent                  │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Debugging Loop            │ debugging-loop-master-agent                    │ /debugging-loop                  │
│   diagnose → fix →        │   dispatches: debugger-agent,                  │                                  │
│   verify → learn          │   test-failure-analyzer-agent                  │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Code Review               │ code-review-master-agent                       │ /code-review-workflow            │
│   quality gates → PR →    │   dispatches: code-reviewer-agent,             │                                  │
│   feedback resolution     │   security-auditor-agent                       │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Documentation             │ documentation-master-agent                     │ /documentation-workflow           │
│   ADR → API docs →        │   dispatches: docs-manager-agent               │                                  │
│   structure → staleness   │                                                │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Session Continuity        │ session-continuity-master-agent                │ /session-continuity              │
│   save → handover         │   dispatches: session-summarizer-agent         │                                  │
│   (or restore → briefing) │                                                │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Learning                  │ learning-self-improvement-master-agent         │ /learning-self-improvement       │
│   capture → detect        │   dispatches: session-summarizer-agent,        │                                  │
│   patterns → validate     │   context-reducer-agent                        │                                  │
├───────────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────┤
│ Skill Authoring           │ skill-authoring-master-agent                   │ /skill-authoring-workflow        │
│   author → validate →     │   dispatches: skill-author-agent               │                                  │
│   register                │                                                │                                  │
└───────────────────────────┴────────────────────────────────────────────────┴──────────────────────────────────┘
```

Each master-agent works **standalone** (invoke directly) or **dispatched** by `project-manager-agent` as part of the full PRD-to-Production pipeline. The orchestration hierarchy follows a 4-tier model:

```
T0  project-manager-agent          ← full pipeline orchestrator
     │
T1  ├── development-loop-master    ← workflow master (standalone or dispatched)
     │    │
T2  │    ├── plan-executor-agent   ← sub-orchestrator
     │    │
T3  │    └── (worker agents)       ← leaf workers (Skill() only)
     │
T1  ├── testing-pipeline-master
     │    │
T2  │    ├── e2e-conductor-agent
     │    │    │
T3  │    │    ├── test-scout-agent
     │    │    ├── visual-inspector-agent
     │    │    └── test-healer-agent
     │    │
T2  │    └── test-pipeline-agent
     │
T1  └���─ ... (6 more workflow masters)
```

Context passes between steps automatically — no skill starts from scratch. See [`docs/specs/workflow-master-agents-spec.md`](docs/specs/workflow-master-agents-spec.md) for the full architecture.

---

## How It Works

### The two types of patterns

```
Hub patterns (generic, reusable)          Project-specific patterns (yours)
  core/.claude/rules/testing.md             .claude/rules/api-result-wrapper.md
  core/.claude/skills/tdd/SKILL.md          .claude/skills/add-sqlalchemy-model/SKILL.md
  core/.claude/agents/code-reviewer.md      .claude/agents/meal-plan-reviewer.md
        |                                          |
        |  copied by recommend.py --provision      |  generated by /synthesize-project
        +------ both end up in your .claude/ ------+
```

**Hub patterns** are generic best practices that work in any project of that stack. `/implement`, `/fix-loop`, `/tdd` — these are the same everywhere.

**Project-specific patterns** are conventions unique to YOUR codebase. "All endpoints must return through `ApiResult[T]`" or "Adding a Room entity requires updating 6 files" — only `/synthesize-project` can generate these because it reads your actual code.

### `/synthesize-project` — provision + synthesize in one command

```
/synthesize-project                     Full flow: hub provision + code synthesis
/synthesize-project --repo owner/name   Remote: analyze a GitHub repo, create a PR
/synthesize-project --skip-hub          Synthesis only (no hub patterns)
/synthesize-project --skip-synthesis    Hub patterns only (no code analysis)
/synthesize-project --update            Re-scan after codebase changes
/synthesize-project --dry-run           Preview without writing files
```

**What it does:**

1. **Provisions hub patterns** — runs `recommend.py --provision` to copy matching stack patterns
2. **Maps your project** — reads config files, entry points, test files
3. **Identifies conventions** — finds 10-20 candidate patterns (rules, skills, agents) and presents them for your review
4. **Gathers evidence** — reads source files to confirm each convention, shows you what it found
5. **Generates patterns** — creates `.claude/` files with proper frontmatter, validated against hub standards
6. **In remote mode** — creates a PR on the target repo with all generated patterns

The skill presents detailed findings at two checkpoints so you see exactly what's being generated before any files are written.

### `/synthesize-hub` — generalize patterns across projects (hub maintainer only)

When multiple projects independently synthesize similar patterns, the hub can learn from them:

```
/synthesize-hub              Scan all bilateral-sync projects
/synthesize-hub owner/repo   Scan a specific project
```

**What it does:**

1. Collects `synthesized: true` patterns from downstream projects (with bilateral consent)
2. Clusters similar patterns using 3-level dedup (hash, structural, semantic)
3. Classifies clusters: GENERALIZABLE (add to hub) vs STYLE (skip) vs DIVERGENT (skip)
4. Drafts generalized patterns using the hub's creator tools (`/writing-skills`, `/claude-guardian`)
5. Creates a PR for hub maintainer review

This is how the hub grows smarter over time — conventions that recur across 3+ projects get generalized into portable hub patterns.

---

## Available Stacks

Stack-specific patterns use filename prefixes. `recommend.py` auto-detects your stacks:

| Stack | Prefix | What it adds |
|-------|--------|-------------|
| `fastapi-python` | `fastapi-*` | API testing agent, DB admin agent, migration/deploy/test skills, backend rules |
| `android-compose` | `android-*` | Compose agent, ADB testing, test runner skills, Android/Compose rules |
| `ai-gemini` | `ai-gemini-*` | Gemini API reference skill |
| `firebase-auth` | `firebase-*` | Firebase dev, AI, Data Connect, test skills |
| `react-nextjs` | `react-*` | React Native dev, E2E testing skills |
| `flutter` | `flutter-*` | Flutter dev, E2E testing skills |
| `vue-nuxt` | `vue-*` / `nuxt-*` | Vue dev, Nuxt dev, Vue test skills |
| `bun-elysia` | `bun-elysia-*` | Bun + Elysia dev rules, test skill |

Universal patterns (no prefix) are included for all stacks.

---

## Key Skills

| Skill | What it does |
|-------|-------------|
| `/synthesize-project` | Provision hub patterns + generate project-specific patterns from your codebase |
| `/implement` | Structured feature implementation with TDD workflow |
| `/fix-issue` | Analyze and fix a GitHub issue end-to-end |
| `/fix-loop` | Iterative fix cycle until tests pass |
| `/tdd` | Strict red-green-refactor cycle |
| `/continue` | Resume work from a previous session |
| `/writing-plans` | Generate detailed implementation plans |
| `/brainstorm` | Explore approaches before implementing |
| `/security-audit` | Static analysis with CodeQL/Semgrep |
| `/update-practices` | Pull latest patterns from hub |
| `/contribute-practice` | Submit a local pattern to the hub |
| `/skill-master` | Find the right skill for any task |
| `/development-loop` | Full build cycle: ideate → plan → implement → verify → commit |
| `/testing-pipeline-workflow` | Full test chain: TDD → fix → verify → quality gates |
| `/debugging-loop` | Structured diagnosis → fix → verify → learn |
| `/code-review-workflow` | Quality gates → PR → review feedback |

See [`core/.claude/README.md`](core/.claude/README.md) for all 155 skills.

---

## Repository Structure

```
core/.claude/                  # Distributable patterns (copy to your project)
  agents/                      #   37 specialized sub-agents (incl. 8 workflow masters)
  skills/                      #   155 slash-command workflows
  rules/                       #   24 scoped coding rules
  hooks/                       #   8 hook examples
  settings.json                #   Minimal defaults
  CLAUDE.md.template           #   Template for project CLAUDE.md

.claude/                       # Hub-only operational config (NOT distributed)
  skills/synthesize-hub/       #   Collect + generalize patterns from projects
  skills/scan-repo/            #   Scan downstream repos
  skills/scan-url/             #   Scan internet sources
  rules/rule-curation.md       #   Curation standards for hub patterns

config/                        # Hub configuration
  repos.yml                    #   Registered downstream projects
  settings.yml                 #   Scan schedules, dedup thresholds, gold standards

config/workflow-contracts.yaml  # Workflow DAGs with artifact contracts (8 workflows)
registry/patterns.json         # Machine-readable index of all 225 patterns
scripts/                       # Python tools (bootstrap, recommend, validate, sync, docs)
docs/                          # Dashboard, getting started, sync architecture, flywheel
```

---

## The Synthesize Flywheel

The hub isn't just a static library — it's a **pattern compiler** that gets smarter with every project:

```
Your project code
       |
       v
  /synthesize-project ──> project-specific .claude/ patterns
       |                          |
       |                    (patterns that survive real usage)
       |                          |
       v                          v
  /contribute-practice ──> hub PR (sanitized, generalized)
       |
       v
  Hub grows smarter ──> better synthesis for the NEXT project
```

**Sharing is opt-in and bilateral.** By default, everything stays local. To participate in the flywheel, set `allow_hub_sharing: true` in `.claude/synthesis-config.yml`. See [docs/synthesize-flywheel.md](docs/synthesize-flywheel.md) for the full design.

---

## Contributing

Found a pattern that works well in your project?

1. Run `/contribute-practice <pattern-path>` inside Claude Code — validates, sanitizes project-specific content, and creates a PR
2. Or add it directly to `core/.claude/` and open a PR. Run `PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py` first.

All patterns must pass the [curation standards](docs/synthesize-flywheel.md): real source, real problem, not already covered.

---

## License

MIT
