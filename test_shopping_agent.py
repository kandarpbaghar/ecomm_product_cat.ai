#!/usr/bin/env python3
"""
Test script for the Shopping Agent
This script demonstrates the shopping agent functionality
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_ecomm import create_app
from shopping_agent.agent import ShoppingAgentFactory
from shopping_agent.llm_providers import LLMProviderFactory


async def test_agent():
    """Test the shopping agent with sample queries"""
    
    print("🤖 Shopping Agent Test")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Test configuration
        test_config = {
            'llm_provider': 'openai',  # Change this to test different providers
            'llm_model': 'gpt-3.5-turbo',
            'openai_api_key': 'your-api-key-here',  # Replace with actual key
            'temperature': 0.7,
            'max_tokens': 500
        }
        
        print(f"Provider: {test_config['llm_provider']}")
        print(f"Model: {test_config['llm_model']}")
        print()
        
        try:
            # Create agent
            print("Creating shopping agent...")
            agent = ShoppingAgentFactory.create_agent(test_config)
            print("✅ Agent created successfully!")
            
            # Test queries
            test_queries = [
                "I'm looking for running shoes under $100",
                "Show me blue shirts",
                "What are your best selling products?",
                "I need a gift for my friend who likes tech gadgets"
            ]
            
            session_id = "test_session_123"
            
            for i, query in enumerate(test_queries, 1):
                print(f"\n🔍 Test Query {i}: {query}")
                print("-" * 40)
                
                try:
                    response = await agent.process_message(
                        message=query,
                        session_id=session_id
                    )
                    
                    if response['success']:
                        print(f"✅ Response: {response['response']}")
                        print(f"📦 Products found: {len(response.get('products', []))}")
                        
                        if response.get('suggestions'):
                            print(f"💡 Suggestions: {', '.join(response['suggestions'])}")
                    else:
                        print(f"❌ Error: {response.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Query failed: {str(e)}")
                
                # Small delay between queries
                await asyncio.sleep(1)
            
            print(f"\n🏁 Test completed!")
            
        except Exception as e:
            print(f"❌ Failed to create agent: {str(e)}")
            print("Make sure you have:")
            print("1. Installed all required packages")
            print("2. Set up a valid API key")
            print("3. Configured the database")


def test_providers():
    """Test which LLM providers are available"""
    print("\n🔌 Available LLM Providers")
    print("=" * 30)
    
    providers = LLMProviderFactory.get_providers()
    
    for provider in providers:
        models = LLMProviderFactory.get_available_models(provider)
        print(f"📡 {provider.title()}")
        print(f"   Models: {', '.join(models)}")
        
        # Test if provider can be created (without API key)
        try:
            test_provider = LLMProviderFactory.create_provider(provider, "test-key")
            print(f"   Status: ✅ Available")
        except ImportError as e:
            print(f"   Status: ❌ Not installed ({str(e)})")
        except Exception as e:
            print(f"   Status: ⚠️  Available but needs configuration")
        
        print()


def test_mcp_server():
    """Test MCP server tools"""
    print("\n🔧 MCP Server Tools Test")
    print("=" * 30)
    
    # This would test the MCP server in a real scenario
    print("MCP Server tools:")
    tools = [
        "search_products_by_text",
        "search_products_by_image", 
        "get_product_details",
        "filter_products",
        "get_similar_products",
        "get_product_recommendations"
    ]
    
    for tool in tools:
        print(f"   🔨 {tool}")
    
    print("\nTo test MCP server, run:")
    print("python shopping_agent/mcp_server.py")


if __name__ == "__main__":
    print("🛍️  E-commerce Shopping Agent Test Suite")
    print("========================================")
    
    # Test available providers
    test_providers()
    
    # Test MCP server tools
    test_mcp_server()
    
    # Ask user if they want to test the agent
    print("\n" + "="*50)
    test_agent_prompt = input("Do you want to test the shopping agent? (y/N): ").lower()
    
    if test_agent_prompt in ['y', 'yes']:
        print("\n⚠️  Make sure to:")
        print("1. Install required packages: pip install -r requirements.txt")
        print("2. Set up your API key in the test_config above")
        print("3. Have some products in your database")
        print()
        
        proceed = input("Ready to proceed? (y/N): ").lower()
        if proceed in ['y', 'yes']:
            asyncio.run(test_agent())
        else:
            print("Test cancelled.")
    
    print("\n🎉 Test suite completed!")
    print("\nNext steps:")
    print("1. Configure API keys at: http://localhost:5000/agent/settings")
    print("2. Start chatting at: http://localhost:5000/agent")
    print("3. Add products to test search functionality")