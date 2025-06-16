"""
MCP Server for Product Search and Management
Provides tools for the shopping agent to interact with the product database
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from mcp import Server, Tool, TextContent, ImageContent
from mcp.server.stdio import stdio_server
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.weaviate_service import WeaviateService
from services.openai_service import OpenAIService
from models import SKU, Category
from database import db
from sqlalchemy import or_, and_


class ProductMCPServer:
    """MCP Server that provides product search and management tools"""
    
    def __init__(self):
        self.server = Server("product-server")
        self.weaviate_service = None
        self.setup_tools()
    
    def init_services(self):
        """Initialize services (called within app context)"""
        if not self.weaviate_service:
            self.weaviate_service = WeaviateService()
    
    def setup_tools(self):
        """Register all available tools"""
        
        @self.server.tool()
        async def search_products_by_text(query: str, limit: int = 10) -> str:
            """
            Search for products using natural language query
            
            Args:
                query: Search query text
                limit: Maximum number of results to return
                
            Returns:
                JSON string with search results
            """
            try:
                self.init_services()
                
                # Try vector search first
                results = []
                try:
                    vector_results = self.weaviate_service.search_by_text(query, limit=limit)
                    for result in vector_results:
                        product_id = result.get('product_id')
                        if product_id:
                            sku = SKU.query.get(product_id)
                            if sku:
                                product_data = sku.to_dict()
                                product_data['relevance_score'] = 1 - result.get('_additional', {}).get('distance', 1)
                                results.append(product_data)
                except Exception as e:
                    print(f"Vector search failed: {e}")
                
                # Fallback to database search if vector search fails or returns no results
                if not results:
                    search_pattern = f"%{query}%"
                    db_results = SKU.query.filter(
                        or_(
                            SKU.title.ilike(search_pattern),
                            SKU.description.ilike(search_pattern),
                            SKU.tags.ilike(search_pattern)
                        )
                    ).limit(limit).all()
                    
                    results = [sku.to_dict() for sku in db_results]
                
                return json.dumps({
                    "success": True,
                    "count": len(results),
                    "products": results
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "products": []
                })
        
        @self.server.tool()
        async def search_products_by_image(image_base64: str, limit: int = 10) -> str:
            """
            Search for similar products using image
            
            Args:
                image_base64: Base64 encoded image
                limit: Maximum number of results to return
                
            Returns:
                JSON string with similar products
            """
            try:
                self.init_services()
                
                results = []
                vector_results = self.weaviate_service.search_by_image(image_base64, limit=limit)
                
                for result in vector_results:
                    product_id = result.get('product_id')
                    if product_id:
                        sku = SKU.query.get(product_id)
                        if sku:
                            product_data = sku.to_dict()
                            product_data['similarity_score'] = 1 - result.get('_additional', {}).get('distance', 1)
                            results.append(product_data)
                
                return json.dumps({
                    "success": True,
                    "count": len(results),
                    "products": results
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "products": []
                })
        
        @self.server.tool()
        async def get_product_details(product_id: int) -> str:
            """
            Get detailed information about a specific product
            
            Args:
                product_id: ID of the product
                
            Returns:
                JSON string with product details
            """
            try:
                sku = SKU.query.get(product_id)
                if sku:
                    product_data = sku.to_dict()
                    
                    # Add category names
                    product_data['category_names'] = [cat.name for cat in sku.categories]
                    
                    # Add variant details if available
                    if sku.variants:
                        product_data['variants'] = [variant.to_dict() for variant in sku.variants]
                    
                    return json.dumps({
                        "success": True,
                        "product": product_data
                    })
                else:
                    return json.dumps({
                        "success": False,
                        "error": "Product not found"
                    })
                    
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
        
        @self.server.tool()
        async def filter_products(
            categories: Optional[List[int]] = None,
            vendors: Optional[List[str]] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            in_stock: bool = True,
            limit: int = 20
        ) -> str:
            """
            Filter products based on various criteria
            
            Args:
                categories: List of category IDs
                vendors: List of vendor names
                min_price: Minimum price filter
                max_price: Maximum price filter
                in_stock: Only show in-stock items
                limit: Maximum number of results
                
            Returns:
                JSON string with filtered products
            """
            try:
                query = SKU.query
                
                if categories:
                    query = query.join(SKU.categories).filter(Category.id.in_(categories))
                
                if vendors:
                    query = query.filter(SKU.vendor.in_(vendors))
                
                if min_price is not None:
                    query = query.filter(SKU.price >= min_price)
                
                if max_price is not None:
                    query = query.filter(SKU.price <= max_price)
                
                if in_stock:
                    query = query.filter(SKU.quantity > 0)
                
                results = query.limit(limit).all()
                
                return json.dumps({
                    "success": True,
                    "count": len(results),
                    "products": [sku.to_dict() for sku in results]
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "products": []
                })
        
        @self.server.tool()
        async def get_similar_products(product_id: int, limit: int = 5) -> str:
            """
            Find products similar to a given product
            
            Args:
                product_id: ID of the reference product
                limit: Maximum number of similar products
                
            Returns:
                JSON string with similar products
            """
            try:
                # Get the reference product
                sku = SKU.query.get(product_id)
                if not sku:
                    return json.dumps({
                        "success": False,
                        "error": "Product not found"
                    })
                
                # Find similar products based on:
                # 1. Same categories
                # 2. Similar price range
                # 3. Same vendor
                # 4. Similar tags
                
                similar_query = SKU.query.filter(SKU.id != product_id)
                
                # Same categories
                if sku.categories:
                    category_ids = [cat.id for cat in sku.categories]
                    similar_query = similar_query.join(SKU.categories).filter(
                        Category.id.in_(category_ids)
                    )
                
                # Similar price range (±20%)
                if sku.price:
                    price_min = float(sku.price) * 0.8
                    price_max = float(sku.price) * 1.2
                    similar_query = similar_query.filter(
                        and_(SKU.price >= price_min, SKU.price <= price_max)
                    )
                
                results = similar_query.limit(limit).all()
                
                # If not enough results, try broader search
                if len(results) < limit:
                    broader_query = SKU.query.filter(SKU.id != product_id)
                    
                    # Same product type or vendor
                    if sku.product_type or sku.vendor:
                        broader_query = broader_query.filter(
                            or_(
                                SKU.product_type == sku.product_type,
                                SKU.vendor == sku.vendor
                            )
                        )
                    
                    additional = broader_query.limit(limit - len(results)).all()
                    results.extend([r for r in additional if r not in results])
                
                return json.dumps({
                    "success": True,
                    "count": len(results),
                    "products": [r.to_dict() for r in results]
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "products": []
                })
        
        @self.server.tool()
        async def get_product_recommendations(
            user_preferences: Dict[str, Any],
            limit: int = 10
        ) -> str:
            """
            Get personalized product recommendations based on user preferences
            
            Args:
                user_preferences: Dictionary containing user preferences like categories, price range, etc.
                limit: Maximum number of recommendations
                
            Returns:
                JSON string with recommended products
            """
            try:
                query = SKU.query
                
                # Apply preference filters
                if 'categories' in user_preferences:
                    query = query.join(SKU.categories).filter(
                        Category.id.in_(user_preferences['categories'])
                    )
                
                if 'price_range' in user_preferences:
                    min_price = user_preferences['price_range'].get('min')
                    max_price = user_preferences['price_range'].get('max')
                    if min_price:
                        query = query.filter(SKU.price >= min_price)
                    if max_price:
                        query = query.filter(SKU.price <= max_price)
                
                if 'vendors' in user_preferences:
                    query = query.filter(SKU.vendor.in_(user_preferences['vendors']))
                
                # Only in-stock items for recommendations
                query = query.filter(SKU.quantity > 0)
                
                # Order by some relevance (could be improved with ML)
                results = query.limit(limit).all()
                
                return json.dumps({
                    "success": True,
                    "count": len(results),
                    "products": [sku.to_dict() for sku in results]
                })
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "products": []
                })
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream)


# Entry point for running as MCP server
if __name__ == "__main__":
    # Initialize Flask app context for database access
    from ai_ecomm import create_app
    app = create_app()
    
    with app.app_context():
        server = ProductMCPServer()
        asyncio.run(server.run())