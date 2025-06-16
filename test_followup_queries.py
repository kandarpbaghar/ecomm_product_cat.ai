#!/usr/bin/env python3
"""
Test script to verify follow-up queries with price updates work correctly
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"

def test_followup_price_queries():
    """Test follow-up queries that update price constraints"""
    
    test_cases = [
        {
            "name": "Shirts price increase",
            "initial_query": "show me shirts below 450",
            "followup_query": "how about 550?",
            "expected_product_type": "shirt",
            "expected_max_price": 550
        },
        {
            "name": "Pants price decrease", 
            "initial_query": "find pants under 1000",
            "followup_query": "what about 800?",
            "expected_product_type": "pant",
            "expected_max_price": 800
        },
        {
            "name": "Shoes price change",
            "initial_query": "show shoes below 200", 
            "followup_query": "how about 300?",
            "expected_product_type": "shoe",
            "expected_max_price": 300
        },
        {
            "name": "Simple number followup",
            "initial_query": "I want dresses under $100",
            "followup_query": "150?",
            "expected_product_type": "dress",
            "expected_max_price": 150
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Test: {test['name']}")
        print(f"Initial: {test['initial_query']}")
        print(f"Follow-up: {test['followup_query']}")
        print('-'*70)
        
        session_id = f"test-followup-{int(time.time())}"
        
        # 1. Send initial query
        initial_data = {
            "message": test['initial_query'],
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/agent/chat", json=initial_data)
        
        if response.status_code != 200:
            print(f"❌ Error in initial query: {response.status_code}")
            continue
        
        initial_response = response.json()
        initial_products = initial_response.get('products', [])
        
        print(f"\nInitial response:")
        print(f"  Message: {initial_response.get('response', '')}")
        print(f"  Products: {len(initial_products)}")
        
        # 2. Send follow-up query
        time.sleep(0.5)  # Small delay
        
        followup_data = {
            "message": test['followup_query'],
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/agent/chat", json=followup_data)
        
        if response.status_code != 200:
            print(f"❌ Error in follow-up query: {response.status_code}")
            continue
        
        followup_response = response.json()
        followup_products = followup_response.get('products', [])
        
        print(f"\nFollow-up response:")
        print(f"  Message: {followup_response.get('response', '')}")
        print(f"  Products: {len(followup_products)}")
        
        # 3. Analyze results
        if followup_products:
            # Check product types
            correct_type_count = 0
            price_violations = []
            
            for product in followup_products:
                title_lower = product.get('title', '').lower()
                price = product.get('price', 0)
                
                # Check product type
                if test['expected_product_type'] in title_lower:
                    correct_type_count += 1
                
                # Check price constraint
                if price and price > test['expected_max_price']:
                    price_violations.append((product.get('title'), price))
            
            print(f"\nAnalysis:")
            print(f"  ✅ Correct product type: {correct_type_count}/{len(followup_products)}")
            
            if price_violations:
                print(f"  ❌ Price violations ({len(price_violations)} products over ${test['expected_max_price']}):")
                for title, price in price_violations[:3]:
                    print(f"    - {title}: ${price}")
            else:
                print(f"  ✅ All products under ${test['expected_max_price']}")
            
            # Show sample products
            print(f"\nSample products:")
            for i, product in enumerate(followup_products[:3]):
                print(f"  {i+1}. {product.get('title')} - ${product.get('price')}")
            
            # Success criteria
            has_correct_types = correct_type_count > 0
            has_no_price_violations = len(price_violations) == 0
            has_more_products = len(followup_products) > len(initial_products)
            
            if has_correct_types and has_no_price_violations:
                print(f"\n✅ SUCCESS: Follow-up query worked correctly!")
                if has_more_products:
                    print(f"  📈 Price increase resulted in more products ({len(initial_products)} → {len(followup_products)})")
            else:
                print(f"\n❌ FAIL: Follow-up query has issues")
                
        else:
            print(f"\n❌ No products found in follow-up query")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")
        time.sleep(0.5)

def test_specific_shirts_450_to_550():
    """Specific test matching the user's reported issue"""
    
    print("\n" + "="*70)
    print("SPECIFIC TEST: Shirts below 450 → how about 550?")
    print("="*70)
    
    session_id = "test-shirts-450-550"
    
    # 1. Initial query: shirts below 450
    print("\n1. Sending initial query: 'show me shirts below 450'")
    initial_data = {
        "message": "show me shirts below 450",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=initial_data)
    if response.status_code == 200:
        initial_response = response.json()
        initial_products = initial_response.get('products', [])
        print(f"   Response: {initial_response.get('response', '')}")
        print(f"   Products found: {len(initial_products)}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        return
    
    # 2. Follow-up query: how about 550?
    print("\n2. Sending follow-up query: 'how about 550?'")
    time.sleep(0.5)
    
    followup_data = {
        "message": "how about 550?",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=followup_data)
    if response.status_code == 200:
        followup_response = response.json()
        followup_products = followup_response.get('products', [])
        print(f"   Response: {followup_response.get('response', '')}")
        print(f"   Products found: {len(followup_products)}")
        
        # 3. Check for the $500 shirt
        if followup_products:
            shirts_500_range = []
            for product in followup_products:
                title = product.get('title', '')
                price = product.get('price', 0)
                
                if 'shirt' in title.lower() and 490 <= price <= 510:  # Around $500
                    shirts_500_range.append((title, price))
            
            if shirts_500_range:
                print(f"\n✅ SUCCESS: Found {len(shirts_500_range)} shirt(s) around $500:")
                for title, price in shirts_500_range:
                    print(f"   - {title}: ${price}")
            else:
                print(f"\n❌ No shirts found in the $500 range")
                print(f"Available shirts:")
                for product in followup_products[:5]:
                    if 'shirt' in product.get('title', '').lower():
                        print(f"   - {product.get('title')}: ${product.get('price')}")
        else:
            print(f"\n❌ No products found at all!")
            
    else:
        print(f"   ❌ Error: {response.status_code}")
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")

if __name__ == "__main__":
    print("=== Testing Follow-up Price Queries ===")
    test_followup_price_queries()
    test_specific_shirts_450_to_550()
    print("\n=== Tests Complete ===")