# Scope: global

# Product Incubation & Graduation (hub-as-factory operating model)

version: "1.0.0"

When the hub BUILDS A PRODUCT (an app/tool the machine ships — NOT factory R&D like a new
pattern/skill/agent/rule/workflow or the machine infra), the product code MUST NOT live in
the hub's git tree. It belongs in an ISOLATED SIBLING folder (`../<product>/`, its own
`.git`, outside the hub so its `git status`/CI/secret-scan never see it) — in-tree product
code breaks the two-`.claude/` boundary, trips hub CI/secret-scan (whole-tree scans),
pollutes the flywheel + trust-score telemetry, and makes graduation a painful history extraction.

- **INCUBATE** as a sibling, provision via `recommend.py --local ../<product> --provision`, operate from the hub session while small.
- **GRADUATE** to its own repo once it outgrows incubation — ANY of: >~500 LOC / >~15 files, needs own CI/deploy/secrets, a 2nd contributor, a first real user, or >7 days active — then `git init` + remote + `/bootstrap-dogfood-project ../<product>`. Surface the move the moment a trigger trips, while it is still cheap.
- When unsure product-vs-R&D, ask: "does this ship as a hub pattern, or its own deployable artifact?" Pattern → in-hub; artifact → sibling. (Serves Goals 1 & 4 + the autonomy north-star; composes with `goal-anchored-decisions.md`, `rule-curation.md`.)

## CRITICAL RULES

- MUST keep product code OUTSIDE the hub git tree (sibling folder, own `.git`); MUST NOT add a product's files to the hub repo.
- MUST graduate an incubated product to its own repo once any trigger fires — never defer into a hub monorepo.
- MUST classify product vs factory-R&D before placing code; only hub patterns / machine infra belong in the hub.
