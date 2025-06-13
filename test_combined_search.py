#!/usr/bin/env python3
"""Test script for combined text+image search functionality"""

import requests
import os
import sys
import json

def test_combined_search():
    """Test the combined text+image search API endpoint"""
    
    # API endpoint
    url = "http://localhost:8082/api/search"
    
    # Test data
    test_query = "shirt"  # Text query
    test_image_path = "/Users/kandarpbaghar/product_cat.ai/uploads/1749691506_shirt_1.jpg"
    
    # Check if image exists
    if not os.path.exists(test_image_path):
        print(f"Error: Test image not found at {test_image_path}")
        return
    
    print(f"Testing combined search with:")
    print(f"- Query: '{test_query}'")
    print(f"- Image: {test_image_path}")
    print("-" * 50)
    
    # Prepare the request
    data = {
        'search_type': 'text_image',
        'query': test_query,
        'limit': '10'
    }
    
    # Open and send the image file
    with open(test_image_path, 'rb') as f:
        files = {'image': ('test_shirt.jpg', f, 'image/jpeg')}
        
        try:
            # Make the request
            print("Sending request to API...")
            response = requests.post(url, data=data, files=files)
            
            # Print response details
            print(f"\nResponse Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            # Parse and print JSON response
            if response.status_code == 200:
                json_response = response.json()
                print(f"\nRaw JSON Response: {json.dumps(json_response, indent=2)}")
                
                # Handle different response formats
                if isinstance(json_response, list):
                    results = json_response
                elif isinstance(json_response, dict):
                    # Check for common response patterns
                    if 'results' in json_response:
                        results = json_response['results']
                    elif 'data' in json_response:
                        results = json_response['data']
                    else:
                        results = [json_response]  # Single result as dict
                else:
                    results = []
                
                print(f"\nProcessed {len(results)} results")
                
                # Print first few results
                if results:
                    for i, result in enumerate(results[:3] if isinstance(results, list) else [results]):
                        print(f"\nResult {i+1}:")
                        print(f"  Product ID: {result.get('product_id')}")
                        print(f"  Title: {result.get('title')}")
                        print(f"  Price: ${result.get('price')}")
                        print(f"  Source: {result.get('_source', 'unknown')}")
                        if '_additional' in result:
                            print(f"  Distance: {result['_additional'].get('distance', 'N/A')}")
                    
                    if len(results) > 3:
                        print(f"\n... and {len(results) - 3} more results")
                    
            else:
                print(f"\nError Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\nError: Could not connect to Flask app. Make sure it's running on port 8082")
        except Exception as e:
            print(f"\nError making request: {e}")
            import traceback
            traceback.print_exc()

def test_server_health():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8082/")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("Combined Text+Image Search Test")
    print("=" * 50)
    
    # Check if server is running
    if not test_server_health():
        print("Error: Flask server is not running on port 8082")
        print("Please start the server first with: python ai_ecomm.py")
        sys.exit(1)
    
    print("Server is running. Starting test...\n")
    test_combined_search()