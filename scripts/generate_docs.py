"""Generate auto-updated documentation for the best practices hub."""

import json
import sys
from datetime import datetime
from pathlib import Path

import yaml


def count_patterns(registry: dict) -> dict:
    """Count patterns by category and type."""
    counts = {"total": 0, "core": 0, "stack_specific": 0, "by_type": {}}
    for name, entry in registry.items():
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        counts["total"] += 1
        if entry.get("category") == "core":
            counts["core"] += 1
        else:
            counts["stack_specific"] += 1
        ptype = entry.get("type", "unknown")
        counts["by_type"][ptype] = counts["by_type"].get(ptype, 0) + 1
    return counts


def generate_dashboard_md(registry: dict, scan_history: list, sync_status: dict) -> str:
    """Generate DASHBOARD.md content."""
    counts = count_patterns(registry)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Claude Best Practices Hub — Dashboard",
        f"> Last updated: {now} (auto-generated)",
        "",
        "## At a Glance",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Patterns | {counts['total']} |",
        f"| Core (universal) | {counts['core']} |",
        f"| Stack-specific | {counts['stack_specific']} |",
    ]

    for ptype, count in sorted(counts["by_type"].items()):
        lines.append(f"| {ptype.title()}s | {count} |")

    lines.extend(["", "## Pattern Inventory", ""])

    core_patterns = {k: v for k, v in registry.items()
                     if not k.startswith("_") and isinstance(v, dict) and v.get("category") == "core"}

    if core_patterns:
        lines.extend(["### Core Patterns", "", "| Name | Type | Version | Source | Dependencies |",
                      "|------|------|---------|--------|--------------|"])
        for name, entry in sorted(core_patterns.items()):
            deps = ", ".join(entry.get("dependencies", [])) or "—"
            lines.append(
                f"| {name} | {entry.get('type', '?')} | {entry.get('version', '?')} | "
                f"{entry.get('source', '?')} | {deps} |"
            )

    lines.extend([
        "",
        "## How to Use",
        "- **Bootstrap new project:** `python scripts/bootstrap.py --stacks android-compose,fastapi-python`",
        "- **Update local practices:** Run `/update-practices` in any Claude Code session",
        "- **Contribute a pattern:** Run `/contribute-practice .claude/skills/my-skill/`",
        "- **Scan a URL:** `gh workflow run scan-internet.yml -f url=\"https://...\"`",
        "- **Scan a repo:** `gh workflow run scan-projects.yml -f repo=\"owner/repo\"`",
        "",
    ])

    return "\n".join(lines)


def generate_stack_catalog(stacks_dir: Path) -> str:
    """Generate STACK-CATALOG.md content."""
    lines = ["# Stack Catalog", "", "Available stacks and their contents.", ""]

    if not stacks_dir.exists():
        return "\n".join(lines + ["_No stacks found._"])

    for stack_dir in sorted(stacks_dir.iterdir()):
        if not stack_dir.is_dir():
            continue
        config_file = stack_dir / "stack-config.yml"
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
            name = config.get("name", stack_dir.name)
            desc = config.get("description", "")
            lines.extend([f"## {name}", f"_{desc}_", ""])

            claude_dir = stack_dir / ".claude"
            if claude_dir.exists():
                for subdir in ["skills", "agents", "hooks", "rules"]:
                    sub = claude_dir / subdir
                    if sub.exists():
                        items = [f.name for f in sub.iterdir() if f.name != ".gitkeep"]
                        if items:
                            lines.append(f"**{subdir.title()}:** {', '.join(items)}")
                lines.append("")

    return "\n".join(lines)


def generate_getting_started(hub_repo: str, available_stacks: list[str]) -> str:
    """Generate GETTING-STARTED.md content."""
    stacks_str = ",".join(available_stacks[:2]) if available_stacks else "core"
    lines = [
        "# Getting Started",
        "",
        "## Quick Start",
        "",
        "### Option A: GitHub Template",
        f'1. Click **"Use this template"** on [{hub_repo}](https://github.com/{hub_repo})',
        "2. Clone your new repo",
        "3. Run bootstrap:",
        "```bash",
        f"python scripts/bootstrap.py --stacks {stacks_str}",
        "```",
        "",
        "### Option B: Bootstrap Existing Project",
        "```bash",
        f"curl -sL https://raw.githubusercontent.com/{hub_repo}/main/bootstrap.sh | bash -s -- --stacks {stacks_str}",
        "```",
        "",
        "## Available Stacks",
        "",
        "| Stack | Description |",
        "|-------|-------------|",
    ]

    for stack in available_stacks:
        lines.append(f"| `{stack}` | See stack-config.yml for details |")

    lines.extend([
        "",
        "## Skills Included",
        "",
        "| Skill | Purpose |",
        "|-------|---------|",
        "| `/update-practices` | Pull latest from hub |",
        "| `/contribute-practice` | Push pattern to hub |",
        "| `/scan-url` | Trigger internet scan |",
        "| `/scan-repo` | Trigger project scan |",
        "",
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    docs_dir = root / "docs"
    docs_dir.mkdir(exist_ok=True)

    registry_path = root / "registry" / "patterns.json"
    with open(registry_path) as f:
        registry = json.load(f)

    dashboard = generate_dashboard_md(registry, [], {})
    (docs_dir / "DASHBOARD.md").write_text(dashboard)
    print("Generated docs/DASHBOARD.md")

    catalog = generate_stack_catalog(root / "stacks")
    (docs_dir / "STACK-CATALOG.md").write_text(catalog)
    print("Generated docs/STACK-CATALOG.md")

    stacks = []
    stacks_dir = root / "stacks"
    if stacks_dir.exists():
        for d in stacks_dir.iterdir():
            if d.is_dir() and (d / "stack-config.yml").exists():
                stacks.append(d.name)

    getting_started = generate_getting_started("abhayla/claude-best-practices", sorted(stacks))
    (docs_dir / "GETTING-STARTED.md").write_text(getting_started)
    print("Generated docs/GETTING-STARTED.md")

    if "--validate" in sys.argv:
        print("Validation passed — all docs generated without errors")
