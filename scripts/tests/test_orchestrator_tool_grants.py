"""Tests for agent tool grants under the single-level dispatch model.

Per `core/.claude/rules/agent-orchestration.md` §2 (Single-Level Dispatch
Model), Claude Code does NOT forward the `Agent` tool to dispatched
subagents regardless of frontmatter (Anthropic docs: "subagents cannot
spawn other subagents"; GH #19077 + #4182; 2026-04-24 runtime probes).

The context-aware invariant checked here, keyed off the `dispatched_from:`
frontmatter field declared by each agent:

- `dispatched_from: T0` — agent is invoked directly by the user; MUST
  declare `Agent` in `tools:` to dispatch worker subagents.
- `dispatched_from: worker` — agent is only ever dispatched as a
  subagent; MUST NOT declare `Agent` in `tools:` (declaring it is
  misleading — runtime strips it).
- `dispatched_from: dual-mode` — agent supports both contexts; MAY
  declare `Agent`, but the worker-mode code path must not depend on it.
  This test does not body-scan for that; it is left to reviewers.
- Field absent — defaults to `worker` (safer assumption; forces
  explicit declaration for T0 agents).

Agents marked `deprecated: true` are skipped — they are on the
deprecation lifecycle and will be removed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / "core" / ".claude" / "agents"


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
    at their dispatch site instead of being dispatched as subagents.
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
            "execution at the parent, silently breaking dispatch. Observed "
            "2026-04-24 in v2-pipeline-testbed."
        )
    raise TypeError(f"unexpected tools type: {type(raw).__name__}")


def _dispatch_context(frontmatter: dict) -> str:
    """Return the declared dispatch context, defaulting to 'worker' if absent."""
    value = frontmatter.get("dispatched_from", "worker")
    if value not in {"T0", "worker", "dual-mode"}:
        raise ValueError(
            f"invalid dispatched_from value {value!r}; "
            f"must be one of T0, worker, dual-mode"
        )
    return value


def _is_template_doc(frontmatter: dict, agent_name: str) -> bool:
    """Identify reference-doc files in the agents dir that are not actually
    invokable agents (e.g., workflow-master-template). Such files have no
    `tools:` field, no body that would be dispatched, and carry no runtime
    contract — exclude them from the invariant."""
    return agent_name.endswith("-template") and frontmatter.get("tools") is None


def _all_agent_files() -> list[Path]:
    """Return all agent files in core/.claude/agents/."""
    return sorted(AGENTS_DIR.glob("*.md"))


def _is_deprecated(frontmatter: dict) -> bool:
    """True if the agent is on the deprecation lifecycle."""
    return bool(frontmatter.get("deprecated"))


# Collect agent fixtures once at module load so parametrize can use names.
_AGENT_PATHS = _all_agent_files()
_AGENT_NAMES = [p.stem for p in _AGENT_PATHS]


@pytest.fixture(params=_AGENT_PATHS, ids=_AGENT_NAMES)
def agent_file(request) -> Path:
    return request.param


# ── Invariant: tools: is YAML list, not scalar ─────────────────────────────


def test_tools_is_yaml_list_not_scalar(agent_file):
    """tools: must be a YAML list. Scalar form silently breaks dispatch."""
    fm = _parse_frontmatter(agent_file)
    if _is_template_doc(fm, agent_file.stem):
        pytest.skip("reference-doc file without tools declaration")
    if "tools" not in fm:
        pytest.skip(
            "agent does not declare tools (default tool set applies); "
            "out of scope for this invariant"
        )
    # _tools_set raises TypeError on scalar form; call to trigger.
    _tools_set(fm)


# ── Invariant: dispatched_from: is declared and valid (T0 and dual-mode) ───


def test_dispatched_from_field_is_valid(agent_file):
    """If declared, dispatched_from: must be one of T0/worker/dual-mode."""
    fm = _parse_frontmatter(agent_file)
    if _is_template_doc(fm, agent_file.stem):
        pytest.skip("reference-doc file")
    # _dispatch_context raises on invalid value; call to trigger.
    _dispatch_context(fm)


# ── Invariant: T0 orchestrators declare Agent in tools ─────────────────────


def test_t0_orchestrator_declares_agent_in_tools(agent_file):
    """Agents marked `dispatched_from: T0` MUST include Agent in tools:
    — they dispatch worker subagents from the user's session.
    """
    fm = _parse_frontmatter(agent_file)
    if _is_template_doc(fm, agent_file.stem):
        pytest.skip("reference-doc file")
    if _is_deprecated(fm):
        pytest.skip("deprecated — on deprecation lifecycle")
    if _dispatch_context(fm) != "T0":
        pytest.skip("not a T0 orchestrator")

    tools = _tools_set(fm)
    assert "Agent" in tools, (
        f"{agent_file.stem} declares dispatched_from: T0 but does not "
        f"include Agent in tools: {sorted(tools)}. T0 orchestrators MUST "
        f"declare Agent to dispatch worker subagents (pattern-structure.md "
        f"Tool Grants table). Either add Agent to tools: or change "
        f"dispatched_from to worker/dual-mode."
    )


# ── Invariant: workers do NOT declare Agent in tools ───────────────────────


def test_worker_does_not_declare_agent_in_tools(agent_file):
    """Agents marked `dispatched_from: worker` (explicit or default) MUST
    NOT include Agent in tools: — runtime strips it, and declaring it is
    misleading (inline dispatch instructions produce silent serial work).
    """
    fm = _parse_frontmatter(agent_file)
    if _is_template_doc(fm, agent_file.stem):
        pytest.skip("reference-doc file")
    if _is_deprecated(fm):
        pytest.skip("deprecated — on deprecation lifecycle")
    if _dispatch_context(fm) != "worker":
        pytest.skip("not a worker (T0 or dual-mode)")

    tools = _tools_set(fm)
    assert "Agent" not in tools, (
        f"{agent_file.stem} declares dispatched_from: worker (or defaults "
        f"to it) but includes Agent in tools: {sorted(tools)}. Workers "
        f"MUST NOT declare Agent — runtime strips it regardless. Any "
        f"nested Agent() dispatch in the body will silently inline. If "
        f"this agent genuinely dispatches subagents, it must run at T0: "
        f"change dispatched_from to T0, and ensure no caller dispatches "
        f"it via Agent()."
    )


# ── Invariant: no Agent in tools for dispatched-from-absent agents ────────


def test_field_absent_defaults_to_worker_invariant(agent_file):
    """When dispatched_from: is absent, the default is 'worker', so the
    worker invariant (no Agent in tools) applies by default. This catches
    new agents that forgot to declare the field."""
    fm = _parse_frontmatter(agent_file)
    if _is_template_doc(fm, agent_file.stem):
        pytest.skip("reference-doc file")
    if _is_deprecated(fm):
        pytest.skip("deprecated")
    if "dispatched_from" in fm:
        pytest.skip("field declared explicitly; checked by the other tests")

    tools = _tools_set(fm)
    assert "Agent" not in tools, (
        f"{agent_file.stem} has no dispatched_from: field (defaults to "
        f"worker) but includes Agent in tools: {sorted(tools)}. Either "
        f"remove Agent from tools, or add `dispatched_from: T0` to the "
        f"frontmatter to declare this agent as a top-level orchestrator."
    )
