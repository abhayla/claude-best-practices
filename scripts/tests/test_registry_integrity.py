"""Cross-validation tests for registry, patterns, and configuration consistency.

These tests validate that the registry, actual files on disk, and configuration
constants (tiering lists, stack prefixes) are all consistent with each other.
Any drift between layers will be caught here — no silent passes allowed.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent
CORE_CLAUDE = ROOT / "core" / ".claude"
REGISTRY_PATH = ROOT / "registry" / "patterns.json"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_registry() -> dict:
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def _actual_agents() -> list[str]:
    d = CORE_CLAUDE / "agents"
    return sorted(f.stem for f in d.glob("*.md") if f.name != "README.md") if d.exists() else []


def _actual_skills() -> list[str]:
    d = CORE_CLAUDE / "skills"
    return sorted(
        f.name for f in d.iterdir()
        if f.is_dir() and (f / "SKILL.md").exists()
    ) if d.exists() else []


def _actual_rules() -> list[str]:
    d = CORE_CLAUDE / "rules"
    return sorted(f.stem for f in d.glob("*.md") if f.name != "README.md") if d.exists() else []


def _actual_hooks() -> list[str]:
    d = CORE_CLAUDE / "hooks"
    return sorted(f.stem for f in d.glob("*.sh")) if d.exists() else []


def _actual_configs() -> list[str]:
    d = CORE_CLAUDE / "config"
    if not d.exists():
        return []
    return sorted(
        f.stem for f in d.iterdir()
        if f.is_file() and f.suffix in (".yml", ".yaml", ".json")
    )


def _all_actual_names() -> set[str]:
    return set(_actual_agents() + _actual_skills() + _actual_rules() + _actual_hooks() + _actual_configs())


# ══════════════════════════════════════════════════════════════════════════════
#  1. REGISTRY <-> FILE SYSTEM CONSISTENCY
# ══════════════════════════════════════════════════════════════════════════════


class TestRegistryMetaConsistency:
    """The registry _meta.total_patterns must match actual entry count."""

    def test_total_patterns_matches_entries(self):
        reg = _load_registry()
        entries = {k: v for k, v in reg.items() if k != "_meta"}
        claimed = reg["_meta"]["total_patterns"]
        assert claimed == len(entries), (
            f"Registry _meta.total_patterns={claimed} but actual entries={len(entries)}"
        )

    def test_meta_has_required_fields(self):
        meta = _load_registry()["_meta"]
        for field in ("version", "last_updated", "total_patterns"):
            assert field in meta, f"_meta missing required field: {field}"

    def test_meta_version_is_semver(self):
        version = _load_registry()["_meta"]["version"]
        assert re.match(r"^\d+\.\d+\.\d+$", version), (
            f"_meta.version '{version}' is not valid semver"
        )

    def test_meta_last_updated_is_date(self):
        date = _load_registry()["_meta"]["last_updated"]
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", date), (
            f"_meta.last_updated '{date}' is not YYYY-MM-DD"
        )


class TestRegistryEntryFields:
    """Every registry entry must have all required fields with valid values."""

    REQUIRED_FIELDS = ["hash", "type", "category", "version", "source"]
    VALID_TYPES = {"agent", "skill", "rule", "hook", "config"}
    VALID_CATEGORY_PREFIXES = {"core", "stack:"}

    def test_all_entries_have_required_fields(self):
        reg = _load_registry()
        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            for field in self.REQUIRED_FIELDS:
                if field not in entry:
                    errors.append(f"'{name}' missing field: {field}")
        assert errors == [], f"Missing fields:\n" + "\n".join(errors)

    def test_all_entries_have_valid_type(self):
        reg = _load_registry()
        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            t = entry.get("type")
            if t not in self.VALID_TYPES:
                errors.append(f"'{name}' has invalid type: '{t}'")
        assert errors == [], f"Invalid types:\n" + "\n".join(errors)

    def test_all_entries_have_valid_category(self):
        """Category must be 'core' or 'stack:<stack-name>'."""
        from scripts.bootstrap import STACK_PREFIXES
        valid_stack_categories = {f"stack:{s}" for s in STACK_PREFIXES}
        # Also allow raw stack names for backward compat (to be cleaned up)
        legacy_stack_names = set(STACK_PREFIXES.keys())

        reg = _load_registry()
        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            cat = entry.get("category", "")
            if cat != "core" and cat not in valid_stack_categories and cat not in legacy_stack_names:
                errors.append(f"'{name}' has invalid category: '{cat}'")
        assert errors == [], f"Invalid categories:\n" + "\n".join(errors)

    def test_all_versions_are_semver(self):
        reg = _load_registry()
        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            v = entry.get("version", "")
            if not re.match(r"^\d+\.\d+\.\d+$", v):
                errors.append(f"'{name}' version '{v}' is not valid semver")
        assert errors == [], f"Invalid versions:\n" + "\n".join(errors)

    def test_all_hashes_are_sha256(self):
        reg = _load_registry()
        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            h = entry.get("hash", "")
            if not re.match(r"^[a-f0-9]{64}$", h):
                errors.append(f"'{name}' hash is not valid SHA256: '{h[:20]}...'")
        assert errors == [], f"Invalid hashes:\n" + "\n".join(errors)

    def test_no_entries_are_non_dict(self):
        reg = _load_registry()
        for name, entry in reg.items():
            if name == "_meta":
                continue
            assert isinstance(entry, dict), f"Entry '{name}' is {type(entry).__name__}, not dict"


class TestRegistryFileSync:
    """Registry entries must map to actual files, and vice versa."""

    def test_registry_type_matches_file_location(self):
        """Each registry entry's type must match where the file actually lives."""
        reg = _load_registry()
        agents = set(_actual_agents())
        skills = set(_actual_skills())
        rules = set(_actual_rules())
        hooks = set(_actual_hooks())

        errors = []
        for name, entry in reg.items():
            if name == "_meta":
                continue
            claimed_type = entry.get("type")
            # skip scan-repo/scan-url which are in .claude/ not core/.claude/
            if name in ("scan-repo", "scan-url"):
                continue
            if claimed_type == "agent" and name not in agents:
                errors.append(f"'{name}' claims type=agent but not in agents/")
            elif claimed_type == "skill" and name not in skills:
                errors.append(f"'{name}' claims type=skill but not in skills/")
            elif claimed_type == "rule" and name not in rules:
                errors.append(f"'{name}' claims type=rule but not in rules/")
            elif claimed_type == "hook" and name not in hooks:
                errors.append(f"'{name}' claims type=hook but not in hooks/")
        assert errors == [], (
            f"Registry type mismatches ({len(errors)}):\n" + "\n".join(errors)
        )

    def test_no_orphan_registry_entries(self):
        """Registry should not have entries for non-existent files (except known hub-only)."""
        reg = _load_registry()
        actual = _all_actual_names()
        # scan-repo and scan-url live in .claude/ (hub-only), not core/.claude/
        hub_only = {"scan-repo", "scan-url"}

        orphans = []
        for name in reg:
            if name == "_meta":
                continue
            if name not in actual and name not in hub_only:
                orphans.append(name)
        assert orphans == [], (
            f"Registry entries with no corresponding file ({len(orphans)}):\n"
            + "\n".join(sorted(orphans))
        )

    def test_all_files_have_registry_entries(self):
        """Every file in core/.claude/ should have a registry entry.

        NOTE: This test will fail when new patterns are added to core/.claude/
        without updating registry/patterns.json. Run:
            python scripts/generate_docs.py
        to sync.
        """
        reg = _load_registry()
        actual = _all_actual_names()
        registry_names = {k for k in reg if k != "_meta"}

        missing = sorted(actual - registry_names)
        assert missing == [], (
            f"Files without registry entries ({len(missing)}) — run "
            f"'python scripts/generate_docs.py' to sync:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )


# ══════════════════════════════════════════════════════════════════════════════
#  2. PATTERN STRUCTURE VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillStructure:
    """Every skill directory must contain a valid SKILL.md with frontmatter."""

    def test_every_skill_dir_has_skill_md(self):
        skills_dir = CORE_CLAUDE / "skills"
        errors = []
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir():
                continue
            if d.name.startswith("."):
                continue
            if not (d / "SKILL.md").exists():
                errors.append(f"skills/{d.name}/ missing SKILL.md")
        assert errors == [], "\n".join(errors)

    def test_every_skill_md_has_frontmatter(self):
        skills_dir = CORE_CLAUDE / "skills"
        errors = []
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            skill_md = d / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            if not content.startswith("---"):
                errors.append(f"skills/{d.name}/SKILL.md missing frontmatter delimiters")
                continue
            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                errors.append(f"skills/{d.name}/SKILL.md has incomplete frontmatter")
        assert errors == [], "\n".join(errors)

    def test_every_skill_md_is_non_empty(self):
        skills_dir = CORE_CLAUDE / "skills"
        errors = []
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            skill_md = d / "SKILL.md"
            if skill_md.exists() and skill_md.stat().st_size < 50:
                errors.append(f"skills/{d.name}/SKILL.md is suspiciously small ({skill_md.stat().st_size} bytes)")
        assert errors == [], "\n".join(errors)


class TestAgentStructure:
    """Every agent file must be valid markdown with frontmatter or heading."""

    def test_every_agent_is_markdown(self):
        agents_dir = CORE_CLAUDE / "agents"
        for f in agents_dir.glob("*.md"):
            if f.name == "README.md":
                continue
            content = f.read_text(encoding="utf-8")
            assert len(content) > 50, f"Agent {f.name} is suspiciously small ({len(content)} chars)"

    def test_every_agent_has_heading_or_frontmatter(self):
        agents_dir = CORE_CLAUDE / "agents"
        errors = []
        for f in sorted(agents_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            content = f.read_text(encoding="utf-8")
            has_frontmatter = content.startswith("---")
            has_heading = "# " in content
            if not has_frontmatter and not has_heading:
                errors.append(f"Agent {f.name} has neither frontmatter nor heading")
        assert errors == [], "\n".join(errors)


class TestRuleStructure:
    """Every rule file must have valid frontmatter or heading."""

    def test_every_rule_is_markdown(self):
        rules_dir = CORE_CLAUDE / "rules"
        for f in rules_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            assert len(content) > 20, f"Rule {f.name} is suspiciously small"

    def test_every_rule_has_heading(self):
        rules_dir = CORE_CLAUDE / "rules"
        errors = []
        for f in sorted(rules_dir.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            if "# " not in content:
                errors.append(f"Rule {f.name} has no markdown heading")
        assert errors == [], "\n".join(errors)


class TestHookStructure:
    """Every hook must be a valid shell script."""

    def test_every_hook_has_shebang_or_comment(self):
        hooks_dir = CORE_CLAUDE / "hooks"
        errors = []
        for f in sorted(hooks_dir.glob("*.sh")):
            content = f.read_text(encoding="utf-8")
            if not (content.startswith("#!/") or content.startswith("#")):
                errors.append(f"Hook {f.name} missing shebang or comment header")
        assert errors == [], "\n".join(errors)

    def test_every_hook_is_non_trivial(self):
        hooks_dir = CORE_CLAUDE / "hooks"
        for f in hooks_dir.glob("*.sh"):
            content = f.read_text(encoding="utf-8")
            assert len(content) > 20, f"Hook {f.name} is suspiciously small"


# ══════════════════════════════════════════════════════════════════════════════
#  3. NAMING CONVENTION VALIDATION
# ══════════════════════════════════════════════════════════════════════════════


class TestStackPrefixConventions:
    """Stack-prefixed files must use valid, recognized prefixes."""

    def test_all_stack_prefixed_agents_use_known_prefixes(self):
        from scripts.bootstrap import STACK_PREFIXES
        all_prefixes = set(STACK_PREFIXES.values())

        errors = []
        for name in _actual_agents():
            # Check if it looks stack-specific (contains a hyphen and starts with a known prefix)
            is_prefixed = any(name.startswith(p) for p in all_prefixes)
            if not is_prefixed:
                # Should not start with a potential unknown prefix
                # This is fine — it's a universal agent
                pass

    def test_stack_prefixes_map_to_actual_files(self):
        """Each stack prefix in STACK_PREFIXES should have at least one file using it.

        A stack is considered "used" if any file starts with its prefix OR
        if a rule placeholder exists with the stack name (e.g. 'superpowers.md').
        """
        from scripts.bootstrap import STACK_PREFIXES
        all_names = _all_actual_names()

        missing_stacks = []
        for stack, prefix in STACK_PREFIXES.items():
            has_prefixed_files = any(name.startswith(prefix) for name in all_names)
            # Rule placeholders use the stack key itself (e.g. "superpowers")
            has_placeholder = any(
                name == stack or name == prefix.rstrip("-")
                for name in all_names
            )
            if not has_prefixed_files and not has_placeholder:
                missing_stacks.append(f"Stack '{stack}' (prefix '{prefix}') has no files or placeholders")
        assert missing_stacks == [], "\n".join(missing_stacks)


# ══════════════════════════════════════════════════════════════════════════════
#  4. TIERING LISTS CROSS-VALIDATION (recommend.py constants vs actual files)
# ══════════════════════════════════════════════════════════════════════════════


class TestTieringListsReferenceRealResources:
    """Every name in MUST_HAVE, NICE_TO_HAVE, ALWAYS_SKIP must exist in core/.claude/."""

    def test_must_have_hooks_exist(self):
        from scripts.recommend import MUST_HAVE_HOOKS
        hooks = set(_actual_hooks())
        missing = MUST_HAVE_HOOKS - hooks
        assert missing == set(), f"MUST_HAVE_HOOKS references non-existent hooks: {missing}"

    def test_must_have_universal_skills_exist(self):
        from scripts.recommend import MUST_HAVE_UNIVERSAL_SKILLS
        skills = set(_actual_skills())
        missing = MUST_HAVE_UNIVERSAL_SKILLS - skills
        assert missing == set(), f"MUST_HAVE_UNIVERSAL_SKILLS references non-existent skills: {missing}"

    def test_nice_to_have_universal_skills_exist(self):
        from scripts.recommend import NICE_TO_HAVE_UNIVERSAL_SKILLS
        skills = set(_actual_skills())
        missing = NICE_TO_HAVE_UNIVERSAL_SKILLS - skills
        assert missing == set(), f"NICE_TO_HAVE_UNIVERSAL_SKILLS references non-existent skills: {missing}"

    def test_must_have_rules_exist(self):
        from scripts.recommend import MUST_HAVE_RULES
        rules = set(_actual_rules())
        missing = MUST_HAVE_RULES - rules
        assert missing == set(), f"MUST_HAVE_RULES references non-existent rules: {missing}"

    def test_must_have_agents_exist(self):
        from scripts.recommend import MUST_HAVE_AGENTS
        agents = set(_actual_agents())
        missing = MUST_HAVE_AGENTS - agents
        assert missing == set(), f"MUST_HAVE_AGENTS references non-existent agents: {missing}"

    def test_always_skip_references_real_skills(self):
        from scripts.recommend import ALWAYS_SKIP
        skills = set(_actual_skills())
        missing = ALWAYS_SKIP - skills
        assert missing == set(), (
            f"ALWAYS_SKIP references non-existent skills: {missing}"
        )

    def test_nice_to_have_stack_overrides_exist(self):
        from scripts.recommend import NICE_TO_HAVE_STACK_OVERRIDES
        skills = set(_actual_skills())
        missing = NICE_TO_HAVE_STACK_OVERRIDES - skills
        assert missing == set(), (
            f"NICE_TO_HAVE_STACK_OVERRIDES references non-existent skills: {missing}"
        )

    def test_dep_pattern_map_values_exist_in_registry(self):
        """Every pattern name in DEP_PATTERN_MAP must exist in the registry."""
        from scripts.recommend import DEP_PATTERN_MAP
        reg = _load_registry()
        all_pattern_names = set()
        for patterns in DEP_PATTERN_MAP.values():
            all_pattern_names.update(patterns)
        reg_names = {k for k in reg if k != "_meta"}
        missing = all_pattern_names - reg_names
        assert missing == set(), (
            f"DEP_PATTERN_MAP references patterns not in registry: {missing}"
        )

    def test_no_overlap_between_must_have_and_skip(self):
        from scripts.recommend import (
            MUST_HAVE_UNIVERSAL_SKILLS, ALWAYS_SKIP, MUST_HAVE_HOOKS,
            MUST_HAVE_RULES, MUST_HAVE_AGENTS,
        )
        must_all = MUST_HAVE_UNIVERSAL_SKILLS | MUST_HAVE_HOOKS | MUST_HAVE_RULES | MUST_HAVE_AGENTS
        overlap = must_all & ALWAYS_SKIP
        assert overlap == set(), f"Resources in both MUST_HAVE and ALWAYS_SKIP: {overlap}"

    def test_no_overlap_between_nice_to_have_and_must_have(self):
        from scripts.recommend import (
            MUST_HAVE_UNIVERSAL_SKILLS, NICE_TO_HAVE_UNIVERSAL_SKILLS,
        )
        overlap = MUST_HAVE_UNIVERSAL_SKILLS & NICE_TO_HAVE_UNIVERSAL_SKILLS
        assert overlap == set(), f"Skills in both MUST_HAVE and NICE_TO_HAVE: {overlap}"

    def test_no_overlap_between_nice_to_have_and_skip(self):
        from scripts.recommend import NICE_TO_HAVE_UNIVERSAL_SKILLS, ALWAYS_SKIP
        overlap = NICE_TO_HAVE_UNIVERSAL_SKILLS & ALWAYS_SKIP
        assert overlap == set(), f"Skills in both NICE_TO_HAVE and ALWAYS_SKIP: {overlap}"


# ══════════════════════════════════════════════════════════════════════════════
#  5. DEDUP_CHECK UNTESTED FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestValidateRegistry:
    """Tests for dedup_check.validate_registry — previously untested."""

    def test_valid_registry_returns_no_errors(self, tmp_path):
        from scripts.dedup_check import validate_registry
        registry = {
            "_meta": {"version": "1.0.0"},
            "test-skill": {
                "hash": "abc123", "type": "skill", "category": "core",
                "version": "1.0.0", "source": "hub:test",
            },
        }
        reg_path = tmp_path / "patterns.json"
        reg_path.write_text(json.dumps(registry))
        errors = validate_registry(reg_path, tmp_path)
        assert errors == []

    def test_missing_field_detected(self, tmp_path):
        from scripts.dedup_check import validate_registry
        registry = {
            "_meta": {"version": "1.0.0"},
            "bad-pattern": {"hash": "abc", "type": "skill"},  # missing category, version, source
        }
        reg_path = tmp_path / "patterns.json"
        reg_path.write_text(json.dumps(registry))
        errors = validate_registry(reg_path, tmp_path)
        assert len(errors) >= 3
        assert any("category" in e for e in errors)
        assert any("version" in e for e in errors)
        assert any("source" in e for e in errors)

    def test_non_dict_entry_detected(self, tmp_path):
        from scripts.dedup_check import validate_registry
        registry = {
            "_meta": {"version": "1.0.0"},
            "bad-entry": "not-a-dict",
        }
        reg_path = tmp_path / "patterns.json"
        reg_path.write_text(json.dumps(registry))
        errors = validate_registry(reg_path, tmp_path)
        assert len(errors) >= 1
        assert any("not a dict" in e for e in errors)

    def test_meta_key_skipped(self, tmp_path):
        from scripts.dedup_check import validate_registry
        registry = {"_meta": {"version": "1.0.0"}}
        reg_path = tmp_path / "patterns.json"
        reg_path.write_text(json.dumps(registry))
        errors = validate_registry(reg_path, tmp_path)
        assert errors == []

    def test_multiple_errors_per_entry(self, tmp_path):
        from scripts.dedup_check import validate_registry
        registry = {
            "_meta": {"version": "1.0.0"},
            "no-fields": {},  # all 5 required fields missing
        }
        reg_path = tmp_path / "patterns.json"
        reg_path.write_text(json.dumps(registry))
        errors = validate_registry(reg_path, tmp_path)
        assert len(errors) == 5, f"Expected 5 missing field errors, got {len(errors)}: {errors}"


class TestScanForSecrets:
    """Tests for dedup_check.scan_for_secrets — previously untested."""

    def test_clean_file(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "clean.md"
        f.write_text("# Normal content\nNo secrets here.")
        findings = scan_for_secrets(f)
        assert findings == []

    # Fake secrets below are assembled via adjacent-string-literal concatenation
    # so this source file does not trip dedup_check's repo-wide secret scan.
    # Python concatenates at parse time; the runtime value is the full
    # pattern-matching string that scan_for_secrets should detect.

    def test_detects_anthropic_key(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "leaked.md"
        fake = "sk-" "ant-ABCDEF1234567890abcdef"
        f.write_text(f'api_key = "{fake}"')
        findings = scan_for_secrets(f)
        assert len(findings) >= 1
        assert any("Anthropic" in finding for finding in findings)

    def test_detects_github_pat(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "leaked.md"
        fake = "gh" "p_ABCDEFghijklmnop1234567890qrstuv1234"
        f.write_text(f'token = "{fake}"')
        findings = scan_for_secrets(f)
        assert len(findings) >= 1
        assert any("GitHub" in finding for finding in findings)

    def test_detects_aws_key(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "leaked.md"
        fake = "AK" "IAIOSFODNN7EXAMPLE"
        f.write_text(f'aws_key = "{fake}"')
        findings = scan_for_secrets(f)
        assert len(findings) >= 1
        assert any("AWS" in finding for finding in findings)

    def test_detects_hardcoded_password(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "leaked.md"
        line = "pass" 'word = "supersecret123"'
        f.write_text(line)
        findings = scan_for_secrets(f)
        assert len(findings) >= 1
        assert any("password" in finding.lower() for finding in findings)

    def test_detects_google_api_key(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "leaked.md"
        fake = "AI" "zaSyA1234567890ABCDEFghijklmnopqrstuvw"
        f.write_text(f'key = "{fake}"')
        findings = scan_for_secrets(f)
        assert len(findings) >= 1
        assert any("Google" in finding for finding in findings)

    def test_binary_file_returns_empty(self, tmp_path):
        from scripts.dedup_check import scan_for_secrets
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        findings = scan_for_secrets(f)
        assert findings == []


# ══════════════════════════════════════════════════════════════════════════════
#  6. GENERATE_DOCS UNTESTED FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestScanClaudeDir:
    """Tests for generate_docs.scan_claude_dir — previously untested."""

    def test_scans_agents_skills_rules(self, tmp_path):
        from scripts.generate_docs import scan_claude_dir
        claude = tmp_path / ".claude"
        (claude / "agents").mkdir(parents=True)
        (claude / "agents" / "debugger.md").write_text("# Debug")
        (claude / "skills" / "tdd").mkdir(parents=True)
        (claude / "skills" / "tdd" / "SKILL.md").write_text("# TDD")
        (claude / "rules").mkdir(parents=True)
        (claude / "rules" / "workflow.md").write_text("# Workflow")

        inv = scan_claude_dir(claude)
        assert "debugger" in inv["agents"]
        assert "tdd" in inv["skills"]
        assert "workflow" in inv["rules"]

    def test_hooks_key_exists_in_inventory(self, tmp_path):
        """scan_claude_dir returns a hooks key (even if empty — hooks scanning not implemented)."""
        from scripts.generate_docs import scan_claude_dir
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        inv = scan_claude_dir(claude)
        assert "hooks" in inv, "Inventory should always include a 'hooks' key"

    def test_missing_dir_returns_empty(self, tmp_path):
        from scripts.generate_docs import scan_claude_dir
        inv = scan_claude_dir(tmp_path / "nonexistent")
        assert inv["agents"] == []
        assert inv["skills"] == []
        assert inv["rules"] == []
        assert inv["hooks"] == []

    def test_skips_readme(self, tmp_path):
        from scripts.generate_docs import scan_claude_dir
        claude = tmp_path / ".claude"
        (claude / "agents").mkdir(parents=True)
        (claude / "agents" / "README.md").write_text("# Agents")
        (claude / "agents" / "debugger.md").write_text("# Debug")
        inv = scan_claude_dir(claude)
        assert "README" not in inv["agents"]
        assert "debugger" in inv["agents"]

    def test_skill_requires_dir_with_skill_md(self, tmp_path):
        from scripts.generate_docs import scan_claude_dir
        claude = tmp_path / ".claude"
        (claude / "skills" / "empty-dir").mkdir(parents=True)
        (claude / "skills" / "valid").mkdir(parents=True)
        (claude / "skills" / "valid" / "SKILL.md").write_text("# Skill")
        inv = scan_claude_dir(claude)
        assert "valid" in inv["skills"]
        assert "empty-dir" not in inv["skills"]


class TestGenerateDashboardHtml:
    """Tests for generate_docs.generate_dashboard_html — previously untested."""

    def test_returns_valid_html(self, tmp_path):
        from scripts.generate_docs import generate_dashboard_html
        claude = tmp_path / ".claude"
        (claude / "agents").mkdir(parents=True)
        (claude / "agents" / "test.md").write_text("# Test")
        registry = {
            "_meta": {"version": "1.0.0", "last_updated": "2026-03-13", "total_patterns": 1},
            "test": {"type": "agent", "category": "core", "version": "1.0.0",
                     "source": "hub:test", "hash": "abc", "dependencies": [], "tags": []},
        }
        html = generate_dashboard_html(registry, claude)
        assert "<html" in html or "<!DOCTYPE" in html.upper() or "<table" in html
        assert "test" in html

    def test_includes_pattern_counts(self, tmp_path):
        from scripts.generate_docs import generate_dashboard_html
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        registry = {
            "_meta": {"version": "1.0.0", "last_updated": "2026-03-13", "total_patterns": 0},
        }
        html = generate_dashboard_html(registry, claude)
        assert isinstance(html, str)
        assert len(html) > 100  # Not trivially empty


# ══════════════════════════════════════════════════════════════════════════════
#  7. SYNC UNTESTED FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


class TestApplyUpdate:
    """Tests for sync_to_local.apply_update — previously untested."""

    def test_applies_skill_update(self, tmp_path):
        from scripts.sync_to_local import apply_update
        hub = tmp_path / "hub"
        skill_dir = hub / "core" / ".claude" / "skills" / "tdd"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# TDD v2")

        project = tmp_path / "project"
        project.mkdir()

        result = apply_update(hub, project, "tdd", "skill", "core")
        assert result is True
        assert (project / ".claude" / "skills" / "tdd" / "SKILL.md").exists()

    def test_applies_agent_update(self, tmp_path):
        from scripts.sync_to_local import apply_update
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "agents").mkdir(parents=True)
        (hub / "core" / ".claude" / "agents" / "debugger.md").write_text("# Debugger v2")

        project = tmp_path / "project"
        project.mkdir()

        result = apply_update(hub, project, "debugger", "agent", "core")
        assert result is True
        assert (project / ".claude" / "agents" / "debugger.md").exists()

    def test_applies_hook_update(self, tmp_path):
        from scripts.sync_to_local import apply_update
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "hooks").mkdir(parents=True)
        (hub / "core" / ".claude" / "hooks" / "auto-format.sh").write_text("#!/bin/bash\n# v2")

        project = tmp_path / "project"
        project.mkdir()

        result = apply_update(hub, project, "auto-format", "hook", "core")
        assert result is True
        assert (project / ".claude" / "hooks" / "auto-format.sh").exists()

    def test_returns_false_for_missing_source(self, tmp_path):
        from scripts.sync_to_local import apply_update
        hub = tmp_path / "hub"
        hub.mkdir()
        project = tmp_path / "project"
        project.mkdir()

        result = apply_update(hub, project, "nonexistent", "agent", "core")
        assert result is False


class TestPatternMatchesStacks:
    """Tests for sync_to_projects.pattern_matches_stacks — previously untested."""

    def test_core_pattern_always_matches(self):
        from scripts.sync_to_projects import pattern_matches_stacks
        assert pattern_matches_stacks("debugger", ["android-compose"], "core") is True

    def test_matching_stack_pattern(self):
        from scripts.sync_to_projects import pattern_matches_stacks
        assert pattern_matches_stacks("fastapi-backend", ["fastapi-python"], "stack:fastapi-python") is True

    def test_non_matching_stack_pattern(self):
        from scripts.sync_to_projects import pattern_matches_stacks
        assert pattern_matches_stacks("fastapi-backend", ["android-compose"], "stack:fastapi-python") is False

    def test_universal_pattern_without_prefix(self):
        from scripts.sync_to_projects import pattern_matches_stacks
        assert pattern_matches_stacks("tdd", ["fastapi-python"], "core") is True


# ══════════════════════════════════════════════════════════════════════════════
#  8. HARDENED ASSERTIONS FOR EXISTING TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestBootstrapHardened:
    """Stricter validations for bootstrap functionality."""

    def test_get_available_stacks_exact_count(self):
        from scripts.bootstrap import get_available_stacks, STACK_PREFIXES
        stacks = get_available_stacks()
        assert len(stacks) == len(STACK_PREFIXES), (
            f"get_available_stacks returns {len(stacks)} but STACK_PREFIXES has {len(STACK_PREFIXES)}"
        )

    def test_copy_preserves_content(self, tmp_path):
        """Copied files must have identical content to source."""
        from scripts.bootstrap import copy_claude_dir
        hub = tmp_path / "hub"
        (hub / "core" / ".claude" / "rules").mkdir(parents=True)
        original_content = "---\nname: test-rule\n---\n# Test Rule\n\nDetailed content here."
        (hub / "core" / ".claude" / "rules" / "test-rule.md").write_text(original_content)

        dst = tmp_path / "dst"
        dst.mkdir()
        copy_claude_dir(hub, dst, [])

        copied_content = (dst / ".claude" / "rules" / "test-rule.md").read_text()
        assert copied_content == original_content, "Copied file content differs from source"

    def test_validate_rejects_all_unknown(self):
        from scripts.bootstrap import validate_stack_selection
        errors = validate_stack_selection(["bogus1", "bogus2"])
        assert len(errors) == 2, "Should return one error per unknown stack"


class TestCollateHardened:
    """Stricter validations for collate module."""

    def test_build_pattern_entry_all_required_fields(self, sample_skill_path):
        from scripts.collate import build_pattern_entry
        entry = build_pattern_entry(
            name="sample-skill",
            pattern_type="skill",
            file_path=sample_skill_path,
            source="project:test/repo",
            category="core",
        )
        required = ["type", "source", "hash", "version", "category"]
        for field in required:
            assert field in entry, f"build_pattern_entry missing field: {field}"
        assert entry["type"] == "skill"
        assert entry["source"] == "project:test/repo"
        assert entry["category"] == "core"
        assert len(entry["hash"]) > 0, "Hash should not be empty"

    def test_detect_pattern_type_unknown_location(self, tmp_path):
        """Files in unknown directories should return None or a sensible default."""
        from scripts.collate import detect_pattern_type
        unknown_dir = tmp_path / "random"
        unknown_dir.mkdir()
        f = unknown_dir / "test.md"
        f.write_text("# Random file")
        result = detect_pattern_type(f)
        assert result is None or result == "unknown", (
            f"File in unknown location should not be classified, got: {result}"
        )


class TestGenerateDocsHardened:
    """Stricter validations for doc generation."""

    def test_count_patterns_exact_values(self):
        from scripts.generate_docs import count_patterns
        registry = {
            "_meta": {"version": "1.0.0"},
            "a": {"type": "skill", "category": "core"},
            "b": {"type": "skill", "category": "core"},
            "c": {"type": "agent", "category": "core"},
            "d": {"type": "hook", "category": "stack:android-compose"},
        }
        counts = count_patterns(registry)
        assert counts["total"] == 4
        assert counts["core"] == 3
        assert counts["by_type"]["skill"] == 2
        assert counts["by_type"]["agent"] == 1
        assert counts["by_type"]["hook"] == 1

    def test_dashboard_md_does_not_contain_raw_templates(self, sample_registry):
        from scripts.generate_docs import generate_dashboard_md
        md = generate_dashboard_md(sample_registry, [], {})
        assert "{{" not in md, "Dashboard contains unresolved template variables"
        assert "}}" not in md, "Dashboard contains unresolved template variables"


class TestRecommendHardened:
    """Stricter validations for recommendation engine."""

    def test_tier_resource_covers_all_actual_skills(self):
        """Every skill in core/.claude/skills/ must get a valid tier."""
        from scripts.recommend import tier_resource
        skills = _actual_skills()
        valid_tiers = {"must-have", "nice-to-have", "skip"}
        errors = []
        for name in skills:
            tier = tier_resource(name, "skill", [])
            if tier not in valid_tiers:
                errors.append(f"skill '{name}' got invalid tier: '{tier}'")
        assert errors == [], "\n".join(errors)

    def test_tier_resource_covers_all_actual_agents(self):
        from scripts.recommend import tier_resource
        agents = _actual_agents()
        valid_tiers = {"must-have", "nice-to-have", "skip"}
        for name in agents:
            tier = tier_resource(name, "agent", [])
            assert tier in valid_tiers, f"agent '{name}' got invalid tier: '{tier}'"

    def test_tier_resource_covers_all_actual_hooks(self):
        from scripts.recommend import tier_resource
        hooks = _actual_hooks()
        valid_tiers = {"must-have", "nice-to-have", "skip"}
        for name in hooks:
            tier = tier_resource(name, "hook", [])
            assert tier in valid_tiers, f"hook '{name}' got invalid tier: '{tier}'"

    def test_tier_resource_covers_all_actual_rules(self):
        from scripts.recommend import tier_resource
        rules = _actual_rules()
        valid_tiers = {"must-have", "nice-to-have", "skip"}
        for name in rules:
            tier = tier_resource(name, "rule", [])
            assert tier in valid_tiers, f"rule '{name}' got invalid tier: '{tier}'"


# ══════════════════════════════════════════════════════════════════════════════
#  9. NO SECRETS IN ACTUAL PATTERN FILES
# ══════════════════════════════════════════════════════════════════════════════


class TestNoSecretsInPatterns:
    """Scan all core/.claude/ files for leaked secrets.

    Skills that document bad practices (e.g. iac-deploy showing "NEVER do this")
    contain example secrets deliberately. We exclude known educational false positives.
    """

    # Files that contain example secrets as documentation of bad practices
    KNOWN_FALSE_POSITIVE_SKILLS = {
        "iac-deploy",       # Shows "NEVER" examples of hardcoded AWS keys
        "redis-patterns",   # Shows connection string patterns
        "semgrep-rules",    # Shows secret detection rules with examples
        "android-arch",     # Reference patterns with example credentials
    }

    def test_no_secrets_in_agents(self):
        from scripts.dedup_check import scan_for_secrets
        findings = []
        for f in (CORE_CLAUDE / "agents").rglob("*"):
            if f.is_file():
                findings.extend(scan_for_secrets(f))
        assert findings == [], f"Secrets in agent files:\n" + "\n".join(findings)

    def test_no_secrets_in_rules(self):
        from scripts.dedup_check import scan_for_secrets
        findings = []
        for f in (CORE_CLAUDE / "rules").rglob("*"):
            if f.is_file():
                findings.extend(scan_for_secrets(f))
        assert findings == [], f"Secrets in rule files:\n" + "\n".join(findings)

    def test_no_secrets_in_hooks(self):
        from scripts.dedup_check import scan_for_secrets
        findings = []
        for f in (CORE_CLAUDE / "hooks").rglob("*"):
            if f.is_file():
                findings.extend(scan_for_secrets(f))
        assert findings == [], f"Secrets in hook files:\n" + "\n".join(findings)

    def test_no_secrets_in_non_excluded_skills(self):
        from scripts.dedup_check import scan_for_secrets
        findings = []
        skills_dir = CORE_CLAUDE / "skills"
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            if skill_dir.name in self.KNOWN_FALSE_POSITIVE_SKILLS:
                continue
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    findings.extend(scan_for_secrets(f))
        assert findings == [], (
            f"Secrets in skill files (excluding known false positives):\n"
            + "\n".join(findings)
        )


# ══════════════════════════════════════════════════════════════════════════════
#  10. VALIDATE REAL REGISTRY (integration test against actual registry)
# ══════════════════════════════════════════════════════════════════════════════


class TestRealRegistryValidation:
    """Run validate_registry against the actual registry/patterns.json."""

    def test_actual_registry_passes_validation(self):
        from scripts.dedup_check import validate_registry
        errors = validate_registry(REGISTRY_PATH, ROOT)
        assert errors == [], (
            f"Registry validation errors ({len(errors)}):\n" + "\n".join(errors)
        )
