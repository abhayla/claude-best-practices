# fable-operating-manual

Make any model operate with **Claude Fable 5's working discipline** — and *prove* how much of it
transferred instead of assuming.

## What this plugin ships

| Piece | What it does |
|---|---|
| `manual/fable5-operating-manual.md` | The full Operating Manual: Fable 5's reasoning **procedures** (not tips), written by Fable at peak capability and grounded in real failure history. Portable — paste it into any Claude Project, Cowork session, or repo. |
| `manual/distilled-core.md` | The ≤100-line distilled core, auto-delivered into every session and every dispatched sub-agent by the hooks below. |
| `hooks/` | SessionStart hook (loads the distilled core into each session) + SubagentStart hook (injects it into every dispatched worker, so no agent runs without the discipline). |
| `skills/model-parity-test/` | `/model-parity-test <model>` — a blind, 3-arm exam: **A** plain model, **B** model + manual, **C** Fable 5 baseline. Trap tests with planted, objectively checkable errors; a separate blind judge scores all arms; output is a scorecard showing exactly how much of the Fable-discipline gap the manual closes. |
| `evals/` | The frozen exam battery (traps, replayed real tasks, judgment probes) + scoring rubric. |

## Why

Fable 5's edge is partly raw intelligence (not transferable) and partly **discipline** — reading the
real intent, re-deriving every number, refusing to guess, attacking its own conclusion before
shipping (transferable, as procedures). This plugin extracts the transferable half, enforces it
mechanically (hooks, not hopes), and measures the result. When the model landscape changes, run
`/model-parity-test <new-model>` and know in one command whether your processes still hold.

## Install

From the claude-best-practices marketplace:

```
/plugin install fable-operating-manual
```

Or load directly from source for a trial run:

```
claude --plugin-dir ./plugins/fable-operating-manual
```

## Usage

- Nothing to configure — the manual's distilled core auto-loads each session and into every sub-agent.
- Read the full manual: `manual/fable5-operating-manual.md` (also usable standalone outside Claude Code).
- Test a model: `/model-parity-test opus` (any model tier; add `--traps-only` for the quick version).
- The scorecard lands in `parity-results/` in your project.

## Honest limits

The manual transfers **discipline** — verification habits, refusal-to-guess, premise-checking. It
does **not** transfer raw intelligence: on genuinely novel hard reasoning, a stronger model still
wins, and the parity scorecard reports that residual gap honestly instead of hiding it.
