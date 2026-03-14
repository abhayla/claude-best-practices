"""Bootstrap a new project from the best practices hub."""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


# Stack prefixes for filtering core/.claude/ contents by stack
STACK_PREFIXES = {
    "fastapi-python": "fastapi-",
    "android-compose": "android-",
    "ai-gemini": "ai-gemini-",
    "firebase-auth": "firebase-",
    "react-nextjs": "react-",
}


def get_available_stacks() -> list[str]:
    """Return list of available stack names."""
    return sorted(STACK_PREFIXES.keys())


def validate_stack_selection(stacks: list[str]) -> list[str]:
    """Validate that selected stacks are known."""
    errors = []
    available = get_available_stacks()
    for stack in stacks:
        if stack not in STACK_PREFIXES:
            errors.append(f"Unknown stack: '{stack}'. Available: {available}")
    return errors


def copy_claude_dir(hub_root: Path, target_dir: Path, stacks: list[str]) -> list[str]:
    """Copy core/.claude/ contents to target .claude/, filtering by selected stacks.

    - Files without a stack prefix are always copied (universal/core).
    - Files with a stack prefix are only copied if that stack is selected.
    """
    copied = []
    claude_src = hub_root / "core" / ".claude"
    if not claude_src.exists():
        return copied

    # Build set of allowed prefixes from selected stacks
    allowed_prefixes = set()
    for stack in stacks:
        prefix = STACK_PREFIXES.get(stack)
        if prefix:
            allowed_prefixes.add(prefix)

    # All known prefixes (to detect stack-specific files)
    all_prefixes = set(STACK_PREFIXES.values())

    for src_file in claude_src.rglob("*"):
        if not src_file.is_file():
            continue
        if src_file.name == ".gitkeep":
            continue

        # Determine if file is stack-specific
        fname = src_file.name
        # For skills, check the parent directory name (skill-name/SKILL.md)
        if fname == "SKILL.md":
            check_name = src_file.parent.name
        else:
            check_name = fname.replace(".md", "")

        is_stack_specific = any(check_name.startswith(p) for p in all_prefixes)

        if is_stack_specific:
            # Only copy if its prefix is in the allowed set
            if not any(check_name.startswith(p) for p in allowed_prefixes):
                continue

        rel = src_file.relative_to(claude_src)
        dst_file = target_dir / ".claude" / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        copied.append(str(Path(".claude") / rel))

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
    errors = validate_stack_selection(stacks)
    if errors:
        print("Stack validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    if dry_run:
        print(f"DRY RUN: Would bootstrap {target_dir} with stacks: {stacks}")
        print(f"  Source: {hub_root / 'core' / '.claude'}")
        prefixes = [STACK_PREFIXES[s] for s in stacks if s in STACK_PREFIXES]
        print(f"  Stack prefixes included: {prefixes}")
        return

    print(f"Copying .claude/ patterns (stacks: {', '.join(stacks)})...")
    copied = copy_claude_dir(hub_root, target_dir, stacks)
    print(f"  Copied {len(copied)} files")

    sync_config = generate_sync_config(hub_repo, stacks)
    sync_path = target_dir / ".claude" / "sync-config.yml"
    sync_path.parent.mkdir(parents=True, exist_ok=True)
    sync_path.write_text(sync_config)
    print(f"Generated {sync_path}")

    template_path = hub_root / "core" / ".claude" / "CLAUDE.md.template"
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
