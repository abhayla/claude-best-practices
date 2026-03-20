# 6. HPA Autoscaling

### CPU-Based Autoscaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Memory-Based Autoscaling

```yaml
metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Custom Metrics (Prometheus Adapter)

```yaml
metrics:
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 100
```

Requires Prometheus + Prometheus Adapter or KEDA for event-driven scaling.

### Scaling Behavior

Control how fast scaling happens to prevent flapping:

```yaml
spec:
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60      # add max 2 pods per minute
        - type: Percent
          value: 50
          periodSeconds: 60
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: 300   # wait 5 min before scaling down
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120     # remove max 1 pod per 2 minutes
```

### Guidelines

- MUST set `minReplicas: 2` for production (HA requires at least 2 pods).
- Set `maxReplicas` based on budget and downstream capacity (DB connections, etc.).
- Scale-down should be slower than scale-up to avoid flapping.
- Combine CPU and memory metrics — use `max` policy so either can trigger scaling.
- HPA requires resource requests to be set on the target deployment.
- For event-driven workloads (queue depth, Kafka lag), use KEDA instead of HPA.

---

