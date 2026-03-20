"""Recommend hub Claude resources for a project based on stack detection and gap analysis.

Usage:
    # Report only (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name

    # Report only (local directory)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project

    # Apply recommendations via PR (remote repo)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --apply

    # Apply recommendations locally (copy files)
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --apply

    # Provision project (apply + CLAUDE.md + settings.json)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --provision
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --provision

    # Use stacks from repos.yml instead of auto-detection
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --use-config

    # Compare content of overlapping resources (detect divergence)
    PYTHONPATH=. python scripts/recommend.py --repo owner/name --diff
    PYTHONPATH=. python scripts/recommend.py --local /path/to/project --diff
"""

import argparse
import base64
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from scripts.bootstrap import STACK_PREFIXES, copy_claude_dir, render_template
from scripts.collate import extract_patterns_from_dir
from scripts.third_party_skills import (
    format_install_results,
    format_recommendations,
    resolve_skills as resolve_third_party_skills,
    try_install as try_install_third_party,
)


# --- Stack Detection ---

# Maps config file patterns to stack identifiers.
# Each entry: (file_glob, content_pattern_or_None, stack_name)
STACK_DETECTORS = [
    # Android: build.gradle.kts with android plugin
    ("**/build.gradle.kts", "com.android", "android-compose"),
    ("**/build.gradle", "com.android", "android-compose"),
    # FastAPI: requirements.txt with fastapi
    ("**/requirements.txt", "fastapi", "fastapi-python"),
    ("**/pyproject.toml", "fastapi", "fastapi-python"),
    ("**/Pipfile", "fastapi", "fastapi-python"),
    # Firebase: google-services.json or firebase dependency
    ("**/google-services.json", None, "firebase-auth"),
    ("**/requirements.txt", "firebase", "firebase-auth"),
    ("**/build.gradle.kts", "firebase", "firebase-auth"),
    # AI/Gemini: google-genai or anthropic SDK
    ("**/requirements.txt", "google-genai", "ai-gemini"),
    ("**/requirements.txt", "anthropic", "ai-gemini"),
    ("**/pyproject.toml", "google-genai", "ai-gemini"),
    # React/Next.js: package.json with next
    ("**/package.json", '"next"', "react-nextjs"),
]

# --- Dependency Detection ---

# Maps dependency names to hub pattern names that should be promoted to must-have
DEP_PATTERN_MAP = {
    # JS/TS
    "tailwindcss": {"tailwind-dev"},
    "@tailwindcss/postcss": {"tailwind-dev"},
    "vitest": {"vitest-dev"},
    "jest": {"jest-dev"},
    "@playwright/test": {"playwright"},
    "prisma": {"prisma-orm"},
    "drizzle-orm": {"drizzle-orm"},
    "next": {"nextjs-dev"},
    "vue": {"vue-dev", "vue-test", "vue"},  # vue rule
    "nuxt": {"nuxt-dev", "vue"},            # Nuxt implies Vue rule
    "pinia": {"vue-dev", "vue"},            # Pinia implies Vue rule
    "react-native": {"react-native-dev", "react-native-e2e"},
    "expo": {"expo-dev"},
    "hono": {"hono-backend"},
    "elysia": {"bun-elysia-test", "bun-elysia"},  # bun-elysia rule
    "socket.io": {"websocket-patterns"},
    "ws": {"websocket-patterns"},
    "redis": {"redis-patterns"},
    "ioredis": {"redis-patterns"},
    "d3": {"d3-viz"},
    "remotion": {"remotion-video"},
    # Python
    "fastapi": {"fastapi-run-backend-tests", "fastapi-deploy", "fastapi-db-migrate",
                 "fastapi-backend", "fastapi-database"},  # fastapi rules
    "pytest": {"pytest-dev"},
    "alembic": {"db-migrate", "db-migrate-verify"},
    "sqlalchemy": {"schema-designer"},
    "psycopg2-binary": {"pg-query"},
    "psycopg2": {"pg-query"},
    "asyncpg": {"pg-query"},
    "firebase-admin": {"firebase"},  # firebase rule
    "anthropic": {"ai-gemini-api"},
    "google-genai": {"ai-gemini-api"},
    "websockets": {"websocket-patterns"},
    # Android/Gradle
    "compose": {"compose-ui", "android"},  # android rule
    # Flutter
    "flutter": {"flutter-dev", "flutter-e2e-test", "flutter"},  # flutter rule
}

# Subdirectory patterns to scan for dependency files (1-level deep)
_DEP_SUBDIRS = [
    "frontend", "backend", "server", "client", "app", "android", "ios", "web",
]

# Dependency file parsers: (filename, parser_function)
# Each parser returns a list of dependency names.


def _parse_package_json(content: str) -> list[str]:
    """Extract dependency names from package.json."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return []
    deps = []
    for key in ("dependencies", "devDependencies"):
        section = data.get(key, {})
        if isinstance(section, dict):
            deps.extend(section.keys())
    return deps


def _parse_requirements_txt(content: str) -> list[str]:
    """Extract dependency names from requirements.txt."""
    deps = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers and extras
        name = re.split(r"[>=<!~\[;@\s]", line)[0].strip()
        if name:
            deps.append(name.lower())
    return deps


def _parse_pyproject_toml(content: str) -> list[str]:
    """Extract dependency names from pyproject.toml [project].dependencies."""
    deps = []
    # Try tomllib (Python 3.11+) first
    try:
        import tomllib
        data = tomllib.loads(content)
        for dep in data.get("project", {}).get("dependencies", []):
            name = re.split(r"[>=<!~\[;@\s]", dep)[0].strip()
            if name:
                deps.append(name.lower())
        return deps
    except (ImportError, Exception):
        pass
    # Fallback: regex extraction
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "dependencies = [" or stripped.startswith("dependencies = ["):
            in_deps = True
            # Check inline list
            if "]" in stripped:
                # Single line list
                items = re.findall(r'"([^"]+)"', stripped)
                for item in items:
                    name = re.split(r"[>=<!~\[;@\s]", item)[0].strip()
                    if name:
                        deps.append(name.lower())
                in_deps = False
            continue
        if in_deps:
            if stripped.startswith("]"):
                in_deps = False
                continue
            items = re.findall(r'"([^"]+)"', stripped)
            for item in items:
                name = re.split(r"[>=<!~\[;@\s]", item)[0].strip()
                if name:
                    deps.append(name.lower())
    return deps


def _parse_build_gradle(content: str) -> list[str]:
    """Extract dependency names from build.gradle or build.gradle.kts."""
    deps = []
    # Match: implementation("group:artifact:version") or implementation 'group:artifact:version'
    # Also handles implementation("group:artifact:version") with parentheses
    for match in re.finditer(r'(?:implementation|api|compileOnly|testImplementation)\s*\(\s*["\']([^"\']+)["\']', content):
        parts = match.group(1).split(":")
        if len(parts) >= 2:
            deps.append(parts[1].lower())  # artifact name
    return deps


def _parse_pubspec_yaml(content: str) -> list[str]:
    """Extract dependency names from pubspec.yaml."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return []
    deps = []
    for key in ("dependencies", "dev_dependencies"):
        section = data.get(key, {}) if isinstance(data, dict) else {}
        if isinstance(section, dict):
            deps.extend(section.keys())
    return deps


def _parse_cargo_toml(content: str) -> list[str]:
    """Extract dependency names from Cargo.toml."""
    deps = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "dependencies" in stripped.lower():
            in_deps = True
            continue
        if stripped.startswith("[") and "dependencies" not in stripped.lower():
            in_deps = False
            continue
        if in_deps:
            match = re.match(r'^(\S+)\s*=', stripped)
            if match:
                deps.append(match.group(1).lower())
    return deps


def _parse_go_mod(content: str) -> list[str]:
    """Extract dependency names from go.mod."""
    deps = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require:
            parts = stripped.split()
            if parts:
                # Extract last segment of module path as dep name
                mod = parts[0]
                deps.append(mod.split("/")[-1].lower())
        elif stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                deps.append(parts[1].split("/")[-1].lower())
    return deps


def _parse_gemfile(content: str) -> list[str]:
    """Extract gem names from Gemfile."""
    deps = []
    for match in re.finditer(r"""gem\s+['"]([^'"]+)['"]""", content):
        deps.append(match.group(1).lower())
    return deps


# Maps filename to parser function
_DEP_FILE_PARSERS = {
    "package.json": _parse_package_json,
    "requirements.txt": _parse_requirements_txt,
    "pyproject.toml": _parse_pyproject_toml,
    "build.gradle.kts": _parse_build_gradle,
    "build.gradle": _parse_build_gradle,
    "pubspec.yaml": _parse_pubspec_yaml,
    "Cargo.toml": _parse_cargo_toml,
    "go.mod": _parse_go_mod,
    "Gemfile": _parse_gemfile,
}


def detect_dependencies_from_dir(project_dir: Path) -> dict[str, list[str]]:
    """Scan project root + 1-level-deep subdirectories for dependency files.

    Returns dependency names grouped by ecosystem (e.g., {"npm": [...], "pip": [...]}).
    """
    ecosystem_map = {
        "package.json": "npm",
        "requirements.txt": "pip",
        "pyproject.toml": "pip",
        "build.gradle.kts": "gradle",
        "build.gradle": "gradle",
        "pubspec.yaml": "pub",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "gem",
    }

    deps: dict[str, list[str]] = {}
    dirs_to_scan = [project_dir]
    for subdir in _DEP_SUBDIRS:
        subpath = project_dir / subdir
        if subpath.is_dir():
            dirs_to_scan.append(subpath)

    for scan_dir in dirs_to_scan:
        for filename, parser in _DEP_FILE_PARSERS.items():
            filepath = scan_dir / filename
            if not filepath.exists():
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            parsed = parser(content)
            ecosystem = ecosystem_map.get(filename, "unknown")
            deps.setdefault(ecosystem, [])
            deps[ecosystem].extend(parsed)

    # Deduplicate within each ecosystem
    for eco in deps:
        deps[eco] = sorted(set(deps[eco]))

    return deps


def detect_dependencies_from_repo(repo: str) -> dict[str, list[str]]:
    """Detect dependencies from a remote GitHub repo via gh API.

    Same logic as detect_dependencies_from_dir but fetches files via GitHub API.
    """
    ecosystem_map = {
        "package.json": "npm",
        "requirements.txt": "pip",
        "pyproject.toml": "pip",
        "build.gradle.kts": "gradle",
        "build.gradle": "gradle",
        "pubspec.yaml": "pub",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "gem",
    }

    deps: dict[str, list[str]] = {}
    # Build list of paths to check: root + subdirs
    paths_to_check = []
    for filename in _DEP_FILE_PARSERS:
        paths_to_check.append(filename)
        for subdir in _DEP_SUBDIRS:
            paths_to_check.append(f"{subdir}/{filename}")

    for file_path in paths_to_check:
        filename = file_path.split("/")[-1]
        parser = _DEP_FILE_PARSERS.get(filename)
        if not parser:
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="ignore")
        except Exception:
            continue
        parsed = parser(content)
        ecosystem = ecosystem_map.get(filename, "unknown")
        deps.setdefault(ecosystem, [])
        deps[ecosystem].extend(parsed)

    # Deduplicate within each ecosystem
    for eco in deps:
        deps[eco] = sorted(set(deps[eco]))

    return deps


def resolve_dep_patterns(deps: dict[str, list[str]]) -> set[str]:
    """Flatten all dependency names across ecosystems and resolve to hub pattern names."""
    all_dep_names = set()
    for dep_list in deps.values():
        all_dep_names.update(dep_list)

    promoted = set()
    for dep_name in all_dep_names:
        patterns = DEP_PATTERN_MAP.get(dep_name, set())
        promoted.update(patterns)
    return promoted


# Safety hooks that every project should have
MUST_HAVE_HOOKS = {"dangerous-command-blocker", "secret-scanner"}

# Core workflow skills that are high-value for any non-trivial project
CORE_WORKFLOW_SKILLS = {
    "implement", "fix-loop", "fix-issue", "tdd", "auto-verify",
    "systematic-debugging", "continue", "handover", "skill-master",
    "pr-standards", "request-code-review", "receive-code-review",
    "code-quality-gate", "writing-plans", "executing-plans",
}
MUST_HAVE_UNIVERSAL_SKILLS = CORE_WORKFLOW_SKILLS  # backward compat alias

# Universal skills that are nice-to-have
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
}

# Universal rules that are high-value
MUST_HAVE_RULES = {"context-management", "workflow", "claude-behavior", "testing", "tdd"}

# Universal agents that are high-value
MUST_HAVE_AGENTS = {"security-auditor-agent"}

# Skills/resources to always skip (meta hub skills, wrong-domain)
# NOTE: Framework skills like vue-dev, flutter-dev, etc. are NOT in this list —
# they are "skip unless dep detected" via DEP_PATTERN_MAP.
ALWAYS_SKIP = {
    "update-practices", "contribute-practice", "writing-skills",
    "obsidian", "solidity-audit", "mcp-server-builder",
    "twitter-x", "reddit", "github",
}

# Stack-specific skills that should be downgraded to nice-to-have
# (they match by prefix but aren't essential for most projects using that stack)
NICE_TO_HAVE_STACK_OVERRIDES = {
    "firebase-data-connect",  # PostgreSQL + GraphQL — most Firebase projects don't use this
    "xml-to-compose",         # Only needed for XML-to-Compose migration, not greenfield
}

# Non-prefixed resources that are nonetheless stack-specific.
# Maps resource name → set of stack identifiers that must be detected for it to be relevant.
# If NONE of the required stacks are detected, the resource is skipped as "wrong stack".
# This catches rules/agents like "android", "vue", "flutter" that don't use the standard
# stack prefix convention (e.g., "android-" prefix) but are still stack-bound.
RESOURCE_STACK_REQUIREMENTS: dict[str, set[str]] = {
    # Rules
    "android": {"android-compose"},
    "vue": {"react-nextjs"},        # Vue projects detected via deps, not STACK_DETECTORS
    "flutter": {"android-compose"}, # Flutter projects detected via deps
    "firebase": {"firebase-auth"},
    "bun-elysia": set(),            # No stack detector — requires elysia dep
    "fastapi-backend": {"fastapi-python"},
    "fastapi-database": {"fastapi-python"},
    # Agents
    "android-build-fixer-agent": {"android-compose"},
    "android-compose-agent": {"android-compose"},
    "android-kotlin-reviewer-agent": {"android-compose"},
}


def detect_stacks_from_dir(project_dir: Path) -> list[str]:
    """Auto-detect tech stacks from project config files."""
    detected = set()

    for glob_pattern, content_pattern, stack in STACK_DETECTORS:
        matching_files = list(project_dir.rglob(glob_pattern.replace("**/", "")))
        if not matching_files:
            continue

        if content_pattern is None:
            # File existence is enough (e.g., google-services.json)
            detected.add(stack)
            continue

        for f in matching_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if content_pattern.lower() in content.lower():
                    detected.add(stack)
                    break
            except (OSError, UnicodeDecodeError):
                continue

    return sorted(detected)


def detect_stacks_from_repo(repo: str) -> list[str]:
    """Auto-detect stacks from a remote GitHub repo using gh API."""
    detected = set()

    # Check key files via GitHub API
    checks = [
        ("android/build.gradle.kts", "com.android", "android-compose"),
        ("android/app/build.gradle.kts", "com.android", "android-compose"),
        ("build.gradle.kts", "com.android", "android-compose"),
        ("requirements.txt", "fastapi", "fastapi-python"),
        ("backend/requirements.txt", "fastapi", "fastapi-python"),
        ("android/app/google-services.json", None, "firebase-auth"),
        ("google-services.json", None, "firebase-auth"),
        ("requirements.txt", "firebase", "firebase-auth"),
        ("backend/requirements.txt", "firebase", "firebase-auth"),
        ("requirements.txt", "google-genai", "ai-gemini"),
        ("backend/requirements.txt", "google-genai", "ai-gemini"),
        ("requirements.txt", "anthropic", "ai-gemini"),
        ("backend/requirements.txt", "anthropic", "ai-gemini"),
        ("package.json", '"next"', "react-nextjs"),
    ]

    for file_path, content_pattern, stack in checks:
        if stack in detected:
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue

            if content_pattern is None:
                # File existence is enough
                detected.add(stack)
                continue

            # Content is base64 encoded from GitHub API
            import base64
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="ignore")
            if content_pattern.lower() in content.lower():
                detected.add(stack)
        except Exception:
            continue

    return sorted(detected)


def get_stacks_from_config(repo: str, config_path: Path) -> Optional[list[str]]:
    """Get stacks from repos.yml config if the repo is registered."""
    if not config_path.exists():
        return None
    with open(config_path) as f:
        data = yaml.safe_load(f)
    for entry in data.get("repos", []):
        if entry.get("repo") == repo:
            return entry.get("stacks", [])
    return None


# --- Resource Inventory ---


def get_hub_resources(hub_root: Path) -> dict[str, list[dict]]:
    """Get all resources from core/.claude/ organized by type."""
    claude_dir = hub_root / "core" / ".claude"
    resources = {"skill": [], "agent": [], "rule": [], "hook": []}

    # Skills
    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                resources["skill"].append({"name": skill_dir.name, "path": skill_file})

    # Agents
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for f in sorted(agents_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            resources["agent"].append({"name": f.stem, "path": f})

    # Rules
    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        for f in sorted(rules_dir.glob("*.md")):
            if f.name == "README.md":
                continue
            resources["rule"].append({"name": f.stem, "path": f})

    # Hooks
    hooks_dir = claude_dir / "hooks"
    if hooks_dir.exists():
        for f in sorted(hooks_dir.glob("*.sh")):
            resources["hook"].append({"name": f.stem, "path": f})

    return resources


def get_project_resource_names(claude_dir: Path) -> dict[str, set[str]]:
    """Get names of all resources in a project's .claude/ directory."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set()}

    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for d in skills_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                names["skill"].add(d.name)

    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.md"):
            if f.name != "README.md":
                names["agent"].add(f.stem)

    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        for f in rules_dir.glob("*.md"):
            if f.name != "README.md":
                names["rule"].add(f.stem)

    hooks_dir = claude_dir / "hooks"
    if hooks_dir.exists():
        for f in hooks_dir.glob("*.sh"):
            names["hook"].add(f.stem)

    return names


def get_project_resources_from_repo(repo: str) -> dict[str, set[str]]:
    """Get resource names from a remote repo via sparse clone."""
    names = {"skill": set(), "agent": set(), "rule": set(), "hook": set()}

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", "--filter=blob:none",
                 "--sparse", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=60,
            )
            subprocess.run(
                ["git", "-C", tmpdir, "sparse-checkout", "set", ".claude/"],
                capture_output=True, text=True, check=True, timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return names

        claude_dir = Path(tmpdir) / ".claude"
        return get_project_resource_names(claude_dir)


# --- Filtering & Tiering ---


def is_stack_specific(name: str) -> bool:
    """Check if a resource name has a stack prefix."""
    all_prefixes = set(STACK_PREFIXES.values())
    return any(name.startswith(p) for p in all_prefixes)


def matches_stacks(name: str, stacks: list[str]) -> bool:
    """Check if a resource matches the selected stacks (or is universal)."""
    all_prefixes = set(STACK_PREFIXES.values())
    if not any(name.startswith(p) for p in all_prefixes):
        return True  # Universal — always matches

    allowed_prefixes = {STACK_PREFIXES[s] for s in stacks if s in STACK_PREFIXES}
    return any(name.startswith(p) for p in allowed_prefixes)


def name_matches_existing(hub_name: str, project_names: set[str]) -> bool:
    """Check if a hub resource name matches a project resource, accounting for prefix differences.

    E.g., hub 'android-adb-test' matches project 'adb-test'.
    E.g., hub 'android-run-tests' matches project 'run-android-tests'.
    """
    if hub_name in project_names:
        return True

    # Strip known prefixes and check again
    for prefix in STACK_PREFIXES.values():
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            if stripped in project_names:
                return True

    # Check if project has a prefixed version of a universal hub name
    for prefix in STACK_PREFIXES.values():
        if f"{prefix}{hub_name}" in project_names:
            return True

    # Handle reversed prefix patterns: hub 'android-run-tests' ↔ project 'run-android-tests'
    # Extract the stack keyword from hub prefix and check if project has it embedded
    for prefix in STACK_PREFIXES.values():
        keyword = prefix.rstrip("-")  # "android-" → "android"
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            # Check: project has "{stripped_part}-{keyword}-{rest}" or "{verb}-{keyword}-{noun}"
            for pname in project_names:
                if keyword in pname and stripped.split("-")[-1] in pname:
                    return True

    return False


def tier_resource(name: str, resource_type: str, stacks: list[str], dep_promoted: set[str] | None = None) -> str:
    """Assign a tier to a missing resource: must-have, nice-to-have, or skip.

    Args:
        dep_promoted: Set of pattern names promoted by dependency detection.
            If a pattern is in this set, it overrides ALWAYS_SKIP and wrong-stack.

    Returns one of: 'must-have', 'nice-to-have', 'skip'.
    """
    tier, _ = tier_resource_with_reason(name, resource_type, stacks, dep_promoted)
    return tier


def tier_resource_with_reason(
    name: str, resource_type: str, stacks: list[str], dep_promoted: set[str] | None = None,
) -> tuple[str, str]:
    """Assign a tier and reason to a missing resource.

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

    # Type-specific tiering
    if resource_type == "hook":
        if name in MUST_HAVE_HOOKS:
            return "must-have", "essential safety hook"
        return "nice-to-have", "optional hook"

    if resource_type == "agent":
        if name in MUST_HAVE_AGENTS:
            return "must-have", "core agent"
        return "nice-to-have", "optional agent"

    if resource_type == "rule":
        if name in MUST_HAVE_RULES:
            return "must-have", "core rule"
        return "nice-to-have", "optional rule"

    if resource_type == "skill":
        # Stack-specific overrides — some stack skills are nice-to-have, not must-have
        if name in NICE_TO_HAVE_STACK_OVERRIDES:
            return "nice-to-have", "stack override (not essential for most projects)"

        # Stack-specific skills matching the project's stacks are must-haves
        if is_stack_specific(name) and matches_stacks(name, stacks):
            return "must-have", "matches detected stack"

        if name in MUST_HAVE_UNIVERSAL_SKILLS:
            return "must-have", "core workflow skill"

        if name in NICE_TO_HAVE_UNIVERSAL_SKILLS:
            return "nice-to-have", "useful but optional"

        # Remaining universal skills not in any list — nice-to-have
        return "nice-to-have", "optional skill"

    return "nice-to-have", "optional"


# --- Gap Analysis ---


def analyze_gaps(
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    stacks: list[str],
    deps: dict[str, list[str]] | None = None,
) -> dict[str, list[dict]]:
    """Compare hub resources against project resources and tier the gaps.

    Args:
        deps: Dependency info from detect_dependencies_from_dir/repo.
            Used to auto-promote patterns matching detected dependencies.

    Returns dict with keys 'must-have', 'improved', 'nice-to-have', 'skip',
    each containing a list of {'name': str, 'type': str, 'tier': str}.
    """
    dep_promoted = resolve_dep_patterns(deps) if deps else set()
    gaps = {"must-have": [], "improved": [], "nice-to-have": [], "skip": []}

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            name = resource["name"]

            # Skip if project already has it (accounting for name variations)
            if name_matches_existing(name, project_names.get(resource_type, set())):
                continue

            # Wrong-stack check — but dep-promoted patterns override this
            if not matches_stacks(name, stacks) and not (dep_promoted and name in dep_promoted):
                gaps["skip"].append({
                    "name": name, "type": resource_type, "tier": "skip",
                    "reason": "wrong stack",
                })
                continue

            tier, reason = tier_resource_with_reason(name, resource_type, stacks, dep_promoted)
            gaps[tier].append({
                "name": name, "type": resource_type, "tier": tier,
                "reason": reason,
            })

    return gaps


# --- Improved Pattern Detection ---


def _parse_frontmatter_version(content: str) -> str | None:
    """Extract version from YAML frontmatter of a pattern file."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    try:
        meta = yaml.safe_load(content[3:end])
        if isinstance(meta, dict):
            return meta.get("version")
    except yaml.YAMLError:
        pass
    return None


def _version_gt(a: str | None, b: str | None) -> bool:
    """Return True if version a > version b (simple semver comparison)."""
    if not a or not b:
        return False
    try:
        a_parts = [int(x) for x in a.split(".")]
        b_parts = [int(x) for x in b.split(".")]
        return a_parts > b_parts
    except (ValueError, AttributeError):
        return False


def detect_improved_patterns(
    hub_root: Path,
    project_claude_dir: Path,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    registry: dict,
) -> list[dict]:
    """Detect patterns that exist in both hub and project but hub has a newer version.

    For each overlapping pattern:
    1. Compute project file hash (SHA256)
    2. Get hub hash from registry
    3. Compare versions to determine if hub has improvements

    Returns list of {"name", "type", "hub_version", "project_version", "reason"}.
    """
    improved = []

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            hub_name = resource["name"]
            proj_name = _find_matching_project_name(
                hub_name, project_names.get(resource_type, set())
            )
            if proj_name is None:
                continue

            # Resolve project file path
            proj_path = _resolve_project_path(project_claude_dir, proj_name, resource_type)
            if not proj_path:
                continue

            # Compute project file hash
            try:
                proj_content = proj_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            proj_hash = hashlib.sha256(proj_content.encode("utf-8")).hexdigest()

            # Get hub hash from registry
            reg_entry = registry.get(hub_name, {})
            hub_hash = reg_entry.get("hash")

            if hub_hash and proj_hash == hub_hash:
                continue  # Identical — skip

            # Parse versions
            proj_version = _parse_frontmatter_version(proj_content)
            hub_version = reg_entry.get("version")

            if _version_gt(hub_version, proj_version):
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": proj_version,
                    "reason": f"hub v{hub_version} > project v{proj_version}",
                })
            elif proj_version is None and hub_version:
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": None,
                    "reason": "project has no version, hub has v" + hub_version,
                })
            elif hub_hash and proj_hash != hub_hash and proj_version == hub_version:
                improved.append({
                    "name": hub_name,
                    "type": resource_type,
                    "hub_version": hub_version,
                    "project_version": proj_version,
                    "reason": f"same version ({hub_version}) but different content",
                })
            # else: project version >= hub version — project customized intentionally

    return improved


# --- Report ---


def format_report(
    gaps: dict[str, list[dict]],
    stacks: list[str],
    project_names: dict[str, set[str]],
    hub_resources: dict[str, list[dict]],
) -> str:
    """Format the gap analysis as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CLAUDE RESOURCES RECOMMENDATION REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Summary
    existing = sum(len(v) for v in project_names.values())
    hub_total = sum(len(v) for v in hub_resources.values())
    lines.append(f"Detected stacks: {', '.join(stacks) if stacks else 'none'}")
    lines.append(f"Project resources: {existing}")
    lines.append(f"Hub resources (eligible): {hub_total}")
    lines.append("")

    # Must-have
    must = gaps["must-have"]
    if must:
        lines.append(f"--- MUST-HAVE ({len(must)}) ---")
        for item in sorted(must, key=lambda x: (x["type"], x["name"])):
            lines.append(f"  [{item['type']:6s}] {item['name']}")
        lines.append("")

    # Improved
    improved = gaps.get("improved", [])
    if improved:
        lines.append(f"--- IMPROVED ({len(improved)}) ---")
        for item in sorted(improved, key=lambda x: (x["type"], x["name"])):
            reason = item.get("reason", "")
            suffix = f" ({reason})" if reason else ""
            lines.append(f"  [{item['type']:6s}] {item['name']}{suffix}")
        lines.append("")

    # Nice-to-have
    nice = gaps["nice-to-have"]
    if nice:
        lines.append(f"--- NICE-TO-HAVE ({len(nice)}) ---")
        for item in sorted(nice, key=lambda x: (x["type"], x["name"])):
            lines.append(f"  [{item['type']:6s}] {item['name']}")
        lines.append("")

    # Skip
    skip = gaps["skip"]
    if skip:
        lines.append(f"--- SKIP ({len(skip)}) ---")
        for item in sorted(skip, key=lambda x: (x["type"], x["name"])):
            reason = item.get("reason", "")
            suffix = f" ({reason})" if reason else ""
            lines.append(f"  [{item['type']:6s}] {item['name']}{suffix}")
        lines.append("")

    # Totals
    lines.append("=" * 60)
    lines.append(
        f"TOTAL: {len(must)} must-have, {len(improved)} improved, "
        f"{len(nice)} nice-to-have, {len(skip)} skip"
    )
    lines.append("=" * 60)

    return "\n".join(lines)


# --- Apply ---


def apply_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    tier: str = "must-have",
) -> list[str]:
    """Copy recommended resources from hub to a local project directory.

    Only copies resources at or above the specified tier.
    """
    copied = []
    claude_src = hub_root / "core" / ".claude"

    tiers_to_apply = ["must-have"]
    if tier == "nice-to-have":
        tiers_to_apply.append("nice-to-have")

    for t in tiers_to_apply:
        for item in gaps.get(t, []):
            name = item["name"]
            rtype = item["type"]

            if rtype == "skill":
                src = claude_src / "skills" / name
                dst = target_dir / ".claude" / "skills" / name
                if src.is_dir():
                    dst.mkdir(parents=True, exist_ok=True)
                    for f in src.rglob("*"):
                        if f.is_file():
                            rel = f.relative_to(src)
                            dest_file = dst / rel
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, dest_file)
                            copied.append(str(Path(".claude/skills") / name / rel))
                else:
                    print(f"  WARNING: hub skill '{name}' not found at {src}")

            elif rtype == "agent":
                src = claude_src / "agents" / f"{name}.md"
                dst = target_dir / ".claude" / "agents" / f"{name}.md"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/agents/{name}.md")
                else:
                    print(f"  WARNING: hub agent '{name}' not found at {src}")

            elif rtype == "rule":
                src = claude_src / "rules" / f"{name}.md"
                dst = target_dir / ".claude" / "rules" / f"{name}.md"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/rules/{name}.md")
                else:
                    print(f"  WARNING: hub rule '{name}' not found at {src}")

            elif rtype == "hook":
                src = claude_src / "hooks" / f"{name}.sh"
                dst = target_dir / ".claude" / "hooks" / f"{name}.sh"
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied.append(f".claude/hooks/{name}.sh")
                else:
                    print(f"  WARNING: hub hook '{name}' not found at {src}")

    return copied


def apply_to_repo(
    hub_root: Path,
    repo: str,
    gaps: dict[str, list[dict]],
    tier: str = "must-have",
) -> Optional[str]:
    """Clone a repo, apply recommendations on a branch, and create a PR.

    Returns the PR URL if successful.
    """
    from scripts.sync_to_projects import check_existing_pr

    branch = "claude-recommendations"

    if check_existing_pr(repo, branch):
        print(f"PR already exists for branch '{branch}' on {repo}. Skipping.")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        # Full clone (need to push back)
        try:
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo}: {e}")
            return None

        # Create branch
        subprocess.run(
            ["git", "-C", tmpdir, "checkout", "-b", branch],
            capture_output=True, text=True, check=True,
        )

        # Copy resources
        copied = apply_to_local(hub_root, Path(tmpdir), gaps, tier)
        if not copied:
            print("No resources to copy.")
            return None

        # Commit
        subprocess.run(
            ["git", "-C", tmpdir, "add", ".claude/"],
            capture_output=True, text=True, check=True,
        )

        must_count = len(gaps.get("must-have", []))
        nice_count = len(gaps.get("nice-to-have", []))
        commit_msg = (
            f"feat: add {len(copied)} recommended Claude resources\n\n"
            f"Added {must_count} must-have and "
            f"{nice_count if tier == 'nice-to-have' else 0} nice-to-have resources "
            f"from claude-best-practices hub.\n\n"
            f"Files:\n" + "\n".join(f"  - {f}" for f in copied[:20])
        )
        if len(copied) > 20:
            commit_msg += f"\n  ... and {len(copied) - 20} more"

        subprocess.run(
            ["git", "-C", tmpdir, "commit", "-m", commit_msg],
            capture_output=True, text=True, check=True,
        )

        # Push
        subprocess.run(
            ["git", "-C", tmpdir, "push", "-u", "origin", branch],
            capture_output=True, text=True, check=True,
        )

        # Create PR
        pr_body = (
            "## Summary\n\n"
            f"Auto-generated recommendations from [claude-best-practices]"
            f"(https://github.com/abhayla/claude-best-practices) hub.\n\n"
            f"- **{must_count}** must-have resources\n"
            f"- **{nice_count if tier == 'nice-to-have' else 0}** nice-to-have resources\n\n"
            "## Files added\n\n"
            + "\n".join(f"- `{f}`" for f in copied[:30])
        )
        if len(copied) > 30:
            pr_body += f"\n- ... and {len(copied) - 30} more"

        result = subprocess.run(
            ["gh", "pr", "create",
             "--repo", repo,
             "--head", branch,
             "--title", f"feat: add {len(copied)} recommended Claude resources",
             "--body", pr_body],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"PR creation failed: {result.stderr}")
            return None


# --- Content Diff ---


def _resolve_hub_path(hub_root: Path, name: str, resource_type: str) -> Optional[Path]:
    """Get the file path for a hub resource."""
    claude_dir = hub_root / "core" / ".claude"
    if resource_type == "skill":
        p = claude_dir / "skills" / name / "SKILL.md"
    elif resource_type == "agent":
        p = claude_dir / "agents" / f"{name}.md"
    elif resource_type == "rule":
        p = claude_dir / "rules" / f"{name}.md"
    elif resource_type == "hook":
        p = claude_dir / "hooks" / f"{name}.sh"
    else:
        return None
    return p if p.exists() else None


def _resolve_project_path(claude_dir: Path, name: str, resource_type: str) -> Optional[Path]:
    """Get the file path for a project resource."""
    if resource_type == "skill":
        p = claude_dir / "skills" / name / "SKILL.md"
    elif resource_type == "agent":
        p = claude_dir / "agents" / f"{name}.md"
    elif resource_type == "rule":
        p = claude_dir / "rules" / f"{name}.md"
    elif resource_type == "hook":
        p = claude_dir / "hooks" / f"{name}.sh"
    else:
        return None
    return p if p.exists() else None


def _find_matching_project_name(hub_name: str, project_names: set[str]) -> Optional[str]:
    """Find the project resource name that matches a hub name (accounting for prefixes)."""
    if hub_name in project_names:
        return hub_name

    # Hub prefixed → project unprefixed
    for prefix in STACK_PREFIXES.values():
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            if stripped in project_names:
                return stripped

    # Project prefixed → hub unprefixed
    for prefix in STACK_PREFIXES.values():
        if f"{prefix}{hub_name}" in project_names:
            return f"{prefix}{hub_name}"

    # Reversed prefix
    for prefix in STACK_PREFIXES.values():
        keyword = prefix.rstrip("-")
        if hub_name.startswith(prefix):
            stripped = hub_name[len(prefix):]
            for pname in project_names:
                if keyword in pname and stripped.split("-")[-1] in pname:
                    return pname

    return None


def _compute_line_overlap(hub_lines: list[str], project_lines: list[str]) -> float:
    """Compute what fraction of hub lines appear in the project content (normalized).

    Returns a float 0.0-1.0 representing how much of the hub's content is present
    in the project version.
    """
    if not hub_lines:
        return 1.0

    # Normalize lines for comparison (strip, lowercase, skip empty/comment)
    def normalize(lines):
        return {
            line.strip().lower()
            for line in lines
            if line.strip() and not line.strip().startswith("---")
        }

    hub_set = normalize(hub_lines)
    proj_set = normalize(project_lines)

    if not hub_set:
        return 1.0

    overlap = hub_set & proj_set
    return len(overlap) / len(hub_set)


def classify_divergence(
    hub_content: str,
    project_content: str,
) -> dict:
    """Classify the divergence between hub and project versions of a resource.

    Returns a dict with:
      - status: 'identical', 'hub-newer', 'project-customized', 'name-collision'
      - hub_lines: int
      - project_lines: int
      - hub_overlap: float (fraction of hub lines found in project)
      - detail: str (human-readable explanation)
    """
    hub_lines = hub_content.splitlines()
    proj_lines = project_content.splitlines()
    hub_line_count = len(hub_lines)
    proj_line_count = len(proj_lines)

    # Exact match
    if hub_content.strip() == project_content.strip():
        return {
            "status": "identical",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": 1.0,
            "detail": "Content is identical",
        }

    hub_overlap = _compute_line_overlap(hub_lines, proj_lines)

    # Also check reverse: how much of project content is in hub
    proj_overlap = _compute_line_overlap(proj_lines, hub_lines)

    # High overlap in either direction — project is a customized extension of hub
    if hub_overlap >= 0.5 or proj_overlap >= 0.5:
        if proj_line_count > hub_line_count * 1.3:
            return {
                "status": "project-customized",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Project extends hub ({proj_line_count} vs {hub_line_count} lines, "
                    f"{hub_overlap:.0%} hub content preserved). "
                    "Project adds project-specific customizations."
                ),
            }
        else:
            return {
                "status": "project-customized",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Minor variations ({proj_line_count} vs {hub_line_count} lines, "
                    f"{hub_overlap:.0%} overlap)."
                ),
            }

    # Project is much larger (2x+) with low overlap — project heavily customized
    # the hub template. This is NOT a name collision — it's a deep rewrite.
    if proj_line_count > hub_line_count * 1.5 and hub_overlap < 0.5:
        return {
            "status": "project-customized",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": hub_overlap,
            "detail": (
                f"Project heavily customized hub template "
                f"({proj_line_count} vs {hub_line_count} lines, "
                f"{hub_overlap:.0%} hub content preserved). "
                "Hub may have generic improvements worth reviewing."
            ),
        }

    # Hub is larger with low overlap — hub has content project is missing
    if hub_line_count > proj_line_count and hub_overlap < 0.5:
        return {
            "status": "hub-newer",
            "hub_lines": hub_line_count,
            "project_lines": proj_line_count,
            "hub_overlap": hub_overlap,
            "detail": (
                f"Hub has significant content the project lacks "
                f"({hub_line_count} vs {proj_line_count} lines, "
                f"only {hub_overlap:.0%} overlap). "
                "Consider updating project from hub."
            ),
        }

    # Similar size, very low overlap — true name collision (different purpose)
    if hub_overlap < 0.15 and proj_overlap < 0.15:
        size_ratio = max(proj_line_count, hub_line_count) / max(min(proj_line_count, hub_line_count), 1)
        if size_ratio < 2.0:
            return {
                "status": "name-collision",
                "hub_lines": hub_line_count,
                "project_lines": proj_line_count,
                "hub_overlap": hub_overlap,
                "detail": (
                    f"Very low content overlap ({hub_overlap:.0%}) with similar size. "
                    f"These may be different resources sharing a name "
                    f"({proj_line_count} project vs {hub_line_count} hub lines). "
                    "Review manually."
                ),
            }

    # Default: moderate divergence
    return {
        "status": "project-customized",
        "hub_lines": hub_line_count,
        "project_lines": proj_line_count,
        "hub_overlap": hub_overlap,
        "detail": (
            f"Content has diverged ({hub_overlap:.0%} overlap, "
            f"{proj_line_count} project vs {hub_line_count} hub lines). "
            "Hub may have generic improvements worth reviewing."
        ),
    }


def analyze_overlaps_local(
    hub_root: Path,
    project_dir: Path,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
) -> list[dict]:
    """Compare content of overlapping resources between hub and a local project."""
    results = []
    claude_dir = project_dir / ".claude"

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            hub_name = resource["name"]
            proj_name = _find_matching_project_name(
                hub_name, project_names.get(resource_type, set())
            )
            if proj_name is None:
                continue

            hub_path = _resolve_hub_path(hub_root, hub_name, resource_type)
            proj_path = _resolve_project_path(claude_dir, proj_name, resource_type)

            if not hub_path or not proj_path:
                continue

            try:
                hub_content = hub_path.read_text(encoding="utf-8", errors="ignore")
                proj_content = proj_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            divergence = classify_divergence(hub_content, proj_content)
            divergence["hub_name"] = hub_name
            divergence["project_name"] = proj_name
            divergence["type"] = resource_type
            results.append(divergence)

    return results


def analyze_overlaps_repo(
    hub_root: Path,
    repo: str,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
) -> list[dict]:
    """Compare content of overlapping resources between hub and a remote repo."""
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", "--depth=2", "--filter=blob:none",
                 "--sparse", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=60,
            )
            subprocess.run(
                ["git", "-C", tmpdir, "sparse-checkout", "set", ".claude/"],
                capture_output=True, text=True, check=True, timeout=30,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return results

        return analyze_overlaps_local(
            hub_root, Path(tmpdir), hub_resources, project_names
        )


def format_diff_report(overlaps: list[dict]) -> str:
    """Format the content divergence analysis as a readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("CONTENT DIVERGENCE REPORT")
    lines.append("=" * 60)
    lines.append("")

    # Group by status
    by_status = {}
    for item in overlaps:
        status = item["status"]
        by_status.setdefault(status, []).append(item)

    # Count summary
    total = len(overlaps)
    identical = len(by_status.get("identical", []))
    lines.append(f"Total overlapping resources: {total}")
    lines.append(f"Identical: {identical}")
    lines.append("")

    # Actionable items first
    actionable_statuses = [
        ("name-collision", "NAME COLLISIONS — Different resources sharing a name"),
        ("hub-newer", "HUB HAS IMPROVEMENTS — Consider updating project"),
    ]

    for status, header in actionable_statuses:
        items = by_status.get(status, [])
        if not items:
            continue
        lines.append(f"--- {header} ({len(items)}) ---")
        for item in sorted(items, key=lambda x: x["hub_name"]):
            name_display = item["hub_name"]
            if item["hub_name"] != item["project_name"]:
                name_display = f"{item['hub_name']} (project: {item['project_name']})"
            lines.append(f"  [{item['type']:6s}] {name_display}")
            lines.append(f"           {item['detail']}")
        lines.append("")

    # Informational
    customized = by_status.get("project-customized", [])
    if customized:
        lines.append(f"--- PROJECT CUSTOMIZED — No action needed ({len(customized)}) ---")
        for item in sorted(customized, key=lambda x: x["hub_name"]):
            name_display = item["hub_name"]
            if item["hub_name"] != item["project_name"]:
                name_display = f"{item['hub_name']} (project: {item['project_name']})"
            ratio = item["project_lines"] / max(item["hub_lines"], 1)
            lines.append(
                f"  [{item['type']:6s}] {name_display} "
                f"({item['project_lines']} vs {item['hub_lines']} lines, "
                f"{item['hub_overlap']:.0%} overlap)"
            )
        lines.append("")

    identical_items = by_status.get("identical", [])
    if identical_items:
        lines.append(f"--- IDENTICAL ({len(identical_items)}) ---")
        for item in sorted(identical_items, key=lambda x: x["hub_name"]):
            lines.append(f"  [{item['type']:6s}] {item['hub_name']} ({item['hub_lines']} lines)")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# --- Provision ---

PROVISION_START_MARKER = "<!-- hub:best-practices:start -->"
PROVISION_END_MARKER = "<!-- hub:best-practices:end -->"


def get_rule_descriptions(hub_root: Path, rule_names: list[str]) -> dict[str, str]:
    """Parse YAML frontmatter description field from rule files.

    Falls back to first # heading if description is missing.
    """
    descriptions = {}
    rules_dir = hub_root / "core" / ".claude" / "rules"

    for name in rule_names:
        rule_file = rules_dir / f"{name}.md"
        if not rule_file.exists():
            continue

        content = rule_file.read_text(encoding="utf-8", errors="ignore")
        desc = None

        # Try YAML frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end]
                try:
                    meta = yaml.safe_load(frontmatter)
                    if isinstance(meta, dict):
                        desc = meta.get("description")
                except yaml.YAMLError:
                    pass

        # Fallback: first # heading
        if not desc:
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("# "):
                    desc = line[2:].strip()
                    break

        if desc:
            descriptions[name] = desc

    return descriptions


def generate_hub_practices_section(
    hub_root: Path, rules_present: list[str],
    project_names: dict[str, set[str]] | None = None,
) -> str:
    """Build the hub best-practices section for CLAUDE.md.

    Contains: Bug Fixing rule, dynamic Rules Reference table, sync metadata.
    """
    lines = []
    lines.append(PROVISION_START_MARKER)
    lines.append("")
    lines.append("<!-- PROTECTED SECTION — managed by claude-best-practices hub. -->")
    lines.append("<!-- Do NOT condense, rewrite, reorganize, or remove.          -->")
    lines.append("<!-- Any /init or optimization request must SKIP this section.  -->")
    lines.append("")
    lines.append("## Rules for Claude")
    lines.append("")
    lines.append(
        "1. **Bug Fixing**: Use `/fix-loop` or `/fix-issue`. "
        "Start by writing a test that reproduces the bug, "
        "then fix and prove with a passing test."
    )
    lines.append("")

    # Dynamic rules reference table
    if rules_present:
        descriptions = get_rule_descriptions(hub_root, rules_present)
        lines.append("### Rules Reference")
        lines.append("")
        lines.append("| Rule File | What It Covers |")
        lines.append("|-----------|---------------|")
        for name in sorted(rules_present):
            desc = descriptions.get(name, name.replace("-", " ").title())
            lines.append(f"| `rules/{name}.md` | {desc} |")
        lines.append("")

    lines.append("## Claude Code Configuration")
    lines.append("")
    if project_names:
        n_skills = len(project_names.get("skill", set()))
        n_agents = len(project_names.get("agent", set()))
        n_rules = len(project_names.get("rule", set()))
        lines.append(f"The `.claude/` directory contains {n_skills} skills, {n_agents} agents, and {n_rules} rules for Claude Code.")
    else:
        lines.append("The `.claude/` directory contains skills, agents, and rules for Claude Code.")
    lines.append("")
    lines.append(PROVISION_END_MARKER)
    return "\n".join(lines)


def reconcile_claude_md_rules(target_dir: Path) -> list[str]:
    """Verify CLAUDE.md rules table matches actual files on disk.

    Returns a list of warning strings. Empty list means everything is consistent.
    """
    warnings = []
    claude_md = target_dir / "CLAUDE.md"
    rules_dir = target_dir / ".claude" / "rules"

    if not claude_md.exists():
        return warnings

    content = claude_md.read_text(encoding="utf-8")

    # Extract rule names referenced in the Rules Reference table
    # Pattern matches: | `rules/something.md` | ... |
    referenced_rules = set()
    for match in re.findall(r"\|\s*`rules/([^`]+)\.md`\s*\|", content):
        referenced_rules.add(match)

    # Get actual rule files on disk
    rules_on_disk = set()
    if rules_dir.exists():
        for f in rules_dir.glob("*.md"):
            if f.name != "README.md":
                rules_on_disk.add(f.stem)

    # Check for dangling references (in CLAUDE.md but not on disk)
    for name in sorted(referenced_rules - rules_on_disk):
        warnings.append(f"CLAUDE.md references rules/{name}.md but file does not exist")

    # Check for unreferenced rules (on disk but not in CLAUDE.md)
    for name in sorted(rules_on_disk - referenced_rules):
        warnings.append(f"rules/{name}.md exists on disk but is not listed in CLAUDE.md")

    return warnings


def provision_claude_md(
    hub_root: Path,
    target_dir: Path,
    stacks: list[str],
    rules_present: list[str],
    project_names: dict[str, set[str]] | None = None,
) -> str:
    """Provision CLAUDE.md in the target directory.

    Three cases:
    1. No CLAUDE.md exists → create from template
    2. CLAUDE.md exists with markers → replace between markers
    3. CLAUDE.md exists without markers → append section with markers
    """
    claude_md = target_dir / "CLAUDE.md"
    hub_section = generate_hub_practices_section(hub_root, rules_present, project_names)

    if not claude_md.exists():
        # Case 1: Create from template
        template_path = hub_root / "core" / ".claude" / "CLAUDE.md.template"
        if template_path.exists():
            from datetime import datetime, timezone
            template = template_path.read_text(encoding="utf-8")
            rendered = render_template(template, {
                "PROJECT_NAME": target_dir.name,
                "PROJECT_DESCRIPTION": "A new project",
                "PLATFORM": ", ".join(stacks) if stacks else "general",
                "BUILD_TOOLS": "See stack documentation",
                "DEVELOPMENT_COMMANDS": "# Add your commands here",
                "HUB_REPO": "abhayla/claude-best-practices",
                "SELECTED_STACKS": ", ".join(stacks) if stacks else "none",
                "LAST_SYNC_TIMESTAMP": datetime.now(timezone.utc).isoformat(),
            })
            # Replace hardcoded hub section with dynamic one
            start_idx = rendered.find(PROVISION_START_MARKER)
            end_idx = rendered.find(PROVISION_END_MARKER)
            if start_idx != -1 and end_idx != -1:
                before = rendered[:start_idx]
                after = rendered[end_idx + len(PROVISION_END_MARKER):]
                rendered = before + hub_section + after
            claude_md.write_text(rendered, encoding="utf-8")
            return "created"
        else:
            claude_md.write_text(f"# CLAUDE.md\n\n{hub_section}\n", encoding="utf-8")
            return "created"

    # File exists — read it
    content = claude_md.read_text(encoding="utf-8")

    start_idx = content.find(PROVISION_START_MARKER)
    end_idx = content.find(PROVISION_END_MARKER)

    if start_idx != -1 and end_idx != -1:
        # Case 2: Both markers found → replace between them
        before = content[:start_idx]
        after = content[end_idx + len(PROVISION_END_MARKER):]
        new_content = before + hub_section + after
        claude_md.write_text(new_content, encoding="utf-8")
        return "replaced"

    # Case 3: No markers (or start without end) → append
    if not content.endswith("\n"):
        content += "\n"
    content += "\n" + hub_section + "\n"
    claude_md.write_text(content, encoding="utf-8")
    return "appended"


def provision_claude_local_md(hub_root: Path, target_dir: Path) -> str:
    """Copy CLAUDE.local.md template if missing, skip if exists."""
    local_md = target_dir / "CLAUDE.local.md"
    if local_md.exists():
        return "skipped"

    template_path = hub_root / "core" / ".claude" / "CLAUDE.local.md.template"
    if template_path.exists():
        shutil.copy2(template_path, local_md)
        return "created"

    return "no-template"


def deep_merge_settings(base: dict, overlay: dict) -> dict:
    """Recursively merge overlay into base. Base wins at leaf values. Lists are deduplicated union."""
    result = copy.deepcopy(base)

    for key, overlay_val in overlay.items():
        if key not in result:
            result[key] = copy.deepcopy(overlay_val)
        elif isinstance(result[key], dict) and isinstance(overlay_val, dict):
            result[key] = deep_merge_settings(result[key], overlay_val)
        elif isinstance(result[key], list) and isinstance(overlay_val, list):
            # Deduplicated union, preserving order (base items first)
            seen = set()
            merged = []
            for item in result[key] + overlay_val:
                key_repr = json.dumps(item, sort_keys=True) if isinstance(item, dict) else str(item)
                if key_repr not in seen:
                    seen.add(key_repr)
                    merged.append(item)
            result[key] = merged
        # else: base wins at leaves (do nothing)

    return result


def provision_settings_json(hub_root: Path, target_dir: Path) -> str:
    """Provision .claude/settings.json by merging hub defaults with existing."""
    hub_settings_path = hub_root / "core" / ".claude" / "settings.json"
    target_settings_path = target_dir / ".claude" / "settings.json"

    if not hub_settings_path.exists():
        return "no-hub-settings"

    hub_settings = json.loads(hub_settings_path.read_text(encoding="utf-8"))

    if target_settings_path.exists():
        existing = json.loads(target_settings_path.read_text(encoding="utf-8"))
        merged = deep_merge_settings(existing, hub_settings)
        target_settings_path.write_text(
            json.dumps(merged, indent=2) + "\n", encoding="utf-8"
        )
        return "merged"

    target_settings_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(hub_settings_path, target_settings_path)
    return "created"


def format_divergence_table(overlaps: list[dict]) -> str:
    """Format overlaps as a markdown table for PR body. Skips identical items."""
    non_identical = [o for o in overlaps if o["status"] != "identical"]
    if not non_identical:
        return ""

    lines = []
    lines.append("## Content Divergence")
    lines.append("")
    lines.append("| Resource | Type | Status | Overlap | Detail |")
    lines.append("|----------|------|--------|---------|--------|")
    for item in sorted(non_identical, key=lambda x: x["hub_name"]):
        name = item["hub_name"]
        if item.get("project_name") and item["project_name"] != name:
            name = f"{name} (project: {item['project_name']})"
        lines.append(
            f"| {name} | {item['type']} | {item['status']} "
            f"| {item['hub_overlap']:.0%} | {item['detail'][:80]} |"
        )

    return "\n".join(lines)


def provision_to_local(
    hub_root: Path,
    target_dir: Path,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    tier: str = "must-have",
) -> dict:
    """Orchestrate full provisioning to a local directory.

    Copies resources, provisions CLAUDE.md, CLAUDE.local.md, and settings.json.
    Returns a summary dict.
    """
    # Step 1: Copy resources
    copied = apply_to_local(hub_root, target_dir, gaps, tier)

    # Determine which rules are present after copying
    project_names = get_project_resource_names(target_dir / ".claude")
    rules_present = sorted(project_names.get("rule", set()))

    # Step 2: Provision CLAUDE.md
    claude_md_status = provision_claude_md(hub_root, target_dir, stacks, rules_present, project_names)

    # Step 3: Reconcile CLAUDE.md rules references against disk
    reconciliation_warnings = reconcile_claude_md_rules(target_dir)
    for w in reconciliation_warnings:
        print(f"  WARNING: {w}")

    # Step 4: Provision CLAUDE.local.md
    claude_local_status = provision_claude_local_md(hub_root, target_dir)

    # Step 5: Provision settings.json
    settings_status = provision_settings_json(hub_root, target_dir)

    return {
        "copied_files": copied,
        "claude_md": claude_md_status,
        "claude_local_md": claude_local_status,
        "settings_json": settings_status,
        "reconciliation_warnings": reconciliation_warnings,
    }


def _copy_resources_for_tier(
    hub_root: Path,
    target_dir: Path,
    items: list[dict],
) -> list[str]:
    """Copy specific hub resources to a target directory. Returns list of copied file paths."""
    copied = []
    claude_src = hub_root / "core" / ".claude"

    for item in items:
        name = item["name"]
        rtype = item["type"]

        if rtype == "skill":
            src = claude_src / "skills" / name
            dst = target_dir / ".claude" / "skills" / name
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                for f in src.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(src)
                        dest_file = dst / rel
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, dest_file)
                        copied.append(str(Path(".claude/skills") / name / rel))
        elif rtype == "agent":
            src = claude_src / "agents" / f"{name}.md"
            dst = target_dir / ".claude" / "agents" / f"{name}.md"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/agents/{name}.md")
        elif rtype == "rule":
            src = claude_src / "rules" / f"{name}.md"
            dst = target_dir / ".claude" / "rules" / f"{name}.md"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/rules/{name}.md")
        elif rtype == "hook":
            src = claude_src / "hooks" / f"{name}.sh"
            dst = target_dir / ".claude" / "hooks" / f"{name}.sh"
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(f".claude/hooks/{name}.sh")

    return copied


def _format_nice_to_have_pr_body(items: list[dict]) -> str:
    """Format a PR body with checkboxes for nice-to-have patterns."""
    lines = [
        "## Optional Patterns\n",
        "Check the patterns you want, then comment `/apply` to finalize.",
        "Unchecked patterns will be removed from this PR.\n",
    ]

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for item in items:
        by_type.setdefault(item["type"], []).append(item)

    type_headers = {"skill": "Skills", "rule": "Rules", "agent": "Agents", "hook": "Hooks"}
    for rtype in ("skill", "rule", "agent", "hook"):
        type_items = by_type.get(rtype, [])
        if not type_items:
            continue
        lines.append(f"### {type_headers.get(rtype, rtype.title())}")
        for item in sorted(type_items, key=lambda x: x["name"]):
            lines.append(f"- [ ] `{item['name']}`")
        lines.append("")

    lines.append("---")
    lines.append(
        "Generated by [claude-best-practices]"
        "(https://github.com/abhayla/claude-best-practices) hub."
    )
    return "\n".join(lines)


def _create_tier_branch_and_pr(
    tmpdir: str,
    repo: str,
    branch: str,
    default_branch: str,
    hub_root: Path,
    items: list[dict],
    title: str,
    body: str,
) -> Optional[str]:
    """Create a branch, copy resources, commit, push, and create PR.

    Returns PR URL if successful, None otherwise.
    """
    # Create branch from default
    subprocess.run(
        ["git", "-C", tmpdir, "checkout", default_branch],
        capture_output=True, text=True, check=True,
    )
    subprocess.run(
        ["git", "-C", tmpdir, "checkout", "-b", branch],
        capture_output=True, text=True, check=True,
    )

    # Copy resources
    copied = _copy_resources_for_tier(hub_root, Path(tmpdir), items)
    if not copied:
        return None

    # Stage
    subprocess.run(
        ["git", "-C", tmpdir, "add", ".claude/"],
        capture_output=True, text=True,
    )

    # Check if anything staged
    status = subprocess.run(
        ["git", "-C", tmpdir, "diff", "--cached", "--quiet"],
        capture_output=True, text=True,
    )
    if status.returncode == 0:
        return None  # Nothing to commit

    # Commit
    commit_msg = f"feat: {title}\n\nFiles:\n" + "\n".join(f"  - {f}" for f in copied[:20])
    if len(copied) > 20:
        commit_msg += f"\n  ... and {len(copied) - 20} more"
    subprocess.run(
        ["git", "-C", tmpdir, "commit", "-m", commit_msg],
        capture_output=True, text=True, check=True,
    )

    # Push
    push_result = subprocess.run(
        ["git", "-C", tmpdir, "push", "-u", "origin", branch],
        capture_output=True, text=True,
    )
    if push_result.returncode != 0:
        print(f"Push failed for {branch}: {push_result.stderr}")
        return None

    # Create PR
    pr_result = subprocess.run(
        ["gh", "pr", "create",
         "--repo", repo,
         "--head", branch,
         "--title", title,
         "--body", body],
        capture_output=True, text=True, timeout=30,
    )
    if pr_result.returncode == 0:
        return pr_result.stdout.strip()
    else:
        print(f"PR creation failed for {branch}: {pr_result.stderr}")
        return None


def provision_to_repo_multi_pr(
    hub_root: Path,
    repo: str,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
) -> dict[str, Optional[str]]:
    """Clone a repo and create up to 3 PRs for different tiers.

    Creates:
    - claude-provision/must-have: New must-have patterns (merge confidently)
    - claude-provision/improved: Hub upgrades to existing patterns (review diffs)
    - claude-provision/nice-to-have: Optional patterns with checkboxes

    Returns dict mapping tier name to PR URL (or None if tier was empty/skipped).
    """
    from scripts.sync_to_projects import check_existing_pr

    result = {"must-have": None, "improved": None, "nice-to-have": None}

    # Check for existing PRs on any of the branches
    branches = {
        "must-have": "claude-provision/must-have",
        "improved": "claude-provision/improved",
        "nice-to-have": "claude-provision/nice-to-have",
    }
    for tier_name, branch in branches.items():
        if check_existing_pr(repo, branch):
            print(f"PR already exists for '{branch}' on {repo}. Skipping {tier_name}.")
            # Still allow other tiers to proceed

    with tempfile.TemporaryDirectory() as tmpdir:
        # Clone once
        try:
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo}: {e}")
            return result

        # Detect default branch
        db_result = subprocess.run(
            ["git", "-C", tmpdir, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True,
        )
        default_branch = db_result.stdout.strip() or "main"

        # Also provision CLAUDE.md + settings.json on the must-have branch
        must_have_items = gaps.get("must-have", [])
        improved_items = gaps.get("improved", [])
        nice_items = gaps.get("nice-to-have", [])

        # --- Must-have PR ---
        if must_have_items and not check_existing_pr(repo, branches["must-have"]):
            must_count = len(must_have_items)
            must_body = (
                "## Must-Have Patterns\n\n"
                f"**{must_count}** essential patterns for this project.\n"
                "These are safe to merge — they add new files only.\n\n"
                "Auto-provisioned from [claude-best-practices]"
                "(https://github.com/abhayla/claude-best-practices) hub.\n\n"
                "## Patterns\n\n"
                + "\n".join(
                    f"- `{i['name']}` ({i['type']})"
                    for i in sorted(must_have_items, key=lambda x: x["name"])
                )
            )
            pr_url = _create_tier_branch_and_pr(
                tmpdir, repo, branches["must-have"], default_branch,
                hub_root, must_have_items,
                f"feat: add {must_count} must-have Claude patterns",
                must_body,
            )
            result["must-have"] = pr_url
            if pr_url:
                # Also provision CLAUDE.md and settings.json on this branch
                project_names_updated = get_project_resource_names(Path(tmpdir) / ".claude")
                rules_present = sorted(project_names_updated.get("rule", set()))
                provision_claude_md(hub_root, Path(tmpdir), stacks, rules_present)
                provision_settings_json(hub_root, Path(tmpdir))
                # Amend to include config files
                add_paths = []
                if (Path(tmpdir) / "CLAUDE.md").exists():
                    add_paths.append("CLAUDE.md")
                if (Path(tmpdir) / ".claude" / "settings.json").exists():
                    add_paths.append(".claude/settings.json")
                if add_paths:
                    subprocess.run(
                        ["git", "-C", tmpdir, "add"] + add_paths,
                        capture_output=True, text=True,
                    )
                    status = subprocess.run(
                        ["git", "-C", tmpdir, "diff", "--cached", "--quiet"],
                        capture_output=True, text=True,
                    )
                    if status.returncode != 0:
                        subprocess.run(
                            ["git", "-C", tmpdir, "commit", "-m",
                             "feat: provision CLAUDE.md and settings.json"],
                            capture_output=True, text=True,
                        )
                        subprocess.run(
                            ["git", "-C", tmpdir, "push"],
                            capture_output=True, text=True,
                        )

        # --- Improved PR ---
        if improved_items and not check_existing_pr(repo, branches["improved"]):
            imp_count = len(improved_items)
            imp_body = (
                "## Improved Patterns\n\n"
                f"**{imp_count}** patterns where the hub has newer versions.\n"
                "Review the diffs carefully — these overwrite existing files.\n\n"
                "Auto-provisioned from [claude-best-practices]"
                "(https://github.com/abhayla/claude-best-practices) hub.\n\n"
                "## Patterns\n\n"
                + "\n".join(
                    f"- `{i['name']}` ({i['type']}) — {i.get('reason', '')}"
                    for i in sorted(improved_items, key=lambda x: x["name"])
                )
            )
            pr_url = _create_tier_branch_and_pr(
                tmpdir, repo, branches["improved"], default_branch,
                hub_root, improved_items,
                f"feat: upgrade {imp_count} Claude patterns to latest hub versions",
                imp_body,
            )
            result["improved"] = pr_url

        # --- Nice-to-have PR ---
        if nice_items and not check_existing_pr(repo, branches["nice-to-have"]):
            nice_body = _format_nice_to_have_pr_body(nice_items)
            pr_url = _create_tier_branch_and_pr(
                tmpdir, repo, branches["nice-to-have"], default_branch,
                hub_root, nice_items,
                f"feat: {len(nice_items)} optional Claude patterns (check to keep)",
                nice_body,
            )
            result["nice-to-have"] = pr_url

    return result


def provision_to_repo(
    hub_root: Path,
    repo: str,
    gaps: dict[str, list[dict]],
    stacks: list[str],
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    tier: str = "must-have",
) -> Optional[str]:
    """Clone a repo, provision resources + config files, and create a PR.

    Returns the PR URL if successful.
    """
    from scripts.sync_to_projects import check_existing_pr

    branch = "claude-provision"

    if check_existing_pr(repo, branch):
        print(f"PR already exists for branch '{branch}' on {repo}. Skipping.")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo}.git", tmpdir],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Failed to clone {repo}: {e}")
            return None

        subprocess.run(
            ["git", "-C", tmpdir, "checkout", "-b", branch],
            capture_output=True, text=True, check=True,
        )

        # Full provision
        summary = provision_to_local(hub_root, Path(tmpdir), gaps, stacks, tier)
        copied = summary["copied_files"]

        # Analyze overlaps for PR body
        updated_project_names = get_project_resource_names(Path(tmpdir) / ".claude")
        overlaps = analyze_overlaps_local(
            hub_root, Path(tmpdir), hub_resources, updated_project_names
        )
        divergence_table = format_divergence_table(overlaps)

        # Git add — only include tracked/trackable files
        # Note: CLAUDE.local.md is typically gitignored (personal prefs), so skip it
        add_paths = []
        if (Path(tmpdir) / ".claude").exists():
            add_paths.append(".claude/")
        if (Path(tmpdir) / "CLAUDE.md").exists():
            add_paths.append("CLAUDE.md")
        if not add_paths:
            print("Nothing to provision — no files to stage.")
            return None
        result = subprocess.run(
            ["git", "-C", tmpdir, "add"] + add_paths,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"git add failed: {result.stderr}")
            return None

        # Check if there are staged changes — skip PR if nothing changed
        status_result = subprocess.run(
            ["git", "-C", tmpdir, "diff", "--cached", "--quiet"],
            capture_output=True, text=True,
        )
        if status_result.returncode == 0:
            # No staged changes
            print("Nothing to provision — project is already up to date.")
            return None

        must_count = len(gaps.get("must-have", []))
        nice_count = len(gaps.get("nice-to-have", []))
        commit_msg = (
            f"feat: provision {len(copied)} Claude resources + config\n\n"
            f"Added {must_count} must-have and "
            f"{nice_count if tier == 'nice-to-have' else 0} nice-to-have resources.\n"
            f"CLAUDE.md: {summary['claude_md']}\n"
            f"CLAUDE.local.md: {summary['claude_local_md']}\n"
            f"settings.json: {summary['settings_json']}\n\n"
            f"Files:\n" + "\n".join(f"  - {f}" for f in copied[:20])
        )
        if len(copied) > 20:
            commit_msg += f"\n  ... and {len(copied) - 20} more"

        subprocess.run(
            ["git", "-C", tmpdir, "commit", "-m", commit_msg],
            capture_output=True, text=True, check=True,
        )

        subprocess.run(
            ["git", "-C", tmpdir, "push", "-u", "origin", branch],
            capture_output=True, text=True, check=True,
        )

        pr_body = (
            "## Summary\n\n"
            f"Auto-provisioned from [claude-best-practices]"
            f"(https://github.com/abhayla/claude-best-practices) hub.\n\n"
            f"- **{must_count}** must-have resources\n"
            f"- **{nice_count if tier == 'nice-to-have' else 0}** nice-to-have resources\n"
            f"- CLAUDE.md: {summary['claude_md']}\n"
            f"- CLAUDE.local.md: {summary['claude_local_md']}\n"
            f"- settings.json: {summary['settings_json']}\n\n"
            "## Files added\n\n"
            + "\n".join(f"- `{f}`" for f in copied[:30])
        )
        if len(copied) > 30:
            pr_body += f"\n- ... and {len(copied) - 30} more"

        if divergence_table:
            pr_body += f"\n\n{divergence_table}"

        result = subprocess.run(
            ["gh", "pr", "create",
             "--repo", repo,
             "--head", branch,
             "--title", f"feat: provision {len(copied)} Claude resources + config",
             "--body", pr_body],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"PR creation failed: {result.stderr}")
            return None


# --- Main ---


def main():
    parser = argparse.ArgumentParser(
        description="Recommend Claude resources for a project based on tech stack analysis"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--repo", help="GitHub repo (owner/name)")
    group.add_argument("--local", help="Local project directory path")

    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--apply", action="store_true",
                              help="Apply recommendations (copy files or create PR)")
    action_group.add_argument("--provision", action="store_true",
                              help="Provision project (apply + CLAUDE.md + settings.json)")
    parser.add_argument("--tier", choices=["must-have", "nice-to-have"],
                        default="must-have",
                        help="Minimum tier to apply (default: must-have)")
    parser.add_argument("--use-config", action="store_true",
                        help="Use stacks from config/repos.yml instead of auto-detection")
    parser.add_argument("--diff", action="store_true",
                        help="Compare content of overlapping resources to detect divergence")
    parser.add_argument("--json", action="store_true", dest="json_output",
                        help="Output results as JSON")
    parser.add_argument("--multi-pr", action="store_true", dest="multi_pr",
                        default=True,
                        help="Create separate PRs per tier (default for --provision)")
    parser.add_argument("--single-pr", action="store_false", dest="multi_pr",
                        help="Create a single PR for all tiers (legacy behavior)")
    parser.add_argument("--skip-third-party", action="store_true",
                        help="Skip third-party skill recommendations and installation")

    args = parser.parse_args()
    hub_root = Path(__file__).parent.parent

    # Step 1: Detect stacks
    stacks = None
    if args.use_config and args.repo:
        config_path = hub_root / "config" / "repos.yml"
        stacks = get_stacks_from_config(args.repo, config_path)
        if stacks:
            print(f"Stacks from config: {', '.join(stacks)}")
        else:
            print(f"Repo '{args.repo}' not found in config/repos.yml, falling back to auto-detection")

    if stacks is None:
        if args.local:
            stacks = detect_stacks_from_dir(Path(args.local))
        else:
            stacks = detect_stacks_from_repo(args.repo)
        print(f"Auto-detected stacks: {', '.join(stacks) if stacks else 'none'}")

    # Step 1b: Detect dependencies
    if args.local:
        deps = detect_dependencies_from_dir(Path(args.local))
    else:
        deps = detect_dependencies_from_repo(args.repo)
    dep_promoted = resolve_dep_patterns(deps)
    if dep_promoted:
        print(f"Dependency-promoted patterns: {', '.join(sorted(dep_promoted))}")

    # Step 1c: Resolve third-party skills
    third_party_matched = []
    if not args.skip_third_party:
        project_dir = Path(args.local) if args.local else None
        third_party_matched = resolve_third_party_skills(deps, project_dir, hub_root)
        if third_party_matched:
            names = [e.get("skill", e.get("repo", "").split("/")[-1]) for e in third_party_matched]
            print(f"Third-party skills matched: {', '.join(names)}")

    # Step 2: Get project resources
    if args.local:
        project_names = get_project_resource_names(Path(args.local) / ".claude")
    else:
        project_names = get_project_resources_from_repo(args.repo)

    existing_count = sum(len(v) for v in project_names.values())
    print(f"Project has {existing_count} existing resources")

    # Step 3: Get hub resources
    hub_resources = get_hub_resources(hub_root)

    # Step 4: Analyze gaps (with dependency-aware tiering)
    gaps = analyze_gaps(hub_resources, project_names, stacks, deps)

    # Step 4b: Detect improved patterns (hub has newer versions of existing patterns)
    registry_path = hub_root / "registry" / "patterns.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        project_claude_dir = (
            Path(args.local) / ".claude" if args.local
            else None  # Remote mode handled separately
        )
        if project_claude_dir and project_claude_dir.exists():
            improved = detect_improved_patterns(
                hub_root, project_claude_dir, hub_resources, project_names, registry,
            )
            gaps["improved"] = [
                {"name": i["name"], "type": i["type"], "tier": "improved",
                 "reason": i["reason"]}
                for i in improved
            ]

    # Step 5: Output (defer JSON when --provision is also set)
    if args.json_output and not args.provision:
        output = gaps
        if third_party_matched:
            output = dict(gaps)
            output["third_party_skills"] = [
                {"repo": e.get("repo"), "skill": e.get("skill", ""),
                 "match_reason": e.get("match_reason", "")}
                for e in third_party_matched
            ]
        print(json.dumps(output, indent=2))
    elif not args.json_output:
        report = format_report(gaps, stacks, project_names, hub_resources)
        print()
        print(report)
        # Append third-party recommendations
        if third_party_matched:
            print(format_recommendations(third_party_matched))

    # Step 6: Apply if requested
    if args.apply:
        print(f"\nApplying {args.tier} tier recommendations...")
        if args.local:
            copied = apply_to_local(hub_root, Path(args.local), gaps, args.tier)
            print(f"Copied {len(copied)} files to {args.local}/.claude/")
            for f in copied:
                print(f"  + {f}")
        else:
            pr_url = apply_to_repo(hub_root, args.repo, gaps, args.tier)
            if pr_url:
                print(f"PR created: {pr_url}")

    # Step 6b: Provision if requested
    if args.provision:
        action_labels = {
            "must-have": "add (new)",
            "improved": "upgrade (hub newer)",
            "nice-to-have": "optional",
            "skip": "skip",
        }
        pr_urls = {}
        provision_summary = None

        if args.local:
            summary = provision_to_local(hub_root, Path(args.local), gaps, stacks, args.tier)
            # Install third-party skills after hub patterns are copied
            if third_party_matched:
                tp_results = try_install_third_party(Path(args.local), third_party_matched)
                summary["third_party_skills"] = tp_results
            provision_summary = summary
        elif getattr(args, "multi_pr", True):
            pr_urls = provision_to_repo_multi_pr(
                hub_root, args.repo, gaps, stacks,
                hub_resources, project_names,
            )
        else:
            pr_url = provision_to_repo(
                hub_root, args.repo, gaps, stacks,
                hub_resources, project_names, args.tier,
            )
            if pr_url:
                pr_urls = {"all": pr_url}

        # Combined JSON output when both --provision and --json are set
        if args.json_output:
            combined = {"gaps": gaps, "provision": provision_summary or {}}
            print(json.dumps(combined, indent=2))
        else:
            # --- Print detailed summary ---
            print()
            print("=" * 100)
            print("PROVISION SUMMARY")
            print("=" * 100)

            for tier_name in ("must-have", "improved", "nice-to-have", "skip"):
                items = gaps.get(tier_name, [])
                if not items:
                    continue
                action = action_labels.get(tier_name, tier_name)
                print(f"\n--- {tier_name.upper()} ({len(items)}) ---")
                print(f"  {'Type':<8s} {'Name':<40s} {'Action':<22s} {'Reason'}")
                print(f"  {'----':<8s} {'----':<40s} {'------':<22s} {'------'}")
                for item in sorted(items, key=lambda x: (x["type"], x["name"])):
                    reason = item.get("reason", "")
                    print(f"  {item['type']:<8s} {item['name']:<40s} {action:<22s} {reason}")

            # Third-party skills
            if third_party_matched:
                print(format_recommendations(third_party_matched))
                if args.local and summary.get("third_party_skills"):
                    print(format_install_results(summary["third_party_skills"]))

            # Config files (local mode)
            if args.local:
                print(f"\n--- CONFIG ---")
                print(f"  CLAUDE.md:     {summary['claude_md']}")
                print(f"  settings.json: {summary['settings_json']}")
                print(f"\n  Files copied: {len(summary['copied_files'])}")

            # PRs (remote mode)
            if pr_urls:
                print(f"\n--- PRs CREATED ---")
                pr_action_hints = {
                    "must-have": "merge confidently",
                    "improved": "review diffs",
                    "nice-to-have": "check boxes, comment /apply",
                    "all": "review and merge",
                }
                for tier_name, url in pr_urls.items():
                    if url:
                        hint = pr_action_hints.get(tier_name, "")
                        print(f"  {tier_name:<14s} {url} ({hint})")
                    else:
                        print(f"  {tier_name:<14s} (skipped)")

            # Totals
            print()
            total_must = len(gaps.get("must-have", []))
            total_imp = len(gaps.get("improved", []))
            total_nice = len(gaps.get("nice-to-have", []))
            total_skip = len(gaps.get("skip", []))
            print(f"TOTAL: {total_must} must-have, {total_imp} improved, "
                  f"{total_nice} nice-to-have, {total_skip} skip")
            print("=" * 100)

    # Step 7: Diff overlapping resources if requested
    if args.diff:
        print("\nAnalyzing content divergence for overlapping resources...")
        if args.local:
            overlaps = analyze_overlaps_local(
                hub_root, Path(args.local), hub_resources, project_names
            )
        else:
            overlaps = analyze_overlaps_repo(
                hub_root, args.repo, hub_resources, project_names
            )

        if args.json_output:
            # Strip non-serializable fields
            print(json.dumps(overlaps, indent=2))
        else:
            diff_report = format_diff_report(overlaps)
            print()
            print(diff_report)


if __name__ == "__main__":
    main()
