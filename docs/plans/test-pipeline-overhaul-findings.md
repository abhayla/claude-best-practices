# Findings: Test Pipeline Overhaul + Screenshot-as-Proof

> **Post-script (2026-04-24, Phase 3.1):** findings on nested `Agent()` dispatch
> and tiered orchestration (T1/T2A/T2B/T3) reflect the pre-platform-constraint
> understanding. Anthropic's docs ([link](https://code.claude.com/docs/en/sub-agents))
> confirm subagents cannot spawn subagents, so the industry-research observations
> that informed the 4-tier plan no longer apply to Claude Code's execution model.
> The current canonical design is `docs/specs/test-pipeline-three-lane-spec-v2.md`
> v2.2 (skill-at-T0). Observations about fail-closed gates, file-based artifacts,
> separation of diagnosis from remediation, and single-mapper principles remain
> valid — only the multi-agent orchestration assumption is retired.

## Discoveries

### Industry Research (validated against best practices)
- File-based JSON artifacts between stages is standard (GitHub Actions, GitLab CI) — not an anti-pattern
- Single canonical change-to-test mapper is best practice (Fowler, Nx) — duplicate mappers are anti-pattern
- Fail-closed is standard for pre-merge gates (GitHub Protected Branches) — fail-open is anti-pattern
- Distributed per-stage artifacts + terminal aggregator is correct pattern (GitLab, Allure)
- Running tests 3x across stages is anti-pattern — 2 targeted + 1 full suite is correct
- Diagnosis should be separated from remediation (Google SRE Book, Anthropic subagent docs)
- 876-line skill is in warning zone per project's own pattern-self-containment.md

### Cross-Reference Audit
- `/code-quality-gate` split has large blast radius: review-gate, architecture-fitness, 2 test files, pipeline config, docs
- Decision: use `references/` directory extraction instead of full split — preserves step numbers, JSON paths, all cross-refs
- `review-gate` orchestrates code-quality-gate and explicitly skips Step 5 when architecture-fitness runs
- `test_pipeline_integrity.py` and `test_pipeline_smoke.py` assert code-quality-gate presence in review-gate

### Token Cost Analysis (screenshot review)
- 1440x900 PNG ≈ 1,728 tokens per image
- 50-test suite at 100% review: ~$0.52 (Sonnet) / ~$0.17 (Haiku)
- Cost is negligible; latency is the real constraint (~30s for 50 images)

## Constraints Found
- `agent-orchestration.md` caps orchestrator at 3-4 responsibilities — test-pipeline-agent is at 4 (lifecycle, dispatch, gates, aggregation)
- Global retry budget: 15 per pipeline run (from orchestration rules)
- Max 2 nesting levels for agent dispatch — orchestrator → worker agent only

## Key Code References
- Orchestration rules: `.claude/rules/agent-orchestration.md`
- Testing contract: `core/.claude/rules/testing.md` (lines 229-351 for structured output)
- Gate check pattern: `auto-verify` STEP 0 and `post-fix-pipeline` STEP 0
- Visual analysis logic: `verify-screenshots` STEP 2 (lines 36-67)
- Failure categories: `test-failure-analyzer-agent` (17 categories, lines 16-37)
- Pipeline config location: `config/` directory (existing pattern from settings.yml, repos.yml)
