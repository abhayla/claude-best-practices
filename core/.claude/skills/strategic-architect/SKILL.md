---
name: strategic-architect
description: >
  Diagnose project health and create strategic plans by identifying bottlenecks,
  assessing architecture fitness, and building improvement roadmaps. Use when the
  team needs a structured assessment, project health check, or strategic planning.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: diagnose|check-in|reassess> [context]"
version: "1.0.1"
type: workflow
---

# Strategic Architect — Project Diagnostics & Planning

Structured project assessment with constraint identification and action planning.

**Mode:** $ARGUMENTS

---

## Modes

| Mode | Trigger | Description |
|------|---------|-------------|
| `diagnose` | Full assessment | 5-round diagnostic with questions → constraint identification → action plan |
| `check-in` | Progress review | Review progress against previous plan, adjust priorities |
| `reassess` | Re-evaluate | Full re-evaluation when circumstances have changed |

---

## STEP 1: Diagnose Mode

### Round 1: Project Context (4 questions)
1. What is the project's primary goal and who are its users?
2. What's the current state — what works and what doesn't?
3. What's the team structure and available resources?
4. What's the timeline and key milestones?

### Round 2: Technical Health (4 questions)
5. What's the architecture and tech stack?
6. What's the testing situation — coverage, confidence, speed?
7. What's the deployment process like?
8. Where is technical debt concentrated?

### Round 3: Delivery & Process (4 questions)
9. How are tasks prioritized and tracked?
10. What's the typical cycle time from idea to production?
11. Where do things get stuck or delayed?
12. How is quality maintained (reviews, CI, monitoring)?

### Round 4: Team & Culture (4 questions)
13. What's the team's biggest strength?
14. What knowledge is siloed or at risk?
15. How are decisions made when there's disagreement?
16. What's morale like and what affects it?

### Round 5: Constraints & Priorities (4 questions)
17. If you could fix ONE thing, what would it be?
18. What's been tried before that didn't work?
19. What's the biggest risk to the project?
20. What would success look like in 90 days?

---

## STEP 2: Constraint Identification

After gathering answers, identify the primary constraint(s):

| Constraint | Symptoms |
|------------|----------|
| C1: Wrong Architecture | Constant rework, features take too long, scaling issues |
| C2: Inconsistent Delivery | Missed deadlines, scope creep, unclear priorities |
| C3: Quality Problems | Frequent bugs, low test confidence, production incidents |
| C4: Knowledge Silos | Bus factor = 1, slow onboarding, tribal knowledge |
| C5: Process Friction | Too much ceremony, slow reviews, blocked PRs |
| C6: Technical Debt | Growing backlog, fear of changing code, workaround accumulation |

---

## STEP 3: Strategic Report

Deliver a structured report with:

1. **Executive Summary** — Primary constraint and recommended focus
2. **Current State Assessment** — Strengths and weaknesses
3. **Constraint Analysis** — Ranked constraints with evidence
4. **Quick Wins** — Actions that can improve things in 1-2 weeks
5. **30-Day Plan** — Specific goals and actions for the first month
6. **90-Day Roadmap** — Quarterly milestones and success criteria
7. **Risks & Mitigations** — What could go wrong and how to handle it
8. **Metrics to Track** — How to measure progress
9. **Review Schedule** — When to check in and reassess

Save the report to `plans/strategic-assessment-{date}.md`.

---

## STEP 4: Check-In Mode

1. Read previous assessment from `plans/`
2. Compare current state against 30-day plan
3. Report: on-track, behind, or ahead for each goal
4. Adjust priorities if needed
5. Identify new blockers or risks

## STEP 5: Reassess Mode

Run a fresh diagnostic with emphasis on what changed since last assessment.
