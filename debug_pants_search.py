#!/usr/bin/env python3
"""
Debug script to test why pants below 1000 doesn't work correctly
"""

import asyncio
from shopping_agent.agent import ShoppingAgent

async def test_pants_search():
    """Test the pants search functionality"""
    
    # Create agent
    agent = ShoppingAgent()
    
    # Test message
    message = "show pants below 1000"
    session_id = "debug-session"
    
    print(f"Testing message: '{message}'")
    print("-" * 50)
    
    # Analyze intent
    tool_choice, params = await agent._analyze_intent_and_choose_tool(message)
    
    print(f"Tool choice: {tool_choice}")
    print(f"Parameters: {params}")
    print("-" * 50)
    
    # If filter_products was chosen, let's see what happens
    if tool_choice == "filter_products":
        # Check if product_type_filter is in params
        product_type_filter = params.get("product_type_filter")
        print(f"Product type filter: {product_type_filter}")
        
        # Remove product_type_filter before calling filter_products
        if "product_type_filter" in params:
            product_type_filter = params.pop("product_type_filter")
        
        # Import and call filter_products
        from shopping_agent.agent import filter_products
        result = filter_products(**params)
        
        products = result.get('products', []) if result.get('success') else []
        print(f"\nProducts returned by filter_products: {len(products)}")
        
        # Show first few products
        for i, product in enumerate(products[:5]):
            print(f"\nProduct {i+1}:")
            print(f"  Title: {product.get('title')}")
            print(f"  Price: ${product.get('price')}")
            print(f"  Title contains 'pant': {'pant' in product.get('title', '').lower()}")
        
        # Now apply product type filtering
        if product_type_filter and products:
            print(f"\n{'='*50}")
            print(f"Applying product type filter: {product_type_filter}")
            
            product_type_keywords = {
                "shirt": ["shirt", "blouse", "top", "tee", "t-shirt"],
                "pants": ["pants", "jeans", "trousers", "slacks", "leggings"],
                "shoes": ["shoes", "shoe", "sneakers", "boots", "sandals", "heels"],
                "dress": ["dress", "gown", "frock"],
                "jacket": ["jacket", "coat", "blazer", "hoodie", "cardigan"]
            }
            
            keywords = product_type_keywords.get(product_type_filter, [product_type_filter])
            print(f"Keywords to match: {keywords}")
            
            filtered_products = []
            for product in products:
                title_lower = product.get('title', '').lower()
                if any(keyword in title_lower for keyword in keywords):
                    filtered_products.append(product)
                    print(f"\n✓ Matched: {product.get('title')}")
                else:
                    print(f"\n✗ Not matched: {product.get('title')}")
            
            print(f"\nFiltered products: {len(filtered_products)}")
            
            # Show filtered products
            for i, product in enumerate(filtered_products):
                print(f"\nFiltered Product {i+1}:")
                print(f"  Title: {product.get('title')}")
                print(f"  Price: ${product.get('price')}")

if __name__ == "__main__":
    print("=== Debugging Pants Search ===\n")
    asyncio.run(test_pants_search())