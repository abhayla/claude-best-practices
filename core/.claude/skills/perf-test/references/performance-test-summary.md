# Performance Test Summary

### k6 Load Test Results
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| p95 latency | 320ms | < 500ms | PASS |
| p99 latency | 890ms | < 1500ms | PASS |
| Error rate | 0.2% | < 1% | PASS |
| Throughput | 245 rps | >= 200 rps | PASS |

### Lighthouse Scores
| Page | Perf | LCP | FID | CLS |
|------|------|-----|-----|-----|
| / | 94 | 1.8s | 32ms | 0.02 |
| /dashboard | 88 | 2.9s | 55ms | 0.08 |

### Bundle Size
| Bundle | Gzipped | Budget | Status |
|--------|---------|--------|--------|
| Total JS | 198KB | < 250KB | PASS |

### Baseline Comparison
| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| p95 latency | 310ms | 320ms | +3.2% OK |
| Bundle size | 192KB | 198KB | +3.1% OK |

### Regressions Found
- /dashboard LCP is 2.9s (target < 2.5s) — investigate image loading
```

---

