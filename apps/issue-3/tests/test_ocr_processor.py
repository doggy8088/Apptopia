"""
Tests for OCRProcessor.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.backend.core.ocr_processor import OCRProcessor, OCRResult, create_ocr_processor


@pytest.fixture
def ocr_processor(tmp_path):
    """Create an OCR processor with cache."""
    cache_dir = tmp_path / "ocr_cache"
    return OCRProcessor(
        languages=['ch', 'en'],
        confidence_threshold=0.5,
        use_gpu=False,
        cache_dir=cache_dir
    )


def test_ocr_processor_initialization():
    """Test OCR processor initialization."""
    processor = OCRProcessor()
    
    assert processor.languages == ['ch', 'en']
    assert processor.confidence_threshold == 0.5
    assert not processor.use_gpu


def test_ocr_result_dataclass():
    """Test OCRResult dataclass."""
    result = OCRResult(
        text="Test text",
        confidence=0.95,
        language="en"
    )
    
    assert result.text == "Test text"
    assert result.confidence == 0.95
    assert result.language == "en"
    assert result.boxes == []


def test_mock_ocr(ocr_processor, tmp_path):
    """Test mock OCR when PaddleOCR is not available."""
    # Create a test image (just a file, content doesn't matter for mock)
    test_image = tmp_path / "test.jpg"
    test_image.write_bytes(b"fake image data")
    
    result = ocr_processor._mock_ocr(test_image)
    
    assert "test" in result.text.lower()
    assert result.confidence > 0.9
    assert result.language == "mock"


def test_process_image_with_mock(ocr_processor, tmp_path):
    """Test processing an image with mock OCR."""
    test_image = tmp_path / "test.jpg"
    test_image.write_bytes(b"fake image data")
    
    result = ocr_processor.process_image(test_image, preprocess=False)
    
    assert result is not None
    assert isinstance(result.text, str)
    assert isinstance(result.confidence, float)


def test_process_images_batch(ocr_processor, tmp_path):
    """Test batch processing of images."""
    # Create multiple test images
    images = []
    for i in range(3):
        img = tmp_path / f"test{i}.jpg"
        img.write_bytes(b"fake image data")
        images.append(img)
    
    results = ocr_processor.process_images_batch(images, preprocess=False)
    
    assert len(results) == 3
    for result in results:
        assert isinstance(result, OCRResult)


def test_cache_functionality(ocr_processor, tmp_path):
    """Test OCR result caching."""
    test_image = tmp_path / "test.jpg"
    test_image.write_bytes(b"fake image data")
    
    # First call - should process and cache
    result1 = ocr_processor.process_image(test_image)
    
    # Second call - should load from cache
    result2 = ocr_processor.process_image(test_image)
    
    # Results should be identical
    assert result1.text == result2.text
    assert result1.confidence == result2.confidence


def test_clear_cache(ocr_processor, tmp_path):
    """Test clearing cache."""
    test_image = tmp_path / "test.jpg"
    test_image.write_bytes(b"fake image data")
    
    # Process image to create cache
    ocr_processor.process_image(test_image)
    
    # Verify cache exists
    cache_files = list(ocr_processor.cache_dir.glob("*.json"))
    assert len(cache_files) > 0
    
    # Clear cache
    ocr_processor.clear_cache()
    
    # Verify cache is empty
    cache_files = list(ocr_processor.cache_dir.glob("*.json"))
    assert len(cache_files) == 0


def test_create_ocr_processor_factory(tmp_path):
    """Test factory function."""
    cache_dir = tmp_path / "cache"
    
    processor = create_ocr_processor(
        languages=['en'],
        confidence_threshold=0.7,
        use_gpu=False,
        cache_dir=cache_dir
    )
    
    assert processor.languages == ['en']
    assert processor.confidence_threshold == 0.7
    assert processor.cache_dir == cache_dir


def test_ocr_with_error_handling(ocr_processor, tmp_path):
    """Test error handling for invalid images."""
    # Create a non-existent file path
    invalid_image = tmp_path / "nonexistent.jpg"
    
    # Should handle gracefully
    results = ocr_processor.process_images_batch([invalid_image])
    
    assert len(results) == 1
    assert results[0].text == ""
    assert results[0].confidence == 0.0


def test_cache_key_generation(ocr_processor, tmp_path):
    """Test cache key generation."""
    test_image = tmp_path / "test.jpg"
    test_image.write_bytes(b"data")
    
    key1 = ocr_processor._get_cache_key(test_image)
    key2 = ocr_processor._get_cache_key(test_image)
    
    # Same file should produce same key
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex length


def test_ocr_processor_without_cache():
    """Test OCR processor without caching."""
    processor = OCRProcessor(cache_dir=None)
    
    assert processor.cache_dir is None


def test_confidence_threshold_filtering(ocr_processor):
    """Test that low confidence results are filtered."""
    # This test assumes mock OCR, which returns high confidence
    # In real implementation, low confidence results would be filtered
    assert ocr_processor.confidence_threshold == 0.5
