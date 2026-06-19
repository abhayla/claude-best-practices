# Scope: global

# Cross-Project Context Capture — one home for facts that outlive a single repo

version: "1.0.0"

Some facts are bigger than the repo you discover them in — a shared vendor account, a
registration number, an API tenant, a contact, a compliance string, a cross-cutting
preference. Captured inside one project, they are invisible to the next and get
re-derived (or re-asked) from scratch. This rule says: the moment such a fact surfaces
or changes in ANY project, capture it to the workspace's cross-project global files in
the SAME session — so every project reads one canonical copy instead of keeping its own.

This is the cross-PROJECT analog of `learnings-routing.md` (which routes a learning to
one home WITHIN a project) and `configuration-ssot.md` (one canonical layer per config
fact). It composes with `security-baseline.md` — secrets follow that rule's
never-in-git discipline, captured to the secrets file, never the repo.

## The two workspace-level homes

A workspace (the directory that holds your project repos) MAY keep two global files,
conventionally at its root — ABOVE every repo so they are never `git add`-able:

| File (example name) | Holds | Route here when the fact is… |
|---|---|---|
| Global context file (e.g. `GLOBAL.md`) | non-secret cross-project facts + preferences: identity, contacts, registrations, links, vendors, compliance text, system/tenant details, UX/infra preferences | generic / non-secret |
| Global secrets file (e.g. `GLOBAL.env`) | SHARED, account-level credentials used by more than one project (keys, tokens, passwords) | a secret / credential |

If the workspace has no such files, this rule is a no-op — do not create them
speculatively (YAGNI). When they exist, they are the SSOT for that class of fact.

## Capture on sight (the standing behavior)

- **The trigger is discovery, not a dedicated task.** Whenever a session surfaces or
  changes a cross-project fact, UPDATE the right global file in the same turn: fits an
  existing section → edit in place (correct, don't duplicate); new topic → append a new
  section. Bump any "last updated" marker the file keeps.
- **Route by sensitivity:** secret/credential → the global secrets file; everything else
  → the global context file. NEVER put a secret in the context file, and never put
  prose/preferences in the secrets file.
- **Project-UNIQUE facts stay local.** Only promote a fact that more than one project
  could need. A single-project secret stays in that project's own `.env`.

## Reference by path — never copy into a repo

- Projects REFERENCE these files by PATH only; they MUST NOT copy the contents into any
  repo file (CLAUDE.md, docs, code, comments). Repos get pushed to remotes — a copied
  global fact leaks private/PII detail, and a stale copy is worse than none.
- One canonical home: when the same fact would otherwise appear in a repo and the global
  file, the repo keeps a one-line pointer to the path, never a duplicate
  (`configuration-ssot.md`).

## CRITICAL RULES

- MUST capture a cross-project fact to the workspace global file in the SAME session it
  surfaces or changes — fits a section → edit in place; new topic → append.
- MUST route by sensitivity: secrets → the global secrets file (per
  `security-baseline.md`); non-secret facts/preferences → the global context file. NEVER
  cross the two.
- MUST reference the global files by PATH only; MUST NOT copy their contents into any
  repo file — they hold private/PII detail and live above all repos by design.
- MUST keep one canonical home — promote only facts ≥2 projects could need; a
  single-project secret stays in that project's `.env`.
- MUST treat this as a no-op when the workspace keeps no such files — do not create them
  speculatively (YAGNI).
