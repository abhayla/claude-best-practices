"""Dual-home resource sync — keep .claude/ (hub) and core/.claude/ (distributable) in lockstep.

A "dual-home" resource lives in BOTH .claude/<kind>/ and core/.claude/<kind>/. The manifest
(config/dual-home-resources.yml) declares each as `synced` (must stay identical) or `divergent`
(intentionally differs, with a reason). This module is the SSOT for discovery + comparison; the
CI gate (scripts/tests/test_dual_home_sync.py) imports it.

CLI:
    python scripts/sync_dual_home.py --check                  # drift report (exit 1 on drift)
    python scripts/sync_dual_home.py --sync <name> --from hub # copy hub -> core for one resource
    python scripts/sync_dual_home.py --sync <name> --from core# copy core -> hub for one resource
    python scripts/sync_dual_home.py --list                   # list every dual-home resource + class
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

from scripts.dedup_check import hash_pattern

# Fences that mark a region as specific to one side of a `shared` resource. They work in any
# comment style (bash `#`, markdown `<!-- -->`) because we match the token anywhere in the line.
_OPEN = re.compile(r"DUAL-SYNC:(HUB|DOWNSTREAM)-ONLY")
_END = re.compile(r"DUAL-SYNC:END")


def strip_specific(text: str) -> str:
    """Drop every DUAL-SYNC:*-ONLY ... DUAL-SYNC:END block, returning the SHARED skeleton."""
    out, skip = [], False
    for line in text.splitlines():
        if _OPEN.search(line):
            skip = True
            continue
        if _END.search(line):
            skip = False
            continue
        if not skip:
            out.append(line)
    return "\n".join(out)


def _norm(text: str) -> str:
    """Same normalization dedup_check uses (strip lines, collapse runs of spaces)."""
    lines = [ln.strip() for ln in text.splitlines()]
    return re.sub(r"  +", " ", "\n".join(lines))


def fence_problems(text: str) -> list[str]:
    """Malformed fences that make strip_specific() unreliable (an unclosed OPEN silently swallows the
    rest of the file → could mask drift). Flags: orphaned END, nested OPEN, or unclosed OPEN."""
    problems, depth, open_line = [], 0, 0
    for i, line in enumerate(text.splitlines(), 1):
        if _OPEN.search(line):
            if depth:
                problems.append(f"line {i}: nested DUAL-SYNC fence (one already open at line {open_line})")
            depth += 1
            open_line = i
        elif _END.search(line):
            if depth == 0:
                problems.append(f"line {i}: DUAL-SYNC:END with no open fence")
            else:
                depth -= 1
    if depth:
        problems.append(f"unclosed DUAL-SYNC fence opened at line {open_line} (missing DUAL-SYNC:END)")
    return problems


def stray_side_markers(text: str, side: str) -> list[str]:
    """A hub file must carry no DOWNSTREAM-ONLY fences (and vice versa) — that would intermingle."""
    forbidden = "DOWNSTREAM" if side == "hub" else "HUB"
    return [ln.strip() for ln in text.splitlines() if f"DUAL-SYNC:{forbidden}-ONLY" in ln]

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / ".claude"
CORE = ROOT / "core" / ".claude"
MANIFEST = ROOT / "config" / "dual-home-resources.yml"
KINDS = ("agents", "skills", "rules", "hooks")


def _cmp_file(kind: str, base: Path, name: str) -> Path:
    """The comparable file for a resource (skills compare their SKILL.md; others the file itself)."""
    return base / kind / name / "SKILL.md" if kind == "skills" else base / kind / name


def discover() -> list[dict]:
    """Every resource present in BOTH hub and core, with its comparable files."""
    found = []
    for kind in KINDS:
        hub_kind = HUB / kind
        if not hub_kind.exists():
            continue
        for item in sorted(hub_kind.iterdir()):
            if item.name.startswith("."):
                continue
            name = item.name
            hub_cmp, core_cmp = _cmp_file(kind, HUB, name), _cmp_file(kind, CORE, name)
            if hub_cmp.exists() and core_cmp.exists():
                entry = {"kind": kind, "name": name, "hub": hub_cmp, "core": core_cmp}
                if kind == "skills":  # skills carry references/ + templates/ beyond SKILL.md
                    entry["hub_dir"] = HUB / kind / name
                    entry["core_dir"] = CORE / kind / name
                found.append(entry)
    return found


def _rel_files(base: Path) -> dict:
    """All non-SKILL.md files under a skill dir, keyed by relative path."""
    return {p.relative_to(base).as_posix(): p
            for p in base.rglob("*") if p.is_file() and p.name != "SKILL.md"}


def extra_file_problems(res: dict) -> list[str]:
    """For a skill: every file beyond SKILL.md (references/, templates/) must match across copies."""
    if not res.get("hub_dir"):
        return []
    hub, core = _rel_files(res["hub_dir"]), _rel_files(res["core_dir"])
    problems = []
    for rel in sorted(set(hub) | set(core)):
        if rel not in hub:
            problems.append(f"only in core: {rel}")
        elif rel not in core:
            problems.append(f"only in hub: {rel}")
        elif hash_pattern(str(hub[rel])) != hash_pattern(str(core[rel])):
            problems.append(f"differs: {rel}")
    return problems


def load_manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}


def classify(kind: str, name: str, manifest: dict) -> str | None:
    """Return 'synced', 'shared', 'divergent', or None (unclassified)."""
    if name in (manifest.get("synced", {}) or {}).get(kind, []) or []:
        return "synced"
    if name in (manifest.get("shared", {}) or {}).get(kind, []) or []:
        return "shared"
    if name in (manifest.get("divergent", {}) or {}).get(kind, {}) or {}:
        return "divergent"
    return None


def in_sync(res: dict) -> bool:
    return hash_pattern(str(res["hub"])) == hash_pattern(str(res["core"]))


def _skeleton(text: str) -> str:
    """Shared skeleton: drop fenced regions + blank lines, then normalize (blanks aren't logic)."""
    body = strip_specific(text)
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    return re.sub(r"  +", " ", "\n".join(lines))


def shared_in_sync(res: dict) -> bool:
    """For a `shared` resource: the skeleton (everything outside the fenced regions) must match."""
    return _skeleton(res["hub"].read_text(encoding="utf-8")) == _skeleton(res["core"].read_text(encoding="utf-8"))


def intermingle_problems(res: dict) -> list[str]:
    """Stray fences: a DOWNSTREAM-ONLY block in the hub file, or HUB-ONLY in core, is intermingling."""
    return (stray_side_markers(res["hub"].read_text(encoding="utf-8"), "hub")
            + stray_side_markers(res["core"].read_text(encoding="utf-8"), "core"))


def check() -> dict:
    """Drift report: unclassified, drifted, intermingled, and malformed (bad fences)."""
    manifest = load_manifest()
    resources = discover()
    unclassified, drifted, intermingled, malformed, ok = [], [], [], [], []
    for r in resources:
        cls = classify(r["kind"], r["name"], manifest)
        if cls is None:
            unclassified.append(r)
        elif cls == "synced":
            # primary file identical AND every references/ file identical
            (ok if (in_sync(r) and not extra_file_problems(r)) else drifted).append(r)
        elif cls == "shared":
            # Validate fences FIRST — a malformed fence makes the skeleton compare unreliable
            # (an unclosed OPEN swallows the rest of the file → could silently hide drift).
            fp = (fence_problems(r["hub"].read_text(encoding="utf-8"))
                  + fence_problems(r["core"].read_text(encoding="utf-8")))
            if fp:
                malformed.append({**r, "problems": fp})
            elif intermingle_problems(r):
                intermingled.append(r)
            elif not shared_in_sync(r) or extra_file_problems(r):
                drifted.append(r)
            else:
                ok.append(r)
        else:  # divergent
            ok.append(r)
    return {"resources": resources, "unclassified": unclassified, "drifted": drifted,
            "intermingled": intermingled, "malformed": malformed, "ok": ok}


def sync_one(name: str, direction: str) -> int:
    """Copy one resource from one side to the other (ONLY safe for `synced` resources)."""
    matches = [r for r in discover() if r["name"] == name]
    if not matches:
        print(f"ERROR: '{name}' is not a dual-home resource (not present in both trees).")
        return 1
    r = matches[0]
    cls = classify(r["kind"], r["name"], load_manifest())
    if cls in ("shared", "divergent"):
        print(f"REFUSED: '{name}' is `{cls}` — a blind copy would CLOBBER the other side's "
              f"{'fenced specific regions' if cls == 'shared' else 'intentional differences'}. "
              f"Edit both sides by hand (shared: keep the skeleton identical; only the fenced bits differ).")
        return 1
    other = "core" if direction == "hub" else "hub"
    if r.get("hub_dir"):  # skill — mirror the WHOLE dir (SKILL.md + references/ + templates/)
        src_dir, dst_dir = (r["hub_dir"], r["core_dir"]) if direction == "hub" else (r["core_dir"], r["hub_dir"])
        shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
    else:
        src, dst = (r["hub"], r["core"]) if direction == "hub" else (r["core"], r["hub"])
        shutil.copyfile(src, dst)
    print(f"synced {r['kind']}/{name}: {direction} -> {other}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Dual-home (.claude <-> core/.claude) sync.")
    ap.add_argument("--check", action="store_true", help="report drift (exit 1 if any)")
    ap.add_argument("--list", action="store_true", help="list every dual-home resource + class")
    ap.add_argument("--sync", metavar="NAME", help="copy one resource between hub and core")
    ap.add_argument("--from", dest="direction", choices=("hub", "core"), help="source side for --sync")
    args = ap.parse_args(argv)

    if args.sync:
        if not args.direction:
            print("ERROR: --sync requires --from hub|core")
            return 2
        return sync_one(args.sync, args.direction)

    if args.list:
        manifest = load_manifest()
        for r in discover():
            print(f"  [{classify(r['kind'], r['name'], manifest) or 'UNCLASSIFIED'}] {r['kind']}/{r['name']}")
        return 0

    # default: --check
    rep = check()
    print(f"dual-home resources: {len(rep['resources'])}  (ok: {len(rep['ok'])}, "
          f"drifted: {len(rep['drifted'])}, intermingled: {len(rep['intermingled'])}, "
          f"malformed: {len(rep['malformed'])}, unclassified: {len(rep['unclassified'])})")
    for r in rep["unclassified"]:
        print(f"  UNCLASSIFIED: {r['kind']}/{r['name']} — add to config/dual-home-resources.yml (synced|shared|divergent)")
    for r in rep["malformed"]:
        print(f"  MALFORMED FENCES: {r['kind']}/{r['name']} — {'; '.join(r['problems'])}")
    for r in rep["drifted"]:
        print(f"  DRIFTED (shared/synced part differs): {r['kind']}/{r['name']} — "
              f"reconcile: python scripts/sync_dual_home.py --sync {r['name']} --from hub|core")
    for r in rep["intermingled"]:
        print(f"  INTERMINGLED: {r['kind']}/{r['name']} — a HUB-ONLY fence in core (or DOWNSTREAM-ONLY in hub); "
              f"move the block to the correct side")
    bad = rep["unclassified"] or rep["drifted"] or rep["intermingled"] or rep["malformed"]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
