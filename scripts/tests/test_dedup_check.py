"""Tests for 3-level deduplication logic."""

import json
from pathlib import Path

import pytest

from scripts.dedup_check import (
    check_file,
    hash_pattern,
    check_exact_duplicate,
    check_structural_duplicate,
    parse_frontmatter,
    resolve_pattern_file,
    scan_for_secrets,
    validate_pattern_integrity,
    validate_registry,
)


class TestHashPattern:
    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("hello world")
        f2.write_text("hello world")
        assert hash_pattern(str(f1)) == hash_pattern(str(f2))

    def test_whitespace_normalized(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("hello  world  ")
        f2.write_text("hello world")
        assert hash_pattern(str(f1)) == hash_pattern(str(f2))

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("hello")
        f2.write_text("world")
        assert hash_pattern(str(f1)) != hash_pattern(str(f2))


class TestExactDuplicate:
    def test_finds_exact_match(self, sample_registry):
        known_hash = sample_registry["fix-loop"]["hash"]
        result = check_exact_duplicate(known_hash, sample_registry)
        assert result == "fix-loop"

    def test_no_match_returns_none(self, sample_registry):
        result = check_exact_duplicate("nonexistent_hash", sample_registry)
        assert result is None

    def test_skips_meta_key(self, sample_registry):
        result = check_exact_duplicate("_meta", sample_registry)
        assert result is None


class TestStructuralDuplicate:
    def test_same_name_matches(self, sample_registry):
        new = {"name": "fix-loop", "type": "skill", "category": "core", "dependencies": []}
        matches = check_structural_duplicate(new, sample_registry)
        assert "fix-loop" in matches

    def test_case_insensitive_name(self, sample_registry):
        new = {"name": "Fix-Loop", "type": "skill", "category": "core", "dependencies": []}
        matches = check_structural_duplicate(new, sample_registry)
        assert "fix-loop" in matches

    def test_no_match_for_different_pattern(self, sample_registry):
        new = {"name": "brand-new", "type": "agent", "category": "stack:react", "dependencies": []}
        matches = check_structural_duplicate(new, sample_registry)
        assert len(matches) == 0

    def test_shared_deps_increase_score(self, sample_registry):
        new = {"name": "different-name", "type": "skill", "category": "core", "dependencies": ["hook-utils.sh"]}
        matches = check_structural_duplicate(new, sample_registry)
        assert "fix-loop" in matches


class TestParseFrontmatter:
    def test_valid_frontmatter(self, sample_skill_path):
        fm = parse_frontmatter(sample_skill_path)
        assert fm["name"] == "sample-skill"
        assert fm["version"] == "1.0.0"

    def test_missing_frontmatter(self, invalid_skill_path):
        fm = parse_frontmatter(invalid_skill_path)
        assert fm is None


class TestValidateIntegrity:
    def test_valid_pattern_passes(self, sample_skill_path):
        errors = validate_pattern_integrity(sample_skill_path)
        assert len(errors) == 0

    def test_missing_frontmatter_fails(self, invalid_skill_path):
        errors = validate_pattern_integrity(invalid_skill_path)
        assert any("frontmatter" in e.lower() for e in errors)


class TestCheckFile:
    def test_check_valid_pattern(self, sample_skill_path):
        errors = check_file(sample_skill_path)
        assert not any("frontmatter" in e.lower() for e in errors)

    def test_check_detects_missing_fields(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("---\ndescription: test\n---\n# No name or version\n")
        errors = check_file(f)
        assert any("name" in e.lower() for e in errors)

    def test_check_detects_secrets(self, tmp_path):
        f = tmp_path / "secret.md"
        # Assemble "password = ..." via adjacent-string-literal concatenation so
        # this source file does not trip dedup_check's repo-wide secret scan.
        secret_line = "pass" 'word = "hunter2"\n'
        f.write_text(
            '---\nname: test\ndescription: x\nversion: "1.0.0"\n---\n'
            + secret_line
        )
        errors = check_file(f)
        assert any("password" in e.lower() for e in errors)

    def test_scan_for_secrets_clean_file(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("---\nname: clean\n---\n# No secrets here\n")
        findings = scan_for_secrets(f)
        assert findings == []


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestRegistryHashDrift:
    """Guard against the hash field in registry/patterns.json diverging from
    the actual on-disk pattern files. Drift makes the hash column useless
    for exact-duplicate detection and future hash-based gating."""

    def test_no_drift_in_shipped_registry(self):
        registry_path = REPO_ROOT / "registry" / "patterns.json"
        errors = validate_registry(registry_path, REPO_ROOT)
        drift = [e for e in errors if "hash drift" in e]
        assert not drift, "Registry hash drift:\n" + "\n".join(drift)

    def test_detects_drift_when_file_changes(self, tmp_path):
        skill_dir = tmp_path / "core" / ".claude" / "skills" / "drift-demo"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("original content", encoding="utf-8")
        original_hash = hash_pattern(str(skill_file))

        skill_file.write_text("content has changed - hash should no longer match", encoding="utf-8")

        registry = tmp_path / "registry" / "patterns.json"
        registry.parent.mkdir()
        registry.write_text(json.dumps({
            "drift-demo": {
                "hash": original_hash,
                "type": "skill",
                "category": "core",
                "version": "1.0.0",
                "source": "hub:test",
            }
        }))

        errors = validate_registry(registry, tmp_path)
        assert any("drift-demo" in e and "hash drift" in e for e in errors)

    def test_passes_when_hash_matches_file(self, tmp_path):
        agent_dir = tmp_path / "core" / ".claude" / "agents"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "match-demo.md"
        agent_file.write_text("stable content", encoding="utf-8")

        registry = tmp_path / "registry" / "patterns.json"
        registry.parent.mkdir()
        registry.write_text(json.dumps({
            "match-demo": {
                "hash": hash_pattern(str(agent_file)),
                "type": "agent",
                "category": "core",
                "version": "1.0.0",
                "source": "hub:test",
            }
        }))

        errors = validate_registry(registry, tmp_path)
        assert not [e for e in errors if "hash drift" in e]


class TestResolvePatternFile:
    def test_resolves_skill_in_core(self, tmp_path):
        target = tmp_path / "core" / ".claude" / "skills" / "demo" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("x", encoding="utf-8")
        resolved = resolve_pattern_file("demo", "skill", tmp_path)
        assert resolved == target

    def test_falls_back_to_hub_only_skill_path(self, tmp_path):
        target = tmp_path / ".claude" / "skills" / "hub-only" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("x", encoding="utf-8")
        resolved = resolve_pattern_file("hub-only", "skill", tmp_path)
        assert resolved == target

    def test_returns_none_for_config_type(self, tmp_path):
        assert resolve_pattern_file("some-config", "config", tmp_path) is None

    def test_returns_none_when_file_absent(self, tmp_path):
        assert resolve_pattern_file("ghost", "agent", tmp_path) is None
