"""
Vector store module for document indexing and retrieval using Chroma.

This module provides a wrapper around ChromaDB for storing and retrieving
document embeddings with metadata support.
"""

from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


class VectorStore:
    """
    Vector store for document embeddings using ChromaDB.
    
    Features:
    - Persistent storage
    - Metadata filtering
    - Batch operations
    - Incremental updates
    - Collection management
    """
    
    def __init__(
        self,
        persist_directory: str,
        collection_name: str = "documents",
        embedding_dim: int = 384
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory for persisting the database
            collection_name: Name of the collection
            embedding_dim: Dimension of embedding vectors
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        if HAS_CHROMADB:
            self.client = chromadb.PersistentClient(
                path=str(self.persist_directory)
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self.client = None
            self.collection = None
            self._mock_store = {}  # Mock storage for testing
    
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            ids: List of document IDs
            embeddings: List of embedding vectors
            documents: List of document texts
            metadatas: Optional list of metadata dicts
        """
        if not ids or not embeddings or not documents:
            return
        
        if len(ids) != len(embeddings) or len(ids) != len(documents):
            raise ValueError("ids, embeddings, and documents must have same length")
        
        if metadatas and len(metadatas) != len(ids):
            raise ValueError("metadatas must have same length as ids")
        
        if self.collection is not None:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        else:
            # Mock storage
            for i, doc_id in enumerate(ids):
                self._mock_store[doc_id] = {
                    'embedding': embeddings[i],
                    'document': documents[i],
                    'metadata': metadatas[i] if metadatas else {}
                }
    
    def update(
        self,
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Update documents in the vector store.
        
        Args:
            ids: List of document IDs to update
            embeddings: Optional list of new embedding vectors
            documents: Optional list of new document texts
            metadatas: Optional list of new metadata dicts
        """
        if not ids:
            return
        
        if self.collection is not None:
            self.collection.update(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        else:
            # Mock update
            for i, doc_id in enumerate(ids):
                if doc_id in self._mock_store:
                    if embeddings:
                        self._mock_store[doc_id]['embedding'] = embeddings[i]
                    if documents:
                        self._mock_store[doc_id]['document'] = documents[i]
                    if metadatas:
                        self._mock_store[doc_id]['metadata'] = metadatas[i]
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete documents from the vector store.
        
        Args:
            ids: List of document IDs to delete
        """
        if not ids:
            return
        
        if self.collection is not None:
            self.collection.delete(ids=ids)
        else:
            # Mock delete
            for doc_id in ids:
                self._mock_store.pop(doc_id, None)
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_embeddings: List of query embedding vectors
            n_results: Number of results to return per query
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results with ids, distances, documents, and metadatas
        """
        if not query_embeddings:
            return {'ids': [], 'distances': [], 'documents': [], 'metadatas': []}
        
        if self.collection is not None:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        else:
            # Mock query - simple distance calculation
            results = {
                'ids': [],
                'distances': [],
                'documents': [],
                'metadatas': []
            }
            
            for query_emb in query_embeddings:
                # Calculate cosine similarity with all stored documents
                similarities = []
                for doc_id, doc_data in self._mock_store.items():
                    # Simple dot product (assuming normalized vectors)
                    similarity = sum(a * b for a, b in zip(query_emb, doc_data['embedding']))
                    distance = 1 - similarity  # Convert to distance
                    similarities.append((doc_id, distance, doc_data))
                
                # Sort by distance and take top n_results
                similarities.sort(key=lambda x: x[1])
                top_results = similarities[:n_results]
                
                results['ids'].append([r[0] for r in top_results])
                results['distances'].append([r[1] for r in top_results])
                results['documents'].append([r[2]['document'] for r in top_results])
                results['metadatas'].append([r[2]['metadata'] for r in top_results])
            
            return results
    
    def get(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get documents from the vector store.
        
        Args:
            ids: Optional list of document IDs
            where: Optional metadata filter
            limit: Optional limit on number of results
            
        Returns:
            Documents with ids, embeddings, documents, and metadatas
        """
        if self.collection is not None:
            results = self.collection.get(
                ids=ids,
                where=where,
                limit=limit
            )
            return results
        else:
            # Mock get
            results = {
                'ids': [],
                'embeddings': [],
                'documents': [],
                'metadatas': []
            }
            
            items = list(self._mock_store.items())
            if ids:
                items = [(k, v) for k, v in items if k in ids]
            if limit:
                items = items[:limit]
            
            for doc_id, doc_data in items:
                results['ids'].append(doc_id)
                results['embeddings'].append(doc_data['embedding'])
                results['documents'].append(doc_data['document'])
                results['metadatas'].append(doc_data['metadata'])
            
            return results
    
    def count(self) -> int:
        """
        Get the number of documents in the collection.
        
        Returns:
            Number of documents
        """
        if self.collection is not None:
            return self.collection.count()
        else:
            return len(self._mock_store)
    
    def reset(self) -> None:
        """Reset the collection (delete all documents)."""
        if self.collection is not None:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        else:
            self._mock_store.clear()
    
    def add_batch(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents in batches.
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts
            batch_size: Size of each batch
            
        Returns:
            List of generated document IDs
        """
        if not documents or not embeddings:
            return []
        
        # Generate IDs
        ids = [str(uuid.uuid4()) for _ in documents]
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_documents = documents[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size] if metadatas else None
            
            self.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_documents,
                metadatas=batch_metadatas
            )
        
        return ids


def create_vector_store(
    persist_directory: str,
    collection_name: str = "documents"
) -> VectorStore:
    """
    Factory function to create a VectorStore instance.
    
    Args:
        persist_directory: Directory for persisting the database
        collection_name: Name of the collection
        
    Returns:
        VectorStore instance
    """
    return VectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
