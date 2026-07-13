---
name: hook-transcript-fixture-test
description: Ship any hook that parses transcripts, turn origin, or session state with fixture tests against CAPTURED REAL transcript samples — never the assumed shape. Use when creating or editing hooks that read transcript JSONL, classify turn types, or detect model output patterns (enhance guards, stop guards, turn-origin classifiers) — and when a guard hook misfires/false-positives, use THIS (capture the misfiring shape as a fixture first), not generic debugging; /systematic-debugging and /fix-loop come after the fixture reproduces the misfire.
version: "1.0.0"
type: workflow
triggers:
  - /hook-transcript-fixture-test
  - "fixture test this hook"
  - "the guard hook is false-positive"
  - "test the hook against real transcripts"
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
argument-hint: "<hook-path> [turn-shapes-to-cover]"
---

# Hook Transcript Fixture Test

Transcript-parsing hooks are this hub's single most-churned mechanism: ~13 fix commits over one
month on the enhance/over-ask guard family (as of 2026-07), nearly all the same defect — the hook was built on an
ASSUMED transcript shape and a real shape broke it (slash commands write TWO user entries, a
marker and a marker-less body; mid-turn text beside tool_use may never persist; machine-origin
turns look like user turns). Every one of those false-positive cycles was preventable by testing
against captured real samples before shipping.

## STEP 1: Enumerate the Turn-Shape Matrix the Hook Branches On

List every turn/transcript shape the hook's logic distinguishes. Minimum viable matrix for a
turn-classifying hook:

| Shape | Known trap |
|---|---|
| Human free-text prompt | baseline |
| Slash command | TWO user entries: `<command-name>` marker + a marker-less body — naive "last user entry" reads the body and misclassifies |
| Skill-execution turn | skill content arrives as a user-role entry that is not human-typed |
| Machine-origin turn (task-notification, scheduled wakeup, system-reminder-only) | not human-typed; ceremony/enforcement must not fire |
| Model turn with parallel tool_use | mid-turn text blocks beside tool_use may never persist to the transcript — a guard asserting on them false-positives |
| Final-submission vs last-entry | guards must read the final SUBMISSION, not the last JSONL entry |

Add any shape your specific hook introduces. Each matrix row becomes at least one fixture.

## STEP 2: Capture Real Samples

Pull REAL transcript excerpts for each row — from live session JSONL under
`~/.claude/projects/<project-dir>/` (main sessions and subagent transcripts; `<project-dir>` is
the project path with separators flattened to dashes, e.g. `D--Abhay-VibeCoding-myrepo`), or by
generating the shape live (run a slash command, trigger a notification) and then excerpting.

- Trim to the minimal entries that exercise the branch (a handful of JSONL lines).
- Anonymize: strip real prompts/PII, keep the STRUCTURE (roles, markers, field names) byte-exact.
- Store under `scripts/tests/fixtures/transcripts/<shape-name>.jsonl` (create the directory on
  first use; or follow the project's existing fixture convention).
- A shape you cannot generate locally (e.g. a scheduled-wakeup turn before any routine exists) is
  recorded as a DOCUMENTED GAP: add a skipped test naming the missing shape and the capture
  condition — never hand-fabricate the fixture to fill the row.

Hand-writing a fixture from memory of the format defeats the entire point — the format in your
memory IS the assumed shape that keeps being wrong.

## STEP 3: Write the Fixture Tests

For each fixture, a test that runs the hook's parse/classify path against the file and asserts
the decision:

- FIRST identify the target hook's ACTUAL I/O contract — hooks in one repo differ (some read
  JSON on stdin per the platform hook contract; some are sourced libraries taking function
  arguments; some read env vars). Read the hook's own input handling before writing the harness.
- **Positive cases** — shapes where the hook SHOULD act (the real violation it exists to catch).
- **Negative cases** — every shape where it must stay silent (slash, machine-origin,
  skill-execution, sanctioned-banner-present). False positives are this hook family's dominant
  defect, so negative cases carry most of the value.
- Invoke the hook through that contract as the platform does (stdin JSON / args / env), not by
  sourcing internal functions only — the I/O boundary is part of what breaks.

## STEP 4: Run the Matrix and Wire Into the Suite

Run the tests; every matrix row must have at least one passing fixture test before the hook
ships. Wire into the standing test suite (`scripts/tests/`) so the NEXT edit to the hook re-runs
the whole matrix — the churn record shows each fix for one shape regressed another until fixtures
held the line.

## STEP 5: On Any Live False-Positive, Capture Before Fixing

When the shipped hook misfires in a live session: FIRST excerpt that session's real transcript
into a new fixture reproducing the misfire, THEN fix against it. Locate the session file by its
session id under `~/.claude/projects/<project-dir>/` (the misfire report or hook log usually
carries the id; otherwise take the newest JSONL there) and excerpt the FULL turn — all entries
belonging to that turn, not just the single line that looks wrong, since misclassification
usually spans adjacent entries. The failing fixture is the regression guard; a fix without it
re-enters the fix-the-fix loop.

## MUST DO

- Always cover every negative shape in STEP 1's matrix — Why: 430+ logged guard misses and ~13
  fix commits came from firing on shapes that should have been exempt
- Always capture fixtures from real transcripts, not from the format documentation or memory —
  Why: the documented/remembered shape is precisely the assumption that has repeatedly been wrong
- Always exercise the hook through its platform I/O contract (stdin JSON, exit codes) — Why:
  parse bugs at the boundary (field renames, missing keys) don't show when testing inner
  functions directly
- Always add a reproducing fixture BEFORE fixing a live misfire — Why: fixes without regression
  fixtures caused the same guard to break a previously-fixed shape at least twice

## MUST NOT DO

- MUST NOT ship a transcript-parsing hook with zero fixture tests — write the STEP 3 minimum
  first — Why: every unfixtured guard in this hub's history entered a multi-PR false-positive
  fix cycle
- MUST NOT assert on mid-turn model text next to tool_use blocks — assert on the final
  submission instead — Why: mid-turn text may never persist to the transcript; guards on it
  false-block correct behavior
- MUST NOT classify turn origin by content heuristics when a deterministic marker exists — use
  the marker/SSOT classifier — Why: duplicated ad-hoc classification drifted between two hooks
  until a shared `classify_turn()` was extracted
- MUST NOT delete or loosen a failing fixture to make a fix pass — fix the hook or consciously
  supersede the fixture with a captured newer shape — Why: a weakened fixture is a silently
  weakened gate (the exact class the weakened-test hunter exists to catch)
