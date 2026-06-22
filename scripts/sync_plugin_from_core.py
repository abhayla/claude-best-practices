"""Keep the prompt-auto-enhance plugin's mirrored files in sync with core/.

SSOT decision (plans/prompt-auto-enhance-plugin.md): core/.claude/ is the single
source of truth; the plugin's skill + rule are GENERATED from core, not hand-edited.
This script enforces that contract so the two copies can never silently drift.

The plugin is NOT a byte-for-byte copy of core — only the "generated from core"
artifacts are mirrored. Plugin-specific files (plugin.json, hooks.json, the
settings-driven hook, enhance-settings.default.json, commands/, README.md) are
intentionally divergent and are NOT covered here.

Comparison normalizes line endings (CRLF/LF), so a Windows checkout that rewrites
endings is not flagged as drift; content is what matters.

Usage:
    python scripts/sync_plugin_from_core.py --check   # gate: exit 1 on drift
    python scripts/sync_plugin_from_core.py --sync    # regenerate plugin from core
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_SKILL = ROOT / "core" / ".claude" / "skills" / "prompt-auto-enhance"
CORE_RULE = ROOT / "core" / ".claude" / "rules" / "prompt-auto-enhance-rule.md"
PLUGIN = ROOT / "plugins" / "prompt-auto-enhance"
PLUGIN_SKILL = PLUGIN / "skills" / "prompt-auto-enhance"

# Mirror map: core source -> plugin destination. Every entry MUST stay
# content-identical (line-endings normalized). Add a row when a new generated
# artifact is introduced; never list a plugin-specific file here.
MIRROR: list[tuple[Path, Path]] = [
    (CORE_RULE, PLUGIN / "prompt-auto-enhance-rule.md"),
    (CORE_SKILL / "SKILL.md", PLUGIN_SKILL / "SKILL.md"),
]
for _ref in sorted((CORE_SKILL / "references").glob("*.md")):
    MIRROR.append((_ref, PLUGIN_SKILL / "references" / _ref.name))


def _norm(p: Path) -> str:
    """Read text with line endings normalized to LF for content comparison."""
    return p.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def check() -> list[str]:
    """Return a list of human-readable drift problems (empty == in sync)."""
    problems: list[str] = []
    for src, dst in MIRROR:
        if not src.exists():
            problems.append(f"missing core source: {src.relative_to(ROOT)}")
            continue
        if not dst.exists():
            problems.append(f"missing plugin mirror: {dst.relative_to(ROOT)}")
            continue
        if _norm(src) != _norm(dst):
            problems.append(
                f"content drift: {dst.relative_to(ROOT)} != {src.relative_to(ROOT)}"
            )
    return problems


def sync() -> list[Path]:
    """Overwrite each plugin mirror with its core source (LF). Returns changed files."""
    changed: list[Path] = []
    for src, dst in MIRROR:
        if not src.exists():
            raise FileNotFoundError(f"core source missing: {src}")
        content = _norm(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or _norm(dst) != content:
            dst.write_text(content, encoding="utf-8", newline="\n")
            changed.append(dst)
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="fail on drift (CI gate)")
    g.add_argument("--sync", action="store_true", help="regenerate plugin from core")
    args = ap.parse_args()

    if args.check:
        problems = check()
        if problems:
            print("Plugin is OUT OF SYNC with core (SSOT). Run --sync to fix:")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"Plugin mirrors core: {len(MIRROR)} files in sync.")
        return 0

    changed = sync()
    if changed:
        print(f"Synced {len(changed)} file(s) from core:")
        for c in changed:
            print(f"  - {c.relative_to(ROOT)}")
    else:
        print("Already in sync — nothing to do.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
