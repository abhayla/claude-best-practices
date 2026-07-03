"""Advisory (non-blocking) eval-coverage touch-trigger gate.

Flags a changed SKILL.md whose skill has no eval report under its sibling
evals/ dir. Warn-first by design (see plans/loop-engineering-adoption.md
Phase 1b): coverage is 4/170 core skills today, so blocking would fail
almost every skill-edit PR. This script only ever emits GitHub ::warning::
annotations and always exits 0 — it never fails CI.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

_SKILL_ROOTS = ("core/.claude/skills/", ".claude/skills/")


def _skill_dir_for(changed_path: str, root: Path) -> Optional[Path]:
    """Return the skill directory for a changed SKILL.md path, or None."""
    normalized = changed_path.replace("\\", "/")
    for prefix in _SKILL_ROOTS:
        if normalized.startswith(prefix) and normalized.endswith("/SKILL.md"):
            rest = normalized[len(prefix):-len("/SKILL.md")]
            if rest and "/" not in rest:
                return root / prefix / rest
    return None


def _has_eval_report(skill_dir: Path) -> bool:
    evals_dir = skill_dir / "evals"
    if not evals_dir.is_dir():
        return False
    return any(evals_dir.glob("*.md"))


def uncovered_changed_skills(changed_files: list, root: Path) -> list:
    """Flag changed skills whose sibling evals/ dir is absent or empty.

    Returns a list of {"skill", "skill_md", "reason"} dicts, one per
    uncovered changed skill (deduped, order-preserving).
    """
    seen = set()
    results = []
    for changed_path in changed_files:
        skill_dir = _skill_dir_for(changed_path, root)
        if skill_dir is None:
            continue
        if skill_dir in seen:
            continue
        seen.add(skill_dir)
        if not _has_eval_report(skill_dir):
            results.append({
                "skill": skill_dir.name,
                "skill_md": changed_path,
                "reason": "no evals/*.md report found",
            })
    return results


def _changed_files_from_git(base: str, root: Path) -> list:
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _resolve_base(cli_base: Optional[str]) -> str:
    if cli_base:
        return cli_base
    import os
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        return f"origin/{base_ref}"
    return "origin/main"


def main(argv: list) -> int:
    base = None
    if "--base" in argv:
        idx = argv.index("--base")
        if idx + 1 < len(argv):
            base = argv[idx + 1]

    root = Path(__file__).resolve().parent.parent
    resolved_base = _resolve_base(base)
    changed_files = _changed_files_from_git(resolved_base, root)

    if not changed_files:
        print(f"check_eval_coverage: no changed files found against {resolved_base}; skipping")
        return 0

    uncovered = uncovered_changed_skills(changed_files, root)

    for item in uncovered:
        print(
            f"::warning::Skill '{item['skill']}' ({item['skill_md']}) has no eval "
            f"report ({item['reason']}) — consider running /skill-evaluator"
        )

    if uncovered:
        print(f"check_eval_coverage: {len(uncovered)} changed skill(s) lack eval coverage")
    else:
        print("check_eval_coverage: all changed skills covered")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
