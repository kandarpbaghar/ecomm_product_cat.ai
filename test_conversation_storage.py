#!/usr/bin/env python3
"""
Test script to verify that conversation history stores complete product information
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"
SESSION_ID = f"test-session-{int(time.time())}"

def test_conversation_with_products():
    """Test that products are stored in conversation history"""
    
    print(f"Testing with session ID: {SESSION_ID}")
    
    # 1. Send a message that should return products
    chat_data = {
        "message": "Show me shirts under $50",
        "session_id": SESSION_ID
    }
    
    print("\n1. Sending chat message...")
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
    
    if response.status_code != 200:
        print(f"Error: Chat request failed with status {response.status_code}")
        print(response.text)
        return
    
    chat_response = response.json()
    print(f"   - Response received: {chat_response.get('response', '')[:100]}...")
    print(f"   - Products returned: {len(chat_response.get('products', []))}")
    
    if chat_response.get('products'):
        print("   - Sample product:")
        product = chat_response['products'][0]
        print(f"     * ID: {product.get('id')}")
        print(f"     * Title: {product.get('title')}")
        print(f"     * Price: ${product.get('price')}")
    
    # 2. Retrieve conversation history
    print("\n2. Retrieving conversation history...")
    history_response = requests.get(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    
    if history_response.status_code != 200:
        print(f"Error: History request failed with status {history_response.status_code}")
        return
    
    history_data = history_response.json()
    messages = history_data.get('messages', [])
    
    print(f"   - Total messages in history: {len(messages)}")
    
    # 3. Check if products are stored in metadata
    assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
    
    if assistant_messages:
        latest_assistant_msg = assistant_messages[0]  # Messages are reversed, so [0] is the latest
        metadata = latest_assistant_msg.get('metadata', {})
        
        print("\n3. Checking stored metadata:")
        print(f"   - Products shown count: {metadata.get('products_shown', 0)}")
        print(f"   - Products array present: {'products' in metadata}")
        
        if 'products' in metadata:
            stored_products = metadata['products']
            print(f"   - Number of products stored: {len(stored_products)}")
            
            if stored_products:
                print("   - Sample stored product:")
                product = stored_products[0]
                print(f"     * ID: {product.get('id')}")
                print(f"     * Title: {product.get('title')}")
                print(f"     * Price: ${product.get('price')}")
                print(f"     * Images: {len(product.get('images', []))} image(s)")
                
                # Verify complete data is stored
                expected_fields = ['id', 'title', 'description', 'price', 'vendor', 'quantity', 'images']
                missing_fields = [field for field in expected_fields if field not in product]
                
                if missing_fields:
                    print(f"\n   ⚠️  Warning: Missing fields in stored product: {missing_fields}")
                else:
                    print("\n   ✅ Success: All product fields are stored!")
        else:
            print("\n   ❌ Error: Products array not found in metadata!")
    else:
        print("\n   ❌ Error: No assistant messages found in history!")
    
    # 4. Clean up - delete conversation history
    print("\n4. Cleaning up test data...")
    delete_response = requests.delete(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    if delete_response.status_code == 200:
        print("   - Test conversation history deleted")
    else:
        print("   - Warning: Could not delete test conversation")

if __name__ == "__main__":
    print("=== Testing Conversation Storage with Products ===")
    test_conversation_with_products()
    print("\n=== Test Complete ===")