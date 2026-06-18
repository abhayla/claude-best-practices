# Scope: global

# Human Approval Gates — the product checkpoints a pipeline MUST pause for

version: "1.0.0"

An autonomous idea→production pipeline MUST pause for explicit USER approval at a
small number of **product checkpoints**, no matter how confident the automation
is. These are *product-acceptance* gates ("does this match what the user wanted?")
and are distinct from `decision-authority.md`, which governs the assistant's
autonomy over reversible execution detail. Skipping them ships fast in the wrong
direction — the failure this rule prevents is "built beautifully, but not what was
asked," discovered too late.

## The mandatory gates (in pipeline order)

| Gate | Fires | User approves | Blocks until |
|---|---|---|---|
| **G1 — Design / UI mockup** | after a sample UI/prototype is produced, BEFORE implementation | "build THIS" — layout, flow, scope of screens | explicit approval |
| **G2 — Feature acceptance** | after build + verification, BEFORE release | "it looks and works as I asked" — the verified feature on the default path | explicit sign-off |
| **G3 — Production deploy** | before shipping to a live environment | the deploy itself (target, timing) | explicit approval — owned by `decision-authority.md` |

## Why these three (and not more)

- Building before **G1** risks implementing the wrong thing beautifully. **G1 has a
  precondition:** the BA discovery completeness audit (`ba-discovery-checklist.md`) MUST be
  clean first — a mockup approved on incomplete discovery just bakes the gap in. Do not present
  G1 while the independent completeness audit dissents.
- Shipping before **G2** makes the user discover the misfit in production.
- **G3** is the irreversible/outward gate `decision-authority.md` already owns; this
  rule only names it as a pipeline checkpoint.

Every other transition (schema, tests, refactors, library choices) is
reversible/internal — the assistant DECIDES it (`decision-authority.md`). Adding
approval gates there is over-asking. Keep human gates to the product-acceptance +
irreversible set; more gates is not more safety, it is friction.

## How a gate behaves

- A gate is a HARD pause: present the **concrete artifact** (mockup screenshot,
  verified-feature evidence, deploy plan) and STOP for an explicit yes. MUST NOT
  infer approval from silence, and MUST NOT treat an automated check (a11y pass,
  tests green, visual diff) as a substitute for the user's product sign-off — the
  automated result *feeds* the gate, it does not replace it.
- A gate pause is **exempt from the decide-don't-ask ban** — product acceptance and
  irreversible deploy are exactly the decisions reserved for the user
  (`decision-authority.md`). Open the pause with the artifact, never a bare
  "should I proceed?".
- Record each approval (what was shown, the decision) against the run state /
  goal-contract (`design-ssot.md`).

## Relationship to the other rules (no duplication)

- `decision-authority.md` — owns WHICH decisions are the user's; this rule names the
  three pipeline points where that applies. Deploy specifics live there.
- `design-ssot.md` — owns the goal-contract that G1 is approved against.
- `supervisor-verification.md` / `independent-test-verification.md` — produce the
  verified evidence G2 is approved against.

## CRITICAL RULES

- MUST pause for explicit user approval at G1 (UI mockup before build), G2 (feature
  acceptance before release), and G3 (production deploy).
- MUST present the concrete artifact at each gate — never infer approval from
  silence or from a green automated check.
- MUST NOT add approval gates to reversible/internal transitions — those are decided
  autonomously (`decision-authority.md`); extra gates are over-asking.
- MUST record each approval against the run / goal-contract.
- MUST treat a gate pause as required clarification, not an over-ask — it is exempt
  from the decide-don't-ask ban.

> **Salience note:** G1/G2 are **advisory-only** — firing on a flow-state ("a mockup exists,
> now about to build") that no prompt/tool signal cleanly detects, so unlike the verifier-edge
> gates they have no deterministic hook. G1's precondition (the BA completeness audit) DOES get
> the `ba-usecase-discovery-reminder.sh` salience layer; the gate pauses themselves rely on this
> rule + the model's discipline. Treat a forgotten G1/G2 as a first-class miss to capture in `lessons.md`.
