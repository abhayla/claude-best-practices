# Scope: global

# Learning → Gate, not Prose (root-cause doctrine)

version: "1.0.0"

Every learning from a failure MUST end as a MACHINE-ENFORCED GATE where one is possible — a prose
lesson or a "MUST" rule is a PATCH that rots under context pressure (evidence: 440+ enhance-card
misses despite a written rule). This operationalizes `rule-writing-meta.md` ("zero-exception
behaviour needs a HOOK, not prose") across ALL fleet/workflow learnings.

## The pipeline (run on EVERY failure/correction)
1. **5-whys to the CLASS, not the instance.** (T-013 class = "dispatched an unresolved material
   assumption", not "scraped the wrong site".)
2. **Can a deterministic gate catch this class?**
   - YES → BUILD THE GATE (preflight script / hook / test / schema field). The gate IS the fix;
     the lesson file only documents it. It must have a self-test proving it blocks the failure
     shape and passes the correct shape.
   - NO (pure judgment) → write the rule AND a telemetry counter; the counter AUTO-ESCALATES the
     class to a gate on its 2nd recurrence.
3. **Recurrence ratchet:** any lesson-class that fires ≥2× is proof prose failed → it converts to a
   gate. Lessons never remain prose-only once recurring.

## CRITICAL RULES
- MUST convert a learning to a machine gate whenever a deterministic check can catch the class;
  a prose-only fix for a gateable class is itself a defect.
- MUST give every gate a self-test (blocks-the-bad-shape + passes-the-good-shape) at build time.
- MUST escalate any lesson-class to a gate on its 2nd occurrence (recurrence ratchet).
- MUST root-cause to the CLASS; never patch only the specific instance.
