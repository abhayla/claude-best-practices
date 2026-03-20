# STEP 2: Write k6 Scripts

### 2.1 Shared Configuration

```javascript
// perf/k6/config.js
export const NFR = {
  p95_latency: 500,   // ms
  p99_latency: 1500,  // ms
  error_rate: 0.01,   // 1%
  min_rps: 200,
};

export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const defaultThresholds = {
  http_req_duration: [`p(95)<${NFR.p95_latency}`, `p(99)<${NFR.p99_latency}`],
  http_req_failed: [`rate<${NFR.error_rate}`],
  iterations: [`rate>=${NFR.min_rps}`],
};
```

### 2.2 Smoke Test (Sanity check — minimal load)

```javascript
// perf/k6/smoke.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultThresholds } from "./config.js";

export const options = {
  vus: 1,
  duration: "30s",
  thresholds: defaultThresholds,
};

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, { "status is 200": (r) => r.status === 200 });
}
```

### 2.3 Load Test (Expected traffic)

```javascript
// perf/k6/load.js
import http from "k6/http";
import { check, sleep } from "k6";
import { BASE_URL, defaultThresholds } from "./config.js";

export const options = {
  stages: [
    { duration: "2m", target: 50 },   // ramp up
    { duration: "5m", target: 50 },   // steady state
    { duration: "2m", target: 0 },    // ramp down
  ],
  thresholds: defaultThresholds,
};

export default function () {
  const res = http.get(`${BASE_URL}/api/v1/resource`);
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### 2.4 Stress Test (Beyond expected limits)

```javascript
// perf/k6/stress.js
export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "3m", target: 100 },
    { duration: "3m", target: 200 },  // beyond normal
    { duration: "3m", target: 300 },  // breaking point
    { duration: "2m", target: 0 },
  ],
  thresholds: defaultThresholds,
};
```

### 2.5 Spike Test (Sudden traffic surge)

```javascript
// perf/k6/spike.js
export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "10s", target: 500 },  // spike
    { duration: "1m", target: 500 },
    { duration: "10s", target: 10 },   // drop
    { duration: "1m", target: 10 },
  ],
  thresholds: defaultThresholds,
};
```

### 2.6 Soak Test (Extended duration for memory leaks)

```javascript
// perf/k6/soak.js
export const options = {
  stages: [
    { duration: "5m", target: 50 },
    { duration: "60m", target: 50 },  // sustained load
    { duration: "5m", target: 0 },
  ],
  thresholds: defaultThresholds,
};
```

---

