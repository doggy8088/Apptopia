"""
Integration Tests

Tests the integration of multiple components working together end-to-end.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backend.core.processor import DocumentProcessor
from backend.core.file_scanner import FileScanner
from backend.core.obsidian_parser import ObsidianParser
from backend.core.chunker import DocumentChunker
from backend.core.embedder import Embedder
from backend.indexer.vector_store import VectorStore
from backend.rag.engine import RAGEngine, RAGConfig
from backend.rag.llm_client import MockLLMClient
from backend.rag.query_processor import QueryProcessor
from backend.rag.conversation import ConversationManager
from backend.rag.response_generator import ResponseGenerator
from backend.graph.builder import GraphBuilder
from backend.graph.analyzer import GraphAnalyzer
from backend.graph.visualizer import GraphVisualizer
from backend.migration.exporter import ExportManager
from backend.migration.importer import ImportManager
from backend.migration.verifier import SourceVerifier
from backend.models.document import Document, DocumentMetadata, DocumentChunk


@pytest.fixture
def test_vault(tmp_path):
    """Create a test Obsidian vault."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    
    # Create test documents
    (vault / "doc1.md").write_text("""# Rust 所有權

Rust 的所有權系統包括三個核心規則：

1. 每個值都有一個所有者
2. 一次只能有一個所有者
3. 當所有者離開作用域時，值會被丟棄

這確保了記憶體安全。

[[doc2]] 提供更多範例。
""", encoding="utf-8")
    
    (vault / "doc2.md").write_text("""# Rust 範例

這裡有一些 Rust 程式碼範例：

```rust
fn main() {
    let s = String::from("hello");
}  // s 離開作用域，記憶體被釋放
```

參考 [[doc1|所有權規則]]。

#rust #programming
""", encoding="utf-8")
    
    (vault / "doc3.md").write_text("""# Python 基礎

Python 是一種高階程式語言。

特點：
- 簡單易學
- 豐富的函式庫
- 適合初學者

#python #programming
""", encoding="utf-8")
    
    return vault


@pytest.fixture
def vector_store(tmp_path):
    """Create a vector store."""
    return VectorStore(persist_directory=str(tmp_path / "chroma"))


@pytest.fixture
def embedder(tmp_path):
    """Create an embedder with cache."""
    return Embedder(cache_dir=str(tmp_path / "cache"))


class TestEndToEndIndexing:
    """Test complete indexing workflow."""
    
    def test_index_to_query_workflow(self, test_vault, vector_store, embedder, tmp_path):
        """Test: Index documents → Query → Get response."""
        # Step 1: Index documents
        processor = DocumentProcessor(
            vector_store=vector_store,
            embedder=embedder,
            use_ocr=False
        )
        
        result = processor.process_folder(test_vault, force_reindex=True)
        
        # Verify indexing
        assert result["processed_count"] >= 3
        assert result["success"] is True
        
        # Step 2: Build RAG engine
        query_processor = QueryProcessor(
            vector_store=vector_store,
            embedder=embedder
        )
        llm_client = MockLLMClient()
        conversation_manager = ConversationManager(
            storage_dir=str(tmp_path / "conversations")
        )
        response_generator = ResponseGenerator()
        
        rag_engine = RAGEngine(
            query_processor=query_processor,
            llm_client=llm_client,
            conversation_manager=conversation_manager,
            response_generator=response_generator,
            config=RAGConfig()
        )
        
        # Step 3: Execute query
        result = rag_engine.query("什麼是 Rust 所有權？")
        
        # Verify response
        assert result.has_local_data is True
        assert result.response is not None
        assert result.retrieved_chunks_count > 0
        assert result.processing_time > 0
        
        # Verify response has citations
        assert len(result.response.citations) > 0


class TestExportImportCycle:
    """Test export-import-verify workflow."""
    
    def test_export_import_verify_workflow(self, test_vault, vector_store, embedder, tmp_path):
        """Test: Index → Export → Import → Verify."""
        # Step 1: Index documents
        processor = DocumentProcessor(
            vector_store=vector_store,
            embedder=embedder,
            use_ocr=False
        )
        
        result = processor.process_folder(test_vault, force_reindex=True)
        assert result["success"] is True
        
        # Get documents (create sample for testing)
        documents = [
            Document(
                doc_id="doc1",
                title="Test Doc 1",
                content="Test content 1",
                file_path=str(test_vault / "doc1.md"),
                metadata=DocumentMetadata(
                    author="Test",
                    created_at="2024-01-01",
                    modified_at="2024-01-01",
                    tags=["test"],
                    file_size=100,
                    language="zh"
                ),
                chunks=[],
                relationships=[],
                status="active"
            )
        ]
        
        # Step 2: Export
        export_dir = tmp_path / "export"
        export_manager = ExportManager(
            vector_store=vector_store,
            export_dir=export_dir
        )
        
        export_path = export_manager.export_all(
            documents=documents,
            source_folders=[str(test_vault)],
            create_archive=True
        )
        
        assert export_path.exists()
        assert export_path.suffix == ".zip"
        
        # Step 3: Import
        import_dir = tmp_path / "import"
        import_dir.mkdir()
        
        vector_store2 = VectorStore(persist_directory=str(import_dir / "chroma"))
        
        import_manager = ImportManager(
            vector_store=vector_store2,
            import_source=export_path
        )
        
        imported_docs = import_manager.import_all()
        
        # Verify import
        assert len(imported_docs) > 0
        
        # Step 4: Verify sources
        verifier = SourceVerifier()
        report = verifier.verify_sources(
            documents=imported_docs,
            source_folders=[test_vault]
        )
        
        # Verify report
        assert report.total_sources >= 1
        assert report.available_sources >= 1


class TestGraphGeneration:
    """Test knowledge graph generation workflow."""
    
    def test_graph_building_and_export(self, test_vault, vector_store, embedder):
        """Test: Index → Build Graph → Analyze → Export."""
        # Step 1: Index documents
        processor = DocumentProcessor(
            vector_store=vector_store,
            embedder=embedder,
            use_ocr=False
        )
        
        result = processor.process_folder(test_vault, force_reindex=True)
        assert result["success"] is True
        
        # Create sample documents with relationships
        documents = [
            Document(
                doc_id="doc1",
                title="Rust 所有權",
                content="Rust ownership content",
                file_path=str(test_vault / "doc1.md"),
                metadata=DocumentMetadata(
                    author="Test",
                    created_at="2024-01-01",
                    modified_at="2024-01-01",
                    tags=["rust"],
                    file_size=100,
                    language="zh"
                ),
                chunks=[],
                relationships=[],
                status="active"
            ),
            Document(
                doc_id="doc2",
                title="Rust 範例",
                content="Rust examples",
                file_path=str(test_vault / "doc2.md"),
                metadata=DocumentMetadata(
                    author="Test",
                    created_at="2024-01-01",
                    modified_at="2024-01-01",
                    tags=["rust", "programming"],
                    file_size=150,
                    language="zh"
                ),
                chunks=[],
                relationships=[],
                status="active"
            )
        ]
        
        # Step 2: Build graph
        builder = GraphBuilder()
        graph = builder.build_graph(documents)
        
        # Verify graph
        assert graph.total_nodes >= 2
        
        # Step 3: Analyze graph
        analyzer = GraphAnalyzer(graph)
        communities = analyzer.detect_communities()
        analyzer.calculate_centrality()
        
        # Verify analysis
        assert len(communities) > 0
        
        # Step 4: Export graph
        visualizer = GraphVisualizer(graph)
        d3_json = visualizer.to_d3_json()
        
        # Verify export
        assert "nodes" in d3_json
        assert "links" in d3_json


class TestMultiTurnConversation:
    """Test multi-turn conversation workflow."""
    
    def test_conversation_with_context(self, test_vault, vector_store, embedder, tmp_path):
        """Test: Multi-turn conversation with context retention."""
        # Step 1: Index documents
        processor = DocumentProcessor(
            vector_store=vector_store,
            embedder=embedder,
            use_ocr=False
        )
        
        result = processor.process_folder(test_vault, force_reindex=True)
        assert result["success"] is True
        
        # Step 2: Build RAG engine
        query_processor = QueryProcessor(
            vector_store=vector_store,
            embedder=embedder
        )
        llm_client = MockLLMClient()
        conversation_manager = ConversationManager(
            storage_dir=str(tmp_path / "conversations")
        )
        response_generator = ResponseGenerator()
        
        rag_engine = RAGEngine(
            query_processor=query_processor,
            llm_client=llm_client,
            conversation_manager=conversation_manager,
            response_generator=response_generator,
            config=RAGConfig()
        )
        
        # Step 3: First query
        result1 = rag_engine.query(
            query="什麼是 Rust？",
            conversation_id="test-session"
        )
        
        assert result1.conversation_id == "test-session"
        assert result1.turn_count == 1
        
        # Step 4: Follow-up query
        result2 = rag_engine.query(
            query="它的主要特點是什麼？",
            conversation_id="test-session"
        )
        
        # Verify conversation continuity
        assert result2.conversation_id == "test-session"
        assert result2.turn_count == 2
        
        # Step 5: Third query
        result3 = rag_engine.query(
            query="給我一個範例",
            conversation_id="test-session"
        )
        
        assert result3.turn_count == 3


class TestErrorHandling:
    """Test error handling across components."""
    
    def test_missing_source_handling(self, vector_store, embedder, tmp_path):
        """Test: Handle missing source folders gracefully."""
        # Create documents with missing source
        documents = [
            Document(
                doc_id="doc1",
                title="Test",
                content="Content",
                file_path="/nonexistent/path/doc.md",
                metadata=DocumentMetadata(
                    author="Test",
                    created_at="2024-01-01",
                    modified_at="2024-01-01",
                    tags=[],
                    file_size=100,
                    language="zh"
                ),
                chunks=[],
                relationships=[],
                status="active"
            )
        ]
        
        # Verify sources
        verifier = SourceVerifier()
        report = verifier.verify_sources(
            documents=documents,
            source_folders=[Path("/nonexistent/path")]
        )
        
        # Verify handling
        assert report.missing_sources == 1
        assert report.available_sources == 0
        assert report.frozen_documents == 1
    
    def test_empty_query_handling(self, vector_store, embedder, tmp_path):
        """Test: Handle empty query gracefully."""
        query_processor = QueryProcessor(
            vector_store=vector_store,
            embedder=embedder
        )
        llm_client = MockLLMClient()
        conversation_manager = ConversationManager(
            storage_dir=str(tmp_path / "conversations")
        )
        response_generator = ResponseGenerator()
        
        rag_engine = RAGEngine(
            query_processor=query_processor,
            llm_client=llm_client,
            conversation_manager=conversation_manager,
            response_generator=response_generator,
            config=RAGConfig()
        )
        
        # Query with no matching results
        result = rag_engine.query("xyzabc123nonexistent")
        
        # Verify graceful handling
        assert result is not None
        assert result.has_local_data is False
