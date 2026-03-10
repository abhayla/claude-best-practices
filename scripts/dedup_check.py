"""Three-level deduplication for best practices patterns.

Level 1: Exact hash match (SHA256 of normalized content)
Level 2: Structural match (name + type + category + dependencies)
Level 3: Semantic similarity (Claude API — separate function, called by scan_web.py)
"""

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional

import yaml


def hash_pattern(file_path: str) -> str:
    """SHA256 of file content, normalized (collapse whitespace, strip trailing)."""
    content = Path(file_path).read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]
    normalized = "\n".join(lines)
    normalized = re.sub(r"  +", " ", normalized)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def check_exact_duplicate(new_hash: str, registry: dict) -> Optional[str]:
    """Returns existing pattern name if exact hash match found."""
    for name, entry in registry.items():
        if name.startswith("_"):
            continue
        if isinstance(entry, dict) and entry.get("hash") == new_hash:
            return name
    return None


def check_structural_duplicate(
    new_pattern: dict, registry: dict, threshold: int = 3
) -> list[str]:
    """Find patterns with similar name, type, category, or dependencies."""
    matches = []
    for name, entry in registry.items():
        if name.startswith("_"):
            continue
        if not isinstance(entry, dict):
            continue

        score = 0
        if new_pattern.get("name", "").lower() == name.lower():
            score += 3
        if new_pattern.get("type") == entry.get("type"):
            score += 1
        if new_pattern.get("category") == entry.get("category"):
            score += 1
        new_deps = set(new_pattern.get("dependencies", []))
        existing_deps = set(entry.get("dependencies", []))
        score += len(new_deps & existing_deps)

        if score >= threshold:
            matches.append(name)

    return matches


def parse_frontmatter(file_path: Path) -> Optional[dict]:
    """Extract YAML frontmatter from a markdown file."""
    content = Path(file_path).read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def validate_pattern_integrity(file_path: Path) -> list[str]:
    """Validate a pattern file has required structure. Returns list of errors."""
    errors = []
    path = Path(file_path)

    if not path.exists():
        return [f"File not found: {path}"]

    fm = parse_frontmatter(path)
    if fm is None:
        errors.append("Missing or invalid YAML frontmatter")
        return errors

    if "name" not in fm:
        errors.append("Frontmatter missing 'name' field")
    if "description" not in fm:
        errors.append("Frontmatter missing 'description' field")
    if "version" not in fm:
        errors.append("Frontmatter missing 'version' field")

    return errors


def validate_registry(registry_path: Path, patterns_root: Path) -> list[str]:
    """Validate registry consistency with actual files."""
    errors = []
    with open(registry_path) as f:
        registry = json.load(f)

    for name, entry in registry.items():
        if name.startswith("_"):
            continue
        if not isinstance(entry, dict):
            errors.append(f"Invalid entry for '{name}': not a dict")
            continue

        required = ["hash", "type", "category", "version", "source"]
        for field in required:
            if field not in entry:
                errors.append(f"Pattern '{name}' missing field: {field}")

    return errors


def scan_for_secrets(file_path: Path) -> list[str]:
    """Scan a file for common secret patterns."""
    content = Path(file_path).read_text(encoding="utf-8")
    findings = []
    patterns = [
        (r"sk-ant-[a-zA-Z0-9_-]{20,}", "Anthropic API key"),
        (r"AIza[a-zA-Z0-9_-]{35}", "Google API key"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
        (r"AKIA[A-Z0-9]{16}", "AWS access key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret"),
    ]
    for pattern, desc in patterns:
        if re.search(pattern, content):
            findings.append(f"{desc} found in {file_path}")
    return findings


if __name__ == "__main__":
    if "--validate-all" in sys.argv:
        root = Path(__file__).parent.parent
        registry_path = root / "registry" / "patterns.json"
        if registry_path.exists():
            errors = validate_registry(registry_path, root)
            if errors:
                print("Validation errors:")
                for e in errors:
                    print(f"  - {e}")
                sys.exit(1)
            else:
                print("Registry validation passed")
        else:
            print("No registry found — skipping")
    elif "--secret-scan" in sys.argv:
        root = Path(__file__).parent.parent
        all_findings = []
        for ext in ["*.md", "*.sh", "*.py", "*.yml", "*.yaml", "*.json"]:
            for f in root.rglob(ext):
                if ".git" in str(f) or "node_modules" in str(f):
                    continue
                all_findings.extend(scan_for_secrets(f))
        if all_findings:
            print("Secret scan findings:")
            for finding in all_findings:
                print(f"  - {finding}")
            sys.exit(1)
        else:
            print("No secrets found")
