"""Extract reusable patterns from project repositories."""

import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from scripts.dedup_check import hash_pattern, parse_frontmatter


def detect_pattern_type(file_path: Path) -> Optional[str]:
    """Detect pattern type from file location."""
    parts = file_path.parts
    for i, part in enumerate(parts):
        if part == "skills":
            return "skill"
        if part == "agents":
            return "agent"
        if part == "hooks":
            return "hook"
        if part == "rules":
            return "rule"
    return None


def extract_patterns_from_dir(claude_dir: Path) -> list[dict]:
    """Extract all patterns from a .claude/ directory."""
    patterns = []

    if not claude_dir.exists():
        return patterns

    # Skills: .claude/skills/*/SKILL.md
    skills_dir = claude_dir / "skills"
    if skills_dir.exists():
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                fm = parse_frontmatter(skill_file)
                if fm and "name" in fm:
                    patterns.append({
                        "name": fm["name"],
                        "type": "skill",
                        "file_path": str(skill_file),
                        "frontmatter": fm,
                    })

    # Agents: .claude/agents/*.md
    agents_dir = claude_dir / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            fm = parse_frontmatter(agent_file)
            name = fm.get("name") if fm else agent_file.stem
            if name:
                patterns.append({
                    "name": name,
                    "type": "agent",
                    "file_path": str(agent_file),
                    "frontmatter": fm or {},
                })

    # Hooks: .claude/hooks/*.sh
    hooks_dir = claude_dir / "hooks"
    if hooks_dir.exists():
        for hook_file in hooks_dir.glob("*.sh"):
            patterns.append({
                "name": hook_file.stem,
                "type": "hook",
                "file_path": str(hook_file),
                "frontmatter": {},
            })
        for hook_file in hooks_dir.glob("*.py"):
            if hook_file.name == "__pycache__":
                continue
            patterns.append({
                "name": hook_file.stem,
                "type": "hook",
                "file_path": str(hook_file),
                "frontmatter": {},
            })

    # Rules: .claude/rules/*.md
    rules_dir = claude_dir / "rules"
    if rules_dir.exists():
        for rule_file in rules_dir.glob("*.md"):
            fm = parse_frontmatter(rule_file)
            patterns.append({
                "name": rule_file.stem,
                "type": "rule",
                "file_path": str(rule_file),
                "frontmatter": fm or {},
            })

    return patterns


def build_pattern_entry(
    name: str,
    pattern_type: str,
    file_path: Path,
    source: str,
    category: str = "core",
) -> dict:
    """Build a registry entry for a pattern."""
    fm = parse_frontmatter(file_path) or {}
    return {
        "hash": hash_pattern(str(file_path)),
        "type": pattern_type,
        "category": category,
        "version": fm.get("version", "1.0.0"),
        "source": source,
        "discovered": date.today().isoformat(),
        "last_updated": date.today().isoformat(),
        "dependencies": fm.get("dependencies", []),
        "visibility": "public",
        "description": fm.get("description", ""),
        "tags": fm.get("tags", []),
        "changelog": f"v{fm.get('version', '1.0.0')}: Initial import",
    }


def collate_repo(repo_url: str, registry: dict) -> list[dict]:
    """Clone a repo and extract new/updated patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            ["git", "clone", "--depth=1", "--filter=blob:none", "--sparse", repo_url, tmpdir],
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            ["git", "-C", tmpdir, "sparse-checkout", "set", ".claude/"],
            capture_output=True, text=True, check=True,
        )

        claude_dir = Path(tmpdir) / ".claude"
        return extract_patterns_from_dir(claude_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collate patterns from project repos")
    parser.add_argument("--repo", help="Specific repo to scan (owner/repo)")
    parser.add_argument("--all", action="store_true", help="Scan all repos from config/repos.yml")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    config_path = root / "config" / "repos.yml"

    if args.repo:
        repos = [{"repo": args.repo}]
    elif args.all and config_path.exists():
        with open(config_path) as f:
            repos = yaml.safe_load(f).get("repos", [])
    else:
        print("Usage: collate.py --repo owner/repo OR --all")
        sys.exit(1)

    registry_path = root / "registry" / "patterns.json"
    with open(registry_path) as f:
        registry = json.load(f)

    for repo_config in repos:
        repo = repo_config["repo"]
        print(f"Scanning {repo}...")
        try:
            patterns = collate_repo(f"https://github.com/{repo}.git", registry)
            print(f"  Found {len(patterns)} patterns")
            for p in patterns:
                print(f"  - {p['name']} ({p['type']})")
        except Exception as e:
            print(f"  Error: {e}")
