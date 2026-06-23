"""Behavioral + structural tests for the agent-team teammate-governance hooks.

These tests use the REAL hook payload schema captured from a live in-process agent team
on 2026-06-23 (see plans/agent-teams-incorporation.md §11):

  TaskCreated   : { session_id, transcript_path, cwd, hook_event_name,
                    task_id, task_subject, task_description }
  TaskCompleted : + teammate_name, team_name   (NO work-product/result field)
  TeammateIdle  : { ..., permission_mode, teammate_name, team_name }  (NO pending count)

Because the captured schema lacks a work-product (TaskCompleted) and a pending count
(TeammateIdle), only the TaskCreated hook can hard-gate. The other two are honest AUDIT
loggers (never block). Hooks covered:

  - team-task-created-deliverable.sh  (TaskCreated  → reject deliverable-less tasks; strict)
  - team-task-completed-verifier.sh   (TaskCompleted → audit log; never blocks)
  - team-teammate-idle-drain.sh       (TeammateIdle → audit log; loop-safe; never blocks)

Pinned safety properties:
  1. TaskCreated fails open by default; strict-mode block delivers feedback on STDERR.
  2. TaskCompleted / TeammateIdle NEVER block (exit 0), even in strict mode.
  3. Multi-word field values are handled safely (regression: an eval-based extractor once
     ran the second word of a spaced subject as a command).
  4. Malformed / empty payloads fail open.
  5. The hooks do NOT blanket-redirect stderr (regression guard for the swallowed-feedback bug).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
HOOKS = ROOT / "core" / ".claude" / "hooks"
RULE = ROOT / "core" / ".claude" / "rules" / "agent-team-selection.md"
REGISTRY = ROOT / "registry" / "patterns.json"

CREATED = HOOKS / "team-task-created-deliverable.sh"
COMPLETED = HOOKS / "team-task-completed-verifier.sh"
IDLE = HOOKS / "team-teammate-idle-drain.sh"

BASH = shutil.which("bash")
JQ = shutil.which("jq")
needs_bash = pytest.mark.skipif(BASH is None, reason="bash not available")
needs_jq = pytest.mark.skipif(JQ is None, reason="jq not available (hooks fail open without it)")


def _run(hook: Path, payload: str, strict: bool = False, cwd: Path = None):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    if JQ:
        env["PATH"] = str(Path(JQ).parent) + ":" + env["PATH"]
    if strict:
        env["TEAM_GOVERNANCE_STRICT"] = "1"
    if cwd is not None:
        env["CLAUDE_PROJECT_DIR"] = str(cwd)
    return subprocess.run(
        [BASH, str(hook)], input=payload, capture_output=True, text=True, timeout=20, env=env
    )


# --------------------------------------------------------------------------- structure
def test_all_three_hooks_exist():
    for h in (CREATED, COMPLETED, IDLE):
        assert h.exists(), f"missing hook: {h}"


def test_rule_exists():
    assert RULE.exists()


def test_hooks_and_rule_registered():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for name, typ in [
        ("team-task-created-deliverable", "hook"),
        ("team-task-completed-verifier", "hook"),
        ("team-teammate-idle-drain", "hook"),
        ("agent-team-selection", "rule"),
    ]:
        assert name in reg and reg[name]["type"] == typ, f"{name} not registered as {typ}"


def test_no_blanket_stderr_redirect():
    """Regression guard: exit-2 feedback is delivered via stderr."""
    for h in (CREATED, COMPLETED, IDLE):
        assert "exec 2>/dev/null" not in h.read_text(encoding="utf-8"), f"{h.name} must not swallow stderr"


def test_no_eval_payload_extraction():
    """Regression guard: payload fields must NOT be parsed via eval (injection + spaces bug)."""
    for h in (CREATED, COMPLETED, IDLE):
        assert "eval " not in h.read_text(encoding="utf-8"), f"{h.name} must not eval payload-derived text"


# ------------------------------------------------------- TaskCreated (real schema, gates)
@needs_bash
@needs_jq
def test_created_real_good_task_strict_allows():
    p = '{"hook_event_name":"TaskCreated","task_id":"1","task_subject":"Analyze TODO CLI — DX lens","task_description":"Read-only analysis of developer-experience trade-offs."}'
    assert _run(CREATED, p, strict=True).returncode == 0


@needs_bash
@needs_jq
def test_created_thin_task_strict_blocks_with_feedback():
    p = '{"hook_event_name":"TaskCreated","task_id":"9","task_subject":"fix","task_description":"it"}'
    res = _run(CREATED, p, strict=True)
    assert res.returncode == 2, "thin subject+description must block in strict mode"
    assert "deliverable" in res.stderr.lower()


@needs_bash
@needs_jq
def test_created_thin_task_non_strict_allows():
    p = '{"hook_event_name":"TaskCreated","task_subject":"fix","task_description":"it"}'
    assert _run(CREATED, p, strict=False).returncode == 0


@needs_bash
def test_created_empty_and_malformed_fail_open():
    assert _run(CREATED, "", strict=True).returncode == 0
    assert _run(CREATED, "{not json", strict=True).returncode == 0


# ------------------------------------------------- TaskCompleted (audit logger, no block)
@needs_bash
@needs_jq
def test_completed_never_blocks_and_audits(tmp_path):
    (tmp_path / ".claude").mkdir()
    p = '{"hook_event_name":"TaskCompleted","task_id":"2","task_subject":"arch lens analysis","teammate_name":"arch-analyst","team_name":"session-4a3e63c9"}'
    res = _run(COMPLETED, p, strict=True, cwd=tmp_path)
    assert res.returncode == 0, "TaskCompleted must never block (no work-product in payload to gate on)"
    log = (tmp_path / ".claude" / ".team-activity.log").read_text(encoding="utf-8")
    assert "TaskCompleted" in log and "arch-analyst" in log
    # regression: a spaced subject must be captured whole, not split into a command
    assert "arch lens analysis" in log


@needs_bash
def test_completed_empty_payload_no_block(tmp_path):
    (tmp_path / ".claude").mkdir()
    assert _run(COMPLETED, "", strict=True, cwd=tmp_path).returncode == 0


# --------------------------------------------------- TeammateIdle (audit logger, loop-safe)
@needs_bash
@needs_jq
def test_idle_never_blocks_and_audits(tmp_path):
    (tmp_path / ".claude").mkdir()
    p = '{"hook_event_name":"TeammateIdle","permission_mode":"auto","teammate_name":"dx-analyst","team_name":"session-4a3e63c9"}'
    res = _run(IDLE, p, strict=True, cwd=tmp_path)
    assert res.returncode == 0, "TeammateIdle must be loop-safe — never re-engage on unknown queue state"
    log = (tmp_path / ".claude" / ".team-activity.log").read_text(encoding="utf-8")
    assert "TeammateIdle" in log and "dx-analyst" in log


@needs_bash
def test_idle_empty_payload_no_block(tmp_path):
    (tmp_path / ".claude").mkdir()
    assert _run(IDLE, "", strict=True, cwd=tmp_path).returncode == 0
