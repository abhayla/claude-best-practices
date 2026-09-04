"""Tests for scripts/context_report.py. Uses only small fixture JSONL files under tmp_path -
never reads the real ~/.claude/projects/ tree."""

import json
import time
from pathlib import Path

from scripts import context_report as cr


def _line(**kwargs) -> str:
    return json.dumps(kwargs) + "\n"


def _usage_entry(model="claude-sonnet-5", input_tokens=100, cache_read=0, cache_creation=0, output=10, tool_names=None):
    content = []
    for name in tool_names or []:
        content.append({"type": "tool_use", "name": name})
    return {
        "message": {
            "role": "assistant",
            "model": model,
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_creation,
                "output_tokens": output,
            },
        }
    }


def _user_entry(text="Hello there, this is the first user message for the fixture transcript"):
    return {"message": {"role": "user", "content": text}}


def _write_transcript(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def test_is_subagent_path_detects_dir_and_prefix(tmp_path):
    assert cr.is_subagent_path(tmp_path / "session" / "subagents" / "whatever.jsonl")
    assert cr.is_subagent_path(tmp_path / "session" / "agent-xyz.jsonl")
    assert not cr.is_subagent_path(tmp_path / "session" / "main-transcript.jsonl")


def test_main_transcript_classified_as_main(tmp_path):
    projects_dir = tmp_path / "projects"
    transcript = projects_dir / "my-project" / "session1.jsonl"
    _write_transcript(transcript, [_user_entry(), _usage_entry(input_tokens=100)])

    stats: dict = {}
    summary = cr.read_transcript(transcript, projects_dir, stats)

    assert summary.kind == "main"
    assert summary.project == "my-project"
    assert summary.calls == 1
    assert summary.first_user_preview.startswith("Hello there")


def test_subagent_transcript_classified_as_sub(tmp_path):
    projects_dir = tmp_path / "projects"
    transcript = projects_dir / "my-project" / "session1" / "subagents" / "agent-1.jsonl"
    _write_transcript(transcript, [_usage_entry()])

    stats: dict = {}
    summary = cr.read_transcript(transcript, projects_dir, stats)

    assert summary.kind == "sub"
    assert summary.project == "my-project"


def test_prelude_share_arithmetic():
    # Two transcripts: first call context 1000 tokens x 3 calls = 3000; second: 500 x 2 = 1000.
    # Total input across all calls must equal the sum of every call's context (not just first).
    s1 = cr.TranscriptSummary(path="a", project="p", kind="main", calls=3, total_input=1000 + 200 + 200,
                               first_call_context=1000, last_call_context=200)
    s2 = cr.TranscriptSummary(path="b", project="p", kind="main", calls=2, total_input=500 + 100,
                               first_call_context=500, last_call_context=100)
    report = cr.build_report([s1, s2], top=20, stats={})

    expected_prelude = 1000 * 3 + 500 * 2
    expected_total_input = (1000 + 200 + 200) + (500 + 100)
    assert report["prelude_share"]["tokens"] == expected_prelude
    assert report["totals"]["total_input_tokens"] == expected_total_input
    assert report["prelude_share"]["pct_of_total_input"] == round(expected_prelude / expected_total_input * 100, 2)


def test_bucket_assignment():
    assert cr.histogram_bucket(0) == "<=20"
    assert cr.histogram_bucket(20) == "<=20"
    assert cr.histogram_bucket(21) == "21-60"
    assert cr.histogram_bucket(60) == "21-60"
    assert cr.histogram_bucket(61) == "61-150"
    assert cr.histogram_bucket(150) == "61-150"
    assert cr.histogram_bucket(151) == "151-400"
    assert cr.histogram_bucket(400) == "151-400"
    assert cr.histogram_bucket(401) == ">400"
    assert cr.histogram_bucket(5000) == ">400"


def test_subagent_histogram_only_counts_sub_transcripts():
    main_s = cr.TranscriptSummary(path="a", project="p", kind="main", calls=500, total_input=100)
    sub_s = cr.TranscriptSummary(path="b", project="p", kind="sub", calls=30, total_input=200)
    report = cr.build_report([main_s, sub_s], top=20, stats={})

    hist = report["subagent_histogram"]
    assert hist["21-60"]["count"] == 1
    assert hist["21-60"]["tokens"] == 200
    # the main transcript (500 calls) must not land in the >400 sub bucket
    assert hist[">400"]["count"] == 0


def test_malformed_line_is_skipped_and_counted(tmp_path):
    projects_dir = tmp_path / "projects"
    transcript = projects_dir / "proj" / "session.jsonl"
    transcript.parent.mkdir(parents=True)
    with open(transcript, "w", encoding="utf-8") as f:
        f.write(json.dumps(_usage_entry(input_tokens=50)) + "\n")
        f.write("{not valid json\n")
        f.write(json.dumps(_usage_entry(input_tokens=70)) + "\n")

    stats: dict = {}
    summary = cr.read_transcript(transcript, projects_dir, stats)

    assert stats["skipped_lines"] == 1
    assert summary.calls == 2
    assert summary.total_input == 120


def test_discover_transcripts_respects_mtime_window(tmp_path):
    projects_dir = tmp_path / "projects"
    fresh = projects_dir / "proj" / "fresh.jsonl"
    stale = projects_dir / "proj" / "stale.jsonl"
    _write_transcript(fresh, [_usage_entry()])
    _write_transcript(stale, [_usage_entry()])

    now = time.time()
    old_time = now - 30 * 86400
    import os
    os.utime(stale, (old_time, old_time))

    stats: dict = {}
    found = list(cr.discover_transcripts(projects_dir, since_ts=now - 7 * 86400, stats=stats))

    assert fresh in found
    assert stale not in found


def test_tool_call_counts_aggregate_across_transcripts(tmp_path):
    projects_dir = tmp_path / "projects"
    t1 = projects_dir / "proj" / "s1.jsonl"
    t2 = projects_dir / "proj" / "s2.jsonl"
    _write_transcript(t1, [_usage_entry(tool_names=["Bash", "Read"])])
    _write_transcript(t2, [_usage_entry(tool_names=["Bash"])])

    stats: dict = {}
    summaries = [
        cr.read_transcript(t1, projects_dir, stats),
        cr.read_transcript(t2, projects_dir, stats),
    ]
    report = cr.build_report(summaries, top=20, stats=stats)

    assert report["tool_call_counts"]["Bash"] == 2
    assert report["tool_call_counts"]["Read"] == 1


def test_json_shape_has_all_six_sections(tmp_path):
    projects_dir = tmp_path / "projects"
    transcript = projects_dir / "proj" / "s1.jsonl"
    _write_transcript(transcript, [_user_entry(), _usage_entry(model="claude-opus-5", tool_names=["Grep"])])

    stats: dict = {}
    summaries = [cr.read_transcript(transcript, projects_dir, stats)]
    report = cr.build_report(summaries, top=20, stats=stats)

    for key in (
        "totals",
        "prelude_share",
        "top_transcripts",
        "subagent_histogram",
        "tool_call_counts",
        "per_model_totals",
    ):
        assert key in report

    assert report["totals"]["transcripts"] == 1
    assert report["top_transcripts"][0]["project"] == "proj"
    assert "claude-opus-5" in report["per_model_totals"]
    assert report["tool_call_counts"]["Grep"] == 1

    # --json must serialize cleanly (no non-JSON types like Counter/dataclass leaking through)
    json.dumps(report)


def test_collect_summaries_end_to_end(tmp_path):
    projects_dir = tmp_path / "projects"
    _write_transcript(projects_dir / "proj" / "main.jsonl", [_user_entry(), _usage_entry(input_tokens=100)])
    _write_transcript(
        projects_dir / "proj" / "sess" / "subagents" / "agent-1.jsonl",
        [_usage_entry(input_tokens=50, model="claude-haiku-4")],
    )

    stats: dict = {}
    summaries = cr.collect_summaries(projects_dir, days=7, stats=stats)

    kinds = {s.kind for s in summaries}
    assert kinds == {"main", "sub"}
    assert len(summaries) == 2
