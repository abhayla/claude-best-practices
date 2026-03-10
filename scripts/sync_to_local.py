"""Sync hub patterns to a local project directory."""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from scripts.dedup_check import hash_pattern


def load_sync_config(project_dir: Path) -> Optional[dict]:
    """Load .claude/sync-config.yml from a project."""
    config_path = project_dir / ".claude" / "sync-config.yml"
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return yaml.safe_load(f)


def compare_versions(hub_version: str, local_version: str) -> int:
    """Compare semver strings. Returns -1, 0, or 1."""
    def parse(v):
        return [int(x) for x in v.lstrip("v").split(".")]
    h, l = parse(hub_version), parse(local_version)
    if h > l:
        return 1
    elif h < l:
        return -1
    return 0


def find_updated_patterns(hub_registry: dict, local_dir: Path) -> list[dict]:
    """Find patterns in hub that are newer than local copies."""
    updates = []
    for name, entry in hub_registry.items():
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        # Check if local has this pattern
        local_hash = None
        pattern_type = entry.get("type", "")
        # Build expected local path based on type
        if pattern_type == "skill":
            local_path = local_dir / ".claude" / "skills" / name / "SKILL.md"
        elif pattern_type == "agent":
            local_path = local_dir / ".claude" / "agents" / f"{name}.md"
        elif pattern_type == "hook":
            local_path = local_dir / ".claude" / "hooks" / f"{name}.sh"
        elif pattern_type == "rule":
            local_path = local_dir / ".claude" / "rules" / f"{name}.md"
        else:
            continue

        if local_path.exists():
            local_hash = hash_pattern(str(local_path))
            if local_hash == entry.get("hash"):
                continue  # Already up to date

        updates.append({
            "name": name,
            "type": pattern_type,
            "hub_version": entry.get("version", "1.0.0"),
            "hub_hash": entry.get("hash"),
            "local_exists": local_path.exists(),
            "local_hash": local_hash,
            "description": entry.get("description", ""),
        })

    return updates


def apply_update(hub_root: Path, project_dir: Path, pattern_name: str, pattern_type: str, category: str) -> bool:
    """Copy a pattern from hub to project. Returns True on success."""
    if pattern_type == "skill":
        src = hub_root / ("core" if category == "core" else f"stacks/{category}") / ".claude" / "skills" / pattern_name
        dst = project_dir / ".claude" / "skills" / pattern_name
    elif pattern_type == "agent":
        src_file = hub_root / ("core" if category == "core" else f"stacks/{category}") / ".claude" / "agents" / f"{pattern_name}.md"
        dst = project_dir / ".claude" / "agents"
        dst.mkdir(parents=True, exist_ok=True)
        if src_file.exists():
            shutil.copy2(src_file, dst / f"{pattern_name}.md")
            return True
        return False
    elif pattern_type == "hook":
        src_file = hub_root / ("core" if category == "core" else f"stacks/{category}") / ".claude" / "hooks" / f"{pattern_name}.sh"
        dst = project_dir / ".claude" / "hooks"
        dst.mkdir(parents=True, exist_ok=True)
        if src_file.exists():
            shutil.copy2(src_file, dst / f"{pattern_name}.sh")
            return True
        return False
    elif pattern_type == "rule":
        src_file = hub_root / ("core" if category == "core" else f"stacks/{category}") / ".claude" / "rules" / f"{pattern_name}.md"
        dst = project_dir / ".claude" / "rules"
        dst.mkdir(parents=True, exist_ok=True)
        if src_file.exists():
            shutil.copy2(src_file, dst / f"{pattern_name}.md")
            return True
        return False
    else:
        return False

    if src.exists() and src.is_dir():
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        return True
    return False
