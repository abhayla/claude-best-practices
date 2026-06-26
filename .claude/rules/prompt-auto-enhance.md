# Scope: global

# Prompt Auto-Enhance

Every response starts with `*Enhanced: <what was checked>*` (under 15 words).

The hook (`prompt-enhance-reminder.sh`) gates triggering: slash-command prompts, prompts
≤15 chars, and known continuation phrases skip injection at the deterministic layer, so the
strengthening pipeline only runs on substantive free-text prompts.

**Slash commands are NEVER enhanced.** A `/command` — user-made OR Anthropic-provided
(`/init`, `/end-session`, `/grill-me`, …) — is run EXACTLY as-is, any size, and is never routed
through the strengthening pipeline. This is the canonical plugin default `enhance_slash_commands:
false` (SSOT: `plugins/prompt-auto-enhance/enhance-settings.default.json`); the hub's operational
`prompt-enhance-reminder.sh` skips `/*`-prompts and the Stop hook `no-overask-guard.sh` exempts
slash-command turns from the enhance-card / diagnosis enforcement. There is nothing to "strengthen"
in a fixed command invocation, so the banner + grade card are suppressed for it. The **governance
tail** (plan-before-coding, decide-don't-ask, grill-when-unsure, narrate-and-stop, git) still
applies to slash-command turns — it is not part of the enhancement process.

**For free-text prompts, the indicator is unconditional on substantive OUTPUT — even when the
hook stayed silent.** The hook gates on PROMPT shape; a short / continuation free-text prompt can
still spawn substantive work, and the discipline fires on the output's blast radius, not the
prompt's shape. Whenever a (non-slash-command) turn produces substantive output (real analysis,
multi-step answer, tool edits/commits), self-apply the banner + full process (transcript
+ grade card + final prompt) + `Role:` line + governance tail even with no reminder injected. The Stop hook `no-overask-guard.sh`
logs substantive turns missing the banner to `.claude/.enhance-misses.log` (telemetry,
non-blocking). Genuinely trivial turns (`yes`/`go ahead`) and slash-command turns are exempt.

## MANDATORY OUTPUT — always SHOW the full enhancement process (default ON)

The one-liner is NOT enough — by default the user wants to SEE the whole pipeline on
every substantive turn. Render FULL mode (not the compact block):

- **Non-trivial prompt:** after the banner, render in this order:
  1. **Pipeline transcript** — per-step counts/deltas (skill STEP 4.5)
  2. **Before→after card + independent reviewer (EVERY turn, no threshold, no bypass)** — per-dim
     before/after scores + Changes Applied. A context-blind `Agent()` reviewer (fresh instance; sees
     only the two prompts + rubric, never the pipeline's scores) re-grades both prompts; the card shows
     its PER-DIMENSION scores (visible Reviewer-after column, not just an overall) — BLIND wins (STEP 3.6).
  3. **Original → Final Strengthened Prompt**, fenced blocks (skill STEP 4.6); the Final
     block MUST open with the R1 `Act as …` persona whenever Role & Framing scored < 7
  4. **`Role: <name> — <why>`** line (R2, stage 4.7) — never a substitute for the R1 persona
- **Trivial / continuation prompt:** render the one-liner
  `*Enhanced: no change — ran your input as-is*` so the user is never left guessing.

Skipping the process on a non-trivial turn is a defect (class-C telemetry backstop). This
section is the SSOT for the FORMAT; skill stages 4–4.7 produce the content. Compact
format-A is a fallback ONLY when the user explicitly asks to reduce verbosity.

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

- **Exactly 1 small gap** → ONE question per turn (no upper limit; stop when confident, not at
  a count). Hold the full list internally; ask the next only after the current is answered,
  sequenced on prior answers — never ask what's already answered, implied, or contradicted.
  Each question gives a **recommended** option + one-line why. Ask only what's unanswerable
  from Tier 1/2 context.
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
