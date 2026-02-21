"""
Source Verifier for checking source folder availability after migration.

This module provides functionality to verify that source folders referenced in
imported documents still exist, marking missing sources as "frozen".
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set
from ..models.document import Document, DocumentStatus


@dataclass
class SourceStatus:
    """Status of a source folder."""
    path: str
    exists: bool
    document_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "exists": self.exists,
            "document_count": self.document_count
        }


@dataclass
class VerificationReport:
    """Report of source folder verification."""
    total_sources: int
    available_sources: int
    missing_sources: int
    frozen_documents: int
    source_statuses: List[SourceStatus]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "total_sources": self.total_sources,
            "available_sources": self.available_sources,
            "missing_sources": self.missing_sources,
            "frozen_documents": self.frozen_documents,
            "source_statuses": [s.to_dict() for s in self.source_statuses]
        }


class SourceVerifier:
    """Verify source folder availability after migration."""
    
    def verify_sources(self, documents: List[Document], 
                      source_folders: List[str]) -> VerificationReport:
        """
        Verify that source folders exist and mark documents accordingly.
        
        Args:
            documents: List of documents to verify
            source_folders: List of source folder paths to check
            
        Returns:
            VerificationReport with verification results
        """
        # Check which source folders exist
        existing_sources = set()
        missing_sources = set()
        
        for folder in source_folders:
            if Path(folder).exists():
                existing_sources.add(folder)
            else:
                missing_sources.add(folder)
        
        # Count documents per source
        source_doc_counts: Dict[str, int] = {}
        frozen_count = 0
        
        for doc in documents:
            # Find which source folder this document belongs to
            doc_source = self._find_document_source(doc, source_folders)
            
            if doc_source:
                source_doc_counts[doc_source] = source_doc_counts.get(doc_source, 0) + 1
                
                # Mark as frozen if source is missing
                if doc_source in missing_sources:
                    doc.status = DocumentStatus.FROZEN
                    frozen_count += 1
                elif doc.status == DocumentStatus.FROZEN and doc_source in existing_sources:
                    # Unfreeze if source is now available
                    doc.status = DocumentStatus.ACTIVE
        
        # Build source statuses
        source_statuses = []
        for folder in source_folders:
            source_statuses.append(SourceStatus(
                path=folder,
                exists=folder in existing_sources,
                document_count=source_doc_counts.get(folder, 0)
            ))
        
        return VerificationReport(
            total_sources=len(source_folders),
            available_sources=len(existing_sources),
            missing_sources=len(missing_sources),
            frozen_documents=frozen_count,
            source_statuses=source_statuses
        )
    
    def _find_document_source(self, document: Document, 
                            source_folders: List[str]) -> str:
        """
        Find which source folder a document belongs to.
        
        Args:
            document: Document to check
            source_folders: List of source folders
            
        Returns:
            Source folder path or empty string if not found
        """
        doc_path = Path(document.file_path)
        
        # Check each source folder
        for folder in source_folders:
            folder_path = Path(folder)
            try:
                # Check if document is within this source folder
                doc_path.relative_to(folder_path)
                return folder
            except ValueError:
                # Not in this folder
                continue
        
        return ""
    
    def get_frozen_documents(self, documents: List[Document]) -> List[Document]:
        """
        Get all documents marked as frozen.
        
        Args:
            documents: List of documents
            
        Returns:
            List of frozen documents
        """
        return [doc for doc in documents if doc.status == DocumentStatus.FROZEN]
    
    def get_available_documents(self, documents: List[Document]) -> List[Document]:
        """
        Get all documents that are not frozen.
        
        Args:
            documents: List of documents
            
        Returns:
            List of available documents
        """
        return [doc for doc in documents if doc.status != DocumentStatus.FROZEN]
