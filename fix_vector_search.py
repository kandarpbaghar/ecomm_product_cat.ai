#!/usr/bin/env python3
"""
Quick Fix for Vector Search Issues

This script addresses the most common issue: products not being indexed in Weaviate.
It will automatically reindex all products to enable vector search.
"""

import requests
import time
import sys

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:8082/")
        return response.status_code == 200
    except:
        return False

def get_vector_stats():
    """Get current vector indexing statistics"""
    try:
        response = requests.get("http://localhost:8082/api/vector/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def start_reindexing():
    """Start the reindexing process"""
    try:
        response = requests.post("http://localhost:8082/api/vector/reindex")
        if response.status_code == 202:
            return response.json().get('task_id')
        return None
    except:
        return None

def monitor_reindexing(task_id):
    """Monitor reindexing progress"""
    print(f"Monitoring reindexing progress (Task ID: {task_id})")
    print("This may take a few minutes depending on the number of products...")
    print()
    
    for attempt in range(60):  # Monitor for up to 10 minutes
        try:
            response = requests.get(f"http://localhost:8082/api/vector/reindex/status/{task_id}")
            if response.status_code == 200:
                status = response.json()
                current_status = status.get('status')
                processed = status.get('processed', 0)
                total = status.get('total', 0)
                current_op = status.get('current_operation', 'Processing...')
                
                # Show progress
                if total > 0:
                    percent = (processed / total) * 100
                    print(f"\r[{percent:5.1f}%] {processed}/{total} - {current_op[:50]}", end="", flush=True)
                else:
                    print(f"\r{current_status}: {current_op[:50]}", end="", flush=True)
                
                if current_status == 'completed':
                    print(f"\n\n✓ Reindexing completed successfully!")
                    print(f"  Processed {processed} products")
                    return True
                elif current_status == 'failed':
                    error = status.get('error', 'Unknown error')
                    print(f"\n\n✗ Reindexing failed: {error}")
                    return False
            
            time.sleep(10)
            
        except Exception as e:
            print(f"\n✗ Error monitoring reindexing: {e}")
            return False
    
    print(f"\n⚠️  Reindexing is taking longer than expected...")
    print("   Check the web interface at http://localhost:8082/vector for status")
    return False

def test_vector_search():
    """Test if vector search is working after reindexing"""
    print("\nTesting vector search...")
    try:
        data = {'type': 'text', 'query': 'test', 'limit': '1'}
        response = requests.post("http://localhost:8082/api/search", data=data)
        
        if response.status_code == 200:
            results = response.json().get('results', [])
            if results:
                # Check if any results came from vector search
                vector_results = [r for r in results if r.get('search_source') == 'vector']
                if vector_results:
                    print("✓ Vector search is now working!")
                    return True
                else:
                    print("⚠️  Search is still using database fallback")
                    return False
            else:
                print("⚠️  No search results (may be normal if no matching products)")
                return True
        else:
            print(f"✗ Search test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error testing search: {e}")
        return False

def main():
    print("=" * 60)
    print("VECTOR SEARCH QUICK FIX")
    print("=" * 60)
    print("This will reindex all products to enable vector search.\n")
    
    # Check server
    if not check_server():
        print("✗ Flask server is not running on port 8082")
        print("  Please start the server first with: python ai_ecomm.py")
        sys.exit(1)
    
    print("✓ Flask server is running")
    
    # Get current stats
    stats = get_vector_stats()
    if stats:
        total_skus = stats.get('total_skus', 0)
        indexed_skus = stats.get('indexed_skus', 0)
        
        print(f"✓ Found {total_skus} products in database")
        print(f"✓ Currently {indexed_skus} products indexed in Weaviate")
        
        if total_skus == 0:
            print("\n✗ No products found in database")
            print("  Please add products first before running vector search")
            sys.exit(1)
        
        if indexed_skus == total_skus:
            print(f"\n✓ All {total_skus} products are already indexed!")
            print("  If vector search is still not working, there may be another issue.")
            
            # Test search anyway
            test_vector_search()
            sys.exit(0)
        
        print(f"\n⚠️  {total_skus - indexed_skus} products need to be indexed")
    else:
        print("⚠️  Could not get vector statistics, proceeding anyway...")
    
    # Confirm with user
    response = input(f"\nProceed with reindexing? (y/n): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Aborted.")
        sys.exit(0)
    
    # Start reindexing
    print("\nStarting reindexing...")
    task_id = start_reindexing()
    
    if not task_id:
        print("✗ Failed to start reindexing")
        print("  Check the Flask console for error messages")
        sys.exit(1)
    
    # Monitor progress
    success = monitor_reindexing(task_id)
    
    if success:
        # Test vector search
        test_vector_search()
        
        print(f"\n{'='*60}")
        print("REINDEXING COMPLETE")
        print(f"{'='*60}")
        print("\nVector search should now be enabled!")
        print("Try searching in the web interface at:")
        print("http://localhost:8082/search")
        print("\nIf you're still seeing keyword search, try:")
        print("1. Clear your browser cache and reload")
        print("2. Run the full diagnosis: python vector_search_diagnosis.py")
    else:
        print(f"\n{'='*60}")
        print("REINDEXING FAILED")
        print(f"{'='*60}")
        print("\nPlease check the Flask console for error messages")
        print("You can also run the full diagnosis: python vector_search_diagnosis.py")

if __name__ == "__main__":
    main()