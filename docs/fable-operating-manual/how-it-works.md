# The Fable Operating Manual — how it works, in simple English

*(Owner-requested explainer, 2026-07-13. Companion to `plugins/fable-operating-manual/README.md`
and the measured results in `PARITY-REPORT.md`. This document explains the system to anyone —
no Claude Code knowledge assumed — and honestly registers every known gap and edge case.)*

---

## 1. The problem this solves

Different AI models drive sessions in this project at different times — the strongest one
(Fable 5) isn't always available, and cheaper ones (Sonnet, Haiku) are deliberately used for
routine work because they cost less. The risk: a weaker model quietly skips the working
discipline — it guesses instead of verifying, trusts a number without re-deriving it, declares
"done" without proof.

A model's strength has two parts:

- **Raw intelligence** — how hard a problem it can solve. *Not transferable.*
- **Discipline** — the habits: read the real intent, re-derive every number, refuse to guess,
  attack your own conclusion before shipping. *Transferable — because habits can be written
  down as procedures.*

The Fable Operating Manual is the written-down discipline, extracted by Fable 5 itself from its
own real failure history, packaged so **any** model gets it automatically.

## 2. The three pieces

| Piece | Plain-English job |
|---|---|
| **The Manual** (`manual/fable5-operating-manual.md`) | The full book of procedures. Portable markdown — works pasted into any AI tool, not just Claude Code. |
| **The distilled core** (`manual/distilled-core.md`, ≤100 lines) | The pocket version. Small enough to load into *every* session without wasting the context window. |
| **The hooks** (`hooks/`) | The delivery mechanism. Two machine-triggered scripts: one loads the pocket version at the start of every session, the other injects it into **every dispatched sub-agent** — so no worker runs without the discipline, no matter which model it is. Hooks are mechanical: they fire whether or not the model "remembers" to ask. |
| **The exam** (`/model-parity-test`) | The proof. A blind 3-arm test — plain model vs. model + manual vs. Fable 5 baseline — using trap tasks with planted, objectively checkable errors, scored by a separate blind judge. It *measures* how much discipline transferred instead of assuming. |

## 3. Why it works with any model

The key design decision: **enforcement is mechanical, not voluntary.**

1. The model never has to *choose* to read the manual — the SessionStart hook puts the core in
   front of it before the first user message is processed.
2. Sub-agents (the workers a session dispatches for parallel tasks) get their own injection via
   the SubagentStart hook — verified live in this environment (the injected text reaches the
   worker verbatim).
3. Compliance is then *measured*, not presumed: the parity exam ran blind on Sonnet and showed
   **plain Sonnet failed 4 discipline traps; Sonnet + manual failed 0** — the manual closed
   100% of the discipline gap at roughly 1/8 the cost. Opus needed no manual (its baseline
   discipline already matched). The scorecard method and numbers: `PARITY-REPORT.md`.
4. The manual is the *soft* layer of a two-layer defense. The *hard* layer is deterministic and
   completely model-independent: CI gates that physically block a bad merge (the full test
   suite, secret scan, registry sync, the plugin version-bump gate), Stop-hooks that block a
   session from ending on an unfinished answer, and daily cron sentinels that re-verify
   standing invariants. A model that ignores the manual still cannot merge broken work.

## 4. Scenario walk-through (what happens, case by case)

| Scenario | What the system does |
|---|---|
| Normal interactive session, any model | SessionStart hook loads the distilled core before work begins. |
| Session dispatches a sub-agent worker | SubagentStart hook injects the core into the worker — every worker, every time. |
| Headless run (`claude -p`, scripts, verifications) | Hooks fire the same way; the core is present. |
| Scheduled cloud routine (e.g. the monthly release scout) | The routine checks out this repo, whose installed plugins include the manual; plus routine prompts carry explicit procedures as a second belt. |
| A *downstream project* (your apps) | The plugin installs there like any other (it is in the recommender's universal list), so app sessions get the same injection. |
| Switching to a new/cheaper model | Run `/model-parity-test <model>` — one command, blind-scored verdict on whether your processes hold on that model *before* trusting it. |
| Fable declines a request (refusal-as-success) | The model-routing playbook falls back to Opus mid-flow; the manual applies to the fallback model identically. |
| Model ignores the manual anyway | The hard layer catches what matters: CI blocks unverified merges, the Stop-hook blocks premature "done", telemetry logs the miss for the compliance lint to surface. |

## 5. Gaps and edge cases — the honest register

No process is gap-free. These are the known ones, each with its current mitigation and residual risk:

| # | Gap / edge case | Mitigation today | Residual risk |
|---|---|---|---|
| G1 | **Prose can be ignored.** The manual is instructions, not physics. | The deterministic layer (CI gates, branch protection, Stop-hooks, version-bump gate) blocks the *consequences* of ignored discipline. Telemetry logs (`.enhance-misses.log` etc.) make ignoring *visible*, and `lint_rule_compliance.py` turns the logs into curation evidence. | A weak model can still waste turns before the hard layer catches it. Accepted cost. |
| G2 | **Plugin not installed → no injection.** | It ships in the recommender's *universal* list (every project is told to install it), and the hub's own sessions carry equivalent operational rules. | A project that skips the recommendation runs bare. Detectable by its absence in the session-start context. |
| G3 | **Long sessions / compaction pressure.** Could the core get squeezed out of context? | The core is deliberately ≤100 lines; hooks re-deliver on every session start and resume, and every *new* sub-agent gets a fresh copy. | Mid-session drift in very long turns is possible — this is exactly what the Stop-hook guards exist for. |
| G4 | **Weakest model tiers unproven.** The exam proved Sonnet; Haiku-class was not part of the blind run. | The standing rule: run `/model-parity-test` on any tier *before* routing real work to it (model-routing confines Haiku to rubric-scoring/classification anyway, where the hard gates dominate). | Untested tier + skipped exam = unknown compliance. Process, not physics. |
| G5 | **Manual drift.** Practices evolve; a stale manual teaches yesterday's rules. | The manual lives in the hub repo under version control; edits follow the plugin lifecycle, and the CI version-bump gate (2026-07-13) makes silent-non-propagation impossible. The frozen exam battery can be re-run after any major revision. | No automatic re-exam cadence yet — re-runs are judgment-triggered. |
| G6 | **Non-Claude-Code runtimes** (plain chat, other IDEs). Hooks are a Claude Code mechanism. | The full manual is deliberately portable markdown — paste it into any tool's system prompt/project instructions. | Manual paste is a human step; nothing enforces it outside Claude Code. |
| G7 | **Raw intelligence is not transferable.** On genuinely novel hard reasoning, a stronger model still wins. | The parity scorecard reports this residual gap honestly (it measures it as its own exam arm); model-routing reserves frontier judgment for the frontier model. | Inherent — this system transfers discipline, not IQ. |
| G8 | **Hook failure or accidental uninstall.** | Hooks are fail-open (a session still works, just without injection — never a lockout); absence is visible in the session-start context; the clean-room validation pipeline proves the plugin serves before each release. | A silent hook regression between releases would need the exam or a context check to notice. |
| G9 | **Injection ≠ mid-session compliance.** A model can start disciplined and degrade as context grows. | Output-side guards judge the *end* of each turn (reviewer-card guard, narrate-and-stop guard, verifier-edge telemetry) — they fire on what was actually produced, not on what was promised. | Guards cover known failure classes; novel drift classes need a new guard (the telemetry→lint→curation loop exists to find them). |

## 6. How to check it yourself (one command each)

- **Is the manual loaded?** Look at the session-start context for the injected operating core,
  or ask the session "what operating manual are you running under?"
- **Does a model hold the discipline?** `/model-parity-test <model>` — scorecard lands in
  `parity-results/`.
- **Is the plugin healthy?** `PYTHONPATH=. python scripts/validate_plugin_cleanroom.py
  fable-operating-manual` — structural + serve proof in one command.

## 7. One-paragraph summary

Write the strongest model's habits down as procedures; deliver them mechanically into every
session and every worker regardless of model; back them with deterministic gates that don't
care which model is driving; and *measure* the transfer with a blind exam instead of trusting
it. Discipline travels; intelligence doesn't; the gates catch whatever falls through; and the
gaps that remain are written down here rather than discovered by surprise.
