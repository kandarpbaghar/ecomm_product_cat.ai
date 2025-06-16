"""
Shopping Agent Blueprint
Handles chat interface and API endpoints for the shopping assistant
"""

from flask import Blueprint, request, jsonify, render_template, session
from flask_restful import Api, Resource
import asyncio
import json
import uuid
from datetime import datetime
import base64

shopping_agent_bp = Blueprint('shopping_agent', __name__)
api = Api(shopping_agent_bp)

# Global agent instance (in production, use proper state management)
_agent_instance = None

def get_db():
    from database import db
    return db

def get_models():
    from models import AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics
    return AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics

def get_or_create_agent():
    """Get or create the shopping agent instance"""
    global _agent_instance
    
    if _agent_instance is None:
        try:
            print("Attempting to import ShoppingAgentFactory...")
            from shopping_agent.agent import ShoppingAgentFactory
            print("ShoppingAgentFactory imported successfully")
            
            # Get current configuration
            AgentConfig, _, _, _ = get_models()
            config = AgentConfig.get_current_config()
            
            if not config:
                print("No config found, creating default config...")
                # Create default config
                config = AgentConfig(
                    llm_provider='openai',
                    llm_model='gpt-4-turbo-preview'
                )
                db = get_db()
                db.session.add(config)
                db.session.commit()
                print("Default config created")
            
            # Create agent from config
            config_dict = {
                'llm_provider': config.llm_provider,
                'llm_model': config.llm_model,
                'openai_api_key': config.openai_api_key,
                'anthropic_api_key': config.anthropic_api_key,
                'google_api_key': config.google_api_key,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens
            }
            print(f"Creating agent with config: {config_dict}")
            
            try:
                _agent_instance = ShoppingAgentFactory.create_agent(config_dict)
                print(f"Agent created successfully: {_agent_instance}")
            except ValueError as e:
                # Agent not configured properly
                print(f"ValueError creating agent: {e}")
                return None
        except ImportError as e:
            # ADK/MCP not installed
            print(f"ImportError - Shopping agent dependencies not available: {e}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            # Other errors during agent creation
            print(f"Exception creating shopping agent: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return _agent_instance


# Page Routes
@shopping_agent_bp.route('/agent')
def agent_chat():
    """Render the chat interface"""
    # Generate or get session ID
    if 'agent_session_id' not in session:
        session['agent_session_id'] = str(uuid.uuid4())
    
    return render_template('shopping_agent.html', session_id=session['agent_session_id'])

@shopping_agent_bp.route('/agent/settings')
def agent_settings():
    """Render the settings page"""
    return render_template('agent_settings.html')


# API Resources
class ChatResource(Resource):
    def post(self):
        """Handle chat messages"""
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', str(uuid.uuid4()))
        image_data = data.get('image')  # Base64 encoded image
        
        # Get or create agent
        agent = get_or_create_agent()
        if not agent:
            return {
                'success': False,
                'error': 'Shopping assistant dependencies not available. The required modules (adk, mcp) are not installed or configured properly.',
                'response': 'I apologize, but I\'m not properly set up yet. The shopping assistant requires additional dependencies to be installed. Please contact your administrator.'
            }, 503
        
        # Log analytics event
        AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics = get_models()
        AgentAnalytics.log_event(session_id, 'message_sent', {
            'has_image': bool(image_data),
            'message_length': len(message)
        })
        
        # Process message asynchronously
        try:
            print(f"Processing message: {message}")
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                agent.process_message(
                    message=message,
                    session_id=session_id,
                    image_data=image_data
                )
            )
            print(f"Agent response: {response}")
            
            # Save conversation to database
            db = get_db()
            
            # Save user message
            user_msg = AgentConversation(
                session_id=session_id,
                role='user',
                content=message,
                message_metadata=json.dumps({'has_image': bool(image_data)})
            )
            db.session.add(user_msg)
            
            # Save assistant response
            assistant_msg = AgentConversation(
                session_id=session_id,
                role='assistant',
                content=response['response'],
                message_metadata=json.dumps({
                    'products_shown': len(response.get('products', [])),
                    'products': response.get('products', []),  # Store complete product data
                    'suggestions': response.get('suggestions', [])
                })
            )
            db.session.add(assistant_msg)
            db.session.commit()
            
            # Track product interactions
            for idx, product in enumerate(response.get('products', [])):
                interaction = AgentProductInteraction(
                    conversation_id=assistant_msg.id,
                    product_id=product.get('id'),
                    interaction_type='shown',
                    position=idx + 1
                )
                db.session.add(interaction)
            
            db.session.commit()
            
            # Log response analytics
            AgentAnalytics.log_event(session_id, 'message_received', {
                'products_count': len(response.get('products', [])),
                'has_suggestions': bool(response.get('suggestions'))
            })
            
            return response
            
        except Exception as e:
            print(f"Chat error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'I apologize, but I encountered an error. Please try again.'
            }, 500
        finally:
            loop.close()


class ImageUploadResource(Resource):
    def post(self):
        """Handle image uploads for visual search"""
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400
        
        file = request.files['image']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        # Read and encode image
        try:
            image_data = file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            return {
                'success': True,
                'image_data': image_base64,
                'filename': file.filename
            }
        except Exception as e:
            return {'error': f'Failed to process image: {str(e)}'}, 500


class ConversationHistoryResource(Resource):
    def get(self, session_id):
        """Get conversation history"""
        AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics = get_models()
        
        # Get history from database
        history = AgentConversation.get_session_history(session_id)
        
        return {
            'success': True,
            'session_id': session_id,
            'messages': [msg.to_dict() for msg in reversed(history)]
        }
    
    def delete(self, session_id):
        """Clear conversation history"""
        db = get_db()
        AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics = get_models()
        
        # Delete conversations
        AgentConversation.query.filter_by(session_id=session_id).delete()
        db.session.commit()
        
        # Clear agent's in-memory history
        agent = get_or_create_agent()
        if agent:
            agent.clear_session(session_id)
        
        return {'success': True, 'message': 'Conversation history cleared'}


class AgentConfigResource(Resource):
    def get(self):
        """Get current agent configuration"""
        AgentConfig, _, _, _ = get_models()
        config = AgentConfig.get_current_config()
        
        if config:
            return {
                'success': True,
                'config': config.to_dict()
            }
        else:
            return {
                'success': True,
                'config': {
                    'llm_provider': 'openai',
                    'llm_model': 'gpt-4-turbo-preview',
                    'temperature': 0.7,
                    'max_tokens': 500
                }
            }
    
    def post(self):
        """Update agent configuration"""
        global _agent_instance
        
        data = request.get_json()
        db = get_db()
        AgentConfig, _, _, _ = get_models()
        
        # Get or create config
        config = AgentConfig.get_current_config()
        if not config:
            config = AgentConfig()
            db.session.add(config)
        
        # Update fields
        if 'llm_provider' in data:
            config.llm_provider = data['llm_provider']
        if 'llm_model' in data:
            config.llm_model = data['llm_model']
        if 'openai_api_key' in data:
            config.openai_api_key = data['openai_api_key']
        if 'anthropic_api_key' in data:
            config.anthropic_api_key = data['anthropic_api_key']
        if 'google_api_key' in data:
            config.google_api_key = data['google_api_key']
        if 'temperature' in data:
            config.temperature = float(data['temperature'])
        if 'max_tokens' in data:
            config.max_tokens = int(data['max_tokens'])
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Reset agent instance to force recreation with new config
        _agent_instance = None
        
        return {
            'success': True,
            'message': 'Configuration updated successfully',
            'config': config.to_dict()
        }


class AgentModelsResource(Resource):
    def get(self):
        """Get available models for each provider"""
        from shopping_agent.llm_providers import LLMProviderFactory
        
        providers = {}
        for provider in LLMProviderFactory.get_providers():
            providers[provider] = {
                'models': LLMProviderFactory.get_available_models(provider),
                'name': provider.title()
            }
        
        return {
            'success': True,
            'providers': providers
        }


class ProductClickResource(Resource):
    def post(self):
        """Track product clicks/interactions"""
        data = request.get_json()
        db = get_db()
        AgentConfig, AgentConversation, AgentProductInteraction, AgentAnalytics = get_models()
        
        # Log the interaction
        if 'conversation_id' in data:
            interaction = AgentProductInteraction(
                conversation_id=data['conversation_id'],
                product_id=data['product_id'],
                interaction_type='clicked',
                position=data.get('position', 0)
            )
            db.session.add(interaction)
            db.session.commit()
        
        # Log analytics
        AgentAnalytics.log_event(
            session_id=data.get('session_id', 'unknown'),
            event_type='product_click',
            event_data={
                'product_id': data['product_id'],
                'position': data.get('position', 0)
            }
        )
        
        return {'success': True}


# Register API endpoints
api.add_resource(ChatResource, '/api/agent/chat')
api.add_resource(ImageUploadResource, '/api/agent/upload')
api.add_resource(ConversationHistoryResource, '/api/agent/history/<string:session_id>')
api.add_resource(AgentConfigResource, '/api/agent/config')
api.add_resource(AgentModelsResource, '/api/agent/models')
api.add_resource(ProductClickResource, '/api/agent/product-click')