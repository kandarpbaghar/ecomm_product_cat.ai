#!/usr/bin/env python3
"""
Test script to verify that clear chat functionality clears both database and in-memory data
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"
SESSION_ID = f"test-clear-{int(time.time())}"

def test_clear_session():
    """Test that clear chat properly clears both database and in-memory data"""
    
    print(f"Testing with session ID: {SESSION_ID}")
    
    # 1. Send a few messages to build up conversation history
    print("\n1. Building conversation history...")
    messages = [
        "Show me shirts",
        "How about something under $30?",
        "Do you have any Nike products?"
    ]
    
    for i, message in enumerate(messages):
        chat_data = {
            "message": message,
            "session_id": SESSION_ID
        }
        
        response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
        if response.status_code == 200:
            print(f"   - Message {i+1} sent successfully")
        else:
            print(f"   - Error sending message {i+1}: {response.status_code}")
            return
        
        time.sleep(0.5)  # Small delay between messages
    
    # 2. Verify conversation history exists
    print("\n2. Verifying conversation history exists...")
    history_response = requests.get(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    
    if history_response.status_code != 200:
        print(f"   - Error retrieving history: {history_response.status_code}")
        return
    
    history_data = history_response.json()
    messages_before = history_data.get('messages', [])
    print(f"   - Messages in history: {len(messages_before)}")
    print(f"   - User messages: {len([m for m in messages_before if m['role'] == 'user'])}")
    print(f"   - Assistant messages: {len([m for m in messages_before if m['role'] == 'assistant'])}")
    
    # 3. Clear the chat
    print("\n3. Clearing chat history...")
    clear_response = requests.delete(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    
    if clear_response.status_code != 200:
        print(f"   - Error clearing history: {clear_response.status_code}")
        print(f"   - Response: {clear_response.text}")
        return
    
    print("   - Chat cleared successfully")
    
    # 4. Verify history is cleared in database
    print("\n4. Verifying database is cleared...")
    history_response = requests.get(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    
    if history_response.status_code != 200:
        print(f"   - Error retrieving history: {history_response.status_code}")
        return
    
    history_data = history_response.json()
    messages_after = history_data.get('messages', [])
    print(f"   - Messages in history after clear: {len(messages_after)}")
    
    if len(messages_after) == 0:
        print("   ✅ Database cleared successfully!")
    else:
        print("   ❌ Database still contains messages!")
        return
    
    # 5. Test that in-memory data is also cleared by sending a new message
    print("\n5. Testing in-memory data is cleared...")
    
    # Send a message that references previous context
    chat_data = {
        "message": "Show me more like those",  # This would fail if context is maintained
        "session_id": SESSION_ID
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
    if response.status_code == 200:
        response_data = response.json()
        response_text = response_data.get('response', '').lower()
        
        # Check if the response indicates the agent doesn't have context
        if any(phrase in response_text for phrase in ["what products", "what would you like", "could you specify", "i'd be happy to help you find"]):
            print("   ✅ In-memory data cleared successfully!")
            print(f"   - Agent response: {response_data.get('response', '')[:100]}...")
        else:
            print("   ⚠️  Agent might still have context")
            print(f"   - Agent response: {response_data.get('response', '')[:100]}...")
    else:
        print(f"   - Error sending test message: {response.status_code}")
    
    # 6. Clean up
    print("\n6. Final cleanup...")
    requests.delete(f"{BASE_URL}/api/agent/history/{SESSION_ID}")
    print("   - Test session cleaned up")

if __name__ == "__main__":
    print("=== Testing Clear Chat Functionality ===")
    test_clear_session()
    print("\n=== Test Complete ===")