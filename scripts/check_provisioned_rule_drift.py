"""Provisioned-rule drift report — mechanism for the "rule-drift" lesson class.

The lesson (MECHANISM-DUE 2026-08-27): `.claude/rules/workflow.md` was fixed in the hub on
2026-07-03 (commit 8e4c4c3d, "resolve audit issues #281, #286, #289, #284 (#294)"), but a
downstream project that copied the OLD (pre-fix) file at provision time keeps carrying the
contradictory copy forever — nothing ever re-diffs a provisioned rule against the hub after
day one. Rules cannot ship in plugins (see docs/SYNC-ARCHITECTURE.md), so a copy is the only
delivery mechanism there is, and a copy silently rots. This script is the detector: for every
registered repo's `.claude/rules/*.md`, it classifies the copy against the hub's own history.

Classification (per file):
    CURRENT       — hash equals the pattern's CURRENT hash in registry/patterns.json.
    STALE         — hash equals some OLDER hub version of the same file (found by walking
                    `core/.claude/rules/<file>`'s git history, capped at the last 30 commits
                    per file for speed — a deeper rewrite predates that cap and is reported
                    as MODIFIED instead of walked further; a row hitting the cap exactly says
                    so via its `note`). Reports the hub commit the project is stuck on. If ANY
                    later hub commit on that file (not just the one immediately after — the
                    whole chain up to HEAD) has a message matching the fix/resolve/contradict
                    wording heuristic, the row is additionally flagged as a CONTRADICTION
                    candidate — a commit-message keyword match, not a verified causal link.
    MODIFIED      — matches no hub version at all: a deliberate project customization.
    RETIRED       — no hub twin file EXISTS, but the hub git history shows one used to and
                    was DELETED (`git log --diff-filter=D`) — the project is still enforcing
                    a rule the hub itself removed. Checked and reported before PROJECT-ONLY;
                    this is worse drift than a harmless local addition, not the same thing.
    PROJECT-ONLY  — no hub twin file exists, and the hub never had one either (a genuine
                    project-local rule).
    UNKNOWN       — the hub's own git history for this file could not be read (git failure,
                    not "no older versions exist" — those two must never be conflated).
    NOTE          — the file (or a lookup needed to classify it) could not be read; never
                    silently reported as a 0 or folded into another status.

Design rules (same spirit as measure_outcomes.py / feature_utilization.py):
  1. REPORT, never judge — no pass/fail, no auto-fix. Exit code is always 0.
  2. READ-ONLY. No files written outside the optional weekly cache under rule-drift/.
  3. "Unreadable"/"unknown" is said out loud as its own status or a note, never folded
     into a silent 0/CURRENT/MODIFIED.
  4. Hashing reuses dedup_check.hash_content (T-401 split of hash_pattern) so a STALE/CURRENT
     verdict here always agrees with the registry's own dedup hash — one hashing algorithm,
     not two that could quietly drift apart from each other.
  5. Every git/subprocess call carries a timeout (SUBPROCESS_TIMEOUT_SECONDS) and the whole
     scan carries a soft wall-clock deadline (DEFAULT_SCAN_DEADLINE_SECONDS, same pattern as
     cost_ledger.py's `deadline`) — a hung git process or a huge repo_registry must degrade to
     a NOTE naming what was skipped, never hang the caller (this runs from a SessionStart
     hook).

Repo registry SSOT: D:/Abhay/GetWorkDone/settings.json -> repo_registry (values are paths;
the `_doc` key is skipped). A missing settings.json or a missing repo path is a NOTE, never
a crash or a silent 0 — this script runs both on this PC (real fleet data) and in hub CI
(where that path does not exist at all).

Working-tree disclosure (T-401 review finding 1): every repo's rows are read off whatever
branch that repo's worktree happens to be checked out to right now, which may not be its
default branch and may be ahead/behind its upstream — a report that does not say so can
silently describe a feature branch as if it were the project's mainline. Each repo section
therefore opens with a "read: working tree @ <branch> (ahead N / behind M of <upstream>)"
line, plus a NOTE when the branch is not the repo's default branch or is behind upstream.

CLI:
    python scripts/check_provisioned_rule_drift.py [--json] [--settings PATH]
        [--repo NAME ...] [--history-cap N] [--deadline-seconds N] [--weekly]

    --weekly: skip the scan entirely if the cache (rule-drift/.last-run.json, gitignored)
    shows a run within the last 7 days; otherwise run and refresh the cache. Always prints
    the one-line summary `rule-drift: N stale across M repos` last, for hooks to `tail -1`.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dedup_check import hash_content, hash_pattern  # noqa: E402

DEFAULT_SETTINGS_PATH = Path(r"D:/Abhay/GetWorkDone/settings.json")
CACHE_PATH = ROOT / "rule-drift" / ".last-run.json"
WEEKLY_SECONDS = 7 * 24 * 60 * 60

SUBPROCESS_TIMEOUT_SECONDS = 15
DEFAULT_SCAN_DEADLINE_SECONDS = 60

# Word-boundary keyword heuristic (T-401 review finding 5) — a plain fix|contradict|resolve
# alternation substring-matches inside words like "suffix" and "fixture", producing
# false-positive CONTRADICTION flags. \b keeps it to whole-word fix/fixes/fixed,
# resolve/resolved/resolves/resolving, contradict*.
CONTRADICTION_RE = re.compile(r"\b(fix(e[sd])?|resolv(e[sd]?|ing)|contradict\w*)\b", re.IGNORECASE)

# Sentinel distinguishing "checked the hub's deletion history, found nothing" (None) from
# "could not check it" (timeout/git error) — conflating the two would silently misreport a
# genuine PROJECT-ONLY file as RETIRED-unconfirmed, or worse, as PROJECT-ONLY outright.
DELETION_CHECK_FAILED = object()

HistoryProvider = Callable[[str], Optional[list]]
DeletionProvider = Callable[[str], object]
GitStateProvider = Callable[[Path], dict]


# --------------------------------------------------------------------------------------
# Pure classification (no git, no disk — fully unit-testable)
# --------------------------------------------------------------------------------------

def classify_rule_copy(project_content: str, hub_current_hash: str, history: Optional[list]) -> dict:
    """Classify one project rule copy against the hub's current hash + capped history.

    `history` is newest-first and includes the commit that produced the CURRENT hub content
    as entry 0 (matches `git log --format=... -- <file>` output verbatim) — real callers get
    this from get_hub_rule_history(); tests inject a plain list of
    (sha, commit_date, message, content) tuples built by hand.

    `history is None` means the hub's git history could not be read at all (a real failure,
    not "no older versions exist") -> UNKNOWN, never silently folded into MODIFIED.
    """
    project_hash = hash_content(project_content)
    if project_hash == hub_current_hash:
        return {"status": "CURRENT"}

    if history is None:
        return {"status": "UNKNOWN", "note": "hub git history unavailable for this file"}

    for i, (sha, commit_date, _msg, content) in enumerate(history):
        if hash_content(content) != project_hash:
            continue
        # Contradiction check: ANY commit newer than this stale version (i.e. any commit the
        # hub made on this file between here and HEAD) whose message reads as a deliberate
        # fix means the project is stuck on pre-fix content. Scan from the commit
        # immediately after the stale one forward to HEAD (index i-1 down to 0) so the
        # reported "changed_by" commit is the one CLOSEST to the stale point that actually
        # reads as a fix, not just the very latest commit on the file.
        contradiction = False
        changed_by_sha = None
        changed_by_msg = None
        for j in range(i - 1, -1, -1):
            newer_sha, _newer_date, newer_msg, _newer_content = history[j]
            if CONTRADICTION_RE.search(newer_msg):
                contradiction = True
                changed_by_sha, changed_by_msg = newer_sha, newer_msg
                break
        return {
            "status": "STALE",
            "hub_commit_sha": sha,
            "hub_commit_date": commit_date,
            "contradiction": contradiction,
            "changed_by_sha": changed_by_sha,
            "changed_by_msg": changed_by_msg,
        }

    return {"status": "MODIFIED"}


# --------------------------------------------------------------------------------------
# Real git providers (thin — the pure functions above do all the reasoning)
# --------------------------------------------------------------------------------------

def get_hub_rule_history(
    filename: str,
    hub_root: Path = ROOT,
    cap: int = 30,
    timeout: float = SUBPROCESS_TIMEOUT_SECONDS,
) -> Optional[list]:
    """Newest-first (sha, commit_date, message, content) for core/.claude/rules/<filename>.

    Capped at the last `cap` commits touching the file (speed — a file with a longer rewrite
    history than that is reported as MODIFIED rather than walked further; callers should note
    the cap when presenting results, per the DoD). Returns None on a git failure or timeout
    (no repo, detached history, a hung process, etc.) so callers can report UNKNOWN instead of
    treating an empty list as "no older versions exist".
    """
    rel = f"core/.claude/rules/{filename}"
    try:
        log = subprocess.run(
            ["git", "-C", str(hub_root), "log", f"-n{cap}", "--format=%H%x1f%cs%x1f%s", "--", rel],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    if log.returncode != 0:
        return None

    history = []
    for line in log.stdout.splitlines():
        parts = line.split("\x1f", 2)
        if len(parts) != 3:
            continue
        sha, commit_date, msg = parts
        try:
            show = subprocess.run(
                ["git", "-C", str(hub_root), "show", f"{sha}:{rel}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            continue  # skip this one version; not fatal to the whole history walk
        if show.returncode != 0:
            continue  # file didn't exist yet at this commit — nothing to hash
        history.append((sha, commit_date, msg, show.stdout))
    return history


def get_hub_rule_deletion(
    filename: str,
    hub_root: Path = ROOT,
    timeout: float = SUBPROCESS_TIMEOUT_SECONDS,
):
    """The most recent commit that DELETED core/.claude/rules/<filename>, if any.

    Returns (sha, commit_date, message) on a hit, None when the hub never had-then-deleted
    this file, or DELETION_CHECK_FAILED on a git error/timeout — the caller must not treat a
    failed check the same as a confirmed "never existed".
    """
    rel = f"core/.claude/rules/{filename}"
    try:
        res = subprocess.run(
            ["git", "-C", str(hub_root), "log", "--diff-filter=D", "-n1", "--format=%H%x1f%cs%x1f%s", "--", rel],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return DELETION_CHECK_FAILED
    if res.returncode != 0:
        return DELETION_CHECK_FAILED
    line = res.stdout.strip()
    if not line:
        return None
    parts = line.split("\x1f", 2)
    if len(parts) != 3:
        return DELETION_CHECK_FAILED
    sha, commit_date, msg = parts
    return (sha, commit_date, msg)


_BRANCH_STATUS_RE = re.compile(r"^## (?P<local>[^.\[]+?)(\.\.\.(?P<upstream>\S+))?(\s+\[(?P<tracking>[^\]]+)\])?\s*$")


def get_repo_git_state(repo_path: Path, timeout: float = SUBPROCESS_TIMEOUT_SECONDS) -> dict:
    """Which branch a repo's working tree is actually checked out to, and how it compares
    to its upstream — the disclosure this report was silently missing (review finding 1).
    Returns {"error": str} on any git failure/timeout instead of guessing.
    """

    def run(args):
        return subprocess.run(
            ["git", "-C", str(repo_path)] + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )

    try:
        branch_res = run(["rev-parse", "--abbrev-ref", "HEAD"])
        status_res = run(["status", "-sb"])
        default_res = run(["symbolic-ref", "refs/remotes/origin/HEAD"])
    except subprocess.TimeoutExpired:
        return {"error": "git state read timed out"}

    if branch_res.returncode != 0 or status_res.returncode != 0:
        return {"error": "git state unreadable (rev-parse/status failed)"}

    branch = branch_res.stdout.strip()
    header = status_res.stdout.splitlines()[0] if status_res.stdout.strip() else ""
    upstream, ahead, behind = None, 0, 0
    m = _BRANCH_STATUS_RE.match(header)
    if m:
        upstream = m.group("upstream")
        tracking = m.group("tracking") or ""
        am = re.search(r"ahead (\d+)", tracking)
        bm = re.search(r"behind (\d+)", tracking)
        ahead = int(am.group(1)) if am else 0
        behind = int(bm.group(1)) if bm else 0

    default_branch = None
    if default_res.returncode == 0 and default_res.stdout.strip():
        default_branch = default_res.stdout.strip().rsplit("/", 1)[-1]

    notes = []
    if default_branch and branch != default_branch:
        notes.append(f"not on default branch (default={default_branch})")
    if behind:
        notes.append(f"behind upstream by {behind}")

    return {
        "branch": branch,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "default_branch": default_branch,
        "notes": notes,
    }


# --------------------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------------------

def _load_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def analyze_repo(
    repo_path: Path,
    hub_root: Path,
    registry: dict,
    history_cache: dict,
    history_provider: HistoryProvider,
    deletion_cache: dict,
    deletion_provider: DeletionProvider,
    history_cap: int,
) -> list:
    rules_dir = repo_path / ".claude" / "rules"
    if not rules_dir.is_dir():
        return []  # no provisioned rules at all — not an error, not a NOTE

    rows = []
    for rule_file in sorted(rules_dir.glob("*.md")):
        filename = rule_file.name
        try:
            project_content = rule_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            rows.append({"file": filename, "status": "NOTE", "note": f"unreadable: {exc}"})
            continue

        pattern_name = filename[:-3] if filename.endswith(".md") else filename
        reg_entry = registry.get(pattern_name) if registry else None
        core_file = hub_root / "core" / ".claude" / "rules" / filename

        if reg_entry and reg_entry.get("type") == "rule" and "hash" in reg_entry:
            hub_hash = reg_entry["hash"]
        elif core_file.is_file():
            hub_hash = hash_pattern(str(core_file))
        else:
            # No hub twin TODAY — but before calling it a harmless project-local rule, check
            # whether the hub used to have one and deleted it. A project still enforcing a
            # retired rule is the worst kind of drift, not the most benign (review finding 2).
            if filename not in deletion_cache:
                deletion_cache[filename] = deletion_provider(filename)
            deletion = deletion_cache[filename]
            if deletion is DELETION_CHECK_FAILED:
                rows.append({
                    "file": filename,
                    "status": "NOTE",
                    "note": "could not check hub deletion history (timeout/error)",
                })
            elif deletion:
                sha, commit_date, msg = deletion
                rows.append({
                    "file": filename,
                    "status": "RETIRED",
                    "note": f"hub deleted it on {commit_date} ({sha[:10]}): {msg}",
                })
            else:
                rows.append({"file": filename, "status": "PROJECT-ONLY"})
            continue

        if filename not in history_cache:
            history_cache[filename] = history_provider(filename)
        history = history_cache[filename]

        result = classify_rule_copy(project_content, hub_hash, history)
        result["file"] = filename
        if history is not None and len(history) == history_cap:
            trunc_note = "history truncated at cap"
            result["note"] = f"{result['note']}; {trunc_note}" if result.get("note") else trunc_note
        rows.append(result)

    return rows


def build_report(
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    hub_root: Path = ROOT,
    history_provider: Optional[HistoryProvider] = None,
    deletion_provider: Optional[DeletionProvider] = None,
    git_state_provider: Optional[GitStateProvider] = None,
    history_cap: int = 30,
    repo_filter: Optional[list] = None,
    deadline_seconds: Optional[float] = DEFAULT_SCAN_DEADLINE_SECONDS,
) -> dict:
    if history_provider is None:
        history_provider = lambda filename: get_hub_rule_history(filename, hub_root, history_cap)  # noqa: E731
    if deletion_provider is None:
        deletion_provider = lambda filename: get_hub_rule_deletion(filename, hub_root)  # noqa: E731
    if git_state_provider is None:
        git_state_provider = get_repo_git_state

    notes = []
    settings = _load_json(settings_path)
    if settings is None:
        notes.append(f"repo registry not found or unreadable: {settings_path}")
        return {"repos": [], "notes": notes, "history_cap": history_cap}

    registry = _load_json(hub_root / "registry" / "patterns.json") or {}

    repo_registry = settings.get("repo_registry", {})
    history_cache: dict = {}
    deletion_cache: dict = {}
    repos_report = []

    # Soft wall-clock deadline (same pattern as cost_ledger.py's `deadline`) — a hung git
    # process or a large repo_registry must degrade to a named-skip NOTE, never hang the
    # SessionStart hook this is wired into (review finding 4).
    deadline = time.monotonic() + deadline_seconds if deadline_seconds else None
    skipped_repos = []

    for repo_name, repo_cfg in repo_registry.items():
        if repo_name == "_doc":
            continue
        if repo_filter and repo_name not in repo_filter:
            continue

        if deadline is not None and time.monotonic() >= deadline:
            skipped_repos.append(repo_name)
            continue

        path_str = repo_cfg.get("path") if isinstance(repo_cfg, dict) else None
        if not path_str:
            notes.append(f"{repo_name}: no 'path' in repo_registry entry")
            repos_report.append({"repo": repo_name, "rows": [], "note": "no path configured", "git_state": None})
            continue
        repo_path = Path(path_str)
        if not repo_path.is_dir():
            note = f"path not found: {path_str}"
            notes.append(f"{repo_name}: {note}")
            repos_report.append({"repo": repo_name, "rows": [], "note": note, "git_state": None})
            continue

        git_state = git_state_provider(repo_path)
        rows = analyze_repo(
            repo_path, hub_root, registry, history_cache, history_provider,
            deletion_cache, deletion_provider, history_cap,
        )
        repos_report.append({"repo": repo_name, "rows": rows, "note": None, "git_state": git_state})

    if skipped_repos:
        notes.append(
            f"scan time budget ({deadline_seconds}s) hit — skipped repos: {', '.join(skipped_repos)}"
        )

    return {"repos": repos_report, "notes": notes, "history_cap": history_cap}


# --------------------------------------------------------------------------------------
# Weekly cache (gitignored) — used only by the auto-pr-reconcile.sh wiring
# --------------------------------------------------------------------------------------

def _cache_is_fresh(cache_path: Path) -> bool:
    cached = _load_json(cache_path)
    if not cached or "run_at" not in cached:
        return False
    try:
        run_at = datetime.fromisoformat(cached["run_at"])
    except ValueError:
        return False
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - run_at).total_seconds() < WEEKLY_SECONDS


def _write_cache(cache_path: Path, summary_line: str) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"run_at": datetime.now(timezone.utc).isoformat(), "summary": summary_line}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # caching is an optimization, never load-bearing


# --------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------

def _summarize(report: dict) -> tuple[int, int]:
    stale_count = 0
    repos_with_stale = 0
    for repo in report["repos"]:
        repo_stale = sum(1 for row in repo["rows"] if row.get("status") == "STALE")
        stale_count += repo_stale
        if repo_stale:
            repos_with_stale += 1
    return stale_count, repos_with_stale


def render_text(report: dict) -> str:
    lines = []
    if report.get("notes"):
        for note in report["notes"]:
            lines.append(f"NOTE: {note}")
    lines.append(f"(hub git history capped at last {report['history_cap']} commits per file)")
    lines.append(
        "([CONTRADICTION-candidate] = commit-message keyword heuristic "
        "(fix/resolve/contradict wording), not a verified causal link)"
    )

    for repo in report["repos"]:
        rows = repo["rows"]
        git_state = repo.get("git_state")
        if not rows and not repo.get("note") and not git_state:
            continue  # no provisioned rules at all — nothing to report
        counts: dict = {}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        counts_str = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no rule files"
        lines.append(f"\n=== {repo['repo']} ({counts_str}) ===")
        if repo.get("note"):
            lines.append(f"  NOTE: {repo['note']}")
        if git_state:
            if git_state.get("error"):
                lines.append(f"  NOTE: {git_state['error']}")
            else:
                upstream = git_state.get("upstream") or "no upstream"
                lines.append(
                    f"  read: working tree @ {git_state['branch']} "
                    f"(ahead {git_state['ahead']} / behind {git_state['behind']} of {upstream})"
                )
                for n in git_state.get("notes", []):
                    lines.append(f"  NOTE: {n}")
        for row in rows:
            status = row["status"]
            detail = ""
            if status == "STALE":
                tag = " [CONTRADICTION-candidate]" if row.get("contradiction") else ""
                detail = f": matches hub {row['hub_commit_sha'][:10]} ({row['hub_commit_date']}){tag}"
            line = f"  {status:<13}{row['file']}{detail}"
            note = row.get("note")
            if note:
                line += f" — {note}"
            lines.append(line)

    stale_count, repos_with_stale = _summarize(report)
    lines.append(f"\nrule-drift: {stale_count} stale across {repos_with_stale} repos")
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS_PATH, help="path to GetWorkDone settings.json")
    parser.add_argument("--repo", action="append", dest="repos", help="limit to this repo_registry key (repeatable)")
    parser.add_argument("--history-cap", type=int, default=30, help="max hub commits walked per rule file")
    parser.add_argument(
        "--deadline-seconds", type=float, default=DEFAULT_SCAN_DEADLINE_SECONDS,
        help="soft wall-clock budget for the whole scan (0 = unbounded)",
    )
    parser.add_argument("--weekly", action="store_true", help="skip if the cache shows a run within the last 7 days")
    args = parser.parse_args()

    if args.weekly and _cache_is_fresh(CACHE_PATH):
        cached = _load_json(CACHE_PATH) or {}
        print(f"rule-drift: cached ({cached.get('summary', 'no summary')})")
        return 0

    report = build_report(
        settings_path=args.settings, repo_filter=args.repos, history_cap=args.history_cap,
        deadline_seconds=(args.deadline_seconds or None),
    )
    stale_count, repos_with_stale = _summarize(report)
    summary_line = f"rule-drift: {stale_count} stale across {repos_with_stale} repos"

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))

    if args.weekly:
        _write_cache(CACHE_PATH, summary_line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
