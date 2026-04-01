# Portability Rules

## No Hardcoded Paths

MUST NOT use absolute paths (`C:\`, `/home/`, `/Users/`, `/var/log/app/`).
Use environment variables (`$PROJECT_ROOT`, `$DATABASE_URL`), relative paths, or generic placeholders.

Exception: paths inside Dockerfile examples, docker-compose, or universally standard OS paths (`/dev/null`, `/etc/hosts`).

## No Project-Specific References

MUST NOT reference specific file names, class names, or module paths as if they exist:
- Use `src/services/<YourService>.ts` not `src/services/UserService.ts`
- Use `com.example.app` not `com.mycompany.myapp`
- Use `your-project` not `claude-best-practices`

## Stack-Prefix Scope

Stack-prefixed patterns (`fastapi-*`, `android-*`, `react-*`) MAY assume their stack's standard tools but MUST NOT assume project-specific directory structures or non-standard configurations.

## No Environment Assumptions

MUST NOT assume a specific OS, package manager, or CI provider unless stack-prefixed. Use conditional patterns:
- `npm test` / `yarn test` / `pnpm test` — not just one
- `python` / `python3` — note both
- Provide alternatives when platform behavior differs
