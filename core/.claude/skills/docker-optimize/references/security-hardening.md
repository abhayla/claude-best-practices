# Security Hardening Details

## Non-Root User (Mandatory)

```dockerfile
# Create a dedicated user
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser

# For alpine
RUN addgroup -S appuser && adduser -S -G appuser appuser

# Switch to non-root BEFORE CMD
USER appuser
CMD ["./app"]
```

## Read-Only Filesystem

```yaml
# In docker-compose.yml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

## No Secrets in Layers

```dockerfile
# NEVER do this -- secret persists in layer history
COPY .env /app/.env
RUN echo "API_KEY=secret" > /app/config

# Use build secrets (BuildKit)
RUN --mount=type=secret,id=api_key \
    cat /run/secrets/api_key > /tmp/key && \
    ./configure --key=$(cat /tmp/key) && \
    rm /tmp/key

# Or pass at runtime
docker run -e API_KEY=secret app
docker run --env-file .env app
```

## Security Scanning with Trivy

```bash
# Scan a built image
trivy image <image-name>

# Scan and fail on HIGH/CRITICAL
trivy image --severity HIGH,CRITICAL --exit-code 1 <image-name>

# Scan Dockerfile for misconfigurations
trivy config Dockerfile

# Scan as part of CI
trivy image --format json --output results.json <image-name>
```

## Security Scanning with Snyk

```bash
# Authenticate
snyk auth

# Test a Docker image
snyk container test <image-name>

# Monitor continuously
snyk container monitor <image-name>
```

## Additional Hardening

```dockerfile
# Drop all capabilities, add only what's needed
# (in docker-compose.yml or docker run)
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE

# No new privileges
security_opt:
  - no-new-privileges:true

# Pin base image by digest for reproducibility
FROM python:3.12-slim@sha256:abc123...
```
