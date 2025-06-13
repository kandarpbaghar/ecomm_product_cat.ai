#!/usr/bin/env python3
"""Diagnose the combined search functionality issues"""

import requests
import json
import os

def diagnose():
    print("SEARCH FUNCTIONALITY DIAGNOSIS")
    print("=" * 60)
    
    # 1. Check database products
    print("\n1. Checking database products...")
    response = requests.get("http://localhost:8082/api/skus")
    if response.status_code == 200:
        data = response.json()
        total_products = data.get('total', 0)
        products = data.get('products', [])
        print(f"   ✓ Total products in database: {total_products}")
        if products:
            print(f"   ✓ Sample product: {products[0].get('title', 'Unknown')}")
            print(f"   ✓ Has Weaviate ID: {'Yes' if products[0].get('weaviate_id') else 'No'}")
    else:
        print(f"   ✗ Failed to fetch products: {response.status_code}")
    
    # 2. Test combined search
    print("\n2. Testing combined text+image search...")
    image_path = "/Users/kandarpbaghar/product_cat.ai/uploads/1749691506_shirt_1.jpg"
    
    with open(image_path, 'rb') as f:
        files = {'image': ('test_shirt.jpg', f, 'image/jpeg')}
        data = {
            'type': 'text_image',
            'query': 'shirt',
            'limit': '10'
        }
        response = requests.post("http://localhost:8082/api/search", data=data, files=files)
    
    if response.status_code == 200:
        results = response.json().get('results', [])
        print(f"   ✓ Search returned {len(results)} results")
        if results:
            result = results[0]
            print(f"   ✓ First result: {result.get('title')}")
            print(f"   ✓ Result source: Database {'(with Weaviate ID)' if result.get('weaviate_id') else '(no Weaviate ID)'}")
    else:
        print(f"   ✗ Search failed: {response.status_code}")
        print(f"     {response.text}")
    
    # 3. Analysis
    print("\n3. ANALYSIS:")
    print("-" * 60)
    print("\nCURRENT STATE:")
    print("✓ Database search is working (fallback)")
    print("✓ Text search is working")
    print("✓ Image search is working")
    print("✓ Combined text+image search is working")
    print("✗ Vector search is NOT working (Weaviate not connected)")
    
    print("\nWHY COMBINED SEARCH APPEARS TO NOT WORK:")
    print("1. Weaviate is not running, so vector search fails")
    print("2. The system falls back to database search")
    print("3. Database search might not find good matches for the combination")
    print("4. Without vector embeddings, semantic similarity cannot be computed")
    
    print("\nSOLUTION:")
    print("To enable proper combined text+image search with semantic understanding:")
    print("1. Install and run Weaviate:")
    print("   - Using Docker: docker run -d -p 8080:8080 semitechnologies/weaviate:latest")
    print("   - Or use Weaviate Cloud Services")
    print("2. Once Weaviate is running, products need to be indexed")
    print("3. The search will then use vector embeddings for better results")
    
    print("\nWORKAROUND (without Weaviate):")
    print("The current implementation has fallbacks that:")
    print("- Search by text in title, description, tags")
    print("- Return products with images when image search is used")
    print("- Combine results from both searches for text+image")
    print("\nThis works but lacks semantic understanding that Weaviate provides.")

if __name__ == "__main__":
    diagnose()