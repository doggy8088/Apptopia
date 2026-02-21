"""
Query Processor for RAG system.

Handles query parsing, expansion, retrieval from vector store,
and context preparation for LLM.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path

from ..indexer.vector_store import VectorStore
from ..core.embedder import Embedder
from ..models.document import DocumentChunk


@dataclass
class RetrievalResult:
    """Result from vector search."""
    chunk: DocumentChunk
    score: float
    document_path: str
    
    def __post_init__(self):
        """Validate result."""
        if self.score < 0 or self.score > 1:
            raise ValueError(f"Score must be between 0 and 1, got {self.score}")


@dataclass
class QueryContext:
    """Context prepared for LLM."""
    query: str
    retrieved_chunks: List[RetrievalResult]
    total_tokens: int
    context_text: str
    
    @property
    def has_results(self) -> bool:
        """Check if any results were retrieved."""
        return len(self.retrieved_chunks) > 0


class QueryProcessor:
    """
    Process user queries and retrieve relevant context.
    
    Features:
    - Query cleaning and normalization
    - Vector similarity search
    - Result ranking and filtering
    - Context preparation with token limits
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Embedder,
        max_results: int = 5,
        min_score: float = 0.3,
        max_context_tokens: int = 2000
    ):
        """
        Initialize query processor.
        
        Args:
            vector_store: Vector store for retrieval
            embedder: Embedder for generating query embeddings
            max_results: Maximum number of results to retrieve
            min_score: Minimum similarity score threshold (0-1)
            max_context_tokens: Maximum tokens for context
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.max_results = max_results
        self.min_score = min_score
        self.max_context_tokens = max_context_tokens
    
    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[str]] = None
    ) -> QueryContext:
        """
        Process a user query and prepare context.
        
        Args:
            query: User's question
            conversation_history: Optional previous messages
        
        Returns:
            QueryContext with retrieved chunks and formatted context
        """
        # Clean and normalize query
        cleaned_query = self._clean_query(query)
        
        # Expand query with conversation history if provided
        expanded_query = self._expand_query(cleaned_query, conversation_history)
        
        # Retrieve relevant chunks
        results = self._retrieve_chunks(expanded_query)
        
        # Build context text
        context_text, total_tokens = self._build_context(results)
        
        return QueryContext(
            query=cleaned_query,
            retrieved_chunks=results,
            total_tokens=total_tokens,
            context_text=context_text
        )
    
    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize query text.
        
        Args:
            query: Raw query string
        
        Returns:
            Cleaned query
        """
        # Remove extra whitespace
        cleaned = " ".join(query.split())
        
        # Remove trailing question marks (keep in query for context)
        # cleaned = cleaned.rstrip('?')
        
        return cleaned.strip()
    
    def _expand_query(
        self,
        query: str,
        conversation_history: Optional[List[str]] = None
    ) -> str:
        """
        Expand query with conversation context.
        
        Args:
            query: Cleaned query
            conversation_history: Previous messages
        
        Returns:
            Expanded query for better retrieval
        """
        if not conversation_history:
            return query
        
        # For V1, just append last message if it adds context
        # More sophisticated expansion can be added later
        if len(conversation_history) > 0:
            last_msg = conversation_history[-1]
            # Check if last message is a question (ends with ?)
            if last_msg and not last_msg.endswith('?'):
                # It's likely a previous answer, skip it
                return query
        
        return query
    
    def _retrieve_chunks(self, query: str) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks from vector store.
        
        Args:
            query: Query text
        
        Returns:
            List of retrieval results
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Query vector store
        search_results = self.vector_store.query(
            query_embeddings=[query_embedding],
            n_results=self.max_results
        )
        
        # Convert to RetrievalResult objects
        results = []
        
        if not search_results or not search_results.get('ids'):
            return results
        
        ids = search_results['ids'][0] if search_results['ids'] else []
        distances = search_results['distances'][0] if search_results.get('distances') else []
        metadatas = search_results['metadatas'][0] if search_results.get('metadatas') else []
        documents = search_results['documents'][0] if search_results.get('documents') else []
        
        for i, chunk_id in enumerate(ids):
            # Convert distance to similarity score
            # ChromaDB returns cosine distance where smaller is better
            # For cosine similarity: similarity = 1 - distance
            # But ChromaDB might return different ranges, so we normalize
            distance = distances[i] if i < len(distances) else 1.0
            
            # If distance is very large (>2), it's likely unnormalized - normalize it
            if distance > 2.0:
                # Assume it's a squared distance or unnormalized, clamp to reasonable range
                score = max(0.0, min(1.0, 1.0 / (1.0 + distance / 100.0)))
            else:
                # Normal cosine distance range [0, 2]
                score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            
            # Filter by minimum score
            if score < self.min_score:
                continue
            
            metadata = metadatas[i] if i < len(metadatas) else {}
            content = documents[i] if i < len(documents) else ""
            
            # Create chunk object (simplified - in real use would reconstruct full chunk)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=metadata.get('document_id', ''),
                content=content,
                start_line=metadata.get('start_line', 0),
                end_line=metadata.get('end_line', 0),
                metadata=metadata
            )
            
            results.append(RetrievalResult(
                chunk=chunk,
                score=score,
                document_path=metadata.get('source_file', metadata.get('file_path', 'unknown'))
            ))
        
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _build_context(
        self,
        results: List[RetrievalResult]
    ) -> Tuple[str, int]:
        """
        Build context text from retrieval results.
        
        Args:
            results: List of retrieval results
        
        Returns:
            Tuple of (context_text, total_tokens)
        """
        if not results:
            return "", 0
        
        context_parts = []
        total_tokens = 0
        
        for i, result in enumerate(results):
            # Format: [Source N] path\nContent\n
            source_label = f"[來源 {i+1}] {result.document_path}"
            if result.chunk.start_line > 0:
                source_label += f" (第{result.chunk.start_line}-{result.chunk.end_line}行)"
            
            chunk_text = f"{source_label}\n{result.chunk.content}\n"
            
            # Estimate tokens (rough: 1 token ~= 4 characters for Chinese, ~4 chars for English)
            # Use conservative estimate
            chunk_tokens = len(chunk_text) // 3
            
            # Check if adding this chunk would exceed limit
            if total_tokens + chunk_tokens > self.max_context_tokens:
                break
            
            context_parts.append(chunk_text)
            total_tokens += chunk_tokens
        
        context_text = "\n---\n".join(context_parts)
        
        return context_text, total_tokens
    
    def format_no_results_message(self, query: str) -> str:
        """
        Format message when no results found.
        
        Args:
            query: Original query
        
        Returns:
            Formatted message
        """
        return f"""抱歉，在本機知識庫中找不到關於「{query}」的相關資料。

這可能表示：
1. 本機資料庫尚未包含此主題的文件
2. 查詢用詞與資料庫內容不匹配

**建議**：
- 嘗試使用不同的關鍵字重新查詢
- 確認相關文件是否已加入知識庫
- 如需協助，可以選擇進行網路搜尋（需要連網）

是否需要協助進行外部查詢？"""
