---
name: rules-paths-frontmatter-gate
description: "The pattern validator rejects the non-existent `globs:` rule frontmatter key and no core rule carries it (Claude Code only honours `paths:`)."
enrolled: "2026-08-28"
source: "T-394 / PR #604; MECHANISM-DUE class rules-frontmatter-globs-instead-of-paths-loads-every-rule-unconditionally"
last_verified: "2026-08-28"
predicates:
  - kind: command
    cmd: "python -c \"import glob,io,re,sys; bad=[f for pat in ('core/.claude/rules/*.md','.claude/rules/*.md','plugins/*/rules/*.md') for f in glob.glob(pat) if re.search(r'^globs:', io.open(f,encoding='utf-8',errors='replace').read(), re.M)]; sys.exit('globs: frontmatter found in: '+', '.join(bad) if bad else 0)\""
  - kind: command
    cmd: "python -m pytest scripts/tests/test_workflow_quality_gate_validate_patterns.py -q -x -k \"globs_field or paths_field\""
on_failure: "A rule with `globs:` frontmatter got in, or the validator stopped rejecting it. Claude Code loads such a rule UNCONDITIONALLY in every session (IPODhan: 81/81 rule files, ~117k tokens at launch before T-394). Rename to `paths:` and restore the validator check."
---

Claude Code honours only `paths:` for path-scoped rules ("Rules without a `paths` field are loaded
unconditionally" — code.claude.com/docs/en/memory, fetched 2026-08-27). The hub had invented
`globs:` and `scripts/workflow_quality_gate_validate_patterns.py` ENFORCED it, so every
"path-scoped" rule in the hub and in every provisioned project loaded in every session. T-394
inverted the validator; T-396 fixed 5 app repos. This goal keeps both halves true: no `globs:` in
any hub-owned rule tree, and the validator's rejection tests still pass.
