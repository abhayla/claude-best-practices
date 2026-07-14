# Fable CoT-Phrase Audit — reasoning_extraction risk sweep (2026-07-14)

**What this is.** Fable 5's safety layer includes a `reasoning_extraction` refusal category
(official: [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback),
[Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)
— "don't instruct Fable 5 to echo its reasoning in response text"). A community report
([learnwithmeai.com](https://www.learnwithmeai.com/p/how-to-prompt-fable-5), **single-source,
unverified**) extends this: legacy CoT-eliciting phrases ("think step by step",
"explain your reasoning") can trip the classifier as false positives. The hub injects
thousands of lines of rule text into every session; this audit swept every injected/dispatched
surface for such phrasing. Approved as item #7 of the 2026-07-14 Fable-usage external scan.

## Method

- **Patterns:** `step(-| )by(-| )step`, `explain/show/share your reasoning|thinking|work`,
  `chain of thought`, `think(ing) aloud/out loud`, `thought process`, `echo/reveal … reasoning`,
  plus a second imperative-form pass (`show|explain|expose|output|state|reveal|echo|verbalize
  … reasoning|thinking|thought`) over the always-injected surfaces.
- **Surfaces, by injection tier:**
  - **T1 always-injected (hub):** `.claude/rules/`, repo `CLAUDE.md`, `CLAUDE.local.md`,
    user-global `~/.claude/CLAUDE.md`, hook-emitted reminder strings (`.claude/hooks/`),
    `plugins/fable-operating-manual/manual/` (distilled core, SessionStart/SubagentStart-injected).
  - **T2 downstream-injected:** `core/.claude/rules/`, plugin hooks.
  - **T3 dispatched:** `.claude/agents/`, `core/.claude/agents/`, plugin agents.
  - **T4 on-demand:** skills (hub, core, plugins).
- **Severity vocabulary:** MED = imperative uses a reported trigger phrase in injected rule
  text; LOW = flagged phrase in an on-demand or softer-imperative context; SAFE = descriptive
  ("step-by-step plan"), mitigation text, logs, or content-domain data.
- **Not done:** no live classifier probe (needs raw-API spend; the single-source claim stays
  labeled unverified). The rewrites below are cheap regardless of whether the claim holds —
  they remove the exposure without weakening any rule.

## Findings

| # | File:line | Injected tier | Phrase | Severity | Proposed rewrite |
|---|---|---|---|---|---|
| F1 | `core/.claude/rules/engineering-roles.md:56` (Debugging Engineer role) | T2 (+ inlined into role dispatches) | "analyze carefully, **think step by step**, find the root cause" | **MED** — the canonical reported trigger phrase, verbatim, as a role imperative | "analyze carefully and systematically, find the **root cause**" |
| F2 | `.claude/rules/claude-behavior.md:7` + `core/.claude/rules/claude-behavior.md:7` (rule 1, dual-home) | T1 + T2 | "In plans, **walk through reasoning step by step** — show WHY this approach over alternatives" | **MED-LOW** — directs reasoning exposure in output + flagged phrase | "In plans, lay out the rationale — show WHY this approach over alternatives, not just WHAT you will do" |
| F3 | `.claude/rules/claude-behavior.md:39` + core copy (rule 13, dual-home) | T1 + T2 | "Diagnose the root cause **step by step** … without **step-by-step** diagnosis" | **LOW** — procedural sense, but imperative about the model's diagnostic process, twice | "Diagnose the root cause methodically before suggesting a fix; jumping straight to a fix without systematic diagnosis leads to wrong fixes" |
| F4 | `core/.claude/skills/receive-code-review/references/answer-questions-p2.md:8` + `plugins/cbp-workflows/` copy | T4 | table row "**Show your reasoning**" | **LOW** — on-demand skill; right-hand cell already scopes it to trade-off justification | header cell → "Explain the trade-off" (plugin copy requires a cbp-workflows version bump — batch with its next release) |

## Non-findings (verified clean)

- `plugins/fable-operating-manual/manual/` (full manual + distilled core): **clean** on both passes.
- Repo `CLAUDE.md`, `CLAUDE.local.md`, user-global `~/.claude/CLAUDE.md`: clean.
- Hook-emitted reminder text (`.claude/hooks/`, plugin hooks): clean.
- `.claude/rules/model-routing.md:19` mentions "echo raw chain-of-thought" **as a prohibition** —
  mitigation text, keep as-is.
- `/prompt-auto-enhance` SKILL already rewrites "think step by step" → "evaluate"/"reason
  through" for reasoning models (its replacement table) — existing partial mitigation at the
  prompt layer; this audit closes the rule-stack layer.
- All remaining grep hits are descriptive/benign: "step-by-step plan/workflow/guide"
  (writing-plans, executing-plans, goal-creator, plan-before-coding, doc templates), agent
  output templates ("Step-by-step fix"), UX content data (CSV), and the gitignored prompt log.

## Application status (owner-gated)

Rule-text changes require explicit owner approval (claude-behavior.md rule 5). F1–F3 are
proposed as ONE batch; on approval the edit checklist is: apply to BOTH dual-home copies
(`test_dual_home_sync.py` gate), resync registry hashes for the registered patterns, respect
the ≤100-line rule budget, run the full local CI quartet. F4 is deferred to the next
cbp-workflows plugin release (version-bump propagation contract).

**Optional follow-up guard (propose, not built):** add the trigger-phrase regex as a
report-only class in `scripts/lint_rule_compliance.py` so a future rule edit reintroducing
the phrasing is flagged at curation time.

## Risk lines

- The trigger claim for "step by step" phrasing is **single-source**; the officially documented
  risk is only instructing reasoning-echo in response text. If the community claim is false,
  these rewrites still cost nothing (meaning preserved) — the asymmetry favors applying them.
- Not tested against the live classifier; a cheap raw-API probe (one Fable call with/without
  the phrases) would settle the claim if ever worth the spend.
- Sweep is regex-based; paraphrased reasoning-exposure imperatives outside the pattern set
  would be missed — the imperative-form second pass reduces but doesn't eliminate this.
