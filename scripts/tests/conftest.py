"""Shared test fixtures for best practices hub scripts."""

import json
from pathlib import Path

import pytest
import yaml


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def sample_registry():
    with open(FIXTURES_DIR / "sample_registry.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_urls():
    with open(FIXTURES_DIR / "sample_urls.yml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_skill_path():
    return FIXTURES_DIR / "sample_skill" / "SKILL.md"


@pytest.fixture
def invalid_skill_path():
    return FIXTURES_DIR / "invalid_skill" / "SKILL.md"


@pytest.fixture
def duplicate_skill_path():
    return FIXTURES_DIR / "duplicate_skill" / "SKILL.md"


@pytest.fixture
def sample_webpage():
    with open(FIXTURES_DIR / "sample_webpage.html") as f:
        return f.read()


@pytest.fixture
def temp_registry(tmp_path):
    """Create a temporary registry for write tests."""
    registry = {
        "_meta": {"version": "1.0.0", "last_updated": "2026-03-09", "total_patterns": 0}
    }
    path = tmp_path / "patterns.json"
    path.write_text(json.dumps(registry, indent=2))
    return path
