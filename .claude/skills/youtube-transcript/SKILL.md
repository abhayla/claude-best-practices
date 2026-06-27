---
name: youtube-transcript
description: Extract the full transcript (and optional metadata) of ANY YouTube video — short, long, or Shorts — given just its link. Tries clean captions first, falls back to yt-dlp subtitle download, and finally to audio + Whisper speech-to-text when a video has NO captions at all. Use whenever the user pastes a YouTube URL and wants the spoken content as text, or asks to summarize / analyze / search a video.
triggers:
  - youtube transcript
  - transcript of this video
  - what does this video say
  - summarize this youtube
  - get the captions
---

# YouTube Transcript Extractor

Give it a YouTube link → get the full spoken text back. Handles any length and any
URL form (`watch?v=`, `youtu.be/`, `/shorts/`, `/live/`, or a bare 11-char id).

## How to run it

The worker is `yt_transcript.py` in this skill directory. From the repo root:

```bash
# Plain text to stdout
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>"

# Save to a file + include title/channel/duration
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>" --meta --out transcript.txt

# Machine-readable (transcript + which method succeeded + attempts)
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>" --json
```

Flags: `--lang en` (preferred caption language) · `--out FILE` · `--json` · `--meta`
· `--force-asr` (skip captions, transcribe audio directly) · `--asr-model tiny|base|small|medium|large-v3`.

When invoked as a skill, run it with `--json`, parse the `transcript` field, and report
the `method` used. If `transcript` is null, read `attempts` to see why each layer failed.

## The fallback chain (first that yields text wins)

1. **youtube-transcript-api** — fast, clean text; manual or auto captions. Primary.
2. **yt-dlp subtitles** — downloads the VTT track and de-duplicates it. Succeeds on some
   tracks where layer 1 hits YouTube's PoToken block, and needs no extra services.
3. **yt-dlp audio + faster-whisper (ASR)** — only when a video has **no captions at all**.
   Downloads audio, runs local speech-to-text. This is the "do whatever it takes" layer
   that off-the-shelf YouTube-transcript MCP servers do **not** have.

## Setup (one-time)

```bash
pip install yt-dlp youtube-transcript-api   # layers 1 & 2
pip install faster-whisper                  # layer 3 (ASR); needs ffmpeg on PATH
```
Verified working with: yt-dlp 2026.6.9, youtube-transcript-api 1.2.4, faster-whisper 1.2.1,
ffmpeg 8.1, Python 3.13.

## Verified test results (2026-06-27)

| Video | Length | Method that won | Output |
|---|---|---|---|
| Me at the zoo (`jNQXAC9IVRw`) | 19 s | youtube-transcript-api | 39 words |
| Mind Field Ep1 (`/shorts/` URL) | 35 min | youtube-transcript-api | 4,072 words |
| Intro to LLMs (`zjkBMFhNj_g`) | 60 min | youtube-transcript-api | 12,151 words |
| Karpathy "build GPT" (`kCc8FmEb1nY`) | 116 min | youtube-transcript-api | 21,030 words |
| 3Blue1Brown neural nets (`aircAruvnKk`) | 19 min | yt-dlp subtitles (standalone) | 3,357 words |
| Gangnam Style, `--lang ko` (`9bZkp7q19f0`) | — | youtube-transcript-api | non-Latin UTF-8 intact |
| Me at the zoo, `--force-asr` | 19 s | faster-whisper ASR | full chain (audio→ffmpeg→text) |

All three layers exercised independently and end-to-end.

## Gotchas & limits (from research + testing)

- **Run from a residential / non-cloud IP.** YouTube blocks known cloud-provider IPs
  (AWS/GCP/Azure) for the caption endpoints. This machine (residential) works directly;
  a cloud host needs a residential proxy or the yt-dlp PoToken plugin.
- **PoToken edge case.** Some caption tracks return an empty body to layer 1
  (youtube-transcript-api issue #592, no upstream fix). The yt-dlp layer covers many of
  these; for the rest, install the [bgutil PoToken plugin](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide).
- **ASR cost is time, not money.** It's fully local (free). A 2-hour video on a CPU with the
  `base` model is slow — use `tiny`/`base` for speed, `small`+ for accuracy. ASR output is
  imperfect (e.g. tiny rendered "trunks" as "prompts"); prefer captions when they exist.
- **Output is always UTF-8** (the script reconfigures stdout) so non-English transcripts
  are not corrupted on Windows.

## Why this over an off-the-shelf MCP

Surveyed servers (`kimtaeyoon83`, `anaisbetts/mcp-youtube`, `jkawamoto`, `sinco-lab`) are
all **caption-only** — they error on videos with no captions. This skill's layer-3 ASR
fallback is what makes "get me the transcript of *any* video" actually hold. If you later
want a always-on MCP tool surface instead of a script, `anaisbetts/mcp-youtube` (yt-dlp
backed) is the closest off-the-shelf option to wrap.
