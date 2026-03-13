# Stage 1: Requirements → PRD — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to generate or parse a complete, unambiguous PRD with user stories, acceptance criteria, NFRs, and requirement tiers — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** None (Wave 1)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Socratic requirements elicitation | `brainstorm` (Step 1: 5 probing questions) | ✅ Covered | — |
| 2 | PRD generation (user stories, ACs, NFRs) | `brainstorm` (Step 5 Alt: PRD mode) | ✅ Covered | — |
| 3 | Existing PRD parsing & normalization | Stage 1 prompt handles this | ✅ Covered | — |
| 4 | GitHub Issue → PRD expansion | Stage 1 prompt handles this | ✅ Covered | — |
| 5 | Requirement tiers (Must/Nice/OOS) | `brainstorm` (Step 5.4) | ✅ Covered | **MoSCoW Prioritization** |
| 6 | Testability audit of ACs | Stage 1 prompt (Step 3.1) | ✅ Covered | — |
| 7 | Requirement dependency mapping | Stage 1 prompt (Step 3.3) | ⚠️ Partial — no traceability matrix | **IEEE 830 (SRS)** |
| 8 | IEEE 830 SRS compliance | `brainstorm` PRD mode (Scope, Glossary, Assumptions, External Interfaces) | ✅ Covered | **IEEE 830** |
| 9 | ISO 25010 quality attributes coverage | `brainstorm` PRD mode (all 8 characteristics with targets) | ✅ Covered | **ISO 25010** |
| 10 | Stakeholder identification & RACI | `brainstorm` PRD mode (Stakeholders & RACI table) | ✅ Covered | **RACI Matrix (PMI)** |
| 11 | Risk register with probability × impact | `brainstorm` PRD mode (Risk Register with P×I scoring) | ✅ Covered | **Risk Management (PMI PMBOK)** |
| 12 | Requirement ID traceability to tests | `brainstorm` PRD mode (Requirements Traceability Matrix) | ✅ Covered | **Requirements Traceability Matrix** |
| 13 | Glossary / ubiquitous language | `brainstorm` PRD mode (Glossary section) | ✅ Covered | **DDD (Eric Evans)** |
| 14 | Assumptions & constraints section | `brainstorm` PRD mode (Assumptions & Constraints section) | ✅ Covered | **IEEE 830 §3.6** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **IEEE 830 (SRS)** | Structured SRS with scope, definitions, assumptions, specific requirements | ⚠️ Has user stories + ACs but missing: scope boundaries, definitions/glossary, assumptions/constraints, external interface requirements |
| **ISO 25010** | 8 quality characteristics: Functional Suitability, Performance Efficiency, Compatibility, Usability, Reliability, Security, Maintainability, Portability | ⚠️ Covers 4/8 (Perf, Security, Usability via a11y, Scalability ≈ Performance). Missing: Compatibility, Reliability, Maintainability, Portability |
| **MoSCoW** | Prioritization framework | ✅ Requirement tiers map to Must/Should/Won't |
| **RACI Matrix** | Stakeholder responsibility assignment | ❌ No stakeholder identification at all |
| **PMI Risk Management** | Probability × Impact scoring, mitigation strategies | ❌ Has "Risks" section but no scoring framework |
| **Requirements Traceability Matrix** | Bidirectional trace: requirement → design → test → code | ⚠️ Forward numbering (US→AC) exists but no trace to test IDs or code |
| **DDD Ubiquitous Language** | Shared glossary preventing term ambiguity | ❌ No glossary |

## Gap Proposals

### Gap 1.1: Enhance `brainstorm` skill PRD mode (Priority: P1)

**Problem it solves:** PRD mode produces a solid base but misses IEEE 830 sections (scope, glossary, assumptions, external interfaces), full ISO 25010 coverage (4/8 characteristics missing), risk scoring, stakeholder RACI, and requirements traceability matrix.

**What to add:**
- IEEE 830 sections: Scope, Definitions/Glossary, Assumptions & Constraints, External Interfaces
- Expand NFRs to cover all 8 ISO 25010 characteristics (add Compatibility, Reliability, Maintainability, Portability)
- Risk register template with Probability (1-5) × Impact (1-5) scoring
- Stakeholder section with RACI roles
- Requirements traceability matrix stub (forward-linking AC IDs to future test IDs)

**Existing coverage:** `brainstorm` Step 5 Alt covers user stories, ACs, NFRs (4 types), milestones, requirement tiers.

### Gap 1.2: `prd-parser` skill (Priority: P2)

**Problem it solves:** No dedicated skill for ingesting existing PRDs in various formats (markdown, Notion export, Jira export, Google Docs) and normalizing to the pipeline's standard format with IEEE 830 validation.

**Existing coverage:** Stage 1 prompt has inline logic for parsing existing PRDs, but it's not reusable outside the pipeline.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `docs/plans/<feature>-prd.md` | Stage 2 (Plan), Stage 3 (Scaffold), Stage 5 (Schema), Stage 6 (Pre-Tests) | Markdown with numbered US-xxx, AC-xxx, NFR-xxx, REQ-xxx IDs |
| Requirements traceability matrix | Stage 6 (Pre-Tests), Stage 8 (Post-Tests) | Table mapping REQ → AC → TEST-ID |
| Risk register | Stage 9 (Review), Stage 10 (Deploy) | Table with risk ID, probability, impact, mitigation |

## Research Targets

- **GitHub**: `IEEE 830 PRD template`, `SRS template markdown`, `product requirements AI autonomous`
- **Reddit**: r/ProductManagement — "PRD for AI coding agents", r/ExperiencedDevs — "requirements traceability"
- **Twitter/X**: `PRD template Claude`, `AI requirements engineering`

## Stack Coverage

Universal — PRD format is stack-agnostic. Stack-specific NFRs (e.g., Android battery, API latency) are handled by ISO 25010 expansion.

## Autonomy Verdict

**✅ Can run autonomously.** `brainstorm` PRD mode now covers: IEEE 830 sections (Scope, Glossary, Assumptions, External Interfaces), all 8 ISO 25010 quality characteristics, RACI stakeholder matrix, risk register with P×I scoring, requirements traceability matrix, and DDD glossary. All 14 capabilities now ✅.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `brainstorm` PRD mode enhanced with IEEE 830, ISO 25010, RACI, risk scoring, traceability, glossary — all 7 ❌ items now ✅ |
| 2026-03-13 | P2 gap resolved: `prd-parser` skill created for multi-format PRD normalization with IEEE 830 validation |
