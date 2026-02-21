"""
Tests for Export Manager

Tests exporting vector database, metadata, and creating migration packages.
"""

import pytest
import json
import shutil
from pathlib import Path
from datetime import datetime

from src.backend.migration.exporter import ExportManager, ExportMetadata, ExportManifest
from src.backend.models.document import (
    Document, DocumentMetadata, DocumentChunk, Relationship
)
from src.backend.indexer.vector_store import VectorStore


@pytest.fixture
def test_documents():
    """Create test documents"""
    docs = []
    for i in range(3):
        doc = Document(
            doc_id=f"doc{i}",
            file_path=Path(f"/test/doc{i}.md"),
            relative_path=Path(f"doc{i}.md"),
            source_folder="test",
            raw_content=f"Content for document {i}",
            parsed_content=f"Content for document {i}",
            metadata=DocumentMetadata(
                title=f"Document {i}",
                tags=[f"tag{i}"],
                word_count=10
            ),
            chunks=[
                DocumentChunk(
                    chunk_id=f"chunk{i}_0",
                    content=f"Chunk 0 of document {i}",
                    document_id=f"doc{i}",
                    start_line=0,
                    end_line=5
                )
            ],
            relationships=[
                Relationship(
                    source_doc_id=f"doc{i}",
                    target_doc_id=f"doc{(i+1)%3}",
                    relationship_type="wikilink"
                )
            ],
            file_size=100,
            file_hash=f"hash{i}"
        )
        docs.append(doc)
    return docs


@pytest.fixture
def export_manager(tmp_path):
    """Create export manager with temp directory"""
    vector_store = VectorStore(persist_directory=str(tmp_path / "chroma_db"))
    export_dir = tmp_path / "export"
    return ExportManager(vector_store, export_dir)


# Test Initialization

def test_export_manager_init(tmp_path):
    """Test export manager initialization"""
    vector_store = VectorStore(persist_directory=str(tmp_path / "chroma_db"))
    export_dir = tmp_path / "export"
    
    manager = ExportManager(vector_store, export_dir)
    
    assert manager.vector_store == vector_store
    assert manager.export_dir == export_dir
    assert export_dir.exists()


# Test Document Export

def test_export_documents(export_manager, test_documents):
    """Test exporting documents to JSON"""
    output_path = export_manager.export_documents(test_documents)
    
    assert output_path.exists()
    assert output_path.name == "documents.json"
    
    # Verify content
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert len(data) == 3
    assert data[0]["doc_id"] == "doc0"


def test_export_documents_structure(export_manager, test_documents):
    """Test exported document structure"""
    output_path = export_manager.export_documents(test_documents)
    
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    doc = data[0]
    assert "doc_id" in doc
    assert "file_path" in doc
    assert "raw_content" in doc
    assert "parsed_content" in doc
    assert "metadata" in doc
    assert "chunks" in doc
    assert "relationships" in doc
    
    # Check metadata structure
    assert "title" in doc["metadata"]
    assert "tags" in doc["metadata"]
    
    # Check chunks structure
    assert len(doc["chunks"]) > 0
    chunk = doc["chunks"][0]
    assert "chunk_id" in chunk
    assert "content" in chunk
    
    # Check relationships structure
    assert len(doc["relationships"]) > 0
    rel = doc["relationships"][0]
    assert "source_doc_id" in rel
    assert "target_doc_id" in rel


def test_export_documents_custom_path(export_manager, test_documents, tmp_path):
    """Test exporting to custom path"""
    custom_path = tmp_path / "custom_docs.json"
    
    output_path = export_manager.export_documents(test_documents, custom_path)
    
    assert output_path == custom_path
    assert custom_path.exists()


# Test Vector Database Export

def test_export_vector_database(export_manager, tmp_path):
    """Test exporting vector database"""
    # Create some dummy database files
    db_dir = tmp_path / "chroma_db"
    db_dir.mkdir(exist_ok=True)
    (db_dir / "dummy_file.bin").write_text("dummy data")
    
    output_path = export_manager.export_vector_database()
    
    assert output_path.exists()
    assert output_path.is_dir()


def test_export_vector_database_empty(export_manager):
    """Test exporting when no database exists"""
    output_path = export_manager.export_vector_database()
    
    # Should create empty directory
    assert output_path.exists()
    assert output_path.is_dir()


# Test Manifest Creation

def test_create_manifest(export_manager, test_documents):
    """Test creating export manifest"""
    source_folders = ["/path/to/notes", "/path/to/docs"]
    
    manifest = export_manager.create_manifest(test_documents, source_folders)
    
    assert isinstance(manifest, ExportManifest)
    assert manifest.metadata.version == ExportManager.EXPORT_VERSION
    assert manifest.metadata.total_documents == 3
    assert manifest.metadata.total_chunks == 3
    assert manifest.metadata.total_relationships == 3
    assert manifest.metadata.source_folders == source_folders


def test_manifest_metadata(export_manager, test_documents):
    """Test manifest metadata"""
    manifest = export_manager.create_manifest(test_documents, [])
    
    assert manifest.metadata.export_date is not None
    # Should be valid ISO format date
    datetime.fromisoformat(manifest.metadata.export_date)


# Test Complete Export

def test_export_all(export_manager, test_documents):
    """Test complete export without archive"""
    source_folders = ["/test/folder"]
    
    export_path = export_manager.export_all(
        test_documents,
        source_folders,
        create_archive=False
    )
    
    assert export_path.exists()
    assert export_path.is_dir()
    
    # Check all files exist
    assert (export_path / "documents.json").exists()
    assert (export_path / "manifest.json").exists()
    assert (export_path / "vector_db").exists()


def test_export_all_with_archive(export_manager, test_documents):
    """Test complete export with ZIP archive"""
    source_folders = ["/test/folder"]
    
    archive_path = export_manager.export_all(
        test_documents,
        source_folders,
        create_archive=True
    )
    
    assert archive_path.exists()
    assert archive_path.suffix == ".zip"


def test_export_manifest_content(export_manager, test_documents):
    """Test manifest file content"""
    export_manager.export_all(test_documents, [], create_archive=False)
    
    manifest_path = export_manager.export_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    
    assert "metadata" in manifest_data
    assert "documents_file" in manifest_data
    assert "vector_db_path" in manifest_data
    
    assert manifest_data["documents_file"] == "documents.json"
    assert manifest_data["vector_db_path"] == "vector_db"


# Test Export Statistics

def test_get_export_stats(export_manager, test_documents):
    """Test getting export statistics"""
    stats = export_manager.get_export_stats(test_documents)
    
    assert "total_documents" in stats
    assert "total_chunks" in stats
    assert "total_relationships" in stats
    assert "total_content_bytes" in stats
    assert "avg_chunks_per_doc" in stats
    assert "avg_relationships_per_doc" in stats
    
    assert stats["total_documents"] == 3
    assert stats["total_chunks"] == 3
    assert stats["total_relationships"] == 3


def test_export_stats_empty(export_manager):
    """Test statistics with empty document list"""
    stats = export_manager.get_export_stats([])
    
    assert stats["total_documents"] == 0
    assert stats["total_chunks"] == 0
    assert stats["avg_chunks_per_doc"] == 0
