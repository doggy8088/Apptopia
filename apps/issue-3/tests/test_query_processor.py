"""
Tests for Query Processor.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import random
from src.backend.rag.query_processor import (
    QueryProcessor,
    RetrievalResult,
    QueryContext
)
from src.backend.indexer.vector_store import VectorStore
from src.backend.models.document import DocumentChunk


class MockEmbedder:
    """Simple mock embedder for testing."""
    
    def __init__(self):
        self.embedding_dim = 384
        # Use a deterministic random for consistent tests
        self._random = random.Random(42)
    
    def embed_text(self, text: str):
        """Generate a mock embedding based on text hash."""
        # Use text hash to generate deterministic embeddings
        text_hash = hash(text)
        self._random.seed(text_hash)
        return [self._random.random() for _ in range(self.embedding_dim)]
    
    def embed_batch(self, texts: list):
        """Generate batch embeddings."""
        return [self.embed_text(t) for t in texts]


@pytest.fixture
def mock_embedder():
    """Create a mock embedder."""
    return MockEmbedder()


@pytest.fixture
def mock_vector_store(tmp_path, mock_embedder):
    """Create a mock vector store with some data."""
    # Use temporary directory for vector store
    store = VectorStore(
        persist_directory=str(tmp_path / "test_vector_store"),
        collection_name="test"
    )
    
    # Add some test chunks with embeddings
    chunks_data = [
        {
            "id": "chunk1",
            "doc_id": "doc1",
            "content": "Rust 的所有權規則包括：每個值都有一個所有者，一次只能有一個所有者，當所有者離開作用域時值會被丟棄。",
            "start": 10,
            "end": 12,
            "file": "Rust 所有權.md"
        },
        {
            "id": "chunk2",
            "doc_id": "doc1",
            "content": "所有權是 Rust 最獨特的功能，它讓 Rust 可以在不需要垃圾回收的情況下保證記憶體安全。",
            "start": 5,
            "end": 7,
            "file": "Rust 所有權.md"
        },
        {
            "id": "chunk3",
            "doc_id": "doc2",
            "content": "Python 使用垃圾回收來管理記憶體，開發者不需要手動管理。",
            "start": 1,
            "end": 2,
            "file": "Python 記憶體管理.md"
        },
    ]
    
    # Generate embeddings for chunks
    for chunk_data in chunks_data:
        embedding = mock_embedder.embed_text(chunk_data["content"])
        
        ids = [chunk_data["id"]]
        embeddings = [embedding]
        documents = [chunk_data["content"]]
        metadatas = [{
            "document_id": chunk_data["doc_id"],
            "source_file": chunk_data["file"],
            "start_line": chunk_data["start"],
            "end_line": chunk_data["end"]
        }]
        
        store.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    
    return store


@pytest.fixture
def query_processor(mock_vector_store, mock_embedder):
    """Create a query processor with mock vector store and embedder."""
    return QueryProcessor(
        vector_store=mock_vector_store,
        embedder=mock_embedder,
        max_results=5,
        min_score=0.3,
        max_context_tokens=2000
    )


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""
    
    def test_valid_result(self):
        """Test creating valid retrieval result."""
        chunk = DocumentChunk(
            chunk_id="test",
            document_id="doc1",
            content="test content",
            start_line=1,
            end_line=2,
            metadata={}
        )
        
        result = RetrievalResult(
            chunk=chunk,
            score=0.85,
            document_path="test.md"
        )
        
        assert result.score == 0.85
        assert result.document_path == "test.md"
        assert result.chunk.content == "test content"
    
    def test_invalid_score(self):
        """Test that invalid scores raise error."""
        chunk = DocumentChunk(
            chunk_id="test",
            document_id="doc1",
            content="test",
            start_line=1,
            end_line=2,
            metadata={}
        )
        
        with pytest.raises(ValueError):
            RetrievalResult(chunk=chunk, score=1.5, document_path="test.md")
        
        with pytest.raises(ValueError):
            RetrievalResult(chunk=chunk, score=-0.1, document_path="test.md")


class TestQueryContext:
    """Test QueryContext dataclass."""
    
    def test_has_results_true(self):
        """Test has_results when results exist."""
        chunk = DocumentChunk(
            chunk_id="test",
            document_id="doc1",
            content="test",
            start_line=1,
            end_line=2,
            metadata={}
        )
        result = RetrievalResult(chunk=chunk, score=0.8, document_path="test.md")
        
        context = QueryContext(
            query="test query",
            retrieved_chunks=[result],
            total_tokens=10,
            context_text="test context"
        )
        
        assert context.has_results is True
    
    def test_has_results_false(self):
        """Test has_results when no results."""
        context = QueryContext(
            query="test query",
            retrieved_chunks=[],
            total_tokens=0,
            context_text=""
        )
        
        assert context.has_results is False


class TestQueryProcessor:
    """Test QueryProcessor functionality."""
    
    def test_initialization(self, mock_vector_store, mock_embedder):
        """Test query processor initialization."""
        processor = QueryProcessor(
            vector_store=mock_vector_store,
            embedder=mock_embedder,
            max_results=10,
            min_score=0.5,
            max_context_tokens=1000
        )
        
        assert processor.max_results == 10
        assert processor.min_score == 0.5
        assert processor.max_context_tokens == 1000
    
    def test_clean_query(self, query_processor):
        """Test query cleaning."""
        # Extra whitespace
        assert query_processor._clean_query("  test   query  ") == "test query"
        
        # Newlines
        assert query_processor._clean_query("test\nquery") == "test query"
        
        # Mixed
        assert query_processor._clean_query("  test\n  query  ") == "test query"
    
    def test_process_query_with_results(self, query_processor):
        """Test processing query that returns results."""
        context = query_processor.process_query("Rust 所有權")
        
        assert context.query == "Rust 所有權"
        assert context.has_results is True
        assert len(context.retrieved_chunks) > 0
        assert context.total_tokens > 0
        assert len(context.context_text) > 0
        
        # Check that results are sorted by score
        if len(context.retrieved_chunks) > 1:
            scores = [r.score for r in context.retrieved_chunks]
            assert scores == sorted(scores, reverse=True)
    
    def test_process_query_no_results(self, query_processor):
        """Test processing query with no matching results."""
        # Query for something not in the mock data
        context = query_processor.process_query("completely unrelated topic xyz123")
        
        # Depending on mock implementation, might return low-score results
        # or no results
        assert context.query == "completely unrelated topic xyz123"
        assert context.total_tokens >= 0
    
    def test_expand_query_without_history(self, query_processor):
        """Test query expansion without conversation history."""
        query = "test query"
        expanded = query_processor._expand_query(query, None)
        
        assert expanded == query
    
    def test_expand_query_with_history(self, query_processor):
        """Test query expansion with conversation history."""
        query = "什麼是所有權？"
        history = ["Rust 是什麼？", "Rust 是一個系統程式語言"]
        
        expanded = query_processor._expand_query(query, history)
        
        # For V1, should return original query
        assert expanded == query
    
    def test_retrieve_chunks(self, query_processor):
        """Test chunk retrieval."""
        results = query_processor._retrieve_chunks("Rust 所有權")
        
        # Should get some results from mock store
        assert isinstance(results, list)
        
        # All results should have valid scores
        for result in results:
            assert 0 <= result.score <= 1
            assert isinstance(result.chunk, DocumentChunk)
    
    def test_build_context(self, query_processor):
        """Test context building from results."""
        chunk1 = DocumentChunk(
            chunk_id="c1",
            document_id="d1",
            content="內容一",
            start_line=10,
            end_line=15,
            metadata={}
        )
        chunk2 = DocumentChunk(
            chunk_id="c2",
            document_id="d2",
            content="內容二",
            start_line=20,
            end_line=25,
            metadata={}
        )
        
        results = [
            RetrievalResult(chunk=chunk1, score=0.9, document_path="file1.md"),
            RetrievalResult(chunk=chunk2, score=0.8, document_path="file2.md"),
        ]
        
        context_text, total_tokens = query_processor._build_context(results)
        
        assert len(context_text) > 0
        assert total_tokens > 0
        assert "來源 1" in context_text
        assert "來源 2" in context_text
        assert "file1.md" in context_text
        assert "file2.md" in context_text
    
    def test_build_context_empty(self, query_processor):
        """Test building context with no results."""
        context_text, total_tokens = query_processor._build_context([])
        
        assert context_text == ""
        assert total_tokens == 0
    
    def test_format_no_results_message(self, query_processor):
        """Test formatting no results message."""
        message = query_processor.format_no_results_message("test query")
        
        assert "test query" in message
        assert "本機知識庫" in message
        assert "建議" in message
        assert "外部查詢" in message
    
    def test_max_context_tokens_limit(self, mock_vector_store, mock_embedder):
        """Test that context respects token limit."""
        processor = QueryProcessor(
            vector_store=mock_vector_store,
            embedder=mock_embedder,
            max_results=10,
            min_score=0.0,  # Accept all results
            max_context_tokens=50  # Very small limit
        )
        
        context = processor.process_query("Rust Python")
        
        # Should not exceed token limit
        assert context.total_tokens <= 50
    
    def test_min_score_filtering(self, mock_vector_store, mock_embedder):
        """Test that low-score results are filtered."""
        processor = QueryProcessor(
            vector_store=mock_vector_store,
            embedder=mock_embedder,
            max_results=10,
            min_score=0.9,  # Very high threshold
            max_context_tokens=2000
        )
        
        context = processor.process_query("test")
        
        # All results should meet min score
        for result in context.retrieved_chunks:
            assert result.score >= 0.9
