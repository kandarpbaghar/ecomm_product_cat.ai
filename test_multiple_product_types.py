#!/usr/bin/env python3
"""
Test script to verify multiple product types in a single query work correctly
"""

import json
import requests
import time

# Configuration
BASE_URL = "http://localhost:5000"

def test_multiple_product_types():
    """Test queries with multiple product types"""
    
    test_cases = [
        {
            "query": "show me shirts and pants below 1000",
            "expected_types": ["shirt", "pant", "jean", "trouser"],
            "max_price": 1000
        },
        {
            "query": "I want shoes and jackets under $500",
            "expected_types": ["shoe", "sneaker", "boot", "jacket", "coat", "blazer"],
            "max_price": 500
        },
        {
            "query": "find me dresses and shirts below $100",
            "expected_types": ["dress", "gown", "shirt", "blouse", "top"],
            "max_price": 100
        },
        {
            "query": "show pants, shoes, and shirts under 750",
            "expected_types": ["pant", "jean", "shoe", "sneaker", "shirt", "blouse"],
            "max_price": 750
        }
    ]
    
    for test in test_cases:
        print(f"\n{'='*70}")
        print(f"Testing: {test['query']}")
        print(f"Expected product types: {', '.join(test['expected_types'][:3])}...")
        print(f"Max price: ${test['max_price']}")
        print('-'*70)
        
        session_id = f"test-multi-{int(time.time())}"
        
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
        
        print(f"\nAgent response: {data.get('response', '')}")
        print(f"Total products found: {len(products)}")
        
        if products:
            # Categorize products by type
            product_categories = {}
            price_violations = []
            
            for product in products:
                title_lower = product.get('title', '').lower()
                price = product.get('price', 0)
                
                # Check price constraint
                if price and price > test['max_price']:
                    price_violations.append((product.get('title'), price))
                
                # Categorize by type
                categorized = False
                for expected_type in test['expected_types']:
                    if expected_type in title_lower:
                        if expected_type not in product_categories:
                            product_categories[expected_type] = []
                        product_categories[expected_type].append(product)
                        categorized = True
                        break
                
                if not categorized:
                    if 'other' not in product_categories:
                        product_categories['other'] = []
                    product_categories['other'].append(product)
            
            # Show results by category
            print("\nProducts by type:")
            for category, items in product_categories.items():
                if category != 'other':
                    print(f"  {category.capitalize()}: {len(items)} products")
                    for item in items[:2]:  # Show first 2 of each type
                        print(f"    - {item.get('title')} - ${item.get('price')}")
            
            # Show unexpected products
            if 'other' in product_categories:
                print(f"\n❌ Unexpected product types: {len(product_categories['other'])} products")
                for item in product_categories['other'][:3]:
                    print(f"    - {item.get('title')} - ${item.get('price')}")
            
            # Check price violations
            if price_violations:
                print(f"\n❌ Products over ${test['max_price']}:")
                for title, price in price_violations[:3]:
                    print(f"    - {title}: ${price}")
            else:
                print(f"\n✅ All products are under ${test['max_price']}")
            
            # Summary
            expected_types_found = [t for t in test['expected_types'] if t in product_categories]
            if len(expected_types_found) >= 2:  # At least 2 different types found
                print(f"\n✅ SUCCESS: Found multiple product types as requested")
            else:
                print(f"\n❌ FAIL: Only found {len(expected_types_found)} product type(s)")
                
        else:
            print("❌ No products found!")
        
        # Clean up
        requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")
        time.sleep(0.5)

def test_specific_shirts_and_pants():
    """Specific test for shirts and pants below 1000"""
    
    print("\n" + "="*70)
    print("SPECIFIC TEST: Shirts and pants below 1000")
    print("="*70)
    
    session_id = "test-shirts-pants-specific"
    
    chat_data = {
        "message": "show me shirts and pants below 1000",
        "session_id": session_id
    }
    
    response = requests.post(f"{BASE_URL}/api/agent/chat", json=chat_data)
    
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        
        print(f"\nAgent response: {data.get('response', '')}")
        print(f"Total products: {len(products)}")
        
        # Count shirts and pants
        shirts = []
        pants = []
        other = []
        
        for product in products:
            title_lower = product.get('title', '').lower()
            
            if any(word in title_lower for word in ['shirt', 'blouse', 'top', 'tee', 't-shirt']):
                shirts.append(product)
            elif any(word in title_lower for word in ['pant', 'jean', 'trouser', 'slack', 'legging']):
                pants.append(product)
            else:
                other.append(product)
        
        print(f"\n✅ Shirts found: {len(shirts)}")
        for product in shirts[:5]:
            print(f"   - {product.get('title')}: ${product.get('price')}")
        
        print(f"\n✅ Pants found: {len(pants)}")
        for product in pants[:5]:
            print(f"   - {product.get('title')}: ${product.get('price')}")
        
        if other:
            print(f"\n❌ Other products found: {len(other)}")
            for product in other[:3]:
                print(f"   - {product.get('title')}: ${product.get('price')}")
        
        # Check if both types are represented
        if shirts and pants:
            print("\n✅ SUCCESS: Both shirts AND pants are included in the results!")
        else:
            missing = []
            if not shirts: missing.append("shirts")
            if not pants: missing.append("pants")
            print(f"\n❌ FAIL: Missing {' and '.join(missing)} in the results!")
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/agent/history/{session_id}")

if __name__ == "__main__":
    print("=== Testing Multiple Product Types in Single Query ===")
    test_multiple_product_types()
    test_specific_shirts_and_pants()
    print("\n=== Tests Complete ===")