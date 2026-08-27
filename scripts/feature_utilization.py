"""Feature utilization meter — which Claude Code features are actually USED, and which are not.

The owner's question is "do I under-use Claude Code, and which parts?". Today the only
answer is a feeling: cost_ledger.py says how much was spent and measure_outcomes.py says
whether the work turned out well, but nothing says which of the platform's capabilities —
skills, agents, plan mode, worktrees, cron, MCP servers, background monitors — were ever
reached for. This module answers it from data that already exists on disk: Claude Code's own
per-session transcript JSONLs (usage) cross-referenced against the skills/agents/plugins
installed on this machine (availability). Used ∩ available = utilization; available − used =
the honest "never touched in N days" list.

Design rules (same spirit as measure_outcomes.py):

  1. REPORT, never judge. No thresholds, no pass/fail, no advice — counts and lists only.
     Under-use is a decision for the owner to make from numbers, not a verdict this script
     hands down.
  2. READ-ONLY and side-effect free. Nothing is written, no network, no ledger appended.
  3. "Not observable" is said out loud, never faked. Hook usage does not appear in
     transcripts at all, so hooks are reported as WIRED (from settings.json) and explicitly
     labelled not-measurable. A missing or unreadable directory becomes a NOTE in the
     header, never a silent zero. A skill name that could credit more than one installed
     plugin is listed as ambiguous rather than credited to a guess.
  4. Three session buckets, never blended: the owner's hands-on sessions, the subagents
     those sessions dispatched, and get-work-done fleet workers. Counting a fleet worker's
     tool calls as the owner's usage would flatter every number in the report.

Transcript layout (per-project, under `--projects-dir`, default `~/.claude/projects/`, the
same tree cost_ledger.py streams):
    <project-slug>/*.jsonl                            — top-level session transcripts
    <project-slug>/<session>/subagents/agent-*.jsonl  — subagent transcripts (they carry the
                                                        PARENT session's sessionId)
Assistant entries carry `message.model` and `message.content` blocks; a block with
`type == "tool_use"` carries the tool `name` and its `input` (Agent -> subagent_type/model,
Skill -> skill). A slash command appears either as a USER entry whose text holds
`<command-name>/name</command-name>` or, for the CLI's own commands, as a
`system`/`local_command` entry. Malformed lines are counted and skipped, never fatal.

CLI:
    python scripts/feature_utilization.py [--days 30] [--repo PATH ...] [--json]
        [--projects-dir PATH]
"""

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

# The platform primitives this meter can actually OBSERVE in a transcript. This is a subset
# of the full capability list — see the header note printed by render_report().
PLATFORM_PRIMITIVES = {
    "Agent": "subagents — dispatch work to an isolated-context worker",
    "Workflow": "multi-agent orchestration graphs",
    # Plan mode is a PERMISSION MODE, not a tool: entering it is a keystroke that leaves no
    # tool call, while presenting the finished plan always calls ExitPlanMode. ExitPlanMode
    # is therefore the observable plan-mode signal; EnterPlanMode is kept as its own row so
    # the gap between the two is visible rather than hidden.
    "ExitPlanMode": "plan mode — a plan was presented for approval",
    "EnterPlanMode": "plan mode entered via the tool (rare — usually a keystroke)",
    "EnterWorktree": "git worktree isolation for parallel work",
    "CronCreate": "scheduled tasks (cron)",
    "ScheduleWakeup": "recurring self-paced runs (/loop)",
    "Monitor": "background watch on a long-running command",
    "Artifact": "published pages (artifacts)",
    "WebSearch": "live web search",
    "WebFetch": "fetch a URL's content",
    "SendMessage": "cross-agent messaging",
    "ToolSearch": "deferred tool schemas loaded on demand",
    "Skill": "invoking a skill from the model side",
    "mcp": "any MCP server tool (counted per server below)",
}

PRIMITIVE_LABELS = {"ExitPlanMode": "plan mode (ExitPlanMode)"}

CAPABILITY_CATALOGUE = "docs/claude-references/capability-catalogue-2026-08-27.md"

# Session buckets: a transcript slug matching any of these is a get-work-done background
# worker, a checker worktree, or a temp clone — machine work, not the owner's hands-on usage.
FLEET_SLUG_MARKERS = (
    "GetWorkDone-workspaces",
    "-worktrees-",
    "-wt-check",
    "-wt-",
    "AppData-Local-Temp",
)
BUCKET_OWNER = "owner"
BUCKET_SUBAGENT = "owner-subagent"
BUCKET_FLEET = "fleet-workers"
BUCKETS = (BUCKET_OWNER, BUCKET_SUBAGENT, BUCKET_FLEET)
OWNER_SIDE = (BUCKET_OWNER, BUCKET_SUBAGENT)

DRIVE_PREFIX = re.compile(r"^[A-Za-z]--")
COMMAND_NAME = re.compile(r"<command-name>/?([^<>\s]+)</command-name>")
MCP_TOOL = re.compile(r"^mcp__([^_]+(?:_[^_]+)*?)__")

# Marketplace cache dirs Claude Code creates while resolving git sources — not installed
# plugins, and enumerating them would invent dozens of "available but unused" skills.
TEMP_MARKETPLACE_PREFIXES = ("temp_git_", "temp_subdir_")


# --------------------------------------------------------------------------------------
# Project / session classification
# --------------------------------------------------------------------------------------

def default_projects_dir() -> Path:
    """Same transcript root cost_ledger.py reads — one source of truth for where they live."""
    return Path.home() / ".claude" / "projects"


def is_fleet_slug(slug: str) -> bool:
    return any(marker in slug for marker in FLEET_SLUG_MARKERS)


def project_bucket(slug: str) -> str:
    """Map a transcript project-slug to its reporting project name: one shared
    `fleet-workers` name for machine sessions, otherwise the drive-stripped slug."""
    if is_fleet_slug(slug):
        return BUCKET_FLEET
    return DRIVE_PREFIX.sub("", slug)


def entry_bucket(slug: str, is_subagent: bool) -> str:
    if is_fleet_slug(slug):
        return BUCKET_FLEET
    return BUCKET_SUBAGENT if is_subagent else BUCKET_OWNER


def is_subagent_path(path: Path) -> bool:
    return "subagents" in path.parts or path.name.startswith("agent-")


# --------------------------------------------------------------------------------------
# Transcript parsing (pure functions — fed fixture lines by the tests)
# --------------------------------------------------------------------------------------

def _entry_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                parts.append(block["text"])
        return "\n".join(parts)
    return ""


def parse_entry(entry: dict) -> dict | None:
    """Turn one transcript entry into the facts this meter needs, or None if it holds none.

    Returns `{"timestamp", "session_id", "tools": [...], "model", "slash": [...]}` where each
    tool is `{"name", "subagent_type", "agent_model", "skill", "mcp_server"}`. Pure: no I/O,
    no counters — the aggregator decides what to do with the facts.
    """
    if not isinstance(entry, dict):
        return None
    etype = entry.get("type")
    facts: dict = {
        "timestamp": entry.get("timestamp"),
        "session_id": entry.get("sessionId"),
        "tools": [],
        "model": None,
        "slash": [],
    }

    message = entry.get("message")
    message = message if isinstance(message, dict) else {}

    if etype == "assistant":
        model = message.get("model")
        if isinstance(model, str):
            facts["model"] = model
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                if not isinstance(name, str):
                    continue
                tool_input = block.get("input")
                tool_input = tool_input if isinstance(tool_input, dict) else {}
                mcp_match = MCP_TOOL.match(name)
                facts["tools"].append(
                    {
                        "name": name,
                        "subagent_type": tool_input.get("subagent_type"),
                        "agent_model": tool_input.get("model"),
                        "skill": tool_input.get("skill"),
                        "mcp_server": mcp_match.group(1) if mcp_match else None,
                    }
                )
    elif etype == "user":
        # The slash marker entry. The body entry that follows it carries no <command-name>,
        # so matching on the tag counts each invocation exactly once.
        facts["slash"] = COMMAND_NAME.findall(_entry_text(message))
    elif etype == "system" and entry.get("subtype") == "local_command":
        # The shape newer CLI versions use for the same thing (one entry, not two).
        content = entry.get("content")
        if isinstance(content, str):
            facts["slash"] = COMMAND_NAME.findall(content)

    if not facts["tools"] and not facts["model"] and not facts["slash"]:
        return None
    return facts


def decode_line(line: str):
    """`(entry, decoded_ok)` for one raw JSONL line.

    `decoded_ok` is False ONLY for a real JSON decode failure — a blank line or a
    perfectly-valid line this meter has no use for is not corruption and must never inflate
    the malformed-line count.
    """
    line = line.strip()
    if not line:
        return None, True
    try:
        return json.loads(line), True
    except (json.JSONDecodeError, ValueError):
        return None, False


def parse_line(line: str) -> dict | None:
    entry, ok = decode_line(line)
    if not ok or entry is None:
        return None
    return parse_entry(entry)


def _parse_timestamp(timestamp) -> datetime | None:
    if not isinstance(timestamp, str):
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _mtime_dt(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def iter_transcript_files(projects_dir: Path, min_mtime: float | None = None, notes: list | None = None):
    """Yield `(slug, path, is_subagent)` for every transcript under `projects_dir`.

    `min_mtime` skips whole files older than the window: transcripts are append-only, so a
    file last written before the window opened cannot hold an entry inside it. This is what
    keeps a 30-day scan of a multi-GB tree cheap.

    Every directory this cannot read appends a NOTE to `notes` — a partial listing that
    reports a confident zero is the failure mode this meter exists to avoid.
    """
    notes = notes if notes is not None else []
    projects_dir = Path(projects_dir)
    if not projects_dir.is_dir():
        notes.append(f"unverified — transcripts dir not found: {projects_dir}")
        return
    try:
        project_dirs = sorted(p for p in projects_dir.iterdir() if p.is_dir())
    except OSError as exc:
        notes.append(f"unverified — could not list {projects_dir}: {exc}")
        return
    for project_dir in project_dirs:
        try:
            files = sorted(project_dir.rglob("*.jsonl"))
        except OSError as exc:
            notes.append(f"unverified — could not list transcripts in {project_dir.name}: {exc}")
            continue
        for path in files:
            try:
                if min_mtime is not None and path.stat().st_mtime < min_mtime:
                    continue
            except OSError as exc:
                notes.append(f"unverified — could not stat {path.name}: {exc}")
                continue
            yield project_dir.name, path, is_subagent_path(path)


def scan_usage(projects_dir: Path, days: int, now: datetime | None = None) -> dict:
    """Stream every transcript in the window and aggregate what was USED, per bucket.

    Window filtering is per-entry on the entry timestamp; an entry with no usable timestamp
    falls back to the file's mtime (honest second-best, counted in `stats`).
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    # 1-day margin: filesystem mtime and entry timestamps can disagree by clock skew, and
    # dropping a file wholesale is unrecoverable, whereas reading one extra file is cheap.
    min_mtime = (cutoff - timedelta(days=1)).timestamp()

    tool_calls = {bucket: Counter() for bucket in BUCKETS}
    tool_sessions = {bucket: defaultdict(set) for bucket in BUCKETS}
    mcp_calls = {bucket: Counter() for bucket in BUCKETS}
    models = {bucket: Counter() for bucket in BUCKETS}
    sessions = {bucket: set() for bucket in BUCKETS}
    slash_calls: Counter = Counter()
    slash_owner: Counter = Counter()
    skill_tool: Counter = Counter()
    skill_tool_owner: Counter = Counter()
    agents: Counter = Counter()  # (subagent_type, model, bucket) -> calls
    projects: dict[str, set] = defaultdict(set)

    notes: list[str] = []
    stats = {
        "files_scanned": 0,
        "subagent_files_scanned": 0,
        "files_skipped": 0,
        "lines_malformed": 0,
        "entries_timestamp_fallback": 0,
    }

    for slug, path, is_subagent in iter_transcript_files(projects_dir, min_mtime=min_mtime, notes=notes):
        bucket = entry_bucket(slug, is_subagent)
        project_name = project_bucket(slug)
        try:
            file_mtime = _mtime_dt(path)
            fh = open(path, encoding="utf-8", errors="replace")
        except OSError as exc:
            stats["files_skipped"] += 1
            notes.append(f"unverified — could not open {path.name}: {exc}")
            continue
        stats["files_scanned"] += 1
        if is_subagent:
            stats["subagent_files_scanned"] += 1
        with fh:
            for line in fh:
                # Cheap prefilter — only these three substrings can produce a fact. Skipping
                # json.loads on the rest is what makes a multi-GB tree scan in seconds.
                if (
                    '"tool_use"' not in line
                    and '"model"' not in line
                    and "<command-name>" not in line
                ):
                    continue
                entry, decoded_ok = decode_line(line)
                if not decoded_ok:
                    stats["lines_malformed"] += 1
                    continue
                if entry is None:
                    continue
                facts = parse_entry(entry)
                if facts is None:
                    continue

                entry_dt = _parse_timestamp(facts["timestamp"])
                if entry_dt is None:
                    entry_dt = file_mtime
                    stats["entries_timestamp_fallback"] += 1
                if entry_dt is None or entry_dt < cutoff:
                    continue

                # Subagent transcripts carry the PARENT session's id, so a subagent's work
                # folds into its parent session rather than inventing a new one.
                session_id = facts["session_id"] or f"{slug}:{path.stem}"
                sessions[bucket].add(session_id)
                if bucket != BUCKET_FLEET:
                    projects[project_name].add(session_id)

                if facts["model"]:
                    models[bucket][facts["model"]] += 1

                # A slash command is typed by a human into a top-level session; a subagent
                # transcript cannot contain one.
                if facts["slash"] and not is_subagent:
                    for name in facts["slash"]:
                        slash_calls[name] += 1
                        if bucket != BUCKET_FLEET:
                            slash_owner[name] += 1

                for tool in facts["tools"]:
                    name = tool["name"]
                    key = "mcp" if tool["mcp_server"] else name
                    tool_calls[bucket][key] += 1
                    tool_sessions[bucket][key].add(session_id)

                    if tool["mcp_server"]:
                        mcp_calls[bucket][tool["mcp_server"]] += 1
                    if name == "Agent" and tool["subagent_type"]:
                        agents[(tool["subagent_type"], tool["agent_model"] or "(inherit)", bucket)] += 1
                    if name == "Skill" and isinstance(tool["skill"], str):
                        skill_tool[tool["skill"]] += 1
                        if bucket != BUCKET_FLEET:
                            skill_tool_owner[tool["skill"]] += 1

    return {
        "cutoff": cutoff,
        "now": now,
        "stats": stats,
        "notes": notes,
        "tool_calls": tool_calls,
        "tool_sessions": {b: {k: len(v) for k, v in tool_sessions[b].items()} for b in BUCKETS},
        "mcp_calls": mcp_calls,
        "models": models,
        "sessions": sessions,
        "slash_calls": slash_calls,
        "slash_owner": slash_owner,
        "skill_tool": skill_tool,
        "skill_tool_owner": skill_tool_owner,
        "agents": agents,
        "projects": {name: len(ids) for name, ids in projects.items()},
        "slug_buckets": {},  # filled by the caller-facing wrapper below
    }


# --------------------------------------------------------------------------------------
# Availability inventory (built from disk — never a hardcoded list of skills/agents)
# --------------------------------------------------------------------------------------

def _names_in(root: Path, kind: str, notes: list | None = None) -> list[str]:
    """Skill names (`<root>/skills/<name>/SKILL.md`) or agent names (`<root>/agents/<name>.md`)."""
    notes = notes if notes is not None else []
    directory = root / kind
    if not directory.is_dir():
        return []
    names = []
    try:
        children = sorted(directory.iterdir())
    except OSError as exc:
        notes.append(f"unverified — could not list {directory}: {exc}")
        return names
    for child in children:
        try:
            if kind == "skills":
                if child.is_dir() and (child / "SKILL.md").is_file():
                    names.append(child.name)
            elif child.is_file() and child.suffix == ".md":
                names.append(child.stem)
        except OSError as exc:
            notes.append(f"unverified — could not stat {child}: {exc}")
    return names


def _version_key(version: str, mtime: float = 0.0) -> tuple:
    """Sort key for one installed plugin version directory.

    Plugin cache dirs are NOT all semver: alongside `0.2.2` sit git hashes (`614b4ebe2319`)
    and literals like `unknown`. Sorting those as plain strings put a hash ABOVE every real
    version, so the inventory was being read out of a stale hash checkout. Rules:
      * a dotted all-numeric version outranks any non-numeric name (hash / "unknown");
      * among non-numeric names the newest directory on disk wins (mtime) — the only
        ordering signal a hash actually carries;
      * numeric components compare as integers, so 0.10 > 0.9;
      * a prerelease suffix sorts BELOW its release: 1.0.0-beta < 1.0.0.
    """
    main = version.split("+", 1)[0]
    main, _, pre = main.partition("-")
    chunks = [c for c in main.split(".") if c]
    if not chunks or not all(c.isdigit() for c in chunks):
        return (0, (), 1, (), mtime)
    release = tuple(int(c) for c in chunks)
    pre_parts = tuple(
        (1, int(p), "") if p.isdigit() else (0, 0, p) for p in pre.split(".") if p
    )
    return (1, release, 0 if pre_parts else 1, pre_parts, mtime)


def _declared_version(version_dir: Path) -> str | None:
    """The version a plugin declares in its own manifest — authoritative over a directory
    name, which may be a git hash carrying no version information at all."""
    manifest = version_dir / ".claude-plugin" / "plugin.json"
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return None
    version = data.get("version") if isinstance(data, dict) else None
    return version if isinstance(version, str) and version.strip() else None


def plugin_versions(cache_dir: Path, notes: list | None = None) -> dict[tuple[str, str], Path]:
    """Highest installed version dir per `(marketplace, plugin)`.

    Keyed by marketplace AND plugin because the same plugin name legitimately exists under
    two marketplaces (e.g. `code-review` ships in both `claude-code-plugins` and
    `claude-plugins-official`); collapsing them on name alone silently drops one install.
    """
    notes = notes if notes is not None else []
    cache_dir = Path(cache_dir)
    if not cache_dir.is_dir():
        notes.append(f"unverified — plugin cache not found: {cache_dir}")
        return {}
    best: dict[tuple[str, str], tuple[tuple, Path]] = {}
    try:
        marketplaces = sorted(p for p in cache_dir.iterdir() if p.is_dir())
    except OSError as exc:
        notes.append(f"unverified — could not list plugin cache {cache_dir}: {exc}")
        return {}
    for marketplace in marketplaces:
        if marketplace.name.startswith(TEMP_MARKETPLACE_PREFIXES):
            continue
        try:
            plugins = sorted(p for p in marketplace.iterdir() if p.is_dir())
        except OSError as exc:
            notes.append(f"unverified — could not list marketplace {marketplace.name}: {exc}")
            continue
        for plugin in plugins:
            try:
                versions = [v for v in plugin.iterdir() if v.is_dir()]
            except OSError as exc:
                notes.append(f"unverified — could not list plugin {plugin.name}: {exc}")
                continue
            for version_dir in versions:
                try:
                    mtime = version_dir.stat().st_mtime
                except OSError:
                    mtime = 0.0
                declared = _declared_version(version_dir)
                key = _version_key(declared or version_dir.name, mtime)
                slot = (marketplace.name, plugin.name)
                current = best.get(slot)
                if current is None or key > current[0]:
                    best[slot] = (key, version_dir)
    return {slot: path for slot, (_, path) in best.items()}


def _read_enabled_plugins(path: Path, notes: list, note_if_missing: bool) -> dict[str, bool]:
    """`enabledPlugins` map from one settings.json — `{}` if the file is missing/unreadable.

    `note_if_missing` is False for the optional per-repo overlay files (`settings.json` /
    `settings.local.json` are commonly absent by design — that is not worth flagging), True
    for the primary user settings file where absence is unusual enough to say out loud.
    """
    path = Path(path)
    if not path.is_file():
        if note_if_missing:
            notes.append(f"unverified — settings file not found: {path}")
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        notes.append(f"unverified — could not read {path}: {exc}")
        return {}
    enabled = data.get("enabledPlugins") if isinstance(data, dict) else None
    return dict(enabled) if isinstance(enabled, dict) else {}


def load_enabled_plugins(user_settings_path, repo_paths, notes: list | None = None) -> dict[str, bool]:
    """Merge `enabledPlugins` (`"<plugin>@<marketplace>": true/false`) across scopes: the
    user's `~/.claude/settings.json`, then each repo's `.claude/settings.json`, then that
    repo's `.claude/settings.local.json` — later scopes win key-by-key, matching the order
    Claude Code itself resolves plugin enablement. A key absent from every scope stays
    absent here (the caller treats "no key" as not-enabled, distinct from an explicit
    `false`, but both read as "don't count this plugin as installed").
    """
    notes = notes if notes is not None else []
    merged: dict[str, bool] = {}
    merged.update(_read_enabled_plugins(Path(user_settings_path), notes, note_if_missing=True))
    for repo in repo_paths or []:
        repo_claude = Path(repo) / ".claude"
        merged.update(_read_enabled_plugins(repo_claude / "settings.json", notes, note_if_missing=False))
        merged.update(
            _read_enabled_plugins(repo_claude / "settings.local.json", notes, note_if_missing=False)
        )
    return merged


def build_inventory(repos, home: Path | None = None, user_settings_path=None) -> dict:
    """Enumerate every skill and agent installed on this machine: user-level, per-repo, and
    the highest installed version of each cached plugin (plugin resources are qualified
    `plugin:name` so a plugin skill can never be confused with a local one).

    A plugin sitting in the cache is not necessarily LOADED — Claude Code only loads what
    `enabledPlugins` in settings.json lists (see `load_enabled_plugins`). Only an ENABLED
    plugin's skills/agents feed `skills`/`agents` (and therefore the coverage math below);
    a cached-but-not-enabled plugin is reported separately in `not_enabled_plugins` so it is
    visible without inflating "available but never used".

    Returns `notes` alongside the inventory — a directory that could not be read is said out
    loud, never reported as "nothing installed here".
    """
    home = Path(home) if home else Path.home()
    notes: list[str] = []
    skills: dict[str, str] = {}   # name -> source label
    agents: dict[str, str] = {}

    user_root = home / ".claude"
    if not user_root.is_dir():
        notes.append(f"unverified — user config dir not found: {user_root}")
    for name in _names_in(user_root, "skills", notes):
        skills[name] = "user"
    for name in _names_in(user_root, "agents", notes):
        agents[name] = "user"

    for repo in repos or []:
        repo_root = Path(repo) / ".claude"
        if not repo_root.is_dir():
            notes.append(f"unverified — repo config dir not found: {repo_root}")
            continue
        label = f"repo:{Path(repo).name}"
        for name in _names_in(repo_root, "skills", notes):
            skills.setdefault(name, label)
        for name in _names_in(repo_root, "agents", notes):
            agents.setdefault(name, label)

    plugins = plugin_versions(home / ".claude" / "plugins" / "cache", notes)
    settings_path = Path(user_settings_path) if user_settings_path else user_root / "settings.json"
    enabled_map = load_enabled_plugins(settings_path, repos, notes)

    enabled_plugins: list[str] = []
    not_enabled_plugins: list[dict] = []
    for (marketplace, plugin_name), version_dir in sorted(plugins.items()):
        plugin_label = f"{marketplace}/{plugin_name}"
        plugin_skills = _names_in(version_dir, "skills", notes)
        plugin_agents = _names_in(version_dir, "agents", notes)
        if enabled_map.get(f"{plugin_name}@{marketplace}") is True:
            enabled_plugins.append(plugin_label)
            for name in plugin_skills:
                skills.setdefault(f"{plugin_name}:{name}", f"plugin:{marketplace}/{plugin_name}")
            for name in plugin_agents:
                agents.setdefault(f"{plugin_name}:{name}", f"plugin:{marketplace}/{plugin_name}")
        else:
            not_enabled_plugins.append(
                {"plugin": plugin_label, "skills": len(plugin_skills), "agents": len(plugin_agents)}
            )

    return {
        "skills": skills,
        "agents": agents,
        "plugins": sorted(f"{m}/{p}" for m, p in plugins),
        "enabled_plugins": sorted(enabled_plugins),
        "not_enabled_plugins": sorted(not_enabled_plugins, key=lambda d: d["plugin"]),
        "notes": notes,
    }


def hook_events(paths) -> dict:
    """Which hook EVENTS are wired, per settings file. Usage of a hook never appears in a
    transcript, so this is a wiring inventory only — the report says so rather than pretending
    a wired hook was 'used'."""
    result = {}
    for path in paths:
        path = Path(path)
        if not path.is_file():
            result[str(path)] = {"events": [], "note": "unverified — file not found"}
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError, ValueError):
            result[str(path)] = {"events": [], "note": "unverified — unreadable/invalid JSON"}
            continue
        hooks = data.get("hooks") if isinstance(data, dict) else None
        events = sorted(hooks) if isinstance(hooks, dict) else []
        result[str(path)] = {"events": events, "note": None}
    return result


def configured_mcp_servers(claude_json: Path, repos) -> dict:
    """Best-effort list of configured MCP servers: `~/.claude.json` `mcpServers` plus each
    repo's `.mcp.json`. A missing file is reported as unverified, never as zero servers."""
    servers: set[str] = set()
    notes: list[str] = []

    claude_json = Path(claude_json)
    if claude_json.is_file():
        try:
            with open(claude_json, encoding="utf-8") as f:
                data = json.load(f)
            servers.update((data.get("mcpServers") or {}).keys())
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            notes.append(f"unverified — could not read {claude_json}")
    else:
        notes.append(f"unverified — {claude_json} not found")

    for repo in repos or []:
        mcp_path = Path(repo) / ".mcp.json"
        if not mcp_path.is_file():
            notes.append(f"unverified — {mcp_path} not found")
            continue
        try:
            with open(mcp_path, encoding="utf-8") as f:
                data = json.load(f)
            servers.update((data.get("mcpServers") or {}).keys())
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            notes.append(f"unverified — could not read {mcp_path}")

    return {"servers": sorted(servers), "notes": notes}


# --------------------------------------------------------------------------------------
# Matching used names to installed resources
# --------------------------------------------------------------------------------------

def _bare(name: str) -> str:
    return name.split(":", 1)[1] if ":" in name else name


def resolve_used(used_names, available) -> dict:
    """Decide which INSTALLED resources a set of observed names actually credits.

    Namespaces are load-bearing: `writing-plans` exists as a local skill, in `superpowers`,
    in `loop-engineering` and in `cbp-build-test-workflows`. Crediting all four from one
    bare observation invents usage. Rules:
      * a qualified observation (`superpowers:writing-plans`) credits that exact entry only;
      * a bare observation (a `/slash` or an unqualified `Skill(...)`) credits only an
        unqualified/local entry of the same name;
      * a bare observation with no local entry but one-or-more plugin entries credits
        NOTHING and is reported as an ambiguous credit, with the candidates listed.
    Returns `{"credited": set, "ambiguous": [(name, [candidates])], "unmatched": [names]}`.
    """
    available = set(available)
    local = {name for name in available if ":" not in name}
    by_bare: dict[str, list[str]] = defaultdict(list)
    for name in available:
        if ":" in name:
            by_bare[_bare(name)].append(name)

    credited: set[str] = set()
    ambiguous: list[tuple[str, list[str]]] = []
    unmatched: list[str] = []

    for used in sorted(set(used_names)):
        if ":" in used:
            if used in available:
                credited.add(used)
            else:
                unmatched.append(used)
            continue
        if used in local:
            credited.add(used)
            continue
        candidates = sorted(by_bare.get(used, []))
        if candidates:
            ambiguous.append((used, candidates))
        else:
            unmatched.append(used)

    return {"credited": credited, "ambiguous": ambiguous, "unmatched": unmatched}


# --------------------------------------------------------------------------------------
# Report assembly
# --------------------------------------------------------------------------------------

def build_report(usage: dict, inventory: dict, mcp_config: dict, hooks: dict, days: int) -> dict:
    calls = usage["tool_calls"]
    sess = usage["tool_sessions"]

    primitives = []
    for name, description in PLATFORM_PRIMITIVES.items():
        owner_calls = calls[BUCKET_OWNER].get(name, 0)
        sub_calls = calls[BUCKET_SUBAGENT].get(name, 0)
        fleet_calls = calls[BUCKET_FLEET].get(name, 0)
        primitives.append(
            {
                "feature": name,
                "label": PRIMITIVE_LABELS.get(name, name),
                "description": description,
                "owner_sessions": sess[BUCKET_OWNER].get(name, 0),
                "subagent_sessions": sess[BUCKET_SUBAGENT].get(name, 0),
                "fleet_sessions": sess[BUCKET_FLEET].get(name, 0),
                "owner_calls": owner_calls,
                "subagent_calls": sub_calls,
                "fleet_calls": fleet_calls,
                "total_calls": owner_calls + sub_calls + fleet_calls,
            }
        )
    primitives.sort(key=lambda p: (-p["owner_calls"], -p["subagent_calls"], p["feature"]))
    primitives_unused = [
        p["feature"] for p in primitives if p["owner_calls"] == 0 and p["subagent_calls"] == 0
    ]

    # --- skills: split the slash stream into real skills vs CLI built-ins ---------------
    skill_names = set(inventory["skills"])
    local_skills = {n for n in skill_names if ":" not in n}
    plugin_bare = {_bare(n) for n in skill_names if ":" in n}

    def _is_skill(name: str) -> bool:
        return name in skill_names or name in local_skills or _bare(name) in plugin_bare

    slash_skills = Counter()
    cli_commands = Counter()
    for name, count in usage["slash_calls"].items():
        (slash_skills if _is_skill(name) else cli_commands)[name] += count

    used_skill_names = set(slash_skills) | set(usage["skill_tool"])
    skills_used = []
    for name in sorted(used_skill_names):
        skills_used.append(
            {
                "skill": name,
                "user_slash": slash_skills.get(name, 0),
                "model_skill_tool": usage["skill_tool"].get(name, 0),
                "total": slash_skills.get(name, 0) + usage["skill_tool"].get(name, 0),
                "owner_invocations": usage["slash_owner"].get(name, 0)
                + usage["skill_tool_owner"].get(name, 0),
            }
        )
    skills_used.sort(key=lambda s: (-s["total"], s["skill"]))

    owner_used_skills = {s["skill"] for s in skills_used if s["owner_invocations"] > 0}
    skill_match_all = resolve_used(used_skill_names, skill_names)
    skill_match_owner = resolve_used(owner_used_skills, skill_names)
    skills_never = sorted(skill_names - skill_match_all["credited"])

    # --- agents ------------------------------------------------------------------------
    agent_rows = []
    for (subagent_type, model, bucket), count in usage["agents"].items():
        agent_rows.append(
            {"subagent_type": subagent_type, "model": model, "bucket": bucket, "calls": count}
        )
    agent_rows.sort(key=lambda a: (-a["calls"], a["subagent_type"], a["model"]))
    agent_names = set(inventory["agents"])
    used_agent_types = {row["subagent_type"] for row in agent_rows}
    owner_used_agents = {row["subagent_type"] for row in agent_rows if row["bucket"] in OWNER_SIDE}
    agent_match_all = resolve_used(used_agent_types, agent_names)
    agent_match_owner = resolve_used(owner_used_agents, agent_names)
    agents_never = sorted(agent_names - agent_match_all["credited"])

    # --- mcp ---------------------------------------------------------------------------
    mcp_total = Counter()
    for bucket in BUCKETS:
        mcp_total.update(usage["mcp_calls"][bucket])
    mcp_never = [s for s in mcp_config["servers"] if s not in mcp_total]

    skills_total = len(skill_names)
    agents_total = len(agent_names)
    covered = len(skill_match_owner["credited"]) + len(agent_match_owner["credited"])
    available = skills_total + agents_total
    coverage_pct = (covered / available * 100) if available else None

    owner_session_ids = usage["sessions"][BUCKET_OWNER] | usage["sessions"][BUCKET_SUBAGENT]

    return {
        "window_days": days,
        "since": usage["cutoff"].isoformat(),
        "generated_at": usage["now"].isoformat(),
        "stats": usage["stats"],
        "notes": list(usage["notes"]) + list(inventory.get("notes", [])),
        "plugins_enabled": sorted(inventory.get("enabled_plugins", [])),
        "plugins_not_enabled": sorted(
            inventory.get("not_enabled_plugins", []), key=lambda d: d["plugin"]
        ),
        "sessions": {
            "owner": len(owner_session_ids),
            "fleet_workers": len(usage["sessions"][BUCKET_FLEET]),
        },
        "projects_by_sessions": dict(
            sorted(usage["projects"].items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "slug_buckets": usage.get("slug_buckets", {}),
        "primitives": primitives,
        "primitives_never_used_by_owner": primitives_unused,
        "skills": {
            "used": skills_used,
            "available_total": skills_total,
            "never_used": skills_never,
            "owner_credited": sorted(skill_match_owner["credited"]),
            "ambiguous_credits": [
                {"observed": name, "candidates": candidates}
                for name, candidates in skill_match_all["ambiguous"]
            ],
            "used_not_installed": skill_match_all["unmatched"],
        },
        "cli_commands": dict(cli_commands.most_common()),
        "agents": {
            "used": agent_rows,
            "available_total": agents_total,
            "never_used": agents_never,
            "owner_credited": sorted(agent_match_owner["credited"]),
            "ambiguous_credits": [
                {"observed": name, "candidates": candidates}
                for name, candidates in agent_match_all["ambiguous"]
            ],
            "used_not_installed": agent_match_all["unmatched"],
        },
        "mcp": {
            "calls_by_server": dict(mcp_total.most_common()),
            "owner_calls": dict(usage["mcp_calls"][BUCKET_OWNER].most_common()),
            "subagent_calls": dict(usage["mcp_calls"][BUCKET_SUBAGENT].most_common()),
            "configured": mcp_config["servers"],
            "never_called": mcp_never,
            "notes": mcp_config["notes"],
        },
        "models": {bucket: dict(usage["models"][bucket].most_common()) for bucket in BUCKETS},
        "hooks": hooks,
        "coverage": {
            "skills_available": skills_total,
            "skills_used_by_owner": len(skill_match_owner["credited"]),
            "agents_available": agents_total,
            "agents_used_by_owner": len(agent_match_owner["credited"]),
            "percent_used_by_owner": coverage_pct,
        },
    }


def render_report(report: dict, scan_seconds: float | None = None) -> str:
    lines: list[str] = []
    add = lines.append

    stats = report["stats"]
    add(f"Claude Code feature utilization — last {report['window_days']} day(s)")
    add(f"  window opens : {report['since']}")
    add(f"  generated    : {report['generated_at']}")
    add(
        f"  transcripts  : {stats['files_scanned']} scanned "
        f"({stats.get('subagent_files_scanned', 0)} subagent), "
        f"{stats['files_skipped']} unreadable, "
        f"{stats['lines_malformed']} malformed line(s) skipped"
    )
    add(
        f"  sessions     : {report['sessions']['owner']} owner hands-on, "
        f"{report['sessions']['fleet_workers']} fleet-worker"
    )
    add(
        f"  plugins      : {len(report['plugins_enabled'])} enabled, "
        f"{len(report['plugins_not_enabled'])} cached-not-enabled"
    )
    add(
        f"  primitives   : transcript-observable subset of {CAPABILITY_CATALOGUE} — a "
        "capability with no tool call of its own cannot be measured here"
    )
    if stats["entries_timestamp_fallback"]:
        add(f"  note         : {stats['entries_timestamp_fallback']} entries dated by file mtime (no timestamp field)")
    if scan_seconds is not None:
        add(f"  scan time    : {scan_seconds:.1f}s")
    for note in report.get("notes", []):
        add(f"  NOTE         : {note}")
    add("")

    not_enabled = report["plugins_not_enabled"]
    add("Cached but NOT enabled (excluded from coverage):")
    if not_enabled:
        for item in not_enabled:
            add(f"    {item['plugin']}: {item['skills']} skill(s), {item['agents']} agent(s)")
    else:
        add("    (none)")
    add("")

    add("1. PLATFORM PRIMITIVES")
    add(
        f"  {'feature':<26} {'owner sess':>10} {'owner calls':>11} {'subagent':>9} "
        f"{'fleet':>7} {'total':>7}"
    )
    for row in report["primitives"]:
        add(
            f"  {row['label']:<26} {row['owner_sessions']:>10} {row['owner_calls']:>11} "
            f"{row['subagent_calls']:>9} {row['fleet_calls']:>7} {row['total_calls']:>7}"
        )
    unused = report["primitives_never_used_by_owner"]
    add("")
    if unused:
        add(f"  Never used by the owner (or their subagents) in {report['window_days']} days ({len(unused)}):")
        for name in unused:
            add(f"    - {PRIMITIVE_LABELS.get(name, name)}  ({PLATFORM_PRIMITIVES[name]})")
    else:
        add("  Every listed primitive was used on the owner side at least once.")
    add("")

    skills = report["skills"]
    add("2. SKILLS")
    add(f"  Used ({len(skills['used'])}):")
    if skills["used"]:
        add(f"    {'skill':<44} {'user /slash':>11} {'model Skill':>12} {'total':>7}")
        for row in skills["used"]:
            add(
                f"    {row['skill']:<44} {row['user_slash']:>11} {row['model_skill_tool']:>12} "
                f"{row['total']:>7}"
            )
    else:
        add("    (none)")
    add("")

    cli = report["cli_commands"]
    add(f"  CLI commands (not skills — no installed skill of that name) ({len(cli)}):")
    if cli:
        add("    " + ", ".join(f"{name} x{count}" for name, count in cli.items()))
        add("    A slash skill living in a repo not passed via --repo would land here too.")
    else:
        add("    (none)")
    add("")

    if skills["ambiguous_credits"]:
        add(f"  Ambiguous credits — bare name matches several installed plugins, so NOT credited ({len(skills['ambiguous_credits'])}):")
        for item in skills["ambiguous_credits"]:
            add(f"    {item['observed']} -> {', '.join(item['candidates'])}")
        add("")

    if skills["used_not_installed"]:
        add(
            f"  Observed but NOT in the installed inventory ({len(skills['used_not_installed'])}) "
            "— built-in Anthropic skills, or skills living in a repo not passed via --repo; "
            "they count as used but cannot count toward coverage:"
        )
        add("    " + ", ".join(skills["used_not_installed"]))
        add("")

    never = skills["never_used"]
    add(f"  Available but never used: {len(never)} of {skills['available_total']} installed")
    for group, names in _group_by_plugin(never):
        add(f"    {group} ({len(names)}): {', '.join(names)}")
    add("")

    agents = report["agents"]
    add("3. AGENTS (subagent_type x model)")
    if agents["used"]:
        add(f"    {'subagent_type':<40} {'model':<16} {'bucket':<16} {'calls':>6}")
        for row in agents["used"]:
            add(
                f"    {row['subagent_type']:<40} {row['model']:<16} {row['bucket']:<16} "
                f"{row['calls']:>6}"
            )
    else:
        add("    (none)")
    add("")
    if agents["ambiguous_credits"]:
        add(f"  Ambiguous credits ({len(agents['ambiguous_credits'])}):")
        for item in agents["ambiguous_credits"]:
            add(f"    {item['observed']} -> {', '.join(item['candidates'])}")
        add("")
    add(f"  Available but never used: {len(agents['never_used'])} of {agents['available_total']} installed")
    for group, names in _group_by_plugin(agents["never_used"]):
        add(f"    {group} ({len(names)}): {', '.join(names)}")
    add("")

    mcp = report["mcp"]
    add("4. MCP SERVERS")
    if mcp["calls_by_server"]:
        for server, count in mcp["calls_by_server"].items():
            owner = mcp["owner_calls"].get(server, 0)
            sub = mcp["subagent_calls"].get(server, 0)
            add(f"    {server:<44} {count:>6} calls ({owner} owner, {sub} subagent)")
    else:
        add("    (no MCP tool calls in window)")
    add(f"  Configured: {', '.join(mcp['configured']) if mcp['configured'] else '(none found)'}")
    add(f"  Configured but never called: {', '.join(mcp['never_called']) if mcp['never_called'] else '(none)'}")
    for note in mcp["notes"]:
        add(f"    {note}")
    add("")

    add("5. MODEL MIX (assistant messages)")
    for bucket in BUCKETS:
        counts = report["models"].get(bucket, {})
        total = sum(counts.values())
        add(f"  {bucket} ({total} messages):")
        if not counts:
            add("    (none)")
        for model, count in counts.items():
            share = (count / total * 100) if total else 0
            add(f"    {model:<30} {count:>7}  {share:5.1f}%")
    add("")

    add("6. HOOKS (wired, not measurable from transcripts)")
    for path, info in report["hooks"].items():
        if info["note"]:
            add(f"    {path}: {info['note']}")
        else:
            add(f"    {path}: {', '.join(info['events']) if info['events'] else '(no hooks wired)'}")
    add("    Hook executions do not appear in transcripts — usage is NOT measured here.")
    add("")

    cov = report["coverage"]
    if cov["percent_used_by_owner"] is None:
        add("Coverage: no skills or agents found on disk — nothing to measure against.")
    else:
        add(
            f"Coverage: the owner used {cov['skills_used_by_owner']}/{cov['skills_available']} installed "
            f"skills and {cov['agents_used_by_owner']}/{cov['agents_available']} installed agents at least "
            f"once in {report['window_days']} days ({cov['percent_used_by_owner']:.1f}% of available)."
        )
    return "\n".join(lines)


def _group_by_plugin(names):
    """Group `plugin:skill` names under their plugin; local names under 'local'."""
    groups: dict[str, list[str]] = defaultdict(list)
    for name in names:
        if ":" in name:
            plugin, bare = name.split(":", 1)
            groups[plugin].append(bare)
        else:
            groups["local"].append(name)
    return sorted(groups.items())


def collect(projects_dir: Path, days: int, repos, home: Path | None = None, now=None) -> dict:
    """One full pass: scan usage, build the inventory, and assemble the report dict."""
    home = Path(home) if home else Path.home()
    usage = scan_usage(projects_dir, days, now=now)
    usage["slug_buckets"] = {
        slug: entry_bucket(slug, False)
        for slug in sorted({p.name for p in Path(projects_dir).iterdir() if p.is_dir()})
    } if Path(projects_dir).is_dir() else {}
    inventory = build_inventory(repos, home=home)
    mcp_config = configured_mcp_servers(home / ".claude.json", repos)
    hooks = hook_events(
        [home / ".claude" / "settings.json"]
        + [Path(repo) / ".claude" / "settings.json" for repo in repos]
    )
    return build_report(usage, inventory, mcp_config, hooks, days)


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Report-only meter of which Claude Code features were used vs available."
    )
    parser.add_argument("--days", type=int, default=30, help="window in days (default 30)")
    parser.add_argument(
        "--repo",
        action="append",
        default=None,
        help="repo whose .claude/ skills+agents count as available (repeatable; default cwd)",
    )
    parser.add_argument("--projects-dir", default=None, help="override the transcripts dir")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    repos = args.repo or [str(Path.cwd())]
    projects_dir = Path(args.projects_dir) if args.projects_dir else default_projects_dir()

    started = time.monotonic()
    report = collect(projects_dir, args.days, repos)
    elapsed = time.monotonic() - started
    report["scan_seconds"] = round(elapsed, 2)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_report(report, scan_seconds=elapsed))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
