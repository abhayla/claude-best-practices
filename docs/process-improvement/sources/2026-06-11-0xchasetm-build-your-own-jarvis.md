Source: https://x.com/0xChaseTM/status/2065047339929047357
Captured: 2026-07-08

# 0xChaseTM — "How to Build Your Own J.A.R.V.I.S (Full Guide)"

Author: 0xChaseTM (@0xChaseTM) · https://x.com/0xChaseTM
Posted: 2026-06-11 · Engagement at capture: 422 likes · 59 retweets · 431,866 views
Nature: X-native long-form post (~4.4k chars), a 5-step DIY recipe for a local, always-on,
voice-activated personal assistant. Same author previously produced the already-captured
Boris/loop-engineering piece — this is a separate, consumer-facing "build your own AI" post,
not a continuation.

## Faithful summary

Thesis: "Tony Stark spent billions on JARVIS. You'll spend $4 a month." The entire build is one
Python file (`jarvis.py`) combining three parts — ears, brain, voice — wired together in a final
step.

**Step 1 — Get the keys.** Only the brain needs a paid key.
- Brain: Anthropic — console.anthropic.com, sign up, load ~$10 credit, copy an API key.
- Ears: free — openWakeWord (wake-word detection, ships its "Hey Jarvis" model inside the
  library, no account/key, runs locally).
- Voice: free — `edge-tts` (Microsoft neural voices, no account/key).
- Cost claim (author's, unverified): a few dozen commands/day ≈ $4/month, so $10 prepaid lasts
  ~2 months; pay-as-you-go is a hard ceiling.

**Step 2 — Ears.** openWakeWord listens locally for "Hey Jarvis"; on trigger, Whisper (`base`
model, ~150MB one-time download) transcribes the next ~5 seconds to text. Both run on-device —
"nothing leaves the room until you've actually spoken."

**Step 3 — Brain.** Sends the transcribed text + a persona system prompt + conversation history
to Claude. Author calls out swapping models: `claude-haiku-4-5` (cheap/fast) ↔
`claude-sonnet-4-6` (default) ↔ `claude-opus-4-8` (smartest) — the same three-tier cost/capability
ladder this hub's `model-routing.md` already codifies for its own dispatch decisions. History list
carries conversational memory across turns (session-only, no persistence layer described).

**Step 4 — Voice.** Claude's reply is sent to `edge-tts`. Author's specific tuning: voice
`en-GB-ThomasNeural`, `rate="-8%"`, `pitch="-6Hz"` — claimed to be what makes it sound like "the
operator from the film" rather than generic TTS.

**Step 5 — Wire together and run.** Set both keys (Anthropic + none needed for the free parts),
run the script; it loops: wake-word → listen → transcribe → Claude → speak. Keep it always-on by
leaving the terminal open or adding to login items.

**Closing framing:** "Building it is the trivial part" — the real edge is in *integrating* it with
calendar, codebase, and inbox once the loop exists; most people will stop at conversation.

## Relevance to this hub — LOW-to-MODERATE

| This post | Hub analogue | Note |
|---|---|---|
| "Ears + brain + voice" loop | tools + memory + loop framing (already captured, `2026-06-08-anatoli-kopadze-build-your-own-ai-agent.md`) | Same underlying "agent = structure around a model" idea, restated for a voice-first consumer assistant rather than a Telegram bot. Redundant at the concept level. |
| Model tiers: Haiku (cheap) / Sonnet (default) / Opus (complex) | `.claude/rules/model-routing.md` (haiku/sonnet/opus dispatch tiers) | Independent corroboration that the same 3-tier cost ladder is the mainstream default for personal-assistant builds, not just hub-internal dispatch. No action — already codified here. |
| Always-on local voice assistant (wake-word + local STT + cloud LLM + local TTS) | No hub analogue | Genuinely new modality vs. the hub's existing captures (which are text/chat or messaging-bot shaped). Nothing in the hub currently addresses a local always-listening voice loop — low priority since the hub has no voice-assistant project today. |
| "Connect it to your calendar/codebase/inbox" as the real value | `notifier-integration.md` (shared Notifier gateway) — only if this pattern ever grows an outward-alerting/messaging leg | This build is local voice I/O, not a WhatsApp/Telegram/email sender, so `notifier-integration.md` does not apply as-is. Flagging only as a forward pointer: if a future "voice JARVIS" project adds owner-facing notifications, it should route through the shared Notifier gateway rather than building a parallel sender — same as any other bot. |
| $4/month cost, model pricing table | — | **Unverified** author claim, not a hub-verified price; cross-check against the `claude-api` skill before quoting to anyone. |

**Honest action:** No hub pattern change warranted. The core "tools+memory+loop" agent framing is
already captured and institutionalized; the only non-redundant element (a local wake-word +
STT + TTS voice loop) has no current hub project to attach to, so there is nothing concrete to
generalize into a pattern yet. Revisit only if/when the hub or a downstream project actually builds
a voice-first assistant — at that point this post's model-tier and TTS-tuning details would be
directly reusable starting material.
