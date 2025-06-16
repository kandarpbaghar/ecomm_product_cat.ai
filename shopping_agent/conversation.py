"""
Conversation Management for Shopping Agent
Handles conversation history, context, and state management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from collections import defaultdict


class Message:
    """Represents a single message in a conversation"""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None):
        self.role = role  # 'user', 'assistant', or 'system'
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self, max_history_length: int = 20):
        self.conversations = defaultdict(list)
        self.max_history_length = max_history_length
        self.contexts = defaultdict(dict)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the conversation"""
        message = Message(role, content, metadata=metadata)
        self.conversations[session_id].append(message)
        
        # Trim history if it exceeds max length
        if len(self.conversations[session_id]) > self.max_history_length:
            # Keep system messages and recent messages
            system_msgs = [m for m in self.conversations[session_id] if m.role == "system"]
            other_msgs = [m for m in self.conversations[session_id] if m.role != "system"]
            
            # Keep last N messages plus system messages
            keep_count = self.max_history_length - len(system_msgs)
            self.conversations[session_id] = system_msgs + other_msgs[-keep_count:]
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history in format suitable for LLM"""
        history = []
        for message in self.conversations[session_id]:
            history.append({
                "role": message.role,
                "content": message.content
            })
        return history
    
    def get_full_history(self, session_id: str) -> List[Message]:
        """Get full conversation history with metadata"""
        return self.conversations[session_id]
    
    def clear_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def set_context(self, session_id: str, key: str, value: Any):
        """Set context value for a session"""
        self.contexts[session_id][key] = value
    
    def get_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get context value for a session"""
        return self.contexts[session_id].get(key, default)
    
    def get_all_context(self, session_id: str) -> Dict[str, Any]:
        """Get all context for a session"""
        return self.contexts[session_id].copy()
    
    def get_summary(self, session_id: str) -> Dict[str, Any]:
        """Get conversation summary"""
        messages = self.conversations[session_id]
        
        if not messages:
            return {
                "message_count": 0,
                "started_at": None,
                "last_message_at": None,
                "user_messages": 0,
                "assistant_messages": 0
            }
        
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]
        
        return {
            "message_count": len(messages),
            "started_at": messages[0].timestamp.isoformat(),
            "last_message_at": messages[-1].timestamp.isoformat(),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "context": self.get_all_context(session_id)
        }
    
    def export_conversation(self, session_id: str) -> str:
        """Export conversation as JSON string"""
        data = {
            "session_id": session_id,
            "messages": [msg.to_dict() for msg in self.conversations[session_id]],
            "context": self.get_all_context(session_id),
            "summary": self.get_summary(session_id)
        }
        return json.dumps(data, indent=2)
    
    def import_conversation(self, data: str) -> str:
        """Import conversation from JSON string"""
        parsed_data = json.loads(data)
        session_id = parsed_data["session_id"]
        
        # Clear existing data
        self.clear_history(session_id)
        
        # Import messages
        for msg_data in parsed_data["messages"]:
            message = Message.from_dict(msg_data)
            self.conversations[session_id].append(message)
        
        # Import context
        if "context" in parsed_data:
            self.contexts[session_id] = parsed_data["context"]
        
        return session_id