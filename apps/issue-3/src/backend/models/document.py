"""
Data models for documents, metadata, and relationships.

These models define the core data structures used throughout the application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum


class DocumentStatus(Enum):
    """Status of a document in the system."""
    ACTIVE = "active"
    FROZEN = "frozen"  # Source folder missing but document retained
    PENDING = "pending"  # Queued for processing
    ERROR = "error"  # Processing failed


class LinkType(Enum):
    """Types of links between documents."""
    WIKILINK = "wikilink"  # [[Document]]
    WIKILINK_HEADER = "wikilink_header"  # [[Document#Header]]
    TAG = "tag"  # #tag
    EMBED = "embed"  # ![[Document]]


@dataclass
class DocumentMetadata:
    """Metadata extracted from document frontmatter and content."""
    
    # Frontmatter fields
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    custom_fields: Dict[str, any] = field(default_factory=dict)
    
    # Content-derived metadata
    title: Optional[str] = None
    headings: List[str] = field(default_factory=list)
    word_count: int = 0
    
    # Links and relationships
    outgoing_links: List['DocumentLink'] = field(default_factory=list)
    incoming_links: List['DocumentLink'] = field(default_factory=list)


@dataclass
class DocumentLink:
    """Represents a link from one document to another."""
    
    target: str  # Target document name or path
    link_type: LinkType
    display_text: Optional[str] = None
    header: Optional[str] = None  # For header links
    source_line: Optional[int] = None


@dataclass
class DocumentChunk:
    """A chunk of document content for vector indexing."""
    
    chunk_id: str
    document_id: str
    content: str
    start_line: int
    end_line: int
    metadata: Dict[str, any] = field(default_factory=dict)
    
    # Vector embedding (populated during indexing)
    embedding: Optional[List[float]] = None


@dataclass
class Document:
    """Represents a complete document in the knowledge base."""
    
    # Identity
    doc_id: str  # Unique identifier (hash or UUID)
    file_path: Path  # Absolute path to source file
    relative_path: Path  # Relative to source folder
    source_folder: str  # Which source folder this belongs to
    
    # Content
    raw_content: str
    parsed_content: str  # After Obsidian syntax processing
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    
    # Chunks (for vector indexing)
    chunks: List[DocumentChunk] = field(default_factory=list)
    
    # Relationships to other documents
    relationships: List['Relationship'] = field(default_factory=list)
    
    # Status
    status: DocumentStatus = DocumentStatus.PENDING
    last_indexed: Optional[datetime] = None
    index_version: str = "0.1.0"  # Track index schema version
    
    # File info
    file_size: int = 0
    file_hash: str = ""  # For change detection
    
    def __post_init__(self):
        """Validate and normalize after initialization."""
        if not self.file_path.exists():
            self.status = DocumentStatus.FROZEN
        
        # Extract title from filename if not set
        if not self.metadata.title:
            self.metadata.title = self.file_path.stem


@dataclass
class SourceFolder:
    """Represents a source folder containing documents."""
    
    folder_id: str
    path: Path
    name: str
    is_active: bool = True  # False if folder is missing (frozen)
    document_count: int = 0
    last_scanned: Optional[datetime] = None
    
    # Scan settings
    recursive: bool = True
    file_patterns: List[str] = field(default_factory=lambda: ["*.md", "*.jpg", "*.png"])
    
    def validate(self) -> bool:
        """Check if folder exists and is accessible."""
        return self.path.exists() and self.path.is_dir()


@dataclass
class Relationship:
    """Represents a relationship between two documents."""
    
    source_doc_id: str
    target_doc_id: str
    relationship_type: str  # "wikilink", "tag", "semantic", etc.
    strength: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, any] = field(default_factory=dict)
    
    # Components of strength (per TECHNICAL_ARCHITECTURE.md)
    keyword_score: float = 0.0  # Weight: 0.3
    vector_score: float = 0.0  # Weight: 0.5
    manual_link_score: float = 0.0  # Weight: 0.2
    
    def calculate_strength(self):
        """Calculate overall relationship strength."""
        self.strength = (
            self.keyword_score * 0.3 +
            self.vector_score * 0.5 +
            self.manual_link_score * 0.2
        )


@dataclass
class KnowledgeBase:
    """Represents the entire knowledge base."""
    
    kb_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    
    # Source folders
    source_folders: List[SourceFolder] = field(default_factory=list)
    
    # Statistics
    total_documents: int = 0
    total_chunks: int = 0
    total_relationships: int = 0
    
    # Index info
    index_version: str = "0.1.0"
    vector_dim: int = 384  # Depends on embedding model
