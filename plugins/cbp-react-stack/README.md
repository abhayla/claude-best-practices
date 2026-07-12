# cbp-react-stack

**The React-family toolbox — the first Tier-2 stack pack of the #187 distribution pilot.**
The workflow plugins (`cbp-build-test-workflows`, `cbp-workflows`) ship *processes* and
deliberately exclude language-specific tools. This pack is those tools for the React family:
install it and the same workflows automatically use the framework-aware path instead of the
generic one.

## Install

```
/plugin install cbp-react-stack
```

(from the hub repo's marketplace — `plugins/.claude-plugin/marketplace.json`.)
Pairs with `cbp-build-test-workflows` — a toolbox alone is just parts.

## What's included

| Type | Name | Role |
|---|---|---|
| Skill | `vitest-dev` | Vitest runner know-how: config, jsdom, coverage, watch quirks — the test-pipeline's React-project lane |
| Skill | `jest-dev` | Jest runner know-how for Jest-based projects |
| Skill | `nextjs-dev` | Next.js development patterns (routing, SSR/ISR, data fetching) |
| Skill | `react-test-patterns` | Component/hook testing patterns (Testing Library idioms) |
| Skill | `react-native-dev` | React Native development patterns |
| Skill | `react-native-e2e` | React Native end-to-end testing |

## Boundaries

- **The `react-nextjs` rule is NOT here:** Claude Code plugins cannot ship auto-loaded
  `rules/*.md` (verified in the #187 spike) — path-scoped rules stay on the provisioning
  path (`recommend.py --provision`).
- **Other stacks get their own packs** (`cbp-python-stack` next); nothing in this pack
  assumes or conflicts with them — install only the packs your project uses.

## Versioning

Installed plugins are version-pinned in Claude Code's cache. Fixes reach you when the hub
bumps `version` in `.claude-plugin/plugin.json` and you run `/plugin update cbp-react-stack`.
