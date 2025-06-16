#!/usr/bin/env python3
"""
Setup script for ADK Shopping Agent
Extracts API keys from existing configuration and sets up ADK environment
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def get_existing_api_keys():
    """Get API keys from existing database configuration"""
    try:
        # Initialize Flask app context
        from ai_ecomm import app
        from models.agent import AgentConfig
        
        with app.app_context():
            config = AgentConfig.get_current_config()
            if config:
                return {
                    'google_api_key': config.google_api_key,
                    'openai_api_key': config.openai_api_key,
                    'anthropic_api_key': config.anthropic_api_key
                }
    except Exception as e:
        print(f"Could not retrieve existing config: {e}")
    
    return {}

def setup_env_file():
    """Setup .env.adk file with existing API keys"""
    existing_keys = get_existing_api_keys()
    
    env_content = """# Google API Key for ADK
# Get your API key from: https://aistudio.google.com/app/apikey
"""
    
    if existing_keys.get('google_api_key'):
        env_content += f"GOOGLE_API_KEY={existing_keys['google_api_key']}\n"
    else:
        env_content += "GOOGLE_API_KEY=your-google-api-key-here\n"
    
    env_content += """
# OpenAI API Key (for image embeddings)
"""
    
    if existing_keys.get('openai_api_key'):
        env_content += f"OPENAI_API_KEY={existing_keys['openai_api_key']}\n"
    else:
        env_content += "OPENAI_API_KEY=your-openai-api-key-here\n"
    
    env_content += """
# Database configuration (for your existing app)
DATABASE_URL=sqlite:///ai_ecomm_cat.db

# Weaviate configuration
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
"""
    
    with open('.env.adk', 'w') as f:
        f.write(env_content)
    
    return existing_keys

def main():
    print("🔧 Setting up ADK Shopping Agent")
    print("=" * 50)
    
    # Setup environment file
    print("📝 Setting up environment configuration...")
    existing_keys = setup_env_file()
    
    if existing_keys.get('google_api_key'):
        print("✅ Found existing Google API key")
    else:
        print("⚠️  No Google API key found - you'll need to add one")
    
    if existing_keys.get('openai_api_key'):
        print("✅ Found existing OpenAI API key")
    else:
        print("⚠️  No OpenAI API key found - you'll need to add one")
    
    print("\n📄 Configuration file created: .env.adk")
    
    if not existing_keys.get('google_api_key'):
        print("\n🔑 To get a Google API key:")
        print("1. Visit: https://aistudio.google.com/app/apikey")
        print("2. Create a new API key")
        print("3. Add it to .env.adk file")
    
    print("\n🚀 Ready to run! Use one of these commands:")
    print("1. python run_adk_agent.py")
    print("2. adk web --agent adk_shopping_agent:agent")
    print("3. adk run --agent adk_shopping_agent:agent")

if __name__ == "__main__":
    main()