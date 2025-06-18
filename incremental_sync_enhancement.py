#!/usr/bin/env python3
"""
Enhancement to add incremental sync capability to Shopify integration
"""

# Add this method to ShopifyService class in services/shopify_service.py

def get_products_incremental(self, updated_at_min: str = None, limit: int = 250, page_info: str = None) -> Dict:
    """Get products from Shopify that were updated after a specific date
    
    Args:
        updated_at_min: ISO 8601 date string (e.g., "2024-01-01T00:00:00Z")
        limit: Number of products per page (max 250)
        page_info: Pagination cursor
        
    Returns:
        Dict with 'products' list and 'page_info' for pagination
    """
    if not self.is_configured():
        return {'products': [], 'page_info': None}
    
    params = {'limit': limit}
    if page_info:
        params['page_info'] = page_info
    if updated_at_min:
        params['updated_at_min'] = updated_at_min
    
    try:
        response = requests.get(
            f"{self.base_url}/products.json",
            headers=self.headers,
            params=params,
            timeout=30
        )
        
        if response.status_code == 200:
            # Extract pagination info from Link header
            link_header = response.headers.get('Link', '')
            next_page_info = self._extract_page_info(link_header, 'next')
            
            return {
                'products': response.json().get('products', []),
                'page_info': next_page_info
            }
        else:
            print(f"Error fetching products: {response.status_code} - {response.text}")
            return {'products': [], 'page_info': None}
    except Exception as e:
        print(f"Error fetching products from Shopify: {e}")
        return {'products': [], 'page_info': None}


# Update the _sync_products method in ShopifySyncResource to support incremental sync:

def _sync_products_incremental(self, sync_log_id, app, test_mode=False):
    """Enhanced sync that supports incremental updates"""
    with app.app_context():
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        
        sync_log = SyncLog.query.get(sync_log_id)
        if not sync_log:
            print(f"Sync log {sync_log_id} not found")
            return
        
        weaviate_service, shopify_service = get_services()
        
        if not shopify_service.is_configured():
            raise Exception("Shopify is not properly configured")
        
        if not test_mode and not shopify_service.test_connection():
            raise Exception("Cannot connect to Shopify")
        
        try:
            # For incremental sync, find the last successful sync
            updated_at_min = None
            if sync_log.sync_type == 'incremental':
                last_sync = SyncLog.query.filter(
                    SyncLog.status == 'completed',
                    SyncLog.sync_type.in_(['full', 'incremental']),
                    SyncLog.id != sync_log_id
                ).order_by(SyncLog.completed_at.desc()).first()
                
                if last_sync and last_sync.completed_at:
                    # Use the completion time of the last sync as the starting point
                    # Subtract 5 minutes to account for any overlap
                    from datetime import timedelta
                    sync_from = last_sync.completed_at - timedelta(minutes=5)
                    updated_at_min = sync_from.strftime('%Y-%m-%dT%H:%M:%SZ')
                    print(f"Incremental sync from: {updated_at_min}")
                else:
                    print("No previous sync found, performing full sync")
                    sync_log.sync_type = 'full'
            
            # Sync collections first (always full sync for collections)
            collections = shopify_service.get_collections()
            
            for collection in collections:
                transformed = shopify_service.transform_collection(collection)
                
                # Create or update category
                category = Category.query.filter_by(shopify_id=transformed['shopify_id']).first()
                if not category:
                    category = Category(**transformed)
                    db.session.add(category)
                else:
                    for key, value in transformed.items():
                        setattr(category, key, value)
            
            db.session.commit()
            
            # Sync products (with incremental support)
            page_info = None
            total_products = 0
            processed_products = 0
            failed_products = 0
            updated_products = 0
            new_products = 0
            
            while True:
                if sync_log.sync_type == 'incremental' and updated_at_min:
                    result = shopify_service.get_products_incremental(
                        updated_at_min=updated_at_min,
                        page_info=page_info
                    )
                else:
                    result = shopify_service.get_products(page_info=page_info)
                
                products = result['products']
                page_info = result['page_info']
                
                if not products:
                    break
                
                total_products += len(products)
                
                for product in products:
                    try:
                        transformed = shopify_service.transform_product(product)
                        
                        # Create or update SKU
                        sku = SKU.query.filter_by(shopify_id=transformed['shopify_id']).first()
                        is_new = sku is None
                        
                        if not sku:
                            sku = SKU()
                            new_products += 1
                        else:
                            updated_products += 1
                        
                        # Update SKU fields
                        for key, value in transformed.items():
                            if key not in ['images', 'variants', 'options']:
                                setattr(sku, key, value)
                        
                        db.session.add(sku)
                        db.session.flush()
                        
                        # Handle images, variants, and options as before...
                        # [Rest of the sync logic remains the same]
                        
                        processed_products += 1
                        
                        # Update sync log progress periodically
                        if processed_products % 10 == 0:
                            sync_log.processed_items = processed_products
                            db.session.commit()
                            
                    except Exception as e:
                        print(f"Error processing product {product.get('id')}: {e}")
                        failed_products += 1
                
                # Don't continue if no more pages
                if not page_info:
                    break
            
            # Update sync log with final results
            sync_log.status = 'completed'
            sync_log.total_items = total_products
            sync_log.processed_items = processed_products
            sync_log.failed_items = failed_products
            sync_log.completed_at = datetime.utcnow()
            
            # Add detailed message for incremental sync
            if sync_log.sync_type == 'incremental':
                sync_log.error_message = f"Incremental sync completed. New: {new_products}, Updated: {updated_products}, Failed: {failed_products}"
            
            db.session.commit()
            
            print(f"Sync completed: Total={total_products}, Processed={processed_products}, Failed={failed_products}")
            if sync_log.sync_type == 'incremental':
                print(f"New products: {new_products}, Updated products: {updated_products}")
                
        except Exception as e:
            print(f"Sync failed: {e}")
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()


# API endpoint to trigger incremental sync:
"""
POST /api/sync/shopify
{
    "sync_type": "incremental"
}

This will:
1. Find the last successful sync
2. Only fetch products updated since that time
3. Update existing products or create new ones
4. Much faster than full sync for regular updates
"""