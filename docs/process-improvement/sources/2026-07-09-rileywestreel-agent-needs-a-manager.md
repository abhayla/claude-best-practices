Source: https://x.com/rileywestreel/status/2075256200472461787
Captured: 2026-07-08

# rileywestreel — "Your AI Agent Needs a Manager, Not Another Prompt"

**Author:** rileywestreel ([@rileywestreel](https://x.com/rileywestreel))
**Posted:** 2026-07-09 · **Engagement at capture:** 20 likes, 4 RTs, 5 replies, 671 views — **very low reach; quality judged independent of reach.**
**Format:** Single long-form X-native article (~9.3k chars) — a practitioner how-to with a worked migration example.
**Nature:** **Consumer/practitioner how-to, ends in a follow-CTA.** Contains **specific product-feature and pricing/benchmark claims attributed to Anthropic** (Managed Agents, Dynamic Workflows, Outcomes, Opus 4.8/4.6 figures) — **flag all as UNVERIFIED** until checked against primary Anthropic docs; treat the rest (the manager/lead/subagent/grader shape) as a restatement of already-captured orchestration doctrine.

---

## ⚠️ Claims to verify before repeating as fact

None of these are independently checked in this capture — they are the article's own attributions:
- **"Managed Agents"** launched with three primitives — persistent memory, a self-grading loop, parallel subagent dispatch — at "Code with Claude 2026," with **Harvey seeing a 6x rise in task completion**.
- **"Dynamic Workflows"** — now GA, "open to Pro subscribers" — where Claude writes its own orchestration script, coordinates up to **1,000 subagents** per run, capped at **16 concurrent**, with the plan living in a script rather than the model's context window.
- **"Outcomes"** — now in public beta — a separate evaluator/grader service scoring output against a rubric.
- The **"C compiler experiment"** — 16 agents, ~2,000 sessions, a 100,000-line compiler that builds the Linux kernel, synchronized via a text-file lock.
- **Opus 4.8 pricing/limits** — 1M token context at "standard API pricing," no premium above 200K tokens, $5/M input + $25/M output; a full-day Dynamic-Workflows run costing "$400–$600."
- **Opus 4.6** "handled a multi-million-line codebase migration... in half the time."

If any of Managed Agents / Dynamic Workflows / Outcomes turn out to be real, newly-GA Anthropic platform primitives (as opposed to the author's own paraphrase of ordinary subagent/skill/hook mechanics), they are exactly the kind of release the `/cc-adoption-scout` skill exists to triage — run it before assuming the hub needs to hand-build anything described here.

---

## The core thesis — a manager, not a bigger prompt

Rewriting one mega-prompt after each failure doesn't fix a single agent working alone with "no one checking the plan, no one grading the output, no one splitting the job." The fix is structure: **a lead that plans, subagents that work in parallel, and a grader that decides when output ships.**

## The four steps

1. **Give the lead a job description, not a task list** — name the outcome + the standard, tell it to plan before acting; do NOT hand it step-by-step instructions for the actual work. The lead's job is deciding the breakdown, not executing it.
2. **Wire subagents with tools, not more prose** — each subagent gets one piece of the job, the tools to do it, a definition of done, and (critically) a **fixed file list** so parallel subagents never collide over the same file.
3. **Add a grader** — a separate evaluator that scores output against a written rubric and sends failures back for a fix, rather than letting the worker decide for itself when it's done. Quoted caution (Mitch Ashley, Futurum Group): once one session fans out into hundreds of subagents, verification/evidence-capture must scale at the same pace as the generation, or review can't keep up.
4. **Set the config so the lead has room to think** — pick a capable model with a large context window explicitly; don't let the lead run under-resourced.

**Worked example:** a 40-file Ruby service migration — lead reads the service, returns 40 independent per-file subtasks with a shared definition-of-done; subagents run in parallel each locked to its own file; grader flags 3 files with a leftover direct query, sends them back with the exact fix; lead reassembles all 40, confirms the full suite is green, hands back one reviewable change with a per-file changelog.

---

## Relevance to this hub — LOW-MODERATE (near-total restatement of existing doctrine; no new mechanism once unverified product claims are set aside)

The lead/subagent/grader shape is the hub's `project-manager-agent` + flat-subagent + maker≠checker pattern, described from the outside with different names. Map:

| Article concept | Existing hub analogue |
|---|---|
| **Lead plans, subagents execute one locked piece each** | `project-manager-agent` (T0 orchestrator, invokes workflow skills); `agent-orchestration.md` flat single-level subagent dispatch; file-list locking ≈ the hub's per-task scoping discipline |
| **Grader scores separately, sends failures back** | `supervisor-verification.md` + `independent-test-verification.md` — maker ≠ checker, the hub's central rule; `quality-gate-evaluator-agent`, `code-reviewer-agent` |
| **"No one checking the plan" is the root failure of a single mega-prompt** | `plan-before-coding.md` (visible plan before first edit) + `decision-authority.md` |
| **Verification/evidence must scale with generation** (Ashley quote) | `trust-score` subsystem (hard gates, per-signal floors) — the hub's answer to exactly this scaling problem |
| **Give the lead a capable model + room to reason** | `model-routing.md` — explicit per-dispatch model tier, escalate on repeated failure |
| **Fixed file list prevents parallel-subagent collision** | `agent-team-selection.md` (worktree for true parallel file isolation vs. flat subagent) |

**No new mechanism survives once the unverified product claims are stripped out.** This is the same conclusion as the khairallah "first team of agents" capture (2026-07-07): a clean restatement of maker≠checker + orchestrator/lead doctrine the hub already implements more rigorously (hard-gated trust score, per-stage graduation, model-tier routing) than this article's grader-as-vibe-check. The one thing genuinely worth a look — NOT because the hub lacks the *pattern*, but because it may be a *platform* primitive the hub is hand-rolling — is whether "Dynamic Workflows" (plan lives in a script outside the model's context, up to 1,000 subagents) is real and GA; if so it is closer to the hub's `loop-engineering` / `agent-team-selection` territory than to anything already captured, and belongs in `/cc-adoption-scout` triage rather than a doctrine change here.

**No action required** on the doctrine itself — restates supervisor/maker≠checker + plan-before-coding + trust-score-style verification-at-scale, all already covered and already stronger. **Action, if any:** run `/cc-adoption-scout` to verify whether Managed Agents / Dynamic Workflows / Outcomes are real shipped Anthropic primitives before treating any of their specifics as fact.

**Cross-links:** [khairallah — first team of AI agents](2026-07-07-khairallah-first-team-of-ai-agents-cowork.md) (same lead/subagent/handoff shape, no-code framing, also flags the maker≠checker gap in its own source); [0xCodila — Loop Engineering / Bilevel](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) (verifier + maker≠checker as one of the "5 building blocks"); [ClaudeDevs — Getting Started with Loops](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party loop taxonomy, same primitives).
