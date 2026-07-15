"""Authoritative SKILL.md resolution for spec-conformance tests (#346 stage 2).

Since the plugins-first-only decision (owner, 2026-07-14), a plugin-covered core skill
is a thin pointer and its LIVE body ships inside a plugin. Spec tests that assert
load-bearing skill behaviors must read the authoritative body, wherever it lives —
same assertions, new SSOT path. Resolution: if the core copy is a #346 pointer
(`type: reference` + a `/plugin install` redirect), return the first plugin copy;
otherwise the core copy.
"""
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parents[2]


def resolve_skill_md(name: str) -> Path:
    core = HUB_ROOT / "core" / ".claude" / "skills" / name / "SKILL.md"
    try:
        text = core.read_text(encoding="utf-8")
    except OSError:
        return core
    if "type: reference" in text and "/plugin install" in text:
        plugins_dir = HUB_ROOT / "plugins"
        for plugin in sorted(plugins_dir.iterdir()):
            candidate = plugin / "skills" / name / "SKILL.md"
            if candidate.exists():
                return candidate
    return core
