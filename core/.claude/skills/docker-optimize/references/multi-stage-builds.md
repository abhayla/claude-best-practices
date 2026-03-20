# Multi-Stage Build Examples

## Pattern: Builder + Runtime (Node.js)

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

## Pattern: Build + Test + Runtime (3-Stage, Python)

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

## Key Rules

- NEVER install build tools (gcc, make, git) in the runtime stage
- Use `AS <name>` aliases -- never reference stages by index number
- Copy only the artifacts needed: compiled binaries, dist folders, installed packages
- If the final image contains compilers or package managers, the multi-stage build is wrong
