# Pitfalls Discovered

## Pitfalls Discovered

- **Don't modify `config/settings.yml` directly** — it is overwritten by the
  build script (`scripts/build.sh:47`). Edit `config/settings.template.yml`
  instead and run `scripts/generate-config.sh`.

- **API rate limit is 100/min, not 1000/min** — the official docs at
  `docs.example.com/limits` are outdated. Discovered by hitting 429 errors
  during integration testing. Workaround: added 600ms delay between requests
  in `src/api/client.py:89`.

- **Test suite requires Docker running locally** — the `test_integration_*`
  tests connect to a Postgres container. No helpful error message if Docker
  is down — tests just hang for 30s then fail with "connection refused."
  Run `docker compose up -d` before testing.

- **The `user.email` field can be null** — despite the schema saying NOT NULL,
  legacy users imported from the old system have null emails. The migration
  (`migrations/005_import_legacy.py`) skipped email validation.
  Always null-check `user.email` before using it in notifications.

- **Branch `feature/auth-v2` has diverged significantly from main** — do NOT
  rebase, it will create 47 conflicts. Merge main into the branch instead.
  Last tested merge: clean as of commit `abc1234`.

- **`npm install` fails on Apple Silicon without Rosetta** — native dependency
  `better-sqlite3` needs `arch -x86_64` prefix. Or install from source with
  `npm install --build-from-source`.
```

---

