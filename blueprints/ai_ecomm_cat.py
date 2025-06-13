from flask import Blueprint, request, jsonify, render_template, current_app
from flask_restful import Api, Resource
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import threading

ai_ecomm_cat_bp = Blueprint('ai_ecomm_cat', __name__)
api = Api(ai_ecomm_cat_bp)

# Initialize services lazily
weaviate_service = None
shopify_service = None

# Global task status storage (use Redis for production)
_task_statuses = {}

def get_services():
    global weaviate_service, shopify_service
    if weaviate_service is None:
        from services.weaviate_service import WeaviateService
        from services.shopify_service import ShopifyService
        weaviate_service = WeaviateService()
        shopify_service = ShopifyService()
    return weaviate_service, shopify_service

def get_db():
    from database import db
    return db

def get_models():
    from models import SKU, Category, SKUImage, SKUVariant, SyncLog
    from models.sku import ProductOption
    return SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption

# Helper functions
def allowed_file(filename):
    from config.config import Config
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Category Resources
class CategoryListResource(Resource):
    def get(self):
        """Get all categories"""
        from config.config import Config
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.ITEMS_PER_PAGE, type=int)
        
        categories = Category.query.paginate(page=page, per_page=per_page)
        
        return {
            'categories': [cat.to_dict() for cat in categories.items],
            'total': categories.total,
            'page': categories.page,
            'pages': categories.pages
        }
    
    def post(self):
        """Create a new category"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        data = request.get_json()
        
        if not data.get('name'):
            return {'error': 'Category name is required'}, 400
        
        category = Category(
            name=data['name'],
            handle=data.get('handle', data['name'].lower().replace(' ', '-')),
            description=data.get('description'),
            parent_id=data.get('parent_id'),
            sort_order=data.get('sort_order', 0),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return category.to_dict(), 201

class CategoryResource(Resource):
    def get(self, category_id):
        """Get a specific category"""
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        category = Category.query.get_or_404(category_id)
        return category.to_dict()
    
    def put(self, category_id):
        """Update a category"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        category.name = data.get('name', category.name)
        category.handle = data.get('handle', category.handle)
        category.description = data.get('description', category.description)
        category.parent_id = data.get('parent_id', category.parent_id)
        category.sort_order = data.get('sort_order', category.sort_order)
        category.is_active = data.get('is_active', category.is_active)
        category.meta_title = data.get('meta_title', category.meta_title)
        category.meta_description = data.get('meta_description', category.meta_description)
        
        db.session.commit()
        
        return category.to_dict()
    
    def delete(self, category_id):
        """Delete a category"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        
        return {'message': 'Category deleted successfully'}, 204

# SKU Resources
class SKUListResource(Resource):
    def get(self):
        """Get all SKUs"""
        from config.config import Config
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', Config.ITEMS_PER_PAGE, type=int)
        category_id = request.args.get('category_id', type=int)
        
        query = SKU.query
        
        if category_id:
            query = query.join(SKU.categories).filter(Category.id == category_id)
        
        skus = query.paginate(page=page, per_page=per_page)
        
        return {
            'skus': [sku.to_dict() for sku in skus.items],
            'total': skus.total,
            'page': skus.page,
            'pages': skus.pages
        }
    
    def post(self):
        """Create a new SKU"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        weaviate_service, shopify_service = get_services()
        
        # Handle both JSON and form data (for image uploads)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Form data with potential file upload
            data = request.form.to_dict()
            image_file = request.files.get('image')
            image_url = data.get('image_url')
        else:
            # JSON data
            data = request.get_json() or {}
            image_file = None
            image_url = data.get('image_url')
        
        if not data.get('title'):
            return {'error': 'SKU title is required'}, 400
        
        sku = SKU(
            title=data['title'],
            handle=data.get('handle', data['title'].lower().replace(' ', '-')),
            description=data.get('description'),
            body_html=data.get('body_html'),
            vendor=data.get('vendor'),
            product_type=data.get('product_type'),
            tags=data.get('tags'),
            price=data.get('price'),
            compare_at_price=data.get('compare_at_price'),
            sku_code=data.get('sku_code'),
            barcode=data.get('barcode'),
            track_quantity=data.get('track_quantity', True),
            quantity=data.get('quantity', 0),
            weight=data.get('weight'),
            weight_unit=data.get('weight_unit', 'kg'),
            meta_title=data.get('meta_title'),
            meta_description=data.get('meta_description')
        )
        
        # Add categories
        category_ids = data.get('category_ids', [])
        if isinstance(category_ids, str):
            category_ids = [category_ids]
        if category_ids:
            try:
                category_ids = [int(cid) for cid in category_ids if cid]
                categories = Category.query.filter(Category.id.in_(category_ids)).all()
                sku.categories = categories
            except (ValueError, TypeError):
                pass
        
        db.session.add(sku)
        db.session.flush()  # Get the SKU ID
        
        # Handle image upload
        if image_file and allowed_file(image_file.filename):
            try:
                # Save uploaded file
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(image_file.filename)
                timestamp = str(int(datetime.utcnow().timestamp()))
                filename = f"{timestamp}_{filename}"
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, filename)
                image_file.save(file_path)
                
                # Create database record
                sku_image = SKUImage(
                    sku_id=sku.id,
                    url=f"/uploads/{filename}",
                    alt_text=sku.title,
                    position=0
                )
                db.session.add(sku_image)
                
            except Exception as e:
                print(f"Error saving uploaded image: {e}")
        
        elif image_url:
            # Add image from URL
            try:
                sku_image = SKUImage(
                    sku_id=sku.id,
                    url=image_url,
                    alt_text=sku.title,
                    position=0
                )
                db.session.add(sku_image)
            except Exception as e:
                print(f"Error saving image URL: {e}")
        
        db.session.commit()
        
        # Add to Weaviate
        weaviate_id = weaviate_service.add_product(sku.to_dict())
        if weaviate_id:
            sku.weaviate_id = weaviate_id
            db.session.commit()
        
        return sku.to_dict(), 201

class SKUResource(Resource):
    def get(self, sku_id):
        """Get a specific SKU"""
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        sku = SKU.query.get_or_404(sku_id)
        return sku.to_dict()
    
    def put(self, sku_id):
        """Update a SKU"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        weaviate_service, shopify_service = get_services()
        
        sku = SKU.query.get_or_404(sku_id)
        
        # Handle both JSON and form data (for image uploads)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Form data with potential file upload
            data = request.form.to_dict()
            image_file = request.files.get('image')
            image_url = data.get('image_url')
            print(f"Updating SKU {sku_id} with form data: {data}")
            print(f"Image file: {image_file}")
        else:
            # JSON data
            data = request.get_json()
            image_file = None
            image_url = data.get('image_url')
            print(f"Updating SKU {sku_id} with JSON data: {data}")
            print(f"Image URL in data: {image_url}")
        
        sku.title = data.get('title', sku.title)
        sku.handle = data.get('handle', sku.handle)
        sku.description = data.get('description', sku.description)
        sku.body_html = data.get('body_html', sku.body_html)
        sku.vendor = data.get('vendor', sku.vendor)
        sku.product_type = data.get('product_type', sku.product_type)
        sku.tags = data.get('tags', sku.tags)
        sku.status = data.get('status', sku.status)
        sku.price = data.get('price', sku.price)
        sku.compare_at_price = data.get('compare_at_price', sku.compare_at_price)
        sku.sku_code = data.get('sku_code', sku.sku_code)
        sku.barcode = data.get('barcode', sku.barcode)
        sku.track_quantity = data.get('track_quantity', sku.track_quantity)
        sku.quantity = data.get('quantity', sku.quantity)
        sku.weight = data.get('weight', sku.weight)
        sku.weight_unit = data.get('weight_unit', sku.weight_unit)
        sku.meta_title = data.get('meta_title', sku.meta_title)
        sku.meta_description = data.get('meta_description', sku.meta_description)
        
        # Update categories
        if 'category_ids' in data:
            category_ids = data.get('category_ids', [])
            # Handle both form data (string/list) and JSON data (list)
            if isinstance(category_ids, str):
                category_ids = [category_ids] if category_ids else []
            elif not isinstance(category_ids, list):
                category_ids = []
            
            if category_ids:
                try:
                    category_ids = [int(cid) for cid in category_ids if cid]
                    categories = Category.query.filter(Category.id.in_(category_ids)).all()
                    sku.categories = categories
                except (ValueError, TypeError) as e:
                    print(f"Error processing category IDs: {e}")
                    pass
        
        # Handle image update (file upload or URL)
        if image_file and allowed_file(image_file.filename):
            print(f"Processing uploaded image file: {image_file.filename}")
            try:
                # Remove existing images
                deleted_count = SKUImage.query.filter_by(sku_id=sku.id).delete()
                print(f"Deleted {deleted_count} existing images")
                
                # Save uploaded file
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(image_file.filename)
                timestamp = str(int(datetime.utcnow().timestamp()))
                filename = f"{timestamp}_{filename}"
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, filename)
                image_file.save(file_path)
                
                # Create database record
                sku_image = SKUImage(
                    sku_id=sku.id,
                    url=f"/uploads/{filename}",
                    alt_text=sku.title,
                    position=0
                )
                db.session.add(sku_image)
                print(f"Added new uploaded image: {filename}")
                
            except Exception as e:
                print(f"Error saving uploaded image: {e}")
        
        elif image_url:
            print(f"Processing image URL: {image_url}")
            # Remove existing images
            deleted_count = SKUImage.query.filter_by(sku_id=sku.id).delete()
            print(f"Deleted {deleted_count} existing images")
            
            # Add new image
            sku_image = SKUImage(
                sku_id=sku.id,
                url=image_url,
                alt_text=sku.title,
                position=0
            )
            db.session.add(sku_image)
            print(f"Added new image from URL: {image_url}")
        else:
            print(f"No image provided. File: {image_file}, URL: {image_url}")
        
        db.session.commit()
        
        # Update in Weaviate
        if sku.weaviate_id:
            weaviate_service.update_product(sku.weaviate_id, sku.to_dict())
        
        return sku.to_dict()
    
    def delete(self, sku_id):
        """Delete a SKU"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        weaviate_service, shopify_service = get_services()
        
        sku = SKU.query.get_or_404(sku_id)
        
        # Delete from Weaviate
        if sku.weaviate_id:
            weaviate_service.delete_product(sku.weaviate_id)
        
        db.session.delete(sku)
        db.session.commit()
        
        return {'message': 'SKU deleted successfully'}, 204

# Search Resources
class SearchResource(Resource):
    def post(self):
        """Search products by text or image with catalog filters support"""
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        weaviate_service, shopify_service = get_services()
        
        search_type = request.form.get('search_type', request.form.get('type', 'text'))
        query = request.form.get('query', '')
        
        # Parse catalog filters if provided
        filters_json = request.form.get('filters', '{}')
        try:
            import json
            catalog_filters = json.loads(filters_json) if filters_json else {}
        except:
            catalog_filters = {}
        
        def apply_catalog_filters(search_results, filters):
            """Apply catalog-style filters to search results"""
            if not filters:
                return search_results
            
            db = get_db()
            filtered_ids = []
            
            # Start with all product IDs from search results
            search_ids = [r.get('product_id') for r in search_results if r.get('product_id')]
            if not search_ids:
                return search_results
            
            # Build query with filters
            query = SKU.query.filter(SKU.id.in_(search_ids))
            
            # Apply category filter
            if filters.get('categories'):
                categories = [c for c in filters['categories'] if c]
                if categories:
                    try:
                        category_ids = [int(c) for c in categories]
                        query = query.join(SKU.categories).filter(Category.id.in_(category_ids))
                    except ValueError:
                        pass
            
            # Apply vendor filter
            if filters.get('vendors'):
                vendors = [v for v in filters['vendors'] if v]
                if vendors:
                    query = query.filter(SKU.vendor.in_(vendors))
            
            # Apply product type filter
            if filters.get('productTypes'):
                product_types = [pt for pt in filters['productTypes'] if pt]
                if product_types:
                    query = query.filter(SKU.product_type.in_(product_types))
            
            # Apply price range filters
            if filters.get('minPrice'):
                try:
                    min_price = float(filters['minPrice'])
                    query = query.filter(SKU.price >= min_price)
                except (ValueError, TypeError):
                    pass
                    
            if filters.get('maxPrice'):
                try:
                    max_price = float(filters['maxPrice'])
                    query = query.filter(SKU.price <= max_price)
                except (ValueError, TypeError):
                    pass
            
            # Apply stock filters
            if not filters.get('inStock', True) and filters.get('outOfStock', False):
                query = query.filter(SKU.quantity == 0)
            elif filters.get('inStock', True) and not filters.get('outOfStock', False):
                query = query.filter(SKU.quantity > 0)
            
            # Apply option filters
            options = filters.get('options', {})
            for option_name, option_values in options.items():
                if option_values:
                    # Join with ProductOption and filter by option values
                    option_skus = db.session.query(ProductOption.sku_id).filter(
                        ProductOption.name == option_name
                    ).all()
                    option_sku_ids = [o[0] for o in option_skus]
                    if option_sku_ids:
                        query = query.filter(SKU.id.in_(option_sku_ids))
            
            # Get filtered SKU IDs
            filtered_skus = query.all()
            filtered_ids = [sku.id for sku in filtered_skus]
            
            # Return only search results that pass the filters
            return [r for r in search_results if r.get('product_id') in filtered_ids]
        
        if search_type == 'text':
            if not query:
                return {'error': 'Please enter a search query'}, 400
            
            # Combine both vector search and database search for better results
            from sqlalchemy import or_, func
            results = []
            
            # First, try vector search through Weaviate
            vector_results = []
            try:
                weaviate_results = weaviate_service.search_by_text(query, limit=5)
                for result in weaviate_results:
                    product_id = result.get('product_id')
                    if product_id:
                        vector_results.append({
                            'product_id': product_id,
                            'title': result.get('title', ''),
                            'description': result.get('description', ''),
                            'price': float(result.get('price', 0)),
                            'image_url': result.get('image_url'),
                            'vendor': result.get('vendor', ''),
                            'product_type': result.get('product_type', ''),
                            '_additional': result.get('_additional', {'distance': 0.5}),
                            '_source': 'vector'
                        })
            except Exception as e:
                print(f"Vector search failed: {e}")
            
            # Database search for additional results and fallback
            search_terms = query.lower().split()
            search_pattern = f"%{query}%"
            
            # Build dynamic OR conditions for multiple search terms
            conditions = []
            for term in search_terms:
                term_pattern = f"%{term}%"
                conditions.extend([
                    SKU.title.ilike(term_pattern),
                    SKU.description.ilike(term_pattern),
                    SKU.tags.ilike(term_pattern),
                    SKU.vendor.ilike(term_pattern),
                    SKU.product_type.ilike(term_pattern),
                    SKU.sku_code.ilike(term_pattern)
                ])
            
            # Primary search: exact phrase match (higher relevance)
            exact_skus = SKU.query.filter(
                or_(
                    SKU.title.ilike(search_pattern),
                    SKU.description.ilike(search_pattern),
                    SKU.tags.ilike(search_pattern),
                    SKU.vendor.ilike(search_pattern),
                    SKU.product_type.ilike(search_pattern),
                    SKU.sku_code.ilike(search_pattern)
                )
            ).limit(7).all()
            
            # Secondary search: individual terms (if we need more results)
            if len(exact_skus) < 5 and len(search_terms) > 1:
                term_skus = SKU.query.filter(or_(*conditions)).limit(7).all()
                # Combine results, avoiding duplicates
                all_skus = exact_skus + [sku for sku in term_skus if sku not in exact_skus]
            else:
                all_skus = exact_skus
            
            # Convert database results to result format
            db_results = []
            for i, sku in enumerate(all_skus[:7]):
                # Simple relevance: exact matches get higher scores
                relevance = 1.0 - (i * 0.1)  # First result = 1.0, second = 0.9, etc.
                if i < len(exact_skus):
                    relevance += 0.1  # Boost for exact phrase matches
                
                db_results.append({
                    'product_id': sku.id,
                    'title': sku.title,
                    'description': sku.description,
                    'price': float(sku.price) if sku.price else 0,
                    'image_url': sku.images[0].url if sku.images else None,
                    'vendor': sku.vendor,
                    'product_type': sku.product_type,
                    '_additional': {'distance': 1.0 - relevance},
                    '_source': 'database'
                })
            
            # Combine vector and database results, prioritizing vector results
            combined_results = []
            seen_ids = set()
            
            # Add vector results first (they have semantic understanding)
            for result in vector_results:
                product_id = result['product_id']
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    combined_results.append(result)
            
            # Add database results that aren't already included
            for result in db_results:
                product_id = result['product_id']
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    combined_results.append(result)
            
            results = combined_results[:10]
            
            # Apply catalog filters to results
            results = apply_catalog_filters(results, catalog_filters)
        
        elif search_type == 'image':
            if 'image' not in request.files:
                return {'error': 'Please upload an image to search with'}, 400
            
            file = request.files['image']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            if file and allowed_file(file.filename):
                results = []
                
                # Try Weaviate image search first
                try:
                    image_base64 = weaviate_service.encode_image_file(file)
                    if image_base64:
                        weaviate_results = weaviate_service.search_by_image(image_base64, limit=10)
                        for result in weaviate_results:
                            product_id = result.get('product_id')
                            if product_id:
                                results.append({
                                    'product_id': product_id,
                                    'title': result.get('title', ''),
                                    'description': result.get('description', ''),
                                    'price': float(result.get('price', 0)),
                                    'image_url': result.get('image_url'),
                                    'vendor': result.get('vendor', ''),
                                    'product_type': result.get('product_type', ''),
                                    '_additional': result.get('_additional', {'distance': 0.5}),
                                    '_source': 'vector_image'
                                })
                except Exception as e:
                    print(f"Image search failed: {e}")
                
                # Fallback: return sample products if vector search failed
                if not results:
                    sample_skus = SKU.query.filter(SKU.images.any()).limit(5).all()
                    
                    for sku in sample_skus:
                        results.append({
                            'product_id': sku.id,
                            'title': sku.title,
                            'description': sku.description,
                            'price': float(sku.price) if sku.price else 0,
                            'image_url': sku.images[0].url if sku.images else None,
                            'vendor': sku.vendor,
                            'product_type': sku.product_type,
                            '_additional': {'distance': 0.5},
                            '_source': 'fallback'
                        })
                    
                    # If no products with images, return all products
                    if not results:
                        all_skus = SKU.query.limit(5).all()
                        for sku in all_skus:
                            results.append({
                                'product_id': sku.id,
                                'title': sku.title,
                                'description': sku.description,
                                'price': float(sku.price) if sku.price else 0,
                                'image_url': sku.images[0].url if sku.images else None,
                                'vendor': sku.vendor,
                                'product_type': sku.product_type,
                                '_additional': {'distance': 0.5},
                                '_source': 'fallback'
                            })
            else:
                return {'error': 'Invalid file type'}, 400
            
            # Apply catalog filters to image search results
            results = apply_catalog_filters(results, catalog_filters)
        
        elif search_type == 'text_image':
            # Combined text and image search
            if not query and 'image' not in request.files:
                return {'error': 'Either search query or image is required for combined search'}, 400
            
            print(f"Combined search request - query: '{query}', has_image: {'image' in request.files}")
            results = []
            
            # Process the request based on what's provided
            image_base64 = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    try:
                        image_base64 = weaviate_service.encode_image_file(file)
                        print(f"Successfully encoded image for combined search")
                    except Exception as e:
                        print(f"Failed to encode image: {e}")
            
            # Try combined search if we have both query and image
            if query and image_base64:
                print("Attempting combined text+image search")
                try:
                    weaviate_results = weaviate_service.search_by_text_and_image(query, image_base64, limit=10)
                    print(f"Weaviate combined search returned {len(weaviate_results)} results")
                    
                    for result in weaviate_results:
                        product_id = result.get('product_id')
                        if product_id:
                            results.append({
                                'product_id': product_id,
                                'title': result.get('title', ''),
                                'description': result.get('description', ''),
                                'price': float(result.get('price', 0)),
                                'image_url': result.get('image_url'),
                                'vendor': result.get('vendor', ''),
                                'product_type': result.get('product_type', ''),
                                '_additional': result.get('_additional', {'distance': 0.5}),
                                '_source': result.get('_search_source', 'vector_text_image')
                            })
                except Exception as e:
                    print(f"Combined search failed: {e}")
            
            # Fallback: use individual search methods if combined failed or not available
            if not results:
                print("No results from combined search, trying individual searches")
                
                # Try text search
                if query:
                    try:
                        text_results = weaviate_service.search_by_text(query, limit=5)
                        print(f"Text search returned {len(text_results)} results")
                        for result in text_results:
                            product_id = result.get('product_id')
                            if product_id:
                                results.append({
                                    'product_id': product_id,
                                    'title': result.get('title', ''),
                                    'description': result.get('description', ''),
                                    'price': float(result.get('price', 0)),
                                    'image_url': result.get('image_url'),
                                    'vendor': result.get('vendor', ''),
                                    'product_type': result.get('product_type', ''),
                                    '_additional': result.get('_additional', {'distance': 0.5}),
                                    '_source': 'text_fallback'
                                })
                    except Exception as e:
                        print(f"Text search fallback failed: {e}")
                
                # Try image search
                if image_base64 and len(results) < 5:
                    try:
                        image_results = weaviate_service.search_by_image(image_base64, limit=5)
                        print(f"Image search returned {len(image_results)} results")
                        seen_ids = {r['product_id'] for r in results}
                        
                        for result in image_results:
                            product_id = result.get('product_id')
                            if product_id and product_id not in seen_ids:
                                results.append({
                                    'product_id': product_id,
                                    'title': result.get('title', ''),
                                    'description': result.get('description', ''),
                                    'price': float(result.get('price', 0)),
                                    'image_url': result.get('image_url'),
                                    'vendor': result.get('vendor', ''),
                                    'product_type': result.get('product_type', ''),
                                    '_additional': result.get('_additional', {'distance': 0.5}),
                                    '_source': 'image_fallback'
                                })
                    except Exception as e:
                        print(f"Image search fallback failed: {e}")
            
            # Final fallback to database search if still no results
            if not results and query:
                print("Using database fallback search")
                from sqlalchemy import or_
                search_pattern = f"%{query}%"
                fallback_skus = SKU.query.filter(
                    or_(
                        SKU.title.ilike(search_pattern),
                        SKU.description.ilike(search_pattern),
                        SKU.tags.ilike(search_pattern)
                    )
                ).limit(5).all()
                
                for sku in fallback_skus:
                    results.append({
                        'product_id': sku.id,
                        'title': sku.title,
                        'description': sku.description,
                        'price': float(sku.price) if sku.price else 0,
                        'image_url': sku.images[0].url if sku.images else None,
                        'vendor': sku.vendor,
                        'product_type': sku.product_type,
                        '_additional': {'distance': 0.5},
                        '_source': 'database_fallback'
                    })
            
            print(f"Combined search final result count: {len(results)}")
            
            # Apply catalog filters to combined search results
            results = apply_catalog_filters(results, catalog_filters)
        else:
            return {'error': 'Invalid search type. Use: text, image, or text_image'}, 400
        
        # Enrich results with database data
        enriched_results = []
        for result in results:
            product_id = result.get('product_id')
            if product_id:
                sku = SKU.query.get(product_id)
                if sku:
                    product_data = sku.to_dict()
                    product_data['similarity_score'] = 1 - result.get('_additional', {}).get('distance', 1)
                    product_data['search_source'] = result.get('_source', 'unknown')
                    enriched_results.append(product_data)
        
        return {'results': enriched_results}

# Shopify Sync Resources
class ShopifySyncResource(Resource):
    def post(self):
        """Sync products from Shopify"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        weaviate_service, shopify_service = get_services()
        
        if not shopify_service.is_configured():
            return {'error': 'Shopify integration not configured. Please configure Shopify settings first.'}, 400
        
        # Get request data first
        data = request.get_json() or {}
        sync_type = data.get('sync_type', 'full')
        test_mode = data.get('test_mode', False)  # Add test mode for development
        
        # Test connection before starting sync (skip in test mode)
        if not test_mode and not shopify_service.test_connection():
            return {'error': 'Cannot connect to Shopify. Please check your Shopify settings.'}, 400
        
        # Check if there's already a running sync
        running_sync = SyncLog.query.filter(SyncLog.status.in_(['started', 'in_progress'])).first()
        if running_sync:
            return {'error': f'A sync is already running (ID: {running_sync.id}). Please wait for it to complete or cancel it first.'}, 400
        
        # Create sync log
        sync_log = SyncLog(
            sync_type=sync_type,
            status='started',
            started_at=datetime.utcnow()
        )
        db.session.add(sync_log)
        db.session.commit()
        
        # Start sync in background - pass the current app instance
        from flask import current_app
        thread = threading.Thread(
            target=self._sync_products,
            args=(sync_log.id, current_app._get_current_object(), test_mode)
        )
        thread.start()
        
        return {'message': 'Sync started', 'sync_id': sync_log.id}, 202
    
    def _sync_products(self, sync_log_id, app, test_mode=False):
        """Background task to sync products"""
        with app.app_context():
            db = get_db()
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            
            sync_log = SyncLog.query.get(sync_log_id)
            if not sync_log:
                print(f"Sync log {sync_log_id} not found")
                return
            
            # Get services within the app context
            weaviate_service, shopify_service = get_services()
            
            # Double-check Shopify configuration (skip connection test in test mode)
            if not shopify_service.is_configured():
                raise Exception("Shopify is not properly configured")
            
            if not test_mode and not shopify_service.test_connection():
                raise Exception("Cannot connect to Shopify")
            
            if test_mode:
                print("Running in TEST MODE - simulating sync")
                # Simulate a quick sync for testing
                import time
                time.sleep(2)  # Simulate processing time
                sync_log.status = 'completed'
                sync_log.total_items = 0
                sync_log.processed_items = 0
                sync_log.failed_items = 0
                sync_log.completed_at = datetime.utcnow()
                db.session.commit()
                print("Test sync completed")
                return
            
            try:
                # Sync collections first
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
                
                # Sync products
                page_info = None
                total_products = 0
                processed_products = 0
                failed_products = 0
                
                while True:
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
                            if not sku:
                                sku = SKU()
                            
                            # Update SKU fields
                            for key, value in transformed.items():
                                if key not in ['images', 'variants', 'options']:
                                    setattr(sku, key, value)
                            
                            db.session.add(sku)
                            db.session.flush()
                            
                            # Handle images
                            SKUImage.query.filter_by(sku_id=sku.id).delete()
                            for img_data in transformed.get('images', []):
                                # Convert variant_ids list to JSON string if present
                                if 'variant_ids' in img_data and isinstance(img_data['variant_ids'], list):
                                    import json
                                    img_data['variant_ids'] = json.dumps(img_data['variant_ids'])
                                image = SKUImage(sku_id=sku.id, **img_data)
                                db.session.add(image)
                            
                            # Handle variants
                            SKUVariant.query.filter_by(sku_id=sku.id).delete()
                            for var_data in transformed.get('variants', []):
                                variant = SKUVariant(sku_id=sku.id, **var_data)
                                db.session.add(variant)
                            
                            # Handle options
                            from models.sku import ProductOption
                            ProductOption.query.filter_by(sku_id=sku.id).delete()
                            for opt_data in transformed.get('options', []):
                                import json
                                option = ProductOption(
                                    sku_id=sku.id,
                                    shopify_id=opt_data.get('shopify_id'),
                                    name=opt_data['name'],
                                    position=opt_data['position'],
                                    values=json.dumps(opt_data['values'])
                                )
                                db.session.add(option)
                            
                            db.session.commit()
                            
                            # Add to Weaviate
                            if sku.weaviate_id:
                                weaviate_service.update_product(sku.weaviate_id, sku.to_dict())
                            else:
                                weaviate_id = weaviate_service.add_product(sku.to_dict())
                                if weaviate_id:
                                    sku.weaviate_id = weaviate_id
                                    db.session.commit()
                            
                            processed_products += 1
                        except Exception as e:
                            print(f"Error processing product: {e}")
                            import traceback
                            print(f"Full traceback: {traceback.format_exc()}")
                            failed_products += 1
                            db.session.rollback()
                    
                    sync_log.total_items = total_products
                    sync_log.processed_items = processed_products
                    sync_log.failed_items = failed_products
                    db.session.commit()
                    
                    if not page_info:
                        break
                
                # Update sync log
                sync_log.status = 'completed'
                sync_log.completed_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                print(f"Sync error: {e}")
                import traceback
                error_details = f"{str(e)}\n{traceback.format_exc()}"
                print(f"Full error traceback: {error_details}")
                
                try:
                    # Try to update sync log with error
                    sync_log = SyncLog.query.get(sync_log_id)
                    if sync_log:
                        sync_log.status = 'failed'
                        sync_log.error_message = str(e)[:500]  # Limit error message length
                        sync_log.completed_at = datetime.utcnow()
                        db.session.commit()
                except Exception as log_error:
                    print(f"Failed to update sync log with error: {log_error}")

class SyncStatusResource(Resource):
    def get(self, sync_id):
        """Get sync status"""
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        sync_log = SyncLog.query.get_or_404(sync_id)
        
        # Check if sync has been running too long (more than 10 minutes)
        if sync_log.status in ['started', 'in_progress']:
            from datetime import datetime, timedelta
            if sync_log.started_at and (datetime.utcnow() - sync_log.started_at) > timedelta(minutes=10):
                # Mark as failed due to timeout
                db = get_db()
                sync_log.status = 'failed'
                sync_log.error_message = 'Sync timed out after 10 minutes'
                sync_log.completed_at = datetime.utcnow()
                db.session.commit()
        
        return sync_log.to_dict()
    
    def delete(self, sync_id):
        """Cancel/reset a sync"""
        db = get_db()
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        sync_log = SyncLog.query.get_or_404(sync_id)
        
        if sync_log.status in ['started', 'in_progress']:
            sync_log.status = 'cancelled'
            sync_log.error_message = 'Cancelled by user'
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()
            return {'message': 'Sync cancelled successfully'}
        else:
            return {'message': f'Sync is already {sync_log.status}'}

# API Documentation Resource
class APIDocResource(Resource):
    def get(self):
        """Get API documentation"""
        from config.config import Config
        endpoints = [
            {
                'path': '/api/categories',
                'methods': ['GET', 'POST'],
                'description': 'List all categories or create a new category'
            },
            {
                'path': '/api/categories/<id>',
                'methods': ['GET', 'PUT', 'DELETE'],
                'description': 'Get, update, or delete a specific category'
            },
            {
                'path': '/api/skus',
                'methods': ['GET', 'POST'],
                'description': 'List all SKUs or create a new SKU'
            },
            {
                'path': '/api/skus/<id>',
                'methods': ['GET', 'PUT', 'DELETE'],
                'description': 'Get, update, or delete a specific SKU'
            },
            {
                'path': '/api/search',
                'methods': ['POST'],
                'description': 'Search products by text query or image'
            },
            {
                'path': '/api/sync/shopify',
                'methods': ['POST'],
                'description': 'Sync products from Shopify'
            },
            {
                'path': '/api/sync/status/<id>',
                'methods': ['GET'],
                'description': 'Get sync operation status'
            }
        ]
        
        return {'endpoints': endpoints, 'version': Config.API_VERSION}

# Debug Resource (remove in production)
class DebugResource(Resource):
    def get(self):
        """Debug endpoint to check database contents"""
        SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
        
        skus = SKU.query.all()
        categories = Category.query.all()
        sync_logs = SyncLog.query.order_by(SyncLog.id.desc()).limit(10).all()
        
        return {
            'sku_count': len(skus),
            'category_count': len(categories),
            'skus': [{'id': sku.id, 'title': sku.title, 'weaviate_id': sku.weaviate_id, 'images': [img.to_dict() for img in sku.images]} for sku in skus[:5]],
            'categories': [{'id': cat.id, 'name': cat.name} for cat in categories[:5]],
            'recent_syncs': [sync.to_dict() for sync in sync_logs]
        }
    
    def post(self):
        """Debug actions"""
        data = request.get_json()
        action = data.get('action')
        
        if action == 'cancel_all_syncs':
            db = get_db()
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            
            # Cancel all running syncs
            running_syncs = SyncLog.query.filter(SyncLog.status.in_(['started', 'in_progress'])).all()
            
            for sync in running_syncs:
                sync.status = 'cancelled'
                sync.error_message = 'Cancelled via debug endpoint'
                sync.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'message': f'Cancelled {len(running_syncs)} running syncs',
                'cancelled_sync_ids': [sync.id for sync in running_syncs]
            }
        
        return {'error': 'Unknown action'}, 400

# Shopify Configuration Resources
class ShopifyConfigResource(Resource):
    def get(self):
        """Get current Shopify configuration"""
        import os
        from config.config import Config
        
        # Check environment variables first
        env_store_url = os.getenv('SHOPIFY_STORE_URL')
        env_access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        env_api_version = os.getenv('SHOPIFY_API_VERSION')
        
        # Try to get stored config from database (we'll create a simple config table)
        db = get_db()
        
        # For now, we'll create a simple config storage in database
        try:
            from sqlalchemy import text
            # Check if we have a config table, if not we'll store in a simple way
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='shopify_config'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                # Create config table
                db.session.execute(text("""
                    CREATE TABLE shopify_config (
                        id INTEGER PRIMARY KEY,
                        store_url TEXT,
                        access_token TEXT,
                        api_version TEXT DEFAULT '2024-01',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
            
            # Get stored config
            stored_config = db.session.execute(text("SELECT * FROM shopify_config ORDER BY id DESC LIMIT 1")).fetchone()
            
            return {
                'store_url': env_store_url or (stored_config[1] if stored_config else ''),
                'access_token': env_access_token or (stored_config[2] if stored_config else ''),
                'api_version': env_api_version or (stored_config[3] if stored_config else '2024-01'),
                'store_url_source': 'environment' if env_store_url else ('database' if stored_config and stored_config[1] else 'none'),
                'access_token_source': 'environment' if env_access_token else ('database' if stored_config and stored_config[2] else 'none'),
                'configured': bool((env_store_url or (stored_config and stored_config[1])) and 
                                (env_access_token or (stored_config and stored_config[2])))
            }
            
        except Exception as e:
            print(f"Error getting Shopify config: {e}")
            return {
                'store_url': env_store_url or '',
                'access_token': env_access_token or '',
                'api_version': env_api_version or '2024-01',
                'store_url_source': 'environment' if env_store_url else 'none',
                'access_token_source': 'environment' if env_access_token else 'none',
                'configured': bool(env_store_url and env_access_token)
            }
    
    def post(self):
        """Save Shopify configuration"""
        import os
        
        # Don't allow saving if environment variables are set
        if os.getenv('SHOPIFY_STORE_URL') or os.getenv('SHOPIFY_ACCESS_TOKEN'):
            return {'error': 'Configuration is set via environment variables and cannot be changed'}, 400
        
        data = request.get_json()
        if not data:
            return {'error': 'No configuration data provided'}, 400
        
        store_url = data.get('store_url', '').strip()
        access_token = data.get('access_token', '').strip()
        api_version = data.get('api_version', '2024-01').strip()
        
        # Validate required fields
        if not store_url or not access_token:
            return {'error': 'Store URL and Access Token are required'}, 400
        
        # Validate format
        if not store_url.endswith('.myshopify.com'):
            return {'error': 'Store URL must end with .myshopify.com'}, 400
        
        if not access_token.startswith('shpat_'):
            return {'error': 'Access token must start with "shpat_"'}, 400
        
        try:
            from sqlalchemy import text
            db = get_db()
            
            # Create table if it doesn't exist
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='shopify_config'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                db.session.execute(text("""
                    CREATE TABLE shopify_config (
                        id INTEGER PRIMARY KEY,
                        store_url TEXT,
                        access_token TEXT,
                        api_version TEXT DEFAULT '2024-01',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            
            # Clear existing config and insert new
            db.session.execute(text("DELETE FROM shopify_config"))
            db.session.execute(
                text("INSERT INTO shopify_config (store_url, access_token, api_version) VALUES (:store_url, :access_token, :api_version)"),
                {"store_url": store_url, "access_token": access_token, "api_version": api_version}
            )
            db.session.commit()
            
            return {'message': 'Configuration saved successfully'}, 200
            
        except Exception as e:
            print(f"Error saving Shopify config: {e}")
            return {'error': 'Failed to save configuration'}, 500

class ShopifyTestResource(Resource):
    def post(self):
        """Test Shopify connection"""
        # Create a new ShopifyService instance to avoid Weaviate initialization
        from services.shopify_service import ShopifyService
        shopify_service = ShopifyService()
        
        if not shopify_service.is_configured():
            return {
                'connected': False,
                'error': 'Shopify is not configured. Please set store URL and access token.'
            }
        
        try:
            # Test connection by fetching shop info
            import requests
            
            response = requests.get(
                f"{shopify_service.base_url}/shop.json",
                headers=shopify_service.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                return {
                    'connected': True,
                    'shop_name': shop_data.get('name', 'Unknown'),
                    'shop_domain': shop_data.get('domain', 'Unknown'),
                    'plan': shop_data.get('plan_name', 'Unknown'),
                    'country': shop_data.get('country_name', 'Unknown')
                }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        error_msg = str(error_data['errors'])
                except:
                    pass
                
                return {
                    'connected': False,
                    'error': error_msg
                }
        
        except requests.exceptions.Timeout:
            return {
                'connected': False,
                'error': 'Connection timeout. Please check your store URL.'
            }
        except requests.exceptions.ConnectionError:
            return {
                'connected': False,
                'error': 'Connection failed. Please check your store URL.'
            }
        except Exception as e:
            return {
                'connected': False,
                'error': f'Connection test failed: {str(e)}'
            }

class ShopifyStatusResource(Resource):
    def get(self):
        """Get Shopify connection status"""
        # Create a new ShopifyService instance to avoid Weaviate initialization
        from services.shopify_service import ShopifyService
        shopify_service = ShopifyService()
        
        if not shopify_service.is_configured():
            return {
                'configured': False,
                'connected': False,
                'message': 'Shopify is not configured'
            }
        
        # Quick connection test
        connected = shopify_service.test_connection()
        
        return {
            'configured': True,
            'connected': connected,
            'message': 'Connected and ready' if connected else 'Configured but connection failed'
        }

# Vector Configuration Resources
class VectorConfigResource(Resource):
    def get(self):
        """Get current vector configuration"""
        import os
        
        # Check environment variables first
        env_url = os.getenv('WEAVIATE_URL')
        env_api_key = os.getenv('WEAVIATE_API_KEY')
        env_vectorizer = os.getenv('WEAVIATE_VECTORIZER')
        env_openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Try to get stored config from database
        db = get_db()
        
        try:
            from sqlalchemy import text
            # Check if we have a vector config table
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_config'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                # Create config table
                db.session.execute(text("""
                    CREATE TABLE vector_config (
                        id INTEGER PRIMARY KEY,
                        weaviate_url TEXT,
                        api_key TEXT,
                        vectorizer TEXT DEFAULT 'text2vec-transformers',
                        timeout INTEGER DEFAULT 30,
                        openai_api_key TEXT,
                        image_embedding_model TEXT DEFAULT 'clip-vit-base-patch32',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
            else:
                # Check if new columns exist and add them if not
                try:
                    # Check for openai_api_key column
                    result = db.session.execute(text("PRAGMA table_info(vector_config)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'openai_api_key' not in columns:
                        db.session.execute(text("ALTER TABLE vector_config ADD COLUMN openai_api_key TEXT"))
                    
                    if 'image_embedding_model' not in columns:
                        db.session.execute(text("ALTER TABLE vector_config ADD COLUMN image_embedding_model TEXT DEFAULT 'clip-vit-base-patch32'"))
                    
                    db.session.commit()
                except Exception as migration_error:
                    print(f"Migration error: {migration_error}")
                    # Continue without failing
            
            # Get stored config
            stored_config = db.session.execute(text("SELECT * FROM vector_config ORDER BY id DESC LIMIT 1")).fetchone()
            
            return {
                'weaviate_url': env_url or (stored_config[1] if stored_config else 'http://localhost:8080'),
                'api_key': env_api_key or (stored_config[2] if stored_config else ''),
                'vectorizer': env_vectorizer or (stored_config[3] if stored_config else 'text2vec-transformers'),
                'timeout': stored_config[4] if stored_config else 30,
                'openai_api_key': env_openai_api_key or (stored_config[5] if stored_config and len(stored_config) > 5 else ''),
                'image_embedding_model': stored_config[6] if stored_config and len(stored_config) > 6 else 'clip-vit-base-patch32',
                'url_source': 'environment' if env_url else ('database' if stored_config and stored_config[1] else 'default'),
                'api_key_source': 'environment' if env_api_key else ('database' if stored_config and stored_config[2] else 'none'),
                'openai_api_key_source': 'environment' if env_openai_api_key else ('database' if stored_config and len(stored_config) > 5 and stored_config[5] else 'none'),
                'configured': bool((env_url or (stored_config and stored_config[1])))
            }
            
        except Exception as e:
            print(f"Error getting vector config: {e}")
            return {
                'weaviate_url': env_url or 'http://localhost:8080',
                'api_key': env_api_key or '',
                'vectorizer': env_vectorizer or 'text2vec-transformers',
                'timeout': 30,
                'openai_api_key': env_openai_api_key or '',
                'image_embedding_model': 'clip-vit-base-patch32',
                'url_source': 'environment' if env_url else 'default',
                'api_key_source': 'environment' if env_api_key else 'none',
                'openai_api_key_source': 'environment' if env_openai_api_key else 'none',
                'configured': bool(env_url)
            }
    
    def post(self):
        """Save vector configuration"""
        import os
        
        # Don't allow saving if environment variables are set
        if os.getenv('WEAVIATE_URL'):
            return {'error': 'Configuration is set via environment variables and cannot be changed'}, 400
        
        data = request.get_json()
        if not data:
            return {'error': 'No configuration data provided'}, 400
        
        weaviate_url = data.get('weaviate_url', '').strip()
        api_key = data.get('api_key', '').strip()
        vectorizer = data.get('vectorizer', 'text2vec-transformers').strip()
        timeout = data.get('timeout', 30)
        openai_api_key = data.get('openai_api_key', '').strip()
        image_embedding_model = data.get('image_embedding_model', 'clip-vit-base-patch32').strip()
        
        # Validate required fields
        if not weaviate_url:
            return {'error': 'Weaviate URL is required'}, 400
        
        try:
            from sqlalchemy import text
            db = get_db()
            
            # Create table if it doesn't exist
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='vector_config'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                db.session.execute(text("""
                    CREATE TABLE vector_config (
                        id INTEGER PRIMARY KEY,
                        weaviate_url TEXT,
                        api_key TEXT,
                        vectorizer TEXT DEFAULT 'text2vec-transformers',
                        timeout INTEGER DEFAULT 30,
                        openai_api_key TEXT,
                        image_embedding_model TEXT DEFAULT 'clip-vit-base-patch32',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
            else:
                # Check if new columns exist and add them if not
                try:
                    result = db.session.execute(text("PRAGMA table_info(vector_config)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'openai_api_key' not in columns:
                        db.session.execute(text("ALTER TABLE vector_config ADD COLUMN openai_api_key TEXT"))
                    
                    if 'image_embedding_model' not in columns:
                        db.session.execute(text("ALTER TABLE vector_config ADD COLUMN image_embedding_model TEXT DEFAULT 'clip-vit-base-patch32'"))
                        
                except Exception as migration_error:
                    print(f"Migration error: {migration_error}")
            
            # Clear existing config and insert new
            db.session.execute(text("DELETE FROM vector_config"))
            db.session.execute(
                text("INSERT INTO vector_config (weaviate_url, api_key, vectorizer, timeout, openai_api_key, image_embedding_model) VALUES (:url, :key, :vectorizer, :timeout, :openai_key, :image_model)"),
                {"url": weaviate_url, "key": api_key, "vectorizer": vectorizer, "timeout": timeout, "openai_key": openai_api_key, "image_model": image_embedding_model}
            )
            db.session.commit()
            
            return {'message': 'Vector configuration saved successfully'}, 200
            
        except Exception as e:
            print(f"Error saving vector config: {e}")
            return {'error': 'Failed to save configuration'}, 500

class VectorTestResource(Resource):
    def post(self):
        """Test Weaviate connection"""
        try:
            weaviate_service, _ = get_services()
            
            # Test basic connection
            schema = weaviate_service.client.schema.get()
            
            return {
                'connected': True,
                'schema_classes': len(schema.get('classes', [])),
                'classes': [cls['class'] for cls in schema.get('classes', [])]
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

class VectorStatusResource(Resource):
    def get(self):
        """Get vector connection status"""
        try:
            # Check if configured
            config_resource = VectorConfigResource()
            config = config_resource.get()
            
            if not config['configured']:
                return {
                    'configured': False,
                    'connected': False,
                    'message': 'Weaviate is not configured'
                }
            
            # Test connection
            weaviate_service, _ = get_services()
            schema = weaviate_service.client.schema.get()
            
            return {
                'configured': True,
                'connected': True,
                'message': 'Connected and ready'
            }
            
        except Exception as e:
            return {
                'configured': True,
                'connected': False,
                'message': f'Connection failed: {str(e)}'
            }

class VectorSchemaResource(Resource):
    def get(self):
        """Check Weaviate schema"""
        try:
            weaviate_service, _ = get_services()
            schema = weaviate_service.client.schema.get()
            
            classes = schema.get('classes', [])
            
            return {
                'schema_exists': len(classes) > 0,
                'class_count': len(classes),
                'classes': [cls['class'] for cls in classes]
            }
            
        except Exception as e:
            return {
                'schema_exists': False,
                'error': str(e)
            }

class VectorStatsResource(Resource):
    def get(self):
        """Get vector index statistics"""
        try:
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            
            # Get database stats
            total_skus = SKU.query.count()
            indexed_skus = SKU.query.filter(SKU.weaviate_id.isnot(None)).count()
            skus_with_images = SKU.query.filter(SKU.images.any()).count()
            
            # Get last indexed time
            last_indexed_sku = SKU.query.filter(SKU.weaviate_id.isnot(None)).order_by(SKU.updated_at.desc()).first()
            last_indexed = last_indexed_sku.updated_at.strftime('%Y-%m-%d %H:%M') if last_indexed_sku else 'Never'
            
            return {
                'total_skus': total_skus,
                'indexed_skus': indexed_skus,
                'skus_with_images': skus_with_images,
                'last_indexed': last_indexed
            }
            
        except Exception as e:
            return {
                'total_skus': 0,
                'indexed_skus': 0,
                'skus_with_images': 0,
                'last_indexed': 'Error',
                'error': str(e)
            }

class VectorReindexResource(Resource):
    def post(self):
        """Start reindexing all products"""
        from flask import current_app
        import threading
        import uuid
        
        task_id = str(uuid.uuid4())
        
        # Start reindexing in background
        thread = threading.Thread(
            target=self._reindex_products,
            args=(task_id, current_app._get_current_object())
        )
        thread.start()
        
        return {'message': 'Reindexing started', 'task_id': task_id}, 202
    
    def _reindex_products(self, task_id, app):
        """Background task to reindex all products"""
        with app.app_context():
            try:
                # Store task status in a simple way (could use Redis for production)
                self._update_task_status(task_id, {
                    'status': 'running',
                    'processed': 0,
                    'total': 0,
                    'current_operation': 'Starting...',
                    'log_entries': ['Reindexing started']
                })
                
                db = get_db()
                SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
                weaviate_service, _ = get_services()
                
                # Get all SKUs
                skus = SKU.query.all()
                total = len(skus)
                
                self._update_task_status(task_id, {
                    'status': 'running',
                    'processed': 0,
                    'total': total,
                    'current_operation': f'Processing {total} products...',
                    'log_entries': [f'Found {total} products to index']
                })
                
                processed = 0
                failed = 0
                
                for sku in skus:
                    try:
                        # Delete existing entry if it exists
                        if sku.weaviate_id:
                            try:
                                weaviate_service.delete_product(sku.weaviate_id)
                            except:
                                pass  # Ignore delete errors
                        
                        # Add product to Weaviate
                        weaviate_id = weaviate_service.add_product(sku.to_dict())
                        
                        if weaviate_id:
                            sku.weaviate_id = weaviate_id
                            db.session.commit()
                            processed += 1
                            
                            self._update_task_status(task_id, {
                                'status': 'running',
                                'processed': processed,
                                'total': total,
                                'current_operation': f'Indexed: {sku.title[:50]}...',
                                'log_entries': [f'Successfully indexed: {sku.title}']
                            })
                        else:
                            failed += 1
                            self._update_task_status(task_id, {
                                'status': 'running',
                                'processed': processed,
                                'total': total,
                                'current_operation': f'Failed: {sku.title[:50]}...',
                                'log_entries': [f'Failed to index: {sku.title}']
                            })
                    
                    except Exception as e:
                        failed += 1
                        print(f"Error indexing SKU {sku.id}: {e}")
                        self._update_task_status(task_id, {
                            'status': 'running',
                            'processed': processed,
                            'total': total,
                            'current_operation': f'Error: {sku.title[:50]}...',
                            'log_entries': [f'Error indexing {sku.title}: {str(e)}']
                        })
                
                # Complete
                self._update_task_status(task_id, {
                    'status': 'completed',
                    'processed': processed,
                    'total': total,
                    'current_operation': 'Completed',
                    'log_entries': [f'Reindexing completed. Processed: {processed}, Failed: {failed}']
                })
                
            except Exception as e:
                print(f"Reindexing error: {e}")
                self._update_task_status(task_id, {
                    'status': 'failed',
                    'processed': 0,
                    'total': 0,
                    'current_operation': 'Failed',
                    'error': str(e),
                    'log_entries': [f'Reindexing failed: {str(e)}']
                })
    
    def _update_task_status(self, task_id, status):
        """Update task status (simple in-memory storage)"""
        global _task_statuses
        _task_statuses[task_id] = status

class VectorReindexStatusResource(Resource):
    def get(self, task_id):
        """Get reindexing status"""
        global _task_statuses
        if task_id in _task_statuses:
            return _task_statuses[task_id]
        else:
            return {
                'status': 'not_found',
                'processed': 0,
                'total': 0,
                'current_operation': 'Task not found',
                'log_entries': []
            }

class VectorReindexStopResource(Resource):
    def post(self):
        """Stop reindexing (placeholder for now)"""
        return {'message': 'Stop signal sent (background tasks will complete current operations)'}

class VectorClearResource(Resource):
    def post(self):
        """Clear the vector index"""
        try:
            db = get_db()
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            weaviate_service, _ = get_services()
            
            # Clear all weaviate_ids from database
            SKU.query.update({SKU.weaviate_id: None})
            db.session.commit()
            
            # Try to delete the schema and recreate it (clears all data)
            try:
                weaviate_service.client.schema.delete_all()
                weaviate_service.setup_schema()
            except Exception as e:
                print(f"Error clearing Weaviate schema: {e}")
            
            return {'message': 'Vector index cleared successfully'}
            
        except Exception as e:
            return {'error': f'Failed to clear index: {str(e)}'}, 500


class CatalogProductsResource(Resource):
    def get(self):
        """Get products for catalog with advanced filtering"""
        try:
            db = get_db()
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            sort = request.args.get('sort', 'relevance')
            
            # Search query
            search_query = request.args.get('q', '')
            
            # Filters
            categories = request.args.getlist('categories') or request.args.get('categories', '').split(',') if request.args.get('categories') else []
            vendors = request.args.getlist('vendors') or request.args.get('vendors', '').split(',') if request.args.get('vendors') else []
            product_types = request.args.getlist('product_types') or request.args.get('product_types', '').split(',') if request.args.get('product_types') else []
            min_price = request.args.get('min_price', type=float)
            max_price = request.args.get('max_price', type=float)
            stock_filter = request.args.get('stock', 'all')  # all, in_stock, out_of_stock
            
            # Start with base query
            query = SKU.query
            vector_results = []
            
            # Apply search - use hybrid approach with vector search + database filtering
            if search_query:
                # Get vector search results first
                try:
                    weaviate_service, _ = get_services()
                    weaviate_results = weaviate_service.search_by_text(search_query, limit=50)  # Get more results for filtering
                    
                    # Extract product IDs from vector search, maintaining order for relevance
                    vector_product_ids = []
                    for result in weaviate_results:
                        product_id = result.get('product_id')
                        if product_id:
                            vector_product_ids.append(product_id)
                    
                    if vector_product_ids:
                        # Use vector search results as the base set
                        query = query.filter(SKU.id.in_(vector_product_ids))
                        vector_results = weaviate_results  # Store for relevance sorting later
                    else:
                        # Fallback to database search if vector search returns no results
                        search_pattern = f'%{search_query}%'
                        query = query.filter(
                            db.or_(
                                SKU.title.ilike(search_pattern),
                                SKU.description.ilike(search_pattern),
                                SKU.tags.ilike(search_pattern),
                                SKU.vendor.ilike(search_pattern),
                                SKU.product_type.ilike(search_pattern)
                            )
                        )
                        
                except Exception as e:
                    print(f"Vector search failed, using database search: {e}")
                    # Fallback to database search
                    search_pattern = f'%{search_query}%'
                    query = query.filter(
                        db.or_(
                            SKU.title.ilike(search_pattern),
                            SKU.description.ilike(search_pattern),
                            SKU.tags.ilike(search_pattern),
                            SKU.vendor.ilike(search_pattern),
                            SKU.product_type.ilike(search_pattern)
                        )
                    )
            
            # Apply category filter
            if categories:
                categories = [c for c in categories if c]  # Remove empty strings
                if categories:
                    query = query.join(SKU.categories).filter(Category.id.in_(categories))
            
            # Apply vendor filter
            if vendors:
                vendors = [v for v in vendors if v]
                if vendors:
                    query = query.filter(SKU.vendor.in_(vendors))
            
            # Apply product type filter
            if product_types:
                product_types = [pt for pt in product_types if pt]
                if product_types:
                    query = query.filter(SKU.product_type.in_(product_types))
            
            # Apply price range filter
            if min_price is not None:
                query = query.filter(SKU.price >= min_price)
            if max_price is not None:
                query = query.filter(SKU.price <= max_price)
            
            # Apply stock filter
            if stock_filter == 'in_stock':
                query = query.filter(SKU.quantity > 0)
            elif stock_filter == 'out_of_stock':
                query = query.filter(SKU.quantity == 0)
            
            # Apply sorting
            if sort == 'price-low':
                query = query.order_by(SKU.price.asc())
            elif sort == 'price-high':
                query = query.order_by(SKU.price.desc())
            elif sort == 'name-asc':
                query = query.order_by(SKU.title.asc())
            elif sort == 'name-desc':
                query = query.order_by(SKU.title.desc())
            elif sort == 'newest':
                query = query.order_by(SKU.created_at.desc())
            else:  # relevance (default)
                if search_query and vector_results:
                    # Use vector search order for relevance - don't apply database sorting
                    pass  # We'll handle ordering after pagination with vector results
                elif search_query:
                    # For relevance without vector results, prioritize title matches
                    query = query.order_by(
                        db.case(
                            (SKU.title.ilike(f'%{search_query}%'), 1),
                            else_=2
                        ),
                        SKU.created_at.desc()
                    )
                else:
                    query = query.order_by(SKU.created_at.desc())
            
            # Handle pagination and ordering
            if search_query and vector_results and sort == 'relevance':
                # For vector search with relevance sorting, we need custom ordering
                all_results = query.all()
                
                # Create a mapping of product_id to vector search order/score
                vector_order = {}
                for i, result in enumerate(vector_results):
                    product_id = result.get('product_id')
                    if product_id:
                        vector_order[product_id] = {
                            'order': i,
                            'score': 1 - result.get('_additional', {}).get('distance', 1)
                        }
                
                # Sort products by vector search relevance
                sorted_results = sorted(all_results, key=lambda sku: vector_order.get(sku.id, {}).get('order', 999))
                
                # Apply manual pagination
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_results = sorted_results[start_idx:end_idx]
                
                # Get products with all relationships
                products = []
                for sku in paginated_results:
                    product_data = sku.to_dict()
                    # Add similarity score from vector search
                    if sku.id in vector_order:
                        product_data['similarity_score'] = vector_order[sku.id]['score']
                        product_data['search_source'] = 'vector_hybrid'
                    products.append(product_data)
                
                # Create pagination info
                total_results = len(all_results)
                
            else:
                # Standard pagination for non-vector searches or other sort orders
                pagination = query.paginate(page=page, per_page=per_page, error_out=False)
                
                # Get products with all relationships
                products = []
                for sku in pagination.items:
                    product_data = sku.to_dict()
                    products.append(product_data)
                
                total_results = pagination.total
            
            return {
                'products': products,
                'total': total_results,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_results + per_page - 1) // per_page  # Ceiling division
            }
            
        except Exception as e:
            print(f"Error in catalog products: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class CatalogFiltersResource(Resource):
    def get(self):
        """Get available filter options for catalog"""
        try:
            db = get_db()
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            
            # Get all categories with product count
            categories = db.session.query(
                Category.id,
                Category.name,
                db.func.count(SKU.id).label('count')
            ).join(Category.products).group_by(Category.id).all()
            
            # Get all vendors with product count
            vendors = db.session.query(
                SKU.vendor,
                db.func.count(SKU.id).label('count')
            ).filter(SKU.vendor != None, SKU.vendor != '').group_by(SKU.vendor).all()
            
            # Get all product types with count
            product_types = db.session.query(
                SKU.product_type,
                db.func.count(SKU.id).label('count')
            ).filter(SKU.product_type != None, SKU.product_type != '').group_by(SKU.product_type).all()
            
            # Get price range
            price_stats = db.session.query(
                db.func.min(SKU.price).label('min_price'),
                db.func.max(SKU.price).label('max_price')
            ).first()
            
            # Get product options
            options = {}
            all_options = ProductOption.query.all()
            
            for option in all_options:
                if option.name not in options:
                    options[option.name] = {}
                
                import json
                try:
                    values = json.loads(option.values) if option.values else []
                    for value in values:
                        if value not in options[option.name]:
                            options[option.name][value] = 0
                        options[option.name][value] += 1
                except:
                    pass
            
            # Format options for response
            formatted_options = {}
            for option_name, values in options.items():
                formatted_options[option_name] = [
                    {'value': value, 'count': count}
                    for value, count in values.items()
                ]
            
            return {
                'categories': [
                    {'value': str(cat.id), 'name': cat.name, 'count': cat.count}
                    for cat in categories
                ],
                'vendors': [
                    {'value': vendor.vendor, 'name': vendor.vendor, 'count': vendor.count}
                    for vendor in vendors
                ],
                'productTypes': [
                    {'value': pt.product_type, 'name': pt.product_type, 'count': pt.count}
                    for pt in product_types
                ],
                'priceRange': {
                    'min': float(price_stats.min_price) if price_stats.min_price else 0,
                    'max': float(price_stats.max_price) if price_stats.max_price else 1000
                },
                'options': formatted_options
            }
            
        except Exception as e:
            print(f"Error getting catalog filters: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}, 500


class ProductDetailResource(Resource):
    def get(self, product_id):
        """Get detailed product information"""
        try:
            SKU, Category, SKUImage, SKUVariant, SyncLog, ProductOption = get_models()
            sku = SKU.query.get_or_404(product_id)
            return sku.to_dict()
        except Exception as e:
            return {'error': str(e)}, 500


# Settings Resources
class SettingsLogoResource(Resource):
    def get(self):
        """Get current company logo"""
        try:
            db = get_db()
            from sqlalchemy import text
            
            # Check if settings table exists
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                return {'logo_url': None}, 404
            
            # Get logo setting
            result = db.session.execute(text("SELECT value FROM settings WHERE key = 'company_logo' ORDER BY id DESC LIMIT 1")).fetchone()
            
            if result and result[0]:
                return {'logo_url': result[0]}
            else:
                return {'logo_url': None}, 404
                
        except Exception as e:
            print(f"Error getting company logo: {e}")
            return {'error': str(e)}, 500
    
    def post(self):
        """Upload company logo"""
        try:
            if 'logo' not in request.files:
                return {'error': 'No logo file provided'}, 400
            
            file = request.files['logo']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            if not allowed_file(file.filename):
                return {'error': 'Invalid file type. Please upload PNG, JPG, or SVG'}, 400
            
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = f"logo_{timestamp}{filename}"
            file_path = os.path.join(uploads_dir, filename)
            
            # Save file
            file.save(file_path)
            
            # Save to database
            db = get_db()
            from sqlalchemy import text
            
            # Create settings table if it doesn't exist
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"))
            table_exists = result.fetchone() is not None
            
            if not table_exists:
                db.session.execute(text("""
                    CREATE TABLE settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT NOT NULL,
                        value TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.commit()
            
            # Remove old logo setting
            db.session.execute(text("DELETE FROM settings WHERE key = 'company_logo'"))
            
            # Add new logo setting
            logo_url = f"/uploads/{filename}"
            db.session.execute(
                text("INSERT INTO settings (key, value) VALUES ('company_logo', :logo_url)"),
                {"logo_url": logo_url}
            )
            db.session.commit()
            
            return {'message': 'Logo uploaded successfully', 'logo_url': logo_url}, 200
            
        except Exception as e:
            print(f"Error uploading logo: {e}")
            return {'error': 'Failed to upload logo'}, 500
    
    def delete(self):
        """Remove company logo"""
        try:
            db = get_db()
            from sqlalchemy import text
            
            # Get current logo to delete file
            result = db.session.execute(text("SELECT value FROM settings WHERE key = 'company_logo' ORDER BY id DESC LIMIT 1")).fetchone()
            
            if result and result[0]:
                # Delete file
                logo_url = result[0]
                if logo_url.startswith('/uploads/'):
                    filename = logo_url.replace('/uploads/', '')
                    file_path = os.path.join(current_app.root_path, 'uploads', filename)
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting logo file: {e}")
            
            # Remove from database
            db.session.execute(text("DELETE FROM settings WHERE key = 'company_logo'"))
            db.session.commit()
            
            return {'message': 'Logo removed successfully'}, 200
            
        except Exception as e:
            print(f"Error removing logo: {e}")
            return {'error': 'Failed to remove logo'}, 500


# Register resources
api.add_resource(CategoryListResource, '/categories')
api.add_resource(CategoryResource, '/categories/<int:category_id>')
api.add_resource(SKUListResource, '/skus')
api.add_resource(SKUResource, '/skus/<int:sku_id>')
api.add_resource(SearchResource, '/search')
api.add_resource(ShopifySyncResource, '/sync/shopify')
api.add_resource(SyncStatusResource, '/sync/status/<int:sync_id>')
api.add_resource(ShopifyConfigResource, '/shopify/config')
api.add_resource(ShopifyTestResource, '/shopify/test')
api.add_resource(ShopifyStatusResource, '/shopify/status')
api.add_resource(VectorConfigResource, '/vector/config')
api.add_resource(VectorTestResource, '/vector/test')
api.add_resource(VectorStatusResource, '/vector/status')
api.add_resource(VectorSchemaResource, '/vector/schema')
api.add_resource(VectorStatsResource, '/vector/stats')
api.add_resource(VectorReindexResource, '/vector/reindex')
api.add_resource(VectorReindexStatusResource, '/vector/reindex/status/<string:task_id>')
api.add_resource(VectorReindexStopResource, '/vector/reindex/stop')
api.add_resource(VectorClearResource, '/vector/clear')
api.add_resource(APIDocResource, '/docs')
api.add_resource(DebugResource, '/debug')
api.add_resource(CatalogProductsResource, '/catalog/products')
api.add_resource(CatalogFiltersResource, '/catalog/filters')
api.add_resource(ProductDetailResource, '/products/<int:product_id>')
api.add_resource(SettingsLogoResource, '/settings/logo')