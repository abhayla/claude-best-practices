Source: https://code.claude.com/docs/en/model-config
Fetched: 2026-06-27

# Model configuration

> Learn about the Claude Code model configuration, including model aliases like `opusplan`

## Available models

For the `model` setting in Claude Code, configure either a **model alias** or a **model name** (Anthropic API: full model name; Bedrock: inference profile ARN; Foundry: deployment name; Vertex: version name).

> **Note:** `ANTHROPIC_BASE_URL` changes where requests are sent, not which model answers them.

### Model aliases

| Alias | Behavior |
| --- | --- |
| `default` | Clears any override → recommended model for your account type |
| `best` | Fable 5 where available, else latest Opus |
| `fable` | Claude Fable 5 — hardest/longest-running tasks |
| `sonnet` | Latest Sonnet — daily coding |
| `opus` | Latest Opus — complex reasoning |
| `haiku` | Fast/efficient Haiku — simple tasks |
| `sonnet[1m]` / `opus[1m]` | 1M-token context window for long sessions |
| `opusplan` | `opus` during plan mode, then `sonnet` for execution |

On the Anthropic API, `opus` → Opus 4.8, `sonnet` → Sonnet 4.6. On Claude Platform on AWS, `opus` → Opus 4.7. On Bedrock/Vertex/Foundry, `opus` → Opus 4.6, `sonnet` → Sonnet 4.5 (newer via full ID or `ANTHROPIC_DEFAULT_*_MODEL`). Pin with a full name (`claude-opus-4-8`) or the env var. Opus 4.8 requires v2.1.154+.

### Work with Fable 5

Fable 5 is the most capable model in Claude Code, for tasks larger than a single sitting — sustains long autonomous sessions, investigates before acting, verifies more. Not the default; select with `/model fable`. To get the most from it: describe the OUTCOME not the steps (and **to keep it working until that outcome holds, set a goal — `/goal`**); hand it ambiguous problems; skip verification reminders; size up larger tasks. Requires v2.1.170+. Safety-classifier-flagged requests (cybersecurity/biology) trigger automatic model fallback to Opus.

### Setting your model

Priority order: (1) `/model <alias|name>` during session (saves as default for new sessions as of v2.1.153; `s` = this-session-only); (2) `claude --model` at startup; (3) `ANTHROPIC_MODEL` env var; (4) `model` field in settings. Project/managed settings take precedence and reapply next launch. `--model`/`ANTHROPIC_MODEL` apply only to the launched session. Resumed sessions keep their saved model.

## Restrict model selection

Enterprise admins use `availableModels` in managed/policy settings to restrict selectable models (matches family `sonnet`, version prefix `claude-sonnet-4-5`, or full ID). Applies to main session, alias resolution, fast mode, subagent models, skill/command models, advisor model, background-agent model. `enforceAvailableModels: true` (v2.1.175+) extends the allowlist to the Default option. Organization model restrictions (Console toggle, v2.1.187+) apply server-side, separately from `availableModels`; both apply together.

## Special model behavior

### `default` model setting (by account type)
- Max, Team Premium, Enterprise pay-as-you-go, Anthropic API → Opus 4.8
- Claude Platform on AWS → Opus 4.7
- Pro, Team Standard, Enterprise subscription seats → Sonnet 4.6
- Bedrock, Vertex, Foundry → Sonnet 4.5

### `opusplan`
Plan mode → `opus`; execution → `sonnet`. Plan-mode Opus uses the same context window as `opus` (1M on auto-upgrade tiers; `opusplan[1m]` forces 1M). When `availableModels` excludes Opus, stays on Sonnet in plan mode.

### Fallback model chains (availability-based)
On overload/unavailable/non-retryable server error, switch to a fallback model. Set via `--fallback-model sonnet,haiku` or `fallbackModel` array in settings. Capped at 3 after dedup. Switch lasts the current turn only. Auth/billing/rate-limit/size/transport errors never trigger.

### Automatic model fallback (content-based, from Fable 5)
Fable 5 runs safety classifiers (cybersecurity/biology). A flagged request re-runs on default Opus (4.8 on Anthropic API / 4.7 on AWS) with a transcript notice; session continues on Opus. Can trigger on the FIRST request (workspace context: CLAUDE.md + git status). Check via `claude --safe-mode` (disables CLAUDE.md/skills/MCP/hooks). `/config` → turn off "switch models when a message is flagged" to be asked each time. Headless: a flagged request ends the turn with a refusal.

### Adjust effort level

[Effort levels](https://platform.claude.com/docs/en/build-with-claude/effort) control adaptive reasoning.

| Model | Levels |
| --- | --- |
| Fable 5 | low, medium, high, xhigh, max |
| Opus 4.8 / Opus 4.7 | low, medium, high, xhigh, max |
| Opus 4.6 / Sonnet 4.6 | low, medium, high, max |

Default effort: `high` on Fable 5 / Opus 4.8 / Opus 4.6 / Sonnet 4.6; `xhigh` on Opus 4.7. `low/medium/high/xhigh` persist; `max` is session-only (deepest reasoning, no token constraint, prone to overthinking). Set via `/effort`, `/model` slider, `--effort`, `CLAUDE_CODE_EFFORT_LEVEL`, `effortLevel` setting, or skill/subagent frontmatter `effort:`. Env var > configured level > model default.

**`ultracode`** — a Claude Code SETTING (not a model effort level) offered in the `/effort` menu: sends `xhigh` to the model AND has Claude orchestrate **dynamic workflows** (`/en/workflows`) for substantive tasks. Session-only. Set via `/effort` or `"ultracode": true` via `--settings` / Agent SDK. Not part of `effortLevel`/`--effort`/`CLAUDE_CODE_EFFORT_LEVEL`.

**`ultrathink`** — include anywhere in a prompt for deeper one-off reasoning without changing the session effort (adds an in-context instruction; API effort unchanged). "think"/"think hard"/"think more" are ordinary prompt text, not keywords.

### Extended thinking
Toggle `Option/Alt+T`; global default via `/config` (`alwaysThinkingEnabled`); `MAX_THINKING_TOKENS=0` disables (except Fable 5, which always thinks). Thinking collapsed by default; `Ctrl+O` verbose. Charged for all thinking tokens.

### Extended context (1M)
Fable 5, Opus 4.6+, Sonnet 4.6 support a 1M-token window. Max/Team/Enterprise auto-upgrade Opus to 1M; Anthropic API Fable 5 / Opus 4.8 / Opus 4.7 always 1M. Sonnet 1M needs usage credits. Disable with `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. `[1m]` suffix works on aliases/full names. No premium for tokens beyond 200K.

## Environment variables (model aliases)

| Env var | Description |
| --- | --- |
| `ANTHROPIC_DEFAULT_FABLE_MODEL` | Model for `fable`; the ID recognized as Fable 5 for content-fallback on 3rd-party providers |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Model for `opus` (and `opusplan` in plan mode) |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Model for `sonnet` (and `opusplan` outside plan mode) |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Model for `haiku`, OR **background functionality** (the small fast model). `ANTHROPIC_SMALL_FAST_MODEL` is DEPRECATED in favor of this |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Model for all subagents + agent teams. Overrides per-invocation `model` and definition frontmatter; `inherit` for normal resolution |

Other sections (3rd-party pinning, `modelOverrides`, capability declaration, prompt-caching disable flags `DISABLE_PROMPT_CACHING[_HAIKU/_SONNET/_OPUS/_FABLE]`) omitted here as not loop/goal-relevant — see source URL for full detail.

**Hub relevance (loop/goal framework):** The two facts that matter for autonomous loops — (1) the **`/goal` evaluator and the auto-mode classifier run on a server-configured "small fast model" independent of `/model`** (the evaluator defaults to **Haiku**, configurable via `ANTHROPIC_DEFAULT_HAIKU_MODEL`; the deprecated `ANTHROPIC_SMALL_FAST_MODEL` is its old name) — so evaluator cost is "typically negligible vs main-turn spend," and (2) **Fable 5 is the model Anthropic explicitly pairs with `/goal`** ("describe the outcome… to keep it working until it holds, set a goal"). Also note **`ultracode`** here = the hub's Workflow-tool orchestration trigger (`/en/workflows`), relevant to the hub's measured skill-at-T0-vs-Workflow A/B. Auto-mode model floors (Opus 4.6+/Sonnet 4.6) are restated in `permission-modes.md`.
