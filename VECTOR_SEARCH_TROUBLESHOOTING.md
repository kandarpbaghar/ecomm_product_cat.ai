# Vector Search Troubleshooting Guide

## Problem: Seeing "Keyword Search" Instead of "Vector Search"

If your search interface shows "keyword search" instead of "vector search", this means the system is falling back to database search rather than using Weaviate for semantic vector search.

## Quick Diagnosis

Run the quick status check:
```bash
python check_vector_status.py
```

## Most Common Issue: Products Not Indexed

The most common reason for seeing keyword search is that **products haven't been indexed in Weaviate yet**.

### Quick Fix
```bash
python fix_vector_search.py
```

This will automatically reindex all your products in Weaviate.

## Comprehensive Diagnosis

For a detailed analysis of all potential issues:
```bash
python vector_search_diagnosis.py
```

This script will:
1. Check if Flask server is running
2. Verify products exist in database
3. Test Weaviate connection
4. Check indexing status
5. Test vector search functionality
6. Provide specific recommendations
7. Offer to run reindexing if needed

## Manual Steps to Enable Vector Search

### Step 1: Check Current Status
```bash
# Quick status
python check_vector_status.py

# Or check via API
curl http://localhost:8082/api/vector/stats
```

### Step 2: Test Weaviate Connection
```bash
# Via API
curl -X POST http://localhost:8082/api/vector/test

# Or via web interface
open http://localhost:8082/vector
```

### Step 3: Reindex Products (if needed)
```bash
# Via script
python fix_vector_search.py

# Or via API
curl -X POST http://localhost:8082/api/vector/reindex

# Or via web interface
# Navigate to http://localhost:8082/vector and click "Reindex"
```

### Step 4: Monitor Reindexing Progress
```bash
# Get task ID from reindex response, then:
curl http://localhost:8082/api/vector/reindex/status/{task_id}
```

## Common Scenarios and Solutions

### Scenario 1: No Products in Database
**Symptoms:** 
- Total products: 0
- No search results

**Solution:**
1. Add products manually via web interface: http://localhost:8082/skus
2. Or sync from Shopify if configured: http://localhost:8082/sync

### Scenario 2: Weaviate Not Connected
**Symptoms:**
- Vector connection test fails
- Products exist but none are indexed

**Solutions:**

**Option A: Use Embedded Weaviate (Easiest)**
- Your app should automatically use embedded Weaviate
- Check Flask console for initialization messages
- No additional setup required

**Option B: Run Weaviate in Docker**
```bash
# Install Docker if not already installed
# Then run:
docker run -d -p 8080:8080 semitechnologies/weaviate:latest
```

**Option C: Use Weaviate Cloud Services**
1. Sign up at https://weaviate.io/developers/wcs
2. Get your URL and API key
3. Configure at http://localhost:8082/vector

### Scenario 3: Products Not Indexed
**Symptoms:**
- Products exist in database
- Weaviate connected
- But indexed_skus = 0

**Solution:**
```bash
python fix_vector_search.py
```

### Scenario 4: Partial Indexing
**Symptoms:**
- Some products indexed but not all
- Inconsistent search results

**Solution:**
- Clear and reindex all products
- Via web interface: http://localhost:8082/vector → "Clear Index" → "Reindex"

### Scenario 5: Vector Search Still Not Working
**Symptoms:**
- All products indexed
- Weaviate connected
- But search still shows "keyword search"

**Solutions:**
1. Clear browser cache and reload
2. Check Flask console for Weaviate errors during search
3. Run full diagnosis: `python vector_search_diagnosis.py`
4. Try different search queries

## API Endpoints for Troubleshooting

### Check Status
```bash
# Vector statistics
GET /api/vector/stats

# Vector configuration
GET /api/vector/config

# Weaviate connection test
POST /api/vector/test
```

### Manage Indexing
```bash
# Start reindexing
POST /api/vector/reindex

# Check reindexing status
GET /api/vector/reindex/status/{task_id}

# Clear index
POST /api/vector/clear
```

### Test Search
```bash
# Test text search
POST /api/search
Content-Type: application/x-www-form-urlencoded

type=text&query=shirt&limit=5
```

## Web Interface Locations

- **Main search interface:** http://localhost:8082/search
- **Vector configuration:** http://localhost:8082/vector
- **Product management:** http://localhost:8082/skus
- **Shopify sync:** http://localhost:8082/sync

## Expected Behavior After Fix

Once vector search is properly enabled:

1. **Search interface** should show "Vector Search" instead of "Keyword Search"
2. **Search results** should include `search_source: 'vector'` in API responses
3. **Semantic search** should work (e.g., "red shirt" finds products with "crimson top")
4. **Combined text+image search** should provide better, more relevant results
5. **Search speed** may be slightly different (usually faster for semantic queries)

## Still Having Issues?

If vector search is still not working after following these steps:

1. **Check Flask console output** for error messages
2. **Run the comprehensive diagnosis:** `python vector_search_diagnosis.py`
3. **Verify your data:**
   - Do you have products with descriptions and images?
   - Are product titles and descriptions meaningful?
4. **Test with simple queries first** (e.g., "shirt", "blue") before complex ones
5. **Check browser developer tools** for any JavaScript errors

## Performance Notes

- **Initial indexing** can take a few minutes for large product catalogs
- **Search performance** should be good once indexed
- **Memory usage** will be higher with vector embeddings
- **Storage** requirements increase with indexed products

## Development vs Production

### Development (Local)
- Embedded Weaviate works fine for testing
- No external dependencies required
- Data stored locally

### Production
- Consider dedicated Weaviate instance
- Use Weaviate Cloud Services for scalability
- Backup vector indexes regularly
- Monitor indexing performance