Source: https://x.com/cyrilXBT/status/2074669139730284735
Captured: 2026-07-08

# cyrilXBT — "How to Actually Set Up Claude Projects That Most Users Don't Know" (full course)

**Author:** cyril ([@cyrilXBT](https://x.com/cyrilXBT))
**Posted:** 2026-07-08 · **Engagement at capture:** 320 likes, 46 RTs, 18 replies, 337k views
**Format:** Single long-form X-native article (~18.5k chars) — a step-by-step course.
**Nature:** **Practitioner how-to, ends in a soft follow-CTA.** No paid bundle, no model-specific pricing/benchmark claims — nothing here needs independent verification before use. **Scope caveat:** this is about **claude.ai Projects (the chat product) + Claude Cowork**, NOT Claude Code / this hub's `.claude/` pattern system. Its value here is transferable *doctrine* about instructions-vs-knowledge, not directly-adoptable hub mechanics.

---

## What it is

A complete setup guide for **Claude Projects** — the persistent workspace that bundles three things: (1) **custom instructions** (a system-level prompt applied to every conversation in the project), (2) a **knowledge base** (files referenced in every conversation), and (3) **scoped conversations** (chats grouped under the same instructions + knowledge).

**The one trip-up stated up front:** conversations inside a project do **NOT** share message history with each other. The shared state is the *instructions and files*, not the chats — every new conversation starts fresh with only those two loaded. Everything in the guide follows from that fact.

Availability: all plans (free capped at 5 projects; project *instructions* are a paid feature); Pro/Max/Team get the full setup.

---

## The core thesis — precision beats volume

> "Project knowledge does not get fully loaded into every response. Claude pulls the most relevant content per query through **retrieval**."

So the single biggest error is treating the knowledge base as a **storage locker** (dump the 40-page brand manual, six months of notes, the strategy deck). Overloading *dilutes retrieval* and eats the context window. **The rule:** keep each knowledge doc **tight and specific, ~1–3 pages**. "A three-page brand voice guide beats a forty-page brand manual every single time." Precision beats volume in the knowledge base, always.

---

## The 7 steps (full fidelity)

1. **Create the project with real intent.** Name it *specifically* ("Newsletter", "Client Proposals", "API Documentation" — not "Work"/"Stuff"). **One project per concern** — never mix backend code with marketing, or client A with client B. Vague name → vague project → accumulates unrelated junk → the dilution problem returns.

2. **Write instructions like a standing brief, not a prompt.** Highest-leverage step. A weak block ("You are a helpful assistant that writes marketing content") gives Claude nothing. A strong block is a **complete standing brief for someone who knows nothing about you yet** — because that is literally the state at the start of every conversation. Template:
   - **ROLE** — specific role + domain + who you're writing for (an audience that knows nothing about them).
   - **WHAT THIS PROJECT IS FOR** — the 3 main tasks; assume every request is one of these unless told otherwise.
   - **HOW TO RESPOND** — Tone / Format / Length, each specific. **"Do not ask clarifying questions unless genuinely blocked. Make a reasonable assumption, state it, and proceed."**
   - **WHAT TO ASSUME** — domain facts / product details / positioning treated as given every time.
   - **NEVER** — the hard bans (AI clichés, certain claims/formats).
   The *"don't ask clarifying questions — assume, state, proceed"* line is called out specifically as the friction-killer that speeds up every session.

3. **Build the knowledge base with precision.** For a content project: a **voice/style guide**, an **audience document**, a **pillars/scope document**, **3–5 of your best actual pieces** ("voice is caught, not taught" — examples teach patterns better than any instruction), and domain **reference material**. Name each file descriptively ("Brand Voice Guide v3", not "notes") so retrieval surfaces the right doc. Limits (Pro/Max/Team): **20 files/project, 30MB/file**, PDF/text/markdown/code/CSV/images. Hitting the ceiling = you're uploading volume, not signal.

4. **Test retrieval before you trust it** (the step almost nobody does). After uploading, open a project conversation and explicitly probe each critical doc: *"Based on the Brand Voice Guide in the project knowledge, how should I approach the opening line? Quote the specific guidance you are using."* If it quotes accurately, retrieval works; if it's generic or can't find it, the file didn't process / naming is too vague / it's buried. Five minutes; the difference between "hope it works" and "know it works."

5. **Pick the right model per conversation.** A project does NOT lock you into one model — you choose per conversation. Use a faster model for routine drafting, a more capable one for deep reasoning/synthesis — same project, same instructions, same knowledge, different engine per task. Most people either overpay (everything on the top model) or underperform (everything on a fast one).

6. **Use conversations as thinking, not just tasks.** Don't only run finished tasks — *think out loud*, explain reasoning, talk through decisions. Because the project is scoped/consistent, these conversations teach Claude your **reasoning patterns**, not just output patterns. Over weeks it starts matching your **judgment**, suggesting approaches that fit how you actually think.

7. **Maintain it — a project is only as current as its files.** Not set-and-forget; outdated knowledge produces *confidently wrong* context (worse than none). Update the voice guide when positioning changes, replace revised specs, **review project instructions quarterly** (six-month-old instructions may now contradict current work, and Claude will faithfully follow the stale rule).

---

## The new layer: Cowork Projects (the part most relevant to a factory operator)

As of the 2026 updates, Projects also live inside **Claude Cowork** (the desktop agentic app), adding capabilities chat-based projects lack:
- **Scoped memory that persists between sessions** — "build on last week's report" and it knows exactly what that was, without leaking into other work.
- **Dedicated local folders** — reads and writes real files on your machine.
- **Scheduled tasks** — runs recurring work on a cadence, unattended.

Same setup logic (clear instructions, tight files, one project per concern) but a higher ceiling: it *executes work against real files and can run on a schedule.* Recommended day-one command: *"Read every file in this folder. Then summarize what you know about this workspace: what is here, what I probably use it for, and what instructions you will follow. If anything is unclear, ask before assuming."*

---

## Four copy-able templates

| Template | Instructions carry | Knowledge carries |
|---|---|---|
| **Content** | writer role + audience + tone + formatting + hard bans | voice guide, audience persona, pillars doc, 3–5 best pieces (examples do the heavy lifting) |
| **Code** | stack, conventions, preferred patterns, never-do's | architecture doc, key source files, coding standards, API docs. **One project per codebase** |
| **Client** | who the client is, brand, preferences, scope | brand guidelines, past deliverables, distilled meeting notes, client-specific constraints. **One project per client** (no voice bleed) |
| **Research** | the question/domain + how findings should be structured | source material, prior notes, working thesis. Closest a chat project gets to a "second brain" |

**The pattern across all four:** *instructions carry standing rules + behavior; knowledge carries reference material + examples.* A behavior rule belongs in instructions; a doc-to-reference belongs in knowledge. Mixing them (behavioral rules in a knowledge file, reference docs pasted in the instruction box) is a quiet way to make a project underperform.

---

## The three personalization layers (all apply at once)

1. **Account-wide instructions** (profile settings) — apply to every chat everywhere. Put universal communication preferences here so you don't repeat them per project.
2. **Project instructions** — apply only inside one project. Keep them focused purely on *what makes that project different.*
3. **Styles** (per chat) — one-off tone/format adjustments.

Separating them correctly stops you repeating universal preferences in every project and keeps each project's instructions focused — "once again, the entire theme."

---

## Relevance to this hub — MODERATE (transferable doctrine; product surface differs)

The mechanics target **claude.ai Projects / Cowork**, not the hub's Claude Code `.claude/` system — so this is **not** a source of directly-adoptable hub patterns. Its value is that several of its principles are **independent external re-derivations of doctrine the hub already holds**, plus a couple of framings worth borrowing verbatim. Map:

| cyril principle | Existing hub analogue |
|---|---|
| Instructions = a **standing brief for someone who knows nothing about you yet** (every conversation starts fresh) | `CLAUDE.md` as auto-loaded project brief; `context-management.md` compaction-survival ("write critical state to disk, not context") |
| **Precision beats volume** — 1–3 page docs; overload dilutes retrieval + eats the window | `context-management.md` #1–2 progressive disclosure + "minimize context imports"; the hub's whole "don't inline large docs, use pointers" doctrine |
| **Instructions-vs-knowledge separation** (behavior rules ≠ reference docs) | The hub's rules (`.claude/rules/`) vs docs (`docs/`) split; `claude-guardian` "place the rule in the right file" |
| **Test retrieval before you trust it** (probe each doc; quote the guidance) | `skill-evaluator` trigger/output evals; `independent-test-verification.md` — same "prove it works, don't hope" instinct, applied to knowledge loading |
| **Maintain it / review instructions quarterly** (stale rules faithfully followed) | `check_freshness.py` stale-pattern detection; `rule-curation.md` reactive curation |
| **One project per concern** (no context bleed) | product-incubation `one product = one isolated sibling`; the two-`.claude/` boundary |
| **Model per conversation** (fast for drafting, capable for reasoning) | `model-routing.md` "cheapest sufficient model per dispatch" — nearly the same rule, stated for the consumer product |

**The two genuinely sharp framings worth capturing (both LOW-priority, documentation-only):**

1. **"Voice is caught, not taught" — examples > description in a knowledge base.** The hub's skill/pattern authoring leans on *prose instructions*; the "3–5 real best examples teach patterns better than any amount of instruction" principle is an argument for the hub's own `writing-skills` / `pattern-structure` guidance to weight **canonical-example references** even more heavily than it does (this already echoes `context-management.md` #4 "Reference Canonical Examples" — cyril is external corroboration, not a new idea).

2. **"Test retrieval" as a first-class setup step.** For any hub/Cowork *project* that relies on a knowledge base (as opposed to code), an explicit "quote the guidance you're using" probe is a cheap verification step the hub's verification doctrine doesn't currently name for the *knowledge-loading* case (only for tests/output). Marginal — most hub work is code, where this doesn't apply.

**Everything else is confirmation, not a gap** — precision-over-volume, instruction/knowledge separation, per-concern isolation, model routing, and freshness maintenance are all already hub doctrine. **No action is required**; the one-line takeaway is that a widely-shared consumer guide independently arrives at the same context-engineering principles the hub encodes, which is corroboration of the hub's approach. **No verification prerequisite** (no model claims).

**Cross-links:** the "harness / context-as-the-real-lever" thesis of the [sairahul New AI Stack note](2026-07-07-sairahul-new-ai-stack-harness-layers.md) and the [Khairallah Operating Manual note](2026-07-08-khairallah-operating-manual-verification-first.md) — cyril is the *consumer-product* expression of the same idea those two state at the systems level.
