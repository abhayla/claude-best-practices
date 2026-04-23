"""Check freshness of internet sources and flag expired ones."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from scripts.scan_web import is_source_expired


def load_url_config(config_path: Path) -> list[dict]:
    """Load URLs from config/urls.yml."""
    if not config_path.exists():
        return []
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("urls", [])


def check_all_sources(sources: list[dict]) -> dict:
    """Check freshness of all sources. Returns report."""
    report = {"total": len(sources), "fresh": 0, "expired": 0, "expired_sources": []}
    for source in sources:
        if is_source_expired(source):
            report["expired"] += 1
            report["expired_sources"].append({
                "url": source.get("url"),
                "last_verified": source.get("last_verified"),
                "expires_after": source.get("expires_after"),
            })
        else:
            report["fresh"] += 1
    return report


def format_report(report: dict) -> str:
    """Format freshness report as readable text."""
    lines = [
        f"Source Freshness Report",
        f"Total: {report['total']}, Fresh: {report['fresh']}, Expired: {report['expired']}",
    ]
    if report["expired_sources"]:
        lines.append("\nExpired Sources:")
        for s in report["expired_sources"]:
            lines.append(f"  - {s['url']} (last verified: {s['last_verified']}, expires: {s['expires_after']})")
    return "\n".join(lines)


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    sources = load_url_config(root / "config" / "urls.yml")
    report = check_all_sources(sources)
    print(format_report(report))
    if report["expired"] > 0:
        sys.exit(1)
