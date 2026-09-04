"""Trap-test + wiring guard for the fire-where-it-pays turn-origin predicate (item 5, Part A).

The shared classifier (.claude/hooks/turn-origin.sh) decides whether a UserPromptSubmit/Stop turn
is HUMAN-typed or MACHINE-origin. The full prompt-auto-enhance ceremony must fire on human prompts
and stay silent on machine turns. This file pins:

  1. The permanent 8-case trap-test (4 machine, 4 human). Bar: 4/4 machine -> machine, and >=3/4
     human -> human, with the "human that OPENS with pasted notification XML" being the sole allowed
     judgment call (it falls to MACHINE — documented in turn-origin.sh).
  2. The hub reminder hook suppresses the full-enhance reminder on a machine turn but still emits
     the governance tail, and renders the full process on a human turn.
  3. Cross-copy + wiring: the classifier ships in hub + core + plugin, and every hook sources it
     with a fail-open stub.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
HUB_LIB = ROOT / ".claude" / "hooks" / "turn-origin.sh"
CORE_LIB = ROOT / "core" / ".claude" / "hooks" / "turn-origin.sh"
PLUGIN_LIB = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "turn-origin.sh"
HUB_REMINDER = ROOT / ".claude" / "hooks" / "prompt-enhance-reminder.sh"
HUB_OVERASK = ROOT / ".claude" / "hooks" / "no-overask-guard.sh"
CORE_OVERASK = ROOT / "core" / ".claude" / "hooks" / "no-overask-guard.sh"
PLUGIN_REMINDER = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "prompt-enhance-reminder.sh"
PLUGIN_GUARD = ROOT / "plugins" / "prompt-auto-enhance" / "hooks" / "enhance-process-guard.sh"

BASH = shutil.which("bash") or "bash"

# ── The permanent trap-test corpus ──
MACHINE_CASES = {
    "task_notification_xml": "<task-notification>Agent finished item 4; 12 files changed.</task-notification>",
    "scheduled_wakeup": "[SCHEDULED WAKEUP] time to check the deploy status and report back",
    "skill_execution": "Base directory for this skill: /repo/.claude/skills/foo\nRun the pipeline now.",
    "system_reminder_only": "<system-reminder>PreToolUse hook: branch not chosen yet this session.</system-reminder>",
    # T-134 (2026-08-15): a headless `claude -p` fleet worker's stdin-piped contract. Every
    # GetWorkDone dispatcher worker prompt carries this WORKER-MERGE GUARD line verbatim
    # (get-work-done SKILL.md STEP 5) regardless of whether the prompt opens with prose or raw
    # YAML frontmatter — mirrors the live T-133 sample (worker ended its JSON result with an
    # "*Enhanced:" banner because this turn was misclassified as human).
    "headless_fleet_worker": (
        "---\nrepo: gorefer\norigin: abc@itsab-PC gorefer\nmodel: sonnet  # mechanical fix\n---\n\n"
        "STANDING MANDATE (verbatim, non-negotiable): You NEVER merge or close ANY pull request — "
        "yours, a foreign one, or anyone else's — and you NEVER push to `main`. Landing "
        "(merge-on-green, closing, deleting a branch) is dispatcher/checker-owned, not yours.\n\n"
        "Fix the stale path in scripts/x.py and open a PR."
    ),
}
HUMAN_CASES = {
    "short_human": "fix the typo in the readme header",
    "long_human": (
        "I want to refactor the auth module so token refresh happens in a background worker "
        "instead of inline, and add tests for the expiry edge cases. Walk me through the plan first."
    ),
    "human_quotes_notification": (
        "The system sent me this: <task-notification>foo fired twice</task-notification> "
        "— why did it fire twice and how do I stop it?"
    ),
    # Judgment call: opens with pasted XML then a real request. Documented to fall to MACHINE.
    "human_leads_with_xml": (
        "<task-notification>build failed</task-notification> can you explain what triggered this "
        "and fix the underlying bug in the pipeline config?"
    ),
}
JUDGMENT_CALL = "human_leads_with_xml"


def _classify(payload: str) -> str:
    res = subprocess.run([BASH, str(HUB_LIB), payload], capture_output=True, text=True)
    return res.stdout.strip()


@pytest.mark.parametrize("name,payload", list(MACHINE_CASES.items()))
def test_machine_cases_all_classify_machine(name, payload):
    assert _classify(payload) == "machine", f"machine case {name!r} misclassified"


def test_human_cases_meet_bar():
    """>=3/4 human -> human, with the documented judgment call the only allowed exception."""
    results = {name: _classify(p) for name, p in HUMAN_CASES.items()}
    human_hits = sum(1 for v in results.values() if v == "human")
    assert human_hits >= 3, f"human bar not met: {results}"
    # every miss MUST be the sanctioned judgment call, never a genuine human prompt
    for name, verdict in results.items():
        if verdict != "human":
            assert name == JUDGMENT_CALL, f"UNSANCTIONED human misclassification: {name}={verdict}"


def test_judgment_call_documented_direction():
    """The opens-with-XML case falls to MACHINE (the cheap-error side) — pin the documented call."""
    assert _classify(HUMAN_CASES[JUDGMENT_CALL]) == "machine"


def test_full_trap_bar():
    """Aggregate bar: all machine cases correct AND >=3/4 human correct."""
    m = sum(1 for p in MACHINE_CASES.values() if _classify(p) == "machine")
    h = sum(1 for p in HUMAN_CASES.values() if _classify(p) == "human")
    assert m == len(MACHINE_CASES), f"machine bar {len(MACHINE_CASES)}/{len(MACHINE_CASES)} not met: {m}/{len(MACHINE_CASES)}"
    assert h >= 3, f"human bar >=3/4 not met: {h}/4"


# ── T-134: headless fleet-worker skip (completion probe #1) ──
def test_headless_fleet_worker_reminder_stays_silent():
    """The plugin's own hook, invoked exactly as the harness would (fabricated stdin payload),
    must skip the full-enhance reminder for a headless worker prompt — the DoD-mandated probe
    for when the live install-cache path can't be exercised without a post-merge /plugin update."""
    out = _run_reminder(MACHINE_CASES["headless_fleet_worker"])
    assert "RENDER THE FULL ENHANCE PROCESS" not in out, "headless worker turn must NOT get the full-enhance reminder"
    assert "*Enhanced" not in out, "headless worker turn must not be told to emit an *Enhanced banner"


def test_interactive_human_prompt_still_triggers_enhance_unchanged():
    """DoD #2: prove interactive typed-prompt behavior is UNCHANGED by this fix — a normal user
    prompt (no dispatcher marker) still triggers the full enhance pipeline via the same gate
    logic/fixtures used above."""
    out = _run_reminder(HUMAN_CASES["long_human"])
    assert "RENDER THE FULL ENHANCE PROCESS" in out, "a normal human prompt must still get the full-enhance reminder"


# ── Hub reminder-hook integration ──
def _run_reminder(prompt: str) -> str:
    res = subprocess.run(
        [BASH, str(HUB_REMINDER)],
        input=f'{{"prompt": {_json(prompt)}}}',
        capture_output=True, text=True, cwd=str(ROOT),
    )
    return res.stdout


def _json(s: str) -> str:
    import json
    return json.dumps(s)


def _run_reminder_session(prompt: str, session_id: str, home: Path) -> str:
    """T-445 round 3: the once-per-session gate writes its marker under $HOME/.claude/, not the
    project's own .claude/ (so a downstream project that tracks .claude/ can never commit it).
    `home` MUST be a throwaway tmp_path — never the real machine HOME — so a test run never
    touches ~/.claude/.enhance-reminder-shown on this PC and pytest's tmp_path fixture handles
    cleanup on its own."""
    import json
    import os
    env = {**os.environ, "HOME": str(home)}
    res = subprocess.run(
        [BASH, str(HUB_REMINDER)],
        input=json.dumps({"prompt": prompt, "session_id": session_id}),
        capture_output=True, text=True, cwd=str(ROOT), env=env,
    )
    return res.stdout


# ── T-445: once-per-session gate on the full reminder + governance tail ──
def test_reminder_full_text_on_first_turn_of_session(tmp_path):
    out = _run_reminder_session(HUMAN_CASES["long_human"], "t445-first-turn", tmp_path)
    assert "RENDER THE FULL ENHANCE PROCESS" in out, "turn 1 of a new session must get the full reminder"
    assert "DECIDE, DON'T ASK" in out, "turn 1 must still get the full governance tail"
    assert (tmp_path / ".claude" / ".enhance-reminder-shown" / "t445-first-turn").exists(), (
        "marker must live under $HOME/.claude/.enhance-reminder-shown/<session_id>"
    )


def test_reminder_one_line_pointer_on_second_turn_same_session(tmp_path):
    _run_reminder_session(HUMAN_CASES["long_human"], "t445-second-turn", tmp_path)  # turn 1: consumes the marker
    out = _run_reminder_session(HUMAN_CASES["long_human"], "t445-second-turn", tmp_path)  # turn 2: same session
    assert "RENDER THE FULL ENHANCE PROCESS" not in out, "turn 2+ of the same session must NOT re-render the full text"
    assert "DECIDE, DON'T ASK" not in out, "turn 2+ must not re-render the full governance tail either"
    assert out.strip() == (
        "Reminder: enhance banner + governance tail apply (SSOT prompt-auto-enhance.md); "
        "full text shown at turn 1."
    )


def test_reminder_full_text_again_on_a_different_session_id(tmp_path):
    _run_reminder_session(HUMAN_CASES["long_human"], "t445-session-a", tmp_path)  # turn 1 of session A
    out = _run_reminder_session(HUMAN_CASES["long_human"], "t445-session-b", tmp_path)  # turn 1 of a DIFFERENT session
    assert "RENDER THE FULL ENHANCE PROCESS" in out, "a new session_id must get its own turn-1 full reminder"


def test_reminder_gate_skipped_when_session_id_absent():
    """No session_id in stdin (older harness, or the pre-existing tests in this file that omit
    it) -> gating is skipped entirely and the full text renders every call, matching pre-T-445
    behavior — this is what keeps test_reminder_renders_full_process_on_human_turn (below)
    order-independent and non-flaky."""
    out1 = _run_reminder(HUMAN_CASES["long_human"])
    out2 = _run_reminder(HUMAN_CASES["long_human"])
    assert "RENDER THE FULL ENHANCE PROCESS" in out1
    assert "RENDER THE FULL ENHANCE PROCESS" in out2


def test_reminder_suppresses_full_process_on_machine_turn():
    out = _run_reminder(MACHINE_CASES["task_notification_xml"])
    assert "RENDER THE FULL ENHANCE PROCESS" not in out, "machine turn must NOT get the full-enhance reminder"
    assert "DECIDE, DON'T ASK" in out, "machine turn must STILL get the governance tail"


def test_reminder_renders_full_process_on_human_turn():
    out = _run_reminder(HUMAN_CASES["long_human"])
    assert "RENDER THE FULL ENHANCE PROCESS" in out, "human turn must get the full-enhance reminder"


# ── T-134: plugin copy, exercised directly (the actual reported defect: plugin installed at
# USER level fires in ANY project, including one with no local reminder copy) ──
def test_plugin_reminder_stays_silent_for_headless_worker_in_any_project(tmp_path):
    """Reproduces the T-133 live-fire shape: a fleet worker's stdin-piped contract, run from a
    neutral project dir (no local hook override) — the exact conditions under which the plugin's
    UserPromptSubmit gate fired and leaked the ceremony into the worker's JSON result."""
    import json
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    out = subprocess.run(
        [BASH, str(PLUGIN_REMINDER)],
        input=json.dumps({"prompt": MACHINE_CASES["headless_fleet_worker"]}),
        capture_output=True, text=True, cwd=str(neutral), env=_os_environ(),
    ).stdout
    assert "REMINDER" not in out, "headless fleet-worker turn must get NO reminder output at all"
    assert "*Enhanced" not in out


# ── Cross-copy + wiring guards ──
def test_classifier_present_in_all_three_trees():
    for p in (HUB_LIB, CORE_LIB, PLUGIN_LIB):
        assert p.exists(), f"missing classifier copy: {p.relative_to(ROOT)}"


def test_hub_and_core_classifier_identical():
    assert HUB_LIB.read_text(encoding="utf-8") == CORE_LIB.read_text(encoding="utf-8"), (
        "hub and core turn-origin.sh must be byte-identical (dual-home synced)"
    )


def test_plugin_reminder_honors_full_process_scope(tmp_path):
    """Plugin reminder: default scope (human-prompts) skips machine turns; 'everywhere' re-enables."""
    import json
    default_settings = ROOT / "plugins" / "prompt-auto-enhance" / "enhance-settings.default.json"
    cfg = json.loads(default_settings.read_text(encoding="utf-8"))
    assert cfg.get("full_process_scope") == "human-prompts", "owner default must be human-prompts"

    # Run from a NEUTRAL cwd (downstream-like project with no local reminder copy), not the
    # hub root: since the coexistence stand-down (2026-07-12) the plugin copy correctly goes
    # SILENT wherever the host wires its own prompt-enhance-reminder.sh — which the hub does.
    # This test's purpose is scope-honoring, not hub-cwd behavior.
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()

    def run_plugin(prompt: str, settings_path: Path) -> str:
        return subprocess.run(
            [BASH, str(PLUGIN_REMINDER)],
            input=json.dumps({"prompt": prompt}),
            capture_output=True, text=True, cwd=str(neutral),
            env={**_os_environ(), "ENHANCE_SETTINGS_FILE": str(settings_path)},
        ).stdout

    machine = MACHINE_CASES["task_notification_xml"]
    human = HUMAN_CASES["long_human"]
    # default (human-prompts): machine turn gets NO reminder, human turn does
    assert "REMINDER" not in run_plugin(machine, default_settings)
    assert "REMINDER" in run_plugin(human, default_settings)
    # everywhere: machine turn DOES get the reminder
    everywhere = tmp_path / "everywhere.json"
    cfg["full_process_scope"] = "everywhere"
    everywhere.write_text(json.dumps(cfg), encoding="utf-8")
    assert "REMINDER" in run_plugin(machine, everywhere)


# ── T-445 round 2/3: plugin copy — once-per-session full-text gate ──
def _run_plugin_reminder(prompt: str, cwd: Path, session_id: str | None = None, home: Path | None = None,
                          settings_file: Path | None = None) -> str:
    """Round 3: the marker lives under $HOME/.claude/.enhance-reminder-shown/<session_id>, so
    `home` MUST be a throwaway tmp_path in any test that passes a session_id — never the real
    machine HOME."""
    import json
    payload = {"prompt": prompt}
    if session_id is not None:
        payload["session_id"] = session_id
    env = _os_environ()
    if home is not None:
        env = {**env, "HOME": str(home)}
    if settings_file is not None:
        env = {**env, "ENHANCE_SETTINGS_FILE": str(settings_file)}
    return subprocess.run(
        [BASH, str(PLUGIN_REMINDER)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(cwd), env=env,
    ).stdout


def test_plugin_reminder_full_text_on_first_turn_of_session(tmp_path):
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    out = _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id="pae-first-turn", home=tmp_path)
    assert "REMINDER" in out, "turn 1 of a new session must get the full reminder"
    assert (tmp_path / ".claude" / ".enhance-reminder-shown" / "pae-first-turn").exists(), (
        "marker must live under $HOME/.claude/.enhance-reminder-shown/<session_id>"
    )


def test_plugin_reminder_one_line_pointer_on_second_turn_same_session(tmp_path):
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id="pae-second-turn", home=tmp_path)  # turn 1
    out = _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id="pae-second-turn", home=tmp_path)  # turn 2
    assert out.strip() == (
        "Reminder: enhance banner + governance tail apply (SSOT prompt-auto-enhance.md); "
        "full text shown at turn 1."
    ), f"turn 2+ of the same session must render only the one-line pointer, got: {out!r}"


def test_plugin_reminder_full_text_again_on_a_different_session_id(tmp_path):
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id="pae-session-a", home=tmp_path)  # turn 1 of A
    out = _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id="pae-session-b", home=tmp_path)  # turn 1 of B
    assert "REMINDER" in out, "a new session_id must get its own turn-1 full reminder"


def test_plugin_reminder_gate_skipped_when_session_id_absent(tmp_path):
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    out1 = _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id=None, home=tmp_path)
    out2 = _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id=None, home=tmp_path)
    assert "REMINDER" in out1 and "REMINDER" in out2, (
        "no session_id -> gating skipped, full text renders every turn (pre-existing behavior)"
    )


def test_plugin_reminder_once_per_session_setting_false_disables_gate(tmp_path):
    import json
    neutral = tmp_path / "neutral-project"
    neutral.mkdir()
    default_settings = ROOT / "plugins" / "prompt-auto-enhance" / "enhance-settings.default.json"
    cfg = json.loads(default_settings.read_text(encoding="utf-8"))
    cfg["reminder_full_text_once_per_session"] = False
    settings_path = tmp_path / "settings-gate-off.json"
    settings_path.write_text(json.dumps(cfg), encoding="utf-8")

    def run_plugin(sid: str) -> str:
        return _run_plugin_reminder(HUMAN_CASES["long_human"], neutral, session_id=sid, home=tmp_path,
                                     settings_file=settings_path)

    out1 = run_plugin("pae-gate-off")
    out2 = run_plugin("pae-gate-off")
    assert "REMINDER" in out1 and "REMINDER" in out2, (
        "reminder_full_text_once_per_session=false must render the full text on every turn"
    )


def test_plugin_default_settings_has_once_per_session_key():
    import json
    default_settings = ROOT / "plugins" / "prompt-auto-enhance" / "enhance-settings.default.json"
    cfg = json.loads(default_settings.read_text(encoding="utf-8"))
    assert cfg.get("reminder_full_text_once_per_session") is True, (
        "reminder_full_text_once_per_session must default to true"
    )
    assert "reminder_full_text_once_per_session" in cfg.get("_help", {}), (
        "the setting must be documented in _help"
    )


def _os_environ() -> dict:
    import os
    return dict(os.environ)


def test_hooks_source_the_classifier_fail_open():
    for hook in (HUB_REMINDER, HUB_OVERASK, CORE_OVERASK, PLUGIN_REMINDER, PLUGIN_GUARD):
        body = hook.read_text(encoding="utf-8")
        assert "turn-origin.sh" in body, f"{hook.name} must source turn-origin.sh"
        assert "classify_turn() { echo human; }" in body, (
            f"{hook.name} must define a fail-open classify_turn stub (missing lib => human => unchanged)"
        )
