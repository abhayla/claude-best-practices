Source: https://code.claude.com/docs/en/auto-mode-config
Fetched: 2026-06-27

# Configure auto mode

> Tell the auto mode classifier which repos, buckets, and domains your organization trusts. Set environment context, override the default block and allow rules, and inspect your effective config with the auto-mode CLI subcommands.

[Auto mode](/en/permission-modes#eliminate-prompts-with-auto-mode) lets Claude Code run without routine permission prompts by routing tool calls through a classifier that blocks anything irreversible, destructive, or aimed outside your environment. Deny and explicit ask rules are evaluated before the classifier and still block or prompt. Use the `autoMode` settings block to tell that classifier which repos, buckets, and domains your organization trusts, so it stops blocking routine internal operations.

> **Note:** Auto mode is available to all users on the Anthropic API. On Amazon Bedrock, Google Cloud Vertex AI, and Microsoft Foundry, you must first set `CLAUDE_CODE_ENABLE_AUTO_MODE`. If Claude Code reports auto mode as unavailable for your account, check the full requirements (supported models and Owner enablement on Team and Enterprise plans).

By default, the classifier trusts only the working directory and the current repo's configured remotes. Actions like pushing to your company's source-control org or writing to a team cloud bucket are blocked until you add them to `autoMode.environment`.

## Where the classifier reads configuration

The classifier reads the same CLAUDE.md content Claude itself loads, so an instruction like "never force push" in your project's CLAUDE.md steers both Claude and the classifier at the same time.

For rules that apply across projects (trusted infrastructure or organization-wide deny rules), use the `autoMode` settings block. Scopes read:

| Scope | File | Use for |
| :--- | :--- | :--- |
| One developer | `~/.claude/settings.json` | Personal trusted infrastructure |
| One project, one developer | `.claude/settings.local.json` | Per-project trusted buckets/services |
| Organization-wide | Managed settings | Trusted infrastructure for all developers |
| `--settings` flag or Agent SDK | Inline JSON | Per-invocation overrides for automation |

The classifier does NOT read `autoMode` from shared project settings in `.claude/settings.json`, so a checked-in repo can't inject its own allow rules. Entries from each scope are combined; a developer can extend `environment`/`allow`/`soft_deny`/`hard_deny` but can't remove managed-settings entries. A developer-added `allow` can override an org `soft_deny` (additive, not a hard policy boundary).

> **Note:** The classifier is a second gate that runs AFTER the permissions system. For actions that must never run regardless of intent or classifier config, use `permissions.deny` in managed settings, which blocks before the classifier and can't be overridden.

## Define trusted infrastructure

`autoMode.environment` tells the classifier which repos, buckets, and domains are trusted; anything not listed is a potential exfiltration target. Include the literal `"$defaults"` to keep the built-in environment list (working repo + configured remotes). Entries are prose (natural-language), not regex. A thorough environment section covers: Organization; Source control; Cloud providers & trusted buckets; Trusted internal domains; Key internal services; Additional context (compliance, multi-tenant).

```json
{
  "autoMode": {
    "environment": [
      "$defaults",
      "Source control: github.example.com/acme-corp and all repos under it",
      "Trusted cloud buckets: s3://acme-build-artifacts, gs://acme-ml-datasets",
      "Trusted internal domains: *.corp.example.com, api.internal.example.com",
      "Key internal services: Jenkins at ci.example.com, Artifactory at artifacts.example.com"
    ]
  }
}
```

## Override the block and allow rules

Three additional fields replace the classifier's built-in rule lists:
- `autoMode.hard_deny`: unconditional security boundaries
- `autoMode.soft_deny`: destructive actions that user intent can clear
- `autoMode.allow`: exceptions to soft block rules

Precedence (four tiers, inside the classifier):
1. `hard_deny` blocks unconditionally — user intent and `allow` don't apply.
2. `soft_deny` blocks next — user intent and `allow` can override.
3. `allow` overrides matching `soft_deny` as exceptions.
4. Explicit user intent overrides remaining soft blocks IF the user's message directly and specifically describes the exact action. General requests ("clean up the repo") do NOT count; "force-push this branch" does.

Include `"$defaults"` to keep built-in rules while adding your own (and continue inheriting updates).

> **Danger:** Setting any of `environment`/`allow`/`soft_deny`/`hard_deny` WITHOUT `"$defaults"` replaces the entire default list for that section — discarding built-ins like force-push, `curl|bash`, production-deploy soft blocks, and the data-exfiltration / auto-mode-bypass hard blocks.

## Inspect the defaults and your effective config

```bash
claude auto-mode defaults   # print built-in environment/allow/soft_deny/hard_deny as JSON
claude auto-mode config     # print what the classifier actually uses (your settings + defaults)
claude auto-mode critique   # AI feedback on your custom allow/soft_deny/hard_deny rules
```

## Review denials

Denials are recorded in `/permissions` → Recently denied. Press `r` to mark for retry. Repeated denials for the same destination usually mean missing context → add it to `autoMode.environment`. To react programmatically, use the `PermissionDenied` hook.

**Hub relevance:** This is the configuration surface behind the hub's S7 Auto-mode policy (`decision-authority.md`) — autonomous `/goal`/`/loop`/routine runs default to `--permission-mode auto`. The four-tier precedence (hard_deny > soft_deny > allow > explicit-intent) and the "$defaults"-or-replace-entirely gotcha matter when a downstream project codifies its trusted infra. The classifier reading CLAUDE.md is why hub deny-intent in CLAUDE.md steers it too. Note the separation: `permissions.deny` (hard, pre-classifier) vs `autoMode.*` (classifier tier).
