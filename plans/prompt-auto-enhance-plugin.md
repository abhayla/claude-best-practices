# Prompt-Auto-Enhance Plugin — Design Spec (WIP)

**Status:** design / gathering owner inputs — DO NOT build yet.
**Goals served:** G6 (first installable cross-project plugin) + G5 (each completed build sub-task accrues an honest trust-score calibration run, 12/30 → 30).
**Source workflow being packaged (4 artifacts + refs):**
- Skill: `.claude/skills/prompt-auto-enhance/SKILL.md` (+ `references/`)
- Rule: `.claude/rules/prompt-auto-enhance.md` (auto-loaded directive / MANDATORY OUTPUT)
- Hook: `.claude/hooks/prompt-enhance-reminder.sh` (UserPromptSubmit — the trigger gate)
- Hook: `.claude/hooks/no-overask-guard.sh` (Stop — the enforcement guard)
- Distributable copies also in `core/.claude/` (skill + `prompt-auto-enhance-rule.md`)

## Core requirement (owner, 2026-06-22)

**Everything hardcoded today becomes a user-editable setting.** A user who installs the
plugin picks: (a) how much of the enhance process they SEE, (b) which prompts get enhanced,
(c) all other input criteria. Settings are chosen at install, editable any time afterward,
and the plugin **auto-adjusts on the next run with no reinstall** (hooks already re-read the
flag file every invocation — same mechanism, generalized to a settings file).

---

## INVENTORY — every entry criterion & hardcoded behavior (cited to source)

### A. Trigger / entry criteria — WHEN does enhancement fire?
| # | Current hardcoded behavior | Source | Proposed knob |
|---|---|---|---|
| A1 | Skip if prompt ≤ **15 characters** (trimmed) | reminder.sh:127 | `trigger.min_length` + `trigger.length_unit` (chars\|words) — **owner noted it should be words, not chars** |
| A2 | Skip exact-match **continuation phrases** (yes/ok/okay/thanks/thank you/sure/got it/sounds good/proceed/continue/go/go ahead/go on/next/done/good/yes please) | reminder.sh:134 | `trigger.continuation_phrases[]` (editable list, add/remove) |
| A3 | Skip **continuation prefixes** ("now do/also/same for/and/then/next") when total ≤ **40 chars** | reminder.sh:143-148 | `trigger.continuation_prefixes[]` + `trigger.continuation_max_length` |
| A4 | **Run mode** `ENHANCE_MODE` = auto \| ask \| off | reminder.sh:51-60 | becomes `run_mode` (superset — see B) |
| A5 | One-shot opt-in: bare `enhance` re-runs prior prompt | reminder.sh:118-124 | `trigger.oneshot_keywords[]` |
| A6 | Substantive-OUTPUT threshold **≥ 300 chars** (what counts as "real work" for output-side firing) | guard.sh:81,156 | `trigger.substantive_output_chars` |

### B. Output / verbosity — WHAT does the user SEE? (the headline ask)
Today verbosity is monolithic (auto = the WHOLE process; ask = nothing + offer; off = nothing).
Owner wants granular component toggles + a true **silent/background** mode.
Decompose the rendered process into independent switches:
| # | Component | Source | Knob |
|---|---|---|---|
| B1 | `*Enhanced:*` banner line | rule MANDATORY OUTPUT | `show.banner` |
| B2 | Pipeline transcript (per-step) | skill STEP 4.5 | `show.transcript` |
| B3 | Diagnosis block (STEP 1) | skill STEP 1 | `show.diagnosis` |
| B4 | Grade card — self scores | skill STEP 4 | `show.grade_card` |
| B5 | **Independent reviewer column** (blind Agent() re-grade) — *real token/latency cost* | skill STEP 3.6 | `show.reviewer_column` + `run.independent_reviewer` (compute, not just display) |
| B6 | Before→after + Changes Applied | skill STEP 2/4 | `show.changes_applied` |
| B7 | Original→Final strengthened prompt | skill STEP 4.6 | `show.final_prompt` |
| B8 | `Role:` line | skill STEP 4.7 | `show.role_line` |
| — | **Presets** | — | `verbosity_preset`: `full` (all on) \| `prompt_only` (B7 only) \| `silent` (render nothing; strengthen internally and just answer) |

### C. Grade / strengthen behavior
| # | Current | Source | Knob |
|---|---|---|---|
| C1 | Skip strengthening for **Grade A** / pure-knowledge prompts | rule "Load-bearing contracts" | `strengthen.skip_at_grade` (default A) |
| C2 | Dimension weights: Task .25 / Context .25 / Role .20 / Output .15 / Verify .15 | rule + skill | `grade.dimensions[]` w/ weights (editable, must sum 1.0) |
| C3 | Inject `Act as …` persona when **Role&Framing < 7** | rule 4.6 / guard.sh:171 | `strengthen.role_threshold` |
| C4 | Independent reviewer runs EVERY turn, no threshold | rule STEP 3.6 | `run.reviewer_min_gap` (e.g. only re-grade if self-score < N) — cost control |

### D. Clarification / confidence gate
| # | Current | Source | Knob |
|---|---|---|---|
| D1 | 1 small gap → one question; ≥2 unknowns or <~95% intent confidence → `/grill-me` | rule "Clarification Gate" | `clarify.enabled`, `clarify.confidence_threshold`, `clarify.max_questions` |

### E. Enforcement (the Stop-hook — what's been blocking this session)
| # | Current | Source | Knob |
|---|---|---|---|
| E1 | Block substantive turn w/ no reviewer card; cap **4** | guard.sh:81-93 | `enforce.reviewer_card` (block\|telemetry\|off) + `enforce.cap` |
| E2 | Block card-without-diagnosis-substance; cap 4 | guard.sh:109-121 | `enforce.diagnosis_substance` (block\|telemetry\|off) |
| E3 | Over-ask detection (trailing offer/MCQ/recommend+?) | guard.sh:175-180 | `enforce.over_ask` (block\|telemetry\|off) |
| E4 | Narrate-and-stop detection | guard.sh:182-183 | `enforce.narrate_and_stop` (block\|telemetry\|off) |
| E5 | keepgoing auto-continue cap **12**/turn | guard.sh:193 | `enforce.keepgoing_cap` |
| E6 | Exemption markers `*Sync-check:*`, `*Session-boundary:*`, blocker keywords | guard.sh:133-149 | `enforce.exemption_markers[]` |
| E7 | Telemetry-only: banner-miss / block-miss / role-miss logs | guard.sh:151-173 | `enforce.telemetry` (on\|off) |

### F. Governance tail (currently ALWAYS on, NOT gated by ENHANCE_MODE)
plan-before-coding, decide-don't-ask, grill-when-unsure, narrate-and-stop — emitted every turn (reminder.sh:69-75).
For a *generic* plugin a downstream user may not want the hub's opinionated governance →
`governance.<each>` = on\|off. (Note: in THIS hub they're deliberately always-on; the plugin
default can preserve that while letting installers opt out.)

### G. Context tiers gathered before responding
Tier 1 (patterns/CLAUDE.md/git) always; Tiers 4-5 conditional (rule "Context tiers").
→ `context.tiers[]` (which to gather).

---

## Settings mechanism (live-editable, auto-adjusting)
- Single settings file read fresh by both hooks every invocation (generalizes the existing
  `.claude/.enhance-mode` pattern → e.g. `enhance-settings.json`). Editing it changes behavior
  on the very next turn — no reinstall. This satisfies "come back and change anything later."
- Inline set-commands (like today's `enhance auto|ask|off`) extended to common knobs.
- Plugin ships sane defaults = current hub behavior, so installing changes nothing until tuned.

## DECISIONS LOG
- **D1 — Plugin home (2026-06-22, OWNER-APPROVED): In-tree monorepo marketplace.**
  Consistency note vs Atlas (own repo): same rule, opposite ends — Atlas was a new/large/independent
  product with no hub source to couple to and had crossed product-incubation graduation triggers
  (own repo required); this is a small, tightly-coupled repackaging of existing hub artifacts
  (in-tree, generate-from-`core/.claude/`). `plugins/prompt-auto-enhance/`
  under a hub `plugins/.claude-plugin/marketplace.json` (git-subdir source); hub = single source
  of truth, plugin skills/hooks generated from `core/.claude/`. Rationale: requirement demands an
  *installable cross-project* plugin (rules out no-marketplace) that the hub keeps maintaining
  (own-repo is premature graduation for a tightly-coupled wrapper). Matches Anthropic's
  `claude-plugins-official` monorepo + the reverted G6 pilot layout. Graduation to own repo later
  is non-breaking (flip marketplace `source` git-subdir→url). Differs from Atlas (own repo) because
  Atlas was a large independent product that earned graduation; this is a small hub-authored wrapper.

- **D2 — Settings mechanism (2026-06-22): single `enhance-settings.json`** read fresh by both
  hooks every invocation (generalizes the existing `.claude/.enhance-mode` flag-file). Editing it
  changes behavior next turn, no reinstall. Determined by the "edit later → auto-adjust" requirement.
- **D3 — Silent-mode semantics (2026-06-22): run-internally.** In `silent`/background mode the
  plugin STILL strengthens the prompt and executes the improved version; it just renders nothing.
  Determined by owner's words: "only the final enhanced prompt should run automatically in the background."

- **D4 — Scope & toggle model (2026-06-22, OWNER-DECIDED + CORRECTED): ONE plugin containing
  EVERYTHING that belongs to prompt-auto-enhance** — the enhancement pipeline + **prompt-auto-enhance's
  OWN self-governance ONLY** (reviewer-card + diagnosis-substance enforcement, banner/MANDATORY-OUTPUT
  discipline, enhance telemetry, the clarification/confidence gate). A **master on/off switch defaulting
  ON**, plus an **individual on/off toggle for every criterion** (inventory groups A–E + G), **all
  default ON** → a fresh install reproduces today's enhance behavior; user switches OFF what they don't want.
  - **EXCLUDED — hub-wide governance is NOT shipped** (owner correction 2026-06-22): decide-don't-ask /
    over-ask (E3), narrate-and-stop (E4) + keepgoing cap (E5), plan-before-coding, role routing /
    engineering-roles, and the standalone grill-when-unsure governance line. These come from
    `decision-authority.md` / `plan-before-coding.md` / `engineering-roles.md` (hub engineering
    discipline, independent of prompt enhancement) and STAY hub-only.
  - **Build impact:** `no-overask-guard.sh` is double-duty today; porting SPLITS it — the plugin's
    Stop hook gets only enhance-process enforcement (reviewer-card + diagnosis-substance + telemetry);
    over-ask/narrate-and-stop/plan/role logic stays in the hub's own hook, unshipped.
- **D5 — Independent reviewer (2026-06-22): a per-criterion toggle, default ON** (follows D4's
  default-ON principle; installers can switch it OFF to cut the token cost).
- **D6 — Trigger length gate (2026-06-22): toggle default ON; unit configurable (chars|words),
  default `words`** (owner-stated); default threshold a tunable setting (start ~4 words ≈ current
  ≤15-char behavior). All other trigger lists (continuation phrases/prefixes) are editable too.
- **D7 — Settings UX (2026-06-22): `enhance-settings.json` is the SSOT** (read fresh each turn),
  with a friendly **`/enhance-config` command** to view/flip toggles and inline set-commands
  (`enhance <key> on|off`) extending today's `enhance auto|ask|off`.

## BUILD PLAN (owner-gated G6 — do NOT start until owner gives go-ahead)
1. Scaffold `plugins/.claude-plugin/marketplace.json` + `plugins/prompt-auto-enhance/.claude-plugin/plugin.json`.
2. Port the skill from `core/.claude/skills/prompt-auto-enhance/` into the plugin `skills/` (generated-from-hub SSOT).
3. SPLIT-port the 2 hooks → plugin gets enhance-process enforcement ONLY (reviewer-card + diagnosis-substance
   + telemetry + banner/clarify); over-ask/narrate-and-stop/plan/role stay in the hub's own hook (D4). Ship `hooks/hooks.json`.
4. Hooks read `enhance-settings.json`: master gate + per-criterion gates; default file = all ON ⇒ identical to today.
5. `/enhance-config` command + inline `enhance <key> on|off` set-commands.
6. README + default `settings.json`.
7. Tests: settings parse, each gate honored, "all-ON == current behavior" regression, silent-mode runs-internally.
8. Register + validate: registry entry, `marketplace.json`, full local CI.
9. **G5 accrual (honest):** record ONE honest calibration run per completed, verified sub-task via
   `collect_signals.py` (real signals only). Expectation: ~8 sub-tasks → +6–8 runs, 12/30 → ~18–20 —
   ADVANCES graduation, does NOT complete it (30 needs more tasks + calibration honesty analysis +
   owner's shadow-mode→auto flip). NO ledger padding — a red/unverified sub-task is not recorded clean.
   PRE-STEP: verify `collect_signals.py` writes to the per-project ledger the 30-run bar counts
   (`trust-score/ledgers/atlas.jsonl`), not just `calibration-ledger.jsonl`.

## v0.2 IMPROVEMENT ROADMAP (owner-approved directions 2026-06-22; NOT yet built)
Owner liked #1, #6; #2 = "make it fully configurable"; asked HOW for #3, #7.

- **R1 (was #1) — real, conditional blind reviewer.** Today the "Reviewer-after" column is self-reported
  (hook only checks the *token*). Fix: dispatch an actual context-blind sub-agent to re-grade, but ONLY
  when warranted (see R2's render-full condition) so cost is paid where it buys integrity. Or, if not
  dispatched, drop the "independent/blind" claim. Highest-integrity fix.
- **R2 (was #2) — expand config toggles.** Add/confirm switches: full card, transcript, grade card,
  reviewer firing, **render-full condition** (e.g. only when grade < N or strengthening changed a lot),
  **when-to-strengthen** vs not, and NEW **`execute_mode: auto | review-first`** — auto-run the
  strengthened prompt, OR present it and WAIT for the user to approve/edit/trigger. All per-criterion, default ON.
- **R3 (was #3) — effectiveness measurement (falsifiable).** `.claude/.enhance-telemetry.jsonl` row per turn
  {grade_before/after, strengthened?, rendered_full?, reviewer_fired?, execute_mode, was_control?}. A
  correction-detector (UserPromptSubmit hook reads transcript) marks the prior turn `corrected_next` when the
  new prompt is a redirect ("no/actually/not what I meant"). Configurable `measure.holdout_pct` skips
  enhancement on X% (control) via `$RANDOM`. `/enhance-stats` reports correction-rate enhanced-vs-control +
  grade delta. Trust-score philosophy: prove enhancement helps, don't assume.
- **R4 (was #6 + #7) — ONE accumulating-context module, two scopes.** Session-scoped store
  `.claude/.enhance-session-context.jsonl` = resolved clarifications (don't re-ask within session, #7);
  persisted store = recurring weak-spot diagnoses across sessions (#6). Plus a SKILL directive: scan the
  conversation before asking a clarification. Shared mechanism, built once.
- Deferred from tier-2: R-enforcement-false-positives (#4), R-self-grade-calibration (#5).

## PROPOSED UNIFIED SETTINGS CATALOG (2026-06-22 — awaiting owner decisions on the 6 NEW vars)
Top-down order (master first, nested when ON). NEW = the model-judged triggers T1–T6 proposed as switches.
1. enabled (master, ON)
2. when_to_run (automatic | ask_first | off)
3. WHICH PROMPTS: skip_short_prompts; skip_these_phrases; skip_phrases_starting_with;
   skip_if_just_a_question [NEW T1, ON]; skip_tip_for_simple_tasks [NEW T2, ON];
   also_check_when_short_prompt_makes_big_work [NEW T4, ON]
4. after_improving (run_immediately | let_me_review_first)
5. DISPLAY: show_the_process; how_much_to_show (every_time | scale_to_prompt_quality [NEW T3] | only_for_weak_prompts);
   weak_prompt_score_below; show_log_only_for_multipart_requests [NEW T5, OFF];
   display.show.{summary_line,step_by_step_log,whats_wrong,score_table,second_opinion_review,list_of_fixes,improved_prompt,assigned_role} (all ON)
6. IMPROVING: skip_if_already_grade (A); add_role_when_score_below (7); always_add_role_if_missing [NEW T6, ON]
7. scoring_criteria; ask_clarifying_questions; quality_checks.{require_review_table,require_fix_details,log_misses}; context_levels
DECISION NEEDED from owner: accept/reject each of the 6 NEW vars + confirm their defaults before building.

## MODEL-JUDGED TRIGGERS not yet configurable (audit 2026-06-22 — candidates for future switches)
These live in the SKILL (decided by model judgment), not the deterministic hooks, so they are NOT
yet on/off switches. Listed for completeness; turning any into a knob is owner-gated future work.
- **T1 — pure-knowledge-question skip:** if the prompt only ASKS a fact (not a do-something task),
  skip strengthening, just answer (SKILL.md:702). [highest-value candidate switch]
- **T2 — simple-task skip:** skip the skill-hint on direct/mechanical/bug-fix/lookup/documentation prompts (rule:94).
- **T3 — compact-vs-full by grade:** Grade A = skip strengthen but still show; Grade B = compact (1-2 fixes);
  weak = full makeover (SKILL.md:128-129,700). Finer than the plugin's binary `display.show_when`. [high-value candidate]
- **T4 — output-blast-radius firing ("/init class"):** fire on how big the OUTPUT is, not how short the
  prompt was (SKILL.md:11-14). Plugin's Stop guard partly does this via min_response_size; no explicit knob.
- **T5 — "3+ distinct parts" transcript gate:** show the step-by-step log only for multi-part requests (SKILL.md:288).
- **T6 — cap-exempt role fix at every grade:** add the `Act as …` role line even when otherwise skipping,
  whenever role/framing is weak (SKILL.md:128,369,937). Partly covered by `improving.add_role_when_score_below`.

## v0.2 PROGRESS (2026-06-22, on branch — verified green, not yet merged)
- **R2 DONE** — `execute_mode`→`after_improving` (run_immediately | let_me_review_first); adaptive
  display condition (`display.show_when` = every_time | only_weak_prompts); render master + per-part
  checkboxes consolidated under `display.show.*`; Stop-hook block-loop guarded in adaptive/reviewer-off modes.
- **Plain-English rename + `_help` DONE** (owner ask) — every jargon key renamed to novice terms
  (run_mode→when_to_run, render→display, enforce→quality_checks, triggers→when_to_enhance, …) with an
  embedded `_help` guide explaining each setting.
- **Global settings tier DONE** (owner ask) — precedence env > project `.claude/` > **global `~/.claude/`** >
  plugin default; inline `enhance …` edits + `/enhance-config` write the global file so one config
  applies to all projects; project file overrides per-project.
- 25 plugin tests + full suite green (1575 passed). R1/R3/R4 (real reviewer, effectiveness telemetry,
  learning/context module) remain on the roadmap above, not yet built.

## STATUS: BUILT & VERIFIED (2026-06-22)
- All files created under `plugins/prompt-auto-enhance/` + marketplace at `plugins/.claude-plugin/marketplace.json`.
- 19 plugin tests + full suite green (1569 passed, 137 skipped, 1 xfailed); dedup/secret-scan/quality-gate all pass.
- Independent code review (code-reviewer-agent): CHANGES-REQUIRED → both majors fixed (dead `independent_reviewer`
  switch + block-loop; shipped the copy-in rule file) + valuable minors (default renamed `enhance-settings.default.json`,
  reviewer-off decouples block B, whitespace-robust set-commands, README hook-enforced-vs-model-only legend). Re-verified green.
- Functional bug caught+fixed by tests: jq `// empty` collapsed boolean `false`, so the master switch never fired — now raw-read.
- G5: one honest calibration run recorded (`--project atlas`, score 85, no hard gate, ESCALATE/shadow) → ledger 12 → 13.
- FOLLOW-UPS (owner-governed, NOT done here): goals.yml G6 DoD + CLAUDE.md "G6 = 0%/orphan, no files exist" are now stale —
  updating what counts toward G6 is an owner call on the host-owned goal SSOT.
