"""Tests for effectiveness-aware tier adjustment in recommend.py."""

import json
from pathlib import Path

import pytest

from scripts.recommend import (
    tier_resource_with_reason,
    _load_tier_registry,
    effectiveness_tier_adjustment,
)


@pytest.fixture(autouse=True)
def _clear_tier_cache():
    """Clear the tier registry cache between tests."""
    _load_tier_registry._cache = {}
    yield
    _load_tier_registry._cache = {}


@pytest.fixture
def registry_with_effectiveness(tmp_path):
    """Registry where some patterns have effectiveness data."""
    registry = {
        "_meta": {"version": "3.0.0", "total_patterns": 4},
        "high-adoption-skill": {
            "type": "skill",
            "tier": "nice-to-have",
            "effectiveness": {
                "adoption_rate": 0.9,
                "retention_days_p50": 45,
                "sample_size": 5,
                "last_updated": "2026-03-31",
            },
        },
        "low-adoption-skill": {
            "type": "skill",
            "tier": "must-have",
            "effectiveness": {
                "adoption_rate": 0.2,
                "retention_days_p50": 3,
                "sample_size": 5,
                "last_updated": "2026-03-31",
            },
        },
        "insufficient-data-skill": {
            "type": "skill",
            "tier": "must-have",
            "effectiveness": {
                "adoption_rate": 0.1,
                "sample_size": 1,
                "last_updated": "2026-03-31",
            },
        },
        "no-effectiveness-skill": {
            "type": "skill",
            "tier": "must-have",
        },
    }
    path = tmp_path / "registry" / "patterns.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(registry, indent=2))
    return tmp_path


# --- Tests: effectiveness_tier_adjustment ---


class TestEffectivenessTierAdjustment:
    """Test that effectiveness data influences tier recommendations."""

    def test_high_adoption_promotes(self):
        """Pattern with high adoption rate gets 'promote' signal."""
        eff = {"adoption_rate": 0.9, "sample_size": 5}
        adjustment = effectiveness_tier_adjustment(eff)
        assert adjustment == "promote"

    def test_low_adoption_demotes(self):
        """Pattern with low adoption rate (< 0.3) across sufficient samples gets 'demote'."""
        eff = {"adoption_rate": 0.2, "sample_size": 5}
        adjustment = effectiveness_tier_adjustment(eff)
        assert adjustment == "demote"

    def test_insufficient_sample_returns_none(self):
        """Fewer than 3 projects = insufficient data, no adjustment."""
        eff = {"adoption_rate": 0.1, "sample_size": 2}
        adjustment = effectiveness_tier_adjustment(eff)
        assert adjustment is None

    def test_medium_adoption_no_change(self):
        """Adoption between 0.3 and 0.7 = neutral, no adjustment."""
        eff = {"adoption_rate": 0.5, "sample_size": 5}
        adjustment = effectiveness_tier_adjustment(eff)
        assert adjustment is None

    def test_no_effectiveness_data_returns_none(self):
        adjustment = effectiveness_tier_adjustment({})
        assert adjustment is None

    def test_missing_adoption_rate_returns_none(self):
        eff = {"sample_size": 5}
        adjustment = effectiveness_tier_adjustment(eff)
        assert adjustment is None

    # --- Boundary value tests ---

    def test_boundary_adoption_exactly_0_3_is_neutral(self):
        """Adoption rate exactly 0.3 should NOT demote (exclusive lower bound)."""
        eff = {"adoption_rate": 0.3, "sample_size": 5}
        assert effectiveness_tier_adjustment(eff) is None

    def test_boundary_adoption_exactly_0_7_promotes(self):
        """Adoption rate exactly 0.7 SHOULD promote (inclusive upper bound)."""
        eff = {"adoption_rate": 0.7, "sample_size": 5}
        assert effectiveness_tier_adjustment(eff) == "promote"

    def test_boundary_sample_size_exactly_3_is_eligible(self):
        """Sample size exactly 3 meets the minimum threshold."""
        eff = {"adoption_rate": 0.9, "sample_size": 3}
        assert effectiveness_tier_adjustment(eff) == "promote"

    # --- Type guard tests ---

    def test_string_adoption_rate_returns_none(self):
        """String adoption_rate should not crash, returns None."""
        eff = {"adoption_rate": "0.9", "sample_size": 5}
        assert effectiveness_tier_adjustment(eff) is None

    def test_nan_adoption_rate_returns_none(self):
        """NaN adoption_rate should not produce wrong comparisons."""
        eff = {"adoption_rate": float("nan"), "sample_size": 5}
        assert effectiveness_tier_adjustment(eff) is None

    def test_string_sample_size_returns_none(self):
        eff = {"adoption_rate": 0.5, "sample_size": "5"}
        assert effectiveness_tier_adjustment(eff) is None


class TestTierWithEffectiveness:
    """Test that tier_resource_with_reason integrates effectiveness signals."""

    def test_low_adoption_adds_warning_to_reason(self, registry_with_effectiveness):
        """Low adoption pattern gets a reason that mentions effectiveness."""
        _load_tier_registry(registry_with_effectiveness)
        tier, reason = tier_resource_with_reason("low-adoption-skill", "skill", [])
        # Should still return the registry tier but with effectiveness warning
        assert "effectiveness" in reason.lower() or "adoption" in reason.lower()

    def test_high_adoption_noted_in_reason(self, registry_with_effectiveness):
        """High adoption pattern gets positive effectiveness note."""
        _load_tier_registry(registry_with_effectiveness)
        tier, reason = tier_resource_with_reason("high-adoption-skill", "skill", [])
        assert "effectiveness" in reason.lower() or "adoption" in reason.lower()

    def test_no_effectiveness_unchanged(self, registry_with_effectiveness):
        """Pattern without effectiveness data uses standard tiering."""
        _load_tier_registry(registry_with_effectiveness)
        tier, reason = tier_resource_with_reason("no-effectiveness-skill", "skill", [])
        assert tier == "must-have"
        assert "registry tier" in reason
