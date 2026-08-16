---
name: downstream-plugin-installability
description: "Every plugin a downstream project is told to install stays actually installable — recommended, registered in the marketplace, and present on disk."
enrolled: "2026-08-16"
source: "T-144 (outward-pointing standing invariants)"
last_verified: "2026-08-16"
predicates:
  - kind: file
    path: config/plugin-recommendations.yml
  - kind: file
    path: plugins/.claude-plugin/marketplace.json
  - kind: command
    cmd: "python -c \"import json,sys,pathlib,re; rec=pathlib.Path('config/plugin-recommendations.yml').read_text(encoding='utf-8'); names=set(re.findall(r'^\\s*-\\s*name:\\s*(\\S+)', rec, re.M)); mk={p['name'] for p in json.load(open('plugins/.claude-plugin/marketplace.json',encoding='utf-8'))['plugins']}; missing=sorted(names-mk); sys.exit('recommended but not in marketplace: '+', '.join(missing) if missing else 0)\""
  - kind: command
    cmd: "python -c \"import json,sys,pathlib; mk=json.load(open('plugins/.claude-plugin/marketplace.json',encoding='utf-8'))['plugins']; bad=[p['name'] for p in mk if not (pathlib.Path('plugins')/p['source'].lstrip('./')/'.claude-plugin'/'plugin.json').is_file()]; sys.exit('marketplace entries with no plugin.json on disk: '+', '.join(bad) if bad else 0)\""
on_failure: "A plugin recommended to downstream projects is missing from the marketplace, or a marketplace entry points at a directory with no plugin.json — a downstream `/plugin install` for it FAILS. Re-register the plugin (/plugin-lifecycle) or drop the recommendation."
---

**Outward-pointing invariant: consumer health, not hub health.**

The hub tells every enrolled project which plugins to install (`config/plugin-recommendations.yml`,
read by `recommend.py`). That advice is a promise made to a machine the hub does not control:
a downstream project runs `/plugin install <name>@claude-best-practices` and either gets a
working capability or an error.

The silent-death mode this catches: a plugin is renamed, retired, or moved, and the
recommendation list keeps naming it. Nothing in the hub breaks — the hub's own tests pass,
its CI is green, its dashboard is fine — because the failure happens in someone else's repo,
at install time, with nobody watching. The same holds for a marketplace entry whose `source`
directory has lost its `plugin.json`: the entry looks registered but serves nothing.

Both predicates are hermetic (no network, no `gh`) so they run identically on the sentinel's
ubuntu runner and on a local Windows checkout, per the predicate discipline in
`goals/README.md`. They check the CONTRACT the hub publishes outward, which is the part a
downstream consumer actually depends on — complementing `plugins-marketplace-integrity` and
`plugin-version-bump-gate`, which guard the hub-internal side of the same machine.
