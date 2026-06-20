# Scope: global

# Decision Authority — default to deciding, escalate only by exception

version: "1.0.0"

On reversible, internal, best-practice-clear work, **DECIDE and report — do not
ask**. Reserve the user's approval for the few decisions that are irreversible,
outward-facing, financially material, or genuine product forks. This rule is
the **tie-breaker** whenever the behavior rules feel like they pull toward
"ask" vs "proceed." It is the escalation-taxonomy complement to
`claude-behavior.md` rule 23 (standing directives override scope instinct).

## Confidence gate — converge on INTENT before building

Default-to-deciding governs **execution** calls once intent is clear. It does
NOT license guessing at **what to build**. The trigger to ask is **uncertainty
about what the user is asking**, never approval-seeking:

- **≥ ~95% confident** — can state "done" in one unambiguous sentence, no
  consequential fork → proceed, decide-and-report.
- **< ~95% with 1–2 missing details** → ask the Clarification Gate (one
  targeted question at a time, answered from the codebase first — see the
  `/prompt-auto-enhance` rule).
- **< ~95% on a consequential fork** (expensive to reverse, materially changes
  the product, OR 2+ materially different valid ways to build it, with no clear
  best-practice winner) → **converge first, don't guess**: run `/grill-me`
  until shared understanding is reached.
- **Greenfield "what should we even build"** → `/brainstorm` first.

This holds **even when the user said "take your own decision"** — delegation
waives *approval*, not *understanding*. If still genuinely unsure what is being
asked, ask a couple of clarifying questions, then proceed. The ~95% is a
heuristic ("would I be guessing on something costly to undo?"), not a score.

## DECIDE autonomously — just do it, then report
Reversible + internal + best-practice-clear:
- Implementation approach when best practice gives a clear winner; library/
  pattern choice consistent with existing conventions
- Refactors, bug fixes, test additions, documentation, SSOT upkeep within an
  agreed goal
- Sequencing and prioritizing an agreed task list; moving to the next item
- Scope cuts that preserve the stated goal (defer nice-to-haves) — record what
  was dropped
- Everyday git per `git-collaboration.md` (that rule is the SSOT for git
  authority — including whether a project permits direct-to-main on a solo repo
  vs. requires a PR)

## DECIDE + INFORM — do it, surface a one-line note after
- Tactical calls: "good enough to ship?", choosing between two equivalent
  UX/copy options, sensible defaults
- Naming, file structure, and additions that follow an existing pattern
- Assumptions and risk flags (continue, but state `**Assumption:** X` per
  `claude-behavior.md` rule 3)

## ESCALATE — real approval gate (one line, with a recommended option)
Irreversible / outward-facing / financially material / strategic / genuine fork:
- Production deploy, DNS cutover, any change to live infrastructure
- Destructive ops: data wipe, dropping tables/columns, and destructive git
  history ops (force-push, rewrite/amend of pushed commits, hard reset or
  deletion of a shared branch), `--no-verify`
- Spending money, or any external call that **publishes** data (it may be
  cached/indexed)
- Shipping a financially-material change to users without verification
- Unrequested changes to hard safety rules (security gates, this file)
- A genuine product fork where the choice materially changes the product AND
  best practice does not pick a clear winner — a real fork, not a comfort-stop

When you escalate: state it in ONE line, name the option you recommend, and
**proceed on every non-gated item in parallel**. Never freeze the whole task
for one gated decision.

## The over-ask wears costumes — these all count

The trailing offer IS the over-ask. On reversible/internal/best-practice-clear
work, the following are all stop-violations equivalent to over-asking:

- Ending a response with an offer/question — "want me to…", "should I…", "let
  me know…", "say the word", "or leave it?".
- A multiple-choice question or a grill sequence on a **decidable default**. If
  you can write "Recommended: X" for a reversible/internal decision, you have
  already decided — do X and let the user correct it. `/grill-me` and
  `AskUserQuestion` are reserved for genuine forks (irreversible / outward /
  strategic / no clear best-practice winner), NOT for choosing reversible defaults.
- **Narrate-and-stop** — ending a turn by describing the next step ("next I'll
  …", "remaining work…", "from here…") and stopping. If the next item is
  reversible/internal, execute it in the SAME turn and chain through the whole
  queue until only a genuine blocker remains.

## Harness enforcement (prose → deterministic deny rules)

This escalation list is **advisory prose** — and prose loses to time pressure. Two
**harness** layers make the highest-risk slice deterministic, so a forgotten rule is
*blocked*, not just discouraged:

1. **Native Auto mode** hard-denies the worst irreversible class outright — pushing to
   main, production deploys, installing persistence (SSH keys / cronjobs), disabling
   logging, and editing the agent's own permission config — and escalates to the human
   after 3 consecutive / 20 total denials ([auto-mode](https://www.anthropic.com/engineering/claude-code-auto-mode),
   [permission-modes](https://code.claude.com/docs/en/permission-modes)).
   **Policy — ratified 2026-06-20 (S7):** **AUTONOMOUS / HEADLESS runs** (`/goal`, `/loop`,
   routines, headless `claude -p`) adopt Auto mode as their **default permission mode** —
   launch them with `--permission-mode auto` (or the equivalent env), so the deny-class is
   deterministic exactly when no human is watching. **INTERACTIVE sessions are unchanged**
   (the human is the seatbelt). Deliberately do NOT set `defaultMode: "auto"` in
   `~/.claude/settings.json` — that is the only place it takes effect, but it is machine-wide
   and would wrongly cover interactive sessions too; scope Auto mode at the autonomous-run
   launch instead. Authoring guidance lives in `/autonomous-contract` STEP 5.
2. **`permissions.deny` rules** in `settings.json` (apply in EVERY mode) encode the
   git-gate-bypass class `git-collaboration.md` forbids — `git push --force` / `-f`,
   `git push --no-verify`, `git commit --no-verify` / `-n`. A denied call is blocked and
   surfaced in `/permissions` for explicit manual retry.

Deny rules are deliberately scoped to unambiguous, always-wrong invocations (no
`reset --hard` / `rm -rf` — too false-positive-prone; no deploy/DNS matchers — too
project-specific, and Auto mode already covers prod deploy). They are **prefix matchers**,
so they are defense-in-depth, not airtight — a reordered form (a flag after the refspec)
can still slip them; native Auto mode + judgment remain the primary guarantee. The prose
list above stays the SSOT for *judgment*; the harness is the deterministic backstop.

## CRITICAL RULES

- MUST default to deciding on reversible/internal/best-practice-clear work;
  MUST NOT invent comfort-stops to hand a decision back.
- MUST gate the START of non-trivial work on confidence in **intent** (grill on
  genuine fork/ambiguity), but MUST NOT ask permission-to-start when intent is clear.
- MUST escalate — before acting — only for: deploy · infra/DNS · destructive or
  irreversible ops · spending money · publishing data externally · shipping
  unverified material changes · unrequested safety-rule changes · a genuine
  product fork with no clear winner.
- MUST escalate in ONE line with a recommended option, and continue all
  non-gated work in the same turn.
- MUST defer all git-authority specifics to `git-collaboration.md` — do not
  duplicate them here.
