"""
LLM Client for RAG system.

Provides interfaces to various LLM providers (mock, OpenAI, Ollama).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json


@dataclass
class LLMMessage:
    """A message in the conversation."""
    role: str  # "system", "user", or "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str = "stop"
    
    def __post_init__(self):
        """Validate fields."""
        if not self.content:
            raise ValueError("Response content cannot be empty")
        if not self.model:
            raise ValueError("Model name cannot be empty")
        if self.tokens_used < 0:
            raise ValueError("Tokens used cannot be negative")


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, model: str = "default"):
        """
        Initialize LLM client.
        
        Args:
            model: Model name/identifier
        """
        self.model = model
    
    @abstractmethod
    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response from messages.
        
        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass


class MockLLMClient(LLMClient):
    """Mock LLM client for testing."""
    
    def __init__(
        self,
        model: str = "mock-model",
        responses: Optional[List[str]] = None,
        default_response: str = "這是一個測試回應。"
    ):
        """
        Initialize mock LLM client.
        
        Args:
            model: Model name
            responses: Pre-defined responses (cycles through them)
            default_response: Default response when responses exhausted
        """
        super().__init__(model)
        self.responses = responses or []
        self.default_response = default_response
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []
    
    def generate(
        self,
        messages: List[LLMMessage],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Generate mock response.
        
        Returns pre-defined responses in order, then default response.
        """
        # Record call
        self.call_history.append({
            "messages": [msg.to_dict() for msg in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "kwargs": kwargs
        })
        
        # Get response
        if self.call_count < len(self.responses):
            content = self.responses[self.call_count]
        else:
            content = self.default_response
        
        self.call_count += 1
        
        # Estimate tokens (rough approximation)
        tokens_used = len(content) // 4
        
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_used=tokens_used,
            finish_reason="stop"
        )
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens (rough approximation: 1 token ≈ 4 characters).
        
        For Chinese text, this is actually quite accurate.
        """
        return max(1, len(text) // 4)
    
    def reset(self):
        """Reset call counter and history."""
        self.call_count = 0
        self.call_history.clear()


class PromptTemplate:
    """Template for building prompts."""
    
    # System prompts
    SYSTEM_RAG = """你是一個智能助手，專門幫助用戶從他們的個人知識庫中查找和理解資訊。

你的任務：
1. 根據提供的上下文（Context）回答用戶的問題
2. 回答時必須引用來源，使用 [來源 N] 的格式
3. 如果上下文中沒有相關資訊，請明確告知用戶
4. 回答要準確、簡潔、有幫助
5. 支援繁體中文和英文

重要規則：
- 只使用提供的上下文回答，不要編造資訊
- 如果不確定，請說「我不確定」
- 引用來源時要具體（檔名和位置）
"""
    
    SYSTEM_SUMMARY = """你是一個專業的內容摘要助手。

你的任務：
1. 閱讀提供的文件內容
2. 生成簡潔、準確的摘要
3. 保留關鍵資訊和重點
4. 使用清晰的結構（如標題、列表）
5. 支援繁體中文和英文
"""
    
    @staticmethod
    def format_rag_prompt(query: str, context: str) -> str:
        """
        Format RAG prompt with query and context.
        
        Args:
            query: User's question
            context: Retrieved context with sources
            
        Returns:
            Formatted prompt
        """
        return f"""請根據以下上下文回答問題。

【上下文】
{context}

【問題】
{query}

【回答】
請根據上下文回答問題，並引用來源。如果上下文中沒有相關資訊，請說「根據本機知識庫中的資料，我找不到相關資訊。」"""
    
    @staticmethod
    def format_no_context_prompt(query: str) -> str:
        """
        Format prompt when no context is available.
        
        Args:
            query: User's question
            
        Returns:
            Formatted prompt
        """
        return f"""用戶問題：{query}

根據本機知識庫中的資料，我找不到相關資訊。

您是否需要我協助您：
1. 重新表述問題，使用不同的關鍵字
2. 搜尋網路上的資訊（需要連接網路）
3. 告訴您如何補充這方面的資料到知識庫

請問您希望我怎麼協助您？"""
    
    @staticmethod
    def format_summary_prompt(title: str, content: str) -> str:
        """
        Format summary generation prompt.
        
        Args:
            title: Document title
            content: Document content
            
        Returns:
            Formatted prompt
        """
        return f"""請為以下文件生成摘要。

【文件標題】
{title}

【文件內容】
{content}

【摘要要求】
1. 簡潔明瞭（100-300字）
2. 包含主要重點
3. 保留關鍵資訊
4. 使用清晰的結構

【摘要】
"""


# Optional: OpenAI Client (commented out by default)
"""
try:
    import openai
    
    class OpenAIClient(LLMClient):
        '''OpenAI API client.'''
        
        def __init__(
            self,
            model: str = "gpt-3.5-turbo",
            api_key: Optional[str] = None
        ):
            super().__init__(model)
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required")
            openai.api_key = self.api_key
        
        def generate(
            self,
            messages: List[LLMMessage],
            max_tokens: int = 1000,
            temperature: float = 0.7,
            **kwargs
        ) -> LLMResponse:
            '''Generate response using OpenAI API.'''
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[msg.to_dict() for msg in messages],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason
            )
        
        def count_tokens(self, text: str) -> int:
            '''Count tokens using tiktoken.'''
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))

except ImportError:
    pass
"""


# Optional: Ollama Client (commented out by default)
"""
try:
    import ollama
    
    class OllamaClient(LLMClient):
        '''Ollama local LLM client.'''
        
        def __init__(
            self,
            model: str = "llama2",
            host: str = "http://localhost:11434"
        ):
            super().__init__(model)
            self.host = host
        
        def generate(
            self,
            messages: List[LLMMessage],
            max_tokens: int = 1000,
            temperature: float = 0.7,
            **kwargs
        ) -> LLMResponse:
            '''Generate response using Ollama.'''
            response = ollama.chat(
                model=self.model,
                messages=[msg.to_dict() for msg in messages],
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **kwargs
                }
            )
            
            return LLMResponse(
                content=response['message']['content'],
                model=self.model,
                tokens_used=response.get('eval_count', 0),
                finish_reason="stop"
            )
        
        def count_tokens(self, text: str) -> int:
            '''Rough token count approximation.'''
            return max(1, len(text) // 4)

except ImportError:
    pass
"""
