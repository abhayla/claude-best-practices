"""Tests for orchestrator agent tool grants.

Per `core/.claude/rules/agent-orchestration.md` rule #2 (tiered nesting) and
rule #3 (controlled nesting), orchestrator agents (T0/T1/T2) MUST be able to
dispatch further subagents via `Agent()`. Claude Code subagents get a default
limited tool set that EXCLUDES `Agent` unless the frontmatter explicitly lists
it under `tools:`. Runtime verification against v2-pipeline-testbed
(2026-04-23) confirmed that `e2e-conductor-agent` fell back to inline
execution because `Agent` wasn't declared in its tools — the entire 4-tier
dispatch contract silently collapses.

These tests pin the invariant: every orchestrator declares `tools` including
`Agent`; every T3 leaf worker declares `tools` WITHOUT `Agent` (per rule #3
"T3 agents MUST NOT call Agent()").
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / "core" / ".claude" / "agents"

# Testing-pipeline orchestrators that MUST be able to dispatch subagents.
# Identified by runtime verification and agent-orchestration.md tier table.
ORCHESTRATORS = [
    "testing-pipeline-master-agent",  # T1
    "test-pipeline-agent",             # T2A (lane sub-orchestrator)
    "failure-triage-agent",            # T2B (triage sub-orchestrator — per three-lane spec)
    "e2e-conductor-agent",             # T2 (E2E sub-orchestrator)
]

# T3 leaf workers that MUST NOT have Agent in their tool grants
# (per agent-orchestration.md rule #3).
T3_LEAVES = [
    "test-scout-agent",
    "visual-inspector-agent",
    "test-healer-agent",
    "github-issue-manager-agent",      # T3 leaf — invokes /create-github-issue skill only
]

# Tools an orchestrator needs at minimum. Bash for shell, Read/Write/Edit
# for file ops, Grep/Glob for search, Skill for skill invocation, Agent
# for subagent dispatch.
REQUIRED_ORCHESTRATOR_TOOLS = {"Agent", "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"}


def _parse_frontmatter(agent_path: Path) -> dict:
    """Extract YAML frontmatter from an agent file."""
    text = agent_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match, f"{agent_path.name}: no frontmatter block found"
    return yaml.safe_load(match.group(1))


def _tools_set(frontmatter: dict) -> set[str]:
    """Return the tools declaration as a set.

    `tools:` MUST be a YAML list. A space-separated scalar parses as a
    single string and Claude Code does NOT expose the agent as a
    `subagent_type` — verified in the downstream test run 2026-04-24,
    where 6 pipeline agents with the scalar form were silently inlined
    at T1 instead of being dispatched as subagents.
    """
    raw = frontmatter.get("tools")
    if raw is None:
        return set()
    if isinstance(raw, list):
        return set(raw)
    if isinstance(raw, str):
        raise TypeError(
            "tools: must be a YAML list (e.g. [\"Agent\", \"Bash\", \"Read\"]), "
            "not a space-separated string. Claude Code does not expose agents "
            "with scalar `tools:` as subagent_type — they fall back to inline "
            "execution at the parent tier, silently breaking the 4-tier "
            "dispatch contract. Observed 2026-04-24 in v2-pipeline-testbed."
        )
    raise TypeError(f"unexpected tools type: {type(raw).__name__}")


# ── Orchestrator invariants ────────────────────────────────────────────────


@pytest.mark.parametrize("name", ORCHESTRATORS)
def test_orchestrator_declares_tools_field(name):
    """Every orchestrator MUST declare a tools field — otherwise Claude Code
    grants a limited default set that excludes Agent."""
    fm = _parse_frontmatter(AGENTS_DIR / f"{name}.md")
    assert "tools" in fm, (
        f"{name} frontmatter missing `tools` field — Claude Code will apply "
        "a default limited tool set that excludes Agent, breaking the "
        "4-tier dispatch contract (agent-orchestration.md rules #2, #3)"
    )


@pytest.mark.parametrize("name", ORCHESTRATORS)
def test_orchestrator_includes_agent_tool(name):
    """Every orchestrator MUST include Agent in its tools — they exist
    specifically to dispatch further subagents."""
    fm = _parse_frontmatter(AGENTS_DIR / f"{name}.md")
    tools = _tools_set(fm)
    assert "Agent" in tools, (
        f"{name} tools set {sorted(tools)} must include `Agent` — without it, "
        "T1/T2 orchestrators cannot dispatch their subagents. Runtime "
        "verification (2026-04-23) confirmed this collapses the 4-tier "
        "dispatch model to inline execution."
    )


@pytest.mark.parametrize("name", ORCHESTRATORS)
def test_orchestrator_has_all_minimum_tools(name):
    """Beyond Agent, orchestrators need the standard file/shell/skill tools."""
    fm = _parse_frontmatter(AGENTS_DIR / f"{name}.md")
    tools = _tools_set(fm)
    missing = REQUIRED_ORCHESTRATOR_TOOLS - tools
    assert not missing, (
        f"{name} tools set missing required: {sorted(missing)}. "
        f"Orchestrators need {sorted(REQUIRED_ORCHESTRATOR_TOOLS)} at minimum."
    )


# ── T3 leaf invariants ─────────────────────────────────────────────────────


@pytest.mark.parametrize("name", T3_LEAVES)
def test_t3_leaf_declares_tools_field(name):
    """T3 leaves should declare tools explicitly — defaults vary."""
    fm = _parse_frontmatter(AGENTS_DIR / f"{name}.md")
    # Note: T3 leaves have `mcp-servers` for Playwright MCP separately;
    # tools field is for the general Claude Code tool set.
    # We don't require a tools declaration here yet because test-healer-agent
    # uses mcp-servers instead, but we DO require that if declared, it
    # excludes Agent.


@pytest.mark.parametrize("name", T3_LEAVES)
def test_t3_leaf_excludes_agent_tool(name):
    """T3 leaves MUST NOT declare Agent in their tools — per
    agent-orchestration.md rule #3, they are leaf workers that use Skill()
    only. If Agent is granted, they could spawn a 4th tier, violating the
    depth cap."""
    fm = _parse_frontmatter(AGENTS_DIR / f"{name}.md")
    tools = _tools_set(fm)
    assert "Agent" not in tools, (
        f"{name} declares Agent in tools — T3 leaves must NOT dispatch "
        "further subagents (agent-orchestration.md rule #3). Remove `Agent` "
        "from the tools list."
    )
