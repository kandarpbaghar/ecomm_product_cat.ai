#!/usr/bin/env python3
"""Test Weaviate reindexing to enable vector search"""

import requests
import json

def reindex_products():
    """Trigger Weaviate reindexing"""
    print("Triggering Weaviate reindexing...")
    print("-" * 50)
    
    url = "http://localhost:8082/api/weaviate/reindex"
    
    response = requests.post(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Reindexing successful!")
        print(f"  Total products: {result.get('total_products', 0)}")
        print(f"  Successfully indexed: {result.get('indexed', 0)}")
        print(f"  Failed: {result.get('failed', 0)}")
        
        if result.get('errors'):
            print("\nErrors encountered:")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
    else:
        print(f"✗ Reindexing failed: {response.status_code}")
        print(f"  Error: {response.text}")

def check_weaviate_schema():
    """Check if Weaviate schema exists"""
    print("\nChecking Weaviate schema...")
    print("-" * 50)
    
    # This will be handled through the Flask app's Weaviate service
    # which might use embedded Weaviate
    print("Schema check will be performed during reindexing")

def test_vector_search_after_reindex():
    """Test search after reindexing"""
    print("\nTesting vector search after reindexing...")
    print("-" * 50)
    
    url = "http://localhost:8082/api/search"
    
    # Test text search
    data = {
        'type': 'text',
        'query': 'shirt',
        'limit': '5'
    }
    
    response = requests.post(url, data=data)
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"✓ Vector text search: {len(results)} results")
        
        # Check if any results came from Weaviate
        weaviate_results = [r for r in results if r.get('weaviate_id')]
        if weaviate_results:
            print(f"  {len(weaviate_results)} results from Weaviate vector search")
        else:
            print("  ⚠️  No results from Weaviate - still using database fallback")

def main():
    print("=" * 50)
    print("WEAVIATE REINDEXING TEST")
    print("=" * 50)
    
    # Check server
    try:
        response = requests.get("http://localhost:8082/")
        if response.status_code != 200:
            print("Error: Flask server is not responding properly")
            return
    except:
        print("Error: Flask server is not running on port 8082")
        return
    
    print("Flask server is running ✓\n")
    
    # Reindex products
    reindex_products()
    
    # Wait a moment for indexing to complete
    import time
    print("\nWaiting for indexing to complete...")
    time.sleep(2)
    
    # Test search
    test_vector_search_after_reindex()
    
    print("\n" + "=" * 50)
    print("NEXT STEPS:")
    print("=" * 50)
    print("\n1. If reindexing succeeded but searches still use fallback:")
    print("   - Weaviate might need to be properly configured")
    print("   - Check Flask console for Weaviate connection errors")
    print("\n2. To enable proper vector search:")
    print("   - Install and run Weaviate locally")
    print("   - Or use Weaviate Cloud Services")
    print("\n3. The combined text+image search will work best with")
    print("   proper vector search enabled through Weaviate")

if __name__ == "__main__":
    main()