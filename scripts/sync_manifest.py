import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file with line-ending normalization."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    normalized = content.replace("\r\n", "\n")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def classify_sync_status(
    hub_hash: str, project_hash: str, manifest_hash: str | None,
) -> str:
    """Classify a pattern's sync status using 3-way comparison.

    Returns one of: 'up-to-date', 'hub-only', 'project-only', 'conflict', 'no-manifest'.
    """
    if hub_hash == project_hash:
        return "up-to-date"
    if manifest_hash is None:
        return "no-manifest"
    if hub_hash != manifest_hash and project_hash == manifest_hash:
        return "hub-only"
    if hub_hash == manifest_hash and project_hash != manifest_hash:
        return "project-only"
    return "conflict"


def load_sync_manifest(project_dir: Path) -> dict:
    """Load sync manifest from project. Returns empty structure if missing/corrupt."""
    manifest_path = project_dir / ".claude" / "sync-manifest.json"
    if not manifest_path.exists():
        return {
            "_meta": {
                "version": "1.0.0",
                "hub_repo": "abhayla/claude-best-practices",
                "created": datetime.now(timezone.utc).isoformat(),
                "last_sync": None,
            },
            "files": {},
        }
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "files" not in data:
            raise ValueError("corrupt manifest")
        return data
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return {
            "_meta": {
                "version": "1.0.0",
                "hub_repo": "abhayla/claude-best-practices",
                "created": datetime.now(timezone.utc).isoformat(),
                "last_sync": None,
            },
            "files": {},
        }


def save_sync_manifest(project_dir: Path, manifest: dict) -> None:
    """Write sync manifest to project directory."""
    manifest["_meta"]["last_sync"] = datetime.now(timezone.utc).isoformat()
    manifest_path = project_dir / ".claude" / "sync-manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_sync_classification(
    hub_root: Path,
    project_dir: Path,
    hub_resources: dict[str, list[dict]],
    project_names: dict[str, set[str]],
    manifest: dict,
) -> dict[str, list[dict]]:
    """Classify all overlapping resources by sync status.

    Returns dict keyed by classification ('up-to-date', 'hub-only',
    'project-only', 'conflict', 'no-manifest'), each a list of items.
    """
    claude_src = hub_root / "core" / ".claude"
    claude_dst = project_dir / ".claude"
    result = {
        "up-to-date": [], "hub-only": [], "project-only": [],
        "conflict": [], "no-manifest": [],
    }

    for resource_type, resources in hub_resources.items():
        for resource in resources:
            name = resource["name"]

            # Only process resources that exist in BOTH hub and project
            if name not in project_names.get(resource_type, set()):
                continue

            # Resolve file paths
            hub_files = _resolve_resource_files(claude_src, name, resource_type)
            project_files = _resolve_resource_files(claude_dst, name, resource_type)

            if not hub_files or not project_files:
                continue

            # Classify based on the primary file (SKILL.md for skills, *.md for others)
            primary_hub = hub_files[0]
            primary_project = project_files[0]
            rel_path = str(primary_hub.relative_to(claude_src)).replace("\\", "/")

            hub_hash = _compute_file_hash(primary_hub)
            project_hash = _compute_file_hash(primary_project)
            manifest_hash = manifest.get("files", {}).get(rel_path, {}).get("hub_hash")

            status = classify_sync_status(hub_hash, project_hash, manifest_hash)
            item = {
                "name": name,
                "type": resource_type,
                "rel_path": rel_path,
                "hub_hash": hub_hash,
                "project_hash": project_hash,
                "manifest_hash": manifest_hash,
                "all_hub_files": [str(f.relative_to(claude_src)).replace("\\", "/") for f in hub_files],
            }
            result[status].append(item)

    return result


def _resolve_resource_files(claude_dir: Path, name: str, resource_type: str) -> list[Path]:
    """Resolve all files for a resource. Returns empty list if not found.

    For skills, SKILL.md is always the primary file (index 0) — sync
    classification uses the primary file to detect hub-vs-project drift.
    """
    if resource_type == "skill":
        skill_dir = claude_dir / "skills" / name
        if not skill_dir.is_dir():
            return []
        all_files = sorted(f for f in skill_dir.rglob("*") if f.is_file())
        # Ensure SKILL.md is the primary file (first element) for sync comparison
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists() and skill_md in all_files:
            all_files.remove(skill_md)
            all_files.insert(0, skill_md)
        return all_files
    elif resource_type == "rule":
        path = claude_dir / "rules" / f"{name}.md"
        return [path] if path.exists() else []
    elif resource_type == "agent":
        path = claude_dir / "agents" / f"{name}.md"
        return [path] if path.exists() else []
    elif resource_type == "hook":
        path = claude_dir / "hooks" / f"{name}.sh"
        return [path] if path.exists() else []
    return []


def update_improved_to_local(
    hub_root: Path, target_dir: Path, items: list[dict],
) -> list[str]:
    """Copy hub versions over existing project files for auto-updatable items."""
    claude_src = hub_root / "core" / ".claude"
    claude_dst = target_dir / ".claude"
    updated = []

    for item in items:
        name = item["name"]
        resource_type = item["type"]
        hub_files = _resolve_resource_files(claude_src, name, resource_type)

        for hub_file in hub_files:
            rel = hub_file.relative_to(claude_src)
            dst_file = claude_dst / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(hub_file, dst_file)
            updated.append(str(Path(".claude") / rel))

    return updated


def update_manifest_after_sync(
    manifest: dict,
    synced_files: list[str],
    hub_root: Path,
) -> dict:
    """Update manifest with hub hashes for all synced files."""
    claude_src = hub_root / "core" / ".claude"
    now = datetime.now(timezone.utc).isoformat()

    for rel_str in synced_files:
        # rel_str is like ".claude/rules/workflow.md" — strip .claude/ prefix
        rel_from_claude = rel_str.replace("\\", "/")
        if rel_from_claude.startswith(".claude/"):
            rel_from_claude = rel_from_claude[len(".claude/"):]

        hub_file = claude_src / rel_from_claude
        if hub_file.exists():
            manifest["files"][rel_from_claude] = {
                "hub_hash": _compute_file_hash(hub_file),
                "synced_at": now,
            }

    return manifest
