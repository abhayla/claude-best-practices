# PHASE 11: Anti-Patterns

### 11.1 Response Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **Hero debugging** | One person debugs alone while others wait | IC coordinates parallel investigation streams |
| **Blame culture** | People hide mistakes or avoid reporting incidents | Blameless post-mortems, celebrate early detection |
| **No IC assigned** | Chaotic response with no coordination | Always assign an IC, even for SEV3 |
| **Skipping severity assessment** | Under-response to serious incidents | Classify severity first, respond accordingly |
| **Fixing forward under pressure** | Deploying untested fixes during an active incident | Rollback first, fix forward after stabilization |
| **Silent investigation** | Debugging without updating the incident channel | Post findings every 15 min (SEV1) or 30 min (SEV2) |
| **Premature all-clear** | Declaring resolution before verifying stability | Monitor for at least 15 min after mitigation before resolving |

### 11.2 Post-Mortem Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **No post-mortem** | Same incidents repeat because root causes are not addressed | Mandatory post-mortem for all SEV1-SEV2 incidents |
| **Blame-oriented post-mortem** | People become defensive, hide information | Blameless analysis focused on systemic improvements |
| **Vague action items** | "Improve monitoring" — never gets done | Specific, measurable actions with owners and due dates |
| **No follow-up on action items** | Post-mortem is written but nothing changes | 2-week review meeting to track action item progress |
| **Delayed post-mortem** | Details are forgotten, less accurate analysis | Complete within 5 business days of resolution |

### 11.3 Organizational Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|-------------|---------|-----------------|
| **No runbooks** | Every incident starts from scratch | Maintain runbooks for known failure modes, update after each incident |
| **Tribal knowledge** | Only one person knows how to fix the system | Document procedures, cross-train team members |
| **Alert fatigue** | Too many low-priority alerts, real alerts get ignored | Tune alerting thresholds, eliminate noisy alerts |
| **No on-call handoff** | Context lost between shifts | Structured handoff document and verbal briefing |
| **Ignoring near-misses** | Only react to full outages, miss preventive opportunities | Track and analyze near-misses with the same rigor as incidents |

---

