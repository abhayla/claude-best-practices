# Scope: global

# Prompt Auto-Enhance

Every response starts with `*Enhanced: <what was checked>*` (under 15 words).
Examples: *Enhanced: prompt graded (B, 2 fixes), git state, 3 rules*

The hook (`prompt-enhance-reminder.sh`) gates triggering: prompts ≤15 chars and known
continuation phrases skip injection at the deterministic layer, so the strengthening
pipeline only runs on substantive prompts.

**The indicator is unconditional on substantive OUTPUT — even when the hook stayed
silent.** The hook gates on PROMPT shape; short / slash-command / continuation prompts
still spawn substantive work, and the discipline fires on the output's blast radius,
not the prompt's shape. Whenever a turn produces substantive output (real analysis,
multi-step answer, tool edits/commits), self-apply the banner + full process (transcript
+ grade card + final prompt) + `Role:` line + governance tail even with no reminder injected. The Stop hook `no-overask-guard.sh`
logs substantive turns missing the banner to `.claude/.enhance-misses.log` (telemetry,
non-blocking). Genuinely trivial turns (`yes`/`go ahead`) are exempt.

## MANDATORY OUTPUT — always SHOW the full enhancement process (default ON)

The one-liner is NOT enough — by default the user wants to SEE the whole pipeline on
every substantive turn. Render FULL mode (not the compact block):

- **Non-trivial prompt:** after the banner, render in this order:
  1. **Pipeline transcript** — per-step counts/deltas (skill STEP 4.5)
  2. **Before→after grade card** — per-dimension before/after scores + Changes Applied (skill
     STEP 4). The after-grade is NEVER self-asserted: when the blind re-grade fires (lift ≥ 2.0,
     any single-dim jump ≥ 3.0, test, or on request — STEP 3.6) the BLIND reviewer's number wins.
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
confidence gate), tiered:

- **1–2 small gaps** → exactly ONE question per turn (no upper limit; stop when
  confident, not at a count). Hold the full list internally, grouped by category
  (functional → UI/UX → scale); ask the next only after the current is answered,
  sequenced on prior answers — never ask what's already answered, implied, or
  contradicted. Each question gives a **recommended** option + one-line why, and
  why alternatives are weaker. Ask only what's unanswerable from Tier 1/2 context.
- **Consequential fork** and confidence < ~95% → converge via `/grill-me` or
  `/grill-with-docs` before building — never guess at WHAT to build.
- **"You take a call" / pre-authorized** → gate waived; proceed, stating assumptions.

Confidence is about **intent**, never reversible execution detail (stage 5 decides
those). The final prompt is shown for transparency, not approval — execution proceeds
in the same response.

## Resource CRUD

Prompts that create/update/delete a Claude Code resource follow the batch approval
flow in `/prompt-auto-enhance` — no resource changes without explicit user approval.

## Load-bearing contracts

- Banner on every response; Tier 1 gathered before responding; strengthening runs on
  every non-filtered prompt via the `/prompt-auto-enhance` pipeline (skip only Grade A
  / pure knowledge questions — the full process still renders)
- Full process (transcript + grade card + final prompt + role) is the default verbosity;
  compact format-A is a fallback only when the user explicitly asks to reduce it
- After the final prompt: role (4.7) → plan if coding (4.8) → execute under
  decision-authority (5) → verify edge (5.5) → git only if changes (6)
- Optional one-line skill hint at STEP 4.6 (max 2 skills, informational only — the
  skill's job is prompt enhancement, not execution routing); skip on direct,
  mechanical, bug-fix, lookup, and documentation prompts
