# Fable distillation-safeguard boundary check (2026-07-14)

**Verdict: the hub's manual-distillation practice sits INSIDE the documented boundary** — it is
"skill distillation" (steering Anthropic's own cheaper models with prose procedures), not the
weight/capability extraction the safeguard targets. Four red lines below keep it that way.
Owner-approved as "decision C" of the 2026-07-14 Fable-usage scan.

## What the safeguard actually is (first-party sources, fetched 2026-07-14)

- **Target:** "large-scale attempts to extract ('distill') Claude's capabilities to train
  competing models" — pattern-based classifier detection; response is fallback/degradation to
  Opus 4.8 rather than hard refusal ([anthropic.com/news/claude-fable-5-mythos-5](https://www.anthropic.com/news/claude-fable-5-mythos-5)).
- **API surface:** the `frontier_llm` refusal category — "the request could assist the
  development of competing AI models, restricted under Anthropic's commercial terms. Benign
  machine learning work can also trigger this category" — and the separate
  `reasoning_extraction` category for requests that ask the model to reproduce internal
  reasoning in response text ([Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)).
- **No explicit public permitted/prohibited line** is drawn for capturing model *behavior* as
  prompts/skills/manuals. However, Anthropic's own prompting guide actively RECOMMENDS the
  practice-shaped activities: constructing memory systems of lessons, refactoring/authoring
  skills from what the model learns, and reading structured `thinking` blocks (not echoed
  reasoning) when visibility is needed ([Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)).

## Our practice, itemized against that boundary

| Hub activity | Shape | Why it's inside the line |
|---|---|---|
| Operating Manual authorship (Fable writes its own working procedures; `plugins/fable-operating-manual/`) | prose heuristics, no CoT, no outputs-as-training-data | The prompting guide's own "capture lessons / author skills" recommendation; steers Claude-family models only |
| Distilled-core per-session injection | prompt steering of Sonnet/Opus | Prompt-space, intra-Claude; zero training |
| Parity exams (`/model-parity-test`, 10–33 blind cases, run a handful of times total) | low-volume behavioral evaluation | Orders of magnitude below "large-scale extraction"; purpose is routing OUR work among Anthropic's own tiers |
| Rubric mining from our own PR ledgers | derives from OUR artifacts, not model probing | Not extraction at all |

Two structural facts do most of the work: **(1) nothing we do trains any model** — no
fine-tuning, no datasets built from Fable outputs; everything stays in prompt/steering space;
**(2) the beneficiary is Anthropic's own model family** — routing between Fable/Opus/Sonnet on
one account is the opposite of "competing models."

## Red lines (the drift this document exists to prevent)

- **R1 — Never train on Fable outputs.** No fine-tuning of ANY model (including open-weights
  internal helpers) on Fable-generated data. The moment "manual" becomes "dataset," we've
  changed category. This is the hard line in the commercial-terms language.
- **R2 — Keep probe volume small; re-check before scaling.** Detection is pattern-based on
  extraction-STYLE querying. Today's exam battery (tens of cases, occasional) is trivially
  small. Before any "run the trap battery nightly across hundreds of cases" automation,
  re-read this doc and reassess — systematic high-volume behavior-mapping is the shape the
  classifier hunts, regardless of intent.
- **R3 — Procedures, never reasoning.** Manuals capture WHAT to do; never elicit, store, or
  replay raw chain-of-thought (`reasoning_extraction` — already codified in
  `model-routing.md` and the 2026-07-14 phrase audit).
- **R4 — A `frontier_llm` flag or repeated silent Opus-degradation is a STOP signal.** Review
  against this doc; never rephrase around the classifier (same doctrine as the cyber category
  in `model-routing.md` preemptive routing).

## Residual ambiguity (flagged honestly)

The hub repo is public, so the Operating Manual's Fable-derived procedures are published.
Anthropic draws no explicit line on sharing behavioral write-ups; community precedent
(multiple public "fable-method"-style distillations) and Anthropic's own published prompting
patterns suggest this is normal practice, but it is an inference, not a documented permission.
Cost of being wrong is low (takedown of prose), and R1–R3 keep the content firmly in the
prose-procedure category. Re-verify if Anthropic publishes explicit guidance on sharing
model-behavior distillations.
