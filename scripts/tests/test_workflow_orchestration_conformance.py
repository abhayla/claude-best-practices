"""Orchestration-protocol conformance guard for the skill-at-T0 workflows.

Senior-QA verification turned into a permanent gate. For each workflow declared
in config/workflow-contracts.yaml, asserts the platform's orchestration contract
(agent-orchestration.md):
  - contract `master_agent` is null (orchestration lives in the skill, Phase 3.x)
  - the entry skill grants `Agent` in allowed-tools (T0 orchestrator) if it dispatches
  - it never dispatches a deprecated agent (e.g. a retired *-master-agent)
  - its canonical `state_file` is referenced in the skill body (single state SSOT)
  - frontmatter `type: workflow`
  - no WORKER PROMPT instructs further dispatch (single-level dispatch)
"""
import json
import re
import pathlib

import pytest
import yaml

HUB = pathlib.Path(__file__).resolve().parents[2]
CONTRACTS = yaml.safe_load(
    (HUB / "config" / "workflow-contracts.yaml").read_text(encoding="utf-8")
)["workflows"]
REGISTRY = json.loads((HUB / "registry" / "patterns.json").read_text(encoding="utf-8"))
DEPRECATED = {k for k, v in REGISTRY.items() if isinstance(v, dict) and v.get("deprecated")}
BUILTIN_AGENTS = {"Explore", "Plan", "general-purpose"}

WORKFLOWS = sorted(CONTRACTS.keys())


def _entry_body(wf):
    entry = CONTRACTS[wf].get("entry_skill", wf)
    p = HUB / "core" / ".claude" / "skills" / entry / "SKILL.md"
    return (entry, p.read_text(encoding="utf-8")) if p.exists() else (entry, None)


@pytest.mark.parametrize("wf", WORKFLOWS)
def test_contract_master_agent_is_null(wf):
    assert CONTRACTS[wf].get("master_agent") is None, (
        f"{wf}: contract master_agent must be null (skill-at-T0); "
        f"got {CONTRACTS[wf].get('master_agent')!r}"
    )


@pytest.mark.parametrize("wf", WORKFLOWS)
def test_entry_skill_conformance(wf):
    entry, body = _entry_body(wf)
    if body is None:
        pytest.skip(f"{wf}: entry_skill '{entry}' has no SKILL.md")
    dispatched = {d for d in re.findall(r'subagent_type=["\']([a-z0-9-]+)["\']', body)
                  if d not in BUILTIN_AGENTS}
    fm = re.search(r'^allowed-tools:\s*"([^"]*)"', body, re.MULTILINE)
    tools = fm.group(1) if fm else ""

    if dispatched:
        assert "Agent" in tools, f"{wf}: dispatches workers but allowed-tools lacks Agent"
    bad = sorted(dispatched & DEPRECATED)
    assert not bad, f"{wf}: dispatches DEPRECATED agent(s) {bad}"
    assert re.search(r"^type:\s*workflow", body, re.MULTILINE), f"{wf}: frontmatter type != workflow"

    sf = CONTRACTS[wf].get("state_file")
    if sf:
        assert sf in body or sf.split("/")[-1] in body, (
            f"{wf}: canonical state_file '{sf}' not referenced in skill body"
        )


@pytest.mark.parametrize("wf", WORKFLOWS)
def test_no_nested_dispatch_in_worker_prompts(wf):
    entry, body = _entry_body(wf)
    if body is None:
        pytest.skip(f"{wf}: no SKILL.md")
    blocks = re.findall(r'subagent_type=["\']([a-z0-9-]+)["\'],\s*prompt="""(.*?)"""', body, re.S)
    offenders = [agent for agent, prompt in blocks
                 if re.search(r'subagent_type=|\bAgent\(', prompt)
                 or re.search(r'\bdispatch\b.*\bagent\b', prompt, re.IGNORECASE)]
    assert not offenders, (
        f"{wf}: worker prompt(s) {offenders} instruct further dispatch — "
        f"workers cannot spawn subagents (single-level dispatch)."
    )
