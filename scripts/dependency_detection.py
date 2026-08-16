import base64
import json
import re
import subprocess
from pathlib import Path
import yaml


STACK_DETECTORS = [
    # Android: build.gradle.kts with android plugin
    ("**/build.gradle.kts", "com.android", "android-compose"),
    ("**/build.gradle", "com.android", "android-compose"),
    # FastAPI: requirements.txt with fastapi
    ("**/requirements.txt", "fastapi", "fastapi-python"),
    ("**/pyproject.toml", "fastapi", "fastapi-python"),
    ("**/Pipfile", "fastapi", "fastapi-python"),
    # Firebase: google-services.json or firebase dependency
    ("**/google-services.json", None, "firebase-auth"),
    ("**/requirements.txt", "firebase", "firebase-auth"),
    ("**/build.gradle.kts", "firebase", "firebase-auth"),
    # AI/Gemini: google-genai or anthropic SDK
    ("**/requirements.txt", "google-genai", "ai-gemini"),
    ("**/requirements.txt", "anthropic", "ai-gemini"),
    ("**/pyproject.toml", "google-genai", "ai-gemini"),
    # React/Next.js: package.json with next
    ("**/package.json", '"next"', "react-nextjs"),
]


DEP_PATTERN_MAP = {
    # JS/TS
    "tailwindcss": {"tailwind-dev"},
    "@tailwindcss/postcss": {"tailwind-dev"},
    "vitest": {"vitest-dev"},
    "jest": {"jest-dev"},
    "@playwright/test": {"playwright"},
    "prisma": {"prisma-orm", "prisma-conventions"},  # prisma rule
    "@prisma/client": {"prisma-orm", "prisma-conventions"},
    "drizzle-orm": {"drizzle-orm"},
    "next": {"nextjs-dev"},
    "vue": {"vue-dev", "vue-test", "vue"},  # vue rule
    "nuxt": {"nuxt-dev", "vue"},            # Nuxt implies Vue rule
    "pinia": {"vue-dev", "vue"},            # Pinia implies Vue rule
    "vuetify": {"vue", "vue-e2e"},          # Vuetify implies Vue rule + Vuetify/Playwright E2E rule
    "react-native": {"react-native-dev", "react-native-e2e"},
    "expo": {"expo-dev"},
    "hono": {"hono-backend", "hono-conventions"},  # hono rule
    "elysia": {"bun-elysia-test", "bun-elysia"},  # bun-elysia rule
    "socket.io": {"websocket-patterns"},
    "ws": {"websocket-patterns"},
    "redis": {"redis-patterns"},
    "ioredis": {"redis-patterns"},
    "d3": {"d3-viz"},
    "remotion": {"remotion-video"},
    # Python
    "fastapi": {"fastapi-run-backend-tests", "fastapi-deploy", "fastapi-db-migrate",
                 "fastapi-backend", "fastapi-database"},  # fastapi rules
    "pytest": {"pytest-dev"},
    "alembic": {"db-migrate", "db-migrate-verify"},
    "sqlalchemy": {"schema-designer"},
    "psycopg2-binary": {"pg-query"},
    "psycopg2": {"pg-query"},
    "asyncpg": {"pg-query"},
    "firebase-admin": {"firebase"},  # firebase rule
    "anthropic": {"ai-gemini-api"},
    "google-genai": {"ai-gemini-api"},
    "websockets": {"websocket-patterns"},
    # Android/Gradle
    "compose": {"compose-ui", "android"},  # android rule
    # Flutter
    "flutter": {"flutter-dev", "flutter-e2e-test", "flutter"},  # flutter rule
}


_DEP_SUBDIRS = [
    "frontend", "backend", "server", "client", "app", "android", "ios", "web",
]


def _parse_package_json(content: str) -> list[str]:
    """Extract dependency names from package.json."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return []
    deps = []
    for key in ("dependencies", "devDependencies"):
        section = data.get(key, {})
        if isinstance(section, dict):
            deps.extend(section.keys())
    return deps


def _parse_requirements_txt(content: str) -> list[str]:
    """Extract dependency names from requirements.txt."""
    deps = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers and extras
        name = re.split(r"[>=<!~\[;@\s]", line)[0].strip()
        if name:
            deps.append(name.lower())
    return deps


def _parse_pyproject_toml(content: str) -> list[str]:
    """Extract dependency names from pyproject.toml [project].dependencies."""
    deps = []
    # Try tomllib (Python 3.11+) first
    try:
        import tomllib
        data = tomllib.loads(content)
        for dep in data.get("project", {}).get("dependencies", []):
            name = re.split(r"[>=<!~\[;@\s]", dep)[0].strip()
            if name:
                deps.append(name.lower())
        return deps
    except (ImportError, Exception):
        pass
    # Fallback: regex extraction
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "dependencies = [" or stripped.startswith("dependencies = ["):
            in_deps = True
            # Check inline list
            if "]" in stripped:
                # Single line list
                items = re.findall(r'"([^"]+)"', stripped)
                for item in items:
                    name = re.split(r"[>=<!~\[;@\s]", item)[0].strip()
                    if name:
                        deps.append(name.lower())
                in_deps = False
            continue
        if in_deps:
            if stripped.startswith("]"):
                in_deps = False
                continue
            items = re.findall(r'"([^"]+)"', stripped)
            for item in items:
                name = re.split(r"[>=<!~\[;@\s]", item)[0].strip()
                if name:
                    deps.append(name.lower())
    return deps


def _parse_build_gradle(content: str) -> list[str]:
    """Extract dependency names from build.gradle or build.gradle.kts."""
    deps = []
    # Match: implementation("group:artifact:version") or implementation 'group:artifact:version'
    # Also handles implementation("group:artifact:version") with parentheses
    for match in re.finditer(r'(?:implementation|api|compileOnly|testImplementation)\s*\(\s*["\']([^"\']+)["\']', content):
        parts = match.group(1).split(":")
        if len(parts) >= 2:
            deps.append(parts[1].lower())  # artifact name
    return deps


def _parse_pubspec_yaml(content: str) -> list[str]:
    """Extract dependency names from pubspec.yaml."""
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return []
    deps = []
    for key in ("dependencies", "dev_dependencies"):
        section = data.get(key, {}) if isinstance(data, dict) else {}
        if isinstance(section, dict):
            deps.extend(section.keys())
    return deps


def _parse_cargo_toml(content: str) -> list[str]:
    """Extract dependency names from Cargo.toml."""
    deps = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and "dependencies" in stripped.lower():
            in_deps = True
            continue
        if stripped.startswith("[") and "dependencies" not in stripped.lower():
            in_deps = False
            continue
        if in_deps:
            match = re.match(r'^(\S+)\s*=', stripped)
            if match:
                deps.append(match.group(1).lower())
    return deps


def _parse_go_mod(content: str) -> list[str]:
    """Extract dependency names from go.mod."""
    deps = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require:
            parts = stripped.split()
            if parts:
                # Extract last segment of module path as dep name
                mod = parts[0]
                deps.append(mod.split("/")[-1].lower())
        elif stripped.startswith("require "):
            parts = stripped.split()
            if len(parts) >= 2:
                deps.append(parts[1].split("/")[-1].lower())
    return deps


def _parse_gemfile(content: str) -> list[str]:
    """Extract gem names from Gemfile."""
    deps = []
    for match in re.finditer(r"""gem\s+['"]([^'"]+)['"]""", content):
        deps.append(match.group(1).lower())
    return deps


_DEP_FILE_PARSERS = {
    "package.json": _parse_package_json,
    "requirements.txt": _parse_requirements_txt,
    "pyproject.toml": _parse_pyproject_toml,
    "build.gradle.kts": _parse_build_gradle,
    "build.gradle": _parse_build_gradle,
    "pubspec.yaml": _parse_pubspec_yaml,
    "Cargo.toml": _parse_cargo_toml,
    "go.mod": _parse_go_mod,
    "Gemfile": _parse_gemfile,
}


def detect_dependencies_from_dir(project_dir: Path) -> dict[str, list[str]]:
    """Scan project root + 1-level-deep subdirectories for dependency files.

    Returns dependency names grouped by ecosystem (e.g., {"npm": [...], "pip": [...]}).
    """
    ecosystem_map = {
        "package.json": "npm",
        "requirements.txt": "pip",
        "pyproject.toml": "pip",
        "build.gradle.kts": "gradle",
        "build.gradle": "gradle",
        "pubspec.yaml": "pub",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "gem",
    }

    deps: dict[str, list[str]] = {}
    dirs_to_scan = [project_dir]
    for subdir in _DEP_SUBDIRS:
        subpath = project_dir / subdir
        if subpath.is_dir():
            dirs_to_scan.append(subpath)

    for scan_dir in dirs_to_scan:
        for filename, parser in _DEP_FILE_PARSERS.items():
            filepath = scan_dir / filename
            if not filepath.exists():
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            parsed = parser(content)
            ecosystem = ecosystem_map.get(filename, "unknown")
            deps.setdefault(ecosystem, [])
            deps[ecosystem].extend(parsed)

    # Deduplicate within each ecosystem
    for eco in deps:
        deps[eco] = sorted(set(deps[eco]))

    return deps


def detect_dependencies_from_repo(repo: str) -> dict[str, list[str]]:
    """Detect dependencies from a remote GitHub repo via gh API.

    Same logic as detect_dependencies_from_dir but fetches files via GitHub API.
    """
    ecosystem_map = {
        "package.json": "npm",
        "requirements.txt": "pip",
        "pyproject.toml": "pip",
        "build.gradle.kts": "gradle",
        "build.gradle": "gradle",
        "pubspec.yaml": "pub",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "gem",
    }

    deps: dict[str, list[str]] = {}
    # Build list of paths to check: root + subdirs
    paths_to_check = []
    for filename in _DEP_FILE_PARSERS:
        paths_to_check.append(filename)
        for subdir in _DEP_SUBDIRS:
            paths_to_check.append(f"{subdir}/{filename}")

    for file_path in paths_to_check:
        filename = file_path.split("/")[-1]
        parser = _DEP_FILE_PARSERS.get(filename)
        if not parser:
            continue
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{repo}/contents/{file_path}",
                 "--jq", ".content"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                continue
            content = base64.b64decode(result.stdout.strip()).decode("utf-8", errors="ignore")
        except Exception:
            continue
        parsed = parser(content)
        ecosystem = ecosystem_map.get(filename, "unknown")
        deps.setdefault(ecosystem, [])
        deps[ecosystem].extend(parsed)

    # Deduplicate within each ecosystem
    for eco in deps:
        deps[eco] = sorted(set(deps[eco]))

    return deps


def resolve_dep_patterns(deps: dict[str, list[str]]) -> set[str]:
    """Flatten all dependency names across ecosystems and resolve to hub pattern names."""
    all_dep_names = set()
    for dep_list in deps.values():
        all_dep_names.update(dep_list)

    promoted = set()
    for dep_name in all_dep_names:
        patterns = DEP_PATTERN_MAP.get(dep_name, set())
        promoted.update(patterns)
    return promoted
