# STEP 10: Common Anti-Patterns

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
