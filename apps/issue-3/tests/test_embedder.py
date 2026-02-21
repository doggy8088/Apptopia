"""
Tests for embedder module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.backend.core.embedder import Embedder, create_embedder


class TestEmbedder:
    """Test cases for Embedder."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test embedder initialization."""
        embedder = Embedder()
        assert embedder.model_name == "paraphrase-multilingual-MiniLM-L12-v2"
        assert embedder.embedding_dim > 0
    
    def test_initialization_with_cache(self):
        """Test embedder initialization with cache directory."""
        embedder = Embedder(cache_dir=str(self.cache_dir))
        assert embedder.cache_dir == self.cache_dir
        assert embedder.use_cache is True
    
    def test_embed_single_text(self):
        """Test embedding single text."""
        embedder = Embedder(use_cache=False)
        text = "Hello world"
        embedding = embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.embedding_dim
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embed_multiple_texts(self):
        """Test embedding multiple texts."""
        embedder = Embedder(use_cache=False)
        texts = ["Hello world", "Goodbye world", "Test text"]
        embeddings = embedder.embed(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == embedder.embedding_dim for emb in embeddings)
    
    def test_embed_chinese_text(self):
        """Test embedding Chinese text."""
        embedder = Embedder(use_cache=False)
        text = "你好世界"
        embedding = embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.embedding_dim
    
    def test_embed_mixed_text(self):
        """Test embedding mixed English and Chinese text."""
        embedder = Embedder(use_cache=False)
        texts = ["Hello 世界", "測試 test", "混合內容 mixed content"]
        embeddings = embedder.embed(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == embedder.embedding_dim for emb in embeddings)
    
    def test_embed_empty_text(self):
        """Test embedding empty text."""
        embedder = Embedder(use_cache=False)
        text = ""
        embedding = embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.embedding_dim
    
    def test_embed_with_cache(self):
        """Test embedding with caching."""
        embedder = Embedder(cache_dir=str(self.cache_dir), use_cache=True)
        text = "Test caching"
        
        # First call - should generate and cache
        embedding1 = embedder.embed(text)
        
        # Second call - should load from cache
        embedding2 = embedder.embed(text)
        
        assert embedding1 == embedding2
        # Check cache file exists
        cache_key = embedder._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.json"
        assert cache_file.exists()
    
    def test_embed_batch(self):
        """Test batch embedding."""
        embedder = Embedder(use_cache=False)
        texts = [f"Text number {i}" for i in range(10)]
        
        embeddings = embedder.embed_batch(texts, batch_size=3)
        
        assert len(embeddings) == 10
        assert all(len(emb) == embedder.embedding_dim for emb in embeddings)
    
    def test_embed_batch_empty(self):
        """Test batch embedding with empty list."""
        embedder = Embedder(use_cache=False)
        embeddings = embedder.embed_batch([])
        
        assert embeddings == []
    
    def test_get_embedding_dimension(self):
        """Test getting embedding dimension."""
        embedder = Embedder()
        dim = embedder.get_embedding_dimension()
        
        assert isinstance(dim, int)
        assert dim > 0
        assert dim == embedder.embedding_dim
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        embedder = Embedder()
        text = "Test text"
        key1 = embedder._get_cache_key(text)
        key2 = embedder._get_cache_key(text)
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA-256 hex digest length
    
    def test_cache_key_different_texts(self):
        """Test that different texts have different cache keys."""
        embedder = Embedder()
        key1 = embedder._get_cache_key("Text 1")
        key2 = embedder._get_cache_key("Text 2")
        
        assert key1 != key2
    
    def test_create_embedder_factory(self):
        """Test factory function."""
        embedder = create_embedder(cache_dir=str(self.cache_dir))
        
        assert isinstance(embedder, Embedder)
        assert embedder.cache_dir == self.cache_dir
    
    def test_embeddings_consistency(self):
        """Test that same text produces same embedding."""
        embedder = Embedder(use_cache=False)
        text = "Consistency test"
        
        emb1 = embedder.embed(text)
        emb2 = embedder.embed(text)
        
        # Should be identical (or very close for numerical stability)
        assert len(emb1) == len(emb2)
        for v1, v2 in zip(emb1, emb2):
            assert abs(v1 - v2) < 1e-6
    
    def test_long_text_embedding(self):
        """Test embedding long text."""
        embedder = Embedder(use_cache=False)
        # Create a long text
        text = " ".join(["This is sentence number {}." .format(i) for i in range(100)])
        
        embedding = embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == embedder.embedding_dim


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
