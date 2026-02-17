"""
Document Processor - Orchestrates the complete document processing pipeline.

This module coordinates all components (scanner, parser, chunker, embedder, 
vector store, OCR) to process documents from folders into a searchable knowledge base.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import time

from ..models.document import Document, DocumentMetadata, DocumentChunk, Relationship, KnowledgeBase, DocumentStatus
from ..utils.file_scanner import FileScanner, FileChange
from ..parsers.obsidian_parser import ObsidianParser
from .chunker import DocumentChunker
from .embedder import Embedder
from .ocr_processor import OCRProcessor
from ..indexer.vector_store import VectorStore


logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics from document processing."""
    total_files: int = 0
    new_files: int = 0
    modified_files: int = 0
    deleted_files: int = 0
    unchanged_files: int = 0
    errors: int = 0
    processing_time: float = 0.0
    relationships_built: int = 0
    error_details: List[Dict[str, str]] = field(default_factory=list)


class DocumentProcessor:
    """
    Main document processing orchestrator.
    
    Coordinates all components to process folders of documents into
    a searchable knowledge base with relationships.
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedder: Optional[Embedder] = None,
        chunker: Optional[DocumentChunker] = None,
        parser: Optional[ObsidianParser] = None,
        ocr_processor: Optional[OCRProcessor] = None,
        file_scanner: Optional[FileScanner] = None,
        max_workers: int = 4
    ):
        """
        Initialize the document processor.
        
        Args:
            vector_store: Vector database for storing embeddings
            embedder: Embedding generator
            chunker: Text chunker
            parser: Document parser
            ocr_processor: OCR processor for images
            file_scanner: File scanner for detecting changes
            max_workers: Number of parallel processing threads
        """
        self.vector_store = vector_store or VectorStore(
            persist_directory="./.chroma_db",
            collection_name="documents"
        )
        self.embedder = embedder or Embedder()
        self.chunker = chunker or DocumentChunker()
        self.parser = parser or ObsidianParser()
        self.ocr_processor = ocr_processor or OCRProcessor()
        self.file_scanner = file_scanner or FileScanner()
        self.max_workers = max_workers
        
        # Track processed documents
        self.documents: Dict[str, Document] = {}
    
    def process_folders(
        self,
        folders: List[str],
        force: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> ProcessingStats:
        """
        Process one or more folders of documents.
        
        Args:
            folders: List of folder paths to process
            force: If True, reprocess all files regardless of changes
            progress_callback: Optional callback(current, total, path) for progress
        
        Returns:
            ProcessingStats with processing results
        """
        start_time = time.time()
        stats = ProcessingStats()
        
        # Scan all folders for files
        all_changes: List[FileChange] = []
        for folder in folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                logger.warning(f"Folder does not exist: {folder}")
                continue
            
            # Get file changes
            if force:
                # Treat all files as new
                files = self.file_scanner.scan_directory(folder, recursive=True)
                changes = [
                    FileChange(
                        path=str(f.path),
                        change_type="new",
                        size=f.size,
                        mtime=f.mtime,
                        hash=f.hash
                    )
                    for f in files
                ]
            else:
                # Detect actual changes
                changes = self.file_scanner.detect_changes(
                    folder,
                    recursive=True
                )
            
            all_changes.extend(changes)
        
        # Filter to only .md files for now
        md_changes = [c for c in all_changes if c.path.endswith('.md')]
        
        stats.total_files = len(md_changes)
        stats.new_files = len([c for c in md_changes if c.change_type == 'new'])
        stats.modified_files = len([c for c in md_changes if c.change_type == 'modified'])
        stats.deleted_files = len([c for c in md_changes if c.change_type == 'deleted'])
        stats.unchanged_files = len([c for c in md_changes if c.change_type == 'unchanged'])
        
        # Process deletions first
        for change in md_changes:
            if change.change_type == 'deleted':
                self._delete_document(change.path)
        
        # Process new and modified files
        to_process = [
            c for c in md_changes 
            if c.change_type in ('new', 'modified')
        ]
        
        if not to_process:
            logger.info("No files to process")
            stats.processing_time = time.time() - start_time
            return stats
        
        # Process documents in parallel
        logger.info(f"Processing {len(to_process)} documents with {self.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_change = {
                executor.submit(self._process_document, change.path): change
                for change in to_process
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_change):
                change = future_to_change[future]
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, len(to_process), change.path)
                
                try:
                    doc = future.result()
                    if doc:
                        self.documents[doc.doc_id] = doc
                        logger.info(f"Successfully processed: {doc.doc_id}")
                except Exception as e:
                    stats.errors += 1
                    error_detail = {
                        'path': change.path,
                        'error': str(e)
                    }
                    stats.error_details.append(error_detail)
                    logger.error(f"Error processing {change.path}: {e}")
        
        # Build relationships between documents
        logger.info("Building document relationships...")
        try:
            self._build_relationships()
            stats.relationships_built = sum(
                len(doc.relationships) for doc in self.documents.values()
            )
        except Exception as e:
            logger.error(f"Error building relationships: {e}")
        
        stats.processing_time = time.time() - start_time
        logger.info(
            f"Processing complete: {stats.new_files} new, "
            f"{stats.modified_files} modified, {stats.deleted_files} deleted, "
            f"{stats.errors} errors in {stats.processing_time:.2f}s"
        )
        
        return stats
    
    def _process_document(self, file_path: str) -> Optional[Document]:
        """
        Process a single document through the full pipeline.
        
        Args:
            file_path: Path to the document
        
        Returns:
            Processed Document or None if error
        """
        try:
            path = Path(file_path)
            
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse document
            parsed_doc = self.parser.parse_content(content, title=path.name)
            metadata_dict = parsed_doc.frontmatter
            plain_text = parsed_doc.plain_text
            extracted_data = {
                'wikilinks': parsed_doc.wikilinks,
                'tags': parsed_doc.tags,
                'images': parsed_doc.images,
                'headings': parsed_doc.headings
            }
            
            # Create DocumentMetadata
            metadata = DocumentMetadata(
                tags=parsed_doc.tags or [],
                aliases=parsed_doc.aliases or [],
                title=parsed_doc.title or path.stem,
                headings=parsed_doc.headings or [],
                word_count=len(plain_text.split()) if plain_text else 0
            )
            
            # Process images with OCR if present
            image_texts = []
            if extracted_data.get('images'):
                for image_ref in extracted_data['images']:
                    # Try to resolve image path relative to document
                    image_path = path.parent / image_ref
                    if image_path.exists():
                        try:
                            ocr_text = self.ocr_processor.process_image(str(image_path))
                            if ocr_text:
                                image_texts.append(ocr_text)
                        except Exception as e:
                            logger.debug(f"OCR failed for {image_path}: {e}")
            
            # Combine text (document + OCR)
            combined_text = plain_text
            if image_texts:
                combined_text += "\n\n" + "\n\n".join(image_texts)
            
            # Chunk text
            chunk_objects = self.chunker.chunk_text(combined_text)
            chunks_text = [chunk.text for chunk in chunk_objects]
            
            # Generate embeddings
            embeddings = self.embedder.embed_batch(chunks_text)
            
            # Create chunks
            chunks = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks_text, embeddings)):
                chunk = DocumentChunk(
                    chunk_id=f"{path.stem}_{i}",
                    document_id=str(path),
                    content=chunk_text,
                    start_line=i * 10,  # Approximate
                    end_line=(i + 1) * 10,  # Approximate
                    embedding=embedding,
                    metadata={
                        'chunk_index': i,
                        'source_file': str(path),
                        'total_chunks': len(chunks_text)
                    }
                )
                chunks.append(chunk)
            
            # Store chunks in vector database
            if chunks:
                self.vector_store.add(
                    ids=[c.chunk_id for c in chunks],
                    embeddings=[c.embedding for c in chunks],
                    documents=[c.content for c in chunks],
                    metadatas=[c.metadata for c in chunks]
                )
            
            # Create document
            doc = Document(
                doc_id=str(path),
                file_path=path,
                relative_path=path.relative_to(path.parent.parent) if path.parent.parent else path,
                source_folder=str(path.parent),
                raw_content=content,
                parsed_content=parsed_doc.parsed_content,
                metadata=metadata,
                chunks=chunks,
                status=DocumentStatus.ACTIVE
            )
            
            return doc
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    def _delete_document(self, file_path: str):
        """
        Remove a deleted document from the system.
        
        Args:
            file_path: Path to the deleted document
        """
        try:
            if file_path in self.documents:
                doc = self.documents[file_path]
                
                # Remove from vector store
                chunk_ids = [c.chunk_id for c in doc.chunks]
                if chunk_ids:
                    self.vector_store.delete(chunk_ids)
                
                # Remove from memory
                del self.documents[file_path]
                
                logger.info(f"Deleted document: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting document {file_path}: {e}")
    
    def _build_relationships(self):
        """
        Build relationships between documents based on:
        1. Explicit wikilinks
        2. Vector similarity
        3. Keyword overlap (future)
        """
        for doc_path, doc in self.documents.items():
            relationships = []
            
            # 1. Extract wikilinks from content
            parsed_doc = self.parser.parse_content(doc.raw_content, title=Path(doc_path).stem)
            wikilinks = parsed_doc.wikilinks or []
            
            # Find matching documents
            for link in wikilinks:
                # Simple matching by filename
                link_name = link.split('|')[0].split('#')[0].strip()
                for other_path, other_doc in self.documents.items():
                    if other_path == doc_path:
                        continue
                    
                    other_name = Path(other_path).stem
                    if link_name == other_name:
                        rel = Relationship(
                            target_doc=other_path,
                            type='wikilink',
                            score=1.0,  # Manual link = 100% confidence
                            metadata={'link_text': link}
                        )
                        relationships.append(rel)
            
            # 2. Find similar documents by vector similarity
            if doc.embedding:
                try:
                    # Query for similar documents
                    results = self.vector_store.query(
                        query_embedding=doc.embedding,
                        top_k=6  # Get 6 to filter out self
                    )
                    
                    for result in results:
                        # Skip self-references
                        source_file = result.get('metadata', {}).get('source_file')
                        if source_file and source_file != doc_path:
                            # Check if not already linked
                            if not any(r.target_doc == source_file for r in relationships):
                                rel = Relationship(
                                    target_doc=source_file,
                                    type='similarity',
                                    score=result.get('score', 0.0),
                                    metadata={'distance': result.get('distance', 0.0)}
                                )
                                relationships.append(rel)
                except Exception as e:
                    logger.debug(f"Error finding similar docs for {doc_path}: {e}")
            
            # Sort by score and keep top 5
            relationships.sort(key=lambda r: r.score, reverse=True)
            doc.relationships = relationships[:5]
    
    def get_knowledge_base(self) -> KnowledgeBase:
        """
        Get the complete knowledge base with all documents.
        
        Returns:
            KnowledgeBase object
        """
        from datetime import datetime
        return KnowledgeBase(
            kb_id="default",
            name="AI知識++",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source_folders=[],
            total_documents=len(self.documents),
            total_chunks=sum(len(doc.chunks) for doc in self.documents.values()),
            total_relationships=sum(len(doc.relationships) for doc in self.documents.values())
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current knowledge base statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            'total_documents': len(self.documents),
            'total_chunks': sum(len(doc.chunks) for doc in self.documents.values()),
            'total_relationships': sum(len(doc.relationships) for doc in self.documents.values()),
            'documents': {
                path: {
                    'chunks': len(doc.chunks),
                    'relationships': len(doc.relationships),
                    'tags': doc.metadata.tags if doc.metadata else []
                }
                for path, doc in self.documents.items()
            }
        }
