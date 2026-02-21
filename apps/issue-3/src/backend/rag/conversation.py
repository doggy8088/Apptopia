"""
Conversation management for multi-turn RAG conversations.

This module provides conversation state management, history tracking,
and context window management for multi-turn conversations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

from .llm_client import LLMMessage


@dataclass
class Conversation:
    """
    Represents a single conversation session.
    
    Attributes:
        session_id: Unique identifier for the conversation
        messages: List of messages in the conversation
        created_at: Timestamp when conversation was created
        updated_at: Timestamp when conversation was last updated
        metadata: Additional metadata (e.g., user info, topic)
        turn_count: Number of user-assistant exchanges
        total_tokens: Approximate total tokens used
    """
    session_id: str
    messages: List[LLMMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, str] = field(default_factory=dict)
    turn_count: int = 0
    total_tokens: int = 0
    
    def add_message(self, message: LLMMessage) -> None:
        """Add a message to the conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        
        # Increment turn count for user or assistant messages
        if message.role in ["user", "assistant"]:
            if message.role == "assistant":
                self.turn_count += 1
    
    def get_messages(self, max_tokens: Optional[int] = None) -> List[LLMMessage]:
        """
        Get conversation messages, respecting token limits.
        
        Args:
            max_tokens: Maximum tokens to include (approximate)
            
        Returns:
            List of messages that fit within token limit
        """
        if max_tokens is None:
            return self.messages.copy()
        
        # Always include system messages
        system_messages = [m for m in self.messages if m.role == "system"]
        other_messages = [m for m in self.messages if m.role != "system"]
        
        # Approximate tokens (4 chars ~= 1 token)
        result = system_messages.copy()
        tokens_used = sum(len(m.content) // 4 for m in system_messages)
        
        # Add messages from most recent, working backwards
        for message in reversed(other_messages):
            message_tokens = len(message.content) // 4
            if tokens_used + message_tokens <= max_tokens:
                result.insert(len(system_messages), message)
                tokens_used += message_tokens
            else:
                break
        
        return result
    
    def clear_history(self, keep_system: bool = True) -> None:
        """
        Clear conversation history.
        
        Args:
            keep_system: Whether to keep system messages
        """
        if keep_system:
            self.messages = [m for m in self.messages if m.role == "system"]
        else:
            self.messages = []
        self.turn_count = 0
        self.total_tokens = 0
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert conversation to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "turn_count": self.turn_count,
            "total_tokens": self.total_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conversation":
        """Create conversation from dictionary."""
        messages = [LLMMessage.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            messages=messages,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
            turn_count=data.get("turn_count", 0),
            total_tokens=data.get("total_tokens", 0)
        )


class ConversationManager:
    """
    Manages multiple conversation sessions.
    
    Provides session creation, retrieval, persistence, and cleanup.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize conversation manager.
        
        Args:
            storage_dir: Directory for persisting conversations (optional)
        """
        self.conversations: Dict[str, Conversation] = {}
        self.storage_dir = Path(storage_dir) if storage_dir else None
        
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def create_conversation(
        self,
        session_id: str,
        system_message: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            session_id: Unique identifier for the conversation
            system_message: Optional system prompt
            metadata: Optional metadata dictionary
            
        Returns:
            New Conversation instance
        """
        conversation = Conversation(
            session_id=session_id,
            metadata=metadata or {}
        )
        
        if system_message:
            conversation.add_message(
                LLMMessage(role="system", content=system_message)
            )
        
        self.conversations[session_id] = conversation
        return conversation
    
    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Get a conversation by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation if found, None otherwise
        """
        # Try in-memory first
        if session_id in self.conversations:
            return self.conversations[session_id]
        
        # Try loading from disk if storage is configured
        if self.storage_dir:
            conv = self.load_conversation(session_id)
            if conv:
                self.conversations[session_id] = conv
                return conv
        
        return None
    
    def save_conversation(self, session_id: str) -> bool:
        """
        Save a conversation to disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.storage_dir:
            return False
        
        conversation = self.conversations.get(session_id)
        if not conversation:
            return False
        
        try:
            file_path = self.storage_dir / f"{session_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Load a conversation from disk.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation if found, None otherwise
        """
        if not self.storage_dir:
            return None
        
        try:
            file_path = self.storage_dir / f"{session_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Conversation.from_dict(data)
        except Exception:
            return None
    
    def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from memory
        if session_id in self.conversations:
            del self.conversations[session_id]
        
        # Remove from disk
        if self.storage_dir:
            try:
                file_path = self.storage_dir / f"{session_id}.json"
                if file_path.exists():
                    file_path.unlink()
                return True
            except Exception:
                return False
        
        return True
    
    def list_conversations(self) -> List[str]:
        """
        List all conversation session IDs.
        
        Returns:
            List of session IDs
        """
        session_ids = set(self.conversations.keys())
        
        # Add sessions from disk
        if self.storage_dir and self.storage_dir.exists():
            for file_path in self.storage_dir.glob("*.json"):
                session_ids.add(file_path.stem)
        
        return sorted(session_ids)
    
    def clear_all(self) -> None:
        """Clear all conversations from memory and disk."""
        # Clear memory
        self.conversations.clear()
        
        # Clear disk
        if self.storage_dir and self.storage_dir.exists():
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    file_path.unlink()
                except Exception:
                    pass
