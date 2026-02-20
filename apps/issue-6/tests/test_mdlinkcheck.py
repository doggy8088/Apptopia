"""Test suite for mdlinkcheck."""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import urllib.error
import socket

from mdlinkcheck.scanner import MarkdownScanner, Link
from mdlinkcheck.checker import LinkChecker
from mdlinkcheck.config import Config


class TestMarkdownScanner:
    """Tests for MarkdownScanner."""
    
    def test_extract_links_basic(self):
        """Test basic link extraction."""
        scanner = MarkdownScanner(".")
        content = """
# Test Document

[External Link](https://example.com)
[Relative Link](./docs/setup.md)
[Anchor Link](#introduction)
"""
        links = scanner._extract_links(content)
        
        assert len(links) == 3
        assert links[0].url == "https://example.com"
        assert links[0].link_type == "http"
        assert links[1].url == "./docs/setup.md"
        assert links[1].link_type == "relative"
        assert links[2].url == "#introduction"
        assert links[2].link_type == "anchor"
    
    def test_ignore_code_blocks(self):
        """Test that links in code blocks are ignored."""
        scanner = MarkdownScanner(".")
        content = """
# Test

This is a [valid link](https://example.com).

```
This is [ignored link](https://ignored.com) in code block.
```

This is another `[inline code](https://ignored.com)`.

    Indented code [also ignored](https://ignored.com)

[Another valid link](https://example.org)
"""
        links = scanner._extract_links(content)
        
        # Should only find the two valid links
        assert len(links) == 2
        assert links[0].url == "https://example.com"
        assert links[1].url == "https://example.org"
    
    def test_reference_style_links(self):
        """Test extraction of reference-style links."""
        scanner = MarkdownScanner(".")
        content = """
# Test

[link text][ref1]

[ref1]: https://example.com
"""
        links = scanner._extract_links(content)
        
        # Should find the reference definition
        assert any(link.url == "https://example.com" for link in links)
    
    def test_classify_link(self):
        """Test link classification."""
        scanner = MarkdownScanner(".")
        
        assert scanner._classify_link("https://example.com") == "http"
        assert scanner._classify_link("http://example.com") == "http"
        assert scanner._classify_link("./docs/file.md") == "relative"
        assert scanner._classify_link("../README.md") == "relative"
        assert scanner._classify_link("#heading") == "anchor"
        assert scanner._classify_link("/posts/article") == "internal"
    
    def test_line_numbers_with_code_blocks(self):
        """Test that line numbers are accurate even with code blocks."""
        scanner = MarkdownScanner(".")
        content = """Line 1
Line 2: [Link1](https://example1.com)
Line 3
Line 4: ```
Line 5: code
Line 6: more code
Line 7: ```
Line 8
Line 9: [Link2](https://example2.com)
Line 10"""
        
        links = scanner._extract_links(content)
        
        # Should find 2 links with correct line numbers
        assert len(links) == 2
        assert links[0].line_number == 2
        assert links[0].url == "https://example1.com"
        assert links[1].line_number == 9
        assert links[1].url == "https://example2.com"

    def test_extract_links_with_parentheses_in_url(self):
        """Test that URLs containing parentheses are extracted correctly."""
        scanner = MarkdownScanner(".")
        content = """
# Test

[Wikipedia](https://en.wikipedia.org/wiki/Entropy_(information_theory))
[Another](https://example.com/page_(version_2))
[Nested](https://example.com/func_(a_(b)))
[Multiple links](url1) and [another](url2) on same line
"""
        links = scanner._extract_links(content)
        
        assert len(links) == 5
        assert links[0].url == "https://en.wikipedia.org/wiki/Entropy_(information_theory)"
        assert links[1].url == "https://example.com/page_(version_2)"
        assert links[2].url == "https://example.com/func_(a_(b))"
        assert links[3].url == "url1"
        assert links[4].url == "url2"
    
    def test_url_length_limit(self):
        """Test that URLs exceeding MAX_URL_LENGTH are not extracted (DoS protection)."""
        scanner = MarkdownScanner(".")
        
        # Create a URL that exceeds the limit
        long_url = "https://example.com/" + "a" * 3000
        content = f"[Link with too long URL]({long_url})"
        
        links = scanner._extract_links(content)
        
        # Should not extract the URL that exceeds the limit
        assert len(links) == 0
    
    def test_url_at_limit_boundary(self):
        """Test URL extraction at the length limit boundary."""
        scanner = MarkdownScanner(".")
        
        # Create a URL just under the limit
        url_base = "https://example.com/"
        remaining_length = scanner.MAX_URL_LENGTH - len(url_base) - 1
        valid_url = url_base + "a" * remaining_length
        
        content = f"[Valid long URL]({valid_url})"
        links = scanner._extract_links(content)
        
        # Should extract the URL within the limit
        assert len(links) == 1
        assert links[0].url == valid_url

class TestLinkChecker:
    """Tests for LinkChecker."""
    
    def test_heading_to_anchor(self):
        """Test heading to anchor conversion."""
        checker = LinkChecker()
        
        # Basic conversion
        assert checker._heading_to_anchor("Installation") == "installation"
        assert checker._heading_to_anchor("Getting Started") == "getting-started"
        
        # Special characters
        assert checker._heading_to_anchor("API Reference (v2)") == "api-reference-v2"
        assert checker._heading_to_anchor("What's New?") == "whats-new"
        
        # Multiple spaces and hyphens
        assert checker._heading_to_anchor("This   has   spaces") == "this-has-spaces"
        assert checker._heading_to_anchor("Already-has-hyphens") == "already-has-hyphens"
        
        # Markdown formatting
        assert checker._heading_to_anchor("**Bold** and *italic*") == "bold-and-italic"
        assert checker._heading_to_anchor("`Code` in heading") == "code-in-heading"
    
    def test_extract_headings(self):
        """Test heading extraction."""
        checker = LinkChecker()
        content = """
# Main Title

Some text

## Section One

More text

### Subsection

```
# Not a heading
## Also not a heading
```

## Section Two
"""
        headings = checker._extract_headings(content)
        
        assert len(headings) == 4
        assert "Main Title" in headings
        assert "Section One" in headings
        assert "Subsection" in headings
        assert "Section Two" in headings
        assert "Not a heading" not in headings
    
    def test_check_relative_link_exists(self, tmp_path):
        """Test checking relative links that exist."""
        # Create test files
        readme = tmp_path / "README.md"
        readme.write_text("# Test")
        assert readme.exists()  # Verify file creation
        
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        setup_md = docs_dir / "setup.md"
        setup_md.write_text("# Setup")
        assert setup_md.exists()  # Verify file creation
        
        checker = LinkChecker()
        link = Link(url="./docs/setup.md", line_number=1, link_type="relative")
        
        result = checker._check_relative_link(link, "README.md", tmp_path)
        
        assert result.status == "ok"
    
    def test_check_relative_link_missing(self, tmp_path):
        """Test checking relative links that don't exist."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test")
        assert readme.exists()  # Verify file creation
        
        checker = LinkChecker()
        link = Link(url="./missing.md", line_number=1, link_type="relative")
        
        result = checker._check_relative_link(link, "README.md", tmp_path)
        
        assert result.status == "broken"
        assert "not found" in result.message
    
    def test_check_anchor_valid(self):
        """Test checking valid anchor links."""
        checker = LinkChecker()
        content = """
# Installation

This is a guide.

## Prerequisites

Need these things.
"""
        
        # Test valid anchors
        link1 = Link(url="#installation", line_number=1, link_type="anchor")
        result1 = checker._check_anchor_link(link1, content)
        assert result1.status == "ok"
        
        link2 = Link(url="#prerequisites", line_number=2, link_type="anchor")
        result2 = checker._check_anchor_link(link2, content)
        assert result2.status == "ok"
    
    def test_check_anchor_invalid_with_suggestion(self):
        """Test checking invalid anchor with suggestion."""
        checker = LinkChecker()
        content = """
# Installation

Follow these steps.
"""
        
        # Typo in anchor
        link = Link(url="#installatoin", line_number=1, link_type="anchor")
        result = checker._check_anchor_link(link, content)
        
        assert result.status == "broken"
        assert "not found" in result.message
        assert "installation" in result.suggestion.lower()
    
    def test_find_similar_anchor(self):
        """Test finding similar anchors."""
        checker = LinkChecker()
        
        valid_anchors = ["installation", "getting-started", "configuration", "troubleshooting"]
        
        # Close match
        suggestion = checker._find_similar_anchor("instalation", valid_anchors)
        assert "installation" in suggestion
        
        # Another close match
        suggestion = checker._find_similar_anchor("geting-started", valid_anchors)
        assert "getting-started" in suggestion
        
        # No close match
        suggestion = checker._find_similar_anchor("xyz", valid_anchors)
        assert suggestion == ""
    
    @patch('urllib.request.urlopen')
    def test_http_link_timeout(self, mock_urlopen):
        """Test that HTTP link timeout is properly handled as warning."""
        checker = LinkChecker()
        link = Link(url="http://example.com", line_number=1, link_type="http")
        
        # Mock: Simulate timeout wrapped in URLError (never makes real request)
        mock_urlopen.side_effect = urllib.error.URLError(socket.timeout())
        
        result = checker._check_http_link(link)
        
        assert result.status == "warning"
        assert result.message == "timeout"
        assert result.status_code == 0

    def test_check_internal_link_skipped(self, tmp_path):
        """Test that internal site paths are always skipped."""
        # Internal links like /posts/xxx depend on framework routing
        # and cannot be reliably verified by file existence checks
        
        checker = LinkChecker()
        
        # Test various internal link patterns
        test_links = [
            "/posts/article-name",      # Blog post style
            "/api/users",                # API endpoint style
            "/docs/guide/setup",         # Nested path
        ]
        
        for url in test_links:
            link = Link(url=url, line_number=1, link_type="internal")
            result = checker._check_internal_link(link)
            
            # All internal links should be marked as ok (skipped)
            assert result.status == "ok"

    @patch('urllib.request.urlopen')
    def test_http_link_head_403_cloudflare_no_fallback(self, mock_urlopen):
        """Test that HEAD 403 with Cloudflare Challenge does NOT fall back to GET."""
        checker = LinkChecker()
        link = Link(url="http://example.com", line_number=1, link_type="http")
        
        # Mock: HEAD returns 403 with Cloudflare Challenge headers
        error = urllib.error.HTTPError(
            "http://example.com", 
            403, 
            "Forbidden", 
            {'cf-mitigated': 'challenge', 'Server': 'cloudflare'}, 
            None
        )
        mock_urlopen.side_effect = error
        
        result = checker._check_http_link(link)
        
        assert result.status == "warning"
        assert result.status_code == 403
        assert result.message == "cloudflare challenge"
        assert mock_urlopen.call_count == 1  # Only HEAD, no GET fallback

    @patch('urllib.request.urlopen')
    def test_http_link_head_403_fallback_to_get(self, mock_urlopen):
        """Test that HEAD 403 falls back to GET request."""
        checker = LinkChecker()
        link = Link(url="http://example.com", line_number=1, link_type="http")
        
        # Mock: HEAD returns 403, GET returns 200
        def side_effect(request, timeout):
            if request.method == "HEAD":
                raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)
            else:  # GET request
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                return mock_response
        
        mock_urlopen.side_effect = side_effect
        
        result = checker._check_http_link(link)
        
        assert result.status == "ok"
        assert result.status_code == 200
        assert mock_urlopen.call_count == 2  # HEAD + GET

    @patch('urllib.request.urlopen')
    def test_http_link_head_405_fallback_to_get(self, mock_urlopen):
        """Test that HEAD 405 falls back to GET request."""
        checker = LinkChecker()
        link = Link(url="http://example.com", line_number=1, link_type="http")
        
        # Mock: HEAD returns 405, GET returns 200
        def side_effect(request, timeout):
            if request.method == "HEAD":
                raise urllib.error.HTTPError(request.full_url, 405, "Method Not Allowed", {}, None)
            else:  # GET request
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                return mock_response
        
        mock_urlopen.side_effect = side_effect
        
        result = checker._check_http_link(link)
        
        assert result.status == "ok"
        assert result.status_code == 200
        assert mock_urlopen.call_count == 2  # HEAD + GET

    @patch('urllib.request.urlopen')
    def test_http_link_head_404_no_fallback(self, mock_urlopen):
        """Test that HEAD 404 does NOT fall back to GET (truly broken)."""
        checker = LinkChecker()
        link = Link(url="http://example.com", line_number=1, link_type="http")
        
        # Mock: HEAD returns 404
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://example.com", 404, "Not Found", {}, None
        )
        
        result = checker._check_http_link(link)
        
        assert result.status == "broken"
        assert result.status_code == 404
        assert mock_urlopen.call_count == 1  # Only HEAD, no fallback

    def test_ssrf_protection_localhost(self):
        """Test SSRF protection blocks localhost variants."""
        checker = LinkChecker()
        
        test_cases = [
            "http://localhost:8080",
            "http://localhost/admin",
            "http://LOCALHOST:3000",  # Case insensitive
            "http://localhost.localdomain/api",
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is True, f"Failed to block: {url}"
    
    def test_ssrf_protection_loopback_ipv4(self):
        """Test SSRF protection blocks loopback IPv4 addresses."""
        checker = LinkChecker()
        
        test_cases = [
            "http://127.0.0.1",
            "http://127.0.0.1:8080",
            "http://127.1.1.1",
            "http://127.255.255.255",
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is True, f"Failed to block: {url}"
    
    def test_ssrf_protection_private_ipv4(self):
        """Test SSRF protection blocks private IPv4 ranges."""
        checker = LinkChecker()
        
        test_cases = [
            "http://192.168.1.1",
            "http://192.168.0.1:3000",
            "http://10.0.0.1",
            "http://10.255.255.255",
            "http://172.16.0.1",
            "http://172.31.255.255",
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is True, f"Failed to block: {url}"
    
    def test_ssrf_protection_link_local(self):
        """Test SSRF protection blocks link-local addresses (AWS/Azure metadata)."""
        checker = LinkChecker()
        
        test_cases = [
            "http://169.254.169.254",  # AWS metadata service
            "http://169.254.169.254/latest/meta-data",
            "http://169.254.0.1",
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is True, f"Failed to block: {url}"
    
    def test_ssrf_protection_loopback_ipv6(self):
        """Test SSRF protection blocks IPv6 loopback."""
        checker = LinkChecker()
        
        test_cases = [
            "http://[::1]",
            "http://[::1]:8080",
            "http://[0:0:0:0:0:0:0:1]",
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is True, f"Failed to block: {url}"
    
    def test_ssrf_protection_allows_public_urls(self):
        """Test SSRF protection allows legitimate public URLs."""
        checker = LinkChecker()
        
        test_cases = [
            "https://github.com",
            "https://example.com",
            "http://8.8.8.8",  # Public IP
            "https://www.google.com",
            "http://1.1.1.1",  # Cloudflare DNS
        ]
        
        for url in test_cases:
            assert checker._is_private_ip(url) is False, f"Should allow: {url}"
    
    def test_ssrf_protection_invalid_urls(self):
        """Test SSRF protection handles invalid URLs gracefully."""
        checker = LinkChecker()
        
        # Invalid URLs should not cause crashes
        test_cases = [
            "not-a-url",
            "http://",
            "://missing-scheme",
            "",
        ]
        
        for url in test_cases:
            # Should not raise exceptions
            result = checker._is_private_ip(url)
            assert isinstance(result, bool)
    
    @patch('urllib.request.urlopen')
    def test_ssrf_protection_blocks_request(self, mock_urlopen):
        """Test that private IPs are blocked before making HTTP requests."""
        checker = LinkChecker()
        link = Link(url="http://192.168.1.1", line_number=1, link_type="http")
        
        result = checker._check_http_link(link)
        
        # Should return warning without making HTTP request
        assert result.status == "warning"
        assert "private IP" in result.message
        assert "security protection" in result.message
        assert mock_urlopen.call_count == 0  # No HTTP request made
    
    @patch('urllib.request.urlopen')
    def test_ssrf_protection_allows_public_request(self, mock_urlopen):
        """Test that public URLs are allowed through to HTTP request."""
        checker = LinkChecker()
        link = Link(url="https://example.com", line_number=1, link_type="http")
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        result = checker._check_http_link(link)
        
        # Should make HTTP request and succeed
        assert result.status == "ok"
        assert result.status_code == 200
        assert mock_urlopen.call_count == 1  # HTTP request made

class TestConfig:
    """Tests for Config."""
    
    def test_load_nonexistent_config(self):
        """Test loading non-existent config file."""
        config = Config.load(Path("/nonexistent/config.json"))
        assert len(config.exclude_patterns) == 0
    
    def test_should_check_url_no_exclusions(self):
        """Test URL checking with no exclusions."""
        config = Config()
        
        assert config.should_check_url("https://example.com")
        assert config.should_check_url("http://localhost:8080")
    
    def test_load_config_with_exclusions(self, tmp_path):
        """Test loading config with URL exclusions."""
        config_file = tmp_path / ".mdlinkcheckrc"
        config_file.write_text("""
{
  "exclude_urls": [
    "^https?://localhost",
    "^https?://127\\\\.0\\\\.0\\\\.1"
  ]
}
""")
        
        config = Config.load(config_file)
        
        assert not config.should_check_url("http://localhost:8080")
        assert not config.should_check_url("http://127.0.0.1:3000")
        assert config.should_check_url("https://example.com")


class TestIntegration:
    """Integration tests."""
    
    def test_scan_local_folder(self, tmp_path):
        """Test scanning local folder."""
        # Create test structure
        (tmp_path / "README.md").write_text("""
# Project

[Link 1](https://example.com)
[Link 2](./docs/guide.md)
[Link 3](#introduction)

## Introduction

Hello world.
""")
        
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "guide.md").write_text("# Guide")
        
        # Scan
        scanner = MarkdownScanner(str(tmp_path))
        markdown_files = scanner.scan()
        
        assert len(markdown_files) == 2
        assert "README.md" in markdown_files
        assert str(Path("docs") / "guide.md") in markdown_files
        
        # Check README links
        readme_links = markdown_files["README.md"].links
        assert len(readme_links) == 3
        
        # Check links
        checker = LinkChecker(timeout=5, max_workers=2)
        results = checker.check_all(markdown_files, tmp_path)
        
        # Verify results
        readme_results = results["README.md"]
        
        # Find the relative link result
        relative_result = next(
            r for r in readme_results.results 
            if r.link.link_type == "relative"
        )
        assert relative_result.status == "ok"
        
        # Find the anchor link result
        anchor_result = next(
            r for r in readme_results.results 
            if r.link.link_type == "anchor"
        )
        assert anchor_result.status == "ok"
