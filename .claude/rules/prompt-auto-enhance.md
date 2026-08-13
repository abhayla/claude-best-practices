# Scope: global

# Prompt Auto-Enhance

Every response starts with `*Enhanced: <what was checked>*` (under 15 words).

The hook (`prompt-enhance-reminder.sh`) gates triggering: slash-command prompts, ≤15-char prompts,
and known continuation phrases skip injection deterministically — the pipeline runs only on substantive free-text prompts.

**Slash commands are NEVER enhanced.** A `/command` — user-made OR Anthropic-provided
(`/init`, `/end-session`, …) — runs EXACTLY as-is, any size: canonical plugin default
`enhance_slash_commands: false` (SSOT: `plugins/prompt-auto-enhance/enhance-settings.default.json`);
`prompt-enhance-reminder.sh` skips `/*`-prompts and `no-overask-guard.sh` exempts those turns from
the enhance-card / diagnosis enforcement. The **governance tail** (plan-before-coding,
decide-don't-ask, grill-when-unsure, narrate-and-stop, git) still applies to slash-command turns.

**For free-text prompts, the indicator fires on substantive OUTPUT — even when the hook stayed
silent** (the hook gates on PROMPT shape; the discipline fires on the output's blast radius):
self-apply the banner + full process + `Role:` line + governance tail. The Stop hook
`no-overask-guard.sh` logs banner misses to `.claude/.enhance-misses.log` (telemetry,
non-blocking). Genuinely trivial turns (`yes`/`go ahead`), slash-command turns, AND **machine-origin turns**
are exempt. **Machine-origin (owner decision 2026-07-10, LOCKED — fire-where-it-pays):** the full
visible process fires ONLY on HUMAN-typed prompts. A task-notification, scheduled-wakeup,
skill-execution, or system-reminder-only turn is NOT human-typed — it gets at most a one-line banner,
never the transcript/grade-card/reviewer ceremony (autonomous work still owes the governance tail).
The classification is deterministic and shared: `.claude/hooks/turn-origin.sh` `classify_turn()` is
the SSOT, sourced by both `prompt-enhance-reminder.sh` and `no-overask-guard.sh` so they cannot drift.

## MANDATORY OUTPUT — sampled: full process on WEAK prompts, one-liner on strong ones (#290)

SAMPLED, not blanket-mandatory, and **HUMAN-SCOPED** (owner 2026-07-10): the full pipeline
(transcript + grade card + independent reviewer) is REQUIRED only on a HUMAN-typed **WEAK prompt**
(a dimension scored < 7, or a fix was applied). Machine-origin turns (see turn-origin.sh) are exempt
from the whole ceremony — banner included.
A **STRONG / Grade-A / zero-fix** prompt just needs the banner + a one-line Grade-A declaration — no full table forced.

- **Weak prompt:** after the banner render, in order: (1) **pipeline transcript** (skill STEP
  4.5); (2) **before→after card + independent reviewer** — a context-blind `Agent()` reviewer
  (fresh instance, sees only the two prompts + rubric) re-grades both; card shows PER-DIMENSION
  scores (Reviewer-after column) + a **mandatory `Overall` row** (weighted total, e.g. `F → B`;
  a card without it is incomplete); the blind Overall WINS the lift; print the `Independent
  reviewer (ran this turn …)` provenance line + self-vs-blind divergence (flag if > 1.0);
  (3) **Original → Final Strengthened Prompt** fenced blocks (STEP 4.6; Final opens with the R1
  `Act as …` persona when Role & Framing < 7); (4) **`Role: <name> — <why>`** line (R2, 4.7).
- **Strong / Grade-A / zero-fix prompt:** banner + one-line declaration in the FIRST 3 lines —
  `*Enhanced: <what was checked> — Grade A, no strengthening needed*`. Full table optional.
- **Trivial / continuation prompt:** the one-liner `*Enhanced: no change — ran your input as-is*`.

Skipping BOTH the full process AND the Grade-A declaration on a substantive turn is a defect
(`no-overask-guard.sh`'s `gradea` detector still blocks it). SSOT for FORMAT when the card
renders; skill stages 4–4.7 produce content. Compact format-A only on explicit user request.

**Ordering (owner defect report 2026-07-15):** the full process renders BEFORE any execution
tool call — never after the work. The ONLY tool call permitted before the render is the
context-blind reviewer dispatch (it produces the card's Reviewer-after column). Per-turn
sequence: (1) dispatch blind reviewer; (2) render banner + transcript + card + Original→Final
+ Role; (3) only then execute (research, edits, worker dispatches). Research needed to ANSWER
the prompt never precedes the card — the card grades the prompt, not the answer.
**Marker attestation (only when the banner itself didn't persist):** the harness drops assistant
text that shares an API response with tool_use, so on rare turns even a correctly-rendered
pre-execution card — banner included — may never reach the transcript. A turn whose FIRST
visible line IS the `*Enhanced:*` banner is its own evidence to the Stop guard (T-116,
owner-approved 2026-08-13 evidence-based curation) — it is never blocked for a missing card or
missing diagnose→fix substance, and the marker is NOT needed. Reserve the marker for the actual
dropped-transcript case: if you rendered the card earlier this turn but the banner does not show
up as the transcript's first line (mid-turn text beside tool_use), `touch
.claude/.enhance-card-rendered` in the FIRST execution tool batch instead (reset per user prompt
by prompt-enhance-reminder.sh).

## The unified per-prompt pipeline (0 → 6)

Stages 0–4.6 strengthen the prompt; 4.7–6 govern execution. Pointer pattern — each
stage's detail lives in its SSOT (`configuration-ssot.md`):

| Stage | What happens | SSOT detail |
|---|---|---|
| **0–4.5** | Grade → diagnose → strengthen, intent gate woven in → transcript | `/prompt-auto-enhance` + `decision-authority.md` |
| **4.6** | Show the final strengthened prompt (gate-resolved intent) | `/prompt-auto-enhance` |
| **4.7 Role** | State `Role: <name> — <why>`, dispatch its agents/skills | `engineering-roles.md` |
| **4.8 Plan** | Visible plan BEFORE the first code edit (skip trivial edits) | `plan-before-coding.md` |
| **5 Execute** | Decide reversible/internal; escalate irreversible in one line + keep working | `decision-authority.md` |
| **5.5 Verify** | Reproduce the doer's gate + independent review before commit; fires on OUTPUT blast radius, even on turns the hook skipped | `supervisor-verification.md`, `independent-test-verification.md` |
| **6 Git** | Only if committable changes: secret-scan → commit → push via `git-manager-agent` | `decision-authority.md`, `git-collaboration.md` |

## Context tiers — gather before responding

1. Existing `.claude/` patterns — know what exists, do not duplicate
2. CLAUDE.md — already loaded, reference it
3. Git state — branch, recent commits, uncommitted changes
4. *(conditional — prompt references files/features)* Nearby files — structural context
5. *(conditional)* `registry/patterns.json` — check before suggesting new patterns

## Clarification & Confidence Gate — ask/grill until confident (before STEP 4.6)

Merged intent-resolution gate (Clarification Gate + `decision-authority.md`
confidence gate), tiered. The gate question opens with the `*Sync-check:*` marker — a
required-intent stop the `no-overask-guard.sh` hook EXEMPTS, never an over-ask:

- **Exactly 1 small gap** → targeted questions (no upper limit; stop when confident). Hold the
  list internally; **pipeline independent questions (owner 2026-07-21):** batch answer-independent
  questions into ONE card (≤4), serialize ONLY on a true dependency — then ask the next question
  FIRST on receiving an answer, processing it after; never ask what's answered/implied/contradicted,
  give a **recommended** option + one-line why, ask only what's unanswerable from Tier 1/2 context.
- **≥2 material unknowns, OR a fork expensive to reverse with no best-practice default**
  (confidence in WHAT to build < ~95%) → `/grill-me` (or `/grill-with-docs` for ADR-worthy
  calls); converge BEFORE strengthening — don't collapse 2+ forks into one question, don't guess.
- **"You take a call" / pre-authorized** → gate waived; proceed, stating assumptions.

Confidence is about **intent**, never reversible execution detail (stage 5 decides those).
The final prompt is shown for transparency — execution proceeds in the same response.

## Resource CRUD

Prompts that create/update/delete a Claude Code resource follow the batch approval
flow in `/prompt-auto-enhance` — no resource changes without explicit user approval.

## Load-bearing contracts

- Banner on every response; Tier 1 gathered before responding; strengthening runs on
  every non-filtered prompt via the `/prompt-auto-enhance` pipeline (skip only Grade A
  / pure knowledge questions — the full process still renders)
- Optional one-line skill hint at STEP 4.6 (max 2 skills, informational only — the
  skill's job is prompt enhancement, not execution routing); skip on direct,
  mechanical, bug-fix, lookup, and documentation prompts
