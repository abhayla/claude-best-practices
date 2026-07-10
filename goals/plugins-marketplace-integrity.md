---
name: plugins-marketplace-integrity
description: "Every plugins/*/.claude-plugin/plugin.json parses as JSON and its name appears in plugins/.claude-plugin/marketplace.json."
enrolled: "2026-07-10"
source: "plugins/.claude-plugin/marketplace.json (G6 monorepo)"
last_verified: "2026-07-10"
predicates:
  - kind: command
    cmd: "python -c \"import glob,json; m=json.load(open('plugins/.claude-plugin/marketplace.json', encoding='utf-8')); names={e['name'] for e in m['plugins']}; bad=[]; [bad.append(f) for f in glob.glob('plugins/*/.claude-plugin/plugin.json') if (lambda p: p['name'] not in names)(json.load(open(f, encoding='utf-8')))]; assert not bad, f'not registered: {bad}'\""
on_failure: "A plugin directory exists under plugins/ with a plugin.json that either fails to parse or is missing from marketplace.json's plugins list — a new/edited plugin was scaffolded without registering it (or a registration was dropped). Run /plugin-lifecycle to fix the registration."
---

This is the fleet-wide invariant behind every single-plugin goal in this ledger: the G6
monorepo marketplace (`plugins/.claude-plugin/marketplace.json`) must stay in lockstep
with every plugin directory under `plugins/`. `/plugin-lifecycle` registers new plugins on
create, but a hand-edited `marketplace.json` or a scaffolded-but-never-registered plugin
directory would silently break `/plugin install <name>` for every affected plugin at once
— a class of failure a single per-plugin goal file wouldn't catch for plugins built after
it was written. This goal re-verifies the whole fleet, not just one plugin, every day.
