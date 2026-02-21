"""
Tests for Import Manager

Tests importing vector database, metadata, and restoring from migration packages.
"""

import pytest
import json
import shutil
import zipfile
from pathlib import Path

from src.backend.migration.importer import ImportManager, ImportResult
from src.backend.migration.exporter import ExportManager
from src.backend.models.document import (
    Document, DocumentMetadata, DocumentChunk, Relationship, DocumentStatus
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
            file_hash=f"hash{i}",
            status=DocumentStatus.ACTIVE
        )
        docs.append(doc)
    return docs


@pytest.fixture
def export_dir(tmp_path, test_documents):
    """Create an export directory with test data"""
    export_path = tmp_path / "export"
    export_path.mkdir()
    
    # Create documents.json
    docs_json = []
    for doc in test_documents:
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
            "status": doc.status.value if hasattr(doc.status, 'value') else "active",
            "file_size": doc.file_size,
            "file_hash": doc.file_hash
        }
        docs_json.append(doc_dict)
    
    with open(export_path / "documents.json", "w", encoding="utf-8") as f:
        json.dump(docs_json, f, indent=2, ensure_ascii=False)
    
    # Create manifest.json
    manifest = {
        "metadata": {
            "export_date": "2024-01-01T00:00:00",
            "version": "1.0",
            "total_documents": len(test_documents),
            "total_chunks": sum(len(doc.chunks) for doc in test_documents),
            "total_relationships": sum(len(doc.relationships) for doc in test_documents),
            "source_folders": ["test"]
        },
        "documents": [],
        "vector_db_path": "vector_db"
    }
    
    with open(export_path / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    # Create empty vector_db directory
    (export_path / "vector_db").mkdir()
    (export_path / "vector_db" / "test.txt").write_text("test vector db")
    
    return export_path


@pytest.fixture
def vector_store(tmp_path):
    """Create a test vector store"""
    db_path = tmp_path / "chroma_db"
    return VectorStore(persist_directory=str(db_path))


def test_import_manager_init(tmp_path, vector_store):
    """Test ImportManager initialization"""
    import_path = tmp_path / "import"
    import_path.mkdir()
    
    manager = ImportManager(vector_store, import_path)
    
    assert manager.vector_store == vector_store
    assert manager.import_source == import_path
    assert manager.errors == []
    assert manager.warnings == []


def test_load_manifest(export_dir, vector_store):
    """Test loading manifest"""
    manager = ImportManager(vector_store, export_dir)
    manifest = manager.load_manifest(export_dir)
    
    assert manifest is not None
    assert "metadata" in manifest
    assert manifest["metadata"]["version"] == "1.0"
    assert manifest["metadata"]["total_documents"] == 3


def test_load_manifest_missing(tmp_path, vector_store):
    """Test loading manifest when file is missing"""
    import_path = tmp_path / "empty"
    import_path.mkdir()
    
    manager = ImportManager(vector_store, import_path)
    manifest = manager.load_manifest(import_path)
    
    assert manifest is None
    assert len(manager.errors) == 1
    assert "Manifest file not found" in manager.errors[0]


def test_import_documents(export_dir, vector_store):
    """Test importing documents"""
    manager = ImportManager(vector_store, export_dir)
    documents = manager.import_documents(export_dir)
    
    assert len(documents) == 3
    assert all(isinstance(doc, Document) for doc in documents)
    
    # Check first document
    doc = documents[0]
    assert doc.doc_id == "doc0"
    assert doc.metadata.title == "Document 0"
    assert len(doc.chunks) == 1
    assert len(doc.relationships) == 1
    assert isinstance(doc.status, DocumentStatus)


def test_import_documents_structure(export_dir, vector_store):
    """Test imported documents have correct structure"""
    manager = ImportManager(vector_store, export_dir)
    documents = manager.import_documents(export_dir)
    
    doc = documents[0]
    
    # Check chunk structure
    chunk = doc.chunks[0]
    assert chunk.chunk_id == "chunk0_0"
    assert chunk.document_id == "doc0"
    assert chunk.content == "Chunk 0 of document 0"
    
    # Check relationship structure
    rel = doc.relationships[0]
    assert rel.source_doc_id == "doc0"
    assert rel.target_doc_id == "doc1"
    assert rel.relationship_type == "wikilink"


def test_import_documents_missing(tmp_path, vector_store):
    """Test importing when documents.json is missing"""
    import_path = tmp_path / "empty"
    import_path.mkdir()
    
    manager = ImportManager(vector_store, import_path)
    documents = manager.import_documents(import_path)
    
    assert len(documents) == 0
    assert len(manager.errors) == 1
    assert "Documents file not found" in manager.errors[0]


def test_import_vector_database(export_dir, vector_store, tmp_path):
    """Test importing vector database"""
    manager = ImportManager(vector_store, export_dir)
    success = manager.import_vector_database(export_dir)
    
    assert success is True
    
    # Check database was copied
    target_dir = Path(vector_store.persist_directory)
    assert target_dir.exists()
    assert (target_dir / "test.txt").exists()


def test_import_vector_database_missing(tmp_path, vector_store):
    """Test importing when vector_db is missing"""
    import_path = tmp_path / "empty"
    import_path.mkdir()
    
    manager = ImportManager(vector_store, import_path)
    success = manager.import_vector_database(import_path)
    
    assert success is False
    assert len(manager.warnings) == 1
    assert "Vector database folder not found" in manager.warnings[0]


def test_import_all(export_dir, vector_store):
    """Test complete import operation"""
    manager = ImportManager(vector_store, export_dir)
    result = manager.import_all()
    
    assert result.success is True
    assert result.imported_documents == 3
    assert result.imported_chunks == 3
    assert result.imported_relationships == 3
    assert len(result.errors) == 0


def test_import_from_zip(export_dir, vector_store, tmp_path):
    """Test importing from ZIP archive"""
    # Create ZIP archive
    zip_path = tmp_path / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_path in export_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(export_dir)
                zipf.write(file_path, arcname)
    
    # Import from ZIP
    manager = ImportManager(vector_store, zip_path)
    result = manager.import_all()
    
    assert result.success is True
    assert result.imported_documents == 3


def test_get_import_info(export_dir, vector_store):
    """Test getting import info without importing"""
    manager = ImportManager(vector_store, export_dir)
    info = manager.get_import_info()
    
    assert info is not None
    assert info["version"] == "1.0"
    assert info["total_documents"] == 3
    assert info["export_date"] == "2024-01-01T00:00:00"


def test_get_import_info_invalid(tmp_path, vector_store):
    """Test getting import info from invalid source"""
    import_path = tmp_path / "empty"
    import_path.mkdir()
    
    manager = ImportManager(vector_store, import_path)
    info = manager.get_import_info()
    
    assert info is None
