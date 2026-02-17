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
        
        assert len(results['markdown']) == 3  # doc1, doc2, doc3
        assert len(results['images']) == 2  # image1, image2
        
        # Check that .obsidian files are excluded
        md_names = [f.name for f in results['markdown']]
        assert 'config.md' not in md_names
    
    def test_scan_directory_non_recursive(self, scanner, test_dir):
        """Test non-recursive directory scanning."""
        results = scanner.scan_directory(test_dir, recursive=False)
        
        assert len(results['markdown']) == 2  # doc1, doc2 (not doc3)
        assert len(results['images']) == 1  # image1 (not image2)
    
    def test_scan_invalid_directory(self, scanner):
        """Test scanning non-existent directory."""
        with pytest.raises(ValueError):
            scanner.scan_directory(Path("/nonexistent/directory"))
    
    def test_detect_new_files(self, scanner, test_dir):
        """Test detection of new files."""
        # First scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        
        changes = scanner.detect_changes(all_files)
        
        # All files should be new on first scan
        assert len(changes['new']) == len(all_files)
        assert len(changes['modified']) == 0
        assert len(changes['unchanged']) == 0
    
    def test_detect_modified_files(self, scanner, test_dir):
        """Test detection of modified files."""
        # First scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        scanner.detect_changes(all_files)
        
        # Modify a file
        time.sleep(0.1)  # Ensure different mtime
        doc1 = test_dir / "doc1.md"
        doc1.write_text("# Modified Document 1")
        
        # Second scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        changes = scanner.detect_changes(all_files)
        
        # doc1 should be detected as modified
        assert len(changes['modified']) == 1
        assert doc1 in changes['modified']
        assert len(changes['new']) == 0
    
    def test_detect_unchanged_files(self, scanner, test_dir):
        """Test detection of unchanged files."""
        # First scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        scanner.detect_changes(all_files)
        
        # Second scan without changes
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        changes = scanner.detect_changes(all_files)
        
        # All files should be unchanged
        assert len(changes['unchanged']) == len(all_files)
        assert len(changes['modified']) == 0
        assert len(changes['new']) == 0
    
    def test_detect_deleted_files(self, scanner, test_dir):
        """Test detection of deleted files."""
        # First scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        scanner.detect_changes(all_files)
        
        # Delete a file
        doc1 = test_dir / "doc1.md"
        doc1.unlink()
        
        # Second scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        changes = scanner.detect_changes(all_files)
        
        # doc1 should be detected as deleted
        assert len(changes['deleted']) == 1
        assert doc1 in changes['deleted']
    
    def test_get_file_info(self, scanner, test_dir):
        """Test getting file information."""
        doc1 = test_dir / "doc1.md"
        info = scanner.get_file_info(doc1)
        
        assert info is not None
        assert info['name'] == 'doc1.md'
        assert info['size'] > 0
        assert info['extension'] == '.md'
        assert len(info['hash']) == 64  # SHA-256 hash
        assert 'modified_time' in info
        assert 'created_time' in info
    
    def test_get_file_info_nonexistent(self, scanner):
        """Test getting info for non-existent file."""
        info = scanner.get_file_info(Path("/nonexistent/file.md"))
        assert info is None
    
    def test_clear_cache(self, scanner, test_dir):
        """Test clearing the file cache."""
        # First scan
        results = scanner.scan_directory(test_dir)
        all_files = results['markdown'] + results['images']
        scanner.detect_changes(all_files)
        
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
        assert len(results['markdown']) == 1
        assert results['markdown'][0].name == 'visible.md'
