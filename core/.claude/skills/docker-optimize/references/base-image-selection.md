# Base Image Selection

### Base Image Selection

| Use Case | Base Image | Approx Size |
|----------|-----------|-------------|
| Go, Rust (static binaries) | `gcr.io/distroless/static-debian12` | ~2 MB |
| Python, Node (need libc) | `*-slim` variants | ~50-80 MB |
| General minimal | `alpine:3.19` | ~7 MB |
| Debug-friendly prod | `*-slim` + debug tools | ~100 MB |
| Security-hardened | `cgr.dev/chainguard/*` | ~10-30 MB |

