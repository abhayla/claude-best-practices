"""Advisory (non-blocking) eval-coverage touch-trigger gate.

Flags a changed SKILL.md whose skill has no eval report under its sibling
evals/ dir. Warn-first by design (see plans/loop-engineering-adoption.md
Phase 1b): coverage is 4/170 core skills today, so blocking would fail
almost every skill-edit PR. Default mode emits GitHub ::warning:: annotations and
exits 0. With --enforce (the RATCHET, owner-approved 2026-07-13): a changed skill
lacking an evals/ report FAILS CI (exit 1) unless it is grandfathered in
config/eval-coverage-grandfather.yml — a shrink-only allowlist of the skills that
predate the gate. New skills must ship with evals from day one.

FRESHNESS (T-370 dod item 4, existence-is-not-freshness finding H7 — 31
SKILL.md commits since the last eval passed the "blocking" gate green): a
changed SKILL.md that HAS an evals/ report is still flagged when its own last
commit (`git log -1 --format=%ct`) is newer than every eval file's last
commit — the eval predates the behavior it claims to cover. Same warn/enforce/
grandfather semantics as the existence check above.
"""

import re
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


def _is_reference_skill(skill_dir: Path) -> bool:
    """True when the skill's frontmatter declares `type: reference`."""
    skill_md = skill_dir / "SKILL.md"
    try:
        head = skill_md.read_text(encoding="utf-8")[:2000]
    except OSError:
        return False
    return bool(re.search(r"^type:\s*reference\s*$", head, re.MULTILINE))


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
        if not skill_dir.exists():
            # Skill directory is gone entirely (a deletion/move, not an edit) —
            # nothing to evaluate, so it can't be "uncovered".
            continue
        if _is_reference_skill(skill_dir):
            # `type: reference` skills are lookup docs / plugin pointers (e.g. the #346
            # stage-2 thin pointers), not executable workflows — evals don't apply.
            # Workflow skills can't dodge the ratchet this way: entry-skill conformance
            # (test_workflow_orchestration_conformance.py) only accepts type:reference
            # for the exact /plugin-install pointer shape.
            continue
        if not _has_eval_report(skill_dir):
            results.append({
                "skill": skill_dir.name,
                "skill_md": changed_path,
                "reason": "no evals/*.md report found",
            })
    return results


def _git_commit_time(path: Path, root: Path) -> Optional[int]:
    """Unix timestamp of the last commit touching `path`, or None (no history / not a git repo)."""
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = str(path)
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    out = proc.stdout.strip()
    return int(out) if out.isdigit() else None


def stale_changed_skills(changed_files: list, root: Path) -> list:
    """Flag changed skills whose SKILL.md's last commit is newer than every eval
    file's last commit — existence of an evals/ report is not freshness (H7).

    Returns a list of {"skill", "skill_md", "reason"} dicts. Skills with no
    evals/ report at all are the EXISTENCE gate's concern (uncovered_changed_skills),
    not this one.
    """
    results = []
    for changed_path in changed_files:
        skill_dir = _skill_dir_for(changed_path, root)
        if skill_dir is None or not skill_dir.exists():
            continue
        if _is_reference_skill(skill_dir):
            continue
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            continue
        eval_files = sorted(evals_dir.glob("*.md"))
        if not eval_files:
            continue
        skill_md_time = _git_commit_time(skill_dir / "SKILL.md", root)
        if skill_md_time is None:
            continue
        newest_eval_time = max((_git_commit_time(f, root) or 0) for f in eval_files)
        if skill_md_time > newest_eval_time:
            results.append({
                "skill": skill_dir.name,
                "skill_md": changed_path,
                "reason": (
                    f"SKILL.md's last commit ({skill_md_time}) is newer than its newest "
                    f"eval's last commit ({newest_eval_time}) — the eval predates the "
                    f"current behavior"
                ),
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


def _grandfathered(root: Path) -> set:
    cfg = root / "config" / "eval-coverage-grandfather.yml"
    if not cfg.exists():
        return set()
    names = set()
    in_list = False
    for line in cfg.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("grandfathered:"):
            in_list = True
        elif in_list and s.startswith("- "):
            names.add(s[2:].strip())
    return names


def main(argv: list) -> int:
    base = None
    if "--base" in argv:
        idx = argv.index("--base")
        if idx + 1 < len(argv):
            base = argv[idx + 1]
    enforce = "--enforce" in argv

    root = Path(__file__).resolve().parent.parent
    resolved_base = _resolve_base(base)
    changed_files = _changed_files_from_git(resolved_base, root)

    if not changed_files:
        print(f"check_eval_coverage: no changed files found against {resolved_base}; skipping")
        return 0

    uncovered = uncovered_changed_skills(changed_files, root)
    stale = stale_changed_skills(changed_files, root)
    grandfathered = _grandfathered(root) if enforce else set()

    blocking = []
    for item in uncovered:
        if enforce and item["skill"] not in grandfathered:
            blocking.append(item)
            print(
                f"::error::Skill '{item['skill']}' ({item['skill_md']}) has no eval "
                f"report ({item['reason']}) — the eval-coverage ratchet blocks changed "
                f"skills without evals/ (grandfather list: config/eval-coverage-grandfather.yml, "
                f"shrink-only). Run /skill-evaluator and commit the report."
            )
        else:
            print(
                f"::warning::Skill '{item['skill']}' ({item['skill_md']}) has no eval "
                f"report ({item['reason']}) — consider running /skill-evaluator"
            )

    for item in stale:
        if enforce and item["skill"] not in grandfathered:
            blocking.append(item)
            print(
                f"::error::Skill '{item['skill']}' ({item['skill_md']}) has a STALE eval "
                f"report ({item['reason']}) — the eval-coverage freshness ratchet blocks "
                f"changed skills whose SKILL.md outran its evals/ report (grandfather list: "
                f"config/eval-coverage-grandfather.yml, shrink-only). Run /skill-evaluator "
                f"and commit a fresh report."
            )
        else:
            print(
                f"::warning::Skill '{item['skill']}' ({item['skill_md']}) has a stale eval "
                f"report ({item['reason']}) — consider running /skill-evaluator"
            )

    if blocking:
        print(f"check_eval_coverage: RATCHET FAILED — {len(blocking)} non-grandfathered changed skill(s) lack evals or are stale")
        return 1
    if uncovered or stale:
        print(
            f"check_eval_coverage: {len(uncovered)} uncovered + {len(stale)} stale "
            f"changed skill(s) (grandfathered)"
        )
    else:
        print("check_eval_coverage: all changed skills covered and fresh")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
