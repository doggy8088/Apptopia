"""
Import Manager for Database Migration

Handles importing vector database, metadata, and relationships
from exported backup files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import json
import shutil
import zipfile
import tempfile

from ..models.document import (
    Document,
    DocumentMetadata,
    DocumentChunk,
    Relationship,
    DocumentStatus
)
from ..indexer.vector_store import VectorStore


@dataclass
class ImportResult:
    """Result of import operation"""
    success: bool
    imported_documents: int
    imported_chunks: int
    imported_relationships: int
    errors: List[str]
    warnings: List[str]


class ImportManager:
    """
    Manager for importing knowledge base data
    
    Imports vector database, document metadata, and relationships
    from exported backup files.
    """
    
    def __init__(self, vector_store: VectorStore, import_source: Path):
        """
        Initialize import manager
        
        Args:
            vector_store: VectorStore to import into
            import_source: Path to import directory or ZIP file
        """
        self.vector_store = vector_store
        self.import_source = Path(import_source)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def _extract_if_archive(self) -> Path:
        """
        Extract ZIP archive if needed
        
        Returns:
            Path to import directory
        """
        if self.import_source.suffix == ".zip":
            # Create temporary directory for extraction
            temp_dir = Path(tempfile.mkdtemp(prefix="import_"))
            
            with zipfile.ZipFile(self.import_source, "r") as zipf:
                zipf.extractall(temp_dir)
            
            return temp_dir
        else:
            return self.import_source
    
    def load_manifest(self, import_dir: Path) -> Optional[Dict]:
        """
        Load import manifest
        
        Args:
            import_dir: Directory containing manifest
        
        Returns:
            Manifest dictionary or None if not found
        """
        manifest_path = import_dir / "manifest.json"
        if not manifest_path.exists():
            self.errors.append("Manifest file not found")
            return None
        
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid manifest JSON: {e}")
            return None
    
    def import_documents(self, import_dir: Path) -> List[Document]:
        """
        Import documents from JSON
        
        Args:
            import_dir: Directory containing documents.json
        
        Returns:
            List of imported Document objects
        """
        docs_path = import_dir / "documents.json"
        if not docs_path.exists():
            self.errors.append("Documents file not found")
            return []
        
        try:
            with open(docs_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid documents JSON: {e}")
            return []
        
        documents = []
        for doc_dict in doc_data:
            try:
                # Reconstruct metadata
                metadata = DocumentMetadata(
                    title=doc_dict["metadata"]["title"],
                    tags=doc_dict["metadata"]["tags"],
                    aliases=doc_dict["metadata"]["aliases"],
                    word_count=doc_dict["metadata"]["word_count"],
                    headings=doc_dict["metadata"]["headings"],
                    custom_fields=doc_dict["metadata"]["custom_fields"]
                )
                
                # Reconstruct chunks
                chunks = []
                for chunk_dict in doc_dict["chunks"]:
                    chunk = DocumentChunk(
                        chunk_id=chunk_dict["chunk_id"],
                        content=chunk_dict["content"],
                        document_id=chunk_dict["document_id"],
                        start_line=chunk_dict["start_line"],
                        end_line=chunk_dict["end_line"],
                        metadata=chunk_dict.get("metadata", {})
                    )
                    chunks.append(chunk)
                
                # Reconstruct relationships
                relationships = []
                for rel_dict in doc_dict["relationships"]:
                    rel = Relationship(
                        source_doc_id=rel_dict["source_doc_id"],
                        target_doc_id=rel_dict["target_doc_id"],
                        relationship_type=rel_dict["relationship_type"],
                        strength=rel_dict["strength"],
                        keyword_score=rel_dict.get("keyword_score", 0.0),
                        vector_score=rel_dict.get("vector_score", 0.0),
                        manual_link_score=rel_dict.get("manual_link_score", 0.0),
                        metadata=rel_dict.get("metadata", {})
                    )
                    relationships.append(rel)
                
                # Reconstruct document
                doc = Document(
                    doc_id=doc_dict["doc_id"],
                    file_path=Path(doc_dict["file_path"]),
                    relative_path=Path(doc_dict["relative_path"]),
                    source_folder=doc_dict["source_folder"],
                    raw_content=doc_dict["raw_content"],
                    parsed_content=doc_dict["parsed_content"],
                    metadata=metadata,
                    chunks=chunks,
                    relationships=relationships,
                    status=DocumentStatus(doc_dict["status"]),
                    file_size=doc_dict.get("file_size", 0),
                    file_hash=doc_dict.get("file_hash", "")
                )
                
                documents.append(doc)
                
            except (KeyError, ValueError) as e:
                self.errors.append(f"Failed to import document {doc_dict.get('doc_id', 'unknown')}: {e}")
                continue
        
        return documents
    
    def import_vector_database(self, import_dir: Path) -> bool:
        """
        Import vector database
        
        Args:
            import_dir: Directory containing vector_db folder
        
        Returns:
            True if successful, False otherwise
        """
        vector_db_path = import_dir / "vector_db"
        if not vector_db_path.exists():
            self.warnings.append("Vector database folder not found")
            return False
        
        # Copy vector database to store's persistence directory
        if self.vector_store.persist_directory:
            target_dir = Path(self.vector_store.persist_directory)
            
            try:
                # Remove existing database if present
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                
                # Copy imported database
                shutil.copytree(vector_db_path, target_dir)
                return True
                
            except Exception as e:
                self.errors.append(f"Failed to import vector database: {e}")
                return False
        else:
            self.warnings.append("Vector store has no persistence directory")
            return False
    
    def import_all(self) -> ImportResult:
        """
        Import complete knowledge base
        
        Returns:
            ImportResult with status and statistics
        """
        self.errors = []
        self.warnings = []
        
        # Extract archive if needed
        import_dir = self._extract_if_archive()
        
        # Load manifest
        manifest = self.load_manifest(import_dir)
        if manifest is None:
            return ImportResult(
                success=False,
                imported_documents=0,
                imported_chunks=0,
                imported_relationships=0,
                errors=self.errors,
                warnings=self.warnings
            )
        
        # Import documents
        documents = self.import_documents(import_dir)
        
        # Import vector database
        vector_db_success = self.import_vector_database(import_dir)
        
        # Calculate statistics
        total_chunks = sum(len(doc.chunks) for doc in documents)
        total_relationships = sum(len(doc.relationships) for doc in documents)
        
        success = len(documents) > 0 and len(self.errors) == 0
        
        # Clean up temporary directory if we extracted an archive
        if self.import_source.suffix == ".zip" and import_dir != self.import_source:
            shutil.rmtree(import_dir, ignore_errors=True)
        
        return ImportResult(
            success=success,
            imported_documents=len(documents),
            imported_chunks=total_chunks,
            imported_relationships=total_relationships,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def get_import_info(self) -> Optional[Dict]:
        """
        Get information about import without actually importing
        
        Returns:
            Dictionary with import information or None if invalid
        """
        import_dir = self._extract_if_archive()
        manifest = self.load_manifest(import_dir)
        
        # Clean up if extracted
        if self.import_source.suffix == ".zip" and import_dir != self.import_source:
            shutil.rmtree(import_dir, ignore_errors=True)
        
        if manifest:
            return manifest.get("metadata", {})
        return None
