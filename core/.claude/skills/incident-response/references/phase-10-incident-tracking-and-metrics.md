# PHASE 10: Incident Tracking and Metrics

### 10.1 Key Metrics

Track these metrics across all incidents to measure and improve response capability:

| Metric | Definition | Target |
|--------|-----------|--------|
| **MTTD** (Mean Time to Detect) | Time from incident start to first alert | < 5 min |
| **MTTA** (Mean Time to Acknowledge) | Time from alert to first human response | < 5 min (SEV1), < 15 min (SEV2) |
| **MTTR** (Mean Time to Resolve) | Time from detection to resolution | < 1 hour (SEV1), < 4 hours (SEV2) |
| **MTTM** (Mean Time to Mitigate) | Time from detection to user-impact mitigation | < 30 min (SEV1) |
| **Incident frequency** | Number of incidents per week/month by severity | Trending down |
| **SLO burn rate** | Error budget consumed per incident | Within monthly budget |
| **Post-mortem completion rate** | Percentage of SEV1-SEV2 incidents with completed post-mortems | 100% |
| **Action item completion rate** | Percentage of post-mortem action items completed on time | > 80% |

### 10.2 Incident Tracking Checklist

For every incident, ensure:

- [ ] Incident record created with severity, timestamps, and IC
- [ ] Timeline documented in real time (not reconstructed afterward)
- [ ] Status page updated (SEV1-SEV3)
- [ ] Post-mortem scheduled within 48 hours (SEV1-SEV2)
- [ ] Post-mortem completed within 5 business days (SEV1-SEV2)
- [ ] Action items assigned with owners and due dates
- [ ] Action items reviewed at 2-week mark
- [ ] Metrics updated in incident tracking system

### 10.3 Monthly Incident Review

Hold a monthly review covering:

1. **Incident count by severity** — trend over time
2. **MTTR / MTTD trends** — are we getting faster?
3. **Repeat incidents** — same root cause appearing multiple times?
4. **Action item completion** — are we following through?
5. **SLO health** — error budget status across services
6. **On-call burden** — pages per shift, off-hours pages, toil assessment

---

