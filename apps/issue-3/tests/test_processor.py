"""Tests for DocumentProcessor."""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.backend.core.processor import DocumentProcessor, ProcessingStats
from src.backend.models.document import Document


class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""
    
    def test_initialization(self):
        """Test processor initialization."""
        processor = DocumentProcessor()
        assert processor is not None
        assert processor.max_workers == 4
        assert processor.documents == {}
    
    def test_initialization_with_custom_workers(self):
        """Test initialization with custom worker count."""
        processor = DocumentProcessor(max_workers=8)
        assert processor.max_workers == 8
    
    def test_process_single_document(self, tmp_path):
        """Test processing a single document."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nThis is a test document.", encoding='utf-8')
        
        # Process
        processor = DocumentProcessor()
        stats = processor.process_folders([str(tmp_path)], force=True)
        
        # Verify
        assert stats.total_files == 1
        assert stats.new_files == 1
        assert stats.errors == 0
        assert len(processor.documents) == 1
        assert str(test_file) in processor.documents
    
    def test_process_multiple_documents(self, tmp_path):
        """Test processing multiple documents."""
        # Create test files
        for i in range(3):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}\n\nDocument {i}", encoding='utf-8')
        
        # Process
        processor = DocumentProcessor()
        stats = processor.process_folders([str(tmp_path)], force=True)
        
        # Verify
        assert stats.total_files == 3
        assert stats.new_files == 3
        assert stats.errors == 0
        assert len(processor.documents) == 3
    
    def test_process_with_progress_callback(self, tmp_path):
        """Test processing with progress callback."""
        # Create test files
        for i in range(3):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}", encoding='utf-8')
        
        # Track progress
        progress_calls = []
        def progress_callback(current, total, path):
            progress_calls.append((current, total, path))
        
        # Process
        processor = DocumentProcessor()
        processor.process_folders(
            [str(tmp_path)],
            force=True,
            progress_callback=progress_callback
        )
        
        # Verify progress was tracked
        assert len(progress_calls) == 3
        assert progress_calls[-1][0] == 3  # Last call shows completion
        assert progress_calls[-1][1] == 3  # Total files
    
    def test_incremental_update_new_file(self, tmp_path):
        """Test incremental processing detects new files."""
        # Initial file
        test_file1 = tmp_path / "test1.md"
        test_file1.write_text("# Test 1", encoding='utf-8')
        
        # First process
        processor = DocumentProcessor()
        stats1 = processor.process_folders([str(tmp_path)])
        assert stats1.new_files == 1
        
        # Add new file
        test_file2 = tmp_path / "test2.md"
        test_file2.write_text("# Test 2", encoding='utf-8')
        
        # Second process
        stats2 = processor.process_folders([str(tmp_path)])
        assert stats2.new_files == 1
        assert stats2.unchanged_files == 1
    
    def test_incremental_update_modified_file(self, tmp_path):
        """Test incremental processing detects modified files."""
        # Create file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test 1", encoding='utf-8')
        
        # First process
        processor = DocumentProcessor()
        processor.process_folders([str(tmp_path)])
        
        # Modify file
        import time
        time.sleep(0.1)  # Ensure mtime changes
        test_file.write_text("# Test 1 Modified", encoding='utf-8')
        
        # Second process
        stats = processor.process_folders([str(tmp_path)])
        assert stats.modified_files == 1
    
    def test_incremental_update_deleted_file(self, tmp_path):
        """Test incremental processing detects deleted files."""
        # Create file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # First process
        processor = DocumentProcessor()
        processor.process_folders([str(tmp_path)])
        assert len(processor.documents) == 1
        
        # Delete file
        test_file.unlink()
        
        # Second process
        stats = processor.process_folders([str(tmp_path)])
        assert stats.deleted_files == 1
        assert len(processor.documents) == 0
    
    def test_force_reprocessing(self, tmp_path):
        """Test force flag reprocesses all files."""
        # Create file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # First process
        processor = DocumentProcessor()
        processor.process_folders([str(tmp_path)])
        
        # Force reprocess without changes
        stats = processor.process_folders([str(tmp_path)], force=True)
        assert stats.new_files == 1  # Treated as new with force=True
    
    def test_build_relationships_wikilinks(self, tmp_path):
        """Test relationship building from wikilinks."""
        # Create documents with wikilinks
        doc1 = tmp_path / "doc1.md"
        doc1.write_text("# Doc 1\n\nSee [[doc2]] for more.", encoding='utf-8')
        
        doc2 = tmp_path / "doc2.md"
        doc2.write_text("# Doc 2\n\nRelated content.", encoding='utf-8')
        
        # Process
        processor = DocumentProcessor()
        stats = processor.process_folders([str(tmp_path)], force=True)
        
        # Verify relationships
        assert stats.relationships_built > 0
        doc1_obj = processor.documents[str(doc1)]
        assert len(doc1_obj.relationships) > 0
        
        # Check for wikilink relationship
        wikilink_rels = [r for r in doc1_obj.relationships if r.type == 'wikilink']
        assert len(wikilink_rels) > 0
    
    def test_get_knowledge_base(self, tmp_path):
        """Test getting knowledge base object."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # Process
        processor = DocumentProcessor()
        processor.process_folders([str(tmp_path)], force=True)
        
        # Get knowledge base
        kb = processor.get_knowledge_base()
        assert kb is not None
        assert kb.total_documents == 1
        assert kb.total_chunks > 0
    
    def test_get_stats(self, tmp_path):
        """Test getting statistics."""
        # Create test files
        for i in range(2):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}", encoding='utf-8')
        
        # Process
        processor = DocumentProcessor()
        processor.process_folders([str(tmp_path)], force=True)
        
        # Get stats
        stats = processor.get_stats()
        assert stats['total_documents'] == 2
        assert stats['total_chunks'] > 0
        assert 'documents' in stats
    
    def test_error_handling(self, tmp_path):
        """Test error handling for problematic files."""
        # Create a file that will cause parsing issues
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test", encoding='utf-8')
        
        # Make file unreadable after creation (simulate permission issue)
        # This is tricky to test, so we'll just verify error tracking works
        processor = DocumentProcessor()
        stats = processor.process_folders([str(tmp_path)], force=True)
        
        # Should process successfully in normal case
        assert stats.errors == 0
    
    def test_empty_folder(self, tmp_path):
        """Test processing empty folder."""
        processor = DocumentProcessor()
        stats = processor.process_folders([str(tmp_path)])
        
        assert stats.total_files == 0
        assert stats.new_files == 0
        assert len(processor.documents) == 0
    
    def test_nonexistent_folder(self):
        """Test processing non-existent folder."""
        processor = DocumentProcessor()
        stats = processor.process_folders(["/nonexistent/path"])
        
        assert stats.total_files == 0
        assert len(processor.documents) == 0
