"""Regression guard: README must not hardcode a stale hub pattern/skill count.

The README front page is the hub's own canonical self-description, so a
"N patterns / N skills / N agents / N rules" claim there is a claim about THIS
hub and MUST match registry/patterns.json (the source of truth). Manual
hardcoded counts drifted three times (229/155/225 vs live) before being made
pointer-style; this guard keeps them honest.

Scope is deliberately README.md ONLY — other docs legitimately cite other
projects' counts, dated research, and illustrative examples, which must NOT be
flagged.
"""
import json
import re
import pathlib

HUB = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = json.loads((HUB / "registry" / "patterns.json").read_text(encoding="utf-8"))

_PATTERNS = {k: v for k, v in REGISTRY.items() if k != "_meta" and isinstance(v, dict)}


def _live_counts():
    by_type = {"patterns": len(_PATTERNS)}
    for t, label in (("skill", "skills"), ("agent", "agents"), ("rule", "rules")):
        by_type[label] = sum(1 for v in _PATTERNS.values() if v.get("type") == t)
    return by_type


def test_readme_hub_counts_match_registry():
    readme = (HUB / "README.md").read_text(encoding="utf-8")
    counts = _live_counts()
    stale = []
    for m in re.finditer(r"\b(\d+)\s+(patterns|skills|agents|rules)\b", readme):
        claimed, label = int(m.group(1)), m.group(2)
        live = counts[label]
        if claimed != live:
            stale.append(f'"{m.group(0)}" but live {label}={live}')
    assert not stale, (
        "README.md hardcodes a hub count that disagrees with registry/patterns.json "
        f"({stale}). Use the pointer pattern (reference registry/patterns.json) "
        "instead of a hardcoded number, or update the number."
    )
