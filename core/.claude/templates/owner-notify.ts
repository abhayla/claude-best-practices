/**
 * Reference template distributed by the hub. See `rules/notifier-integration.md`.
 * The receiving contract is Notifier's `/notify` (NotifyEvent) + `/heartbeat`
 * (github.com/abhayla/Notifier). Not compiled in the hub — drop it into your
 * project, set the project name below, and type-check it there.
 *
 * Fire-and-forget owner alerting → the Notifier gateway. This is a DETECTOR
 * client: your app calls notifyOwner() at events worth telling the owner
 * about; Notifier routes them to Telegram/WhatsApp/email per its own config.
 *
 * NON-BREAKING BY CONSTRUCTION:
 *  - no-op when NOTIFIER_URL / NOTIFIER_KEY are unset (dev, test, or before
 *    the env lands in production) — nothing changes for local/CI runs.
 *  - fire-and-forget with a 2s timeout: never awaited in a request's critical
 *    path, never throws. A dead/slow Notifier can NEVER break the host app.
 */

// Swap for your project's logger — failures must be logged at debug, never thrown.
const log = { debug: (...args: unknown[]) => console.debug(...args) };

// <-- set per project: must match this project's `projects.<name>` key in Notifier's config.yaml
const PROJECT = process.env.NOTIFIER_PROJECT ?? "your-project";

export type OwnerSeverity = "P0" | "P1" | "P2" | "info";

export function notifyOwner(
  severity: OwnerSeverity,
  title: string,
  opts: { body?: string; type?: string; dedupeKey?: string } = {},
): void {
  const url = process.env.NOTIFIER_URL;
  const key = process.env.NOTIFIER_KEY;
  if (!url || !key) return; // not configured → silent no-op

  void (async () => {
    try {
      await fetch(`${url.replace(/\/$/, "")}/notify`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Api-Key": key },
        body: JSON.stringify({
          project: PROJECT,
          severity,
          title,
          body: opts.body,
          type: opts.type,
          dedupeKey: opts.dedupeKey,
        }),
        signal: AbortSignal.timeout(2000),
      });
    } catch (err) {
      // Owner-alerting must never disturb the host app — log at debug and move on.
      log.debug("notifyOwner failed (non-fatal):", err instanceof Error ? err.message : String(err));
    }
  })();
}

/**
 * Uptime heartbeat → Notifier's missed-heartbeat watchdog (dead-man's switch).
 * Call on your own schedule (setInterval / cron) with the SAME name and
 * intervalMinutes every time; the watchdog alerts the owner when a beat goes
 * missing. Requires Notifier ≥ heartbeat-watchdog release — see the Notifier
 * watchdog contract.
 */
export function heartbeat(name: string, intervalMinutes: number): void {
  const url = process.env.NOTIFIER_URL;
  const key = process.env.NOTIFIER_KEY;
  if (!url || !key) return; // not configured → silent no-op

  void (async () => {
    try {
      await fetch(`${url.replace(/\/$/, "")}/heartbeat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Api-Key": key },
        body: JSON.stringify({ project: PROJECT, name, intervalMinutes }),
        signal: AbortSignal.timeout(2000),
      });
    } catch (err) {
      log.debug("heartbeat failed (non-fatal):", err instanceof Error ? err.message : String(err));
    }
  })();
}
