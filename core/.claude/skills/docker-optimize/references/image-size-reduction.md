# Image Size Reduction Details

## Alpine Caveats

- Uses musl libc instead of glibc -- some Python packages with C extensions may fail
- DNS resolution behaves differently (no `search` directive by default)
- Use `*-slim` variants instead of alpine when encountering musl compatibility issues

## Reduce Layer Bloat

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

## .dockerignore Template

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

## Size Audit

After building, audit the image:

```bash
# Show image size
docker images <image-name>

# Inspect layer sizes
docker history <image-name>

# Deep analysis with dive
dive <image-name>
```
