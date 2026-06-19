---
name: vps-deploy
description: >
  Deploy a built app to a Linux VPS over SSH — rsync artifacts to the webroot,
  validate + reload nginx (or reload a PM2 process), smoke-test the live URL, and
  roll back automatically if the smoke check fails. Use when shipping a static
  site or Node/PM2 app to a self-managed VPS (not a PaaS). NOT for Kubernetes
  (use /k8s-deploy), IaC provisioning (use /iac-deploy), or choosing a deploy
  strategy (use /deploy-strategy first).
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<artifact-dir> [--app static|pm2] [--staging] [--no-rollback]"
version: "1.0.0"
type: workflow
triggers:
  - vps deploy
  - deploy to vps
  - ssh deploy
  - nginx deploy
  - rsync deploy
---

# vps-deploy — SSH + rsync + nginx/PM2 deploy with smoke + rollback

Ships a locally-built artifact to a Linux VPS you control over SSH. This is the
**deterministic, reversible** finish-line step for the "deploy = done" goal: it
deploys, **proves the live URL works**, and **rolls back on failure** — it never
leaves a half-deployed site live.

> **G3 GATE (human-approval-gates.md):** a production deploy is an irreversible,
> outward action. This skill MUST be invoked with explicit user go for the target
> environment; it does not self-trigger. For first-time or high-risk deploys, run
> `/deploy-strategy` first to choose the approach.

## Deploy coordinates (env contract — never hardcode host/keys in the skill)

Read all target coordinates from the environment (project `.env` / the shared
credential base) — MUST NOT hardcode an IP, hostname, key, or webroot:

| Var | Meaning |
|---|---|
| `DEPLOY_HOST` | VPS IP or hostname |
| `DEPLOY_USER` | SSH user — prefer an **unprivileged deploy user**, not root |
| `DEPLOY_SSH_KEY` | path to the private key (lives in `~/.ssh/`, never in a repo) |
| `DEPLOY_WEBROOT` | target dir for static artifacts (e.g. `/var/www/<site>`) |
| `DEPLOY_URL` | the live URL to smoke-test after deploy |
| `DEPLOY_VHOST` | (optional) nginx vhost/server_name to validate; omit to skip nginx steps |
| `DEPLOY_PM2_NAME` | (optional, `--app pm2`) the PM2 process name to reload |

Connect with: `ssh -i "$DEPLOY_SSH_KEY" "$DEPLOY_USER@$DEPLOY_HOST" '<cmd>'`.
A read-only probe (`whoami`) MUST succeed in STEP 0 before any write.

## STEP 0: Preflight (read-only — BLOCK on any miss)

1. Assert every required env var is set (`DEPLOY_HOST/USER/SSH_KEY/WEBROOT/URL`).
   Missing → emit `{"result":"BLOCKED","blocker":"MISSING_DEPLOY_ENV"}` and stop.
2. Assert the local artifact dir (`$ARGUMENTS`) exists and is non-empty.
3. SSH read-only probe: `ssh ... 'whoami; nginx -v 2>&1; df -h "$DEPLOY_WEBROOT" | tail -1'`.
   Unreachable/timeout → `{"result":"BLOCKED","blocker":"VPS_UNREACHABLE"}`.
4. **Scope guard:** if `DEPLOY_VHOST` matches an EXISTING vhost that is NOT the one
   you intend to deploy, BLOCK — never overwrite another site's vhost. With
   `--staging`, the vhost MUST be a dedicated staging `server_name` (e.g.
   `staging.<domain>` or a `*.<vps-hostname>` name), never a production one.

## STEP 1: Backup the current release (reversible-by-default)

Before writing anything, snapshot the current webroot on the VPS so rollback is
possible: `ssh ... 'tar czf "$DEPLOY_WEBROOT.bak-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DEPLOY_WEBROOT" . 2>/dev/null || true'`.
Retain the most recent **5** backups; delete older ones. Record the backup path —
STEP 5 restores from it.

## STEP 2: Sync artifacts

`rsync -az --delete <artifact-dir>/ "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_WEBROOT/"`
(via the key). `--delete` makes the webroot match the build exactly; the STEP 1
backup is the safety net. For `--app pm2`, rsync the app dir to its deploy path
instead of a static webroot.

## STEP 3: nginx vhost / PM2 reload — VALIDATE before activating

- **Static (`--app static`, default):** if `DEPLOY_VHOST` is set, write/refresh the
  vhost file, then **`ssh ... 'nginx -t'` FIRST**. Reload (`nginx -s reload` /
  `systemctl reload nginx`) **only if `nginx -t` exits 0** — a bad config that
  reloads can take down EVERY site on the box. If `nginx -t` fails, do NOT reload;
  jump to STEP 5 (the synced files are inert until a reload).
- **PM2 (`--app pm2`):** `ssh ... 'pm2 reload "$DEPLOY_PM2_NAME" --update-env'`;
  confirm the process returns to `online`.

## STEP 4: Post-deploy smoke (the proof — not optional)

Curl the live URL from the VPS and/or locally:
`curl -fsS -o /dev/null -w '%{http_code}' "$DEPLOY_URL"`. Assert (a) a 2xx/3xx
status AND (b) a **content marker** unique to this release (a string/asset that
proves the NEW build is served, not a cached or old page). "It returned 200" over a
blank/old page is NOT a pass — verify substance (see output-plausibility-verification.md).

## STEP 5: Rollback on smoke-fail

If STEP 3's `nginx -t` failed or STEP 4's smoke failed: restore the STEP 1 backup
into the webroot, `nginx -t` + reload (or `pm2 reload`), and re-smoke. Emit
`{"result":"FAILED","rolled_back":true,...}` and escalate via /incident-response if
the rollback itself does not restore a healthy live URL.

## STEP 6: Report

Write `test-results/vps-deploy.json`:
```json
{ "result": "PASSED|FAILED", "url": "<DEPLOY_URL>", "host": "<DEPLOY_HOST>",
  "vhost": "<DEPLOY_VHOST|null>", "rolled_back": false,
  "backup": "<path>", "smoke_status": 200, "evidence": "<marker matched>" }
```
`result=PASSED` only when the smoke check confirmed the new release on the live URL.

## CRITICAL RULES

- MUST run `nginx -t` and require exit 0 BEFORE any nginx reload — a bad reload can
  break every co-hosted site.
- MUST NOT overwrite or edit a vhost/webroot that belongs to another site; with
  `--staging` the target MUST be a dedicated non-production `server_name`.
- MUST back up the current release (STEP 1) before syncing; rollback (STEP 5) is
  mandatory on smoke-fail unless `--no-rollback` is explicitly passed.
- MUST gate `result=PASSED` on a real live-URL smoke that verifies NEW-release
  substance, never just an HTTP 200.
- MUST source host/user/key/webroot from env vars — NEVER hardcode them in the skill
  or a repo file; keys stay in `~/.ssh/`.
- MUST prefer an unprivileged deploy user over root; MUST NOT disable host-key
  checking blindly in a way that persists.
- MUST treat the production deploy as a G3 human-approval gate — invoked with
  explicit user go, never self-triggered.
