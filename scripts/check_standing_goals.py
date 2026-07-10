"""Standing-goal sentinel: re-verify every enrolled goals/*.md invariant.

"A goal verified once is an assumption with a timestamp." A finished deliverable is
verified once at ship time and never re-checked again — the motivating failure class
(core/.claude/rules/web-analytics-instrumentation.md) is a GA4 snippet that rendered but
silently stopped reaching the collector, unnoticed because nothing re-checked it.

Each goals/<slug>.md (see goals/README.md for the format) carries cheap read-only
predicates. This script re-evaluates every one and reports pass/fail. Run daily by
.github/workflows/standing-goals.yml (cron-only by design — never wired into PR CI).

    PYTHONPATH=. python scripts/check_standing_goals.py                      # report + exit code
    PYTHONPATH=. python scripts/check_standing_goals.py --json               # machine-readable
    PYTHONPATH=. python scripts/check_standing_goals.py --update-timestamps  # refresh last_verified on passing goals
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
GOALS_DIR = REPO_ROOT / "goals"
VALID_KINDS = {"file", "command"}


def _split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split '---\\nYAML\\n---\\nbody' into (parsed frontmatter or None, raw frontmatter block).

    Returns (None, "") when the file has no valid frontmatter fence at all.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, ""
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None, ""
    raw_fm = "".join(lines[1:end_idx])
    try:
        parsed = yaml.safe_load(raw_fm)
    except yaml.YAMLError:
        return None, raw_fm
    if not isinstance(parsed, dict):
        return None, raw_fm
    return parsed, raw_fm


def load_goal_files(goals_dir: Path = GOALS_DIR) -> list[Path]:
    """Every goals/*.md except README.md, sorted for deterministic reports."""
    if not goals_dir.exists():
        return []
    return sorted(p for p in goals_dir.glob("*.md") if p.name != "README.md")


def validate_frontmatter(fm: dict | None) -> str | None:
    """Return an error string if frontmatter is malformed, else None."""
    if fm is None:
        return "unparseable or missing frontmatter"
    if not fm.get("name"):
        return "missing required field 'name'"
    predicates = fm.get("predicates")
    if not predicates or not isinstance(predicates, list):
        return "missing or empty 'predicates' list"
    for pred in predicates:
        if not isinstance(pred, dict) or pred.get("kind") not in VALID_KINDS:
            return f"predicate has unknown kind: {pred!r}"
    return None


def evaluate_predicate(pred: dict, repo_root: Path = REPO_ROOT) -> tuple[bool, str]:
    """Evaluate one predicate. Returns (passed, reason)."""
    kind = pred.get("kind")
    if kind == "file":
        path = pred.get("path", "")
        exists = (repo_root / path).exists()
        return exists, ("" if exists else f"file not found: {path}")
    if kind == "command":
        cmd = pred.get("cmd", "")
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=repo_root, timeout=60,
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return True, ""
            detail = (result.stderr or result.stdout or "").strip().splitlines()
            reason = detail[-1] if detail else f"exit code {result.returncode}"
            return False, f"command failed ({result.returncode}): {reason}"
        except subprocess.TimeoutExpired:
            return False, "command timed out after 60s"
        except Exception as e:  # noqa: BLE001 — any predicate execution failure is a fail, not a crash
            return False, f"command raised {type(e).__name__}: {e}"
    return False, f"unknown predicate kind: {kind!r}"


def evaluate_goal(path: Path, repo_root: Path = REPO_ROOT) -> dict:
    """Evaluate a single goal file. Returns a result dict (never raises)."""
    name = path.stem
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return {"name": name, "path": str(path), "passed": False,
                "malformed": True, "error": f"could not read file: {e}",
                "predicates": [], "on_failure": "", "last_verified": None}

    fm, _raw = _split_frontmatter(text)
    error = validate_frontmatter(fm)
    if error:
        return {"name": fm.get("name", name) if fm else name, "path": str(path),
                "passed": False, "malformed": True, "error": error,
                "predicates": [], "on_failure": (fm or {}).get("on_failure", ""),
                "last_verified": (fm or {}).get("last_verified")}

    results = []
    for pred in fm["predicates"]:
        passed, reason = evaluate_predicate(pred, repo_root)
        results.append({"predicate": pred, "passed": passed, "reason": reason})

    all_passed = all(r["passed"] for r in results)
    return {
        "name": fm["name"], "path": str(path), "passed": all_passed,
        "malformed": False, "error": None, "predicates": results,
        "on_failure": fm.get("on_failure", ""), "last_verified": fm.get("last_verified"),
    }


def check_all_goals(goals_dir: Path | None = None, repo_root: Path | None = None) -> dict:
    """Evaluate every enrolled goal. Returns the full report dict.

    goals_dir/repo_root default to the module-level GOALS_DIR/REPO_ROOT, resolved at
    CALL time (not import time) so tests can monkeypatch the module globals.
    """
    goals_dir = goals_dir if goals_dir is not None else GOALS_DIR
    repo_root = repo_root if repo_root is not None else REPO_ROOT
    files = load_goal_files(goals_dir)
    goals = [evaluate_goal(f, repo_root) for f in files]
    passing = sum(1 for g in goals if g["passed"])
    return {"total": len(goals), "passing": passing, "failing": len(goals) - passing,
            "goals": goals}


def format_report(report: dict) -> str:
    lines = [
        f"Standing goals: {report['total']} total, {report['passing']} passing, "
        f"{report['failing']} failing/malformed",
    ]
    failing = [g for g in report["goals"] if not g["passed"]]
    for g in failing:
        if g["malformed"]:
            lines.append(f"  - {g['name']} — MALFORMED: {g['error']}")
            continue
        first_fail = next((p for p in g["predicates"] if not p["passed"]), None)
        reason = first_fail["reason"] if first_fail else "unknown failure"
        hint = f" — hint: {g['on_failure']}" if g["on_failure"] else ""
        holding_since = f" (holding since {g['last_verified']})" if g["last_verified"] else ""
        lines.append(f"  - {g['name']} — {reason}{hint}{holding_since}")
    return "\n".join(lines)


def update_timestamps(report: dict, today: str | None = None) -> list[Path]:
    """Rewrite last_verified to today for every PASSING goal, byte-for-byte otherwise.

    Only the `last_verified: "..."` frontmatter line is touched; everything else
    (including comments, key order, and the body) is preserved untouched.
    """
    today = today or date.today().isoformat()
    updated = []
    for g in report["goals"]:
        if not g["passed"]:
            continue
        path = Path(g["path"])
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            continue
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx is None:
            continue
        changed = False
        for i in range(1, end_idx):
            stripped = lines[i].lstrip()
            if stripped.startswith("last_verified:"):
                indent = lines[i][: len(lines[i]) - len(stripped)]
                newline = lines[i][-2:] if lines[i].endswith("\r\n") else lines[i][-1:]
                if not newline.strip() == "" or newline not in ("\n", "\r\n"):
                    newline = "\n"
                lines[i] = f'{indent}last_verified: "{today}"{newline}'
                changed = True
                break
        if changed:
            path.write_text("".join(lines), encoding="utf-8")
            updated.append(path)
    return updated


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Standing-goal invariant sentinel")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--update-timestamps", action="store_true",
                     help="rewrite last_verified to today for passing goals only")
    args = ap.parse_args(argv)

    report = check_all_goals()

    if args.update_timestamps:
        update_timestamps(report)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_report(report))

    return 1 if report["failing"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
