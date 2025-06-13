#!/usr/bin/env python3
"""
Comprehensive Vector Search Diagnosis Tool

This script diagnoses why vector search is showing as keyword search instead of vector search.
It checks:
1. Weaviate connection status
2. Products indexed in Weaviate 
3. Vector search functionality
4. Reindexing process

Run this script to identify and fix vector search issues.
"""

import requests
import json
import sys
import os

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")

def print_subsection(title):
    """Print a formatted subsection header"""
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")

def check_flask_server():
    """Check if Flask server is running"""
    print_subsection("Checking Flask Server")
    try:
        response = requests.get("http://localhost:8082/")
        if response.status_code == 200:
            print("✓ Flask server is running")
            return True
        else:
            print(f"✗ Flask server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Flask server: {e}")
        print("  Please start the server with: python ai_ecomm.py")
        return False

def check_database_products():
    """Check products in database"""
    print_subsection("Checking Database Products")
    try:
        response = requests.get("http://localhost:8082/api/skus?per_page=5")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            products = data.get('skus', [])
            print(f"✓ Total products in database: {total}")
            
            if products:
                print("\nSample products:")
                for i, product in enumerate(products[:3]):
                    weaviate_id = product.get('weaviate_id')
                    print(f"  {i+1}. {product.get('title', 'No title')}")
                    print(f"     Weaviate ID: {weaviate_id if weaviate_id else 'NOT INDEXED'}")
                    print(f"     Images: {len(product.get('images', []))}")
                
                # Count indexed vs non-indexed
                indexed_count = sum(1 for p in products if p.get('weaviate_id'))
                print(f"\n✓ Indexed in Weaviate: {indexed_count}/{len(products)} (sample)")
                
                return total, indexed_count > 0
            else:
                print("✗ No products found in database")
                return 0, False
        else:
            print(f"✗ Failed to fetch products: {response.status_code}")
            return 0, False
    except Exception as e:
        print(f"✗ Error checking database: {e}")
        return 0, False

def check_vector_config():
    """Check vector/Weaviate configuration"""
    print_subsection("Checking Vector Configuration")
    try:
        response = requests.get("http://localhost:8082/api/vector/config")
        if response.status_code == 200:
            config = response.json()
            print(f"✓ Weaviate URL: {config.get('weaviate_url')}")
            print(f"✓ Vectorizer: {config.get('vectorizer')}")
            print(f"✓ Configured: {config.get('configured')}")
            return config.get('configured', False)
        else:
            print(f"✗ Failed to get vector config: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error checking vector config: {e}")
        return False

def test_vector_connection():
    """Test Weaviate connection"""
    print_subsection("Testing Weaviate Connection")
    try:
        response = requests.post("http://localhost:8082/api/vector/test")
        if response.status_code == 200:
            result = response.json()
            if result.get('connected'):
                print("✓ Weaviate connection successful")
                print(f"  Schema classes: {result.get('schema_classes', 0)}")
                print(f"  Classes: {result.get('classes', [])}")
                return True
            else:
                print(f"✗ Weaviate connection failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Vector test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing vector connection: {e}")
        return False

def check_vector_stats():
    """Check vector indexing statistics"""
    print_subsection("Checking Vector Index Statistics")
    try:
        response = requests.get("http://localhost:8082/api/vector/stats")
        if response.status_code == 200:
            stats = response.json()
            total_skus = stats.get('total_skus', 0)
            indexed_skus = stats.get('indexed_skus', 0)
            skus_with_images = stats.get('skus_with_images', 0)
            last_indexed = stats.get('last_indexed', 'Never')
            
            print(f"✓ Total SKUs in database: {total_skus}")
            print(f"✓ SKUs indexed in Weaviate: {indexed_skus}")
            print(f"✓ SKUs with images: {skus_with_images}")
            print(f"✓ Last indexed: {last_indexed}")
            
            if indexed_skus == 0:
                print("\n⚠️  NO PRODUCTS ARE INDEXED IN WEAVIATE!")
                print("   This is why you're seeing keyword search instead of vector search.")
                return False, total_skus
            elif indexed_skus < total_skus:
                print(f"\n⚠️  Only {indexed_skus}/{total_skus} products are indexed.")
                print("   Some products may not appear in vector search results.")
                return True, total_skus
            else:
                print(f"\n✓ All {indexed_skus} products are indexed in Weaviate.")
                return True, total_skus
        else:
            print(f"✗ Failed to get vector stats: {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"✗ Error checking vector stats: {e}")
        return False, 0

def test_vector_search():
    """Test if vector search is actually working"""
    print_subsection("Testing Vector Search")
    try:
        # Test text search
        data = {'type': 'text', 'query': 'shirt', 'limit': '3'}
        response = requests.post("http://localhost:8082/api/search", data=data)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            print(f"✓ Text search returned {len(results)} results")
            
            if results:
                # Check search sources
                vector_results = [r for r in results if r.get('search_source') == 'vector']
                db_results = [r for r in results if r.get('search_source') == 'database']
                
                print(f"  Vector search results: {len(vector_results)}")
                print(f"  Database fallback results: {len(db_results)}")
                
                if vector_results:
                    print("✓ Vector search is working!")
                    print(f"  Example: {vector_results[0].get('title')}")
                    return True
                else:
                    print("✗ All results came from database fallback")
                    print("  Vector search is not working properly")
                    return False
            else:
                print("✗ No search results returned")
                return False
        else:
            print(f"✗ Search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing vector search: {e}")
        return False

def run_reindexing():
    """Run the reindexing process"""
    print_subsection("Starting Reindexing Process")
    try:
        response = requests.post("http://localhost:8082/api/vector/reindex")
        if response.status_code == 202:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✓ Reindexing started with task ID: {task_id}")
            
            # Monitor reindexing progress
            print("\nMonitoring reindexing progress...")
            import time
            
            for attempt in range(30):  # Monitor for up to 5 minutes
                time.sleep(10)
                status_response = requests.get(f"http://localhost:8082/api/vector/reindex/status/{task_id}")
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_status = status.get('status')
                    processed = status.get('processed', 0)
                    total = status.get('total', 0)
                    current_op = status.get('current_operation', 'Processing...')
                    
                    print(f"  Status: {current_status} - {processed}/{total} - {current_op}")
                    
                    if current_status == 'completed':
                        print("✓ Reindexing completed successfully!")
                        return True
                    elif current_status == 'failed':
                        error = status.get('error', 'Unknown error')
                        print(f"✗ Reindexing failed: {error}")
                        return False
                else:
                    print(f"✗ Failed to get reindexing status: {status_response.status_code}")
                    return False
            
            print("⚠️  Reindexing is taking longer than expected...")
            return False
            
        else:
            print(f"✗ Failed to start reindexing: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error starting reindexing: {e}")
        return False

def provide_recommendations(has_products, weaviate_connected, vector_search_working, products_indexed):
    """Provide specific recommendations based on diagnosis"""
    print_section("DIAGNOSIS RESULTS & RECOMMENDATIONS")
    
    print("\nDIAGNOSIS SUMMARY:")
    print(f"  Database has products: {'✓' if has_products else '✗'}")
    print(f"  Weaviate connected: {'✓' if weaviate_connected else '✗'}")
    print(f"  Products indexed: {'✓' if products_indexed else '✗'}")
    print(f"  Vector search working: {'✓' if vector_search_working else '✗'}")
    
    print("\nRECOMMENDATIONS:")
    
    if not has_products:
        print("\n1. NO PRODUCTS IN DATABASE")
        print("   - Add products manually via the web interface")
        print("   - Or sync from Shopify if configured")
        print("   - Navigate to http://localhost:8082/skus to add products")
    
    elif not weaviate_connected:
        print("\n1. WEAVIATE CONNECTION ISSUE")
        print("   The connection test failed. This means:")
        print("   a) Weaviate is not running, OR")
        print("   b) Configuration is incorrect")
        print("\n   SOLUTIONS:")
        print("   Option A - Use embedded Weaviate (easiest):")
        print("     - Your app should automatically fall back to embedded Weaviate")
        print("     - Check Flask console for Weaviate initialization messages")
        print("\n   Option B - Install and run Weaviate locally:")
        print("     - Install Docker if not already installed")
        print("     - Run: docker run -d -p 8080:8080 semitechnologies/weaviate:latest")
        print("     - Then rerun this diagnosis")
        print("\n   Option C - Use Weaviate Cloud Services:")
        print("     - Sign up at https://weaviate.io/developers/wcs")
        print("     - Update configuration at http://localhost:8082/vector")
    
    elif not products_indexed:
        print("\n1. PRODUCTS NOT INDEXED IN WEAVIATE")
        print("   This is the most likely reason you're seeing keyword search.")
        print("   Even though Weaviate is connected, no products have been indexed.")
        print("\n   SOLUTION - Reindex all products:")
        print("     - Run reindexing from this script (option below)")
        print("     - Or via web interface: http://localhost:8082/vector")
        print("     - Or via API: POST http://localhost:8082/api/vector/reindex")
    
    elif not vector_search_working:
        print("\n1. VECTOR SEARCH NOT FUNCTIONING PROPERLY")
        print("   Products are indexed but vector search is still falling back to database.")
        print("\n   SOLUTIONS:")
        print("     - Try reindexing products to refresh the vector embeddings")
        print("     - Check Flask console for Weaviate errors during search")
        print("     - Verify Weaviate schema is correct")
    
    else:
        print("\n✓ EVERYTHING LOOKS GOOD!")
        print("   Vector search should be working properly.")
        print("   If you're still seeing keyword search, try:")
        print("   - Clear browser cache and reload")
        print("   - Test search with different queries")
        print("   - Check the search results for 'search_source' field")

def main():
    """Main diagnosis function"""
    print_section("VECTOR SEARCH DIAGNOSIS TOOL")
    print("This tool will diagnose why vector search appears as keyword search")
    print("and provide specific steps to fix the issue.")
    
    # Step 1: Check Flask server
    if not check_flask_server():
        sys.exit(1)
    
    # Step 2: Check database products
    total_products, has_some_indexed = check_database_products()
    has_products = total_products > 0
    
    # Step 3: Check vector configuration
    vector_configured = check_vector_config()
    
    # Step 4: Test Weaviate connection
    weaviate_connected = test_vector_connection()
    
    # Step 5: Check vector statistics
    products_indexed, total_db_products = check_vector_stats()
    
    # Step 6: Test actual vector search
    vector_search_working = False
    if weaviate_connected and products_indexed:
        vector_search_working = test_vector_search()
    
    # Step 7: Provide recommendations
    provide_recommendations(has_products, weaviate_connected, vector_search_working, products_indexed)
    
    # Step 8: Offer to run reindexing if needed
    if has_products and weaviate_connected and not products_indexed:
        print(f"\n{'='*60}")
        print("REINDEXING OPTION")
        print(f"{'='*60}")
        print(f"\nYou have {total_db_products} products that need to be indexed.")
        response = input("\nWould you like to start reindexing now? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            success = run_reindexing()
            if success:
                print("\n✓ Reindexing completed! Vector search should now work.")
                print("  Try searching again in the web interface.")
            else:
                print("\n✗ Reindexing failed. Check Flask console for errors.")
        else:
            print("\nTo reindex later:")
            print("  - Use this script again")
            print("  - Or navigate to http://localhost:8082/vector")
            print("  - Or POST to http://localhost:8082/api/vector/reindex")
    
    print(f"\n{'='*60}")
    print("DIAGNOSIS COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()