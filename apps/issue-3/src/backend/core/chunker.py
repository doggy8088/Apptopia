"""
Document chunking module for semantic text segmentation.

This module implements semantic chunking strategy that splits documents
into meaningful chunks while preserving context and semantic coherence.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


@dataclass
class Chunk:
    """Represents a document chunk with metadata."""
    text: str
    start_index: int
    end_index: int
    token_count: int
    metadata: dict


class DocumentChunker:
    """
    Semantic document chunker that splits text into meaningful chunks.
    
    Features:
    - Semantic boundaries (paragraphs, headings)
    - Configurable chunk size with overlap
    - Context preservation through metadata
    - Special handling for code blocks
    - Chinese text support
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 102,  # ~20% of 512
        preserve_code_blocks: bool = True
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target token count per chunk
            chunk_overlap: Number of tokens to overlap between chunks
            preserve_code_blocks: Whether to keep code blocks intact
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.preserve_code_blocks = preserve_code_blocks
        
        # Initialize tokenizer if available
        if HAS_TIKTOKEN:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 4 chars for English, 1.5 for Chinese)
            # Use conservative estimate
            return len(text) // 3
    
    def split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences, handling both English and Chinese.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Pattern handles:
        # - English: . ! ? followed by space or newline
        # - Chinese: 。！？ (may or may not have space after)
        # Split on Chinese punctuation or English punctuation with space
        pattern = r'(?<=[.!?])\s+|(?<=[。！？])|(?:\n\n+)'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def extract_code_blocks(self, text: str) -> Tuple[List[Tuple[int, int, str]], str]:
        """
        Extract code blocks from text and return cleaned text.
        
        Args:
            text: Input text with code blocks
            
        Returns:
            Tuple of (code_blocks, cleaned_text)
            code_blocks is list of (start, end, code) tuples
        """
        code_blocks = []
        pattern = r'```[\s\S]*?```'
        
        for match in re.finditer(pattern, text):
            start, end = match.span()
            code_blocks.append((start, end, match.group()))
        
        # Replace code blocks with markers
        cleaned_text = re.sub(pattern, '[CODE_BLOCK]', text)
        
        return code_blocks, cleaned_text
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Chunk]:
        """
        Chunk text into semantic segments.
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # Extract code blocks if needed
        code_blocks = []
        working_text = text
        if self.preserve_code_blocks:
            code_blocks, working_text = self.extract_code_blocks(text)
        
        # Split into sentences
        sentences = self.split_by_sentences(working_text)
        
        if not sentences:
            return []
        
        # Build chunks
        current_chunk = []
        current_tokens = 0
        current_start = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # Check if adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk_end = current_start + len(chunk_text)
                
                chunks.append(Chunk(
                    text=chunk_text,
                    start_index=current_start,
                    end_index=chunk_end,
                    token_count=current_tokens,
                    metadata=metadata.copy()
                ))
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_tokens = 0
                for j in range(len(current_chunk) - 1, -1, -1):
                    sent_tokens = self.count_tokens(current_chunk[j])
                    if overlap_tokens + sent_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, current_chunk[j])
                        overlap_tokens += sent_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
                current_start = chunk_end - len(' '.join(overlap_sentences))
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(Chunk(
                text=chunk_text,
                start_index=current_start,
                end_index=current_start + len(chunk_text),
                token_count=current_tokens,
                metadata=metadata.copy()
            ))
        
        # Re-insert code blocks if they were extracted
        if self.preserve_code_blocks and code_blocks:
            chunks = self._reinsert_code_blocks(chunks, code_blocks, text)
        
        return chunks
    
    def _reinsert_code_blocks(
        self,
        chunks: List[Chunk],
        code_blocks: List[Tuple[int, int, str]],
        original_text: str
    ) -> List[Chunk]:
        """
        Re-insert code blocks into chunks.
        
        Args:
            chunks: List of chunks with [CODE_BLOCK] markers
            code_blocks: List of (start, end, code) tuples
            original_text: Original text with code blocks
            
        Returns:
            Updated chunks with code blocks restored
        """
        # Simple approach: replace markers with actual code
        for chunk in chunks:
            if '[CODE_BLOCK]' in chunk.text:
                # Find which code block(s) belong to this chunk
                for start, end, code in code_blocks:
                    chunk.text = chunk.text.replace('[CODE_BLOCK]', code, 1)
        
        return chunks
    
    def chunk_document(
        self,
        content: str,
        title: str = "",
        headings: List[str] = None,
        tags: List[str] = None
    ) -> List[Chunk]:
        """
        Chunk a document with enhanced metadata.
        
        Args:
            content: Document content
            title: Document title
            headings: List of section headings
            tags: List of tags
            
        Returns:
            List of chunks with metadata
        """
        metadata = {
            'title': title,
            'headings': headings or [],
            'tags': tags or []
        }
        
        return self.chunk_text(content, metadata)


def create_chunker(
    chunk_size: int = 512,
    chunk_overlap: int = 102
) -> DocumentChunker:
    """
    Factory function to create a DocumentChunker instance.
    
    Args:
        chunk_size: Target token count per chunk
        chunk_overlap: Number of tokens to overlap
        
    Returns:
        DocumentChunker instance
    """
    return DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
