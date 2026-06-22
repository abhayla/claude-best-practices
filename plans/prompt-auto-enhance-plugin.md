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
- **D1 — Plugin home (2026-06-22): In-tree monorepo marketplace.** `plugins/prompt-auto-enhance/`
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

## OPEN DESIGN DECISIONS (need owner input)
1. **Length unit**: switch A1 to **words** (owner-stated) — confirm default value (e.g. ≥ 5 words?).
2. **Silent mode semantics**: in `silent`, do we still RUN the strengthening internally and
   answer the *strengthened* prompt (compute cost, better answer) — or skip strengthening
   entirely (zero cost, raw answer)? Materially different.
3. **Independent reviewer by default**: it's the biggest token cost. Default ON (quality) or
   OFF (cheap), with opt-in? 
4. **Settings UI**: JSON file only, or also an interactive `/enhance-config` setup command?
5. **Plugin home**: in-tree G6 factory artifact, or incubated sibling per product-incubation rule?
6. **Governance tail**: bundle into this plugin (toggleable) or keep it a separate concern?
