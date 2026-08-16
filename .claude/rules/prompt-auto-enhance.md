# Scope: global

# Prompt Auto-Enhance

Every response starts with `*Enhanced: <what was checked>*` (under 15 words).

## Prompt-side gate (input) — `prompt-enhance-reminder.sh`

Skips injecting the reminder (deterministic, UserPromptSubmit): a `/command` prompt, any
size (`enhance_slash_commands: false` is the canonical plugin default — SSOT
`plugins/prompt-auto-enhance/enhance-settings.default.json`); a machine-origin turn
(`turn-origin.sh` `classify_turn()` = `machine` — task-notification, scheduled-wakeup,
skill-execution, system-reminder-only); a ≤15-char prompt; or a known continuation phrase.
The **governance tail** (plan-before-coding, decide-don't-ask, grill-when-unsure,
narrate-and-stop, git) is emitted on every turn regardless, including slash/machine ones —
it is not part of the pipeline this rule governs.

## Output-side gate (what's actually checked) — `no-overask-guard.sh`

The hook gates on PROMPT shape; this gate fires on OUTPUT blast radius instead, so it also
covers turns the prompt-side gate stayed silent on. Below is every check it runs — a duty
with no line here is **guidance only**, not machine-verified; the skill (`/prompt-auto-enhance`
STEP 4–4.7) owns the "how", this rule owns the "what's checked".

**TELEMETRY-ONLY, never blocking** (T-143, owner-approved 2026-08-16, review Fix 3: 840
stop-violation auto-continues + 534 enhance-misses over 3 months of rule-tightening never
converged compliance, and each block cost a paid extra model turn — the logs stay as the
instrument, the whip is gone). Every check below LOGS a miss to `.claude/.overask-violations.log`
or `.claude/.enhance-misses.log` (unchanged files/line formats — `scripts/lint_rule_compliance.py`
still works off them) and lets the turn end; none of them re-open a turn or emit
`{"decision":"block"}`. Applies only to a substantive (≥300-char), non-exempt turn unless noted:
- **Card check**: needs a markdown row combining `before|after|self` with `reviewer`, OR one
  of `reviewer-after` / `reviewer col` / `blind re-grade` / `independent-reviewer`, PLUS a
  closing `overall` row (`overall`, a letter transition like `b → a`, or `weighted total`).
  Either missing → logged as `reviewer-card-miss`.
- **Substance check** (only once a card matched): needs `diagnosis:`, `changes applied`, a
  `MISSING_*`/`VAGUE_INTENT`/`UNDER_CONSTRAINED` taxonomy tag, or a grade-a/zero-fix token.
  Missing → logged as `diagnosis-substance-miss`.
- **Banner short-circuit** (T-116): a turn whose first line matches `^\*enhanced` skips both
  checks above outright — no card or marker required.
- **Marker attestation**: when the harness drops a same-response pre-execution card (shares
  an API response with tool_use) so it never reaches the transcript, touching
  `.claude/.enhance-card-rendered.<session_id>` satisfies both checks in its place — real hook
  state, not prose.
- **Over-ask / narrate-and-stop**: a trailing offer, multiple-choice, recommendation+question,
  or deferred-next-step ending on reversible work → logged as `stop-violation (<class>)`.

**EXEMPTIONS** (checked before the checks above; a hit skips all output-side telemetry):
`is_slash` (last submission opens `<command-name>`, `Base directory for this skill:`, or a
literal leading `/`) and `machine` (`classify_turn()`) exempt everything below. `trivial`
(first line matches `ran (your )?input as-is|ran as-is|no change —|no enhancement`, turn
<600 chars) and `gradea` (first 3 lines match `grade a[^a-z]|grade: a|no strengthening
needed|no change —|ran (your )?input as-is|ran as-is|0 fix|no fix|prompt already strong
\(grade [0-9]`) exempt only the card/substance checks.

**Also telemetry-only** (logged to `.claude/.enhance-misses.log`):
- `enhance-banner-miss`: substantive, non-`is_slash`/non-`machine` turn whose first line does
  NOT match `^\*enhanced` (not gated by `trivial`/`gradea`).
- `enhance-block-miss`: banner present, not `gradea`, but none of `final prompt|what
  changed|ran (your )?input as-is|ran as-is|no change — ran|no enhancement` appear anywhere
  — the banner ran but nothing marks what got strengthened.
- `role-miss`: a `final (strengthened )?prompt` block exists with no `act as`.

Everything else previously described here — transcript formatting, the reviewer provenance
line, the >1.0 self-vs-blind divergence flag, exact tool-call ordering — is skill-owned
procedure (`/prompt-auto-enhance` STEP 4–4.7), not a hook-checked rule obligation. No new
always-on prose duty is added beyond the checks above.

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
