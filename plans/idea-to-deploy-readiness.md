# Plan — Idea → Production-Deployed Readiness (Goal #3)

**Status:** active · **Created:** 2026-06-17 · **Owner:** Abhay
**Anchors:** README goal #3 (idea → production-deployed, role-per-stage) ·
`engineering-roles.md` · `decision-authority.md` · audit 2026-06-17 (4 parallel stage agents)

## Why

README goal #3 commits the hub to taking an idea all the way to a **deployed** app, with
the right role owning each stage. A 2026-06-17 audit found the build→test→verify core is
production-grade, but **three gaps break the full chain**. This plan closes them generically
in `core/` so any downstream project inherits the capability.

## Decisions (locked 2026-06-17)

- **Operating model (dogfood loop):** Claude conceives its OWN app idea and drives it
  idea→production-deployed THROUGH this pipeline. Every gap hit during the real build is closed
  in the hub *then*, justified by a concrete caller (no speculative YAGNI), and the app keeps
  moving. Build the app and upgrade the hub interleaved — the app is the forcing function, the
  hub upgrades are the durable output. (Abhay's reframing, 2026-06-17.)
- **Deploy target:** Hostinger **VPS** — executor is SSH + Docker (portable, not MCP-session-bound).
- **Scope:** hub upgrades land generically in `core/.claude/`; the app lives in its own repo/dir.
  The app exists to *exercise and prove* the chain, not as the deliverable — the hardened hub is.
- **Domain BA:** a generic BA becomes domain-deep by **researching the domain at runtime**
  (wire existing research primitives into the requirements stage) — NOT by pre-shipping N
  static per-domain modules (that stays YAGNI-rejected). This is Abhay's reframing.
- **Human-in-the-loop:** explicit user-approval pauses are REQUIRED at (a) UI mockup before
  build and (b) before production deploy; plus a feature sign-off after verification.

## Units (sequence)

### Unit 1 — Human-approval gates (SSOT spine) · low risk · DO FIRST
- **New rule** `core/.claude/rules/human-approval-gates.md` (`# Scope: global`): defines the
  mandatory human checkpoints in the idea→deploy pipeline — UI/design-mockup approval before
  implementation, feature acceptance after verification, production-deploy approval (the last
  one points to `decision-authority.md`, which already gates deploy — no duplication).
- Registry: add entry + bump `_meta.total_patterns` + `last_updated`; run
  `pytest scripts/tests/` (esp. `test_registry_integrity.py`), the 2 validators, `generate_docs.py`.
- Verification: validators green + full pytest green.

### Unit 2 — Domain-research BA step · medium risk
- Enhance `core/.claude/skills/brainstorm` requirements stage + the Product Manager role
  routing in `engineering-roles.md` to dispatch domain research (`/research-mode`,
  `/deep-research`, `web-research-specialist-agent`, `/grill-with-docs`) BEFORE asking
  clarification, then write domain-specific acceptance criteria.
- Verification: a brainstorm run on a regulated-domain idea surfaces domain-specific questions
  + ACs that a generic run would miss.

### Unit 3 — VPS deploy-executor · high risk · BUILD DURING FIRST REAL APP
- **New skill** `core/.claude/skills/vps-deploy` (`type: workflow`): SSH + `docker compose`
  deploy to a Hostinger VPS, env/secret injection at deploy time, post-deploy smoke against
  the live URL, rollback on smoke-fail; wire into the DevOps/Release role.
- Deferred deliberately: building a VPS deployer before the real app's stack + live server is
  speculative. Needs Abhay's host + credentials at deploy time (escalate then).
- Verification: deploy a throwaway container to the VPS, confirm live-URL smoke + rollback.

### Unit 4 — Pipeline integration · medium risk
- Wire Units 1–3 into `project-manager-agent` + `config/pipeline-stages.yaml`: insert the
  approval-gate pauses, the domain-research step, and the deploy-executor stage; update
  `docs/stages/STAGE-4-HTML-DEMO.md` (remove "runs autonomously" where a gate now pauses) and
  STAGE-10-DEPLOY.
- Verification: smoke-test the pipeline DAG; `test_workflow_closure_consistency.py` green.

## Done = README goal #3 is truthfully met: an idea runs idea→clarify(domain-deep)→UI+approve
→build→test→verify→sign-off→deploy-to-VPS, with the right role at each stage.
