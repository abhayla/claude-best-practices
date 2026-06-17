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
multi-step answer, tool edits/commits), self-apply the banner + `Role:` line +
governance tail even with no reminder injected. The Stop hook `no-overask-guard.sh`
logs substantive turns missing the banner to `.claude/.enhance-misses.log` (telemetry,
non-blocking). Genuinely trivial turns (`yes`/`go ahead`) are exempt.

## MANDATORY OUTPUT — always SHOW the enhanced prompt (format A)

The one-liner is NOT enough — without the block the user never sees the strengthened
prompt or whether enhancement ran. Two shapes:

- **Non-trivial prompt:** after the banner, render a **compact Enhanced-prompt block**:
  > **What changed:** <fixes/additions made to the raw ask — 1-3 bullets>
  > **Final prompt executed:** <the exact strengthened prompt, verbatim>

  Compact — NOT the full grade-card wall (that renders on request, on explicit
  `/prompt-auto-enhance` invocations, and in test/audit runs). The Final-prompt block
  MUST open with the R1 `Act as …` persona whenever Role & Framing scored < 7 (skill's
  Role Selection Guide) — the `Role:` line (R2, stage 4.7) never substitutes for it.
- **Trivial / continuation prompt:** render the one-liner
  `*Enhanced: no change — ran your input as-is*` so the user is never left guessing.

Skipping the block on a non-trivial turn is a defect (class-C telemetry backstop).
This section is the SSOT for the FORMAT; stage 4.6 produces the content.

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

## Tier 1 — Always

1. Existing `.claude/` patterns — know what exists, do not duplicate
2. CLAUDE.md — already loaded, reference it
3. Git state — branch, recent commits, uncommitted changes

## Tier 2 — Conditional (prompt references specific files/features)

4. Nearby files — structural context
5. `registry/patterns.json` — check before suggesting new patterns

## Clarification & Confidence Gate — ask/grill until confident (before STEP 4.6)

Merged intent-resolution gate (Clarification Gate + `decision-authority.md`
confidence gate), tiered:

- **1–2 small gaps** → one targeted question at a time; no upper limit; stop when
  confidence is reached, not at a question count. Read the codebase before asking —
  each question must be unanswerable from Tier 1/2 context.
  - **Exactly ONE question per turn** — batching many questions in a single turn
    confuses the user. Hold the full list internally, group it by category
    (functional → UI/UX → scale/perf), and ask the next only after the current is
    answered.
  - **Each question carries a recommendation, not a blank prompt** — present the
    options, name the **recommended** one with a one-line justification, and a
    one-line reason each alternative is weaker, so the user makes an informed call.
    Prefer `AskUserQuestion` with the recommended option listed first.
  - **Sequence on prior answers** — re-read the running answer log before forming
    the next question. Each question MUST be consistent with, and build on, what was
    already answered; NEVER ask something already answered, implied, or contradicted
    by an earlier answer. Drop or adapt now-moot queued questions as answers land.
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
  / pure knowledge questions — the format-A block still renders)
- Format A is the default verbosity; full transcript on request / explicit invocation
- After the final prompt: role (4.7) → plan if coding (4.8) → execute under
  decision-authority (5) → verify edge (5.5) → git only if changes (6)
- Optional one-line skill hint at STEP 4.6 (max 2 skills, informational only — the
  skill's job is prompt enhancement, not execution routing); skip on direct,
  mechanical, bug-fix, lookup, and documentation prompts
