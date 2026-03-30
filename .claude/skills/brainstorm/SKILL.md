---
name: brainstorm
description: >
  Explore intent through Socratic questioning, propose approaches with trade-offs,
  and produce a spec document. Use before building anything non-trivial to clarify
  requirements and evaluate alternatives.
triggers:
  - brainstorm
  - explore ideas
  - design
  - spec
  - requirements
  - trade-offs
  - approaches
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<feature or problem description>"
version: "1.0.0"
type: workflow
---

# Brainstorm — Socratic Exploration & Spec Writing

Structured exploration of a problem space before committing to implementation.

**Topic:** $ARGUMENTS

---

## STEP 1: Understand Intent

Ask 3-5 probing questions before proposing anything. Do NOT skip this step even if the request seems simple.

1. **Who is the user?** Who will use this feature and in what context?
2. **What problem does this solve?** What is painful or missing today?
3. **What does success look like?** How will we know this works?
4. **What are the constraints?** Time budget, tech stack limitations, scope boundaries?
5. **What is out of scope?** What should this explicitly NOT do?

Wait for answers before proceeding. If the user says "just build it," push back once — misunderstood requirements cost more than five questions.

---

## STEP 2: Deep Research

Conduct thorough research before proposing anything. Delegate to subagents for breadth.

### 2.1 Internal Codebase Research
1. Identify existing patterns, modules, and conventions relevant to the request
2. Find related code that this feature must integrate with or extend
3. Surface edge cases, potential conflicts, and architectural constraints
4. Note any prior attempts or partial implementations

### 2.2 External Research (when applicable)
5. **Similar implementations** — Search for how other projects solve this problem. Use `WebSearch` to find open-source implementations, blog posts, or Stack Overflow discussions with concrete patterns.
6. **Documentation & standards** — Review official documentation for relevant libraries, APIs, or protocols. Check for best practices, known pitfalls, and recommended patterns.
7. **Design patterns** — Identify applicable design patterns (e.g., event sourcing, CQRS, circuit breaker, saga). Reference pattern names so the team has shared vocabulary.
8. **Known failure modes** — Research common mistakes when implementing this type of feature. What do post-mortems say? What do "things I wish I knew" articles highlight?

### 2.3 Research Brief
Summarize findings in a structured brief before moving to approaches:

```
Research Brief:
- Internal: <what exists, what we can reuse, what constrains us>
- External: <how others solve this, recommended patterns>
- Risks: <known failure modes, common mistakes>
- Open questions: <what we still don't know>
```

---

## STEP 3: Propose Approaches

Present 2-3 distinct approaches. For each, include a one-paragraph description and the trade-offs table:

| Criteria | Approach A | Approach B | Approach C |
|----------|-----------|-----------|-----------|
| Complexity | | | |
| Maintainability | | | |
| Performance | | | |
| Time to implement | | | |
| Risk | | | |

**Recommend one approach** with clear reasoning. Explain why the others are worse for this specific situation, not in general.

Wait for user approval before proceeding. If the user picks a different approach, switch without resistance.

---

## STEP 4: Design in Sections

Break the chosen approach into logical sections. Present each section one at a time for incremental review:

- **Data model changes** — New or modified schemas, types, or structures
- **API / interface changes** — New endpoints, function signatures, or contracts
- **UI changes** — Screens, components, or user-facing behavior (if applicable)
- **Migration needs** — Data migrations, feature flags, backward compatibility
- **Integration points** — How this connects to existing systems

Do NOT present everything at once. Walk through section by section, waiting for feedback on each before moving to the next.

---

## STEP 5: Write Spec Document

Produce a concise spec containing:

1. **Problem statement** — What we are solving and why
2. **Chosen approach** — Which approach was selected and the reasoning
3. **Design sections** — Details from Step 4, refined with feedback
4. **Requirement tiers** — Classify every requirement:
   - **Must** — Non-negotiable for the feature to ship
   - **Nice** — Valuable but deferrable to a follow-up
   - **Out of Scope** — Explicitly excluded to prevent scope creep
5. **Open questions** — Anything still unresolved
6. **Success criteria** — Measurable outcomes that prove this works

Save the spec to a location the user specifies. If no preference, suggest `docs/specs/{feature-name}-spec.md`.

The spec is a living document — update it as understanding evolves during implementation.

### Step 5 Alternative: PRD (Product Requirements Document)

If the user needs formal requirements (for team handoff, stakeholder review, or project tracking), produce a PRD instead of a spec. Ask: "Do you need a spec (technical) or PRD (product-facing)?"

PRD format (IEEE 830 aligned):

```markdown
# PRD: <Feature Name>

## Meta
- Author: <name or "Claude Code">
- Date: <ISO-8601>
- Status: DRAFT | REVIEW | APPROVED
- Version: 1.0

## Scope
<What is included AND what is explicitly excluded. Define system boundaries.>

## Glossary
Define domain-specific terms to prevent ambiguity (DDD ubiquitous language):
| Term | Definition |
|------|-----------|
| <term> | <precise definition used throughout this PRD> |

## Stakeholders & RACI
| Role | Person/Team | R(esponsible) | A(ccountable) | C(onsulted) | I(nformed) |
|------|------------|:---:|:---:|:---:|:---:|
| Product Owner | <name> | | A | | |
| Engineering | <team> | R | | | |
| Design | <team> | | | C | |
| QA | <team> | R | | | |

## Overview
<1-paragraph summary of what we're building and why>

## Problem Statement
<What problem exists? What happens without this feature? Who is affected?>

## Assumptions & Constraints
- **Assumptions:** <what we believe to be true but haven't verified>
- **Constraints:** <technical, business, regulatory limitations>
- **Dependencies:** <external systems, teams, or timelines we depend on>

## User Stories
- US-001: As a <role>, I want to <action>, so that <benefit>
- US-002: As a <role>, I want to <action>, so that <benefit>
(Number every story for traceability)

## Acceptance Criteria
For each user story (every criterion MUST be testable — specific, measurable, automatable):
- AC-001 (US-001): Given <precondition>, when <action>, then <expected result>
- AC-002 (US-001): Given <precondition>, when <action>, then <expected result>

## Non-Functional Requirements (ISO 25010)
All 8 quality characteristics — provide specific measurable targets:

| ID | Characteristic | Requirement | Target |
|----|---------------|-------------|--------|
| NFR-001 | **Functional Suitability** | <completeness, correctness, appropriateness> | <metric> |
| NFR-002 | **Performance Efficiency** | Response time, throughput, resource utilization | p95 < Xms, Xrps |
| NFR-003 | **Compatibility** | Co-existence with other systems, interoperability | <specific systems> |
| NFR-004 | **Usability** | Learnability, operability, error protection, accessibility | WCAG 2.1 AA |
| NFR-005 | **Reliability** | Maturity, availability, fault tolerance, recoverability | X% uptime, RTO Xm |
| NFR-006 | **Security** | Confidentiality, integrity, non-repudiation, accountability | <auth method, encryption> |
| NFR-007 | **Maintainability** | Modularity, reusability, analysability, modifiability, testability | <coverage %, complexity> |
| NFR-008 | **Portability** | Adaptability, installability, replaceability | <platforms, environments> |

## External Interfaces
- **User Interfaces:** <screens, CLI commands, API consumers>
- **System Interfaces:** <external APIs, databases, message queues>
- **Hardware Interfaces:** <if applicable>
- **Communication Interfaces:** <protocols, data formats>

## Risk Register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|----|------|:-:|:-:|:-:|-----------|
| RISK-001 | <description> | 3 | 4 | 12 | <mitigation strategy> |
| RISK-002 | <description> | 2 | 5 | 10 | <mitigation strategy> |

## Requirements Traceability Matrix
| Requirement | User Story | Acceptance Criteria | Test ID (TBD) | Status |
|------------|-----------|-------------------|--------------|--------|
| REQ-M001 | US-001 | AC-001, AC-002 | — | Draft |
| REQ-M002 | US-002 | AC-003 | — | Draft |

## Requirement Tiers (MoSCoW)
### Must Have (MVP)
- REQ-M001: <requirement> [US-001, AC-001]
### Should Have (v1.1)
- REQ-S001: <requirement> [US-003]
### Could Have (future)
- REQ-C001: <requirement>
### Won't Have (out of scope)
- REQ-W001: <what and why excluded>

## Milestones
| ID | Milestone | Scope | Requirements | Target |
|----|-----------|-------|-------------|--------|
| M1 | MVP | <core stories> | REQ-M001..M005 | <date> |
| M2 | Enhancement | <additional> | REQ-S001..S003 | <date> |

## Success Metrics
- <measurable outcome 1>
- <measurable outcome 2>

## Open Questions
- <anything unresolved — must be empty before PRD is APPROVED>
```

Save the PRD to `docs/specs/{feature-name}-prd.md`.

---

## STEP 6: Handoff

Summarize the spec/PRD in 3-5 bullet points and suggest the appropriate next step:

- **`/writing-plans`** — For features that need detailed task breakdown before implementation
- **`/implement`** — For well-scoped features ready to build directly
- **`/plan-to-issues`** — For PRDs that need to be tracked as GitHub Issues with epics
- **`/adversarial-review`** — For high-risk features that need plan review before execution

---

## MUST DO

- Always complete Step 1 questioning, even for "obvious" requests
- Always present trade-offs across multiple approaches, not just the "best" option
- Always wait for user approval between Steps 3, 4, and 5
- Always ground proposals in actual codebase research (Step 2)
- Update the spec document when new information surfaces

## MUST NOT DO

- MUST NOT skip questioning and jump straight to solutions
- MUST NOT present a single approach as the only option — always offer alternatives
- MUST NOT dump the entire design at once — present section by section
- MUST NOT treat the spec as final — it evolves with the conversation
- MUST NOT begin implementation during this skill — brainstorm produces a spec, not code
