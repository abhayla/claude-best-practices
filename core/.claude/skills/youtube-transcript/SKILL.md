---
name: youtube-transcript
description: Extract the full transcript (and optional metadata) of ANY YouTube video — short, long, or Shorts — given just its link. Tries clean captions first, falls back to yt-dlp subtitle download, and finally to audio + Whisper speech-to-text when a video has NO captions at all. Use whenever the user pastes a YouTube URL and wants the spoken content as text, or asks to summarize / analyze / search a video.
type: workflow
version: 1.0.0
allowed-tools: Bash, Read, Write
argument-hint: "<youtube-url> [--out file.txt] [--meta]"
---

# YouTube Transcript Extractor

Give it a YouTube link → get the full spoken text back. Handles any length and any URL
form (`watch?v=`, `youtu.be/`, `/shorts/`, `/live/`, or a bare 11-char id). The worker is
`yt_transcript.py` in this skill directory; the steps below drive it.

## STEP 1: Resolve the link and pick the output

Take the YouTube URL (or id) from the user. Decide where the text should go:
- to the chat → run plain (stdout),
- to a file → pass `--out <file>`. If the user asks for "filename = video name", first read
  the title (`--meta --json`), strip Windows-illegal characters `<>:"/\|?*`, and use that.
- **Save transcript files OUTSIDE the project's git tree** (e.g. a sibling `transcripts/`
  folder) so deliverables don't pollute the repo.

## STEP 2: Run the extractor

```bash
# clean text to stdout
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>"

# save to a file, include title/channel/duration
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>" --meta --out transcript.txt

# machine-readable: transcript + which method won + per-layer attempts
python .claude/skills/youtube-transcript/yt_transcript.py "<URL>" --json
```

Flags: `--lang en` (preferred caption language) · `--out FILE` · `--json` · `--meta` ·
`--force-asr` (skip captions, transcribe audio directly) · `--asr-model tiny|base|small|medium|large-v3`.

## STEP 3: Read the result and let the fallback chain work

Prefer `--json` when scripting: parse `transcript` and report the `method` used. The tool
tries three layers automatically, first that yields text wins:

1. **youtube-transcript-api** — fast, clean text; manual or auto captions. Primary.
2. **yt-dlp subtitles** — downloads the VTT track and de-duplicates it; succeeds on some
   tracks where layer 1 hits YouTube's PoToken block, with no extra services.
3. **yt-dlp audio + faster-whisper (ASR)** — only when a video has **no captions at all**.
   Downloads audio, runs local speech-to-text. This is the "do whatever it takes" layer
   that off-the-shelf YouTube-transcript MCP servers do **not** have.

If `transcript` is null, read `attempts` to see why each layer failed (e.g. blocked, no
subs, ASR package missing).

## STEP 4: Save and report

Write the file if requested (STEP 1 path), then report: the method that won, word/char
count, and the saved path. If you produced a deliverable file for the user, surface it.

## Setup (one-time)

```bash
pip install yt-dlp youtube-transcript-api   # layers 1 & 2
pip install faster-whisper                  # layer 3 (ASR); needs ffmpeg on PATH
```
Verified with: yt-dlp 2026.6.9, youtube-transcript-api 1.2.4, faster-whisper 1.2.1,
ffmpeg 8.1, Python 3.13. Output is forced to UTF-8 so non-English transcripts are not
corrupted on Windows (cp1252).

## Verified test results

| Video | Length | Method that won | Output |
|---|---|---|---|
| Me at the zoo (`jNQXAC9IVRw`) | 19 s | youtube-transcript-api | 39 words |
| Mind Field Ep1 (`/shorts/` URL) | 35 min | youtube-transcript-api | 4,072 words |
| Intro to LLMs (`zjkBMFhNj_g`) | 60 min | youtube-transcript-api | 12,151 words |
| Karpathy "build GPT" (`kCc8FmEb1nY`) | 116 min | youtube-transcript-api | 21,030 words |
| 3Blue1Brown neural nets (`aircAruvnKk`) | 19 min | yt-dlp subtitles (standalone) | 3,357 words |
| Gangnam Style, `--lang ko` (`9bZkp7q19f0`) | — | youtube-transcript-api | non-Latin UTF-8 intact |
| Kurzgesagt consciousness | 10 min | faster-whisper ASR (auto-fallback) | 1,401 words |

All three layers exercised independently and end-to-end.

## Gotchas & limits

- **Run from a residential / non-cloud IP.** YouTube blocks known cloud-provider IPs
  (AWS/GCP/Azure) for the caption endpoints; a cloud host needs a residential proxy or the
  yt-dlp PoToken plugin.
- **PoToken edge case.** Some caption tracks return an empty body to layer 1
  (youtube-transcript-api issue #592, no upstream fix). Layer 2 covers many of these; for
  the rest, install the [bgutil PoToken plugin](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide).
- **ASR cost is time, not money.** Fully local + free. A 2-hour video on CPU with `base` is
  slow — use `tiny`/`base` for speed, `small`+ for accuracy. ASR is imperfect (tiny rendered
  "trunks" as "prompts"); prefer captions when they exist.
- **No hard volume cap**, but YouTube temporarily rate-limits heavy bulk scraping from one
  IP — space requests out for hundreds of videos.

## Why this over an off-the-shelf MCP

Surveyed servers (`kimtaeyoon83`, `anaisbetts/mcp-youtube`, `jkawamoto`, `sinco-lab`) are
all **caption-only** — they error on videos with no captions. This skill's layer-3 ASR
fallback is what makes "get the transcript of *any* video" actually hold.
