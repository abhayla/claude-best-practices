"""Phase 5.1b — close the self-updating loop: scan discovery -> actionable GitHub issue.

5.1a wires release-tracking URLs into the weekly internet scan; `scan_web.py` +
`discovery_adapter.py` DETECT and persist discoveries to `config/discoveries.json`.
This module turns a *migratable* discovery (a high-confidence, high-trust pattern
from an official source that the hub does NOT already have) into a deduplicated
GitHub issue, so a newly-shipped native primitive becomes tracked migration work
instead of sitting unread in a report. (The exact gap that let the hub fall behind
~6 native features before the 2026-06-19 manual audit.)

Reuses `discovery_adapter` (load + registry check) and the `/create-github-issue`
dedup/label conventions. Dry-run by DEFAULT; `--apply` actually files via `gh`.

    PYTHONPATH=. python scripts/discovery_to_issue.py            # dry-run (prints plan)
    PYTHONPATH=. python scripts/discovery_to_issue.py --apply    # file/update issues
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from scripts.discovery_adapter import load_discoveries, is_in_registry

# A discovery is "migratable" (worth an auto-issue) only when it is a confident,
# officially-sourced, genuinely-new pattern — never noise.
MIGRATABLE_MIN_CONFIDENCE = 80
MIGRATABLE_TYPES = {"skill", "agent", "rule", "hook"}
ISSUE_LABEL = "discovery"


def migratable_signature(entry: dict) -> str:
    """Stable dedup marker for a discovery's issue (survives re-scans)."""
    return f"discovery:{entry.get('type', 'unknown')}:{entry.get('name', 'unknown')}"


def select_migratable(data: dict, min_confidence: int = MIGRATABLE_MIN_CONFIDENCE,
                      registry_check=is_in_registry) -> list[dict]:
    """Pure selection — the auto-issue candidates. No side effects (testable).

    Migratable = pending + confidence>=min + high trust + a known pattern type +
    not already shipped in the hub registry.
    """
    out = []
    for d in data.get("discoveries", []):
        if d.get("status") != "pending":
            continue
        if d.get("confidence", 0) < min_confidence:
            continue
        if d.get("source_trust") != "high":
            continue
        if d.get("type") not in MIGRATABLE_TYPES:
            continue
        if registry_check(d.get("name", "")):
            continue
        out.append(d)
    return out


def _issue_body(entry: dict) -> str:
    sig = migratable_signature(entry)
    sources = "\n".join(f"- {s}" for s in entry.get("sources", [entry.get("source", "?")]))
    return (
        f"**Auto-filed by the self-updating scan (Phase 5.1b).** A migratable pattern was "
        f"discovered that the hub does not yet have.\n\n"
        f"- **Pattern:** `{entry.get('name')}` (type: `{entry.get('type')}`)\n"
        f"- **Confidence:** {entry.get('confidence')} · **trust:** {entry.get('source_trust')}\n"
        f"- **Discovered:** {entry.get('discovered')} · **seen:** {entry.get('seen_count', 1)}×\n"
        f"- **Sources:**\n{sources}\n\n"
        f"- **Preview:** {entry.get('content_preview', '')[:280]}\n\n"
        f"**Next step (human):** evaluate vs the hub — adopt-by-pointer, migrate a hand-rolled "
        f"pattern onto it, or reject (then `discovery_adapter.py --reject`). "
        f"Dedup marker: `{sig}`."
    )


def _gh(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def _existing_issue(sig: str) -> str | None:
    """Return the URL of an open/closed issue already tracking this signature, else None."""
    code, out = _gh(["issue", "list", "--label", ISSUE_LABEL, "--state", "all",
                     "--search", sig, "--json", "number,url,body", "--limit", "50"])
    if code != 0:
        return None
    try:
        for it in json.loads(out or "[]"):
            if sig in (it.get("body") or ""):
                return it.get("url")
    except json.JSONDecodeError:
        return None
    return None


def file_issues(candidates: list[dict], apply: bool) -> dict:
    """Create/update one issue per migratable discovery (dedup by signature)."""
    actions = []
    for e in candidates:
        sig = migratable_signature(e)
        title = f"[discovery] adopt/migrate: {e.get('name')} ({e.get('type')})"
        if not apply:
            actions.append({"signature": sig, "action": "DRY_RUN", "title": title})
            continue
        existing = _existing_issue(sig)
        if existing:
            code, out = _gh(["issue", "comment", existing, "--body",
                             f"Still surfaced by the scan ({e.get('discovered')}, "
                             f"seen {e.get('seen_count', 1)}×). {sig}"])
            actions.append({"signature": sig, "action": "COMMENTED", "url": existing,
                            "ok": code == 0})
        else:
            code, out = _gh(["issue", "create", "--title", title,
                             "--body", _issue_body(e),
                             "--label", f"{ISSUE_LABEL},discovery-type-{e.get('type')}"])
            actions.append({"signature": sig, "action": "CREATED",
                            "url": out if code == 0 else None, "ok": code == 0})
    return {"result": "OK", "applied": apply, "candidates": len(candidates), "actions": actions}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase 5.1b: scan discovery -> GitHub issue")
    ap.add_argument("--apply", action="store_true",
                    help="actually create/update issues via gh (default: dry-run)")
    ap.add_argument("--min-confidence", type=int, default=MIGRATABLE_MIN_CONFIDENCE)
    args = ap.parse_args(argv)

    data = load_discoveries()
    candidates = select_migratable(data, min_confidence=args.min_confidence)
    report = file_issues(candidates, apply=args.apply)
    print(json.dumps(report, indent=2))
    # No silent failure (error-handling.md): when actually filing, a gh failure on ANY
    # action must surface as a non-zero exit (the workflow step uses continue-on-error so
    # it annotates the run without killing the scan). Dry-run always succeeds.
    failed = [a for a in report["actions"] if a.get("ok") is False]
    return 1 if (args.apply and failed) else 0


if __name__ == "__main__":
    sys.exit(main())
