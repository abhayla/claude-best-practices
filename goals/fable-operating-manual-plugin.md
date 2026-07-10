---
name: fable-operating-manual-plugin
description: "The 5th G6 plugin (fable-operating-manual) stays installable: its manifest parses and it is registered in the marketplace."
enrolled: "2026-07-10"
source: "PR #313, PR #315"
last_verified: "2026-07-10"
predicates:
  - kind: file
    path: plugins/fable-operating-manual/.claude-plugin/plugin.json
  - kind: command
    cmd: "python -c \"import json; p=json.load(open('plugins/fable-operating-manual/.claude-plugin/plugin.json', encoding='utf-8')); assert 'version' in p; m=json.load(open('plugins/.claude-plugin/marketplace.json', encoding='utf-8')); names=[e['name'] for e in m['plugins']]; assert p['name'] in names, f'{p[\\\"name\\\"]} not in marketplace'\""
on_failure: "The plugin manifest lost its version field, or its marketplace.json entry was removed/renamed — a downstream `/plugin install fable-operating-manual` would silently fail to resolve. Re-check plugins/.claude-plugin/marketplace.json and the plugin.json version bump discipline (see /plugin-lifecycle skill)."
---

`fable-operating-manual` is the hub's 5th in-tree G6 marketplace plugin (`plugins/`
monorepo). Being "installable" depends on two things staying true simultaneously: the
plugin's own `plugin.json` must parse as valid JSON with a `version`, and the plugin's
`name` must still appear in `plugins/.claude-plugin/marketplace.json`'s `plugins` list.
Either one can silently drift — a manifest edit that drops `version`, or a marketplace
edit (e.g. adding a 6th plugin) that accidentally clobbers this entry — and a downstream
`/plugin install` would fail with no other signal until someone actually tries it.
