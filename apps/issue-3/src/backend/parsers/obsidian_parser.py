"""
Obsidian Markdown Parser

Parses Obsidian-flavored Markdown files according to the syntax support matrix
defined in docs/OBSIDIAN_SYNTAX_SUPPORT.md.

Supported syntax (P1 - Full Support):
- YAML Frontmatter
- Wikilinks: [[document]], [[document|display]], [[document#header]]
- Tags: #tag, #parent/child
- Obsidian images: ![100](path)
- Standard Markdown

Degraded support (P2):
- Code blocks with titles (title removed)
- Callouts (converted to blockquotes)
- Embeds (converted to links)

Not supported (P3):
- Dataview queries
- Canvas files
- Plugin syntax
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import frontmatter


@dataclass
class ParsedDocument:
    """Result of parsing an Obsidian Markdown document."""
    
    # Content
    raw_content: str
    parsed_content: str  # After processing Obsidian syntax
    plain_text: str  # For vector embedding
    
    # Frontmatter
    frontmatter: Dict[str, any]
    
    # Extracted elements
    title: Optional[str] = None
    tags: List[str] = None
    aliases: List[str] = None
    headings: List[str] = None
    wikilinks: List[Dict[str, str]] = None
    images: List[Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize lists if None."""
        if self.tags is None:
            self.tags = []
        if self.aliases is None:
            self.aliases = []
        if self.headings is None:
            self.headings = []
        if self.wikilinks is None:
            self.wikilinks = []
        if self.images is None:
            self.images = []


class ObsidianParser:
    """Parser for Obsidian-flavored Markdown."""
    
    # Regex patterns (compiled for performance)
    WIKILINK_PATTERN = re.compile(
        r'\[\[([^#\]|]+?)(?:#([^\]|]+?))?(?:\|([^\]]+?))?\]\]'
    )
    # Match tags including Chinese/Unicode characters
    TAG_PATTERN = re.compile(r'#([\w\u4e00-\u9fff_/-]+)', re.UNICODE)
    OBSIDIAN_IMAGE_PATTERN = re.compile(r'!\[(\d+(?:x\d+)?)\]\(([^)]+)\)')
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_TITLE_PATTERN = re.compile(r'```(\w+)\s+title:"([^"]+)"')
    CALLOUT_PATTERN = re.compile(r'>\s*\[!(\w+)\]\s*(.+)?', re.MULTILINE)
    EMBED_PATTERN = re.compile(r'!\[\[([^\]]+)\]\]')
    
    def __init__(self):
        """Initialize the parser."""
        pass
    
    def parse_file(self, file_path: Path) -> ParsedDocument:
        """
        Parse an Obsidian Markdown file.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            ParsedDocument with extracted content and metadata
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        return self.parse_content(raw_content, file_path.stem)
    
    def parse_content(self, content: str, title: str = None) -> ParsedDocument:
        """
        Parse Obsidian Markdown content.
        
        Args:
            content: Raw markdown content
            title: Optional document title
            
        Returns:
            ParsedDocument with extracted content and metadata
        """
        # Parse frontmatter
        post = frontmatter.loads(content)
        frontmatter_data = post.metadata
        content_without_frontmatter = post.content
        
        # Extract title
        if not title:
            title = frontmatter_data.get('title')
        
        # Extract tags from frontmatter
        tags = self._extract_tags_from_frontmatter(frontmatter_data)
        
        # Extract tags from content
        content_tags = self._extract_inline_tags(content_without_frontmatter)
        tags.extend(content_tags)
        tags = list(set(tags))  # Remove duplicates
        
        # Extract aliases
        aliases = frontmatter_data.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases]
        elif not isinstance(aliases, list):
            aliases = []
        
        # Extract wikilinks
        wikilinks = self._extract_wikilinks(content_without_frontmatter)
        
        # Extract headings
        headings = self._extract_headings(content_without_frontmatter)
        
        # Extract images
        images = self._extract_images(content_without_frontmatter)
        
        # Process content (degrade unsupported syntax)
        parsed_content = self._process_content(content_without_frontmatter)
        
        # Generate plain text (remove all markdown formatting)
        plain_text = self._generate_plain_text(parsed_content)
        
        return ParsedDocument(
            raw_content=content,
            parsed_content=parsed_content,
            plain_text=plain_text,
            frontmatter=frontmatter_data,
            title=title,
            tags=tags,
            aliases=aliases,
            headings=headings,
            wikilinks=wikilinks,
            images=images
        )
    
    def _extract_tags_from_frontmatter(self, frontmatter: Dict) -> List[str]:
        """Extract tags from YAML frontmatter."""
        tags = []
        
        # Handle 'tags' field
        tags_field = frontmatter.get('tags', [])
        if isinstance(tags_field, str):
            tags.append(tags_field)
        elif isinstance(tags_field, list):
            tags.extend(tags_field)
        
        # Handle nested tags (split by /)
        expanded_tags = []
        for tag in tags:
            # Remove leading # if present
            tag = tag.lstrip('#')
            expanded_tags.append(tag)
            
            # Add parent tags for nested structure
            # e.g., "程式語言/Rust" -> ["程式語言", "程式語言/Rust"]
            if '/' in tag:
                parts = tag.split('/')
                for i in range(1, len(parts)):
                    parent = '/'.join(parts[:i])
                    if parent not in expanded_tags:
                        expanded_tags.append(parent)
        
        return expanded_tags
    
    def _extract_inline_tags(self, content: str) -> List[str]:
        """Extract inline tags from content (e.g., #rust #programming)."""
        matches = self.TAG_PATTERN.findall(content)
        tags = []
        
        for tag in matches:
            tags.append(tag)
            
            # Add parent tags for nested structure
            if '/' in tag:
                parts = tag.split('/')
                for i in range(1, len(parts)):
                    parent = '/'.join(parts[:i])
                    if parent not in tags:
                        tags.append(parent)
        
        return tags
    
    def _extract_wikilinks(self, content: str) -> List[Dict[str, str]]:
        """
        Extract wikilinks from content.
        
        Patterns:
        - [[Document]]
        - [[Document|Display Text]]
        - [[Document#Header]]
        - [[Document#Header|Display Text]]
        """
        matches = self.WIKILINK_PATTERN.findall(content)
        wikilinks = []
        
        for match in matches:
            document, header, display = match
            wikilinks.append({
                'target': document,
                'header': header if header else None,
                'display': display if display else None,
                'type': 'wikilink_header' if header else 'wikilink'
            })
        
        return wikilinks
    
    def _extract_headings(self, content: str) -> List[str]:
        """Extract all headings from content."""
        matches = self.HEADING_PATTERN.findall(content)
        headings = [heading_text.strip() for _, heading_text in matches]
        return headings
    
    def _extract_images(self, content: str) -> List[Dict[str, str]]:
        """Extract Obsidian-style images with size parameters."""
        matches = self.OBSIDIAN_IMAGE_PATTERN.findall(content)
        images = []
        
        for size, path in matches:
            images.append({
                'path': path,
                'size': size,
                'type': 'obsidian_image'
            })
        
        # Also extract standard markdown images
        standard_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
        standard_matches = standard_pattern.findall(content)
        
        for alt, path in standard_matches:
            # Skip if already captured as Obsidian image
            if not any(img['path'] == path for img in images):
                images.append({
                    'path': path,
                    'alt': alt,
                    'type': 'markdown_image'
                })
        
        return images
    
    def _process_content(self, content: str) -> str:
        """
        Process content to degrade unsupported syntax.
        
        P2 - Degraded support:
        - Remove code block titles
        - Convert callouts to standard blockquotes
        - Convert embeds to links
        """
        # Remove code block titles: ```rust title:"..." -> ```rust
        content = self.CODE_BLOCK_TITLE_PATTERN.sub(r'```\1', content)
        
        # Convert callouts: > [!note] Text -> > Text
        content = self.CALLOUT_PATTERN.sub(r'> \2', content)
        
        # Convert embeds to links: ![[Document]] -> [[Document]]
        content = self.EMBED_PATTERN.sub(r'[[\1]]', content)
        
        return content
    
    def _generate_plain_text(self, content: str) -> str:
        """
        Generate plain text from markdown content.
        
        Removes:
        - Markdown formatting (* _ ` # [] () etc.)
        - Wikilinks (keeps the text)
        - Code blocks
        - HTML tags
        """
        text = content
        
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        
        # Convert wikilinks to plain text
        text = self.WIKILINK_PATTERN.sub(r'\1\3', text)  # Keep document name or display text
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold
        text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Strikethrough
        
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
        
        # Remove headings #
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text


def parse_obsidian_file(file_path: Path) -> ParsedDocument:
    """
    Convenience function to parse an Obsidian file.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        ParsedDocument with extracted content and metadata
    """
    parser = ObsidianParser()
    return parser.parse_file(file_path)
