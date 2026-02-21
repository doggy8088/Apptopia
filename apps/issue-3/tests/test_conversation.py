"""
Tests for conversation management.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.backend.rag.conversation import Conversation, ConversationManager
from src.backend.rag.llm_client import LLMMessage


class TestConversation:
    """Tests for Conversation class."""
    
    def test_conversation_creation(self):
        """Test creating a conversation."""
        conv = Conversation(session_id="test-123")
        assert conv.session_id == "test-123"
        assert len(conv.messages) == 0
        assert conv.turn_count == 0
        assert conv.total_tokens == 0
        assert isinstance(conv.metadata, dict)
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = Conversation(session_id="test-123")
        
        # Add system message
        conv.add_message(LLMMessage(role="system", content="You are helpful"))
        assert len(conv.messages) == 1
        assert conv.turn_count == 0  # System messages don't count as turns
        
        # Add user message
        conv.add_message(LLMMessage(role="user", content="Hello"))
        assert len(conv.messages) == 2
        assert conv.turn_count == 0  # Turn not complete until assistant responds
        
        # Add assistant message
        conv.add_message(LLMMessage(role="assistant", content="Hi there!"))
        assert len(conv.messages) == 3
        assert conv.turn_count == 1  # Now we have a complete turn
    
    def test_get_messages_without_limit(self):
        """Test getting all messages without token limit."""
        conv = Conversation(session_id="test-123")
        conv.add_message(LLMMessage(role="system", content="System"))
        conv.add_message(LLMMessage(role="user", content="User 1"))
        conv.add_message(LLMMessage(role="assistant", content="Assistant 1"))
        
        messages = conv.get_messages()
        assert len(messages) == 3
        assert messages[0].role == "system"
    
    def test_get_messages_with_token_limit(self):
        """Test getting messages with token limit."""
        conv = Conversation(session_id="test-123")
        
        # Add messages (each ~10 tokens based on content length)
        conv.add_message(LLMMessage(role="system", content="You are helpful"))  # ~4 tokens
        conv.add_message(LLMMessage(role="user", content="First question with many words"))  # ~7 tokens
        conv.add_message(LLMMessage(role="assistant", content="First answer here"))  # ~4 tokens
        conv.add_message(LLMMessage(role="user", content="Second question"))  # ~4 tokens
        conv.add_message(LLMMessage(role="assistant", content="Second answer"))  # ~3 tokens
        
        # Request messages with limit of 15 tokens
        # Should get: system (4) + most recent messages that fit
        messages = conv.get_messages(max_tokens=15)
        
        # System message is always included
        assert messages[0].role == "system"
        
        # Should have some recent messages
        assert len(messages) >= 2  # At least system + 1 recent
        assert len(messages) <= 5  # Not all if total exceeds limit
    
    def test_clear_history_keep_system(self):
        """Test clearing history while keeping system messages."""
        conv = Conversation(session_id="test-123")
        conv.add_message(LLMMessage(role="system", content="System"))
        conv.add_message(LLMMessage(role="user", content="User"))
        conv.add_message(LLMMessage(role="assistant", content="Assistant"))
        
        conv.clear_history(keep_system=True)
        
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "system"
        assert conv.turn_count == 0
    
    def test_clear_history_all(self):
        """Test clearing all history."""
        conv = Conversation(session_id="test-123")
        conv.add_message(LLMMessage(role="system", content="System"))
        conv.add_message(LLMMessage(role="user", content="User"))
        
        conv.clear_history(keep_system=False)
        
        assert len(conv.messages) == 0
        assert conv.turn_count == 0
    
    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        conv = Conversation(
            session_id="test-123",
            metadata={"user": "alice"}
        )
        conv.add_message(LLMMessage(role="user", content="Hello"))
        
        # Convert to dict
        data = conv.to_dict()
        assert data["session_id"] == "test-123"
        assert len(data["messages"]) == 1
        assert data["metadata"]["user"] == "alice"
        
        # Convert back
        conv2 = Conversation.from_dict(data)
        assert conv2.session_id == conv.session_id
        assert len(conv2.messages) == len(conv.messages)
        assert conv2.metadata == conv.metadata


class TestConversationManager:
    """Tests for ConversationManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    def test_create_conversation(self):
        """Test creating a conversation."""
        manager = ConversationManager()
        conv = manager.create_conversation("session-1")
        
        assert conv.session_id == "session-1"
        assert "session-1" in manager.conversations
    
    def test_create_conversation_with_system_message(self):
        """Test creating conversation with system message."""
        manager = ConversationManager()
        conv = manager.create_conversation(
            "session-1",
            system_message="You are helpful"
        )
        
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "system"
        assert conv.messages[0].content == "You are helpful"
    
    def test_create_conversation_with_metadata(self):
        """Test creating conversation with metadata."""
        manager = ConversationManager()
        conv = manager.create_conversation(
            "session-1",
            metadata={"user": "alice", "topic": "rust"}
        )
        
        assert conv.metadata["user"] == "alice"
        assert conv.metadata["topic"] == "rust"
    
    def test_get_conversation(self):
        """Test getting a conversation."""
        manager = ConversationManager()
        manager.create_conversation("session-1")
        
        conv = manager.get_conversation("session-1")
        assert conv is not None
        assert conv.session_id == "session-1"
    
    def test_get_nonexistent_conversation(self):
        """Test getting a conversation that doesn't exist."""
        manager = ConversationManager()
        conv = manager.get_conversation("nonexistent")
        assert conv is None
    
    def test_save_and_load_conversation(self, temp_dir):
        """Test saving and loading a conversation."""
        manager = ConversationManager(storage_dir=temp_dir)
        
        # Create and save conversation
        conv = manager.create_conversation("session-1")
        conv.add_message(LLMMessage(role="user", content="Hello"))
        
        assert manager.save_conversation("session-1")
        
        # Load conversation
        loaded = manager.load_conversation("session-1")
        assert loaded is not None
        assert loaded.session_id == "session-1"
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Hello"
    
    def test_save_without_storage_dir(self):
        """Test saving without storage directory configured."""
        manager = ConversationManager()
        manager.create_conversation("session-1")
        
        # Should return False when no storage dir
        assert not manager.save_conversation("session-1")
    
    def test_delete_conversation(self):
        """Test deleting a conversation."""
        manager = ConversationManager()
        manager.create_conversation("session-1")
        
        assert "session-1" in manager.conversations
        
        manager.delete_conversation("session-1")
        
        assert "session-1" not in manager.conversations
    
    def test_delete_conversation_from_disk(self, temp_dir):
        """Test deleting a conversation from disk."""
        manager = ConversationManager(storage_dir=temp_dir)
        
        # Create, save, and delete
        manager.create_conversation("session-1")
        manager.save_conversation("session-1")
        
        file_path = temp_dir / "session-1.json"
        assert file_path.exists()
        
        manager.delete_conversation("session-1")
        
        assert not file_path.exists()
    
    def test_list_conversations(self):
        """Test listing conversations."""
        manager = ConversationManager()
        manager.create_conversation("session-1")
        manager.create_conversation("session-2")
        
        sessions = manager.list_conversations()
        assert "session-1" in sessions
        assert "session-2" in sessions
        assert len(sessions) == 2
    
    def test_list_conversations_from_disk(self, temp_dir):
        """Test listing conversations including those on disk."""
        manager = ConversationManager(storage_dir=temp_dir)
        
        # Create and save conversations
        manager.create_conversation("session-1")
        manager.save_conversation("session-1")
        
        # Create new manager (doesn't have session-1 in memory)
        manager2 = ConversationManager(storage_dir=temp_dir)
        manager2.create_conversation("session-2")
        
        sessions = manager2.list_conversations()
        assert "session-1" in sessions  # From disk
        assert "session-2" in sessions  # From memory
    
    def test_clear_all(self, temp_dir):
        """Test clearing all conversations."""
        manager = ConversationManager(storage_dir=temp_dir)
        
        # Create conversations
        manager.create_conversation("session-1")
        manager.create_conversation("session-2")
        manager.save_conversation("session-1")
        manager.save_conversation("session-2")
        
        assert len(manager.conversations) == 2
        assert len(list(temp_dir.glob("*.json"))) == 2
        
        manager.clear_all()
        
        assert len(manager.conversations) == 0
        assert len(list(temp_dir.glob("*.json"))) == 0
    
    def test_get_conversation_loads_from_disk(self, temp_dir):
        """Test that get_conversation loads from disk if not in memory."""
        manager = ConversationManager(storage_dir=temp_dir)
        
        # Create and save conversation
        conv = manager.create_conversation("session-1")
        conv.add_message(LLMMessage(role="user", content="Hello"))
        manager.save_conversation("session-1")
        
        # Remove from memory
        del manager.conversations["session-1"]
        
        # Get should load from disk
        loaded = manager.get_conversation("session-1")
        assert loaded is not None
        assert loaded.session_id == "session-1"
        assert len(loaded.messages) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
