"""
Tests for document chunker.
"""

import pytest
from src.backend.core.chunker import DocumentChunker, create_chunker


class TestDocumentChunker:
    """Test cases for DocumentChunker."""
    
    def test_initialization(self):
        """Test chunker initialization."""
        chunker = DocumentChunker(chunk_size=256, chunk_overlap=50)
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 50
        assert chunker.preserve_code_blocks is True
    
    def test_count_tokens_simple(self):
        """Test token counting."""
        chunker = DocumentChunker()
        text = "Hello world"
        count = chunker.count_tokens(text)
        assert count > 0
        assert count < 20  # Should be around 2-3 tokens
    
    def test_count_tokens_chinese(self):
        """Test token counting with Chinese text."""
        chunker = DocumentChunker()
        text = "你好世界"
        count = chunker.count_tokens(text)
        assert count > 0
    
    def test_split_by_sentences_english(self):
        """Test sentence splitting for English."""
        chunker = DocumentChunker()
        text = "Hello world. This is a test. How are you?"
        sentences = chunker.split_by_sentences(text)
        assert len(sentences) >= 3
        assert "Hello world." in sentences[0]
    
    def test_split_by_sentences_chinese(self):
        """Test sentence splitting for Chinese."""
        chunker = DocumentChunker()
        text = "你好世界。這是測試。你好嗎？"
        sentences = chunker.split_by_sentences(text)
        assert len(sentences) >= 3
    
    def test_split_by_sentences_mixed(self):
        """Test sentence splitting for mixed English and Chinese."""
        chunker = DocumentChunker()
        text = "Hello 世界。This is 測試。"
        sentences = chunker.split_by_sentences(text)
        assert len(sentences) >= 2
    
    def test_extract_code_blocks(self):
        """Test code block extraction."""
        chunker = DocumentChunker()
        text = """Some text before.
```python
def hello():
    print("world")
```
Some text after."""
        
        code_blocks, cleaned = chunker.extract_code_blocks(text)
        assert len(code_blocks) == 1
        assert 'def hello' in code_blocks[0][2]
        assert '[CODE_BLOCK]' in cleaned
        assert 'def hello' not in cleaned
    
    def test_extract_multiple_code_blocks(self):
        """Test extraction of multiple code blocks."""
        chunker = DocumentChunker()
        text = """
```python
code1
```
middle text
```javascript
code2
```
"""
        code_blocks, cleaned = chunker.extract_code_blocks(text)
        assert len(code_blocks) == 2
        assert cleaned.count('[CODE_BLOCK]') == 2
    
    def test_chunk_text_simple(self):
        """Test basic text chunking."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk.text, str) for chunk in chunks)
        assert all(chunk.token_count > 0 for chunk in chunks)
    
    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        chunker = DocumentChunker()
        chunks = chunker.chunk_text("")
        assert len(chunks) == 0
        
        chunks = chunker.chunk_text("   ")
        assert len(chunks) == 0
    
    def test_chunk_text_with_metadata(self):
        """Test chunking with metadata."""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        text = "This is a test. Another sentence."
        metadata = {'title': 'Test Doc', 'tags': ['test']}
        
        chunks = chunker.chunk_text(text, metadata)
        assert len(chunks) > 0
        assert chunks[0].metadata['title'] == 'Test Doc'
        assert chunks[0].metadata['tags'] == ['test']
    
    def test_chunk_text_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = DocumentChunker(chunk_size=30, chunk_overlap=10)
        text = ". ".join([f"Sentence number {i}" for i in range(20)])
        
        chunks = chunker.chunk_text(text)
        
        # Should have multiple chunks
        assert len(chunks) > 1
        
        # Check for overlap (last part of chunk N should appear in chunk N+1)
        if len(chunks) >= 2:
            chunk1_end = chunks[0].text.split()[-3:]
            chunk2_start = chunks[1].text.split()[:5]
            # Some overlap should exist
            assert any(word in chunk2_start for word in chunk1_end)
    
    def test_chunk_text_with_code_blocks(self):
        """Test chunking text with code blocks."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        text = """This is some text.
```python
def hello():
    return "world"
```
More text after code."""
        
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 0
        
        # Code block should be in at least one chunk
        full_text = ' '.join(chunk.text for chunk in chunks)
        assert 'def hello' in full_text
    
    def test_chunk_document(self):
        """Test chunking a complete document."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        content = "This is the introduction. " * 10
        
        chunks = chunker.chunk_document(
            content=content,
            title="Test Document",
            headings=["Introduction", "Body"],
            tags=["test", "sample"]
        )
        
        assert len(chunks) > 0
        assert chunks[0].metadata['title'] == "Test Document"
        assert "Introduction" in chunks[0].metadata['headings']
        assert "test" in chunks[0].metadata['tags']
    
    def test_chunk_long_document(self):
        """Test chunking a longer document."""
        chunker = DocumentChunker(chunk_size=200, chunk_overlap=40)
        
        # Create a longer document
        paragraphs = [
            "This is paragraph one. It contains multiple sentences. Each sentence adds meaning.",
            "This is paragraph two. It continues the narrative. More information is provided.",
            "Paragraph three brings new ideas. The discussion deepens. Context expands.",
            "Finally, paragraph four concludes. Everything ties together. The end."
        ]
        content = "\n\n".join(paragraphs)
        
        chunks = chunker.chunk_document(content, title="Long Doc")
        
        assert len(chunks) > 0
        # All chunks should have reasonable token counts
        assert all(chunk.token_count > 0 for chunk in chunks)
        assert all(chunk.token_count <= chunker.chunk_size * 1.2 for chunk in chunks)
    
    def test_chunk_chinese_document(self):
        """Test chunking Chinese document."""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        content = """這是一個測試文件。
它包含多個句子。
每個句子都有意義。

這是第二段。
它繼續敘述。
提供更多資訊。"""
        
        chunks = chunker.chunk_document(content, title="中文測試")
        
        assert len(chunks) > 0
        assert chunks[0].metadata['title'] == "中文測試"
        # Verify Chinese text is preserved
        full_text = ' '.join(chunk.text for chunk in chunks)
        assert "測試" in full_text
    
    def test_create_chunker_factory(self):
        """Test factory function."""
        chunker = create_chunker(chunk_size=256, chunk_overlap=50)
        assert isinstance(chunker, DocumentChunker)
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
