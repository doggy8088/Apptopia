"""
Embedding generation module for document vectorization.

This module provides embedding generation using sentence-transformers
with support for Chinese and multi-language content.
"""

from typing import List, Union, Optional
import hashlib
import json
from pathlib import Path


try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class Embedder:
    """
    Document embedding generator using sentence-transformers.
    
    Features:
    - Multi-language support (including Chinese)
    - Batch processing
    - Caching mechanism
    - Fallback to mock embeddings for testing
    """
    
    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir: Optional[str] = None,
        use_cache: bool = True
    ):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of the sentence-transformer model
            cache_dir: Directory for caching embeddings
            use_cache: Whether to use caching
        """
        self.model_name = model_name
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        if HAS_SENTENCE_TRANSFORMERS:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
        else:
            self.model = None
            self.embedding_dim = 384  # Default dimension for paraphrase-multilingual-MiniLM
    
    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.
        
        Args:
            text: Input text
            
        Returns:
            Cache key (SHA-256 hash)
        """
        content = f"{self.model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """
        Load embedding from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Embedding vector or None if not found
        """
        if not self.use_cache or not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return data['embedding']
            except Exception:
                return None
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: List[float]):
        """
        Save embedding to cache.
        
        Args:
            cache_key: Cache key
            embedding: Embedding vector
        """
        if not self.use_cache or not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({'embedding': embedding}, f)
        except Exception:
            pass  # Silently fail on cache write errors
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """
        Generate a mock embedding for testing (when model not available).
        
        Args:
            text: Input text
            
        Returns:
            Mock embedding vector
        """
        # Simple hash-based mock embedding
        hash_val = hashlib.sha256(text.encode()).digest()
        # Convert to floats in range [-1, 1]
        embedding = [
            (int.from_bytes(hash_val[i:i+2], 'big') / 32768.0) - 1.0
            for i in range(0, min(len(hash_val), self.embedding_dim * 2), 2)
        ]
        # Pad or trim to correct dimension
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)
        return embedding[:self.embedding_dim]
    
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text(s).
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Single embedding or list of embeddings
        """
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        embeddings = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache first
        for i, t in enumerate(texts):
            if self.use_cache:
                cache_key = self._get_cache_key(t)
                cached = self._load_from_cache(cache_key)
                if cached:
                    embeddings.append((i, cached))
                    continue
            
            texts_to_embed.append(t)
            indices_to_embed.append(i)
        
        # Generate embeddings for non-cached texts
        if texts_to_embed:
            if self.model is not None:
                # Use real model
                new_embeddings = self.model.encode(
                    texts_to_embed,
                    convert_to_numpy=True,
                    show_progress_bar=False
                ).tolist()
            else:
                # Use mock embeddings
                new_embeddings = [
                    self._generate_mock_embedding(t)
                    for t in texts_to_embed
                ]
            
            # Add to results and cache
            for idx, emb in zip(indices_to_embed, new_embeddings):
                embeddings.append((idx, emb))
                if self.use_cache:
                    cache_key = self._get_cache_key(texts_to_embed[indices_to_embed.index(idx)])
                    self._save_to_cache(cache_key, emb)
        
        # Sort by original index
        embeddings.sort(key=lambda x: x[0])
        result = [emb for _, emb in embeddings]
        
        return result[0] if is_single else result
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Process in batches
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.embed(batch)
            all_embeddings.extend(embeddings if isinstance(embeddings[0], list) else [embeddings])
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim


def create_embedder(
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    cache_dir: Optional[str] = None
) -> Embedder:
    """
    Factory function to create an Embedder instance.
    
    Args:
        model_name: Name of the sentence-transformer model
        cache_dir: Directory for caching embeddings
        
    Returns:
        Embedder instance
    """
    return Embedder(model_name=model_name, cache_dir=cache_dir)
