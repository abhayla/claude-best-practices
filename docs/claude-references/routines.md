Source: https://code.claude.com/docs/en/routines
Fetched: 2026-06-27

# Automate work with routines

> Put Claude Code on autopilot. Define routines that run on a schedule, trigger on API calls, or react to GitHub events from Anthropic-managed cloud infrastructure.

> **Note:** Routines are in research preview. Behavior, limits, and the API surface may change.

A routine is a saved Claude Code configuration: a prompt, one or more repositories, and a set of connectors, packaged once and run automatically. Routines execute on Anthropic-managed cloud infrastructure, so they keep working when your laptop is closed.

Each routine can have one or more triggers:
- **Scheduled**: recurring cadence (hourly/nightly/weekly) or once at a specific future time.
- **API**: trigger on demand via HTTP POST to a per-routine endpoint with a bearer token.
- **GitHub**: run in response to repo events (pull requests, releases).

A single routine can combine triggers. Available on Pro, Max, Team, Enterprise with Claude Code on the web enabled. Create/manage at claude.ai/code/routines or from the CLI with `/schedule`. Team/Enterprise Owners can disable routines org-wide.

## Example use cases

- **Backlog maintenance** (schedule) — label/assign issues nightly, post summary to Slack.
- **Alert triage** (API) — monitoring tool POSTs the alert; routine correlates stack trace with commits, opens a draft fix PR.
- **Bespoke code review** (GitHub `pull_request.opened`) — applies team checklist, inline comments.
- **Deploy verification** (API) — CD pipeline calls after deploy; smoke-checks, posts go/no-go.
- **Docs drift** (schedule) — scans merged PRs weekly, opens docs update PRs.
- **Library port** (GitHub `pull_request.closed` merged) — ports a change to a parallel SDK, opens matching PR.

## Create a routine

From web (claude.ai/code/routines), Desktop (Routines → New routine → Remote; Local instead creates a Desktop scheduled task), or CLI. All three write to the same cloud account.

**Routines run autonomously as full cloud sessions: there is no permission-mode picker and no approval prompts during a run.** Reach is determined by selected repositories + branch-push setting, the environment's network access/variables, and included connectors — scope each to what's needed. Routines belong to your individual claude.ai account (not shared with teammates), count against your daily run allowance, and act AS you (commits/PRs carry your GitHub user; connector actions use your linked accounts).

Form steps: name + prompt (most important — self-contained, explicit about success; includes a model selector used on every run) → select repositories (cloned each run from default branch; Claude creates `claude/`-prefixed branches) → select environment (network access level, env vars/secrets, cached setup script) → select trigger(s) → review connectors (all connected MCP connectors included by default — remove unneeded; Claude can use every tool incl. writes without asking) + permissions (enable "Allow unrestricted branch pushes" per repo to push to non-`claude/` branches).

### Create from the CLI

`/schedule` creates a scheduled routine conversationally (e.g. `/schedule daily PR review at 9am`, or one-off `/schedule clean up feature flag in one week`). `/schedule` in CLI creates SCHEDULED routines only — add API/GitHub triggers on the web. Also: `/schedule list`, `/schedule update`, `/schedule run`.

## Configure triggers

### Schedule trigger
Preset frequencies: hourly, daily, weekdays, weekly. Times entered in local zone, converted automatically. Runs may start a few minutes late (consistent stagger offset per routine). Custom interval: pick closest preset then `/schedule update` to set a cron expression. **Minimum interval is one hour; more-frequent expressions are rejected.** One-off runs auto-disable after firing (marked "Ran"); they do NOT count against the daily routine cap (draw normal subscription usage).

### API trigger
Gives a routine a dedicated HTTP endpoint. POST with bearer token starts a new session, returns a session URL. Added from the web only (CLI can't create/revoke tokens). Token shown once. POST to `/fire`:

```bash
curl -X POST https://api.anthropic.com/v1/claude_code/routines/trig_.../fire \
  -H "Authorization: Bearer sk-ant-oat01-xxxxx" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "anthropic-version: 2023-06-01" \
  -H "Content-Type: application/json" \
  -d '{"text": "Sentry alert SEN-4521 fired in prod. Stack trace attached."}'
```

Optional `text` field = run-specific context (alert body, failing log), passed as a literal string (not parsed). Returns `{type: routine_fire, claude_code_session_id, claude_code_session_url}`. The `/fire` endpoint is under the `experimental-cc-routine-2026-04-01` beta header (claude.ai users only; not part of the Claude Platform API).

### GitHub trigger
Starts a new session per matching event. Requires the Claude GitHub App installed (note: `/web-setup` grants clone access but does NOT install the App / enable webhooks). Supported events: Pull request (opened/closed/assigned/labeled/synchronized/…), Release (created/published/edited/deleted). Pull-request filters: Author, Title, Body, Base branch, Head branch, Labels, Is draft, Is merged — operators: equals / contains / starts with / is one of / is not one of / matches regex (regex tests the WHOLE value — use `.*hotfix.*`). Each matching event = its own session (no session reuse).

## Manage routines

Detail page shows repos, connectors, prompt, schedule, API tokens, GitHub triggers, past runs. **Run now** starts immediately. Pause/resume via the Repeats toggle. Edit changes name/prompt/repos/env/connectors/triggers. Delete removes the routine (past sessions remain).

> **Note:** A green status means the session started and exited without an INFRASTRUCTURE error — NOT that the task succeeded. Open the run to confirm what Claude actually did (blocked network requests, missing connector tools, task-level failures surface in the transcript, not the status indicator).

Default environment uses **Trusted** network access (default allowlist of package registries, cloud APIs, container registries, common dev domains reachable; arbitrary domains fail `403` `x-deny-reason: host_not_allowed`). MCP connector traffic routes through Anthropic's servers. By default Claude can only push to `claude/`-prefixed branches.

## Usage and limits

Routines draw down subscription usage like interactive sessions, PLUS a daily cap on runs started per account. Over the cap: metered overage if usage credits are on, else rejected until reset. One-off runs are exempt from the daily routine cap.

## Troubleshooting (selected)

- `/schedule` "No commands match"/"Unknown command": requires a claude.ai subscription login (not Console API key / Bedrock / Vertex / Foundry — unset `ANTHROPIC_API_KEY`/`ANTHROPIC_AUTH_TOKEN`/`apiKeyHelper`); telemetry-disable env vars (`DISABLE_TELEMETRY`, `DO_NOT_TRACK`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`, `DISABLE_GROWTHBOOK`) break the feature-flag fetch `/schedule` depends on; not available inside a Claude-Code-on-the-web session; CLI older than v2.1.81 → `claude update`.
- "Routines are disabled by your organization's policy": a Team/Enterprise Owner turned off the Routines toggle (server-side).

**Hub relevance:** This is the DURABLE, session-independent tier the hub's research doc flags for "don't put durable automation on a 7-day-expiring `/loop`." Routines = cloud, ≥1-hr min, fresh clone (no local files), autonomous (no permission picker — so the hub's deny-class safety must be encoded via `permissions.deny` in committed settings or the prompt, since auto-mode tiers don't apply the same way). The GitHub-event + API triggers overlap the hub's existing `auto-pr`/scan crons and `/autofix-pr`; the hub keeps durable crons on GitHub Actions today — routines are the managed alternative to evaluate. `/schedule` is the CLI surface; sabrina.dev's "loop engineering" pairs `/goal` with routines for durability.
