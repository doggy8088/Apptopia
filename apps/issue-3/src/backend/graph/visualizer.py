"""
Graph Visualizer for Knowledge Graph Export

Exports document knowledge graphs in various formats:
- D3.js force-directed graph (JSON)
- Mermaid diagram syntax
- Obsidian graph view format
- GraphML (standard graph format)
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set
import json

from .builder import DocumentGraph, GraphNode, GraphEdge
from .analyzer import GraphAnalyzer


@dataclass
class D3Node:
    """D3.js node format"""
    id: str
    name: str
    group: int  # Community/cluster ID
    degree: int
    centrality: float


@dataclass
class D3Link:
    """D3.js link format"""
    source: str
    target: str
    value: float  # Edge weight


@dataclass
class D3Graph:
    """D3.js graph format"""
    nodes: List[D3Node]
    links: List[D3Link]


class GraphVisualizer:
    """
    Visualizer for document knowledge graphs
    
    Exports graphs in various formats for different visualization tools.
    """
    
    def __init__(self, graph: DocumentGraph):
        """
        Initialize visualizer with a document graph
        
        Args:
            graph: DocumentGraph to visualize
        """
        self.graph = graph
        self.analyzer = GraphAnalyzer(graph)
    
    def to_d3_json(
        self,
        min_edge_weight: float = 0.0,
        max_nodes: Optional[int] = None
    ) -> str:
        """
        Export graph to D3.js force-directed graph format
        
        Args:
            min_edge_weight: Minimum edge weight to include
            max_nodes: Maximum number of nodes (keeps highest centrality)
        
        Returns:
            JSON string in D3.js format
        """
        # Calculate centrality if needed
        self.analyzer.calculate_pagerank()
        
        # Get nodes (optionally filtered by centrality)
        nodes_to_include = set(self.graph.nodes.keys())
        if max_nodes and len(nodes_to_include) > max_nodes:
            # Keep top N by centrality
            sorted_nodes = sorted(
                self.graph.nodes.items(),
                key=lambda x: x[1].centrality,
                reverse=True
            )
            nodes_to_include = {node_id for node_id, _ in sorted_nodes[:max_nodes]}
        
        # Create D3 nodes
        d3_nodes = []
        for node_id in nodes_to_include:
            node = self.graph.nodes[node_id]
            d3_nodes.append(D3Node(
                id=node_id,
                name=node.title,
                group=node.community if node.community is not None else 0,
                degree=node.degree,
                centrality=node.centrality
            ))
        
        # Create D3 links (only between included nodes)
        d3_links = []
        for edge in self.graph.edges:
            if (edge.source_id in nodes_to_include and
                edge.target_id in nodes_to_include and
                edge.weight >= min_edge_weight):
                d3_links.append(D3Link(
                    source=edge.source_id,
                    target=edge.target_id,
                    value=edge.weight
                ))
        
        # Create D3 graph
        d3_graph = D3Graph(nodes=d3_nodes, links=d3_links)
        
        # Convert to JSON
        graph_dict = {
            "nodes": [asdict(node) for node in d3_graph.nodes],
            "links": [asdict(link) for link in d3_graph.links]
        }
        
        return json.dumps(graph_dict, ensure_ascii=False, indent=2)
    
    def to_mermaid(
        self,
        direction: str = "TD",
        max_nodes: Optional[int] = None,
        min_edge_weight: float = 0.3
    ) -> str:
        """
        Export graph to Mermaid diagram syntax
        
        Args:
            direction: Graph direction (TD=top-down, LR=left-right, etc.)
            max_nodes: Maximum number of nodes to include
            min_edge_weight: Minimum edge weight to show
        
        Returns:
            Mermaid diagram syntax string
        """
        lines = [f"graph {direction}"]
        
        # Get nodes to include
        nodes_to_include = set(self.graph.nodes.keys())
        if max_nodes and len(nodes_to_include) > max_nodes:
            # Keep nodes with highest degree
            sorted_nodes = sorted(
                self.graph.nodes.items(),
                key=lambda x: x[1].degree,
                reverse=True
            )
            nodes_to_include = {node_id for node_id, _ in sorted_nodes[:max_nodes]}
        
        # Add nodes with labels
        node_labels = {}
        for node_id in nodes_to_include:
            node = self.graph.nodes[node_id]
            # Sanitize title for Mermaid (remove special chars)
            safe_title = node.title.replace("[", "").replace("]", "")
            safe_title = safe_title.replace("(", "").replace(")", "")
            safe_title = safe_title[:30]  # Limit length
            
            # Create node ID (alphanumeric only)
            safe_id = node_id.replace("-", "_").replace(".", "_")
            node_labels[node_id] = safe_id
            
            # Add node with label
            lines.append(f'    {safe_id}["{safe_title}"]')
        
        # Add edges
        added_edges = set()
        for edge in self.graph.edges:
            if (edge.source_id in nodes_to_include and
                edge.target_id in nodes_to_include and
                edge.weight >= min_edge_weight):
                
                # Avoid duplicate edges (undirected)
                edge_key = tuple(sorted([edge.source_id, edge.target_id]))
                if edge_key not in added_edges:
                    added_edges.add(edge_key)
                    
                    source_id = node_labels[edge.source_id]
                    target_id = node_labels[edge.target_id]
                    
                    # Edge style based on weight
                    if edge.weight > 0.7:
                        connector = "==>"  # Strong connection
                    elif edge.weight > 0.4:
                        connector = "-->"  # Medium connection
                    else:
                        connector = "-.->"  # Weak connection
                    
                    lines.append(f"    {source_id} {connector} {target_id}")
        
        return "\n".join(lines)
    
    def to_obsidian_format(
        self,
        center_node: Optional[str] = None,
        max_depth: int = 2
    ) -> Dict[str, any]:
        """
        Export graph in Obsidian graph view compatible format
        
        Args:
            center_node: Central node to expand from (None = full graph)
            max_depth: Maximum depth from center node
        
        Returns:
            Dict with Obsidian-compatible graph data
        """
        # Determine nodes to include
        if center_node and center_node in self.graph.nodes:
            # Expand from center node
            neighbors = self.analyzer.get_neighbors(center_node, max_distance=max_depth)
            nodes_to_include = {center_node}
            for distance_nodes in neighbors.values():
                nodes_to_include.update(distance_nodes)
        else:
            # Include all nodes
            nodes_to_include = set(self.graph.nodes.keys())
        
        # Build node data
        nodes_data = []
        for node_id in nodes_to_include:
            node = self.graph.nodes[node_id]
            nodes_data.append({
                "id": node_id,
                "title": node.title,
                "path": node.file_path,
                "tags": node.tags,
                "degree": node.degree,
                "community": node.community
            })
        
        # Build edge data
        edges_data = []
        for edge in self.graph.edges:
            if (edge.source_id in nodes_to_include and
                edge.target_id in nodes_to_include):
                edges_data.append({
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "weight": edge.weight,
                    "type": edge.relationship_type
                })
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "center": center_node,
            "depth": max_depth if center_node else None
        }
    
    def to_graphml(self) -> str:
        """
        Export graph to GraphML format
        
        Returns:
            GraphML XML string
        """
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        lines.append('  <key id="title" for="node" attr.name="title" attr.type="string"/>')
        lines.append('  <key id="path" for="node" attr.name="path" attr.type="string"/>')
        lines.append('  <key id="degree" for="node" attr.name="degree" attr.type="int"/>')
        lines.append('  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>')
        lines.append('  <key id="type" for="edge" attr.name="type" attr.type="string"/>')
        lines.append('  <graph id="G" edgedefault="undirected">')
        
        # Add nodes
        for node_id, node in self.graph.nodes.items():
            lines.append(f'    <node id="{node_id}">')
            lines.append(f'      <data key="title">{self._escape_xml(node.title)}</data>')
            lines.append(f'      <data key="path">{self._escape_xml(node.file_path)}</data>')
            lines.append(f'      <data key="degree">{node.degree}</data>')
            lines.append('    </node>')
        
        # Add edges
        for i, edge in enumerate(self.graph.edges):
            lines.append(f'    <edge id="e{i}" source="{edge.source_id}" target="{edge.target_id}">')
            lines.append(f'      <data key="weight">{edge.weight:.4f}</data>')
            lines.append(f'      <data key="type">{edge.relationship_type}</data>')
            lines.append('    </edge>')
        
        lines.append('  </graph>')
        lines.append('</graphml>')
        
        return "\n".join(lines)
    
    def filter_by_tags(self, tags: List[str]) -> DocumentGraph:
        """
        Create filtered graph containing only nodes with specified tags
        
        Args:
            tags: List of tags to filter by
        
        Returns:
            New DocumentGraph with filtered nodes
        """
        filtered_graph = DocumentGraph()
        
        # Add nodes with matching tags
        for node_id, node in self.graph.nodes.items():
            if any(tag in node.tags for tag in tags):
                filtered_graph.add_node(node)
        
        # Add edges between included nodes
        for edge in self.graph.edges:
            if (edge.source_id in filtered_graph.nodes and
                edge.target_id in filtered_graph.nodes):
                filtered_graph.add_edge(edge)
        
        return filtered_graph
    
    def expand_from_node(
        self,
        node_id: str,
        max_hops: int = 2
    ) -> DocumentGraph:
        """
        Create subgraph by expanding from a specific node
        
        Args:
            node_id: Starting node ID
            max_hops: Maximum number of hops to expand
        
        Returns:
            New DocumentGraph with expanded nodes
        """
        if node_id not in self.graph.nodes:
            return DocumentGraph()
        
        # Get neighbors at different distances
        neighbors = self.analyzer.get_neighbors(node_id, max_distance=max_hops)
        
        # Collect all node IDs to include
        nodes_to_include = {node_id}
        for distance_nodes in neighbors.values():
            nodes_to_include.update(distance_nodes)
        
        # Create subgraph
        subgraph = DocumentGraph()
        
        # Add nodes
        for nid in nodes_to_include:
            if nid in self.graph.nodes:
                subgraph.add_node(self.graph.nodes[nid])
        
        # Add edges
        for edge in self.graph.edges:
            if (edge.source_id in nodes_to_include and
                edge.target_id in nodes_to_include):
                subgraph.add_edge(edge)
        
        return subgraph
    
    def _escape_xml(self, text: str) -> str:
        """Escape special XML characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;")
                   .replace("'", "&apos;"))
