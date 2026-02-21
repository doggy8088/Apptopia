"""
Tests for Graph Analyzer

Tests community detection, centrality metrics, hub identification,
path finding, and other graph analysis capabilities.
"""

import pytest
from src.backend.graph.builder import (
    GraphBuilder, GraphNode, GraphEdge, DocumentGraph
)
from src.backend.graph.analyzer import (
    GraphAnalyzer, CommunityInfo, HubDocument, PathInfo
)
from src.backend.models.document import Document, DocumentMetadata, Relationship


def create_test_documents():
    """Create test documents for graph analysis"""
    docs = []
    
    # Create documents with relationships
    for i in range(10):
        doc = Document(
            doc_id=f"doc{i}",
            file_path=f"/test/doc{i}.md",
            content=f"Content {i}",
            metadata=DocumentMetadata(
                title=f"Document {i}",
                tags=[f"tag{i % 3}"],  # Group into 3 clusters
                created_at="2024-01-01T00:00:00",
                modified_at="2024-01-01T00:00:00"
            ),
            chunks=[],
            relationships=[]
        )
        docs.append(doc)
    
    # Add some wikilink relationships
    docs[0].relationships.append(Relationship(
        source_doc_id="doc0",
        target_doc_id="doc1",
        relationship_type="wikilink"
    ))
    docs[1].relationships.append(Relationship(
        source_doc_id="doc1",
        target_doc_id="doc2",
        relationship_type="wikilink"
    ))
    docs[3].relationships.append(Relationship(
        source_doc_id="doc3",
        target_doc_id="doc4",
        relationship_type="wikilink"
    ))
    docs[6].relationships.append(Relationship(
        source_doc_id="doc6",
        target_doc_id="doc7",
        relationship_type="wikilink"
    ))
    
    return docs


def create_test_graph():
    """Create a test graph for analysis"""
    # Create simple graph with known structure
    graph = DocumentGraph()
    
    # Add nodes (3 clusters of nodes)
    for i in range(9):
        node = GraphNode(
            doc_id=f"doc{i}",
            title=f"Document {i}",
            file_path=f"/test/doc{i}.md",
            tags=[f"tag{i // 3}"],  # Create 3 groups
            metadata={}
        )
        graph.add_node(node)
    
    # Add edges to create communities
    # Cluster 0: doc0, doc1, doc2 (tightly connected)
    graph.add_edge(GraphEdge("doc0", "doc1", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc1", "doc2", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc0", "doc2", 0.8, 0.0, 0.8, 0.0, "similarity"))
    
    # Cluster 1: doc3, doc4, doc5 (tightly connected)
    graph.add_edge(GraphEdge("doc3", "doc4", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc4", "doc5", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc3", "doc5", 0.8, 0.0, 0.8, 0.0, "similarity"))
    
    # Cluster 2: doc6, doc7, doc8 (tightly connected)
    graph.add_edge(GraphEdge("doc6", "doc7", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc7", "doc8", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc6", "doc8", 0.8, 0.0, 0.8, 0.0, "similarity"))
    
    # Add some inter-cluster edges (weaker)
    graph.add_edge(GraphEdge("doc2", "doc3", 0.3, 0.0, 0.3, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc5", "doc6", 0.3, 0.0, 0.3, 0.0, "similarity"))
    
    return graph


# Test Community Detection

def test_analyzer_initialization():
    """Test analyzer initialization"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    assert analyzer.graph == graph
    assert analyzer.nx_graph is not None
    assert analyzer._communities is None
    assert analyzer._pagerank is None


def test_detect_communities():
    """Test community detection"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    communities = analyzer.detect_communities()
    
    # Should detect communities
    assert len(communities) > 0
    assert all(isinstance(c, CommunityInfo) for c in communities)
    
    # Check community properties
    for comm in communities:
        assert comm.size > 0
        assert len(comm.nodes) == comm.size
        assert 0.0 <= comm.density <= 1.0
        assert comm.avg_centrality >= 0.0


def test_communities_update_nodes():
    """Test that community detection updates node information"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    # Before detection, nodes have no community
    assert all(node.community is None for node in graph.nodes.values())
    
    communities = analyzer.detect_communities()
    
    # After detection, nodes should have community assignments
    assert any(node.community is not None for node in graph.nodes.values())


# Test Centrality Metrics

def test_calculate_pagerank():
    """Test PageRank calculation"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    pagerank = analyzer.calculate_pagerank()
    
    # Should have PageRank for all nodes
    assert len(pagerank) == graph.total_nodes
    assert all(0.0 <= score <= 1.0 for score in pagerank.values())
    
    # Sum of PageRank scores should be close to 1.0
    total = sum(pagerank.values())
    assert abs(total - 1.0) < 0.01
    
    # Nodes should be updated
    for node_id, node in graph.nodes.items():
        assert node.centrality > 0.0


def test_calculate_degree_centrality():
    """Test degree centrality calculation"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    degree_cent = analyzer.calculate_degree_centrality()
    
    # Should have degree centrality for all nodes
    assert len(degree_cent) == graph.total_nodes
    assert all(0.0 <= score <= 1.0 for score in degree_cent.values())
    
    # Nodes should have degree updated
    for node in graph.nodes.values():
        assert node.degree >= 0


def test_calculate_betweenness_centrality():
    """Test betweenness centrality calculation"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    betweenness = analyzer.calculate_betweenness_centrality()
    
    # Should have betweenness for all nodes
    assert len(betweenness) == graph.total_nodes
    assert all(score >= 0.0 for score in betweenness.values())


# Test Hub Identification

def test_identify_hubs():
    """Test hub document identification"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    hubs = analyzer.identify_hubs(top_n=5)
    
    # Should return top hubs
    assert len(hubs) <= 5
    assert all(isinstance(h, HubDocument) for h in hubs)
    
    # Hubs should have valid properties
    for hub in hubs:
        assert hub.doc_id in graph.nodes
        assert hub.degree >= 0
        assert hub.pagerank > 0.0
        assert hub.betweenness >= 0.0


def test_hubs_sorted_by_importance():
    """Test that hubs are sorted by combined importance"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    hubs = analyzer.identify_hubs(top_n=graph.total_nodes)
    
    # Hubs should be sorted (higher scores first)
    for i in range(len(hubs) - 1):
        # Combined score should be decreasing or equal
        score1 = 0.5 * hubs[i].pagerank + 0.3 * hubs[i].betweenness
        score2 = 0.5 * hubs[i+1].pagerank + 0.3 * hubs[i+1].betweenness
        assert score1 >= score2


# Test Path Finding

def test_find_shortest_path_exists():
    """Test finding shortest path when path exists"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    # Path exists between doc0 and doc2
    path_info = analyzer.find_shortest_path("doc0", "doc2")
    
    assert path_info is not None
    assert isinstance(path_info, PathInfo)
    assert path_info.source_id == "doc0"
    assert path_info.target_id == "doc2"
    assert len(path_info.path) >= 2
    assert path_info.length >= 1
    assert path_info.total_weight > 0.0


def test_find_shortest_path_not_exists():
    """Test finding shortest path when no path exists"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    # Add isolated node
    isolated_node = GraphNode("isolated", "Isolated", "/isolated.md", [], {})
    graph.add_node(isolated_node)
    analyzer = GraphAnalyzer(graph)  # Recreate with new graph
    
    # No path to isolated node
    path_info = analyzer.find_shortest_path("doc0", "isolated")
    
    assert path_info is None


def test_find_all_paths():
    """Test finding all paths between nodes"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    # Find all paths from doc0 to doc5
    paths = analyzer.find_all_paths("doc0", "doc5", max_length=5)
    
    # Should find at least one path
    assert len(paths) > 0
    assert all(isinstance(p, PathInfo) for p in paths)
    
    # All paths should start and end correctly
    for path in paths:
        assert path.source_id == "doc0"
        assert path.target_id == "doc5"
        assert path.path[0] == "doc0"
        assert path.path[-1] == "doc5"
        assert path.length <= 5


# Test Neighbors

def test_get_neighbors_one_hop():
    """Test getting 1-hop neighbors"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    neighbors = analyzer.get_neighbors("doc0", max_distance=1)
    
    # Should have neighbors at distance 1
    assert 1 in neighbors
    assert len(neighbors[1]) > 0
    
    # doc1 and doc2 should be neighbors
    assert "doc1" in neighbors[1] or "doc2" in neighbors[1]


def test_get_neighbors_two_hops():
    """Test getting 2-hop neighbors"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    neighbors = analyzer.get_neighbors("doc0", max_distance=2)
    
    # Should have neighbors at distances 1 and possibly 2
    assert 1 in neighbors
    
    # Total neighbors should be reasonable
    total_neighbors = sum(len(nodes) for nodes in neighbors.values())
    assert total_neighbors > 0


# Test Clustering

def test_calculate_clustering_coefficient():
    """Test clustering coefficient calculation"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    clustering = analyzer.calculate_clustering_coefficient()
    
    # Should have clustering for all nodes
    assert len(clustering) == graph.total_nodes
    assert all(0.0 <= c <= 1.0 for c in clustering.values())


# Test Graph Statistics

def test_get_graph_statistics():
    """Test overall graph statistics"""
    graph = create_test_graph()
    analyzer = GraphAnalyzer(graph)
    
    stats = analyzer.get_graph_statistics()
    
    # Should have all expected statistics
    assert "nodes" in stats
    assert "edges" in stats
    assert "density" in stats
    assert "is_connected" in stats
    assert "avg_clustering" in stats
    assert "avg_degree" in stats
    
    # Values should be reasonable
    assert stats["nodes"] == graph.total_nodes
    assert stats["edges"] == graph.total_edges
    assert 0.0 <= stats["density"] <= 1.0
    assert stats["avg_degree"] >= 0.0
