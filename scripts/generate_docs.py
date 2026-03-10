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


def generate_dashboard_html(registry: dict, stacks_dir: Path) -> str:
    """Generate an interactive HTML dashboard."""
    counts = count_patterns(registry)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Build pattern rows
    pattern_rows = []
    for name, entry in sorted(registry.items()):
        if name.startswith("_") or not isinstance(entry, dict):
            continue
        deps = ", ".join(entry.get("dependencies", [])) or "—"
        tags = ", ".join(entry.get("tags", [])) or "—"
        pattern_rows.append(f"""
            <tr data-type="{entry.get('type', '')}" data-category="{entry.get('category', '')}">
                <td>{name}</td>
                <td><span class="badge badge-{entry.get('type', 'unknown')}">{entry.get('type', '?')}</span></td>
                <td>{entry.get('category', '?')}</td>
                <td>{entry.get('version', '?')}</td>
                <td>{entry.get('source', '?')}</td>
                <td>{deps}</td>
                <td>{tags}</td>
            </tr>""")

    # Build stack sections
    stack_sections = []
    if stacks_dir.exists():
        for stack_dir in sorted(stacks_dir.iterdir()):
            if not stack_dir.is_dir():
                continue
            config_file = stack_dir / "stack-config.yml"
            if config_file.exists():
                with open(config_file) as f:
                    config = yaml.safe_load(f)
                stack_sections.append(f"""
                    <div class="stack-card">
                        <h3>{config.get('name', stack_dir.name)}</h3>
                        <p>{config.get('description', '')}</p>
                    </div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Best Practices Hub — Dashboard</title>
<style>
:root {{
    --bg: #f8f9fa; --card-bg: #fff; --text: #212529; --border: #dee2e6;
    --primary: #6f42c1; --primary-light: #e8dff5;
    --badge-skill: #0d6efd; --badge-hook: #198754; --badge-agent: #dc3545; --badge-rule: #fd7e14;
}}
[data-theme="dark"] {{
    --bg: #1a1a2e; --card-bg: #16213e; --text: #e0e0e0; --border: #2a2a4a;
    --primary: #a78bfa; --primary-light: #2d2250;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }}
.header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }}
h1 {{ color: var(--primary); }}
.theme-toggle {{ cursor: pointer; padding: 0.5rem 1rem; border: 1px solid var(--border); border-radius: 8px; background: var(--card-bg); color: var(--text); }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; text-align: center; }}
.stat-card .number {{ font-size: 2rem; font-weight: bold; color: var(--primary); }}
.stat-card .label {{ font-size: 0.85rem; color: var(--text); opacity: 0.7; margin-top: 0.25rem; }}
.search {{ width: 100%; padding: 0.75rem 1rem; border: 1px solid var(--border); border-radius: 8px; font-size: 1rem; background: var(--card-bg); color: var(--text); margin-bottom: 1rem; }}
.filters {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }}
.filter-btn {{ padding: 0.4rem 0.8rem; border: 1px solid var(--border); border-radius: 20px; cursor: pointer; background: var(--card-bg); color: var(--text); font-size: 0.85rem; }}
.filter-btn.active {{ background: var(--primary); color: white; border-color: var(--primary); }}
table {{ width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 12px; overflow: hidden; }}
th {{ background: var(--primary-light); padding: 0.75rem; text-align: left; cursor: pointer; user-select: none; }}
th:hover {{ opacity: 0.8; }}
td {{ padding: 0.75rem; border-top: 1px solid var(--border); }}
tr:hover {{ background: var(--primary-light); }}
.badge {{ padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; color: white; }}
.badge-skill {{ background: var(--badge-skill); }}
.badge-hook {{ background: var(--badge-hook); }}
.badge-agent {{ background: var(--badge-agent); }}
.badge-rule {{ background: var(--badge-rule); }}
.badge-unknown {{ background: #6c757d; }}
.section {{ margin-top: 2rem; }}
.section h2 {{ margin-bottom: 1rem; cursor: pointer; }}
.section h2::before {{ content: "▼ "; font-size: 0.8em; }}
.section.collapsed h2::before {{ content: "▶ "; }}
.section.collapsed .section-content {{ display: none; }}
.stacks-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }}
.stack-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }}
.stack-card h3 {{ color: var(--primary); margin-bottom: 0.5rem; }}
.footer {{ margin-top: 3rem; text-align: center; font-size: 0.85rem; opacity: 0.6; }}
</style>
</head>
<body>
<div class="header">
    <h1>Claude Best Practices Hub</h1>
    <button class="theme-toggle" onclick="toggleTheme()">Toggle Dark Mode</button>
</div>
<p style="margin-bottom:1rem;opacity:0.7">Last updated: {now} (auto-generated)</p>

<div class="stats">
    <div class="stat-card"><div class="number">{counts['total']}</div><div class="label">Total Patterns</div></div>
    <div class="stat-card"><div class="number">{counts['core']}</div><div class="label">Core</div></div>
    <div class="stat-card"><div class="number">{counts['stack_specific']}</div><div class="label">Stack-specific</div></div>
    {"".join(f'<div class="stat-card"><div class="number">{c}</div><div class="label">{t.title()}s</div></div>' for t, c in sorted(counts['by_type'].items()))}
</div>

<div class="section" id="patterns-section">
    <h2 onclick="toggleSection('patterns-section')">Pattern Inventory</h2>
    <div class="section-content">
        <input type="text" class="search" placeholder="Search patterns..." oninput="filterTable(this.value)">
        <div class="filters">
            <button class="filter-btn active" onclick="filterType('all', this)">All</button>
            <button class="filter-btn" onclick="filterType('skill', this)">Skills</button>
            <button class="filter-btn" onclick="filterType('hook', this)">Hooks</button>
            <button class="filter-btn" onclick="filterType('agent', this)">Agents</button>
            <button class="filter-btn" onclick="filterType('rule', this)">Rules</button>
        </div>
        <table id="patterns-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Name</th>
                    <th onclick="sortTable(1)">Type</th>
                    <th onclick="sortTable(2)">Category</th>
                    <th onclick="sortTable(3)">Version</th>
                    <th onclick="sortTable(4)">Source</th>
                    <th onclick="sortTable(5)">Dependencies</th>
                    <th onclick="sortTable(6)">Tags</th>
                </tr>
            </thead>
            <tbody>{"".join(pattern_rows) if pattern_rows else "<tr><td colspan='7' style='text-align:center;opacity:0.5'>No patterns yet</td></tr>"}
            </tbody>
        </table>
    </div>
</div>

<div class="section" id="stacks-section">
    <h2 onclick="toggleSection('stacks-section')">Available Stacks</h2>
    <div class="section-content">
        <div class="stacks-grid">{"".join(stack_sections) if stack_sections else "<p>No stacks configured.</p>"}
        </div>
    </div>
</div>

<div class="footer">
    <p>Claude Best Practices Hub — <a href="https://github.com/abhayla/claude-best-practices">GitHub</a></p>
</div>

<script>
function toggleTheme() {{
    const html = document.documentElement;
    html.setAttribute('data-theme', html.getAttribute('data-theme') === 'dark' ? '' : 'dark');
}}
function toggleSection(id) {{
    document.getElementById(id).classList.toggle('collapsed');
}}
function filterTable(query) {{
    const rows = document.querySelectorAll('#patterns-table tbody tr');
    query = query.toLowerCase();
    rows.forEach(row => {{
        row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    }});
}}
function filterType(type, btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const rows = document.querySelectorAll('#patterns-table tbody tr');
    rows.forEach(row => {{
        if (type === 'all' || row.dataset.type === type) {{
            row.style.display = '';
        }} else {{
            row.style.display = 'none';
        }}
    }});
}}
function sortTable(col) {{
    const table = document.getElementById('patterns-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const dir = table.dataset.sortDir === 'asc' ? 'desc' : 'asc';
    table.dataset.sortDir = dir;
    rows.sort((a, b) => {{
        const aText = a.cells[col]?.textContent || '';
        const bText = b.cells[col]?.textContent || '';
        return dir === 'asc' ? aText.localeCompare(bText) : bText.localeCompare(aText);
    }});
    rows.forEach(row => tbody.appendChild(row));
}}
</script>
</body>
</html>"""


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

    # Generate HTML dashboard
    dashboard_html = generate_dashboard_html(registry, root / "stacks")
    (docs_dir / "dashboard.html").write_text(dashboard_html, encoding="utf-8")
    print("Generated docs/dashboard.html")

    if "--validate" in sys.argv:
        print("Validation passed — all docs generated without errors")
