# CLAUDE.md "Production & monitoring" block — template

Reference template distributed by the hub. See `rules/notifier-integration.md`.

Copy the block below into your project's `CLAUDE.md` (replace every `<placeholder>`)
and keep it current. **Dual-source intent:** this block is the decentralized
*read layer* — how any Claude session learns the project's prod-deploy and
Notifier-link status from `CLAUDE.md` alone; Notifier's admin config
(`projects.<name>` in its `config.yaml`) remains the *authoritative live registry*.

```markdown
## Production & monitoring

- **Deployed:** <url> · host <VPS/Vercel/…> · since <date>.
- **Owner alerts:** Notifier gateway (`NOTIFIER_URL`/`NOTIFIER_KEY` set in prod env) — wired: <yes/no>. Detectors: <signup/5xx/DB-down/boot-env/domain…>.
- **Uptime heartbeat:** Notifier missed-heartbeat watchdog — heartbeat sent every <N> min: <yes/no>. (Do NOT use healthchecks.io/UptimeRobot/cron-ping.me — Notifier supersedes them.)
- **Live registry:** this project appears in Notifier's admin config as `projects.<name>`.
```
