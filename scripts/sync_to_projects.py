"""Sync hub patterns to registered project repos via PRs."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml


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


def build_sync_diff(hub_registry: dict, remote_config: dict) -> list[dict]:
    """Compute which patterns need syncing to a project."""
    selected_stacks = remote_config.get("selected_stacks", [])
    last_version = remote_config.get("last_sync_version", "v0.0")

    updates = []
    for name, entry in hub_registry.items():
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        category = entry.get("category", "core")
        if category != "core" and category.replace("stack:", "") not in selected_stacks:
            continue
        updates.append({
            "name": name,
            "type": entry.get("type"),
            "version": entry.get("version"),
            "category": category,
        })
    return updates
