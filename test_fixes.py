#!/usr/bin/env python3
import requests
import time

API_BASE = "http://localhost:8082/api"

def test_html_stripping_and_empty_sku():
    """Test that HTML tags are stripped from description and empty sku_code is handled"""
    
    print("Testing HTML stripping and empty SKU code handling...")
    
    # First create a product with HTML in description and empty sku_code
    test_product = {
        "title": "Test Product HTML and Empty SKU",
        "handle": "test-product-html-empty-sku",
        "description": "<p>This is a test product with <strong>HTML tags</strong> in the description.</p><p>It has multiple paragraphs too!</p>",
        "body_html": "<h1>Product Details</h1><p>This field should keep HTML</p>",
        "price": 99.99,
        "sku_code": "",  # Empty string - should be converted to None
        "barcode": "",
        "vendor": "Test Vendor",
        "product_type": "Test Type",
        "tags": "test, html, empty-sku",
        "quantity": 10
    }
    
    # Create the product
    response = requests.post(f"{API_BASE}/skus", json=test_product)
    if response.status_code != 201:
        print(f"Error creating product: {response.json()}")
        return
    
    created_product = response.json()
    product_id = created_product['id']
    print(f"Created product with ID: {product_id}")
    
    # Now retrieve the product to see how it's returned
    response = requests.get(f"{API_BASE}/skus/{product_id}")
    if response.status_code != 200:
        print(f"Error retrieving product: {response.json()}")
        return
    
    retrieved_product = response.json()
    
    # Check the results
    print("\n=== Test Results ===")
    print(f"Original description: {test_product['description']}")
    print(f"Retrieved description: {retrieved_product['description']}")
    print(f"Body HTML preserved: {retrieved_product['body_html']}")
    print(f"SKU code (empty string -> None): '{test_product['sku_code']}' -> {retrieved_product['sku_code']}")
    
    # Test updating with empty sku_code
    print("\n=== Testing Update with Empty SKU ===")
    update_data = {
        "title": "Updated Test Product",
        "sku_code": "",  # Should not cause UNIQUE constraint error
        "description": "<p>Updated description with <em>different</em> HTML tags</p>"
    }
    
    response = requests.put(f"{API_BASE}/skus/{product_id}", json=update_data)
    if response.status_code != 200:
        print(f"Error updating product: {response.json()}")
    else:
        print("Successfully updated product with empty sku_code!")
        updated_product = response.json()
        print(f"Updated title: {updated_product['title']}")
        print(f"Updated description: {updated_product['description']}")
        print(f"Updated sku_code: {updated_product['sku_code']}")
    
    # Clean up
    print("\n=== Cleaning up ===")
    response = requests.delete(f"{API_BASE}/skus/{product_id}")
    if response.status_code == 204:
        print("Test product deleted successfully")
    else:
        print(f"Error deleting product: {response.status_code}")

if __name__ == "__main__":
    test_html_stripping_and_empty_sku()