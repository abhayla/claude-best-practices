"""Tests for third-party agent skills detection and recommendation."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from scripts.third_party_skills import (
    load_registry,
    resolve_skills,
    format_recommendations,
    check_npx_available,
    try_install,
    format_install_results,
    validate_registry,
    _build_install_command,
    _glob_matches,
)


# --- Fixtures ---


@pytest.fixture
def hub_with_registry(tmp_path):
    """Create a minimal hub with a third-party-skills.yml."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    registry = {
        "skills": [
            {
                "repo": "redis/agent-skills",
                "skill": "redis-development",
                "description": "Redis best practices",
                "dependencies": ["redis", "ioredis", "aioredis", "bull", "bullmq", "@redis/client"],
                "url": "https://github.com/redis/agent-skills",
                "prerequisites": "Node.js (npx)",
                "tags": ["database", "cache", "redis"],
            }
        ]
    }
    (config_dir / "third-party-skills.yml").write_text(
        yaml.dump(registry, default_flow_style=False)
    )
    return tmp_path


@pytest.fixture
def hub_with_multi_registry(tmp_path):
    """Hub with multiple registry entries including ecosystem-filtered and file-signal ones."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    registry = {
        "skills": [
            {
                "repo": "redis/agent-skills",
                "skill": "redis-development",
                "description": "Redis best practices",
                "dependencies": ["redis", "ioredis"],
            },
            {
                "repo": "hashicorp/agent-skills",
                "skill": "terraform",
                "description": "Terraform skills",
                "dependencies": ["cdktf"],
                "file_signals": ["**/*.tf"],
            },
            {
                "repo": "vercel-labs/agent-skills",
                "description": "React/Next.js skills",
                "dependencies": ["next", "react"],
                "ecosystems": ["npm"],
            },
        ]
    }
    (config_dir / "third-party-skills.yml").write_text(
        yaml.dump(registry, default_flow_style=False)
    )
    return tmp_path


@pytest.fixture
def project_with_redis_pip(tmp_path):
    """Project with redis in requirements.txt."""
    project = tmp_path / "myproject"
    project.mkdir()
    (project / "requirements.txt").write_text("fastapi>=0.100\nredis>=5.0\nuvicorn\n")
    return project


@pytest.fixture
def project_with_redis_npm(tmp_path):
    """Project with ioredis in package.json."""
    project = tmp_path / "myproject"
    project.mkdir()
    pkg = {"dependencies": {"express": "^4.0", "ioredis": "^5.0"}}
    (project / "package.json").write_text(json.dumps(pkg))
    return project


@pytest.fixture
def project_with_terraform(tmp_path):
    """Project with .tf files."""
    project = tmp_path / "myproject"
    project.mkdir()
    infra = project / "infra"
    infra.mkdir()
    (infra / "main.tf").write_text('resource "aws_instance" "web" {}')
    return project


@pytest.fixture
def project_with_next_npm(tmp_path):
    """Project with next in package.json."""
    project = tmp_path / "myproject"
    project.mkdir()
    pkg = {"dependencies": {"next": "^14.0", "react": "^18.0"}}
    (project / "package.json").write_text(json.dumps(pkg))
    return project


@pytest.fixture
def project_empty(tmp_path):
    """Empty project directory."""
    project = tmp_path / "myproject"
    project.mkdir()
    return project


# --- load_registry ---


class TestLoadRegistry:
    def test_loads_valid_registry(self, hub_with_registry):
        result = load_registry(hub_with_registry)
        assert len(result) == 1
        assert result[0]["repo"] == "redis/agent-skills"
        assert result[0]["skill"] == "redis-development"

    def test_returns_empty_if_missing_file(self, tmp_path):
        result = load_registry(tmp_path)
        assert result == []

    def test_returns_empty_on_invalid_yaml(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "third-party-skills.yml").write_text(": : invalid: yaml: [")
        result = load_registry(tmp_path)
        assert result == []

    def test_returns_empty_if_skills_not_list(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "third-party-skills.yml").write_text("skills: not-a-list")
        result = load_registry(tmp_path)
        assert result == []

    def test_returns_empty_if_root_not_dict(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "third-party-skills.yml").write_text("- just a list")
        result = load_registry(tmp_path)
        assert result == []


# --- resolve_skills ---


class TestResolveSkills:
    def test_matches_redis_from_pip(self, hub_with_registry):
        deps = {"pip": ["fastapi", "redis", "uvicorn"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1
        assert matched[0]["repo"] == "redis/agent-skills"
        assert matched[0]["skill"] == "redis-development"
        assert "redis" in matched[0]["match_reason"]
        assert "pip" in matched[0]["match_reason"]

    def test_matches_ioredis_from_npm(self, hub_with_registry):
        deps = {"npm": ["express", "ioredis"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1
        assert "ioredis" in matched[0]["match_reason"]

    def test_matches_bull_from_npm(self, hub_with_registry):
        deps = {"npm": ["bull"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1
        assert "bull" in matched[0]["match_reason"]

    def test_no_match_when_no_redis_deps(self, hub_with_registry):
        deps = {"pip": ["fastapi", "sqlalchemy"], "npm": ["express"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert matched == []

    def test_no_match_on_empty_deps(self, hub_with_registry):
        matched = resolve_skills({}, None, hub_with_registry)
        assert matched == []

    def test_no_duplicate_matches(self, hub_with_registry):
        """If multiple deps match the same entry, it should appear only once."""
        deps = {"pip": ["redis"], "npm": ["ioredis", "bull"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1

    def test_case_insensitive_matching(self, hub_with_registry):
        deps = {"pip": ["Redis"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1

    def test_empty_registry(self, tmp_path):
        deps = {"pip": ["redis"]}
        matched = resolve_skills(deps, None, tmp_path)
        assert matched == []

    def test_matches_file_signals(self, hub_with_multi_registry, project_with_terraform):
        deps = {}  # no deps, but .tf files exist
        matched = resolve_skills(deps, project_with_terraform, hub_with_multi_registry)
        tf_matches = [m for m in matched if m["skill"] == "terraform"]
        assert len(tf_matches) == 1
        assert "files" in tf_matches[0]["match_reason"]

    def test_ecosystem_filter_matches_npm(self, hub_with_multi_registry, project_with_next_npm):
        deps = {"npm": ["next", "react"]}
        matched = resolve_skills(deps, project_with_next_npm, hub_with_multi_registry)
        vercel_matches = [m for m in matched if m["repo"] == "vercel-labs/agent-skills"]
        assert len(vercel_matches) == 1

    def test_ecosystem_filter_blocks_wrong_ecosystem(self, hub_with_multi_registry):
        """'next' in pip should NOT match vercel-labs (ecosystems: [npm])."""
        deps = {"pip": ["next"]}
        matched = resolve_skills(deps, None, hub_with_multi_registry)
        vercel_matches = [m for m in matched if m["repo"] == "vercel-labs/agent-skills"]
        assert len(vercel_matches) == 0

    def test_file_signals_no_project_dir(self, hub_with_multi_registry):
        """file_signals should be skipped when project_dir is None (remote repo)."""
        deps = {}
        matched = resolve_skills(deps, None, hub_with_multi_registry)
        assert matched == []

    def test_multiple_entries_match(self, hub_with_multi_registry):
        """Both redis and terraform should match when both deps are present."""
        deps = {"pip": ["redis"]}
        project = hub_with_multi_registry  # reuse as project dir (has no .tf files)
        matched = resolve_skills(deps, project, hub_with_multi_registry)
        repos = {m["repo"] for m in matched}
        assert "redis/agent-skills" in repos


# --- _glob_matches ---


class TestGlobMatches:
    def test_simple_glob(self, tmp_path):
        (tmp_path / "main.tf").write_text("resource {}")
        assert _glob_matches(tmp_path, "*.tf") is True

    def test_recursive_glob(self, tmp_path):
        subdir = tmp_path / "infra"
        subdir.mkdir()
        (subdir / "main.tf").write_text("resource {}")
        assert _glob_matches(tmp_path, "**/*.tf") is True

    def test_no_match(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')")
        assert _glob_matches(tmp_path, "*.tf") is False

    def test_empty_dir(self, tmp_path):
        assert _glob_matches(tmp_path, "*.tf") is False


# --- _build_install_command ---


class TestBuildInstallCommand:
    def test_with_skill(self):
        entry = {"repo": "redis/agent-skills", "skill": "redis-development"}
        assert _build_install_command(entry) == "npx skills add redis/agent-skills --skill redis-development"

    def test_without_skill(self):
        entry = {"repo": "vercel-labs/agent-skills"}
        assert _build_install_command(entry) == "npx skills add vercel-labs/agent-skills"


# --- format_recommendations ---


class TestFormatRecommendations:
    def test_empty_input(self):
        assert format_recommendations([]) == ""

    def test_formats_single_skill(self):
        matched = [{
            "repo": "redis/agent-skills",
            "skill": "redis-development",
            "match_reason": "redis (pip)",
            "url": "https://github.com/redis/agent-skills",
            "prerequisites": "Node.js (npx)",
        }]
        output = format_recommendations(matched)
        assert "redis-development" in output
        assert "redis (pip)" in output
        assert "npx skills add redis/agent-skills" in output
        assert "Node.js (npx)" in output
        assert "https://github.com/redis/agent-skills" in output
        assert "RECOMMENDED THIRD-PARTY SKILLS" in output

    def test_formats_multiple_skills(self):
        matched = [
            {"repo": "redis/agent-skills", "skill": "redis-development",
             "match_reason": "redis (pip)", "prerequisites": "Node.js (npx)"},
            {"repo": "hashicorp/agent-skills", "skill": "terraform",
             "match_reason": "*.tf files", "prerequisites": "Node.js (npx)"},
        ]
        output = format_recommendations(matched)
        assert "redis-development" in output
        assert "terraform" in output

    def test_deduplicates_prerequisites(self):
        matched = [
            {"repo": "a/b", "skill": "x", "match_reason": "foo", "prerequisites": "Node.js (npx)"},
            {"repo": "c/d", "skill": "y", "match_reason": "bar", "prerequisites": "Node.js (npx)"},
        ]
        output = format_recommendations(matched)
        assert output.count("Node.js (npx)") == 1  # only in prerequisites line

    def test_skill_name_fallback_to_repo(self):
        """When 'skill' is not set, use last segment of repo."""
        matched = [{"repo": "vercel-labs/agent-skills", "match_reason": "next (npm)"}]
        output = format_recommendations(matched)
        assert "agent-skills" in output


# --- check_npx_available ---


class TestCheckNpxAvailable:
    @patch("scripts.third_party_skills.shutil.which", return_value="/usr/local/bin/npx")
    def test_available(self, mock_which):
        assert check_npx_available() is True
        mock_which.assert_called_once_with("npx")

    @patch("scripts.third_party_skills.shutil.which", return_value=None)
    def test_not_available(self, mock_which):
        assert check_npx_available() is False


# --- try_install ---


class TestTryInstall:
    def test_dry_run_skips(self, tmp_path):
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched, dry_run=True)
        assert "redis/agent-skills:redis-development" in results
        assert "dry run" in results["redis/agent-skills:redis-development"]

    @patch("scripts.third_party_skills.check_npx_available", return_value=False)
    def test_npx_not_available(self, mock_check, tmp_path):
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched)
        assert "npx not available" in results["redis/agent-skills:redis-development"]

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run")
    def test_successful_install(self, mock_run, mock_check, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched)
        assert results["redis/agent-skills:redis-development"] == "installed"
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "npx" in call_args[0][0]
        assert "redis/agent-skills" in call_args[0][0]
        assert "--skill" in call_args[0][0]
        assert "redis-development" in call_args[0][0]
        assert "-y" in call_args[0][0]

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run")
    def test_failed_install(self, mock_run, mock_check, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="npm ERR! 404")
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched)
        assert "failed" in results["redis/agent-skills:redis-development"]
        assert "404" in results["redis/agent-skills:redis-development"]

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run", side_effect=subprocess.TimeoutExpired("npx", 120))
    def test_timeout(self, mock_run, mock_check, tmp_path):
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched)
        assert "timeout" in results["redis/agent-skills:redis-development"]

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run", side_effect=OSError("No such file"))
    def test_os_error(self, mock_run, mock_check, tmp_path):
        matched = [{"repo": "redis/agent-skills", "skill": "redis-development"}]
        results = try_install(tmp_path, matched)
        assert "failed" in results["redis/agent-skills:redis-development"]

    def test_empty_matched(self, tmp_path):
        results = try_install(tmp_path, [])
        assert results == {}

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run")
    def test_install_without_skill_name(self, mock_run, mock_check, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        matched = [{"repo": "vercel-labs/agent-skills"}]
        results = try_install(tmp_path, matched)
        assert results["vercel-labs/agent-skills:"] == "installed"
        cmd = mock_run.call_args[0][0]
        assert "--skill" not in cmd

    @patch("scripts.third_party_skills.check_npx_available", return_value=True)
    @patch("scripts.third_party_skills.subprocess.run")
    def test_multiple_installs_independent(self, mock_run, mock_check, tmp_path):
        """One failure should not block the other."""
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="error"),
            MagicMock(returncode=0),
        ]
        matched = [
            {"repo": "a/b", "skill": "x"},
            {"repo": "c/d", "skill": "y"},
        ]
        results = try_install(tmp_path, matched)
        assert "failed" in results["a/b:x"]
        assert results["c/d:y"] == "installed"


# --- format_install_results ---


class TestFormatInstallResults:
    def test_empty(self):
        assert format_install_results({}) == ""

    def test_formats_results(self):
        results = {
            "redis/agent-skills:redis-development": "installed",
            "hashicorp/agent-skills:terraform": "failed (timeout)",
        }
        output = format_install_results(results)
        assert "installed" in output
        assert "failed (timeout)" in output
        assert "redis/agent-skills:redis-development" in output


# --- validate_registry ---


class TestValidateRegistry:
    def test_valid_registry(self, hub_with_registry):
        errors = validate_registry(hub_with_registry)
        assert errors == []

    def test_missing_file_is_ok(self, tmp_path):
        errors = validate_registry(tmp_path)
        assert errors == []

    def test_invalid_yaml(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        (config / "third-party-skills.yml").write_text(": : bad")
        errors = validate_registry(tmp_path)
        assert any("Invalid YAML" in e for e in errors)

    def test_root_not_dict(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        (config / "third-party-skills.yml").write_text("- just a list")
        errors = validate_registry(tmp_path)
        assert any("Root must be a YAML mapping" in e for e in errors)

    def test_skills_not_list(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        (config / "third-party-skills.yml").write_text("skills: not-a-list")
        errors = validate_registry(tmp_path)
        assert any("must be a list" in e for e in errors)

    def test_missing_repo(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{"description": "test", "dependencies": ["redis"]}]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("Missing or invalid 'repo'" in e for e in errors)

    def test_missing_description(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{"repo": "a/b", "dependencies": ["redis"]}]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("Missing 'description'" in e for e in errors)

    def test_no_trigger_mechanism(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{"repo": "a/b", "description": "test", "dependencies": []}]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("non-empty 'dependencies' or 'file_signals'" in e for e in errors)

    def test_file_signals_is_valid_trigger(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{
            "repo": "a/b", "description": "test",
            "dependencies": [], "file_signals": ["**/*.tf"],
        }]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert errors == []

    def test_unknown_ecosystem(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{
            "repo": "a/b", "description": "test",
            "dependencies": ["foo"], "ecosystems": ["unknown_eco"],
        }]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("Unknown ecosystem" in e for e in errors)

    def test_duplicate_entry(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [
            {"repo": "a/b", "skill": "x", "description": "test", "dependencies": ["foo"]},
            {"repo": "a/b", "skill": "x", "description": "test2", "dependencies": ["bar"]},
        ]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("Duplicate" in e for e in errors)

    def test_entry_not_dict(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": ["not-a-dict"]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert any("must be a mapping" in e for e in errors)

    def test_valid_ecosystems(self, tmp_path):
        config = tmp_path / "config"
        config.mkdir()
        data = {"skills": [{
            "repo": "a/b", "description": "test",
            "dependencies": ["foo"], "ecosystems": ["npm", "pip"],
        }]}
        (config / "third-party-skills.yml").write_text(yaml.dump(data))
        errors = validate_registry(tmp_path)
        assert errors == []


# --- Integration: resolve_skills with real dependency detection ---


class TestResolveWithRealDeps:
    """Test resolve_skills with the same deps format that recommend.py produces."""

    def test_redis_in_requirements_txt(self, hub_with_registry):
        deps = {"pip": ["fastapi", "redis", "uvicorn"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1
        assert matched[0]["skill"] == "redis-development"

    def test_ioredis_in_package_json(self, hub_with_registry):
        deps = {"npm": ["express", "ioredis", "typescript"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1
        assert matched[0]["skill"] == "redis-development"

    def test_bullmq_in_package_json(self, hub_with_registry):
        deps = {"npm": ["bullmq"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1

    def test_redis_client_scoped_package(self, hub_with_registry):
        deps = {"npm": ["@redis/client"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1

    def test_no_redis_anywhere(self, hub_with_registry):
        deps = {"pip": ["django", "celery"], "npm": ["react", "next"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert matched == []

    def test_redis_in_multiple_ecosystems(self, hub_with_registry):
        """Redis in both pip and npm should still only match once."""
        deps = {"pip": ["redis"], "npm": ["ioredis"]}
        matched = resolve_skills(deps, None, hub_with_registry)
        assert len(matched) == 1


# --- Validate the actual config/third-party-skills.yml ---


class TestActualRegistry:
    """Validate the real registry file ships valid."""

    def test_actual_registry_is_valid(self):
        hub_root = Path(__file__).parent.parent.parent
        errors = validate_registry(hub_root)
        assert errors == [], f"Registry validation errors: {errors}"

    def test_actual_registry_loads(self):
        hub_root = Path(__file__).parent.parent.parent
        skills = load_registry(hub_root)
        assert len(skills) >= 1
        assert any(s.get("repo") == "redis/agent-skills" for s in skills)
