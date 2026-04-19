"""Extract reusable patterns from project repositories."""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from scripts.dedup_check import hash_pattern, parse_frontmatter


# Patterns matched by sanitize_pattern_text — checked in order. Each replacement
# uses a distinct placeholder so a reader can tell at a glance what got
# scrubbed. Regexes are written conservatively to avoid false positives on
# legitimate pattern content (relative paths in backticks, example IDs).
_SANITIZE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Secret prefixes (checked first so path sanitization doesn't partial-match them)
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"), "<redacted-secret>"),
    (re.compile(r"sk_live_[A-Za-z0-9]{10,}"), "<redacted-secret>"),
    (re.compile(r"sk_test_[A-Za-z0-9]{10,}"), "<redacted-secret>"),
    (re.compile(r"ghp_[A-Za-z0-9]{36,}"), "<redacted-secret>"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{30,}"), "<redacted-secret>"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "<redacted-secret>"),
    # Email addresses
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "<email>"),
    # Windows absolute paths (e.g., C:\Users\alice\project)
    (re.compile(r"\b[A-Za-z]:\\[\w\\.\- ]+"), "<abs-path>"),
    # POSIX absolute paths — only match known user-namespace prefixes to avoid
    # mangling legitimate top-level references (/etc/hosts, /dev/null, etc.)
    (re.compile(r"/(?:home|Users|root|var/users)/[\w.\-]+(?:/[\w.\-]+)*"), "<abs-path>"),
]


def sanitize_pattern_text(text: str) -> str:
    """Scrub sensitive strings from pattern text before the pattern leaves the
    project boundary (hub contribution, PR, aggregation, etc.).

    Targets three classes:
      - Absolute filesystem paths (POSIX user-namespace + Windows)
      - Email addresses
      - Known secret-prefix token shapes (Anthropic, OpenAI-stripe-style,
        GitHub PAT, AWS access keys)

    Relative paths in backticks (e.g., `src/auth/`) are intentionally left
    alone — those are legitimate pattern content. The POSIX path regex is
    scoped to user-namespace prefixes (/home/, /Users/, /root/, /var/users/)
    so we don't mangle /etc/hosts, /dev/null, etc.
    """
    for pattern, replacement in _SANITIZE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


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


def _load_synthesis_config(claude_dir: Path) -> dict:
    """Read .claude/synthesis-config.yml if present. Returns {} if absent."""
    cfg_path = claude_dir / "synthesis-config.yml"
    if not cfg_path.exists():
        return {}
    try:
        return yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}


def _is_pattern_private(pattern: dict, private_list: list[str]) -> bool:
    """True if the pattern is listed in private_patterns (by 'type/name' or
    'rules/name.md' style) or has private: true in its frontmatter."""
    fm = pattern.get("frontmatter") or {}
    if fm.get("private") is True:
        return True
    if not private_list:
        return False
    name = pattern["name"]
    ptype = pattern["type"]
    # Build a set of identifier forms the private_patterns list might use
    candidates = {
        name,
        f"{ptype}s/{name}",          # e.g. skills/internal-ops
        f"{ptype}s/{name}.md",       # e.g. rules/internal-ops.md
        f"{ptype}s/{name}/SKILL.md", # e.g. skills/internal-ops/SKILL.md
    }
    return any(entry in candidates for entry in private_list)


def extract_patterns_from_dir(claude_dir: Path) -> list[dict]:
    """Extract all patterns from a .claude/ directory, respecting the
    project's synthesis-config.yml privacy settings.

    If synthesis-config.yml has `allow_hub_sharing: false` (the default in
    new projects), returns []. Otherwise, filters out patterns listed in
    `private_patterns` and patterns with `private: true` in frontmatter."""
    patterns = []

    if not claude_dir.exists():
        return patterns

    cfg = _load_synthesis_config(claude_dir)
    # The config's default is explicit opt-in. If the key is missing but the
    # file exists, treat it as off. If the whole file is missing, treat it
    # as pre-config (backward compat) and allow sharing.
    if cfg:
        if not cfg.get("allow_hub_sharing", False):
            return []
    private_patterns = (cfg.get("private_patterns") if cfg else None) or []

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

    # Filter out private patterns (listed in config or marked in frontmatter)
    patterns = [p for p in patterns if not _is_pattern_private(p, private_patterns)]

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
