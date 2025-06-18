# Incremental Sync Guide for Shopify Integration

## Overview

The incremental sync feature allows you to sync only products that have been updated since the last successful sync, making it much faster and more efficient than a full sync.

## How It Works

1. **Tracking Last Sync**: The system records the completion time of each successful sync in the `sync_logs` table.

2. **Finding Changed Products**: When an incremental sync is triggered, it:
   - Finds the most recent successful sync (full or incremental)
   - Uses Shopify's `updated_at_min` parameter to fetch only products updated after that time
   - Subtracts 5 minutes from the last sync time to ensure no updates are missed

3. **Fallback to Full Sync**: If no previous successful sync is found, it automatically falls back to a full sync.

## Usage

### Via Web UI

1. Navigate to the Shopify Management page
2. Click the **"Incremental Sync"** button (blue button with clockwise arrow icon)
3. Confirm the action when prompted
4. Monitor the sync progress in real-time

### Via API

```bash
# Trigger incremental sync
curl -X POST http://localhost:8082/api/sync/shopify \
  -H "Content-Type: application/json" \
  -d '{"sync_type": "incremental"}'

# Response
{
  "message": "Sync started",
  "sync_id": 123
}

# Check sync status
curl http://localhost:8082/api/sync/status/123
```

## Sync Types

1. **Full Sync** (`sync_type: "full"`)
   - Syncs all products from Shopify
   - Use for initial setup or periodic complete refresh
   - Takes longer but ensures complete data consistency

2. **Incremental Sync** (`sync_type: "incremental"`)
   - Only syncs products updated since last sync
   - Much faster for regular updates
   - Ideal for frequent synchronization (hourly, daily)

## Best Practices

1. **Initial Setup**: Run a full sync first to populate your database
2. **Regular Updates**: Use incremental sync for frequent updates (e.g., every hour)
3. **Periodic Full Sync**: Run a full sync weekly or monthly to ensure data integrity
4. **Monitor Sync Logs**: Check the sync history to ensure syncs are completing successfully

## Sync Results

After an incremental sync completes, the sync log will show:
- **New Products**: Products that didn't exist in your database
- **Updated Products**: Existing products that were modified
- **Failed Products**: Products that couldn't be synced (with error details)

Example sync log message:
```
Incremental sync completed. New: 5, Updated: 23, Failed: 0
```

## Technical Details

### Modified Files

1. **`services/shopify_service.py`**
   - Added `updated_at_min` parameter to `get_products()` method
   - Supports date-based filtering for incremental updates

2. **`blueprints/ai_ecomm_cat.py`**
   - Enhanced `_sync_products()` to handle incremental sync logic
   - Tracks new vs updated products
   - Provides detailed sync summary

3. **`templates/shopify_management.html`**
   - Added "Incremental Sync" button to the UI
   - Shows sync type in the sync history

### Database Considerations

- The `sync_logs` table stores sync history with timestamps
- `sync_type` field distinguishes between 'full' and 'incremental' syncs
- `error_message` field contains the sync summary for incremental syncs

## Troubleshooting

1. **Incremental sync performs full sync**: This happens when no previous successful sync is found. Run a full sync first.

2. **Missing products**: If products are missing after incremental sync:
   - Check if they were updated within the sync window
   - Run a full sync to ensure all products are captured

3. **Sync failures**: Check the sync log for error messages and ensure:
   - Shopify credentials are valid
   - API rate limits aren't exceeded
   - Network connectivity is stable

## Example Implementation

```python
# Trigger incremental sync programmatically
import requests

response = requests.post(
    "http://localhost:8082/api/sync/shopify",
    json={"sync_type": "incremental"}
)

if response.status_code == 202:
    sync_id = response.json()['sync_id']
    print(f"Incremental sync started with ID: {sync_id}")
```