"""Scan internet sources for Claude Code best practices."""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
import yaml
from bs4 import BeautifulSoup


TRUST_LEVELS = {"high": 3, "medium": 2, "low": 1}


def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    """Fetch a URL and return its content. Returns None on failure."""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "ClaudeBestPracticesHub/1.0"
        })
        if resp.status_code != 200:
            return None
        return resp.text
    except Exception:
        return None


def extract_code_blocks(html: str) -> list[str]:
    """Extract code blocks from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        text = code.get_text() if code else pre.get_text()
        if text.strip():
            blocks.append(text.strip())
    return blocks


def is_source_expired(source: dict) -> bool:
    """Check if an internet source has expired."""
    last_verified = source.get("last_verified", "2000-01-01")
    expires_after = source.get("expires_after", "90d")

    match = re.match(r"(\d+)d", expires_after)
    if not match:
        return False
    days = int(match.group(1))

    try:
        verified_date = datetime.fromisoformat(last_verified)
    except ValueError:
        verified_date = datetime.strptime(last_verified, "%Y-%m-%d")

    return datetime.now() - verified_date > timedelta(days=days)


def filter_by_trust_level(sources: list[dict], min_level: str = "medium") -> list[dict]:
    """Filter sources by minimum trust level."""
    min_score = TRUST_LEVELS.get(min_level, 2)
    return [s for s in sources if TRUST_LEVELS.get(s.get("trust_level", "low"), 1) >= min_score]


def extract_patterns_from_content(content: str, source_url: str) -> list[dict]:
    """Extract potential patterns from page content."""
    blocks = extract_code_blocks(content)
    patterns = []

    for block in blocks:
        if "---" in block and ("name:" in block or "description:" in block):
            fm_match = re.search(r"---\s*\n(.*?)\n---", block, re.DOTALL)
            if fm_match:
                try:
                    fm = yaml.safe_load(fm_match.group(1))
                    if fm and "name" in fm:
                        patterns.append({
                            "name": fm["name"],
                            "type": "skill" if "allowed-tools" in fm else "agent",
                            "content": block,
                            "source_url": source_url,
                            "frontmatter": fm,
                        })
                except yaml.YAMLError:
                    pass

        if block.startswith("#!/bin/bash") or block.startswith("#!/usr/bin/env bash"):
            patterns.append({
                "name": "extracted-hook",
                "type": "hook",
                "content": block,
                "source_url": source_url,
                "frontmatter": {},
            })

    return patterns


def build_search_urls(topic: str) -> list[str]:
    """Build search URLs from a topic string or topic name from config.

    Accepts either:
      - A topic name matching config/topics.yml (e.g., "jetpack-compose-testing")
      - A free-text search query (e.g., "android kotlin claude code skills")

    Returns a list of URLs to scan (GitHub search, raw content pages).
    """
    root = Path(__file__).parent.parent
    urls = []

    # Check if topic matches a configured topic name
    topics_path = root / "config" / "topics.yml"
    keywords = []
    if topics_path.exists():
        with open(topics_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        for t in config.get("topics", []):
            if t.get("name") == topic:
                keywords = t.get("keywords", [])
                break

    # If no config match, treat the entire topic string as a keyword
    if not keywords:
        keywords = [topic]

    for kw in keywords:
        # GitHub code search — look for CLAUDE.md, SKILL.md, agents with these keywords
        query = kw.replace(" ", "+")
        urls.append(f"https://github.com/search?q={query}+path%3A.claude&type=code")
        urls.append(f"https://github.com/search?q={query}+SKILL.md&type=code")
        # GitHub repo search
        urls.append(f"https://github.com/search?q={query}&type=repositories")

    return urls


def scan_url(url: str) -> list[dict]:
    """Scan a single URL and return discovered patterns."""
    print(f"Scanning URL: {url}")
    content = fetch_url(url)
    if content:
        patterns = extract_patterns_from_content(content, url)
        print(f"  Found {len(patterns)} potential patterns")
        for p in patterns:
            print(f"    - {p['name']} ({p['type']}) from {p['source_url']}")
        return patterns
    else:
        print("  Failed to fetch URL")
        return []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan internet for best practices")
    parser.add_argument("--url", help="Specific URL to scan")
    parser.add_argument("--topic", help="Topic name (from config/topics.yml) or free-text search query")
    parser.add_argument("--all", action="store_true", help="Scan all from config")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    all_patterns = []

    if args.url:
        all_patterns = scan_url(args.url)
    elif args.topic:
        search_urls = build_search_urls(args.topic)
        print(f"Topic: {args.topic}")
        print(f"Generated {len(search_urls)} search URLs")
        for url in search_urls:
            all_patterns.extend(scan_url(url))
        print(f"\nTotal patterns found for topic '{args.topic}': {len(all_patterns)}")
    elif args.all:
        urls_path = root / "config" / "urls.yml"
        if urls_path.exists():
            with open(urls_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
            sources = config.get("urls", [])
            active = [s for s in sources if not is_source_expired(s)]
            active = filter_by_trust_level(active)
            print(f"Scanning {len(active)} active sources...")
            for source in active:
                all_patterns.extend(scan_url(source["url"]))
        # Also scan all configured topics
        topics_path = root / "config" / "topics.yml"
        if topics_path.exists():
            with open(topics_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            for t in config.get("topics", []):
                topic_name = t.get("name", "")
                print(f"\nScanning topic: {topic_name}")
                search_urls = build_search_urls(topic_name)
                for url in search_urls:
                    all_patterns.extend(scan_url(url))
        print(f"\nTotal patterns found: {len(all_patterns)}")
    else:
        print("Usage: scan_web.py --url URL | --topic TOPIC | --all")
