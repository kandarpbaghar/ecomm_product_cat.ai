"""
Database models for Shopping Agent
"""

from database import db
from datetime import datetime
import json


class AgentConfig(db.Model):
    """Store agent configuration settings"""
    __tablename__ = 'agent_config'
    
    id = db.Column(db.Integer, primary_key=True)
    llm_provider = db.Column(db.String(50), default='openai')
    llm_model = db.Column(db.String(100), default='gpt-4-turbo-preview')
    openai_api_key = db.Column(db.Text)
    anthropic_api_key = db.Column(db.Text)
    google_api_key = db.Column(db.Text)
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=500)
    system_prompt_type = db.Column(db.String(50), default='shopping_assistant')
    custom_system_prompt = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'system_prompt_type': self.system_prompt_type,
            'custom_system_prompt': self.custom_system_prompt,
            'has_openai_key': bool(self.openai_api_key),
            'has_anthropic_key': bool(self.anthropic_api_key),
            'has_google_key': bool(self.google_api_key),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_current_config(cls):
        """Get the current configuration (latest)"""
        return cls.query.order_by(cls.id.desc()).first()


class AgentConversation(db.Model):
    """Store conversation history"""
    __tablename__ = 'agent_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # user, assistant, system
    content = db.Column(db.Text, nullable=False)
    message_metadata = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    products_shown = db.relationship('AgentProductInteraction', backref='conversation', lazy='dynamic')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'metadata': json.loads(self.message_metadata) if self.message_metadata else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_session_history(cls, session_id, limit=50):
        """Get conversation history for a session"""
        return cls.query.filter_by(session_id=session_id)\
                       .order_by(cls.created_at.desc())\
                       .limit(limit)\
                       .all()


class AgentProductInteraction(db.Model):
    """Track products shown/interacted with during conversations"""
    __tablename__ = 'agent_product_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('agent_conversations.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('skus.id'))
    interaction_type = db.Column(db.String(50))  # shown, clicked, compared, etc.
    position = db.Column(db.Integer)  # Position in results
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('SKU', backref='agent_interactions')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'product_id': self.product_id,
            'interaction_type': self.interaction_type,
            'position': self.position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentAnalytics(db.Model):
    """Store analytics data for agent performance"""
    __tablename__ = 'agent_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), index=True)
    event_type = db.Column(db.String(50))  # session_start, search, product_view, etc.
    event_data = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'event_type': self.event_type,
            'event_data': json.loads(self.event_data) if self.event_data else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def log_event(cls, session_id, event_type, event_data=None):
        """Log an analytics event"""
        event = cls(
            session_id=session_id,
            event_type=event_type,
            event_data=json.dumps(event_data) if event_data else None
        )
        db.session.add(event)
        db.session.commit()
        return event