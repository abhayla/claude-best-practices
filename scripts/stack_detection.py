import base64
import subprocess
from pathlib import Path
from typing import Optional
import yaml

from scripts.dependency_detection import STACK_DETECTORS


def detect_stacks_from_dir(project_dir: Path) -> list[str]:
    """Auto-detect tech stacks from project config files."""
    detected = set()

    for glob_pattern, content_pattern, stack in STACK_DETECTORS:
        matching_files = list(project_dir.rglob(glob_pattern.replace("**/", "")))
        if not matching_files:
            continue

        if content_pattern is None:
            # File existence is enough (e.g., google-services.json)
            detected.add(stack)
            continue

        for f in matching_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if content_pattern.lower() in content.lower():
                    detected.add(stack)
                    break
            except (OSError, UnicodeDecodeError):
                continue

    return sorted(detected)


def detect_stacks_from_repo(repo: str) -> list[str]:
    """Auto-detect stacks from a remote GitHub repo using gh API."""
    detected = set()

    # Check key files via GitHub API
    checks = [
        ("android/build.gradle.kts", "com.android", "android-compose"),
        ("android/app/build.gradle.kts", "com.android", "android-compose"),
        ("build.gradle.kts", "com.android", "android-compose"),
        ("requirements.txt", "fastapi", "fastapi-python"),
        ("backend/requirements.txt", "fastapi", "fastapi-python"),
        ("android/app/google-services.json", None, "firebase-auth"),
        ("google-services.json", None, "firebase-auth"),
        ("requirements.txt", "firebase", "firebase-auth"),
        ("backend/requirements.txt", "firebase", "firebase-auth"),
        ("requirements.txt", "google-genai", "ai-gemini"),
        ("backend/requirements.txt", "google-genai", "ai-gemini"),
        ("requirements.txt", "anthropic", "ai-gemini"),
        ("backend/requirements.txt", "anthropic", "ai-gemini"),
        ("package.json", '"next"', "react-nextjs"),
    ]

    for file_path, content_pattern, stack in checks:
        if stack in detected:
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue

            if content_pattern is None:
                # File existence is enough
                detected.add(stack)
                continue

            # Content is base64 encoded from GitHub API
            import base64
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="ignore")
            if content_pattern.lower() in content.lower():
                detected.add(stack)
        except Exception:
            continue

    return sorted(detected)


def get_stacks_from_config(repo: str, config_path: Path) -> Optional[list[str]]:
    """Get stacks from repos.yml config if the repo is registered."""
    if not config_path.exists():
        return None
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for entry in data.get("repos", []):
        if entry.get("repo") == repo:
            return entry.get("stacks", [])
    return None
