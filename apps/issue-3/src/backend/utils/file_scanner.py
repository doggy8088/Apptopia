"""
File Scanner

Scans directories for Markdown and image files, detects changes,
and manages document discovery.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime


class FileScanner:
    """Scans directories for documents and images."""
    
    def __init__(self, file_patterns: List[str] = None):
        """
        Initialize the file scanner.
        
        Args:
            file_patterns: List of glob patterns (default: ["*.md", "*.jpg", "*.png"])
        """
        self.file_patterns = file_patterns or ["*.md", "*.jpg", "*.png"]
        self._file_cache: Dict[Path, Tuple[float, str]] = {}  # path -> (mtime, hash)
    
    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> Dict[str, List[Path]]:
        """
        Scan a directory for files matching patterns.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            Dictionary mapping file type to list of paths
            {'markdown': [...], 'images': [...]}
        """
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
        
        results = {
            'markdown': [],
            'images': []
        }
        
        for pattern in self.file_patterns:
            if recursive:
                files = directory.rglob(pattern)
            else:
                files = directory.glob(pattern)
            
            for file_path in files:
                # Skip hidden files and Obsidian config
                if self._should_skip(file_path):
                    continue
                
                # Categorize by extension
                ext = file_path.suffix.lower()
                if ext == '.md':
                    results['markdown'].append(file_path)
                elif ext in ['.jpg', '.jpeg', '.png']:
                    results['images'].append(file_path)
        
        return results
    
    def detect_changes(
        self,
        files: List[Path]
    ) -> Dict[str, List[Path]]:
        """
        Detect which files have changed since last scan.
        
        Args:
            files: List of file paths to check
            
        Returns:
            Dictionary with 'new', 'modified', 'unchanged' keys
        """
        changes = {
            'new': [],
            'modified': [],
            'unchanged': [],
            'deleted': []
        }
        
        current_files = set(files)
        cached_files = set(self._file_cache.keys())
        
        # Detect deleted files
        deleted = cached_files - current_files
        changes['deleted'] = list(deleted)
        
        # Check existing files
        for file_path in current_files:
            if not file_path.exists():
                continue
            
            current_mtime = file_path.stat().st_mtime
            
            if file_path not in self._file_cache:
                # New file
                changes['new'].append(file_path)
                file_hash = self._compute_file_hash(file_path)
                self._file_cache[file_path] = (current_mtime, file_hash)
            else:
                # Check if modified
                cached_mtime, cached_hash = self._file_cache[file_path]
                
                if current_mtime > cached_mtime:
                    # File might be modified, verify with hash
                    current_hash = self._compute_file_hash(file_path)
                    
                    if current_hash != cached_hash:
                        changes['modified'].append(file_path)
                        self._file_cache[file_path] = (current_mtime, current_hash)
                    else:
                        changes['unchanged'].append(file_path)
                else:
                    changes['unchanged'].append(file_path)
        
        # Clean up deleted files from cache
        for deleted_file in deleted:
            if deleted_file in self._file_cache:
                del self._file_cache[deleted_file]
        
        return changes
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if a file should be skipped."""
        # Skip hidden files
        if any(part.startswith('.') for part in file_path.parts):
            return True
        
        # Skip Obsidian config directories
        if '.obsidian' in file_path.parts or '.smart-env' in file_path.parts:
            return True
        
        return False
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read in chunks for large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error computing hash for {file_path}: {e}")
            return ""
    
    def get_file_info(self, file_path: Path) -> Dict[str, any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        
        return {
            'path': file_path,
            'name': file_path.name,
            'size': stat.st_size,
            'modified_time': datetime.fromtimestamp(stat.st_mtime),
            'created_time': datetime.fromtimestamp(stat.st_ctime),
            'extension': file_path.suffix.lower(),
            'hash': self._compute_file_hash(file_path)
        }
    
    def clear_cache(self):
        """Clear the file cache."""
        self._file_cache.clear()
