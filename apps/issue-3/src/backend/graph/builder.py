"""
Graph Builder for document relationships.

Builds a knowledge graph from documents based on:
- 20% Manual wikilinks (from Obsidian [[links]])
- 50% Vector similarity (embedding cosine similarity)
- 30% Keyword matching (shared terms)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import re

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

from ..models.document import Document, Relationship


@dataclass
class GraphNode:
    """Represents a document node in the graph."""
    
    doc_id: str
    title: str
    file_path: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)
    degree: int = 0  # Number of connections
    centrality: float = 0.0  # Centrality score
    community: Optional[int] = None  # Community ID


@dataclass
class GraphEdge:
    """Represents a relationship edge between documents."""
    
    source_id: str
    target_id: str
    weight: float = 0.0  # Combined score [0, 1]
    wikilink_score: float = 0.0   # 20% weight
    vector_score: float = 0.0      # 50% weight
    keyword_score: float = 0.0     # 30% weight
    relationship_type: str = "computed"  # "wikilink", "similarity", "keyword", or "computed"
    
    def calculate_weight(self):
        """Calculate combined weight from component scores."""
        self.weight = (
            self.wikilink_score * 0.2 +
            self.vector_score * 0.5 +
            self.keyword_score * 0.3
        )


@dataclass
class DocumentGraph:
    """Complete document knowledge graph."""
    
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    
    @property
    def total_nodes(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)
    
    @property
    def total_edges(self) -> int:
        """Get total number of edges."""
        return len(self.edges)
    
    def get_node(self, doc_id: str) -> Optional[GraphNode]:
        """Get node by document ID."""
        return self.nodes.get(doc_id)
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        self.nodes[node.doc_id] = node
    
    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        self.edges.append(edge)
        
        # Update degree counts
        if edge.source_id in self.nodes:
            self.nodes[edge.source_id].degree += 1
        if edge.target_id in self.nodes:
            self.nodes[edge.target_id].degree += 1
    
    def get_edges_for_node(self, doc_id: str) -> List[GraphEdge]:
        """Get all edges connected to a node."""
        return [
            edge for edge in self.edges
            if edge.source_id == doc_id or edge.target_id == doc_id
        ]
    
    def to_networkx(self) -> Optional[any]:
        """Convert to NetworkX graph for advanced algorithms."""
        if not NETWORKX_AVAILABLE:
            return None
        
        G = nx.Graph()
        
        # Add nodes
        for doc_id, node in self.nodes.items():
            G.add_node(doc_id, **{
                'title': node.title,
                'file_path': node.file_path,
                'tags': node.tags,
                'degree': node.degree,
                'centrality': node.centrality,
                'community': node.community
            })
        
        # Add edges
        for edge in self.edges:
            G.add_edge(
                edge.source_id,
                edge.target_id,
                weight=edge.weight,
                wikilink_score=edge.wikilink_score,
                vector_score=edge.vector_score,
                keyword_score=edge.keyword_score,
                relationship_type=edge.relationship_type
            )
        
        return G


class GraphBuilder:
    """Builds document knowledge graphs."""
    
    def __init__(
        self,
        min_edge_weight: float = 0.1,
        max_edges_per_node: int = 20,
        keyword_min_length: int = 3
    ):
        """
        Initialize graph builder.
        
        Args:
            min_edge_weight: Minimum weight threshold for edges (0-1)
            max_edges_per_node: Maximum number of edges per node
            keyword_min_length: Minimum length for keywords
        """
        self.min_edge_weight = min_edge_weight
        self.max_edges_per_node = max_edges_per_node
        self.keyword_min_length = keyword_min_length
    
    def build_graph(
        self,
        documents: List[Document],
        embeddings: Optional[Dict[str, List[float]]] = None
    ) -> DocumentGraph:
        """
        Build complete knowledge graph from documents.
        
        Args:
            documents: List of documents to build graph from
            embeddings: Optional dict mapping doc_id to embedding vector
        
        Returns:
            DocumentGraph with nodes and weighted edges
        """
        graph = DocumentGraph()
        
        # Step 1: Create nodes from documents
        for doc in documents:
            node = GraphNode(
                doc_id=doc.doc_id,
                title=doc.metadata.title or doc.file_path.stem,
                file_path=str(doc.file_path),
                tags=doc.metadata.tags,
                metadata={
                    'word_count': doc.metadata.word_count,
                    'chunk_count': len(doc.chunks)
                }
            )
            graph.add_node(node)
        
        # Step 2: Build edges with combined scores
        doc_pairs = []
        for i, doc1 in enumerate(documents):
            for doc2 in documents[i+1:]:
                doc_pairs.append((doc1, doc2))
        
        for doc1, doc2 in doc_pairs:
            edge = self._build_edge(doc1, doc2, embeddings)
            
            # Only add if above threshold
            if edge and edge.weight >= self.min_edge_weight:
                graph.add_edge(edge)
        
        # Step 3: Prune edges if too many per node
        self._prune_edges(graph)
        
        return graph
    
    def _build_edge(
        self,
        doc1: Document,
        doc2: Document,
        embeddings: Optional[Dict[str, List[float]]] = None
    ) -> Optional[GraphEdge]:
        """
        Build an edge between two documents.
        
        Calculates scores from:
        - Wikilinks (20% weight)
        - Vector similarity (50% weight)
        - Keyword matching (30% weight)
        """
        edge = GraphEdge(
            source_id=doc1.doc_id,
            target_id=doc2.doc_id
        )
        
        # Calculate wikilink score (20%)
        edge.wikilink_score = self._calculate_wikilink_score(doc1, doc2)
        
        # Calculate vector similarity score (50%)
        if embeddings:
            edge.vector_score = self._calculate_vector_score(
                doc1.doc_id,
                doc2.doc_id,
                embeddings
            )
        
        # Calculate keyword score (30%)
        edge.keyword_score = self._calculate_keyword_score(doc1, doc2)
        
        # Combine scores
        edge.calculate_weight()
        
        # Determine relationship type
        if edge.wikilink_score > 0:
            edge.relationship_type = "wikilink"
        elif edge.vector_score > edge.keyword_score:
            edge.relationship_type = "similarity"
        elif edge.keyword_score > 0:
            edge.relationship_type = "keyword"
        
        return edge if edge.weight > 0 else None
    
    def _calculate_wikilink_score(self, doc1: Document, doc2: Document) -> float:
        """
        Calculate wikilink score based on explicit links.
        
        Returns 1.0 if documents are linked, 0.0 otherwise.
        """
        # Check if doc1 has wikilink to doc2
        for rel in doc1.relationships:
            if rel.target_doc_id == doc2.doc_id:
                if rel.relationship_type in ["wikilink", "wikilink_header"]:
                    return 1.0
        
        # Check reverse direction
        for rel in doc2.relationships:
            if rel.target_doc_id == doc1.doc_id:
                if rel.relationship_type in ["wikilink", "wikilink_header"]:
                    return 1.0
        
        return 0.0
    
    def _calculate_vector_score(
        self,
        doc1_id: str,
        doc2_id: str,
        embeddings: Dict[str, List[float]]
    ) -> float:
        """
        Calculate vector similarity score using cosine similarity.
        
        Returns similarity in [0, 1] range.
        """
        if doc1_id not in embeddings or doc2_id not in embeddings:
            return 0.0
        
        vec1 = embeddings[doc1_id]
        vec2 = embeddings[doc2_id]
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Normalize to [0, 1]
        return max(0.0, min(1.0, (similarity + 1) / 2))
    
    def _calculate_keyword_score(self, doc1: Document, doc2: Document) -> float:
        """
        Calculate keyword overlap score using Jaccard similarity.
        
        Extracts keywords from:
        - Document tags
        - Document title
        - Common words (simple extraction)
        
        Returns Jaccard similarity in [0, 1] range.
        """
        keywords1 = self._extract_keywords(doc1)
        keywords2 = self._extract_keywords(doc2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_keywords(self, doc: Document) -> Set[str]:
        """
        Extract keywords from document.
        
        Uses:
        - Tags (highest priority)
        - Title words
        - High-frequency terms (simple extraction)
        """
        keywords = set()
        
        # Add tags
        for tag in doc.metadata.tags:
            # Handle nested tags: "程式語言/Rust" -> ["程式語言", "Rust"]
            parts = tag.split('/')
            for part in parts:
                if len(part) >= self.keyword_min_length:
                    keywords.add(part.lower())
        
        # Add title words
        title = doc.metadata.title or doc.file_path.stem
        words = re.findall(r'\b\w+\b', title.lower())
        for word in words:
            if len(word) >= self.keyword_min_length:
                keywords.add(word)
        
        return keywords
    
    def _prune_edges(self, graph: DocumentGraph):
        """
        Prune edges to limit connections per node.
        
        Keeps only the top N highest-weight edges for each node.
        """
        if self.max_edges_per_node <= 0:
            return
        
        # Group edges by node
        node_edges: Dict[str, List[Tuple[GraphEdge, float]]] = {}
        for edge in graph.edges:
            if edge.source_id not in node_edges:
                node_edges[edge.source_id] = []
            if edge.target_id not in node_edges:
                node_edges[edge.target_id] = []
            # Store edge with weight for sorting
            node_edges[edge.source_id].append((edge, edge.weight))
            node_edges[edge.target_id].append((edge, edge.weight))
        
        # Find edges to keep - each node votes for its top N edges
        edge_votes: Dict[int, int] = {}  # edge id -> vote count
        for node_id, edge_list in node_edges.items():
            # Sort by weight descending
            edge_list.sort(key=lambda x: x[1], reverse=True)
            
            # Vote for top N edges
            for edge, _ in edge_list[:self.max_edges_per_node]:
                edge_id = id(edge)
                edge_votes[edge_id] = edge_votes.get(edge_id, 0) + 1
        
        # Keep edges that got at least one vote
        # This ensures both ends of the edge are satisfied
        edges_to_keep = set(edge_votes.keys())
        
        # Filter graph edges
        graph.edges = [e for e in graph.edges if id(e) in edges_to_keep]
        
        # Recalculate degrees
        for node in graph.nodes.values():
            node.degree = 0
        for edge in graph.edges:
            graph.nodes[edge.source_id].degree += 1
            graph.nodes[edge.target_id].degree += 1
