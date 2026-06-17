# SDLC + Loop-Engineering Coverage Map

How this hub's idea→production pipeline (README goal #3) maps to two industry reference
models, with an **honest** documented / implemented / tested status per stage. Updated
2026-06-17. Gaps here are the same ones tracked in `plans/idea-to-deploy-readiness.md`.

## Reference A — 10-step SDLC (Communication → Operation & Maintenance)

| # | SDLC stage | Hub owner (role · skills) | Documented | Implemented | Tested |
|---|---|---|---|---|---|
| 1 | Communication | PM · `/brainstorm`, prompt-auto-enhance clarification gate | yes | yes | weak — no skill eval |
| 2 | Requirement Gathering | BA/PM · `/brainstorm` `/grill-me` `/to-prd` `/prd-parser` (IEEE-830 PRD) | yes | yes (generic) | weak |
| 3 | Feasibility Study | Architect · brainstorm trade-offs, `/strategic-architect`, `/change-risk-scoring` | yes | partial — no dedicated skill, folded into brainstorm/architect | weak |
| 4 | System Analysis (planning) | Architect · `/writing-plans` `/strategic-architect` `/schema-designer` | yes | yes | weak |
| 5 | Software Design | UI/UX + Architect · `/ui-ux-pro-max` `/html-prototype` `/adr` + **G1 approval gate** | yes | yes | weak |
| 6 | Coding | Full-Stack/Frontend · `/implement` `/development-loop` `/tdd`, stack dev skills | yes | yes | yes |
| 7 | Testing | QA · `/test-pipeline` (3-lane) `/e2e-visual-run` `/fix-loop`, independent + supervisor verification | yes | yes | yes (smoke-tested) |
| 8 | Integration | QA · `/contract-test` `/integration-test` `/ci-cd-setup` | yes | yes | yes |
| 9 | **Implementation (deploy/rollout)** | DevOps · deploy skills **generate configs only** — executor is **Unit 3, unbuilt** | yes | **NO — gap** | **no** |
| 10 | **Operation & Maintenance** | DevOps · `/monitoring-setup` `/incident-response` `/disaster-recovery`, notifier-integration | yes | partial — config-only, tied to #9 | no |

**Verdict:** stages 1–8 are documented + implemented (testing well-tested; design/planning stages
lack per-skill evals). Stages 9–10 are documented + role-defined but **not executable** — the
deploy-executor gap (`/vps-deploy`, Unit 3), built during the first real app once stack + VPS
credentials exist.

## Reference B — Loop Engineering (Addy Osmani, "every builder needs in 2026")

The hub productized this exact pattern as the `loop-engineering` skill (v1.1.0). The cycle
DISCOVER→PLAN→EXECUTE(Maker)→VERIFY(Checker)→SHIP|FEEDBACK is the skill's STEP 2–6.

| Building block | Hub implementation | Status |
|---|---|---|
| 1. Automations (Git PR / schedule) | `/loop`, `/goal`, cron, CI workflow triggers | full |
| 2. Worktrees (separate workspaces) | maker dispatched with `isolation=worktree`; `/git-worktrees` | full |
| 3. Skills (project context, rules) | 164 skills + 47 rules | full |
| 4. Plugins (GitHub, MCP, Claude) | gh CLI, MCP servers, plugins | full |
| 5. Subagents (Maker vs Checker) | maker `plan-executor-agent` ≠ checker `code-reviewer-agent`; `independent-test-verification.md` | full |
| 6. Memory (project log — markdown + DB) | `lessons.md`, `.claude/learnings.json`, auto-memory, telemetry JSON, `/handover` | full |

**Verdict:** fully compliant — the hub *is* this diagram.

## Honest cross-cutting gaps

1. **Deploy execution (SDLC 9–10):** configs are generated, never executed. Unit 3.
2. **Per-skill eval coverage:** pipeline-level testing is strong, but 0/164 skills and 6/39 agents
   have evals — "everything individually eval-gated" is not yet true (audit gap C).
3. **Domain-aware requirements (SDLC 2):** generic today; the domain-research BA step (Unit 2)
   makes it domain-deep, built when a real domain idea arrives.
4. **Measured self-feedback:** the loop self-heals + learns, but "provably improving over time"
   needs accumulated telemetry (Unit 5).
