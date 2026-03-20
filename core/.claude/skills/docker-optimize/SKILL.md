---
name: docker-optimize
description: >
  Optimize Dockerfiles and Docker Compose configurations for production readiness.
  Covers multi-stage builds, layer caching, image size reduction, security hardening,
  health checks, compose orchestration, multi-platform builds, performance tuning,
  anti-pattern detection, and language-specific optimizations.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<dockerfile-path-or-optimization-goal>"
version: "1.0.0"
type: workflow
triggers:
  - docker optimize
  - dockerfile
  - docker compose
  - container image
  - multi-stage build
---

# Docker Optimization

Analyze and optimize Docker configurations for the specified target.

**Request:** $ARGUMENTS

---

## STEP 1: Assess Current State

1. Locate all Dockerfiles, `docker-compose*.yml`, and `.dockerignore` files in the project
2. Read each Dockerfile and note current base images, layer count, and build patterns
3. Check for existing `.dockerignore` -- if missing, flag immediately
4. Identify the language/runtime stack to select appropriate optimizations
5. Note the current image size if a built image exists (`docker images`)

---

## STEP 2: Multi-Stage Builds

Separate build-time dependencies from runtime. Every production Dockerfile MUST use multi-stage builds. Use Builder + Runtime (2-stage) or Build + Test + Runtime (3-stage) patterns.

**Read:** `references/multi-stage-builds.md` for complete Dockerfile examples and key rules.

Core principle: copy only artifacts needed (compiled binaries, dist folders, installed packages). If the final image contains compilers or package managers, the multi-stage build is wrong.

---

## STEP 3: Layer Caching

Docker caches layers top-down. A changed layer invalidates all subsequent layers. Order instructions from most stable (base image) to least stable (source code).

**Read:** `references/layer-caching.md` for ordering examples, cache-busting mistakes table, and BuildKit cache mount patterns.

Key rule: always copy dependency manifests and install before copying source code.

---

## STEP 4: Image Size Reduction

Minimize image size through base image selection, layer consolidation, and build context exclusion.

**Read:** `references/image-size-reduction.md` for Alpine caveats, layer bloat fixes, `.dockerignore` template, and size audit commands.

Key decisions:
- Use `*-slim` variants instead of alpine when musl compatibility is an issue
- Combine `apt-get update` and `apt-get install` in a single RUN with cleanup
- Always create a `.dockerignore` to exclude `.git`, `node_modules`, `.env`, test files

---

## STEP 5: Security Hardening

Every production container MUST run as non-root, never embed secrets in layers, and use security scanning.

**Read:** `references/security-hardening.md` for non-root user setup, read-only filesystem, build secrets, Trivy/Snyk scanning, and capability dropping.

Key checklist:
- Add `USER` instruction before `CMD`
- Use `--mount=type=secret` for build-time secrets (BuildKit)
- Pin base images by digest for reproducibility
- Run `trivy image --severity HIGH,CRITICAL --exit-code 1` in CI

---

## STEP 6: Health Checks

Every service MUST have a health check. Use HTTP, TCP, or file-based checks depending on the service type.

**Read:** `references/health-checks.md` for HEALTHCHECK examples, parameter recommendations, graceful shutdown patterns, and application-level signal handling.

Key rules:
- Use exec form (`["cmd", "arg"]`) for CMD -- shell form breaks signal handling
- Set `--start-period` to app startup time + buffer
- Set `--timeout` to 3-5s (fail fast)

---

## STEP 7: Docker Compose

Structure compose files with base config, dev overrides, and prod overrides. Use `depends_on` with `condition: service_healthy` for startup ordering.

**Read:** `references/docker-compose.md` for full service structure examples, dev/prod override patterns, and environment management.

Key pattern:
- `docker-compose.yml` -- base shared config
- `docker-compose.override.yml` -- auto-loaded dev overrides
- `docker-compose.prod.yml` -- explicit prod config with resource limits

---

## STEP 8: Build Arguments and Multi-Platform

Use `ARG` for build-time configuration and `ENV` for runtime. Use BuildKit buildx for multi-platform images.

**Read:** `references/build-args-multiplatform.md` for ARG/ENV patterns, conditional logic, and platform-aware Dockerfile examples.

---

## STEP 9: Performance Tuning

Enable BuildKit (`DOCKER_BUILDKIT=1`) for faster builds and better caching. Use `.dockerignore` to reduce build context size.

**Read:** `references/performance-tuning.md` for detailed performance tuning reference material.

```bash
# Check build context size
docker build --no-cache . 2>&1 | grep "Sending build context"
```

---

## STEP 10: Common Anti-Patterns

Lint Dockerfiles with hadolint to catch common mistakes before they reach production.

**Read:** `references/common-anti-patterns.md` for detailed anti-patterns reference material.

```bash
# Use hadolint for Dockerfile linting
hadolint Dockerfile

# Run via Docker (no local install)
docker run --rm -i hadolint/hadolint < Dockerfile
```

---

## STEP 11: Language-Specific Patterns

Select the appropriate pattern for your runtime stack. Each language has specific optimizations for dependency caching, binary compilation, and minimal base images.

**Read:** `references/language-patterns.md` for complete Dockerfiles and key points for Python, Node.js, Go, Java, and Rust.

| Language | Base Image | Key Optimization |
|----------|-----------|-----------------|
| Python | `python:*-slim` | `pip wheel` in builder, `--no-cache-dir` |
| Node.js | `node:*-alpine` | `npm ci --omit=dev`, built-in `node` user |
| Go | `golang:*-alpine` | `CGO_ENABLED=0`, distroless final (~2MB) |
| Java | `eclipse-temurin:*-jdk-alpine` | `jlink` custom JRE (-200MB) |
| Rust | `rust:*-alpine` | Dummy-build trick for dep caching, distroless final |

---

## STEP 12: Apply Optimizations

1. Implement changes to Dockerfiles following the patterns above
2. Update or create `.dockerignore` file
3. Update `docker-compose*.yml` files if present
4. Build the optimized image and compare size with the original
5. Run security scan on the new image
6. Verify health checks work correctly

---

## CRITICAL RULES

- NEVER leave containers running as root in production -- always add a USER instruction
- NEVER embed secrets (API keys, passwords, tokens) in Dockerfile instructions or layers
- NEVER use `latest` tag for base images -- pin specific versions for reproducibility
- ALWAYS create a `.dockerignore` to exclude `.git`, `node_modules`, `.env`, and test files
- ALWAYS use exec form (`["cmd", "arg"]`) for CMD and ENTRYPOINT -- shell form breaks signal handling
- ALWAYS combine `apt-get update` and `apt-get install` in a single RUN with cleanup
- ALWAYS copy dependency manifests and install before copying source code for proper layer caching
- Prefer `COPY` over `ADD` unless extracting archives or fetching URLs
- Run `hadolint` or `trivy config` on Dockerfiles before committing
- Set resource limits in production compose files to prevent OOM and CPU starvation
