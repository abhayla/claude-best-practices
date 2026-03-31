"""Aggregate pattern effectiveness telemetry from enrolled projects.

Computes adoption rates, retention, and error prevention rates by scanning
project .claude/ directories and learnings.json files. Writes effectiveness
data back to registry/patterns.json.

Usage:
    PYTHONPATH=. python scripts/aggregate_telemetry.py [--registry PATH] [--config PATH]
"""

import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Pattern types tracked for adoption. Hooks and configs are excluded because
# they have no standard file path convention that can be reliably scanned.
_TRACKED_TYPES = {"skills", "agents", "rules"}


def scan_project_adoption(project_dir: Path) -> dict[str, dict]:
    """Scan a project's .claude/ to determine which provisioned patterns are adopted.

    Reads the sync manifest to know what was provisioned, then checks which
    pattern directories still exist. Returns per-pattern adoption data.

    Returns:
        Dict mapping pattern name to {status, retention_days, provisioned_date}.
        Empty dict if no manifest or no .claude/ dir.
    """
    claude_dir = project_dir / ".claude"
    manifest_path = claude_dir / "sync-manifest.json"

    if not manifest_path.exists():
        return {}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}

    files = manifest.get("files", {})
    if not files:
        return {}

    now = datetime.now(timezone.utc)
    result = {}

    for rel_path, meta in files.items():
        # Extract pattern name from path like "skills/fix-loop/SKILL.md"
        match = re.match(r"^(skills|agents|rules)/([^/]+)", rel_path)
        if not match:
            continue

        resource_type, pattern_name = match.groups()

        # Check if the pattern still exists on disk
        if resource_type == "skills":
            exists = (claude_dir / "skills" / pattern_name / "SKILL.md").exists()
        elif resource_type == "agents":
            exists = (claude_dir / "agents" / f"{pattern_name}.md").exists()
        elif resource_type == "rules":
            exists = (claude_dir / "rules" / f"{pattern_name}.md").exists()
        else:
            continue

        # Compute retention days from provisioned_date
        provisioned_date = meta.get("provisioned_date")
        retention_days = 0
        if provisioned_date:
            try:
                pdate = datetime.fromisoformat(provisioned_date)
                if pdate.tzinfo is None:
                    pdate = pdate.replace(tzinfo=timezone.utc)
                retention_days = max(0, (now - pdate).days)
            except (ValueError, TypeError):
                retention_days = 0

        result[pattern_name] = {
            "status": "adopted" if exists else "deleted",
            "retention_days": retention_days,
            "provisioned_date": provisioned_date,
        }

    return result


def compute_adoption_rate(
    pattern_name: str, project_signals: list[dict[str, dict]]
) -> Optional[float]:
    """Compute adoption rate for a pattern across multiple projects.

    Only counts projects where the pattern was provisioned (present in signals).
    Returns None if pattern was never provisioned to any project.
    """
    provisioned_count = 0
    adopted_count = 0

    for signals in project_signals:
        if pattern_name not in signals:
            continue
        provisioned_count += 1
        if signals[pattern_name].get("status") == "adopted":
            adopted_count += 1

    if provisioned_count == 0:
        return None

    return round(adopted_count / provisioned_count, 2)


def compute_retention_days(
    pattern_name: str, project_signals: list[dict[str, dict]]
) -> Optional[float]:
    """Compute median retention days for a pattern across projects.

    Returns None if no data available.
    """
    days = []
    for signals in project_signals:
        if pattern_name not in signals:
            continue
        entry = signals[pattern_name]
        if "retention_days" in entry:
            days.append(entry["retention_days"])

    if not days:
        return None

    return statistics.median(days)


def compute_error_prevention_rate(
    pattern_name: str, all_learnings: list[dict]
) -> Optional[float]:
    """Compute error prevention effectiveness from linked learnings.

    Looks at all learnings linked to this pattern via hub_pattern_link.
    A single occurrence = 1.0 (caught once, addressed).
    Multiple occurrences of the same error class = lower rate (recurring despite pattern).

    The rate measures: 1 - (recurring_error_classes / total_error_classes).

    Returns None if no learnings are linked to this pattern.
    """
    linked_entries = []
    for project_learnings in all_learnings:
        for entry in project_learnings.get("learnings", []):
            if entry.get("hub_pattern_link") == pattern_name:
                linked_entries.append(entry)

    if not linked_entries:
        return None

    # Group by error class (using tag signature as proxy)
    error_classes: dict[str, int] = {}
    for entry in linked_entries:
        tags = tuple(sorted(entry.get("tags", [])))
        tag_key = "|".join(tags) if tags else entry.get("error", {}).get("message", "unknown")
        error_classes[tag_key] = error_classes.get(tag_key, 0) + 1

    if not error_classes:
        return 1.0

    # Rate: fraction of error classes that occurred only once (addressed, didn't recur)
    single_occurrence = sum(1 for count in error_classes.values() if count == 1)
    total_classes = len(error_classes)

    return round(single_occurrence / total_classes, 2)


def aggregate_project_telemetry(
    project_dirs: list[Path],
    learnings_dirs: Optional[list[Path]] = None,
) -> dict[str, dict]:
    """Aggregate telemetry from multiple project directories.

    Returns per-pattern effectiveness data ready for registry writing.
    """
    if not project_dirs:
        return {}

    # Scan adoption from each project
    project_signals = [scan_project_adoption(d) for d in project_dirs]

    # Collect all pattern names seen across all projects
    all_patterns: set[str] = set()
    for signals in project_signals:
        all_patterns.update(signals.keys())

    # Load learnings from projects (if available)
    all_learnings = []
    for d in (learnings_dirs or project_dirs):
        learnings_path = d / ".claude" / "learnings.json"
        if learnings_path.exists():
            try:
                data = json.loads(learnings_path.read_text(encoding="utf-8"))
                all_learnings.append(data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = {}

    for pattern in sorted(all_patterns):
        adoption = compute_adoption_rate(pattern, project_signals)
        retention = compute_retention_days(pattern, project_signals)
        prevention = compute_error_prevention_rate(pattern, all_learnings)

        # Count projects where this pattern was provisioned
        sample = sum(1 for s in project_signals if pattern in s)

        result[pattern] = {
            "adoption_rate": adoption,
            "retention_days_p50": retention,
            "error_prevention_rate": prevention,
            "sample_size": sample,
            "last_updated": now_str,
        }

    return result


def write_effectiveness_to_registry(
    registry_path: Path, effectiveness: dict[str, dict]
) -> None:
    """Write effectiveness data into registry/patterns.json.

    Only writes to patterns that exist in the registry.
    Omits None values (insufficient data).
    Preserves all existing registry fields.
    """
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return  # Do not crash on corrupt registry

    for pattern_name, eff_data in effectiveness.items():
        if pattern_name not in registry or not isinstance(registry[pattern_name], dict):
            continue

        # Filter out None values
        clean_eff = {k: v for k, v in eff_data.items() if v is not None}

        if clean_eff:
            registry[pattern_name]["effectiveness"] = clean_eff

    # Atomic write: write to temp file then replace
    tmp_path = registry_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(registry_path)


def load_telemetry_aggregates(path: Path) -> dict:
    """Load telemetry aggregates from config/telemetry-aggregates.json."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def save_telemetry_aggregates(path: Path, aggregates: dict) -> None:
    """Save telemetry aggregates to config/telemetry-aggregates.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(aggregates, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate pattern effectiveness telemetry")
    parser.add_argument("--registry", default="registry/patterns.json",
                        help="Path to registry/patterns.json")
    parser.add_argument("--config", default="config/repos.yml",
                        help="Path to config/repos.yml")
    parser.add_argument("--output", default="config/telemetry-aggregates.json",
                        help="Path to write aggregates")
    args = parser.parse_args()

    print("Pattern Effectiveness Telemetry Aggregation")
    print("=" * 50)
    print(f"Registry: {args.registry}")
    print(f"Config: {args.config}")
    print(f"Output: {args.output}")
    print()
    print("Note: Run with local project directories for local aggregation.")
    print("For remote repos, use sync_to_projects.py with --scan-adoption flag.")
