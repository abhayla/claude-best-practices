---
name: goal-pulse
description: Show the project's per-goal status and the single highest-value next action, so work stays anchored to the documented goals. Use at the start of a work session or when deciding what to do next.
type: workflow
allowed-tools: "Read Grep Glob Bash"
version: "0.0.1"
---

# Goal Pulse (cbp-workflows pilot)

A minimal, real skill shipped via a **plugin** (not copied into the project) — the proof artifact for Goal 6's split-distribution design.

## STEP 1: Read the documented goals
Read the project's goal SSOT (`README.md` goals section, or `goals.yml` if the project uses Atlas). Enumerate each goal with its title.

## STEP 2: Surface status + the next action
For each goal, state a one-line status (on-track / drifting / not-started). Then name the **single highest-value next action** — the goal with the largest gap toward its definition-of-done — and the concrete first file or task to advance it.

## STEP 3: Anchor the work
Begin the session on that top-ranked gap. Re-run this skill after a meaningful change to confirm the work moved the intended goal.

## MUST DO
- Anchor every substantive session to the documented goals — never start work that advances no stated goal.
- Surface the highest-gap goal first; do not bury it.

## MUST NOT DO
- MUST NOT invent goals not in the project's goal SSOT.
- MUST NOT claim a goal is "done" without checking its definition-of-done.
