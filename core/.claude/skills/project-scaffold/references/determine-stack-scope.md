# STEP 1: Determine Stack & Scope

## STEP 1: Determine Stack & Scope

1. **Parse input** — Accept a stack name (e.g., "fastapi", "next.js", "android"), a PRD file path, or inline description
2. **If PRD provided** — Extract tech stack from the PRD's NFRs, constraints, and milestones
3. **Confirm stack** — Present the detected stack and ask for confirmation:

```
Detected stack: FastAPI + PostgreSQL + React (Next.js)
Scaffolding includes:
  ✓ Package manifests & lockfiles
  ✓ Folder structure (Clean Architecture layers)
  ✓ Linter + formatter
  ✓ Test framework
  ✓ Git hooks (pre-commit)
  ✓ CI pipeline (GitHub Actions)
  ✓ Docker Compose dev environment
  ✓ Security baseline (dependency audit, SAST, Dependabot)
  ✓ 12-factor compliance
  ✓ Commitlint + semantic versioning
  ✓ .editorconfig + shared IDE settings
  ✓ Health endpoint
  ✓ License file

Proceed? [Y/n]
```

Wait for confirmation before generating files.

---

