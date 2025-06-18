import requests
from typing import List, Dict, Optional
from datetime import datetime
import os

class ShopifyService:
    def __init__(self, store_url: str = None, access_token: str = None, api_version: str = None):
        # First check parameters, then environment variables, then database
        self.store_url = store_url or os.getenv('SHOPIFY_STORE_URL')
        self.access_token = access_token or os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.api_version = api_version or os.getenv('SHOPIFY_API_VERSION', '2024-01')
        
        # If not found in env vars, try to load from database
        if not self.store_url or not self.access_token:
            self._load_from_database()
        
        if self.store_url:
            # Remove trailing slash and ensure https
            self.store_url = self.store_url.rstrip('/')
            if not self.store_url.startswith('https://'):
                self.store_url = f"https://{self.store_url}"
            
            self.base_url = f"{self.store_url}/admin/api/{self.api_version}"
        else:
            self.base_url = None
        
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        } if self.access_token else {}
    
    def is_configured(self) -> bool:
        """Check if Shopify service is properly configured"""
        return bool(self.store_url and self.access_token)
    
    def test_connection(self) -> bool:
        """Test connection to Shopify store"""
        if not self.is_configured():
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Shopify connection test failed: {e}")
            return False
    
    def get_products(self, limit: int = 250, page_info: str = None, updated_at_min: str = None) -> Dict:
        """Get products from Shopify with optional date filter for incremental sync
        
        Args:
            limit: Number of products per page (max 250)
            page_info: Pagination cursor
            updated_at_min: ISO 8601 date string to get products updated after this date
            
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
            print(f"Fetching products updated since: {updated_at_min}")
        
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
                
                products = response.json().get('products', [])
                print(f"Fetched {len(products)} products from Shopify")
                
                return {
                    'products': products,
                    'page_info': next_page_info
                }
            else:
                print(f"Error fetching products: {response.status_code} - {response.text}")
                return {'products': [], 'page_info': None}
        except Exception as e:
            print(f"Error fetching products from Shopify: {e}")
            return {'products': [], 'page_info': None}
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get a single product from Shopify"""
        if not self.is_configured():
            return None
        
        try:
            response = requests.get(
                f"{self.base_url}/products/{product_id}.json",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get('product')
            else:
                print(f"Error fetching product {product_id}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching product from Shopify: {e}")
            return None
    
    def get_collections(self, limit: int = 250) -> List[Dict]:
        """Get collections (categories) from Shopify"""
        if not self.is_configured():
            return []
        
        try:
            # Get custom collections
            custom_response = requests.get(
                f"{self.base_url}/custom_collections.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            
            # Get smart collections
            smart_response = requests.get(
                f"{self.base_url}/smart_collections.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            
            collections = []
            
            if custom_response.status_code == 200:
                collections.extend(custom_response.json().get('custom_collections', []))
            
            if smart_response.status_code == 200:
                collections.extend(smart_response.json().get('smart_collections', []))
            
            return collections
        except Exception as e:
            print(f"Error fetching collections from Shopify: {e}")
            return []
    
    def get_collection_products(self, collection_id: str, limit: int = 250) -> List[Dict]:
        """Get products in a specific collection"""
        if not self.is_configured():
            return []
        
        try:
            response = requests.get(
                f"{self.base_url}/collections/{collection_id}/products.json",
                headers=self.headers,
                params={'limit': limit},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('products', [])
            else:
                print(f"Error fetching collection products: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching collection products from Shopify: {e}")
            return []
    
    def transform_product(self, shopify_product: Dict) -> Dict:
        """Transform Shopify product to our database format"""
        # Get the first variant as the main product info
        first_variant = shopify_product.get('variants', [{}])[0]
        
        transformed = {
            'shopify_id': str(shopify_product.get('id')),
            'title': shopify_product.get('title', ''),
            'handle': shopify_product.get('handle', ''),
            'description': shopify_product.get('body_html', ''),
            'body_html': shopify_product.get('body_html', ''),
            'vendor': shopify_product.get('vendor', ''),
            'product_type': shopify_product.get('product_type', ''),
            'tags': shopify_product.get('tags', ''),
            'status': 'active' if shopify_product.get('status') == 'active' else 'draft',
            'price': first_variant.get('price'),
            'compare_at_price': first_variant.get('compare_at_price'),
            'sku_code': first_variant.get('sku', ''),
            'barcode': first_variant.get('barcode', ''),
            'weight': first_variant.get('weight'),
            'weight_unit': first_variant.get('weight_unit', 'kg'),
            'track_quantity': first_variant.get('inventory_management') == 'shopify',
            'quantity': first_variant.get('inventory_quantity', 0),
            'published_at': self._parse_datetime(shopify_product.get('published_at')),
            
            # New Shopify fields
            'template_suffix': shopify_product.get('template_suffix', ''),
            'published_scope': shopify_product.get('published_scope', 'web'),
            'admin_graphql_api_id': shopify_product.get('admin_graphql_api_id', ''),
            
            'images': [],
            'variants': [],
            'options': []
        }
        
        # Transform images
        for idx, image in enumerate(shopify_product.get('images', [])):
            transformed['images'].append({
                'shopify_id': str(image.get('id')),
                'url': image.get('src'),
                'alt_text': image.get('alt', ''),
                'position': idx,
                'width': image.get('width'),
                'height': image.get('height'),
                'variant_ids': image.get('variant_ids', []),
                'admin_graphql_api_id': image.get('admin_graphql_api_id', '')
            })
        
        # Transform variants
        for idx, variant in enumerate(shopify_product.get('variants', [])):
            transformed['variants'].append({
                'shopify_id': str(variant.get('id')),
                'title': variant.get('title', ''),
                'price': variant.get('price'),
                'compare_at_price': variant.get('compare_at_price'),
                'sku_code': variant.get('sku', ''),
                'barcode': variant.get('barcode', ''),
                'weight': variant.get('weight'),
                'weight_unit': variant.get('weight_unit', 'kg'),
                'inventory_quantity': variant.get('inventory_quantity', 0),
                
                # New Shopify variant fields
                'inventory_policy': variant.get('inventory_policy', 'deny'),
                'fulfillment_service': variant.get('fulfillment_service', 'manual'),
                'taxable': variant.get('taxable', True),
                'grams': variant.get('grams'),
                'image_id': str(variant.get('image_id')) if variant.get('image_id') else None,
                'inventory_item_id': str(variant.get('inventory_item_id')) if variant.get('inventory_item_id') else None,
                'old_inventory_quantity': variant.get('old_inventory_quantity'),
                'requires_shipping': variant.get('requires_shipping', True),
                'admin_graphql_api_id': variant.get('admin_graphql_api_id', ''),
                
                'option1': variant.get('option1'),
                'option2': variant.get('option2'),
                'option3': variant.get('option3'),
                'position': idx
            })
        
        # Transform options
        for idx, option in enumerate(shopify_product.get('options', [])):
            transformed['options'].append({
                'shopify_id': str(option.get('id')) if option.get('id') else None,
                'name': option.get('name', ''),
                'position': option.get('position', idx),
                'values': option.get('values', [])
            })
        
        return transformed
    
    def transform_collection(self, shopify_collection: Dict) -> Dict:
        """Transform Shopify collection to our category format"""
        return {
            'shopify_id': str(shopify_collection.get('id')),
            'name': shopify_collection.get('title', ''),
            'handle': shopify_collection.get('handle', ''),
            'description': shopify_collection.get('body_html', ''),
            'sort_order': shopify_collection.get('sort_order', 0),
            'meta_title': shopify_collection.get('title', ''),
            'meta_description': shopify_collection.get('body_html', '')
        }
    
    def _extract_page_info(self, link_header: str, rel: str) -> Optional[str]:
        """Extract page_info from Link header"""
        if not link_header:
            return None
        
        links = link_header.split(',')
        for link in links:
            if f'rel="{rel}"' in link:
                # Extract URL from < >
                url_match = link.split('<')[1].split('>')[0]
                # Extract page_info parameter
                if 'page_info=' in url_match:
                    return url_match.split('page_info=')[1].split('&')[0]
        
        return None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse Shopify datetime string to Python datetime object"""
        if not datetime_str:
            return None
        
        try:
            # Shopify uses ISO format with timezone
            # Example: "2025-06-12T04:06:40-04:00"
            from dateutil import parser
            return parser.parse(datetime_str)
        except Exception:
            try:
                # Fallback to basic ISO format
                return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            except Exception:
                return None
    
    def _load_from_database(self):
        """Load configuration from database if not in environment variables"""
        try:
            # Try to import Flask and get current app context
            from flask import current_app, has_app_context
            
            # Check if we're in app context
            if has_app_context() and current_app:
                from database import db
                from sqlalchemy import text
                
                # Check if config table exists
                result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='shopify_config'"))
                table_exists = result.fetchone() is not None
                
                if table_exists:
                    # Get stored config
                    stored_config = db.session.execute(text("SELECT store_url, access_token, api_version FROM shopify_config ORDER BY id DESC LIMIT 1")).fetchone()
                    
                    if stored_config:
                        self.store_url = self.store_url or stored_config[0]
                        self.access_token = self.access_token or stored_config[1]
                        self.api_version = self.api_version or stored_config[2] or '2024-01'
                        
        except Exception as e:
            # Silently fail if we can't load from database
            # This is normal when running outside Flask app context
            pass