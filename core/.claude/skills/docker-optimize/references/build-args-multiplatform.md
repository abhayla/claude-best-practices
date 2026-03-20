# Build Arguments and Multi-Platform Builds

## ARG/ENV Patterns

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

## Multi-Platform Builds with Buildx

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
