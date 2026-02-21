"""
OCR processor for extracting text from images.

Supports Traditional Chinese and English using PaddleOCR.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import hashlib
import json

try:
    from paddleocr import PaddleOCR
    from PIL import Image
    import cv2
    import numpy as np
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    np = None  # Define np as None when not available
    cv2 = None
    logging.warning("PaddleOCR not available. OCR will use mock implementation.")


logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    language: str
    boxes: List[Tuple[Tuple[int, int], str, float]] = None  # (bbox, text, confidence)
    
    def __post_init__(self):
        if self.boxes is None:
            self.boxes = []


class OCRProcessor:
    """
    Process images to extract text using PaddleOCR.
    
    Supports Traditional Chinese (cht) and English (en).
    """
    
    def __init__(
        self,
        languages: List[str] = None,
        confidence_threshold: float = 0.5,
        use_gpu: bool = False,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize OCR processor.
        
        Args:
            languages: List of language codes ['ch', 'en'] (default: ['ch', 'en'])
            confidence_threshold: Minimum confidence for accepting results
            use_gpu: Whether to use GPU acceleration
            cache_dir: Directory for caching OCR results
        """
        self.languages = languages or ['ch', 'en']
        self.confidence_threshold = confidence_threshold
        self.use_gpu = use_gpu
        self.cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize PaddleOCR if available
        if PADDLEOCR_AVAILABLE:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',  # Chinese model also supports English
                use_gpu=use_gpu,
                show_log=False
            )
        else:
            self.ocr = None
            logger.warning("Using mock OCR implementation")
    
    def process_image(
        self,
        image_path: Path,
        preprocess: bool = True
    ) -> OCRResult:
        """
        Process a single image and extract text.
        
        Args:
            image_path: Path to image file
            preprocess: Whether to preprocess image
            
        Returns:
            OCRResult with extracted text
        """
        # Check cache first
        if self.cache_dir:
            cached_result = self._load_from_cache(image_path)
            if cached_result:
                logger.debug(f"Using cached OCR result for {image_path}")
                return cached_result
        
        # Process image
        if self.ocr is None:
            # Mock implementation
            result = self._mock_ocr(image_path)
        else:
            result = self._real_ocr(image_path, preprocess)
        
        # Save to cache
        if self.cache_dir:
            self._save_to_cache(image_path, result)
        
        return result
    
    def process_images_batch(
        self,
        image_paths: List[Path],
        preprocess: bool = True
    ) -> List[OCRResult]:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of image paths
            preprocess: Whether to preprocess images
            
        Returns:
            List of OCRResults
        """
        results = []
        for image_path in image_paths:
            try:
                result = self.process_image(image_path, preprocess)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing image {image_path}: {e}")
                # Return empty result on error
                results.append(OCRResult(
                    text="",
                    confidence=0.0,
                    language="unknown"
                ))
        
        return results
    
    def _real_ocr(self, image_path: Path, preprocess: bool) -> OCRResult:
        """Perform real OCR using PaddleOCR."""
        # Load and optionally preprocess image
        if preprocess:
            image = self._preprocess_image(image_path)
        else:
            image = str(image_path)
        
        # Run OCR
        result = self.ocr.ocr(image, cls=True)
        
        # Parse results
        if not result or not result[0]:
            return OCRResult(
                text="",
                confidence=0.0,
                language="unknown"
            )
        
        # Extract text and confidence
        texts = []
        confidences = []
        boxes = []
        
        for line in result[0]:
            bbox, (text, confidence) = line
            if confidence >= self.confidence_threshold:
                texts.append(text)
                confidences.append(confidence)
                boxes.append((tuple(map(tuple, bbox)), text, confidence))
        
        # Combine text
        full_text = '\n'.join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            language='ch',  # PaddleOCR Chinese model
            boxes=boxes
        )
    
    def _mock_ocr(self, image_path: Path) -> OCRResult:
        """Mock OCR for testing without PaddleOCR."""
        # Generate deterministic mock text based on filename
        name = image_path.stem
        mock_text = f"Mock OCR result for {name}"
        
        return OCRResult(
            text=mock_text,
            confidence=0.95,
            language='mock'
        )
    
    def _preprocess_image(self, image_path: Path):
        """
        Preprocess image for better OCR results.
        
        Steps:
        1. Read image
        2. Convert to grayscale
        3. Resize if too large
        4. Increase contrast
        5. Denoise
        """
        # Read image
        img = cv2.imread(str(image_path))
        
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Resize if too large (max 2000px on longest side)
        height, width = gray.shape
        max_dimension = max(height, width)
        if max_dimension > 2000:
            scale = 2000 / max_dimension
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height))
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(contrast, None, 10, 7, 21)
        
        return denoised
    
    def _get_cache_key(self, image_path: Path) -> str:
        """Generate cache key for image."""
        # Use file path and modification time
        stat = image_path.stat()
        key_str = f"{image_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _load_from_cache(self, image_path: Path) -> Optional[OCRResult]:
        """Load OCR result from cache."""
        cache_key = self._get_cache_key(image_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return OCRResult(
                text=data['text'],
                confidence=data['confidence'],
                language=data['language'],
                boxes=data.get('boxes', [])
            )
        except Exception as e:
            logger.warning(f"Error loading cache for {image_path}: {e}")
            return None
    
    def _save_to_cache(self, image_path: Path, result: OCRResult):
        """Save OCR result to cache."""
        cache_key = self._get_cache_key(image_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            data = {
                'text': result.text,
                'confidence': result.confidence,
                'language': result.language,
                'boxes': result.boxes
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"Error saving cache for {image_path}: {e}")
    
    def clear_cache(self):
        """Clear all cached OCR results."""
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("OCR cache cleared")


def create_ocr_processor(
    languages: List[str] = None,
    confidence_threshold: float = 0.5,
    use_gpu: bool = False,
    cache_dir: Optional[Path] = None
) -> OCRProcessor:
    """
    Factory function to create OCRProcessor.
    
    Args:
        languages: List of language codes
        confidence_threshold: Minimum confidence threshold
        use_gpu: Whether to use GPU
        cache_dir: Cache directory path
        
    Returns:
        Configured OCRProcessor instance
    """
    return OCRProcessor(
        languages=languages,
        confidence_threshold=confidence_threshold,
        use_gpu=use_gpu,
        cache_dir=cache_dir
    )
