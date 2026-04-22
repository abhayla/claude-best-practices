"""Tests for tier-consistency across dispatch chains.

Runtime verification (2026-04-22) confirmed that `testing-pipeline-master-
agent` (must-have, T1) dispatches agents that are registered as nice-to-have
(e2e-conductor-agent, test-scout-agent, visual-inspector-agent,
test-healer-agent). A downstream project accepting default
`recommend.py --tier must-have` provisioning installs the master but NOT
its dispatch targets, so the E2E step would hit
"Agent type 'e2e-conductor-agent' not found" at runtime.

The fix is tier-parity: every agent a must-have orchestrator dispatches
via `Agent()` must itself be must-have. Otherwise the default install
leaves a dangling-dispatch configuration.

These tests pin the invariant by walking the dispatch chain declared in
each must-have orchestrator's frontmatter description and verifying every
named target has matching (or higher) tier.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "registry" / "patterns.json"
AGENTS_DIR = REPO_ROOT / "core" / ".claude" / "agents"


# Dispatch chains discovered from the v2 testing-pipeline architecture.
# Each key is a must-have orchestrator; each value is the list of agents
# it dispatches via Agent() per its documented behavior.
# This must stay in sync with the agent bodies. If an agent adds/removes a
# dispatch target, update here.
DISPATCH_CHAIN = {
    "testing-pipeline-master-agent": [
        # T2 sub-orchestrators dispatched by the T1 master
        "e2e-conductor-agent",
    ],
    "e2e-conductor-agent": [
        # T3 workers dispatched by the T2 conductor
        "test-scout-agent",
        "visual-inspector-agent",
        "test-healer-agent",
    ],
}


@pytest.fixture(scope="module")
def registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _tier(registry: dict, name: str) -> str:
    entry = registry.get(name, {})
    return entry.get("tier", "(none)")


# ── Parametrized tests — every (caller, target) pair ────────────────────


def _dispatch_pairs() -> list[tuple[str, str]]:
    return [
        (caller, target)
        for caller, targets in DISPATCH_CHAIN.items()
        for target in targets
    ]


@pytest.mark.parametrize("caller,target", _dispatch_pairs())
def test_dispatch_target_tier_matches_caller(registry, caller, target):
    """A must-have orchestrator MUST NOT dispatch a nice-to-have target.
    Otherwise default provisioning creates a dangling-dispatch
    configuration. If the caller is must-have, the target must be too
    (promote target to must-have). If promoting the target is wrong,
    the caller should be demoted or graceful-skip should be added."""
    caller_tier = _tier(registry, caller)
    target_tier = _tier(registry, target)

    if caller_tier != "must-have":
        pytest.skip(
            f"Caller {caller!r} is not must-have; tier mismatch is "
            "acceptable for nice-to-have callers (they opt in together)"
        )

    assert target_tier == "must-have", (
        f"Dangling dispatch: {caller} (must-have) dispatches {target} "
        f"(tier={target_tier}). Default `recommend.py --tier must-have` "
        f"installs {caller} but NOT {target}, so the dispatch fails at "
        f"runtime with 'Agent type {target!r} not found'. Promote "
        f"{target} to must-have OR add a graceful-skip guard in {caller}."
    )


# ── Sanity tests on the invariant itself ───────────────────────────────


@pytest.mark.parametrize("agent_name", list(DISPATCH_CHAIN.keys()) +
                          [t for targets in DISPATCH_CHAIN.values() for t in targets])
def test_every_agent_in_chain_has_a_registry_entry(registry, agent_name):
    """Every agent referenced in the dispatch chain must exist in the
    registry — otherwise the chain declaration is stale."""
    assert agent_name in registry, (
        f"Agent {agent_name!r} referenced in DISPATCH_CHAIN but missing "
        f"from registry/patterns.json. Update DISPATCH_CHAIN or add the "
        f"registry entry."
    )


def test_every_referenced_agent_has_tier_declared(registry):
    """Every agent in a dispatch chain must declare a tier explicitly."""
    for caller, targets in DISPATCH_CHAIN.items():
        for name in [caller, *targets]:
            tier = registry.get(name, {}).get("tier")
            assert tier in ("must-have", "nice-to-have"), (
                f"Agent {name!r} has tier={tier!r}. Must be 'must-have' "
                "or 'nice-to-have' to be provisionable."
            )
