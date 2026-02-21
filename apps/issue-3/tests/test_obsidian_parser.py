"""
Tests for Obsidian Parser

Tests parsing of Obsidian-flavored Markdown according to
docs/OBSIDIAN_SYNTAX_SUPPORT.md
"""

import pytest
from pathlib import Path
from src.backend.parsers.obsidian_parser import ObsidianParser, parse_obsidian_file


class TestObsidianParser:
    """Test suite for ObsidianParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return ObsidianParser()
    
    def test_parse_yaml_frontmatter(self, parser):
        """Test YAML frontmatter parsing."""
        content = """---
tags:
  - rust
  - programming
aliases:
  - Rust Ownership
title: Rust 所有權
---

# Content
This is test content.
"""
        result = parser.parse_content(content)
        
        assert result.frontmatter['title'] == 'Rust 所有權'
        assert 'rust' in result.tags
        assert 'programming' in result.tags
        assert 'Rust Ownership' in result.aliases
    
    def test_parse_nested_tags(self, parser):
        """Test nested tag parsing (e.g., #程式語言/Rust)."""
        content = """---
tags:
  - 程式語言/Rust
---

Content with #rust/ownership #programming
"""
        result = parser.parse_content(content)
        
        # Check frontmatter tags
        assert '程式語言/Rust' in result.tags
        assert '程式語言' in result.tags  # Parent tag
        
        # Check inline tags
        assert 'rust/ownership' in result.tags
        assert 'rust' in result.tags  # Parent tag
        assert 'programming' in result.tags
    
    def test_parse_basic_wikilink(self, parser):
        """Test basic wikilink [[Document]]."""
        content = "See [[Rust 所有權]] for details."
        result = parser.parse_content(content)
        
        assert len(result.wikilinks) == 1
        assert result.wikilinks[0]['target'] == 'Rust 所有權'
        assert result.wikilinks[0]['type'] == 'wikilink'
        assert result.wikilinks[0]['header'] is None
        assert result.wikilinks[0]['display'] is None
    
    def test_parse_wikilink_with_display(self, parser):
        """Test wikilink with display text [[Document|Display]]."""
        content = "See [[Rust 所有權|ownership]] for details."
        result = parser.parse_content(content)
        
        assert len(result.wikilinks) == 1
        assert result.wikilinks[0]['target'] == 'Rust 所有權'
        assert result.wikilinks[0]['display'] == 'ownership'
    
    def test_parse_wikilink_with_header(self, parser):
        """Test wikilink with header [[Document#Header]]."""
        content = "See [[Rust 所有權#作用域]] for details."
        result = parser.parse_content(content)
        
        assert len(result.wikilinks) == 1
        assert result.wikilinks[0]['target'] == 'Rust 所有權'
        assert result.wikilinks[0]['header'] == '作用域'
        assert result.wikilinks[0]['type'] == 'wikilink_header'
    
    def test_parse_wikilink_with_header_and_display(self, parser):
        """Test wikilink [[Document#Header|Display]]."""
        content = "See [[Rust 所有權#作用域|scope]] for details."
        result = parser.parse_content(content)
        
        assert len(result.wikilinks) == 1
        assert result.wikilinks[0]['target'] == 'Rust 所有權'
        assert result.wikilinks[0]['header'] == '作用域'
        assert result.wikilinks[0]['display'] == 'scope'
    
    def test_parse_headings(self, parser):
        """Test heading extraction."""
        content = """# Main Title
Some content
## Section 1
Content
### Subsection 1.1
More content
"""
        result = parser.parse_content(content)
        
        assert len(result.headings) == 3
        assert 'Main Title' in result.headings
        assert 'Section 1' in result.headings
        assert 'Subsection 1.1' in result.headings
    
    def test_parse_obsidian_image(self, parser):
        """Test Obsidian-style image with size."""
        content = "![100](path/to/image.png)"
        result = parser.parse_content(content)
        
        assert len(result.images) == 1
        assert result.images[0]['path'] == 'path/to/image.png'
        assert result.images[0]['size'] == '100'
        assert result.images[0]['type'] == 'obsidian_image'
    
    def test_degrade_code_block_title(self, parser):
        """Test P2 degradation: code block title removal."""
        content = '```python title:"Example"\nprint("hello")\n```'
        result = parser.parse_content(content)
        
        # Title should be removed
        assert 'title:' not in result.parsed_content
        assert '```python' in result.parsed_content
    
    def test_degrade_callout(self, parser):
        """Test P2 degradation: callout to blockquote."""
        content = "> [!note] Important\n> This is a note"
        result = parser.parse_content(content)
        
        # [!note] should be removed
        assert '[!note]' not in result.parsed_content
        assert '> Important' in result.parsed_content or '>' in result.parsed_content
    
    def test_degrade_embed(self, parser):
        """Test P2 degradation: embed to link."""
        content = "![[Rust 所有權]]"
        result = parser.parse_content(content)
        
        # Embed should become link
        assert '![[' not in result.parsed_content
        assert '[[Rust 所有權]]' in result.parsed_content
    
    def test_generate_plain_text(self, parser):
        """Test plain text generation."""
        content = """# Title

This is **bold** and *italic* text.

See [[Document]] for more.

`code` and ```python
code block
```
"""
        result = parser.parse_content(content)
        
        # Plain text should have no markdown
        assert '**' not in result.plain_text
        assert '*' not in result.plain_text
        assert '[[' not in result.plain_text
        assert '```' not in result.plain_text
        assert '#' not in result.plain_text or result.plain_text.count('#') < content.count('#')
    
    def test_parse_multiple_wikilinks(self, parser):
        """Test parsing multiple wikilinks in one document."""
        content = """
See [[Document1]] and [[Document2|Display]] for more.
Also check [[Document3#Header]].
"""
        result = parser.parse_content(content)
        
        assert len(result.wikilinks) == 3
        targets = [link['target'] for link in result.wikilinks]
        assert 'Document1' in targets
        assert 'Document2' in targets
        assert 'Document3' in targets


class TestParseObsidianFile:
    """Test file parsing function."""
    
    def test_parse_real_file(self, tmp_path):
        """Test parsing an actual file."""
        # Create a test file
        test_file = tmp_path / "test.md"
        content = """---
tags:
  - test
---

# Test Document

This is a [[test]] document.
"""
        test_file.write_text(content, encoding='utf-8')
        
        # Parse it
        result = parse_obsidian_file(test_file)
        
        assert result.title == 'test'
        assert 'test' in result.tags
        assert len(result.wikilinks) == 1
        assert result.wikilinks[0]['target'] == 'test'
