"""Behavioral + structural tests for the agent-team teammate-governance hooks.

Covers the three hooks shipped with the agent-teams incorporation
(plans/agent-teams-incorporation.md):

  - team-task-created-deliverable.sh   (TaskCreated  → reject deliverable-less tasks)
  - team-task-completed-verifier.sh    (TaskCompleted → block unverified completions)
  - team-teammate-idle-drain.sh        (TeammateIdle → keep working while queue non-empty)

The load-bearing safety properties these tests pin:
  1. FAIL-OPEN by default — no strict flag ⇒ always exit 0 (never block a teammate).
  2. Strict mode (TEAM_GOVERNANCE_STRICT=1) hard-blocks (exit 2) ONLY on a real violation,
     and delivers feedback on STDERR (the agent-teams exit-2 feedback channel).
  3. The idle hook is LOOP-SAFE — it never re-engages on an empty/unknown queue.
  4. Malformed / empty payloads fail open.
  5. The hooks do NOT blanket-redirect stderr (regression guard for the bug where
     `exec 2>/dev/null` swallowed the exit-2 feedback).
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
# Parse-dependent assertions need jq; without it the hooks correctly no-op (fail open).
needs_jq = pytest.mark.skipif(JQ is None, reason="jq not available (hooks fail open without it)")


def _run(hook: Path, payload: str, strict: bool = False):
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    if JQ:
        env["PATH"] = str(Path(JQ).parent) + ":" + env["PATH"]
    if strict:
        env["TEAM_GOVERNANCE_STRICT"] = "1"
    return subprocess.run(
        [BASH, str(hook)], input=payload, capture_output=True, text=True, timeout=20, env=env
    )


# --------------------------------------------------------------------------- structure
def test_all_three_hooks_exist():
    for h in (CREATED, COMPLETED, IDLE):
        assert h.exists(), f"missing hook: {h}"


def test_rule_exists():
    assert RULE.exists(), "agent-team-selection.md rule must exist"


def test_hooks_and_rule_registered():
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for name, typ in [
        ("team-task-created-deliverable", "hook"),
        ("team-task-completed-verifier", "hook"),
        ("team-teammate-idle-drain", "hook"),
        ("agent-team-selection", "rule"),
    ]:
        assert name in reg, f"{name} not registered in registry/patterns.json"
        assert reg[name]["type"] == typ, f"{name} should be type {typ}"


def test_no_blanket_stderr_redirect():
    """Regression guard: exit-2 feedback is delivered via stderr, so the hooks MUST NOT
    blanket-redirect stderr to /dev/null (the original bug)."""
    for h in (CREATED, COMPLETED, IDLE):
        body = h.read_text(encoding="utf-8")
        assert "exec 2>/dev/null" not in body, (
            f"{h.name} must not blanket-redirect stderr — it swallows exit-2 feedback"
        )


def test_hooks_default_fail_open_guard_present():
    for h in (CREATED, COMPLETED, IDLE):
        body = h.read_text(encoding="utf-8")
        assert "TEAM_GOVERNANCE_STRICT" in body, f"{h.name} must gate hard-block on the strict flag"


# ------------------------------------------------------------------- created-deliverable
@needs_bash
def test_created_thin_task_non_strict_allows():
    res = _run(CREATED, '{"task":{"description":"fix it"}}', strict=False)
    assert res.returncode == 0, "non-strict must allow (fail-open)"


@needs_bash
@needs_jq
def test_created_thin_task_strict_blocks_with_feedback():
    res = _run(CREATED, '{"task":{"description":"fix it"}}', strict=True)
    assert res.returncode == 2, "strict + thin task must block"
    assert "deliverable" in res.stderr.lower(), "must deliver feedback on stderr"


@needs_bash
@needs_jq
def test_created_good_task_strict_allows():
    res = _run(CREATED, '{"task":{"description":"Add OAuth refresh-token rotation to the auth service"}}', strict=True)
    assert res.returncode == 0, "a task with a clear deliverable must pass even in strict mode"


@needs_bash
def test_created_empty_payload_fails_open():
    assert _run(CREATED, "", strict=True).returncode == 0


@needs_bash
def test_created_malformed_json_fails_open():
    assert _run(CREATED, "{not json", strict=True).returncode == 0


# -------------------------------------------------------------------- completed-verifier
@needs_bash
def test_completed_no_evidence_non_strict_allows():
    assert _run(COMPLETED, '{"task":{"result":"done, looks good"}}', strict=False).returncode == 0


@needs_bash
@needs_jq
def test_completed_no_evidence_strict_blocks_with_feedback():
    res = _run(COMPLETED, '{"task":{"result":"done, looks good"}}', strict=True)
    assert res.returncode == 2, "strict + no evidence must block"
    assert "evidence" in res.stderr.lower(), "must deliver feedback on stderr"


@needs_bash
@needs_jq
def test_completed_with_evidence_strict_allows():
    res = _run(COMPLETED, '{"task":{"result":"ran pytest, 14 passed, gate green"}}', strict=True)
    assert res.returncode == 0, "completion WITH verification evidence must pass"


@needs_bash
def test_completed_empty_payload_fails_open():
    assert _run(COMPLETED, "", strict=True).returncode == 0


# ----------------------------------------------------------------------- teammate-idle
@needs_bash
@needs_jq
def test_idle_empty_queue_strict_is_loop_safe():
    """The critical loop-safety property: never re-engage on an empty queue."""
    assert _run(IDLE, '{"pending_tasks":0}', strict=True).returncode == 0


@needs_bash
@needs_jq
def test_idle_pending_work_strict_keeps_working():
    res = _run(IDLE, '{"pending_tasks":3}', strict=True)
    assert res.returncode == 2, "strict + pending work must keep the teammate working"
    assert res.stderr.strip(), "must deliver feedback on stderr"


@needs_bash
@needs_jq
def test_idle_pending_work_non_strict_allows_idle():
    assert _run(IDLE, '{"pending_tasks":3}', strict=False).returncode == 0


@needs_bash
def test_idle_no_pending_field_fails_open():
    assert _run(IDLE, '{"teammate":"researcher"}', strict=True).returncode == 0


@needs_bash
@needs_jq
def test_idle_non_integer_pending_is_loop_safe():
    assert _run(IDLE, '{"pending_tasks":"lots"}', strict=True).returncode == 0
