"""
File Scanner

Scans directories for Markdown and image files, detects changes,
and manages document discovery.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    mtime: float
    hash: str


@dataclass
class FileChange:
    """Represents a change to a file."""
    path: str
    change_type: str  # 'new', 'modified', 'deleted', 'unchanged'
    size: int = 0
    mtime: float = 0.0
    hash: str = ""


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
        directory: str,
        recursive: bool = True
    ) -> List[FileInfo]:
        """
        Scan a directory for files matching patterns.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of FileInfo objects
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory does not exist: {directory}")
        
        results = []
        
        for pattern in self.file_patterns:
            if recursive:
                files = dir_path.rglob(pattern)
            else:
                files = dir_path.glob(pattern)
            
            for file_path in files:
                # Skip hidden files and Obsidian config
                if self._should_skip(file_path):
                    continue
                
                # Get file info
                stat = file_path.stat()
                file_hash = self._compute_file_hash(file_path)
                
                info = FileInfo(
                    path=file_path,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                    hash=file_hash
                )
                results.append(info)
        
        return results
    
    def detect_changes(
        self,
        directory: str,
        recursive: bool = True
    ) -> List[FileChange]:
        """
        Detect which files have changed since last scan.
        
        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of FileChange objects
        """
        # Scan current files
        current_files = self.scan_directory(directory, recursive)
        current_paths = {str(f.path): f for f in current_files}
        cached_paths = set(str(p) for p in self._file_cache.keys())
        
        changes = []
        
        # Detect deleted files
        deleted_paths = cached_paths - set(current_paths.keys())
        for path in deleted_paths:
            changes.append(FileChange(
                path=path,
                change_type='deleted'
            ))
            # Remove from cache
            path_obj = Path(path)
            if path_obj in self._file_cache:
                del self._file_cache[path_obj]
        
        # Check current files
        for path_str, file_info in current_paths.items():
            path_obj = file_info.path
            
            if path_obj not in self._file_cache:
                # New file
                changes.append(FileChange(
                    path=path_str,
                    change_type='new',
                    size=file_info.size,
                    mtime=file_info.mtime,
                    hash=file_info.hash
                ))
                self._file_cache[path_obj] = (file_info.mtime, file_info.hash)
            else:
                # Check if modified
                cached_mtime, cached_hash = self._file_cache[path_obj]
                
                if file_info.hash != cached_hash:
                    changes.append(FileChange(
                        path=path_str,
                        change_type='modified',
                        size=file_info.size,
                        mtime=file_info.mtime,
                        hash=file_info.hash
                    ))
                    self._file_cache[path_obj] = (file_info.mtime, file_info.hash)
                else:
                    changes.append(FileChange(
                        path=path_str,
                        change_type='unchanged',
                        size=file_info.size,
                        mtime=file_info.mtime,
                        hash=file_info.hash
                    ))
        
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
