# cbp-python-stack

**The Python/FastAPI toolbox — second Tier-2 stack pack of the #187 distribution pilot**
(first: `cbp-react-stack`). The workflow plugins ship *processes* and deliberately exclude
language-specific tools; this pack is those tools for Python backends. Install it and the
same workflows automatically use the framework-aware path instead of the generic one.

## Install

```
/plugin install cbp-python-stack
```

(from the hub repo's marketplace — `plugins/.claude-plugin/marketplace.json`.)
Pairs with `cbp-build-test-workflows` — a toolbox alone is just parts.

## What's included

| Type | Name | Role |
|---|---|---|
| Skill | `pytest-dev` | Pytest runner know-how: fixtures, parametrize, markers, coverage — the test-pipeline's Python lane |
| Skill | `fastapi-run-backend-tests` | FastAPI backend test execution (TestClient/httpx patterns, async tests) |
| Skill | `fastapi-db-migrate` | Alembic migration authoring + verification for FastAPI/SQLAlchemy apps |
| Skill | `fastapi-deploy` | FastAPI deployment patterns |
| Agent | `fastapi-api-tester-agent` | API-lane test worker for the pipeline |
| Agent | `fastapi-database-admin-agent` | Database admin/migration worker |

## Boundaries

- **The `fastapi-backend` / `fastapi-database` rules are NOT here:** plugins cannot ship
  auto-loaded `rules/*.md` (#187 spike) — path-scoped rules stay on the provisioning path.
- **Other stacks get their own packs** (`cbp-react-stack` for the React family); install
  only the packs your project uses.

## Versioning

Installed plugins are version-pinned in Claude Code's cache. Fixes reach you when the hub
bumps `version` in `.claude-plugin/plugin.json` and you run `/plugin update cbp-python-stack`.
