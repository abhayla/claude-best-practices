# Docker Compose Examples

## Service Structure

```yaml
# docker-compose.yml (base -- shared config)
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

## Dev vs Prod Overrides

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

## Environment Management

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
