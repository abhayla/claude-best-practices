"""PR2 pre-merge migration script for test-pipeline-three-lane.

Closes all open `pipeline-failure`-labeled GitHub Issues that were created with
the PR1 dedup-hash format (2-field: test_id + category) BEFORE PR2 ships its
3-field hash (test_id + category + failing_commit_sha_short). Without this
migration, failures persisting across the PR1->PR2 boundary would produce
duplicate Issues because the new hash format would not match existing PR1-format
Issues.

Per spec:
- docs/specs/test-pipeline-three-lane-spec.md v1.6 §8 PR2 deployment checkbox
- REQ-M011 (hash transition migration)
- Success criterion #31

USAGE:
    # Dry-run (recommended first):
    python scripts/pr2_premerge_migration.py --dry-run

    # Real run (closes Issues):
    python scripts/pr2_premerge_migration.py

    # Custom window (default: 30 days, matches dedup_window_days config):
    python scripts/pr2_premerge_migration.py --days 60

ONE-SHOT: run once at PR2 merge time. Not part of the runtime test suite.

PRECONDITIONS:
- gh CLI installed and authenticated (gh auth status passes)
- Current working directory is a git repo with github.com origin remote
- User has Issue write access to the repo

EXIT CODES:
    0 = success (or dry-run shows no Issues to close)
    1 = at least one Issue close failed
    2 = preflight failure (gh not installed/authenticated, etc.)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


COMMENT_BODY = (
    "Closing pre-PR2 Issue. The test-pipeline-three-lane PR2 deployment changed "
    "the dedup hash format from `(test_id, category)` to "
    "`(test_id, category, failing_commit_sha_short)` to prevent cross-run "
    "conflation. If this failure recurs after PR2 deploys, a fresh Issue will "
    "be created with the v2 dedup format. Manual cross-link if needed.\n\n"
    "Per spec docs/specs/test-pipeline-three-lane-spec.md v1.6 §8 PR2 atomic "
    "switchover; REQ-M011."
)


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess and return CompletedProcess. Raises on check failure."""
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def preflight() -> None:
    """Verify gh CLI works and we have a github.com remote. Exits 2 on failure."""
    try:
        run(["gh", "--version"])
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: gh CLI not installed. Install from https://cli.github.com/", file=sys.stderr)
        sys.exit(2)

    try:
        run(["gh", "auth", "status"])
    except subprocess.CalledProcessError:
        print("ERROR: gh not authenticated. Run: gh auth login", file=sys.stderr)
        sys.exit(2)

    try:
        result = run(["git", "remote", "get-url", "origin"])
        if "github.com" not in result.stdout:
            print(
                f"ERROR: origin remote is not a github.com URL: {result.stdout.strip()}",
                file=sys.stderr,
            )
            sys.exit(2)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: could not read git remote origin: {e.stderr}", file=sys.stderr)
        sys.exit(2)


def list_pipeline_failure_issues(window_days: int) -> list[dict]:
    """Return list of open Issues labeled pipeline-failure created in the last N days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).strftime("%Y-%m-%d")
    result = run([
        "gh", "issue", "list",
        "--label", "pipeline-failure",
        "--state", "open",
        "--search", f"created:>={cutoff}",
        "--json", "number,title,createdAt,labels",
        "--limit", "1000",
    ])
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"ERROR: gh returned non-JSON: {e}", file=sys.stderr)
        sys.exit(1)


def close_issue(number: int, dry_run: bool) -> bool:
    """Close an issue with the migration comment. Returns True on success."""
    if dry_run:
        print(f"  [DRY-RUN] Would close #{number}")
        return True

    try:
        run(["gh", "issue", "close", str(number), "--comment", COMMENT_BODY])
        print(f"  CLOSED: #{number}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  FAILED to close #{number}: {e.stderr}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be closed without closing")
    parser.add_argument("--days", type=int, default=30, help="Look back window in days (default: 30, matches dedup_window_days config)")
    args = parser.parse_args()

    print(f"PR2 pre-merge migration {'(DRY-RUN)' if args.dry_run else '(REAL)'} — looking back {args.days} days")

    preflight()
    print("OK — preflight passed (gh installed + authenticated + github.com remote)")

    issues = list_pipeline_failure_issues(args.days)
    if not issues:
        print(f"OK — no open pipeline-failure Issues from the last {args.days} days; PR2 safe to merge")
        return 0

    print(f"\nFound {len(issues)} open Issue(s) to close:")
    for issue in issues:
        labels = ", ".join(l["name"] for l in issue.get("labels", []))
        print(f"  #{issue['number']}: {issue['title']} (created {issue['createdAt']}, labels: {labels})")

    print(f"\n{'Simulating' if args.dry_run else 'Closing'} Issues...")
    failures = 0
    for issue in issues:
        if not close_issue(issue["number"], args.dry_run):
            failures += 1

    if failures:
        print(f"\nFAIL: {failures} Issue close(s) failed", file=sys.stderr)
        return 1

    print(f"\nOK — {'would close' if args.dry_run else 'closed'} {len(issues)} Issue(s); PR2 safe to merge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
