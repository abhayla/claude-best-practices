"""Tier-A workflow validation: registry dependency-closure consistency.

Locks in the development-loop-class fix (PRs #49/#54/#55/#56): a workflow/
orchestrator skill that dispatches a worker agent via Agent(subagent_type=...)
MUST declare that agent in its registry `dependencies`, or provisioning ships
the skill without its worker. Also guards that no pattern declares a deprecated
dependency. These run repo-wide so the defect class cannot regress.
"""
import json
import re
import pathlib

import pytest

HUB = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = json.loads((HUB / "registry" / "patterns.json").read_text(encoding="utf-8"))
# Built-in Claude Code agents are not hub patterns and are correctly never deps.
BUILTIN_AGENTS = {"Explore", "Plan", "general-purpose"}

_DEPRECATED = {k for k, v in REGISTRY.items()
               if isinstance(v, dict) and v.get("deprecated")}


def _frontmatter_type(body: str) -> str | None:
    m = re.search(r"^type:\s*(\w+)", body, re.MULTILINE)
    return m.group(1) if m else None


def _agent_dispatching_workflow_skills():
    """Names of non-deprecated, non-reference skills that actually dispatch agents."""
    out = []
    for sp in sorted((HUB / "core" / ".claude" / "skills").glob("*/SKILL.md")):
        name = sp.parent.name
        entry = REGISTRY.get(name, {})
        if not isinstance(entry, dict) or entry.get("deprecated"):
            continue
        body = sp.read_text(encoding="utf-8")
        if _frontmatter_type(body) == "reference":
            # reference/guide skills may show illustrative dispatches, not runtime ones
            continue
        agents = {a for a in re.findall(r'subagent_type=["\']([a-z0-9-]+)["\']', body)
                  if a not in BUILTIN_AGENTS}
        if agents:
            out.append(name)
    return out


@pytest.mark.parametrize("name", _agent_dispatching_workflow_skills())
def test_dispatched_agents_declared_in_closure(name):
    body = (HUB / "core" / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    dispatched = {a for a in re.findall(r'subagent_type=["\']([a-z0-9-]+)["\']', body)
                  if a not in BUILTIN_AGENTS}
    # only registry-known agents are provisionable deps
    known = {a for a in dispatched if a in REGISTRY}
    deps = set(REGISTRY.get(name, {}).get("dependencies", []))
    missing = sorted(known - deps)
    assert not missing, (
        f"{name} dispatches {missing} via Agent() but they are NOT in its registry "
        f"`dependencies` — provisioning would ship {name} without these workers."
    )


def test_no_pattern_declares_a_deprecated_dependency():
    bad = {}
    for name, entry in REGISTRY.items():
        if not isinstance(entry, dict) or name == "_meta":
            continue
        depr = sorted(set(entry.get("dependencies", [])) & _DEPRECATED)
        if depr:
            bad[name] = depr
    assert not bad, f"patterns declaring deprecated dependencies: {bad}"


def test_at_least_the_known_workflows_are_covered():
    # guard against the discovery regex silently matching nothing
    covered = set(_agent_dispatching_workflow_skills())
    assert {"development-loop", "test-pipeline"} <= covered, (
        f"expected core workflows in coverage set, got {sorted(covered)}"
    )
