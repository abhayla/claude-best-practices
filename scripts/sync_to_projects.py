"""Sync hub patterns to registered project repos via PRs."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml

from scripts.bootstrap import STACK_PREFIXES


def load_repos_config(config_path: Path) -> list[dict]:
    """Load repos from config/repos.yml."""
    if not config_path.exists():
        return []
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("repos", [])


def get_repo_sync_config(repo: str) -> Optional[dict]:
    """Fetch .claude/sync-config.yml from a GitHub repo via API."""
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/.claude/sync-config.yml",
             "--jq", ".content", "-H", "Accept: application/vnd.github.v3.raw"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return yaml.safe_load(result.stdout)
    except Exception:
        pass
    return None


def check_existing_pr(repo: str, branch: str) -> bool:
    """Check if there's already an open PR for the sync branch."""
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            prs = json.loads(result.stdout)
            return len(prs) > 0
    except Exception:
        pass
    return False


def pattern_matches_stacks(pattern_name: str, selected_stacks: list[str], category: str) -> bool:
    """Check if a pattern should be synced to a project based on its stacks.

    Uses prefix-based matching: a pattern with name 'fastapi-backend' matches
    the 'fastapi-python' stack because it starts with the 'fastapi-' prefix.
    Core patterns (no stack prefix) always match.
    """
    # Build allowed prefixes from selected stacks
    allowed_prefixes = set()
    for stack in selected_stacks:
        prefix = STACK_PREFIXES.get(stack)
        if prefix:
            allowed_prefixes.add(prefix)

    # All known prefixes
    all_prefixes = set(STACK_PREFIXES.values())

    # Check if this pattern is stack-specific
    is_stack_specific = any(pattern_name.startswith(p) for p in all_prefixes)

    if not is_stack_specific:
        # Core pattern — always matches
        return True

    # Stack-specific — check if its prefix is allowed
    return any(pattern_name.startswith(p) for p in allowed_prefixes)


def build_sync_diff(hub_registry: dict, remote_config: dict) -> list[dict]:
    """Compute which patterns need syncing to a project."""
    selected_stacks = remote_config.get("selected_stacks", [])

    updates = []
    for name, entry in hub_registry.items():
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        category = entry.get("category", "core")
        if not pattern_matches_stacks(name, selected_stacks, category):
            continue
        updates.append({
            "name": name,
            "type": entry.get("type"),
            "version": entry.get("version"),
            "category": category,
        })
    return updates
