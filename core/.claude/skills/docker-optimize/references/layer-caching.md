# Layer Caching Details

## Instruction Ordering (Most Stable to Least Stable)

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

## Cache-Busting Mistakes to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| `COPY . .` before `pip install` | Source changes bust dep cache | Copy manifest first, install, then copy source |
| `RUN apt-get update` alone | Stale package index gets cached | Combine with `apt-get install` in one RUN |
| `ARG VERSION` before `COPY` | Changing arg busts all layers below | Place ARGs as late as possible |
| Timestamps in build | Every build creates new layer | Use `SOURCE_DATE_EPOCH` for reproducibility |

## BuildKit Cache Mounts

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
