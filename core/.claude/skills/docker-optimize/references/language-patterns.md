# Language-Specific Docker Patterns

## Python

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

## Node.js

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

## Go

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
- `CGO_ENABLED=0` produces a static binary -- no libc dependency
- `-ldflags="-s -w"` strips debug info, reducing binary size ~30%
- Distroless has no shell -- use `ENTRYPOINT` with exec form only
- Cache `go mod download` separately from source copy

## Java (with jlink)

```dockerfile
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
- Use `jlink` to create a custom minimal JRE -- reduces image by 200+ MB
- Cache Gradle/Maven dependency download before source copy
- Use `--no-daemon` in containers to avoid zombie processes
- Spring Boot layered JARs can further optimize caching

## Rust

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
