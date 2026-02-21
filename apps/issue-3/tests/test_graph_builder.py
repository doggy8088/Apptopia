"""
Tests for Graph Builder.

Tests the complete graph building pipeline including:
- Node creation
- Edge creation with weighted scores
- Wikilink, vector similarity, and keyword scoring
- Edge pruning
"""

import pytest
from pathlib import Path
from datetime import datetime

from src.backend.graph.builder import (
    GraphNode,
    GraphEdge,
    DocumentGraph,
    GraphBuilder
)
from src.backend.models.document import (
    Document,
    DocumentMetadata,
    DocumentChunk,
    Relationship,
    DocumentStatus
)


# --- Fixtures ---

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    # Document 1: Rust
    doc1 = Document(
        doc_id="rust-ownership",
        file_path=Path("/test/rust-ownership.md"),
        relative_path=Path("rust-ownership.md"),
        source_folder="test",
        raw_content="Rust 所有權系統確保記憶體安全",
        parsed_content="Rust 所有權系統確保記憶體安全",
        metadata=DocumentMetadata(
            title="Rust 所有權",
            tags=["程式語言/Rust", "記憶體管理"],
            word_count=100
        ),
        chunks=[],
        relationships=[],
        status=DocumentStatus.ACTIVE
    )
    
    # Document 2: Python
    doc2 = Document(
        doc_id="python-gc",
        file_path=Path("/test/python-gc.md"),
        relative_path=Path("python-gc.md"),
        source_folder="test",
        raw_content="Python 使用垃圾回收管理記憶體",
        parsed_content="Python 使用垃圾回收管理記憶體",
        metadata=DocumentMetadata(
            title="Python 記憶體管理",
            tags=["程式語言/Python", "記憶體管理"],
            word_count=80
        ),
        chunks=[],
        relationships=[],
        status=DocumentStatus.ACTIVE
    )
    
    # Document 3: C++ (links to Rust)
    doc3 = Document(
        doc_id="cpp-memory",
        file_path=Path("/test/cpp-memory.md"),
        relative_path=Path("cpp-memory.md"),
        source_folder="test",
        raw_content="C++ 手動管理記憶體",
        parsed_content="C++ 手動管理記憶體",
        metadata=DocumentMetadata(
            title="C++ 記憶體管理",
            tags=["程式語言/C++", "記憶體管理"],
            word_count=90
        ),
        chunks=[],
        relationships=[
            Relationship(
                source_doc_id="cpp-memory",
                target_doc_id="rust-ownership",
                relationship_type="wikilink"
            )
        ],
        status=DocumentStatus.ACTIVE
    )
    
    return [doc1, doc2, doc3]


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    return {
        "rust-ownership": [0.8, 0.6, 0.4],  # Similar to C++
        "python-gc": [0.3, 0.9, 0.7],       # Different direction
        "cpp-memory": [0.7, 0.5, 0.3]       # Similar to Rust
    }


# --- GraphNode Tests ---

def test_graph_node_creation():
    """Test GraphNode creation."""
    node = GraphNode(
        doc_id="test-1",
        title="Test Document",
        file_path="/test/doc.md",
        tags=["test", "sample"]
    )
    
    assert node.doc_id == "test-1"
    assert node.title == "Test Document"
    assert node.degree == 0
    assert node.centrality == 0.0
    assert node.community is None


def test_graph_node_with_metadata():
    """Test GraphNode with metadata."""
    node = GraphNode(
        doc_id="test-2",
        title="Test",
        file_path="/test",
        metadata={"word_count": 100}
    )
    
    assert node.metadata["word_count"] == 100


# --- GraphEdge Tests ---

def test_graph_edge_creation():
    """Test GraphEdge creation."""
    edge = GraphEdge(
        source_id="doc1",
        target_id="doc2",
        wikilink_score=1.0,
        vector_score=0.8,
        keyword_score=0.6
    )
    
    edge.calculate_weight()
    
    # Combined: 0.2*1.0 + 0.5*0.8 + 0.3*0.6 = 0.2 + 0.4 + 0.18 = 0.78
    assert abs(edge.weight - 0.78) < 0.01


def test_graph_edge_weights():
    """Test edge weight calculation with different scores."""
    # Only wikilink
    edge1 = GraphEdge("a", "b", wikilink_score=1.0)
    edge1.calculate_weight()
    assert abs(edge1.weight - 0.2) < 0.01  # 0.2 * 1.0
    
    # Only vector
    edge2 = GraphEdge("a", "b", vector_score=1.0)
    edge2.calculate_weight()
    assert abs(edge2.weight - 0.5) < 0.01  # 0.5 * 1.0
    
    # Only keyword
    edge3 = GraphEdge("a", "b", keyword_score=1.0)
    edge3.calculate_weight()
    assert abs(edge3.weight - 0.3) < 0.01  # 0.3 * 1.0


# --- DocumentGraph Tests ---

def test_document_graph_creation():
    """Test DocumentGraph creation."""
    graph = DocumentGraph()
    
    assert graph.total_nodes == 0
    assert graph.total_edges == 0


def test_document_graph_add_node():
    """Test adding nodes to graph."""
    graph = DocumentGraph()
    node = GraphNode("doc1", "Test", "/test")
    
    graph.add_node(node)
    
    assert graph.total_nodes == 1
    assert graph.get_node("doc1") == node


def test_document_graph_add_edge():
    """Test adding edges to graph."""
    graph = DocumentGraph()
    node1 = GraphNode("doc1", "Test1", "/test1")
    node2 = GraphNode("doc2", "Test2", "/test2")
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    edge = GraphEdge("doc1", "doc2", weight=0.8)
    graph.add_edge(edge)
    
    assert graph.total_edges == 1
    assert node1.degree == 1
    assert node2.degree == 1


def test_document_graph_get_edges_for_node():
    """Test retrieving edges for a node."""
    graph = DocumentGraph()
    
    graph.add_node(GraphNode("doc1", "Test1", "/test1"))
    graph.add_node(GraphNode("doc2", "Test2", "/test2"))
    graph.add_node(GraphNode("doc3", "Test3", "/test3"))
    
    graph.add_edge(GraphEdge("doc1", "doc2", weight=0.8))
    graph.add_edge(GraphEdge("doc1", "doc3", weight=0.6))
    
    edges = graph.get_edges_for_node("doc1")
    
    assert len(edges) == 2
    assert all(e.source_id == "doc1" or e.target_id == "doc1" for e in edges)


# --- GraphBuilder Tests ---

def test_graph_builder_creation():
    """Test GraphBuilder initialization."""
    builder = GraphBuilder()
    
    assert builder.min_edge_weight == 0.1
    assert builder.max_edges_per_node == 20


def test_graph_builder_custom_params():
    """Test GraphBuilder with custom parameters."""
    builder = GraphBuilder(
        min_edge_weight=0.3,
        max_edges_per_node=5
    )
    
    assert builder.min_edge_weight == 0.3
    assert builder.max_edges_per_node == 5


def test_build_graph_nodes(sample_documents):
    """Test building graph nodes from documents."""
    builder = GraphBuilder()
    graph = builder.build_graph(sample_documents)
    
    assert graph.total_nodes == 3
    assert "rust-ownership" in graph.nodes
    assert "python-gc" in graph.nodes
    assert "cpp-memory" in graph.nodes


def test_build_graph_with_wikilinks(sample_documents):
    """Test graph building with wikilinks."""
    builder = GraphBuilder(min_edge_weight=0.0)
    graph = builder.build_graph(sample_documents)
    
    # Should have edge from cpp-memory to rust-ownership
    edges = graph.get_edges_for_node("cpp-memory")
    rust_edges = [e for e in edges if "rust-ownership" in [e.source_id, e.target_id]]
    
    assert len(rust_edges) > 0
    assert any(e.wikilink_score > 0 for e in rust_edges)


def test_build_graph_with_embeddings(sample_documents, sample_embeddings):
    """Test graph building with vector embeddings."""
    builder = GraphBuilder(min_edge_weight=0.0)
    graph = builder.build_graph(sample_documents, sample_embeddings)
    
    # Should calculate vector similarities
    edges = graph.edges
    assert any(e.vector_score > 0 for e in edges)


def test_build_graph_keyword_matching(sample_documents):
    """Test keyword-based edge creation."""
    builder = GraphBuilder(min_edge_weight=0.0)
    graph = builder.build_graph(sample_documents)
    
    # All docs share "記憶體管理" tag
    edges = graph.edges
    assert any(e.keyword_score > 0 for e in edges)


def test_edge_weight_threshold(sample_documents):
    """Test edge filtering by minimum weight."""
    # High threshold - fewer edges
    builder = GraphBuilder(min_edge_weight=0.5)
    graph = builder.build_graph(sample_documents)
    
    assert all(e.weight >= 0.5 for e in graph.edges)


def test_edge_pruning(sample_documents):
    """Test edge pruning to limit connections."""
    builder = GraphBuilder(
        min_edge_weight=0.0,
        max_edges_per_node=1  # Limit to 1 edge per node
    )
    graph = builder.build_graph(sample_documents)
    
    # With 3 nodes and max 1 edge per node, we should have at most 2 edges total
    # (since each edge connects 2 nodes, and we want roughly 1 edge per node)
    # Due to voting mechanism, a node might end up with up to max_edges_per_node + 1
    # but the total should be reasonable
    assert graph.total_edges <= 3  # With 3 nodes, max reasonable is 3 edges
    
    # Verify pruning worked - without it we'd have more edges
    assert graph.total_edges < 3  # Should be less than all possible pairs


def test_wikilink_score_calculation():
    """Test wikilink score calculation."""
    builder = GraphBuilder()
    
    # Create docs with wikilink
    doc1 = Document(
        doc_id="doc1",
        file_path=Path("/test/doc1.md"),
        relative_path=Path("doc1.md"),
        source_folder="test",
        raw_content="Test",
        parsed_content="Test",
        metadata=DocumentMetadata(title="Doc1"),
        chunks=[],
        relationships=[
            Relationship(
                source_doc_id="doc1",
                target_doc_id="doc2",
                relationship_type="wikilink"
            )
        ],
        status=DocumentStatus.ACTIVE
    )
    
    doc2 = Document(
        doc_id="doc2",
        file_path=Path("/test/doc2.md"),
        relative_path=Path("doc2.md"),
        source_folder="test",
        raw_content="Test",
        parsed_content="Test",
        metadata=DocumentMetadata(title="Doc2"),
        chunks=[],
        relationships=[],
        status=DocumentStatus.ACTIVE
    )
    
    score = builder._calculate_wikilink_score(doc1, doc2)
    assert score == 1.0


def test_vector_score_calculation():
    """Test vector similarity score calculation."""
    builder = GraphBuilder()
    
    # Identical vectors
    embeddings = {
        "doc1": [1.0, 0.0, 0.0],
        "doc2": [1.0, 0.0, 0.0]
    }
    score = builder._calculate_vector_score("doc1", "doc2", embeddings)
    assert abs(score - 1.0) < 0.01
    
    # Opposite vectors
    embeddings = {
        "doc1": [1.0, 0.0, 0.0],
        "doc2": [-1.0, 0.0, 0.0]
    }
    score = builder._calculate_vector_score("doc1", "doc2", embeddings)
    assert abs(score - 0.0) < 0.01


def test_keyword_extraction(sample_documents):
    """Test keyword extraction from documents."""
    builder = GraphBuilder()
    
    keywords1 = builder._extract_keywords(sample_documents[0])  # Rust doc
    
    # Should extract from tags and title
    assert len(keywords1) > 0
    assert any("rust" in k.lower() for k in keywords1)


def test_keyword_score_calculation(sample_documents):
    """Test keyword score calculation."""
    builder = GraphBuilder()
    
    # Rust and Python both have "記憶體管理" tag
    score = builder._calculate_keyword_score(
        sample_documents[0],
        sample_documents[1]
    )
    
    # Should have overlap
    assert score > 0


def test_empty_document_list():
    """Test building graph with no documents."""
    builder = GraphBuilder()
    graph = builder.build_graph([])
    
    assert graph.total_nodes == 0
    assert graph.total_edges == 0


def test_single_document():
    """Test building graph with single document."""
    builder = GraphBuilder()
    
    doc = Document(
        doc_id="single",
        file_path=Path("/test/single.md"),
        relative_path=Path("single.md"),
        source_folder="test",
        raw_content="Test",
        parsed_content="Test",
        metadata=DocumentMetadata(title="Single"),
        chunks=[],
        relationships=[],
        status=DocumentStatus.ACTIVE
    )
    
    graph = builder.build_graph([doc])
    
    assert graph.total_nodes == 1
    assert graph.total_edges == 0  # No edges with single node


def test_relationship_type_determination():
    """Test determining relationship type based on scores."""
    builder = GraphBuilder()
    
    # Wikilink dominant
    edge1 = GraphEdge("a", "b", wikilink_score=1.0, vector_score=0.5, keyword_score=0.3)
    edge1.calculate_weight()
    
    doc_a = Document(
        "a", Path("/a"), Path("a"), "test", "test", "test", 
        DocumentMetadata(), [], 
        [Relationship("a", "b", "wikilink")], 
        DocumentStatus.ACTIVE
    )
    doc_b = Document(
        "b", Path("/b"), Path("b"), "test", "test", "test",
        DocumentMetadata(), [], [], 
        DocumentStatus.ACTIVE
    )
    
    result1 = builder._build_edge(doc_a, doc_b, None)
    assert result1.relationship_type == "wikilink"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
