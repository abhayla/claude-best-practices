# writing-skills — Author Learnings Log

Process lessons from authoring runs. Read at STEP 1.0 of every run; append
per STEP 10. Distinct from the reference self-update protocol (Step 2.6),
which improves authored skills — this file improves the authoring process.
Promote to SKILL.md at 2+ occurrences.

---

## 2026-08-06 — Founding entry (instagram-post-fetch authoring run)

- Skill authored/updated: instagram-post-fetch (new, v1.0.0)
- What went wrong / what was learned: a skill whose knowledge lives in a
  LEARNINGS.md ledger legitimately skips the Step 2.6 reference protocol
  ("persists knowledge through another mechanism") — but the authoring
  checklist (Step 5.1) still demands the protocol row, which reads as a
  failure unless the exemption is cited explicitly in the eval report.
  Cite the exemption in the eval, don't silently skip.
- Status: CANDIDATE

## 2026-08-06 — Dual-home sync check missing from update flow (CI failure PR #495)

- Skill authored/updated: skill-evaluator (2.5.0 → 2.6.0)
- What went wrong / what was learned: edited only the hub copy of a skill
  classified `synced` in `config/dual-home-resources.yml` —
  test_dual_home_sync failed CI (hub/core drift). Before editing ANY
  .claude/ skill, grep `config/dual-home-resources.yml` for it; if synced,
  run `python scripts/sync_dual_home.py --sync <bare-name> --from hub`
  (bare name, no `skills/` prefix — the prefixed form errors) AND resync
  the registry entry (hash + version + last_updated) since the core copy
  is a registered pattern. Candidate SKILL.md fix: add this check to
  Step 1.3 Update mode.
- Status: CANDIDATE
