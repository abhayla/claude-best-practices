# Verification Checklist

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

