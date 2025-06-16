#!/usr/bin/env python3
"""
Test script to verify product type + price filtering works correctly
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"

def test_product_filtering():
    """Test various product type + price combinations"""
    
    test_cases = [
        {"query": "show pants below 1000", "expected_type": "pant"},
        {"query": "show me shirts under $50", "expected_type": "shirt"},
        {"query": "find jeans less than $100", "expected_type": "jean"},
        {"query": "I want shoes under 200", "expected_type": "shoe"},
        {"query": "show me dresses below $150", "expected_type": "dress"},
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['query']}")
        print(f"Expected product type: {test['expected_type']}")
        print('-'*60)
        
        session_id = f"test-filter-{int(time.time())}"
        
        # Send the query
        chat_data = {
            "message": test['query'],
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
        
        if response.status_code != 200:
            print(f"❌ Error: Request failed with status {response.status_code}")
            continue
        
        data = response.json()
        products = data.get('products', [])
        
        print(f"Response: {data.get('response', '')}")
        print(f"Products found: {len(products)}")
        
        if products:
            # Check if products match the expected type
            matching_products = 0
            non_matching_products = []
            
            for product in products:
                title_lower = product.get('title', '').lower()
                if test['expected_type'] in title_lower:
                    matching_products += 1
                else:
                    non_matching_products.append(product.get('title'))
            
            print(f"\n✅ Matching products: {matching_products}/{len(products)}")
            
            if non_matching_products:
                print(f"❌ Non-matching products found:")
                for title in non_matching_products[:5]:  # Show first 5
                    print(f"   - {title}")
            
            # Show sample products
            print("\nSample products:")
            for i, product in enumerate(products[:3]):
                print(f"  {i+1}. {product.get('title')} - ${product.get('price')}")
        else:
            print("❌ No products found!")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")
        time.sleep(0.5)  # Small delay between tests

def test_specific_pants_query():
    """Specifically test the pants below 1000 query"""
    
    print("\n" + "="*60)
    print("SPECIFIC TEST: Pants below 1000")
    print("="*60)
    
    session_id = "test-pants-specific"
    
    chat_data = {
        "message": "show pants below 1000",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        
        print(f"\nAgent response: {data.get('response', '')}")
        print(f"Total products: {len(products)}")
        
        # Check for pants
        pants_found = []
        other_products = []
        
        for product in products:
            title = product.get('title', '')
            price = product.get('price', 0)
            
            if any(word in title.lower() for word in ['pant', 'jean', 'trouser', 'slack', 'legging']):
                pants_found.append((title, price))
            else:
                other_products.append((title, price))
        
        print(f"\n✅ Pants/trousers found: {len(pants_found)}")
        for title, price in pants_found[:10]:  # Show first 10
            print(f"   - {title}: ${price}")
        
        if other_products:
            print(f"\n❌ Other products found: {len(other_products)}")
            for title, price in other_products[:5]:  # Show first 5
                print(f"   - {title}: ${price}")
        
        # Price check
        over_budget = [(t, p) for t, p in (pants_found + other_products) if p and p > 1000]
        if over_budget:
            print(f"\n❌ Products over $1000 found: {len(over_budget)}")
            for title, price in over_budget[:3]:
                print(f"   - {title}: ${price}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")

if __name__ == "__main__":
    print("=== Testing Product Type + Price Filtering ===")
    test_product_filtering()
    test_specific_pants_query()
    print("\n=== Tests Complete ===")