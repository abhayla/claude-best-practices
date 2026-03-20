# Health Checks & Graceful Shutdown

## Dockerfile HEALTHCHECK Examples

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# TCP health check (no curl needed)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["sh", "-c", "echo > /dev/tcp/localhost/8080 || exit 1"]

# File-based health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["test", "-f", "/tmp/healthy"]

# Custom script
COPY healthcheck.sh /usr/local/bin/
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["healthcheck.sh"]
```

## Health Check Parameters

| Parameter | Default | Recommendation |
|-----------|---------|---------------|
| `--interval` | 30s | 10-30s for critical services |
| `--timeout` | 30s | 3-5s (fail fast) |
| `--start-period` | 0s | Set to app startup time + buffer |
| `--retries` | 3 | 2-3 for most services |

## Graceful Shutdown

```dockerfile
# Use exec form so signals reach the process
CMD ["python", "app.py"]  # Correct: PID 1 receives SIGTERM

# WRONG: shell form wraps in /bin/sh, signals don't propagate
CMD python app.py

# For apps that need cleanup time
STOPSIGNAL SIGTERM
# In docker-compose.yml:
# stop_grace_period: 30s
```

## Application-Level Shutdown

```python
# Python example: handle SIGTERM
import signal, sys

def shutdown_handler(signum, frame):
    print("Shutting down gracefully...")
    # Close DB connections, flush buffers, etc.
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
```

```javascript
// Node.js example: handle SIGTERM
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down...');
  server.close(() => {
    process.exit(0);
  });
});
```
