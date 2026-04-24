"""Runtime probe — assert the Claude Code platform does not forward the
Agent tool to dispatched subagents.

This is an INTEGRATION test: it requires a live Claude Code session to
dispatch a throwaway subagent and observe its actual tool list. Unlike
`test_orchestrator_tool_grants.py` (which is static frontmatter analysis),
this test detects regressions at the platform level — if Anthropic ever
changes the policy to forward `Agent` to subagents, this probe becomes
the first signal.

The probe is marked `@pytest.mark.integration` and `@pytest.mark.skipif`
unless `CLAUDE_CODE_INTEGRATION=1` is set in the environment. It cannot
run in a pure Python CI — it requires the `claude` CLI (Claude Code) on
PATH plus valid credentials. Run it manually as part of a release
verification, or wire into a CI job that has Claude Code provisioned.

Background: the original finding (2026-04-24) was surfaced via three
independent runtime probes (testbed SUBAGENT_DISPATCH_PROBE event, hub
general-purpose subagent, and T0 self-test). Anthropic's official docs
[1] and open issues [2][3] confirm the behavior is intentional platform
design, not a bug.

[1] https://code.claude.com/docs/en/sub-agents — "subagents cannot spawn other subagents"
[2] https://github.com/anthropics/claude-code/issues/19077
[3] https://github.com/anthropics/claude-code/issues/4182
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


CLAUDE_AVAILABLE = shutil.which("claude") is not None
INTEGRATION_ENABLED = os.environ.get("CLAUDE_CODE_INTEGRATION") == "1"


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (CLAUDE_AVAILABLE and INTEGRATION_ENABLED),
        reason=(
            "Runtime probe requires `claude` CLI on PATH AND "
            "CLAUDE_CODE_INTEGRATION=1 env var (opt-in). Set both to run."
        ),
    ),
]


PROBE_PROMPT = """You are a throwaway subagent running a one-time probe.

Your only task: list the tools you have access to, as a JSON array of
tool names, on a single line prefixed with `TOOL_LIST:`.

Example output:
TOOL_LIST: ["Bash", "Read", "Write", "Grep", "Glob"]

Do not run any tools. Do not produce any other output. Exit immediately
after printing the TOOL_LIST line.
"""


def _dispatch_probe() -> list[str]:
    """Dispatch a throwaway subagent via `claude -p` and parse its tool list.

    Returns the list of tool names the subagent reports having access to.
    """
    result = subprocess.run(
        ["claude", "-p", PROBE_PROMPT],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"`claude -p` failed with exit {result.returncode}: {result.stderr}"
    )
    # Parse TOOL_LIST: [...] from stdout
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("TOOL_LIST:"):
            payload = line[len("TOOL_LIST:"):].strip()
            try:
                tools = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"could not parse TOOL_LIST payload as JSON: {payload!r} ({exc})"
                )
            assert isinstance(tools, list), (
                f"TOOL_LIST payload is not a JSON array: {payload!r}"
            )
            return [str(t) for t in tools]
    raise AssertionError(
        f"probe subagent did not emit a TOOL_LIST: line. stdout:\n{result.stdout}"
    )


def test_dispatched_subagent_does_not_have_agent_tool():
    """Live platform probe: dispatched subagents MUST NOT have Agent.

    If this test starts FAILING (i.e., Agent appears in the tool list),
    Anthropic's platform has changed — revisit `agent-orchestration.md` §2
    and the downstream skill-at-T0 pattern, because the single-dispatch-
    level constraint may no longer hold.
    """
    tools = _dispatch_probe()
    assert "Agent" not in tools, (
        f"REGRESSION: Dispatched subagent reports Agent in its tool list: "
        f"{tools}. This CONTRADICTS the platform constraint documented in "
        f"agent-orchestration.md §2 and Anthropic's official docs. If the "
        f"platform has changed, revisit the single-dispatch-level "
        f"architecture — the skill-at-T0 pattern may no longer be "
        f"necessary."
    )


def test_dispatched_subagent_still_has_skill_and_bash():
    """Sanity check: the subagent does have a meaningful tool set; the
    probe's failure mode should not be 'dispatched subagent has no tools'
    — that would be a different kind of regression.
    """
    tools = _dispatch_probe()
    # These are universally available to dispatched subagents per
    # 2026-04-24 observations and standard Claude Code behavior.
    expected_available = {"Bash", "Read", "Grep", "Glob"}
    missing = expected_available - set(tools)
    assert not missing, (
        f"Dispatched subagent is missing expected tools: {sorted(missing)}. "
        f"Observed tools: {tools}. Has the default subagent tool set "
        f"changed? Investigate before accepting."
    )
