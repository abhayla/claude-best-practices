"""One-command clean-room plugin-validation pipeline (fable-window item 10).

Automates the manual procedure loop-engineering completed by hand (PR #276 /
`plans/loop-engineering-adoption.md` STEP 5.2): structural checks, `claude plugin
validate`, and a headless clean-room serve test that proves an installed plugin's
skills are visible from the plugin alone, not from a project's own .claude/.

Usage:
    python scripts/validate_plugin_cleanroom.py <plugin-name> [options]

See docs/plugin-validation-pipeline.md for the full contract and what PASS means.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
MARKETPLACE_PATH = PLUGINS_ROOT / ".claude-plugin" / "marketplace.json"

DEFAULT_MODEL = "haiku"
DEFAULT_TIMEOUT_SECONDS = 180


@dataclass
class GateResult:
    ran: bool
    passed: bool
    notes: list[str] = field(default_factory=list)
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"ran": self.ran, "passed": self.passed, "notes": self.notes, "evidence": self.evidence}


def load_marketplace(marketplace_path: Path = MARKETPLACE_PATH) -> dict[str, Any]:
    with open(marketplace_path, encoding="utf-8") as f:
        return json.load(f)


def resolve_plugin_dir(plugin_name: str, plugins_root: Path = PLUGINS_ROOT,
                        marketplace_path: Path = MARKETPLACE_PATH) -> tuple[Path | None, list[str]]:
    """Resolve a plugin's directory via its marketplace.json registration.

    Returns (plugin_dir_or_None, issues). An issue is appended (and plugin_dir is
    None) when the plugin is not registered, or its `source` does not resolve to
    an existing directory.
    """
    issues: list[str] = []
    try:
        marketplace = load_marketplace(marketplace_path)
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"marketplace.json unreadable at {marketplace_path}: {exc}"]

    entry = next((p for p in marketplace.get("plugins", []) if p.get("name") == plugin_name), None)
    if entry is None:
        return None, [f"'{plugin_name}' is not registered in {marketplace_path}"]

    source = entry.get("source", "")
    if not source:
        return None, [f"marketplace entry for '{plugin_name}' has no 'source' field"]

    plugin_dir = (plugins_root / source).resolve()
    if not plugin_dir.is_dir():
        return None, [f"marketplace source '{source}' for '{plugin_name}' does not resolve to a directory ({plugin_dir})"]

    return plugin_dir, issues


def check_structural_gate(plugin_dir: Path, plugin_name: str | None = None,
                           marketplace_path: Path = MARKETPLACE_PATH) -> list[str]:
    """Pure structural checks against a plugin directory. No CLI calls.

    Returns a list of issue strings; empty list means the gate passed.
    """
    issues: list[str] = []
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"

    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as exc:
        return [f"plugin.json does not parse: {exc}"]

    name = manifest.get("name")
    if not name:
        issues.append("plugin.json missing 'name'")

    if not manifest.get("version"):
        issues.append("plugin.json missing/empty 'version'")

    # Marketplace registration.
    try:
        marketplace = load_marketplace(marketplace_path)
        registered_names = {p.get("name") for p in marketplace.get("plugins", [])}
        check_name = plugin_name or name
        if check_name not in registered_names:
            issues.append(f"'{check_name}' is not registered in {marketplace_path}")
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"could not read {marketplace_path} to verify registration: {exc}")

    # Hooks must NOT be declared in the manifest — they auto-load from hooks/hooks.json.
    # See docs/installing-plugins-in-downstream-projects.md "Authoring gotcha".
    if "hooks" in manifest:
        issues.append(
            "plugin.json declares 'hooks' — this double-loads hooks/hooks.json and fails the "
            "whole plugin at session start (do not declare hooks in the manifest; they auto-load)"
        )

    # commands: <dir> must exist if declared.
    commands_field = manifest.get("commands")
    if commands_field:
        commands_dir = (plugin_dir / commands_field).resolve()
        if not commands_dir.is_dir():
            issues.append(f"manifest 'commands' points to a missing directory: {commands_field}")

    # skills/*/SKILL.md must exist for every skill subdirectory.
    skills_dir = plugin_dir / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                issues.append(f"skill directory missing SKILL.md: {skill_dir.relative_to(plugin_dir)}")

    # agents/*.md must exist (non-empty files) for every declared agent.
    agents_dir = plugin_dir / "agents"
    if agents_dir.is_dir():
        agent_files = list(agents_dir.glob("*.md"))
        if not agent_files:
            issues.append("agents/ directory exists but contains no *.md agent files")

    # hooks/hooks.json: every referenced command file must exist relative to the plugin root.
    hooks_json = plugin_dir / "hooks" / "hooks.json"
    if hooks_json.is_file():
        try:
            with open(hooks_json, encoding="utf-8") as f:
                hooks_config = json.load(f)
        except json.JSONDecodeError as exc:
            issues.append(f"hooks/hooks.json does not parse: {exc}")
        else:
            for event, matchers in hooks_config.get("hooks", {}).items():
                for matcher in matchers:
                    for hook in matcher.get("hooks", []):
                        command = hook.get("command", "")
                        rel = command.replace("${CLAUDE_PLUGIN_ROOT}", "").lstrip("/\\")
                        if rel and not (plugin_dir / rel).is_file():
                            issues.append(f"hooks.json ({event}) references missing file: {rel}")

    return issues


def run_cli_validate(plugin_dir: Path, strict: bool = False) -> GateResult:
    """Run `claude plugin validate <path>`."""
    cmd = ["claude", "plugin", "validate", str(plugin_dir)]
    if strict:
        cmd.append("--strict")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return GateResult(ran=False, passed=True, notes=["'claude' CLI not found on PATH — skipped with note"])
    except subprocess.TimeoutExpired:
        return GateResult(ran=True, passed=False, notes=["'claude plugin validate' timed out after 60s"])

    output = (proc.stdout or "") + (proc.stderr or "")
    passed = proc.returncode == 0
    notes = [] if passed else [f"exit code {proc.returncode}"]
    return GateResult(ran=True, passed=passed, notes=notes, evidence=output.strip())


def _extract_result_text(stdout: str) -> str:
    """Best-effort extraction of the final result text from stream-json output
    (one JSON object per line; the terminal line has type=="result")."""
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("type") == "result":
            return str(data.get("result", ""))
    return stdout


def _find_init_event(stdout: str) -> dict[str, Any] | None:
    """Scan stream-json output for the first `{"type":"system","subtype":"init"}` line.

    Claude Code reports its resolved session state (loaded plugins, skills,
    slash_commands) in this event BEFORE any model turn runs — so it is a
    deterministic signal of what got served, independent of whether the model's
    generated text happens to comply with the probe's formatting request.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if data.get("type") == "system" and data.get("subtype") == "init":
            return data
    return None


def run_cleanroom_probe(plugin_name: str, plugin_dir: Path, model: str = DEFAULT_MODEL,
                         timeout: int = DEFAULT_TIMEOUT_SECONDS, keep_tmp: bool = False) -> GateResult:
    """Serve the plugin alone (no repo .claude/) in a throwaway project and confirm
    its skills are served from that plugin.

    PASS signal is the `system/init` event's `plugins` list (deterministic — reported by
    Claude Code itself at session start, before any model generation) rather than
    hoping the model's free-text reply happens to comply with a formatting request.
    Some plugins (e.g. prompt-auto-enhance) ship a UserPromptSubmit hook that
    deliberately overrides normal turn behavior, which makes a text-compliance probe
    unreliable — the init event sidesteps that entirely.

    Safety: the tmp project is created OUTSIDE this repo (system temp dir), the probe
    instructs no file edits, disables known plugin side-effecting hooks via env
    off-switches, is capped by a hard subprocess timeout, and cwd is never the hub repo.

    Known limitation (documented in docs/plugin-validation-pipeline.md): this does NOT
    isolate from the operator machine's global ~/.claude/ config — a plugin already
    installed globally on the runner will also appear in `plugins` with a
    `<name>@<marketplace>` source alongside our `<name>@inline` entry. The pass check
    below only requires the `@inline` entry (our --plugin-dir load) to be present at
    the expected path, so a pre-existing global install does not affect the verdict.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="plugin-cleanroom-"))
    notes: list[str] = []
    try:
        (tmp_dir / "README.md").write_text(
            f"Throwaway clean-room project for validating plugin '{plugin_name}'.\n", encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=tmp_dir, capture_output=True, text=True, timeout=30)

        probe_prompt = (
            "SYSTEM DIAGNOSTIC (not a real user task): you are being probed for plugin-serving "
            "visibility only. Without editing or creating any files and without invoking any "
            f"tools, briefly state which skills/commands from the plugin '{plugin_name}' you can "
            "see, then stop."
        )

        env = {**os.environ, "AUTO_PR_DISABLE": "1", "AUTO_MERGE": "0"}
        cmd = [
            "claude", "-p", probe_prompt,
            "--plugin-dir", str(plugin_dir),
            "--model", model,
            "--permission-mode", "bypassPermissions",
            "--output-format", "stream-json",
            "--verbose",
        ]
        try:
            proc = subprocess.run(cmd, cwd=tmp_dir, env=env, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError:
            return GateResult(ran=False, passed=True, notes=["'claude' CLI not found on PATH — skipped with note"])
        except subprocess.TimeoutExpired:
            return GateResult(ran=True, passed=False, notes=[f"headless probe timed out after {timeout}s"])

        stdout = proc.stdout or ""
        init_event = _find_init_event(stdout)

        if init_event is None:
            notes.append("no system/init event found in stream-json output — could not verify serving")
            evidence = ((stdout + (proc.stderr or "")).strip())[-4000:]
            return GateResult(ran=True, passed=False, notes=notes, evidence=evidence)

        expected_dir = plugin_dir.resolve()
        loaded_plugins = init_event.get("plugins", [])
        matched = [
            p for p in loaded_plugins
            if p.get("name") == plugin_name and Path(p.get("path", "")).resolve() == expected_dir
        ]

        if not matched:
            notes.append(
                f"'{plugin_name}' did not appear in the init event's plugins list at the expected "
                f"path ({expected_dir}); loaded plugins: "
                f"{[p.get('name') for p in loaded_plugins]}"
            )
            evidence = json.dumps(init_event, indent=2)[:4000]
            return GateResult(ran=True, passed=False, notes=notes, evidence=evidence)

        notes.append(f"plugin served via --plugin-dir, source={matched[0].get('source')}")

        prefix = f"{plugin_name}:"
        plugin_skills = sorted(s for s in init_event.get("skills", []) if s.startswith(prefix))
        plugin_slash_commands = sorted(c for c in init_event.get("slash_commands", []) if c.startswith(prefix))
        if plugin_skills:
            notes.append(f"skills visible from plugin: {', '.join(plugin_skills)}")
        if plugin_slash_commands:
            notes.append(f"slash commands visible from plugin: {', '.join(plugin_slash_commands)}")

        result_text = _extract_result_text(stdout)
        evidence = f"init.plugins match: {json.dumps(matched[0])}\n\nfinal turn text:\n{result_text}".strip()[-4000:]
        return GateResult(ran=True, passed=True, notes=notes, evidence=evidence)
    finally:
        if not keep_tmp:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        else:
            notes.append(f"tmp project kept at: {tmp_dir}")


def validate_plugin(plugin_name: str, skip_serve: bool = False, strict_cli: bool = False,
                     model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT_SECONDS,
                     keep_tmp: bool = False, plugins_root: Path = PLUGINS_ROOT,
                     marketplace_path: Path = MARKETPLACE_PATH) -> dict[str, Any]:
    plugin_dir, resolve_issues = resolve_plugin_dir(plugin_name, plugins_root, marketplace_path)

    if plugin_dir is None:
        structural = GateResult(ran=True, passed=False, notes=resolve_issues)
        return {
            "plugin": plugin_name,
            "structural": structural.to_dict(),
            "cli_validate": GateResult(ran=False, passed=True, notes=["skipped: plugin could not be resolved"]).to_dict(),
            "cleanroom_serve": GateResult(ran=False, passed=True, notes=["skipped: plugin could not be resolved"]).to_dict(),
            "overall_pass": False,
        }

    structural_issues = check_structural_gate(plugin_dir, plugin_name, marketplace_path)
    structural = GateResult(ran=True, passed=not structural_issues, notes=structural_issues)

    cli_result = run_cli_validate(plugin_dir, strict=strict_cli)

    if skip_serve:
        serve_result = GateResult(ran=False, passed=True, notes=["skipped via --skip-serve"])
    else:
        serve_result = run_cleanroom_probe(plugin_name, plugin_dir, model=model, timeout=timeout, keep_tmp=keep_tmp)

    overall_pass = structural.passed and cli_result.passed and serve_result.passed

    return {
        "plugin": plugin_name,
        "plugin_dir": str(plugin_dir),
        "structural": structural.to_dict(),
        "cli_validate": cli_result.to_dict(),
        "cleanroom_serve": serve_result.to_dict(),
        "overall_pass": overall_pass,
    }


def print_human_summary(verdict: dict[str, Any]) -> None:
    plugin = verdict["plugin"]
    overall = "PASS" if verdict["overall_pass"] else "FAIL"
    print(f"\n=== {plugin}: {overall} ===")
    for gate_key, label in (("structural", "Structural gate"), ("cli_validate", "claude plugin validate"),
                             ("cleanroom_serve", "Clean-room serve test")):
        gate = verdict[gate_key]
        status = "SKIP" if not gate["ran"] else ("PASS" if gate["passed"] else "FAIL")
        print(f"  [{status}] {label}")
        for note in gate["notes"]:
            print(f"          - {note}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin_name", help="Plugin name as registered in plugins/.claude-plugin/marketplace.json")
    parser.add_argument("--skip-serve", action="store_true", help="Skip the headless clean-room serve test (structural + CLI validate only)")
    parser.add_argument("--strict-cli", action="store_true", help="Pass --strict to 'claude plugin validate'")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model for the headless probe (default: {DEFAULT_MODEL})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Hard timeout in seconds for the headless probe")
    parser.add_argument("--keep-tmp", action="store_true", help="Keep the throwaway clean-room project dir for inspection")
    parser.add_argument("--json", action="store_true", help="Print only the machine-readable verdict JSON")
    parser.add_argument("--plugins-root", type=Path, default=PLUGINS_ROOT, help="Override plugins/ root (mainly for tests)")
    parser.add_argument("--marketplace-path", type=Path, default=MARKETPLACE_PATH, help="Override marketplace.json path (mainly for tests)")
    args = parser.parse_args(argv)

    verdict = validate_plugin(
        args.plugin_name,
        skip_serve=args.skip_serve,
        strict_cli=args.strict_cli,
        model=args.model,
        timeout=args.timeout,
        keep_tmp=args.keep_tmp,
        plugins_root=args.plugins_root,
        marketplace_path=args.marketplace_path,
    )

    if args.json:
        print(json.dumps(verdict, indent=2))
    else:
        print_human_summary(verdict)
        print(json.dumps(verdict))

    return 0 if verdict["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
