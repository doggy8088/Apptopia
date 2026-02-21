"""
Graph Analyzer for Knowledge Graph Analysis

Provides advanced graph analysis capabilities including:
- Community detection (Louvain algorithm)
- Centrality metrics (PageRank, degree, betweenness)
- Hub document identification
- Path finding between documents
- Graph clustering analysis
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
from collections import defaultdict

from .builder import DocumentGraph, GraphNode


@dataclass
class CommunityInfo:
    """Information about a community/cluster in the graph"""
    community_id: int
    nodes: List[str]  # Document IDs
    size: int
    density: float  # Internal edge density
    avg_centrality: float


@dataclass
class HubDocument:
    """Information about a hub document"""
    doc_id: str
    title: str
    degree: int
    pagerank: float
    betweenness: float
    community: Optional[int] = None


@dataclass
class PathInfo:
    """Information about a path between two documents"""
    source_id: str
    target_id: str
    path: List[str]  # List of document IDs
    length: int
    total_weight: float  # Sum of edge weights along path


class GraphAnalyzer:
    """
    Analyzer for document knowledge graphs
    
    Provides various graph analysis algorithms including
    community detection, centrality metrics, and path finding.
    """
    
    def __init__(self, graph: DocumentGraph):
        """
        Initialize analyzer with a document graph
        
        Args:
            graph: DocumentGraph to analyze
        """
        self.graph = graph
        self.nx_graph = graph.to_networkx()
        self._communities: Optional[List[Set[str]]] = None
        self._pagerank: Optional[Dict[str, float]] = None
        self._betweenness: Optional[Dict[str, float]] = None
    
    def detect_communities(self, resolution: float = 1.0) -> List[CommunityInfo]:
        """
        Detect communities using Louvain algorithm
        
        Args:
            resolution: Resolution parameter for community detection
                       (higher = more communities)
        
        Returns:
            List of CommunityInfo objects
        """
        # Use Louvain community detection
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(
                self.nx_graph,
                resolution=resolution
            )
        except ImportError:
            # Fallback: use NetworkX's greedy modularity
            communities_gen = nx.community.greedy_modularity_communities(
                self.nx_graph
            )
            partition = {}
            for comm_id, comm in enumerate(communities_gen):
                for node in comm:
                    partition[node] = comm_id
        
        # Group nodes by community
        communities_dict: Dict[int, List[str]] = defaultdict(list)
        for node_id, comm_id in partition.items():
            communities_dict[comm_id].append(node_id)
        
        # Calculate community info
        community_infos = []
        for comm_id, nodes in communities_dict.items():
            # Calculate density (edges within community / possible edges)
            subgraph = self.nx_graph.subgraph(nodes)
            n = len(nodes)
            if n > 1:
                possible_edges = n * (n - 1) / 2
                actual_edges = subgraph.number_of_edges()
                density = actual_edges / possible_edges if possible_edges > 0 else 0.0
            else:
                density = 0.0
            
            # Calculate average centrality
            pagerank = self.calculate_pagerank()
            avg_centrality = sum(pagerank.get(node, 0.0) for node in nodes) / len(nodes)
            
            community_infos.append(CommunityInfo(
                community_id=comm_id,
                nodes=nodes,
                size=len(nodes),
                density=density,
                avg_centrality=avg_centrality
            ))
        
        # Cache communities
        self._communities = [set(comm.nodes) for comm in community_infos]
        
        # Update graph nodes with community info
        for comm_info in community_infos:
            for node_id in comm_info.nodes:
                if node_id in self.graph.nodes:
                    self.graph.nodes[node_id].community = comm_info.community_id
        
        return sorted(community_infos, key=lambda x: x.size, reverse=True)
    
    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """
        Calculate PageRank centrality for all nodes
        
        Args:
            alpha: Damping parameter (default: 0.85)
        
        Returns:
            Dict mapping node IDs to PageRank scores
        """
        if self._pagerank is None:
            self._pagerank = nx.pagerank(self.nx_graph, alpha=alpha)
        
        # Update graph nodes
        for node_id, score in self._pagerank.items():
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id].centrality = score
        
        return self._pagerank
    
    def calculate_degree_centrality(self) -> Dict[str, float]:
        """
        Calculate degree centrality (normalized degree)
        
        Returns:
            Dict mapping node IDs to degree centrality scores
        """
        degree_cent = nx.degree_centrality(self.nx_graph)
        
        # Update graph nodes
        for node_id, degree in self.nx_graph.degree():
            if node_id in self.graph.nodes:
                self.graph.nodes[node_id].degree = degree
        
        return degree_cent
    
    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """
        Calculate betweenness centrality
        
        Returns:
            Dict mapping node IDs to betweenness scores
        """
        if self._betweenness is None:
            self._betweenness = nx.betweenness_centrality(self.nx_graph)
        
        return self._betweenness
    
    def identify_hubs(self, top_n: int = 10) -> List[HubDocument]:
        """
        Identify hub documents based on centrality metrics
        
        Args:
            top_n: Number of top hubs to return
        
        Returns:
            List of HubDocument objects sorted by importance
        """
        # Calculate all metrics
        pagerank = self.calculate_pagerank()
        degree_cent = self.calculate_degree_centrality()
        betweenness = self.calculate_betweenness_centrality()
        
        # Get communities if not already computed
        if self._communities is None:
            self.detect_communities()
        
        # Create hub documents
        hubs = []
        for node_id, node in self.graph.nodes.items():
            hub = HubDocument(
                doc_id=node_id,
                title=node.title,
                degree=node.degree,
                pagerank=pagerank.get(node_id, 0.0),
                betweenness=betweenness.get(node_id, 0.0),
                community=node.community
            )
            hubs.append(hub)
        
        # Sort by combined score (weighted average of metrics)
        hubs.sort(
            key=lambda h: (
                0.5 * h.pagerank +
                0.3 * h.betweenness +
                0.2 * (h.degree / max(1, self.graph.total_nodes))
            ),
            reverse=True
        )
        
        return hubs[:top_n]
    
    def find_shortest_path(
        self,
        source_id: str,
        target_id: str,
        weight: str = "weight"
    ) -> Optional[PathInfo]:
        """
        Find shortest path between two documents
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            weight: Edge attribute to use as weight (default: "weight")
        
        Returns:
            PathInfo object or None if no path exists
        """
        if source_id not in self.nx_graph or target_id not in self.nx_graph:
            return None
        
        try:
            # Find shortest path (weighted)
            path = nx.shortest_path(
                self.nx_graph,
                source=source_id,
                target=target_id,
                weight=weight
            )
            
            # Calculate total weight
            total_weight = 0.0
            for i in range(len(path) - 1):
                edge_data = self.nx_graph[path[i]][path[i+1]]
                total_weight += edge_data.get(weight, 1.0)
            
            return PathInfo(
                source_id=source_id,
                target_id=target_id,
                path=path,
                length=len(path) - 1,  # Number of edges
                total_weight=total_weight
            )
        except nx.NetworkXNoPath:
            return None
    
    def find_all_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: int = 5
    ) -> List[PathInfo]:
        """
        Find all simple paths between two documents
        
        Args:
            source_id: Source document ID
            target_id: Target document ID
            max_length: Maximum path length (number of edges)
        
        Returns:
            List of PathInfo objects
        """
        if source_id not in self.nx_graph or target_id not in self.nx_graph:
            return []
        
        try:
            paths = list(nx.all_simple_paths(
                self.nx_graph,
                source=source_id,
                target=target_id,
                cutoff=max_length
            ))
            
            path_infos = []
            for path in paths:
                # Calculate total weight
                total_weight = 0.0
                for i in range(len(path) - 1):
                    edge_data = self.nx_graph[path[i]][path[i+1]]
                    total_weight += edge_data.get("weight", 1.0)
                
                path_infos.append(PathInfo(
                    source_id=source_id,
                    target_id=target_id,
                    path=path,
                    length=len(path) - 1,
                    total_weight=total_weight
                ))
            
            # Sort by length and weight
            path_infos.sort(key=lambda p: (p.length, -p.total_weight))
            return path_infos
        except nx.NetworkXNoPath:
            return []
    
    def get_neighbors(
        self,
        node_id: str,
        max_distance: int = 1
    ) -> Dict[int, List[str]]:
        """
        Get neighbors at different distances from a node
        
        Args:
            node_id: Node ID to get neighbors for
            max_distance: Maximum distance (number of hops)
        
        Returns:
            Dict mapping distance to list of node IDs at that distance
        """
        if node_id not in self.nx_graph:
            return {}
        
        neighbors_by_distance: Dict[int, List[str]] = defaultdict(list)
        visited = {node_id}
        current_level = {node_id}
        
        for distance in range(1, max_distance + 1):
            next_level = set()
            for node in current_level:
                for neighbor in self.nx_graph.neighbors(node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.add(neighbor)
                        neighbors_by_distance[distance].append(neighbor)
            
            if not next_level:
                break
            current_level = next_level
        
        return dict(neighbors_by_distance)
    
    def calculate_clustering_coefficient(self) -> Dict[str, float]:
        """
        Calculate clustering coefficient for each node
        
        Returns:
            Dict mapping node IDs to clustering coefficients
        """
        return nx.clustering(self.nx_graph)
    
    def get_graph_statistics(self) -> Dict[str, any]:
        """
        Get overall graph statistics
        
        Returns:
            Dict with various graph statistics
        """
        stats = {
            "nodes": self.nx_graph.number_of_nodes(),
            "edges": self.nx_graph.number_of_edges(),
            "density": nx.density(self.nx_graph),
            "is_connected": nx.is_connected(self.nx_graph),
        }
        
        # Connected components
        if not stats["is_connected"]:
            stats["num_components"] = nx.number_connected_components(self.nx_graph)
            stats["largest_component_size"] = len(max(
                nx.connected_components(self.nx_graph),
                key=len
            ))
        
        # Average clustering
        stats["avg_clustering"] = nx.average_clustering(self.nx_graph)
        
        # Average degree
        degrees = [d for n, d in self.nx_graph.degree()]
        stats["avg_degree"] = sum(degrees) / len(degrees) if degrees else 0.0
        
        return stats
