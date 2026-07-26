"""Prerequisites-contract compliance inventory (report-only).

Scans every SKILL.md in the hub (.claude/skills/), the distributable template
(core/.claude/skills/) and the plugin monorepo (plugins/*/skills/) for the
prerequisites-preflight contract landed 2026-07-26 (writing-skills §2.3b /
skill-evaluator §0.5): a `## Prerequisites` section (or explicit
`Prerequisites: none`) and, when prerequisites exist, a `## STEP 0: Preflight`
gate. Drives the wave-based sweep in plans/prereq-contract-sweep.md.

Report-only: always exits 0. A future wave-5 `--enforce` mode (owner-gated)
will turn this into the CI ratchet, mirroring check_eval_coverage.py.

Usage:
    PYTHONPATH=. python scripts/check_prereq_contract.py [--json OUT.json]
"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import yaml

TREES = [
    (".claude/skills/*/SKILL.md", "hub"),
    ("core/.claude/skills/*/SKILL.md", "core"),
    ("plugins/*/skills/*/SKILL.md", "plugin"),
]

POINTER_RE = re.compile(
    r"POINTER to the installable|no longer distributed as a copied template"
)
PREREQ_RE = re.compile(r"^##+\s*Prerequisites\b", re.M)
STEP0_RE = re.compile(r"^##+\s*STEP 0[:.]", re.M)
DEPRECATED_STUBS = {"save-session", "cc-adoption-scout"}


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _flatten_names(node) -> list:
    out = []
    if isinstance(node, dict):
        for v in node.values():
            out += _flatten_names(v)
    elif isinstance(node, list):
        for v in node:
            out += _flatten_names(v)
    elif isinstance(node, str):
        out.append(node)
    return out


def collect(root: Path) -> list:
    gf_file = root / "config" / "eval-coverage-grandfather.yml"
    grandfathered = set()
    if gf_file.exists():
        grandfathered = set(
            _flatten_names(yaml.safe_load(gf_file.read_text(encoding="utf-8")))
        )

    rows = []
    for pattern, tree in TREES:
        for p in sorted(glob.glob(str(root / pattern))):
            path = Path(p)
            text = path.read_text(encoding="utf-8")
            fm = _frontmatter(text)
            name = fm.get("name") or path.parent.name
            if not isinstance(name, str):
                name = path.parent.name
            evals = list(path.parent.glob("evals/*.md"))
            has_prereq = bool(PREREQ_RE.search(text)) or "Prerequisites: none" in text
            rows.append(
                {
                    "name": name,
                    "tree": tree,
                    "path": path.as_posix(),
                    "type": fm.get("type", "?"),
                    "version": str(fm.get("version", "?")),
                    "pointer": bool(POINTER_RE.search(text)),
                    "deprecated_stub": path.parent.name in DEPRECATED_STUBS,
                    "prereq": has_prereq,
                    "step0": bool(STEP0_RE.search(text)),
                    "grandfathered": name in grandfathered,
                    "evals": bool(evals),
                }
            )
    return rows


def main(argv: list) -> int:
    root = Path(".")
    rows = collect(root)
    if "--json" in argv:
        out = argv[argv.index("--json") + 1]
        Path(out).write_text(json.dumps(rows, indent=1), encoding="utf-8")

    exempt = [r for r in rows if r["pointer"] or r["deprecated_stub"]]
    scope = [r for r in rows if not r["pointer"] and not r["deprecated_stub"]]
    missing = [r for r in scope if not r["prereq"]]
    print(
        f"check_prereq_contract: {len(rows)} SKILL.md | exempt (pointer/deprecated): "
        f"{len(exempt)} | compliant: {len(scope) - len(missing)} | missing: {len(missing)}"
    )
    for tree in ("hub", "core", "plugin"):
        t = [r for r in missing if r["tree"] == tree]
        blocked = [
            r for r in t
            if tree != "plugin" and not r["grandfathered"] and not r["evals"]
        ]
        print(f"  {tree}: {len(t)} missing ({len(blocked)} ratchet-blocked)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
