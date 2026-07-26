# Prerequisites-Contract Compliance Sweep

Owner-approved deferred phase of the prerequisites-preflight contract (landed 2026-07-26,
PR #463; contract SSOT: `writing-skills` §2.3b, review gate: `skill-evaluator` §0.5).
Goal: every existing skill DECLARES its prerequisites (tools/CLIs, credentials, files,
services, AND user inputs/decisions), VERIFIES them in a `## STEP 0: Preflight` while the
user is present, and HARD-STOPS with one consolidated missing list — no mid-run input
requests, no undeclared fallbacks. End state: flip the CI ratchet (wave 5).

Inventory tool: `scripts/check_prereq_contract.py` (report-only; re-run per wave).
Baseline 2026-07-26: **286 SKILL.md · 34 pointer stubs (exempt) · 14 compliant · 238 missing.**

## Policy (set 2026-07-26)

- **Pointer stubs exempt** — the plugin body is the SSOT; fix it, not the pointer.
- **Deprecated alias stubs exempt** (`save-session`, `cc-adoption-scout`) — they only redirect.
- **`Prerequisites: none` must be explicit** (one line + reason); STEP 0 only when ≥1 real
  prerequisite exists. Reference-type skills usually land on explicit-none.
- **Declared fallback ladders are legal** (e.g. youtube-transcript captions→yt-dlp→Whisper)
  — document them inside the Prerequisites section.
- **Never renumber existing steps** — STEP 0 inserts before STEP 1.
- **Version bump MINOR** per skill; dual-home twins updated in the same change (synced → identical;
  shared → same insertion outside DUAL-SYNC fences; divergent → per-copy insertion); registered
  skills get registry hash+version+changelog resync; plugin bodies get their plugin.json bumped
  once per wave.
- **Ratchet-blocked skills** (not grandfathered + no evals — editing them fails
  `check_eval_coverage --enforce`) are batched WITH a real `/skill-evaluator full` eval each.

## Waves

| Wave | Scope | Count | Status |
|---|---|---|---|
| 1 | Hub+core synced pairs, no plugin twin, ratchet-safe: anthropic-multi-agent-research-system-skill, executing-plans, five-advisors, github, grill-me, reddit, twitter-x, youtube-transcript | 8 pairs | **THIS PR** |
| 2 | Core-tree ratchet-safe remainder (no plugin twin), batches of ~15 | ~100 | pending |
| 3 | Plugin-grouped batches, one plugin.json bump each: branch-lifecycle (branch-choice, continue, end-session, start-session, git-branch-lifecycle[shared]); cbp-workflows (claude-guardian, skill-master, + its other bodies); loop-engineering + cbp-build-test-workflows (brainstorm, writing-plans, + bodies); cbp-learning-workflow; prompt-auto-enhance (plugin-as-SSOT); stack packs | ~67 bodies + their hub/core twins | pending |
| 4 | Ratchet-blocked (eval-paired): 19 hub (apply-selections, bootstrap-dogfood-project, hook-transcript-fixture-test, modern-data-pipeline-diagram, platform-event-live-probe, plugin-lifecycle, provision-report, review-new-claude-features, scan-discovery-report, scan-repo [+ its known description defects], scan-url, self-improve, ssot-workflow-audit, synthesize-hub, synthesize-project, workflow-doc-reviewer, get-work-done, verify-effect-at-destination) + 4 core (dependency-migration-triage, full-defect-surface-sweep, mock-data-hunter, weakened-test-hunter — verify eval locations first; memory says weakened-test-hunter HAS evals) | 23 | pending |
| 5 | CI ratchet: extend `check_prereq_contract.py` with `--enforce` + shrink-only grandfather list; wire into validate-pr.yml | 1 | OWNER-GATED |

Known data quirks: `get-work-done` and `verify-effect-at-destination` frontmatter `name:`
parses oddly (showed as `.claude` in inventory) — fix frontmatter in wave 4.

## Per-skill recipe (waves 1–3)

1. Read the full skill body; enumerate REAL prerequisites from what it actually invokes
   (CLIs, env/creds, MCP/services, files, mid-run user prompts to front-load).
2. Insert `## Prerequisites` right after the title/intro block. None → explicit-none line.
   Any → class table/bullets + declared fallbacks + `## STEP 0: Preflight` before STEP 1
   (verify each item · collect all user inputs · ONE consolidated missing list · hard-stop;
   MUST NOT start with known-missing / pause mid-run / improvise undeclared fallback).
3. MINOR version bump; mirror to twins per dual-home class; registry resync for registered.
4. Wave gate: dual-home tests + full local CI (pre-git-merge-checker-agent) + eval-ratchet
   check; land CI-gated via auto-merge.

## Status log

- 2026-07-26: Inventory baseline taken (286 files, 238 missing); waves 1+2 executed on
  `feat/prereq-sweep-wave1` — 8 hub+core pairs + 104 core-only skills, 112 registry entries
  resynced, compliance 14 → 134. Next: wave 3 (plugin-grouped), wave 4 (eval-paired), wave 5
  (CI ratchet, owner-gated).
