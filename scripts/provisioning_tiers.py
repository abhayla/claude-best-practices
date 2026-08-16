import json
from pathlib import Path
from typing import Optional

from scripts.hub_resources import is_stack_specific, matches_stacks


MUST_HAVE_HOOKS = {"dangerous-command-blocker", "secret-scanner"}


CORE_WORKFLOW_SKILLS = {
    "implement", "fix-loop", "fix-github-issue", "tdd", "auto-verify",
    "systematic-debugging", "continue", "handover", "skill-master",
    "pr-standards", "request-code-review", "receive-code-review",
    "code-quality-gate", "writing-plans", "executing-plans",
    "verify-screenshots", "post-fix-pipeline", "test-pipeline",
    "regression-test", "prompt-auto-enhance", "e2e-best-practices",
    "e2e-visual-run",
}


MUST_HAVE_UNIVERSAL_SKILLS = CORE_WORKFLOW_SKILLS  # backward compat alias


NICE_TO_HAVE_UNIVERSAL_SKILLS = {
    "security-audit",
    "adversarial-review",
    "branching",
    "git-worktrees",
    "brainstorm",
    "subagent-driven-dev",
    "batch",
    "supply-chain-audit",
    "learn-n-improve",
    "twitter-x",
    "reddit",
    "github",
}


MUST_HAVE_RULES = {"context-management", "workflow", "claude-behavior", "testing", "tdd-rule"}


MUST_HAVE_AGENTS = {"security-auditor-agent", "tester-agent"}


ALWAYS_SKIP = {
    "contribute-practice",
    "obsidian", "mcp-server-builder",
    # solidity-audit removed 2026-05-24: reclassified as need-basis (Ethereum stack).
    # Behavior preserved via registry tier=skip in patterns.json; if a Solidity stack
    # detector is added later, it can promote via dep_promoted set.
}


NICE_TO_HAVE_STACK_OVERRIDES = {
    "firebase-data-connect",  # PostgreSQL + GraphQL — most Firebase projects don't use this
    "xml-to-compose",         # Only needed for XML-to-Compose migration, not greenfield
}


RESOURCE_STACK_REQUIREMENTS: dict[str, set[str]] = {
    # Rules
    "android": {"android-compose"},
    "vue": {"react-nextjs"},        # Vue projects detected via deps, not STACK_DETECTORS
    "flutter": {"android-compose"}, # Flutter projects detected via deps
    "firebase": {"firebase-auth"},
    "bun-elysia": set(),            # No stack detector — requires elysia dep
    "hono-conventions": set(),      # No stack detector — requires hono dep
    "prisma-conventions": set(),    # No stack detector — requires prisma dep
    "vue-e2e": set(),               # No stack detector — requires vuetify dep
    "fastapi-backend": {"fastapi-python"},
    "fastapi-database": {"fastapi-python"},
    # Agents
    "android-build-fixer-agent": {"android-compose"},
    "android-compose-agent": {"android-compose"},
    "android-kotlin-reviewer-agent": {"android-compose"},
}


def _load_tier_registry(hub_root: Path | None = None) -> dict[str, dict]:
    """Load registry/patterns.json for tier lookups. Cached after first load."""
    if not hasattr(_load_tier_registry, "_cache"):
        _load_tier_registry._cache = {}
    if hub_root and not _load_tier_registry._cache:
        path = hub_root / "registry" / "patterns.json"
        if path.exists():
            _load_tier_registry._cache = json.loads(path.read_text(encoding="utf-8"))
    return _load_tier_registry._cache


def tier_resource(name: str, resource_type: str, stacks: list[str], dep_promoted: set[str] | None = None) -> str:
    """Assign a tier to a missing resource: must-have, nice-to-have, or skip.

    Args:
        dep_promoted: Set of pattern names promoted by dependency detection.
            If a pattern is in this set, it overrides ALWAYS_SKIP and wrong-stack.

    Returns one of: 'must-have', 'nice-to-have', 'skip'.
    """
    tier, _ = tier_resource_with_reason(name, resource_type, stacks, dep_promoted)
    return tier


def effectiveness_tier_adjustment(eff: dict) -> Optional[str]:
    """Compute tier adjustment signal from effectiveness data.

    Returns:
        'promote' if high adoption (>= 0.7) across sufficient samples (>= 3).
        'demote' if low adoption (< 0.3) across sufficient samples (>= 3).
        None if insufficient data, neutral adoption, or invalid types.

    Boundary behavior:
        adoption_rate=0.3 → None (neutral, not demoted)
        adoption_rate=0.7 → 'promote' (inclusive upper threshold)
        sample_size=3 → eligible (minimum required)
    """
    if not eff:
        return None

    adoption = eff.get("adoption_rate")
    sample = eff.get("sample_size", 0)

    # Type guards: reject non-numeric values
    if not isinstance(adoption, (int, float)) or not isinstance(sample, (int, float)):
        return None

    # Guard against NaN
    if adoption != adoption or sample != sample:  # NaN != NaN
        return None

    if sample < 3:
        return None

    if adoption >= 0.7:
        return "promote"
    elif adoption < 0.3:
        return "demote"

    return None


def tier_resource_with_reason(
    name: str, resource_type: str, stacks: list[str], dep_promoted: set[str] | None = None,
) -> tuple[str, str]:
    """Assign a tier and reason to a missing resource.

    Tiering priority:
    1. Dependency promotion (overrides everything)
    2. Always-skip list
    3. Wrong-stack detection
    4. Registry `tier` field (SSOT — every pattern must have this)
    5. Effectiveness data (advisory — appended to reason, does not override tier)

    The registry is the single source of truth for tier classification.
    CI validator (validate_registry_tiers) enforces that every pattern
    in registry/patterns.json has a valid tier field.

    Returns (tier, reason) where tier is 'must-have', 'nice-to-have', or 'skip'.
    """
    # Dependency promotion overrides ALWAYS_SKIP and wrong-stack
    if dep_promoted and name in dep_promoted:
        return "must-have", "dependency detected in project"

    # Always-skip list
    if name in ALWAYS_SKIP:
        return "skip", "always-skip list"

    # Wrong-stack resources (prefix-based detection)
    if is_stack_specific(name) and not matches_stacks(name, stacks):
        return "skip", "wrong stack"

    # Wrong-stack resources (non-prefixed but stack-bound)
    if name in RESOURCE_STACK_REQUIREMENTS:
        required_stacks = RESOURCE_STACK_REQUIREMENTS[name]
        if required_stacks and not required_stacks.intersection(stacks):
            return "skip", "wrong stack"
        if not required_stacks:
            # Empty set means "requires dep detection only" — skip if not dep-promoted
            return "skip", "wrong stack"

    # Registry-driven tiering — SINGLE SOURCE OF TRUTH
    # Every pattern in registry/patterns.json must have a tier field.
    # CI validator (validate_registry_tiers) enforces this.
    registry = _load_tier_registry()
    if name in registry and isinstance(registry[name], dict):
        reg_tier = registry[name].get("tier")
        if reg_tier in ("must-have", "nice-to-have", "skip"):
            # Append effectiveness signal to reason if available
            eff = registry[name].get("effectiveness", {})
            adjustment = effectiveness_tier_adjustment(eff)
            if adjustment == "promote":
                adoption = eff.get("adoption_rate", 0)
                return reg_tier, f"registry tier ({reg_tier}); high effectiveness adoption ({adoption:.0%})"
            elif adjustment == "demote":
                adoption = eff.get("adoption_rate", 0)
                return reg_tier, f"registry tier ({reg_tier}); low effectiveness adoption ({adoption:.0%})"
            return reg_tier, f"registry tier ({reg_tier})"

    # Config files inherit the tier of their associated skill.
    if resource_type == "config":
        CONFIG_SKILL_MAP = {
            "e2e-pipeline": "e2e-visual-run",
            "test-pipeline": "test-pipeline",
        }
        associated_skill = CONFIG_SKILL_MAP.get(name)
        if associated_skill:
            skill_tier, skill_reason = tier_resource_with_reason(
                associated_skill, "skill", stacks, dep_promoted
            )
            return skill_tier, f"runtime config for {associated_skill}"

    # Default for patterns not yet in registry (shouldn't happen if CI passes)
    return "nice-to-have", "not in registry (add tier field to patterns.json)"
