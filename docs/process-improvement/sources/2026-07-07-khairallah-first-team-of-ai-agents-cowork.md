Source: https://x.com/eng_khairallah1/status/2074410155689542072
Captured: 2026-07-08

# Khairallah — "How to Build Your First Team of AI Agents Using Claude" (full course, no-code / Cowork)

**Author:** Khairallah ([@eng_khairallah1](https://x.com/eng_khairallah1)) — *same author as the [Operating Manual capture](2026-07-08-khairallah-operating-manual-verification-first.md)*
**Posted:** 2026-07-07 · **Engagement at capture:** 235 likes, 52 RTs, 32 replies, 354k views
**Format:** Single long-form X-native article (~13.5k chars) — a step-by-step no-code course.
**Nature:** **Consumer how-to, ends in a follow-CTA.** No paid bundle. No model-specific pricing/benchmark claims — nothing needs independent verification. **Scope caveat:** targets **Claude Cowork (the desktop agentic app)** for non-coders, NOT the hub's `.claude/` agent/skill system. Value here is a clean **mental model + a canonical multi-agent pipeline example**, not adoptable hub mechanics.

---

## The core mental model — every agent = 4 pieces

Stated as the whole foundation:

1. **Role** — one *specific* job ("research agent", "writing agent"), not "an AI that does stuff." The more specific, the better it performs.
2. **Instructions** — *process + quality standard + output format.* Not "research this topic" but "find 5 sources, summarize each in 3 sentences, identify conflicting claims, produce a synthesis with a recommendation."
3. **Tools** — what it can access in the real world (web search, files, email, calendar). Determines what it can *do* beyond generating text.
4. **Memory** — how it remembers past work / your preferences. Separates a one-time tool from a persistent assistant.

Agent-vs-chatbot framing: *a chatbot waits for step-by-step instructions (babysitting); an agent takes a high-level goal and figures out the rest (delegation). Delegation is where the leverage lives.*

---

## The canonical example — a 4-agent Content Production Team

The heart of the piece. Each agent has a tight role, instructions, and a **defined file handoff** — the output of one is the input of the next:

| Agent | Job | Writes to |
|---|---|---|
| **Research Agent** | 5 subtopics → key facts/stats/expert opinions → contradictions → structured brief + "Key Takeaways" (3–5 actionable) | `/Research/[topic]-research.md` |
| **Outline Agent** | read brief → strongest angle → headline (number + curiosity hook) → section-by-section outline (points, examples, word counts) → hook + CTA paragraphs | `/Outlines/[topic]-outline.md` |
| **Writer Agent** | read outline → full article, ≤3-sentence paragraphs, bold key phrases, all specific numbers, consistent tone; explicit "does NOT sound like" bans | `/Drafts/[topic]-draft.md` |
| **Editor Agent** | read draft → check accuracy/flow/tone/redundancy → improve weak openings/vague statements/transitions/endings → cut non-value sentences → final | `/Published/[topic]-final.md` |

**Running the team:** feed topic to Research → its output to Outline → to Writer → to Editor. *"Raw topic to published piece in under 30 minutes, with zero writing from you."*

Three more copy-able team configs given: **Business Intelligence** (Data Collection → Analysis → Report → Recommendation), **Customer Research** (Survey → Data Processing → Pattern Detection → Insight), **Social Media** (Trend → Content Planning → Writing → Optimization). *"Every team: specialized roles, clear instructions, defined handoffs."*

---

## The 4 advanced techniques

1. **Scheduled agent workflows** — `/schedule` in Cowork runs agents on a timer (Mon 7am Research pulls trending topics → 8am Outline drafts top 3 → you pick → Writer produces). "Content pipeline on autopilot."
2. **Context files for consistency** — a `context.md` (audience / niche / tone / never-use word bans / always-include / format) that **every agent reads before starting any task**. Ensures consistency across the whole team.
3. **Feedback loops** — after each output, give *specific* feedback ("prioritize real-world examples over definitions next time"). Agents learn your standards without you repeating instructions.
4. **Multi-step automated workflows** — chain agents in one instruction ("run the full pipeline: research → outline → write → edit, save all intermediate files, deliver final to /Published"). Cowork handles it end-to-end.

---

## Relevance to this hub — MODERATE (a clean teaching model; near-total mechanical overlap; corroboration, not gaps)

This is the **no-code / consumer expression of orchestration the hub already does at an engineering level.** The value is the *pedagogy* (a crisp 4-piece model, a canonical file-handoff pipeline), not new mechanics. Map:

| khairallah concept | Existing hub analogue |
|---|---|
| Agent = **Role / Instructions / Tools / Memory** | `core/.claude/agents/*.md` frontmatter (role + allowed tools) + `engineering-roles.md` (Role router) + `context-management.md` (file-as-memory) |
| **Specialized roles + defined handoffs** (output→input) | `config/workflow-contracts.yaml` (step DAGs + artifact contracts); `config/pipeline-stages.yaml`; the 8 workflow skills |
| **Output → FILES, not transient context** (each agent writes `.md`) | `context-management.md` "scratchpad / write critical state to disk"; the structured-return mandate in `agent-orchestration.md` — the hub already treats sub-agent output as artifacts |
| **`context.md` read before every task** | `CLAUDE.md` auto-load; `subagent-governance-inject.sh` (injects standing mandates into every worker) |
| **Scheduled workflows (`/schedule`)** | the hub's cron/`scan-*.yml` scheduled workflows + `ScheduleWakeup`/loop cadence |
| **Feedback loops → agents learn your standards** | `learning-self-improvement` / `.claude/tasks/lessons.md` — accumulate corrections across sessions |
| **Multi-step chained pipeline** | `loop-engineering` DISCOVER→PLAN→EXECUTE→VERIFY→SHIP; `project-manager-agent` PRD-to-Production |

**The one framing worth borrowing (LOW priority, documentation-only):** the **Role / Instructions / Tools / Memory** four-piece model is the cleanest one-line teaching definition of an agent seen across these captures — cross-references the same "tools + memory + loop" definition already flagged in the [Kopadze note](2026-06-08-anatoli-kopadze-build-your-own-ai-agent.md). If the hub ever writes a *non-developer-facing* onboarding doc for its agent system, this 4-piece frame is the model to use. No new hub *pattern* — the mechanics are all already present and more sophisticated (maker≠checker verification, trust-score gating, agent-team-vs-subagent-vs-worktree selection) than this consumer guide covers.

**Notable gap in the source (not the hub):** the guide has **no independent verification / checker step** — the Editor Agent reviews the *same lineage's* draft (author-grades-own-work), which the hub explicitly forbids via `independent-test-verification.md` (maker ≠ checker). This is a place the hub's doctrine is *stronger* than the popular guide, worth remembering when this 4-agent pipeline shape is cited.

**No action required** — confirmation the hub's orchestration matches (and exceeds) the state of the popular art. **No verification prerequisite** (no model claims). **Cross-links:** the same author's [Operating Manual](2026-07-08-khairallah-operating-manual-verification-first.md); the [cyril Claude Projects course](2026-07-08-cyril-claude-projects-full-course.md) (instructions-vs-knowledge separation is the single-agent version of this multi-agent handoff discipline).
