"""
Tests for RAG Engine - Complete end-to-end RAG pipeline.
"""

import pytest
from dataclasses import dataclass
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock

from apps.issue_3.src.backend.rag.engine import (
    RAGConfig,
    RAGResult,
    RAGStats,
    RAGEngine
)
from apps.issue_3.src.backend.rag.query_processor import QueryContext, RetrievalResult
from apps.issue_3.src.backend.rag.llm_client import LLMMessage, LLMResponse, MockLLMClient
from apps.issue_3.src.backend.rag.conversation import Conversation, ConversationManager
from apps.issue_3.src.backend.rag.response_generator import ResponseGenerator, FormattedResponse


# Mock classes
@dataclass
class MockChunk:
    """Mock chunk for testing."""
    content: str
    metadata: Dict[str, Any]


class TestRAGConfig:
    """Tests for RAGConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = RAGConfig()
        
        assert config.max_results == 5
        assert config.min_score == 0.3
        assert config.max_context_tokens == 2000
        assert config.max_llm_tokens == 1000
        assert config.temperature == 0.7
        assert config.max_conversation_tokens == 4000
        assert config.suggest_external is True
        assert config.include_confidence is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RAGConfig(
            max_results=10,
            min_score=0.5,
            temperature=0.9
        )
        
        assert config.max_results == 10
        assert config.min_score == 0.5
        assert config.temperature == 0.9


class TestRAGResult:
    """Tests for RAGResult."""
    
    def test_result_creation(self):
        """Test RAG result creation."""
        response = FormattedResponse(
            content="Test response",
            citations=[],
            has_local_data=True
        )
        
        result = RAGResult(
            query="test query",
            response=response,
            conversation_id="test-123",
            turn_count=1,
            processing_time=0.5,
            has_local_data=True,
            retrieved_chunks_count=3,
            llm_tokens_used=100
        )
        
        assert result.query == "test query"
        assert result.conversation_id == "test-123"
        assert result.turn_count == 1
        assert result.processing_time == 0.5
        assert result.has_local_data is True
        assert result.retrieved_chunks_count == 3
        assert result.llm_tokens_used == 100
        assert result.error is None


class TestRAGStats:
    """Tests for RAGStats."""
    
    def test_initial_stats(self):
        """Test initial statistics."""
        stats = RAGStats()
        
        assert stats.total_queries == 0
        assert stats.successful_queries == 0
        assert stats.failed_queries == 0
        assert stats.total_processing_time == 0.0
        assert stats.average_processing_time == 0.0
    
    def test_update_successful(self):
        """Test updating stats with successful result."""
        stats = RAGStats()
        
        result = RAGResult(
            query="test",
            response=FormattedResponse("answer", [], True),
            conversation_id="test",
            turn_count=1,
            processing_time=1.0,
            has_local_data=True,
            retrieved_chunks_count=5,
            llm_tokens_used=100
        )
        
        stats.update(result)
        
        assert stats.total_queries == 1
        assert stats.successful_queries == 1
        assert stats.failed_queries == 0
        assert stats.total_processing_time == 1.0
        assert stats.average_processing_time == 1.0
        assert stats.total_chunks_retrieved == 5
        assert stats.total_tokens_used == 100
    
    def test_update_failed(self):
        """Test updating stats with failed result."""
        stats = RAGStats()
        
        result = RAGResult(
            query="test",
            response=FormattedResponse("error", [], False),
            conversation_id="test",
            turn_count=0,
            processing_time=0.5,
            has_local_data=False,
            error="Test error"
        )
        
        stats.update(result)
        
        assert stats.total_queries == 1
        assert stats.successful_queries == 0
        assert stats.failed_queries == 1
    
    def test_average_processing_time(self):
        """Test average processing time calculation."""
        stats = RAGStats()
        
        # Add multiple results
        for processing_time in [1.0, 2.0, 3.0]:
            result = RAGResult(
                query="test",
                response=FormattedResponse("answer", [], True),
                conversation_id="test",
                turn_count=1,
                processing_time=processing_time,
                has_local_data=True
            )
            stats.update(result)
        
        assert stats.total_queries == 3
        assert stats.total_processing_time == 6.0
        assert stats.average_processing_time == 2.0


class TestRAGEngine:
    """Tests for RAGEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock components
        self.query_processor = Mock()
        self.llm_client = MockLLMClient(
            responses=["這是 AI 生成的答案。"]
        )
        self.conversation_manager = ConversationManager()
        self.response_generator = ResponseGenerator()
        
        # Create engine
        self.engine = RAGEngine(
            query_processor=self.query_processor,
            llm_client=self.llm_client,
            conversation_manager=self.conversation_manager,
            response_generator=self.response_generator
        )
    
    def test_initialization(self):
        """Test RAG engine initialization."""
        assert self.engine.query_processor is not None
        assert self.engine.llm_client is not None
        assert self.engine.conversation_manager is not None
        assert self.engine.response_generator is not None
        assert isinstance(self.engine.config, RAGConfig)
        assert isinstance(self.engine.stats, RAGStats)
    
    def test_query_with_results(self):
        """Test query with successful retrieval."""
        # Mock query processor to return results
        mock_chunks = [
            MockChunk(
                content="Rust 的所有權系統",
                metadata={
                    'file_path': 'rust.md',
                    'start_line': 1,
                    'end_line': 2,
                    'score': 0.9
                }
            )
        ]
        
        mock_context = QueryContext(
            query="什麼是 Rust？",
            retrieved_chunks=mock_chunks,
            context_text="Rust 的所有權系統",
            has_results=True
        )
        
        self.query_processor.process_query.return_value = mock_context
        
        # Execute query
        result = self.engine.query("什麼是 Rust？")
        
        # Verify result
        assert result.query == "什麼是 Rust？"
        assert result.has_local_data is True
        assert result.retrieved_chunks_count == 1
        assert result.error is None
        assert result.turn_count > 0
        
        # Verify stats updated
        assert self.engine.stats.total_queries == 1
        assert self.engine.stats.successful_queries == 1
    
    def test_query_no_results(self):
        """Test query when no results found."""
        # Mock query processor to return no results
        mock_context = QueryContext(
            query="不存在的查詢",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        
        self.query_processor.process_query.return_value = mock_context
        
        # Execute query
        result = self.engine.query("不存在的查詢")
        
        # Verify result
        assert result.query == "不存在的查詢"
        assert result.has_local_data is False
        assert result.retrieved_chunks_count == 0
        assert "未找到" in result.response.content
    
    def test_query_with_conversation_id(self):
        """Test query with existing conversation."""
        # First query creates conversation
        mock_context = QueryContext(
            query="第一個問題",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        self.query_processor.process_query.return_value = mock_context
        
        result1 = self.engine.query("第一個問題", conversation_id="test-conv")
        
        # Second query uses same conversation
        result2 = self.engine.query("第二個問題", conversation_id="test-conv")
        
        assert result1.conversation_id == "test-conv"
        assert result2.conversation_id == "test-conv"
        assert result2.turn_count > result1.turn_count
    
    def test_query_multi_turn(self):
        """Test multi-turn conversation."""
        mock_chunks = [
            MockChunk(
                content="測試內容",
                metadata={
                    'file_path': 'test.md',
                    'start_line': 1,
                    'end_line': 1,
                    'score': 0.8
                }
            )
        ]
        
        mock_context = QueryContext(
            query="測試",
            retrieved_chunks=mock_chunks,
            context_text="測試內容",
            has_results=True
        )
        self.query_processor.process_query.return_value = mock_context
        
        # Multiple queries in same conversation
        conv_id = "multi-turn-test"
        
        result1 = self.engine.query("問題 1", conversation_id=conv_id)
        result2 = self.engine.query("問題 2", conversation_id=conv_id)
        result3 = self.engine.query("問題 3", conversation_id=conv_id)
        
        assert result1.turn_count == 1
        assert result2.turn_count == 2
        assert result3.turn_count == 3
    
    def test_query_error_handling(self):
        """Test error handling in query."""
        # Mock query processor to raise error
        self.query_processor.process_query.side_effect = Exception("Test error")
        
        result = self.engine.query("測試錯誤")
        
        assert result.error is not None
        assert "錯誤" in result.response.content
        assert self.engine.stats.failed_queries == 1
    
    def test_clear_conversation(self):
        """Test clearing conversation history."""
        # Create conversation with messages
        conv_id = "clear-test"
        mock_context = QueryContext(
            query="test",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        self.query_processor.process_query.return_value = mock_context
        
        self.engine.query("問題 1", conversation_id=conv_id)
        self.engine.query("問題 2", conversation_id=conv_id)
        
        # Clear conversation
        self.engine.clear_conversation(conv_id, keep_system=True)
        
        # Verify cleared
        conversation = self.conversation_manager.get_conversation(conv_id)
        # Should only have system message
        assert len([m for m in conversation.messages if m.role == "system"]) == 1
        assert len([m for m in conversation.messages if m.role != "system"]) == 0
    
    def test_get_stats(self):
        """Test getting engine statistics."""
        # Run some queries
        mock_context = QueryContext(
            query="test",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        self.query_processor.process_query.return_value = mock_context
        
        self.engine.query("Query 1")
        self.engine.query("Query 2")
        
        stats = self.engine.get_stats()
        
        assert stats.total_queries == 2
        assert isinstance(stats, RAGStats)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        # Run query to update stats
        mock_context = QueryContext(
            query="test",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        self.query_processor.process_query.return_value = mock_context
        
        self.engine.query("Test")
        assert self.engine.stats.total_queries == 1
        
        # Reset stats
        self.engine.reset_stats()
        
        assert self.engine.stats.total_queries == 0
        assert self.engine.stats.successful_queries == 0
    
    def test_custom_config(self):
        """Test engine with custom configuration."""
        custom_config = RAGConfig(
            max_results=10,
            min_score=0.5,
            temperature=0.9
        )
        
        engine = RAGEngine(
            query_processor=self.query_processor,
            llm_client=self.llm_client,
            conversation_manager=self.conversation_manager,
            config=custom_config
        )
        
        assert engine.config.max_results == 10
        assert engine.config.min_score == 0.5
        assert engine.config.temperature == 0.9
    
    def test_system_message_override(self):
        """Test query with custom system message."""
        mock_context = QueryContext(
            query="test",
            retrieved_chunks=[],
            context_text="",
            has_results=False
        )
        self.query_processor.process_query.return_value = mock_context
        
        result = self.engine.query(
            "測試問題",
            conversation_id="custom-system",
            system_message="你是一個 Python 專家。"
        )
        
        # Verify conversation was created with custom system message
        conversation = self.conversation_manager.get_conversation("custom-system")
        system_messages = [m for m in conversation.messages if m.role == "system"]
        
        assert len(system_messages) > 0
        assert "Python 專家" in system_messages[0].content
