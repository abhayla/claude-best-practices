---
description: Portability standards for patterns distributed via core/.claude/. Ensures patterns work in any project without modification.
globs: ["core/.claude/**/*.md"]
---

# Pattern Portability Standards

## No Hardcoded Paths

MUST NOT use absolute paths (`C:\`, `/home/`, `/Users/`, `/var/log/app/`). Use environment variables (`$PROJECT_ROOT`, `$DATABASE_URL`), relative paths, or generic placeholders (`/path/to/project`).

Exception: paths inside Dockerfile examples, docker-compose volume mounts, or OS-level references that are universally standard (e.g., `/dev/null`, `/etc/hosts`).

## No Project-Specific References

MUST NOT reference specific file names, class names, or module paths as if they exist in the target project. Use generic placeholders instead:
- `src/services/<YourService>.ts` not `src/services/UserService.ts`
- `com.example.app` not `com.mycompany.myapp`
- `your-project` not `claude-best-practices`

## Stack-Prefix Scope

Stack-prefixed patterns (`fastapi-*`, `android-*`, `react-*`) MAY assume their stack's standard tools and conventions (e.g., `pytest` for FastAPI, `Gradle` for Android) but MUST NOT assume project-specific directory structures, custom tooling, or non-standard configurations.

## Least-Privilege `allowed-tools`

Read-only skills (status checks, analysis, reference lookups) MUST NOT include `Write`, `Edit`, or `Bash` in `allowed-tools`. Each tool listed expands what the skill can do — and what can go wrong. Only list tools that the skill's steps actually use.

| Skill Type | Expected Tools |
|---|---|
| Analysis / read-only | `Read Grep Glob` |
| Workflow with modifications | `Bash Read Write Edit Grep Glob` |
| Skill that delegates | Add `Skill` only if it calls other skills |
| Skill that needs subagents | Add `Agent` only if it spawns subagents |

## No Environment Assumptions

MUST NOT assume a specific OS, package manager, or CI provider unless the pattern is stack-prefixed. Use conditional patterns:
- `npm test` / `yarn test` / `pnpm test` — not just one
- `python` / `python3` — note both or use a variable
- Provide alternatives when platform behavior differs
