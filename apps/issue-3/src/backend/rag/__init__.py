"""
RAG (Retrieval Augmented Generation) module for AI知識++.

This module provides the core RAG functionality including query processing,
LLM integration, conversation management, and response generation.
"""

# Import components as they become available
from .query_processor import QueryProcessor

__all__ = [
    "QueryProcessor",
]

# Will be added as implemented:
# from .llm_client import LLMClient, MockLLMClient
# from .conversation import ConversationManager, Conversation  
# from .response_generator import ResponseGenerator
# from .engine import RAGEngine
