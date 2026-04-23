"""Contract tests for the enriched-context schema that callers pass to
test-failure-analyzer-agent. The schema lives in
`core/.claude/config/e2e-pipeline.yml` under `error_context_enrichment`.
These tests verify:

- The config block exists and has a stable shape.
- Every enriched rule is valid regex with a supported `field`.
- The analyzer agent body documents the schema so downstream callers know
  what to populate — without this documentation, the "enrichment is opt-in"
  contract drifts from what the analyzer actually accepts.
- The analyzer stays a T3 leaf (no MCP tools granted, no Agent dispatch).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "core" / ".claude" / "config" / "e2e-pipeline.yml"
ANALYZER_PATH = (
    REPO_ROOT / "core" / ".claude" / "agents" / "test-failure-analyzer-agent.md"
)
SUPPORTED_FIELDS = {
    "console_messages",
    "network_failures",
    "dom_snapshot",
    "last_url",
    "page_title",
}


@pytest.fixture(scope="module")
def config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def analyzer_body() -> str:
    return ANALYZER_PATH.read_text(encoding="utf-8")


def test_enrichment_block_exists(config):
    assert "error_context_enrichment" in config, (
        "e2e-pipeline.yml must define error_context_enrichment for the analyzer "
        "schema contract"
    )


def test_enrichment_has_schema_version(config):
    block = config["error_context_enrichment"]
    assert "schema_version" in block
    assert re.match(r"^\d+\.\d+\.\d+$", block["schema_version"]), (
        "schema_version must be SemVer"
    )


def test_enrichment_required_is_optional_by_default(config):
    block = config["error_context_enrichment"]
    assert block.get("required") is False, (
        "Enrichment MUST be opt-in so legacy callers without MCP access "
        "continue to work — required=true would break backward compatibility"
    )


def test_enrichment_captured_fields_all_supported(config):
    block = config["error_context_enrichment"]
    fields = set(block["captured_fields"])
    unknown = fields - SUPPORTED_FIELDS
    assert not unknown, f"Unknown captured_fields: {unknown}"


def test_enrichment_rules_compile_as_regex(config):
    rules = config["error_context_enrichment"]["enriched_rules"]
    assert rules, "At least one enriched rule is required"
    for rule in rules:
        assert "id" in rule
        assert "pattern" in rule
        assert "field" in rule
        assert "category" in rule
        assert "confidence" in rule
        try:
            re.compile(rule["pattern"])
        except re.error as exc:
            pytest.fail(f"Rule {rule['id']}: invalid regex — {exc}")


def test_enrichment_rules_target_supported_fields(config):
    for rule in config["error_context_enrichment"]["enriched_rules"]:
        assert rule["field"] in SUPPORTED_FIELDS, (
            f"Rule {rule['id']} targets unsupported field {rule['field']!r}"
        )


def test_enrichment_confidences_in_range(config):
    for rule in config["error_context_enrichment"]["enriched_rules"]:
        conf = rule["confidence"]
        assert 0.0 <= conf <= 1.0, f"Rule {rule['id']} confidence out of range"


def test_analyzer_documents_schema(analyzer_body):
    assert "enriched_context" in analyzer_body, (
        "Analyzer agent must document the enriched_context input schema so "
        "downstream callers know what to pass"
    )
    assert "Stage 0" in analyzer_body or "Input Schema" in analyzer_body


def test_analyzer_classification_source_includes_enriched(analyzer_body):
    assert '"enriched-context-regex"' in analyzer_body, (
        "classification_source enum must include the enriched-context variant "
        "so downstream consumers can distinguish it from plain deterministic-regex"
    )


def test_analyzer_declares_t3_leaf_purity(analyzer_body):
    frontmatter_match = re.search(r"^---\n(.*?)\n---", analyzer_body, re.DOTALL)
    assert frontmatter_match, "Analyzer must have YAML frontmatter"
    frontmatter = frontmatter_match.group(1)
    tools_match = re.search(r"tools:\s*(\[.*?\])", frontmatter, re.DOTALL)
    assert tools_match, "Analyzer frontmatter must declare `tools:`"
    tools = tools_match.group(1)
    assert "Agent" not in tools, (
        "T3 leaf analyzer MUST NOT have Agent in its tools — enrichment is "
        "provided by dispatchers, not fetched by the analyzer itself"
    )
    assert "mcp__" not in tools, (
        "T3 leaf analyzer MUST NOT call MCP tools — live browser signals "
        "must arrive pre-captured via enriched_context"
    )


def test_analyzer_version_bumped(analyzer_body):
    version_match = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', analyzer_body)
    assert version_match, "Analyzer must declare a SemVer version"
    version = version_match.group(1)
    major, minor, _ = (int(p) for p in version.split("."))
    assert major >= 2, f"Analyzer version {version} — expected >= 2.0.0"
    assert (major, minor) >= (2, 1), (
        f"Analyzer version {version} — adding the enriched_context schema is a "
        "MINOR bump (new additive capability). Expected >= 2.1.0."
    )
