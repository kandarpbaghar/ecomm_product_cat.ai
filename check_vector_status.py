#!/usr/bin/env python3
"""
Quick Vector Search Status Check

This script quickly checks:
1. How many products are in the database
2. How many are indexed in Weaviate  
3. Whether vector search is working
"""

import requests
import sys

def main():
    print("VECTOR SEARCH STATUS CHECK")
    print("=" * 40)
    
    # Check server
    try:
        response = requests.get("http://localhost:8082/")
        if response.status_code != 200:
            print("✗ Flask server not responding")
            sys.exit(1)
    except:
        print("✗ Flask server not running on port 8082")
        sys.exit(1)
    
    print("✓ Flask server running")
    
    # Get vector stats
    try:
        response = requests.get("http://localhost:8082/api/vector/stats")
        if response.status_code == 200:
            stats = response.json()
            total_skus = stats.get('total_skus', 0)
            indexed_skus = stats.get('indexed_skus', 0)
            last_indexed = stats.get('last_indexed', 'Never')
            
            print(f"✓ Products in database: {total_skus}")
            print(f"✓ Products indexed in Weaviate: {indexed_skus}")
            print(f"✓ Last indexed: {last_indexed}")
            
            if total_skus == 0:
                print("\n⚠️  No products in database")
                print("   Add products first before using vector search")
            elif indexed_skus == 0:
                print("\n❌ NO PRODUCTS INDEXED IN WEAVIATE")
                print("   This is why you see keyword search instead of vector search")
                print("   Run: python fix_vector_search.py")
            elif indexed_skus < total_skus:
                print(f"\n⚠️  Only {indexed_skus}/{total_skus} products indexed")
                print("   Run: python fix_vector_search.py")
            else:
                print(f"\n✅ All {indexed_skus} products are indexed!")
                
                # Test if vector search actually works
                try:
                    data = {'type': 'text', 'query': 'test', 'limit': '1'}
                    search_response = requests.post("http://localhost:8082/api/search", data=data)
                    if search_response.status_code == 200:
                        results = search_response.json().get('results', [])
                        if results:
                            vector_results = [r for r in results if r.get('search_source') == 'vector']
                            if vector_results:
                                print("✅ Vector search is working!")
                            else:
                                print("❌ Vector search still falling back to database")
                                print("   Run: python vector_search_diagnosis.py")
                        else:
                            print("⚠️  Search returned no results (may be normal)")
                    else:
                        print("⚠️  Could not test search functionality")
                except:
                    print("⚠️  Could not test search functionality")
        else:
            print("✗ Could not get vector statistics")
    except Exception as e:
        print(f"✗ Error getting vector stats: {e}")
    
    # Check Weaviate connection
    try:
        response = requests.post("http://localhost:8082/api/vector/test")
        if response.status_code == 200:
            result = response.json()
            if result.get('connected'):
                print("✓ Weaviate connection working")
            else:
                print(f"✗ Weaviate connection failed: {result.get('error')}")
        else:
            print("✗ Weaviate connection test failed")
    except:
        print("✗ Could not test Weaviate connection")
    
    print(f"\n{'='*40}")
    print("QUICK ACTIONS:")
    print("- Full diagnosis: python vector_search_diagnosis.py")
    print("- Fix indexing: python fix_vector_search.py")
    print("- Web interface: http://localhost:8082/vector")

if __name__ == "__main__":
    main()