"""Tests for internet scanning and pattern extraction."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import pytest

from scripts.scan_web import (
    fetch_url,
    extract_code_blocks,
    is_source_expired,
    filter_by_trust_level,
)


class TestFetchUrl:
    @patch("scripts.scan_web.requests.get")
    def test_successful_fetch(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, text="<html>content</html>")
        result = fetch_url("https://example.com")
        assert result == "<html>content</html>"

    @patch("scripts.scan_web.requests.get")
    def test_404_returns_none(self, mock_get):
        mock_get.return_value = MagicMock(status_code=404)
        result = fetch_url("https://example.com/missing")
        assert result is None

    @patch("scripts.scan_web.requests.get")
    def test_timeout_returns_none(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        result = fetch_url("https://example.com/slow")
        assert result is None


class TestExtractCodeBlocks:
    def test_extracts_from_pre_code(self, sample_webpage):
        blocks = extract_code_blocks(sample_webpage)
        assert len(blocks) >= 2
        assert any("auto-retry" in b.lower() or "auto_retry" in b.lower() or "retry" in b.lower() for b in blocks)

    def test_empty_html_returns_empty(self):
        blocks = extract_code_blocks("<html><body>No code here</body></html>")
        assert len(blocks) == 0


class TestIsSourceExpired:
    def test_not_expired(self):
        source = {"last_verified": datetime.now().isoformat()[:10], "expires_after": "90d"}
        assert is_source_expired(source) is False

    def test_expired(self):
        old_date = (datetime.now() - timedelta(days=100)).isoformat()[:10]
        source = {"last_verified": old_date, "expires_after": "90d"}
        assert is_source_expired(source) is True


class TestFilterByTrustLevel:
    def test_filters_low_trust(self):
        sources = [
            {"url": "a.com", "trust_level": "high"},
            {"url": "b.com", "trust_level": "low"},
            {"url": "c.com", "trust_level": "medium"},
        ]
        filtered = filter_by_trust_level(sources, min_level="medium")
        assert len(filtered) == 2
        assert all(s["trust_level"] in ("high", "medium") for s in filtered)
