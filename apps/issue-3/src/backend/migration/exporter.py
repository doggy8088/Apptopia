"""
Export Manager for Database Migration

Handles exporting vector database, metadata, and relationships
for migration to different systems or backup purposes.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import shutil
import zipfile

from ..models.document import Document
from ..indexer.vector_store import VectorStore


@dataclass
class ExportMetadata:
    """Metadata about the export"""
    export_date: str
    version: str  # Export format version
    total_documents: int
    total_chunks: int
    total_relationships: int
    source_folders: List[str]


@dataclass
class ExportManifest:
    """Complete export manifest"""
    metadata: ExportMetadata
    documents: List[Dict]  # Serialized documents
    vector_db_path: str
    checksum: Optional[str] = None


class ExportManager:
    """
    Manager for exporting knowledge base data
    
    Exports vector database, document metadata, and relationships
    in a portable format.
    """
    
    EXPORT_VERSION = "1.0"
    
    def __init__(self, vector_store: VectorStore, export_dir: Path):
        """
        Initialize export manager
        
        Args:
            vector_store: VectorStore to export
            export_dir: Directory for export files
        """
        self.vector_store = vector_store
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_documents(
        self,
        documents: List[Document],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export documents metadata to JSON
        
        Args:
            documents: List of documents to export
            output_path: Optional custom output path
        
        Returns:
            Path to exported documents file
        """
        if output_path is None:
            output_path = self.export_dir / "documents.json"
        
        # Serialize documents
        doc_data = []
        for doc in documents:
            doc_dict = {
                "doc_id": doc.doc_id,
                "file_path": str(doc.file_path),
                "relative_path": str(doc.relative_path),
                "source_folder": doc.source_folder,
                "raw_content": doc.raw_content,
                "parsed_content": doc.parsed_content,
                "metadata": {
                    "title": doc.metadata.title,
                    "tags": doc.metadata.tags,
                    "aliases": doc.metadata.aliases,
                    "word_count": doc.metadata.word_count,
                    "headings": doc.metadata.headings,
                    "custom_fields": doc.metadata.custom_fields
                },
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "document_id": chunk.document_id,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "metadata": chunk.metadata
                    }
                    for chunk in doc.chunks
                ],
                "relationships": [
                    {
                        "source_doc_id": rel.source_doc_id,
                        "target_doc_id": rel.target_doc_id,
                        "relationship_type": rel.relationship_type,
                        "strength": rel.strength,
                        "keyword_score": rel.keyword_score,
                        "vector_score": rel.vector_score,
                        "manual_link_score": rel.manual_link_score,
                        "metadata": rel.metadata
                    }
                    for rel in doc.relationships
                ],
                "status": doc.status.value,
                "file_size": doc.file_size,
                "file_hash": doc.file_hash
            }
            doc_data.append(doc_dict)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(doc_data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_vector_database(
        self,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export vector database
        
        Args:
            output_path: Optional custom output path
        
        Returns:
            Path to exported vector database directory
        """
        if output_path is None:
            output_path = self.export_dir / "vector_db"
        
        # ChromaDB stores data in a directory
        # Copy the entire persistence directory
        if self.vector_store.persist_directory:
            source_dir = Path(self.vector_store.persist_directory)
            if source_dir.exists():
                # Copy directory recursively
                if output_path.exists():
                    shutil.rmtree(output_path)
                shutil.copytree(source_dir, output_path)
            else:
                # Create empty directory if source doesn't exist
                output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def create_manifest(
        self,
        documents: List[Document],
        source_folders: List[str]
    ) -> ExportManifest:
        """
        Create export manifest
        
        Args:
            documents: Documents being exported
            source_folders: Source folder paths
        
        Returns:
            ExportManifest object
        """
        # Count chunks and relationships
        total_chunks = sum(len(doc.chunks) for doc in documents)
        total_relationships = sum(len(doc.relationships) for doc in documents)
        
        metadata = ExportMetadata(
            export_date=datetime.now().isoformat(),
            version=self.EXPORT_VERSION,
            total_documents=len(documents),
            total_chunks=total_chunks,
            total_relationships=total_relationships,
            source_folders=source_folders
        )
        
        manifest = ExportManifest(
            metadata=metadata,
            documents=[],  # Will be in separate file
            vector_db_path="vector_db"
        )
        
        return manifest
    
    def export_all(
        self,
        documents: List[Document],
        source_folders: List[str],
        create_archive: bool = True
    ) -> Path:
        """
        Export complete knowledge base
        
        Args:
            documents: All documents to export
            source_folders: Source folder paths
            create_archive: Whether to create ZIP archive
        
        Returns:
            Path to export directory or ZIP file
        """
        # Export documents
        docs_path = self.export_documents(documents)
        
        # Export vector database
        vector_db_path = self.export_vector_database()
        
        # Create manifest
        manifest = self.create_manifest(documents, source_folders)
        
        # Write manifest
        manifest_path = self.export_dir / "manifest.json"
        manifest_dict = {
            "metadata": asdict(manifest.metadata),
            "documents_file": "documents.json",
            "vector_db_path": "vector_db"
        }
        
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_dict, f, ensure_ascii=False, indent=2)
        
        # Create ZIP archive if requested
        if create_archive:
            archive_path = self.export_dir.parent / f"{self.export_dir.name}.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add all files in export directory
                for file_path in self.export_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.export_dir)
                        zipf.write(file_path, arcname)
            
            return archive_path
        
        return self.export_dir
    
    def get_export_stats(self, documents: List[Document]) -> Dict[str, any]:
        """
        Get statistics about what will be exported
        
        Args:
            documents: Documents to be exported
        
        Returns:
            Dict with export statistics
        """
        total_chunks = sum(len(doc.chunks) for doc in documents)
        total_relationships = sum(len(doc.relationships) for doc in documents)
        total_content_size = sum(len(doc.raw_content.encode('utf-8')) for doc in documents)
        
        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "total_relationships": total_relationships,
            "total_content_bytes": total_content_size,
            "avg_chunks_per_doc": total_chunks / len(documents) if documents else 0,
            "avg_relationships_per_doc": total_relationships / len(documents) if documents else 0
        }
