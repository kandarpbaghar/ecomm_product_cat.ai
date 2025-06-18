#!/usr/bin/env python3
"""
Test script for incremental Shopify sync
"""
import requests
import time
import json

API_BASE = "http://localhost:8082/api"

def test_incremental_sync():
    print("=== Testing Incremental Shopify Sync ===\n")
    
    # First, check sync status to see if there's a previous sync
    print("1. Checking for previous syncs...")
    
    # Get the last sync log to see if there was a previous sync
    # In a real implementation, you might have an endpoint for this
    
    # Trigger incremental sync
    print("\n2. Triggering incremental sync...")
    response = requests.post(
        f"{API_BASE}/sync/shopify",
        json={"sync_type": "incremental"}
    )
    
    if response.status_code == 202:
        sync_data = response.json()
        sync_id = sync_data.get('sync_id')
        print(f"   Sync started successfully! Sync ID: {sync_id}")
        
        # Monitor sync progress
        print("\n3. Monitoring sync progress...")
        while True:
            time.sleep(2)  # Check every 2 seconds
            
            status_response = requests.get(f"{API_BASE}/sync/status/{sync_id}")
            if status_response.status_code == 200:
                status = status_response.json()
                
                print(f"   Status: {status['status']}")
                print(f"   Progress: {status['processed_items']}/{status['total_items']} items")
                
                if status['status'] == 'completed':
                    print(f"\n✅ Sync completed successfully!")
                    print(f"   Total items: {status['total_items']}")
                    print(f"   Processed: {status['processed_items']}")
                    print(f"   Failed: {status['failed_items']}")
                    
                    # For incremental sync, the error_message contains the summary
                    if status.get('error_message') and 'Incremental sync completed' in status['error_message']:
                        print(f"   Summary: {status['error_message']}")
                    
                    break
                elif status['status'] == 'failed':
                    print(f"\n❌ Sync failed!")
                    print(f"   Error: {status.get('error_message', 'Unknown error')}")
                    break
            else:
                print(f"   Failed to get sync status: {status_response.status_code}")
                break
    else:
        print(f"   Failed to start sync: {response.status_code}")
        if response.content:
            print(f"   Error: {response.json()}")

def show_sync_usage():
    print("\n=== How to Use Incremental Sync ===\n")
    print("1. Full Sync (syncs all products):")
    print("   POST /api/sync/shopify")
    print("   { \"sync_type\": \"full\" }")
    print()
    print("2. Incremental Sync (only updated products since last sync):")
    print("   POST /api/sync/shopify")
    print("   { \"sync_type\": \"incremental\" }")
    print()
    print("3. Check Sync Status:")
    print("   GET /api/sync/status/{sync_id}")
    print()
    print("Incremental sync will:")
    print("- Find the last successful sync (full or incremental)")
    print("- Only fetch products updated since that time")
    print("- Be much faster than full sync for regular updates")
    print("- Fall back to full sync if no previous sync exists")
    print()
    print("Best Practice:")
    print("- Run full sync once initially or periodically (e.g., weekly)")
    print("- Run incremental sync frequently (e.g., every hour or daily)")
    print("- This keeps your catalog up-to-date with minimal API calls")

if __name__ == "__main__":
    # First show usage
    show_sync_usage()
    
    # Then run test
    print("\n" + "="*50 + "\n")
    user_input = input("Do you want to run an incremental sync test? (y/n): ")
    if user_input.lower() == 'y':
        test_incremental_sync()
    else:
        print("Test skipped. You can manually trigger sync using the API endpoints shown above.")