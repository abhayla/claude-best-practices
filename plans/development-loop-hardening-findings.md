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

4. **Provisioning closure mechanism — RESOLVED (2026-06-15): there is NONE.** `recommend.py --provision` (which `/synthesize-project` STEP 1 delegates to entirely) selects patterns by TIER (must-have/nice-to-have via stack matching in `assign_tier`, recommend.py:754+), then copies files (`_resolve_resource_files`/`_copy_if_changed`). It NEVER reads a pattern's registry `dependencies` field — the only "dependencies" logic (recommend.py:141/169/223) is PROJECT-dependency detection (package.json/pyproject → stack promotion). `bootstrap.py` has no closure logic either.
   - Consequence: fixing #1 is necessary (correctness) but NOT sufficient — nothing consumes the field at provision time.
   - The closure likely travels INCIDENTALLY because workflow skills + their worker agents are universal (unprefixed) → classified must-have. To be VERIFIED empirically in the sandbox: provision via /synthesize-project and check whether `plan-executor-agent`, `planner-researcher-agent`, brainstorm, auto-verify, post-fix-pipeline all land.
   - Therefore the PREFLIGHT BLOCK (Finding #2 fix) is the load-bearing safety net regardless of provisioning. Building a real closure-resolver in recommend.py is deferred unless the sandbox proves the incidental closure fails (YAGNI).

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
