Source: https://x.com/AnatoliKopadze/status/2063985608381362576
Article: X-native long-form article — "AI Agents. What they are and how to Build Your Own Step by Step."
Author: Anatoli Kopadze (@AnatoliKopadze) · X: https://x.com/AnatoliKopadze · Telegram: https://t.me/kopadzemp
Posted: 2026-06-08
Captured: 2026-07-01
Capture method: ADHX API (twitter-x skill Option A) returned the complete `article.content` (9,125 chars) — verified-complete, not reconstructed
Media: 1 image saved under ./img/kopadze-claude-model-costs.jpg (Claude model input/output pricing + monthly-cost table; OCR'd verbatim below)
Engagement at capture: 896 likes · 135 retweets · 32 replies · 3,356,370 views
Relevance to this hub: a beginner-facing "build a Claude-powered Telegram agent on a VPS" walkthrough. Most of it (agent spectrum, agent types) is entry-level and below the hub's altitude, BUT its final two sections — **the memory/context-loss problem and its four fixes**, and the **skills-as-incremental-capabilities** framing — are a plain-English restatement of patterns this hub already institutionalizes (compaction survival, checkpoint/handover, progressive disclosure, `/end-session`+`/continue`, per-skill capability growth). Value here is as an *external corroboration* datapoint (3.36M views → these patterns are mainstream), and a reminder that the hub's context-management rule maps 1:1 onto what the broader community independently converged on. Companion to the loop sources [[2026-06-30-andrew-ng-3-product-development-loops]], [[2026-karpathy-loops-md-field-notes]], [[2026-06-13-claude-loops-while-you-sleep]].

# Anatoli Kopadze — "AI Agents. What They Are and How to Build Your Own, Step by Step"

## Thesis
Agents are **not a category, they are a spectrum**. What separates a basic LLM chat from a true
agent is not the model — it's the **structure around it**. An agent has three things a chat does
not: **tools** it can call on its own (search, filesystem, code execution, external APIs),
**memory** that persists across tasks (not just within a session), and a **loop** that keeps
running until the task is finished (not until it emits one response). The more of those three you
add, the less the human is involved.

## The spectrum (chat → agent)
1. **Basic chat** — ask, answer, session ends. No tools, no ongoing goal, no ability to act.
2. **Claude + tools** — searches the web, reads a file, generates an image on its own initiative. Slightly agentic.
3. **Multi-step workflow** — you give a goal; Claude decomposes → executes each step → checks results → delivers. Human not involved between steps.
4. **Fully autonomous agent** — runs on a schedule, monitors inputs, calls external services, completes complex tasks with no human in the loop. Set the goal once, check the output.

The gap from bottom to top is **not a different model** — it's tools + memory + loop around the same model.

## Types of agents you can build today
- **Research agent** — gathers info across sources, extracts what matters, returns a structured summary.
- **Writing agent** — writes to a system you define (tone/format/audience); handles drafts, rewrites, edits.
- **Code agent** — writes code, runs it, reads errors, fixes, repeats (the implementation/debugging loop).
- **Business agent** — repetitive tasks: emails, customer requests, lead qualification, reports; autopilot once rules are set.
- **Personal agent** — schedule, tasks, briefings, day-to-day planning.

## The build (Claude Code → Telegram bot on a VPS)
Use Claude Code to build a Telegram bot that runs on a remote server with Claude as its brain;
Claude Code writes all the code, you describe what you want in plain English. ~10–20 minutes, no
coding required. Prereqs:
1. **Claude API key** (console.anthropic.com) — pay-per-usage; a personal bot at ~50 msgs/day ≈ **$1–5/mo** depending on model.
2. **Telegram bot token** from BotFather.
3. **A Linux VPS** — 1 CPU / 1 GB RAM / 20 GB storage is ample; DigitalOcean, Hetzner, or Vultr basic plans ≈ **$4–6/mo**. Install with `npm i -g @anthropic-ai/claude-code`.

### Model choice + cost table (OCR of `img/kopadze-claude-model-costs.jpg`)
| Model | Input | Output | 50 msgs/day |
|---|---|---|---|
| Haiku 4.5 | $0.80/M | $4/M | ~$1/mo |
| Sonnet 4.6 | $3/M | $15/M | ~$3–5/mo |
| Opus 4.8 | $5/M | $25/M | ~$8–12/mo |

Author's guidance: **Sonnet 4.6** for most personal bots (strong + affordable); **Haiku 4.5** to
minimize cost; **Opus 4.8** only for complex analytical agents where answer quality is critical.
*(NB — model/pricing figures are the author's as of 2026-06-08; treat as the source's claim, not a hub-verified price. Cross-check against the `claude-api` skill before quoting.)*

### Setup shape
- **Prompt 1** — build everything: give the agent a personality, deploy as a background service, add persistent memory between sessions.
- **Prompt 2** — describe the agent type (paste a Research / Writing / Code / Business-Email / Personal-Planning template into "The agent should be:").
- **Skills added over time** (each a new plain-English prompt Claude Code turns into code): web search; save notes to a file; **restrict the bot to your own account only** (else anyone who finds it burns your API credits); track API costs; scheduled daily briefing.

### Ops cheatsheet (from the article)
- Update personality → edit the system-prompt variable at the top of the bot file, save, `sudo systemctl restart your-bot-name`.
- Is it running? → `sudo systemctl status your-bot-name` ("active (running)" vs "failed").
- Read logs → `journalctl -u your-bot-name -n 50`.
- Add a skill → open Claude Code in the project folder, "Add X feature to the bot."

## The memory problem every agent has (the section that matters most for this hub)
The most common failure: the agent **loses context** between sessions, across long tasks, or after
too many messages — then repeats work or makes mistakes. Three ways it happens: (a) long tasks
exceed the context limit and the agent loses the original goal/decisions/constraints; (b) a new
session starts from zero; (c) an interruption mid-task leaves no record of where it stopped.

**Four fixes:**
1. **Progress note after every major step** — what was done, what was decided, what's left; paste it at the start of the next session to restore context. *(= the hub's checkpoint / handover / `/end-session`+`/continue` discipline.)*
2. **Summarize every ~10–15 messages** — forces context compression before overflow. *(= rolling summary / scratchpad sync checkpoint.)*
3. **Compress-and-continue before the thread gets too long** — ask for a short summary, continue from it. *(= compaction survival.)*
4. **Put always-needed facts directly in the system prompt** — Claude reads them at the start of every conversation, so they're always in context. *(= CLAUDE.md / persistent memory.)*

Named prompt templates in the article (not reproduced — titles only): Checkpoint Prompt, Memory File Prompt, Context Recovery Prompt, Rolling Summary Prompt.

---

## Why this matters to THIS hub (capture-time note — not yet an action)
- **Independent, mass-audience corroboration** (3.36M views) that the hub's `context-management.md`
  rule (progressive disclosure, scratchpad, compaction survival, handover) is the *mainstream*
  answer to the agent memory problem — the four community fixes map 1:1 onto rules the hub already
  ships. Low novelty, high confidence signal.
- **"tools + memory + loop" as the crisp definition of agentic** is a clean teaching framing; could
  sharpen the intro of `loop-engineering-spec.md` or an onboarding doc if one is ever written.
- **Security footgun worth noting**: "restrict the bot to your own account only, or anyone who finds
  it burns your API credits" — a good reminder for any Telegram/Notifier-style bot the hub builds
  (the shared Notifier gateway is localhost-only, which already embodies this; worth a line in
  `notifier-integration.md` if bots ever get user-facing).
- **Deferred improvement-pass items** (nothing acted on here, per the store's rule): (1) consider a
  one-line "tools + memory + loop" definition + the four memory-fixes cross-reference in
  `context-management.md` / `loop-engineering-spec.md`; (2) consider an auth-lock reminder for
  user-facing bots in `notifier-integration.md`. Both are low-priority — the substance already
  exists in the hub; this source mostly validates it.
