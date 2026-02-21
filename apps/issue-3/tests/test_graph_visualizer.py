"""
Tests for Graph Visualizer

Tests export functionality for D3.js, Mermaid, Obsidian, and GraphML formats.
"""

import pytest
import json
from src.backend.graph.builder import GraphBuilder, GraphNode, GraphEdge, DocumentGraph
from src.backend.graph.visualizer import GraphVisualizer, D3Node, D3Link, D3Graph


def create_test_graph():
    """Create a test graph for visualization"""
    graph = DocumentGraph()
    
    # Add nodes
    for i in range(6):
        node = GraphNode(
            doc_id=f"doc{i}",
            title=f"Document {i}",
            file_path=f"/test/doc{i}.md",
            tags=[f"tag{i % 2}"],
            metadata={}
        )
        graph.add_node(node)
    
    # Add edges to create structure
    graph.add_edge(GraphEdge("doc0", "doc1", 0.9, 0.0, 0.9, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc1", "doc2", 0.8, 0.0, 0.8, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc2", "doc3", 0.7, 0.0, 0.7, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc3", "doc4", 0.6, 0.0, 0.6, 0.0, "similarity"))
    graph.add_edge(GraphEdge("doc0", "doc5", 0.5, 0.0, 0.5, 0.0, "similarity"))
    
    return graph


# Test Initialization

def test_visualizer_initialization():
    """Test visualizer initialization"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    assert visualizer.graph == graph
    assert visualizer.analyzer is not None


# Test D3.js Export

def test_to_d3_json_basic():
    """Test basic D3.js JSON export"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    json_str = visualizer.to_d3_json()
    
    # Should be valid JSON
    data = json.loads(json_str)
    assert "nodes" in data
    assert "links" in data
    assert len(data["nodes"]) == 6
    assert len(data["links"]) == 5


def test_to_d3_json_with_filtering():
    """Test D3.js export with edge weight filtering"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    json_str = visualizer.to_d3_json(min_edge_weight=0.7)
    
    data = json.loads(json_str)
    # Should filter edges with weight < 0.7
    assert len(data["links"]) < 5


def test_to_d3_json_with_max_nodes():
    """Test D3.js export with node limit"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    json_str = visualizer.to_d3_json(max_nodes=3)
    
    data = json.loads(json_str)
    # Should limit to 3 nodes
    assert len(data["nodes"]) == 3


def test_d3_node_structure():
    """Test D3 node structure"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    json_str = visualizer.to_d3_json()
    data = json.loads(json_str)
    
    # Check node structure
    node = data["nodes"][0]
    assert "id" in node
    assert "name" in node
    assert "group" in node
    assert "degree" in node
    assert "centrality" in node


def test_d3_link_structure():
    """Test D3 link structure"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    json_str = visualizer.to_d3_json()
    data = json.loads(json_str)
    
    # Check link structure
    link = data["links"][0]
    assert "source" in link
    assert "target" in link
    assert "value" in link


# Test Mermaid Export

def test_to_mermaid_basic():
    """Test basic Mermaid diagram export"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    mermaid = visualizer.to_mermaid()
    
    # Should start with graph directive
    assert mermaid.startswith("graph")
    # Should contain node definitions
    assert "[" in mermaid and "]" in mermaid
    # Should contain edges
    assert "-->" in mermaid or "==>" in mermaid


def test_to_mermaid_with_direction():
    """Test Mermaid with different directions"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    # Top-down
    mermaid_td = visualizer.to_mermaid(direction="TD")
    assert "graph TD" in mermaid_td
    
    # Left-right
    mermaid_lr = visualizer.to_mermaid(direction="LR")
    assert "graph LR" in mermaid_lr


def test_to_mermaid_with_filtering():
    """Test Mermaid with edge weight filtering"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    mermaid = visualizer.to_mermaid(min_edge_weight=0.8)
    
    # Should have fewer edges
    edge_count = mermaid.count("-->") + mermaid.count("==>")
    assert edge_count < 5


# Test Obsidian Format

def test_to_obsidian_format_full_graph():
    """Test Obsidian format export for full graph"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    obsidian_data = visualizer.to_obsidian_format()
    
    assert "nodes" in obsidian_data
    assert "edges" in obsidian_data
    assert len(obsidian_data["nodes"]) == 6
    assert len(obsidian_data["edges"]) == 5


def test_to_obsidian_format_with_center():
    """Test Obsidian format with center node expansion"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    obsidian_data = visualizer.to_obsidian_format(
        center_node="doc0",
        max_depth=1
    )
    
    assert obsidian_data["center"] == "doc0"
    assert obsidian_data["depth"] == 1
    # Should include center and its neighbors
    assert len(obsidian_data["nodes"]) > 0


def test_obsidian_node_structure():
    """Test Obsidian node structure"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    obsidian_data = visualizer.to_obsidian_format()
    
    node = obsidian_data["nodes"][0]
    assert "id" in node
    assert "title" in node
    assert "path" in node
    assert "tags" in node
    assert "degree" in node


def test_obsidian_edge_structure():
    """Test Obsidian edge structure"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    obsidian_data = visualizer.to_obsidian_format()
    
    edge = obsidian_data["edges"][0]
    assert "source" in edge
    assert "target" in edge
    assert "weight" in edge
    assert "type" in edge


# Test GraphML Export

def test_to_graphml():
    """Test GraphML XML export"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    graphml = visualizer.to_graphml()
    
    # Should be valid XML
    assert graphml.startswith('<?xml')
    assert '<graphml' in graphml
    assert '</graphml>' in graphml
    assert '<node' in graphml
    assert '<edge' in graphml


def test_graphml_structure():
    """Test GraphML structure"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    graphml = visualizer.to_graphml()
    
    # Should have key definitions
    assert '<key id="title"' in graphml
    assert '<key id="weight"' in graphml
    
    # Should have node and edge counts
    node_count = graphml.count('<node id=')
    edge_count = graphml.count('<edge id=')
    assert node_count == 6
    assert edge_count == 5


# Test Filtering

def test_filter_by_tags():
    """Test filtering graph by tags"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    filtered = visualizer.filter_by_tags(["tag0"])
    
    # Should only include nodes with tag0
    assert filtered.total_nodes <= graph.total_nodes
    for node in filtered.nodes.values():
        assert "tag0" in node.tags


def test_filter_by_tags_empty():
    """Test filtering with non-existent tag"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    filtered = visualizer.filter_by_tags(["nonexistent"])
    
    # Should return empty graph
    assert filtered.total_nodes == 0
    assert filtered.total_edges == 0


# Test Expansion

def test_expand_from_node():
    """Test expanding subgraph from a node"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    subgraph = visualizer.expand_from_node("doc0", max_hops=1)
    
    # Should include doc0 and its neighbors
    assert "doc0" in subgraph.nodes
    assert subgraph.total_nodes > 1
    assert subgraph.total_nodes < graph.total_nodes


def test_expand_from_invalid_node():
    """Test expanding from non-existent node"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    subgraph = visualizer.expand_from_node("invalid", max_hops=1)
    
    # Should return empty graph
    assert subgraph.total_nodes == 0


def test_expand_with_max_hops():
    """Test expansion with different hop limits"""
    graph = create_test_graph()
    visualizer = GraphVisualizer(graph)
    
    subgraph_1 = visualizer.expand_from_node("doc0", max_hops=1)
    subgraph_2 = visualizer.expand_from_node("doc0", max_hops=2)
    
    # 2-hop should include more nodes
    assert subgraph_2.total_nodes >= subgraph_1.total_nodes
