from pathlib import Path
import yaml


def load_plugin_recommendations(config_path: Path) -> dict:
    """Load config/plugin-recommendations.yml; returns {} when absent (feature degrades off)."""
    if not config_path.exists():
        return {}
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def recommend_plugins(stacks: list[str], deps: dict[str, list[str]], config: dict) -> dict:
    """Map detected stacks + dependencies to the marketplace plugins a project should install.

    Returns {"marketplace", "universal": [{name, why}], "stack_packs": [names],
             "provision_note", "install_commands": [...]} — empty dict if config is empty.
    """
    if not config:
        return {}
    marketplace = config.get("marketplace", "")
    universal = config.get("universal", []) or []

    packs: set[str] = set()
    for stack in stacks or []:
        packs.update(config.get("by_stack", {}).get(stack, []))
    all_dep_names = set()
    for dep_list in (deps or {}).values():
        all_dep_names.update(dep_list)
    for dep_name in all_dep_names:
        packs.update(config.get("by_dependency", {}).get(dep_name, []))

    names = [u["name"] if isinstance(u, dict) else u for u in universal] + sorted(packs)
    suffix = f"@{marketplace}" if marketplace else ""
    return {
        "marketplace": marketplace,
        "universal": universal,
        "stack_packs": sorted(packs),
        "provision_note": config.get("provision_note", ""),
        "install_commands": [f"/plugin install {n}{suffix}" for n in names],
    }


def print_plugin_recommendations(rec: dict) -> None:
    """Print the PLUGIN RECOMMENDATIONS report section (no-op on empty rec)."""
    if not rec:
        return
    print("\n=== PLUGIN RECOMMENDATIONS (install-not-copy) ===")
    for u in rec["universal"]:
        name, why = (u["name"], u.get("why", "")) if isinstance(u, dict) else (u, "")
        print(f"  [universal] {name}" + (f" — {why}" if why else ""))
    for p in rec["stack_packs"]:
        print(f"  [stack]     {p}")
    if not rec["stack_packs"]:
        print("  [stack]     (no stack pack matched — universal plugins only)")
    print("  Install (after one-time `/plugin marketplace add <hub>`):")
    for cmd in rec["install_commands"]:
        print(f"    {cmd}")
    if rec.get("provision_note"):
        print(f"  Note: {rec['provision_note']}")
