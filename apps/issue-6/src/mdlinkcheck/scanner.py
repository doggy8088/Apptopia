"""Markdown file scanner and link parser."""

import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
import urllib.request
import json


@dataclass
class Link:
    """Represents a link found in a Markdown file."""
    url: str
    line_number: int
    link_type: str  # 'http', 'relative', 'anchor'


@dataclass
class MarkdownFile:
    """Represents a Markdown file with its links."""
    path: str
    links: List[Link]
    content: str  # For anchor checking


class MarkdownScanner:
    """Scans and extracts links from Markdown files."""
    
    def __init__(self, source: str):
        self.source = source
        self.base_path: Path = Path(".")
        self.source_name: str = source
        
    def scan(self) -> Dict[str, MarkdownFile]:
        """Scan for Markdown files and extract links."""
        if self.source.startswith("http://") or self.source.startswith("https://"):
            return self._scan_github_repo()
        else:
            return self._scan_local_folder()
    
    def _scan_local_folder(self) -> Dict[str, MarkdownFile]:
        """Scan local folder for Markdown files."""
        folder_path = Path(self.source).resolve()
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.source}")
        
        self.base_path = folder_path
        self.source_name = str(folder_path)
        
        markdown_files = {}
        for md_file in folder_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                relative_path = md_file.relative_to(folder_path)
                links = self._extract_links(content)
                markdown_files[str(relative_path)] = MarkdownFile(
                    path=str(relative_path),
                    links=links,
                    content=content,
                )
            except Exception as e:
                print(f"Warning: Could not read {md_file}: {e}")
        
        return markdown_files
    
    def _scan_github_repo(self) -> Dict[str, MarkdownFile]:
        """Scan GitHub repository for Markdown files via API."""
        # Parse GitHub URL
        match = re.match(r"https://github\.com/([^/]+)/([^/]+)", self.source)
        if not match:
            raise ValueError(f"Invalid GitHub URL: {self.source}")
        
        owner, repo = match.groups()
        repo = repo.rstrip("/")
        
        self.source_name = f"{owner}/{repo}"
        
        # Get repository contents via GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        
        try:
            req = urllib.request.Request(api_url)
            req.add_header("Accept", "application/vnd.github.v3+json")
            
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Failed to fetch repository contents: {e}")
        
        # Filter Markdown files
        markdown_files = {}
        for item in data.get("tree", []):
            if item["type"] == "blob" and item["path"].endswith(".md"):
                try:
                    content = self._fetch_file_content(owner, repo, item["path"])
                    links = self._extract_links(content)
                    markdown_files[item["path"]] = MarkdownFile(
                        path=item["path"],
                        links=links,
                        content=content,
                    )
                except Exception as e:
                    print(f"Warning: Could not fetch {item['path']}: {e}")
        
        return markdown_files
    
    def _fetch_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch file content from GitHub."""
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        req = urllib.request.Request(api_url)
        req.add_header("Accept", "application/vnd.github.v3.raw")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    
    def _extract_links(self, content: str) -> List[Link]:
        """Extract links from Markdown content, ignoring code blocks."""
        links = []
        
        # Remove code blocks (both ``` and indented)
        content_without_code = self._remove_code_blocks(content)
        
        lines = content_without_code.split("\n")
        
        for line_num, line in enumerate(lines, start=1):
            # Find Markdown links [text](url)
            for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line):
                url = match.group(2)
                link_type = self._classify_link(url)
                links.append(Link(url=url, line_number=line_num, link_type=link_type))
            
            # Find reference-style links [text][ref] and [ref]: url
            for match in re.finditer(r'^\[([^\]]+)\]:\s*(.+)$', line):
                url = match.group(2).strip()
                link_type = self._classify_link(url)
                links.append(Link(url=url, line_number=line_num, link_type=link_type))
        
        return links
    
    def _remove_code_blocks(self, content: str) -> str:
        """Remove code blocks from content."""
        # Remove fenced code blocks (``` or ~~~)
        content = re.sub(r'```[\s\S]*?```', '', content)
        content = re.sub(r'~~~[\s\S]*?~~~', '', content)
        
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        
        # Remove indented code blocks (4 spaces or 1 tab at start of line)
        lines = content.split("\n")
        result_lines = []
        for line in lines:
            if not (line.startswith("    ") or line.startswith("\t")):
                result_lines.append(line)
            else:
                result_lines.append("")  # Keep line numbers consistent
        
        return "\n".join(result_lines)
    
    def _classify_link(self, url: str) -> str:
        """Classify link type."""
        if url.startswith("#"):
            return "anchor"
        elif url.startswith("http://") or url.startswith("https://"):
            return "http"
        elif url.startswith("/"):
            return "internal"
        else:
            return "relative"
