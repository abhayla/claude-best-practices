# References

### 8.2 Quality Checklist

Before saving, verify the handover passes these checks:

| Check | Criteria |
|-------|----------|
| **Actionable next steps** | Can a fresh session start item #1 immediately without asking questions? |
| **No orphan references** | Every file path, issue number, and URL referenced actually exists? |
| **Decision completeness** | Every non-trivial decision has reasoning documented? |
| **Pitfall specificity** | Each pitfall has enough detail to prevent the next session from repeating it? |
| **State accuracy** | Git state, test results, and env state are current (not stale from earlier in session)? |
| **Deduplication** | No information repeated across sections? |
| **Concise summaries** | Summary section is 3-5 bullets, not a wall of text? |
| **Complexity estimates** | Every next step has a complexity tag? |

### 8.3 Length Guidelines

| Section | Target Length | Notes |
|---------|-------------|-------|
| Summary | 3-5 lines | High-level only |
| Since Last Handover | 3-8 lines | Skip if no previous handover |
| Decisions | 1 row per decision | Include all non-trivial decisions |
| Workarounds | 1 block per workaround | Include risk if forgotten |
| Pitfalls | 2-3 lines each | Specific and preventive |
| Current State | As needed | Accuracy over brevity |
| Next Steps | 4-8 items typical | Each must be self-contained |
| Learnings | 3-6 items | Only actionable insights |
| References | All relevant paths/links | Completeness matters |

---

