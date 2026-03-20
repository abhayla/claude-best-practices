# STEP 4: Git Hooks & Conventional Commits

### 4.1 Pre-commit Hook

**Python** — Use `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: lint
        name: ruff check
        entry: ruff check --fix
        language: system
        types: [python]
      - id: format
        name: ruff format
        entry: ruff format
        language: system
        types: [python]
      - id: typecheck
        name: mypy
        entry: mypy
        language: system
        types: [python]
        pass_filenames: false
```

**Node/TS** — Use Husky + lint-staged:
```json
// package.json
{
  "lint-staged": {
    "*.{ts,tsx,js,jsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md,yml}": ["prettier --write"]
  }
}
```

### 4.2 Commitlint

Enforce conventional commits:

**Node** — `commitlint.config.js`:
```js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'subject-max-length': [2, 'always', 72],
  },
};
```

**Python/Go/Rust** — Use a commit-msg hook script:
```bash
#!/usr/bin/env bash
