"""Generate the root-level .claude-plugin/marketplace.json from plugins/.claude-plugin/marketplace.json.

Claude Code's GitHub-URL/owner-shorthand marketplace-add forms
(`claude plugin marketplace add <owner>/<repo>`) only look for
`.claude-plugin/marketplace.json` at the repository ROOT, and once fetched that way
the marketplace has no local copy to resolve relative plugin `source` paths against.

`plugins/.claude-plugin/marketplace.json` stays the single source of truth (every
script, goal, and doc already points at it). This script derives a root mirror with
each plugin's `source` rewritten from `./<name>` to `./plugins/<name>` so it resolves
correctly when Claude Code clones the whole repo for a GitHub-URL marketplace add.

Usage:
    python scripts/generate_root_marketplace.py            # write/update the root mirror
    python scripts/generate_root_marketplace.py --check     # exit 1 if the root mirror is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_MARKETPLACE_PATH = REPO_ROOT / "plugins" / ".claude-plugin" / "marketplace.json"
ROOT_MARKETPLACE_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

GENERATED_NOTICE = (
    "GENERATED FILE — do not hand-edit. Derived from plugins/.claude-plugin/marketplace.json "
    "by scripts/generate_root_marketplace.py so the GitHub-URL marketplace-add form "
    "(`claude plugin marketplace add <owner>/<repo>`) resolves plugin sources correctly. "
    "Edit the source file and re-run the generator."
)


def derive_root_marketplace(source: dict[str, Any]) -> dict[str, Any]:
    root = json.loads(json.dumps(source))  # deep copy
    root["metadata"] = dict(root.get("metadata", {}))
    root["metadata"]["_generated"] = GENERATED_NOTICE
    for plugin in root.get("plugins", []):
        rel = plugin.get("source", "")
        if rel.startswith("./"):
            rel = rel[2:]
        plugin["source"] = f"./plugins/{rel}"
    return root


def render(marketplace: dict[str, Any]) -> str:
    return json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the root marketplace.json is missing or out of sync; write nothing.",
    )
    args = parser.parse_args()

    if not SOURCE_MARKETPLACE_PATH.is_file():
        print(f"ERROR: source marketplace not found at {SOURCE_MARKETPLACE_PATH}", file=sys.stderr)
        return 1

    with open(SOURCE_MARKETPLACE_PATH, encoding="utf-8") as f:
        source = json.load(f)

    derived = derive_root_marketplace(source)
    rendered = render(derived)

    if args.check:
        if not ROOT_MARKETPLACE_PATH.is_file():
            print(f"STALE: {ROOT_MARKETPLACE_PATH} does not exist — run scripts/generate_root_marketplace.py", file=sys.stderr)
            return 1
        current = ROOT_MARKETPLACE_PATH.read_text(encoding="utf-8")
        if current != rendered:
            print(
                f"STALE: {ROOT_MARKETPLACE_PATH} is out of sync with {SOURCE_MARKETPLACE_PATH} "
                "— run scripts/generate_root_marketplace.py",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {ROOT_MARKETPLACE_PATH} is in sync")
        return 0

    ROOT_MARKETPLACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROOT_MARKETPLACE_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {ROOT_MARKETPLACE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
