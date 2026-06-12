# Scope: global

# Plan Before Coding

**One-line rule:** For any non-trivial change, produce a **visible plan** BEFORE writing the first
line of code. Planning is the cheapest place to catch a wrong approach; code written before a plan
is the most expensive place to discover one.

This file is the SSOT for the "plan first" discipline. It sits **after** the intent/confidence
gate (`decision-authority.md` — which decides *what* to build) and **before** TDD
(`tdd-rule.md`) and the step-by-step development workflow (`workflow.md`).

## When a plan is MANDATORY

Produce a plan before the first code edit when ANY of these hold:

- The task touches **3+ files**, or needs **3+ ordered steps**.
- It's a **new feature, screen, endpoint, schema change, refactor, or migration**.
- It involves an **architectural decision or trade-off** with more than one defensible answer.
- It changes **domain-critical calculation or data-integrity logic** (money, dosage, scoring,
  permissions — anywhere a silently-wrong number or state is worse than a crash).
- You would otherwise be **guessing at structure** — you cannot yet name the files you will change.

## When a plan is NOT required (just do it)

- Typo / one-line fix / rename / dependency bump / comment.
- A single-file change with one obvious, unambiguous edit.
- Read-only investigation, Q&A, or running tests/verification.

Do NOT gold-plate a plan onto trivial work — that is its own waste (KISS).

## What the plan MUST contain

A plan is not a restatement of the ask. It MUST show:

1. **Approach + WHY** — the chosen approach and why it beats the alternatives, not just *what*
   you will do.
2. **Files to create/modify** — the concrete list, by path. If you cannot list them, you are not
   ready to plan — explore the codebase first.
3. **Build sequence** — ordered steps, each independently verifiable.
4. **Verification** — how each step is proven: which test, which build/run command, which
   UI/DB signal.
5. **Risks / assumptions** — what could break, plus an explicit `**Assumption:** X` line for
   anything uncertain.

## How to surface it

- **Substantive / multi-step work** → use **plan mode** so the plan is reviewed before any edit;
  execute on approval. When requirements are still unclear, run `/brainstorm` or
  `/writing-plans` first.
- **Finalized scope handed to an unattended executor** → author a contract via
  `/autonomous-contract` — the contract IS the plan for autonomous runs.
- **Smaller-but-non-trivial work** that does not warrant plan mode → write a short **inline plan
  block** (Approach / Files / Steps / Verification) in the response BEFORE the first
  `Edit`/`Write`.

## Root-cause map is part of the plan (not a separate step)

The plan MUST trace the **root cause to its single source** and **enumerate EVERY
consumer/surface** the fix touches BEFORE the first edit — so the fix is the root-cause fix,
never a patch of one visible symptom that leaves siblings live. Patching the first symptom you
see, then discovering more mid-verify, is the failure this prevents (canonical incident shape: an
empty-state fix patched the headline metric but left sibling labels and chips false, because the
consumer map wasn't drawn first). If you cannot list every surface a change affects, you are not
ready to edit — finish the map.

## Propagation to dispatched workers (ALL invoked roles)

Plan-before-coding AND root-cause-not-patch are NOT just the orchestrator's discipline — they
bind **every role/agent the orchestrator dispatches to change code**. So:

- The dispatch prompt to any code-changing worker MUST require: "produce a plan (approach + full
  file/consumer map + verification) before editing; fix the ROOT cause across ALL affected
  surfaces, never a one-symptom patch."
- The orchestrator (supervisor, `supervisor-verification.md`) MUST verify the returned work was
  root-cause + complete (no un-touched siblings), not accept a worker's patch.
- Independent reviewers MUST be asked to check specifically for "is this the root cause or a
  patch?" and "are all sibling surfaces covered?".

## Relationship to the other gates (no duplication)

- **Confidence gate** (`decision-authority.md`) decides WHAT to build by converging on intent.
  Planning comes AFTER intent is locked and decides HOW.
- **TDD** (`tdd-rule.md`) red-first follows the plan: the plan names the tests; TDD writes them
  failing-first.
- **Autonomous contract** (`/autonomous-contract`) is the planning artifact for unattended runs.
- Per-turn reminders of this rule (e.g. via a prompt-submit hook) keep it from being missed under
  context pressure — see `prompt-auto-enhance-rule.md`.

## CRITICAL RULES

- MUST produce a visible plan (plan mode, autonomous contract, or inline plan block) before the
  FIRST code edit on any non-trivial change.
- MUST include the concrete file list + WHY-this-approach + verification steps — a plan missing
  these is a restatement, not a plan.
- MUST re-plan immediately if the approach goes sideways mid-implementation instead of pushing
  forward.
- MUST draw the root-cause + full consumer/surface map BEFORE the first edit — fix the root
  across ALL surfaces, never a one-symptom patch.
- MUST propagate both mandates (plan-first + root-cause) to EVERY dispatched code-changing
  worker via the dispatch prompt, and verify the returned work honored them (no patches, no
  un-touched siblings).
- MUST NOT force a plan onto trivial/mechanical work (KISS) — the trigger list above is the gate.
- MUST NOT duplicate the confidence-gate / TDD / contract content — cross-reference, never copy
  (`configuration-ssot.md`).
