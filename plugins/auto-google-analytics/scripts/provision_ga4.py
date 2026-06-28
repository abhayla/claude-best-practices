#!/usr/bin/env python3
"""Auto-provision one GA4 property + web data stream per site via a service-account key.

Portable productization of the proven hub rollout script: no hardcoded sites, key path,
SA email or gcloud path — everything comes from CLI args / env / settings. Idempotent:
skips a site whose property displayName already exists, and reuses an existing web stream.

Token minting (in priority order, all bypass the user-ADC analytics-scope block because
they use the SERVICE-ACCOUNT key directly):
  1. google-auth library if installed (preferred — zero external process, fully portable).
  2. gcloud CLI fallback (GCLOUD_PATH or `gcloud` on PATH) for environments without google-auth.

The ONE irreducible human prerequisite: a service account with `analytics.edit`, granted
Administrator at the GA ACCOUNT level, key JSON on disk. Google blocks automation-browser
login, so this single grant cannot be automated — once done, every project is zero-touch.

Usage:
  provision_ga4.py --site "My Site=https://example.com" [--site "Other=https://b.com" ...] \
                   [--key PATH] [--out PATH] [--tz Asia/Kolkata] [--cur INR]
Env fallbacks: GA_PROVISION_SA_KEY (key path), GA_PROVISION_TZ, GA_PROVISION_CURRENCY,
GCLOUD_PATH. Output JSON (default ./.claude/analytics-inventory.json) maps origin -> IDs.
Exit codes: 0 ok; 2 config/precondition error; 3 API error.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ADMIN = "https://analyticsadmin.googleapis.com/v1beta"
SCOPE = "https://www.googleapis.com/auth/analytics.edit"
ACK_TEXT = (
    "I acknowledge that I have the necessary privacy disclosures and rights from my end users "
    "for the collection and processing of their data, including the association of such data with "
    "the visitation information Google Analytics collects from my site and/or app property."
)


def _die(code, msg):
    sys.stderr.write(msg.rstrip() + "\n")
    sys.exit(code)


def mint_token(key_path):
    """Return an OAuth access token for the SA key, via google-auth or gcloud."""
    if not key_path or not os.path.exists(key_path):
        _die(2, f"SA_KEY_MISSING: no service-account key at '{key_path}'. "
                "Set --key or GA_PROVISION_SA_KEY. See the plugin README for the one-time setup.")
    # 1) google-auth (preferred, no subprocess)
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        creds = service_account.Credentials.from_service_account_file(
            key_path, scopes=[SCOPE])
        creds.refresh(Request())
        if creds.token:
            return creds.token
    except ImportError:
        pass
    except Exception as e:  # malformed key, clock skew, etc.
        _die(2, f"TOKEN_MINT_FAILED (google-auth): {e}")
    # 2) gcloud fallback
    gcloud = os.environ.get("GCLOUD_PATH", "gcloud")
    try:
        with open(key_path, encoding="utf-8") as f:
            sa_email = json.load(f).get("client_email", "")
        subprocess.run([gcloud, "auth", "activate-service-account",
                        "--key-file", key_path], capture_output=True, text=True)
        r = subprocess.run([gcloud, "auth", "print-access-token", sa_email,
                            "--scopes", SCOPE], capture_output=True, text=True)
        tok = r.stdout.strip()
        if tok:
            return tok
        _die(2, "TOKEN_MINT_FAILED (gcloud): " + (r.stderr or "no token returned").strip())
    except FileNotFoundError:
        _die(2, "NO_TOKEN_BACKEND: install `google-auth` (pip install google-auth) "
                "or the gcloud CLI to mint a token from the SA key.")


def api(method, path, tok, body=None):
    url = path if path.startswith("http") else ADMIN + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read() or "{}")
    except urllib.error.HTTPError as e:
        _die(3, f"API {method} {url} -> {e.code}: {e.read().decode()[:400]}")


def parse_sites(raw_sites):
    sites = []
    for s in raw_sites:
        if "=" not in s:
            _die(2, f"BAD_SITE '{s}': expected 'Display Name=https://origin'.")
        name, origin = s.split("=", 1)
        sites.append((name.strip(), origin.strip()))
    return sites


def main():
    ap = argparse.ArgumentParser(description="Auto-provision GA4 properties + web streams.")
    ap.add_argument("--site", action="append", default=[], required=True,
                    help="'Display Name=https://origin' (repeatable).")
    ap.add_argument("--key", default=os.environ.get("GA_PROVISION_SA_KEY", ""))
    ap.add_argument("--out", default=os.path.join(".claude", "analytics-inventory.json"))
    ap.add_argument("--tz", default=os.environ.get("GA_PROVISION_TZ", "Asia/Kolkata"))
    ap.add_argument("--cur", default=os.environ.get("GA_PROVISION_CURRENCY", "INR"))
    args = ap.parse_args()

    sites = parse_sites(args.site)
    tok = mint_token(args.key)

    summaries = api("GET", "/accountSummaries", tok).get("accountSummaries", [])
    if not summaries:
        _die(2, "NO_GA_ACCOUNT_VISIBLE: the SA is not yet granted Administrator at the "
                "GA account level. Grant it once in GA Admin, then re-run.")
    account = summaries[0]["account"]
    print(f"# GA account visible: {account} ({summaries[0].get('displayName')})")

    existing = {p.get("displayName"): p.get("property")
                for s in summaries for p in s.get("propertySummaries", [])}

    out = {}
    for name, origin in sites:
        if name in existing:
            prop = existing[name]
            print(f"= {name}: property exists ({prop})")
        else:
            prop = api("POST", "/properties", tok, {
                "parent": account, "displayName": name,
                "timeZone": args.tz, "currencyCode": args.cur})["name"]
            print(f"+ {name}: created property {prop}")
        # Attest User Data Collection (required before data collection / MP secrets; idempotent).
        api("POST", f"/{prop}:acknowledgeUserDataCollection", tok, {"acknowledgement": ACK_TEXT})
        streams = api("GET", f"/{prop}/dataStreams", tok).get("dataStreams", [])
        web = next((s for s in streams if s.get("type") == "WEB_DATA_STREAM"), None)
        if not web:
            web = api("POST", f"/{prop}/dataStreams", tok, {
                "type": "WEB_DATA_STREAM", "displayName": name + " Web",
                "webStreamData": {"defaultUri": origin}})
        mid = web.get("webStreamData", {}).get("measurementId")
        out[origin] = {"property": prop, "measurement_id": mid, "stream": web.get("name")}
        print(f"  -> {origin}  Measurement ID = {mid}")

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    payload = {"account": account, "sites": out}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\n# wrote {out_path}")


if __name__ == "__main__":
    main()
