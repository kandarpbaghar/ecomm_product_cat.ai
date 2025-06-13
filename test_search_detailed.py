#!/usr/bin/env python3
"""Detailed test for combined text+image search functionality with console output monitoring"""

import requests
import os
import sys
import json
import time

def test_text_search():
    """Test text-only search"""
    print("\n1. Testing TEXT-ONLY search")
    print("-" * 30)
    
    url = "http://localhost:8082/api/search"
    data = {
        'type': 'text',
        'query': 'shirt',
        'limit': '5'
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"✓ Text search successful: {len(results)} results found")
        if results:
            print(f"  First result: {results[0].get('title', 'No title')}")
    else:
        print(f"✗ Text search failed: {response.status_code}")
        print(f"  Error: {response.text}")

def test_image_search():
    """Test image-only search"""
    print("\n2. Testing IMAGE-ONLY search")
    print("-" * 30)
    
    url = "http://localhost:8082/api/search"
    image_path = "/Users/kandarpbaghar/product_cat.ai/uploads/1749691506_shirt_1.jpg"
    
    data = {
        'type': 'image',
        'limit': '5'
    }
    
    with open(image_path, 'rb') as f:
        files = {'image': ('test_shirt.jpg', f, 'image/jpeg')}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"✓ Image search successful: {len(results)} results found")
        if results:
            print(f"  First result: {results[0].get('title', 'No title')}")
    else:
        print(f"✗ Image search failed: {response.status_code}")
        print(f"  Error: {response.text}")

def test_combined_search():
    """Test combined text+image search"""
    print("\n3. Testing COMBINED TEXT+IMAGE search")
    print("-" * 30)
    
    url = "http://localhost:8082/api/search"
    image_path = "/Users/kandarpbaghar/product_cat.ai/uploads/1749691506_shirt_1.jpg"
    
    data = {
        'type': 'text_image',
        'query': 'shirt',
        'limit': '10'
    }
    
    print(f"Query: '{data['query']}'")
    print(f"Image: {os.path.basename(image_path)}")
    
    with open(image_path, 'rb') as f:
        files = {'image': ('test_shirt.jpg', f, 'image/jpeg')}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        json_response = response.json()
        results = json_response.get('results', [])
        print(f"\n✓ Combined search successful: {len(results)} results found")
        
        if results:
            print("\nResults breakdown:")
            for i, result in enumerate(results[:3]):
                print(f"\n  Result {i+1}:")
                print(f"    ID: {result.get('id')}")
                print(f"    Title: {result.get('title')}")
                print(f"    Description: {result.get('description', 'N/A')[:50]}...")
                print(f"    Price: ${result.get('price', 0)}")
                print(f"    Vendor: {result.get('vendor', 'N/A')}")
                print(f"    Tags: {result.get('tags', [])}")
                print(f"    Similarity Score: {result.get('similarity_score', 'N/A')}")
                
                # Check if this came from Weaviate or database fallback
                if result.get('weaviate_id'):
                    print(f"    Source: Weaviate (ID: {result['weaviate_id']})")
                else:
                    print(f"    Source: Database fallback")
        else:
            print("\n⚠️  No results returned. This indicates the search is not working properly.")
            print("\nPossible issues:")
            print("  1. Weaviate is not running or not properly configured")
            print("  2. Products are not indexed in Weaviate")
            print("  3. The search query/image combination has no matches")
            print("  4. There's an error in the search logic")
            
    else:
        print(f"\n✗ Combined search failed: {response.status_code}")
        print(f"  Error: {response.text}")

def check_weaviate_status():
    """Check if Weaviate is running and accessible"""
    print("\n4. Checking Weaviate status")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8080/v1/meta")
        if response.status_code == 200:
            print("✓ Weaviate is running and accessible")
            meta = response.json()
            print(f"  Version: {meta.get('version', 'Unknown')}")
        else:
            print("✗ Weaviate returned error:", response.status_code)
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Weaviate at http://localhost:8080")
        print("  Make sure Weaviate is running")
    except Exception as e:
        print(f"✗ Error checking Weaviate: {e}")

def main():
    print("=" * 50)
    print("COMPREHENSIVE SEARCH FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Check server health
    try:
        response = requests.get("http://localhost:8082/")
        if response.status_code != 200:
            print("Error: Flask server is not responding properly")
            sys.exit(1)
    except:
        print("Error: Flask server is not running on port 8082")
        print("Please start the server first with: python ai_ecomm.py")
        sys.exit(1)
    
    print("Flask server is running ✓")
    
    # Run all tests
    test_text_search()
    time.sleep(1)
    
    test_image_search()
    time.sleep(1)
    
    test_combined_search()
    time.sleep(1)
    
    check_weaviate_status()
    
    print("\n" + "=" * 50)
    print("RECOMMENDATIONS:")
    print("=" * 50)
    print("\n1. Check Flask console output for detailed logs")
    print("2. If searches return no results, try:")
    print("   - Reindexing products in Weaviate: POST /api/weaviate/reindex")
    print("   - Checking if Weaviate is properly configured")
    print("   - Verifying products exist in the database")
    print("\n3. The combined search should use both text and image features")
    print("   to find the most relevant products")

if __name__ == "__main__":
    main()