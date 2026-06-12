"""Reference template distributed by the hub. See `rules/notifier-integration.md`.

The receiving contract is Notifier's `/notify` (NotifyEvent) + `/heartbeat`
(github.com/abhayla/Notifier). Reference template — adapt imports to your
project (`requests` shown; `httpx` works identically with ``timeout=2``).

Fail-open by construction: silent no-op when NOTIFIER_URL / NOTIFIER_KEY are
unset (dev, CI, pre-deploy); 2s timeout; every failure swallowed and logged at
debug; never raises. A dead/slow Notifier can NEVER break the host app.

Note: these calls are synchronous and may block up to 2s — in a hot request
path, run them via a background task/thread (the TS template's fire-and-forget
equivalent) rather than inline.
"""

import logging
import os

import requests  # adapt to your project; httpx.post(...) is a drop-in here

log = logging.getLogger(__name__)

# <-- set per project: must match this project's `projects.<name>` key in Notifier's config.yaml
PROJECT = os.environ.get("NOTIFIER_PROJECT", "your-project")


def notify_owner(severity, title, body=None, type=None, dedupe_key=None):
    """Owner alert via Notifier. severity: "P0" | "P1" | "P2" | "info"."""
    url = os.environ.get("NOTIFIER_URL")
    key = os.environ.get("NOTIFIER_KEY")
    if not url or not key:
        return  # not configured → silent no-op
    payload = {
        "project": PROJECT,
        "severity": severity,
        "title": title,
        "body": body,
        "type": type,
        "dedupeKey": dedupe_key,
    }
    try:
        requests.post(
            f"{url.rstrip('/')}/notify",
            # Omit unset optionals: Notifier's validator rejects JSON null for
            # `type` (400) — mirror JSON.stringify's undefined-key dropping.
            json={k: v for k, v in payload.items() if v is not None},
            headers={"X-Api-Key": key},
            timeout=2,
        )
    except Exception as err:  # noqa: BLE001 — owner-alerting must never disturb the host app
        log.debug("notify_owner failed (non-fatal): %s", err)


def heartbeat(name, interval_minutes):
    """Uptime heartbeat → Notifier's missed-heartbeat watchdog (dead-man's switch).

    Call on your own schedule with the SAME name and interval_minutes every
    time; the watchdog alerts the owner when a beat goes missing. Requires
    Notifier >= heartbeat-watchdog release — see the Notifier watchdog contract.
    """
    url = os.environ.get("NOTIFIER_URL")
    key = os.environ.get("NOTIFIER_KEY")
    if not url or not key:
        return  # not configured → silent no-op
    try:
        requests.post(
            f"{url.rstrip('/')}/heartbeat",
            json={"project": PROJECT, "name": name, "intervalMinutes": interval_minutes},
            headers={"X-Api-Key": key},
            timeout=2,
        )
    except Exception as err:  # noqa: BLE001
        log.debug("heartbeat failed (non-fatal): %s", err)
