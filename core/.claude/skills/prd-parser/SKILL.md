---
name: prd-parser
description: >
  Parse and normalize existing PRDs from markdown, Notion export,
  Jira export, or Google Docs into the pipeline's standard PRD format with IEEE 830
  validation. Use when importing or converting an existing PRD for downstream pipeline consumption.
triggers:
  - parse prd
  - normalize prd
  - import prd
  - convert prd
  - validate prd
  - prd parser
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<path to PRD file or directory>"
version: "1.0.0"
type: workflow
---

# PRD Parser — Normalize & Validate Existing PRDs

Parse an existing PRD from any common format, normalize it to the standard PRD
structure, validate against IEEE 830, and produce a gap report.

**Input:** $ARGUMENTS

---

## STEP 1: Detect Format

Read the input file(s) at the provided path and classify the source format.

| Format | Detection Signals |
|--------|-------------------|
| **Plain Markdown** | `.md` extension, standard heading structure |
| **Notion Export** | Notion metadata comments, UUID-style filenames, nested toggle blocks, callout blocks |
| **Jira Export (CSV)** | `.csv` extension, columns like `Summary`, `Description`, `Story Points`, `Issue Type` |
| **Jira Export (JSON)** | `.json` extension, `fields.summary`, `fields.description`, `fields.issuetype` |
| **Google Docs (exported MD)** | Google-style heading IDs, `[image]` placeholders, flat heading hierarchy |
| **Custom / Unknown** | None of the above — fall back to heading-based section extraction |

Report the detected format before proceeding:

```
Format Detection:
  Source: <file path>
  Detected format: <format name>
  Confidence: High / Medium / Low
  Signals: <what triggered detection>
```

If confidence is Low, ask the user to confirm the format before continuing.

---

## STEP 2: Parse Sections

Extract content into a normalized intermediate representation. Map source-specific
structures to canonical section names.

### 2.1 Section Mapping

Map whatever headings or structures exist to canonical PRD sections:

| Canonical Section | Common Variants |
|-------------------|-----------------|
| Meta | Header, Document Info, Properties, Metadata |
| Scope | Project Scope, Boundaries, In/Out of Scope |
| Glossary | Definitions, Terms, Terminology, Ubiquitous Language |
| Stakeholders | RACI, Roles, Team, Owners |
| Overview | Summary, Executive Summary, Introduction, Background |
| Problem Statement | Problem, Motivation, Context, Why |
| Assumptions & Constraints | Assumptions, Limitations, Dependencies, Prerequisites |
| User Stories | Stories, Requirements, Use Cases, Jobs to Be Done, Features |
| Acceptance Criteria | ACs, Definition of Done, Scenarios, Given-When-Then |
| Non-Functional Requirements | NFRs, Quality Attributes, SLAs, Performance Requirements |
| External Interfaces | Integrations, APIs, System Interfaces, UI Specs |
| Risk Register | Risks, Risk Assessment, Threats, Mitigations |
| Traceability Matrix | Requirements Matrix, Mapping, Coverage |
| Requirement Tiers | MoSCoW, Priority, Must/Should/Could/Won't, P0/P1/P2 |
| Milestones | Timeline, Roadmap, Phases, Schedule |
| Success Metrics | KPIs, OKRs, Success Criteria, Measures of Success |
| Open Questions | TBDs, Unknowns, Decisions Needed, Parking Lot |

### 2.2 Jira-Specific Parsing

For Jira CSV/JSON exports:
1. Group issues by `Epic Link` or `Parent` to form user story clusters
2. Map `Issue Type = Story` to User Stories, `Issue Type = Bug` to constraints
3. Extract `Acceptance Criteria` from description field (look for Given/When/Then or checkbox patterns)
4. Map `Priority` (Highest/High/Medium/Low/Lowest) to MoSCoW tiers
5. Extract `Fix Version` to Milestones

### 2.3 Notion-Specific Parsing

For Notion exports:
1. Expand toggle blocks — content inside toggles is often requirements detail
2. Parse database tables as structured data (user stories, risks)
3. Convert callout blocks to notes/warnings in the output
4. Handle nested page links by reading referenced files if available

### 2.4 Unmapped Content

Any content that does not map to a canonical section:
- Collect under an `## Unmapped Content` appendix in the output
- Tag each block with its original heading or location
- Flag for user review in the gap report

---

## STEP 3: Normalize to Standard PRD Format

Transform the parsed sections into the standard PRD format matching the brainstorm
skill's PRD output (IEEE 830 aligned). Apply these normalization rules:

### 3.1 ID Assignment

Assign IDs where the source lacks them:
- User Stories: `US-001`, `US-002`, ...
- Acceptance Criteria: `AC-001 (US-001)`, `AC-002 (US-001)`, ...
- NFRs: `NFR-001`, `NFR-002`, ...
- Risks: `RISK-001`, `RISK-002`, ...
- Requirements: `REQ-M001` (Must), `REQ-S001` (Should), `REQ-C001` (Could), `REQ-W001` (Won't)

If the source already has IDs, preserve them and note the original-to-normalized
ID mapping in the output.

### 3.2 User Story Normalization

Convert requirements to standard user story format:
- **Input:** "Users should be able to reset their password"
- **Output:** `US-00N: As a user, I want to reset my password, so that I can regain access to my account`

If the source already uses "As a..., I want..., so that..." format, preserve it.
If the benefit clause ("so that") is missing, add `[NEEDS BENEFIT CLAUSE]` as a
placeholder and flag in the gap report.

### 3.3 Acceptance Criteria Normalization

Convert to Given/When/Then format where possible:
- **Input:** "Password must be at least 8 characters"
- **Output:** `AC-00N (US-00N): Given a user is on the reset password form, when they enter a password shorter than 8 characters, then the system displays a validation error`

If conversion to Given/When/Then would lose precision, keep the original phrasing
and note it.

### 3.4 NFR Normalization

Map NFRs to ISO 25010 quality characteristics. If the source uses different
categories, reclassify:

| ISO 25010 Characteristic | Common Source Labels |
|--------------------------|---------------------|
| Functional Suitability | Completeness, Correctness, Feature Coverage |
| Performance Efficiency | Speed, Latency, Throughput, Load, Response Time |
| Compatibility | Integration, Interoperability, Coexistence |
| Usability | UX, Accessibility, Learnability, WCAG |
| Reliability | Uptime, Availability, Fault Tolerance, SLA |
| Security | Auth, Encryption, Privacy, OWASP, Compliance |
| Maintainability | Code Quality, Test Coverage, Modularity, Tech Debt |
| Portability | Cross-platform, Migration, Deployment Environments |

### 3.5 MoSCoW Classification

If the source uses a different prioritization scheme, map to MoSCoW:

| Source Scheme | Must Have | Should Have | Could Have | Won't Have |
|---------------|-----------|-------------|------------|------------|
| P0/P1/P2/P3 | P0 | P1 | P2 | P3 |
| High/Med/Low | High | Medium | Low | — |
| Critical/Major/Minor | Critical | Major | Minor | — |
| Jira Priority | Highest+High | Medium | Low | Lowest |
| T-shirt (S/M/L/XL) | — (by effort, not priority) | Flag for manual classification | | |

If no priority information exists, place all requirements as `[NEEDS TRIAGE]`
under Must Have and flag in the gap report.

---

## STEP 4: IEEE 830 Validation

Run a completeness check against the IEEE 830 standard. Every item below MUST
be present and non-empty in the normalized PRD. Score each as Present, Partial,
or Missing.

### Validation Checklist

| # | Section | Status | Notes |
|---|---------|--------|-------|
| 1 | **Scope** — system boundaries, inclusions, exclusions | | |
| 2 | **Glossary** — domain terms with precise definitions | | |
| 3 | **Assumptions & Constraints** — stated assumptions, technical/business constraints, dependencies | | |
| 4 | **External Interfaces** — UI, system, hardware, communication interfaces | | |
| 5 | **User Stories with IDs** — numbered, role-action-benefit format | | |
| 6 | **Acceptance Criteria** — testable, linked to user stories | | |
| 7 | **Non-Functional Requirements** — all 8 ISO 25010 characteristics addressed | | |
| 8 | **Risk Register** — identified risks with probability, impact, mitigation | | |
| 9 | **Traceability Matrix** — requirements linked to stories, ACs, and tests | | |
| 10 | **MoSCoW Tiers** — all requirements classified as Must/Should/Could/Won't | | |

### Scoring

- **Complete:** 8-10 sections Present
- **Adequate:** 5-7 sections Present (remainder Partial or Missing)
- **Incomplete:** < 5 sections Present

---

## STEP 5: Gap Report

Produce a structured gap report summarizing what is missing or weak.

```
IEEE 830 Gap Report
═══════════════════
Source: <original file path>
Format: <detected format>
Score: <Complete / Adequate / Incomplete> (<N>/10 sections present)

Missing Sections:
  - <section name>: <what is needed>

Partial Sections:
  - <section name>: <what exists> → <what is missing>

Normalization Flags:
  - <N> user stories missing benefit clause [NEEDS BENEFIT CLAUSE]
  - <N> acceptance criteria not in Given/When/Then format
  - <N> requirements missing priority [NEEDS TRIAGE]
  - <N> NFRs missing measurable targets
  - <N> risks missing mitigation strategy

Unmapped Content:
  - <N> blocks from original document did not map to standard sections

Recommended Actions:
  1. <highest priority gap to fill>
  2. <next priority>
  3. ...
```

Present the gap report to the user and wait for acknowledgment before writing
the output file.

---

## STEP 6: Output Normalized PRD

Write the normalized PRD using the exact structure from the brainstorm skill's
PRD format (Meta, Scope, Glossary, Stakeholders & RACI, Overview, Problem
Statement, Assumptions & Constraints, User Stories, Acceptance Criteria,
Non-Functional Requirements, External Interfaces, Risk Register, Requirements
Traceability Matrix, Requirement Tiers, Milestones, Success Metrics, Open
Questions).

- Preserve all original content that mapped successfully
- Insert `<!-- GAP: ... -->` HTML comments where sections are Missing or Partial,
  describing what the author needs to fill in
- Include the ID mapping table if original IDs were remapped
- Append the gap report as a final section: `## Appendix: IEEE 830 Gap Report`

Save to the location the user specifies. If no preference, suggest
`docs/specs/{feature-name}-prd-normalized.md`.

### Handoff

After writing the normalized PRD, suggest next steps:

- **Fill gaps** — Work through `<!-- GAP: ... -->` comments to complete missing sections
- **`/brainstorm`** — If the PRD is too thin, use brainstorm to regenerate from scratch using the parsed content as input
- **`/writing-plans`** — Break the PRD into implementation tasks
- **`/plan-to-issues`** — Convert the PRD into tracked GitHub Issues
- **`/adversarial-review`** — Review the PRD for risks and blind spots before implementation

---

## MUST DO

- Always detect and confirm format before parsing (Step 1)
- Always preserve original content — normalization adds structure, never removes information
- Always assign IDs to all user stories, ACs, NFRs, risks, and requirements
- Always run the full IEEE 830 validation checklist (Step 4) — do not skip items
- Always produce the gap report (Step 5) before writing the output file
- Always include `<!-- GAP: ... -->` markers for missing or partial sections
- Always show the user the gap report and wait for acknowledgment before writing output

## MUST NOT DO

- MUST NOT discard or summarize away original content — if it does not map, put it in Unmapped Content
- MUST NOT fabricate requirements, user stories, or acceptance criteria that are not in the source — flag gaps instead
- MUST NOT skip IEEE 830 validation even if the PRD looks complete
- MUST NOT write the output file without showing the gap report first
- MUST NOT modify the source file — always write to a new output path
- MUST NOT duplicate the brainstorm skill's job — this skill normalizes existing PRDs, it does not generate new ones from scratch
