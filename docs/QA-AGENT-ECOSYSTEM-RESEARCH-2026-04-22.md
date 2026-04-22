# QA Agent Ecosystem — GitHub Research

**Date:** 2026-04-22
**Researcher:** Claude Code (Opus 4.7)
**Trigger:** Audit of `claude-best-practices` hub QA architecture (4-tier orchestration, dual-signal verdict, confidence-gated auto-healing) against comparable public repos.
**Method:** 9 GitHub repo searches via `gh` CLI + 2 web searches + deep-inspection of the 2 closest architectural analogues.

---

## TL;DR

- The closest architectural peer is **`fugazi/test-automation-skills-agents`** (112⭐, actively maintained April 2026) — Claude Code QA plugin with 13 agents + 10 skills.
- The closest functional peer is **`nirarad/playwright-ai-qa-agent`** — standalone TS app with confidence-gated auto-healing that mirrors our classification + confidence pattern.
- **No public repo combines all of:** 4-tier orchestration + dual-signal verdict (ARIA + screenshot) + config-driven DAG + per-tier retry budgets + stack-scoped distribution. This hub's architecture is ahead of the publicly visible field.
- Lessons worth stealing: **(1)** deterministic pre-classification short-circuit (nirarad), **(2)** direct browser control for healers via Playwright MCP (fugazi), **(3)** Constitution pattern inlined in each agent body for primacy (fugazi), **(4)** standalone CI binary (nirarad), **(5)** GitHub Issue auto-creation for real bugs (nirarad).

---

## Search strategy

Queries executed via `gh search repos`:
1. `AI agent testing`
2. `self-healing test automation`
3. `visual regression AI`
4. `playwright AI`
5. `browser agent`
6. `LLM test automation`
7. `test automation LLM`
8. `multi-agent testing framework`
9. `autonomous software engineer bug fix`

Web searches:
1. `top open source AI agent QA test automation frameworks 2026 self-healing visual regression GitHub`
2. `GitHub "claude code" agents skills test automation defect detection auto-fix 2026 repository`

Deep-inspection targets (full file reads via `gh api`):
- `fugazi/test-automation-skills-agents` — `qa-orchestrator.agent.md`, `playwright-test-healer.agent.md`, `flaky-test-hunter.agent.md`, `orchestration-workflow.instructions.md`
- `nirarad/playwright-ai-qa-agent` — `orchestrator.ts`, `classifier.ts`, tree listing

---

## Repos found, ranked by architectural relevance

### Tier A — Direct architectural peers

#### 1. `fugazi/test-automation-skills-agents` — 112⭐ (actively maintained)
URL: https://github.com/fugazi/test-automation-skills-agents

**QA plugin marketplace for Claude Code with 13 specialized agents + 10 skills. This is the closest analogue to this hub.**

- **Layout:** `agents/*.agent.md`, `skills/<name>/SKILL.md`, `instructions/*.instructions.md` — matches our `.claude/agents/`, `.claude/skills/`, `.claude/rules/` layout.
- **Orchestration:** `qa-orchestrator` agent routes via declarative `handoffs:` in YAML frontmatter. **Flat 2-tier pattern**: orchestrator ↔ specialists. No depth cap.
- **Specialist agents:** `playwright-test-planner`, `playwright-test-generator`, `playwright-test-healer`, `flaky-test-hunter`, `test-refactor-specialist`, `api-tester-specialist`, `selenium-test-specialist`, `selenium-test-executor`, `architect`, `docs-agent`, `implementation-plan`, `principal-software-engineer`.
- **Workflow:** 8-step "Test Orchestration Pattern" (TOP) — Initialize → Explore → Plan → Generate → Implement → Review → Refactor → Run.
- **"Constitution" pattern:** every agent body inlines non-negotiable MUST DO / WON'T DO at the top. Examples:
  - Selector priority: `getByRole > getByLabel > getByPlaceholder > getByText > getByTestId > CSS`
  - Never `waitForTimeout()` or `waitForLoadState('networkidle')`
  - Never XPath
  - Web-first assertions only
  - External test data (no hardcoding)
- **Browser control for healer:** `playwright-test-healer` agent has MCP tools `browser_snapshot`, `browser_evaluate`, `browser_console_messages`, `browser_network_requests`, `test_debug`, `test_run`. Can *drive a real browser* during diagnosis.
- **Models:** Claude Opus 4.5/4.6.
- **Distribution:** `.claude-plugin/marketplace.json` — Claude Code plugin marketplace.

**Gaps vs our hub:**
- No tiered depth limits (T0/T1/T2/T3).
- No dual-signal verdict (exit-code only).
- No global or per-tier retry budget.
- No screenshot-as-authoritative-verdict for UI tests.
- No external config DAG (handoffs are inlined in agent frontmatter).
- No visual proof review step.
- No contradiction detection across stages.

#### 2. `nirarad/playwright-ai-qa-agent` — 4⭐
URL: https://github.com/nirarad/playwright-ai-qa-agent

**Standalone TypeScript app (runs in CI after Playwright tests, not a Claude Code plugin).**

- **Structure:** `agent/` directory with `orchestrator.ts`, `classifier.ts`, `healer.ts`, `reporter.ts`, `context.ts`, `config.ts`, `env.ts`, plus `agent/llm/` with clients for Anthropic, Google, Ollama, OpenAI, Mock.
- **Classifier categories:** `BROKEN_LOCATOR | REAL_BUG | FLAKY | ENV_ISSUE` — maps 1:1 to our `SELECTOR / LOGIC_BUG / FLAKY_TEST / INFRASTRUCTURE`.
- **Confidence-gated healing:** `AGENT_CONFIDENCE_THRESHOLD` env var with identical semantics to our `healing.confidence_threshold: 0.85`.
- **Deterministic pre-classification (novel):** if error matches `Locator:` regex, force-classify as BROKEN_LOCATOR with 0.93 confidence *before* calling LLM. Saves an LLM call and eliminates classification variance for clear-cut cases. Our pre-classification heuristics table has this idea but isn't codified as a hard short-circuit.
- **Actions on classification:**
  - `REAL_BUG` → auto-creates GitHub Issue with full diagnosis and repro steps (`enableBugIssue` flag)
  - `BROKEN_LOCATOR` → auto-opens PR with locator heals (`enableHealPr` flag)
  - `FLAKY` / `ENV_ISSUE` → logged, no action
- **Limits:** `maxFailuresPerRun`, `interRequestDelayMs`, LLM retry with exponential backoff (`llmMaxAttempts`, `llmRetryInitialDelayMs`, `llmRetryMaxDelayMs`).
- **CI-aware:** `AGENT_ENABLE_IN_CI` gate — agent skips entirely if not explicitly enabled for CI.
- **Cursor rules:** ships with `.cursor/rules/` including `healer-single-locator-noop-guard.mdc` and `ci-agent-guardrails.mdc`.

**Why interesting despite low stars:** architecturally mature, production-minded code; small because it's narrow-scope (only Playwright, only Node CI).

### Tier B — Self-healing frameworks (smaller, lessons only)

| Repo | Stars | URL | Note |
|---|---|---|---|
| `darkokos21/self-healing-framework-playwright` | 4 | https://github.com/darkokos21/self-healing-framework-playwright | ML-ranking of selector candidates with scikit-learn confidence scores. Separate FastAPI healer service. |
| `Usman-alpha/AI-SelfHealing-Agent` | 1 | https://github.com/Usman-alpha/AI-SelfHealing-Agent | Claude + LangGraph + Playwright, Python. |
| `gkushang/openai-self-healing-tests` | 0 | https://github.com/gkushang/openai-self-healing-tests | Historical reference — early OpenAI-driven healer. |
| `mdemir3/testalyst` | 0 | https://github.com/mdemir3/testalyst | LangGraph multi-agent BDD + UI + API self-heal, MCP-based. Early stage. |
| `Bhargavchirumamilla/BDDTestAutomation-LLM-AI-Self-Auto-healing` | 1 | — | Java BDD framework with LLM healing. |

### Tier C — Browser-agent infrastructure (adjacent, not QA-native)

| Repo | Stars | URL | Note |
|---|---|---|---|
| `browserbase/stagehand` | 22.3K | https://github.com/browserbase/stagehand | SDK layer for browser agents. People build QA on top, but it's not QA itself. |
| `magnitudedev/browser-agent` | 4.0K | https://github.com/magnitudedev/browser-agent | Vision-first browser agent — vision-before-DOM. Interesting for visual verification. |
| `lmnr-ai/index` | 2.3K | https://github.com/lmnr-ai/index | SOTA browser agent for autonomous tasks. |
| `Planetary-Computers/autotab-starter` | 1.0K | https://github.com/Planetary-Computers/autotab-starter | Build browser agents for real-world tasks. |
| `m1guelpf/browser-agent` | 726 | https://github.com/m1guelpf/browser-agent | Rust + GPT-4 browser agent. |
| `CursorTouch/Web-Use` | 247 | https://github.com/CursorTouch/Web-Use | CDP-powered browser agent. |

These are **operators**, not verifiers. Not directly comparable.

### Tier D — Claude Code skill ecosystems (meta-patterns)

| Repo | URL | Note |
|---|---|---|
| `wshobson/agents` | https://github.com/wshobson/agents | Coordinates 7 agents: backend-architect → database-architect → frontend-developer → test-automator → security-auditor → deployment-engineer → observability-engineer. Linear pipeline, not QA-focused. |
| `affaan-m/everything-claude-code` | https://github.com/affaan-m/everything-claude-code | 48 agents + 183 skills, Claude Code Hackathon (Cerebral Valley x Anthropic, Feb 2026), 1282 tests @ 98% coverage. |
| `VoltAgent/awesome-agent-skills` | https://github.com/VoltAgent/awesome-agent-skills | Curated list of 1000+ skills including Playwright patterns. |
| `levnikolaevich/claude-code-skills` | https://github.com/levnikolaevich/claude-code-skills | Plugin suite + bundled MCP servers covering full delivery lifecycle. |
| `darcyegb/ClaudeCodeAgents` | https://github.com/darcyegb/ClaudeCodeAgents | QA agents for Claude Code (small, focused). |
| `BehiSecc/awesome-claude-skills` | https://github.com/BehiSecc/awesome-claude-skills | Curated Claude Skills list. |
| `langwatch/langwatch` | 3.2K | https://github.com/langwatch/langwatch | LLM evaluation and AI agent testing platform (testing the LLM, not testing via LLM). |

---

## Architecture comparison — them vs us

| Capability | fugazi | nirarad | claude-best-practices (ours) |
|---|---|---|---|
| **Orchestration depth** | Flat (2-tier) | Flat (single binary) | **4-tier (T0→T1→T2→T3) with depth cap** |
| **Config-driven DAG** | Handoffs inline in agent frontmatter | Hardcoded flow | **External `workflow-contracts.yaml` with gate expressions** |
| **Dual-signal verdict** | No — exit code only | No — exit code only | **Yes — ARIA YAML + screenshot** |
| **Visual proof review** | No | No | **Yes (auto-verify Step 2.5, mandatory for UI tests)** |
| **Confidence-gated healing** | Partial (decision-autonomy levels) | **Yes (threshold env var)** | **Yes (0.85 default)** |
| **Deterministic pre-classification** | No | **Yes (Locator regex → BROKEN_LOCATOR @ 0.93)** | Partial (heuristics table, not hard-coded short-circuit) |
| **Global retry budget** | No | `maxFailuresPerRun` (partial) | **Yes (15 default, per-tier enforced)** |
| **State SSOT** | Implicit in agent context | JSON results file | **Per-scope state file (`.pipeline/` / `.workflows/`)** |
| **Direct browser control for healer** | **Yes (Playwright MCP)** | Via test logs only | No (file edits via fix-loop) |
| **Auto-fix action surface** | File edits | **GitHub Issue + PR** | Local commit + file edits |
| **Constitution (inlined rules)** | **Yes, per-agent body** | Implicit in prompts | In `.claude/rules/` (separated from agents) |
| **Stack-scoped distribution** | Single config | Single app | **Yes (`fastapi-*`, `android-*`, `react-*`, etc.)** |
| **Standalone CI runnable** | Needs Claude Code | **Yes (standalone CI binary)** | Needs Claude Code |
| **Quarantine + probe-run recovery** | No | No | **Yes (flakiness_score + decay_window)** |
| **Cross-stage contradiction detection** | No | No | **Yes (aggregator flags)** |
| **Self-improving telemetry** | No | No | **Yes (duration_hints, flakiness_score from history)** |

---

## Genuine lessons worth stealing (ranked)

### 1. Constitution pattern (from fugazi)
Every agent body opens with non-negotiable MUST DO / WON'T DO. We push those to `.claude/rules/*.md` for context savings — but for *safety-critical* rules (no XPath, no hard waits, selector priority), inlining in each agent body gives primacy reinforcement. LLMs bias toward beginnings and endings of prompts.

**Apply to:** `test-healer-agent` (inline "never auto-fix LOGIC_BUG", "never exceed retry budget"), `visual-inspector-agent` (inline "screenshot is authoritative for UI tests"), `test-scout-agent` (inline "write state after every test").

### 2. Deterministic pre-classification short-circuit (from nirarad)
Before calling the LLM classifier, regex-match the error for unambiguous patterns and force-assign the category with a fixed confidence.

Example (nirarad's actual pattern):
```typescript
const RULE_BASED_BROKEN_LOCATOR_CONFIDENCE = 0.93
const LOCATOR_RULE_EXPLANATION_ONLY_HINT = `Deterministic rule (non-negotiable): Playwright reported locator-resolution failure, so the failure category is fixed as BROKEN_LOCATOR. Your JSON "category" and "confidence" will be ignored; output valid JSON with the usual schema anyway.`
```

**Apply to:** `test-failure-analyzer-agent`. Add regex gate for `Locator:`, `TimeoutError`, `ECONNREFUSED`, `no such table` → force category + 0.9+ confidence, skip LLM call. Saves cost AND eliminates classification variance.

### 3. Direct browser control for healers (from fugazi)
Their `playwright-test-healer` has MCP tools that let it inspect the live app during healing. Our healer (via `/fix-loop`) is blind: it only sees stderr.

**Apply to:** add Playwright MCP tools to `test-healer-agent` — `browser_snapshot`, `browser_evaluate`, `browser_console_messages`, `browser_network_requests`. Lets the healer actually *see* why the selector failed instead of guessing from error text. Major accuracy improvement for SELECTOR classification healing.

### 4. Standalone CI mode (from nirarad)
Their agent runs as a plain Node process in CI — no Claude Code required. Reads `test-results/*.json`, drives the fix/heal/report cycle headlessly.

**Apply to:** build a Python entry point for `testing-pipeline-master-agent` that operates without the Claude Code harness. Would let this hub's QA pipeline run in GitHub Actions / GitLab CI without an interactive agent.

### 5. GitHub Issue auto-creation for REAL_BUG (from nirarad)
When a failure classifies as LOGIC_BUG (not auto-fixable), open a GitHub Issue with full diagnosis, screenshots, and reproduction steps automatically.

**Apply to:** extend `test-healer-agent` or `testing-pipeline-master-agent` aggregation step — for every `known_issues` entry with classification LOGIC_BUG or VISUAL_REGRESSION, call `gh issue create` with the diagnosis. Closes the loop from detection to tracked work.

### 6. MCP-mediated inspection (from fugazi + testalyst)
Both use MCP servers for browser control and healing. testalyst has `mcp_servers/mcp_browser.py` and `mcp_servers/mcp_healer.py` as separate servers. Cleaner separation than our Agent-dispatches-Agent model.

**Apply to:** longer-term architectural consideration — could extract the healer as an MCP server so it's reusable across orchestrators.

---

## What we do that they don't (our differentiators)

1. **4-tier orchestration with depth enforcement** — no other repo encodes tier discipline. Most are flat or 2-level.
2. **Dual-signal verdict as a design principle** — screenshot authority for UI is a stance no other repo takes; they all treat exit code as authoritative.
3. **Config-driven DAG with artifact contracts and gate expressions** — others hardcode orchestration in agent bodies.
4. **Per-stage retry budget composed with global budget** — nirarad has a partial; no one else.
5. **Cross-stage contradiction detection** in aggregator — unique.
6. **Probe-run recovery from quarantine** — flakiness_score decay window is novel.
7. **Stack-scoped pattern distribution** — no comparable repo organizes by stack prefix for selective provisioning.
8. **Visual proof review as a mandatory override step** — unique.
9. **State SSOT per orchestration scope** (workflow-scoped state files) — well ahead of implicit-context approaches.
10. **Self-improving telemetry** (duration_hints + flakiness_score persisted across runs) — unique among comparable repos.

---

## Honest assessment of our position

**Strengths:** Our architecture is genuinely more sophisticated than anything visible in the first 100 GitHub results. The 4-tier model, dual-signal verdict, config-driven DAG, and cross-stage contradiction detection are well beyond what the field is doing publicly.

**Weaknesses exposed by this research:**
- **No direct browser control for healers** — fugazi is ahead here (meaningful accuracy impact).
- **No deterministic pre-classification shortcut** — nirarad is ahead here (cost + variance).
- **No standalone CI mode** — nirarad ships a CI binary; we require Claude Code.
- **No external issue creation** — nirarad surfaces REAL_BUG as GitHub Issues; we don't surface them outside `known_issues`.
- **Constitution rules live outside agents** — fugazi inlines them for primacy; we separate for context savings, but safety-critical rules would benefit from inlining.

**Unverified:** Most of the >500-star "AI test automation" results are commercial products with closed-source cores (QA Wolf, Virtuoso, Momentic, Baserock, Panto, TestMu, LambdaTest). I did not deep-inspect those since their architecture isn't publicly comparable. Open-source QA-agent frameworks with >1K stars and this hub's level of orchestration sophistication don't appear to exist. **The field is still sparse.**

---

## Recommended next actions (ranked by ROI)

| # | Action | Source | Effort | Impact |
|---|---|---|---|---|
| 1 | Deterministic pre-classification gate in `test-failure-analyzer-agent` (regex short-circuit before LLM) | nirarad | 1 file, ~30 lines | High reliability + cost savings |
| 2 | Add Playwright MCP tools to `test-healer-agent` for live browser inspection during healing | fugazi | ~1 day | High accuracy on SELECTOR fixes |
| 3 | GitHub Issue auto-creation for LOGIC_BUG / VISUAL_REGRESSION in `known_issues` | nirarad | ~3 hrs | Medium — closes detection→tracked-work loop |
| 4 | Inline safety-critical Constitution rules in each worker agent body (selector priority, no hard waits, etc.) | fugazi | ~half day | Medium — primacy reinforcement |
| 5 | Standalone Python CI entry point for `testing-pipeline-master-agent` | nirarad | ~2 days | Medium-high — unblocks CI integration without Claude Code |

---

## Sources

### GitHub repositories (via `gh` CLI)
- https://github.com/fugazi/test-automation-skills-agents
- https://github.com/nirarad/playwright-ai-qa-agent
- https://github.com/darkokos21/self-healing-framework-playwright
- https://github.com/Usman-alpha/AI-SelfHealing-Agent
- https://github.com/mdemir3/testalyst
- https://github.com/browserbase/stagehand
- https://github.com/magnitudedev/browser-agent
- https://github.com/lmnr-ai/index
- https://github.com/wshobson/agents
- https://github.com/affaan-m/everything-claude-code
- https://github.com/VoltAgent/awesome-agent-skills
- https://github.com/darcyegb/ClaudeCodeAgents
- https://github.com/levnikolaevich/claude-code-skills
- https://github.com/BehiSecc/awesome-claude-skills

### Web (ecosystem landscape)
- https://www.qawolf.com/blog/the-12-best-ai-testing-tools-in-2026
- https://www.virtuosoqa.com/post/best-ai-testing-tools
- https://www.testmuai.com/blog/open-source-ai-testing-tools/
- https://momentic.ai/blog/open-source-test-automation-tools
- https://www.baserock.ai/blog/best-ai-testing-tools-in-2026
- https://testgrid.io/blog/ai-testing-tools/
- https://bugbug.io/blog/test-automation-tools/open-source-automation-tools/
- https://testguild.com/7-innovative-ai-test-automation-tools-future-third-wave/

---

*Document frozen at 2026-04-22. Star counts and repo activity will drift. Re-run the `gh search` queries above to refresh when this research needs updating.*

---

## Applied — 2026-04-22

The recommendations from this research were implemented as the
**testing-pipeline overhaul** on branch `feat/testing-pipeline-overhaul`
(8 commits, 1081 tests passing). Map of research findings to delivered work:

| Recommendation | Commit | File(s) |
|---|---|---|
| **#1** Deterministic pre-classification (from nirarad) | `feat(agents)!: upgrade T3 workers + failure analyzer to pipeline v2` | `test-failure-analyzer-agent.md` (18 regex rules, `classification_source` field, `healer_category` mapping) + `core/.claude/config/e2e-pipeline.yml` (`classification_rules[]` array) |
| **#2** Playwright MCP for healer (from fugazi) | same commit | `test-healer-agent.md` frontmatter declares MCP server as hard dep; `e2e-pipeline.yml` `healing.use_playwright_mcp: true` |
| **#3** GitHub Issue auto-creation (from nirarad) | `feat(pipeline)!: tier-nested cleanup...` | `testing-pipeline-master-agent.md` aggregation step with sha256 signature dedup + 30-day window; `e2e-pipeline.yml` `issue_creation` config block |
| **#4** Standalone CI aggregator (narrow scope) | `feat(pipeline): add standalone pipeline_aggregator.py with 13 tests` | `scripts/pipeline_aggregator.py` (290 LOC, pure read/compute/write) + 14 aggregator tests |
| **#5** Inline Constitution per agent (from fugazi) | distributed across `feat(agents)!:` and `feat(e2e)!:` and `feat(pipeline)!:` commits | Every rewritten T2/T3 agent gains a `## NON-NEGOTIABLE` block at the top of its body, with pointer to `core/.claude/rules/agent-orchestration.md` and `testing.md` for the authoritative text (SSOT-respecting) |

Additionally, 10 architectural gaps surfaced during this session's review
were addressed in the same branch:

- Gap #8 (state-file path inconsistency) — `e2e-conductor-agent` dual-mode
  path detection
- Gap #9 (retry-budget non-composition) — `remaining_budget` passed by T1
  through dispatch context, T2 honors
- Gap #10 (cleanup-at-init clobbering parent) — `rm -rf` guarded by
  mode==standalone
- Gap #11 (aggregation duplicated) — consolidated to T1 (`testing-pipeline-
  master-agent`), T2 agents deferred
- Gap #17 (silent-degradation) — `auto-verify` UI_VERIFICATION_DEGRADED
  gate with opt-out flag
- Gap #18 (contradictions observable but not blocking) —
  `contradictions.action: warn | block` config
- Gap #19 (e2e-visual-run / e2e-conductor-agent parallel implementations) —
  skill wraps agent; `references/` removed, content migrated into agents
- State-schema versioning — `schema_version: "1.0.0"` first field of every
  state file

**Not applied in this overhaul** (deferred):
- Full Claude-Code-free headless runner (user narrowed Phase F to aggregation
  only; issue #N for follow-up)
- GitHub Actions CI workflow wiring for the standalone aggregator
- Port of testing-pipeline into the remaining framework-native runners
  (android-run-e2e, flutter-e2e-test, react-native-e2e) — out of scope per
  plan's "non-goals" section

Synthetic Playwright fixture at `scripts/tests/fixtures/playwright-demo/`
exercises all 7 scenarios (pass, broken-locator, timing, visual-change,
logic, flaky, infra) and drives `scripts/tests/test_pipeline_e2e.py` which
verifies the aggregator produces correct verdicts for each.

