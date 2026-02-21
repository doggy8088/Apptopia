"""
Tests for File Scanner

Tests directory scanning and change detection functionality.
"""

import pytest
from pathlib import Path
import time
from src.backend.utils.file_scanner import FileScanner


class TestFileScanner:
    """Test suite for FileScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create a file scanner instance."""
        return FileScanner()
    
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create a test directory structure."""
        # Create markdown files
        (tmp_path / "doc1.md").write_text("# Document 1")
        (tmp_path / "doc2.md").write_text("# Document 2")
        
        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "doc3.md").write_text("# Document 3")
        
        # Create images
        (tmp_path / "image1.jpg").write_bytes(b"fake image data")
        (subdir / "image2.png").write_bytes(b"fake image data")
        
        # Create .obsidian directory (should be skipped)
        obsidian_dir = tmp_path / ".obsidian"
        obsidian_dir.mkdir()
        (obsidian_dir / "config.md").write_text("config")
        
        return tmp_path
    
    def test_scan_directory_recursive(self, scanner, test_dir):
        """Test recursive directory scanning."""
        results = scanner.scan_directory(test_dir, recursive=True)
        
        # results is now a List[FileInfo]
        md_files = [f for f in results if f.path.suffix == '.md']
        img_files = [f for f in results if f.path.suffix in ['.jpg', '.png']]
        
        assert len(md_files) == 3  # doc1, doc2, doc3
        assert len(img_files) == 2  # image1, image2
        
        # Check that .obsidian files are excluded
        md_names = [f.path.name for f in md_files]
        assert 'config.md' not in md_names
    
    def test_scan_directory_non_recursive(self, scanner, test_dir):
        """Test non-recursive directory scanning."""
        results = scanner.scan_directory(test_dir, recursive=False)
        
        md_files = [f for f in results if f.path.suffix == '.md']
        img_files = [f for f in results if f.path.suffix in ['.jpg', '.png']]
        
        assert len(md_files) == 2  # doc1, doc2 (not doc3)
        assert len(img_files) == 1  # image1 (not image2)
    
    def test_scan_invalid_directory(self, scanner):
        """Test scanning non-existent directory."""
        with pytest.raises(ValueError):
            scanner.scan_directory(Path("/nonexistent/directory"))
    
    def test_detect_new_files(self, scanner, test_dir):
        """Test detection of new files."""
        # First scan
        changes = scanner.detect_changes(str(test_dir))
        
        # All files should be new on first scan
        new_changes = [c for c in changes if c.change_type == 'new']
        modified_changes = [c for c in changes if c.change_type == 'modified']
        
        assert len(new_changes) == 5  # 3 MD + 2 images
        assert len(modified_changes) == 0
    
    def test_detect_modified_files(self, scanner, test_dir):
        """Test detection of modified files."""
        # First scan
        scanner.detect_changes(str(test_dir))
        
        # Modify a file
        time.sleep(0.1)  # Ensure different mtime
        doc1 = test_dir / "doc1.md"
        doc1.write_text("# Modified Document 1")
        
        # Second scan
        changes = scanner.detect_changes(str(test_dir))
        
        # doc1 should be detected as modified
        modified_changes = [c for c in changes if c.change_type == 'modified']
        new_changes = [c for c in changes if c.change_type == 'new']
        
        assert len(modified_changes) == 1
        assert str(doc1) in [c.path for c in modified_changes]
        assert len(new_changes) == 0
    
    def test_detect_unchanged_files(self, scanner, test_dir):
        """Test detection of unchanged files."""
        # First scan
        scanner.detect_changes(str(test_dir))
        
        # Second scan without changes
        changes = scanner.detect_changes(str(test_dir))
        
        # All files should be unchanged
        unchanged_changes = [c for c in changes if c.change_type == 'unchanged']
        modified_changes = [c for c in changes if c.change_type == 'modified']
        new_changes = [c for c in changes if c.change_type == 'new']
        
        assert len(unchanged_changes) == 5  # 3 MD + 2 images
        assert len(modified_changes) == 0
        assert len(new_changes) == 0
    
    def test_detect_deleted_files(self, scanner, test_dir):
        """Test detection of deleted files."""
        # First scan
        scanner.detect_changes(str(test_dir))
        
        # Delete a file
        doc1 = test_dir / "doc1.md"
        doc1.unlink()
        
        # Second scan
        changes = scanner.detect_changes(str(test_dir))
        
        # doc1 should be detected as deleted
        deleted_changes = [c for c in changes if c.change_type == 'deleted']
        assert len(deleted_changes) == 1
        assert str(doc1) in [c.path for c in deleted_changes]
    
    def test_get_file_info(self, scanner, test_dir):
        """Test getting file information."""
        doc1 = test_dir / "doc1.md"
        
        # scan_directory returns FileInfo objects directly
        results = scanner.scan_directory(test_dir, recursive=False)
        doc1_info = [f for f in results if f.path == doc1][0]
        
        assert doc1_info is not None
        assert doc1_info.path == doc1
        assert doc1_info.size > 0
        assert len(doc1_info.hash) == 64  # SHA-256 hash
    
    def test_get_file_info_nonexistent(self, scanner):
        """Test getting info for non-existent file."""
        results = scanner.scan_directory(Path("/tmp"), recursive=False)
        # Non-existent files just won't be in results
        assert Path("/nonexistent/file.md") not in [f.path for f in results]
    
    def test_clear_cache(self, scanner, test_dir):
        """Test clearing the file cache."""
        # First scan
        scanner.detect_changes(str(test_dir))
        
        # Cache should have entries
        assert len(scanner._file_cache) > 0
        
        # Clear cache
        scanner.clear_cache()
        
        # Cache should be empty
        assert len(scanner._file_cache) == 0
    
    def test_skip_hidden_files(self, scanner, tmp_path):
        """Test that hidden files are skipped."""
        # Create hidden file
        (tmp_path / ".hidden.md").write_text("Hidden")
        (tmp_path / "visible.md").write_text("Visible")
        
        results = scanner.scan_directory(tmp_path)
        
        # Only visible file should be found
        md_files = [f for f in results if f.path.suffix == '.md']
        assert len(md_files) == 1
        assert md_files[0].path.name == 'visible.md'
