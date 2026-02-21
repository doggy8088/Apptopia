"""
Tests for Source Verifier.
"""

import pytest
from pathlib import Path
from src.backend.migration.verifier import (
    SourceVerifier,
    SourceStatus,
    VerificationReport
)
from src.backend.models.document import Document, DocumentMetadata, DocumentStatus


def create_test_document(doc_id: str, file_path: str, 
                        status: DocumentStatus = DocumentStatus.ACTIVE, 
                        create_file: bool = False) -> Document:
    """Helper to create test documents."""
    path = Path(file_path)
    
    # Create file if requested
    if create_file:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Content for {doc_id}")
    
    doc = Document(
        doc_id=doc_id,
        file_path=path,
        relative_path=path.name,
        source_folder=str(path.parent),
        raw_content=f"Content for {doc_id}",
        parsed_content=f"Content for {doc_id}",
        metadata=DocumentMetadata(),
        chunks=[],
        relationships=[],
        status=status
    )
    
    # Override status after __post_init__ if needed
    if not create_file:
        doc.status = status
    
    return doc


class TestSourceStatus:
    """Test SourceStatus dataclass."""
    
    def test_create_source_status(self):
        """Test creating source status."""
        status = SourceStatus(
            path="/path/to/folder",
            exists=True,
            document_count=5
        )
        
        assert status.path == "/path/to/folder"
        assert status.exists is True
        assert status.document_count == 5
    
    def test_source_status_to_dict(self):
        """Test converting source status to dict."""
        status = SourceStatus(
            path="/test/path",
            exists=False,
            document_count=3
        )
        
        result = status.to_dict()
        assert result["path"] == "/test/path"
        assert result["exists"] is False
        assert result["document_count"] == 3


class TestVerificationReport:
    """Test VerificationReport dataclass."""
    
    def test_create_report(self):
        """Test creating verification report."""
        statuses = [
            SourceStatus("/path1", True, 2),
            SourceStatus("/path2", False, 1)
        ]
        
        report = VerificationReport(
            total_sources=2,
            available_sources=1,
            missing_sources=1,
            frozen_documents=1,
            source_statuses=statuses
        )
        
        assert report.total_sources == 2
        assert report.available_sources == 1
        assert report.missing_sources == 1
        assert report.frozen_documents == 1
        assert len(report.source_statuses) == 2
    
    def test_report_to_dict(self):
        """Test converting report to dict."""
        statuses = [SourceStatus("/path", True, 1)]
        report = VerificationReport(
            total_sources=1,
            available_sources=1,
            missing_sources=0,
            frozen_documents=0,
            source_statuses=statuses
        )
        
        result = report.to_dict()
        assert result["total_sources"] == 1
        assert result["available_sources"] == 1
        assert result["missing_sources"] == 0
        assert result["frozen_documents"] == 0
        assert len(result["source_statuses"]) == 1


class TestSourceVerifier:
    """Test SourceVerifier."""
    
    def test_verify_all_sources_exist(self, tmp_path):
        """Test verification when all sources exist."""
        # Create source folders
        folder1 = tmp_path / "folder1"
        folder2 = tmp_path / "folder2"
        folder1.mkdir()
        folder2.mkdir()
        
        # Create documents with actual files
        docs = [
            create_test_document("doc1", str(folder1 / "file1.md"), create_file=True),
            create_test_document("doc2", str(folder2 / "file2.md"), create_file=True)
        ]
        
        verifier = SourceVerifier()
        report = verifier.verify_sources(
            docs,
            [str(folder1), str(folder2)]
        )
        
        assert report.total_sources == 2
        assert report.available_sources == 2
        assert report.missing_sources == 0
        assert report.frozen_documents == 0
        
        # All documents should remain active
        for doc in docs:
            assert doc.status == DocumentStatus.ACTIVE
    
    def test_verify_with_missing_source(self, tmp_path):
        """Test verification with missing source."""
        # Create only one folder
        folder1 = tmp_path / "folder1"
        folder1.mkdir()
        folder2_path = tmp_path / "folder2"  # Doesn't exist
        
        # Create documents (doc2 won't have a file)
        docs = [
            create_test_document("doc1", str(folder1 / "file1.md"), create_file=True),
            create_test_document("doc2", str(folder2_path / "file2.md"), create_file=False)
        ]
        
        verifier = SourceVerifier()
        report = verifier.verify_sources(
            docs,
            [str(folder1), str(folder2_path)]
        )
        
        assert report.total_sources == 2
        assert report.available_sources == 1
        assert report.missing_sources == 1
        assert report.frozen_documents == 1
        
        # doc1 should be active, doc2 should be frozen
        assert docs[0].status == DocumentStatus.ACTIVE
        assert docs[1].status == DocumentStatus.FROZEN
    
    def test_verify_unfreezes_when_source_returns(self, tmp_path):
        """Test that frozen docs get unfrozen when source returns."""
        folder = tmp_path / "folder"
        folder.mkdir()
        
        # Create document file and mark as frozen initially
        doc = create_test_document("doc1", str(folder / "file.md"), 
                                  status=DocumentStatus.FROZEN, create_file=True)
        # Manually set to frozen (overriding __post_init__)
        doc.status = DocumentStatus.FROZEN
        
        verifier = SourceVerifier()
        report = verifier.verify_sources([doc], [str(folder)])
        
        # Should be unfrozen now
        assert doc.status == DocumentStatus.ACTIVE
        assert report.frozen_documents == 0
    
    def test_get_frozen_documents(self):
        """Test getting frozen documents."""
        docs = [
            create_test_document("doc1", "/path1", DocumentStatus.ACTIVE),
            create_test_document("doc2", "/path2", DocumentStatus.FROZEN),
            create_test_document("doc3", "/path3", DocumentStatus.FROZEN)
        ]
        
        verifier = SourceVerifier()
        frozen = verifier.get_frozen_documents(docs)
        
        assert len(frozen) == 2
        assert all(d.status == DocumentStatus.FROZEN for d in frozen)
    
    def test_get_available_documents(self):
        """Test getting available documents."""
        docs = [
            create_test_document("doc1", "/path1", DocumentStatus.ACTIVE),
            create_test_document("doc2", "/path2", DocumentStatus.FROZEN),
            create_test_document("doc3", "/path3", DocumentStatus.ACTIVE)
        ]
        
        verifier = SourceVerifier()
        available = verifier.get_available_documents(docs)
        
        assert len(available) == 2
        assert all(d.status != DocumentStatus.FROZEN for d in available)
    
    def test_document_counts_per_source(self, tmp_path):
        """Test document counting per source."""
        folder1 = tmp_path / "folder1"
        folder2 = tmp_path / "folder2"
        folder1.mkdir()
        folder2.mkdir()
        
        docs = [
            create_test_document("doc1", str(folder1 / "file1.md"), create_file=True),
            create_test_document("doc2", str(folder1 / "file2.md"), create_file=True),
            create_test_document("doc3", str(folder2 / "file3.md"), create_file=True)
        ]
        
        verifier = SourceVerifier()
        report = verifier.verify_sources(
            docs,
            [str(folder1), str(folder2)]
        )
        
        # Check document counts
        folder1_status = [s for s in report.source_statuses if s.path == str(folder1)][0]
        folder2_status = [s for s in report.source_statuses if s.path == str(folder2)][0]
        
        assert folder1_status.document_count == 2
        assert folder2_status.document_count == 1
    
    def test_empty_documents_list(self, tmp_path):
        """Test verification with no documents."""
        folder = tmp_path / "folder"
        folder.mkdir()
        
        verifier = SourceVerifier()
        report = verifier.verify_sources([], [str(folder)])
        
        assert report.total_sources == 1
        assert report.available_sources == 1
        assert report.frozen_documents == 0
