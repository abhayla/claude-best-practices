#!/usr/bin/env python3
"""Browser-free verification that a GA4 stream actually receives data.

Removes the analytics-setup STEP 6 hard dependency on a browser (Playwright / Chrome
DevTools MCP). Flow, all server-side via the service-account key:
  1. Ensure a Measurement Protocol api_secret exists for the stream (Admin API; idempotent).
  2. Send a test event to the MP collect endpoint (and the /debug endpoint first, to surface
     any validationMessages without polluting data).
  3. Poll the GA4 Data API realtime report until our event / an active user appears.
A real hit reaching GA4 is the substance — snippet presence is not. Exit 0 = verified,
4 = sent-but-not-seen (inconclusive), 2 = config error, 3 = API error.

Usage:
  verify_hit.py --from-inventory .claude/analytics-inventory.json [--origin https://x] [--key PATH]
  verify_hit.py --property properties/123 --stream <stream> --id G-XXX [--key PATH]
Env fallback: GA_PROVISION_SA_KEY.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

ADMIN = "https://analyticsadmin.googleapis.com/v1beta"
DATA = "https://analyticsdata.googleapis.com/v1beta"
MP = "https://www.google-analytics.com"
SCOPES = ["https://www.googleapis.com/auth/analytics.edit",
          "https://www.googleapis.com/auth/analytics.readonly"]
EVENT = "auto_google_analytics_verify"


def _die(code, msg):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def mint_token(key_path):
    if not key_path or not os.path.exists(key_path):
        _die(2, f"SA_KEY_MISSING: no service-account key at '{key_path}'.")
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
        creds.refresh(Request())
        if creds.token:
            return creds.token
    except ImportError:
        pass
    except Exception as e:
        _die(2, f"TOKEN_MINT_FAILED (google-auth): {e}")
    import subprocess
    gcloud = os.environ.get("GCLOUD_PATH", "gcloud")
    try:
        with open(key_path, encoding="utf-8") as f:
            sa_email = json.load(f).get("client_email", "")
        subprocess.run([gcloud, "auth", "activate-service-account", "--key-file", key_path],
                       capture_output=True, text=True)
        r = subprocess.run([gcloud, "auth", "print-access-token", sa_email,
                            "--scopes", ",".join(SCOPES)], capture_output=True, text=True)
        if r.stdout.strip():
            return r.stdout.strip()
        _die(2, "TOKEN_MINT_FAILED (gcloud): " + (r.stderr or "no token").strip())
    except FileNotFoundError:
        _die(2, "NO_TOKEN_BACKEND: install `google-auth` or the gcloud CLI.")


def api(method, url, tok, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or "{}")
    except urllib.error.HTTPError as e:
        _die(3, f"API {method} {url} -> {e.code}: {e.read().decode()[:400]}")


ACK_TEXT = (
    "I acknowledge that I have the necessary privacy disclosures and rights from my end users "
    "for the collection and processing of their data, including the association of such data with "
    "the visitation information Google Analytics collects from my site and/or app property."
)


def ack_user_data_collection(prop, tok):
    """Attest the User Data Collection Acknowledgement (required before MP secrets can be
    created). Idempotent — safe to call on an already-acknowledged property."""
    api("POST", f"{ADMIN}/{prop}:acknowledgeUserDataCollection", tok, {"acknowledgement": ACK_TEXT})


def ensure_mp_secret(stream, tok):
    url = f"{ADMIN}/{stream}/measurementProtocolSecrets"
    for s in api("GET", url, tok).get("measurementProtocolSecrets", []):
        if s.get("secretValue"):
            return s["secretValue"]
    return api("POST", url, tok, {"displayName": "auto-google-analytics verify"}).get("secretValue")


def send_mp(measurement_id, secret, client_id):
    body = json.dumps({"client_id": client_id,
                       "events": [{"name": EVENT, "params": {"debug_mode": 1}}]}).encode()
    qs = f"?measurement_id={measurement_id}&api_secret={secret}"
    # debug endpoint first — surfaces validationMessages without recording
    try:
        with urllib.request.urlopen(urllib.request.Request(
                MP + "/debug/mp/collect" + qs, data=body, method="POST")) as r:
            msgs = json.loads(r.read() or "{}").get("validationMessages", [])
            if msgs:
                _die(4, "MP_VALIDATION_FAILED: " + json.dumps(msgs)[:400])
    except urllib.error.HTTPError as e:
        _die(3, f"MP debug -> {e.code}: {e.read().decode()[:200]}")
    # real hit
    urllib.request.urlopen(urllib.request.Request(
        MP + "/mp/collect" + qs, data=body, method="POST")).read()


def poll_realtime(prop, tok, tries=10, delay=3):
    url = f"{DATA}/{prop}:runRealtimeReport"
    payload = json.dumps(
        {"dimensions": [{"name": "eventName"}], "metrics": [{"name": "eventCount"}]}).encode()
    for n in range(tries):
        req = urllib.request.Request(url, data=payload, method="POST", headers={
            "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                rep = json.loads(resp.read() or "{}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 403 and ("SERVICE_DISABLED" in body or "has not been used" in body):
                _die(2, "DATA_API_DISABLED: enable the Google Analytics Data API once for this "
                        "project, then re-run:\n  gcloud services enable analyticsdata.googleapis.com "
                        "--project=<your-gcp-project>\n(The test event WAS sent and accepted; only "
                        "realtime confirmation needs the Data API.)")
            _die(3, f"realtime API -> {e.code}: {body[:300]}")
        for row in rep.get("rows", []):
            if (row.get("dimensionValues") or [{}])[0].get("value") == EVENT:
                return True
        time.sleep(delay)
    return False


def main():
    ap = argparse.ArgumentParser(description="Browser-free GA4 hit verification.")
    ap.add_argument("--from-inventory", default="")
    ap.add_argument("--origin", default="")
    ap.add_argument("--property", default="")
    ap.add_argument("--stream", default="")
    ap.add_argument("--id", default="")
    ap.add_argument("--key", default=os.environ.get("GA_PROVISION_SA_KEY", ""))
    args = ap.parse_args()

    prop, stream, mid = args.property, args.stream, args.id
    if args.from_inventory:
        with open(args.from_inventory, encoding="utf-8") as f:
            sites = json.load(f).get("sites", {})
        rec = sites.get(args.origin) if args.origin else (
            next(iter(sites.values())) if len(sites) == 1 else None)
        if not rec:
            _die(2, "INVENTORY_AMBIGUOUS: pass --origin to pick a site from the inventory.")
        prop, stream, mid = rec["property"], rec["stream"], rec["measurement_id"]
    if not (prop and stream and mid):
        _die(2, "MISSING_TARGET: need --property + --stream + --id, or --from-inventory.")

    tok = mint_token(args.key)
    ack_user_data_collection(prop, tok)
    secret = ensure_mp_secret(stream, tok)
    if not secret:
        _die(3, "MP_SECRET_FAILED: could not create/read a Measurement Protocol secret.")
    cid = str(uuid.uuid4())
    print(f"# sending test event '{EVENT}' to {mid} (client {cid})")
    send_mp(mid, secret, cid)
    print("# polling realtime report...")
    if poll_realtime(prop, tok):
        print(f"VERIFIED: '{EVENT}' is visible in {prop} realtime — data is flowing.")
        sys.exit(0)
    _die(4, "NOT_SEEN: event sent but not visible in realtime within the window "
            "(realtime can lag; re-run, or check the property/stream).")


if __name__ == "__main__":
    main()
