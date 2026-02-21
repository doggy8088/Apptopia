"""
Tests for LLM Client.
"""

import pytest
from src.backend.rag.llm_client import (
    LLMMessage,
    LLMResponse,
    LLMClient,
    MockLLMClient,
    PromptTemplate
)


class TestLLMMessage:
    """Test LLMMessage dataclass."""
    
    def test_create_message(self):
        """Test creating a message."""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
    
    def test_to_dict(self):
        """Test converting message to dict."""
        msg = LLMMessage(role="assistant", content="Hi there")
        d = msg.to_dict()
        assert d == {"role": "assistant", "content": "Hi there"}


class TestLLMResponse:
    """Test LLMResponse dataclass."""
    
    def test_create_response(self):
        """Test creating a response."""
        resp = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            tokens_used=10
        )
        assert resp.content == "Test response"
        assert resp.model == "gpt-3.5-turbo"
        assert resp.tokens_used == 10
        assert resp.finish_reason == "stop"
    
    def test_empty_content_raises_error(self):
        """Test that empty content raises error."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            LLMResponse(content="", model="test", tokens_used=0)
    
    def test_empty_model_raises_error(self):
        """Test that empty model raises error."""
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            LLMResponse(content="test", model="", tokens_used=0)
    
    def test_negative_tokens_raises_error(self):
        """Test that negative tokens raises error."""
        with pytest.raises(ValueError, match="Tokens used cannot be negative"):
            LLMResponse(content="test", model="test", tokens_used=-1)


class TestMockLLMClient:
    """Test MockLLMClient."""
    
    def test_initialization(self):
        """Test client initialization."""
        client = MockLLMClient()
        assert client.model == "mock-model"
        assert client.call_count == 0
        assert len(client.call_history) == 0
    
    def test_generate_with_default_response(self):
        """Test generating with default response."""
        client = MockLLMClient()
        messages = [LLMMessage(role="user", content="Hello")]
        
        response = client.generate(messages)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "這是一個測試回應。"
        assert response.model == "mock-model"
        assert response.tokens_used > 0
        assert client.call_count == 1
    
    def test_generate_with_predefined_responses(self):
        """Test generating with pre-defined responses."""
        client = MockLLMClient(
            responses=["First response", "Second response"]
        )
        messages = [LLMMessage(role="user", content="Hello")]
        
        # First call
        resp1 = client.generate(messages)
        assert resp1.content == "First response"
        assert client.call_count == 1
        
        # Second call
        resp2 = client.generate(messages)
        assert resp2.content == "Second response"
        assert client.call_count == 2
        
        # Third call (should use default)
        resp3 = client.generate(messages)
        assert resp3.content == "這是一個測試回應。"
        assert client.call_count == 3
    
    def test_call_history(self):
        """Test that call history is recorded."""
        client = MockLLMClient()
        messages = [
            LLMMessage(role="system", content="You are helpful"),
            LLMMessage(role="user", content="What is Rust?")
        ]
        
        client.generate(messages, max_tokens=500, temperature=0.5)
        
        assert len(client.call_history) == 1
        call = client.call_history[0]
        assert len(call["messages"]) == 2
        assert call["max_tokens"] == 500
        assert call["temperature"] == 0.5
    
    def test_count_tokens(self):
        """Test token counting."""
        client = MockLLMClient()
        
        # English text (roughly 4 chars per token)
        text1 = "Hello world"
        assert client.count_tokens(text1) >= 1
        
        # Chinese text (also roughly 4 chars per token)
        text2 = "這是一個測試"
        assert client.count_tokens(text2) >= 1
        
        # Long text
        text3 = "a" * 1000
        assert client.count_tokens(text3) == 250
    
    def test_reset(self):
        """Test resetting client state."""
        client = MockLLMClient(responses=["Response 1"])
        messages = [LLMMessage(role="user", content="Hello")]
        
        # Make some calls
        client.generate(messages)
        client.generate(messages)
        assert client.call_count == 2
        assert len(client.call_history) == 2
        
        # Reset
        client.reset()
        assert client.call_count == 0
        assert len(client.call_history) == 0
        
        # Should cycle through responses again
        resp = client.generate(messages)
        assert resp.content == "Response 1"


class TestPromptTemplate:
    """Test PromptTemplate."""
    
    def test_system_prompts_exist(self):
        """Test that system prompts are defined."""
        assert PromptTemplate.SYSTEM_RAG
        assert PromptTemplate.SYSTEM_SUMMARY
        assert "知識庫" in PromptTemplate.SYSTEM_RAG
        assert "摘要" in PromptTemplate.SYSTEM_SUMMARY
    
    def test_format_rag_prompt(self):
        """Test formatting RAG prompt."""
        query = "Rust 的所有權是什麼？"
        context = "[來源 1] Rust 所有權.md\n所有權是 Rust 的核心特性..."
        
        prompt = PromptTemplate.format_rag_prompt(query, context)
        
        assert query in prompt
        assert context in prompt
        assert "上下文" in prompt
        assert "問題" in prompt
        assert "回答" in prompt
    
    def test_format_no_context_prompt(self):
        """Test formatting no context prompt."""
        query = "什麼是量子計算？"
        
        prompt = PromptTemplate.format_no_context_prompt(query)
        
        assert query in prompt
        assert "找不到相關資訊" in prompt
        assert "協助" in prompt
    
    def test_format_summary_prompt(self):
        """Test formatting summary prompt."""
        title = "Rust 所有權系統"
        content = "Rust 使用所有權系統來管理記憶體..."
        
        prompt = PromptTemplate.format_summary_prompt(title, content)
        
        assert title in prompt
        assert content in prompt
        assert "摘要" in prompt
        assert "文件" in prompt


class TestLLMClientInterface:
    """Test LLMClient abstract interface."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            LLMClient()
    
    def test_mock_implements_interface(self):
        """Test that MockLLMClient implements interface."""
        client = MockLLMClient()
        
        # Should have required methods
        assert hasattr(client, 'generate')
        assert hasattr(client, 'count_tokens')
        assert callable(client.generate)
        assert callable(client.count_tokens)


class TestIntegration:
    """Integration tests for LLM components."""
    
    def test_complete_conversation_flow(self):
        """Test a complete conversation flow."""
        client = MockLLMClient(
            responses=[
                "Rust 的所有權系統是其核心特性，確保記憶體安全。[來源 1]",
                "借用允許在不轉移所有權的情況下使用值。[來源 2]"
            ]
        )
        
        # First turn
        messages1 = [
            LLMMessage(role="system", content=PromptTemplate.SYSTEM_RAG),
            LLMMessage(role="user", content="什麼是 Rust 所有權？")
        ]
        resp1 = client.generate(messages1)
        assert "所有權" in resp1.content
        
        # Second turn (with history)
        messages2 = messages1 + [
            LLMMessage(role="assistant", content=resp1.content),
            LLMMessage(role="user", content="什麼是借用？")
        ]
        resp2 = client.generate(messages2)
        assert "借用" in resp2.content
        
        # Verify history
        assert client.call_count == 2
        assert len(client.call_history) == 2
