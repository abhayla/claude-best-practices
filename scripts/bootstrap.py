"""Bootstrap a new project from the best practices hub."""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


def load_stack_config(config_path: Path) -> Optional[dict]:
    """Load a stack's configuration file."""
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return yaml.safe_load(f)


def validate_stack_selection(stacks: list[str], configs: dict) -> list[str]:
    """Validate that selected stacks are compatible."""
    errors = []
    for stack in stacks:
        if stack not in configs:
            errors.append(f"Unknown stack: '{stack}'. Available: {list(configs.keys())}")
            continue
        conflicts = configs[stack].get("conflicts_with", [])
        for other in stacks:
            if other in conflicts:
                errors.append(f"Stack '{stack}' conflicts with '{other}'")
    return errors


def copy_layer(src_dir: Path, dst_dir: Path) -> list[str]:
    """Copy a layer's .claude/ contents to destination. Returns copied file paths."""
    copied = []
    claude_src = src_dir / ".claude"
    if not claude_src.exists():
        return copied

    for src_file in claude_src.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.name == ".gitkeep":
            continue

        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied.append(str(rel))

    return copied


def render_template(template: str, variables: dict) -> str:
    """Replace {{VARIABLE}} placeholders in template."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    result = re.sub(r"\{\{#if .*?\}\}.*?\{\{/if\}\}", "", result, flags=re.DOTALL)
    return result


def generate_sync_config(hub_repo: str, stacks: list[str], sync_target: str = "project") -> str:
    """Generate a sync-config.yml for a project."""
    config = {
        "hub_repo": hub_repo,
        "sync_target": sync_target,
        "selected_stacks": stacks,
        "last_sync_version": "v1.0",
        "last_sync_timestamp": datetime.utcnow().isoformat() + "Z",
        "auto_check_on_session_start": True,
    }
    return yaml.dump(config, default_flow_style=False, sort_keys=False)


def bootstrap(hub_root: Path, target_dir: Path, stacks: list[str], hub_repo: str, dry_run: bool = False):
    """Bootstrap a project from the hub."""
    configs = {}
    stacks_dir = hub_root / "stacks"
    if stacks_dir.exists():
        for stack_dir in stacks_dir.iterdir():
            if stack_dir.is_dir():
                cfg = load_stack_config(stack_dir / "stack-config.yml")
                if cfg:
                    configs[cfg["name"]] = cfg

    errors = validate_stack_selection(stacks, configs)
    if errors:
        print("Stack validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    if dry_run:
        print(f"DRY RUN: Would bootstrap {target_dir} with stacks: {stacks}")
        print(f"  Core: {hub_root / 'core'}")
        for s in stacks:
            print(f"  Stack: {hub_root / 'stacks' / s}")
        return

    print("Copying core patterns...")
    copied = copy_layer(hub_root / "core", target_dir)
    print(f"  Copied {len(copied)} files")

    for stack in stacks:
        stack_dir = hub_root / "stacks" / stack
        if stack_dir.exists():
            print(f"Copying {stack} stack...")
            copied = copy_layer(stack_dir, target_dir)
            print(f"  Copied {len(copied)} files")

    sync_config = generate_sync_config(hub_repo, stacks)
    sync_path = target_dir / ".claude" / "sync-config.yml"
    sync_path.parent.mkdir(parents=True, exist_ok=True)
    sync_path.write_text(sync_config)
    print(f"Generated {sync_path}")

    template_path = hub_root / "core" / "CLAUDE.md.template"
    if template_path.exists():
        template = template_path.read_text()
        rendered = render_template(template, {
            "PROJECT_NAME": target_dir.name,
            "PROJECT_DESCRIPTION": "A new project",
            "PLATFORM": ", ".join(stacks),
            "BUILD_TOOLS": "See stack documentation",
            "DEVELOPMENT_COMMANDS": "# Add your commands here",
            "HUB_REPO": hub_repo,
            "SELECTED_STACKS": ", ".join(stacks),
            "LAST_SYNC_TIMESTAMP": datetime.utcnow().isoformat(),
        })
        claude_md = target_dir / "CLAUDE.md"
        if not claude_md.exists():
            claude_md.write_text(rendered)
            print(f"Generated {claude_md}")

    print(f"\nBootstrap complete! Stacks: {', '.join(stacks)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap a project from the hub")
    parser.add_argument("--stacks", required=True, help="Comma-separated stack names")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--hub", default=None, help="Hub repo root (default: this repo)")
    parser.add_argument("--hub-repo", default="abhayla/claude-best-practices", help="Hub repo name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    hub_root = Path(args.hub) if args.hub else Path(__file__).parent.parent
    target = Path(args.target)
    stacks = [s.strip() for s in args.stacks.split(",")]

    bootstrap(hub_root, target, stacks, args.hub_repo, args.dry_run)
