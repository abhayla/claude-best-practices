#!/usr/bin/env python3
"""yt_transcript.py - extract a full transcript from any YouTube video.

Strategy (first method that yields text wins):
  1. youtube-transcript-api : fast, clean; manual or auto captions
  2. yt-dlp subtitles       : manual subs, then auto-generated (VTT -> text);
                              succeeds on some tracks where method 1 hits the
                              YouTube PoToken block
  3. yt-dlp audio + Whisper : ASR fallback when a video has NO captions at all

stdout in --json mode contains ONLY the JSON object; all progress goes to stderr.

Usage:
  python yt_transcript.py <url-or-id> [--lang en] [--out FILE] [--json]
                          [--force-asr] [--asr-model base] [--meta]

Deps:  pip install yt-dlp youtube-transcript-api          # methods 1 & 2
       pip install faster-whisper   (+ ffmpeg on PATH)    # method 3 (ASR)
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

YT_ID_RE = re.compile(r"(?:v=|/shorts/|youtu\.be/|/embed/|/v/|/live/)([A-Za-z0-9_-]{11})")


def extract_video_id(url_or_id: str) -> str:
    s = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    m = YT_ID_RE.search(s)
    if m:
        return m.group(1)
    raise ValueError(f"Could not extract a video id from: {url_or_id!r}")


# ---------------------------------------------------------------- method 1
def via_transcript_api(video_id: str, lang: str):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None, "youtube-transcript-api not installed"
    # Support both the 1.x instance API and the legacy static API.
    try:
        api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id, languages=[lang, "en"])
        except Exception:
            fetched = api.fetch(video_id)
        snippets = list(fetched)
        text = " ".join(s.text for s in snippets if getattr(s, "text", "").strip())
        if text.strip():
            return text, "youtube-transcript-api"
    except Exception as e1:
        try:
            data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, "en"])
            text = " ".join(d["text"] for d in data if d.get("text", "").strip())
            if text.strip():
                return text, "youtube-transcript-api (legacy)"
        except Exception as e2:
            return None, f"transcript-api failed: {e1} | {e2}"
    return None, "transcript-api: empty"


# ---------------------------------------------------------------- VTT parse
def vtt_to_text(vtt: str) -> str:
    lines = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line or line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()  # strip inline <00:00:01.000>/<c> tags
        if line:
            lines.append(line)
    out = []  # de-duplicate consecutive repeats (auto-caption rolling lines)
    for ln in lines:
        if not out or out[-1] != ln:
            out.append(ln)
    return " ".join(out)


# ---------------------------------------------------------------- method 2
def via_ytdlp_subs(video_id: str, lang: str, workdir: Path):
    url = f"https://www.youtube.com/watch?v={video_id}"
    base = workdir / video_id
    cmd = [
        sys.executable, "-m", "yt_dlp", "--skip-download",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", f"{lang}.*,{lang},en.*,en",
        "--sub-format", "vtt", "-o", str(base), url,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    vtts = sorted(workdir.glob(f"{video_id}*.vtt"))
    manual = [v for v in vtts if ".auto." not in v.name and "-orig" not in v.name]
    for v in (manual or vtts):
        txt = vtt_to_text(v.read_text(encoding="utf-8", errors="ignore"))
        if txt.strip():
            kind = "manual" if v in manual else "auto"
            return txt, f"yt-dlp subtitles ({kind}: {v.name})"
    return None, f"yt-dlp: no usable subs (rc={p.returncode}) {p.stderr.strip()[-200:]}"


# ---------------------------------------------------------------- method 3
def via_ytdlp_asr(video_id: str, workdir: Path, model_name: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None, "faster-whisper not installed (ASR fallback unavailable)"
    url = f"https://www.youtube.com/watch?v={video_id}"
    audio = workdir / f"{video_id}.mp3"
    cmd = [
        sys.executable, "-m", "yt_dlp", "-x", "--audio-format", "mp3",
        "--audio-quality", "5", "-o", str(workdir / f"{video_id}.%(ext)s"), url,
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if not audio.exists():
        cand = [c for c in sorted(workdir.glob(f"{video_id}.*"))
                if c.suffix.lower() in (".mp3", ".m4a", ".webm", ".opus")]
        if not cand:
            return None, f"yt-dlp audio download failed (rc={p.returncode}) {p.stderr.strip()[-200:]}"
        audio = cand[0]
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio), beam_size=1)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    if text:
        return text, f"faster-whisper ASR (model={model_name}, lang={info.language})"
    return None, "ASR produced empty text"


# ---------------------------------------------------------------- metadata
def fetch_meta(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [sys.executable, "-m", "yt_dlp", "--skip-download", "--dump-single-json", url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return None
    try:
        j = json.loads(p.stdout)
    except Exception:
        return None
    return {
        "id": j.get("id"), "title": j.get("title"),
        "channel": j.get("channel") or j.get("uploader"),
        "duration_s": j.get("duration"), "upload_date": j.get("upload_date"),
        "view_count": j.get("view_count"),
        "description": (j.get("description") or "")[:500],
    }


def get_transcript(url_or_id, lang="en", force_asr=False, asr_model="base",
                   want_meta=False, workdir=None):
    video_id = extract_video_id(url_or_id)
    result = {"video_id": video_id, "transcript": None, "method": None, "attempts": []}
    if want_meta:
        result["meta"] = fetch_meta(video_id)

    tmp = Path(workdir or tempfile.mkdtemp(prefix="ytt_"))
    tmp.mkdir(parents=True, exist_ok=True)

    if not force_asr:
        for fn in (lambda: via_transcript_api(video_id, lang),
                   lambda: via_ytdlp_subs(video_id, lang, tmp)):
            text, note = fn()
            result["attempts"].append(note)
            if text:
                result["transcript"], result["method"] = text, note
                return result

    text, note = via_ytdlp_asr(video_id, tmp, asr_model)
    result["attempts"].append(note)
    if text:
        result["transcript"], result["method"] = text, note
    return result


def main():
    ap = argparse.ArgumentParser(description="Extract a YouTube transcript.")
    ap.add_argument("url")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--force-asr", action="store_true")
    ap.add_argument("--asr-model", default="base")
    ap.add_argument("--meta", action="store_true")
    args = ap.parse_args()

    for stream in (sys.stdout, sys.stderr):  # force UTF-8 so non-ASCII transcripts survive (Windows defaults to cp1252)
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    r = get_transcript(args.url, lang=args.lang, force_asr=args.force_asr,
                       asr_model=args.asr_model, want_meta=args.meta)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        m = r.get("meta")
        if m:
            print(f"# {m['title']}  [{m['channel']}, {m['duration_s']}s]\n")
        if r["transcript"]:
            print(f"[method: {r['method']}]  [chars: {len(r['transcript'])}]\n")
            print(r["transcript"])
        else:
            print(f"FAILED. attempts: {r['attempts']}", file=sys.stderr)
            sys.exit(2)

    if args.out and r["transcript"]:
        Path(args.out).write_text(r["transcript"], encoding="utf-8")
        print(f"\n[saved -> {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
