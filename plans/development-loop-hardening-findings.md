# Findings: development-loop hardening (downstream-foolproofing)

Created: 2026-06-15

## Discoveries (analysis of `development-loop` SKILL + contract + orchestration rule)

1. **Registry dependency closure is WRONG** (`registry/patterns.json` → `development-loop.dependencies`):
   - Lists `development-loop-master-agent` — DEPRECATED; the skill body (lines 31, 253) forbids dispatching it.
   - Lists `executing-plans` — not invoked by the skill body.
   - OMITS `plan-executor-agent` and `planner-researcher-agent` — the two agents the skill ACTUALLY dispatches via `Agent()` (SKILL lines 101, 141).
   - Impact: any provisioning that trusts this field co-provisions the wrong/deprecated closure and misses the real workers → EXECUTE fails downstream with "Agent type not found".

2. **No preflight in the skill.** STEP 4 dispatches `plan-executor-agent` blind. `/test-pipeline` documents the correct pattern (pattern-structure.md "registry session-pinning"): probe the runtime registry early and BLOCK with `WORKER_REGISTRY_NOT_LOADED` if a required agent is missing. `development-loop` has no such STEP 0/1 probe → silent inline failure or hard crash mid-run.

3. **Portability: `src/` assumption** in `config/workflow-contracts.yaml` → `development-loop.steps[execute].artifacts_out.source.path: "src/"`. Violates pattern-portability ("MUST NOT assume project-specific directory structures"). Real stacks: Android `app/src/main`, FastAPI `backend/`, Flutter `lib/`, Go module root. Needs to be project-detected or non-binding/descriptive.

4. **Provisioning closure mechanism — UNVERIFIED.** `recommend.py` matched "dependency" in grep; must confirm whether it co-provisions a skill's full closure (agents + sub-skills) and from WHICH source (the stale registry field vs. live scan). This determines whether fixing #1 is sufficient.

5. **Runtime-artifact dirs.** Skill writes `.workflows/development-loop/`, `test-results/`, `test-evidence/`. These are ephemeral; provisioning should ensure they're `.gitignore`d downstream (testing.md already mandates gitignoring test-results/ + test-evidence/).

## Constraints Found
- Single-level dispatch (agent-orchestration.md): development-loop MUST run at T0; workers cannot re-dispatch. Testing it end-to-end means running it from T0 (this session), which is valid.
- post-fix-pipeline COMMIT requires the sandbox to be a git repo.
- auto-verify genericity is load-bearing: development-loop's cross-stack usability is capped by auto-verify's test-command detection.

## Key Code References
- `core/.claude/skills/development-loop/SKILL.md` — orchestrator body (STEP 0–7)
- `config/workflow-contracts.yaml` → `workflows.development-loop` — step DAG + artifact contracts
- `core/.claude/rules/agent-orchestration.md` — single-level dispatch, registry session-pinning
- `core/.claude/rules/pattern-structure.md` — "registry session-pinning" preflight pattern
- `core/.claude/agents/plan-executor-agent.md`, `planner-researcher-agent.md` — the real workers
- `scripts/recommend.py`, `scripts/bootstrap.py` — provisioning entry points
