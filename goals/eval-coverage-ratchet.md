---
name: eval-coverage-ratchet
description: "The eval-coverage ratchet (blocking --enforce mode + shrink-only grandfather list) stays on disk and wired into validate-pr."
enrolled: "2026-07-13"
source: "owner-approved backlog item 2026-07-13; PR #354"
last_verified: "2026-07-13"
predicates:
  - kind: file
    path: config/eval-coverage-grandfather.yml
  - kind: command
    cmd: "python -c \"import io; t=io.open('.github/workflows/validate-pr.yml',encoding='utf-8').read(); assert 'check_eval_coverage.py --enforce' in t\""
on_failure: "The eval-coverage ratchet was unwired (step lost --enforce) or its grandfather list was deleted — skill changes stop being held to eval coverage and the ratchet's only-improves guarantee is gone. Restore from PR #354; the wiring pin test is scripts/tests/test_eval_coverage_ratchet.py."
---

`check_eval_coverage.py --enforce` (validate-pr step): a changed skill without `evals/`
FAILS CI unless grandfathered in `config/eval-coverage-grandfather.yml` — a shrink-only
list whose entries a test forces out as evals are added. New skills ship with evals from
day one.
