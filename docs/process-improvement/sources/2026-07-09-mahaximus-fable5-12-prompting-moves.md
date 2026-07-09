Source: https://x.com/Mahaximus_/status/2075194100937015410
Captured: 2026-07-08

# Mahaximus (@Mahaximus_) — "Claude Fable 5. The New Rules of Prompting. 12 Moves That Unlock Full Potential"

**Author:** Mahaximus ([@Mahaximus_](https://x.com/Mahaximus_))
**Posted:** 2026-07-09 · **Engagement at capture:** 19 likes, 0 RTs, 2,732 views
**Format:** Single long-form X-native article (~11.9k chars).
**Nature:** **Fable-5 prompting-doctrine listicle.** Frames Fable 5 as needing an entirely different prompting style than Sonnet/Opus, then lays out 12 numbered "moves" grouped into three sections: how prompting style must shift, where Fable 5 shines, and mistakes carried over from older models.

---

## ⚠️ Verification gate — do NOT propagate as fact until checked vs `claude-api` / official docs

- "Fable 5 has three effort levels — default is medium" — **unverified specific**; matches the hub's known `effort` param concept but the exact level names/default were not independently confirmed in this capture.
- "1 million token context window ≈ 750,000 words ≈ 10 full-length novels" — **unverified arithmetic/marketing framing**, not sourced to official docs in this piece.
- "Asking it to show chain-of-thought can trigger a refusal entirely" — **unverified behavioral claim**, no measurement given; distinct from (and narrower than) the refusal→Opus-fallback mechanism tracked as a pending verify-then-codify item in other captures — this piece does NOT mention that fallback mechanism at all.
- Solar-system/eclipse-simulation "launch day demo" claim — **unverified anecdote**, not fetched/confirmed from an Anthropic source in this capture.
- "$50 per million output tokens" for Fable 5 — **unverified pricing claim**, do not cite without checking current official pricing.
- Reference to a "Code with Claude Tokyo 2026 keynote" (42 min) — **unverified/unfetched**; not cached in `docs/claude-references/`.

---

## The 12 moves (faithful summary)

**Shift in how you prompt**
1. Give goals, not steps — over-specifying the route limits the model's own judgment.
2. Don't ask it to show its reasoning — narrating chain-of-thought interrupts adaptive thinking rather than improving it; ask for a post-hoc explanation instead if insight is needed.
3. Set the effort level explicitly before starting rather than letting the default (claimed: medium) apply to tasks that deserve more or less.
4. Give it more context than feels necessary — paste full documents/threads/history rather than summarizing, citing the 1M-token window.

**Where Fable 5 shines**
5. Long unattended agentic runs — plan, execute, self-check across hours without a check-in every step.
6. Creative writing — specificity in setup/character/tone/constraint beats generic asks; don't just describe style.
7. Complex multi-step reasoning chains that older models couldn't sustain across a single run.
8. Agentic work — treat it as someone briefed with a goal + constraints who plans, delegates to sub-agents, and self-checks, not a chatbot operated turn-by-turn.

**Mistakes carried over from older models**
9. Micromanaging the approach (format/angle/sub-task handoffs) — control that helped Sonnet/Opus limits Fable 5.
10. Starting a fresh chat each session instead of keeping one long-running conversation that holds full project context.
11. Using Fable 5 for simple/cheap tasks where Sonnet is faster and far cheaper — "barbell" style task-to-model matching.
12. For voice/style, paste a real writing sample rather than describing the style in words.

---

## Relevance to this hub — LOW-MODERATE (broad corroboration, no net-new mechanism)

Nearly all 12 moves restate doctrine this hub already enforces. Map:

| Mahaximus's move | Existing hub analogue |
|---|---|
| #1 Goals not steps | `decision-authority.md`; `plan-before-coding.md` (plan states intent, not micromanaged steps) |
| #2 Don't ask for exposed reasoning | No direct hub rule — a prompting-style note, not a governance gap |
| #3 Set effort level explicitly | `.claude/rules/model-routing.md` (explicit model/tier choice per dispatch — same "don't let it default" discipline, different knob) |
| #4 Give full context, don't summarize | `context-management.md` — in tension with "progressive disclosure" (pointers over inlining); this hub optimizes for token economy at T0, so this move applies more to single large-context sessions than to the hub's subagent-delegation model |
| #5 Long unattended agentic runs | `loop-engineering` skill's DISCOVER→PLAN→EXECUTE→VERIFY meta-loop with hard budgets |
| #6 Creative writing specificity | No hub analogue (content-domain guidance, not governance) |
| #7 Complex reasoning chains | No direct hub rule — capability description, not a process |
| #8 Agentic delegation | `agent-orchestration.md`, `agent-team-selection.md` (subagent dispatch, flat vs team) |
| #9 Don't micromanage | `decision-authority.md` (decide-don't-ask for reversible/internal work) |
| #10 Stay in one long conversation | Partially in tension with this hub's session-continuity model (`/end-session`, `/continue`, `/start-session`) which deliberately persists state to disk ACROSS sessions rather than keeping one long-lived chat — the hub's answer to context loss is durable file state, not an indefinitely long conversation |
| #11 Barbell — cheapest sufficient model | `.claude/rules/model-routing.md` — **verbatim match**: "cheapest sufficient model per dispatch," haiku/sonnet/opus tiers, escalate one tier on failure |
| #12 Paste voice samples, don't describe style | No hub analogue (content-domain guidance) |

**Net-new for the hub: none.** This is the weakest-signal capture in the Fable-5 cluster so far by relevance — several moves (#2, #6, #7, #12) are prompting/content-craft tips outside this hub's governance scope entirely, and the two moves that touch hub doctrine most directly (#4 give-more-context, #10 stay-in-one-chat) actually sit in mild tension with this hub's established patterns (progressive disclosure; disk-based session continuity over indefinite single-conversation persistence) rather than reinforcing them — worth noting as a discrepancy, not a rule change, since the hub's approach is a deliberate multi-session/multi-agent design choice, not an oversight. The refusal-fallback mechanism tracked as a pending item elsewhere is **not** mentioned in this piece.

**Action: none.** File for corroboration-count and discrepancy-tracking purposes only. Cross-links: [undefinedKi Fable guide](2026-07-04-undefinedki-build-anything-with-fable5.md), [KanikaBK 10 mistakes](2026-07-08-kanikabk-10-mistakes-with-fable5.md) (same model-routing + goal-setting corroboration; neither mentions the context-window tension noted above).
