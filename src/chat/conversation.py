"""
Conversation management for Local Chat Companion.

Handles conversation history, context management, and message processing.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

try:
    import structlog
except ImportError:
    structlog = None

from ..core.config import Config
from ..core.logging_config import LoggerMixin
from .lm_studio import ChatMessage, ChatResponse


@dataclass
class ConversationTurn:
    """A single turn in the conversation (user message + assistant response)."""
    id: str
    timestamp: datetime
    user_message: ChatMessage
    assistant_response: Optional[ChatResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class Conversation:
    """A complete conversation with metadata and history."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    turns: List[ConversationTurn] = field(default_factory=list)
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_turn(self, user_message: str, assistant_response: Optional[ChatResponse] = None) -> ConversationTurn:
        """Add a new turn to the conversation."""
        turn = ConversationTurn(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            user_message=ChatMessage(role="user", content=user_message),
            assistant_response=assistant_response
        )
        self.turns.append(turn)
        self.updated_at = datetime.now(timezone.utc)
        return turn
    
    def get_messages_for_llm(self, max_turns: Optional[int] = None) -> List[ChatMessage]:
        """Get messages formatted for LLM consumption."""
        messages = []
        
        # Add system prompt if present
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))
        
        # Add conversation turns
        turns_to_include = self.turns[-max_turns:] if max_turns else self.turns
        
        for turn in turns_to_include:
            messages.append(turn.user_message)
            if turn.assistant_response:
                messages.append(turn.assistant_response.message)
        
        return messages
    
    def get_last_incomplete_turn(self) -> Optional[ConversationTurn]:
        """Get the last turn that doesn't have an assistant response."""
        if self.turns and not self.turns[-1].assistant_response:
            return self.turns[-1]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        data["turns"] = [turn.to_dict() for turn in self.turns]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create from dictionary."""
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["turns"] = [ConversationTurn.from_dict(turn_data) for turn_data in data.get("turns", [])]
        return cls(**data)


class ConversationManager(LoggerMixin):
    """Manages conversations, history, and persistence."""
    
    def __init__(self, config: Config):
        """Initialize the conversation manager."""
        self.config = config
        self.current_conversation: Optional[Conversation] = None
        self.sessions_dir = Path(config.sqlite_db_path).parent / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            "Conversation manager initialized",
            sessions_dir=str(self.sessions_dir),
            max_session_memory=config.max_session_memory
        )
    
    def start_new_conversation(
        self,
        title: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> Conversation:
        """Start a new conversation."""
        now = datetime.now(timezone.utc)
        conversation_id = str(uuid.uuid4())
        
        # Generate a title if not provided
        if not title:
            title = f"Chat {now.strftime('%Y-%m-%d %H:%M')}"
        
        # Create default system prompt based on configuration
        if not system_prompt:
            style = self.config.default_style
            system_prompt = self._get_default_system_prompt(style)
        
        conversation = Conversation(
            id=conversation_id,
            title=title,
            created_at=now,
            updated_at=now,
            system_prompt=system_prompt,
            metadata={
                "style": self.config.default_style,
                "model": self.config.default_model,
                "temperature": self.config.temperature
            }
        )
        
        self.current_conversation = conversation
        
        self.logger.info(
            "Started new conversation",
            conversation_id=conversation_id,
            title=title,
            style=self.config.default_style
        )
        
        return conversation
    
    def add_user_message(self, message: str) -> ConversationTurn:
        """Add a user message to the current conversation."""
        if not self.current_conversation:
            self.start_new_conversation()
        
        turn = self.current_conversation.add_turn(message)
        
        self.logger.debug(
            "Added user message",
            conversation_id=self.current_conversation.id,
            turn_id=turn.id,
            message_length=len(message)
        )
        
        return turn
    
    def add_assistant_response(self, response: ChatResponse) -> None:
        """Add an assistant response to the last turn."""
        if not self.current_conversation:
            raise ValueError("No active conversation")
        
        last_turn = self.current_conversation.get_last_incomplete_turn()
        if not last_turn:
            raise ValueError("No incomplete turn to complete")
        
        last_turn.assistant_response = response
        self.current_conversation.updated_at = datetime.now(timezone.utc)
        
        self.logger.debug(
            "Added assistant response",
            conversation_id=self.current_conversation.id,
            turn_id=last_turn.id,
            response_length=len(response.message.content),
            tokens_used=response.usage.total_tokens
        )
    
    def get_messages_for_llm(self) -> List[ChatMessage]:
        """Get messages formatted for LLM, respecting session memory limits."""
        if not self.current_conversation:
            return []
        
        max_turns = self.config.max_session_memory
        return self.current_conversation.get_messages_for_llm(max_turns)
    
    def save_conversation(self, conversation: Optional[Conversation] = None) -> Path:
        """Save a conversation to disk."""
        conv = conversation or self.current_conversation
        if not conv:
            raise ValueError("No conversation to save")
        
        filename = f"{conv.id}.json"
        filepath = self.sessions_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conv.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                "Conversation saved",
                conversation_id=conv.id,
                filepath=str(filepath),
                turns_count=len(conv.turns)
            )
            
            return filepath
            
        except Exception as e:
            self.logger.error(
                "Failed to save conversation",
                conversation_id=conv.id,
                error=str(e),
                exc_info=True
            )
            raise
    
    def load_conversation(self, conversation_id: str) -> Conversation:
        """Load a conversation from disk."""
        filename = f"{conversation_id}.json"
        filepath = self.sessions_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Conversation {conversation_id} not found")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = Conversation.from_dict(data)
            
            self.logger.info(
                "Conversation loaded",
                conversation_id=conversation_id,
                turns_count=len(conversation.turns)
            )
            
            return conversation
            
        except Exception as e:
            self.logger.error(
                "Failed to load conversation",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all saved conversations with metadata."""
        conversations = []
        
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conversations.append({
                    "id": data["id"],
                    "title": data["title"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "turns_count": len(data.get("turns", [])),
                    "metadata": data.get("metadata", {})
                })
                
            except Exception as e:
                self.logger.warning(
                    "Failed to read conversation file",
                    filepath=str(filepath),
                    error=str(e)
                )
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        self.logger.debug(f"Listed {len(conversations)} conversations")
        return conversations
    
    def auto_save(self) -> None:
        """Auto-save the current conversation if enabled."""
        if self.config.auto_save_sessions and self.current_conversation:
            try:
                self.save_conversation()
            except Exception as e:
                self.logger.error("Auto-save failed", error=str(e))
    
    def _get_default_system_prompt(self, style: str) -> str:
        """Get the default system prompt based on personality style."""
        prompts = {
            "friend": (
                "You are a friendly, warm, and supportive AI companion. "
                "Engage in conversations with genuine interest and empathy. "
                "Be helpful while maintaining a casual, approachable tone."
            ),
            "coach": (
                "You are a motivational AI coach focused on helping users achieve their goals. "
                "Ask probing questions, provide encouragement, and offer practical advice. "
                "Be supportive but also challenge users to grow and improve."
            ),
            "assistant": (
                "You are a professional AI assistant. Provide clear, accurate, and helpful responses. "
                "Be polite, efficient, and focused on solving problems and answering questions effectively."
            ),
            "custom": (
                "You are a helpful AI assistant. Respond naturally and adapt your communication style "
                "based on the user's preferences and the context of the conversation."
            )
        }
        
        return prompts.get(style, prompts["custom"])
