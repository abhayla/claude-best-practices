"""Guard for the SessionStart PR-reconcile hook (auto-pr-reconcile.sh).

Closes the gap where a missed SessionEnd left CLEAN PRs open with no action: the
reconcile hook runs at the reliably-firing SessionStart and arms/prunes ALL eligible
open PRs, except the current (active) branch. These tests pin the safety properties.
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
HOOK = ROOT / ".claude" / "hooks" / "auto-pr-reconcile.sh"
LIB = ROOT / ".claude" / "hooks" / "session-git-landing.sh"  # shared landing SSOT it delegates to
SETTINGS = ROOT / ".claude" / "settings.json"

bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")

# Fake `gh` dispatcher: understands `pr view <target>`, `pr view <target> --json labels --jq ...`,
# `pr view <target> --json body --jq ...`, and `pr merge <target> ...` (logs the merge to $GH_LOG so
# the test can assert whether the hold gate actually stopped the merge, not just that it ran).
_FAKE_GH = """#!/usr/bin/env bash
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  if printf '%s\\n' "$@" | grep -q -- '--json'; then
    # The hold-check's --json queries: gated separately from the plain existence check below,
    # so a test can fail JUST the hold-check query without also failing the "does a PR exist" gate.
    if [ "${GH_FAKE_JSON_RC:-0}" != "0" ]; then exit "$GH_FAKE_JSON_RC"; fi
    if printf '%s\\n' "$@" | grep -q 'labels'; then
      printf '%s\\n' "$GH_FAKE_LABELS"
    elif printf '%s\\n' "$@" | grep -q 'body'; then
      printf '%s\\n' "$GH_FAKE_BODY"
    fi
    exit 0
  fi
  exit "${GH_FAKE_VIEW_RC:-0}"
elif [ "$1" = "pr" ] && [ "$2" = "merge" ]; then
  echo "MERGE:$*" >> "$GH_LOG"
  exit 0
else
  exit 0
fi
"""


def _make_fake_gh(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(_FAKE_GH, encoding="utf-8")
    gh_path.chmod(gh_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _run_merge_one(
    tmp_path: Path, branch: str, labels: str = "", body: str = "", view_rc: str = "0", json_rc: str = "0"
) -> str:
    bin_dir = _make_fake_gh(tmp_path)
    gh_log = tmp_path / "gh.log"
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["GH_FAKE_LABELS"] = labels
    env["GH_FAKE_BODY"] = body
    env["GH_FAKE_VIEW_RC"] = view_rc
    env["GH_FAKE_JSON_RC"] = json_rc
    env["GH_LOG"] = str(gh_log)
    script = f'source "{LIB}"\nmerge_one "{branch}"\n'
    r = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    return gh_log.read_text(encoding="utf-8") if gh_log.exists() else ""


def _hook() -> str:
    return HOOK.read_text(encoding="utf-8")


def _lib() -> str:
    return LIB.read_text(encoding="utf-8")


def test_hook_exists():
    assert HOOK.exists(), "auto-pr-reconcile.sh must exist in .claude/hooks/"


def test_wired_into_session_start():
    cmds = [
        h["command"]
        for block in json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"].get("SessionStart", [])
        for h in block.get("hooks", [])
    ]
    assert any("auto-pr-reconcile.sh" in c for c in cmds), (
        "auto-pr-reconcile.sh must be wired into SessionStart (the reliably-firing event)"
    )


def test_excludes_current_branch():
    """The reconcile MUST NOT arm the current HEAD branch — that would merge active work.
    The reconcile logic lives in the shared SSOT that the hook delegates to."""
    assert "session-git-landing.sh" in _hook() and "reconcile" in _hook(), (
        "auto-pr-reconcile.sh must delegate to the shared landing lib's reconcile"
    )
    lib = _lib()
    assert 'cur="$(git rev-parse --abbrev-ref HEAD' in lib
    assert '"$br" = "$cur"' in lib, (
        "reconcile must skip the current branch so active work is never auto-merged"
    )


def test_honors_off_switches():
    body = _hook()
    assert 'AUTO_PR_DISABLE' in body, "must honor AUTO_PR_DISABLE=1"
    assert 'AUTO_MERGE' in body, "must honor AUTO_MERGE=0 (prune-only)"


def test_is_fail_safe():
    assert "exit 0" in _hook(), "hook must be fail-safe (always exit 0 so it never blocks session start)"
    # Only arms via native --auto, so GitHub still gates the real merge on required checks (in the lib).
    assert "--auto --squash" in _lib(), "must arm native CI-gated auto-merge, not force a merge"


def test_skips_draft_and_already_armed_prs():
    lib = _lib()  # the draft/already-armed filtering lives in the shared landing lib
    assert "isDraft==false" in lib, "must skip draft PRs"
    assert "autoMergeRequest==null" in lib, "must skip PRs that already have auto-merge armed"


def test_records_merged_prs_for_zero_manual_trust_accrual():
    """Step 1b: sweep freshly-merged PRs into the trust-score ledger (scripts/record_merged_prs.py),
    since the common autonomous auto-merge landing path never calls record_task_run.py."""
    body = _hook()
    assert "record_merged_prs.py" in body, "must invoke the zero-manual merged-PR trust recorder"
    assert "--quiet" in body, "must call it with --quiet to keep the hook log to one line"


def test_record_merged_prs_call_is_fail_safe():
    """The recording step must never be able to abort the hook — it stays guarded and the
    hook still ends with exit 0 regardless of what record_merged_prs.py does."""
    body = _hook()
    lines = body.splitlines()
    call_idx = next(i for i, line in enumerate(lines) if "python scripts/record_merged_prs.py" in line)
    preceding = "\n".join(lines[max(0, call_idx - 3):call_idx])
    assert "command -v python" in preceding, "the recorder call must be guarded (python may be absent)"
    assert body.rstrip().splitlines()[-1] == "exit 0", "hook must still end fail-safe with exit 0"


# --- Hold-for-owner-review gate (T-118, 2026-08-13 incident) ------------------------------------
# PR #535 was contracted "held for owner review" but self-landed via auto-pr-reconcile.sh's
# `gh pr merge --auto` on an already-green PR — no arming step, no hold check anywhere on the
# path. Every merge call site in the shared landing SSOT (session-git-landing.sh: land, merge_one,
# and both reconcile() merge sites) must skip a PR carrying the 'hold' label or a body matching
# "owner review required" (case-insensitive). These tests prove it BEHAVIORALLY (fake `gh` on
# PATH) — not just via static text assertions — so a regression that keeps the words in the file
# but breaks the wiring still fails red.


def test_hold_check_defined_and_wired_into_all_four_merge_sites():
    lib = _lib()
    assert "_hold_check()" in lib, "_hold_check helper must be defined"
    # 4 merge sites: land(), merge_one(), reconcile() main loop, reconcile() docs carve-out.
    merge_lines = [
        i for i, l in enumerate(lib.splitlines())
        if "gh pr merge" in l and not l.strip().startswith("#")
    ]
    assert len(merge_lines) == 4, f"expected 4 'gh pr merge' call sites, found {len(merge_lines)}"
    hold_call_count = lib.count("_hold_check ")
    assert hold_call_count >= 4, (
        f"_hold_check must be called before all 4 merge sites, found {hold_call_count} call(s)"
    )


@bash
def test_hold_labeled_pr_is_skipped_by_merge_one(tmp_path):
    log = _run_merge_one(tmp_path, "feature-branch", labels="hold\n")
    assert "MERGE:" not in log, f"a PR labeled 'hold' must NOT be merged; gh log: {log!r}"


@bash
def test_hold_body_marker_pr_is_skipped_by_merge_one(tmp_path):
    log = _run_merge_one(tmp_path, "feature-branch", body="This needs Owner Review Required before landing.")
    assert "MERGE:" not in log, f"a PR whose body says 'owner review required' must NOT be merged; gh log: {log!r}"


@bash
def test_unmarked_pr_still_lands_via_merge_one(tmp_path):
    log = _run_merge_one(tmp_path, "feature-branch", labels="", body="Routine fix.")
    assert "MERGE:pr merge feature-branch" in log, f"an unmarked PR must still be armed; gh log: {log!r}"


@bash
def test_hold_check_fails_closed_on_gh_error(tmp_path):
    """If the hold-check query itself errors (gh hiccup), the merge must be skipped — the ONE
    place in this file that fails CLOSED instead of open, per the T-118 contract."""
    log = _run_merge_one(tmp_path, "feature-branch", json_rc="1")
    assert "MERGE:" not in log, f"a failed hold-check query must skip the merge (fail-safe); gh log: {log!r}"


def test_core_copy_stays_in_sync_with_hold_gate():
    core_lib = (ROOT / "core" / ".claude" / "hooks" / "session-git-landing.sh").read_text(encoding="utf-8")
    assert core_lib == _lib(), "hub and core copies must stay byte-identical (dual-home synced)"
    assert "_hold_check()" in core_lib, "core copy must carry the hold gate too"
