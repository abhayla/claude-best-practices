Source: https://x.com/0xMoysei/status/2072808742274392194
Captured: 2026-07-08

# 0xMoysei (@0xMoysei) — "Master Claude With Fable 5: 6 Rules Straight From Anthropic's Docs"

**Author:** 0xMoysei ([@0xMoysei](https://x.com/0xMoysei))
**Posted:** 2026-07-02 · **Engagement at capture:** 110 likes, 17 RTs, 258,733 views
**Format:** Single long-form X-native article (~6.8k chars).
**Nature:** **Fable-5 migration/usage-rules piece explicitly framed as sourced from Anthropic's own prompting guide** ("Anthropic shipped a prompting guide with the model... these 6 rules restore it"). Structured as 6 numbered rules, then a 7th synthesis rule ("Delete Before You Add") and an 8th "where to spend the promo window" pitch section — so the "6 rules" headline undercounts the piece's actual content by 2 sections.

---

## ⚠️ Verification gate — do NOT propagate as fact until checked vs `claude-api` / official docs

- **The core framing claim — that this piece quotes/paraphrases an actual Anthropic-published Fable-5 prompting guide — is itself checkable and NOT verified in this capture.** Before citing any "Anthropic says X" line from this piece, fetch the real guide (likely at a `platform.claude.com/docs/.../prompting-claude-fable-5`-style URL, per the sibling `KanikaBK` capture) and cache it under `docs/claude-references/` per `claude-docs-cache.md` — do not trust this tweet's paraphrase as the source of record.
- **Pricing claim** — "$10/M input, $50/M output, 1M context, 128k output ceiling," GA June 9, pulled offline then redeployed July 1 "with updated cybersecurity safeguards," 50%-of-weekly-plan-limit promo through July 7 — **all unverified**, cross-check against `claude-api` skill / official pricing page before reuse.
- **Refusal→Opus-fallback claim (rule 6)** — "session reroutes to Opus 4.8 with a notification... rate around 5% of sessions... `/model fable` takes you back, but if the trigger stays in context, the next request bounces you again" — this is the **pending verify-then-codify item** also seen in other Fable-5 captures in this cluster; still unverified here, but this piece adds a new specific claim (~5% session rate, sticky-trigger behavior) worth folding into that verification task once it's actioned.
- **Safety-classifier taxonomy claim (rule 6)** — "3 categories: offensive cybersecurity techniques, biology/life sciences methods, extraction of the model's own thinking" — unverified, not cross-checked against Anthropic's actual usage-policy/safety documentation.
- **Alex Albert attribution** ("put the migration advice in 3 moves") in rule 7 — unverified quote/paraphrase attribution, not sourced to a specific post or transcript here.
- **Anecdotal case examples** ("drafting an email nobody asked for," "creating defensive git-branch backups" as named Anthropic-guide examples) — unverified specifics.
- **"21,000 lines of TypeScript across 90+ commits" three.js clone claim** (section 8) — unverified specific, no link to the referenced "one public project."

---

## The 6 rules (+ 2 bonus sections) — faithful summary

1. **Give it the why** — state intent/context before the request, not just the task ("I'm renegotiating a Q3 delivery date..." vs. "write an email about the delay"). Lets the model pick the right files/tone without asking.
2. **Set explicit negatives** — pair each instruction with what the model should NOT do (2 cited examples: unrequested email drafts, unrequested defensive git-branch backups). Boundaries matter more than task description.
3. **Match the effort dial** — `low/medium/high/xhigh`; Anthropic recommends `high` as default, `xhigh` for capability-sensitive work, `medium/low` for routine tasks. Claim: Fable on `low` effort can exceed prior-model `xhigh` performance at lower cost. Model choice follows the same logic — use Sonnet when a task fits Sonnet.
4. **Stop over-planning, let it act** — replace "research everything and plan before acting" with "act once you have enough information." Reserve a separate planning phase for drafting the spec on a cheaper model (Opus), then hand the finished prompt to Fable for the long autonomous run.
5. **Make it prove it** — bake a verification block into skills/agents/CLAUDE.md (not pasted per-prompt) to counter models reporting "done" before done; claims this "nearly eliminated fabricated status reports" in Anthropic's testing.
6. **Never ask for raw reasoning** — a standing "explain your reasoning" instruction can trip the `reasoning_extraction` safety classifier (1 of 3 categories, alongside offensive-cyber and bio/life-sciences), causing a refusal + an automatic reroute to Opus 4.8 (claimed ~5% of sessions, "sticky" if the trigger stays in context). Fix: audit CLAUDE.md/system prompts for reasoning-echo instructions; use a summarized-thinking display setting instead.
7. **(Synthesis) Delete before you add** — the guide's through-line is subtraction: remove hardcoded process steps, exhaustive formatting rules, and defensive repetition that compensated for weaker older models. Cites "Alex Albert" migration advice: default to high/xhigh effort, rewrite old CLAUDE.md instructions, let the model use more judgment. Suggests having Fable audit its own session history to produce a ranked list of skills to create/promote and stale CLAUDE.md lines.
8. **(Pitch) Where to point it before the promo window closes** — 3 suggested high-value uses: large-repo code review, cloning a paid tool via Opus-research→PRD→Fable-build, and running the rule-7 self-audit to generate new skill files.

---

## Relevance to this hub — LOW-MODERATE (near-total overlap with existing doctrine; one pending-verification item reinforced)

| 0xMoysei's rule | Existing hub analogue |
|---|---|
| #1 Give it the why (intent before request) | `prompt-auto-enhance.md` Clarification & Confidence Gate; `decision-authority.md` state assumptions |
| #2 Explicit negatives / boundary blocks | Rule 20/21 (scope discipline, YAGNI) — partial overlap, not a direct match; no hub rule mandates paired "don't do X" negatives specifically |
| #3 Effort dial + cheapest-sufficient model | `.claude/rules/model-routing.md` — direct match: "cheapest sufficient model per dispatch," escalate one tier on failure |
| #4 Stop over-planning, act when ready; cheap-model plan → expensive-model build | `claude-behavior.md` rule 1 (plan mode for non-trivial tasks) is in tension with this — hub still gates plan-before-coding; `model-routing.md`'s opus-for-design/sonnet-for-execution split partially echoes the plan-cheap/build-expensive split, but roles are reversed (hub uses opus for the hard design work, not the cheap draft) |
| #5 Make it prove it (verification block in skills, not per-prompt) | `supervisor-verification.md`, `independent-test-verification.md`, `claude-behavior.md` rule 4 (verify before reporting complete) |
| #6 Never ask for raw reasoning / refusal→Opus reroute | No hub rule addresses this directly; reinforces the **pending verify-then-codify item** already flagged in the `KanikaBK` and other Fable-5 captures in this cluster — adds a new specific (~5% session rate, sticky-trigger behavior) to fold in once that item is actioned |
| #7 Delete before you add (subtract prescriptive instructions) | `rule-curation.md` (reactive, not speculative curation) is adjacent but governs pattern curation, not CLAUDE.md pruning specifically — no direct hub analogue for "periodically prune your own CLAUDE.md for Fable-5 fit" |
| #8 Promo-window pitch | Marketing/time-boxed content, not applicable to hub doctrine |

**Net-new for the hub:** none actionable today. The refusal→Opus-fallback mechanism (rule 6) remains a **pending verify-then-codify item** — this capture adds specificity (~5% rate, sticky trigger) worth including when that item is finally verified against official docs, but does not on its own justify a new rule. Rule 2 (explicit negatives) and rule 7 (prune CLAUDE.md for a more capable model) are the only two facets not already covered nearly verbatim elsewhere in the cluster, but both are general prompting hygiene rather than hub-specific gaps.

**Action:** File for corroboration-count purposes only. No hub rule change. Before any future capture cites this piece's "Anthropic says" claims as fact (pricing, promo terms, safety-classifier taxonomy, refusal rate), fetch and cache the actual Anthropic Fable-5 prompting guide per `claude-docs-cache.md`. Cross-links: [KanikaBK 10 mistakes](2026-07-08-kanikabk-10-mistakes-with-fable5.md) (same refusal-fallback pending-verify item, same model-routing corroboration), [undefinedKi Fable guide](2026-07-04-undefinedki-build-anything-with-fable5.md), [Mahaximus 12 prompting moves](2026-07-09-mahaximus-fable5-12-prompting-moves.md).
