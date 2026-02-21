"""
Tests for Response Generator.
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any

from apps.issue_3.src.backend.rag.response_generator import (
    Citation,
    FormattedResponse,
    ResponseGenerator
)


# Mock classes for testing
@dataclass
class MockChunk:
    """Mock chunk for testing."""
    content: str
    metadata: Dict[str, Any]


@dataclass
class MockQueryContext:
    """Mock query context for testing."""
    query: str
    retrieved_chunks: List[MockChunk]
    has_results: bool = True


class TestCitation:
    """Tests for Citation class."""
    
    def test_citation_creation(self):
        """Test citation creation."""
        citation = Citation(
            source_id=1,
            file_path="test.md",
            start_line=10,
            end_line=15,
            snippet="Test content"
        )
        
        assert citation.source_id == 1
        assert citation.file_path == "test.md"
        assert citation.start_line == 10
        assert citation.end_line == 15
        assert citation.snippet == "Test content"
    
    def test_citation_to_markdown_single_line(self):
        """Test citation markdown for single line."""
        citation = Citation(
            source_id=1,
            file_path="Rust所有權.md",
            start_line=10,
            end_line=10,
            snippet="所有權是 Rust 的核心特性"
        )
        
        markdown = citation.to_markdown()
        assert "[來源 1]" in markdown
        assert "Rust所有權.md" in markdown
        assert "第10行" in markdown
        assert "所有權是 Rust 的核心特性" in markdown
    
    def test_citation_to_markdown_multiple_lines(self):
        """Test citation markdown for multiple lines."""
        citation = Citation(
            source_id=2,
            file_path="Python教學.md",
            start_line=20,
            end_line=25,
            snippet="Python 是一種高階程式語言"
        )
        
        markdown = citation.to_markdown()
        assert "[來源 2]" in markdown
        assert "第20-25行" in markdown


class TestFormattedResponse:
    """Tests for FormattedResponse class."""
    
    def test_formatted_response_creation(self):
        """Test formatted response creation."""
        citations = [
            Citation(1, "test.md", 1, 1, "snippet 1"),
            Citation(2, "test2.md", 2, 2, "snippet 2")
        ]
        
        response = FormattedResponse(
            content="Answer with sources",
            citations=citations,
            has_local_data=True,
            confidence="高"
        )
        
        assert response.content == "Answer with sources"
        assert len(response.citations) == 2
        assert response.has_local_data is True
        assert response.confidence == "高"
    
    def test_formatted_response_to_markdown_with_citations(self):
        """Test markdown formatting with citations."""
        citations = [
            Citation(1, "test.md", 1, 1, "snippet 1")
        ]
        
        response = FormattedResponse(
            content="這是答案",
            citations=citations,
            has_local_data=True,
            confidence="高"
        )
        
        markdown = response.to_markdown()
        assert "這是答案" in markdown
        assert "*信心度：高*" in markdown
        assert "## 📚 參考來源" in markdown
        assert "[來源 1]" in markdown
    
    def test_formatted_response_to_markdown_no_local_data(self):
        """Test markdown formatting when no local data."""
        response = FormattedResponse(
            content="未找到本機資料",
            citations=[],
            has_local_data=False
        )
        
        markdown = response.to_markdown()
        assert markdown == "未找到本機資料"
        assert "參考來源" not in markdown


class TestResponseGenerator:
    """Tests for ResponseGenerator class."""
    
    def test_initialization(self):
        """Test response generator initialization."""
        generator = ResponseGenerator()
        assert generator is not None
    
    def test_format_response_with_results(self):
        """Test formatting response with local results."""
        generator = ResponseGenerator()
        
        # Create mock context
        chunks = [
            MockChunk(
                content="Rust 的所有權系統確保記憶體安全",
                metadata={
                    'file_path': 'Rust所有權.md',
                    'start_line': 10,
                    'end_line': 12,
                    'score': 0.9
                }
            )
        ]
        context = MockQueryContext(
            query="什麼是 Rust 所有權？",
            retrieved_chunks=chunks
        )
        
        llm_response = "Rust 的所有權系統是一種記憶體管理機制。"
        
        formatted = generator.format_response(
            llm_response,
            context,
            has_local_data=True
        )
        
        assert formatted.has_local_data is True
        assert len(formatted.citations) == 1
        assert formatted.citations[0].file_path == 'Rust所有權.md'
        assert formatted.confidence in ['高', '中', '低']
    
    def test_format_response_multiple_citations(self):
        """Test formatting with multiple citations."""
        generator = ResponseGenerator()
        
        chunks = [
            MockChunk(
                content="內容 1",
                metadata={
                    'file_path': 'doc1.md',
                    'start_line': 1,
                    'end_line': 2,
                    'score': 0.8
                }
            ),
            MockChunk(
                content="內容 2",
                metadata={
                    'file_path': 'doc2.md',
                    'start_line': 5,
                    'end_line': 7,
                    'score': 0.7
                }
            )
        ]
        context = MockQueryContext(
            query="測試查詢",
            retrieved_chunks=chunks
        )
        
        formatted = generator.format_response(
            "測試答案",
            context,
            has_local_data=True
        )
        
        assert len(formatted.citations) == 2
        assert formatted.citations[0].source_id == 1
        assert formatted.citations[1].source_id == 2
    
    def test_format_no_results_response(self):
        """Test formatting when no results found."""
        generator = ResponseGenerator()
        
        formatted = generator.format_no_results_response(
            query="不存在的查詢",
            suggest_external=True
        )
        
        assert formatted.has_local_data is False
        assert len(formatted.citations) == 0
        assert "未找到" in formatted.content
        assert "不存在的查詢" in formatted.content
        assert "外部搜尋" in formatted.content
    
    def test_format_no_results_without_suggestions(self):
        """Test no results without external suggestions."""
        generator = ResponseGenerator()
        
        formatted = generator.format_no_results_response(
            query="測試",
            suggest_external=False
        )
        
        assert "外部搜尋" not in formatted.content
    
    def test_format_summary_response(self):
        """Test formatting document summary."""
        generator = ResponseGenerator()
        
        formatted = generator.format_summary_response(
            summary="這是一份關於 Python 的文件摘要。",
            document_path="Python教學.md",
            total_chunks=10
        )
        
        assert formatted.has_local_data is True
        assert "# 📝 文件摘要" in formatted.content
        assert "Python教學.md" in formatted.content
        assert "10 個" in formatted.content
        assert "這是一份關於 Python 的文件摘要。" in formatted.content
        assert len(formatted.citations) == 1
    
    def test_clean_response_removes_citations(self):
        """Test citation marker removal."""
        generator = ResponseGenerator()
        
        response = "答案在這裡 [來源 1] 和這裡 [Source 2]。"
        cleaned = generator._clean_response(response)
        
        assert "[來源 1]" not in cleaned
        assert "[Source 2]" not in cleaned
        assert "答案在這裡" in cleaned
    
    def test_calculate_confidence_high(self):
        """Test high confidence calculation."""
        generator = ResponseGenerator()
        
        chunks = [
            MockChunk(
                content="test",
                metadata={'score': 0.9}
            ),
            MockChunk(
                content="test2",
                metadata={'score': 0.8}
            )
        ]
        context = MockQueryContext(
            query="test",
            retrieved_chunks=chunks
        )
        
        confidence = generator._calculate_confidence(context)
        assert confidence == "高"
    
    def test_calculate_confidence_medium(self):
        """Test medium confidence calculation."""
        generator = ResponseGenerator()
        
        chunks = [
            MockChunk(
                content="test",
                metadata={'score': 0.6}
            )
        ]
        context = MockQueryContext(
            query="test",
            retrieved_chunks=chunks
        )
        
        confidence = generator._calculate_confidence(context)
        assert confidence == "中"
    
    def test_calculate_confidence_low(self):
        """Test low confidence calculation."""
        generator = ResponseGenerator()
        
        chunks = [
            MockChunk(
                content="test",
                metadata={'score': 0.3}
            )
        ]
        context = MockQueryContext(
            query="test",
            retrieved_chunks=chunks
        )
        
        confidence = generator._calculate_confidence(context)
        assert confidence == "低"
    
    def test_suggest_related_queries(self):
        """Test related query suggestions."""
        generator = ResponseGenerator()
        
        similar_docs = [
            "Rust 基礎教學",
            "Rust 所有權系統",
            "Rust 生命週期"
        ]
        
        suggestions = generator.suggest_related_queries(
            "Rust 教學",
            similar_docs
        )
        
        assert "相關主題建議" in suggestions
        assert "Rust 基礎教學" in suggestions
        assert "Rust 所有權系統" in suggestions
    
    def test_suggest_related_queries_empty(self):
        """Test suggestions with empty list."""
        generator = ResponseGenerator()
        
        suggestions = generator.suggest_related_queries(
            "測試",
            []
        )
        
        assert suggestions == ""
    
    def test_extract_citations_truncates_long_snippets(self):
        """Test that long snippets are truncated."""
        generator = ResponseGenerator()
        
        long_content = "A" * 300
        chunks = [
            MockChunk(
                content=long_content,
                metadata={
                    'file_path': 'test.md',
                    'start_line': 1,
                    'end_line': 1,
                    'score': 0.8
                }
            )
        ]
        context = MockQueryContext(
            query="test",
            retrieved_chunks=chunks
        )
        
        citations = generator._extract_citations("test", context)
        
        assert len(citations) == 1
        assert len(citations[0].snippet) <= 203  # 200 + "..."
        assert citations[0].snippet.endswith("...")
