"""Link checker module."""

import urllib.request
import urllib.error
import socket
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import difflib

from .scanner import MarkdownFile, Link
from .config import Config


@dataclass
class LinkResult:
    """Result of checking a single link."""
    link: Link
    status: str  # 'ok', 'broken', 'warning'
    status_code: int = 0
    message: str = ""
    suggestion: str = ""


@dataclass
class FileResult:
    """Results for all links in a file."""
    file_path: str
    results: List[LinkResult]
    
    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.status == "ok")
    
    @property
    def broken_count(self) -> int:
        return sum(1 for r in self.results if r.status == "broken")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == "warning")


class LinkChecker:
    """Checks the health of links in Markdown files."""
    
    def __init__(self, timeout: int = 10, max_workers: int = 10, config: Config = None):
        self.timeout = timeout
        self.max_workers = max_workers
        self.config = config or Config()
    
    def check_all(self, markdown_files: Dict[str, MarkdownFile], base_path: Path) -> Dict[str, FileResult]:
        """Check all links in all files."""
        results = {}
        
        for file_path, md_file in markdown_files.items():
            file_results = []
            
            # Group links by type for efficient processing
            http_links = [link for link in md_file.links if link.link_type == "http"]
            relative_links = [link for link in md_file.links if link.link_type == "relative"]
            anchor_links = [link for link in md_file.links if link.link_type == "anchor"]
            
            # Check HTTP links concurrently
            if http_links:
                file_results.extend(self._check_http_links_concurrent(http_links))
            
            # Check relative links
            for link in relative_links:
                file_results.append(self._check_relative_link(link, file_path, base_path))
            
            # Check anchor links
            for link in anchor_links:
                file_results.append(self._check_anchor_link(link, md_file.content))
            
            results[file_path] = FileResult(file_path=file_path, results=file_results)
        
        return results
    
    def _check_http_links_concurrent(self, links: List[Link]) -> List[LinkResult]:
        """Check HTTP links concurrently."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_link = {
                executor.submit(self._check_http_link, link): link
                for link in links
            }
            
            for future in as_completed(future_to_link):
                results.append(future.result())
        
        return results
    
    def _check_http_link(self, link: Link) -> LinkResult:
        """Check a single HTTP link."""
        # Check if URL should be excluded
        if not self.config.should_check_url(link.url):
            return LinkResult(
                link=link,
                status="ok",
                message="excluded by config",
            )
        
        try:
            req = urllib.request.Request(link.url, method="HEAD")
            req.add_header("User-Agent", "mdlinkcheck/1.0")
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return LinkResult(
                    link=link,
                    status="ok",
                    status_code=response.status,
                )
        
        except urllib.error.HTTPError as e:
            return LinkResult(
                link=link,
                status="broken",
                status_code=e.code,
                message=f"{e.code}",
            )
        
        except urllib.error.URLError as e:
            # Check if the error is due to timeout
            if isinstance(e.reason, socket.timeout):
                return LinkResult(
                    link=link,
                    status="warning",
                    message="timeout",
                )
            return LinkResult(
                link=link,
                status="broken",
                message=str(e.reason) if hasattr(e, "reason") else str(e),
            )
        
        except Exception as e:
            return LinkResult(
                link=link,
                status="warning",
                message=str(e),
            )
    
    def _check_relative_link(self, link: Link, current_file: str, base_path: Path) -> LinkResult:
        """Check a relative path link."""
        # Resolve the relative path
        current_dir = base_path / Path(current_file).parent
        target_path = (current_dir / link.url).resolve()
        
        if target_path.exists():
            return LinkResult(
                link=link,
                status="ok",
            )
        else:
            return LinkResult(
                link=link,
                status="broken",
                message="file not found",
            )
    
    def _check_anchor_link(self, link: Link, content: str) -> LinkResult:
        """Check an anchor link."""
        # Extract anchor (remove leading #)
        anchor = link.url[1:] if link.url.startswith("#") else link.url
        
        # Extract all headings from content
        headings = self._extract_headings(content)
        
        # Convert heading to anchor format (GitHub style)
        heading_anchors = [self._heading_to_anchor(h) for h in headings]
        
        if anchor in heading_anchors:
            return LinkResult(
                link=link,
                status="ok",
            )
        else:
            # Try to find similar anchors for suggestions
            suggestion = self._find_similar_anchor(anchor, heading_anchors)
            
            return LinkResult(
                link=link,
                status="broken",
                message="anchor not found",
                suggestion=suggestion,
            )
    
    def _extract_headings(self, content: str) -> List[str]:
        """Extract all headings from Markdown content."""
        headings = []
        
        # Remove code blocks first
        content = re.sub(r'```[\s\S]*?```', '', content)
        content = re.sub(r'~~~[\s\S]*?~~~', '', content)
        
        for line in content.split("\n"):
            # Match ATX-style headings (# Heading)
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                heading_text = match.group(2).strip()
                headings.append(heading_text)
        
        return headings
    
    def _heading_to_anchor(self, heading: str) -> str:
        """Convert heading text to GitHub-style anchor."""
        # Remove markdown formatting
        heading = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', heading)  # [text](url) -> text
        heading = re.sub(r'`([^`]+)`', r'\1', heading)  # `code` -> code
        heading = re.sub(r'\*\*([^*]+)\*\*', r'\1', heading)  # **bold** -> bold
        heading = re.sub(r'\*([^*]+)\*', r'\1', heading)  # *italic* -> italic
        heading = re.sub(r'__([^_]+)__', r'\1', heading)  # __bold__ -> bold
        heading = re.sub(r'_([^_]+)_', r'\1', heading)  # _italic_ -> italic
        
        # Convert to lowercase
        heading = heading.lower()
        
        # Replace spaces with hyphens
        heading = re.sub(r'\s+', '-', heading)
        
        # Remove non-alphanumeric characters except hyphens
        heading = re.sub(r'[^a-z0-9\-]', '', heading)
        
        # Remove consecutive hyphens
        heading = re.sub(r'-+', '-', heading)
        
        # Remove leading/trailing hyphens
        heading = heading.strip('-')
        
        return heading
    
    def _find_similar_anchor(self, anchor: str, valid_anchors: List[str]) -> str:
        """Find a similar valid anchor using fuzzy matching."""
        if not valid_anchors:
            return ""
        
        # Use difflib to find close matches
        close_matches = difflib.get_close_matches(anchor, valid_anchors, n=1, cutoff=0.6)
        
        if close_matches:
            return f"did you mean #{close_matches[0]}?"
        
        return ""
