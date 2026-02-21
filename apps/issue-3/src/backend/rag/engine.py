"""
RAG Engine - Complete end-to-end RAG pipeline orchestrator.

This module coordinates all Phase 2 components to provide:
- Complete query → retrieval → generation → response flow
- Multi-turn conversation support
- Error handling and fallbacks
- Performance tracking
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

from .query_processor import QueryProcessor, QueryContext
from .llm_client import LLMClient, LLMMessage
from .conversation import ConversationManager, Conversation
from .response_generator import ResponseGenerator, FormattedResponse


@dataclass
class RAGConfig:
    """Configuration for RAG engine."""
    
    # Query processing
    max_results: int = 5
    min_score: float = 0.3
    max_context_tokens: int = 2000
    
    # LLM
    max_llm_tokens: int = 1000
    temperature: float = 0.7
    
    # Conversation
    max_conversation_tokens: int = 4000
    
    # Response
    suggest_external: bool = True
    include_confidence: bool = True


@dataclass
class RAGResult:
    """Result from RAG query."""
    
    query: str
    response: FormattedResponse
    conversation_id: str
    turn_count: int
    processing_time: float
    has_local_data: bool
    retrieved_chunks_count: int = 0
    llm_tokens_used: int = 0
    error: Optional[str] = None


@dataclass
class RAGStats:
    """Statistics for RAG engine."""
    
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    total_chunks_retrieved: int = 0
    total_tokens_used: int = 0
    
    def update(self, result: RAGResult):
        """Update stats with new result."""
        self.total_queries += 1
        
        if result.error:
            self.failed_queries += 1
        else:
            self.successful_queries += 1
        
        self.total_processing_time += result.processing_time
        self.average_processing_time = self.total_processing_time / self.total_queries
        self.total_chunks_retrieved += result.retrieved_chunks_count
        self.total_tokens_used += result.llm_tokens_used


class RAGEngine:
    """
    Complete RAG (Retrieval Augmented Generation) engine.
    
    Orchestrates the full pipeline:
    1. Query processing and retrieval
    2. Context preparation
    3. LLM generation
    4. Response formatting
    5. Conversation management
    
    Features:
    - End-to-end query → response
    - Multi-turn conversations
    - Error handling and fallbacks
    - Performance tracking
    - Configurable parameters
    """
    
    def __init__(
        self,
        query_processor: QueryProcessor,
        llm_client: LLMClient,
        conversation_manager: ConversationManager,
        response_generator: Optional[ResponseGenerator] = None,
        config: Optional[RAGConfig] = None
    ):
        """
        Initialize RAG engine.
        
        Args:
            query_processor: Query processor instance
            llm_client: LLM client instance
            conversation_manager: Conversation manager instance
            response_generator: Response generator (optional)
            config: RAG configuration (optional)
        """
        self.query_processor = query_processor
        self.llm_client = llm_client
        self.conversation_manager = conversation_manager
        self.response_generator = response_generator or ResponseGenerator()
        self.config = config or RAGConfig()
        self.stats = RAGStats()
    
    def query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> RAGResult:
        """
        Process a user query through the complete RAG pipeline.
        
        Args:
            query: User query text
            conversation_id: Optional conversation ID for multi-turn
            system_message: Optional system message for new conversations
            
        Returns:
            RAGResult with response and metadata
        """
        start_time = time.time()
        
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(
                conversation_id,
                system_message
            )
            
            # Step 1: Query processing and retrieval
            query_context = self._process_query(query, conversation)
            
            # Step 2: Check if we have results
            if not query_context.has_results:
                return self._handle_no_results(
                    query,
                    conversation.session_id,
                    conversation.turn_count,
                    start_time
                )
            
            # Step 3: Generate LLM response
            llm_response, tokens_used = self._generate_llm_response(
                query_context,
                conversation
            )
            
            # Step 4: Format response with citations
            formatted_response = self.response_generator.format_response(
                llm_response,
                query_context,
                has_local_data=True
            )
            
            # Step 5: Update conversation
            self._update_conversation(
                conversation,
                query,
                formatted_response.content
            )
            
            # Create result
            processing_time = time.time() - start_time
            result = RAGResult(
                query=query,
                response=formatted_response,
                conversation_id=conversation.session_id,
                turn_count=conversation.turn_count,
                processing_time=processing_time,
                has_local_data=True,
                retrieved_chunks_count=len(query_context.retrieved_chunks),
                llm_tokens_used=tokens_used
            )
            
            # Update stats
            self.stats.update(result)
            
            return result
            
        except Exception as e:
            # Handle errors gracefully
            processing_time = time.time() - start_time
            error_result = RAGResult(
                query=query,
                response=FormattedResponse(
                    content=f"❌ 處理查詢時發生錯誤：{str(e)}",
                    citations=[],
                    has_local_data=False
                ),
                conversation_id=conversation_id or "error",
                turn_count=0,
                processing_time=processing_time,
                has_local_data=False,
                error=str(e)
            )
            
            self.stats.update(error_result)
            return error_result
    
    def summarize_document(
        self,
        document_path: str,
        conversation_id: Optional[str] = None
    ) -> RAGResult:
        """
        Generate a summary for a specific document.
        
        Args:
            document_path: Path to document to summarize
            conversation_id: Optional conversation ID
            
        Returns:
            RAGResult with summary
        """
        start_time = time.time()
        
        try:
            # Get or create conversation
            conversation = self._get_or_create_conversation(
                conversation_id,
                "你是一個專業的文件摘要助手。"
            )
            
            # Retrieve document chunks
            # Note: This is a simplified version
            # In practice, would filter by document_path
            query = f"summarize:{document_path}"
            query_context = self.query_processor.process_query(query)
            
            if not query_context.has_results:
                return self._handle_no_results(
                    f"文件摘要: {document_path}",
                    conversation.session_id,
                    conversation.turn_count,
                    start_time
                )
            
            # Generate summary using LLM
            messages = conversation.get_messages(
                max_tokens=self.config.max_conversation_tokens
            )
            
            # Add summary prompt
            from .llm_client import PromptTemplate
            summary_prompt = PromptTemplate.format_summary_prompt(
                query_context.context_text
            )
            messages.append(LLMMessage(role="user", content=summary_prompt))
            
            llm_response_obj = self.llm_client.generate(
                messages,
                max_tokens=self.config.max_llm_tokens,
                temperature=self.config.temperature
            )
            
            # Format summary
            formatted_response = self.response_generator.format_summary_response(
                llm_response_obj.content,
                document_path,
                len(query_context.retrieved_chunks)
            )
            
            processing_time = time.time() - start_time
            result = RAGResult(
                query=f"摘要: {document_path}",
                response=formatted_response,
                conversation_id=conversation.session_id,
                turn_count=conversation.turn_count,
                processing_time=processing_time,
                has_local_data=True,
                retrieved_chunks_count=len(query_context.retrieved_chunks),
                llm_tokens_used=llm_response_obj.tokens_used
            )
            
            self.stats.update(result)
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = RAGResult(
                query=f"摘要: {document_path}",
                response=FormattedResponse(
                    content=f"❌ 生成摘要時發生錯誤：{str(e)}",
                    citations=[],
                    has_local_data=False
                ),
                conversation_id=conversation_id or "error",
                turn_count=0,
                processing_time=processing_time,
                has_local_data=False,
                error=str(e)
            )
            
            self.stats.update(error_result)
            return error_result
    
    def clear_conversation(self, conversation_id: str, keep_system: bool = True):
        """
        Clear conversation history.
        
        Args:
            conversation_id: Conversation to clear
            keep_system: Whether to keep system message
        """
        conversation = self.conversation_manager.get_conversation(conversation_id)
        if conversation:
            conversation.clear_history(keep_system=keep_system)
            self.conversation_manager.save_conversation(conversation_id)
    
    def get_stats(self) -> RAGStats:
        """Get engine statistics."""
        return self.stats
    
    def reset_stats(self):
        """Reset statistics."""
        self.stats = RAGStats()
    
    def _get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        system_message: Optional[str]
    ) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id:
            conversation = self.conversation_manager.get_conversation(conversation_id)
            if conversation:
                return conversation
        
        # Create new conversation
        from .llm_client import PromptTemplate
        system_msg = system_message or PromptTemplate.SYSTEM_RAG
        
        # Generate ID if not provided
        if not conversation_id:
            conversation_id = f"rag_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return self.conversation_manager.create_conversation(
            session_id=conversation_id,
            system_message=system_msg
        )
    
    def _process_query(
        self,
        query: str,
        conversation: Conversation
    ) -> QueryContext:
        """Process query with conversation history."""
        # Get recent messages for context
        history_text = ""
        if conversation.turn_count > 0:
            recent_messages = conversation.get_messages(max_tokens=500)
            # Skip system message
            recent_messages = [m for m in recent_messages if m.role != "system"]
            if recent_messages:
                history_text = "\n".join([
                    f"{m.role}: {m.content}"
                    for m in recent_messages[-4:]  # Last 2 turns
                ])
        
        # Process query with history
        return self.query_processor.process_query(
            query,
            conversation_history=history_text
        )
    
    def _generate_llm_response(
        self,
        query_context: QueryContext,
        conversation: Conversation
    ) -> tuple[str, int]:
        """Generate LLM response."""
        # Get conversation messages
        messages = conversation.get_messages(
            max_tokens=self.config.max_conversation_tokens
        )
        
        # Add current query with context
        from .llm_client import PromptTemplate
        user_message = PromptTemplate.format_rag_prompt(
            query_context.query,
            query_context.context_text
        )
        messages.append(LLMMessage(role="user", content=user_message))
        
        # Generate response
        response = self.llm_client.generate(
            messages,
            max_tokens=self.config.max_llm_tokens,
            temperature=self.config.temperature
        )
        
        return response.content, response.tokens_used
    
    def _update_conversation(
        self,
        conversation: Conversation,
        query: str,
        response: str
    ):
        """Update conversation with query and response."""
        conversation.add_message(LLMMessage(role="user", content=query))
        conversation.add_message(LLMMessage(role="assistant", content=response))
        
        # Save conversation
        self.conversation_manager.save_conversation(conversation.session_id)
    
    def _handle_no_results(
        self,
        query: str,
        conversation_id: str,
        turn_count: int,
        start_time: float
    ) -> RAGResult:
        """Handle case when no results found."""
        formatted_response = self.response_generator.format_no_results_response(
            query,
            suggest_external=self.config.suggest_external
        )
        
        processing_time = time.time() - start_time
        result = RAGResult(
            query=query,
            response=formatted_response,
            conversation_id=conversation_id,
            turn_count=turn_count,
            processing_time=processing_time,
            has_local_data=False
        )
        
        self.stats.update(result)
        return result
