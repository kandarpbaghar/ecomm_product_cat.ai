#!/usr/bin/env python3
"""
Test script for hybrid context extraction in shopping agent
"""

import asyncio
import os
from shopping_agent.agent import ShoppingAgent

async def test_context_retention():
    """Test that context is retained across queries"""
    print("Testing Hybrid Context Extraction")
    print("=" * 50)
    
    # Initialize agent
    agent = ShoppingAgent()
    session_id = "test_session_123"
    
    # Test cases
    test_cases = [
        # Simple cases (should use fast path)
        {
            "query": "show me pants",
            "expected_path": "fast",
            "description": "Simple product search"
        },
        {
            "query": "find products under $100",
            "expected_path": "fast",
            "description": "Simple price filter"
        },
        
        # Complex cases (should use LLM)
        {
            "query": "show me above 600",
            "expected_path": "llm",
            "description": "Context-dependent price filter (should remember pants)"
        },
        {
            "query": "how about in blue color",
            "expected_path": "llm",
            "description": "Color filter with context"
        },
        {
            "query": "what about Nike brand",
            "expected_path": "llm",
            "description": "Brand filter with context"
        },
        {
            "query": "show me similar but cheaper",
            "expected_path": "llm",
            "description": "Complex contextual request"
        }
    ]
    
    # Clear previous session
    agent.clear_session(session_id)
    
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test['description']}")
        print(f"Query: {test['query']}")
        
        try:
            # Process message
            result = await agent.process_message(
                message=test['query'],
                session_id=session_id
            )
            
            print(f"Success: {result.get('success', False)}")
            print(f"Response: {result.get('response', 'No response')[:100]}...")
            
            if result.get('products'):
                print(f"Products found: {len(result['products'])}")
                # Show first product details
                if result['products']:
                    first_product = result['products'][0]
                    print(f"  - {first_product.get('title', 'No title')}: ${first_product.get('price', 'N/A')}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    # Check for required environment variable
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_API_KEY='your-api-key'")
        exit(1)
    
    asyncio.run(test_context_retention())