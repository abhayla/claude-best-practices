---
name: docker-optimize
description: >
  Optimize Dockerfiles and Docker Compose configurations for production readiness.
  Covers multi-stage builds, layer caching, image size reduction, security hardening,
  health checks, compose orchestration, multi-platform builds, performance tuning,
  anti-pattern detection, and language-specific optimizations.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<dockerfile-path-or-optimization-goal>"
---

# Docker Optimization

Analyze and optimize Docker configurations for the specified target.

**Request:** $ARGUMENTS

---

## STEP 1: Assess Current State

1. Locate all Dockerfiles, `docker-compose*.yml`, and `.dockerignore` files in the project
2. Read each Dockerfile and note current base images, layer count, and build patterns
3. Check for existing `.dockerignore` — if missing, flag immediately
4. Identify the language/runtime stack to select appropriate optimizations
5. Note the current image size if a built image exists (`docker images`)

---

## STEP 2: Multi-Stage Builds

Separate build-time dependencies from runtime. Every production Dockerfile MUST use multi-stage builds.

### Pattern: Builder + Runtime

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

### Pattern: Build + Test + Runtime (3-Stage)

```dockerfile
# Stage 1: Dependencies
FROM python:3.12-slim AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Test
FROM python:3.12-slim AS test
WORKDIR /app
COPY --from=deps /install /usr/local
COPY . .
RUN python -m pytest tests/ --tb=short

# Stage 3: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=deps /install /usr/local
COPY src/ ./src/
USER nobody
CMD ["python", "-m", "src.main"]
```

### Key Rules

- NEVER install build tools (gcc, make, git) in the runtime stage
- Use `AS <name>` aliases — never reference stages by index number
- Copy only the artifacts needed: compiled binaries, dist folders, installed packages
- If the final image contains compilers or package managers, the multi-stage build is wrong

---

## STEP 3: Layer Caching

Docker caches layers top-down. A changed layer invalidates all subsequent layers.

### Instruction Ordering (Most Stable to Least Stable)

```dockerfile
# 1. Base image (rarely changes)
FROM python:3.12-slim

# 2. System packages (changes occasionally)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Dependency manifests (changes when deps change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Source code (changes frequently)
COPY . .

# 5. Build step (depends on source)
RUN python -m compileall src/
```

### Cache-Busting Mistakes to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `COPY . .` before `pip install` | Source changes bust dep cache | Copy manifest first, install, then copy source |
| `RUN apt-get update` alone | Stale package index gets cached | Combine with `apt-get install` in one RUN |
| `ARG VERSION` before `COPY` | Changing arg busts all layers below | Place ARGs as late as possible |
| Timestamps in build | Every build creates new layer | Use `SOURCE_DATE_EPOCH` for reproducibility |

### BuildKit Cache Mounts

```dockerfile
# Cache pip downloads across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache apt packages across builds
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y libpq-dev

# Cache Go modules
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download
```

---

## STEP 4: Image Size Reduction

### Base Image Selection

| Use Case | Base Image | Approx Size |
|----------|-----------|-------------|
| Go, Rust (static binaries) | `gcr.io/distroless/static-debian12` | ~2 MB |
| Python, Node (need libc) | `*-slim` variants | ~50-80 MB |
| General minimal | `alpine:3.19` | ~7 MB |
| Debug-friendly prod | `*-slim` + debug tools | ~100 MB |
| Security-hardened | `cgr.dev/chainguard/*` | ~10-30 MB |

### Alpine Caveats

- Uses musl libc instead of glibc — some Python packages with C extensions may fail
- DNS resolution behaves differently (no `search` directive by default)
- Use `*-slim` variants instead of alpine when encountering musl compatibility issues

### Reduce Layer Bloat

```dockerfile
# WRONG: Leaves apt cache in layer
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# RIGHT: Single layer, clean in same RUN
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
```

### .dockerignore Patterns

Create a `.dockerignore` in the same directory as the Dockerfile:

```
# Version control
.git
.gitignore

# Dependencies (rebuilt in container)
node_modules
__pycache__
*.pyc
.venv
vendor

# Build artifacts
dist
build
*.o
*.a

# IDE and editor files
.vscode
.idea
*.swp
*.swo

# CI/CD
.github
.gitlab-ci.yml
Jenkinsfile

# Documentation
*.md
docs/
LICENSE

# Docker files (prevent recursive inclusion)
Dockerfile*
docker-compose*
.dockerignore

# Environment and secrets
.env
.env.*
*.pem
*.key
credentials.json

# Test files
tests/
test/
*_test.go
*.test.js
*.spec.ts
coverage/
.nyc_output
```

### Size Audit

After building, audit the image:

```bash
# Show image size
docker images <image-name>

# Inspect layer sizes
docker history <image-name>

# Deep analysis with dive
dive <image-name>
```

---

## STEP 5: Security Hardening

### Non-Root User (Mandatory)

```dockerfile
# Create a dedicated user
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/false appuser

# For alpine
RUN addgroup -S appuser && adduser -S -G appuser appuser

# Switch to non-root BEFORE CMD
USER appuser
CMD ["./app"]
```

### Read-Only Filesystem

```dockerfile
# In docker-compose.yml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
```

### No Secrets in Layers

```dockerfile
# NEVER do this — secret persists in layer history
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

### Security Scanning with Trivy

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

### Security Scanning with Snyk

```bash
# Authenticate
snyk auth

# Test a Docker image
snyk container test <image-name>

# Monitor continuously
snyk container monitor <image-name>
```

### Additional Hardening

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

---

## STEP 6: Health Checks

### Dockerfile HEALTHCHECK

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

### Health Check Parameters

| Parameter | Default | Recommendation |
|-----------|---------|---------------|
| `--interval` | 30s | 10-30s for critical services |
| `--timeout` | 30s | 3-5s (fail fast) |
| `--start-period` | 0s | Set to app startup time + buffer |
| `--retries` | 3 | 2-3 for most services |

### Graceful Shutdown

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

### Application-Level Shutdown

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

---

## STEP 7: Docker Compose

### Service Structure

```yaml
# docker-compose.yml (base — shared config)
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    ports:
      - "${APP_PORT:-3000}:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

volumes:
  pgdata:

networks:
  backend:
    driver: bridge
```

### Dev vs Prod Overrides

```yaml
# docker-compose.override.yml (auto-loaded, dev-only)
services:
  app:
    build:
      target: builder  # Use builder stage with dev tools
    volumes:
      - .:/app          # Bind mount for hot reload
      - /app/node_modules  # Preserve container's node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=true
    command: ["npm", "run", "dev"]

  db:
    ports:
      - "5432:5432"  # Expose DB port for local tools
```

```yaml
# docker-compose.prod.yml
services:
  app:
    build:
      target: runtime
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

```bash
# Run dev (auto-loads override)
docker compose up

# Run prod
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Management

```yaml
# Use .env file for variable substitution
# .env
APP_PORT=3000
POSTGRES_PASSWORD=changeme

# Reference in compose
services:
  app:
    ports:
      - "${APP_PORT}:3000"
```

### Networking Best Practices

- Use custom bridge networks — never rely on the default bridge
- Service names are DNS hostnames within the same network
- Isolate frontend and backend into separate networks
- Only expose ports that external clients need

```yaml
networks:
  frontend:
  backend:
    internal: true  # No external access

services:
  proxy:
    networks: [frontend, backend]
  api:
    networks: [backend]
  db:
    networks: [backend]
```

---

## STEP 8: Build Arguments and Multi-Platform

### ARG/ENV Patterns

```dockerfile
# Build-time arguments (not in final image unless converted to ENV)
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

# Convert to runtime env var if needed
ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}

# Use ARGs for conditional logic
ARG INSTALL_DEV_DEPS=false
RUN if [ "$INSTALL_DEV_DEPS" = "true" ]; then \
        pip install -r requirements-dev.txt; \
    fi
```

```bash
# Pass build args
docker build --build-arg PYTHON_VERSION=3.11 --build-arg APP_VERSION=1.2.3 .
```

### Multi-Platform Builds with Buildx

```bash
# Create a builder instance
docker buildx create --name multiarch --use

# Build for multiple platforms
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag myapp:latest \
    --push .

# Build and load locally (single platform only)
docker buildx build --platform linux/amd64 --load -t myapp:latest .
```

```dockerfile
# Platform-aware Dockerfile
FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -o /app/server .

FROM --platform=$TARGETPLATFORM gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
CMD ["/server"]
```

---

## STEP 9: Performance Tuning

### Volume Strategies

| Type | Use Case | Syntax |
|------|----------|--------|
| Bind mount | Dev: live code reload | `./src:/app/src` |
| Named volume | Data persistence (DB, uploads) | `pgdata:/var/lib/postgresql/data` |
| tmpfs | Temporary/sensitive data, faster I/O | `tmpfs: /tmp` |
| Anonymous volume | Preserve container-only dirs | `/app/node_modules` |

### Resource Limits

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
    # OOM settings
    mem_swappiness: 0
    oom_kill_disable: false
```

### Build Performance

```bash
# Enable BuildKit (faster builds, better caching)
export DOCKER_BUILDKIT=1

# Parallel multi-stage builds (BuildKit default)
# Stages that don't depend on each other build concurrently

# Use .dockerignore to reduce build context size
# Large build contexts slow down every build

# Check build context size
docker build --no-cache . 2>&1 | grep "Sending build context"
```

### Logging Configuration

```yaml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"   # Rotate at 10MB
        max-file: "3"     # Keep 3 rotated files
        compress: "true"
```

---

## STEP 10: Common Anti-Patterns

### Detection Checklist

| Anti-Pattern | Detection | Fix |
|-------------|-----------|-----|
| Running as root | No `USER` instruction | Add non-root user, switch before CMD |
| apt-get without cleanup | `apt-get install` without `rm -rf /var/lib/apt/lists/*` | Combine install + cleanup in one RUN |
| COPY . before deps | `COPY .` appears before dependency install | Copy manifest first, install, then copy source |
| No .dockerignore | Missing `.dockerignore` file | Create with patterns from Step 4 |
| Latest tag | `FROM python:latest` | Pin specific version: `FROM python:3.12-slim` |
| Multiple CMD/ENTRYPOINT | More than one CMD instruction | Only last CMD takes effect — consolidate |
| Secrets in build | `ENV API_KEY=...` or `COPY .env` | Use `--mount=type=secret` or runtime env vars |
| Large base image | Using full `ubuntu` or `python` (non-slim) | Switch to `-slim` or `-alpine` variants |
| Shell form CMD | `CMD python app.py` | Use exec form: `CMD ["python", "app.py"]` |
| No health check | Missing HEALTHCHECK instruction | Add HEALTHCHECK (see Step 6) |
| ADD for local files | `ADD . /app` for non-archive local files | Use COPY — ADD has implicit tar extraction and URL fetch |
| Hardcoded ports/hosts | `ENV DB_HOST=192.168.1.50` | Use service names and environment variables |

### Automated Lint Check

```bash
# Use hadolint for Dockerfile linting
hadolint Dockerfile

# Run via Docker (no local install)
docker run --rm -i hadolint/hadolint < Dockerfile

# Ignore specific rules
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y curl
```

---

## STEP 11: Language-Specific Patterns

### Python

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Build wheels (portable, no compile needed at runtime)
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app

# Install pre-built wheels (no gcc needed)
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

COPY src/ ./src/
USER nobody
CMD ["python", "-m", "src.main"]
```

Key points:
- Use `pip wheel` in builder to pre-compile C extensions
- Use `--no-cache-dir` with pip to avoid caching downloaded packages
- Use `python:*-slim` instead of alpine to avoid musl issues with numpy, pandas, etc.
- Set `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` in production

### Node.js

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app

# Install deps with clean install (respects lockfile exactly)
COPY package.json package-lock.json ./
RUN npm ci

# Build
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production

# Production deps only
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

COPY --from=builder /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

Key points:
- Use `npm ci` instead of `npm install` for deterministic builds
- Use `--omit=dev` in runtime to exclude devDependencies
- The `node` user is built into the official Node image
- Set `NODE_ENV=production` before `npm ci` to affect package behavior

### Go

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Cache module downloads
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w" \
    -o /server ./cmd/server

# Distroless: ~2MB final image
FROM gcr.io/distroless/static-debian12
COPY --from=builder /server /server
USER nonroot:nonroot
ENTRYPOINT ["/server"]
```

Key points:
- `CGO_ENABLED=0` produces a static binary — no libc dependency
- `-ldflags="-s -w"` strips debug info, reducing binary size ~30%
- Distroless has no shell — use `ENTRYPOINT` with exec form only
- Cache `go mod download` separately from source copy

### Java (Spring Boot)

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app

COPY gradle/ gradle/
COPY gradlew build.gradle.kts settings.gradle.kts ./
RUN ./gradlew dependencies --no-daemon

COPY src/ src/
RUN ./gradlew bootJar --no-daemon -x test

# Use jlink to create minimal JRE
FROM eclipse-temurin:21-jdk-alpine AS jre-builder
RUN jlink \
    --add-modules java.base,java.logging,java.sql,java.naming,java.management,java.instrument,java.desktop \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --compress=zip-6 \
    --output /custom-jre

FROM alpine:3.19 AS runtime
COPY --from=jre-builder /custom-jre /opt/java
ENV PATH="/opt/java/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar

RUN addgroup -S appuser && adduser -S -G appuser appuser
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["sh", "-c", "echo > /dev/tcp/localhost/8080 || exit 1"]
CMD ["java", "-jar", "app.jar"]
```

Key points:
- Use `jlink` to create a custom minimal JRE — reduces image by 200+ MB
- Cache Gradle/Maven dependency download before source copy
- Use `--no-daemon` in containers to avoid zombie processes
- Spring Boot layered JARs can further optimize caching

### Rust

```dockerfile
FROM rust:1.77-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /app

# Cache dependencies via dummy build
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release && rm -rf src target/release/deps/myapp*

COPY src/ src/
RUN cargo build --release

FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/target/release/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

Key points:
- Use the dummy-build trick to cache dependency compilation
- Alpine + musl gives static binaries by default
- Final image with distroless is typically 5-15 MB

---

## STEP 12: Apply Optimizations

1. Implement changes to Dockerfiles following the patterns above
2. Update or create `.dockerignore` file
3. Update `docker-compose*.yml` files if present
4. Build the optimized image and compare size with the original
5. Run security scan on the new image
6. Verify health checks work correctly

---

## Verification Checklist

| Check | Command | Status |
|-------|---------|--------|
| Image builds successfully | `docker build -t app:optimized .` | |
| Multi-stage used | `grep -c "^FROM" Dockerfile` (should be >= 2) | |
| Non-root user | `docker run app:optimized whoami` (not root) | |
| .dockerignore exists | `test -f .dockerignore` | |
| No secrets in layers | `docker history app:optimized` | |
| Health check defined | `docker inspect app:optimized \| jq '.[0].Config.Healthcheck'` | |
| Image size reduced | Compare `docker images` before and after | |
| Security scan clean | `trivy image --severity HIGH,CRITICAL app:optimized` | |
| Compose services start | `docker compose up -d && docker compose ps` | |
| Graceful shutdown works | `docker compose stop` (exits within grace period) | |

---

## CRITICAL RULES

- NEVER leave containers running as root in production — always add a USER instruction
- NEVER embed secrets (API keys, passwords, tokens) in Dockerfile instructions or layers
- NEVER use `latest` tag for base images — pin specific versions for reproducibility
- ALWAYS create a `.dockerignore` to exclude `.git`, `node_modules`, `.env`, and test files
- ALWAYS use exec form (`["cmd", "arg"]`) for CMD and ENTRYPOINT — shell form breaks signal handling
- ALWAYS combine `apt-get update` and `apt-get install` in a single RUN with cleanup
- ALWAYS copy dependency manifests and install before copying source code for proper layer caching
- Prefer `COPY` over `ADD` unless extracting archives or fetching URLs
- Run `hadolint` or `trivy config` on Dockerfiles before committing
- Set resource limits in production compose files to prevent OOM and CPU starvation
